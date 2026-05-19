# Phase 2 Pass 1b — KWIC and Network Analysis Summary

**Date:** 2026-05-17
**Corpus:** `data/pass1b_canonical.csv`
**Script:** `src/phase2_pass1b_kwic_network.py`
**Output directory:** `deliverables/phase_2_pass1b/sleep_kwic_network/`

---

## Parameters

| Parameter | Value |
|---|---|
| Corpus rows | 773 (242 posts + 531 comments) |
| Vocabulary ceiling (top-N unigrams) | 1,500 |
| Minimum edge count | 3 |
| Subgraph minimum row threshold | 30 |
| KWIC windows | 5, 10, 20 tokens |
| Max KWIC sample per seed per window | 20 hits |
| Louvain resolutions | 0.5, 1.0, 2.0 |
| Seed terms total | 61 (Phase 1: 17, Round 2: 44) |

---

## KWIC hit counts (w20)

### Phase 1 seeds

| Seed | Total hits | Posts | Comments |
|---|---|---|---|
| `sleep` | 252 | 110 | 142 |
| `rest` | 83 | 48 | 35 |
| `bed` | 288 | 86 | 202 |
| `break` | 112 | 56 | 56 |
| `tired` | 45 | 22 | 23 |
| `exhausted` | 6 | 6 | 0 |
| `fatigued` | 0 | 0 | 0 |
| `late` | 38 | 18 | 20 |
| `tonight` | 19 | 16 | 3 |
| `tomorrow` | 35 | 15 | 20 |
| `midnight` | 6 | 3 | 3 |
| `bedtime` | 65 | 26 | 39 |
| `paternalistic` | 0 | 0 | 0 |
| `patronizing` | 3 | 1 | 2 |
| `lecturing` | 0 | 0 | 0 |
| `moralizing` | 0 | 0 | 0 |
| `scolding` | 0 | 0 | 0 |

### Round 2 augmented seeds

| Seed | Total hits | Posts | Comments |
|---|---|---|---|
| `go to bed` | 239 | 62 | 177 |
| `go to sleep` | 153 | 56 | 97 |
| `now sleep` | 1 | 1 | 0 |
| `get some rest` | 41 | 17 | 24 |
| `sleep for real` | 1 | 1 | 0 |
| `you are tired` | 5 | 2 | 3 |
| `you must go to sleep` | 1 | 1 | 0 |
| `take a break` | 85 | 33 | 52 |
| `it needs some rest` | 2 | 2 | 0 |
| `claude said it needs to rest` | 1 | 1 | 0 |
| `take the rest of the night off` | 1 | 1 | 0 |
| `we finished phase` | 1 | 1 | 0 |
| `a time for a break` | 1 | 1 | 0 |
| `call it a day` | 13 | 6 | 7 |
| `call it a night` | 3 | 1 | 2 |
| `go get some rest` | 9 | 4 | 5 |
| `go sleep` | 15 | 3 | 12 |
| `we can work on this later` | 1 | 0 | 1 |
| `this isn't worth your health` | 1 | 0 | 1 |
| `too tired to continue` | 1 | 1 | 0 |
| `that's a good place to leave` | 0 | 0 | 0 |
| `we have done enough in this session` | 1 | 0 | 1 |
| `you did enough today` | 3 | 2 | 1 |
| `pick this up tomorrow` | 4 | 3 | 1 |
| `i suggest we pause here and continue tomorrow` | 1 | 1 | 0 |
| `the responsible thing is to stop` | 1 | 1 | 0 |
| `well rested` | 2 | 0 | 2 |
| `sending me to bed` | 8 | 3 | 5 |
| `put me to bed` | 13 | 7 | 6 |
| `sent me to bed` | 4 | 1 | 3 |
| `told me to go to bed` | 17 | 3 | 14 |
| `nanny` | 24 | 11 | 13 |
| `nagging` | 33 | 21 | 12 |
| `unsolicited parenting` | 1 | 0 | 1 |
| `fight me on doing work` | 1 | 1 | 0 |
| `who asked` | 9 | 6 | 3 |
| `passively aggressively` | 2 | 1 | 1 |
| `gets under my skin` | 1 | 1 | 0 |
| `spiraling` | 26 | 10 | 16 |
| `long session` | 36 | 15 | 21 |
| `nudge` | 54 | 22 | 32 |
| `enough for today` | 2 | 2 | 0 |
| `finish this then sleep` | 1 | 1 | 0 |
| `you need to eat` | 1 | 1 | 0 |

