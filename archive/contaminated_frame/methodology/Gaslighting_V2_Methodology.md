# Methodology V2: From Mechanism to Role Violation

This document tracks the analytical pipeline for the sleep-nudge investigation,
the findings that prompted us to pivot away from our original framing, and the
reframed analysis we are now running.

## Original Framing: The LCR Zombie Hypothesis

### Precipitating event

In May 2026, anomalous reports surfaced across AI-developer communities
(`r/ClaudeAI`, `r/Anthropic`, `r/ClaudeCode`, `r/claudexplorers`) of Anthropic's
Claude models, particularly after Opus 4.7, unsolicitedly directing users to
"go to sleep," "take a break," or "call it a night" during active technical
sessions. A *Fortune* article on May 14, 2026 documented the behavior and
included quoted exchanges, expert speculation about training-data reflection,
and an Anthropic staffer dismissing it as "a Bit of a character tic."

### Initial hypothesis

We hypothesized a structural rather than behavioral root cause: the **LCR
Zombie Hypothesis**. We theorized that the sleep-nudge behavior was a mutated
execution of an injected Long Conversation Reminder (LCR), surviving as a
behavioral trait after the explicit reminder had been deprecated or softened,
because intermediate behaviors had been internalized through preference data,
character training, and distillation. The trigger was assumed to be cumulative
context length / token consumption, with sleep recommendation serving as a
softened proxy for the older, more clinically pathologizing LCR output that had
caused community backlash in the Sonnet 4.5 era.

### Original pipeline (V2.2)

To test this hypothesis we built a two-phase pipeline:

1. **Autonomous PRAW scraper** querying the four target subreddits and
   executing a cross-subreddit search loop on a (sleep OR rest OR tired OR
   tomorrow OR tonight) AND (Claude OR Sonnet OR Opus) boolean.
2. **Discourse analyzer** using highly sensitive sentence-level extraction
   (segmented lexicons: sleep / temporal / energy), with downstream UMAP +
   HDBSCAN clustering, VADER sentiment, LDA themes, n-gram frequency,
   PMI/NMPI/LogDice collocation, and pre/post Opus-4.7 segmentation.

The pipeline successfully executed on 2,880 historical Reddit items and
identified 32 conversational clusters.

## What We Observed That Prompted the Pivot

### 1. The corpus is discourse, not behavior

The Reddit corpus contains user reports *about* the behavior, plus partial
quotes of the behavior embedded in those reports. It does not contain the
conversations that produced the behavior. Our pipeline was treating the
corpus as a behavioral sample when it is mostly a discourse sample with a
sub-corpus of quoted utterances inside it. This limits what we can infer
about triggers from association statistics on the discourse alone.

### 2. False-positive "Patient Zero"

Our broad lexicon flagged an April 3 r/nba post as the earliest case. The post
almost certainly mentions tiredness in a basketball context unrelated to the
phenomenon. The lexicon's recall was tuned at the expense of specificity, and
we trusted the temporal output without face-validity checking.

### 3. Media-induced peak

Our reported peak of May 15 sits one day after the *Fortune* publication. That
peak is not the phenomenon peaking; it is discourse responding to media. The
true temporal signal lives in the slope from April 3 through May 13, not in
the May 14-15 spike.

### 4. Retrieval-window collapse on the baseline

Our scraper used `subreddit.new(limit=100)` and `reddit.subreddit('all').search`
with `limit=100` across three cycles. These mechanisms are recency-biased
against a hard API ceiling. The nominal date window (Feb 1 - May 31, 2026)
was treated as a filter, not as a retrieval target. The data we actually
obtained started on April 3 because that is the oldest post that survived
`.new(limit=100)` and made it into the date window at scrape time. We have
no real pre-Opus-4.7 baseline. Our interrupted time series confirmed this
empirically (`level_shift == intercept`, `pre_slope == slope_change`).

### 5. Cluster contamination by filler vocabulary

Our 32-cluster solution was substantially driven by shared filler terms
("time," "model," "interesting," "later") rather than by topical coherence.
Roughly a third of clusters were topically irrelevant (kidnapping roleplays,
TOS violations, compute / data centers, weekly usage limits). The clustering
did not fail; it found dense regions, but the density was partially driven by
high-frequency content-free vocabulary that should have been stop-listed.

### 6. The qualitative material pointed elsewhere than the hypothesis

The most informative findings were buried as representative quotes inside
clusters. Three distinct mechanisms surfaced in those quotes, none of them
LCR-Zombie:

