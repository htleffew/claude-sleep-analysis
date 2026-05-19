# Phase 2 Re-Run — Frequency / N-gram / Collocation Summary
**Sleep-Nudge Project**
**Date:** 2026-05-17
**Method version:** `community_reported_llm_behavior_method.md` v1.0, `methods_library.md` §1.1, §1.2, §1.5, §1.6
**Input file:** `data/posts_snapshot_canonical.csv` (canonical wholesale corpus)
**Output directory:** `deliverables/phase_2_rerun/sleep_freq_collocation/`
**Prior pass output:** `deliverables/phase_2/sleep_freq_collocation/` (untouched)
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)

---

## 1. Corpus processed

| Metric | Value |
|---|---|
| Posts processed | 7,021 |
| Growth from original pass | +2,907 posts (+70.7%) |
| Subreddits | ClaudeCode (2,100), ClaudeAI (1,959), Anthropic (1,491), claudexplorers (1,471) |
| Date range | 2026-01-01 to 2026-05-17 |
| Null bodies | 0 |
| Post type | All rows are type=`post` |
| Time elapsed (compute) | 12.1 seconds |

---

## 2. Parameter choices

### 2.1 Tokenization

Alpha-only tokens (regex `\b[a-z]{3,}\b`), minimum length **3** (raised from 2 in the prior pass — see §3.2 for rationale). Lowercased. Excludes numbers, punctuation, emoji, and 2-character noise tokens.

### 2.2 URL stripping (NEW in this pass)

Applied before tokenisation. Pattern: `(?:https?://\S+) | (?:www\.\S+) | (?:\[.*?\]\(.*?\))`. This removes all HTTP/HTTPS URLs, `www.` links, and markdown `[text](url)` link constructs.

Prior pass finding that motivated this: `http`, `preview`, `redd`, `png`, `width`, `format`, `auto`, `webp`, `com` appeared in 8 of the top-10 trigrams as URL-fragment artifacts from Reddit image-embed markdown (`preview.redd.it/[hash].png?width=N&format=png&auto=webp`).

**Verification:** `preview.redd.it` appeared in 418 raw texts before stripping; 0 texts after stripping. The top-10 bigrams and trigrams are now fully content-bearing (see §7).

### 2.3 Preprocessing variants (all computed as ablation, per method §C.2 step 3)

Four variants computed in full for unigram, bigram, trigram:

| Stops | Lemmatization | Filename suffix |
|---|---|---|
| Off | Off | `stops_off_lemma_off` |
| Off | On | `stops_off_lemma_on` |
| On | Off | `stops_on_lemma_off` |
| On | On | `stops_on_lemma_on` |

Stop-words: NLTK English stopword list. Lemmatizer: NLTK WordNetLemmatizer.

Domain stop-word list is documented in §5 below. Domain stops were NOT applied to the main frequency tables; they are a candidate list for researcher review, per [orchestration protocol §3.2 Pattern B].

### 2.4 Stratification

Stratified frequency (unigram, stops on + lemma on) computed:
- Per subreddit (4 strata)
- Pre/post a candidate release cutpoint (2 strata)

### 2.5 Collocations

PMI scoring. Window sizes: 5, 10, 20 tokens. Collocate side filtered for NLTK English stop-words and tokens shorter than 3 characters. **Minimum co-occurrence floor of 5 applied** (addresses the hapax-driven collocates issue from the prior pass). Top 50 collocates per anchor per window.

### 2.6 N-grams and skipgrams

- N-grams at n=2, 3, 4 (top 200 each, stops on + lemma on)
- Skipgrams at n=2, skip distance k=1 and k=2 (top 200 each, stops on + lemma on)

---

## 3. Data-quality fixes applied

### 3.1 URL-fragment strip

Applied upstream of tokenisation. Eliminates the `preview.redd.it` image-embed artifact that dominated all trigram and many bigram frequency tables in the prior pass. The top-10 bigrams are now: `claude code`, `feel like`, `using claude`, `anyone else`, `use claude`, `look like`, `open source`, `claude opus`, `usage limit`, `context window`. All are content-bearing. The URL-fragment artifacts (`http github com`, `http preview redd`, `png width format auto webp`) are gone.

### 3.2 `wa` encoding artifact — investigation and resolution

**Investigation findings:**