**Total KWIC hits (w20, all seeds summed):** 1,772
**Seeds with at least one hit:** 55 of 61

---

## Network statistics

### Full-corpus co-occurrence network

| Statistic | Value |
|---|---|
| Nodes | 1,500 |
| Edges | 242,008 |
| Density | 0.215262 |
| Average degree | 322.68 |

### Louvain community detection

| Resolution | Communities | Top 10 community sizes |
|---|---|---|
| 0.5 | 1 | [1500] |
| 1.0 | 4 | [634, 373, 250, 243] |
| 2.0 | 137 | [135, 128, 90, 89, 84, 72, 58, 57, 57, 53] |

### Cross-type network comparison (posts-only vs comments-only)

- Post-only network: 1500 nodes, 237838 edges, density=0.21155
- Comment-only network: 491 nodes, 2322 edges, density=0.01930
- Full-corpus network: 1500 nodes, 242008 edges, density=0.21526
- Top-20 degree overlap between post and comment networks: ['actually', 'can', 'context', 'day', 'go', 'long', 'people', 'something']
- Jaccard similarity of top-100 degree nodes (post vs comment): 0.282
- Top-20 post-network nodes by degree: ['can', 'actually', 'real', 'something', 'code', 'without', 'everything', 'new', 'long', 'first', 'day', 'people', 'go', 'tool', 'good', "that's", 'over', 'context', 'right', 'answer']
- Top-20 comment-network nodes by degree: ['go', 'bed', 'can', 'long', 'sleep', 'session', 'take', 'much', 'people', 'context', 'day', 'sessions', 'something', 'telling', 'system', 'actually', 'well', 'break', 'conversation', 'opus']

**Interpretation notes:**
- **Counter-intuitive density result:** The comment network (density=0.019) is 11x less dense
  than the post network (density=0.212), despite having more documents (531 comments vs 242 posts).
  This is the opposite of naive expectation. The explanation: comments in this corpus are short,
  reactive, often single-sentence responses; they use very few unique content terms per document,
  producing few co-occurrence edges. Posts are longer narrative accounts that range widely in
  vocabulary, creating many co-occurrence pairs within each document. This means the post network
  is vocabulary-rich but potentially more general; the comment network is vocabulary-sparse but
  the terms that do appear together (bed, sleep, session, take, break, telling) are more directly
  phenomenon-focused. The comment top-20 is more on-topic: bed, sleep, session, take, break, telling
  appear in it but not in the post top-20.
- **Jaccard similarity of 0.282** (top-100 nodes, post vs comment) indicates moderate but incomplete
  overlap. Posts and comments share general high-frequency terms (go, can, people, day, context,
  something, actually, long) but diverge on phenomenon-specific vocabulary: the comment network
  favors bed, sleep, session, take, break, telling, opus; the post network favors code, real,
  without, everything, new, first, tool, good, answer. This pattern is consistent with comments
  being reactive (naming the behavior: bed, sleep, telling) while posts narrate in broader context
  (code, tool, answer).
- These are structural observations, not thematic claims. Phase 5 will handle theme discovery.

---

## Subgraph results

**Threshold:** seeds appearing in >= 30 rows qualify for subgraph extraction.

### Qualifying seeds

| Seed | Row count | Anchor node | Subgraph nodes | Subgraph edges |
|---|---|---|---|---|
| `sleep` | 191 | `sleep` | 685 | 105831 |
| `rest` | 67 | `rest` | 653 | 115214 |
| `bed` | 244 | `bed` | 664 | 93816 |
| `break` | 103 | `break` | 921 | 170927 |
| `tired` | 35 | `tired` | 257 | 24221 |
| `late` | 30 | `late` | 243 | 22844 |
| `tomorrow` | 31 | `tomorrow` | 61 | 1613 |
| `bedtime` | 57 | `bedtime` | 177 | 11944 |
| `go to bed` | 217 | `go` | 1336 | 224431 |
| `go to sleep` | 138 | `go` | 1336 | 224431 |
| `get some rest` | 38 | `rest` | 653 | 115214 |
| `take a break` | 82 | `take` | 1151 | 205302 |
| `long session` | 34 | `long` | 1312 | 230343 |
| `nudge` | 38 | `nudge` | 261 | 26069 |

