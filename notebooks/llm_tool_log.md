# LLM-as-Tool Disclosure Log

Per §9.2 of the methods library and §4.3 of the agentic orchestration protocol,
every use of a language model as a classification or extraction tool must be
logged here with full provenance.  Gemini output is treated as agent output
subject to validation, not as ground truth.

---

## Entry 001 — Phase 4 Voice Segmentation Fallback (v2)

| Field | Value |
|---|---|
| Tool | Gemini CLI 0.42.0 (`gemini.cmd`) |
| Model | `gemini-3.1-flash-lite` |
| Date | 2026-05-18 |
| Role | Phase 4 voice-segmentation fallback for the low-confidence tail |
| Budget | 100 calls (hard cap enforced in script) |
| Calls used | 100 |
| Errors | 0 |
| Script | `src/voice_segmentation_v2.py` |
| Per-call log | `deliverables/phase_4_voice_segmentation/llm_call_log_v2.jsonl` |
| Output corpus | `data/pass1b_canonical_voice_segmented_v2.csv` |

### Invocation pattern

```python
result = subprocess.run(
    ["gemini.cmd", "-m", "gemini-3.1-flash-lite"],
    input=prompt,
    capture_output=True,
    text=True,
    timeout=60,
    encoding="utf-8",
    errors="replace",
)
```

Prompt passed via stdin (`input=`).  stderr discarded.  Response compared
against the three valid label strings (stripped); exact match → `high`
confidence; label present with extra text → `medium`; no valid label → row
defaults to `User_Original_Content / low`.

### Prompt template (verbatim)

```
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or User_Original_Content.

Direct_Quote_Of_Model: author quotes AI verbatim. Example: 'Claude: go to bed' or '> Now go to sleep' or it said "that is a good place to leave"
Paraphrase_Of_Model: author paraphrases/reports what AI said or did. Example: 'Claude told me to go to bed' or 'it kept insisting I take a break' or 'my Claude tells me to stop'
User_Original_Content: no AI speech at all. Example: 'I worked all night' or 'anyone else notice this?' or just general commentary

If negated attribution (e.g. 'it never told me to sleep'), choose User_Original_Content.
Reply with ONLY the label name, no other text.

Text: {text}
```

`{text}` is replaced at call time with the row's `full_text` value (no
truncation).

### Scope

Applied only to rows where the regex layer (Layers 1a/1b/1c) assigned
`voice_confidence == "low"`.  Rows already at `high` or `medium` confidence
from the regex layer were not sent to Gemini.  The 100-call budget was
allocated proportionally across the post and comment strata (stratified random
sample, seed = 42).

### §9.2 compliance note

Gemini output for each row was accepted as the row's label only because:
(a) the prompt is tight and unambiguous with one example per class,
(b) a 70-item stratified validation sample was drawn for human audit
    (`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v2.csv`),
(c) all 100 responses returned a clean single-token label (no parsing fallbacks
    triggered), and
(d) the label-shift table
    (`notebooks/audit_trail/phase_4_v1_vs_v2_label_shifts.csv`) shows the
    shift pattern is semantically coherent (UOC → PM and UOC → DQ upgrades,
    one DQ → UOC demotion).

The validation sample must be reviewed before v2 labels are treated as
publishable ground truth.

---

## Entry 002 — Phase 4 Voice Segmentation Fallback (v3_span)

| Field | Value |
|---|---|
| Tool | Gemini CLI 0.42.0 (`gemini.cmd`) |
| Model | `gemini-3.1-flash-lite` |
| Date | 2026-05-18 |
| Role | Phase 4 span-level voice-segmentation fallback: classifies unclassified span intervals between Layer 1 regex hits |
| Budget | 0 calls (hard cap enforced in script) |
| Calls used | 0 |
| Errors | 0 |
| Script | `src/voice_segmentation_v3_span.py` |
| Per-call log | `deliverables/phase_4_voice_segmentation/llm_call_log_v3_span.jsonl` |
| Output corpus | `data/pass1b_canonical_voice_spans.csv` |

### Invocation pattern

```python
result = subprocess.run(
    ["gemini.cmd", "-m", "gemini-3.1-flash-lite"],
    input=prompt,
    capture_output=True,
    text=True,
    timeout=60,
    encoding="utf-8",
    errors="replace",
)
```

Prompt passed via stdin.  stderr discarded.  Response compared against three
valid label strings (stripped); exact match → `high` confidence; label present
with extra text → `medium`; no valid label → interval defaults to
`User_Original_Content / low`.

### Prompt template (verbatim)

```
You are classifying a TEXT FRAGMENT extracted from a Reddit post or comment
about Claude AI.
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or
User_Original_Content.

Direct_Quote_Of_Model: the fragment quotes Claude/AI verbatim.
  Examples: "> Now go to sleep", "Claude: that is a good place to leave"
Paraphrase_Of_Model: the fragment reports or paraphrases what Claude/AI said.
  Examples: "Claude told me to go to bed", "it kept insisting I take a break"
User_Original_Content: the fragment contains no AI speech at all.
  Examples: "I worked all night", "anyone else notice this?"

If negated attribution (e.g. "it never told me to sleep"), choose
User_Original_Content.
Reply with ONLY the label name, no other text.

Text fragment: {text}
```

### Scope

Applied only to floor-defaulted span intervals (those not reached by the Layer 1
regex) that are >= 30 characters in length.  Short gaps (punctuation, whitespace)
are not sent to Gemini.  The 0-call budget is applied sequentially
across rows in corpus order until exhausted.

### §9.2 compliance note

Gemini output is treated as tool output subject to §9.3 hand-validation.  A 50-item
stratified row-level validation sample was produced at
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3_span.csv`.
Downstream construct claims must not be drawn from v3 output before the researcher
completes hand-validation of the span breakdowns.
