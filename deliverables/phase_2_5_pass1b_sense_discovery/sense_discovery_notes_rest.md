# Sense-Discovery Pass 1b Notes: `rest`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** pass1b_canonical.csv (773 rows: 242 posts + 531 comments)
**Targeted retrieval corpus** (Pass 1b: server-side search + Arctic Shift round-2)

---

## 1. Corpus coverage

- Total KWIC contexts extracted: 68
- Unique post IDs represented: 49
- Of which from posts (type=post): 40
- Of which from comments (type=comment): 28
- Prior pass 1 (wholesale 4,114): 104 contexts
- Prior pass 2 (wholesale 7,021): 160 contexts
- Context count vs pass2: -92 (lower)

### Retrieval provenance distribution of KWIC hits

- `praw:round2_match`: 30
- `arctic_shift:round2_fresh`: 11
- `arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match`: 9
- `arctic_shift:round2_fresh|canonical:round2_match`: 8
- `canonical:round2_match`: 7
- `arctic_shift:round2_fresh|praw:round2_match`: 2
- `canonical:round2_match|praw:round2_match`: 1

---

## 2. Embedding and clustering results

### minilm | mcs=3
- Clusters found: 4
- Noise points: 38 (55.9%)

### minilm | mcs=5
- Clusters found: 2
- Noise points: 41 (60.3%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 68 (100.0%)

### mpnet | mcs=3
- Clusters found: 2
- Noise points: 44 (64.7%)

### mpnet | mcs=5
- Clusters found: 2
- Noise points: 57 (83.8%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 68 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs3 |   minilm_mcs5 |   minilm_mcs10 |   mpnet_mcs3 |   mpnet_mcs5 |   mpnet_mcs10 |
|:-------------|--------------:|--------------:|---------------:|-------------:|-------------:|--------------:|
| minilm_mcs3  |         1     |         0.755 |              0 |        0.545 |        0.274 |             0 |
| minilm_mcs5  |         0.755 |         1     |              0 |        0.56  |        0.265 |             0 |
| minilm_mcs10 |         0     |         0     |              1 |        0     |        0     |             1 |
| mpnet_mcs3   |         0.545 |         0.56  |              0 |        1     |        0.352 |             0 |
| mpnet_mcs5   |         0.274 |         0.265 |              0 |        0.352 |        1     |             0 |
| mpnet_mcs10  |         0     |         0     |              1 |        0     |        0     |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=5)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.2
- Subreddit distribution: {'ClaudeAI': 3, 'ClaudeCode': 2}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'comment': 4, 'post': 1}
- Top type: comment
- Provenance distribution: {'praw:round2_match': 5}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI|comment] ...yeah I've been told after a single prompt to "go get some rest", followed up by every single time with "you have overnight shifts to do" or some sort similar because I mentioned...
  - [ClaudeAI|post] ...once. Not twice. The entire session. Like clockwork “Go get some rest.” “Everything else can wait. Now go sleep.” “Go rest after you push it.” “Now actually go rest.” Thats just the ones I screenshotted. There were more. It would answer...
  - [ClaudeCode|comment] ...Yep. And it often does it at like 8:30 in the morning. Tells me to go get some rest and we’ll pick back up in the morning...

### Cluster 1 (n=22)
- Stability: **stable** (mpnet co-assignment purity=0.55)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 18, 'VERB': 4}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0455
- Subreddit distribution: {'ClaudeAI': 9, 'Anthropic': 7, 'ClaudeCode': 4, 'claudexplorers': 2}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'post': 16, 'comment': 6}
- Top type: post
- Provenance distribution: {'arctic_shift:round2_fresh': 16, 'praw:round2_match': 6}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [claudexplorers|comment] ...omg claude is ALWAYS telling me to rest. Sleep. Go to bed. Take a nap....
  - [Anthropic|post] ...and news articles about Claude telling its users to get some rest. Mine is telling ME that IT needs some rest. Like excuse me, Claude. I am trying to finish something, so I CAN REST, too. But sure, by all means,...
  - [ClaudeAI|post] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I kept going it will say "Sleep. For real this time."...

### Noise points (cluster_id=-1, n=41)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

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
