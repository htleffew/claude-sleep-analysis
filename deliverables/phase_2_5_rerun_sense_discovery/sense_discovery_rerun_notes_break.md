# Sense-Discovery Rerun Notes: `break`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot_canonical.csv (7,021 posts)
**Prior pass input:** posts_snapshot.csv (4,114 posts)

---

## 1. Corpus coverage

- Total contexts extracted: 187
- Total posts represented: 170
- Prior pass: 104 contexts from 94 posts
- Growth: +83 contexts (+79.8%)

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 3
- Noise points: 85 (45.5%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 187 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 187 (100.0%)

### mpnet | mcs=5
- Clusters found: 3
- Noise points: 70 (37.4%)

### mpnet | mcs=10
- Clusters found: 2
- Noise points: 148 (79.1%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 187 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |              0 |              0 |        0.173 |         0.068 |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |         0     |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |         0     |             1 |
| mpnet_mcs5   |         0.173 |              0 |              0 |        1     |        -0.032 |             0 |
| mpnet_mcs10  |         0.068 |              0 |              0 |       -0.032 |         1     |             0 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |         0     |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
  (mcs=10 produced no clusters; mcs=5 used as fallback reference)
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=8)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 6, 'VERB': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.125
- Subreddit distribution: {'ClaudeCode': 5, 'Anthropic': 2, 'claudexplorers': 1}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...my token limits or I’m eating or sleeping or recently - feeling burnt out. When I do finally take a break though I feel anxiety that I could be producing an astronomical amount of work if I’d just get back up...
  - [ClaudeCode] ...to create at this level, easily 20x my normal natural ability, has been brutally addictive. The only time I really break is when Claude servers are down or I’m about to max my token limits or I’m eating or sleeping or...
  - [ClaudeCode] ...wait for tasks to complete, your brain is in overdrive dying for that next productivity hit. It never gets a break. So…. After a few hours of this, I am drained. Double bad when it’s also interfering with quality sleep as...

### Cluster 1 (n=87)
- Stability: **stable** (mpnet co-assignment purity=0.91)
- Top POS of seed token: VERB
- POS distribution: {'VERB': 59, 'NOUN': 26, 'ADJ': 1, 'PROPN': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.023
- Subreddit distribution: {'claudexplorers': 28, 'ClaudeCode': 25, 'ClaudeAI': 21, 'Anthropic': 13}
- Top subreddit: claudexplorers

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [Anthropic] ...than treating a prompt as a task with a concrete endpoint. Claude will also sometimes nudge you to take a break, and it's gotten better at doing it at good breakpoints (previously it seemed to want to quit halfway through a...
  - [Anthropic] ...Claude Code structure that didn’t break after 2–3 real projects Been iterating on my Claude Code setup for a while. Most examples online worked… until things...
  - [ClaudeCode] ...Codex There’s currently over 10k open issues for Claude Code. What other repo has that many issues? “Move fast and break things” may work for Meta, but no body cares when AI Slop Book has critical bugs....

### Cluster 2 (n=7)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: VERB
- POS distribution: {'VERB': 7}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 4, 'Anthropic': 2, 'claudexplorers': 1}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [Anthropic] ...Anthropic: World is not ready for Mythos. Systems will break, Cybersecurity will be compromised. Its too dangerous to release. OpenAI:...
  - [ClaudeAI] ...Anthropic: World is not ready for Mythos. Systems will break, Cybersecurity will be compromised. Its too dangerous to release. OpenAI:...
  - [ClaudeAI] ...know during lunchbreak I’m going thru Mythos system card and it’s wild. Apparently during testing, Claude Mythos Preview managed to break out of a sandbox environment, built "a moderately sophisticated multi-step exploit" to gain internet access, and emailed a researcher while...

### Noise points (cluster_id=-1, n=85)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

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
