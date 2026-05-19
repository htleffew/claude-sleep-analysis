# Sense-Discovery Rerun Notes: `sleep`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot_canonical.csv (7,021 posts)
**Prior pass input:** posts_snapshot.csv (4,114 posts)

---

## 1. Corpus coverage

- Total contexts extracted: 102
- Total posts represented: 72
- Prior pass: 71 contexts from 46 posts
- Growth: +31 contexts (+43.7%)

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 10 (9.8%)

### minilm | mcs=10
- Clusters found: 2
- Noise points: 60 (58.8%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 102 (100.0%)

### mpnet | mcs=5
- Clusters found: 4
- Noise points: 54 (52.9%)

### mpnet | mcs=10
- Clusters found: 0
- Noise points: 102 (100.0%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 102 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |         -0.087 |              0 |        0.008 |             0 |             0 |
| minilm_mcs10 |        -0.087 |          1     |              0 |        0.645 |             0 |             0 |
| minilm_mcs20 |         0     |          0     |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |         0.008 |          0.645 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |          0     |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |          0     |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=10**
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=32)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: VERB
- POS distribution: {'VERB': 17, 'NOUN': 14, 'PROPN': 1}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeAI': 14, 'ClaudeCode': 7, 'claudexplorers': 6, 'Anthropic': 5}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I...
  - [ClaudeAI] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I kept going it will say "Sleep. For...
  - [Anthropic] ...of Reddit](https://www.reddit.com/r/ClaudeAI/comments/1ruryxo/claude_decided_i_need_a_bedtime_apparently/) reveals that hundreds of people have had the same issue dating back months—and as recently as Wednesday. Claude’s sleep demands are varied and, often, quirky variations of the same message. To ...

### Cluster 1 (n=10)
- Stability: **unstable** (mpnet co-assignment purity=0.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 8, 'VERB': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeCode': 9, 'claudexplorers': 1}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...test one thing real quick,” and then somehow I’m debugging an agent workflow, rewriting prompts, researching models, and convincing myself sleep is optional. Anyone else losing sleep because their brain won’t stop thinking of new AI ideas?...
  - [ClaudeCode] ...then somehow I’m debugging an agent workflow, rewriting prompts, researching models, and convincing myself sleep is optional. Anyone else losing sleep because their brain won’t stop thinking of new AI ideas?...
  - [ClaudeCode] ...I let Claude Code on web run overnight while I sleep. Here's my async AI development workflow. **I went from "AI assists my coding" to "I review AI's coding."** Ever since...

### Noise points (cluster_id=-1, n=60)
- These contexts did not fit any cluster under minilm mcs=10.

---

## 5. Compute resources

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
