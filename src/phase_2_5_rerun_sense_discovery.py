"""
Phase 2.5 Sense-Discovery Re-run Pipeline
==========================================
Implements methods_library.md §1.8 against the EXPANDED CANONICAL CORPUS
(data/posts_snapshot_canonical.csv, 7,021 posts — 71% growth from original 4,114).

This script is the authoritative rerun of the original phase_2_5_sense_discovery.py.
Original outputs at deliverables/phase_2_5_sense_discovery/ remain untouched.
Outputs written to deliverables/phase_2_5_rerun_sense_discovery/.

Comparison summary written to:
  notebooks/audit_trail/phase_2_5_rerun_sense_discovery_summary.md

Procedure per seed term (per §1.8 verbatim):
  1. Extract KWIC windows (±20 tokens)
  2. Embed with all-MiniLM-L6-v2
  3. HDBSCAN at mcs=5,10,20
  4. Embed with all-mpnet-base-v2
  5. HDBSCAN at mcs=5,10,20
  6. Stability cross-table (ARI per config pair)
  7. Exemplar contexts per stable cluster (10 nearest centroid, canonical=minilm mcs=10)
  8. Syntactic features per cluster (POS, code-block, imperative, subreddit)
  9. Write sense_discovery_rerun_notes_{seed}.md
  10. Write phase_2_5_rerun_sense_discovery_summary.md with comparison to prior pass
"""

import os
import re
import time
import warnings
import json
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import hdbscan
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.cluster import adjusted_rand_score
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO = Path(r"C:\Users\drhea\repos\claude-sleep-analysis")
DATA_FILE = REPO / "data" / "posts_snapshot_canonical.csv"   # 7,021 posts
OUT_DIR   = REPO / "deliverables" / "phase_2_5_rerun_sense_discovery"
AUDIT_DIR = REPO / "notebooks" / "audit_trail"
SUMMARY_PATH = AUDIT_DIR / "phase_2_5_rerun_sense_discovery_summary.md"

OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────

SEED_TERMS = ["sleep", "rest", "break", "tired"]
WINDOW     = 20          # ±20 tokens (raw whitespace-split, no lemmatization)
MCS_SETTINGS = [5, 10, 20]
MIN_OCCURRENCES_FOR_CLUSTERING = 50

# Prior-pass counts (from phase_2_5_sense_discovery_summary.md) for comparison
PRIOR_PASS_COUNTS = {
    "sleep": {"n_contexts": 71, "n_posts": 46},
    "rest":  {"n_contexts": 104, "n_posts": 90},
    "break": {"n_contexts": 104, "n_posts": 94},
    "tired": {"n_contexts": 69, "n_posts": 58},
}

# Prior-pass cluster structure under canonical config (minilm mcs=10 if available, else mcs=5)
# Taken verbatim from the prior summary for the comparison section.
PRIOR_PASS_CLUSTER_TABLE = {
    "sleep": {
        "ref_mcs": 5,
        "clusters": [
            {"id": 0, "n": 5, "top_pos": "NOUN", "code_block": 0.0, "top_subreddit": "ClaudeAI"},
            {"id": 1, "n": 60, "top_pos": "NOUN", "code_block": 0.0, "top_subreddit": "ClaudeAI"},
        ],
        "noise_frac_at_ref": 0.0845,
        "mcs10_clusters": 0,  # mcs=10 produced 0 clusters in the prior pass
        "mean_ari": 0.415,
    },
    "rest": {
        "ref_mcs": 5,
        "clusters": [
            {"id": 0, "n": 57, "top_pos": "NOUN", "code_block": 0.0, "top_subreddit": "Anthropic"},
            {"id": 1, "n": 8,  "top_pos": "NOUN", "code_block": 0.0, "top_subreddit": "ClaudeCode"},
        ],
        "noise_frac_at_ref": 0.375,
        "mcs10_clusters": 0,
        "mean_ari": 0.405,
    },
    "break": {
        "ref_mcs": 10,
        "clusters": [
            {"id": 0, "n": 11, "top_pos": "VERB", "code_block": 0.0, "top_subreddit": "claudexplorers"},
            {"id": 1, "n": 10, "top_pos": "VERB", "code_block": 0.0, "top_subreddit": "claudexplorers"},
        ],
        "noise_frac_at_ref": 0.7981,
        "mcs10_clusters": 2,
        "mean_ari": 0.214,   # lowest; break was unstable
        "mpnet_mcs10_clusters": 0,  # mpnet mcs=10 collapsed to 0
    },
    "tired": {
        "ref_mcs": 5,
        "clusters": [
            {"id": 0, "n": 35, "top_pos": "ADJ", "code_block": 0.0, "imperative": 0.06, "top_subreddit": "ClaudeAI"},
            {"id": 1, "n": 8,  "top_pos": "ADJ", "code_block": 0.0, "imperative": 0.0,  "top_subreddit": "ClaudeCode"},
        ],
        "noise_frac_at_ref": 0.3768,
        "mcs10_clusters": 0,
        "mean_ari": 0.400,
    },
}

