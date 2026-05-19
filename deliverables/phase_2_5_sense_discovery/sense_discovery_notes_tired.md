# Sense-Discovery Notes: `tired`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot.csv (4,114 Pass 1a wholesale posts)

---

## 1. Corpus coverage

- Total contexts extracted: 69
- Total posts represented: 58

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 26 (37.7%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 69 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 69 (100.0%)

### mpnet | mcs=5
- Clusters found: 2
- Noise points: 54 (78.3%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 69 (100.0%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 69 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |              0 |              0 |       -0.004 |             0 |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |             1 |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |        -0.004 |              0 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
  (mcs=10 produced no clusters; mcs=5 used as fallback reference)
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=35)
- Stability: **stable** (mpnet co-assignment purity=0.67)
- Top POS of seed token: ADJ
- POS distribution: {'ADJ': 35}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0571
- Subreddit distribution: {'ClaudeAI': 12, 'ClaudeCode': 12, 'claudexplorers': 8, 'Anthropic': 3}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...I got tired of Claude Code silently dying at rate limits during mid task, so I built something I got tired of Claude...
  - [claudexplorers] ...at this thing." Claude, "Yes, but also you are tired GO TAKE A BREAK NOW." Never tell Claude you are tired for any reason, Claude won't let it go!...
  - [claudexplorers] ...say, what's up?" Me, "I was wondering if we could look at this thing." Claude, "Yes, but also you are tired GO TAKE A BREAK NOW." Never tell Claude you are tired for any reason, Claude won't let it go!...

### Cluster 1 (n=8)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: ADJ
- POS distribution: {'ADJ': 8}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeCode': 6, 'ClaudeAI': 1, 'Anthropic': 1}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...it built 4 new tools I didn't even ask for I’ve been obsessed with autonomous agents lately, but I got tired of them hitting walls because they didn't have the right "tools" or because their context window turned to mush after...
  - [ClaudeCode] ...I Built a Persistent "Third Brain" with 16 Production-Ready Claude code Agent Skills Hey [r/SideProject](https://www.reddit.com/r/SideProject/),I got tired of AI chats being one-off — knowledge disappearing after every conversation.So I built Third Brain V5: a set of 16...
  - [ClaudeCode] ...I Built a Persistent "Third Brain" with 16 Production-Ready Claude Agent Skills Hey [r/SideProject](https://www.reddit.com/r/SideProject/),I got tired of AI chats being one-off — knowledge disappearing after every conversation.So I built Third Brain V5: a set of 16...

### Noise points (cluster_id=-1, n=26)
- These contexts did not fit any cluster under minilm mcs=10.

---

## 5. Compute resources

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
