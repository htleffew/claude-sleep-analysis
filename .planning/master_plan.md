# Master Plan: Sleep-Nudge + LCR Paper Arxiv Submission

Owner: Heather Leffew, PhD. Working solo.

Dependency: LCR paper must be on arxiv with a DOI before the sleep-nudge paper can be submitted, because the sleep-nudge paper's methodological framework cites the LCR paper as the prior empirical work.

---

## Phase 0: Sleep-nudge corrections completed in working session of 2026-05-16

All items in this phase are already merged into `paper/leffew_2026_care-without-consent.md`, the `.tex` mirror, the README, and the methodology documents.

- §6.3 rewrite: dropped the false "recall substantially below 50%" claim; replaced with the measured 84.6% capture rate on the canonical-phrase slice and the 93.5% structural-cue recall lower bound from the new audit
- §6.5 rewrite: dropped the false "OLS without correction" claim; ITS correctly described as using Newey-West HAC SEs; Prais-Winsten GLS and weekly block-bootstrap noted as unrun sensitivity checks
- Table 1: all PMI, lift, NMPI values refreshed against `deliverables/pmi_disclosure_nudge.csv`
- Table 2: all directional values refreshed; ordering reversed (affective now slightly ahead of temporal), narrative reframed honestly
- §4.5 cluster description: rewritten to match `feature_clusters.csv`; the prior "Cluster 4, n=484, P(nudge)=1.00" description was fictional
- §4.1 corpus stats refreshed: 2,266 → 2,279 nudges; 2,186 → 3,051 spans across 2,571 distinct posts; 40 → 34 transcripts; factor ratios 14.6/19.9/20.0 → 14.7/27.7/17.0
- Orphan-figure cleanup: "52 confirmed" → 60, "10 confirmed cases" → 13, "19% of confirmed" → 22%, "81% combined" → 77%, lift 5.3 → 5.0, PMI 2.39 → 2.31
- §3.3 V1 figure corrected: V1 produces 2,602 spans across 2,188 posts, not 2,186 spans
- §3.8 transcript-count discrepancy clarified
- New artifacts: `src/recall_audit.py`, `src/run_v1_baseline.py`, `deliverables/quote_spans_v1.csv`, `deliverables/recall_audit_report.txt`, `deliverables/recall_audit_sample.csv`
- README, methodology document (both copies), supplementary materials lists synced

---

## Phase 1: Sleep-nudge precision and cleanup fixes (small, no decisions required)

Time estimate: 30-45 minutes. Can run in parallel with LCR work.

- C1: §2.3 "Guardrail Paradox" attribution check. The phrase is in the portfolio report (2025b) per the methodology document, not in the Medium article (2025a). Adjust the citation in §2.3 from "(2025a, 2025b)" to "(2025b)" at that specific phrase.
- C2: §4.6 "iatrogenic harm" usage. Add "(Leffew, 2025a)" citation; the term "iatrogenic recursive escalation" was coined in the Medium article.
- C3: "Bit of a character tic" quote precision. Fortune frames it as "is a 'Bit of a character tic'"; adjust the paper's quote so the "a" sits outside the quote marks.
- C4: Liphardt affiliation. Optional. Add "and CEO of OpenMind" or leave compressed; current "Stanford bioengineer" is accurate.
- E1: Delete `deliverables/paper_draft.md` (stale snapshot, no longer referenced).
- E2: Resolve `methodology/Gaslighting_V2_Methodology.md` vs `deliverables/Gaslighting_V2_Methodology.md` duplication. Keep canonical in `methodology/`; remove duplicate.
- E3: Audit `CITATION.cff` for stale fields.

---

## Phase 2: Sleep-nudge substantive additions (drafts for review)

Time estimate: 2-3 hours for drafting, plus Dr. Leffew's review time.

- B2: §6.1 rewrite for solo-coder framing. State conditions clearly; no apology; note schema designed to minimize interpretive latitude; case-level CSV released for independent re-coding.
- B3: §1 clinical-positioning sentence. Establishes author's training in clinical-psychiatric-crisis-intervention. No claims about Anthropic's staffing.
- B7: §5.2 H1 acknowledgment sentence. Notes that under directional construction, H1 (mirroring) sits roughly co-equal with H3 (time-anchoring) and that H4 subsumes both.
- B4: §5.5 clinical-standards paragraph. Evaluates scaffolding for wellness-coded output categories against principles of licensed clinical practice (role-warrant disclosure, evidence-based intervention design, de-escalation primacy, user-context gating). Cites Pope & Vasquez, Joiner. Frames as clinical standards question, not staffing question.
- B5: §4.7.1 harm-taxonomy continuity paragraph. The *kinds* of harms documented in 2025a (induced paranoia, weaponized memory, vulnerability override) reappear in the sleep-nudge corpus with different surface triggers. Empirical claim only.
- B6: §2.3 or §5.X counter-objection paragraph engaging the strongest critique of the clinical-misconduct analogy (LLMs lack role-warrant structure). Counter: the objection mistakes output-category for role-inheritance; objection holds regardless of professional-warrant structure.

