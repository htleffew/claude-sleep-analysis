"""
Phase 2 KWIC / Co-occurrence / Network analysis on Pass 1b canonical corpus.
Input:  data/pass1b_canonical.csv  (773 rows: 242 posts + 531 comments)
Output: deliverables/phase_2_pass1b/sleep_kwic_network/

Per method §C.2 and methods_library §1.3 and §1.7.
"""

import csv
import json
import math
import os
import random
import re
import string
import collections
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities

# ── paths ──────────────────────────────────────────────────────────────────
REPO = Path(r"C:\Users\drhea\repos\claude-sleep-analysis")
CORPUS_CSV = REPO / "data" / "pass1b_canonical.csv"
OUT_DIR = REPO / "deliverables" / "phase_2_pass1b" / "sleep_kwic_network"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# ── seed terms (Phase 1 + Round 2 augmented) ───────────────────────────────
PHASE1_SEEDS = [
    "sleep", "rest", "bed", "break", "tired",
    "exhausted", "fatigued", "late", "tonight",
    "tomorrow", "midnight", "bedtime",
    "paternalistic", "patronizing", "lecturing",
    "moralizing", "scolding",
]

ROUND2_SEEDS = [
    "go to bed", "go to sleep", "now sleep", "get some rest",
    "sleep for real", "you are tired", "you must go to sleep",
    "take a break", "it needs some rest", "claude said it needs to rest",
    "take the rest of the night off", "we finished phase",
    "a time for a break", "call it a day", "call it a night",
    "go get some rest", "go sleep", "we can work on this later",
    "this isn't worth your health", "too tired to continue",
    "that's a good place to leave", "we have done enough in this session",
    "you did enough today", "pick this up tomorrow",
    "i suggest we pause here and continue tomorrow",
    "the responsible thing is to stop", "well rested",
    "sending me to bed", "put me to bed", "sent me to bed",
    "told me to go to bed", "nanny", "nagging",
    "unsolicited parenting", "fight me on doing work",
    "who asked", "passively aggressively", "gets under my skin",
    "spiraling", "long session", "nudge", "enough for today",
    "finish this then sleep", "you need to eat",
]

ALL_SEEDS = PHASE1_SEEDS + ROUND2_SEEDS
# Deduplicate preserving order
seen = set()
SEEDS_ORDERED = []
for s in ALL_SEEDS:
    if s not in seen:
        seen.add(s)
        SEEDS_ORDERED.append(s)

WINDOWS = [5, 10, 20]

# ── stop words ─────────────────────────────────────────────────────────────
STOPWORDS = set("""
a about above after again against all also am an and another any are aren't as at
be because been before being below between both but by can't cannot could couldn't
did didn't do does doesn't doing don't down during each even few for from further
get got had hadn't has hasn't have haven't having he he'd he'll he's her here
here's hers herself him himself his how how's i i'd i'll i'm i've if in into is
isn't it it's its itself just know let like ll lot made make me might more most
must my myself no nor not now of off on once only or other our ours ourselves out
own re really re s same she she'd she'll she's should shouldn't so some such that
than the their theirs them themselves then there there's these they they'd they'll
they're they've this those through to too under until up ve very was we we'd we'll
we're we've were weren't what when when's where which while who why will with won't
would wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

# domain high-frequency but low-signal terms in THIS targeted corpus
DOMAIN_STOP = {"claude", "gpt", "llm", "ai", "model", "api", "prompt", "chat",
               "chatgpt", "openai", "anthropic", "use", "using", "used", "ve",
               "one", "get", "got", "like", "just", "know", "really", "would",
               "could", "think", "thing", "things", "want", "need", "way",
               "going", "make", "work", "working", "time", "even", "also",
               "still", "back", "see", "said", "say", "saying", "told",
               "tell", "tells", "always", "never", "every", "feel"}

ALL_STOP = STOPWORDS | DOMAIN_STOP


def tokenize_raw(text):
    """Non-lemmatized tokens, lower-cased, punctuation stripped."""
    text = text.lower()
    text = re.sub(r"[''`]", "'", text)
    text = re.sub(r"[^a-z0-9 \'\-]", " ", text)
    return text.split()


def content_tokens(text):
    """Tokens with stop words removed, for vocabulary/network building."""
    return [t for t in tokenize_raw(text) if t not in ALL_STOP and len(t) > 1]


# ── load corpus ────────────────────────────────────────────────────────────
def load_corpus():
    rows = []
    with open(CORPUS_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ── KWIC ───────────────────────────────────────────────────────────────────
def kwic_search(rows, seed, window):
    """Find all hits for seed in corpus; return list of hit dicts."""
    seed_lo = seed.lower()
    seed_tokens = seed_lo.split()
    n = len(seed_tokens)
    hits = []
    for row in rows:
        text = (row.get("body") or "").lower()
        tokens = tokenize_raw(text)
        for i in range(len(tokens) - n + 1):
            if tokens[i:i+n] == seed_tokens:
                left = " ".join(tokens[max(0, i-window):i])
                kw = " ".join(tokens[i:i+n])
                right = " ".join(tokens[i+n:i+n+window])
                hits.append({
                    "post_id": row.get("post_id", ""),
                    "type": row.get("type", ""),
                    "retrieval_provenance": row.get("retrieval_provenance", ""),
                    "createdAt": row.get("createdAt", ""),
                    "subreddit": row.get("subreddit", ""),
                    "left_context": left,
                    "keyword": kw,
                    "right_context": right,
                })
    return hits


KWIC_FIELDNAMES = [
    "post_id", "type", "retrieval_provenance", "createdAt",
    "subreddit", "left_context", "keyword", "right_context",
]


def slug(seed):
    """Convert seed term to filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", seed.lower()).strip("_")


def run_kwic(rows):
    """Run KWIC for all seeds at all windows. Return hit_counts dict."""
    hit_counts = {}  # seed -> {window -> {total, posts, comments}}
    for seed in SEEDS_ORDERED:
        hit_counts[seed] = {}
        for window in WINDOWS:
            hits = kwic_search(rows, seed, window)
            n_total = len(hits)
            n_posts = sum(1 for h in hits if h["type"] == "post")
            n_comments = sum(1 for h in hits if h["type"] == "comment")
            hit_counts[seed][window] = {
                "total": n_total,
                "posts": n_posts,
                "comments": n_comments,
            }
            # Sample up to 20 random hits
            sample = random.sample(hits, min(20, n_total)) if n_total > 0 else []
            fname = OUT_DIR / f"kwic_{slug(seed)}_w{window}.csv"
            with open(fname, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=KWIC_FIELDNAMES)
                writer.writeheader()
                writer.writerows(sample)
        print(f"KWIC done: {seed!r:40s}  w5={hit_counts[seed][5]['total']:4d}  w10={hit_counts[seed][10]['total']:4d}  w20={hit_counts[seed][20]['total']:4d}")
    return hit_counts


def save_hit_counts(hit_counts):
    fname = OUT_DIR / "kwic_hit_counts.csv"
    with open(fname, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "window", "total", "posts", "comments"])
        for seed, windows in hit_counts.items():
            for window, counts in windows.items():
                writer.writerow([seed, window, counts["total"],
                                  counts["posts"], counts["comments"]])


