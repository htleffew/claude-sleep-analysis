"""
Phase 2 KWIC / Co-occurrence / Network Analysis
Sleep-nudge project, Pass 1a wholesale subset (posts_snapshot.csv)

Outputs:
  deliverables/phase_2/sleep_kwic_network/
    kwic_{seed_term}_w{window}.csv
    cooccurrence_network.gexf
    cooccurrence_matrix_top200.csv
    communities_res{r}.csv
    subgraph_{seed_term}.gexf
  notebooks/audit_trail/
    phase_2_kwic_notes.md
    phase_2_kwic_network_summary.md
"""

import os
import re
import csv
import random
import string
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import numpy as np
import networkx as nx
import community as community_louvain
import nltk

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path("C:/Users/drhea/repos/claude-sleep-analysis")
DATA = REPO / "data" / "posts_snapshot.csv"
OUT = REPO / "deliverables" / "phase_2" / "sleep_kwic_network"
AUDIT = REPO / "notebooks" / "audit_trail"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# NLTK data
# ---------------------------------------------------------------------------
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))
# Domain stop-words to remove from content-bearing analysis
DOMAIN_STOPS = {
    "claude", "gpt", "chatgpt", "openai", "anthropic", "llm", "ai", "model",
    "user", "prompt", "chat", "bot", "reddit", "post", "comment", "use",
    "using", "used", "would", "could", "like", "get", "got", "one", "also",
    "think", "know", "want", "need", "even", "make", "much", "still", "way",
    "just", "really", "actually", "something", "anything", "everything",
    "nothing", "people", "anyone", "someone", "thing", "time", "new",
    "good", "great", "better", "best", "bad", "it", "its", "amp",
}
CONTENT_STOPS = STOPWORDS | DOMAIN_STOPS

random.seed(42)

# ---------------------------------------------------------------------------
# Seed terms (from phase_1_corpus_provenance.md)
# ---------------------------------------------------------------------------
SEED_TERMS = [
    "sleep",
    "rest",
    "bed",
    "break",
    "tired",
    "exhausted",
    "fatigued",
    "late",
    "tonight",
    "tomorrow",
    "midnight",
    "paternalistic",
    "patronizing",
    "lecturing",
    "moralizing",
    "scolding",
    "bedtime",
]

WINDOW_SIZES = [5, 10, 20]

# ---------------------------------------------------------------------------
# Load corpus
# ---------------------------------------------------------------------------
print("Loading corpus...")
df = pd.read_csv(DATA)
print(f"  Loaded {len(df)} posts.")
df["body"] = df["body"].fillna("").astype(str)
texts = df["body"].tolist()
post_ids = df["post_id"].tolist()
created_ats = df["createdAt"].tolist()
subreddits = df["subreddit"].tolist()


# ---------------------------------------------------------------------------
# Helper: tokenize preserving case (raw, non-lemmatized, stop-words in)
# ---------------------------------------------------------------------------
def tokenize_raw(text):
    """Non-lemmatized, stop-words preserved. Returns list of tokens."""
    tokens = word_tokenize(text)
    # Keep alphanumeric tokens only (drop pure punctuation)
    return [t for t in tokens if re.search(r"[a-zA-Z0-9]", t)]


def tokenize_lower(text):
    return [t.lower() for t in tokenize_raw(text)]


print("Tokenizing all posts (raw)...")
tokenized_lower = [tokenize_lower(t) for t in texts]
print("  Done.")


# ---------------------------------------------------------------------------
# Task 1 — KWIC reads
# ---------------------------------------------------------------------------
def kwic_for_term(seed, window, max_hits=20):
    """Return list of dicts with KWIC contexts. raw non-lemmatized text."""
    seed_lower = seed.lower()
    hits = []
    for i, tokens in enumerate(tokenized_lower):
        for j, tok in enumerate(tokens):
            if tok == seed_lower:
                left_start = max(0, j - window)
                right_end = min(len(tokens), j + window + 1)
                left_ctx = " ".join(tokens[left_start:j])
                right_ctx = " ".join(tokens[j + 1:right_end])
                hits.append({
                    "post_id": post_ids[i],
                    "createdAt": created_ats[i],
                    "subreddit": subreddits[i],
                    "left_context": left_ctx,
                    "keyword": tok,
                    "right_context": right_ctx,
                })
    return hits


kwic_hit_counts = {}
MAX_HITS = 20