---

## Phase 3: Sleep-nudge Phase 3 sampling (methodologically critical)

Time estimate: setup 30 minutes (mine); coding 6-10 hours (Dr. Leffew, at her pace).

- B1.1: Write `src/sample_phase3.py` that draws stratified random N=50 from the 2,279 nudge-positive posts, excluding the 180 already coded in Phase 1+2. Stratification: speaker-label cue presence, work-context lexical hit, pre/post Opus 4.7 release.
- B1.2: Commit the sampling script before any Phase 3 coding begins. Pre-registration documented via timestamped commit.
- B1.3: Generate `deliverables/cases_to_code_phase3.csv` ready for coding.
- B1.4: Write §3.8 Phase 3 design paragraph and §4.6.X Phase 3 results placeholder, both committed to the paper before results are known.
- B1.5: Reframe §3.8 Phase 2 description from "external calibration" to "within-cluster homogeneity check."
- B1.6: Dr. Leffew codes the 50 cases at her pace using the same 9-dimension schema.
- B1.7: Compute Phase 3 summary statistics and fill in the §4.6.X subsection.

---

## Phase 4: Sleep-nudge reproducibility infrastructure

Time estimate: 30 minutes.

- D1: Write `src/freeze_state.py` that generates `deliverables/pipeline_state.json` capturing file hashes (SHA-256), row counts (89,982 / 2,279 / 3,051 / 2,571 / 2,602 / 2,188 / 34 / 60 / 180), base rates (0.0253), and analysis timestamp. Locks released artifacts to the paper's numbers deterministically.

---

## Phase 5: LCR paper audit (transition begins here)

Time estimate: depends on what's there; expect 4-8 hours of audit and edits.

- L1: Read the LCR paper end to end in `C:\Users\drhea\repos\claude-lcr-analysis` (or wherever it lives).
- L2: Apply the same audit framework that surfaced the sleep-nudge problems:
  - Stale figures vs current data
  - Internal contradictions between methods, results, limitations
  - Citations matching what artifacts on disk actually contain
  - V1 vs V2 artifact reconciliation
  - Counter-objection paragraph
  - Solo-coder framing in limitations
  - Clinical-positioning sentence in introduction
  - Cluster descriptions matching released CSVs
  - PMI/ITS tables matching released CSVs
  - Quote precision against external sources cited
- L3: Run an equivalent extractor recall audit if relevant to the LCR methodology
- L4: Build LCR's consolidated correction inventory
- L5: Execute all corrections
- L6: Final consistency sweep

---

## Phase 6: LCR paper arxiv preparation

Time estimate: 2-4 hours.

- L7: Final cold-read pass on the LCR paper
- L8: Compile PDF
- L9: Prepare arxiv metadata (title, authors, abstract, categories — likely cs.CL, cs.CY, possibly cs.AI)
- L10: Dr. Leffew submits to arxiv
- L11: Receive DOI

---

## Phase 7: Sleep-nudge final integration

Time estimate: 30-60 minutes.

- S1: Update sleep-nudge citations of "Leffew (2025b)" to point to the DOI'd arxiv preprint of the LCR paper (which may now be Leffew 2026 depending on submission date).
- S2: Confirm Phase 3 results are integrated.
- S3: Final cold-read pass on the sleep-nudge paper.

---

## Phase 8: Sleep-nudge arxiv submission

- S4: Compile PDF
- S5: Prepare arxiv metadata
- S6: Dr. Leffew submits to arxiv

---

## Sequencing rationale

Phase 1 (sleep-nudge cleanup) can run in parallel with anything else; it doesn't depend on the LCR work.

Phase 2 (sleep-nudge drafts) can be written and reviewed any time; integration into the paper can happen after Phase 7 to avoid late-stage rework.

Phase 3 (sleep-nudge Phase 3 sampling) setup happens before the coding; coding runs at Dr. Leffew's pace and can overlap with LCR work.

Phase 4 (reproducibility) is an end-stage lock and should happen after all content edits.

Phases 5-6 (LCR audit and arxiv) are the bottleneck and should be prioritized.

Phases 7-8 are gated on LCR DOI receipt.

---

## What I am doing right now

Transitioning to Phase 5: opening the LCR paper repository and beginning the audit.