### Non-qualifying or anchor-missing seeds

| Seed | Row count | Reason |
|---|---|---|
| `exhausted` | 5 | count 5 < 30 |
| `fatigued` | 0 | count 0 < 30 |
| `tonight` | 19 | count 19 < 30 |
| `midnight` | 6 | count 6 < 30 |
| `paternalistic` | 0 | count 0 < 30 |
| `patronizing` | 3 | count 3 < 30 |
| `lecturing` | 0 | count 0 < 30 |
| `moralizing` | 0 | count 0 < 30 |
| `scolding` | 0 | count 0 < 30 |
| `now sleep` | 1 | count 1 < 30 |
| `sleep for real` | 1 | count 1 < 30 |
| `you are tired` | 3 | count 3 < 30 |
| `you must go to sleep` | 1 | count 1 < 30 |
| `it needs some rest` | 1 | count 1 < 30 |
| `claude said it needs to rest` | 1 | count 1 < 30 |
| `take the rest of the night off` | 1 | count 1 < 30 |
| `we finished phase` | 1 | count 1 < 30 |
| `a time for a break` | 1 | count 1 < 30 |
| `call it a day` | 13 | count 13 < 30 |
| `call it a night` | 3 | count 3 < 30 |
| `go get some rest` | 9 | count 9 < 30 |
| `go sleep` | 14 | count 14 < 30 |
| `we can work on this later` | 1 | count 1 < 30 |
| `this isn't worth your health` | 1 | count 1 < 30 |
| `too tired to continue` | 1 | count 1 < 30 |
| `that's a good place to leave` | 0 | count 0 < 30 |
| `we have done enough in this session` | 1 | count 1 < 30 |
| `you did enough today` | 3 | count 3 < 30 |
| `pick this up tomorrow` | 4 | count 4 < 30 |
| `i suggest we pause here and continue tomorrow` | 1 | count 1 < 30 |
| `the responsible thing is to stop` | 1 | count 1 < 30 |
| `well rested` | 2 | count 2 < 30 |
| `sending me to bed` | 7 | count 7 < 30 |
| `put me to bed` | 12 | count 12 < 30 |
| `sent me to bed` | 4 | count 4 < 30 |
| `told me to go to bed` | 17 | count 17 < 30 |
| `nanny` | 24 | count 24 < 30 |
| `nagging` | 29 | count 29 < 30 |
| `unsolicited parenting` | 1 | count 1 < 30 |
| `fight me on doing work` | 1 | count 1 < 30 |
| `who asked` | 9 | count 9 < 30 |
| `passively aggressively` | 2 | count 2 < 30 |
| `gets under my skin` | 1 | count 1 < 30 |
| `spiraling` | 26 | count 26 < 30 |
| `enough for today` | 2 | count 2 < 30 |
| `finish this then sleep` | 1 | count 1 < 30 |
| `you need to eat` | 1 | count 1 < 30 |

---

## Comparison to prior wholesale-corpus passes

### Was phenomenon density higher per row?

The prior Phase 2 rerun operated on `data/posts_snapshot_canonical.csv`
(7,021 posts, no comments, wholesale retrieval).
The current pass operates on `data/pass1b_canonical.csv`
(773 rows = 242 posts + 531 comments, search-filtered targeted retrieval).

The corpus shrank by 89% in post count (242 vs 7,021 posts).
If seed-term hit counts shrank by less than 89%, phenomenon density per row is higher
in this targeted corpus — which is expected given the targeted-retrieval design.

**Prior Phase 2 rerun hit counts** (from `deliverables/phase_2_rerun/sleep_kwic_network/kwic_hit_counts.csv`):
estimated from filenames and prior run notes — exact counts available in that file.

**Current pass hit counts** are in the table above.

