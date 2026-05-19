# Phase 2.5 Pass 1b Sense-Discovery Summary

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** data/pass1b_canonical.csv — 773 rows (242 posts + 531 comments)
**Corpus type:** Targeted retrieval (Pass 1b: server-side search + Arctic Shift round-2)
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Models:** sentence-transformers/all-MiniLM-L6-v2, sentence-transformers/all-mpnet-base-v2
**Clustering:** HDBSCAN (min_cluster_size=3,5,10; min_samples=1; metric=euclidean; eom)
**Canonical config:** MiniLM + mcs=5
**NLP:** spaCy en_core_web_sm (POS tagging)

---

## 1. Per-seed structural summary

### `sleep`

- Total contexts extracted: 236
- Prior pass 1 (wholesale 4,114): 71
- Prior pass 2 (wholesale 7,021): 102
- Of which: 104 from posts, 132 from comments

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 3 | 2 | 5.08% |
| minilm | 5 | 3 | 31.36% |
| minilm | 10 | 2 | 61.02% |
| mpnet | 3 | 4 | 18.64% |
| mpnet | 5 | 3 | 19.92% |
| mpnet | 10 | 2 | 54.24% |

**Stability (ARI, all config pairs):** mean=0.214, min=-0.048, max=0.990

- Highest agreement: mpnet_mcs3 vs mpnet_mcs5 (ARI=0.990)
- Lowest agreement: minilm_mcs3 vs minilm_mcs10 (ARI=-0.048)

**Reference clusters (minilm mcs=5): 3 clusters**

  Cluster 0 (n=7): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=claudexplorers, top_type=comment, type_dist={'comment': 6, 'post': 1}
  Cluster 1 (n=150): top_pos=NOUN, code_block=0%, imperative=7%, top_subreddit=ClaudeAI, top_type=comment, type_dist={'comment': 81, 'post': 69}
  Cluster 2 (n=5): top_pos=NOUN, code_block=0%, imperative=20%, top_subreddit=ClaudeAI, top_type=comment, type_dist={'comment': 5}

**Time elapsed:** 7.2s

### `rest`

- Total contexts extracted: 68
- Prior pass 1 (wholesale 4,114): 104
- Prior pass 2 (wholesale 7,021): 160
- Of which: 40 from posts, 28 from comments

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 3 | 4 | 55.88% |
| minilm | 5 | 2 | 60.29% |
| minilm | 10 | 0 | 100.00% |
| mpnet | 3 | 2 | 64.71% |
| mpnet | 5 | 2 | 83.82% |
| mpnet | 10 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.250, min=0.000, max=1.000

- Highest agreement: minilm_mcs10 vs mpnet_mcs10 (ARI=1.000)
- Lowest agreement: mpnet_mcs5 vs mpnet_mcs10 (ARI=0.000)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=5): top_pos=NOUN, code_block=0%, imperative=20%, top_subreddit=ClaudeAI, top_type=comment, type_dist={'comment': 4, 'post': 1}
  Cluster 1 (n=22): top_pos=NOUN, code_block=0%, imperative=5%, top_subreddit=ClaudeAI, top_type=post, type_dist={'post': 16, 'comment': 6}

**Time elapsed:** 3.2s

### `break`

- Total contexts extracted: 105
- Prior pass 1 (wholesale 4,114): 104
- Prior pass 2 (wholesale 7,021): 187
- Of which: 54 from posts, 51 from comments

**Cluster counts by configuration:**

| Model | mcs | Clusters | Noise fraction |
|---|---|---|---|
| minilm | 3 | 2 | 62.86% |
| minilm | 5 | 2 | 62.86% |
| minilm | 10 | 0 | 100.00% |
| mpnet | 3 | 4 | 11.43% |
| mpnet | 5 | 0 | 100.00% |
| mpnet | 10 | 0 | 100.00% |

**Stability (ARI, all config pairs):** mean=0.253, min=-0.099, max=1.000

- Highest agreement: minilm_mcs3 vs minilm_mcs5 (ARI=1.000)
- Lowest agreement: minilm_mcs5 vs mpnet_mcs3 (ARI=-0.099)

**Reference clusters (minilm mcs=5): 2 clusters**

  Cluster 0 (n=34): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeAI, top_type=comment, type_dist={'comment': 20, 'post': 14}
  Cluster 1 (n=5): top_pos=NOUN, code_block=0%, imperative=0%, top_subreddit=ClaudeAI, top_type=comment, type_dist={'comment': 3, 'post': 2}

**Time elapsed:** 2.6s

### `tired`

- Total contexts extracted: 41
- Prior pass 1 (wholesale 4,114): 69
- Prior pass 2 (wholesale 7,021): 126
- Of which: 20 from posts, 21 from comments
- **Below clustering floor (<50 contexts). Not clustered.**

---

## 2. Cross-seed observation

- No seeds showed a dominant code-block cluster (>20% threshold).
  Replicates both prior wholesale passes.

**Subreddit-dominant clusters:**
  `sleep`: {'ClaudeAI': 2, 'claudexplorers': 1}
  `rest`: {'ClaudeAI': 2}
  `break`: {'ClaudeAI': 2}

**Post vs comment distribution across clusters:**
  `sleep`:
    Cluster 0: {'comment': 6, 'post': 1}
    Cluster 1: {'comment': 81, 'post': 69}
    Cluster 2: {'comment': 5}
  `rest`:
    Cluster 0: {'comment': 4, 'post': 1}
    Cluster 1: {'post': 16, 'comment': 6}
  `break`:
    Cluster 0: {'comment': 20, 'post': 14}
    Cluster 1: {'comment': 3, 'post': 2}