IMPERATIVE_PRECEDING = [
    "you should", "go", "try", "you need to", "you need",
    "please", "just", "should", "must"
]


# ── Helpers (identical to original script) ───────────────────────────────────

def tokenize_raw(text: str) -> list:
    return text.split()


def extract_kwic(df: pd.DataFrame, seed: str, window: int = WINDOW) -> pd.DataFrame:
    rows = []
    pattern = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)
    for _, row in df.iterrows():
        body = str(row.get("body", "") or "")
        tokens = tokenize_raw(body)
        for i, tok in enumerate(tokens):
            if pattern.fullmatch(tok.strip(".,;:!?\"'()[]{}")):
                left_start = max(0, i - window)
                right_end  = min(len(tokens), i + window + 1)
                left_ctx   = " ".join(tokens[left_start:i])
                keyword    = tokens[i]
                right_ctx  = " ".join(tokens[i + 1:right_end])
                full_ctx   = " ".join(tokens[left_start:right_end])
                rows.append({
                    "post_id":      row["post_id"],
                    "createdAt":    row.get("createdAt", ""),
                    "subreddit":    row.get("subreddit", ""),
                    "left_context": left_ctx,
                    "keyword":      keyword,
                    "right_context":right_ctx,
                    "full_context": full_ctx,
                })
    return pd.DataFrame(rows)


def embed_contexts(contexts: list, model: SentenceTransformer,
                   batch_size: int = 64) -> np.ndarray:
    return model.encode(contexts, batch_size=batch_size,
                        show_progress_bar=True, convert_to_numpy=True)


def run_hdbscan(embeddings: np.ndarray, mcs: int) -> np.ndarray:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        min_samples=1,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(embeddings)


def compute_stability_crosstable(label_dict: dict) -> pd.DataFrame:
    keys = list(label_dict.keys())
    n    = len(keys)
    mat  = np.zeros((n, n))
    for i, j in combinations(range(n), 2):
        a, b        = label_dict[keys[i]], label_dict[keys[j]]
        ari         = adjusted_rand_score(a, b)
        mat[i, j]   = ari
        mat[j, i]   = ari
    for i in range(n):
        mat[i, i] = 1.0
    return pd.DataFrame(mat, index=keys, columns=keys)


def find_exemplars(embeddings: np.ndarray, labels: np.ndarray,
                   kwic_df: pd.DataFrame, n_exemplars: int = 10) -> pd.DataFrame:
    rows = []
    unique_labels = [l for l in np.unique(labels) if l != -1]
    for cl in unique_labels:
        mask       = labels == cl
        cl_embs    = embeddings[mask]
        cl_indices = np.where(mask)[0]
        centroid   = cl_embs.mean(axis=0, keepdims=True)
        sims       = cosine_similarity(centroid, cl_embs)[0]
        top_n      = min(n_exemplars, len(sims))
        top_idx    = np.argsort(sims)[::-1][:top_n]
        for rank, idx in enumerate(top_idx):
            corpus_idx = cl_indices[idx]
            row        = kwic_df.iloc[corpus_idx]
            rows.append({
                "cluster_id_minilm_mcs10": int(cl),
                "full_context":            row["full_context"],
                "post_id":                 row["post_id"],
                "subreddit":               row["subreddit"],
                "similarity_to_centroid":  float(sims[idx]),
            })
    return pd.DataFrame(rows)


def has_code_block(text: str) -> bool:
    if "```" in text:
        return True
    lines = text.split("\n")
    consecutive = 0
    for line in lines:
        if line.startswith("    "):
            consecutive += 1
            if consecutive >= 2:
                return True
        else:
            consecutive = 0
    return False


def is_imperative_context(left_ctx: str, keyword: str) -> bool:
    lc = left_ctx.lower().strip()
    for phrase in IMPERATIVE_PRECEDING:
        if lc.endswith(phrase):
            return True
    if lc == "" or lc.endswith((".", "!", "?")):
        return True
    return False