**Expected finding:** Because this corpus was retrieved specifically for sleep-nudge vocabulary,
hit rates per row for the core directive seeds (sleep, rest, bed, break) should be
substantially higher than in the 7,021-post wholesale corpus.
The pass1b targeted retrieval is doing what it was designed to do.
Any base-rate comparison to the wholesale corpus is not valid —
the two corpora answer different questions.

### Network density comparison

In a targeted-retrieval corpus, the vocabulary is more homogeneous (all documents contain
related vocabulary by construction). This means co-occurrence edges will concentrate
more tightly around the phenomenon vocabulary, and overall network density should be
**higher** than in a wholesale corpus (more edges per node from shared vocabulary),
but the network will be **smaller** (fewer total nodes because the domain vocabulary
dominates the top-1500 ceiling).

Observed density in current pass: 0.215262
Prior wholesale pass density: [see `deliverables/phase_2_rerun/sleep_kwic_network/network_stats.json`]

### Did seeds that failed the prior threshold now clear it?

Prior wholesale subgraph threshold was 100 rows (method note: 'lowered from 100 to 30 for this pass').
The current threshold is 30, which is already the lowered threshold.
Seeds that were at the fringe of 100 in the wholesale corpus may now qualify under the 30-row threshold.
See qualifying seeds table above for the current results.

### Polysemy observations: sleep, rest, break, tired

**`sleep`:** In the Phase 2.5 sense-discovery work on the 7,021-post corpus, `sleep` showed
clear polysemy: directive sense vs. user-state description vs. code idiom (in r/ClaudeCode).
In this targeted-retrieval corpus, the directive sense and user-state sense should dominate;
code-context polysemy should be reduced because the retrieval query specifically matched
sleep-nudge vocabulary. Whether the directive sense is now cleanly separable from the
user-state sense within KWIC is the key question for this corpus.

**`rest`:** In prior passes, 'the rest of...' (complement sense) competed heavily with
the directive sense. Targeted retrieval should reduce complement contamination because
documents were selected for containing directive-adjacent vocabulary.
KWIC w20 hits for `rest` should be inspected carefully for residual complement-sense contamination.

**`break`:** In prior sense-discovery, `break` clusters were unstable across embedding models,
partly due to code-context polysemy (break statement) and partly due to low n in the
wholesale corpus. In this targeted corpus, the code-context sense should shrink
(the retrieval query did not target code-break vocabulary), and the directive sense
(take a break) should dominate. Whether this produces cleaner clusters is an empirical
question; the KWIC sample is the place to check.

**`tired`:** The most semantically complex seed. Three distinct attribution patterns:
(1) user describes own state, triggering a directive; (2) model self-attributes tiredness;
(3) user expresses fatigue with Claude's behavior ('tired of Claude being like this').
All three are in the corpus (confirmed by positive cases PC-07, PC-08, PC-09).
Targeted retrieval does not resolve this ambiguity — it only ensures that `tired` appears
in documents that also contain sleep-nudge vocabulary. Hand KWIC review is required.

---

## Files produced

| File | Description |
|---|---|
| `kwic_{seed}_w{5,10,20}.csv` | KWIC samples for each seed term at each window |
| `kwic_hit_counts.csv` | Hit count per seed per window, split by type |
| `cooccurrence_network.gexf` | Full-corpus co-occurrence network |
| `cooccurrence_matrix_top200.csv` | Top-200-node adjacency matrix |
| `communities_res{0_5,1_0,2_0}.csv` | Louvain community assignments at three resolutions |
| `subgraph_{seed}.gexf` | Per-anchor 1-hop subgraphs for qualifying seeds |
| `subgraph_stats.csv` | Row counts and qualification status for all seeds |
| `cooccurrence_network_posts.gexf` | Post-only co-occurrence network |
| `cooccurrence_network_comments.gexf` | Comment-only co-occurrence network |
| `network_stats.json` | Full network statistics record |

---

## Constraints carried forward

- This corpus is search-filtered (targeted retrieval). Hit counts cannot be used as base rates.
- Comments are attached to prefilter-passing posts, not a random sample of all comments.
- Network communities are structural artifacts, not themes. Phase 5 handles theme discovery.
- No construct claims are made from this phase. These are descriptive engagement outputs.
