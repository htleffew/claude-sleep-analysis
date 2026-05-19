# Phase 2 Re-run: KWIC and Network Analysis Summary

**Date:** 2026-05-17
**Method phase:** [method §C.2] Descriptive Engagement
**Input:** `data/posts_snapshot_canonical.csv` — 7,021 posts
**Output directory:** `deliverables/phase_2_rerun/sleep_kwic_network/`
**Script:** `src/phase2_rerun_kwic_network.py`
**Prior pass:** `deliverables/phase_2/sleep_kwic_network/` — operated on `data/posts_snapshot.csv` (4,114 posts)
**Corpus growth:** 4,114 → 7,021 (71% expansion via `posts_snapshot_canonical.csv`)

---

## 1. Parameters

| Parameter | Value |
|---|---|
| Corpus | `data/posts_snapshot_canonical.csv` |
| Total posts | 7,021 |
| Subreddit breakdown | ClaudeCode: 2,100; ClaudeAI: 1,959; Anthropic: 1,491; claudexplorers: 1,471 |
| KWIC window sizes | 5, 10, 20 tokens each side |
| Max KWIC sample per seed per window | 20 (random, seed=42) |
| Co-occurrence vocabulary size | Top-2,000 content-bearing unigrams |
| Minimum edge weight | 5 |
| Louvain resolutions | 0.5, 1.0, 2.0 |
| Per-anchor subgraph threshold | 100 posts containing the seed term |
| Random seed | 42 |
| Tokenization | NLTK `word_tokenize`, alphabetic tokens only (no contractions), lowercase |
| Stop-words | Inline English stop-word list + domain-specific stops (claude, gpt, llm, ai, model, anthropic, openai, prompt, user, using, use, https, http, www, reddit, and ~30 additional high-frequency domain terms) |

---

## 2. KWIC hit counts

### Token occurrences vs posts-containing-term

| Seed term | Token hits (w10 = total) | Posts with term | Prior pass token hits | Growth |
|---|---|---|---|---|
| `sleep` | 103 | 73 | 71 | +45% |
| `rest` | 171 | 147 | 112 | +53% |
| `bed` | 54 | 45 | 39 | +38% |
| `break` | 191 | 173 | 106 | +80% |
| `tired` | 128 | 105 | 71 | +80% |
| `exhausted` | 29 | 28 | 20 | +45% |
| `fatigued` | 1 | 1 | 0 | -- |
| `late` | 77 | 67 | 56 | +38% |
| `tonight` | 55 | 47 | 38 | +45% |
| `tomorrow` | 101 | 75 | 70 | +44% |
| `midnight` | 17 | 13 | 8 | +113% |
| `paternalistic` | 4 | 4 | 4 | 0% |
| `patronizing` | 1 | 1 | 0 | -- |
| `lecturing` | 1 | 1 | 1 | 0% |
| `moralizing` | 3 | 2 | 3 | 0% |
| `scolding` | 1 | 1 | 0 | -- |
| `bedtime` | 5 | 5 | 4 | +25% |

Notes:
- Prior pass hit counts are token occurrences as reported in `phase_2_kwic_notes.md`. This run distinguishes token occurrences from post-level unique counts; the prior pass did not make this distinction systematically.
- KWIC files at w5, w10, w20 contain the same total hit count because window size affects context shown, not how many tokens are found.
- `fatigued` and `patronizing` and `scolding` gained 1 token hit each from near-zero -- effectively absent at both scales.

### Growth pattern

Most seeds grew at roughly 40-55% above the prior pass, consistent with proportional corpus expansion (71% growth). `break` and `tired` grew faster (80%) -- possibly reflecting an influx of posts about coding-context breakage and user fatigue with AI tools that became more topical in the broader scrape's time coverage. `paternalistic`, `moralizing`, `lecturing` showed zero or minimal growth, consistent with these being vocabulary confined to a stable sub-community rather than trending corpus-wide.

---

## 3. Network statistics

### Full co-occurrence graph

| Statistic | Re-run (7,021 posts) | Prior pass (4,114 posts) | Change |
|---|---|---|---|
| Nodes (top-N vocabulary) | 2,000 | 2,000 | -- |
| Edges (count >= 5) | 974,487 | Not reported | -- |
| Graph density | **0.4875** | **0.33 (reported)** | +48% increase |
| Largest connected component | 2,000 nodes (same as full graph) | Not reported | -- |

