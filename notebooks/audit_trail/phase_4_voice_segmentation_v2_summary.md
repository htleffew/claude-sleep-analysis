# Phase 4 Voice Segmentation — v2 Summary

**Script:** `src/voice_segmentation_v2.py`
**Date run:** 2026-05-18
**Input:** `data/pass1b_canonical.csv` (773 rows)
**Output:** `data/pass1b_canonical_voice_segmented_v2.csv`

---

## Parameters

| Parameter | Value |
|---|---|
| Regex layers | 1a (strong-signal DQ, high conf), 1b (paraphrase signals, medium conf), 1c (weak heuristics, low conf) |
| LLM fallback tool | Gemini CLI 0.42.0, model `gemini-3.1-flash-lite` |
| LLM budget cap | 100 calls |
| LLM target rows | `voice_confidence == "low"` from regex layer (592 rows eligible) |
| Sampling strategy | Stratified random sample across post/comment strata, seed = 42 |
| Confidence threshold for §C.4 | high + medium = "reliably segmentable" |
| Random seed | 42 |

---

## V2 Label Distribution

### Overall (773 rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | 31 | 4.0% |
| Paraphrase_Of_Model | 203 | 26.3% |
| User_Original_Content | 539 | 69.7% |

### By stratum — Posts (242 rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | 19 | 7.9% |
| Paraphrase_Of_Model | 58 | 24.0% |
| User_Original_Content | 165 | 68.2% |

### By stratum — Comments (531 rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | 12 | 2.3% |
| Paraphrase_Of_Model | 145 | 27.3% |
| User_Original_Content | 374 | 70.4% |

---

## Confidence Distribution (V2)

| Tier | Count | Percent | Source |
|---|---|---|---|
| high | 246 | 31.8% | Regex Layer 1a + Gemini exact-match responses |
| medium | 35 | 4.5% | Regex Layer 1b + Gemini near-match responses |
| low | 492 | 63.6% | Layer 1c or not sampled for LLM fallback |
| **high + medium** | **281** | **36.4%** | Reliably segmentable |

---

## Comparison to V1

| Metric | V1 | V2 | Change |
|---|---|---|---|
| Direct_Quote_Of_Model | 24 (3.1%) | 31 (4.0%) | +7 rows |
| Paraphrase_Of_Model | 168 (21.7%) | 203 (26.3%) | +35 rows |
| User_Original_Content | 581 (75.2%) | 539 (69.7%) | -42 rows |
| Reliable (high+med) | 182/773 (23.5%) | 281/773 (36.4%) | +99 rows (+12.9 pp) |
| Rows with changed label | — | 44 (5.7%) | — |
| Rows with upgraded confidence | — | 100 | — |
| Rows with downgraded confidence | — | 1 | — |

### Label-shift matrix (V1 label -> V2 label)

| V1 | V2 | Count |
|---|---|---|
| Direct_Quote | Direct_Quote | 23 |
| Direct_Quote | User_Content | 1 |
| Paraphrase | Paraphrase | 168 |
| User_Content | Direct_Quote | 8 |
| User_Content | Paraphrase | 35 |
| User_Content | User_Content | 538 |

The dominant shifts are UOC → PM (35 rows) and UOC → DQ (8 rows), consistent
with the LLM correctly identifying paraphrase and direct-quote signals that
the regex layer missed.  One DQ → UOC demotion is expected from cases where
the blockquote or attribution pattern was a false positive.

---

## LLM Fallback Call Statistics

| Metric | Value |
|---|---|
| Calls issued | 100 |
| Calls succeeded | 100 |
| Errors | 0 |
| Average latency | ~9.3 s/call |
| Min latency | ~8.4 s |
| Max latency | ~15.4 s |
| Gemini-assigned DQ | 8 |
| Gemini-assigned PM | 36 |
| Gemini-assigned UOC | 56 |
| All Gemini responses at high confidence | yes (clean single-label responses) |

Per-call log: `deliverables/phase_4_voice_segmentation/llm_call_log_v2.jsonl`

---

## §C.4 Threshold Determination

The §C.4 decision rule requires **≥ 70% of the corpus to be reliably
segmentable** (high + medium confidence) before voice segmentation results are
used in downstream quantitative analysis.

| | V1 | V2 |
|---|---|---|
| Reliable fraction | 23.5% | 36.4% |
| Meets §C.4 threshold (≥ 70%) | No | No |

V2 improves reliable segmentation by 12.9 percentage points relative to V1,
driven entirely by the Gemini fallback upgrading 100 previously low-confidence
rows.  However, **36.4% remains well below the 70% threshold**.  The 592
low-confidence rows that were eligible for LLM fallback but not sampled
(492 rows after 100 were sampled) continue to hold `low` confidence.

To reach the §C.4 threshold, the remaining ~492 low-confidence rows would need
to be processed.  Options: (a) expand the LLM budget to cover all 592 eligible
rows in a subsequent run, or (b) apply additional regex patterns targeting
corpus-specific signals identified in the validation sample audit.

Until the 70% threshold is met, voice labels should be reported with the
confidence caveat and downstream analyses restricted to the 281 high+medium
rows or treated as exploratory.

---

## Validation Sample

A 70-item stratified validation sample was drawn for human audit:
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v2.csv`

Strata: 20 Direct_Quote, 20 Paraphrase, 30 User_Content, oversampling 30
low-confidence rows to surface potential errors in the LLM fallback tail.

**This sample must be reviewed before v2 labels are treated as publishable
ground truth.**

---

## Recommendation

V2 supersedes V1 as the operational voice segmentation for this corpus.
Reasons:

1. The LLM fallback now works (100/100 calls succeeded vs. 0/100 in v1).
2. Reliable fraction improved from 23.5% to 36.4%.
3. Label shifts are semantically coherent and directionally expected.
4. V1 outputs are preserved at `data/pass1b_canonical_voice_segmented.csv`
   for provenance; the v1 vs. v2 comparison table is at
   `notebooks/audit_trail/phase_4_v1_vs_v2_label_shifts.csv`.

The §C.4 threshold is still not met.  A follow-on run with an expanded budget
(or additional regex patterns) is needed before voice-segmented counts can be
used in primary analysis tables.