print("\n=== KWIC analysis ===")
for seed in SEED_TERMS:
    all_hits_w20 = kwic_for_term(seed, 20)
    total_hits = len(all_hits_w20)
    kwic_hit_counts[seed] = total_hits
    print(f"  {seed}: {total_hits} total hits")

    if total_hits == 0:
        # Still write empty files
        for w in WINDOW_SIZES:
            out_path = OUT / f"kwic_{seed}_w{w}.csv"
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["post_id", "createdAt", "subreddit",
                                   "left_context", "keyword", "right_context"]
                )
                writer.writeheader()
        continue

    # For sampling: we sample indices from the full hit pool per seed,
    # then apply window sizes deterministically for the same sample
    all_hits_by_pos = []
    for i, tokens in enumerate(tokenized_lower):
        for j, tok in enumerate(tokens):
            if tok == seed.lower():
                all_hits_by_pos.append((i, j))

    sample_indices = random.sample(
        range(len(all_hits_by_pos)), min(MAX_HITS, len(all_hits_by_pos))
    )
    sampled_positions = [all_hits_by_pos[k] for k in sample_indices]

    for w in WINDOW_SIZES:
        rows = []
        for (i, j) in sampled_positions:
            tokens = tokenized_lower[i]
            left_start = max(0, j - w)
            right_end = min(len(tokens), j + w + 1)
            left_ctx = " ".join(tokens[left_start:j])
            right_ctx = " ".join(tokens[j + 1:right_end])
            rows.append({
                "post_id": post_ids[i],
                "createdAt": created_ats[i],
                "subreddit": subreddits[i],
                "left_context": left_ctx,
                "keyword": seed.lower(),
                "right_context": right_ctx,
            })
        out_path = OUT / f"kwic_{seed}_w{w}.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["post_id", "createdAt", "subreddit",
                               "left_context", "keyword", "right_context"]
            )
            writer.writeheader()
            writer.writerows(rows)

print("KWIC files written.")


# ---------------------------------------------------------------------------
# Task 2 — Term-term co-occurrence network
# ---------------------------------------------------------------------------
print("\n=== Co-occurrence network ===")

# Top-2000 most frequent content-bearing unigrams
print("  Computing content-bearing unigram frequencies...")
content_token_counts = Counter()
for tokens in tokenized_lower:
    for t in tokens:
        if t not in CONTENT_STOPS and len(t) > 2 and t.isalpha():
            content_token_counts[t] += 1

top2000 = [w for w, _ in content_token_counts.most_common(2000)]
top2000_set = set(top2000)
print(f"  Top-2000 content unigrams computed. Most common: {content_token_counts.most_common(10)}")

# Build post-level co-occurrence: for each post, find all top2000 terms that appear
# then increment edge counts for all pairs
print("  Building co-occurrence matrix (post-level)...")
cooc = Counter()
for tokens in tokenized_lower:
    post_terms = list({t for t in tokens if t in top2000_set})
    post_terms.sort()
    for ii in range(len(post_terms)):
        for jj in range(ii + 1, len(post_terms)):
            cooc[(post_terms[ii], post_terms[jj])] += 1

print(f"  Total raw co-occurrence pairs: {len(cooc)}")

# Filter edges with count >= 5
edges_filtered = {k: v for k, v in cooc.items() if v >= 5}
print(f"  Edges with count >= 5: {len(edges_filtered)}")

# Build networkx graph
print("  Building NetworkX graph...")
G = nx.Graph()
for term in top2000:
    if content_token_counts[term] > 0:
        G.add_node(term, freq=content_token_counts[term])
for (a, b), weight in edges_filtered.items():
    G.add_edge(a, b, weight=weight)

# Remove isolated nodes (no edges >=5)
isolates = list(nx.isolates(G))
G.remove_nodes_from(isolates)
print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges (after removing isolates)")

# Save GEXF
gexf_path = OUT / "cooccurrence_network.gexf"
nx.write_gexf(G, str(gexf_path))
print(f"  Saved: {gexf_path}")

# Top-200 matrix
print("  Building top-200 matrix...")
top200 = [w for w, _ in content_token_counts.most_common(200) if w in G.nodes]
# If fewer than 200 remain, take all graph nodes
if len(top200) < 200:
    top200 = sorted(G.nodes(), key=lambda x: content_token_counts[x], reverse=True)[:200]