**Density increased, not decreased.** The prior pass reported density of 0.33 and framed this as "less general-vocab dominance" being a desired direction. At 0.49, the re-run graph is *denser*, not less dense. This indicates that with 71% more posts, the top-2,000 vocabulary terms co-occur with each other more thoroughly -- terms that were marginally connected at 4,114 posts are now robustly connected at 7,021. This is the expected behavior of a co-occurrence graph as N grows: edges accumulate faster than nodes because the vocabulary ceiling is fixed at 2,000. A denser graph does not indicate better or worse signal; it indicates the vocabulary ceiling has been fully saturated with co-occurrence evidence at this corpus size.

A sparser graph would require either raising the `min_edge` threshold above 5, or raising the vocabulary ceiling beyond 2,000 to include rarer terms. Neither is recommended without a specific analytical motivation, as both changes affect graph structure in ways that interact with the Louvain community detection.

### Louvain community detection

| Resolution | Communities | Community size distribution (top 10) |
|---|---|---|
| 0.5 | 9 | 1,990; 2; 2; 1; 1; 1; 1; 1; 1 |
| 1.0 | 3 | 769; 638; 593 |
| 2.0 | 447 | 91; 86; 61; 59; 57; 44; 40; 35; 30; 27 |

**Resolution 0.5 produces one mega-community of 1,990 nodes** -- essentially the entire graph assigned to one community with 8 isolate-sized fringe communities. This is consistent with a very dense graph where low-resolution Louvain cannot find meaningful partitions.

**Resolution 1.0 produces three near-equal communities** (769, 638, 593 nodes) that partition the vocabulary into roughly three sectors of comparable size. Per method §1.3 anti-pattern guidance: these communities are a structural artifact of the term graph and must not be interpreted as themes. Their existence is noted here for comparative purposes only.

**Resolution 2.0 produces 447 communities** with the ten largest ranging from 27 to 91 nodes -- granular enough to correspond to lexical sub-clusters around specific topic areas. Again, not interpreted as themes here.

**Comparison to prior pass:** The prior pass reported resolution-specific community counts but not size distributions. The density increase from 0.33 to 0.49 explains why resolution 0.5 is now essentially uninformative (mega-community). The prior pass likely showed more balanced communities at 0.5 because the sparser graph had more internal structure at that resolution.

---

## 4. Per-anchor subgraphs

### Seeds clearing the 100-post threshold

| Seed | Posts with term | Ego subgraph nodes | Ego subgraph edges | Ego density |
|---|---|---|---|---|
| `rest` | 147 | 1,166 | 525,780 | 0.774 |
| `break` | 173 | 1,432 | 696,331 | 0.680 |
| `tired` | 105 | 649 | 194,271 | 0.924 |

**Three seeds cleared the threshold.** In the prior pass, `rest` (estimated ~112 posts) and `break` (~106 posts) were near or above threshold. The re-run confirms both and adds `tired` (105 posts). Per the prior `phase_2_kwic_notes.md`, the original pass had `sleep` at 71 hits -- below threshold. The expanded corpus raises `sleep` to 73 posts with 103 token hits -- still below threshold.

**`sleep` did not clear the 100-post threshold.** Despite growing from 71 to 103 token hits, the post-level count is 73, which is below the subgraph threshold. The primary seed term for the phenomenon under study (the thing Claude directs users to do) is not frequent enough in wholesale posts to generate a subgraph. This is consistent with the corpus being mostly general Claude usage, not sleep-nudge focused.

**Seeds that did NOT clear threshold:**

| Seed | Posts with term | Delta from threshold |
|---|---|---|
| `sleep` | 73 | -27 |
| `tomorrow` | 75 | -25 |
| `late` | 67 | -33 |
| `tonight` | 47 | -53 |
| `bed` | 45 | -55 |
| `exhausted` | 28 | -72 |
| `midnight` | 13 | -87 |
| All evaluative terms | 1-5 | well below |

---

## 5. Comparison to prior pass

### Did seed-term hit counts grow with the corpus expansion?

Yes. All seed terms with nonzero hits in the prior pass grew in the re-run. Growth rates ranged from 0% (evaluative terms: `paternalistic`, `moralizing`, `lecturing`) to 80% (`break`, `tired`). The 0% growth on evaluative terms is notable: it suggests these terms are not proportionally distributed across the broader wholesale corpus -- they appear in a fixed number of posts regardless of corpus size. This is consistent with these terms being used by a specific user sub-community concentrated in the original Pass 1a sample.

### Did network density decrease (indicating less general-vocab dominance)?

No. Density increased from 0.33 to 0.49. As explained in §3 above, this is expected behavior as N grows with a fixed vocabulary ceiling. The question as framed in the task specification assumed density would decrease with a larger corpus; the opposite occurred because co-occurrence accumulation saturates a fixed vocabulary more thoroughly. The observation that the prior pass density of 0.33 was already very high (random graph at 2,000 nodes and minimum edge count would have much lower density) suggests the corpus was already general-vocab dominated at 4,114 posts, and more posts made it more so, not less.

