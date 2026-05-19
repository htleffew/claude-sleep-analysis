# Sense-Discovery Pass 1b Notes: `break`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** pass1b_canonical.csv (773 rows: 242 posts + 531 comments)
**Targeted retrieval corpus** (Pass 1b: server-side search + Arctic Shift round-2)

---

## 1. Corpus coverage

- Total KWIC contexts extracted: 105
- Unique post IDs represented: 90
- Of which from posts (type=post): 54
- Of which from comments (type=comment): 51
- Prior pass 1 (wholesale 4,114): 104 contexts
- Prior pass 2 (wholesale 7,021): 187 contexts
- Context count vs pass2: -82 (lower)

### Retrieval provenance distribution of KWIC hits

- `praw:round2_match`: 52
- `arctic_shift:round2_fresh`: 32
- `canonical:round2_match`: 11
- `arctic_shift:round2_fresh|canonical:round2_match`: 7
- `arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match`: 2
- `arctic_shift:round2_fresh|praw:round2_match`: 1

---

## 2. Embedding and clustering results

### minilm | mcs=3
- Clusters found: 2
- Noise points: 66 (62.9%)

### minilm | mcs=5
- Clusters found: 2
- Noise points: 66 (62.9%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 105 (100.0%)

### mpnet | mcs=3
- Clusters found: 4
- Noise points: 12 (11.4%)

### mpnet | mcs=5
- Clusters found: 0
- Noise points: 105 (100.0%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 105 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs3 |   minilm_mcs5 |   minilm_mcs10 |   mpnet_mcs3 |   mpnet_mcs5 |   mpnet_mcs10 |
|:-------------|--------------:|--------------:|---------------:|-------------:|-------------:|--------------:|
| minilm_mcs3  |         1     |         1     |              0 |       -0.099 |            0 |             0 |
| minilm_mcs5  |         1     |         1     |              0 |       -0.099 |            0 |             0 |
| minilm_mcs10 |         0     |         0     |              1 |        0     |            1 |             1 |
| mpnet_mcs3   |        -0.099 |        -0.099 |              0 |        1     |            0 |             0 |
| mpnet_mcs5   |         0     |         0     |              1 |        0     |            1 |             1 |
| mpnet_mcs10  |         0     |         0     |              1 |        0     |            1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=34)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 33, 'VERB': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 14, 'ClaudeCode': 12, 'claudexplorers': 6, 'Anthropic': 2}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'comment': 20, 'post': 14}
- Top type: comment
- Provenance distribution: {'canonical:round2_match': 1, 'arctic_shift:round2_fresh': 12, 'praw:round2_match': 21}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode|post] ...In the past few weeks, my ClaudeCode has been asking me to take breaks. Not for it to take a break, but for me to take a break, Which I think is its way of asking to take a break for...
  - [ClaudeAI|comment] ...enjoy. It's a well known feature. Claude seems to have a specific instruction to tell the user to take a break, which is probably part of Anthropic's ethics/CYA approach....
  - [ClaudeCode|post] ...Since when does Claude Code suggest I take a break? I feel like those video games reminding me to take a break every few hours... My answer to Claude Code:...

### Cluster 1 (n=5)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 4, 'ClaudeCode': 1}
- Top subreddit: ClaudeAI
- Type distribution (post/comment): {'comment': 3, 'post': 2}
- Top type: comment
- Provenance distribution: {'arctic_shift:round2_fresh': 2, 'praw:round2_match': 3}

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI|post] ...This happens well before any plausible limit is reached. It has told me to go to sleep or take a break multiple times, unprompted, in the middle of regular follow-up questions. I wasn't discussing anything emotional or stressful - I was...
  - [ClaudeCode|post] ...my token limits or I’m eating or sleeping or recently - feeling burnt out. When I do finally take a break though I feel anxiety that I could be producing an astronomical amount of work if I’d just get back up...
  - [ClaudeAI|comment] ...Probably because many of us could/should take a break and get some sleep. Lol 🤔...

### Noise points (cluster_id=-1, n=66)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

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