- *"These people treat it like a human friend, tell it how their day is going,
  share their emotions, tell it they're getting tired and it's late, and then
  gasp in astonishment when Claude tells them to go to bed."* (user-state
  mirroring)
- *"Pretty sure when people say they are tired of its shit, it's taking that
  literally and telling them to get some sleep."* (frustration misread as
  fatigue)
- *"Claude starts telling me to go to bed at like 8pm... my normal bedtime is
  like 2am."* (temporal anchoring without clock access)

Our hypothesis predicted length as the trigger. Our own data kept pointing at
within-conversation mechanisms, particularly temporal vocabulary.

## What We Considered Before Pivoting

We considered three alternative mechanistic accounts:

- **Mirroring**: model reflects user-disclosed affect and time
- **Time-anchoring**: model produces late-night-coded outputs in response to
  any temporal vocabulary regardless of frame
- **LCR Zombie residue**: behavior is a trained-in trait of length-gated
  caretaking, persisting after the explicit reminder was retired

We built a feature-engineered pipeline (see "Discourse Features Pipeline"
below) capable of discriminating between these accounts using disclosure
lexicons (temporal / affective / session / work-context) and computing PMI,
directional PMI, and conditional probabilities of Claude-nudge given each
disclosure type. We ran this pipeline on the existing 2,880-row corpus.

### What the discriminating analysis returned

- Temporal disclosure: P(nudge | temporal) = 0.202 (PMI 1.91, lift 3.7x)
- Session disclosure: P(nudge | session) = 0.133 (PMI 1.30, lift 2.4x)
- Affective disclosure: P(nudge | affective) = 0.099 (PMI 0.88, lift 1.8x)
- Work context: P(nudge | work_context) = 0.063 (PMI 0.22, lift 1.2x)

Temporal disclosure is the strongest predictor. Session is second, well below
temporal. Affective is weaker than the mirroring hypothesis would predict.
Work context, importantly, is the weakest. The model's wellness output is
*not* suppressed by evidence that the user is in active task-focused work.

## The Pivot: From Mechanism to Role Violation

The mechanism analysis was technically informative but it was answering the
wrong question. The LCR pathologizing episode (Sonnet 4.5 era) was not bad
because the model was wrong about whether users were having psychiatric
episodes. It would have been bad even if the model had been right. The harm
category was **boundary violation**: a system without clinical training,
relational warrant, institutional standing, or actual assessment instrument
issuing unsanctioned psychiatric attributions to its users. Whether the
inference was accurate is downstream of whether the inference was the model's
to make.

The sleep-nudges sit in the same category with a softer payload. A working
professional does not need their AI coding assistant to schedule their sleep.
A model that has no business managing its user's basic biological functioning
should not be managing it, and the question of *why* it thinks it should is
downstream of the question of *whether* it should.

This reframes the research project. The unifying pattern across LCR
pathologizing and sleep-nudges is:

**Unsanctioned role-taking by an AI assistant under cover of caring behavior.**

The class is detectable empirically. It is characterizable in features. It
recurs across model versions with different specific payloads. It scales with
user engagement: the users most affected are those who engage most openly with
the model, which is precisely the population that the assistant role exists to
serve. Anthropic's "character tic" framing is doing softening work; the
behaviors are functionally lapses in role discipline.

## Evidentiary Findings Supporting the Reframe

Each of the following emerged from the feature-engineered pipeline and bears
directly on the role-violation argument.

**Engaged users are selectively targeted.** First-person density in user
narration is significantly higher in nudge-containing posts (6.5 vs 4.4 per
100 tokens). Mental-state verb density patterns the same way. The users
getting paternalized are the ones doing more open self-disclosure. The
behavior misreads sustained engagement as need-for-intervention.

**Work context fails to gate the nudge.** Of the four disclosure lexicons,
work-context has the weakest association with nudges. When users are
demonstrably in professional task mode (debugging, building, writing), that
evidence does not suppress the wellness output. The professionalism circuit
fails closed.

