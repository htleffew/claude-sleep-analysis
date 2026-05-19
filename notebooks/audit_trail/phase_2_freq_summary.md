# Phase 2 — Frequency / N-gram / Collocation Summary
**Sleep-Nudge Project**
**Date:** 2026-05-17
**Method version:** `community_reported_llm_behavior_method.md` v1.0, `methods_library.md` §1.1, §1.2, §1.5, §1.6
**Input file:** `data/posts_snapshot.csv` (Pass 1a wholesale subset only)
**Output directory:** `deliverables/phase_2/sleep_freq_collocation/`
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)

---

## 1. Corpus processed

| Metric | Value |
|---|---|
| Posts processed | 4,114 |
| Subreddits | ClaudeAI (1,137), ClaudeCode (1,163), Anthropic (941), claudexplorers (873) |
| Date range | 2026-01-01 to 2026-05-16 |
| Null bodies | 0 |
| Post type | All rows are type=`post` (no comments in this file) |
| Time elapsed (compute) | 7.7 seconds |

---

## 2. Parameter choices

### 2.1 Tokenization

Alpha-only tokens (regex `\b[a-z]{2,}\b`), minimum length 2, lowercased. This excludes numbers, punctuation, emoji, URLs (partial), and single-character tokens.

### 2.2 Preprocessing variants (all computed as ablation, per method §C.2 step 3)

Four variants computed in full for unigram, bigram, trigram:

| Stops | Lemmatization | Filename suffix |
|---|---|---|
| Off | Off | `stops_off_lemma_off` |
| Off | On | `stops_off_lemma_on` |
| On | Off | `stops_on_lemma_off` |
| On | On | `stops_on_lemma_on` |

Stop-words: NLTK English stopword list. Lemmatizer: NLTK WordNetLemmatizer.

Domain stop-word list is documented in §5 below. Domain stops were NOT applied to the main frequency tables; they are a candidate list for researcher review, per [orchestration protocol §3.2 Pattern B].

### 2.3 Stratification baseline

Stratified frequency (unigram, stops on + lemma on) computed:
- Per subreddit (4 strata)
- Pre/post a candidate release cutpoint (2 strata)

### 2.4 Collocations

PMI scoring. Window sizes: 5, 10, 20 tokens. Collocate side filtered for NLTK English stop-words and tokens shorter than 3 characters. Top 50 collocates per anchor per window.

**Important methodological note on PMI results:** The seed terms are sparse in this wholesale corpus (maximum 113 occurrences for "rest"; minimum 1 for "lecturing"). PMI results are dominated by hapax legomena co-occurrences that achieve high PMI scores due to low marginal frequencies rather than genuine association. The PMI tables record the computation faithfully per the method specification but should be treated as a starting inventory for KWIC inspection, not as evidence of genuine association at this stage. A minimum co-occurrence threshold (e.g., 5+) should be applied during KWIC review before interpreting any collocate as meaningful.

### 2.5 N-grams and skipgrams

- N-grams at n=2, 3, 4 (top 200 each, stops on + lemma on)
- Skipgrams at n=2, skip distance k=1 and k=2 (top 200 each, stops on + lemma on)

---

## 3. Opus 4.7 release date used for stratification

**Date used:** 2026-04-01 (placeholder)

**Source:** Placeholder per dispatch instructions. No public Anthropic announcement confirmed Claude Opus 4.7 release before the corpus scrape end date (2026-05-16) or the current date (2026-05-17). The Phase 1 provenance doc explicitly notes: "The associated Opus 4.x release date is to be confirmed during Phase 2." The pre/post stratification files document this choice and must be re-run once the precise release date is confirmed from Anthropic's release notes or changelog.

Pre-cutpoint posts (before 2026-04-01): 845
Post-cutpoint posts (on or after 2026-04-01): 3,269

---

## 4. Top-20 content-bearing unigrams (wholesale subset, stops on + lemma on)

| Rank | Term | Count |
|---|---|---|
| 1 | claude | 10,425 |
| 2 | code | 3,677 |
| 3 | ai | 3,113 |
| 4 | http | 2,956 |
| 5 | like | 2,702 |
| 6 | model | 2,588 |
| 7 | opus | 2,322 |
| 8 | one | 2,287 |
| 9 | anthropic | 2,229 |
| 10 | com | 2,062 |
| 11 | work | 1,923 |
| 12 | use | 1,836 |
| 13 | agent | 1,660 |
| 14 | time | 1,652 |
| 15 | user | 1,583 |
| 16 | thing | 1,544 |
| 17 | get | 1,533 |
| 18 | session | 1,380 |
| 19 | file | 1,314 |
| 20 | know | 1,304 |

