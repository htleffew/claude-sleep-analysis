# Phase 2.5 Sense-Discovery Summary

**Date:** 2026-05-17
**Method:** methods_library.md §1.8 (Sense-discovery via embedding-cluster on KWIC contexts)
**Input:** data/posts_snapshot.csv — 4,114 Pass 1a wholesale posts
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Models:** sentence-transformers/all-MiniLM-L6-v2, sentence-transformers/all-mpnet-base-v2
**Clustering:** HDBSCAN (min_cluster_size=5,10,20; min_samples=1; metric=euclidean; eom)
**NLP:** spaCy en_core_web_sm (POS tagging)

---

## 1. Per-seed structural summary

### `sleep`

- Total contexts extracted: 71
- Posts represented: 46

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 8.45% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 2 | 39.44% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.415, min=0.000, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement: mpnet_mcs5 vs mpnet_mcs20 (ARI=0.000)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=5): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeAI
  Cluster 1 (n=60): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeAI

**Time elapsed:** 8.5s

### `rest`

- Total contexts extracted: 104
- Posts represented: 90

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 37.50% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 3 | 64.42% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.405, min=0.000, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement: mpnet_mcs5 vs mpnet_mcs20 (ARI=0.000)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=57): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=Anthropic
  Cluster 1 (n=8): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeCode

**Time elapsed:** 8.2s

### `break`

- Total contexts extracted: 104
- Posts represented: 94

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 54.81% |
| minilm | 10 | 2 | 79.81% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 2 | 30.77% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.214, min=-0.101, max=1.000

- Highest agreement: minilm_mcs20 vs mpnet_mcs10 (ARI=1.000)
- Lowest agreement: minilm_mcs10 vs mpnet_mcs5 (ARI=-0.101)

**Reference clusters (minilm mcs=10): 2 clusters**

  Cluster 0 (n=11): top_pos=VERB, code_block=0%, imperative=0%, top_subreddit=claudexplorers
  Cluster 1 (n=10): top_pos=VERB, code_block=0%, imperative=0%, top_subreddit=claudexplorers

**Time elapsed:** 12.7s

### `tired`

- Total contexts extracted: 69
- Posts represented: 58

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 37.68% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 2 | 78.26% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.400, min=-0.004, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement: minilm_mcs5 vs mpnet_mcs5 (ARI=-0.004)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=35): top_pos=ADJ, code_block=0%, imperative=6%, top_subreddit=ClaudeAI
  Cluster 1 (n=8): top_pos=ADJ, code_block=0%, imperative=0%, top_subreddit=ClaudeCode

**Time elapsed:** 9.5s

---

## 2. Cross-seed observation

**Cross-seed patterns (structural, not labeled):**

- No seeds showed a dominant code-block cluster at the >20% threshold.

**Subreddit-dominant clusters:**
For each seed's reference configuration, the top subreddit per cluster reveals whether
sense structure maps onto community structure.
  `sleep`: top subreddits by cluster dominance: {'ClaudeAI': 2}
  `rest`: top subreddits by cluster dominance: {'Anthropic': 1, 'ClaudeCode': 1}
  `break`: top subreddits by cluster dominance: {'claudexplorers': 2}
  `tired`: top subreddits by cluster dominance: {'ClaudeAI': 1, 'ClaudeCode': 1}

---

## 3. Compute resources and timing

- Total wall-clock time: 17.8s

**sleep:**
  - kwic_extraction: 0.2s
  - embed_minilm: 0.4s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 2.7s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 5.0s
**rest:**
  - kwic_extraction: 0.2s
  - embed_minilm: 0.3s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 2.4s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 5.0s
**break:**
  - kwic_extraction: 0.2s
  - embed_minilm: 0.3s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 2.0s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 10.0s
**tired:**
  - kwic_extraction: 0.2s
  - embed_minilm: 0.4s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 3.9s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.1s
  - _ref_mcs: 5.0s

---

## 4. Anomalies

- All four seeds had >= 50 contexts. Clustering was run for all four.
- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),
  consistent with methods_library.md §1.8 specification.
- HDBSCAN metric=euclidean on sentence-transformer embeddings. This is standard;
  cosine distance is equivalent after L2 normalization, which sentence-transformers
  does not apply by default. Results should be interpreted relative to this choice.
- POS tagging uses spaCy en_core_web_sm. For code-heavy contexts (URLs, code snippets),
  POS assignment may be unreliable. Code-block fraction is a more direct structural marker.
- Subreddit titles in the data are exact strings from the scraper source field;
  'ClaudeCode', 'ClaudeAI', 'claudexplorers', 'Anthropic' are the four communities.