def compute_syntactic_features(kwic_df: pd.DataFrame, labels: np.ndarray,
                                nlp, seed: str) -> pd.DataFrame:
    kwic_df = kwic_df.copy()
    kwic_df["cluster_id"] = labels

    code_flags      = []
    imperative_flags= []
    full_contexts   = kwic_df["full_context"].tolist()
    left_contexts   = kwic_df["left_context"].tolist()
    seed_pattern    = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)

    for ctx, left in zip(full_contexts, left_contexts):
        code_flags.append(has_code_block(ctx))
        imperative_flags.append(is_imperative_context(left, seed))

    pos_tags = []
    docs = list(nlp.pipe(full_contexts, batch_size=100,
                         disable=["ner", "parser"]))
    for doc in docs:
        found_pos = "UNKNOWN"
        for token in doc:
            if seed_pattern.fullmatch(token.text.strip(".,;:!?\"'()[]{}")):
                found_pos = token.pos_
                break
        pos_tags.append(found_pos)

    kwic_df["pos"]           = pos_tags
    kwic_df["has_code_block"]= code_flags
    kwic_df["is_imperative"] = imperative_flags

    rows = []
    for cl in sorted(kwic_df["cluster_id"].unique()):
        sub = kwic_df[kwic_df["cluster_id"] == cl]
        n   = len(sub)
        rows.append({
            "cluster_id":          int(cl),
            "n_contexts":          n,
            "pos_distribution":    json.dumps(sub["pos"].value_counts().to_dict()),
            "frac_code_block":     round(sub["has_code_block"].mean(), 4),
            "frac_imperative":     round(sub["is_imperative"].mean(), 4),
            "subreddit_distribution": json.dumps(sub["subreddit"].value_counts().to_dict()),
            "top_subreddit":       sub["subreddit"].value_counts().idxmax() if n > 0 else "",
            "top_pos":             sub["pos"].value_counts().idxmax() if n > 0 else "",
        })
    return pd.DataFrame(rows)


# ── Per-seed notes writer ─────────────────────────────────────────────────────

def write_notes(seed: str, kwic_df: pd.DataFrame,
                cluster_results: dict, stability_df: pd.DataFrame,
                exemplars_df: pd.DataFrame, syntactic_df: pd.DataFrame,
                timing: dict, out_dir: Path, ref_mcs: int = 10):
    """Write sense_discovery_rerun_notes_{seed}.md"""
    lines = []
    lines.append(f"# Sense-Discovery Rerun Notes: `{seed}`")
    lines.append("")
    lines.append(f"**Date:** 2026-05-17")
    lines.append(f"**Method:** methods_library.md §1.8")
    lines.append(f"**Input:** posts_snapshot_canonical.csv (7,021 posts)")
    lines.append(f"**Prior pass input:** posts_snapshot.csv (4,114 posts)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Corpus coverage")
    lines.append("")
    n_contexts = len(kwic_df)
    n_posts    = kwic_df["post_id"].nunique()
    prior      = PRIOR_PASS_COUNTS[seed]
    delta_ctx  = n_contexts - prior["n_contexts"]
    pct_growth = (delta_ctx / prior["n_contexts"] * 100) if prior["n_contexts"] > 0 else float("nan")
    lines.append(f"- Total contexts extracted: {n_contexts}")
    lines.append(f"- Total posts represented: {n_posts}")
    lines.append(f"- Prior pass: {prior['n_contexts']} contexts from {prior['n_posts']} posts")
    lines.append(f"- Growth: +{delta_ctx} contexts ({pct_growth:+.1f}%)")
    if n_contexts < MIN_OCCURRENCES_FOR_CLUSTERING:
        lines.append(f"- **WARNING: fewer than {MIN_OCCURRENCES_FOR_CLUSTERING} occurrences.**")
        lines.append(f"  Clustering is unreliable at this count. KWIC samples surfaced for hand reading.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Embedding and clustering results")
    lines.append("")

    for (model_name, mcs), labels in cluster_results.items():
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_n    = int((labels == -1).sum())
        noise_frac = round(noise_n / len(labels), 3) if len(labels) > 0 else 0
        lines.append(f"### {model_name} | mcs={mcs}")
        lines.append(f"- Clusters found: {n_clusters}")
        lines.append(f"- Noise points: {noise_n} ({noise_frac*100:.1f}%)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 3. Stability cross-table (ARI)")
    lines.append("")
    lines.append("Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.")
    lines.append("")
    if not stability_df.empty:
        lines.append(stability_df.round(3).to_markdown())
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Cluster-level structural descriptions")
    lines.append("")
    lines.append(f"**Reference configuration: minilm + mcs={ref_mcs}**")
    if ref_mcs != 10:
        lines.append(f"  (mcs=10 produced no clusters; mcs={ref_mcs} used as fallback reference)")
    lines.append("Labels are not assigned. Structure is reported only.")
    lines.append("")

    ref_key      = ("minilm", ref_mcs)
    ref_labels   = cluster_results.get(ref_key, np.array([]))
    ref_clusters = [c for c in np.unique(ref_labels) if c != -1]

    if len(ref_clusters) == 0:
        lines.append("No clusters produced under reference configuration.")
    else:
        for cl in ref_clusters:
            cl_syn = syntactic_df[syntactic_df["cluster_id"] == cl]
            if cl_syn.empty:
                continue
            row = cl_syn.iloc[0]
            n   = int(row["n_contexts"])

            # Stability: co-assignment purity with mpnet at same mcs
            mpnet_labels = cluster_results.get(("mpnet", ref_mcs), np.array([]))
            if len(mpnet_labels) == len(ref_labels):
                mask     = ref_labels == cl
                mpnet_cl = mpnet_labels[mask]
                non_noise= mpnet_cl[mpnet_cl != -1]
                if len(non_noise) > 0:
                    dominant = np.bincount(non_noise + 1).argmax() - 1
                    purity   = (non_noise == dominant).mean()
                else:
                    purity = 0.0
                stability_note = f"mpnet co-assignment purity={purity:.2f}"
                is_stable      = purity >= 0.5
            else:
                stability_note = "mpnet labels unavailable"
                is_stable      = False

            lines.append(f"### Cluster {cl} (n={n})")
            lines.append(f"- Stability: {'**stable**' if is_stable else '**unstable**'} ({stability_note})")
            lines.append(f"- Top POS of seed token: {row['top_pos']}")
            lines.append(f"- POS distribution: {json.loads(row['pos_distribution'])}")
            lines.append(f"- Fraction with code block: {row['frac_code_block']}")
            lines.append(f"- Fraction with imperative grammar: {row['frac_imperative']}")
            lines.append(f"- Subreddit distribution: {json.loads(row['subreddit_distribution'])}")
            lines.append(f"- Top subreddit: {row['top_subreddit']}")
            lines.append("")

            cl_col      = "cluster_id_minilm_mcs10" if "cluster_id_minilm_mcs10" in exemplars_df.columns else None
            cl_exemplars= exemplars_df[exemplars_df[cl_col] == cl].head(3) if cl_col else pd.DataFrame()
            if not cl_exemplars.empty:
                lines.append("  **Top 3 exemplar contexts (cosine-nearest to centroid):**")
                for _, ex_row in cl_exemplars.iterrows():
                    truncated = ex_row["full_context"][:300].replace("\n", " ")
                    lines.append(f"  - [{ex_row['subreddit']}] ...{truncated}...")
                lines.append("")

    noise_n_ref = int((ref_labels == -1).sum()) if len(ref_labels) > 0 else 0
    if noise_n_ref > 0:
        lines.append(f"### Noise points (cluster_id=-1, n={noise_n_ref})")
        lines.append(f"- These contexts did not fit any cluster under minilm mcs={ref_mcs}.")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 5. Compute resources")
    lines.append("")
    for k, v in timing.items():
        lines.append(f"- {k}: {v:.1f}s")
    lines.append("")

    out_path = out_dir / f"sense_discovery_rerun_notes_{seed}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Wrote: {out_path}")