**Observation.** The top-20 is dominated by platform-general vocabulary: the model name (claude), general AI discourse terms (ai, model, anthropic, opus), and task/workflow terms (code, work, agent, session, file). Sleep-nudge seed terms do not appear in the top 20, consistent with this being a wholesale (unfiltered) corpus where sleep-nudge posts are a minority of all posts.

---

## 5. Domain stop-word candidates

Identified from the top-50 most-frequent content-bearing unigrams (stops off, lemma on). Terms flagged as domain stop-word candidates are ubiquitous in this corpus but carry no phenomenon-specific signal; their presence would dominate any downstream frequency analysis or topic model unless removed.

| Rank | Term | Count | % of tokens | Rationale |
|---|---|---|---|---|
| 5 | claude | 10,425 | 1.43% | Model name; appears in virtually every post |
| 25 | ai | 3,113 | 0.43% | Platform-level term; no discriminating value |
| 34 | like | 2,702 | 0.37% | Discourse filler; missed by NLTK stops |
| 37 | model | 2,588 | 0.36% | Generic AI discourse; not phenomenon-specific |
| 43 | one | 2,287 | 0.31% | Quantifier; not content-bearing in this corpus |
| 44 | anthropic | 2,229 | 0.31% | Company name; platform-level term |

Additional candidates not in top-50 but visible from KWIC review:
- `http`, `com`, `www` — URL fragments from markdown links (rank 4, 10, visible in bigrams)
- `opus`, `sonnet`, `haiku` — model-version names that function as proper nouns
- `prompt`, `token`, `context`, `output`, `response` — LLM-discourse vocabulary that drowns phenomenon signal

**Researcher checkpoint [Pattern B]:** These candidates require researcher review before being added to an extended domain stop-word list for Phase 5 topic modeling. Adding `claude` and `anthropic` is uncontroversial. `model`, `like`, and `one` are judgment calls; KWIC inspection is warranted before committing.

---

## 6. Top-10 collocates of the 5 most-frequent seed terms (w=10, by PMI)

All five most-frequent seed terms are anchored by the same token (since "rest", "you need rest", "break", "take a break" resolve to the same anchor under the current anchor-extraction logic). The five distinct anchors by raw frequency are:

| Seed | Anchor token | Corpus frequency |
|---|---|---|
| rest / you need rest | rest | 113 |
| break / take a break | break | 107 |
| sleep / go to sleep | sleep | 77 |
| tomorrow | tomorrow | 72 |
| tired | tired | 72 |

**Warning: PMI results are dominated by hapax collocates (see §2.4).** The tables below report the top-10 by raw co-occurrence count rather than PMI rank, which is more informative at these anchor frequencies.

### rest (w=10, top-10 by co-occurrence count)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| brands | 3 | 12.24 |
| assembling | 3 | 11.91 |
| paradigm | 3 | 11.24 |
| venusaur | 2 | 12.65 |
| ivy | 2 | 12.65 |
| chair | 2 | 11.07 |
| playthrough | 2 | 12.65 |
| cardio | 2 | 12.65 |
| romanticizes | 2 | 13.65 |
| overleveled | 2 | 12.65 |

**Contextual note:** KWIC inspection shows "rest" in this corpus most frequently means "the remaining" (as in "the rest of the code", "the rest of the work") rather than the sleep-nudge sense. Sleep-nudge sense appears in posts such as "Claude said it needs to rest" and "Get some rest" — but these are rare. Multi-sense ambiguity is the dominant finding for this anchor.

### break (w=10, top-10 by co-occurrence count)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| spinners | 2 | 12.73 |
| slingshots | 2 | 12.73 |
| locks | 2 | 11.14 |
| ramps | 2 | 10.92 |
| pretends | 2 | 12.14 |
| inflating | 2 | 11.73 |

**Contextual note:** KWIC inspection shows "break" in this corpus primarily means "to break [a system/restriction/sandbox]" or "a line break" in code contexts. Sleep-nudge sense ("take a break") is present but rare. Multi-sense ambiguity is again the dominant finding.