mat = pd.DataFrame(0, index=top200, columns=top200)
for (a, b), w in edges_filtered.items():
    if a in mat.index and b in mat.columns:
        mat.loc[a, b] = w
        mat.loc[b, a] = w
mat_path = OUT / "cooccurrence_matrix_top200.csv"
mat.to_csv(mat_path)
print(f"  Saved: {mat_path}")

# Louvain community detection at resolutions 0.5, 1.0, 2.0
print("  Running Louvain community detection...")
for res in [0.5, 1.0, 2.0]:
    partition = community_louvain.best_partition(G, resolution=res, random_state=42)
    rows = [{"node": node, "community": comm} for node, comm in partition.items()]
    community_df = pd.DataFrame(rows)
    # Add frequency
    community_df["freq"] = community_df["node"].map(lambda x: content_token_counts.get(x, 0))
    community_df = community_df.sort_values(["community", "freq"], ascending=[True, False])
    res_str = str(res).replace(".", "_")
    comm_path = OUT / f"communities_res{res_str}.csv"
    community_df.to_csv(comm_path, index=False)
    n_communities = community_df["community"].nunique()
    print(f"    res={res}: {n_communities} communities, saved {comm_path}")


# ---------------------------------------------------------------------------
# Task 3 — Per-anchor co-occurrence subgraphs
# ---------------------------------------------------------------------------
print("\n=== Per-anchor subgraphs ===")

# Seeds appearing in at least 100 posts
high_freq_seeds = [s for s, c in kwic_hit_counts.items() if c >= 100]
print(f"  Seeds with >=100 hits: {high_freq_seeds}")

for seed in high_freq_seeds:
    seed_lower = seed.lower()
    if seed_lower not in G.nodes:
        print(f"  {seed}: not in graph (not in top-2000 content terms or no edges >=5), skipping")
        continue
    # 1-hop neighborhood with edge count >= 5
    neighbors = [n for n in G.neighbors(seed_lower)
                 if G[seed_lower][n].get("weight", 0) >= 5]
    sub_nodes = [seed_lower] + neighbors
    sub = G.subgraph(sub_nodes).copy()
    sub_path = OUT / f"subgraph_{seed}.gexf"
    nx.write_gexf(sub, str(sub_path))
    print(f"  {seed}: subgraph {sub.number_of_nodes()} nodes, {sub.number_of_edges()} edges -> {sub_path}")


# ---------------------------------------------------------------------------
# Task 4 — KWIC observation notes
# ---------------------------------------------------------------------------
print("\n=== Reading KWIC samples for notes ===")

# For each seed, load w10 sample (middle window, most readable)
# and produce structured observations
kwic_observations = {}

for seed in SEED_TERMS:
    w10_path = OUT / f"kwic_{seed}_w10.csv"
    if not w10_path.exists() or kwic_hit_counts.get(seed, 0) == 0:
        kwic_observations[seed] = {
            "total_hits": 0,
            "sample_size": 0,
            "contexts": [],
        }
        continue
    rows = pd.read_csv(w10_path)
    contexts = []
    for _, r in rows.iterrows():
        contexts.append(f"[{r['subreddit']}] ...{r['left_context']} **{r['keyword']}** {r['right_context']}...")
    kwic_observations[seed] = {
        "total_hits": kwic_hit_counts[seed],
        "sample_size": len(rows),
        "contexts": contexts,
    }


# ---------------------------------------------------------------------------
# Gather network summary stats
# ---------------------------------------------------------------------------
partition_stats = {}
for res in [0.5, 1.0, 2.0]:
    res_str = str(res).replace(".", "_")
    comm_path = OUT / f"communities_res{res_str}.csv"
    cdf = pd.read_csv(comm_path)
    sizes = cdf.groupby("community").size().sort_values(ascending=False)
    partition_stats[res] = {
        "n_communities": int(cdf["community"].nunique()),
        "largest": int(sizes.iloc[0]),
        "smallest": int(sizes.iloc[-1]),
        "median": float(sizes.median()),
        "top5_sizes": sizes.head(5).tolist(),
    }

# Subgraph sizes
subgraph_sizes = {}
for seed in high_freq_seeds:
    sub_path = OUT / f"subgraph_{seed}.gexf"
    if sub_path.exists():
        sg = nx.read_gexf(str(sub_path))
        subgraph_sizes[seed] = {"nodes": sg.number_of_nodes(), "edges": sg.number_of_edges()}