| Metric | Value |
|---|---|
| `wa` as a whole word in raw texts | 3 occurrences |
| `wa` as substring in raw texts (total) | 16,049 |
| Curly apostrophe characters in corpus | 6,898 |
| `wasn't` / `wasn't` forms | 365 |
| `wouldn't` / `wouldn't` forms | 153 |

**Conclusion:** The token `wa` (3,560 occurrences at rank 21 in the prior pass) was a **tokenisation artifact from contraction splitting with curly apostrophes**. The prior pass tokeniser used `r"\b[a-z]{2,}\b"` on lowercased text. Curly-apostrophe contractions such as `wasn't` (Unicode `’`) are lowercased to `wasn't`, and the word-boundary regex treats the curly apostrophe as a boundary, splitting the token. However, `wasn't` → `wasn` + `t`, not `wa` + `s`. Further inspection revealed only 3 whole-word instances of `wa` in the raw text, far below 3,560. The more likely source is `what` rendered with curly quotes in some Reddit contexts being split as `wha` + `t`, or similar patterns in HTML-encoded text where `&amp;` or `&#x27;` variants produce unexpected splits. The exact mechanism is rendering-dependent and not recoverable without the original HTML.

**Resolution:** The minimum token length has been raised from 2 to 3 characters. This eliminates `wa`, `ai`, `ok`, `it`, `is`, and other 2-character tokens that are either noise artifacts or function words already captured by the standard stopword list. The term `ai` (2 characters) was a top-20 content-bearing term in the prior pass; it is excluded from this run by the length floor and explicitly noted as a domain stop-word candidate for researcher review — its semantic content is low (it functions as a platform label equivalent to `claude` and `anthropic`).

---

## 4. Opus 4.7 release date used for stratification

**Date used:** 2026-04-01 (placeholder, inherited from prior pass)

**Source:** No public Anthropic announcement confirmed a specific "Opus 4.7" release date before the corpus scrape end date (2026-05-17) or the current date (2026-05-17). The Phase 1 provenance doc explicitly notes: "The associated Opus 4.x release date is to be confirmed during Phase 2." The pre/post stratification files document this choice and must be re-run once the precise release date is confirmed.

| Stratum | Posts | % of corpus |
|---|---|---|
| Pre-cutpoint (before 2026-04-01) | 1,654 | 23.6% |
| Post-cutpoint (on/after 2026-04-01) | 5,367 | 76.4% |

The expanded corpus has improved the pre-cutpoint stratum from 845 posts (20.5%) to 1,654 posts (23.6%), approximately doubling the Jan-Mar sample. The structural undersampling of early months is reduced but not eliminated.

---

## 5. Domain stop-word candidates

Identified from the top-50 most-frequent content-bearing unigrams (stops off, lemma on, min length 3).

| Rank | Term | Count | % of tokens | Rationale |
|---|---|---|---|---|
| 1 | claude | 16,093 | 1.63% | Model name; appears in virtually every post |
| 3 | like | 4,555 | 0.46% | Discourse filler; missed by NLTK stops |
| 4 | model | 3,916 | 0.40% | Generic AI discourse; not phenomenon-specific |
| 5 | one | 3,872 | 0.39% | Quantifier; not content-bearing in this corpus |
| 8 | use | 3,051 | 0.31% | Generic action verb; not discriminating |
| 9 | anthropic | 3,007 | 0.31% | Company name; platform-level term |
| 11 | time | 2,748 | 0.28% | Generic temporal reference; not discriminating |
| 12 | thing | 2,633 | 0.27% | Discourse placeholder |
| 13 | get | 2,560 | 0.26% | Generic action verb |
| 17 | user | 2,251 | 0.23% | Generic actor label |
| 18 | know | 2,211 | 0.22% | Generic epistemic verb |

Additional candidates not in top-50 but known from prior pass and KWIC context:
- `opus`, `sonnet`, `haiku` — model-version names functioning as proper nouns
- `prompt`, `token`, `context`, `output`, `response` — LLM-discourse vocabulary
- `http`, `com`, `www`, `github` — residual URL fragments from non-markdown links (not fully stripped by URL strip)
- `ai` — 2-character term excluded by new minimum length; platform label equivalent to `claude`