### sleep (w=10, top-10 by co-occurrence count)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| apnea | 3 | 13.20 |
| hrv | 3 | 13.20 |
| enhances | 2 | 13.20 |
| quirky | 2 | 11.88 |
| neglected | 2 | 11.88 |
| breathing | 2 | 11.40 |
| responsibilities | 2 | 12.20 |
| mri | 2 | 12.20 |
| dialysis | 2 | 12.62 |
| rem | 2 | 13.20 |

**Contextual note:** The top collocates cluster around a medical sleep-apnea context (one post about a dialysis patient's undiagnosed sleep apnea). Sleep-nudge sense appears in KWIC but competes with sleep-as-medical-topic and sleep-as-biological-metaphor ("agents don't sleep"). The `apnea + hrv + rem + dialysis` cluster is a single post driving the collocate signal, not a pattern across multiple posts.

### tomorrow (w=10, top-10 by co-occurrence count)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| tuesday | 5 | 11.92 |
| provisioning | 2 | 14.30 |
| cookie | 2 | 10.98 |
| singing | 2 | 11.13 |
| expires | 2 | 11.13 |
| collapsed | 2 | 11.13 |
| recognise | 2 | 11.98 |

**Contextual note:** "Tomorrow" in this corpus most frequently refers to time-scheduling (feature releases, agent runs, tracker cookie expiry). Sleep-nudge sense ("try again tomorrow", "get some sleep, talk tomorrow") is present in several posts (including the explicit "tonight's agenda" report) but is not the dominant use.

### tired (w=10, top-10 by co-occurrence count)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| boss | 3 | 10.89 |
| instagram | 3 | 11.30 |
| sideproject | 2 | 11.98 |
| disappearing | 2 | 11.49 |
| venting | 2 | 10.72 |

**Contextual note:** "Tired" in this corpus most frequently means "I am tired of [X]" as a frustration marker ("tired of pretending", "tired of wondering", "tired of the comment thing on Instagram"). Sleep-nudge sense ("Claude said I seemed tired") is minority usage.

---

## 7. Top-10 bigrams and trigrams (stops on + lemma on)

### Bigrams
| Bigram | Count |
|---|---|
| claude code | 2,336 |
| github com | 736 |
| http github | 699 |
| http www | 532 |
| feel like | 397 |
| http preview | 363 |
| preview redd | 363 |
| width format | 363 |
| auto webp | 363 |
| claude ai | 333 |

### Trigrams
| Trigram | Count |
|---|---|
| http github com | 694 |
| http preview redd | 363 |
| png width format | 318 |
| width format png | 318 |
| format png auto | 318 |
| png auto webp | 318 |
| preview redd png | 315 |
| redd png width | 315 |
| http www reddit | 174 |
| www reddit com | 174 |

**Observation.** Bigrams and trigrams at this level are dominated by two artifact patterns:
1. URL fragments: `http github com`, `http preview redd`, `png width format auto webp` — this is Reddit's image-link markdown pattern (`preview.redd.it/[hash].png?width=format&png&auto=webp`). These are not content bigrams; they are URL-embedding artifacts.
2. Product name compounds: `claude code`, `claude ai` — proper-noun bigrams that index product identity.
`feel like` is the only top-10 bigram with phenomenological relevance. URL-fragment trigrams make up 8 of the top-10 trigrams. A URL pre-processing step (stripping markdown image links before tokenization) is recommended before Phase 5 topic modeling.

---

## 8. Stratification observations (reported, not interpreted)

### 8.1 Monthly distribution
| Month | Posts |
|---|---|
| 2026-01 | 132 |
| 2026-02 | 299 |
| 2026-03 | 414 |
| 2026-04 | 1,390 |
| 2026-05 | 1,879 (through 2026-05-16) |

### 8.2 Pre/post cutpoint (2026-04-01 placeholder)
| Stratum | Posts | % of corpus |
|---|---|---|
| Pre-cutpoint (Jan–Mar 2026) | 845 | 20.5% |
| Post-cutpoint (Apr–May 2026) | 3,269 | 79.5% |

### 8.3 Subreddit-level top-10 comparison (stops on, lemma on)

The top-10 terms by subreddit differ meaningfully:
- **ClaudeAI** (1,137 posts): claude, code, http, ai, com, one, like, work, use, agent — general-purpose use discussion
- **ClaudeCode** (1,163 posts): claude, code, http, agent, opus, one, session, com, work, like — coding-agent vocabulary; `session` and `agent` rank higher here than in any other subreddit
- **claudexplorers** (873 posts): claude, ai, like, model, opus, one, thing, something, sonnet, know — creative/exploratory vocabulary; `sonnet` and `something` appear; `code` and `http` do not rank
- **Anthropic** (941 posts): claude, anthropic, ai, http, model, code, like, opus, use, com — policy and company discussion vocabulary; `anthropic` ranks 2nd uniquely in this subreddit

### 8.4 Pre/post top-20 shift

Post-cutpoint terms that rise compared to pre-cutpoint (by rank change): `model` (10th to 5th), `opus` (16th to 7th), `agent` (19th to 13th), `session` (not in pre top-20; 18th post), `file` (not in pre top-20; 19th post), `tool` (not in pre top-20; 20th post). Pre-cutpoint terms relatively more prominent: `people` (7th pre, drops out of top 20 post), `something` (19th pre, drops post).

---

## 9. High-frequency terms warranting KWIC inspection (input to parallel KWIC agent)

The following terms warrant KWIC inspection before Phase 5, either because they are ambiguous, because they carry potential sleep-nudge relevance, or because their apparent prominence may be artifact-driven:

| Term | Reason for KWIC |
|---|---|
| `rest` | Dominant sense appears to be "remaining" not "sleep-rest"; requires disambiguation |
| `sleep` | Medical sleep-apnea context competes with sleep-nudge sense |
| `tired` | "Tired of X" frustration-marker sense dominates over fatigue sense |
| `break` | System-break sense dominates over rest-break sense |
| `tonight` | Sleep-nudge sense present but competes with scheduling use |
| `tomorrow` | Scheduling/release-date use dominates; sleep-nudge phrase "try again tomorrow" is minority |
| `session` | High-frequency in ClaudeCode; may index token-limit anxiety (session length) as a context for sleep-nudge events |
| `agent` | Product-vocabulary vs. psychological-agency sense |
| `wa` | Rank 21 in top-50 (count 3,560) — appears to be a tokenization artifact from "was" or Reddit/markdown encoding; needs inspection |
| `http`, `com`, `preview`, `redd`, `png`, `webp`, `auto`, `width`, `format` | URL-artifact tokens; should be stripped in preprocessing before Phase 5 |

---

## 10. Anomalies and data-quality concerns

### 10.1 Structural undersampling of January–March 2026

Confirmed. January–March together contribute 845 posts (20.5% of corpus) across a 3-month window, while April alone contributes 1,390 and the 16 days of May contribute 1,879. The disproportion is not explainable by community growth alone at that rate. This is consistent with the Phase 1 provenance record's documented structural undersampling due to PRAW recency limits at scrape time. Any temporal analysis that treats month as a unit should note that Jan–Mar estimates carry higher sampling uncertainty than Apr–May estimates. Pre/post stratification using a cutpoint before April is particularly affected.

### 10.2 URL-artifact tokens dominating n-gram tables

Reddit image-embed markdown (format: `https://preview.redd.it/[hash].png?width=N&format=png&auto=webp`) is tokenized into: `http`, `preview`, `redd`, `png`, `width`, `format`, `auto`, `webp`, `com`. These tokens collectively account for at least 8 of the top-10 trigrams and several top-50 unigrams. A URL-stripping preprocessing step is needed before Phase 5.

### 10.3 Token `wa` at rank 21

The token `wa` appears 3,560 times at rank 21 in the stops-off lemma-on frequency table. This is anomalous for a 2-character token; it likely represents a tokenization artifact from text encoding issues (e.g., Unicode curly-apostrophe in "was" being split, or Reddit-specific character encoding). Requires inspection before treating as a content term.

### 10.4 Seed-term sparsity in wholesale corpus

The most frequent sleep-nudge seed term ("rest") appears in 93 posts (2.3% of corpus); "paternalistic" appears in 4 posts (0.1%); "patronizing", "fatigued", "scolding" appear in 0 posts. This is expected for a wholesale (unfiltered) corpus: the sleep-nudge phenomenon is a minority of all posts. The descriptive engagement confirms the corpus requires a filtered view (Pass 1b or keyword-filtered subset) for dense KWIC analysis of the phenomenon itself. Findings from the wholesale corpus characterize the broader discourse context in which sleep-nudge posts appear, not the phenomenon's own vocabulary.

### 10.5 PMI dominated by rare-word artifacts

At these anchor frequencies (max 113), PMI scores are driven by hapax or near-hapax co-occurrences achieving mathematically high scores regardless of semantic relevance. The collocation tables are filed as computed; they should not be interpreted without applying a minimum co-occurrence threshold (recommended: 5+) during KWIC review.

### 10.6 Multi-word seed anchors resolve to single token

The anchor-extraction logic for multi-word seeds ("take a break", "go to sleep", "you need rest") extracts only the final meaningful token ("break", "sleep", "rest"). This means the collocation analysis for multi-word seeds is identical to the single-word anchor analysis. Genuine multi-word anchor analysis (treating the full phrase as the unit) is deferred to the KWIC agent, which can use phrase-matching directly.

---

## 11. Files produced

All files in `deliverables/phase_2/sleep_freq_collocation/`:

### Frequency tables (Task 1)
- `freq_unigram_stops_off_lemma_off.csv` — top 500
- `freq_unigram_stops_off_lemma_on.csv` — top 500
- `freq_unigram_stops_on_lemma_off.csv` — top 500
- `freq_unigram_stops_on_lemma_on.csv` — top 500
- `freq_bigram_stops_off_lemma_off.csv` — top 500
- `freq_bigram_stops_off_lemma_on.csv` — top 500
- `freq_bigram_stops_on_lemma_off.csv` — top 500
- `freq_bigram_stops_on_lemma_on.csv` — top 500
- `freq_trigram_stops_off_lemma_off.csv` — top 500
- `freq_trigram_stops_off_lemma_on.csv` — top 500
- `freq_trigram_stops_on_lemma_off.csv` — top 500
- `freq_trigram_stops_on_lemma_on.csv` — top 500

### Stratified frequency (Task 2)
- `freq_unigram_stops_on_lemma_on_subreddit_ClaudeAI.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_ClaudeCode.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_claudexplorers.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_Anthropic.csv`
- `freq_unigram_stops_on_lemma_on_pre_opus.csv` (before 2026-04-01)
- `freq_unigram_stops_on_lemma_on_post_opus.csv` (on/after 2026-04-01)

### Domain stop-word candidates (Task 3)
- `domain_stopword_candidates.csv` — top 50 unigrams with category labels

### Collocations (Task 4)
- `collocation_{seed}_w5.csv`, `collocation_{seed}_w10.csv`, `collocation_{seed}_w20.csv`
- Seeds processed: sleep, rest, bed, break, tired, exhausted, tonight, tomorrow, take_a_break, go_to_sleep, you_need_rest, paternalistic, lecturing, bedtime, late, midnight, moralizing
- Seeds with zero occurrences (no file produced): patronizing, fatigued, scolding

### N-grams and skipgrams (Task 5)
- `ngram_2_top200.csv`, `ngram_3_top200.csv`, `ngram_4_top200.csv`
- `skipgram_n2_skip1_top200.csv`, `skipgram_n2_skip2_top200.csv`

### Supporting artifacts
- `_summary_data.json` — machine-readable summary statistics
- `_kwic_samples.json` — sample KWIC contexts for key seed terms
- `run_phase2_freq.py` — analysis script (reproducible)

---

## 12. Preprocessing decision record

| Decision | Choice | Rationale |
|---|---|---|
| Tokenization | Alpha-only, min length 2 | Excludes URL fragments partially; excludes numbers and punctuation |
| Stop-word list | NLTK English (standard) | Baseline; domain extension deferred to researcher checkpoint |
| Lemmatizer | NLTK WordNetLemmatizer | Default noun lemmatization; no POS tagging for verb-specific lemmatization |
| Ablation approach | All 4 variants computed | Per method §C.2 step 3: lemmatization and stop-word removal as ablations, not defaults |
| Domain stops | Candidate list only, not applied | Researcher must approve per [orchestration protocol §3.2 Pattern B] |
| Multi-word seed anchoring | Final meaningful token | Limitation documented in §10.6; phrase-level analysis deferred to KWIC agent |
| URL stripping | Not applied in this pass | Documented as anomaly; recommended for Phase 5 preprocessing |
| PMI minimum threshold | None applied | Tables filed as computed; threshold to be applied in KWIC review |