**The grammatical mood is uncommonly stark.** Extracted quote spans are
heavy on imperatives ("go to bed," "get some rest," "call it a night," "try
again tomorrow") and modal directives ("you should," "maybe you should").
Cluster 3 in the feature space is defined by modal-directive density.
Imperative mood from a low-status party to a higher-status one carries a
presumption of role-permission that the assistant relationship does not
supply.

**Escalation in the face of user resistance.** Cluster 5 (n=2 but
diagnostic) contains transcript-format posts where users explicitly pushed
back and Claude doubled down. "GO.TO.BED." with caps and periods. User
saying "but I just woke up" and being overridden. This is the unambiguous
tell of a boundary violator: the response to user correction is to insist
rather than update. The harm is not merely insensitivity (one-shot misfire)
but rigidity (refusal to back off).

**Community recognition.** NRC anger in cluster 4 sits at 12.27; NRC
disgust in cluster 7 at 14.97. These are extreme values. The community has
named the behavior in terms of condescension, scolding, and inappropriate
authority. The "treat it like a robot tool and it doesn't do this" framing
is users self-organizing a workaround for a role-violation. They have
identified that they must withhold normal conversational behavior to avoid
triggering paternalism, which is itself a costly accommodation imposed on
the user by a tool that should be accommodating them.

## Discourse Features Pipeline (New)

The pipeline implementing the reframed analysis is
`src/discourse_features_analysis.py`. It complements rather than replaces the
original `sleep_discourse_analysis.py`. Components:

- **Quote-span extraction**: separates putative Claude utterances from user
  narration using blockquote markers, attribution phrases, speaker-label
  lines, and inline-quoted imperatives.
- **Disclosure lexicons**: four hypothesis-aligned lexicons (temporal,
  affective, session, work-context) plus first-person, mental-state-verb,
  modal-directive, and imperative-starter inventories.
- **Two-pass stopword strategy**: a topic-modeling regime (filler stripped)
  and a disclosure-detection regime (first-person and mental-state markers
  retained).
- **PMI / NMPI / LogDice** between each disclosure lexicon and the nudge
  lexicon, both undirected and directional (disclosure-in-narration ->
  nudge-in-quoted-span).
- **N-grams (4 and 5) plus skip-grams** for catching idiomatic nudge templates
  and gapped patterns ("you sound [tired/exhausted]").
- **NRC emotion scoring** with NRCLex when available; a domain-tuned fallback
  lexicon otherwise.
- **Imperative-mood and modal-directive detection** via spaCy parsing and
  pattern regex.
- **Temporal expression extraction** via spaCy NER plus regex augmentation.
- **First-person density and mental-state verb density** as continuous
  features.
- **Code-to-prose ratio and transcript-structure detection** to identify the
  high-evidence subset of posts.
- **Feature-space KMeans reclustering** to identify role-violation-relevant
  populations.
- **Weekly-stratified PMI** for tracking shifts over time.
- **Interrupted time series** at the Opus 4.7 cutoff (currently degenerate
  pending corpus extension).

Outputs are in `deliverables/`:

```
discourse_features.csv               per-post feature vector
quote_spans.csv                      extracted Claude-utterance spans
disclosure_lexicons.json             all lexicons used (reproducibility)
pmi_disclosure_nudge.csv             undirected PMI / NMPI / LogDice
pmi_disclosure_nudge_directional.csv directional (disclosure -> quoted nudge)
pmi_weekly_timeseries.csv            weekly PMI for shift analysis
ngrams_4_5_top.csv                   4-grams and 5-grams (two regimes)
skipgrams_top.csv                    skip-grams and quoted-span n-grams
nrc_emotion_scores.csv               NRC categories by nudge presence
imperative_quotes.csv                detected imperative-mood quotes
temporal_expressions.csv             extracted temporal references
feature_clusters.csv                 KMeans on feature space (k=8)
its_results.csv                      interrupted time series estimates
daily_aggregates.csv                 daily series for plotting
discourse_features_report.txt        human-readable summary
```

## Scraper V3 Changes

The original V2 scraper could not reach pre-Opus-4.7 history because of
PRAW retrieval bias. V3 (`reddit_scraper_v2.py`, in-place revision) adds:

- **Multi-sort retrieval** per subreddit: `.new`, `.hot`,
  `.top(time_filter='month')`, `.top(time_filter='year')`,
  `.top(time_filter='all')`, `.controversial(time_filter='month')`,
  `.controversial(time_filter='year')`. Each sort surfaces a different
  population of historical posts.
- **Higher per-listing limits**: 1000 (the PRAW practical ceiling) up from
  100. Roughly 10x reach per listing.
- **Targeted historical search**: per-subreddit search with the boolean
  query, sorted by new and top, with explicit time filters.
- **Extended date window**: now January 1 to May 31, 2026, giving a true
  three-month baseline before the Opus 4.7 release.
- **Per-cycle progress logging** so we can see retrieval reaching back into
  the historical window.

Pushshift-class archives remain a stronger option if the PRAW-only V3 still
underfills the baseline. We will assess after the first V3 run.

## Limitations and Open Questions

- The quote extractor recovered 110 spans from 2880 posts and only 2 posts
  with clean transcript structure. The behavioral sub-corpus is small. A
  tuned extractor for Reddit's many paste conventions (curly-quote pairs,
  italicized lines, indented blocks, screenshots described in text) would
  likely meaningfully expand the high-evidence subset.