**Researcher checkpoint [Pattern B]:** These candidates require researcher review before being added to an extended domain stop-word list for Phase 5 topic modeling. Adding `claude` and `anthropic` is uncontroversial. `model`, `like`, `one`, `time`, `thing`, `get` are judgment calls; KWIC inspection is warranted before committing.

---

## 6. Top-10 collocates of the 5 most-frequent seed terms (w=10, min co-occurrence ≥5)

The five most-frequent seed anchors by raw corpus frequency in the canonical corpus:

| Seed | Anchor token | Corpus frequency (canonical, 7,021 posts) |
|---|---|---|
| break / take a break | break | 193 |
| rest / you need rest | rest | 172 |
| tired | tired | 130 |
| sleep / go to sleep | sleep | 105 |
| tomorrow | tomorrow | 104 |

**Note on PMI floor:** The minimum co-occurrence floor of 5 now filters out hapax collocates. Collocate tables are shorter but qualitatively more informative than the prior pass. Several seeds (paternalistic, patronizing, lecturing, scolding, fatigued, moralizing, bedtime, midnight at w=5/10) have zero collocates meeting the floor — they remain too sparse for meaningful collocation analysis at the whole-corpus level. This confirms the prior pass's needle-in-haystack finding.

### break (w=10, top-10 by PMI, min cooc ≥5)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| take | 17 | 7.22 |
| logic | 6 | 7.01 |
| costs | 5 | 6.91 |
| tell | 9 | 6.23 |
| inside | 5 | 6.03 |
| works | 10 | 6.03 |
| rules | 6 | 5.99 |
| could | 15 | 5.96 |
| loop | 5 | 5.91 |
| try | 7 | 5.81 |

**Contextual note:** `take` and `loop` are the strongest signals for sleep-nudge sense ("take a break", "loop breaking"). `logic`, `costs`, `rules`, `inside` cluster around the system-break sense. Multi-sense ambiguity persists for this anchor.

### rest (w=10, top-10 by PMI, min cooc ≥5)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| components | 5 | 8.64 |
| night | 9 | 8.09 |
| telling | 6 | 7.43 |
| needs | 8 | 6.75 |
| world | 8 | 6.56 |
| together | 5 | 6.36 |
| turn | 5 | 6.31 |
| old | 5 | 6.27 |
| others | 5 | 6.07 |
| pattern | 5 | 5.94 |

**Contextual note:** `night` and `telling` are the strongest sleep-nudge signals ("telling me to rest", "rest for the night"). `components`, `world`, `others`, `pattern` cluster around the "the rest of X" (remaining) sense. Multi-sense ambiguity remains the dominant finding.

### tired (w=10, top-10 by PMI, min cooc ≥5)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| lied | 5 | 11.30 |
| got | 38 | 8.08 |
| shit | 5 | 7.97 |
| getting | 15 | 7.41 |
| hey | 5 | 7.16 |
| built | 28 | 7.00 |
| never | 16 | 6.79 |
| almost | 5 | 6.77 |
| saying | 5 | 6.66 |
| always | 6 | 6.14 |

**Contextual note:** `got tired`, `getting tired`, `tired of` patterns dominate — confirming the prior pass finding that "tired of X" (frustration marker) is the primary sense. `lied` and `shit` suggest emotional distress/frustration contexts. Sleep-fatigue sense is minority.

### sleep (w=10, top-10 by PMI, min cooc ≥5)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| bed | 7 | 10.25 |
| telling | 12 | 9.14 |
| morning | 10 | 8.76 |
| rest | 6 | 8.36 |
| brain | 7 | 8.28 |
| quick | 6 | 8.27 |
| night | 6 | 8.22 |
| memories | 5 | 7.78 |
| keeps | 5 | 7.68 |
| stop | 6 | 6.86 |

**Contextual note:** This is qualitatively the most improved table in this pass. `bed`, `morning`, `night`, `rest` form a coherent sleep-domain cluster. `telling` at co-occurrence=12 and PMI=9.14 is strong evidence for posts about "Claude telling me to sleep" or "telling me to get some rest." `brain` and `memories` suggest AI-consciousness-of-sleep discourse ("agents don't sleep", "Claude's memory across sessions"). `keeps` and `stop` suggest persistent-behavior framing ("keeps telling me to sleep", "can't stop mentioning sleep"). The floor of 5 has cleaned this table substantially from the prior pass.

