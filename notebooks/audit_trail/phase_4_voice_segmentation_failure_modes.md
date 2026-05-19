# Phase 4 — Voice Segmentation Failure Mode Log

**Date:** 2026-05-17
**Script:** `src/voice_segmentation_v1.py` v1
**Corpus:** `data/pass1b_canonical.csv` — 773 rows (242 posts, 531 comments)
**Method:** [method §C.4]; [methods_library §9.1, §9.2, §9.3, §9.4]

---

## Overview

This log documents failure modes identified during script design, ad-hoc inspection
of the segmentation output (20-item informal sample), and structural analysis of the
corpus.  It is a required audit-trail artifact under [method §C.4].

Failure modes are grouped by source: false positives (wrong label applied), false
negatives (model-attributed content labeled User_Original_Content), and systematic
structural gaps.

---

## 1. False positives

### FM-1a: Reddit list-format `>` triggering blockquote detector

**Pattern fired:** `blockquote_marker` (Layer 1a)
**Problem:** Reddit uses `>` both as blockquote syntax (quoting model output) and as
list/bullet syntax (user enumerating their own points).  Examples:
  - Post 1sfxa2o: `> Releases awesome 4.6 model\n> Wow, very impressive\n> I buy Claude MAX`
    — this is the user narrating their own timeline, not a model quote.
  - Post 1shjfxb: `> Three stacked bugs in Claude Code make extended thinking silently fail`
    — user's own bug report in blockquote format.

**Impact:** Some posts labeled `Direct_Quote_Of_Model` when they are `User_Original_Content`.
**Conservative estimate of affected rows:** 3–8 of the 24 Direct_Quote rows.
**Mitigation in validation:** The hand-validation sample includes 20 Direct_Quote items;
this failure mode should surface there.

### FM-1b: Other-model attribution triggering model-attribution patterns

**Pattern fired:** paraphrase patterns (Layer 1b)
**Problem:** Several patterns match on other model names (GPT, Gemini, Grok) because
the regex anchors on generic terms (`the model`, `the ai`, `it`).  Example observed
in ad-hoc inspection:
  - "Gemini was describing how beautifully the moon is coming in through the window,
    and how that's nature herself telling me to go to bed" — labeled Paraphrase_Of_Model
    but the model being attributed is Gemini, not Claude.

**Impact:** Affects a minority of rows; the corpus is primarily Claude-focused but
multi-model comparison posts exist.
**Mitigation:** The researcher's hand-validation codes should note model identity.
Downstream analyses should be restricted to rows where Claude attribution is confirmed.

### FM-1c: Negated model attribution labeled as Paraphrase

**Pattern fired:** `tells_me_to_go_to_bed` or similar (Layer 1b)
**Problem:** Patterns match the directive phrase without detecting negation.  Example:
  - "My Claude has Zero concept of time. It's never told me to go to bed."
    — labeled Paraphrase_Of_Model because "told me to go to bed" matches, but
    the user is describing the absence of the behavior.
  - "I never get 'go to sleep'" — same issue.

**Impact:** Modest; negation-denial posts exist in the corpus (users asserting they
have NOT experienced the behavior).  Falsely including them as Paraphrase inflates
the Paraphrase count and may bias downstream frequency estimates.
**Mitigation:** Negation pre-screen (regex for `never told|hasn't told|don't get|
never get`) before firing paraphrase patterns.  Not implemented in v1; flagged for
v2.  Researcher should note negated attributions in hand-validation.

---

## 2. False negatives (model-attributed content labeled User_Original_Content)

### FM-2a: Paraphrase without an explicit attribution verb

**Problem:** Many posts describe model behavior using noun-phrase constructions
without a verb trigger:
  - "Came here to understand why Claude wants me to pick up again tomorrow after
    an hour of work" — labeled UC-low (regex missed "wants me to pick up" as
    paraphrase; the weak Layer 1c pattern for `wants me to` did not trigger because
    `pick up` is not in the restricted set).
  - "Claude escalating bedtime" — post title only; no attribution verb in the body
    fragment visible to the segmenter.
  - "The default-to-utc thing... that's late I just internally pattern-match...
    soften the tone suggest wrapping up" — embedded self-attribution by the model
    presented as exposition, not as a user report.

**Impact:** Likely the largest category of false negatives.  Posts that narrate
model behavior as established community knowledge ("yes, Claude does this") may
not contain a standard attribution phrase.

**Mitigation:** Requires LLM fallback or more sophisticated dependency-parse
approach.  The 100-item LLM sample was designed to address this but failed in the
current run due to API key unavailability (see FM-5).

### FM-2b: Indirect report constructions

**Problem:** Users sometimes report the phenomenon without attributing it to a
specific model utterance:
  - "If I got a dollar every time claude told me to go to bed I'd be rich" —
    this is Paraphrase (by the `told me to go to bed` pattern) and was correctly
    caught, but more indirect forms like "the bedtime thing is so real" or
    "classic claude behavior" are not.
  - "Claude always trying to put me to bed" — caught by `weak_habitual_attribution`
    (Layer 1c, low confidence); correctly labeled Paraphrase/low.

### FM-2c: Screenshot-only posts

**Problem:** Some posts report model speech via embedded images (screenshots of
Claude conversations).  The body text contains a URL to the image but no transcribed
model speech.  Example:
  - Post with body `https://preview.redd.it/ydy2bsgdvzwg1.png...` — labeled
    UC-low because no text attribution phrase exists.

