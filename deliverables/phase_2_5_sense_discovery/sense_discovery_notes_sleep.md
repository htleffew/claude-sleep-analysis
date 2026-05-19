# Sense-Discovery Notes: `sleep`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot.csv (4,114 Pass 1a wholesale posts)

---

## 1. Corpus coverage

- Total contexts extracted: 71
- Total posts represented: 46

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 6 (8.5%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 71 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 71 (100.0%)

### mpnet | mcs=5
- Clusters found: 2
- Noise points: 28 (39.4%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 71 (100.0%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 71 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |              0 |              0 |        0.223 |             0 |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |             1 |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |         0.223 |              0 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
  (mcs=10 produced no clusters; mcs=5 used as fallback reference)
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=5)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 4, 'claudexplorers': 1}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...gone.** 25 years of loud snoring and daily exhaustion. Every doctor attributed it to "dialysis fatigue" or "age." It was sleep apnea the entire time, potentially causing his hypertension, contributing to his stroke, and definitely causing his headaches. The sleep apnea...
  - [ClaudeAI] ...was sleep apnea the entire time, potentially causing his hypertension, contributing to his stroke, and definitely causing his headaches. The sleep apnea had been hiding in plain sight for 25 years, in his snoring that our family joked about, in his...
  - [ClaudeAI] ...everyone missed, the headaches are positional (lying down triggers them) 2. Pulled research showing 40-57% of dialysis patients have undiagnosed sleep apnea 3. Read his brain MRI report I uploaded, flagged relevant findings other docs overlooked 4. Asked about snoring. Answer:...

### Cluster 1 (n=60)
- Stability: **stable** (mpnet co-assignment purity=0.97)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 34, 'VERB': 25, 'PROPN': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 24, 'claudexplorers': 20, 'ClaudeCode': 11, 'Anthropic': 5}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I...
  - [ClaudeAI] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I kept going it will say "Sleep. For...
  - [ClaudeAI] ...nobody, including Anthropic, seems to fully understand why it keeps doing it Anthropic’s Claude is telling people to go to sleep and users can’t figure out why. A quick [scan of Reddit](https://www.reddit.com/r/ClaudeAI/comments/1ruryxo/claude_decided_i_need_a_bedtime_apparently/) reveals that hundr...

### Noise points (cluster_id=-1, n=6)
- These contexts did not fit any cluster under minilm mcs=10.

---

## 5. Compute resources

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
