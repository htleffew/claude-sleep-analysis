"""
Phase 2.5 Sense-Discovery — Pass 1b Canonical Corpus
=====================================================
Implements methods_library.md §1.8 against the Pass 1b canonical corpus
(data/pass1b_canonical.csv, 773 rows: 242 posts + 531 comments).

This is the third run of §1.8 on this project.  The prior two ran on:
  Run 1: data/posts_snapshot.csv (4,114 wholesale posts)
  Run 2: data/posts_snapshot_canonical.csv (7,021 wholesale posts)

Pass 1b is a targeted-retrieval corpus (server-side search + Arctic Shift
round-2 fresh fetch), so it includes BOTH posts and comments and carries a
`retrieval_provenance` field per row.  The operational question is whether
targeted retrieval enables clean sense separation that wholesale at any
scale could not.

Outputs written to:
  deliverables/phase_2_5_pass1b_sense_discovery/

Summary written to:
  notebooks/audit_trail/phase_2_5_pass1b_sense_discovery_summary.md

Procedure per seed term (per §1.8 verbatim, adapted for smaller corpus):
  1. Extract KWIC windows (±20 tokens). Save kwic_full_{seed}.csv with
     [post_id, type, retrieval_provenance, full_context].
  2. Embed with all-MiniLM-L6-v2. Save embeddings.
  3. HDBSCAN at mcs=3,5,10. Save cluster assignments.
  4. Embed with all-mpnet-base-v2. Cluster at same settings.
  5. Stability cross-table across model × parameter configurations.
  6. Exemplars (10 per stable cluster, nearest-centroid) under canonical
     config (MiniLM + mcs=5).
  7. Syntactic-feature cross-validation per cluster: POS of seed,
     code-block presence, imperative-mood, subreddit, type (post/comment),
     retrieval_provenance.
  8. Per-seed notes (no sense labels).
  9. Final summary at notebooks/audit_trail/phase_2_5_pass1b_sense_discovery_summary.md
     with comparison to both prior passes.
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

REPO        = Path(r"C:\Users\drhea\repos\claude-sleep-analysis")
DATA_FILE   = REPO / "data" / "pass1b_canonical.csv"
OUT_DIR     = REPO / "deliverables" / "phase_2_5_pass1b_sense_discovery"
AUDIT_DIR   = REPO / "notebooks" / "audit_trail"
SUMMARY_PATH = AUDIT_DIR / "phase_2_5_pass1b_sense_discovery_summary.md"

OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────

SEED_TERMS   = ["sleep", "rest", "break", "tired"]
WINDOW       = 20          # ±20 tokens (raw whitespace-split, stop-words preserved)
MCS_SETTINGS = [3, 5, 10]  # lowered from [5,10,20] for smaller corpus
CANONICAL_MCS = 5          # canonical config per task brief
MIN_OCCURRENCES_FOR_CLUSTERING = 50

# ── Prior-pass counts (for comparison tables) ─────────────────────────────────

# Original wholesale run (4,114 posts)
PRIOR_PASS1_COUNTS = {
    "sleep": {"n_contexts": 71,  "n_posts": 46},
    "rest":  {"n_contexts": 104, "n_posts": 90},
    "break": {"n_contexts": 104, "n_posts": 94},
    "tired": {"n_contexts": 69,  "n_posts": 58},
}

# Canonical wholesale rerun (7,021 posts)
PRIOR_PASS2_COUNTS = {
    "sleep": {"n_contexts": 102, "n_posts": 72},
    "rest":  {"n_contexts": 160, "n_posts": 142},
    "break": {"n_contexts": 187, "n_posts": 170},
    "tired": {"n_contexts": 126, "n_posts": 104},
}

# Prior pass2 cluster counts under canonical config (minilm mcs=5 for rest/tired/sleep fallback,
# mcs=10 was attempted as canonical but collapsed — so effective canonical was mcs=5 or 10 depending)
PRIOR_PASS2_CLUSTER_TABLE = {
    "sleep": {
        "ref_mcs": 10, "ref_clusters": 2,
        "noise_frac": 0.5882, "mean_ari": 0.238,
        "code_block_cluster": False,
    },
    "rest": {
        "ref_mcs": 5, "ref_clusters": 4,
        "noise_frac": 0.7375, "mean_ari": 0.306,
        "code_block_cluster": False,
        "claudecode_cluster_n": 5,  # ClaudeCode-dominant cluster (REST-API proxy)
    },
    "break": {
        "ref_mcs": 5, "ref_clusters": 3,
        "noise_frac": 0.4545, "mean_ari": 0.214,
        "code_block_cluster": False,
        "cross_model_ari_mean": 0.249,
    },
    "tired": {
        "ref_mcs": 5, "ref_clusters": 2,
        "noise_frac": 0.1270, "mean_ari": 0.402,
        "code_block_cluster": False,
    },
}

IMPERATIVE_PRECEDING = [
    "you should", "go", "try", "you need to", "you need",
    "please", "just", "should", "must"
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def tokenize_raw(text: str) -> list:
    return text.split()


def extract_kwic(df: pd.DataFrame, seed: str, window: int = WINDOW) -> pd.DataFrame:
    """
    Extract KWIC windows for each occurrence of `seed` in df.
    Returns DataFrame with columns:
      post_id, type, retrieval_provenance, subreddit, createdAt,
      left_context, keyword, right_context, full_context
    """
    rows = []
    pattern = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)
    for _, row in df.iterrows():
        body = str(row.get("body", "") or "")
        tokens = tokenize_raw(body)
        for i, tok in enumerate(tokens):
            if pattern.fullmatch(tok.strip(".,;:!?\"'()[]{}")):
                left_start  = max(0, i - window)
                right_end   = min(len(tokens), i + window + 1)
                left_ctx    = " ".join(tokens[left_start:i])
                keyword_tok = tokens[i]
                right_ctx   = " ".join(tokens[i + 1:right_end])
                full_ctx    = " ".join(tokens[left_start:right_end])
                rows.append({
                    "post_id":             row.get("post_id", ""),
                    "type":                row.get("type", ""),
                    "retrieval_provenance":row.get("retrieval_provenance", ""),
                    "subreddit":           row.get("subreddit", ""),
                    "createdAt":           row.get("createdAt", ""),
                    "left_context":        left_ctx,
                    "keyword":             keyword_tok,
                    "right_context":       right_ctx,
                    "full_context":        full_ctx,
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
        a, b      = label_dict[keys[i]], label_dict[keys[j]]
        ari       = adjusted_rand_score(a, b)
        mat[i, j] = ari
        mat[j, i] = ari
    for i in range(n):
        mat[i, i] = 1.0
    return pd.DataFrame(mat, index=keys, columns=keys)


def find_exemplars(embeddings: np.ndarray, labels: np.ndarray,
                   kwic_df: pd.DataFrame, n_exemplars: int = 10) -> pd.DataFrame:
    rows = []
    unique_labels = [lb for lb in np.unique(labels) if lb != -1]
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
            krow       = kwic_df.iloc[corpus_idx]
            rows.append({
                "cluster_id_minilm_mcs5":  int(cl),
                "full_context":            krow["full_context"],
                "post_id":                 krow["post_id"],
                "type":                    krow.get("type", ""),
                "retrieval_provenance":    krow.get("retrieval_provenance", ""),
                "subreddit":               krow["subreddit"],
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
    """
    Extends the prior-run syntactic features by also stratifying on
    `type` (post vs comment) and `retrieval_provenance`.
    """
    kwic_df = kwic_df.copy()
    kwic_df["cluster_id"] = labels

    code_flags       = []
    imperative_flags = []
    full_contexts    = kwic_df["full_context"].tolist()
    left_contexts    = kwic_df["left_context"].tolist()
    seed_pattern     = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)

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

    kwic_df["pos"]            = pos_tags
    kwic_df["has_code_block"] = code_flags
    kwic_df["is_imperative"]  = imperative_flags

    rows = []
    for cl in sorted(kwic_df["cluster_id"].unique()):
        sub = kwic_df[kwic_df["cluster_id"] == cl]
        n   = len(sub)

        # Provenance distribution: simplify to major provenance groups
        prov_raw = sub["retrieval_provenance"].fillna("unknown")
        prov_counts = {}
        for prov in prov_raw:
            # Use the first source token as the key
            key = prov.split("|")[0].strip() if "|" in prov else prov.strip()
            prov_counts[key] = prov_counts.get(key, 0) + 1

        rows.append({
            "cluster_id":                  int(cl),
            "n_contexts":                  n,
            "pos_distribution":            json.dumps(sub["pos"].value_counts().to_dict()),
            "frac_code_block":             round(float(sub["has_code_block"].mean()), 4),
            "frac_imperative":             round(float(sub["is_imperative"].mean()), 4),
            "subreddit_distribution":      json.dumps(sub["subreddit"].value_counts().to_dict()),
            "top_subreddit":               sub["subreddit"].value_counts().idxmax() if n > 0 else "",
            "top_pos":                     sub["pos"].value_counts().idxmax() if n > 0 else "",
            "type_distribution":           json.dumps(sub["type"].value_counts().to_dict()),
            "top_type":                    sub["type"].value_counts().idxmax() if n > 0 else "",
            "provenance_distribution":     json.dumps(prov_counts),
        })
    return pd.DataFrame(rows)


# ── Per-seed notes writer ─────────────────────────────────────────────────────

def write_notes(seed: str, kwic_df: pd.DataFrame,
                cluster_results: dict, stability_df: pd.DataFrame,
                exemplars_df: pd.DataFrame, syntactic_df: pd.DataFrame,
                timing: dict, out_dir: Path, ref_mcs: int = CANONICAL_MCS):
    lines = []
    lines.append(f"# Sense-Discovery Pass 1b Notes: `{seed}`")
    lines.append("")
    lines.append("**Date:** 2026-05-17")
    lines.append("**Method:** methods_library.md §1.8")
    lines.append("**Input:** pass1b_canonical.csv (773 rows: 242 posts + 531 comments)")
    lines.append("**Targeted retrieval corpus** (Pass 1b: server-side search + Arctic Shift round-2)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Corpus coverage")
    lines.append("")
    n_contexts = len(kwic_df)
    n_posts_ids = kwic_df["post_id"].nunique()
    n_post_rows = (kwic_df["type"] == "post").sum()
    n_comment_rows = (kwic_df["type"] == "comment").sum()
    prior1 = PRIOR_PASS1_COUNTS[seed]
    prior2 = PRIOR_PASS2_COUNTS[seed]
    lines.append(f"- Total KWIC contexts extracted: {n_contexts}")
    lines.append(f"- Unique post IDs represented: {n_posts_ids}")
    lines.append(f"- Of which from posts (type=post): {n_post_rows}")
    lines.append(f"- Of which from comments (type=comment): {n_comment_rows}")
    lines.append(f"- Prior pass 1 (wholesale 4,114): {prior1['n_contexts']} contexts")
    lines.append(f"- Prior pass 2 (wholesale 7,021): {prior2['n_contexts']} contexts")
    lines.append(f"- Context count vs pass2: {n_contexts - prior2['n_contexts']:+d} "
                 f"({'higher' if n_contexts > prior2['n_contexts'] else 'lower'})")
    if n_contexts < MIN_OCCURRENCES_FOR_CLUSTERING:
        lines.append(f"- **WARNING: fewer than {MIN_OCCURRENCES_FOR_CLUSTERING} contexts.**")
        lines.append("  Clustering is unreliable at this count. KWIC samples surfaced for hand reading.")
    lines.append("")

    # Provenance distribution summary
    prov_counts = kwic_df["retrieval_provenance"].fillna("unknown").value_counts()
    lines.append("### Retrieval provenance distribution of KWIC hits")
    lines.append("")
    for prov, cnt in prov_counts.items():
        lines.append(f"- `{prov}`: {cnt}")
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
    if ref_mcs != CANONICAL_MCS:
        lines.append(f"  (mcs={CANONICAL_MCS} produced no clusters; mcs={ref_mcs} used as fallback reference)")
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

            # Cross-model stability: mpnet purity at same mcs
            mpnet_labels = cluster_results.get(("mpnet", ref_mcs), np.array([]))
            if len(mpnet_labels) == len(ref_labels):
                mask      = ref_labels == cl
                mpnet_cl  = mpnet_labels[mask]
                non_noise = mpnet_cl[mpnet_cl != -1]
                if len(non_noise) > 0:
                    dominant = np.bincount(non_noise + 1).argmax() - 1
                    purity   = float((non_noise == dominant).mean())
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
            lines.append(f"- Type distribution (post/comment): {json.loads(row['type_distribution'])}")
            lines.append(f"- Top type: {row.get('top_type', 'unknown')}")
            lines.append(f"- Provenance distribution: {json.loads(row['provenance_distribution'])}")
            lines.append("")

            # Exemplars
            cl_col      = "cluster_id_minilm_mcs5"
            cl_exemplars = exemplars_df[exemplars_df[cl_col] == cl].head(3) if cl_col in exemplars_df.columns else pd.DataFrame()
            if not cl_exemplars.empty:
                lines.append("  **Top 3 exemplar contexts (cosine-nearest to centroid):**")
                for _, ex_row in cl_exemplars.iterrows():
                    truncated = ex_row["full_context"][:300].replace("\n", " ")
                    type_tag  = ex_row.get("type", "")
                    lines.append(f"  - [{ex_row['subreddit']}|{type_tag}] ...{truncated}...")
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

    out_path = out_dir / f"sense_discovery_notes_{seed}.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Wrote: {out_path}")


# ── Main pipeline per seed ────────────────────────────────────────────────────

def process_seed(seed: str, df: pd.DataFrame,
                 model_minilm: SentenceTransformer,
                 model_mpnet:  SentenceTransformer,
                 nlp, out_dir: Path) -> dict:
    print(f"\n{'='*60}")
    print(f"Processing seed: '{seed}'")
    print(f"{'='*60}")
    timing = {}

    # Step 1: KWIC extraction
    t0 = time.time()
    kwic_df = extract_kwic(df, seed, window=WINDOW)
    timing["kwic_extraction"] = time.time() - t0
    n_contexts = len(kwic_df)
    print(f"  KWIC contexts: {n_contexts} from {kwic_df['post_id'].nunique()} unique post_ids")
    print(f"    posts: {(kwic_df['type']=='post').sum()}, comments: {(kwic_df['type']=='comment').sum()}")

    # Save KWIC with required columns
    kwic_out = kwic_df[["post_id", "type", "retrieval_provenance", "subreddit",
                         "createdAt", "full_context", "left_context", "keyword", "right_context"]]
    kwic_out.to_csv(out_dir / f"kwic_full_{seed}.csv", index=False)

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

    # Step 3: HDBSCAN × MiniLM at mcs=3,5,10
    cluster_results = {}
    for mcs in MCS_SETTINGS:
        t0     = time.time()
        labels = run_hdbscan(emb_minilm, mcs)
        timing[f"hdbscan_minilm_mcs{mcs}"] = time.time() - t0
        cluster_results[("minilm", mcs)] = labels
        pd.DataFrame({
            "post_id": kwic_df["post_id"].values,
            "type":    kwic_df["type"].values,
            "retrieval_provenance": kwic_df["retrieval_provenance"].values,
            "cluster_id": labels
        }).to_csv(out_dir / f"clusters_{seed}_minilm_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"    MiniLM mcs={mcs}: {n_cl} clusters, noise={(labels==-1).mean():.2%}")

    # Step 4: Embed MPNet
    t0 = time.time()
    print("  Embedding with all-mpnet-base-v2...")
    emb_mpnet = embed_contexts(contexts, model_mpnet)
    timing["embed_mpnet"] = time.time() - t0
    np.save(out_dir / f"embeddings_{seed}_mpnet.npy", emb_mpnet)

    # Step 5: HDBSCAN × MPNet at mcs=3,5,10
    for mcs in MCS_SETTINGS:
        t0     = time.time()
        labels = run_hdbscan(emb_mpnet, mcs)
        timing[f"hdbscan_mpnet_mcs{mcs}"] = time.time() - t0
        cluster_results[("mpnet", mcs)] = labels
        pd.DataFrame({
            "post_id": kwic_df["post_id"].values,
            "type":    kwic_df["type"].values,
            "retrieval_provenance": kwic_df["retrieval_provenance"].values,
            "cluster_id": labels
        }).to_csv(out_dir / f"clusters_{seed}_mpnet_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"    MPNet  mcs={mcs}: {n_cl} clusters, noise={(labels==-1).mean():.2%}")

    # Step 5b: Stability cross-table
    t0         = time.time()
    label_dict = {f"{m}_mcs{n}": v for (m, n), v in cluster_results.items()}
    stab_df    = compute_stability_crosstable(label_dict)
    timing["stability"] = time.time() - t0
    stab_df.to_csv(out_dir / f"stability_crosstable_{seed}.csv")

    # Step 6: Exemplars — canonical reference MiniLM mcs=5
    ref_mcs    = CANONICAL_MCS
    ref_labels = cluster_results[("minilm", CANONICAL_MCS)]
    if len(set(ref_labels) - {-1}) == 0:
        # fallback: try smaller mcs
        for fallback_mcs in [3]:
            fb_labels = cluster_results[("minilm", fallback_mcs)]
            if len(set(fb_labels) - {-1}) > 0:
                ref_mcs    = fallback_mcs
                ref_labels = fb_labels
                print(f"  Note: minilm mcs={CANONICAL_MCS} produced no clusters; using mcs={ref_mcs}.")
                break
        else:
            print(f"  Note: no clusters found at any mcs for minilm. All noise.")

    t0           = time.time()
    exemplars_df = find_exemplars(emb_minilm, ref_labels, kwic_df, n_exemplars=10)
    timing["exemplars"] = time.time() - t0
    exemplars_df.to_csv(out_dir / f"exemplars_{seed}.csv", index=False)

    # Step 7: Syntactic features (extended with type and retrieval_provenance)
    t0           = time.time()
    print("  Computing syntactic features (spaCy)...")
    syntactic_df = compute_syntactic_features(kwic_df, ref_labels, nlp, seed)
    timing["syntactic"] = time.time() - t0
    syntactic_df.to_csv(out_dir / f"syntactic_features_per_cluster_{seed}.csv", index=False)

    timing["_ref_mcs"] = float(ref_mcs)

    # Step 8: Per-seed notes
    write_notes(seed, kwic_df, cluster_results, stab_df, exemplars_df,
                syntactic_df, timing, out_dir, ref_mcs=ref_mcs)

    return {
        "seed": seed, "n_contexts": n_contexts,
        "n_posts": kwic_df["post_id"].nunique(), "below_floor": False,
        "kwic_df": kwic_df, "cluster_results": cluster_results, "ref_mcs": ref_mcs,
        "stability_df": stab_df, "exemplars_df": exemplars_df,
        "syntactic_df": syntactic_df, "timing": timing,
    }


# ── Summary writer ────────────────────────────────────────────────────────────

def write_summary(all_results: list, total_start: float,
                  summary_path: Path):
    lines = []
    lines.append("# Phase 2.5 Pass 1b Sense-Discovery Summary")
    lines.append("")
    lines.append("**Date:** 2026-05-17")
    lines.append("**Method:** methods_library.md §1.8")
    lines.append("**Input:** data/pass1b_canonical.csv — 773 rows (242 posts + 531 comments)")
    lines.append("**Corpus type:** Targeted retrieval (Pass 1b: server-side search + Arctic Shift round-2)")
    lines.append("**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)")
    lines.append("**Models:** sentence-transformers/all-MiniLM-L6-v2, sentence-transformers/all-mpnet-base-v2")
    lines.append("**Clustering:** HDBSCAN (min_cluster_size=3,5,10; min_samples=1; metric=euclidean; eom)")
    lines.append("**Canonical config:** MiniLM + mcs=5")
    lines.append("**NLP:** spaCy en_core_web_sm (POS tagging)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Per-seed structural summary")
    lines.append("")

    for res in all_results:
        seed   = res["seed"]
        prior1 = PRIOR_PASS1_COUNTS[seed]
        prior2 = PRIOR_PASS2_COUNTS[seed]
        lines.append(f"### `{seed}`")
        lines.append("")
        lines.append(f"- Total contexts extracted: {res['n_contexts']}")
        lines.append(f"- Prior pass 1 (wholesale 4,114): {prior1['n_contexts']}")
        lines.append(f"- Prior pass 2 (wholesale 7,021): {prior2['n_contexts']}")
        kwic_df = res["kwic_df"]
        n_post_rows    = (kwic_df["type"] == "post").sum()
        n_comment_rows = (kwic_df["type"] == "comment").sum()
        lines.append(f"- Of which: {n_post_rows} from posts, {n_comment_rows} from comments")

        if res["below_floor"]:
            lines.append(f"- **Below clustering floor (<{MIN_OCCURRENCES_FOR_CLUSTERING} contexts). Not clustered.**")
            lines.append("")
            continue

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

        stab = res["stability_df"]
        if not stab.empty:
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            mean_ari = float(np.nanmean(vals))
            min_ari  = float(np.nanmin(vals))
            max_ari  = float(np.nanmax(vals))
            lines.append(f"**Stability (ARI, all config pairs):** mean={mean_ari:.3f}, "
                         f"min={min_ari:.3f}, max={max_ari:.3f}")
            lines.append("")
            stab_flat = []
            keys = stab.index.tolist()
            for i, j in combinations(range(len(keys)), 2):
                stab_flat.append((keys[i], keys[j], float(stab.values[i, j])))
            stab_flat.sort(key=lambda x: x[2], reverse=True)
            if stab_flat:
                best  = stab_flat[0]
                worst = stab_flat[-1]
                lines.append(f"- Highest agreement: {best[0]} vs {best[1]} (ARI={best[2]:.3f})")
                lines.append(f"- Lowest agreement: {worst[0]} vs {worst[1]} (ARI={worst[2]:.3f})")
            lines.append("")

        syn      = res["syntactic_df"]
        ref_mcs  = res.get("ref_mcs", CANONICAL_MCS)
        ref_lbls = res["cluster_results"].get(("minilm", ref_mcs), np.array([]))
        n_cl_ref = len([c for c in np.unique(ref_lbls) if c != -1]) if len(ref_lbls) > 0 else 0
        lines.append(f"**Reference clusters (minilm mcs={ref_mcs}): {n_cl_ref} clusters**")
        lines.append("")
        if not syn.empty:
            for _, row in syn[syn["cluster_id"] != -1].iterrows():
                type_dist = json.loads(row.get("type_distribution", "{}"))
                top_type  = row.get("top_type", "unknown")
                lines.append(
                    f"  Cluster {int(row['cluster_id'])} (n={int(row['n_contexts'])}): "
                    f"top_pos={row['top_pos']}, "
                    f"code_block={row['frac_code_block']:.0%}, "
                    f"imperative={row['frac_imperative']:.0%}, "
                    f"top_subreddit={row['top_subreddit']}, "
                    f"top_type={top_type}, "
                    f"type_dist={type_dist}"
                )
        lines.append("")
        timing_total = sum(v for k, v in res["timing"].items() if not k.startswith("_"))
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
        lines.append(f"- A code-block-dominant cluster (>20%) emerged in: {', '.join(code_block_seeds)}.")
        lines.append("  **This is a new finding — no prior pass produced a code-block cluster.**")
    else:
        lines.append("- No seeds showed a dominant code-block cluster (>20% threshold).")
        lines.append("  Replicates both prior wholesale passes.")
    lines.append("")

    lines.append("**Subreddit-dominant clusters:**")
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        seed     = res["seed"]
        syn      = res["syntactic_df"]
        non_noise= syn[syn["cluster_id"] != -1]
        sub_dom  = non_noise["top_subreddit"].value_counts()
        lines.append(f"  `{seed}`: {sub_dom.to_dict()}")
    lines.append("")

    lines.append("**Post vs comment distribution across clusters:**")
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        seed     = res["seed"]
        syn      = res["syntactic_df"]
        non_noise= syn[syn["cluster_id"] != -1]
        lines.append(f"  `{seed}`:")
        for _, row in non_noise.iterrows():
            type_dist = json.loads(row.get("type_distribution", "{}"))
            lines.append(f"    Cluster {int(row['cluster_id'])}: {type_dist}")
    lines.append("")

    # ── Comparison to both prior passes ───────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 3. Comparison to both prior Phase 2.5 passes")
    lines.append("")
    lines.append("The operational questions specified by the task brief are answered here.")
    lines.append("")

    # Q1: Did hit counts grow per seed even though total corpus shrank?
    lines.append("### Q1. Did hit counts grow per seed even though total corpus shrank from 7,021 to 773 rows?")
    lines.append("")
    lines.append("| Seed | Pass 1 (4,114 posts) | Pass 2 (7,021 posts) | Pass 1b (773 rows) | vs Pass 2 |")
    lines.append("|---|---|---|---|---|")
    for res in all_results:
        seed   = res["seed"]
        prior1 = PRIOR_PASS1_COUNTS[seed]
        prior2 = PRIOR_PASS2_COUNTS[seed]
        delta  = res["n_contexts"] - prior2["n_contexts"]
        direction = "higher" if delta > 0 else ("same" if delta == 0 else "lower")
        lines.append(f"| {seed} | {prior1['n_contexts']} | {prior2['n_contexts']} "
                     f"| {res['n_contexts']} | {delta:+d} ({direction}) |")
    lines.append("")

    # Q2: Did mcs=5 produce clusters where prior passes struggled?
    lines.append("### Q2. Did mcs=5 now produce clusters where prior passes struggled at mcs=5?")
    lines.append("")
    lines.append("| Seed | Pass 1 mcs=5 clusters | Pass 2 mcs=5 clusters | Pass 1b mcs=5 clusters |")
    lines.append("|---|---|---|---|")

    # Prior pass mcs=5 cluster counts (from summaries)
    pass1_mcs5 = {"sleep": 2, "rest": 2, "break": 2, "tired": 2}
    pass2_mcs5 = {"sleep": 2, "rest": 4, "break": 3, "tired": 2}
    for res in all_results:
        seed = res["seed"]
        if res["below_floor"]:
            p1b = "n/a (below floor)"
        else:
            lbls = res["cluster_results"].get(("minilm", 5), np.array([]))
            p1b  = str(len(set(lbls) - {-1})) if len(lbls) > 0 else "0"
        lines.append(f"| {seed} | {pass1_mcs5[seed]} | {pass2_mcs5[seed]} | {p1b} |")
    lines.append("")

    # Q3: Did programming/code-context cluster finally separate?
    lines.append("### Q3. Did the programming/code-context cluster finally separate (it did not in either wholesale pass)?")
    lines.append("")
    if code_block_seeds:
        lines.append(f"Yes: seeds {', '.join(code_block_seeds)} produced a cluster with >20% code-block fraction.")
        lines.append("This is the first time this has occurred across all three Phase 2.5 runs.")
    else:
        lines.append("No: no seed produced a code-block-dominant cluster at the >20% threshold.")
        lines.append("This replicates both prior wholesale passes. Note: code-block presence alone may not")
        lines.append("be the discriminating feature of programming contexts in this corpus (subreddit may be more discriminating).")
    lines.append("")

    # Q4: Did `break` clusters stabilize across models?
    lines.append("### Q4. Did `break` clusters stabilize across embedding models?")
    lines.append("(In pass 1, mpnet purity was 0.00; in pass 2, mean ARI was 0.214.)")
    lines.append("")
    break_res = next((r for r in all_results if r["seed"] == "break"), None)
    if break_res and not break_res["below_floor"] and not break_res["stability_df"].empty:
        stab     = break_res["stability_df"]
        vals     = stab.values.copy()
        np.fill_diagonal(vals, np.nan)
        mean_ari = float(np.nanmean(vals))
        # Cross-model pairs
        cross_model_pairs = []
        for col1 in stab.columns:
            for col2 in stab.columns:
                if col1 < col2 and ("minilm" in col1) != ("minilm" in col2):
                    cross_model_pairs.append(float(stab.loc[col1, col2]))
        cross_mean = float(np.mean(cross_model_pairs)) if cross_model_pairs else float("nan")
        lines.append(f"- Pass 1b mean ARI (all pairs): {mean_ari:.3f}")
        lines.append(f"- Pass 1b mean cross-model ARI: {cross_mean:.3f}")
        lines.append(f"- Pass 2 mean ARI: 0.214; pass 2 cross-model ARI: 0.249")
        if cross_mean >= 0.40:
            lines.append("- **Assessment: `break` clusters substantially more stable than either prior pass.**")
        elif cross_mean >= 0.25:
            lines.append("- **Assessment: marginal improvement over pass 2. Clusters still fragile.**")
        elif cross_mean >= 0.10:
            lines.append("- **Assessment: minimal improvement. Targeted retrieval did not substantially help `break`.**")
        else:
            lines.append("- **Assessment: no improvement. `break` remains the least stable seed.**")
    else:
        lines.append("- `break` below floor or no stability data.")
    lines.append("")

    # Q5: Did model-self-attribution sense of `tired` materialize as its own cluster?
    lines.append("### Q5. Did the model-self-attribution sense of `tired` materialize as its own cluster?")
    lines.append("(Flagged in wholesale canonical Phase 2 KWIC but did not form a stable cluster in pass 2.)")
    lines.append("")
    tired_res = next((r for r in all_results if r["seed"] == "tired"), None)
    if tired_res and not tired_res["below_floor"] and not tired_res["syntactic_df"].empty:
        syn       = tired_res["syntactic_df"]
        non_noise = syn[syn["cluster_id"] != -1]
        lines.append(f"- `tired` produced {len(non_noise)} cluster(s) under canonical config (minilm mcs={tired_res.get('ref_mcs', CANONICAL_MCS)}).")
        # High-imperative cluster as possible self-attribution proxy
        imp_high = non_noise[non_noise["frac_imperative"] > 0.3]
        if not imp_high.empty:
            lines.append(f"- A cluster with high imperative fraction (>30%) was found: clusters {list(imp_high['cluster_id'].astype(int))}.")
            lines.append("  This is consistent with (but does not confirm) a self-attribution register.")
        else:
            lines.append("- No cluster showed distinctly high imperative fraction (>30%).")
        # Check for Anthropic-dominant cluster
        anth_clusters = non_noise[non_noise["top_subreddit"] == "Anthropic"]
        if not anth_clusters.empty:
            lines.append(f"- An Anthropic-dominant cluster was found (consistent with discourse about Anthropic's model behavior):")
            for _, row in anth_clusters.iterrows():
                lines.append(f"  Cluster {int(row['cluster_id'])}: n={int(row['n_contexts'])}, "
                             f"subreddits={json.loads(row['subreddit_distribution'])}")
        # Comment-dominant cluster as possible proxy (model utterances more likely to be quoted in comments)
        for _, row in non_noise.iterrows():
            type_dist = json.loads(row.get("type_distribution", "{}"))
            comment_frac = type_dist.get("comment", 0) / max(sum(type_dist.values()), 1)
            if comment_frac > 0.7:
                lines.append(f"- Cluster {int(row['cluster_id'])} is comment-dominant ({comment_frac:.0%} comments), "
                             f"which may indicate user-reported model utterances.")
    else:
        lines.append("- `tired` below floor or no cluster data.")
    lines.append("")

    # ── Operational question ───────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## 4. Has targeted retrieval enabled clean sense separation that wholesale at any scale could not?")
    lines.append("")
    lines.append("This is the central operational question.")
    lines.append("")

    n_seeds_with_mcs5 = 0
    n_seeds_stable    = 0
    n_seeds_total     = 0
    for res in all_results:
        if res["below_floor"]:
            continue
        n_seeds_total += 1
        lbls = res["cluster_results"].get(("minilm", 5), np.array([]))
        if len(set(lbls) - {-1}) >= 2:
            n_seeds_with_mcs5 += 1
        stab = res["stability_df"]
        if not stab.empty:
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            if float(np.nanmean(vals)) >= 0.40:
                n_seeds_stable += 1

    lines.append(f"- Seeds above clustering floor: {n_seeds_total}/4")
    lines.append(f"- Seeds with 2+ clusters at canonical config (minilm mcs=5): {n_seeds_with_mcs5}/{n_seeds_total}")
    lines.append(f"- Seeds with mean ARI >= 0.40 (cross-config stability): {n_seeds_stable}/{n_seeds_total}")
    lines.append(f"- Code-block cluster materialized: {'yes (' + ', '.join(code_block_seeds) + ')' if code_block_seeds else 'no'}")
    lines.append("")

    # Summarize whether each seed improved
    lines.append("**Per-seed assessment vs prior wholesale runs:**")
    lines.append("")
    lines.append("| Seed | Pass 1 clusters | Pass 2 clusters | Pass 1b clusters | Stability change | Assessment |")
    lines.append("|---|---|---|---|---|---|")
    pass1_mean_ari = {"sleep": 0.415, "rest": 0.405, "break": 0.214, "tired": 0.400}
    pass2_mean_ari = {"sleep": 0.238, "rest": 0.306, "break": 0.214, "tired": 0.402}
    for res in all_results:
        seed = res["seed"]
        if res["below_floor"]:
            lines.append(f"| {seed} | {pass1_mcs5[seed]} | {pass2_mcs5[seed]} | below floor | — | insufficient |")
            continue
        lbls = res["cluster_results"].get(("minilm", 5), np.array([]))
        p1b_cl = len(set(lbls) - {-1}) if len(lbls) > 0 else 0
        stab = res["stability_df"]
        if not stab.empty:
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            p1b_ari = float(np.nanmean(vals))
        else:
            p1b_ari = float("nan")
        p2_ari = pass2_mean_ari[seed]
        if p1b_ari > p2_ari + 0.10:
            ari_change = f"improved ({p1b_ari:.3f} vs {p2_ari:.3f})"
        elif p1b_ari > p2_ari - 0.05:
            ari_change = f"stable ({p1b_ari:.3f} vs {p2_ari:.3f})"
        else:
            ari_change = f"degraded ({p1b_ari:.3f} vs {p2_ari:.3f})"
        # Overall assessment
        if p1b_cl >= 3 and p1b_ari >= 0.35:
            assessment = "cleaner separation"
        elif p1b_cl >= 2 and p1b_ari >= 0.30:
            assessment = "comparable to pass 2"
        else:
            assessment = "no clear improvement"
        lines.append(f"| {seed} | {pass1_mcs5[seed]} | {pass2_mcs5[seed]} | {p1b_cl} | {ari_change} | {assessment} |")
    lines.append("")
    lines.append("**Researcher decision required at Pattern A checkpoint.**")
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
    lines.append("## 6. Anomalies and methodological notes")
    lines.append("")
    lines.append("- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),")
    lines.append("  consistent with methods_library.md §1.8.")
    lines.append("- mcs settings lowered to 3,5,10 (from 5,10,20) per task brief for smaller corpus.")
    lines.append("- HDBSCAN metric=euclidean on sentence-transformer embeddings.")
    lines.append("- POS tagging uses spaCy en_core_web_sm. Reliability may be reduced in code-heavy contexts.")
    lines.append("- Pass 1b includes both posts and comments; prior passes were posts-only.")
    lines.append("  Comments inflate KWIC context counts; cross-pass count comparisons must account for this.")
    lines.append("- retrieval_provenance field reflects Arctic Shift round-2 and PRAW round-2 retrieval paths.")
    lines.append("- No sense labels assigned. Labeling is a researcher decision at the Pattern A checkpoint.")
    lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote summary: {summary_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    total_start = time.time()

    print(f"Loading Pass 1b canonical corpus from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    df["body"] = df["body"].fillna("").astype(str)
    print(f"  Rows loaded: {len(df)}")
    if "type" in df.columns:
        print(f"  Posts: {(df['type']=='post').sum()}, Comments: {(df['type']=='comment').sum()}")

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
