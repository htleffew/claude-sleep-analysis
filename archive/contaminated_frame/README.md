# Archived: Contaminated Frame

**Status:** Preserved for provenance only. Do NOT treat any artifact in this directory as methodological guidance for the active project.

## What this is

Every artifact under `archive/contaminated_frame/` was produced under a methodological frame that has since been retired. That frame:

- Pre-imposed four user-disclosure domains ("temporal / affective / session-length / work-context") on the sleep-nudge corpus before any descriptive exploration had been performed. These domains became the analytical scaffold and were never themselves derived from the data.
- Treated the four domains as factor-analytically valid without ever conducting the descriptive layer (frequency distributions, collocations, KWIC reads, multi-k topic stability) that would justify a factor-structure claim.
- Subsequently exported those four domains laterally into the sibling LCR project, contaminating that project's frame in turn.
- Operationalized constructs through hand-picked regex lexicons with no stop-word handling, no lemmatization, and no contextual disambiguation.
- Reached for academic-lab tooling assumptions (inter-rater Kappa, API-based programmatic audits, supervised classifiers at scale) that the single-researcher observational design cannot support.
- Built a paper draft (`leffew_2026_care-without-consent.md/.tex/.pdf`) on top of these unvalidated constructs.

## Why it is here, not deleted

The raw scrape data and the scraper code remain at the repo root because they are frame-neutral infrastructure. The archived materials are preserved because:

1. They document the methodological history of the project (provenance).
2. Hand-coded case files contain genuine human judgments that may be re-used under a properly grounded frame.
3. The `pm_html_nested_snapshot/` subdirectory preserves the entirety of a now-removed nested folder (`Pm_html/projects/Claude_Sleep_Analysis_V2/`) that mixed sleep and LCR work; some of its contents are LCR-relevant rather than sleep-relevant. See its own contents for detail.

## What an agent reading this should do

- **Do not** read the archived `paper/`, `notebooks/`, `src/`, `deliverables/`, `figures/`, `methodology/`, `v2_abductive_pipeline/`, or `pm_html_nested_snapshot/` to learn what the project is about or how to proceed.
- **Do** read the root-level `AGENTS.md` and `README.md` for the active methodological frame.
- **Do** read the foundational Medium article and original gaslighting notebook in `C:\Users\drhea\repos\Pm_html\projects\Claude_Gaslighting\` for the phenomenological grounding that applies to *both* the LCR and the sleep work.
