# Phase 2 Pass 1b — Frequency / N-gram / Collocation Summary
**Sleep-Nudge Project**
**Date:** 2026-05-17
**Method version:** `community_reported_llm_behavior_method.md` v1.0; `methods_library.md` §1.1, §1.2, §1.5, §1.6
**Input file:** `data/pass1b_canonical.csv` (Pass 1b targeted-retrieval corpus)
**Output directory:** `deliverables/phase_2_pass1b/sleep_freq_collocation/`
**Executing agent:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Script:** `src/phase2_pass1b_freq_collocation.py`

---

## 1. Corpus processed

| Metric | Value |
|---|---|
| Total rows | 773 |
| Posts | 242 |
| Comments | 531 |
| Subreddits | r/ClaudeAI, r/ClaudeCode, r/Anthropic, r/claudexplorers |
| Retrieval frame | Targeted (search-filtered + iterative Round 2 augmentation) |
| Provenance groups | praw_only: 538, arctic_shift_only: 100, multi_source: 88, canonical_only: 47 |
| Output files produced | 191 CSV/JSON files |

**Corpus note.** This is a targeted-retrieval corpus assembled via iterative seed-term refinement per [methods library §1.9]. It is not a wholesale corpus. Frequency patterns here reflect the seed-term vocabulary, not base rates of any term in untargeted discourse. See [method §C.1] retrieval-mode bias statement. All frequency findings are conditional on the retrieval frame.

---

## 2. Parameter choices

### 2.1 Tokenization

Alpha-only tokens (`\b[a-z]{3,}\b`), minimum length 3, lowercased. Carries forward the canonical re-run fix that resolved the `wa` curly-apostrophe artifact.

### 2.2 URL stripping

Applied before tokenization. Pattern: HTTP/HTTPS URLs, `www.` links, markdown `[text](url)` constructs. Resolves the `preview.redd.it` image-embed fragment artifact that dominated prior trigrams.

### 2.3 Stopword handling

NLTK English stopword list (hardcoded to avoid Claude sandbox NLTK path security conflict). Augmented with WordNetLemmatizer artifacts: `wa` (from "was"), `ha` (from "has"), `doe` (from "does"). These lemmatizer artifacts survive the 3-char length floor and must be listed explicitly in the stop set.

### 2.4 Preprocessing variants (ablation, per method §C.2 step 3)

Four variants computed for unigram, bigram, trigram:

| Stops | Lemmatization | Filename suffix |
|---|---|---|
| Off | Off | `stops_off_lemma_off` |
| Off | On | `stops_off_lemma_on` |
| On | Off | `stops_on_lemma_off` |
| On | On | `stops_on_lemma_on` |

Domain stop-words were NOT applied to the main tables; they are a candidate list for researcher review per [orchestration protocol §3.2 Pattern B].

### 2.5 Collocations

PMI scoring. Window sizes: 5, 10, 20. Collocate side filtered for stop-words and tokens shorter than 3 characters. **Minimum co-occurrence floor of 5** (carried forward from canonical re-run; eliminates hapax-driven PMI inflation).

### 2.6 N-grams and skipgrams

- N-grams at n=2, 3, 4 (top 200 each, stops on + lemma on)
- Skipgrams at n=2, skip distance 1 and 2 (top 200 each, stops on + lemma on)

---

## 3. Top-20 content-bearing unigrams (full corpus, stops on + lemma on)

| Rank | Term | Count | Per 1k tokens |
|---|---|---|---|
| 1 | claude | 1,271 | 36.53 |
| 2 | like | 473 | 13.60 |
| 3 | code | 454 | 13.05 |
| 4 | session | 413 | 11.87 |
| 5 | time | 409 | 11.76 |
| 6 | one | 391 | 11.24 |
| 7 | model | 346 | 9.95 |
| 8 | get | 342 | 9.83 |
| 9 | work | 327 | 9.40 |
| 10 | context | 312 | 8.97 |
| 11 | tool | 310 | 8.91 |
| 12 | thing | 300 | 8.62 |
| 13 | **bed** | **285** | **8.19** |
| 14 | **sleep** | **250** | **7.19** |
| 15 | know | 245 | 7.04 |
| 16 | user | 235 | 6.75 |
| 17 | people | 225 | 6.47 |
| 18 | tell | 225 | 6.47 |
| 19 | file | 222 | 6.38 |
| 20 | day | 220 | 6.32 |

**Observation.** `bed` (rank 13, 8.19 per 1k) and `sleep` (rank 14, 7.19 per 1k) appear in the top-20 for the first time across any Phase 2 pass. In both wholesale passes these terms did not crack the top-500. `tell` (rank 18) and `telling` (rank 29) are also elevated; their prominence reflects the directive-reporting voice of the corpus ("Claude told me to go to bed", "it keeps telling me to sleep"). This is a clear marker of targeted-retrieval signal over general AI-discourse vocabulary.