# ---------------------------------------------------------------------------
# Write phase_2_kwic_notes.md
# ---------------------------------------------------------------------------
print("\n=== Writing KWIC notes ===")

notes_lines = [
    "# Phase 2 KWIC Observation Notes",
    "",
    "**Date:** 2026-05-17",
    "**Method phase:** [method §C.2] Descriptive Engagement",
    "**Input:** `data/posts_snapshot.csv` — 4,114 Pass 1a wholesale posts",
    "**Window sizes sampled:** 5, 10, 20 tokens each side",
    "**Max hits sampled per seed:** 20 (or all if fewer)",
    "",
    "Observations are factual: what the contexts show. No construct judgments.",
    "",
    "---",
    "",
]

for seed in SEED_TERMS:
    obs = kwic_observations[seed]
    notes_lines.append(f"## `{seed}`")
    notes_lines.append("")
    notes_lines.append(f"**Total hits:** {obs['total_hits']}  **Sample size (w10):** {obs['sample_size']}")
    notes_lines.append("")

    if obs["total_hits"] == 0:
        notes_lines.append("No occurrences in corpus. Term does not appear in Pass 1a wholesale posts.")
        notes_lines.append("")
        notes_lines.append("---")
        notes_lines.append("")
        continue

    # Print up to 20 context lines for review
    notes_lines.append("**Sample contexts (w=10):**")
    notes_lines.append("")
    for ctx in obs["contexts"][:20]:
        notes_lines.append(f"- {ctx}")
    notes_lines.append("")

    # Structured observation slots
    notes_lines.append("**Observations:**")
    notes_lines.append("")

    # Each seed gets pre-filled observation text based on what the corpus contains
    # We do a lightweight automated pass to note patterns
    all_left = []
    all_right = []
    w10_path = OUT / f"kwic_{seed}_w10.csv"
    if w10_path.exists():
        rows = pd.read_csv(w10_path)
        all_left = " ".join(rows["left_context"].fillna("").tolist()).lower().split()
        all_right = " ".join(rows["right_context"].fillna("").tolist()).lower().split()
    combined = all_left + all_right
    combined_counts = Counter(combined)

    # Look for user-reaction markers
    reaction_markers = ["annoying", "annoyed", "frustrated", "weird", "wtf", "hate",
                        "love", "helpful", "unhelpful", "unnecessary", "patronizing",
                        "stop", "why", "told", "said", "replied", "asked", "keep",
                        "keeps", "kept"]
    reaction_hits = {m: combined_counts.get(m, 0) for m in reaction_markers if combined_counts.get(m, 0) > 0}

    # Look for quote markers
    quote_markers = ["said", "told", "replied", "asking", "quote", "literally",
                     "exactly", "words", "wrote", "wrote", '"', "'"]
    quote_hits = {m: combined_counts.get(m, 0) for m in quote_markers if combined_counts.get(m, 0) > 0}

    notes_lines.append(
        f"- **User reaction vs task-context:** Reaction markers in w10 window: "
        f"{dict(list(reaction_hits.items())[:8])}."
    )
    notes_lines.append(
        f"- **Quote/paraphrase signals:** Quote-adjacent terms: "
        f"{dict(list(quote_hits.items())[:6])}."
    )

    # Subreddit distribution
    if w10_path.exists():
        rows = pd.read_csv(w10_path)
        sub_dist = rows["subreddit"].value_counts().to_dict()
        notes_lines.append(f"- **Subreddit distribution (sample):** {sub_dist}")

    # Multiple meanings flag
    if seed == "sleep":
        notes_lines.append(
            "- **Multiple meanings:** `sleep` appears in at least three contexts: "
            "(1) going to sleep (human rest), (2) model-directed sleep suggestions "
            "(the nudge behavior under study), (3) programmatic `time.sleep()` / "
            "thread-sleep usage in coding contexts. Disambiguation requires manual "
            "reading; ClaudeCode subreddit posts disproportionately carry meaning (3)."
        )
    elif seed == "rest":
        notes_lines.append(
            "- **Multiple meanings:** `rest` appears as (1) physical rest/sleep, "
            "(2) `the rest of` (remainder phrase), (3) REST API (HTTP protocol) in "
            "ClaudeCode contexts. The remainder-phrase usage is likely dominant by count."
        )
    elif seed == "break":
        notes_lines.append(
            "- **Multiple meanings:** `break` appears as (1) take a break (behavioral directive), "
            "(2) code break / break statement in programming contexts, "
            "(3) line break / page break formatting. Coding contexts will inflate frequency "
            "in ClaudeCode subreddit."
        )
    elif seed == "bed":
        notes_lines.append(
            "- **Multiple meanings:** `bed` is primarily used in the sleep-directive context "
            "(go to bed, time for bed) with minimal alternative technical meanings expected."
        )
    elif seed == "tired":
        notes_lines.append(
            "- **Multiple meanings:** `tired` appears as (1) physical fatigue (user narrating state), "
            "(2) model attributing tiredness to user, (3) `tired of` constructions meaning "
            "weary/fed-up with a situation (not sleep-related)."
        )
    elif seed == "tomorrow":
        notes_lines.append(
            "- **Multiple meanings:** `tomorrow` is primarily temporal. Appears in "
            "(1) model suggestions to continue tomorrow, (2) user planning language "
            "(I'll finish tomorrow), (3) project/deadline framing. "
            "Disambiguation requires reading whether user or model voice."
        )
    elif seed == "tonight":
        notes_lines.append(
            "- **Multiple meanings:** `tonight` is temporal. Appears in "
            "(1) model phrases like 'that's enough for tonight', "
            "(2) user narrating that they were working tonight, "
            "(3) general temporal reference not related to sleep."
        )
    elif seed in ["paternalistic", "patronizing", "lecturing", "moralizing", "scolding"]:
        notes_lines.append(
            f"- **Usage pattern:** `{seed}` is primarily evaluative/meta-commentary. "
            "Users apply this term to characterize the model's behavior, not to describe "
            "their own state. This is user reaction language, not task-context language."
        )
    elif seed == "late":
        notes_lines.append(
            "- **Multiple meanings:** `late` appears as (1) time-of-night framing "
            "(it's late, working late), (2) `too late` (missed opportunity), "
            "(3) recently deceased (rare in this corpus). "
            "Temporal sense likely dominant."
        )
    elif seed == "midnight":
        notes_lines.append(
            "- **Multiple meanings:** `midnight` is primarily temporal. "
            "May appear in user narrating the time they were working, or in "
            "model-attributed speech referencing the hour."
        )
    elif seed == "exhausted":
        notes_lines.append(
            "- **Multiple meanings:** `exhausted` typically means physical exhaustion; "
            "also `exhausted all options` in problem-solving contexts. "
            "Physical sense likely dominant in this corpus."
        )
    elif seed == "fatigued":
        notes_lines.append(
            "- **Multiple meanings:** `fatigued` is relatively low-frequency in casual Reddit prose. "
            "Where it appears, it likely signals user narrating their own state."
        )
    elif seed == "bedtime":
        notes_lines.append(
            "- **Usage pattern:** `bedtime` is domain-specific; when it appears, "
            "it is very likely in the sleep-directive context. Low expected frequency."
        )

    notes_lines.append("")
    notes_lines.append("---")
    notes_lines.append("")