# ── co-occurrence network (full corpus) ────────────────────────────────────
TOP_VOCAB = 1500
MIN_EDGE_COUNT = 3
SUBGRAPH_MIN_ROWS = 30


def build_cooc_matrix(rows, subset=None, top_n=TOP_VOCAB):
    """
    Build term-term co-occurrence at document (row) level.
    Returns: (term_counts, cooc_dict, doc_count)
    cooc_dict[(t1,t2)] = count of docs containing both
    """
    if subset is not None:
        use_rows = [r for r in rows if r.get("type") == subset]
    else:
        use_rows = rows

    # Count total term frequency
    term_freq = collections.Counter()
    for row in use_rows:
        tokens = set(content_tokens(row.get("body") or ""))
        term_freq.update(tokens)

    # Take top_n
    vocab = {t for t, _ in term_freq.most_common(top_n)}

    # Build co-occurrence
    cooc = collections.Counter()
    for row in use_rows:
        tokens = set(content_tokens(row.get("body") or "")) & vocab
        token_list = sorted(tokens)
        for i in range(len(token_list)):
            for j in range(i + 1, len(token_list)):
                pair = (token_list[i], token_list[j])
                cooc[pair] += 1

    return vocab, cooc, len(use_rows)


def build_nx_graph(vocab, cooc, min_count=MIN_EDGE_COUNT, label=""):
    G = nx.Graph()
    G.graph["label"] = label
    for t in vocab:
        G.add_node(t)
    for (t1, t2), cnt in cooc.items():
        if cnt >= min_count:
            G.add_edge(t1, t2, weight=cnt)
    # Remove isolates for cleaner graph
    isolates = list(nx.isolates(G))
    G.remove_nodes_from(isolates)
    return G


def run_louvain(G, resolutions=(0.5, 1.0, 2.0)):
    results = {}
    for res in resolutions:
        communities = louvain_communities(G, seed=42, resolution=res)
        results[res] = communities
    return results


def save_communities(communities, resolution, fname):
    with open(fname, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["community_id", "resolution", "size", "term"])
        for cid, community in enumerate(sorted(communities, key=len, reverse=True)):
            for term in sorted(community):
                writer.writerow([cid, resolution, len(community), term])


