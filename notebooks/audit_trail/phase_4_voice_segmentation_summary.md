# Phase 4 — Voice Segmentation Summary

**Date:** 2026-05-17
**Script:** `src/voice_segmentation_v1.py`
**Corpus:** `data/pass1b_canonical.csv` — 773 rows (242 posts, 531 comments)
**Output:** `data/pass1b_canonical_voice_segmented.csv`
**Method:** [method §C.4]; [methods_library §9.1, §9.2, §9.3, §9.4]

---

## 1. Heuristic patterns implemented

The segmenter uses a three-layer architecture:

### Layer 1a — Strong-signal direct-quote markers (high confidence)

Five pattern families, compiled once, applied in order.  First match wins.

| Pattern | Example trigger | Note |
|---------|----------------|------|
| Reddit blockquote `>` | `> Now go to bed` | Covers `>` and `&gt;`; see FM-1a for FP risk |
| Attribution phrase + open quote mark | `Claude said "go to bed"` | Matches `said/wrote/replied` + `"` or `"` |
| Standalone speaker label on own line | `Claude:` followed by content | `^Claude\s*:\s*` (multiline) |
| Speaker label + colon + quote | `Claude: "you need rest"` | Overlaps with above |
| Attribution phrase + quoted block 5–200 chars | `it told me "that's a good place to leave"` | Captures reconstructed verbatim |

### Layer 1b — Paraphrase-signal regex (high/medium confidence)

Seventeen pattern families derived from KWIC Phase 2 inspection and the 25 Round 1
positive cases.  Confidence is high for patterns with specific corpus attestation,
medium for more general attribution-verb patterns.

Key families: `my claude tells me`, `mine is/keeps telling`, `kept telling me`,
third-person model self-attribution (`Claude said it needs to rest`), `basically said`,
`sent/put me to bed`, attribution-verb directives (`told me to go to bed`), `is like`
reported speech, narrative reconstruction (`and then it said`), model-judgment
attribution (`it decides I'm procrastinating`), habitual `would say`, specific corpus
phrases (`asks me to go to sleep`), `tells you to go to bed`, `claude telling users`,
repeated-attribution adverbs (`constantly telling me`), `I asked and it said`.

### Layer 1c — Weak corpus-specific signals (low confidence)

Four additional patterns for the regex residual where no Layer 1a/1b pattern fires.
Assigned low confidence because they carry higher false-positive risk (bare present-tense
attribution, bare `tells me to go to bed` without leading attribution marker, etc.).
These improve label coverage on the ambiguous tail while flagging the items for
researcher scrutiny.

### Layer 2 — LLM-assisted fallback (§9.2)

**Model:** `claude-haiku-4-5` via the Anthropic SDK.
**Design:** A stratified random sample of 100 ambiguous rows (after Layer 1 misses)
is selected before the main loop, proportional to post/comment stratum size.  Each
call sends the row body (truncated to 2000 characters) to claude-haiku-4-5 with a
ternary classification prompt requesting JSON output with `label` and `confidence`.
Every call is logged to `deliverables/phase_4_voice_segmentation/llm_call_log.jsonl`
with row_id, model, full prompt text, raw response, assigned label, timestamp, and
call number.

**Budget:** 100 calls hard-capped.  The 101st call is blocked and the row defaults
to `User_Original_Content/low`.

**Execution status for this run:** All 100 LLM calls failed with authentication error
(`No API key`).  The `ANTHROPIC_API_KEY` environment variable is not set in the bash
subprocess context.  This is a known execution environment limitation.  See FM-3a in
the failure mode log.  To activate LLM fallback: set `ANTHROPIC_API_KEY` and re-run
`python src/voice_segmentation_v1.py`.  The script is idempotent — it clears the
LLM log at the start of each run.

---

## 2. Distribution of voice labels and confidence levels

### Overall

| Label | n | % |
|-------|---|---|
| Direct_Quote_Of_Model | 24 | 3.1% |
| Paraphrase_Of_Model | 168 | 21.7% |
| User_Original_Content | 581 | 75.2% |

| Confidence | n | % |
|-----------|---|---|
| high | 147 | 19.0% |
| medium | 35 | 4.5% |
| low | 591 | 76.5% |
| **high + medium** | **182** | **23.5%** |

### Posts (242 rows)

| Label | n | % of posts |
|-------|---|-----------|
| Direct_Quote_Of_Model | 17 | 7.0% |
| Paraphrase_Of_Model | 49 | 20.2% |
| User_Original_Content | 176 | 72.7% |

### Comments (531 rows)

| Label | n | % of comments |
|-------|---|--------------|
| Direct_Quote_Of_Model | 7 | 1.3% |
| Paraphrase_Of_Model | 119 | 22.4% |
| User_Original_Content | 405 | 76.3% |

### By source (what assigned the label)

| Source | n | Description |
|--------|---|-------------|
| regex | 182 | Layer 1a/1b pattern fired — high or medium confidence |
| regex (low, from 1c) | 10 | Layer 1c weak-signal pattern fired — low confidence |
| llm | 100 | LLM sample selected (all 100 errored; label = UC/low) |
| regex_default | 481 | No pattern fired; defaulted to UC/low |

---

## 3. Reliable-segmentation fraction (§C.4 decision-rule input)

**Reliably segmentable (high + medium confidence): 182/773 = 23.5%**
**Not reliably segmentable (low confidence): 591/773 = 76.5%**

The 23.5% figure is a conservative lower bound under the current execution conditions:
- All 100 LLM fallback calls failed due to absent API key.
- If the LLM calls are re-run successfully, some proportion of the 591 low-confidence
  rows will be upgraded.  Based on the ad-hoc inspection (see §6), a substantial
  portion of those 581 UC/low rows are genuine user-voice content (not model speech),
  so the upgrade may be smaller than the 76.5% rate suggests.

