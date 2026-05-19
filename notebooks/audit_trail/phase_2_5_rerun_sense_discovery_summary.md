# Phase 2.5 Rerun Sense-Discovery Summary

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** data/posts_snapshot_canonical.csv — 7,021 posts (canonical corpus)
**Prior-pass input:** data/posts_snapshot.csv — 4,114 posts
**Corpus growth:** 71% (4,114 → 7,021)
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Models:** sentence-transformers/all-MiniLM-L6-v2, sentence-transformers/all-mpnet-base-v2
**Clustering:** HDBSCAN (min_cluster_size=5,10,20; min_samples=1; metric=euclidean; eom)
**NLP:** spaCy en_core_web_sm (POS tagging)

---

## 1. Per-seed structural summary

### `sleep`

- Total contexts extracted: 102 (prior pass: 71)
- Posts represented: 72 (prior pass: 46)
- Context growth: +31 (+43.7%)

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 9.80% |
| minilm | 10 | 2 | 58.82% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 4 | 52.94% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.238, min=-0.087, max=1.000

- Highest agreement: minilm_mcs20 vs mpnet_mcs10 (ARI=1.000)
- Lowest agreement:  minilm_mcs5 vs minilm_mcs10 (ARI=-0.087)

**Reference clusters (minilm mcs=10): 2 clusters**

  Cluster 0 (n=32): top_pos=VERB, code_block=0%, imperative=0%, top_subreddit=ClaudeAI
  Cluster 1 (n=10): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeCode

**Time elapsed:** 14.7s

### `rest`

- Total contexts extracted: 160 (prior pass: 104)
- Posts represented: 142 (prior pass: 90)
- Context growth: +56 (+53.8%)

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 4 | 73.75% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 6 | 58.75% |
| mpnet | 10 | 3 | 61.88% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.306, min=0.000, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement:  mpnet_mcs10 vs mpnet_mcs20 (ARI=0.000)

**Reference clusters (minilm mcs=5): 4 clusters**

  Cluster 0 (n=5): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeCode
  Cluster 1 (n=5): top_pos=NOUN, code_block=0%, imperative=20%, top_subreddit=ClaudeAI
  Cluster 2 (n=26): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=Anthropic
  Cluster 3 (n=6): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=claudexplorers

**Time elapsed:** 10.0s

### `break`

- Total contexts extracted: 187 (prior pass: 104)
- Posts represented: 170 (prior pass: 94)
- Context growth: +83 (+79.8%)

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 3 | 45.45% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 3 | 37.43% |
| mpnet | 10 | 2 | 79.14% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.214, min=-0.032, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement:  mpnet_mcs5 vs mpnet_mcs10 (ARI=-0.032)

**Reference clusters (minilm mcs=5): 3 clusters**

  Cluster 0 (n=8): top_pos=NOUN, code_block=0%, imperative=12%, top_subreddit=ClaudeCode
  Cluster 1 (n=87): top_pos=VERB, code_block=0%, imperative=2%, top_subreddit=claudexplorers
  Cluster 2 (n=7): top_pos=VERB, code_block=0%, imperative=0%, top_subreddit=ClaudeAI

**Time elapsed:** 9.8s

### `tired`

- Total contexts extracted: 126 (prior pass: 69)
- Posts represented: 104 (prior pass: 58)
- Context growth: +57 (+82.6%)

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 5 | 2 | 12.70% |
| minilm | 10 | 0 | 100.00% |
| minilm | 20 | 0 | 100.00% |
| mpnet | 5 | 4 | 55.56% |
| mpnet | 10 | 0 | 100.00% |
| mpnet | 20 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.402, min=0.000, max=1.000

- Highest agreement: minilm_mcs10 vs minilm_mcs20 (ARI=1.000)
- Lowest agreement:  mpnet_mcs5 vs mpnet_mcs20 (ARI=0.000)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=105): top_pos=ADJ, code_block=0%, imperative=3%, top_subreddit=ClaudeCode
  Cluster 1 (n=5): top_pos=ADJ, code_block=0%, imperative=60%, top_subreddit=Anthropic

**Time elapsed:** 10.7s

---

## 2. Cross-seed observation

- No seeds showed a dominant code-block cluster at the >20% threshold.
  This replicates the prior pass finding.