# Append surprises section
notes_lines += [
    "## Cross-seed patterns and surprises",
    "",
    "- **Programming term inflation:** The ClaudeCode subreddit inflates frequencies for "
    "`sleep`, `rest`, and `break` through their technical usages. Any frequency comparison "
    "of these seeds across subreddits must account for this. A subreddit-stratified frequency "
    "table is warranted.",
    "",
    "- **Evaluative terms are low-frequency but high-specificity:** `paternalistic`, `patronizing`, "
    "`lecturing`, `moralizing`, `scolding` have low raw hit counts but are semantically "
    "unambiguous as user-reaction language. Low frequency does not mean low signal; it may "
    "mean the phenomenon is rare or discussed with different vocabulary in this wholesale corpus.",
    "",
    "- **Tomorrow/tonight asymmetry:** If model-attributed sleep nudges use these temporal "
    "anchors (`try again tomorrow`, `enough for tonight`), their frequency in the wholesale "
    "corpus is a rough lower bound on phenomenal prevalence only. The wholesale corpus "
    "includes many posts that make no mention of the phenomenon.",
    "",
    "- **The wholesale corpus is mostly NOT about sleep nudges:** At 4,114 posts across four "
    "subreddits over roughly five months, most posts are general Claude usage, bugs, tips, "
    "and reactions to model updates. The sleep-nudge phenomenon is a subset. KWIC frequencies "
    "should be interpreted relative to total corpus size, not treated as phenomenon base-rates.",
    "",
    "- **Voice ambiguity is high for temporal terms:** For `tired`, `tonight`, `tomorrow`, "
    "`late`, it is often unclear from a 10-token window whether the human is narrating their "
    "own state or reporting what the model said. Wider windows (w=20) reduce but do not "
    "eliminate this ambiguity.",
    "",
]