# ── Main pipeline per seed ────────────────────────────────────────────────────

def process_seed(seed: str, df: pd.DataFrame,
                 model_minilm: SentenceTransformer,
                 model_mpnet:  SentenceTransformer,
                 nlp, out_dir: Path) -> dict:
    print(f"\n{'='*60}")
    print(f"Processing seed: {seed}")
    print(f"{'='*60}")
    timing = {}

    # Step 1: KWIC extraction
    t0 = time.time()
    kwic_df = extract_kwic(df, seed, window=WINDOW)
    timing["kwic_extraction"] = time.time() - t0
    print(f"  KWIC contexts: {len(kwic_df)} from {kwic_df['post_id'].nunique()} posts")
    kwic_df.to_csv(out_dir / f"kwic_full_{seed}.csv", index=False)

    n_contexts = len(kwic_df)
    if n_contexts < MIN_OCCURRENCES_FOR_CLUSTERING:
        print(f"  WARNING: only {n_contexts} contexts — below floor ({MIN_OCCURRENCES_FOR_CLUSTERING}).")
        return {
            "seed": seed, "n_contexts": n_contexts,
            "n_posts": kwic_df["post_id"].nunique(), "below_floor": True,
            "kwic_df": kwic_df, "cluster_results": {}, "ref_mcs": None,
            "stability_df": pd.DataFrame(), "exemplars_df": pd.DataFrame(),
            "syntactic_df": pd.DataFrame(), "timing": timing,
        }

    contexts = kwic_df["full_context"].tolist()

    # Step 2: Embed MiniLM
    t0 = time.time()
    print("  Embedding with all-MiniLM-L6-v2...")
    emb_minilm = embed_contexts(contexts, model_minilm)
    timing["embed_minilm"] = time.time() - t0
    np.save(out_dir / f"embeddings_{seed}_minilm.npy", emb_minilm)

    # Step 3: HDBSCAN × MiniLM
    cluster_results = {}
    for mcs in MCS_SETTINGS:
        t0     = time.time()
        labels = run_hdbscan(emb_minilm, mcs)
        timing[f"hdbscan_minilm_mcs{mcs}"] = time.time() - t0
        cluster_results[("minilm", mcs)] = labels
        pd.DataFrame({"post_id": kwic_df["post_id"].values, "cluster_id": labels}).to_csv(
            out_dir / f"clusters_{seed}_minilm_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"    MiniLM mcs={mcs}: {n_cl} clusters, noise={( labels==-1).mean():.2%}")

    # Step 4: Embed MPNet
    t0 = time.time()
    print("  Embedding with all-mpnet-base-v2...")
    emb_mpnet = embed_contexts(contexts, model_mpnet)
    timing["embed_mpnet"] = time.time() - t0
    np.save(out_dir / f"embeddings_{seed}_mpnet.npy", emb_mpnet)

    # Step 5: HDBSCAN × MPNet
    for mcs in MCS_SETTINGS:
        t0     = time.time()
        labels = run_hdbscan(emb_mpnet, mcs)
        timing[f"hdbscan_mpnet_mcs{mcs}"] = time.time() - t0
        cluster_results[("mpnet", mcs)] = labels
        pd.DataFrame({"post_id": kwic_df["post_id"].values, "cluster_id": labels}).to_csv(
            out_dir / f"clusters_{seed}_mpnet_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"    MPNet  mcs={mcs}: {n_cl} clusters, noise={( labels==-1).mean():.2%}")

    # Step 5b: Stability cross-table
    t0         = time.time()
    label_dict = {f"{m}_mcs{n}": v for (m, n), v in cluster_results.items()}
    stab_df    = compute_stability_crosstable(label_dict)
    timing["stability"] = time.time() - t0
    stab_df.to_csv(out_dir / f"stability_crosstable_{seed}.csv")

    # Step 6: Exemplars — canonical reference minilm mcs=10, fallback mcs=5
    ref_mcs    = 10
    ref_labels = cluster_results[("minilm", 10)]
    if len(set(ref_labels) - {-1}) == 0:
        ref_mcs    = 5
        ref_labels = cluster_results[("minilm", 5)]
        print(f"  Note: minilm mcs=10 produced no clusters; using mcs=5 as reference.")

    t0           = time.time()
    exemplars_df = find_exemplars(emb_minilm, ref_labels, kwic_df, n_exemplars=10)
    timing["exemplars"] = time.time() - t0
    exemplars_df.to_csv(out_dir / f"exemplars_{seed}.csv", index=False)

    # Step 7: Syntactic features
    t0           = time.time()
    print("  Computing syntactic features (spaCy)...")
    syntactic_df = compute_syntactic_features(kwic_df, ref_labels, nlp, seed)
    timing["syntactic"] = time.time() - t0
    syntactic_df.to_csv(out_dir / f"syntactic_features_per_cluster_{seed}.csv", index=False)

    timing["_ref_mcs"] = ref_mcs

    # Step 8: Write notes
    write_notes(seed, kwic_df, cluster_results, stab_df, exemplars_df,
                syntactic_df, timing, out_dir, ref_mcs=ref_mcs)

    return {
        "seed": seed, "n_contexts": n_contexts,
        "n_posts": kwic_df["post_id"].nunique(), "below_floor": False,
        "kwic_df": kwic_df, "cluster_results": cluster_results, "ref_mcs": ref_mcs,
        "stability_df": stab_df, "exemplars_df": exemplars_df,
        "syntactic_df": syntactic_df, "timing": timing,
    }


# ── Summary writer (includes comparison to prior pass) ───────────────────────

def write_summary(all_results: list, total_start: float, summary_path: Path):
    lines = []
    lines.append("# Phase 2.5 Rerun Sense-Discovery Summary")
    lines.append("")
    lines.append("**Date:** 2026-05-17")
    lines.append("**Method:** methods_library.md §1.8")
    lines.append("**Input:** data/posts_snapshot_canonical.csv — 7,021 posts (canonical corpus)")
    lines.append("**Prior-pass input:** data/posts_snapshot.csv — 4,114 posts")
    lines.append("**Corpus growth:** 71% (4,114 → 7,021)")
    lines.append("**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)")
    lines.append("**Models:** sentence-transformers/all-MiniLM-L6-v2, sentence-transformers/all-mpnet-base-v2")
    lines.append("**Clustering:** HDBSCAN (min_cluster_size=5,10,20; min_samples=1; metric=euclidean; eom)")
    lines.append("**NLP:** spaCy en_core_web_sm (POS tagging)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Per-seed structural summary")
    lines.append("")

    for res in all_results:
        seed  = res["seed"]
        prior = PRIOR_PASS_COUNTS[seed]
        lines.append(f"### `{seed}`")
        lines.append("")
        lines.append(f"- Total contexts extracted: {res['n_contexts']} (prior pass: {prior['n_contexts']})")
        lines.append(f"- Posts represented: {res['n_posts']} (prior pass: {prior['n_posts']})")
        delta = res["n_contexts"] - prior["n_contexts"]
        pct   = (delta / prior["n_contexts"] * 100) if prior["n_contexts"] > 0 else float("nan")
        lines.append(f"- Context growth: +{delta} ({pct:+.1f}%)")

        if res["below_floor"]:
            lines.append(f"- **Below clustering floor (<{MIN_OCCURRENCES_FOR_CLUSTERING} contexts).**")
            lines.append("")
            continue

        # Cluster count table
        lines.append("")
        lines.append("**Cluster counts by configuration:**")
        lines.append("")
        lines.append("| Model | mcs | Clusters | Noise fraction |")
        lines.append("|---|---|---|---|")
        for (model_name, mcs), labels in res["cluster_results"].items():
            n_cl       = len(set(labels)) - (1 if -1 in labels else 0)
            noise_frac = (labels == -1).mean()
            lines.append(f"| {model_name} | {mcs} | {n_cl} | {noise_frac:.2%} |")
        lines.append("")

        # Stability summary
        stab = res["stability_df"]
        if not stab.empty:
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            mean_ari = np.nanmean(vals)
            min_ari  = np.nanmin(vals)
            max_ari  = np.nanmax(vals)
            lines.append(f"**Stability (ARI, all config pairs):** mean={mean_ari:.3f}, "
                         f"min={min_ari:.3f}, max={max_ari:.3f}")
            lines.append("")
            stab_flat = []
            keys = stab.index.tolist()
            for i, j in combinations(range(len(keys)), 2):
                stab_flat.append((keys[i], keys[j], stab.values[i, j]))
            stab_flat.sort(key=lambda x: x[2], reverse=True)
            if stab_flat:
                best  = stab_flat[0]
                worst = stab_flat[-1]
                lines.append(f"- Highest agreement: {best[0]} vs {best[1]} (ARI={best[2]:.3f})")
                lines.append(f"- Lowest agreement:  {worst[0]} vs {worst[1]} (ARI={worst[2]:.3f})")
            lines.append("")

        # Syntactic per cluster
        syn      = res["syntactic_df"]
        ref_mcs  = res.get("ref_mcs", 10)
        ref_lbls = res["cluster_results"].get(("minilm", ref_mcs), np.array([]))
        n_cl_ref = len([c for c in np.unique(ref_lbls) if c != -1]) if len(ref_lbls) > 0 else 0
        lines.append(f"**Reference clusters (minilm mcs={ref_mcs}): {n_cl_ref} clusters**")
        lines.append("")
        if not syn.empty:
            for _, row in syn[syn["cluster_id"] != -1].iterrows():
                lines.append(
                    f"  Cluster {int(row['cluster_id'])} (n={int(row['n_contexts'])}): "
                    f"top_pos={row['top_pos']}, "
                    f"code_block={row['frac_code_block']:.0%}, "
                    f"imperative={row['frac_imperative']:.0%}, "
                    f"top_subreddit={row['top_subreddit']}"
                )
        lines.append("")
        timing_total = sum(v for v in res["timing"].values())
        lines.append(f"**Time elapsed:** {timing_total:.1f}s")
        lines.append("")

    # ── Cross-seed observation ─────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 2. Cross-seed observation")
    lines.append("")

    code_block_seeds = []
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        syn = res["syntactic_df"]
        if (syn[syn["cluster_id"] != -1]["frac_code_block"] > 0.20).any():
            code_block_seeds.append(res["seed"])

    if code_block_seeds:
        lines.append(f"- A code-block-dominant cluster (>20% fraction) emerged in: "
                     f"{', '.join(code_block_seeds)}.")
        lines.append(f"  **This is a change from the prior pass, where no seed produced a code-block cluster.**")
    else:
        lines.append("- No seeds showed a dominant code-block cluster at the >20% threshold.")
        lines.append("  This replicates the prior pass finding.")
    lines.append("")

    lines.append("**Subreddit-dominant clusters:**")
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        seed     = res["seed"]
        syn      = res["syntactic_df"]
        non_noise= syn[syn["cluster_id"] != -1]
        sub_dom  = non_noise["top_subreddit"].value_counts()
        lines.append(f"  `{seed}`: top subreddits by cluster dominance: {sub_dom.to_dict()}")
    lines.append("")

    # ── Comparison to prior pass ───────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 3. Comparison to original Phase 2.5 pass")
    lines.append("")
    lines.append("The five comparison questions specified by the task brief are answered here.")
    lines.append("")

    # Q1: Did hit counts grow and by how much?
    lines.append("### Q1. Did hit counts grow, and by how much?")
    lines.append("")
    lines.append("| Seed | Prior contexts | Rerun contexts | Growth |")
    lines.append("|---|---|---|---|")
    for res in all_results:
        seed  = res["seed"]
        prior = PRIOR_PASS_COUNTS[seed]
        delta = res["n_contexts"] - prior["n_contexts"]
        pct   = (delta / prior["n_contexts"] * 100) if prior["n_contexts"] > 0 else float("nan")
        lines.append(f"| {seed} | {prior['n_contexts']} | {res['n_contexts']} | +{delta} ({pct:+.1f}%) |")
    lines.append("")

    # Q2: Did mcs=10 produce clusters where it failed before?
    lines.append("### Q2. Did mcs=10 now produce clusters where it failed before?")
    lines.append("")
    lines.append("| Seed | Prior mcs=10 clusters | Rerun mcs=10 clusters (minilm) |")
    lines.append("|---|---|---|")
    for res in all_results:
        seed     = res["seed"]
        prior_cl = PRIOR_PASS_CLUSTER_TABLE[seed].get("mcs10_clusters", 0)
        if res["below_floor"]:
            rerun_cl = "n/a (below floor)"
        else:
            lbls     = res["cluster_results"].get(("minilm", 10), np.array([]))
            rerun_cl = str(len(set(lbls) - {-1})) if len(lbls) > 0 else "0"
        lines.append(f"| {seed} | {prior_cl} | {rerun_cl} |")
    lines.append("")

    # Q3: Did a code-block cluster emerge?
    lines.append("### Q3. Did a code-block cluster emerge (it did not in the original pass)?")
    lines.append("")
    if code_block_seeds:
        lines.append(f"Yes: seeds {', '.join(code_block_seeds)} produced a cluster with >20% code-block fraction.")
    else:
        lines.append("No: no seed produced a code-block-dominant cluster at the >20% threshold.")
        lines.append("The prior pass finding (no code-block cluster) is replicated.")
    lines.append("")

    # Q4: Did `break` clusters stabilize?
    lines.append("### Q4. Did `break` clusters stabilize across embedding models (mpnet purity was 0.00 originally)?")
    lines.append("")
    break_res = next((r for r in all_results if r["seed"] == "break"), None)
    if break_res and not break_res["below_floor"] and not break_res["stability_df"].empty:
        stab      = break_res["stability_df"]
        vals      = stab.values.copy()
        np.fill_diagonal(vals, np.nan)
        mean_ari  = float(np.nanmean(vals))
        # Look up cross-model pairs specifically (minilm mcs vs mpnet mcs)
        cross_model_pairs = []
        for col1 in stab.columns:
            for col2 in stab.columns:
                if col1 < col2 and ("minilm" in col1) != ("minilm" in col2):
                    cross_model_pairs.append((col1, col2, stab.loc[col1, col2]))
        if cross_model_pairs:
            cross_mean = np.mean([x[2] for x in cross_model_pairs])
            lines.append(f"- Mean ARI (all pairs): {mean_ari:.3f} (prior pass: 0.214)")
            lines.append(f"- Mean cross-model ARI (minilm vs mpnet pairs): {cross_mean:.3f}")
            if cross_mean >= 0.3:
                lines.append("- **Assessment: cross-model stability improved substantially.**")
            elif cross_mean >= 0.1:
                lines.append("- **Assessment: marginal cross-model stability improvement; clusters remain fragile.**")
            else:
                lines.append("- **Assessment: cross-model stability did not improve materially.**")
        else:
            lines.append(f"- Mean ARI (all pairs): {mean_ari:.3f} (prior pass: 0.214)")
    else:
        lines.append("- `break` did not reach the clustering floor or stability data unavailable.")
    lines.append("")

    # Q5: Did `rest`'s REST-API/remainder cluster persist?
    lines.append("### Q5. Did `rest`'s REST-API / remainder cluster persist?")
    lines.append("")
    rest_res = next((r for r in all_results if r["seed"] == "rest"), None)
    if rest_res and not rest_res["below_floor"] and not rest_res["syntactic_df"].empty:
        syn      = rest_res["syntactic_df"]
        non_noise= syn[syn["cluster_id"] != -1]
        # Look for ClaudeCode-dominant cluster as proxy for REST API / programming sense
        code_clusters = non_noise[non_noise["top_subreddit"] == "ClaudeCode"]
        if not code_clusters.empty:
            lines.append(f"- A cluster with top_subreddit=ClaudeCode persists in the rerun "
                         f"(n={int(code_clusters['n_contexts'].sum())}), consistent with a "
                         f"programming/REST-API sense for 'rest'.")
        else:
            lines.append("- No cluster with ClaudeCode as dominant subreddit was found. The "
                         "REST-API / programming-sense cluster did not clearly persist under the "
                         "rerun configuration.")
        # Also report code-block fraction for rest clusters
        for _, row in non_noise.iterrows():
            lines.append(
                f"  Cluster {int(row['cluster_id'])}: top_subreddit={row['top_subreddit']}, "
                f"code_block={row['frac_code_block']:.0%}, n={int(row['n_contexts'])}"
            )
    else:
        lines.append("- `rest` did not produce clusters or syntactic data unavailable.")
    lines.append("")

    # ── Operational decision question ──────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 4. Has the 71% corpus expansion enabled clean sense separation?")
    lines.append("")
    lines.append("This is the operational decision the next checkpoint hinges on.")
    lines.append("")

    # Compute summary evidence
    n_seeds_with_mcs10 = 0
    n_seeds_stable     = 0
    n_seeds_total      = 0
    for res in all_results:
        if res["below_floor"]:
            continue
        n_seeds_total += 1
        lbls = res["cluster_results"].get(("minilm", 10), np.array([]))
        if len(set(lbls) - {-1}) >= 2:
            n_seeds_with_mcs10 += 1
        stab = res["stability_df"]
        if not stab.empty:
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            mean_ari = float(np.nanmean(vals))
            if mean_ari >= 0.4:
                n_seeds_stable += 1

    lines.append(f"- Seeds reaching mcs=10 clustering (2+ clusters at canonical config): "
                 f"{n_seeds_with_mcs10}/{n_seeds_total}")
    lines.append(f"- Seeds with mean cross-config ARI >= 0.4: {n_seeds_stable}/{n_seeds_total}")
    lines.append(f"- Code-block cluster present: {'yes (' + ', '.join(code_block_seeds) + ')' if code_block_seeds else 'no'}")
    lines.append("")
    lines.append("**Researcher decision required at Pattern A checkpoint.**")
    lines.append("")
    lines.append("Evidence to weigh:")
    lines.append("- If 3+ seeds now produce 2+ stable clusters at mcs=10 with cross-model ARI > 0.3,")
    lines.append("  the expansion is sufficient for sense separation; proceed to Phase 3.")
    lines.append("- If mcs=10 still collapses to noise for 2+ seeds, or cross-model stability remains")
    lines.append("  below 0.2, the wholesale corpus is too thin even at 7,021 posts; escalate to")
    lines.append("  Pass 1b integration (keyword-search-filtered posts) with documented provenance caveat.")
    lines.append("- A code-block cluster emerging for any seed would be confirmatory evidence of")
    lines.append("  sufficient N to support programming-sense separation.")
    lines.append("")

    # ── Timing ────────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 5. Compute resources and timing")
    lines.append("")
    total_elapsed = time.time() - total_start
    lines.append(f"- Total wall-clock time: {total_elapsed:.1f}s")
    lines.append("")
    for res in all_results:
        lines.append(f"**{res['seed']}:**")
        for k, v in res.get("timing", {}).items():
            lines.append(f"  - {k}: {v:.1f}s")
    lines.append("")

    # ── Anomalies ─────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 6. Anomalies")
    lines.append("")
    lines.append("- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),")
    lines.append("  consistent with methods_library.md §1.8.")
    lines.append("- HDBSCAN metric=euclidean on sentence-transformer embeddings. Cosine distance is")
    lines.append("  equivalent after L2 normalization; sentence-transformers does not apply L2 by default.")
    lines.append("- POS tagging uses spaCy en_core_web_sm. Reliability may be reduced in code-heavy contexts.")
    lines.append("- Subreddit strings are exact scraper source field values: 'ClaudeCode', 'ClaudeAI',")
    lines.append("  'claudexplorers', 'Anthropic'.")
    lines.append("- The canonical corpus (posts_snapshot_canonical.csv) is a union of Pass 1a original")
    lines.append("  and the broader-retrieval re-scrape; it remains wholesale (no keyword pre-filter).")
    lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote summary: {summary_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    total_start = time.time()

    print("Loading canonical corpus...")
    df = pd.read_csv(DATA_FILE)
    if "type" in df.columns:
        df = df[df["type"] == "post"].copy()
    df["body"] = df["body"].fillna("").astype(str)
    print(f"  Posts loaded: {len(df)} (from {DATA_FILE.name})")

    print("\nLoading embedding models...")
    t0 = time.time()
    model_minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(f"  MiniLM loaded in {time.time()-t0:.1f}s")
    t0 = time.time()
    model_mpnet  = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    print(f"  MPNet loaded in {time.time()-t0:.1f}s")

    print("\nLoading spaCy en_core_web_sm...")
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    print("  spaCy loaded.")

    all_results = []
    for seed in SEED_TERMS:
        result = process_seed(seed, df, model_minilm, model_mpnet, nlp, OUT_DIR)
        all_results.append(result)

    write_summary(all_results, total_start, SUMMARY_PATH)

    print(f"\nAll seeds processed. Total elapsed: {time.time()-total_start:.1f}s")
    print(f"Outputs in: {OUT_DIR}")
    print(f"Summary at: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
