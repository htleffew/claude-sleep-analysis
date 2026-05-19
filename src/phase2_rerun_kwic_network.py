"""
Phase 2 Re-run: KWIC / Co-occurrence / Network Analysis
on the expanded canonical corpus (7,021 posts).

Method: community_reported_llm_behavior_method.md §C.2
Library: methods_library.md §1.3, §1.7
Input:   data/posts_snapshot_canonical.csv
Output:  deliverables/phase_2_rerun/sleep_kwic_network/
"""

import os
import re
import random
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 stdout so box-drawing chars survive on Windows cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np
import networkx as nx
import nltk

# --ensure nltk data --────────────────────────────────────────────────────────
for pkg in ["punkt", "punkt_tab"]:
    try:
        nltk.data.find(f"tokenizers/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

from nltk.tokenize import word_tokenize

# Inline English stop-words (avoids NLTK corpus path security issue in sandbox)
_ENGLISH_STOPS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","yourselves","he","him","his","himself","she","her","hers","herself",
    "it","its","itself","they","them","their","theirs","themselves","what","which",
    "who","whom","this","that","these","those","am","is","are","was","were","be",
    "been","being","have","has","had","having","do","does","did","doing","a","an",
    "the","and","but","if","or","because","as","until","while","of","at","by",
    "for","with","about","against","between","into","through","during","before",
    "after","above","below","to","from","up","down","in","out","on","off","over",
    "under","again","further","then","once","here","there","when","where","why",
    "how","all","both","each","few","more","most","other","some","such","no",
    "nor","not","only","own","same","so","than","too","very","can","will",
    "just","don","should","now","ain","aren","couldn","didn","doesn","hadn",
    "hasn","haven","isn","mightn","mustn","needn","shan","shouldn","wasn",
    "weren","won","wouldn",
}

# --paths --───────────────────────────────────────────────────────────────────
REPO = Path(r"C:\Users\drhea\repos\claude-sleep-analysis")
CORPUS_CSV = REPO / "data" / "posts_snapshot_canonical.csv"
OUT_DIR = REPO / "deliverables" / "phase_2_rerun" / "sleep_kwic_network"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# --seed terms (from phase_1_corpus_provenance.md) --─────────────────────────
SEED_TERMS = [
    "sleep", "rest", "bed", "break", "tired", "exhausted",
    "fatigued", "late", "tonight", "tomorrow", "midnight",
    "paternalistic", "patronizing", "lecturing", "moralizing", "scolding",
    "bedtime",
]

WINDOW_SIZES = [5, 10, 20]
MAX_SAMPLE = 20

# --domain stop-words (method §1.1 anti-pattern: extend standard list) --──────
DOMAIN_STOPS = {
    "claude", "gpt", "llm", "ai", "model", "anthropic", "openai",
    "prompt", "user", "using", "use", "used", "like", "just", "get",
    "got", "one", "nan", "would", "could", "also", "really", "want",
    "know", "think", "time", "even", "still", "make", "much", "see",
    "going", "going", "way", "thing", "things", "something", "anything",
    "someone", "anyone", "good", "well", "back", "bit", "lot", "day",
    "work", "working", "need", "new", "im", "ive", "dont", "doesnt",
    "cant", "isnt", "wasnt", "nt", "ve", "re", "ll", "s", "n",
    "de", "la", "en", "el", "https", "http", "www", "com", "reddit",
    "every", "actually", "right", "without", "first",
}
STOP_WORDS = _ENGLISH_STOPS | DOMAIN_STOPS


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Load corpus
# ═══════════════════════════════════════════════════════════════════════════════
print("Loading corpus ...")
df = pd.read_csv(CORPUS_CSV)
df["body"] = df["body"].fillna("").astype(str)
print(f"  Rows: {len(df):,}  Subreddits: {df['subreddit'].value_counts().to_dict()}")


def tokenize_raw(text: str) -> list[str]:
    """Lower-case word tokenize, keep purely alphabetic tokens (no apostrophes/contractions)."""
    return [t.lower() for t in word_tokenize(text) if re.match(r"^[a-z][a-z-]*$", t.lower())]


def tokenize_content(text: str) -> list[str]:
    """Lower-case, stop-word-removed, domain-stop-removed, min length 3."""
    return [t for t in tokenize_raw(text) if t not in STOP_WORDS and len(t) > 2]