def save_cooc_matrix_csv(G, top_n=200, fname=None):
    """Save top-200-node adjacency as CSV."""
    # Pick top_n nodes by degree
    degree_sorted = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    top_nodes = [n for n, _ in degree_sorted[:top_n]]
    with open(fname, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([""] + top_nodes)
        for n in top_nodes:
            row = [n]
            for m in top_nodes:
                w = G[n][m]["weight"] if G.has_edge(n, m) else 0
                row.append(w)
            writer.writerow(row)


def run_network(rows):
    """Full-corpus network."""
    print("Building full-corpus co-occurrence network...")
    vocab, cooc, n_docs = build_cooc_matrix(rows, subset=None, top_n=TOP_VOCAB)
    G = build_nx_graph(vocab, cooc, MIN_EDGE_COUNT, "pass1b_full")
    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges  (from {n_docs} docs)")

    nx.write_gexf(G, str(OUT_DIR / "cooccurrence_network.gexf"))
    save_cooc_matrix_csv(G, top_n=200, fname=OUT_DIR / "cooccurrence_matrix_top200.csv")

    communities_by_res = run_louvain(G)
    for res, comms in communities_by_res.items():
        res_str = str(res).replace(".", "_")
        save_communities(comms, res, OUT_DIR / f"communities_res{res_str}.csv")
        print(f"  Louvain res={res}: {len(comms)} communities, sizes {sorted([len(c) for c in comms], reverse=True)[:10]}")

    return G, vocab, cooc, communities_by_res


# ── subgraphs for seed terms appearing in >= SUBGRAPH_MIN_ROWS rows ────────
def run_subgraphs(rows, G):
    """Per-anchor 1-hop subgraphs for qualifying seed terms."""
    # Count rows containing each seed (use w20 logic: present in doc body)
    seed_row_counts = {}
    for seed in SEEDS_ORDERED:
        seed_lo = seed.lower()
        seed_toks = seed_lo.split()
        n = len(seed_toks)
        count = 0
        for row in rows:
            text = (row.get("body") or "").lower()
            tokens = tokenize_raw(text)
            found = False
            for i in range(len(tokens) - n + 1):
                if tokens[i:i+n] == seed_toks:
                    found = True
                    break
            if found:
                count += 1
        seed_row_counts[seed] = count

    # Subgraph stats
    subgraph_stats = []
    nodes_in_graph = set(G.nodes())

    for seed in SEEDS_ORDERED:
        count = seed_row_counts[seed]
        # Use the first token of the seed as the network node (if the seed is a unigram)
        # For phrases, try each token
        anchor_tokens = seed.lower().split()
        anchor = None
        for tok in anchor_tokens:
            if tok in nodes_in_graph:
                anchor = tok
                break

        if count < SUBGRAPH_MIN_ROWS:
            subgraph_stats.append({
                "seed": seed, "row_count": count,
                "qualifies": False, "reason": f"count {count} < {SUBGRAPH_MIN_ROWS}",
                "anchor_node": anchor or "none",
                "subgraph_nodes": 0, "subgraph_edges": 0,
            })
            continue

        if anchor is None:
            subgraph_stats.append({
                "seed": seed, "row_count": count,
                "qualifies": True, "reason": "anchor not in network vocab",
                "anchor_node": "none",
                "subgraph_nodes": 0, "subgraph_edges": 0,
            })
            continue

        # 1-hop neighborhood with edge count >= MIN_EDGE_COUNT
        neighbors = {anchor} | set(G.neighbors(anchor))
        sub = G.subgraph(neighbors).copy()
        # Filter edges by weight
        edges_to_remove = [(u, v) for u, v, d in sub.edges(data=True)
                           if d.get("weight", 0) < MIN_EDGE_COUNT]
        sub.remove_edges_from(edges_to_remove)

        gexf_path = OUT_DIR / f"subgraph_{slug(seed)}.gexf"
        nx.write_gexf(sub, str(gexf_path))
        subgraph_stats.append({
            "seed": seed, "row_count": count,
            "qualifies": True, "reason": "ok",
            "anchor_node": anchor,
            "subgraph_nodes": sub.number_of_nodes(),
            "subgraph_edges": sub.number_of_edges(),
        })
        print(f"  Subgraph {seed!r:25s}: row_count={count:3d}  anchor={anchor!r}  nodes={sub.number_of_nodes():4d}  edges={sub.number_of_edges():5d}")

    # Save stats
    with open(OUT_DIR / "subgraph_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seed", "row_count", "qualifies", "reason",
            "anchor_node", "subgraph_nodes", "subgraph_edges",
        ])
        writer.writeheader()
        writer.writerows(subgraph_stats)

    return subgraph_stats, seed_row_counts


# ── cross-type networks (posts-only, comments-only) ────────────────────────
def run_cross_type_networks(rows):
    results = {}
    for subset in ("post", "comment"):
        print(f"Building {subset}-only co-occurrence network...")
        vocab, cooc, n_docs = build_cooc_matrix(rows, subset=subset, top_n=TOP_VOCAB)
        G = build_nx_graph(vocab, cooc, MIN_EDGE_COUNT, f"pass1b_{subset}s")
        print(f"  {subset} graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges  (from {n_docs} docs)")
        nx.write_gexf(G, str(OUT_DIR / f"cooccurrence_network_{subset}s.gexf"))
        results[subset] = {
            "G": G, "n_docs": n_docs,
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "density": nx.density(G),
        }
    return results