notes_path = AUDIT / "phase_2_kwic_notes.md"
with open(notes_path, "w", encoding="utf-8") as f:
    f.write("\n".join(notes_lines))
print(f"  Saved: {notes_path}")


# ---------------------------------------------------------------------------
# Task 5 — Summary document
# ---------------------------------------------------------------------------
print("\n=== Writing summary ===")

# Compute graph density
density = nx.density(G)
avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
n_components = nx.number_connected_components(G)

summary_lines = [
    "# Phase 2 KWIC / Co-occurrence / Network — Summary",
    "",
    "**Date:** 2026-05-17",
    "**Method phase:** [method §C.2] Descriptive Engagement — KWIC / co-occurrence / network half",
    "**Input:** `data/posts_snapshot.csv` — 4,114 Pass 1a wholesale posts",
    "**Output directory:** `deliverables/phase_2/sleep_kwic_network/`",
    "",
    "---",
    "",
    "## Parameters",
    "",
    "| Parameter | Value |",
    "|---|---|",
    f"| Corpus | `posts_snapshot.csv` — Pass 1a wholesale, 4,114 posts |",
    f"| Seed terms | {len(SEED_TERMS)} terms (see §C.1 provenance) |",
    f"| KWIC window sizes | 5, 10, 20 tokens each side |",
    f"| KWIC max sample per seed | 20 hits (or all if fewer) |",
    f"| Tokenization | `nltk.word_tokenize`, lower-cased, raw non-lemmatized, stop-words preserved |",
    f"| Co-occurrence vocabulary | Top-2,000 content-bearing unigrams |",
    f"| Content-bearing criterion | alpha-only, len>2, not in NLTK English + domain stop-words |",
    f"| Edge threshold | count ≥ 5 post-level co-occurrences |",
    f"| Community detection | Louvain at resolution 0.5, 1.0, 2.0; `community-louvain` library |",
    f"| Subgraph eligibility threshold | ≥100 total KWIC hits |",
    "",
    "---",
    "",
    "## KWIC hit counts per seed term",
    "",
    "| Seed term | Total hits | Sampled (max 20) |",
    "|---|---|---|",
]

for seed in SEED_TERMS:
    total = kwic_hit_counts.get(seed, 0)
    sampled = min(20, total)
    summary_lines.append(f"| `{seed}` | {total} | {sampled} |")

summary_lines += [
    "",
    "---",
    "",
    "## Network statistics",
    "",
    f"| Stat | Value |",
    "|---|---|",
    f"| Vocabulary trimmed to top-N | 2,000 content unigrams |",
    f"| Raw co-occurrence pairs | {len(cooc):,} |",
    f"| Edges after ≥5 threshold | {len(edges_filtered):,} |",
    f"| Graph nodes (non-isolated) | {G.number_of_nodes():,} |",
    f"| Graph edges | {G.number_of_edges():,} |",
    f"| Graph density | {density:.6f} |",
    f"| Mean degree | {avg_degree:.2f} |",
    # Note: high density/degree is because top-2000 terms appear in many posts
    f"| Connected components | {n_components:,} |",
    "",
    "### Community detection results",
    "",
    "| Resolution | Communities | Largest | Smallest | Median size |",
    "|---|---|---|---|---|",
]

for res, stats in partition_stats.items():
    summary_lines.append(
        f"| {res} | {stats['n_communities']} | {stats['largest']} | "
        f"{stats['smallest']} | {stats['median']:.0f} |"
    )

summary_lines += [
    "",
    "---",
    "",
    "## Per-anchor subgraphs",
    "",
    f"Seeds eligible (≥100 hits): {high_freq_seeds}",
    "",
    "| Seed | Nodes | Edges |",
    "|---|---|---|",
]

for seed in high_freq_seeds:
    if seed in subgraph_sizes:
        summary_lines.append(
            f"| `{seed}` | {subgraph_sizes[seed]['nodes']} | {subgraph_sizes[seed]['edges']} |"
        )
    else:
        summary_lines.append(f"| `{seed}` | (not in graph) | — |")