# Pre-tokenize once for efficiency
print("Tokenizing corpus (raw) ...")
df["tokens_raw"] = df["body"].apply(tokenize_raw)
print("Tokenizing corpus (content) ...")
df["tokens_content"] = df["body"].apply(tokenize_content)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. KWIC for each seed term at windows 5, 10, 20
# ═══════════════════════════════════════════════════════════════════════════════
print("\n-- Task 1: KWIC reads --")

kwic_hit_counts = {}  # seed -> total_hit_count

for seed in SEED_TERMS:
    seed_lower = seed.lower()
    hit_counts_seed = {}

    for w in WINDOW_SIZES:
        rows = []
        for _, row in df.iterrows():
            tokens = row["tokens_raw"]
            indices = [i for i, t in enumerate(tokens) if t == seed_lower]
            for idx in indices:
                left = tokens[max(0, idx - w): idx]
                right = tokens[idx + 1: idx + 1 + w]
                rows.append({
                    "post_id": row["post_id"],
                    "createdAt": row["createdAt"],
                    "subreddit": row["subreddit"],
                    "left_context": " ".join(left),
                    "keyword": seed,
                    "right_context": " ".join(right),
                })

        total_hits = len(rows)
        hit_counts_seed[w] = total_hits

        # sample up to 20
        sample = random.sample(rows, min(MAX_SAMPLE, len(rows))) if rows else []
        out_df = pd.DataFrame(sample)
        fname = OUT_DIR / f"kwic_{seed}_w{w}.csv"
        out_df.to_csv(fname, index=False)

    kwic_hit_counts[seed] = hit_counts_seed
    total_w10 = hit_counts_seed[10]
    print(f"  {seed:18s}  w10 hits={total_w10:4d}  w5={hit_counts_seed[5]:4d}  w20={hit_counts_seed[20]:4d}")

# Save hit counts summary
hit_df = pd.DataFrame(
    [(s, w, c) for s, wc in kwic_hit_counts.items() for w, c in wc.items()],
    columns=["seed_term", "window", "total_hits"]
)
hit_df.to_csv(OUT_DIR / "kwic_hit_counts.csv", index=False)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Co-occurrence network on top-2,000 content-bearing unigrams
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--Task 2: Co-occurrence network --")

# Count all content-bearing unigrams
print("  Counting unigram frequencies ...")
unigram_counter = Counter()
for tokens in df["tokens_content"]:
    unigram_counter.update(tokens)

TOP_N = 2000
top_terms = [t for t, _ in unigram_counter.most_common(TOP_N)]
top_set = set(top_terms)
print(f"  Top-{TOP_N} content-bearing terms selected. Top 20: {top_terms[:20]}")

# Build co-occurrence matrix (post-level: terms that appear in the same post)
print("  Building co-occurrence matrix ...")
cooc = defaultdict(Counter)

for tokens in df["tokens_content"]:
    present = set(tokens) & top_set
    present_list = sorted(present)
    for i, t1 in enumerate(present_list):
        for t2 in present_list[i + 1:]:
            cooc[t1][t2] += 1
            cooc[t2][t1] += 1

# Filter edges with count >= 5
MIN_EDGE = 5
print(f"  Building NetworkX graph (min_edge={MIN_EDGE}) ...")
G = nx.Graph()
G.add_nodes_from(top_terms)

for t1, neighbors in cooc.items():
    if t1 not in top_set:
        continue
    for t2, weight in neighbors.items():
        if t2 not in top_set or weight < MIN_EDGE:
            continue
        if not G.has_edge(t1, t2):
            G.add_edge(t1, t2, weight=weight)

print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
density = nx.density(G)
print(f"  Density: {density:.6f}")

# Save GEXF
gexf_path = OUT_DIR / "cooccurrence_network.gexf"
nx.write_gexf(G, str(gexf_path))
print(f"  Saved: {gexf_path}")

# Top-200-node matrix
print("  Computing top-200-node matrix ...")
top200 = [t for t, _ in unigram_counter.most_common(200)]
matrix_data = {}
for t1 in top200:
    row = {}
    for t2 in top200:
        if t1 == t2:
            row[t2] = 0
        else:
            row[t2] = cooc[t1].get(t2, 0)
    matrix_data[t1] = row
