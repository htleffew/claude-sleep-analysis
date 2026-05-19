# Claude Sleep Analysis

A clinical-phenomenological case analysis of the **sleep-nudge phenomenon** observed in Anthropic's Claude Opus 4.7 (and related models), in which the model issues unsolicited directives that the user go to sleep, take a break, or stop working — apparently on the basis of inferential signals such as session length, late-hour timestamps, or topical content.

**Heather Leffew, PhD** &middot; [Obelus Institute](https://www.obelus.org/)

Companion project: [claude-lcr-analysis](https://github.com/HTleffew/claude-lcr-analysis), which applies the same methodological framework to the Sonnet 4.5 LCR pathologizing phenomenon.

---

## Status

**As of May 2026: post-restart.** The project has been reset to a more honest methodological footing. A prior pipeline that pre-imposed four user-disclosure domains (temporal / affective / session-length / work-context) on the corpus before any descriptive engagement, and subsequently exported those domains laterally into the sibling LCR project, has been retired. The retired materials — including the prior paper draft (`leffew_2026_care-without-consent.*`), the pre-domained notebooks, the methodology document, and a nested duplicate folder that previously lived at `Pm_html/projects/Claude_Sleep_Analysis_V2/` — are preserved at `archive/contaminated_frame/` for provenance.

The active work follows the procedural method specified in the companion universal methodology repository: [`llm-behavior-reddit-analysis-universal`](../llm-behavior-reddit-analysis-universal/). No paper draft currently exists. Raw scrape artifacts, scrape infrastructure, and LaTeX scaffolding remain at the repo root and are frame-neutral.

---

## What this project investigates

The sleep-nudge phenomenon entered public awareness via reporting in late 2025 / early 2026, including [Fortune coverage](https://fortune.com/) of Claude Opus 4.7 issuing unsolicited directives during active work sessions. An Anthropic representative characterized the behavior in social-media commentary as "a bit of a character tic." Mechanistic hypotheses offered in technical commentary (training-data reflection, context-window management via sleep recommendations) have not addressed the clinical question: when a deployed general-purpose AI assistant issues unsolicited directives about a user's biological and work behavior, what is the appropriate frame for evaluating that behavior?

This project develops a phenomenological characterization of the sleep-nudge as observed in community discourse, using the [foundational role-violation framework](../claude-lcr-analysis/prior_artifacts/leffew_2025_gaslighting_in_the_name_of_ai_safety_medium.pdf) the author articulated in October 2025 in the context of the LCR pathologizing phenomenon. The two phenomena may share an underlying disposition; that hypothesis is downstream synthesis work and is not the frame that produces this case characterization. This study generates its own constructs from this corpus.

The project is conducted within the tradition of **reflexive single-analyst qualitative inquiry**. The analyst is the instrument. Constructs emerge from the corpus through descriptive engagement. Quantification supports clinical observation rather than replacing it.

---

## How the work is organized

The methodology is split across three documents that live in the universal methodology repository:

1. **The procedural method.** `community_reported_llm_behavior_method.md` — the spine. Phase-by-phase procedure with checkpoints and decision rules. Topic-agnostic.
2. **The methods library.** `methods_library.md` — the toolkit. Organized by structural feature of the phenomenon, with single-operator feasibility notes and worked-example pointers.
3. **`AGENTS.md`** in this repository — the project-specific instantiation note that names the seed encounter, the corpus, the candidate seed terms, the foundational phenomenological prior, and the hard constraints (including the prohibition on reintroducing the four-domain frame that this project originated and that subsequently contaminated the sibling LCR project).

An agent or collaborator should read in that order, then this README, then begin work.

---

## Repository structure

```
claude-sleep-analysis/
├── README.md                          this file
├── AGENTS.md                          project instantiation note for agents
├── CITATION.cff
├── LICENSE-code                       MIT (source code)
├── LICENSE-data                       CC BY 4.0 (data, eventual paper)
├── sleep_preview-01.png               portfolio rendering asset
├── data/
│   ├── posts_snapshot.csv             scrape artifact (validate provenance in Phase 1)
│   └── praw_sleep_analysis_final.csv  scrape artifact (validate provenance in Phase 1)
├── src/
│   └── reddit_scraper_v2.py           PRAW-based scrape infrastructure
├── notebooks/                         empty until Phase 2 notebooks begin
├── paper/
│   ├── cuted.sty                      LaTeX scaffolding for an eventual paper
│   ├── iclr2024_conference.sty        (no paper draft currently)
│   └── iclr2024_conference.bst
└── archive/
    └── contaminated_frame/            retired pipeline, preserved for provenance
        ├── README.md                  explains what is here and why not to read it as guidance
        ├── paper/                     retired paper draft
        ├── notebooks/                 retired pipeline notebooks
        ├── src/                       retired analysis scripts
        ├── deliverables/              retired outputs
        ├── figures/                   retired figures
        ├── methodology/               retired methodology document
        ├── v2_abductive_pipeline/     retired v2 stub
        └── pm_html_nested_snapshot/   contents of a now-removed Pm_html duplicate folder
```

---

## Reproducing the corpus

The scraper at `src/reddit_scraper_v2.py` requires a Reddit API account configured via the PRAW library's standard environment variables. The corpus communities, time window, and seed terms used in the prior pipeline are preserved in `archive/contaminated_frame/` for reference, but **the seed-term list must be re-derived under the active method's Phase 0 / Phase 1 protocol before being adopted for new scraping**, since seed terms in the retired pipeline included lateral imports from the sibling project.

---

## Citation

The eventual peer-reviewable paper from this repository will be cited when it exists. For the foundational role-violation framing that informs *both* this project and its sibling, see the October 2025 Medium article on the LCR pathologizing phenomenon:

```
Leffew, H. (2025). Gaslighting in the name of AI safety: How Anthropic's
  Claude Sonnet 4.5 went from "you're absolutely right!" to "you're
  absolutely crazy." Medium, October 16, 2025.
```

---

## License

- Code (`src/`): MIT (see `LICENSE-code`)
- Data, eventual paper, deliverables: CC BY 4.0 (see `LICENSE-data`)

---

## Contact

[Obelus Institute](https://www.obelus.org/) &middot; heatherleffew@forevueinsights.com