### Did any previously-below-threshold seeds now clear the 100-post threshold?

Yes. `tired` is newly above threshold (105 posts, up from approximately 71 token hits in prior pass). `sleep`, despite growing to 103 token hits, has only 73 posts with the term -- it did not clear the threshold. `tomorrow` at 75 posts is close but below.

### Did the polysemy observations on `sleep`, `rest`, `break`, `tired` change at the larger scale?

**`sleep`:** Tripartite polysemy (human rest / sleep-directive behavior / programmatic `time.sleep()`) holds at larger scale. A fourth sense -- medical/physiological sleep (sleep architecture, sleep apnea) -- is more visible at 103 hits than it was at 71 hits. The additional corpus volume did not collapse the senses; it made minority senses more visible.

**`rest`:** Tripartite polysemy (remainder phrase / REST API / physical rest) holds. The remainder-phrase sense remains dominant. No new senses emerged.

**`break`:** Tripartite polysemy (code break / take a break / line break formatting) holds. The sleep-directive sense of `break` (model telling user to take a break) remains a minority sense not reliably surfaced in random w10 KWIC samples at this N. The corpus expansion did not improve the signal-to-noise ratio for this seed.

**`tired`:** Polysemy expanded. A fourth sense emerged at larger N: model attributing tiredness to itself ("too tired to continue"). This sense was not visible at 71 hits in the prior pass. It is now a documentable observation at 105 posts. The "tired of" (fed-up) sense remains dominant by count.

**Overall polysemy conclusion:** Larger corpus reveals minority senses, not fewer senses. The sense-discovery work ([method §1.8]) documented in `deliverables/phase_2_5_sense_discovery/` is validated: KWIC reading alone at any corpus size cannot reliably disambiguate these terms; embedding-cluster sense discovery is the appropriate technique for sense separation on the primary seeds.

---

## 6. Top-50 content-bearing unigram frequencies (re-run)

Selected from `network_stats.json`. These are post-deduplication, post-stop-word-removal, post-domain-stop-removal counts.

| Rank | Term | Count |
|---|---|---|
| 1 | code | 5,774 |
| 2 | opus | 3,237 |
| 3 | people | 1,937 |
| 4 | any | 1,864 |
| 5 | context | 1,845 |
| 6 | usage | 1,603 |
| 7 | built | 1,572 |
| 8 | real | 1,551 |
| 9 | agent | 1,548 |
| 10 | session | 1,434 |
| 11 | system | 1,390 |
| 12 | sonnet | 1,366 |
| 13 | project | 1,300 |
| 14 | plan | 1,235 |
| 15 | better | 1,235 |
| 16 | models | 1,229 |
| 17 | different | 1,159 |
| 18 | files | 1,141 |
| 19 | memory | 1,108 |
| 20 | tool | 1,092 |

The top-20 is dominated by programming/AI-workflow vocabulary. `opus` and `sonnet` (model names) rank second and twelfth despite being domain stops only partially -- they survived the stop-word filter because they were not listed. This is an ablation note: adding `opus`, `sonnet`, `haiku` as domain stops would clean the vocabulary further but is not required for the network structure observation. The sleep-directive vocabulary (`sleep`, `bed`, `rest`, `tired`) does not appear in the top-50, consistent with the wholesale corpus being predominantly general Claude usage rather than sleep-nudge focused.

---

## 7. Output file inventory

All outputs in `deliverables/phase_2_rerun/sleep_kwic_network/`:

| File pattern | Description |
|---|---|
| `kwic_{seed}_w{5,10,20}.csv` | KWIC samples (up to 20 hits, cols: post_id, createdAt, subreddit, left_context, keyword, right_context) |
| `kwic_hit_counts.csv` | Total token hit counts per seed per window |
| `cooccurrence_network.gexf` | Full 2,000-node co-occurrence graph (Gephi-compatible) |
| `cooccurrence_matrix_top200.csv` | 200x200 term-term co-occurrence matrix |
| `communities_res0_5.csv` | Louvain community assignments, resolution 0.5 |
| `communities_res1_0.csv` | Louvain community assignments, resolution 1.0 |
| `communities_res2_0.csv` | Louvain community assignments, resolution 2.0 |
| `subgraph_{rest,break,tired}.gexf` | Ego subgraphs for threshold-clearing seeds |
| `subgraph_stats.csv` | Node/edge/density counts for each subgraph |
| `network_stats.json` | Complete network statistics in machine-readable format |

Original Phase 2 deliverables in `deliverables/phase_2/sleep_kwic_network/` are untouched.
