# Sense-Discovery Notes: `rest`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot.csv (4,114 Pass 1a wholesale posts)

---

## 1. Corpus coverage

- Total contexts extracted: 104
- Total posts represented: 90

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 2
- Noise points: 39 (37.5%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 104 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 104 (100.0%)

### mpnet | mcs=5
- Clusters found: 3
- Noise points: 67 (64.4%)

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
| minilm_mcs5  |         1     |              0 |              0 |        0.077 |             0 |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |             1 |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs5   |         0.077 |              0 |              0 |        1     |             0 |             0 |
| mpnet_mcs10  |         0     |              1 |              1 |        0     |             1 |             1 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |             1 |             1 |

---

## 4. Cluster-level structural descriptions

**Reference configuration: minilm + mcs=5**
  (mcs=10 produced no clusters; mcs=5 used as fallback reference)
Labels are not assigned. Structure is reported only.

### Cluster 0 (n=57)
- Stability: **stable** (mpnet co-assignment purity=0.78)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 49, 'VERB': 8}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'Anthropic': 16, 'ClaudeAI': 15, 'ClaudeCode': 15, 'claudexplorers': 11}
- Top subreddit: Anthropic

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...Claude said it needs to rest.. What? I was using Claude across multiple sessions to deploy automations for a client. Everything was going well, Claude was...
  - [Anthropic] ...and news articles about Claude telling its users to get some rest. Mine is telling ME that IT needs some rest. Like excuse me, Claude. I am trying to finish something, so I CAN REST, too. But sure, by all means,...
  - [ClaudeCode] ...or similar… I’ll do like 30 minutes of work and then Claude will be like “do this and take the rest of the night off” or “we finished phase 1: A time for a break”. It really gets under my skin...

### Cluster 1 (n=8)
- Stability: **stable** (mpnet co-assignment purity=1.00)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 8}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'ClaudeCode': 3, 'ClaudeAI': 2, 'Anthropic': 2, 'claudexplorers': 1}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...I wanted. Of course. But the code is there, the architecture is there, and it solid and it works. The rest is QA and adjustments, and i can finally update my app...
  - [Anthropic] ...I mapped, I could only find two that had been previously documented with anything close to a full schema; the rest were either undocumented or only described at the UI level. # Where the docs live The full documentation is 100+...
  - [ClaudeCode] ...stitch.withgoogle.com → Settings → API Keys ⚠️ **Gemini models only** — Uses GEMINI_3_PRO or GEMINI_3_FLASH under the hood ⚠️ **No REST API yet** — MCP/SDK only (someone asked on the Google AI forum, official answer is "not yet") ⚠️ **HTML is...

### Noise points (cluster_id=-1, n=39)
- These contexts did not fit any cluster under minilm mcs=10.

---

## 5. Compute resources

- kwic_extraction: 0.2s
- embed_minilm: 0.3s
- hdbscan_minilm_mcs5: 0.0s
- hdbscan_minilm_mcs10: 0.0s
- hdbscan_minilm_mcs20: 0.0s
- embed_mpnet: 2.4s
- hdbscan_mpnet_mcs5: 0.0s
- hdbscan_mpnet_mcs10: 0.0s
- hdbscan_mpnet_mcs20: 0.0s
- stability: 0.0s
- exemplars: 0.0s
- syntactic: 0.2s
- _ref_mcs: 5.0s