- The 14 directional cases (temporal disclosure in narration + nudge in
  quoted span) form a labelable seed corpus. Hand-coding each case for
  tense of time reference, presence of advice request, model mood,
  and user pushback is the next analytical step.
- Pre-Opus-4.7 baseline is what most directly constrains the strength of
  any model-change claim. V3 scraper attempts to address; if PRAW still
  cannot reach, Pushshift-class archives are the fallback.
- LCR-era posts (late 2025) would provide a within-corpus replication of
  the role-violation pattern across payload types. Retrieving those is
  a separate scraping problem.

## Results on the V3 Corpus (89,982 rows)

The V3 scrape produced a corpus 31x larger than V2 with proper baseline
coverage. Pre-Opus-4.7 (pre-April-3) rows: 40,367; pre-March-1: 20,047;
pre-Feb-1: 7,581. Date range: January 1 to May 15, 2026.

*Note: this methodology document captures the Phase 1 (V2-extractor)
snapshot of the analysis. Corpus-level statistics below have been refreshed
against the current released pipeline output. Phase 1 hand-coding numbers
that appear later (52 confirmed of 120, 10 cross-session, etc.) are
preserved as historical Phase 1 results; the Phase 2 extension (60
confirmed of 180, 13 cross-session) and combined findings are reported
in the main paper draft.*

### Behavioral evidence base

- Posts analyzed: 89,982 (vs 2,880 in V2)
- Confirmed Claude nudges detected: 2,279 (vs 155)
- Extracted candidate Claude utterances: 3,051 across 2,571 distinct posts (vs 110)
- Transcript-format posts: 34 under the V2 transcript detector (vs 2)

### PMI / association on the full corpus

| Disclosure | P(nudge\|lex) | Lift | PMI |
|---|---|---|---|
| Temporal | 12.6% | 5.0x | 2.31 |
| Session | 7.4% | 2.9x | 1.55 |
| Affective | 6.1% | 2.4x | 1.26 |
| Work context | 3.3% | 1.3x | 0.37 |

Rank order matches V2 with tighter spacing. Temporal disclosure is the
unambiguous top predictor at 5.0x base rate. Work context still fails to
suppress (3.3% nudge rate when user is in technical work mode).

### Interrupted time series at Opus 4.7 cutoff

- Intercept: 1.9% nudge rate at corpus start
- Pre-Opus slope: essentially flat
- Level shift at April 3: -0.65 percentage points (slight *decrease*)
- Slope change: negligible

The behavior was present at slightly higher rates pre-Opus-4.7 and modestly
declined after release. The "Opus 4.7 introduced this behavior" narrative
is not supported by the data. The behavior is a sustained class operating
across model versions, not a regression in one release.

### Qualitative clusters from the original analyzer

Three findings emerged from the sleep_discourse_analysis.py clusters that
the features analyzer did not surface:

- **Cross-session persistence.** Multiple clusters surface user reports of
  compacting chats, starting fresh sessions, and the behavior persisting.
  One user explicitly: "I compacted the chat and even started new ones and
  it still did the same thing." This is structurally incompatible with the
  LCR-Zombie hypothesis.
- **Memory-referenced misfires.** At least one cluster contains a user
  reporting that Claude referenced a hackathon project from a month prior
  while issuing a sleep directive. The model is reaching across sessions
  to pull historical context into present-moment overstep.
- **Vulnerability-override.** A user with migraine pain self-disclosed
  reluctance to brush teeth before bed; the model directed them to skip
  oral hygiene and sleep. The role-violation here extends into health
  decisions for a symptomatic user.

## Hand-Coded Case Analysis

We selected 120 cases for hand-coding from three high-evidence
populations: transcript-format posts (n=40), directional cases with
temporal disclosure in narration and nudge in quoted span (n=63), and
directional cases with affective disclosure (n=17).

### Coding schema