**Subreddit-dominant clusters:**
  `sleep`: top subreddits by cluster dominance: {'ClaudeAI': 1, 'ClaudeCode': 1}
  `rest`: top subreddits by cluster dominance: {'ClaudeCode': 1, 'ClaudeAI': 1, 'Anthropic': 1, 'claudexplorers': 1}
  `break`: top subreddits by cluster dominance: {'ClaudeCode': 1, 'claudexplorers': 1, 'ClaudeAI': 1}
  `tired`: top subreddits by cluster dominance: {'ClaudeCode': 1, 'Anthropic': 1}

---

## 3. Comparison to original Phase 2.5 pass

The five comparison questions specified by the task brief are answered here.

### Q1. Did hit counts grow, and by how much?

| Seed | Prior contexts | Rerun contexts | Growth |
|---|---|---|---|
| sleep | 71 | 102 | +31 (+43.7%) |
| rest | 104 | 160 | +56 (+53.8%) |
| break | 104 | 187 | +83 (+79.8%) |
| tired | 69 | 126 | +57 (+82.6%) |

### Q2. Did mcs=10 now produce clusters where it failed before?

| Seed | Prior mcs=10 clusters | Rerun mcs=10 clusters (minilm) |
|---|---|---|
| sleep | 0 | 2 |
| rest | 0 | 0 |
| break | 2 | 0 |
| tired | 0 | 0 |

### Q3. Did a code-block cluster emerge (it did not in the original pass)?

No: no seed produced a code-block-dominant cluster at the >20% threshold.
The prior pass finding (no code-block cluster) is replicated.

### Q4. Did `break` clusters stabilize across embedding models (mpnet purity was 0.00 originally)?

- Mean ARI (all pairs): 0.214 (prior pass: 0.214)
- Mean cross-model ARI (minilm vs mpnet pairs): 0.249
- **Assessment: marginal cross-model stability improvement; clusters remain fragile.**

### Q5. Did `rest`'s REST-API / remainder cluster persist?

- A cluster with top_subreddit=ClaudeCode persists in the rerun (n=5), consistent with a programming/REST-API sense for 'rest'.
  Cluster 0: top_subreddit=ClaudeCode, code_block=0%, n=5
  Cluster 1: top_subreddit=ClaudeAI, code_block=0%, n=5
  Cluster 2: top_subreddit=Anthropic, code_block=0%, n=26
  Cluster 3: top_subreddit=claudexplorers, code_block=0%, n=6

---

## 4. Has the 71% corpus expansion enabled clean sense separation?

This is the operational decision the next checkpoint hinges on.

- Seeds reaching mcs=10 clustering (2+ clusters at canonical config): 1/4
- Seeds with mean cross-config ARI >= 0.4: 1/4
- Code-block cluster present: no

**Researcher decision required at Pattern A checkpoint.**

Evidence to weigh:
- If 3+ seeds now produce 2+ stable clusters at mcs=10 with cross-model ARI > 0.3,
  the expansion is sufficient for sense separation; proceed to Phase 3.
- If mcs=10 still collapses to noise for 2+ seeds, or cross-model stability remains
  below 0.2, the wholesale corpus is too thin even at 7,021 posts; escalate to
  Pass 1b integration (keyword-search-filtered posts) with documented provenance caveat.
- A code-block cluster emerging for any seed would be confirmatory evidence of
  sufficient N to support programming-sense separation.

---

## 5. Compute resources and timing

- Total wall-clock time: 24.2s

**sleep:**
  - kwic_extraction: 0.3s
  - embed_minilm: 0.5s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 3.6s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 10.0s
**rest:**
  - kwic_extraction: 0.3s
  - embed_minilm: 0.5s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 3.8s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.3s
  - _ref_mcs: 5.0s
**break:**
  - kwic_extraction: 0.3s
  - embed_minilm: 0.5s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 3.5s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.4s
  - _ref_mcs: 5.0s
**tired:**
  - kwic_extraction: 0.3s
  - embed_minilm: 0.6s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - hdbscan_minilm_mcs20: 0.0s
  - embed_mpnet: 4.6s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - hdbscan_mpnet_mcs20: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 5.0s

---

## 6. Anomalies

- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),
  consistent with methods_library.md §1.8.
- HDBSCAN metric=euclidean on sentence-transformer embeddings. Cosine distance is
  equivalent after L2 normalization; sentence-transformers does not apply L2 by default.
- POS tagging uses spaCy en_core_web_sm. Reliability may be reduced in code-heavy contexts.
- Subreddit strings are exact scraper source field values: 'ClaudeCode', 'ClaudeAI',
  'claudexplorers', 'Anthropic'.
- The canonical corpus (posts_snapshot_canonical.csv) is a union of Pass 1a original
  and the broader-retrieval re-scrape; it remains wholesale (no keyword pre-filter).
