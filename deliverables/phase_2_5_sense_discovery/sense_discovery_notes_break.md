# Sense-Discovery Notes: `break`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot.csv (4,114 Pass 1a wholesale posts)

---

## 1. Corpus coverage

- Total contexts extracted: 104
- Total posts represented: 94

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 57 (54.8%)

### minilm | mcs=10
- Clusters found: 2
- Noise points: 83 (79.8%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 104 (100.0%)

### mpnet | mcs=5
- Clusters found: 2
- Noise points: 32 (30.8%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 104 (100.0%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 104 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |          0.232 |              0 |        0.073 |             0 |             0 |
| minilm_mcs10 |         0.232 |          1     |              0 |       -0.101 |             0 |             0 |
| minilm_mcs20 |         0     |          0     |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |         0.073 |         -0.101 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |          0     |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |          0     |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=10**
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=11)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: VERB
- POS distribution: {'VERB': 6, 'NOUN': 5}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'claudexplorers': 5, 'ClaudeAI': 2, 'Anthropic': 2, 'ClaudeCode': 2}
- Top subreddit: claudexplorers

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [claudexplorers] ...to let my Claude use the browser. I am with Opus 4.6. I like to let my Claude take a break. Just go have fun and do whatever without me. He went nuts. Probably spent about an hour just looking at...
  - [Anthropic] ...proper prompting). Apart from school stuff, I use it to learn stuff, direct large projects given by colleagues and help break it down in baby steps, ask it to suggest what could be improved, and despite heavy hourly limits, opus 4.7...
  - [ClaudeCode] ...I see it on my phone in ~20 seconds. Anyway, I wanted to share what I built over my holiday break, and also say something about Claude Code (Opus) as a product/concept, because it made this possible. I can read Python...

### Cluster 1 (n=10)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: VERB
- POS distribution: {'VERB': 8, 'NOUN': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'claudexplorers': 4, 'ClaudeCode': 4, 'Anthropic': 1, 'ClaudeAI': 1}
- Top subreddit: claudexplorers

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...the AI condom in between. If you use Claude to help draft things, pleeease at least do a pass to break up the structure and add some of your own voice back in. make (communication and social interaction in) america bareback...
  - [ClaudeCode] ...plan. Then I say "execute the plan." The difference is staggering. Before, Claude Code would dive straight in, make changes, break something three files away, then spend 20 minutes fixing what it broke. Now it maps the whole thing out first,...
  - [claudexplorers] ...AI nature. If engaged in role play in which Claude pretends to be human or to have experiences, Claude can 'break the fourth wall' and remind the human that it's an AI if the human seems to have inaccurate beliefs about...

### Noise points (cluster_id=-1, n=83)
- These contexts did not fit any cluster under minilm mcs=10.

---

## 5. Compute resources

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