matrix_df = pd.DataFrame(matrix_data, index=top200)
matrix_df.to_csv(OUT_DIR / "cooccurrence_matrix_top200.csv")
print(f"  Saved matrix {matrix_df.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Louvain community detection at 3 resolutions
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--Louvain community detection --")
from community import best_partition

# Use the largest connected component for Louvain
Gcc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
print(f"  LCC: {Gcc.number_of_nodes()} nodes, {Gcc.number_of_edges()} edges")

louvain_results = {}
for res in [0.5, 1.0, 2.0]:
    partition = best_partition(Gcc, resolution=res, random_state=42)
    n_communities = len(set(partition.values()))
    print(f"  Resolution {res}: {n_communities} communities")
    louvain_results[res] = partition

    rows = [{"term": t, "community": c} for t, c in partition.items()]
    res_str = str(res).replace(".", "_")
    out_path = OUT_DIR / f"communities_res{res_str}.csv"
    pd.DataFrame(rows).sort_values("community").to_csv(out_path, index=False)

# Summarize community sizes
for res, partition in louvain_results.items():
    comm_sizes = Counter(partition.values())
    sizes_sorted = sorted(comm_sizes.values(), reverse=True)
    print(f"  Resolution {res} community sizes: {sizes_sorted[:10]} ... total {len(sizes_sorted)}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Per-anchor subgraphs for seeds with >= 100 post-hits
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--Task 3: Per-anchor subgraphs --")

# Compute post-level hit counts (unique posts mentioning seed)
seed_post_hits = {}
for seed in SEED_TERMS:
    seed_lower = seed.lower()
    count = df["tokens_raw"].apply(lambda toks: seed_lower in toks).sum()
    seed_post_hits[seed] = count
    print(f"  {seed:18s}  posts with term={count}")

threshold_seeds = [s for s, c in seed_post_hits.items() if c >= 100]
print(f"\n  Seeds clearing 100-post threshold: {threshold_seeds}")

subgraph_stats = {}
for seed in threshold_seeds:
    if seed not in G:
        print(f"  {seed}: not in graph vocabulary — skipping subgraph")
        subgraph_stats[seed] = {"in_graph": False, "nodes": 0, "edges": 0}
        continue

    # Ego graph (seed + all neighbors)
    ego = nx.ego_graph(G, seed, radius=1)
    subgraph_stats[seed] = {
        "in_graph": True,
        "nodes": ego.number_of_nodes(),
        "edges": ego.number_of_edges(),
        "density": nx.density(ego),
    }
    gexf_out = OUT_DIR / f"subgraph_{seed}.gexf"
    nx.write_gexf(ego, str(gexf_out))
    print(f"  {seed}: ego subgraph {ego.number_of_nodes()} nodes, {ego.number_of_edges()} edges → {gexf_out.name}")

pd.DataFrame(subgraph_stats).T.to_csv(OUT_DIR / "subgraph_stats.csv")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Save network summary statistics
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--Saving network statistics --")
net_stats = {
    "corpus_posts": len(df),
    "top_n_terms": TOP_N,
    "min_edge_weight": MIN_EDGE,
    "graph_nodes": G.number_of_nodes(),
    "graph_edges": G.number_of_edges(),
    "graph_density": density,
    "lcc_nodes": Gcc.number_of_nodes(),
    "lcc_edges": Gcc.number_of_edges(),
    "louvain": {
        str(res): {
            "n_communities": len(set(p.values())),
            "top10_sizes": sorted(Counter(p.values()).values(), reverse=True)[:10],
        }
        for res, p in louvain_results.items()
    },
    "seed_post_hits": seed_post_hits,
    "threshold_seeds_100": threshold_seeds,
    "subgraph_stats": subgraph_stats,
    "unigram_freq_top50": {t: c for t, c in unigram_counter.most_common(50)},
}

class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)

with open(OUT_DIR / "network_stats.json", "w", encoding="utf-8") as f:
    json.dump(net_stats, f, indent=2, cls=_NumpyEncoder)

print(f"  Saved network_stats.json")
print("\nDone. All outputs in:", OUT_DIR)