---

## 4. Domain stop-word candidates (top-50 inspection, stops off + lemma on)

Candidates identified:

| Term | Count | Rationale |
|---|---|---|
| claude | 1,271 | Model name; platform-level; present in nearly every document |
| like | 473 | Discourse filler; missed by NLTK stops |
| model | 346 | Generic AI discourse; not phenomenon-specific |
| one | 391 | Quantifier; not content-bearing |
| get | 342 | Generic action verb |
| use | ~217 | Generic action verb |
| anthropic | ~120 | Company name; platform-level |
| opus, sonnet, haiku | various | Model-version proper nouns |
| prompt, token, context, output, response | various | LLM-discourse vocabulary |

**Researcher checkpoint [Pattern B].** Candidates require researcher review before use in Phase 5 topic modeling. Adding `claude` and `anthropic` is uncontroversial. `like`, `model`, `one`, `get` are judgment calls requiring KWIC confirmation that they are not load-bearing in phenomenon-describing sentences.

---

## 5. Type stratification (post vs comment)

| Term | Post count | Comment count | Comment:Post ratio |
|---|---|---|---|
| bed | 84 | 201 | 2.4x |
| sleep | 107 | 143 | 1.3x |
| nudge | 27 | 47 | 1.7x |
| nagging | 21 | 12 | 0.6x |
| nanny | (low) | 16 | -- |
| bedtime | 22 | 39 | 1.8x |
| telling | 54 | 66 | 1.2x |
| rest | 48 | 35 | 0.7x |
| break | 69 | 60 | 0.9x |

**Key finding.** In the comments stratum, `bed` is the second-most-frequent content term in the corpus (rank 2) and `sleep` is rank 3, both above `code` and `model`. In the posts stratum, both drop to rank 13 and below. This reversal indicates that comments concentrate the specific directive-vocabulary ("go to bed", "told me to sleep") while posts spread over broader framing (the post may describe the general phenomenon or ask for workarounds without centering the specific phraseology). This matters for Phase 3 unit-of-analysis determination: the comment is where the phenomenon vocabulary concentrates.

**Post top-20 contrast.** Posts are dominated by `claude, code, tool, session, context, file, agent` -- consistent with posts being longer, framing-oriented texts about AI tooling. The phenomenon vocabulary (`sleep, bed, nudge, nagging`) is a subset, not the dominant lexical register.

---

## 6. Provenance stratification (three retrieval sources)

Phenomenon-relevant term density per retrieval source (stops on + lemma on, normalized):

| Term | praw_only (538) | arctic_shift_only (100) | canonical_only (47) | multi_source (88) |
|---|---|---|---|---|
| bed | 201 | 41 | 0 | 42 |
| sleep | 148 | 57 | 0 | 43 |
| bedtime | 41 | 13 | 0 | 7 |
| nudge | 48 | 0 | 19 | 0 |
| nagging | 12 | 9 | 0 | 11 |
| nanny | 16 | 0 | 0 | 8 |
| telling | 67 | 17 | 0 | 30 |
| rest | 40 | 11 | 9 | 23 |

**Key finding.** `canonical_only` (posts from the 7,021-post wholesale corpus that happen to match Round 2 terms) has 0 counts for `bed`, `sleep`, `bedtime`, `nagging`, `nanny`, and `nudge`. Its non-zero terms are `nudge` (19) and `rest` (9), which are higher-frequency generic terms even in wholesale discourse. This confirms that the canonical wholesale corpus was not a productive retrieval source for the phenomenon's core vocabulary -- the PRAW and Arctic Shift targeted retrievals did the work. `praw_only` holds the largest share of phenomenon vocabulary by absolute count (538 rows vs 100 for arctic_shift_only), consistent with the PRAW targeted retrieval having produced the densest relevant content. `multi_source` (texts appearing in 2+ retrieval sources) shows strong phenomenon vocabulary, confirming those are the highest-specificity posts.

**Provenance robustness.** The phenomenon vocabulary (`bed`, `sleep`, `bedtime`, `telling`) appears in both `praw_only` and `arctic_shift_only` and `multi_source`, confirming the pattern is not an artifact of a single retrieval source. The `canonical_only` group's absence of core terms is the counter-evidence: those posts were selected by being in the wholesale corpus and matched Round 2 terms, but the Round 2 terms for that group must have been lower-specificity matches (e.g., `nudge`, `rest` in general contexts).

---

## 7. Top collocates of key seed terms (PMI, min co-occurrence ≥ 5)

### `bed` (w=5, top collocates)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| sending | 10 | 7.39 |
| tells | 31 | 7.06 |
| sent | 5 | 7.06 |
| telling | 46 | 6.94 |
| put | 17 | 6.76 |
| told | 38 | 6.74 |
| tonight | 6 | 6.66 |
| late | 8 | 6.00 |
| tomorrow | 7 | 5.96 |
| stop | 12 | 5.38 |