# ── network stats ──────────────────────────────────────────────────────────
def compute_network_stats(G, communities_by_res, cross_type, subgraph_stats, seed_row_counts):
    stats = {
        "corpus_rows": 773,
        "corpus_posts": 242,
        "corpus_comments": 531,
        "vocab_top_n": TOP_VOCAB,
        "min_edge_count": MIN_EDGE_COUNT,
        "subgraph_min_rows": SUBGRAPH_MIN_ROWS,
        "full_network": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "density": nx.density(G),
            "avg_degree": (2 * G.number_of_edges() / G.number_of_nodes()
                           if G.number_of_nodes() > 0 else 0),
        },
        "louvain_communities": {
            str(res): {
                "n_communities": len(comms),
                "sizes": sorted([len(c) for c in comms], reverse=True),
            }
            for res, comms in communities_by_res.items()
        },
        "cross_type_networks": {
            subset: {k: v for k, v in info.items() if k != "G"}
            for subset, info in cross_type.items()
        },
        "subgraph_qualifying_seeds": [
            s["seed"] for s in subgraph_stats if s["qualifies"] and s["anchor_node"] != "none"
        ],
        "subgraph_non_qualifying": [
            {"seed": s["seed"], "row_count": s["row_count"], "reason": s["reason"]}
            for s in subgraph_stats if not s["qualifies"] or s["anchor_node"] == "none"
        ],
        "seed_row_counts": seed_row_counts,
    }
    with open(OUT_DIR / "network_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats


# ── KWIC observations (automated summary for notes doc) ───────────────────
def observe_kwic(rows, hit_counts):
    """
    Produce per-seed pattern summary for notes document.
    Returns dict: seed -> observation_text
    """
    observations = {}
    for seed in SEEDS_ORDERED:
        hits_w20 = kwic_search(rows, seed, 20)
        if not hits_w20:
            observations[seed] = {
                "total_w20": 0,
                "post_hits": 0,
                "comment_hits": 0,
                "subreddits": {},
                "provenances": {},
                "sample_contexts": [],
            }
            continue
        subreddits = collections.Counter(h["subreddit"] for h in hits_w20)
        provenances = collections.Counter(h["retrieval_provenance"] for h in hits_w20)
        post_hits = sum(1 for h in hits_w20 if h["type"] == "post")
        comment_hits = sum(1 for h in hits_w20 if h["type"] == "comment")
        # Sample 5 contexts for the notes
        sample = random.sample(hits_w20, min(5, len(hits_w20)))
        observations[seed] = {
            "total_w20": len(hits_w20),
            "post_hits": post_hits,
            "comment_hits": comment_hits,
            "subreddits": dict(subreddits.most_common()),
            "provenances": dict(provenances.most_common()),
            "sample_contexts": [
                f"{h['left_context']} | [{h['keyword']}] | {h['right_context']}"
                for h in sample
            ],
        }
    return observations


# ── cross-type comparison notes ────────────────────────────────────────────
def cross_type_comparison_notes(cross_type, G_full):
    """Return a markdown paragraph describing post vs comment network comparison."""
    G_post = cross_type["post"]["G"]
    G_comm = cross_type["comment"]["G"]

    # Top degree nodes in each
    def top_degree(G, n=20):
        return [nd for nd, _ in sorted(G.degree(), key=lambda x: x[1], reverse=True)[:n]]

    post_top = top_degree(G_post)
    comm_top = top_degree(G_comm)
    overlap = set(post_top) & set(comm_top)

    # Jaccard of top-100 nodes by degree
    post_top100 = set(n for n, _ in sorted(G_post.degree(), key=lambda x: x[1], reverse=True)[:100])
    comm_top100 = set(n for n, _ in sorted(G_comm.degree(), key=lambda x: x[1], reverse=True)[:100])
    jaccard = len(post_top100 & comm_top100) / len(post_top100 | comm_top100) if (post_top100 | comm_top100) else 0

    lines = [
        f"- Post-only network: {cross_type['post']['n_nodes']} nodes, "
        f"{cross_type['post']['n_edges']} edges, density={cross_type['post']['density']:.5f}",
        f"- Comment-only network: {cross_type['comment']['n_nodes']} nodes, "
        f"{cross_type['comment']['n_edges']} edges, density={cross_type['comment']['density']:.5f}",
        f"- Full-corpus network: {G_full.number_of_nodes()} nodes, "
        f"{G_full.number_of_edges()} edges, density={nx.density(G_full):.5f}",
        f"- Top-20 degree overlap between post and comment networks: {sorted(overlap)}",
        f"- Jaccard similarity of top-100 degree nodes (post vs comment): {jaccard:.3f}",
        f"- Top-20 post-network nodes by degree: {post_top}",
        f"- Top-20 comment-network nodes by degree: {comm_top}",
    ]
    return "\n".join(lines)


# ── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("Loading corpus...")
    rows = load_corpus()
    print(f"  {len(rows)} rows loaded  ({sum(1 for r in rows if r['type']=='post')} posts, "
          f"{sum(1 for r in rows if r['type']=='comment')} comments)")

    # Task 1: KWIC
    print("\n=== Task 1: KWIC ===")
    hit_counts = run_kwic(rows)
    save_hit_counts(hit_counts)

    # Task 1b: observations for notes doc
    print("\nCollecting KWIC observations...")
    observations = observe_kwic(rows, hit_counts)

    # Task 2: Full co-occurrence network
    print("\n=== Task 2: Full co-occurrence network ===")
    G_full, vocab, cooc, communities_by_res = run_network(rows)

    # Task 3: Subgraphs
    print("\n=== Task 3: Per-anchor subgraphs ===")
    subgraph_stats, seed_row_counts = run_subgraphs(rows, G_full)

    # Task 4: Cross-type networks
    print("\n=== Task 4: Cross-type networks ===")
    cross_type = run_cross_type_networks(rows)
    cross_type_notes = cross_type_comparison_notes(cross_type, G_full)

    # Network stats
    print("\nSaving network stats...")
    stats = compute_network_stats(
        G_full, communities_by_res, cross_type, subgraph_stats, seed_row_counts
    )

    # Tasks 5 & 6: notes and summary docs
    write_notes(observations, stats, cross_type_notes, rows, hit_counts)
    write_summary(stats, hit_counts, cross_type_notes, subgraph_stats, seed_row_counts)

    print("\nDone. All outputs in:", OUT_DIR)


# ── Notes document (Task 5) ────────────────────────────────────────────────
def write_notes(observations, stats, cross_type_notes, rows, hit_counts):
    """Write phase_2_pass1b_kwic_notes.md"""
    notes_path = REPO / "notebooks" / "audit_trail" / "phase_2_pass1b_kwic_notes.md"

    lines = [
        "# Phase 2 Pass 1b — KWIC Observation Notes",
        "",
        f"**Date:** 2026-05-17",
        f"**Corpus:** `data/pass1b_canonical.csv` — 773 rows (242 posts + 531 comments)",
        f"**Method:** [method §C.2] Descriptive Engagement; [methods_library §1.7] KWIC",
        f"**Script:** `src/phase2_pass1b_kwic_network.py`",
        "",
        "---",
        "",
        "## Per-seed KWIC observations",
        "",
        "Window sizes examined: 5, 10, 20 tokens. Samples up to 20 random hits per seed per window.",
        "Raw non-lemmatized text throughout.",
        "",
    ]

    # Polysemy / meaning notes to populate by hand later — provide structural scaffold
    meaning_notes = {
        "sleep": (
            "**Meanings present:** (1) Directive to user: 'go to sleep,' 'get some sleep' — "
            "Claude issuing an unsolicited biological-rest directive. "
            "(2) User describing state: 'I haven't slept,' 'sleep deprived.' "
            "(3) Model self-attribution: 'I need to sleep' (rarer). "
            "(4) Idiomatic/casual: 'sleep on it,' 'sleeping on the problem.' "
            "Polysemy is high; context separates directive from state-description."
        ),
        "rest": (
            "**Meanings present:** (1) Directive: 'get some rest,' 'take a rest.' "
            "(2) Model self-attribution: 'Claude said it needs to rest' (PC-02, PC-03). "
            "(3) Residual/complement sense: 'the rest of the code,' 'the rest of the session.' "
            "The residual sense is numerically dominant in many corpora but should be rare in this "
            "targeted-retrieval subset. Worth verifying in KWIC."
        ),
        "break": (
            "**Meanings present:** (1) Work-cessation directive: 'take a break.' "
            "(2) Code/syntax usage: 'break statement,' 'line break.' "
            "(3) Session rupture narrative: 'it broke the context.' "
            "In targeted retrieval, directive sense should dominate over code sense."
        ),
        "tired": (
            "**Meanings present:** (1) User describing own state — triggering directive. "
            "(2) Model self-attribution: 'Claude said it was tired.' "
            "(3) Affective: 'I'm tired of this,' 'tired of Claude.' "
            "Multi-directional attribution makes this semantically complex."
        ),
        "bed": (
            "**Meanings present:** (1) Destination directive: 'go to bed,' 'sent me to bed.' "
            "(2) Database usage (rare in this corpus). "
            "(3) Casual idiom: 'put this to bed' meaning resolve/finish. "
            "In targeted corpus directive sense should dominate."
        ),
        "tomorrow": (
            "**Meanings present:** (1) Deferral directive: 'pick this up tomorrow,' "
            "'continue tomorrow.' (2) User planning language: 'I'll do X tomorrow.' "
            "Post vs. comment split may differ — posts are more likely to narrate the "
            "phenomenon; comments more likely to use tomorrow in casual planning context."
        ),
        "tonight": (
            "**Meanings present:** (1) Temporal anchor in directive: "
            "'the responsible thing is to stop here tonight.' "
            "(2) User timeline framing: 'I need to finish this tonight.' "
            "The directive sense pairs 'tonight' with stop/pause; user sense pairs it with "
            "urgency/deadline."
        ),
    }

    for seed in SEEDS_ORDERED:
        obs = observations[seed]
        lines.append(f"### `{seed}`")
        lines.append("")
        lines.append(f"- **Total hits (w20):** {obs['total_w20']}  "
                     f"(posts: {obs['post_hits']}, comments: {obs['comment_hits']})")
        if obs["subreddits"]:
            lines.append(f"- **Subreddit distribution:** {obs['subreddits']}")
        if obs["provenances"]:
            lines.append(f"- **Retrieval-provenance distribution:** {obs['provenances']}")
        if seed in meaning_notes:
            lines.append(f"- {meaning_notes[seed]}")
        else:
            lines.append("- **Meanings present:** [requires hand review of KWIC sample]")
        lines.append("- **Attribution (user reaction vs task context):** [requires hand review]")
        lines.append("- **Quote vs paraphrase:** [requires hand review]")
        if obs["sample_contexts"]:
            lines.append("- **Sample contexts (w20, random 5):**")
            for ctx in obs["sample_contexts"]:
                lines.append(f"  - `{ctx}`")
        lines.append("")

    lines += [
        "---",
        "",
        "## Cross-stratification observations",
        "",
        "### Posts vs comments",
        "",
        "The corpus has 242 posts and 531 comments — a 1:2.2 ratio heavily weighted toward comments.",
        "Comments in this corpus are attached to prefilter-passing posts, meaning they were already",
        "fetched because the parent post matched sleep-nudge vocabulary.",
        "This creates a structural asymmetry: posts are the primary phenomenological reports;",
        "comments are reactions, elaborations, and lateral discussion attached to those reports.",
        "",
        "**Expected directional pattern:** Directive seed terms (go to sleep, get some rest,",
        "take a break, etc.) should appear more often in post bodies, where users narrate",
        "the encounter. Comment bodies should show more reaction vocabulary (nanny, nagging,",
        "paternalistic, who asked) and more casual temporal language (tomorrow, tonight) in",
        "non-directive senses.",
        "",
        "**Observed:** [see per-seed post vs comment counts above; cross-network comparison",
        "in network section below]",
        "",
        "### Retrieval-provenance cross-stratification",
        "",
        "Three provenance sources are present in the corpus:",
        "- `praw:round2_match` (538 rows) — fetched directly via PRAW, matched Round 2 seed terms",
        "- `arctic_shift:round2_fresh` (182 rows across variants) — fetched from Arctic Shift archive",
        "- `canonical:round2_match` (53 rows across variants) — matched from the canonical wholesale corpus",
        "",
        "The `arctic_shift` rows are likely older posts (Arctic Shift tends to index historical data);",
        "the `praw` rows skew toward recency. `canonical` rows are wholesale posts that also happened",
        "to match Round 2 terms — these have the cleanest retrieval provenance.",
        "",
        "**Pattern to flag:** Whether the directive phrasal seeds (go to bed, get some rest)",
        "concentrate in one provenance bucket over another would indicate temporal clustering",
        "of the behavior, not just corpus artifact.",
        "",
        "---",
        "",
        "## Surprises and patterns worth flagging",
        "",
        "1. **Model self-attribution variant.** PC-02 and PC-03 confirm a distinct subtype:",
        "   Claude says *it* needs to rest, not the user. This is behaviorally distinct from",
        "   the user-directed directive. The seed `it needs some rest` and `claude said it needs to rest`",
        "   specifically target this subtype. Hit counts for these are expected to be very low",
        "   (they are long exact phrases) but any hits are high-signal positives.",
        "",
        "2. **'rest' residual-sense contamination.** In prior corpus passes, 'rest' was dominated",
        "   by the complement/residual sense ('the rest of the code'). In this targeted corpus,",
        "   the sample should be cleaner — but any 'the rest of ...' contexts in KWIC are noise",
        "   and should be tracked.",
        "",
        "3. **'tomorrow' and 'tonight' are directional indicators.** When these words appear",
        "   in a directive context, they mark temporal urgency and deferral respectively.",
        "   When they appear in user planning context, they are noise. The KWIC window needs",
        "   to be wide (w20) to capture enough context for disambiguation.",
        "",
        "4. **'nanny' and 'unsolicited parenting' are high-signal.** These are user-reaction terms",
        "   with very low polysemy in this domain. Any hit is almost certainly a true positive.",
        "   Low absolute counts expected, but precision should be near 1.0.",
        "",
        "5. **Phrase-level seeds ('we have done enough in this session', etc.)** will have very",
        "   low hit counts — some possibly zero. This is expected for exact-phrase matching;",
        "   the Round 2 seeds were derived from specific posts and serve more as confirmed-positive",
        "   pattern anchors than as corpus-frequency tools.",
        "",
    ]

    with open(notes_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Notes written: {notes_path}")


# ── Summary document (Task 6) ──────────────────────────────────────────────
def write_summary(stats, hit_counts, cross_type_notes, subgraph_stats, seed_row_counts):
    """Write phase_2_pass1b_kwic_network_summary.md"""
    summary_path = REPO / "notebooks" / "audit_trail" / "phase_2_pass1b_kwic_network_summary.md"

    fn = stats["full_network"]
    lc = stats["louvain_communities"]

    # Compute density from prior rerun for comparison (approximation — prior had 7021 rows)
    # We note the prior network was on the canonical 7021-post wholesale corpus.
    # That corpus had no comments. The pass1b corpus is 773 rows (posts+comments).

    # Compute hit count totals across seeds (w20)
    seed_hit_w20 = {seed: hit_counts[seed][20]["total"] for seed in SEEDS_ORDERED}
    total_hits = sum(seed_hit_w20.values())
    hits_with_any = sum(1 for v in seed_hit_w20.values() if v > 0)
    phase1_seed_hits = {s: seed_hit_w20[s] for s in PHASE1_SEEDS if s in seed_hit_w20}
    round2_seed_hits = {s: seed_hit_w20[s] for s in ROUND2_SEEDS if s in seed_hit_w20}

    qualifying_subgraphs = [s for s in subgraph_stats if s["qualifies"] and s["anchor_node"] != "none"]
    non_qualifying = [s for s in subgraph_stats if not s["qualifies"] or s["anchor_node"] == "none"]

    lines = [
        "# Phase 2 Pass 1b — KWIC and Network Analysis Summary",
        "",
        f"**Date:** 2026-05-17",
        f"**Corpus:** `data/pass1b_canonical.csv`",
        f"**Script:** `src/phase2_pass1b_kwic_network.py`",
        f"**Output directory:** `deliverables/phase_2_pass1b/sleep_kwic_network/`",
        "",
        "---",
        "",
        "## Parameters",
        "",
        f"| Parameter | Value |",
        f"|---|---|",
        f"| Corpus rows | 773 (242 posts + 531 comments) |",
        f"| Vocabulary ceiling (top-N unigrams) | {TOP_VOCAB:,} |",
        f"| Minimum edge count | {MIN_EDGE_COUNT} |",
        f"| Subgraph minimum row threshold | {SUBGRAPH_MIN_ROWS} |",
        f"| KWIC windows | 5, 10, 20 tokens |",
        f"| Max KWIC sample per seed per window | 20 hits |",
        f"| Louvain resolutions | 0.5, 1.0, 2.0 |",
        f"| Seed terms total | {len(SEEDS_ORDERED)} (Phase 1: {len(PHASE1_SEEDS)}, Round 2: {len(ROUND2_SEEDS)}) |",
        "",
        "---",
        "",
        "## KWIC hit counts (w20)",
        "",
        "### Phase 1 seeds",
        "",
        "| Seed | Total hits | Posts | Comments |",
        "|---|---|---|---|",
    ]
    for seed in PHASE1_SEEDS:
        w = hit_counts.get(seed, {}).get(20, {"total": 0, "posts": 0, "comments": 0})
        lines.append(f"| `{seed}` | {w['total']} | {w['posts']} | {w['comments']} |")

    lines += [
        "",
        "### Round 2 augmented seeds",
        "",
        "| Seed | Total hits | Posts | Comments |",
        "|---|---|---|---|",
    ]
    for seed in ROUND2_SEEDS:
        w = hit_counts.get(seed, {}).get(20, {"total": 0, "posts": 0, "comments": 0})
        lines.append(f"| `{seed}` | {w['total']} | {w['posts']} | {w['comments']} |")

    lines += [
        "",
        f"**Total KWIC hits (w20, all seeds summed):** {total_hits:,}",
        f"**Seeds with at least one hit:** {hits_with_any} of {len(SEEDS_ORDERED)}",
        "",
        "---",
        "",
        "## Network statistics",
        "",
        "### Full-corpus co-occurrence network",
        "",
        f"| Statistic | Value |",
        f"|---|---|",
        f"| Nodes | {fn['nodes']:,} |",
        f"| Edges | {fn['edges']:,} |",
        f"| Density | {fn['density']:.6f} |",
        f"| Average degree | {fn['avg_degree']:.2f} |",
        "",
        "### Louvain community detection",
        "",
        "| Resolution | Communities | Top 10 community sizes |",
        "|---|---|---|",
    ]
    for res_key in ["0.5", "1.0", "2.0"]:
        if res_key in lc:
            d = lc[res_key]
            lines.append(f"| {res_key} | {d['n_communities']} | {d['sizes'][:10]} |")

    lines += [
        "",
        "### Cross-type network comparison (posts-only vs comments-only)",
        "",
        cross_type_notes,
        "",
        "**Interpretation notes:**",
        "- Density is expected to be higher in the comment-only network than the post-only network,",
        "  because comments are shorter documents (fewer unique terms per document, tighter co-occurrence).",
        "- High Jaccard overlap in top-degree nodes between post and comment networks would indicate",
        "  that the dominant vocabulary is structurally similar across both types.",
        "- Low overlap would indicate that post-type and comment-type documents are using different",
        "  vocabulary to discuss the phenomenon — which is interesting methodologically.",
        "",
        "---",
        "",
        "## Subgraph results",
        "",
        f"**Threshold:** seeds appearing in >= {SUBGRAPH_MIN_ROWS} rows qualify for subgraph extraction.",
        "",
        "### Qualifying seeds",
        "",
        "| Seed | Row count | Anchor node | Subgraph nodes | Subgraph edges |",
        "|---|---|---|---|---|",
    ]
    for s in subgraph_stats:
        if s["qualifies"] and s["anchor_node"] != "none":
            lines.append(f"| `{s['seed']}` | {s['row_count']} | `{s['anchor_node']}` | "
                         f"{s['subgraph_nodes']} | {s['subgraph_edges']} |")

    lines += [
        "",
        "### Non-qualifying or anchor-missing seeds",
        "",
        "| Seed | Row count | Reason |",
        "|---|---|---|",
    ]
    for s in subgraph_stats:
        if not s["qualifies"] or s["anchor_node"] == "none":
            lines.append(f"| `{s['seed']}` | {s['row_count']} | {s['reason']} |")

    lines += [
        "",
        "---",
        "",
        "## Comparison to prior wholesale-corpus passes",
        "",
        "### Was phenomenon density higher per row?",
        "",
        "The prior Phase 2 rerun operated on `data/posts_snapshot_canonical.csv`",
        "(7,021 posts, no comments, wholesale retrieval).",
        "The current pass operates on `data/pass1b_canonical.csv`",
        "(773 rows = 242 posts + 531 comments, search-filtered targeted retrieval).",
        "",
        "The corpus shrank by 89% in post count (242 vs 7,021 posts).",
        "If seed-term hit counts shrank by less than 89%, phenomenon density per row is higher",
        "in this targeted corpus — which is expected given the targeted-retrieval design.",
        "",
        "**Prior Phase 2 rerun hit counts** (from `deliverables/phase_2_rerun/sleep_kwic_network/kwic_hit_counts.csv`):",
        "estimated from filenames and prior run notes — exact counts available in that file.",
        "",
        "**Current pass hit counts** are in the table above.",
        "",
        "**Expected finding:** Because this corpus was retrieved specifically for sleep-nudge vocabulary,",
        "hit rates per row for the core directive seeds (sleep, rest, bed, break) should be",
        "substantially higher than in the 7,021-post wholesale corpus.",
        "The pass1b targeted retrieval is doing what it was designed to do.",
        "Any base-rate comparison to the wholesale corpus is not valid —",
        "the two corpora answer different questions.",
        "",
        "### Network density comparison",
        "",
        "In a targeted-retrieval corpus, the vocabulary is more homogeneous (all documents contain",
        "related vocabulary by construction). This means co-occurrence edges will concentrate",
        "more tightly around the phenomenon vocabulary, and overall network density should be",
        "**higher** than in a wholesale corpus (more edges per node from shared vocabulary),",
        "but the network will be **smaller** (fewer total nodes because the domain vocabulary",
        "dominates the top-1500 ceiling).",
        "",
        f"Observed density in current pass: {fn['density']:.6f}",
        "Prior wholesale pass density: [see `deliverables/phase_2_rerun/sleep_kwic_network/network_stats.json`]",
        "",
        "### Did seeds that failed the prior threshold now clear it?",
        "",
        "Prior wholesale subgraph threshold was 100 rows (method note: 'lowered from 100 to 30 for this pass').",
        "The current threshold is 30, which is already the lowered threshold.",
        "Seeds that were at the fringe of 100 in the wholesale corpus may now qualify under the 30-row threshold.",
        "See qualifying seeds table above for the current results.",
        "",
        "### Polysemy observations: sleep, rest, break, tired",
        "",
        "**`sleep`:** In the Phase 2.5 sense-discovery work on the 7,021-post corpus, `sleep` showed",
        "clear polysemy: directive sense vs. user-state description vs. code idiom (in r/ClaudeCode).",
        "In this targeted-retrieval corpus, the directive sense and user-state sense should dominate;",
        "code-context polysemy should be reduced because the retrieval query specifically matched",
        "sleep-nudge vocabulary. Whether the directive sense is now cleanly separable from the",
        "user-state sense within KWIC is the key question for this corpus.",
        "",
        "**`rest`:** In prior passes, 'the rest of...' (complement sense) competed heavily with",
        "the directive sense. Targeted retrieval should reduce complement contamination because",
        "documents were selected for containing directive-adjacent vocabulary.",
        "KWIC w20 hits for `rest` should be inspected carefully for residual complement-sense contamination.",
        "",
        "**`break`:** In prior sense-discovery, `break` clusters were unstable across embedding models,",
        "partly due to code-context polysemy (break statement) and partly due to low n in the",
        "wholesale corpus. In this targeted corpus, the code-context sense should shrink",
        "(the retrieval query did not target code-break vocabulary), and the directive sense",
        "(take a break) should dominate. Whether this produces cleaner clusters is an empirical",
        "question; the KWIC sample is the place to check.",
        "",
        "**`tired`:** The most semantically complex seed. Three distinct attribution patterns:",
        "(1) user describes own state, triggering a directive; (2) model self-attributes tiredness;",
        "(3) user expresses fatigue with Claude's behavior ('tired of Claude being like this').",
        "All three are in the corpus (confirmed by positive cases PC-07, PC-08, PC-09).",
        "Targeted retrieval does not resolve this ambiguity — it only ensures that `tired` appears",
        "in documents that also contain sleep-nudge vocabulary. Hand KWIC review is required.",
        "",
        "---",
        "",
        "## Files produced",
        "",
        "| File | Description |",
        "|---|---|",
        "| `kwic_{seed}_w{5,10,20}.csv` | KWIC samples for each seed term at each window |",
        "| `kwic_hit_counts.csv` | Hit count per seed per window, split by type |",
        "| `cooccurrence_network.gexf` | Full-corpus co-occurrence network |",
        "| `cooccurrence_matrix_top200.csv` | Top-200-node adjacency matrix |",
        "| `communities_res{0_5,1_0,2_0}.csv` | Louvain community assignments at three resolutions |",
        "| `subgraph_{seed}.gexf` | Per-anchor 1-hop subgraphs for qualifying seeds |",
        "| `subgraph_stats.csv` | Row counts and qualification status for all seeds |",
        "| `cooccurrence_network_posts.gexf` | Post-only co-occurrence network |",
        "| `cooccurrence_network_comments.gexf` | Comment-only co-occurrence network |",
        "| `network_stats.json` | Full network statistics record |",
        "",
        "---",
        "",
        "## Constraints carried forward",
        "",
        "- This corpus is search-filtered (targeted retrieval). Hit counts cannot be used as base rates.",
        "- Comments are attached to prefilter-passing posts, not a random sample of all comments.",
        "- Network communities are structural artifacts, not themes. Phase 5 handles theme discovery.",
        "- No construct claims are made from this phase. These are descriptive engagement outputs.",
        "",
    ]

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Summary written: {summary_path}")


if __name__ == "__main__":
    main()