---

## 3. Comparison to both prior Phase 2.5 passes

The operational questions specified by the task brief are answered here.

### Q1. Did hit counts grow per seed even though total corpus shrank from 7,021 to 773 rows?

| Seed | Pass 1 (4,114 posts) | Pass 2 (7,021 posts) | Pass 1b (773 rows) | vs Pass 2 |
|---|---|---|---|---|
| sleep | 71 | 102 | 236 | +134 (higher) |
| rest | 104 | 160 | 68 | -92 (lower) |
| break | 104 | 187 | 105 | -82 (lower) |
| tired | 69 | 126 | 41 | -85 (lower) |

### Q2. Did mcs=5 now produce clusters where prior passes struggled at mcs=5?

| Seed | Pass 1 mcs=5 clusters | Pass 2 mcs=5 clusters | Pass 1b mcs=5 clusters |
|---|---|---|---|
| sleep | 2 | 2 | 3 |
| rest | 2 | 4 | 2 |
| break | 2 | 3 | 2 |
| tired | 2 | 2 | n/a (below floor) |

### Q3. Did the programming/code-context cluster finally separate (it did not in either wholesale pass)?

No: no seed produced a code-block-dominant cluster at the >20% threshold.
This replicates both prior wholesale passes. Note: code-block presence alone may not
be the discriminating feature of programming contexts in this corpus (subreddit may be more discriminating).

### Q4. Did `break` clusters stabilize across embedding models?
(In pass 1, mpnet purity was 0.00; in pass 2, mean ARI was 0.214.)

- Pass 1b mean ARI (all pairs): 0.253
- Pass 1b mean cross-model ARI: 0.200
- Pass 2 mean ARI: 0.214; pass 2 cross-model ARI: 0.249
- **Assessment: minimal improvement. Targeted retrieval did not substantially help `break`.**

### Q5. Did the model-self-attribution sense of `tired` materialize as its own cluster?
(Flagged in wholesale canonical Phase 2 KWIC but did not form a stable cluster in pass 2.)

- `tired` below floor or no cluster data.

---

## 4. Has targeted retrieval enabled clean sense separation that wholesale at any scale could not?

This is the central operational question.

- Seeds above clustering floor: 3/4
- Seeds with 2+ clusters at canonical config (minilm mcs=5): 3/3
- Seeds with mean ARI >= 0.40 (cross-config stability): 0/3
- Code-block cluster materialized: no

**Per-seed assessment vs prior wholesale runs:**

| Seed | Pass 1 clusters | Pass 2 clusters | Pass 1b clusters | Stability change | Assessment |
|---|---|---|---|---|---|
| sleep | 2 | 2 | 3 | stable (0.214 vs 0.238) | no clear improvement |
| rest | 2 | 4 | 2 | degraded (0.250 vs 0.306) | no clear improvement |
| break | 2 | 3 | 2 | stable (0.253 vs 0.214) | no clear improvement |
| tired | 2 | 2 | below floor | — | insufficient |

**Researcher decision required at Pattern A checkpoint.**

---

## 5. Compute resources and timing

- Total wall-clock time: 17.3s

**sleep:**
  - kwic_extraction: 0.0s
  - embed_minilm: 0.9s
  - hdbscan_minilm_mcs3: 0.0s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - embed_mpnet: 5.8s
  - hdbscan_mpnet_mcs3: 0.0s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.4s
  - _ref_mcs: 5.0s
**rest:**
  - kwic_extraction: 0.0s
  - embed_minilm: 0.4s
  - hdbscan_minilm_mcs3: 0.0s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - embed_mpnet: 2.6s
  - hdbscan_mpnet_mcs3: 0.0s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.1s
  - _ref_mcs: 5.0s
**break:**
  - kwic_extraction: 0.0s
  - embed_minilm: 0.3s
  - hdbscan_minilm_mcs3: 0.0s
  - hdbscan_minilm_mcs5: 0.0s
  - hdbscan_minilm_mcs10: 0.0s
  - embed_mpnet: 2.2s
  - hdbscan_mpnet_mcs3: 0.0s
  - hdbscan_mpnet_mcs5: 0.0s
  - hdbscan_mpnet_mcs10: 0.0s
  - stability: 0.0s
  - exemplars: 0.0s
  - syntactic: 0.2s
  - _ref_mcs: 5.0s
**tired:**
  - kwic_extraction: 0.0s

---

## 6. Anomalies and methodological notes

- KWIC window is ±20 raw whitespace tokens (no lemmatization, stop-words preserved),
  consistent with methods_library.md §1.8.
- mcs settings lowered to 3,5,10 (from 5,10,20) per task brief for smaller corpus.
- HDBSCAN metric=euclidean on sentence-transformer embeddings.
- POS tagging uses spaCy en_core_web_sm. Reliability may be reduced in code-heavy contexts.
- Pass 1b includes both posts and comments; prior passes were posts-only.
  Comments inflate KWIC context counts; cross-pass count comparisons must account for this.
- retrieval_provenance field reflects Arctic Shift round-2 and PRAW round-2 retrieval paths.
- No sense labels assigned. Labeling is a researcher decision at the Pattern A checkpoint.