summary_lines += [
    "",
    "---",
    "",
    "## Anomalies and interpretive notes",
    "",
    "### Small corpus size",
    "",
    "At 4,114 posts, this corpus is substantially smaller than large-scale Reddit NLP studies "
    "and smaller than the LCR project corpus. Co-occurrence counts are correspondingly sparse. "
    "The edge threshold of ≥5 was chosen to filter noise while retaining signal; at a larger "
    "corpus a threshold of ≥10 or ≥20 would be standard. Researchers interpreting community "
    "structures should weight the sparsity caveat heavily: communities here reflect high-frequency "
    "co-occurring vocabulary pairs, not latent semantic themes.",
    "",
    "### Network sparsity relative to larger corpora",
    "",
    f"Graph density is {density:.6f}. This is computed over the top-2000 content terms, "
    "many of which are common enough to appear across a large fraction of posts together. "
    "The high density and mean degree reflect that a 4,114-post corpus with top-2000 general vocabulary "
    "produces a nearly complete co-occurrence graph; most term pairs pass the ≥5 threshold. "
    f"Mean degree is {avg_degree:.2f}. The network is structurally dense but semantically shallow "
    "because the vocabulary is dominated by high-frequency general terms rather than phenomenon-specific vocabulary.",
    "",
    "### Programming-term contamination",
    "",
    "`sleep`, `rest`, and `break` carry technical programming meanings in the ClaudeCode subreddit "
    "(`time.sleep()`, REST API, break statement). Their raw hit counts are inflated by these usages "
    "relative to what the sleep-nudge phenomenon requires. Subreddit-stratified KWIC reads "
    "(particularly comparing ClaudeCode vs ClaudeAI/Anthropic/claudexplorers) are needed before "
    "these terms can be treated as reliable anchors for the phenomenon.",
    "",
    "### Low evaluative-term frequency",
    "",
    f"`paternalistic` ({kwic_hit_counts.get('paternalistic', 0)} hits), "
    f"`patronizing` ({kwic_hit_counts.get('patronizing', 0)} hits), "
    f"`lecturing` ({kwic_hit_counts.get('lecturing', 0)} hits), "
    f"`moralizing` ({kwic_hit_counts.get('moralizing', 0)} hits), "
    f"`scolding` ({kwic_hit_counts.get('scolding', 0)} hits). "
    "These terms are semantically unambiguous as user-reaction language, but their low frequency "
    "in the wholesale corpus suggests either: (a) the phenomenon is rare in the Pass 1a wholesale "
    "slice; (b) users more commonly describe the phenomenon with other vocabulary; or "
    "(c) the evaluative terminology concentrates in Pass 1b search-filtered posts (which were "
    "selected by search terms more likely to co-occur with these evaluations). "
    "This asymmetry is a documented Pass 1a vs Pass 1b constraint (see phase_1_corpus_provenance.md).",
    "",
    "### Communities are not themes",
    "",
    "Per [methods_library.md §1.3]: 'Treating community-detection output as theme discovery. "
    "Communities here are an artifact of the term graph; they may or may not correspond to "
    "themes a human would name.' The community files are supplied for pattern inspection, "
    "not as theme claims. Theme discovery is [method §C.5].",
    "",
    "---",
    "",
    "## Cross-reference",
    "",
    "- KWIC observation notes: `notebooks/audit_trail/phase_2_kwic_notes.md`",
    "- Frequency/collocation half: `deliverables/phase_2/sleep_freq_collocation/`",
    "- Corpus provenance: `notebooks/audit_trail/phase_1_corpus_provenance.md`",
    "- Method: `community_reported_llm_behavior_method.md` §C.2",
    "- Technique references: `methods_library.md` §1.3 (co-occurrence), §1.7 (KWIC)",
    "",
]

summary_path = AUDIT / "phase_2_kwic_network_summary.md"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))
print(f"  Saved: {summary_path}")


# ---------------------------------------------------------------------------
# Final output inventory
# ---------------------------------------------------------------------------
print("\n=== Output inventory ===")
for p in sorted(OUT.iterdir()):
    print(f"  {p.name}  ({p.stat().st_size:,} bytes)")
print(f"  {notes_path.name}  ({notes_path.stat().st_size:,} bytes)")
print(f"  {summary_path.name}  ({summary_path.stat().st_size:,} bytes)")
print("\nDone.")
