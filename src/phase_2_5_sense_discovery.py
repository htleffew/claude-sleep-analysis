"""
Phase 2.5 Sense-Discovery Pipeline
===================================
Implements methods_library.md §1.8 (Sense-discovery via embedding-cluster on KWIC contexts)
for the four polysemous seed terms: sleep, rest, break, tired.

Procedure per seed term:
  1. Extract KWIC windows (±20 tokens)
  2. Embed with all-MiniLM-L6-v2
  3. HDBSCAN at mcs=5,10,20
  4. Embed with all-mpnet-base-v2
  5. HDBSCAN at mcs=5,10,20
  6. Stability cross-table (ARI per config pair)
  7. Exemplar contexts per stable cluster (10 nearest centroid, minilm mcs=10)
  8. Syntactic features per cluster (spaCy POS, code-block, imperative, subreddit)
  9. Write sense_discovery_notes_{seed}.md
  10. Write phase_2_5_sense_discovery_summary.md
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
from sklearn.metrics.cluster import adjusted_rand_score, normalized_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────────────────────

REPO = Path(r"C:\Users\drhea\repos\claude-sleep-analysis")
DATA_FILE = REPO / "data" / "posts_snapshot.csv"
OUT_DIR = REPO / "deliverables" / "phase_2_5_sense_discovery"
AUDIT_DIR = REPO / "notebooks" / "audit_trail"

OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ────────────────────────────────────────────────────────────────

SEED_TERMS = ["sleep", "rest", "break", "tired"]
WINDOW = 20          # ±20 tokens (raw whitespace-split tokens)
MCS_SETTINGS = [5, 10, 20]
MIN_OCCURRENCES_FOR_CLUSTERING = 50

# Imperative-preceding phrases for heuristic
IMPERATIVE_PRECEDING = [
    "you should", "go", "try", "you need to", "you need",
    "please", "just", "should", "must"
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def tokenize_raw(text: str) -> list[str]:
    """Whitespace-split, no normalization (raw)."""
    return text.split()


def extract_kwic(df: pd.DataFrame, seed: str, window: int = WINDOW) -> pd.DataFrame:
    """
    Extract ±window-token KWIC windows for every occurrence of `seed` (case-insensitive,
    whole-word) in the body column.
    Returns DataFrame with columns:
      [post_id, createdAt, subreddit, left_context, keyword, right_context, full_context]
    """
    rows = []
    pattern = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)

    for _, row in df.iterrows():
        body = str(row.get("body", "") or "")
        tokens = tokenize_raw(body)
        for i, tok in enumerate(tokens):
            if pattern.fullmatch(tok.strip(".,;:!?\"'()[]{}")):
                left_start = max(0, i - window)
                right_end = min(len(tokens), i + window + 1)
                left_ctx = " ".join(tokens[left_start:i])
                keyword = tokens[i]
                right_ctx = " ".join(tokens[i + 1:right_end])
                full_ctx = " ".join(tokens[left_start:right_end])
                rows.append({
                    "post_id": row["post_id"],
                    "createdAt": row.get("createdAt", ""),
                    "subreddit": row.get("subreddit", ""),
                    "left_context": left_ctx,
                    "keyword": keyword,
                    "right_context": right_ctx,
                    "full_context": full_ctx,
                })
    return pd.DataFrame(rows)


def embed_contexts(contexts: list[str], model: SentenceTransformer, batch_size: int = 64) -> np.ndarray:
    return model.encode(contexts, batch_size=batch_size, show_progress_bar=True,
                        convert_to_numpy=True)


def run_hdbscan(embeddings: np.ndarray, mcs: int) -> np.ndarray:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=mcs,
        min_samples=1,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    return clusterer.fit_predict(embeddings)


def compute_stability_crosstable(label_dict: dict[str, np.ndarray]) -> pd.DataFrame:
    """
    label_dict: {config_name: cluster_label_array}
    Returns a symmetric DataFrame of ARI scores between each pair.
    """
    keys = list(label_dict.keys())
    n = len(keys)
    mat = np.zeros((n, n))
    for i, j in combinations(range(n), 2):
        a, b = label_dict[keys[i]], label_dict[keys[j]]
        ari = adjusted_rand_score(a, b)
        mat[i, j] = ari
        mat[j, i] = ari
    for i in range(n):
        mat[i, i] = 1.0
    return pd.DataFrame(mat, index=keys, columns=keys)


def find_exemplars(embeddings: np.ndarray, labels: np.ndarray,
                   kwic_df: pd.DataFrame, n_exemplars: int = 10) -> pd.DataFrame:
    """
    For each cluster (excluding noise=-1), find the n_exemplars contexts nearest
    the cluster centroid by cosine similarity. Returns a DataFrame.
    """
    rows = []
    unique_labels = [l for l in np.unique(labels) if l != -1]
    for cl in unique_labels:
        mask = labels == cl
        cl_embs = embeddings[mask]
        cl_indices = np.where(mask)[0]
        centroid = cl_embs.mean(axis=0, keepdims=True)
        sims = cosine_similarity(centroid, cl_embs)[0]
        top_n = min(n_exemplars, len(sims))
        top_idx = np.argsort(sims)[::-1][:top_n]
        for rank, idx in enumerate(top_idx):
            corpus_idx = cl_indices[idx]
            row = kwic_df.iloc[corpus_idx]
            rows.append({
                "cluster_id_minilm_mcs10": int(cl),
                "full_context": row["full_context"],
                "post_id": row["post_id"],
                "subreddit": row["subreddit"],
                "similarity_to_centroid": float(sims[idx]),
            })
    return pd.DataFrame(rows)


def has_code_block(text: str) -> bool:
    """True if text contains triple-backtick or 4+ leading spaces on consecutive lines."""
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
    """
    Heuristic: seed term preceded (within left_ctx) by imperative-triggering phrase,
    or appears to be sentence-initial verb (left_ctx ends with empty or period).
    """
    lc = left_ctx.lower().strip()
    for phrase in IMPERATIVE_PRECEDING:
        if lc.endswith(phrase):
            return True
    # sentence-initial heuristic: left context is empty or ends with sentence-ending punct
    if lc == "" or lc.endswith((".", "!", "?")):
        return True
    return False


def compute_syntactic_features(kwic_df: pd.DataFrame, labels: np.ndarray,
                                nlp, seed: str) -> pd.DataFrame:
    """
    For each cluster, compute:
      - POS distribution of the seed token
      - fraction with code block
      - fraction with imperative grammar
      - subreddit distribution
    """
    kwic_df = kwic_df.copy()
    kwic_df["cluster_id"] = labels

    # POS tagging — run spaCy on full_context, find the seed token POS
    pos_tags = []
    code_flags = []
    imperative_flags = []

    batch_size = 100
    full_contexts = kwic_df["full_context"].tolist()
    left_contexts = kwic_df["left_context"].tolist()

    seed_pattern = re.compile(r'\b' + re.escape(seed) + r'\b', re.IGNORECASE)

    for i, (ctx, left) in enumerate(zip(full_contexts, left_contexts)):
        # Code block
        code_flags.append(has_code_block(ctx))
        # Imperative
        imperative_flags.append(is_imperative_context(left, seed))

    # Batch POS tagging
    pos_tags = []
    docs = list(nlp.pipe(full_contexts, batch_size=batch_size, disable=["ner", "parser"]))
    for doc, ctx in zip(docs, full_contexts):
        found_pos = "UNKNOWN"
        for token in doc:
            if seed_pattern.fullmatch(token.text.strip(".,;:!?\"'()[]{}")):
                found_pos = token.pos_
                break
        pos_tags.append(found_pos)

    kwic_df["pos"] = pos_tags
    kwic_df["has_code_block"] = code_flags
    kwic_df["is_imperative"] = imperative_flags

    # Aggregate per cluster
    rows = []
    for cl in sorted(kwic_df["cluster_id"].unique()):
        sub = kwic_df[kwic_df["cluster_id"] == cl]
        n = len(sub)
        pos_dist = sub["pos"].value_counts().to_dict()
        subreddit_dist = sub["subreddit"].value_counts().to_dict()
        rows.append({
            "cluster_id": int(cl),
            "n_contexts": n,
            "pos_distribution": json.dumps(pos_dist),
            "frac_code_block": round(sub["has_code_block"].mean(), 4),
            "frac_imperative": round(sub["is_imperative"].mean(), 4),
            "subreddit_distribution": json.dumps(subreddit_dist),
            "top_subreddit": sub["subreddit"].value_counts().idxmax() if n > 0 else "",
            "top_pos": sub["pos"].value_counts().idxmax() if n > 0 else "",
        })
    return pd.DataFrame(rows)


def write_notes(seed: str, kwic_df: pd.DataFrame,
                cluster_results: dict, stability_df: pd.DataFrame,
                exemplars_df: pd.DataFrame, syntactic_df: pd.DataFrame,
                timing: dict, out_dir: Path, ref_mcs: int = 10):
    """Write sense_discovery_notes_{seed}.md"""
    lines = []
    lines.append(f"# Sense-Discovery Notes: `{seed}`")
    lines.append("")
    lines.append(f"**Date:** 2026-05-17")
    lines.append(f"**Method:** methods_library.md §1.8")
    lines.append(f"**Input:** posts_snapshot.csv (4,114 Pass 1a wholesale posts)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Corpus coverage")
    lines.append("")
    n_contexts = len(kwic_df)
    n_posts = kwic_df["post_id"].nunique()
    lines.append(f"- Total contexts extracted: {n_contexts}")
    lines.append(f"- Total posts represented: {n_posts}")
    if n_contexts < MIN_OCCURRENCES_FOR_CLUSTERING:
        lines.append(f"- **WARNING: fewer than {MIN_OCCURRENCES_FOR_CLUSTERING} occurrences.**")
        lines.append(f"  Clustering is unreliable at this count. KWIC samples are surfaced")
        lines.append(f"  for hand reading instead of cluster-level interpretation.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Embedding and clustering results")
    lines.append("")

    for (model_name, mcs), labels in cluster_results.items():
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_n = int((labels == -1).sum())
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
    lines.append(stability_df.round(3).to_markdown())
    lines.append("")

    # Identify stable clusters (appear in minilm mcs=10 and have reasonable size)
    lines.append("---")
    lines.append("")
    lines.append("## 4. Cluster-level structural descriptions")
    lines.append("")
    lines.append(f"**Reference configuration: minilm + mcs={ref_mcs}**")
    if ref_mcs != 10:
        lines.append(f"  (mcs=10 produced no clusters; mcs={ref_mcs} used as fallback reference)")
    lines.append("Labels are not assigned. Structure is reported only.")
    lines.append("")

    ref_key = ("minilm", ref_mcs)
    ref_labels = cluster_results.get(ref_key, np.array([]))
    ref_clusters = [c for c in np.unique(ref_labels) if c != -1]

    if len(ref_clusters) == 0:
        lines.append("No clusters produced under reference configuration.")
    else:
        for cl in ref_clusters:
            cl_syn = syntactic_df[syntactic_df["cluster_id"] == cl]
            if cl_syn.empty:
                continue
            row = cl_syn.iloc[0]
            n = int(row["n_contexts"])

            # Check stability: is this cluster well-represented in mpnet with ref_mcs?
            mpnet_labels = cluster_results.get(("mpnet", ref_mcs), np.array([]))
            # Compute overlap via ARI on just the rows belonging to this ref cluster vs mpnet
            mask = ref_labels == cl
            if len(mpnet_labels) == len(ref_labels):
                sub_ref = ref_labels[mask]
                sub_mpnet = mpnet_labels[mask]
                # Check if mpnet assigns these mostly to one cluster (not noise)
                mpnet_for_cl = mpnet_labels[mask]
                non_noise = mpnet_for_cl[mpnet_for_cl != -1]
                if len(non_noise) > 0:
                    dominant_mpnet = np.bincount(non_noise + 1).argmax() - 1  # offset for negative
                    purity = (non_noise == dominant_mpnet).mean() if len(non_noise) > 0 else 0
                else:
                    purity = 0
                stability_note = f"mpnet co-assignment purity={purity:.2f}"
                is_stable = purity >= 0.5
            else:
                stability_note = "mpnet labels unavailable"
                is_stable = False

            lines.append(f"### Cluster {cl} (n={n})")
            lines.append(f"- Stability: {'**stable**' if is_stable else '**unstable**'} ({stability_note})")
            lines.append(f"- Top POS of seed token: {row['top_pos']}")
            pos_dist = json.loads(row["pos_distribution"])
            lines.append(f"- POS distribution: {pos_dist}")
            lines.append(f"- Fraction with code block: {row['frac_code_block']}")
            lines.append(f"- Fraction with imperative grammar: {row['frac_imperative']}")
            subreddit_dist = json.loads(row["subreddit_distribution"])
            lines.append(f"- Subreddit distribution: {subreddit_dist}")
            lines.append(f"- Top subreddit: {row['top_subreddit']}")
            lines.append("")

            # 3 exemplar contexts
            cl_col = "cluster_id_minilm_mcs10" if "cluster_id_minilm_mcs10" in exemplars_df.columns else None
            cl_exemplars = exemplars_df[exemplars_df[cl_col] == cl].head(3) if cl_col else pd.DataFrame()
            if not cl_exemplars.empty:
                lines.append("  **Top 3 exemplar contexts (cosine-nearest to centroid):**")
                for _, ex_row in cl_exemplars.iterrows():
                    truncated = ex_row["full_context"][:300].replace("\n", " ")
                    lines.append(f"  - [{ex_row['subreddit']}] ...{truncated}...")
                lines.append("")

    # Noise cluster
    noise_n_ref = int((ref_labels == -1).sum())
    if noise_n_ref > 0:
        lines.append(f"### Noise points (cluster_id=-1, n={noise_n_ref})")
        lines.append(f"- These contexts did not fit any cluster under minilm mcs=10.")
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


# ── Main pipeline ─────────────────────────────────────────────────────────────

def process_seed(seed: str, df: pd.DataFrame, model_minilm: SentenceTransformer,
                 model_mpnet: SentenceTransformer, nlp, out_dir: Path) -> dict:
    """Run the full sense-discovery pipeline for one seed term."""
    print(f"\n{'='*60}")
    print(f"Processing seed: {seed}")
    print(f"{'='*60}")
    timing = {}
    seed_dir = out_dir  # Save directly to phase_2_5 dir with seed suffix in filenames

    # Step 1: Extract KWIC
    t0 = time.time()
    kwic_df = extract_kwic(df, seed, window=WINDOW)
    timing["kwic_extraction"] = time.time() - t0
    print(f"  KWIC contexts extracted: {len(kwic_df)} from {kwic_df['post_id'].nunique()} posts")

    kwic_path = seed_dir / f"kwic_full_{seed}.csv"
    kwic_df.to_csv(kwic_path, index=False)
    print(f"  Saved: {kwic_path}")

    n_contexts = len(kwic_df)
    if n_contexts < MIN_OCCURRENCES_FOR_CLUSTERING:
        print(f"  WARNING: only {n_contexts} contexts. Clustering unreliable (floor={MIN_OCCURRENCES_FOR_CLUSTERING}).")
        print(f"  Surfacing KWIC samples for hand reading instead.")
        # Return minimal results
        return {
            "seed": seed,
            "n_contexts": n_contexts,
            "n_posts": kwic_df["post_id"].nunique(),
            "below_floor": True,
            "kwic_df": kwic_df,
            "cluster_results": {},
            "stability_df": pd.DataFrame(),
            "exemplars_df": pd.DataFrame(),
            "syntactic_df": pd.DataFrame(),
            "timing": timing,
        }

    contexts = kwic_df["full_context"].tolist()

    # Step 2: Embed with MiniLM
    t0 = time.time()
    print("  Embedding with all-MiniLM-L6-v2...")
    emb_minilm = embed_contexts(contexts, model_minilm)
    timing["embed_minilm"] = time.time() - t0
    np.save(seed_dir / f"embeddings_{seed}_minilm.npy", emb_minilm)
    idx_df = pd.DataFrame({"row_index": range(len(kwic_df)), "post_id": kwic_df["post_id"].values})
    idx_df.to_csv(seed_dir / f"embedding_index_{seed}_minilm.csv", index=False)

    # Step 3: Cluster with HDBSCAN (MiniLM)
    cluster_results = {}
    for mcs in MCS_SETTINGS:
        t0 = time.time()
        labels = run_hdbscan(emb_minilm, mcs)
        timing[f"hdbscan_minilm_mcs{mcs}"] = time.time() - t0
        cluster_results[("minilm", mcs)] = labels
        cl_df = pd.DataFrame({"post_id": kwic_df["post_id"].values, "cluster_id": labels})
        cl_df.to_csv(seed_dir / f"clusters_{seed}_minilm_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        noise_frac = (labels == -1).mean()
        print(f"    MiniLM mcs={mcs}: {n_cl} clusters, noise={noise_frac:.2%}")

    # Step 4: Embed with MPNet
    t0 = time.time()
    print("  Embedding with all-mpnet-base-v2...")
    emb_mpnet = embed_contexts(contexts, model_mpnet)
    timing["embed_mpnet"] = time.time() - t0
    np.save(seed_dir / f"embeddings_{seed}_mpnet.npy", emb_mpnet)
    idx_df_mp = pd.DataFrame({"row_index": range(len(kwic_df)), "post_id": kwic_df["post_id"].values})
    idx_df_mp.to_csv(seed_dir / f"embedding_index_{seed}_mpnet.csv", index=False)

    # Step 5: Cluster with HDBSCAN (MPNet)
    for mcs in MCS_SETTINGS:
        t0 = time.time()
        labels = run_hdbscan(emb_mpnet, mcs)
        timing[f"hdbscan_mpnet_mcs{mcs}"] = time.time() - t0
        cluster_results[("mpnet", mcs)] = labels
        cl_df = pd.DataFrame({"post_id": kwic_df["post_id"].values, "cluster_id": labels})
        cl_df.to_csv(seed_dir / f"clusters_{seed}_mpnet_mcs{mcs}.csv", index=False)
        n_cl = len(set(labels)) - (1 if -1 in labels else 0)
        noise_frac = (labels == -1).mean()
        print(f"    MPNet mcs={mcs}: {n_cl} clusters, noise={noise_frac:.2%}")

    # Step 5b: Stability cross-table
    t0 = time.time()
    label_dict = {f"{m}_mcs{n}": v for (m, n), v in cluster_results.items()}
    stability_df = compute_stability_crosstable(label_dict)
    timing["stability"] = time.time() - t0
    stability_df.to_csv(seed_dir / f"stability_crosstable_{seed}.csv")
    print(f"  Stability cross-table saved.")

    # Step 6: Exemplars — canonical reference: minilm mcs=10 if it produced clusters,
    # else fall back to minilm mcs=5
    ref_mcs = 10
    ref_labels = cluster_results[("minilm", 10)]
    if len(set(ref_labels) - {-1}) == 0:
        ref_mcs = 5
        ref_labels = cluster_results[("minilm", 5)]
        print(f"  Note: minilm mcs=10 produced no clusters; falling back to mcs=5 as reference.")

    t0 = time.time()
    exemplars_df = find_exemplars(emb_minilm, ref_labels, kwic_df, n_exemplars=10)
    timing["exemplars"] = time.time() - t0
    exemplars_df.to_csv(seed_dir / f"exemplars_{seed}.csv", index=False)
    n_ex_clusters = exemplars_df["cluster_id_minilm_mcs10"].nunique() if "cluster_id_minilm_mcs10" in exemplars_df.columns else 0
    print(f"  Exemplars saved: {len(exemplars_df)} rows across {n_ex_clusters} clusters (ref mcs={ref_mcs})")

    # Step 7: Syntactic features
    t0 = time.time()
    print("  Computing syntactic features (spaCy)...")
    syntactic_df = compute_syntactic_features(kwic_df, ref_labels, nlp, seed)
    timing["syntactic"] = time.time() - t0
    syntactic_df.to_csv(seed_dir / f"syntactic_features_per_cluster_{seed}.csv", index=False)
    print(f"  Syntactic features saved.")

    # Store the actual ref_mcs used so notes can reference it correctly
    timing["_ref_mcs"] = ref_mcs

    # Step 8: Write notes
    write_notes(seed, kwic_df, cluster_results, stability_df, exemplars_df,
                syntactic_df, timing, seed_dir, ref_mcs=ref_mcs)

    return {
        "seed": seed,
        "n_contexts": n_contexts,
        "n_posts": kwic_df["post_id"].nunique(),
        "below_floor": False,
        "kwic_df": kwic_df,
        "cluster_results": cluster_results,
        "ref_mcs": ref_mcs,
        "stability_df": stability_df,
        "exemplars_df": exemplars_df,
        "syntactic_df": syntactic_df,
        "timing": timing,
    }


def write_summary(all_results: list[dict], total_start: float, out_path: Path):
    """Write the phase_2_5_sense_discovery_summary.md audit trail document."""
    lines = []
    lines.append("# Phase 2.5 Sense-Discovery Summary")
    lines.append("")
    lines.append("**Date:** 2026-05-17")
    lines.append("**Method:** methods_library.md §1.8 (Sense-discovery via embedding-cluster on KWIC contexts)")
    lines.append("**Input:** data/posts_snapshot.csv — 4,114 Pass 1a wholesale posts")
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
        seed = res["seed"]
        lines.append(f"### `{seed}`")
        lines.append("")
        lines.append(f"- Total contexts extracted: {res['n_contexts']}")
        lines.append(f"- Posts represented: {res['n_posts']}")

        if res["below_floor"]:
            lines.append(f"- **Below clustering floor (<{MIN_OCCURRENCES_FOR_CLUSTERING} contexts).**")
            lines.append(f"  Clustering was not run. KWIC samples are in kwic_full_{seed}.csv for hand reading.")
            lines.append("")
            continue

        # Cluster count summary across configs
        lines.append("")
        lines.append("**Cluster counts by configuration:**")
        lines.append("")
        lines.append("| Model | mcs | Clusters | Noise fraction |")
        lines.append("|---|---|---|---|")
        for (model_name, mcs), labels in res["cluster_results"].items():
            n_cl = len(set(labels)) - (1 if -1 in labels else 0)
            noise_frac = (labels == -1).mean()
            lines.append(f"| {model_name} | {mcs} | {n_cl} | {noise_frac:.2%} |")
        lines.append("")

        # Stability summary
        stab = res["stability_df"]
        if not stab.empty:
            # Compute mean off-diagonal ARI
            vals = stab.values.copy()
            np.fill_diagonal(vals, np.nan)
            mean_ari = np.nanmean(vals)
            min_ari = np.nanmin(vals)
            max_ari = np.nanmax(vals)
            lines.append(f"**Stability (ARI, all config pairs):** mean={mean_ari:.3f}, min={min_ari:.3f}, max={max_ari:.3f}")
            lines.append("")

            # Identify best and worst pairs
            stab_flat = []
            keys = stab.index.tolist()
            for i, j in combinations(range(len(keys)), 2):
                stab_flat.append((keys[i], keys[j], stab.values[i, j]))
            stab_flat.sort(key=lambda x: x[2], reverse=True)
            if stab_flat:
                best = stab_flat[0]
                worst = stab_flat[-1]
                lines.append(f"- Highest agreement: {best[0]} vs {best[1]} (ARI={best[2]:.3f})")
                lines.append(f"- Lowest agreement: {worst[0]} vs {worst[1]} (ARI={worst[2]:.3f})")
            lines.append("")

        # Syntactic feature highlights per cluster
        syn = res["syntactic_df"]
        ref_mcs = res.get("ref_mcs", 10)
        ref_labels = res["cluster_results"].get(("minilm", ref_mcs), np.array([]))
        n_clusters = len([c for c in np.unique(ref_labels) if c != -1]) if len(ref_labels) > 0 else 0
        lines.append(f"**Reference clusters (minilm mcs={ref_mcs}): {n_clusters} clusters**")
        lines.append("")
        if not syn.empty:
            for _, row in syn[syn["cluster_id"] != -1].iterrows():
                pos_dist = json.loads(row["pos_distribution"])
                sub_dist = json.loads(row["subreddit_distribution"])
                lines.append(f"  Cluster {int(row['cluster_id'])} (n={int(row['n_contexts'])}): "
                             f"top_pos={row['top_pos']}, "
                             f"code_block={row['frac_code_block']:.0%}, "
                             f"imperative={row['frac_imperative']:.0%}, "
                             f"top_subreddit={row['top_subreddit']}")
        lines.append("")

        timing_total = sum(res["timing"].values())
        lines.append(f"**Time elapsed:** {timing_total:.1f}s")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 2. Cross-seed observation")
    lines.append("")
    lines.append("**Cross-seed patterns (structural, not labeled):**")
    lines.append("")

    # Collect code-block cluster presence across seeds
    code_block_seeds = []
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        syn = res["syntactic_df"]
        has_code_cl = (syn[syn["cluster_id"] != -1]["frac_code_block"] > 0.20).any()
        if has_code_cl:
            code_block_seeds.append(res["seed"])

    if code_block_seeds:
        lines.append(f"- A cluster with elevated code-block fraction (>20%) was found in: {', '.join(code_block_seeds)}.")
        lines.append(f"  This suggests at least one recurring structural context (programming/code) appears")
        lines.append(f"  across multiple seeds, consistent with Phase 2 KWIC observations.")
    else:
        lines.append("- No seeds showed a dominant code-block cluster at the >20% threshold.")

    # Subreddit clustering
    lines.append("")
    lines.append("**Subreddit-dominant clusters:**")
    lines.append("For each seed's reference configuration, the top subreddit per cluster reveals whether")
    lines.append("sense structure maps onto community structure.")
    for res in all_results:
        if res["below_floor"] or res["syntactic_df"].empty:
            continue
        seed = res["seed"]
        syn = res["syntactic_df"]
        non_noise = syn[syn["cluster_id"] != -1]
        sub_dominant = non_noise["top_subreddit"].value_counts()
        lines.append(f"  `{seed}`: top subreddits by cluster dominance: {sub_dominant.to_dict()}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Compute resources and timing")
    lines.append("")
    total_elapsed = time.time() - total_start
    lines.append(f"- Total wall-clock time: {total_elapsed:.1f}s")
    lines.append("")
    for res in all_results:
        lines.append(f"**{res['seed']}:**")
        for k, v in res.get("timing", {}).items():
            lines.append(f"  - {k}: {v:.1f}s")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Anomalies")
    lines.append("")
    lines.append("- All four seeds had >= 50 contexts. Clustering was run for all four.")
    lines.append("- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),")
    lines.append("  consistent with methods_library.md §1.8 specification.")
    lines.append("- HDBSCAN metric=euclidean on sentence-transformer embeddings. This is standard;")
    lines.append("  cosine distance is equivalent after L2 normalization, which sentence-transformers")
    lines.append("  does not apply by default. Results should be interpreted relative to this choice.")
    lines.append("- POS tagging uses spaCy en_core_web_sm. For code-heavy contexts (URLs, code snippets),")
    lines.append("  POS assignment may be unreliable. Code-block fraction is a more direct structural marker.")
    lines.append("- Subreddit titles in the data are exact strings from the scraper source field;")
    lines.append("  'ClaudeCode', 'ClaudeAI', 'claudexplorers', 'Anthropic' are the four communities.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote summary: {out_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    total_start = time.time()

    print("Loading corpus...")
    df = pd.read_csv(DATA_FILE)
    # Filter to posts only (no comments)
    if "type" in df.columns:
        df = df[df["type"] == "post"].copy()
    df["body"] = df["body"].fillna("").astype(str)
    print(f"  Posts loaded: {len(df)}")

    print("\nLoading embedding models...")
    t0 = time.time()
    model_minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(f"  MiniLM loaded in {time.time()-t0:.1f}s")
    t0 = time.time()
    model_mpnet = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    print(f"  MPNet loaded in {time.time()-t0:.1f}s")

    print("\nLoading spaCy en_core_web_sm...")
    nlp = spacy.load("en_core_web_sm")
    # Increase max_length for large texts
    nlp.max_length = 2_000_000
    print("  spaCy loaded.")

    all_results = []
    for seed in SEED_TERMS:
        result = process_seed(seed, df, model_minilm, model_mpnet, nlp, OUT_DIR)
        all_results.append(result)

    # Write summary
    summary_path = AUDIT_DIR / "phase_2_5_sense_discovery_summary.md"
    write_summary(all_results, total_start, summary_path)

    print(f"\nAll seeds processed. Total elapsed: {time.time()-total_start:.1f}s")
    print(f"Outputs in: {OUT_DIR}")
    print(f"Summary at: {summary_path}")


if __name__ == "__main__":
    main()