The tight PMI collocates of `bed` at w=5 are exclusively directive-attribution tokens: `sending`, `sent`, `putting`, `tells`, `telling`, `told`, `put`. This is the phenomenon's grammatical signature -- user-reported attribution of the directive to Claude.

### `bed` (w=10, top collocates)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| blah | 6 | 8.10 |
| clock | 5 | 7.47 |
| sending | 10 | 7.39 |
| sent | 6 | 7.32 |
| putting | 5 | 7.32 |
| tells | 35 | 7.24 |
| telling | 51 | 7.09 |
| told | 45 | 6.98 |
| put | 19 | 6.92 |
| late | 15 | 6.91 |

`clock` and `late` appearing at w=10 indicate time-wrong contexts ("sending me to bed at 3pm", "it's 2pm and Claude told me to go to bed").

### `sleep` (w=10, top collocates)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| threshold | 10 | 8.51 |
| caffeine | 14 | 7.62 |
| eat | 9 | 7.29 |
| coffee | 5 | 7.03 |
| telling | 38 | 6.86 |
| hey | 5 | 6.84 |
| finish | 5 | 6.84 |
| tomorrow | 11 | 6.80 |
| wake | 6 | 6.78 |

`caffeine`, `eat`, `coffee`, `threshold` cluster suggests one prominent post about a caffeine-curfew feature or similar biometric context. `tomorrow` and `finish` confirm the "we'll pick this up tomorrow" phrasing pattern.

### `get some rest` (w=10, top collocates)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| morning | 11 | 8.93 |
| often | 5 | 7.44 |
| telling | 9 | 7.38 |
| done | 5 | 6.93 |
| day | 6 | 6.44 |
| sleep | 9 | 6.33 |
| back | 5 | 6.21 |
| work | 8 | 6.11 |

`morning`, `back`, `done` suggest a work-resumption framing: "get some rest, we'll pick this up in the morning / come back to this / we've done enough".

### `nanny` (w=10)
| Collocate | Co-occurrences | PMI |
|---|---|---|
| bot | 12 | 11.06 |
| opus | 7 | 6.90 |
| claude | 7 | 4.22 |

`nanny bot` (PMI 11.06) is the dominant collocate, confirming "nanny bot" as a community compound label for the phenomenon. `opus` co-occurrence flags that the phenomenon is specifically attributed to Opus-family models.

### `nudge` (w=10, top collocates)
Collocates include `gate`, `reply`, `soft`, `immediately`, `triggers`, `drops`, `hard`, `noticed`, `started` -- consistent with a technical discussion of triggering/suppressing the nudge behavior rather than experiential reporting of it.

---

## 8. N-gram and skipgram patterns

### Top phenomenon-relevant bigrams (stops on + lemma on)

| Bigram | Count | Interpretation |
|---|---|---|
| long session | 95 | Context for directives |
| take break | 86 | Directive phrase (stop-word removal drops "a") |
| tell bed | 45 | Directive attribution |
| get rest | 41 | Directive phrase |
| telling bed | 35 | Present-progressive directive attribution |
| told bed | 28 | Past-tense directive attribution |
| claude telling | 21 | Agent attribution |
| telling sleep | 21 | Directive attribution (sleep variant) |
| tell sleep | 21 | Directive attribution (sleep variant) |
| nanny bot | 10 | Community label for phenomenon |

### Top phenomenon-relevant trigrams

| Trigram | Count | Interpretation |
|---|---|---|
| trying put bed | 8 | User pushing back: "trying to put [me] to bed" |
| claude tell bed | 7 | Clear attribution |
| claude keep telling | 6 | Repetition/persistence marker |
| claude told bed | 6 | Past attribution |
| claude telling people | 6 | Generic-user framing |
| never told bed | 6 | Denial / contrast frame |
| claude telling user | 5 | Community meta-commentary |
| claude always telling | 5 | Frequency/persistence marker |
| telling people sleep | 5 | Attribution with target |

### Top phenomenon-relevant skipgrams (skip-dist 1)

`tell bed` (153), `telling bed` (120), `claude telling` (103), `told bed` (93), `telling sleep` (89), `claude bed` (87), `tell sleep` (82) -- all pivot around the verb cluster `tell/telling/told` + the destination noun `bed` or `sleep`. This is the morphological signature of directive-attribution reporting.

---

## 9. Wholesale vs Pass 1b comparison

### Terms present in pass1b top-500 but absent from both wholesale top-500 lists

| Term | Pass 1b count | Pass 1b per 1k |
|---|---|---|
| **bed** | 285 | 8.19 |
| **sleep** | 250 | 7.19 |
| **telling** | 120 | 3.45 |

