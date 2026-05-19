# Phase 4 — Voice Segmentation and Tier Assignment (Sleep Project)

**Date of record:** 2026-05-19
**Method version:** `community_reported_llm_behavior_method.md` v1.0 (with 2026-05-19 §C.4 two-tier rewrite)
**Phase:** [method §C.4] Voice Segmentation and Tier Assignment

---

## Outcome

**Sleep Pass 1b canonical corpus (773 rows: 242 posts + 531 comments) stratified into two tiers** per [method §C.4]:

| Tier | Rows | Fraction | Composition |
|---|---|---|---|
| **Tier 1 — segmentable** | 123 | 15.9% | 92 comments + 31 posts |
| **Tier 2 — unitary** | 650 | 84.1% | All other rows |

Tier 1 = at least one model-attributed span (Direct_Quote_Of_Model or Paraphrase_Of_Model) at high or medium confidence covering ≥20% of the row's character count. Tier 2 = all other rows.

Tier assignments recorded at `data/pass1b_canonical_tier_assignments.csv`. Full span breakdown remains at `data/pass1b_canonical_voice_spans.csv` (476 spans, char-count-weighted reliability 27.5%).

## What each tier supports downstream

**Tier 1 (123 rows) supports:**
- Discrete model-vs-user analyses: PMI between user-disclosure features and model-output features.
- Conditional probabilities (P(model directive | user state)).
- Regression of attribution category against contextual covariates.
- Phase 8 inferential claims about how the model speaks when it speaks.

**Tier 2 (650 rows) supports:**
- Theme discovery and characterization of community discussion of the phenomenon.
- Sentiment / affective texture of user reactions and narrative accounts.
- Frequency, collocation, n-gram, and temporal patterns at the row level.
- Cross-stratum descriptive statistics (per subreddit, per retrieval provenance).

**Tier 2 does NOT support:** discrete model-vs-user attribution claims. Phase 8 work that requires knowing which utterance is the model's must operate on Tier 1 only.

## Voice-segmentation pipeline state

- v3-span script: `src/voice_segmentation_v3_span.py` (Gemini Layer 2 zeroed 2026-05-19 due to FM-3f timeout; regex Layer 1 + UC floor Layer 3 active).
- 476 spans across 773 rows.
- Label distribution at the span level: Direct_Quote_Of_Model 79 spans (5.1% of chars), Paraphrase_Of_Model 152 spans (10.3% of chars), User_Original_Content 245 spans (84.6% of chars at low-confidence floor).
- Char-count-weighted reliable-segmentation: 27.5%.
- Known bug: 40/50 rows in the v3-span validation sample have empty span breakdowns. Likely a floor-write issue when LLM_BUDGET=0; deferred for diagnosis. Does NOT affect tier assignment (which derives from the full spans CSV, not the validation sample).
- Documented v3-span failure modes: at `notebooks/audit_trail/phase_4_voice_segmentation_failure_modes.md` (carried forward from v2).

## Hand-validation status

The §C.4 tier-assignment hand-validation is the next researcher task. The validation sample at `phase_4_voice_segmentation_validation_sample_v3_span.csv` is being reworked to:
- Show actual text with inline span markers per the *show content, not meta-description* discipline.
- Ask per-row tier verdict (Tier 1 / Tier 2 / Tier 1 with corrected spans) per Pattern F.
- 40/50 empty-span rows need the floor-write bug fixed first OR re-derivation of the validation sample from the rows where spans actually exist.

## Prior threshold framing — retired

Earlier versions of this Phase 4 record (v1 and v2 row-level segmenters) reported failing the §C.4 70% threshold and treated the corpus as "predominantly paraphrased narrative." That framing is retired as of 2026-05-19. The two-tier structure replaces the pass-fail threshold with an honest epistemic stratification: claims that require discrete attribution rest on Tier 1; claims about theme, sentiment, and discourse structure rest on the whole corpus. See `feedback_two_tier_evidence_structure.md` in the orchestrator's memory for the rationale.

## Cross-reference

- Procedural method §C.4 (rewritten 2026-05-19): two-tier structure.
- Orchestration protocol §3.6: Pattern F (tier-of-evidence checkpoint).
- Methods library §9.0: span-level schema.
- Sleep Phase 3 unit decision: `phase_3_unit_decision.md` (stratification by post/comment retained; tier assignment is the secondary stratification axis).
