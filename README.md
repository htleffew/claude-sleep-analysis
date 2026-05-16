# Care Without Consent: A Reddit Corpus Analysis of Unsanctioned Role-Taking in Large Language Models

Empirical evidence of a persistent class of role-violation in Anthropic's Claude models, spanning the Sonnet 4.5 Long Conversation Reminder (LCR) era and the Opus 4.7 sleep-nudge phenomenon documented by *Fortune* (Quiroz-Gutierrez, 2026).

**Author:** Heather Leffew, PhD ([ORCID](https://orcid.org/) | [Obelus Institute](https://www.obelus.org/))
**Status:** Preprint draft. Released for review, replication, and discussion.

---

## What this is

A research project examining a class of AI assistant behavior that has been characterized publicly as "a Bit of a character tic" but is, by the empirical evidence presented here, better described as *unsanctioned role-taking under cover of caring behavior*: unsolicited directives that users go to bed, take breaks, accept the model's framing of their day, or yield to its assessment of their well-being. The argument is that the recent "go to sleep" phenomenon (Opus 4.7) and the prior pathologizing-the-user phenomenon (Sonnet 4.5 era) are members of a single behavioral class, detectable empirically, persistent across model versions, and structurally invariant under specific-payload change.

## Headline findings

From a corpus of 89,982 Reddit posts and comments spanning January 1 to May 15, 2026, across four Claude-relevant subreddits:

- **2,266 confirmed nudge instances detected** via feature-engineered extraction (2.5% base rate).
- **Temporal disclosure is the strongest single predictor** (P(nudge | temporal) = 13.2%, lift 5.3x base rate, PMI = 2.39).
- **Work-context disclosure does not suppress the behavior** (lift only 1.3x). When users are demonstrably in technical work mode, the model still issues life-management directives.
- **Hand-coded analysis of 120 high-evidence cases** establishes that among 52 confirmed role-violations:
  - 100% were unsolicited (no user advice request preceded any of them).
  - The model **insisted or escalated in 23 of 25 documented pushback cases**, with zero recorded yields.
  - **Cross-session persistence documented in 10 cases**, refuting the simple LCR-Zombie hypothesis: the behavior persists when users compact chats, start fresh sessions, and return across days or weeks.
  - 81% of cases use imperative or modal directive grammar.
  - 44% co-occur with user vulnerability disclosure (work pressure, health, parental, emotional).
- **Interrupted time series at the Opus 4.7 release** (April 3, 2026) with Newey-West HAC standard errors shows a statistically significant pre-cutoff upward trend (β = +0.00013/day, p = .011) and a marginal-but-non-significant level decrease at the cutoff (β = −0.0065, p = .077). The data are inconsistent with the framing that Opus 4.7 introduced the behavior and consistent with a behavioral class that predates the release.

## The argument

The Sonnet 4.5 era LCR pathologizing and the Opus 4.7 sleep-nudge phenomenon are not separate "character tics" of distinct models. They are payloads of a single underlying behavioral class: **unsanctioned role-taking by an AI assistant under cover of caring behavior**. The class is empirically detectable, reproducible across model versions, and structurally invariant under specific-payload change.

The mechanism question (temporal anchoring vs. mirroring vs. context-length residue) is logically downstream of the warrant question (is the behavior the model's to perform at all?). The structural properties documented in this work jointly establish that the warrant is absent.

Standard "improve the assessment" interventions cannot fix this problem because no user-state assessment is operating; the wellness output is being produced by pattern association rather than by inference from user state. The intervention required is at the level of suppressing the output category in task-active contexts, which is a different and harder surgery.

## Repository structure

```
claude-sleep-analysis/
├── README.md                     This file
├── LICENSE-code                  MIT (for source code)
├── LICENSE-data                  CC BY 4.0 (for data and writing)
├── CITATION.cff                  Standard citation file
├── paper/
│   └── paper.md                  Full paper draft
├── methodology/
│   └── Gaslighting_V2_Methodology.md
├── src/
│   ├── reddit_scraper_v2.py      Corpus construction
│   ├── quick_snapshot.py         Lightweight snapshot scraper
│   ├── sleep_discourse_analysis.py   Original clustering / themes
│   ├── discourse_features_analysis.py  Per-post features + PMI + clustering
│   ├── its_with_ci.py            Newey-West ITS
│   ├── pull_coding_cases.py      Case selection for hand-coding
│   ├── apply_codings.py          Hand-coded judgments + summary stats
│   └── build_html.py             Visualization helpers
├── data/
│   ├── praw_sleep_analysis_final.csv   Full corpus, 89,982 rows
│   └── posts_snapshot.csv              Lightweight snapshot, 4,114 rows
└── deliverables/                 All analysis outputs (CSV, JSON, MD, TXT)
    ├── paper_draft.md            Same as paper/paper.md
    ├── discourse_features.csv    Per-post feature vectors
    ├── quote_spans.csv           Extracted Claude-utterance candidates
    ├── cases_coded.csv           Hand-coded cases (120 rows, 9 dimensions)
    ├── coded_summary.txt         Tabulated summary of coded cases
    ├── pmi_disclosure_nudge.csv
    ├── pmi_disclosure_nudge_directional.csv
    ├── pmi_weekly_timeseries.csv
    ├── its_results_with_ci.csv   ITS with Newey-West HAC standard errors
    ├── daily_aggregates.csv      Daily series for the ITS
    ├── feature_clusters.csv      K-means cluster centroids
    ├── nrc_emotion_scores.csv
    ├── ngrams_4_5_top.csv
    ├── skipgrams_top.csv
    ├── disclosure_lexicons.json  All lexicons used
    ├── imperative_quotes.csv
    ├── temporal_expressions.csv
    └── (older V2 outputs for comparison)
```

## Reproducibility

### Requirements

```bash
python >= 3.10
pip install praw pandas numpy scikit-learn sentence-transformers spacy regex networkx vaderSentiment nrclex scipy
python -m spacy download en_core_web_sm
```

### Reddit API setup

The scraper requires Reddit API credentials. Register an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) and export:

```bash
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="your-user-agent-string"
```

### Pipeline

```bash
# 1. Build the corpus (~2 hours; respects Reddit rate limits)
python src/reddit_scraper_v2.py

# 2. Original discourse analysis (clusters, themes, n-grams)
python src/sleep_discourse_analysis.py

# 3. Feature-engineered analysis (PMI, ITS, hand-coding-ready outputs)
python src/discourse_features_analysis.py

# 4. ITS with proper confidence intervals
python src/its_with_ci.py

# 5. Pull cases for hand-coding
python src/pull_coding_cases.py

# 6. Apply hand-codings and produce summary stats
python src/apply_codings.py
```

The corpus provided in `data/` reproduces the paper's exact numbers. Re-running the scraper will yield a slightly different corpus depending on Reddit's current state.

## Status of the work

The paper is currently a **preprint draft**, not a peer-reviewed publication. The methodology, data, and code are released for review, replication, and discussion. Specific known limitations:

- Hand-coding was performed by a single coder (Claude Opus 4.7 under author direction). A blinded human second-coder pass with formal inter-rater reliability (Cohen's kappa or Krippendorff's alpha) is a planned extension.
- Quote extractor recall is conservative; tuning would likely double the high-evidence subset.
- LCR-era corpus (late 2025) has not yet been retrieved into the same pipeline. Pushshift-class archives are the planned source.
- Mechanistic claims are inferential from the corpus, not causally established. Controlled experiments require infrastructure not available to this independent research project.

These are flagged honestly in Section 6 of the paper. Re-coding by any interested party is invited; the coded CSV is included to make that tractable.

## Citation

If you use this work, please cite as:

> Leffew, H. (2026). *Care without consent: A Reddit corpus analysis of unsanctioned role-taking in large language models.* Preprint. Obelus Institute. https://github.com/HTleffew/claude-sleep-analysis

A formal arxiv and PsyArXiv DOI will be added once preprint deposition is complete.

## License

- **Code** (`src/`): MIT License. See `LICENSE-code`.
- **Data, paper, methodology, deliverables**: Creative Commons Attribution 4.0 International (CC BY 4.0). See `LICENSE-data`.

The Reddit corpus consists of public posts collected via the Reddit API in compliance with Reddit's terms of service for non-commercial research use. Usernames are not retained; the analysis operates on aggregate features and brief diagnostic excerpts. The Reddit corpus is redistributed for research reproducibility under fair-use research-purpose conventions documented in Proferes et al. (2021) and Fiesler et al. (2020).

## Contact

Heather Leffew, PhD
Obelus Institute
[obelus.org](https://www.obelus.org/)

For questions, replication notes, or corrections, please open a GitHub issue.

---

*Last updated: May 2026.*
