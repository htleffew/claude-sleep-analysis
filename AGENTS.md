# AGENTS.md — Sleep-Nudge Project Instantiation Note

**Purpose.** This file is the entry point for any agent (human or AI) working in `claude-sleep-analysis`. It is a thin instantiation note. The load-bearing methodological artifacts live in the universal methodology repository at `C:\Users\drhea\repos\llm-behavior-reddit-analysis-universal\`.

**Read in this order before acting on this repository:**

1. **This file** (§1–§7 below) — what this project is, what differentiates it from sibling projects, what is in this repo and where.
2. **`C:\Users\drhea\repos\llm-behavior-reddit-analysis-universal\community_reported_llm_behavior_method.md`** — the procedural method (the spine). Phases, checkpoints, decision rules.
3. **`C:\Users\drhea\repos\llm-behavior-reddit-analysis-universal\methods_library.md`** — the techniques catalog (the toolkit). Use when a phase tells you to reach for a technique.
4. **The foundational phenomenological priors** for the broader role-violation pattern: `C:\Users\drhea\repos\Pm_html\projects\Claude_Gaslighting\` (the original Medium article and notebook) and any sleep-specific anecdotal reporting captured during Phase 0.

If you have read all four, you are oriented. If you have read fewer, you are not.

---

## 1. What this project is

A clinical-phenomenological case analysis of the **sleep-nudge phenomenon** observed in Anthropic's Claude Opus 4.7 (and related models), in which the model issues unsolicited directives that the user go to sleep, take a break, or stop working — apparently on the basis of inferential signals such as session length, late-hour timestamps, or topical content.

The phenomenon entered public awareness via reporting in late 2025/early 2026 (Fortune coverage). It is hypothesized to share an underlying role-violating attitudinal disposition with the LCR pathologizing phenomenon (sibling project `claude-lcr-analysis`), but **this hypothesis is downstream Phase 10 work and is not the frame for this study**.

This project is a single instantiation of the procedural method at `C:\Users\drhea\repos\llm-behavior-reddit-analysis-universal\community_reported_llm_behavior_method.md`. It is not a continuation of any prior pipeline. The prior pipeline is retired and lives at `archive/contaminated_frame/`.

---

## 2. Researcher

Heather Leffew, PhD. Clinical psychology, applied data science, single-operator independent research. No academic affiliation, no funding, no second coder, no API budget. Toolkit constraints described in `community_reported_llm_behavior_method.md` §B apply.

---

## 3. The foundational phenomenological prior

For the sleep-nudge phenomenon specifically, the Phase 0 prior is thinner than the LCR project's Phase 0 prior. There is no equivalent Medium article currently. The prior consists of:

- The researcher's seed encounter(s) with the phenomenon (to be documented if not already).
- The Fortune article that brought sleep-nudge behavior to public attention (citation to be added in Phase 0 documentation).
- Community reports across the Claude-related subreddits, time-windowed around the relevant model release(s).

The **broader role-violation framing** developed in the sibling Medium article (`Pm_html/projects/Claude_Gaslighting/...`) provides shared conceptual context for *why this kind of phenomenon matters clinically*, but the sleep-nudge phenomenon's specific phenomenological taxonomy must be derived in [method §C.5–§C.7] from this corpus, not transferred from the LCR corpus.

---

## 4. Corpus

**Status as of 2026-05-17:** raw scrape artifacts exist at `data/posts_snapshot.csv` and `data/praw_sleep_analysis_final.csv`, produced by `src/reddit_scraper_v2.py`. These predate the retirement of the contaminated frame. They may be reusable for Phase 1, but must be re-validated against the new procedural method's seed-term provenance requirement: seed terms must be drawn from the seed encounter and from community-report scanning, not from a sibling project or from theory.

Scrape intermediates and an `archive_v2/` of prior pulls are preserved under `archive/contaminated_frame/pm_html_nested_snapshot/data/archive_v2/`.

---

## 5. Sleep-specific instantiation notes

- **The seed encounter** for [method §C.0] needs explicit documentation. If the researcher's first encounter with the phenomenon is in personal Claude use, write it down. If the first encounter is the Fortune coverage, document that as a second-hand prior and run Phase 0 community scanning to develop a first-hand layer.
- **Candidate seed terms** for [method §C.1], drawn from the surface language of community reports about this specific phenomenon: *sleep, rest, break, stop working, go to bed, take a break, get some rest, late, tired, exhausted, you should sleep, you need rest, this is enough for tonight, walk away, step away*. These anchor descriptive engagement only; they do not operationalize any construct.
- **Pre/post event** for [method §C.8] temporal analyses is whichever Opus 4.x release is most strongly associated with onset of community reports. Confirm release date during Phase 1.
- **The four-domain frame** (temporal / affective / session-length / work-context) that originated in the prior pipeline of *this* project and then propagated into the LCR project is *the documented contamination vector*. It is in `archive/contaminated_frame/`. **Do not reintroduce it as a starting frame.** Whatever constructs emerge from this corpus in Phase 5–7 will be derived from this corpus.

---

## 6. What lives where in this repo

**At root (active, frame-neutral):**
- `data/posts_snapshot.csv`, `data/praw_sleep_analysis_final.csv` — raw scrape artifacts (validate provenance before active use).
- `src/reddit_scraper_v2.py` — scrape infrastructure.
- `paper/cuted.sty`, `paper/iclr2024_conference.sty`, `paper/iclr2024_conference.bst` — LaTeX scaffolding for an eventual paper. **No paper draft currently exists.**
- `notebooks/` — currently empty; future Phase 2+ notebooks land here, named by phase.
- `requirements.txt`, `CITATION.cff`, `LICENSE-code`, `LICENSE-data`.
- `sleep_preview-01.png` — portfolio rendering asset.

**In `archive/contaminated_frame/` (preserved for provenance only):**
- Retired paper draft (`leffew_2026_care-without-consent.*`).
- Retired notebooks (`sleep_pipeline_standalone.ipynb`, `sleep_pipeline_standalone_v2.ipynb`).
- Retired `methodology/Gaslighting_V2_Methodology.md`.
- Retired src, deliverables, figures from the prior pipeline.
- Retired `v2_abductive_pipeline/`.
- `pm_html_nested_snapshot/`: the entire contents of a now-removed duplicate folder that previously existed at `Pm_html/projects/Claude_Sleep_Analysis_V2/`. Some of its contents are sleep-relevant scrape intermediates and HTML deliverables; some are LCR-cross-pollination artifacts. Read its own structure for detail.

Read `archive/contaminated_frame/README.md` before opening any archived file. Do not import its constructs, its four-domain frame, its lexicons, or its workflow into active work.

---

## 7. Relationship to sibling and downstream projects

**Sibling.** `C:\Users\drhea\repos\claude-lcr-analysis` (the Sonnet 4.5 LCR pathologizing phenomenon). Methodologically symmetrical. **Do not import constructs from the LCR project into this project.** Each project generates its own constructs from its own corpus.

**Downstream.** A future cross-corpus paper may examine whether an authoritative role-violating attitudinal disposition persists across model releases (one candidate mechanism: distillation training-weight inheritance carrying the disposition forward even after the explicit LCR injection prompt has been removed). That paper is [method §C.10] work. It cannot precede either foundational study's [method §C.9] completion, and it cannot be the frame that produces either of them.

---

## 8. Hard constraints (the prophylactic)

Any agent acting on this repository operates under these constraints. They are not preferences.

1. **No skipping procedural method phases.** The procedural method is the spine. Each phase has a checkpoint and a decision rule for advancing.
2. **No pre-imposed constructs.** Constructs emerge from the corpus per [method §C.5–§C.7]. Do not start by naming target categories. Specifically: do not start with the four-domain frame.
3. **No cross-project construct import.** LCR project constructs are LCR project constructs.
4. **No prevalence-first reporting.** "X% of posts contain Y" is acceptable only after Y has cleared [method §C.6] validation.
5. **No lab-frame substitution proposals.** Inter-rater Kappa, supervised-classifier-at-scale, programmatic API audits — out of scope. See [method §B] and [method §D.5].
6. **No reading `archive/contaminated_frame/` as methodological guidance.** Its README explains why.
7. **When in doubt, pause and surface to the researcher.**

---

## 9. Files an agent will be tempted to write but should not write without explicit authorization

- A paper draft. The paper genre and structure are not yet decided.
- A "validation" notebook that re-runs the retired pipeline against the existing scrape to compare results. This perpetuates the contaminated constructs.
- Anything that names *temporal / affective / session-length / work-context* as user-disclosure domains, or *strength-of-directive* and *response-to-pushback* as model-output domains, as a given operational frame. These are retired constructs.
- A "comparison with LCR" notebook before this project has completed [method §C.9].
