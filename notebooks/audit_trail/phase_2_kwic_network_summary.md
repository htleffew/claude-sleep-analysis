# Phase 2 KWIC / Co-occurrence / Network — Summary

**Date:** 2026-05-17
**Method phase:** [method §C.2] Descriptive Engagement — KWIC / co-occurrence / network half
**Input:** `data/posts_snapshot.csv` — 4,114 Pass 1a wholesale posts
**Output directory:** `deliverables/phase_2/sleep_kwic_network/`

---

## Parameters

| Parameter | Value |
|---|---|
| Corpus | `posts_snapshot.csv` — Pass 1a wholesale, 4,114 posts |
| Seed terms | 17 terms (see §C.1 provenance) |
| KWIC window sizes | 5, 10, 20 tokens each side |
| KWIC max sample per seed | 20 hits (or all if fewer) |
| Tokenization | `nltk.word_tokenize`, lower-cased, raw non-lemmatized, stop-words preserved |
| Co-occurrence vocabulary | Top-2,000 content-bearing unigrams |
| Content-bearing criterion | alpha-only, len>2, not in NLTK English + domain stop-words |
| Edge threshold | count ≥ 5 post-level co-occurrences |
| Community detection | Louvain at resolution 0.5, 1.0, 2.0; `community-louvain` library |
| Subgraph eligibility threshold | ≥100 total KWIC hits |

---

## KWIC hit counts per seed term

| Seed term | Total hits | Sampled (max 20) |
|---|---|---|
| `sleep` | 71 | 20 |
| `rest` | 112 | 20 |
| `bed` | 39 | 20 |
| `break` | 106 | 20 |
| `tired` | 71 | 20 |
| `exhausted` | 20 | 20 |
| `fatigued` | 0 | 0 |
| `late` | 56 | 20 |
| `tonight` | 38 | 20 |
| `tomorrow` | 70 | 20 |
| `midnight` | 8 | 8 |
| `paternalistic` | 4 | 4 |
| `patronizing` | 0 | 0 |
| `lecturing` | 1 | 1 |
| `moralizing` | 3 | 3 |
| `scolding` | 0 | 0 |
| `bedtime` | 4 | 4 |

---

## Network statistics

| Stat | Value |
|---|---|
| Vocabulary trimmed to top-N | 2,000 content unigrams |
| Raw co-occurrence pairs | 1,668,786 |
| Edges after ≥5 threshold | 655,008 |
| Graph nodes (non-isolated) | 1,998 |
| Graph edges | 655,008 |
| Graph density | 0.328324 |
| Mean degree | 655.66 |
| Connected components | 1 |

### Community detection results

| Resolution | Communities | Largest | Smallest | Median size |
|---|---|---|---|---|
| 0.5 | 17 | 1970 | 1 | 1 |
| 1.0 | 4 | 782 | 13 | 602 |
| 2.0 | 327 | 96 | 1 | 2 |

---

## Per-anchor subgraphs

Seeds eligible (≥100 hits): ['rest', 'break']

| Seed | Nodes | Edges |
|---|---|---|
| `rest` | 768 | 232974 |
| `break` | 923 | 306543 |

---

## Anomalies and interpretive notes

### Small corpus size

At 4,114 posts, this corpus is substantially smaller than large-scale Reddit NLP studies and smaller than the LCR project corpus. Co-occurrence counts are correspondingly sparse. The edge threshold of ≥5 was chosen to filter noise while retaining signal; at a larger corpus a threshold of ≥10 or ≥20 would be standard. Researchers interpreting community structures should weight the sparsity caveat heavily: communities here reflect high-frequency co-occurring vocabulary pairs, not latent semantic themes.

### Network density — an important counter-intuition

Graph density is 0.328324 and mean degree is 655.66. These numbers are surprisingly high and are explained by the corpus structure: the top-2000 content terms are dominated by common vocabulary (code, work, every, context, etc.) that appears across enough posts that most pairs clear the ≥5 edge threshold. In a small corpus (4,114 posts) with high-frequency general vocabulary, the co-occurrence graph approaches completeness for top-N terms, which is the opposite of the sparsity one might expect from small N. The practical consequence is that the Louvain communities are not well-separated at resolution 0.5 (one dominant mega-community of 1,970 nodes at that resolution). The resolution=1.0 partition with 4 communities of roughly balanced size is more analytically tractable, and resolution=2.0 fragments into 327 micro-communities. The network is structurally dense but semantically shallow because the vocabulary is dominated by high-frequency general terms rather than phenomenon-specific vocabulary. The seed terms relevant to the sleep-nudge phenomenon appear infrequently enough that they are not among the top-2000 anchors driving network structure.

### Programming-term contamination

`sleep`, `rest`, and `break` carry technical programming meanings in the ClaudeCode subreddit (`time.sleep()`, REST API, break statement). Their raw hit counts are inflated by these usages relative to what the sleep-nudge phenomenon requires. Subreddit-stratified KWIC reads (particularly comparing ClaudeCode vs ClaudeAI/Anthropic/claudexplorers) are needed before these terms can be treated as reliable anchors for the phenomenon.

### Low evaluative-term frequency

`paternalistic` (4 hits), `patronizing` (0 hits), `lecturing` (1 hits), `moralizing` (3 hits), `scolding` (0 hits). These terms are semantically unambiguous as user-reaction language, but their low frequency in the wholesale corpus suggests either: (a) the phenomenon is rare in the Pass 1a wholesale slice; (b) users more commonly describe the phenomenon with other vocabulary; or (c) the evaluative terminology concentrates in Pass 1b search-filtered posts (which were selected by search terms more likely to co-occur with these evaluations). This asymmetry is a documented Pass 1a vs Pass 1b constraint (see phase_1_corpus_provenance.md).

### Communities are not themes

Per [methods_library.md §1.3]: 'Treating community-detection output as theme discovery. Communities here are an artifact of the term graph; they may or may not correspond to themes a human would name.' The community files are supplied for pattern inspection, not as theme claims. Theme discovery is [method §C.5].

---

## Cross-reference

- KWIC observation notes: `notebooks/audit_trail/phase_2_kwic_notes.md`
- Frequency/collocation half: `deliverables/phase_2/sleep_freq_collocation/`
- Corpus provenance: `notebooks/audit_trail/phase_1_corpus_provenance.md`
- Method: `community_reported_llm_behavior_method.md` §C.2
- Technique references: `methods_library.md` §1.3 (co-occurrence), §1.7 (KWIC)
