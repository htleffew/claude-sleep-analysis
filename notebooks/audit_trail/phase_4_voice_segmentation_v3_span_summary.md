# Phase 4 Voice Segmentation — v3 Span-Level Summary

**Date:** 2026-05-18
**Script:** `src/voice_segmentation_v3_span.py`
**Corpus:** `data/pass1b_canonical.csv` — 773 rows (242 posts, 531 comments)
**Method:** [method §C.4]; [methods_library §9.0, §9.1, §9.2, §9.3]

---

## 1. Total spans produced

**476** spans across 773 rows.
Total corpus character count: 163,117

---

## 2. Distribution by label (span count and character count)

| Label | Spans | % of spans | Characters | % of chars |
|---|---|---|---|---|
| Direct_Quote_Of_Model | 79 | 16.6% | 8,370 | 5.1% |
| Paraphrase_Of_Model | 152 | 31.9% | 16,766 | 10.3% |
| User_Original_Content | 245 | 51.5% | 137,981 | 84.6% |
| Unclassifiable | 0 | 0.0% | 0 | 0.0% |

---

## 3. Distribution by confidence

| Confidence | Spans | % of spans | Characters | % of chars |
|---|---|---|---|---|
| high | 222 | 46.6% | 42,805 | 26.2% |
| medium | 20 | 4.2% | 2,051 | 1.3% |
| low | 234 | 49.2% | 118,261 | 72.5% |

---

## 4. §C.4 reliable-segmentation fraction (70% threshold)

The §C.4 threshold is computed as:
> sum of high + medium confidence spans' character counts ÷ total corpus character count

- High-confidence character count : 42,805
- Medium-confidence character count: 2,051
- High + medium total              : 44,856
- Total corpus characters          : 163,117
- **Reliable-segmentation fraction : 0.275 (27.5%)**

**§C.4 threshold determination: DOES NOT MEET the 70% threshold.**

---

## 5. Per-type stratification (post vs comment)

### 5a. Span label distribution

| Type | Direct_Quote | Paraphrase | User_Content | Unclassifiable |
|---|---|---|---|---|
| post | 71 | 51 | 134 | 0 |
| comment | 8 | 101 | 111 | 0 |

### 5b. Confidence distribution by type

| Type | High | Medium | Low |
|---|---|---|---|
| post | 128 | 10 | 118 |
| comment | 94 | 10 | 116 |

---

## 6. Source distribution

| Source | Spans |
|---|---|
| regex | 226 |
| floor | 151 |
| llm:gemini-3.1-flash-lite | 99 |

LLM calls used: 0 / 0 budget
LLM call errors: 0

---

## 7. Comparison to v2 row-level: §C.4 threshold under corrected schema

**v2 (row-level, deprecated):** the §C.4 reliable-segmentation fraction was
computed as the proportion of *rows* with high or medium confidence labels.
That measure treated a 10-character row identically to a 10,000-character row.

**v3 (span-level, corrected):** the fraction is computed as
*character-count-weighted* coverage of high + medium confidence spans.
This is the correct operationalization per §9.0 of methods_library.md.

v2's row-level fraction over-counted rows where a single clause triggered
a high-confidence regex match but the surrounding paragraphs were floor-
defaulted User_Original_Content.  v3 correctly weights those surrounding
paragraphs at their actual character count, which lowers the threshold
metric relative to v2's count-based report.

---

## 8. v3-span-specific failure modes observed

| ID | Mode | Direction | Span-level impact |
|---|---|---|---|
| FM-SB1 | Sentence-boundary expansion over-labels adjacent neutral text | FP | Sentence that contains the trigger phrase is labeled entirely, dragging neutral clauses into model-attribution spans |
| FM-SB2 | Very short floor gaps (< 30 chars) skip LLM; assigned floor | FN | Connective phrases, punctuation, and transition words between attributed sentences default to User_Original_Content/low rather than being promoted |
| FM-SB3 | Multi-sentence narrative reconstructions span several sentences; regex captures only the triggering sentence | FN | Text before and after the matching sentence may be part of the same attributed narration but falls into floor spans |
| FM-1a | Reddit `>` as list, not blockquote (inherited from v2) | FP | Blockquote pattern labels the entire '>'-prefixed sentence as Direct_Quote |
| FM-1c | Negated attribution (inherited; negation pre-screen partially mitigates) | FP | Negation pre-screen fires on a 30-char window before the match; negations located after the match are missed |
| FM-2c | Screenshot-only posts: no text to segment | FN | Entire body defaults to floor User_Original_Content/low |

---

*Validation sample:* 50 rows at
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3_span.csv`.
Researcher review of `span_breakdown_serialized` column constitutes the §9.3
hand-validation step.  The §C.4 70% threshold determination above is provisional
pending that review.