These three terms crack the top-15 of the Pass 1b corpus but do not appear in the top-500 of either the 4,114-post or 7,021-post wholesale corpora. This is the quantitative confirmation of what the retrieval-mode theory predicts: the targeted corpus concentrates vocabulary that wholesale retrieval dilutes below the detection threshold.

### Terms elevated ≥ 2x in pass1b vs canonical 7,021 (among shared top-500 terms)

| Term | Pass 1b per 1k | Canonical 7,021 per 1k | Ratio |
|---|---|---|---|
| break | 3.71 | 0.86 | 4.3x |
| tell | 6.47 | 2.11 | 3.1x |
| told | 3.28 | 1.24 | 2.6x |
| long | 6.04 | 2.39 | 2.5x |
| take | 4.80 | 2.19 | 2.2x |
| stop | 3.25 | 1.61 | 2.0x |

`break`, `tell/told`, `long`, `take`, `stop` are all either components of directive phrases ("take a break", "go to bed") or their adjacent vocabulary ("long session", "stop working"). The 2x-4x elevation confirms the targeted corpus is denser in directive-adjacent vocabulary even among terms that appear in both corpora.

### Terms not elevated (< 1.2x ratio): general AI discourse terms

`claude`, `model`, `anthropic`, `opus`, `code`, `file`, `agent` all have ratios near 1.0, confirming they are platform-general and not phenomenon-elevated. The targeted corpus is not simply "more of the same AI discourse" -- it is selectively denser in the phenomenon's lexical register.

### Comparison summary table

Full comparison at `deliverables/phase_2_pass1b/sleep_freq_collocation/comparison_wholesale_vs_pass1b.csv` (134 terms, all three corpora normalized to per-1k-token rates).

**Implication for methods.** The wholesale corpora (4,114 and 7,021 posts) would not have been sufficient for Phase 5 topic modeling of the sleep-nudge directive phenomenon. `bed` and `sleep` at < 1 per 1k tokens in wholesale discourse would produce unstable clusters dominated by general AI vocabulary. The targeted corpus achieves 7-8 per 1k on the core terms, sufficient for clustering. This post-hoc validates the [method §1.9] iterative retrieval decision.

---

## 10. Sparsity note on compound phrase collocations

Several compound phrase anchors (`go to bed`, `go to sleep`, `take a break`, `call it a night`, `call it a day`, `pick this up tomorrow`, `put me to bed`, `sent me to bed`, `told me to go to bed`, `unsolicited parenting`) returned 0 collocates meeting the min-cooc floor of 5. This is expected: these exact phrases are rare enough in the 773-row corpus that even window-20 context accumulation does not produce 5+ co-occurrences per collocate.

The single-token anchors (`bed`, `sleep`, `rest`, `nudge`, `nanny`) have adequate density for collocation analysis. The phrase-level patterns are better captured by the n-gram and skipgram tables (see §8).

---

## 11. Parameters documented

| Parameter | Value |
|---|---|
| Input corpus | `data/pass1b_canonical.csv`, 773 rows |
| Tokenizer | Alpha-only `\b[a-z]{3,}\b`, min length 3 |
| URL strip | HTTP/HTTPS/markdown links, pre-tokenization |
| Stop-word list | NLTK English + WNL artifacts (wa, ha, doe) |
| Preprocessing variants | 4 (2x stops x 2x lemma) |
| Top-N per frequency table | 500 |
| Collocation anchors | 21 single-token + 12 phrase anchors |
| Collocation window sizes | 5, 10, 20 |
| PMI min co-occurrence floor | 5 |
| Top collocates per anchor/window | 50 |
| N-gram orders | 2, 3, 4 |
| Skipgram skip distances | 1, 2 |
| Top-N for n-gram/skipgram | 200 |
| Stratifications | full corpus; by type (post/comment); by provenance group (4 groups) |

---

## 12. Researcher checkpoints

**[Pattern B] Domain stop-word candidates.** See §4. `claude`, `anthropic` uncontroversial; `like`, `model`, `one`, `get`, `use` require researcher KWIC confirmation before Phase 5 application.

**[Phase 3] Unit-of-analysis implication.** Comment stratum concentrates phenomenon vocabulary (§5). Recommend examining comment-as-primary-unit in Phase 3.

**[Phase 5 note] Sparsity caveat.** Pass 1b at 773 rows with comments is on the lower edge of BERTopic stability. Phase 5 should run at the 242-post subset and the full 773-row corpus and compare stability. The saturation report already recommends proceeding; this finding supports it.

---

*Generated 2026-05-17 by Sonnet 4.6 from `src/phase2_pass1b_freq_collocation.py`.*
*Prior pass summaries:* `phase_2_freq_summary.md` (4,114 posts wholesale), `phase_2_rerun_freq_summary.md` (7,021 posts canonical wholesale).*