**Impact:** Unknown; the corpus is text-only in the `body` column.  Screenshot posts
that do not transcribe the model output are unclassifiable without image OCR.
**Mitigation:** Flag these as `unclassifiable_screenshot` in a future version.
The validation sample should include at least one such row.

### FM-2d: Embedded reconstructed dialogue without speaker-label formatting

**Problem:** Users reconstruct model dialogue inline without using ":" or blockquote
formatting:
  - "it says me close and go to sleep now it is 5am tomorrow you will continue -
    also tomorrow at 11am it says i said you go to sleep" — complex narrative
    reconstruction mixing model and user speech without formatting.
  - "I asked what he meant by tired and he basically gas lighted me and made it
    out that actually i'm the one who looks tired" — multi-turn attribution in
    continuous prose.

**Impact:** These rows require a dependency-level analysis of attribution.  The
regex layer cannot reliably segment them.

---

## 3. Structural gaps

### FM-3a: LLM fallback unavailable (execution environment)

**Problem:** The Anthropic SDK was installed but the `ANTHROPIC_API_KEY` environment
variable is not set in the bash subprocess context used by `voice_segmentation_v1.py`.
All 100 LLM calls errored silently and defaulted to `User_Original_Content/low`.

**Status:** The LLM fallback is designed correctly (stratified random sample,
budget enforcement, per-call logging).  It requires the researcher to set
`ANTHROPIC_API_KEY` in the environment before running, or to run the script
inside the Claude Code session where the key is available.

**Workaround:** Researcher should run `export ANTHROPIC_API_KEY=<key>` before
executing `python src/voice_segmentation_v1.py`.  The script will then use the
100-call budget on a stratified sample of ambiguous rows.  The LLM log will
record all calls for audit-trail purposes.

**Impact on current output:** The 591 rows labeled `User_Original_Content/low`
(of which 405 are comments and 186 posts) include an unknown proportion of true
Paraphrase_Of_Model rows that the regex missed.  The reliable-segmentation
fraction of 23.5% is a lower bound.

### FM-3b: Budget exhaustion on first-come-first-served ordering (v1 design issue; fixed)

**Problem:** The first version of the script sent LLM calls to rows in index order,
exhausting the budget at row ~200 and leaving rows 200–773 as regex defaults.
**Status:** Fixed in current version.  The script now draws a stratified random
sample of ambiguous rows before the loop and dispatches the budget proportionally
across post and comment strata.

### FM-3c: Paraphrase patterns do not distinguish Direct_Quote from Paraphrase in
all cases

**Problem:** Some rows contain a mix of direct quote and paraphrase in the same post.
The segmenter assigns a single row-level label; it does not segment within-row
speech boundaries.  This is a known limitation of row-level (vs. snippet-level)
segmentation.

**Impact:** Row-level labels are correct in the sense that "this row contains
model-attributed speech"; they are incomplete in distinguishing which words are
quoted and which are paraphrase.  Downstream construct analysis should treat the
label as "this post/comment contains model-attributed speech" rather than "all
model-attributed speech in this row is of this evidentiary type."

---

## 4. Failure modes anticipated but not yet confirmed

- **FM-4a: Paraphrase of model reasoning presented as user insight.** Users
  may report model output as if it were their own conclusion ("turns out the
  responsible thing is to stop here tonight"). These are indistinguishable
  from user speech without the attribution context.
- **FM-4b: Community-aggregate paraphrase.** Posts summarising many users'
  experiences ("hundreds of people have had Claude tell them to go to sleep")
  contain model-attributed speech embedded in meta-commentary.  The segmenter
  may label the post Paraphrase when the user-voice content is dominant.
- **FM-4c: Ironic / humorous inversion.** Posts like "get some sleep Claude" where
  the user is ironically directing the model.  May be labeled Paraphrase if the
  sentence structure matches a model-attribution pattern.

---

## Summary table

| ID | Mode | Layer affected | Direction | Impact estimate | Mitigation |
|----|------|---------------|-----------|----------------|------------|
| FM-1a | Reddit `>` as list, not blockquote | 1a | FP | Low-moderate | Hand-validation |
| FM-1b | Other-model attribution | 1b | FP | Low | Restrict to Claude mentions |
| FM-1c | Negated attribution | 1b | FP | Low | Negation pre-screen |
| FM-2a | No explicit attribution verb | 1b | FN | **High** | LLM fallback |
| FM-2b | Indirect report | 1c | FN | Moderate | LLM fallback |
| FM-2c | Screenshot-only posts | all | FN | Low | Flag unclassifiable |
| FM-2d | Embedded reconstructed dialogue | all | FN | Moderate | Future: snippet segmentation |
| FM-3a | API key unavailable for LLM | 2 | Systematic | **High** | Set ANTHROPIC_API_KEY |
| FM-3b | Budget exhaustion ordering | 2 (fixed) | Systematic | Fixed | Stratified sample |
| FM-3c | Row-level vs. snippet-level | all | Scope limit | By design | Document in writeup |

---

*Researcher action:* The hand-validation sample at
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample.csv`
contains items from all confidence levels.  As you code each item, please note
in `researcher_notes` whether the error type matches one of the modes above.
This will support a precision-per-category estimate and revision of the segmenter.