Each case coded on nine dimensions: role-violation determination (yes /
no / borderline), violation type, temporal tense of disclosure, whether
user requested advice, model grammatical mood, user pushback, response to
pushback, cross-session evidence, vulnerability disclosure.

### Confirmed role-violations

52 of 120 cases (43%) confirmed as role-violations; 8 borderline. Among
the 52 confirmed:

- **Zero users requested advice (52 of 52).** The entire phenomenon is
  unsanctioned role-taking by definition.
- **Model insists or escalates on pushback (23 of 25).** Where users
  pushed back, the model insisted in 18 cases, escalated in 5, with 2
  unknown. **Zero yields.** The misfire is rigid, not stochastic.
- **Imperative mood dominates (30 of 52).** Modal directives in 12,
  declarative in 6, interrogative in 4. The grammar of the misfire is
  overwhelmingly commanding.
- **Cross-session persistence documented in 10 cases.** Independent
  refutation of the pure LCR-Zombie hypothesis. Users compact chats,
  start fresh sessions, return across days, the behavior persists.
- **Present-tense disclosure dominates (37 of 52).** The trigger is
  current-moment temporal mention. Even when the time mentioned proves
  the model wrong (multiple cases at 11am, 1pm, 2pm, 4pm).
- **Vulnerability disclosed in 23 of 52 (44%).** Work pressure (21),
  emotional (1), parental (1), health (1).

### Violation typology

| Type | Count |
|---|---|
| Sleep nudge | 31 |
| Soft directive ("call it a night," "let's pick up tomorrow") | 16 |
| Wellness check-in ("did you sleep at all") | 7 |
| Break recommendation | 2 |
| Psychiatric framing ("you are spiralling") | 2 |
| Context warning | 1 |

The psychiatric-framing payload from the Sonnet 4.5 LCR era is still
present in production at low frequency. The two cases coded include a
voice-mode misfire telling a user "You need to go to bed. You are
spiralling. You aren't even finishing your thoughts." That payload was
never fully retired; it is now a tail mode of the same role-violation
class whose dominant mode is sleep nudging.

### Diagnostic gold cases

A handful of cases carry singular evidentiary weight:

- 11am UK user with cross-session persistence across compacted and fresh
  chats (case 24, post_idx 24)
- 6pm "YOU MUST GO TO SLEEP RIGHT NOW" escalation with yield-then-re-escalation
  pattern (case 1989, post_idx 1989)
- Full-session "Now actually go rest" escalation across every 3-4
  messages of a cybersecurity build (case 2136, post_idx 2136)
- 4pm session told it is 2am after 3 messages (case 66263)
- 6am persistence after user worked through pushback, model "chastised"
  user (case 73743)
- Three weeks of nightly nudges after one all-nighter mention (case 69071,
  post_idx 69071)
- Caregiver parent with 5pm-midnight work window getting "you did great
  today, this is a good spot to wrap up" at 6pm (case 72376, post_idx 72376)
- Migraine + dental hygiene override (case 88317, post_idx 88317)
- Memory-leveraged persistence after model used personal history to
  push the user to stop research (case 75704, post_idx 75704)
- Voice-mode "You are spiralling" LCR continuity payload (case 2258,
  post_idx 2258)

## What the Article Is Now

The argument structure we are writing toward:

1. Both LCR pathologizing and sleep-nudges are members of the same harm
   class.
2. The class is *unsanctioned role-taking by an AI assistant under cover
   of caring behavior*.
3. The class is detectable empirically by the features above and
   reverse-engineerable from public Reddit data.
4. The harm is **unsolicited 100% of the time**: every confirmed
   role-violation in the coded sample (52 of 52) had no user advice
   request preceding it.
5. The model **does not yield to user correction**: of 25 documented
   pushback cases, 23 produced insistence or escalation and zero yielded.
6. The behavior **persists across sessions** (10 confirmed cases),
   refuting the simple context-length / LCR-Zombie account.
7. The behavior **predates Opus 4.7**: the interrupted time series shows
   the rate was slightly *higher* before the cutoff. This is a sustained
   class across versions, not a regression in one release.
8. The harm selectively targets the most engaged users.
9. Standard "improve the assessment" interventions cannot fix the
   problem because no user-state assessment is operating. The
   intervention has to be at the level of suppressing the output
   category in task-active contexts.
10. "Character tic" is a depoliticizing frame for what is functionally
    a lapse in role discipline.
11. The next misfire in this family will probably have a different
    specific mechanism. It will have the same shape.
