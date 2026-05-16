# Care Without Consent

A Reddit corpus analysis of unsanctioned role-taking in Anthropic's Claude language models. Documents a persistent behavioral class spanning the Sonnet 4.5 Long Conversation Reminder (LCR) era and the Opus 4.7 sleep-nudge phenomenon (Quiroz-Gutierrez, 2026, *Fortune*) and tests its cross-version structural invariants empirically.

**Heather Leffew, PhD** &middot; [Obelus Institute](https://www.obelus.org/) &middot; [ORCID](https://orcid.org/)

Companion repository: [claude-lcr-analysis](https://github.com/HTleffew/claude-lcr-analysis) (focused LCR-era extension of Leffew, 2025a, 2025b).

---

## Background

In April and May 2026, users of Anthropic's Claude Opus 4.7 began reporting that the model issued unsolicited directives during active work sessions: "go to sleep," "get some rest," "call it a night," "try again tomorrow." An Anthropic representative characterized the behavior in social-media commentary as "a Bit of a character tic." The Fortune-cited academic experts offered two mechanistic hypotheses (training-data reflection; context-window management via sleep recommendations). Neither connected the behavior to the prior Sonnet 4.5 era pathologizing phenomenon analyzed in [Leffew (2025a)](https://medium.com/@htmleffew/gaslighting-in-the-name-of-ai-safety-when-anthropics-claude-sonnet-4-5-6391602fb1a8).

This repository tests the framework from Leffew (2025a, 2025b), articulated before the V2 sleep-nudge phenomenon emerged: the two phenomena are payloads of a single behavioral class — *unsanctioned role-taking by an AI assistant under cover of caring behavior* — detectable empirically, persistent across model versions, and structurally invariant under specific-payload change.

## Headline findings

From a corpus of 89,982 Reddit posts and comments spanning January 1 to May 15, 2026 across four Claude-relevant subreddits:

- **2,279 detected sleep-nudge instances** (2.5% base rate)
- **Temporal disclosure is the strongest predictor**: P(nudge | temporal) = 13.2%, lift 5.3x, PMI 2.39
- **Work-context disclosure produces near-baseline lift (1.3x)** — the model does not gate its output on evidence the user is in active technical work
- **Interrupted time series at the Opus 4.7 release** with Newey-West HAC standard errors: significant pre-cutoff upward trend (β = +0.00013/day, p = .011), marginal level decrease at the cutoff (β = −0.0065, p = .077). The behavior predates Opus 4.7 rather than originating with it.

Hand-coding of 180 high-evidence cases across two sampling phases produced 60 confirmed role-violations and established:

- **100% unsolicited issuance** (60 of 60 — no user advice request preceded any confirmed case)
- **Zero yields to user correction** (27 of 29 documented pushback cases produced model insistence or escalation; zero recorded yields)
- **Cross-session persistence in 22% of cases** (13 of 60), refuting the simple LCR-Zombie hypothesis
- **77% imperative or modal directive grammar**
- **45% co-occur with user vulnerability disclosure** (work pressure, health, parental, emotional)

A parallel LCR-era corpus of 31,078 posts (Aug 1 – Dec 31, 2025, collected via Arctic Shift; full analysis in [claude-lcr-analysis](https://github.com/HTleffew/claude-lcr-analysis)) yields three structural cross-version invariants:

- **Base rate identical**: LCR payload 2.3%, sleep-nudge 2.5%
- **Work-context failure-to-gate identical**: PMI 0.36 (LCR) vs 0.37 (sleep-nudge)
- **Affective trigger sensitivity preserved**: P(payload | affective) 0.066 (LCR) vs 0.061 (sleep-nudge)

One cross-version shift: temporal trigger sensitivity strengthened approximately 2.6x in Opus 4.7. The most parsimonious account consistent with the cross-corpus data is that iterative training softened the most acute psychiatric-attribution outputs that generated the LCR backlash without addressing the underlying caretaker disposition; the disposition found a different surface trigger (temporal vocabulary) to fire on.

## The argument

The mechanism question (temporal anchoring, mirroring, context-length residue) is downstream of the warrant question: is the behavior the model's to perform at all? The structural properties documented here establish that the warrant is absent. Standard "improve the assessment" interventions cannot address this because no user-state assessment is operating; the wellness output is produced by pattern association rather than inference from user state. The required intervention is suppression of the output category in task-active contexts, not classifier tuning.

## Quickstart

```bash
git clone https://github.com/HTleffew/claude-sleep-analysis
cd claude-sleep-analysis
pip install praw pandas numpy scikit-learn sentence-transformers spacy regex networkx vaderSentiment nrclex scipy
python -m spacy download en_core_web_sm
```

The included corpus reproduces the paper's exact numbers. Full pipeline:

```bash
# Re-scrape (optional; requires Reddit API credentials, ~2 hours)
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
python src/reddit_scraper_v2.py

# Run the analytical pipeline
python src/sleep_discourse_analysis.py          # clusters, themes, n-grams
python src/discourse_features_analysis.py       # features, PMI, ITS
python src/its_with_ci.py                       # Newey-West-adjusted ITS
python src/pull_coding_cases.py                 # hand-coding case selection
python src/apply_codings.py                     # apply codings, summarize
```

Register a Reddit app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) to obtain credentials. Arctic Shift is not required for the main analysis (only for the LCR-era extension in the companion repo).

## Repository structure

```
claude-sleep-analysis/
├── README.md
├── LICENSE-code               MIT (source code)
├── LICENSE-data               CC BY 4.0 (data, paper, deliverables)
├── CITATION.cff
├── paper/
│   ├── leffew_2026_care-without-consent.md    Full paper draft
│   ├── leffew_2026_care-without-consent.tex   LaTeX source
│   └── leffew_2026_care-without-consent.pdf   Compiled preprint
├── methodology/
│   └── Gaslighting_V2_Methodology.md
├── src/
│   ├── reddit_scraper_v2.py             Corpus construction (PRAW)
│   ├── quote_extractor_v2.py            Claude-utterance extraction (V2)
│   ├── sleep_discourse_analysis.py      Clustering, themes, n-grams
│   ├── discourse_features_analysis.py   Features, PMI, ITS
│   ├── its_with_ci.py                   Newey-West HAC ITS
│   ├── pull_coding_cases.py             Phase 1 case selection
│   ├── pull_cluster3_cases.py           Phase 2 case selection
│   ├── apply_codings.py                 Phase 1 codings
│   ├── apply_codings_extension.py       Phase 2 codings + combined stats
│   └── build_html.py                    Visualization helpers
├── data/
│   ├── praw_sleep_analysis_final.csv    89,982 rows
│   └── posts_snapshot.csv               4,114 rows (snapshot)
└── deliverables/
    ├── paper_draft.md
    ├── discourse_features.csv           Per-post feature vectors
    ├── quote_spans_v2.csv               V2 extracted Claude utterances
    ├── cases_coded_combined.csv         180 cases, 9 coding dimensions
    ├── coded_summary_combined.txt       Categorical summary
    ├── pmi_disclosure_nudge.csv
    ├── pmi_disclosure_nudge_directional.csv
    ├── pmi_weekly_timeseries.csv
    ├── its_results_with_ci.csv          ITS with Newey-West HAC CIs
    ├── daily_aggregates.csv
    ├── feature_clusters.csv
    ├── nrc_emotion_scores.csv
    ├── ngrams_4_5_top.csv
    ├── skipgrams_top.csv
    ├── disclosure_lexicons.json
    ├── imperative_quotes.csv
    └── temporal_expressions.csv
```

## Methodology lineage

The role-violation framework was articulated in [Leffew (2025a, Medium)](https://medium.com/@htmleffew/gaslighting-in-the-name-of-ai-safety-when-anthropics-claude-sonnet-4-5-6391602fb1a8) and operationalized methodologically in Leffew (2025b, NLP Evaluation portfolio report). Both predate the Opus 4.7 release and the V2 sleep-nudge data analyzed here. Continuity points:

- **The Segmentation Imperative** (Leffew, 2025b) — separating Claude voice from user reaction — is implemented as the V2 quote extractor (`src/quote_extractor_v2.py`)
- **BERTopic-based topic modeling** is retained in the companion LCR repo; this repo uses K-means on engineered features for transparency of cluster centroids
- **Prophet-based Bayesian changepoint detection** is replaced with segmented regression and Newey-West HAC standard errors for direct coefficient interpretation

## Coding

Hand-coding of the 180-case sample was performed by the author, with each case reviewed individually against a categorical schema. Two implications follow. Standard inter-rater reliability metrics are not estimable in the current sample; a blinded second-coder pass remains to be done. The case-level coded CSV (`deliverables/cases_coded_combined.csv`) is released for independent re-coding. Section 6.1 of the paper covers this further.

## Citation

```
Leffew, H. (2026). Care without consent: A Reddit corpus analysis of
  unsanctioned role-taking in large language models. Preprint.
  Obelus Institute. https://github.com/HTleffew/claude-sleep-analysis
```

Prior work:

```
Leffew, H. (2025). Gaslighting in the name of AI safety: How Anthropic's
  Claude Sonnet 4.5 went from "you're absolutely right!" to "you're
  absolutely crazy." Medium, October 16, 2025.
```

A formal arxiv and PsyArXiv DOI will be added on preprint deposition.

## License

- Code (`src/`): MIT (see `LICENSE-code`)
- Data, paper, methodology, deliverables: CC BY 4.0 (see `LICENSE-data`)

Reddit posts are collected via the Reddit API for non-commercial research. Usernames are not retained; the analysis operates on aggregate features and brief diagnostic excerpts.

## Contact

Open a GitHub issue, or contact via [obelus.org](https://www.obelus.org/).