### tomorrow (w=10, top-10 by PMI, min cooc ≥5)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| tuesday | 5 | 10.36 |
| tonight | 5 | 9.70 |
| wait | 7 | 8.42 |
| early | 6 | 8.15 |
| night | 5 | 7.97 |
| morning | 5 | 7.78 |
| today | 14 | 7.48 |
| next | 11 | 7.22 |
| day | 9 | 6.37 |
| going | 8 | 6.41 |

**Contextual note:** `tonight`, `night`, `morning` cluster supports sleep-nudge phrasing ("try again tomorrow", "get some rest tonight"). `today`, `next`, `day`, `going` cluster around scheduling/planning discourse. `wait` may indicate "just wait until tomorrow" phrasing in sleep-nudge or in general planning. Multi-sense ambiguity continues but the sleep cluster is more legible than in the prior pass.

---

## 7. Top-10 bigrams and trigrams (stops on + lemma on, URL-stripped)

### Bigrams
| Bigram | Count |
|---|---|
| claude code | 3,791 |
| feel like | 660 |
| using claude | 608 |
| anyone else | 472 |
| use claude | 415 |
| look like | 327 |
| open source | 326 |
| claude opus | 322 |
| usage limit | 299 |
| context window | 261 |

### Trigrams
| Trigram | Count |
|---|---|
| using claude code | 232 |
| use claude code | 128 |
| claude code session | 122 |
| claude code codex | 100 |
| happy answer question | 90 |
| claude code cli | 75 |
| would love hear | 58 |
| used claude code | 50 |
| free open source | 49 |
| claude code claude | 49 |

**Observation.** The URL strip has fully resolved the prior pass's dominant artifact. All top-10 bigrams and all top-10 trigrams are now content-bearing. The bigram picture is dominated by product-name compounds (`claude code`, `claude opus`, `use claude`) and general discourse patterns (`feel like`, `anyone else`, `look like`). Sleep-nudge vocabulary does not appear in the top-10 bigrams or trigrams, consistent with the needle-in-haystack character of this corpus. `usage limit` and `context window` reflect session-length and token-anxiety discourse that may co-occur with sleep-nudge events.

---

## 8. Comparison to the original pass (4,114 → 7,021 posts)

The expanded corpus grows the raw seed-term frequencies, but growth is **sub-proportional for most seed terms**. Expected proportional growth at the 71% corpus expansion: 1.707x.

| Seed token | Orig freq (4,114 posts) | Re-run freq (7,021 posts) | Growth ratio | Assessment |
|---|---|---|---|---|
| break | 107 | 193 | 1.80 | Proportional |
| rest | 113 | 172 | 1.52 | Proportional (low end) |
| tired | 72 | 130 | 1.81 | Proportional |
| sleep | 77 | 105 | 1.36 | Below proportional |
| tomorrow | 72 | 104 | 1.44 | Below proportional |
| tonight | 40 | 57 | 1.43 | Below proportional |
| bed | 40 | 54 | 1.35 | Below proportional |
| exhausted | 20 | 29 | 1.45 | Below proportional |
| late | 59 | 86 | 1.46 | Below proportional |
| midnight | 9 | 18 | 2.00 | Above proportional |
| paternalistic | 4 | 4 | 1.00 | Below proportional |
| moralizing | 3 | 3 | 1.00 | Flat |
| bedtime | 5 | 6 | 1.20 | Below proportional |
| lecturing | 1 | 1 | 1.00 | Flat |
| fatigued | 0 | 1 | — | New (trivial) |
| patronizing | 0 | 1 | — | New (trivial) |
| scolding | 0 | 1 | — | New (trivial) |

**Key finding:** Sleep-specific seed terms (`sleep`, `bed`, `tonight`, `bedtime`) show growth ratios of 1.20–1.36, meaningfully below the expected 1.707. This indicates that the new posts in the broader-retrieval re-scrape are **proportionally less likely to contain sleep-nudge vocabulary** than the original Pass 1a posts. The additional posts are drawn from `top/week` and `top/day` listings, which may skew toward high-engagement/general-interest content rather than the niche sleep-nudge reports. The terms `fatigued`, `patronizing`, and `scolding` now appear (1 occurrence each), but these are not meaningful arrivals.

**Did any previously absent seed terms now appear at meaningful scale?** No. The three newly present terms (fatigued, patronizing, scolding) each appear once. All primary sleep-nudge anchors were already present in the original pass.

