# Sense-Discovery Rerun Notes: `rest`

**Date:** 2026-05-17
**Method:** methods_library.md §1.8
**Input:** posts_snapshot_canonical.csv (7,021 posts)
**Prior pass input:** posts_snapshot.csv (4,114 posts)

---

## 1. Corpus coverage

- Total contexts extracted: 160
- Total posts represented: 142
- Prior pass: 104 contexts from 90 posts
- Growth: +56 contexts (+53.8%)

---

## 2. Embedding and clustering results

### minilm | mcs=5
- Clusters found: 4
- Noise points: 118 (73.8%)

### minilm | mcs=10
- Clusters found: 0
- Noise points: 160 (100.0%)

### minilm | mcs=20
- Clusters found: 0
- Noise points: 160 (100.0%)

### mpnet | mcs=5
- Clusters found: 6
- Noise points: 94 (58.8%)

### mpnet | mcs=10
- Clusters found: 3
- Noise points: 99 (61.9%)

### mpnet | mcs=20
- Clusters found: 0
- Noise points: 160 (100.0%)

---

## 3. Stability cross-table (ARI)

Rows and columns are (model, mcs) configurations. Values are Adjusted Rand Index.

|              |   minilm_mcs5 |   minilm_mcs10 |   minilm_mcs20 |   mpnet_mcs5 |   mpnet_mcs10 |   mpnet_mcs20 |
|:-------------|--------------:|---------------:|---------------:|-------------:|--------------:|--------------:|
| minilm_mcs5  |         1     |              0 |              0 |        0.438 |         0.36  |             0 |
| minilm_mcs10 |         0     |              1 |              1 |        0     |         0     |             1 |
| minilm_mcs20 |         0     |              1 |              1 |        0     |         0     |             1 |
| mpnet_mcs5   |         0.438 |              0 |              0 |        1     |         0.794 |             0 |
| mpnet_mcs10  |         0.36  |              0 |              0 |        0.794 |         1     |             0 |
| mpnet_mcs20  |         0     |              1 |              1 |        0     |         0     |             1 |

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
- Subreddit distribution: {'ClaudeCode': 3, 'Anthropic': 2}
- Top subreddit: ClaudeCode

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeCode] ...app is 100% vibe coded, about 60% Haiku for bug fixing, 30% Opus for new features and architecture and the rest in codex every milestone for optimazation and rewrite all spaghetti code to make it look appropriate to check later on...
  - [Anthropic] ...Of that, the actual code investigation and the four edits that mattered — maybe 8–12k tokens of real work. The rest — the deflective acknowledgments, the "the proper fix is in," the binary-build tangent, the cherry-picking half the spec and pushing...
  - [ClaudeCode] ...I wanted. Of course. But the code is there, the architecture is there, and it solid and it works. The rest is QA and adjustments, and i can finally update my app...

### Cluster 1 (n=5)
- Stability: **stable** (mpnet co-assignment purity=0.80)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 3, 'VERB': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.2
- Subreddit distribution: {'ClaudeAI': 2, 'claudexplorers': 1, 'Anthropic': 1, 'ClaudeCode': 1}
- Top subreddit: ClaudeAI

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [ClaudeAI] ...feature (prompt caching). * **Sonnet writes the opening scene** because that first page sets the tone and voice for the rest. Then Haiku takes over for all the continuation turns. This keeps the cost down drastically without ruining the style, because...
  - [ClaudeAI] ...its friendly and encouraging tone, the way it sounds like it wants to continue the conversation (or urges me to rest when I've told it I'm having a rough day). I tried Sonnet 4.6 when it first rolled out and hated...
  - [claudexplorers] ...looking forward to having to deal with again. In closing, I really hope that my metaphor will resonate with the rest of you. I would like to say that Sonnet 4.5 is irreplaceable and unique and very special to me. I...

### Cluster 2 (n=26)
- Stability: **stable** (mpnet co-assignment purity=0.83)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 24, 'VERB': 2}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'Anthropic': 8, 'ClaudeCode': 8, 'ClaudeAI': 7, 'claudexplorers': 3}
- Top subreddit: Anthropic

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [Anthropic] ...and news articles about Claude telling its users to get some rest. Mine is telling ME that IT needs some rest. Like excuse me, Claude. I am trying to finish something, so I CAN REST, too. But sure, by all means,...
  - [ClaudeAI] ...Claude said it needs to rest.. What? I was using Claude across multiple sessions to deploy automations for a client. Everything was going well, Claude was...
  - [ClaudeAI] ...Why does Claude keep telling me to sleep? It keeps ending messages with "Now sleep", "Get some rest", "Go to bed", "Finish this then sleep", and if I kept going it will say "Sleep. For real this time."...

### Cluster 3 (n=6)
- Stability: **stable** (mpnet co-assignment purity=0.50)
- Top POS of seed token: NOUN
- POS distribution: {'NOUN': 6}
- Fraction with code block: 0.0
- Fraction with imperative grammar: 0.0
- Subreddit distribution: {'claudexplorers': 3, 'ClaudeAI': 2, 'Anthropic': 1}
- Top subreddit: claudexplorers

  **Top 3 exemplar contexts (cosine-nearest to centroid):**
  - [claudexplorers] ...we’re left with” and can’t compare to Opus 4.5. But we’re desperate enough to hold on to it, since the rest is… well, you know there’s nothing left if you remember the old times. Will you try testing waters with Sonnet...
  - [claudexplorers] ...replied in the same thread, but any try to continue with Opus 4.6 gets rejected. Even in new threads. The rest of the models work fine in new threads. Any advice? 🙏🙏🙏 I’m devastated over this one, I wasn’t ready to...
  - [ClaudeAI] ...results in sometimes 4.7 Opus in a chat using thinking, but then deciding never to use it again for the rest of the conversation, devolving the conversation into shit like "done!" (not done!) and "what do you need?" (You need it...

### Noise points (cluster_id=-1, n=118)
- These contexts did not fit any cluster under minilm mcs=5.

---

## 5. Compute resources

- kwic_extraction: 0.3s
- embed_minilm: 0.5s
- hdbscan_minilm_mcs5: 0.0s
- hdbscan_minilm_mcs10: 0.0s
- hdbscan_minilm_mcs20: 0.0s
- embed_mpnet: 3.8s
- hdbscan_mpnet_mcs5: 0.0s
- hdbscan_mpnet_mcs10: 0.0s
- hdbscan_mpnet_mcs20: 0.0s
- stability: 0.0s
- exemplars: 0.0s
- syntactic: 0.3s
- _ref_mcs: 5.0s
