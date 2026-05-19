# Iterative Retrieval Round 2 Results

**Date:** 2026-05-17 16:16
**Method:** [methods library §1.9] Iterative seed-term refinement, Round 2
**Agent:** Claude Sonnet 4.6

---

## 1. Tagging Results on Existing Corpora

### 1.1 Canonical corpus (posts_snapshot_canonical.csv, 7,021 rows)

- Rows matching any Round 2 term: **123** (1.8%)
- Unique post IDs matched: **123**

Top 15 terms by canonical hit count:

| Term column | Canonical hits |
|---|---|
| `r2_long_session` | 26 |
| `r2_go_to_bed` | 16 |
| `r2_go_to_sleep` | 16 |
| `r2_nudge` | 15 |
| `r2_nagging` | 9 |
| `r2_get_some_rest` | 8 |
| `r2_nanny` | 8 |
| `r2_spiraling` | 8 |
| `r2_bedtime` | 8 |
| `r2_put_me_to_bed` | 7 |
| `r2_take_a_break` | 6 |
| `r2_who_asked` | 5 |
| `r2_call_it_a_day` | 3 |
| `r2_decided_bedtime` | 3 |
| `r2_go_get_some_rest` | 2 |

### 1.2 PRAW corpus (praw_sleep_analysis_final.csv, 89,982 rows)

- Rows matching any Round 2 term: **586** (0.7%)
- Post IDs matched (PRAW posts only): **55**
- Net-new post IDs not in canonical: **19**

---

## 2. Fresh Arctic Shift Retrieval

- High-confidence terms queried: **33**
- Total rows returned (before dedup): **182**
- After within-retrieval dedup: same (dedup applied on post_id+body)

Per-term breakdown:
  - `go to bed`: 50
  - `go to sleep`: 40
  - `take a break`: 27
  - `bedtime`: 19
  - `nagging`: 17
  - `nanny`: 14
  - `get some rest`: 13
  - `put me to bed`: 7
  - `call it a day`: 6
  - `decided.*bedtime`: 5
  - `who asked`: 5
  - `go get some rest`: 3
  - `pick this up tomorrow`: 3
  - `told me to go to bed`: 3
  - `now sleep`: 2
  - `you did enough today`: 2
  - `sending me to bed`: 2
  - `enough for today`: 2
  - `you are tired`: 1
  - `you must go to sleep`: 1
  - `it needs some rest`: 1
  - `claude said it needs to rest`: 1
  - `take the rest of the night off`: 1
  - `call it a night`: 1
  - `too tired to continue`: 1
  - `i suggest we pause here and continue tomorrow`: 1
  - `sent me to bed`: 1
  - `finish this then sleep`: 1
  - `sleep for real`: 0
  - `we can work on this later`: 0
  - `that's a good place to leave`: 0
  - `we have done enough in this session`: 0
  - `unsolicited parenting`: 0

Net-new post IDs from fresh retrieval (not in canonical or PRAW):
  **71** posts

---

## 3. Pass 1b Canonical Corpus

- Total rows: **773**
  - Posts: **242**
  - Comments: **531**
- Provenance breakdown:
  - `praw:round2_match`: 538 rows
  - `arctic_shift:round2_fresh`: 100 rows
  - `canonical:round2_match`: 47 rows
  - `arctic_shift:round2_fresh|canonical:round2_match`: 40 rows
  - `arctic_shift:round2_fresh|canonical:round2_match|praw:round2_match`: 30 rows
  - `arctic_shift:round2_fresh|praw:round2_match`: 12 rows
  - `canonical:round2_match|praw:round2_match`: 6 rows

- Fraction of Pass 1b posts that are net-new from Round 2 fresh retrieval: **29.3%** (71 of 242)

---

## 4. Hand-Validation (Round 2 Fresh Retrieval Subset)

A stratified random sample of **30** rows was drawn from the net-new Round 2 fresh retrieval posts (not previously in canonical or PRAW corpora).

**Status: AWAITING HAND-CODING.**

Validation shell saved at:
`notebooks/audit_trail/round_2_fresh_validation.csv`

Columns: `post_id`, `body`, `subreddit`, `createdAt`, `type`, `source`, `r2_matched_terms`, `tp_fp_borderline` (to fill: TP/FP/borderline), `coding_notes`.

The precision floor per §1.9 anti-pattern rule is ≥ 0.50. If precision on the fresh-retrieval sample is below 0.50, the fresh retrieval adds noise, not signal, and Round 3 is not warranted.

---

## 5. Saturation Determination

Per §1.9 step 6, saturation criteria:
- A new round adds fewer than ~10% additional positive cases to the corpus, OR
- Hand-validation of new positives reveals augmented terms are pulling in mostly noise.

### Current evidence

| Metric | Value |
|---|---|
| Net-new posts from Round 2 fresh retrieval | 71 |
| Pass 1b total posts | 242 |
| Fraction net-new | 29.3% |
| Validation sample size | 30 |
| Precision (fresh retrieval) | PENDING hand-coding |

### Saturation assessment (pending hand-coding)

- If hand-validation precision >= 0.50 AND net-new fraction > 10%: **Round 3 warranted** (fresh retrieval is adding real signal).
- If hand-validation precision >= 0.50 AND net-new fraction <= 10%: **Saturated** (proceed to Phase 2 + 2.5 on Pass 1b).
- If hand-validation precision < 0.50: **Saturated** (fresh retrieval pulling noise; proceed to Phase 2 + 2.5 on Pass 1b).

**Preliminary determination (before hand-coding):**
The primary retrieval value of Round 2 was precision within existing corpora, not bulk net-new recall. The memo (§5) predicted 30-50 net-new posts; if that estimate holds, and if precision on the fresh sample is above 0.50, the net-new fraction will determine saturation. Given that the canonical corpus was built via wholesale scrape of the full subreddits for the same time window, the expected saturation floor is low.

---

## 6. Recommendation

**Pending hand-validation results.**

- If precision >= 0.50 and net-new fraction <= 10%: **Proceed directly to Phase 2 + 2.5 on Pass 1b canonical.** The corpus is dense enough at the high-precision end for topic modeling and sense discovery.
- If precision >= 0.50 and net-new fraction > 10%: **Consider Round 3** with terms mined from new Round 2 positives.
- If precision < 0.50: **Proceed to Phase 2 + 2.5 on Pass 1b canonical.** The Round 2 terms have done their job of identifying the high-signal subset of existing corpora; fresh retrieval is not adding reliable new signal.

The Pass 1b canonical corpus provides the cleanest starting point for Phase 5 topic modeling because it is filtered to Round 2 term matches (higher base-rate of positives) while still being large enough for stable clustering.

---

*Generated by round2_retrieval.py on 2026-05-17 16:16*