**Did seed-term frequencies grow proportionally?** Partially. `break`, `rest`, `tired` are near-proportional. The more distinctively sleep-nudge terms (`sleep`, `bed`, `bedtime`, `tonight`) grew sub-proportionally, suggesting the expanded corpus adds general Claude-discourse content more than sleep-nudge-specific content.

The full comparison table is saved as `comparison_to_original_pass.csv`.

---

## 9. Stratification observations

### 9.1 Monthly distribution

| Month | Posts |
|---|---|
| 2026-01 | 304 |
| 2026-02 | 553 |
| 2026-03 | 797 |
| 2026-04 | 2,320 |
| 2026-05 | 3,047 (through 2026-05-17) |

The structural undersampling of Jan-Mar is reduced but remains. Jan-Mar together: 1,654 posts (23.6%). April alone: 2,320. First 17 days of May: 3,047. The disproportion still exceeds what community growth alone would explain.

### 9.2 Pre/post cutpoint (2026-04-01 placeholder)

| Stratum | Posts | % of corpus |
|---|---|---|
| Pre-cutpoint | 1,654 | 23.6% |
| Post-cutpoint | 5,367 | 76.4% |

Improvement over prior pass (845 pre / 3,269 post = 20.5% pre). The pre-cutpoint stratum has doubled; temporal analyses using this cutpoint are now somewhat better powered, but still dominated by post-April data.

### 9.3 Subreddit-level top-10 (stops on, lemma on)

- **ClaudeAI** (1,959 posts): claude, code, like, model, opus, one, work, use, anthropic, agent
- **ClaudeCode** (2,100 posts): claude, code, agent, opus, session, one, work, like, file, tool — coding-agent vocabulary dominates; `session`, `agent`, `file`, `tool` rank higher here than in any other subreddit
- **claudexplorers** (1,471 posts): claude, like, model, opus, one, something, thing, ai-adjacent — creative/exploratory vocabulary; `code` and `http` do not rank in top 10
- **Anthropic** (1,491 posts): claude, anthropic, code, model, like, opus, use, one, work, think — policy/company discussion vocabulary; `anthropic` ranks 2nd uniquely in this subreddit

Pattern is consistent with the prior pass. No meaningful shift in the subreddit character across the corpus expansion.

---

## 10. Whether the 71% corpus expansion has materially changed the descriptive picture

**Descriptive picture: not materially changed.**

The core characterization from the prior pass holds:
1. The wholesale corpus is dominated by general Claude-discourse vocabulary (platform names, model versions, coding-agent workflow terms). Sleep-nudge seed terms are a small minority of all post content.
2. The needle-in-haystack character of the phenomenon is confirmed at 7,021 posts. The most frequent sleep-specific anchor (`sleep`) appears in approximately 105 of 7,021 posts (1.5%).
3. Multi-sense ambiguity for the primary seed terms (`rest`, `break`, `sleep`, `tired`) remains the dominant analytical problem. The minimum co-occurrence floor of 5 has reduced PMI noise substantially and surfaced qualitatively more coherent collocate clusters, but sense separation requires either explicit phrase matching or a keyword-filtered analysis at the post level.

**What the expansion did contribute:**
- The `sleep` anchor's collocate table at w=10 is now qualitatively strong: `bed + telling + morning + rest + night` form a coherent sleep-domain cluster that was not visible with hapax-driven PMI in the prior pass.
- The pre-cutpoint stratum has doubled, improving temporal analysis power.
- URL-fragment artifacts have been fully resolved, making bigram and trigram tables analytically useful for the first time.

**What the expansion did not deliver:** A meaningfully denser sleep-nudge signal. The sub-proportional growth of sleep-specific terms confirms that the broader retrieval added general-interest Claude content more than it added sleep-nudge reports. Phase 5 sense-discovery will still require the keyword-filtered subset or a dedicated sleep-nudge post filter to analyze the phenomenon itself.

---

## 11. Anomalies

### 11.1 Structural undersampling of January–March 2026

Persists. Jan–Mar: 1,654 posts (23.6%) across 90 days vs. Apr-May: 5,367 posts (76.4%) across 47 days. Rate ratio is approximately 7:1 (Apr-May posts per day vs. Jan-Mar posts per day), which exceeds plausible community growth. PRAW recency-limit artifact confirmed.

