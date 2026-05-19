# Sense-Discovery Rerun Notes: `tired`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot_canonical.csv (7,021 posts)
**Prior pass input:** posts_snapshot.csv (4,114 posts)

---

## 1. Corpus coverage

- Total contexts extracted: 126
- Total posts represented: 104
- Prior pass: 69 contexts from 58 posts
- Growth: +57 contexts (+82.6%)

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 16 (12.7%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 126 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 126 (100.0%)

### mpnet | mcs=5
- Clusters found: 4
- Noise points: 70 (55.6%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 126 (100.0%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 126 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |              0 |              0 |        0.035 |             0 |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |             1 |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |         0.035 |              0 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
  (mcs=10 produced no clusters; mcs=5 used as fallback reference)
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=105)
- Stability: **stable** (mpnet co-assignment purity=0.78)
- Top POS of seed token: ADJ
- POS distribution: {'ADJ': 104, 'PROPN': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0286
- Subreddit distribution: {'ClaudeCode': 41, 'ClaudeAI': 34, 'claudexplorers': 19, 'Anthropic': 11}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...anyone else feel like coding with claude is basically having a super smart pair programmer who never gets tired :D okay so ive been seeing all this drama about claude getting nerfed and people complaining about lazy responses but...
  - [ClaudeCode] ...I got tired of Claude Code silently dying at rate limits during mid task, so I built something I got tired of Claude...
  - [ClaudeAI] ...I'm an AI Dev who got tired of typing 3,000+ words/day to Claude, so Claude and I built a voice extension together. No code written by me....

### Cluster 1 (n=5)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: ADJ
- POS distribution: {'ADJ': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.6
- Subreddit distribution: {'Anthropic': 5}
- Top subreddit: Anthropic

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [Anthropic] ...of the pack and you burned it almost instantaneously. I am just so... tired. Tired of corporations doing this shit. Tired of being lied to, tired of never trusting a product, tired of being permanently in an adversarial relationship with every...
  - [Anthropic] ...things you had above the rest of the pack and you burned it almost instantaneously. I am just so... tired. Tired of corporations doing this shit. Tired of being lied to, tired of never trusting a product, tired of being permanently...
  - [Anthropic] ...only things you had above the rest of the pack and you burned it almost instantaneously. I am just so... tired. Tired of corporations doing this shit. Tired of being lied to, tired of never trusting a product, tired of being...

### Noise points (cluster_id=-1, n=16)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

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