**The §C.4 decision rule requires ≥70% reliable segmentation, or an explicit decision
to treat the corpus as predominantly paraphrased narrative.**

At 23.5% reliable segmentation, the current output does not meet the 70% threshold.
The recommended path forward is:

1. Re-run with `ANTHROPIC_API_KEY` set to activate LLM fallback.
2. Complete the researcher hand-validation of the 70-item sample to establish
   precision-per-category on the regex output.
3. Use hand-validation findings to refine patterns (especially negation handling,
   screenshot detection, indirect report constructions).
4. Document whether the corpus should be treated as a "predominantly paraphrased
   narrative" corpus per §C.4 — this changes what downstream claims can be made.

---

## 4. Failure modes anticipated

See `phase_4_voice_segmentation_failure_modes.md` for the full log.  Summary:

- **FM-1a** Reddit `>` list format triggering blockquote detector (false positive)
- **FM-1b** Other-model attribution triggering patterns (false positive)
- **FM-1c** Negated model attribution labeled as Paraphrase (false positive)
- **FM-2a** No explicit attribution verb (largest false-negative category)
- **FM-2b** Indirect report constructions (false negative)
- **FM-2c** Screenshot-only posts (unclassifiable)
- **FM-2d** Embedded reconstructed dialogue in continuous prose (false negative)
- **FM-3a** LLM fallback unavailable (API key required to activate)

---

## 5. Validation sample: what the researcher needs to do

The hand-validation sample is at:
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample.csv`

**Composition (69 items total):**
- 20 predicted Direct_Quote_Of_Model
- 20 predicted Paraphrase_Of_Model
- 29 predicted User_Original_Content (over-sampled because 10 overlap with low-conf
  stratum — some are genuinely hard-to-classify cases)
- Stratified across post/comment within each prediction class

**Columns the researcher fills in:**
- `researcher_label` — choose from: Direct_Quote_Of_Model, Paraphrase_Of_Model,
  User_Original_Content, Unclassifiable
- `researcher_notes` — free text; please note failure mode type if identifiable
  (FM-1a, FM-1b, FM-1c, FM-2a, FM-2b, FM-2c, FM-2d) and any other observations

**What to do with the results:**
1. Fill in `researcher_label` and `researcher_notes` for each of the 69 items.
2. Compute precision per class: (items where segmenter correct) / (items in that
   predicted class).
3. Record results in `notebooks/audit_trail/phase_4_segmentation_validation.md`
   (the audit-trail document named in the agentic orchestration protocol).
4. Use the precision estimates and failure-mode tallies to decide:
   a. Whether the reliable-segmentation fraction meets the §C.4 70% threshold
      (likely "no" unless LLM fallback substantially upgrades the residual).
   b. Whether to treat the corpus as predominantly paraphrased narrative (§C.4
      documented alternative path).
   c. Which regex patterns to revise in v2 of the segmenter.

**Time budget:** The methods library estimates 1–2 hours for a 50–100 item validation
pass (§9.3).

---

## 6. Predicted segmentation reliability (agent informal inspection)

The following observations are from a 20-item ad-hoc sample inspected before
researcher hand-validation.  This is not a precision estimate; it is the agent's
self-inspection used to calibrate the failure-mode log.

**High-confidence Direct_Quote items (n~5 inspected):**
- Clearly correct: `>Now go to bed` (blockquote, 1 item); `Claude: tells me to go
  to bed` (speaker-label, 1 item).
- Probably false positive: Two posts where `>` marks a Reddit list rather than a
  model quote.
- Estimated precision at high-confidence DQ: ~60–70% (4–5 of ~7 likely correct,
  pending hand-validation).

**High-confidence Paraphrase items (n~5 inspected):**
- Correctly labeled: "My Claude AI running coach... tells me what to do like a coach"
  (correct paraphrase of model behavior); "Okay but how do I get it to stop telling
  me to go to bed" (correct).
- False positive: "Gemini was describing how beautifully the moon..." (other-model
  attribution); "My Claude has Zero concept of time. It's never told me to go to
  bed" (negated directive).
- Estimated precision at high-confidence PM: ~70–80%.

**Medium-confidence Paraphrase items (n~5 inspected):**
- All 5 inspected appeared correctly labeled (e.g., "Claude code told me to go to
  bed at 9am"; "After one question it will tell me to go to bed").
- Estimated precision at medium PM: ~85–90%.

**Low-confidence User_Original_Content items (n~5 inspected):**
- Mostly correct (user narration, no model attribution), but 1 of 5 was clearly
  a Paraphrase miss: "Came here to understand why Claude wants me to pick up again
  tomorrow" (model-attribution missed by regex).
- Estimated precision at low UC: ~75–80% correct UC labeling (meaning ~20–25% are
  actually Paraphrase_Of_Model).

**Overall estimated reliable fraction after hand-validation refinement:** 55–65%
of rows could be reliably segmented with a revised segmenter (v2) incorporating
negation handling and LLM fallback.  The 70% threshold is achievable but not yet met.

---

## 7. Next steps

1. Set `ANTHROPIC_API_KEY` and re-run to activate LLM fallback on the 100-item
   stratified ambiguous sample.
2. Complete researcher hand-validation (§9.3) on the 70-item sample.
3. Based on hand-validation: implement negation pre-screen, screenshot flag, and
   other v2 improvements documented in the failure-mode log.
4. Re-run v2 segmenter and re-compute reliable-segmentation fraction.
5. Document the §C.4 decision: does the updated fraction meet 70%, or is the corpus
   to be treated as predominantly paraphrased narrative?
6. Record checkpoint outcome in `phase_4_segmentation_validation.md` per the
   orchestration protocol (§4.1).
