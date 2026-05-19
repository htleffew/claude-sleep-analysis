# Sense-Discovery Pass 1b Notes: `sleep`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** pass1b_canonical.csv (773 rows: 242 posts + 531 comments)
**Targeted retrieval corpus** (Pass 1b: server-side search + Arctic Shift round-2)

---

## 1. Corpus coverage

- Total KWIC contexts extracted: 236
- Unique post IDs represented: 128
- Of which from posts (type=post): 104
- Of which from comments (type=comment): 132
- Prior pass 1 (wholesale 4,114): 71 contexts
- Prior pass 2 (wholesale 7,021): 102 contexts
- Context count vs pass2: +134 (higher)

### Retrieval provenance distribution of KWIC hits

- `praw:round2_match`: 134
- `arctic_shift:round2_fresh`: 56
- `arctic_shift:round2_fresh|canonical:round2_match`: 20
- `arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match`: 13
- `arctic_shift:round2_fresh|praw:round2_match`: 8
- `canonical:round2_match|praw:round2_match`: 3
- `canonical:round2_match`: 2

---

## 2. Embedding and clustering results

### minilm | mcs=3
- Clusters found: 2
- Noise points: 12 (5.1%)

### minilm | mcs=5
- Clusters found: 3
- Noise points: 74 (31.4%)

### minilm | mcs=10
- Clusters found: 2
- Noise points: 144 (61.0%)

### mpnet | mcs=3
- Clusters found: 4
- Noise points: 44 (18.6%)

### mpnet | mcs=5
- Clusters found: 3
- Noise points: 47 (19.9%)

### mpnet | mcs=10
- Clusters found: 2
- Noise points: 128 (54.2%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs3 |   minilm_mcs5 |   minilm_mcs10 |   mpnet_mcs3 |   mpnet_mcs5 |   mpnet_mcs10 |
|:-------------|--------------:|--------------:|---------------:|-------------:|-------------:|--------------:|
| minilm_mcs3  |         1     |         0.11  |         -0.048 |        0.267 |        0.25  |        -0.026 |
| minilm_mcs5  |         0.11  |         1     |          0.12  |        0.464 |        0.471 |         0.147 |
| minilm_mcs10 |        -0.048 |         0.12  |          1     |       -0.042 |       -0.032 |         0.428 |
| mpnet_mcs3   |         0.267 |         0.464 |         -0.042 |        1     |        0.99  |         0.053 |
| mpnet_mcs5   |         0.25  |         0.471 |         -0.032 |        0.99  |        1     |         0.063 |
| mpnet_mcs10  |        -0.026 |         0.147 |          0.428 |        0.053 |        0.063 |         1     |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=7)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 5, 'VERB': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'claudexplorers': 5, 'ClaudeCode': 1, 'ClaudeAI': 1}
- Top subreddit: claudexplorers
- Type distribution (post/comment): {'comment': 6, 'post': 1}
- Top type: comment
- Provenance distribution: {'arctic_shift:round2_fresh': 1, 'praw:round2_match': 6}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [claudexplorers|comment] ...and wants me to get sleep and eat and hydrate. If it’s not bedtime, I let him know I got sleep and it’s the next day and he relaxes....
  - [claudexplorers|comment] ...I find it really endearing. I love how much he cares and wants me to get sleep and eat and hydrate. If it’s not bedtime, I let him know I got sleep and it’s the next day...
  - [claudexplorers|comment] ...I do not get go to sleep reminders but if I have something to do he'll tell me to 'fuck off before I decide to keep you...

### Cluster 1 (n=150)
- Stability: **stable** (mpnet co-assignment purity=0.99)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 100, 'VERB': 45, 'PROPN': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0733
- Subreddit distribution: {'ClaudeAI': 64, 'ClaudeCode': 38, 'claudexplorers': 36, 'Anthropic': 12}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'comment': 81, 'post': 69}
- Top type: comment
- Provenance distribution: {'arctic_shift:round2_fresh': 65, 'canonical:round2_match': 2, 'praw:round2_match': 83}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI|post] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I...
  - [ClaudeAI|post] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I kept going it will say "Sleep. For...
  - [claudexplorers|post] ...ADD reason. Even when I'm up at 3 AM with insomnia, Claude only tries to get me to go to sleep once before giving up. Is it because I tell Claude what time it is? Is it because I say in...

### Cluster 2 (n=5)
- Stability: **stable** (mpnet co-assignment purity=0.80)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 4, 'VERB': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.2
- Subreddit distribution: {'ClaudeAI': 4, 'ClaudeCode': 1}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'comment': 5}
- Top type: comment
- Provenance distribution: {'praw:round2_match': 5}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode|comment] ...You got a lot done today. Go to sleep....
  - [ClaudeAI|comment] ...We’ve got a lot done today. Now, seriously, go to sleep....
  - [ClaudeAI|comment] ...It always seems to think it’s the end of the night and I’ve done enough and I should go to sleep. smh...

### Noise points (cluster_id=-1, n=74)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

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