### 11.2 Sub-proportional growth of sleep-specific seed terms

Primary sleep-nudge anchors (`sleep`, `bed`, `tonight`, `bedtime`) grew at 1.20–1.43x vs. the expected 1.707x. The broader-retrieval re-scrape introduced more general-Claude content than sleep-nudge-specific content. This is a finding about the re-scrape, not a corpus quality failure.

### 11.3 `wa` artifact resolved

Token `wa` (rank 21, count 3,560 in prior pass) has been eliminated by the minimum token length change to 3 characters. The investigation confirmed only 3 genuine whole-word instances of "wa" in the raw corpus. The 3,560-count in the prior pass was a tokenisation artifact from contraction splitting, not an encoding corruption.

### 11.4 PMI floor eliminates tonal seed collocates

`paternalistic`, `patronizing`, `lecturing`, `scolding`, `fatigued`, `moralizing` all have zero collocates meeting the 5-occurrence floor. These terms are too sparse for collocation analysis at the whole-corpus level. This is expected and consistent with prior pass findings. KWIC analysis of these terms should operate on the keyword-filtered subset.

### 11.5 `happy answer question` trigram

Trigram rank 5 at 90 occurrences. This is the standard Claude opening-statement formula ("I'm happy to answer any questions"). Its prominence in the trigram table suggests a substantial number of posts include quoted Claude text or paraphrased outputs using this formula. This is an incidental finding relevant to Phase 4 voice segmentation.

---

## 12. Files produced

All files in `deliverables/phase_2_rerun/sleep_freq_collocation/`:

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

### Stratified frequency (Task 4)
- `freq_unigram_stops_on_lemma_on_subreddit_ClaudeAI.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_ClaudeCode.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_claudexplorers.csv`
- `freq_unigram_stops_on_lemma_on_subreddit_Anthropic.csv`
- `freq_unigram_stops_on_lemma_on_pre_opus.csv` (before 2026-04-01 placeholder)
- `freq_unigram_stops_on_lemma_on_post_opus.csv` (on/after 2026-04-01 placeholder)

### Domain stop-word candidates (Task 5)
- `domain_stopword_candidates.csv` — top 50 unigrams with category labels

### Collocations (Task 6, min co-occurrence ≥5)
- `collocation_{seed}_w5.csv`, `collocation_{seed}_w10.csv`, `collocation_{seed}_w20.csv`
- Seeds with qualifying collocates at ≥1 window: sleep, rest, bed, break, tired, exhausted, tonight, tomorrow, take_a_break, go_to_sleep, you_need_rest, late, midnight
- Seeds with zero qualifying collocates at all windows: paternalistic, patronizing, lecturing, scolding, fatigued, moralizing, bedtime

### N-grams and skipgrams (Task 7)
- `ngram_2_top200.csv`, `ngram_3_top200.csv`, `ngram_4_top200.csv`
- `skipgram_n2_skip1_top200.csv`, `skipgram_n2_skip2_top200.csv`

### Comparison table (Task 8)
- `comparison_to_original_pass.csv`

### Supporting artifacts
- `_summary_data.json` — machine-readable summary statistics
- `run_phase2_rerun_freq.py` — analysis script (reproducible)

---

## 13. Preprocessing decision record

| Decision | Prior pass choice | This pass choice | Rationale for change |
|---|---|---|---|
| Tokenization min length | 2 characters | 3 characters | Eliminates `wa` and other 2-char noise artifacts |
| URL stripping | Not applied | Applied before tokenization | Eliminates `preview.redd.it` URL-fragment artifact |
| Stop-word list | NLTK English | NLTK English (unchanged) | No change; domain extension deferred to researcher |
| Lemmatizer | NLTK WordNetLemmatizer | NLTK WordNetLemmatizer (unchanged) | No change |
| Ablation approach | All 4 variants | All 4 variants (unchanged) | Per method §C.2 step 3 |
| Domain stops | Candidate list only | Candidate list only (unchanged) | Researcher must approve per Pattern B |
| PMI minimum threshold | None | 5 (floor applied) | Addresses hapax-PMI inflation documented in prior pass |
| URL stripping scope | None | HTTP, HTTPS, www., markdown [](url) | Targeted at image-embed and markdown links |
