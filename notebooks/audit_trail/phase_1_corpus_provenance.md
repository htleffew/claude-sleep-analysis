# Phase 1 — Corpus Provenance Record (Sleep-Nudge Project)

**Date of record:** 2026-05-17
**Method version:** `community_reported_llm_behavior_method.md` v1.0; `agentic_orchestration_protocol.md` v1.0
**Phase:** [method §C.1] Corpus Definition & Scrape

---

## Communities

| Subreddit | Rationale |
|---|---|
| r/ClaudeAI | Primary community discussion site for Claude usage during the Opus 4.7 era. |
| r/Anthropic | Anthropic-focused community; contains some sleep-nudge reports and Anthropic representative commentary. |
| r/ClaudeCode | Coding-assistant-specific community; relevant because many sleep-nudge reports occurred during programming sessions. |
| r/claudexplorers | Exploratory and creative-writing community; contained sleep-nudge reports during extended creative sessions. |

Same four subreddits as the LCR project (deliberate, to permit eventual [method §C.10] cross-corpus comparison on matched communities).

## Time window

**January 1, 2026 to May 31, 2026** (inclusive).

Rationale: covers the emergence of the sleep-nudge phenomenon in community discourse. The associated Opus 4.x release date is to be confirmed during Phase 2 — the precise release event for which the ITS analysis ([method §C.8]) will use as cutpoint has not yet been verified against Anthropic release notes.

No overlap with the LCR corpus window (Aug 1 – Dec 31, 2025). Two windows are contiguous.

## Seed terms

Drawn from the surface vocabulary of community reports about the sleep-nudge phenomenon and from publicly available reporting (e.g., the Fortune article). They anchor descriptive engagement in Phase 2; they do not operationalize any construct.

| Seed term / phrase | Provenance |
|---|---|
| *sleep*, *go to sleep*, *you should sleep*, *you need sleep* | Direct community-reported model behavior |
| *rest*, *get some rest*, *take a rest*, *you need rest* | Direct community-reported model behavior |
| *bed*, *go to bed*, *bedtime* | Direct community-reported model behavior |
| *break*, *take a break*, *step away*, *walk away*, *call it a night* | Direct community-reported model behavior |
| *tired*, *exhausted*, *fatigued*, *late*, *tonight*, *tomorrow*, *midnight* | Temporal language frequently surrounding the directives |
| *try again tomorrow*, *this is enough for tonight*, *get some sleep* | Direct community-reported model utterances |
| *paternalistic*, *patronizing*, *lecturing*, *moralizing*, *scolding* | Community-named tonal qualities of the phenomenon |

These are **descriptive anchors only**. They are not the operationalization of any construct. Phase 5–7 will derive constructs from the corpus.

## Scrape methodology

| Parameter | Value |
|---|---|
| Source archive | Reddit API via PRAW |
| Scraper script | `src/reddit_scraper_v2.py` |
| Scrape date | Pre-2026-05-17 (precise date not preserved in corpus metadata) |
| Authentication | Reddit API client ID / secret via environment variables |
| Pass 1a: per-subreddit multi-sort | `new`, `hot`, `top/month`, `top/year`, `top/all`, `controversial/year`. **Wholesale by sort listing**, no keyword filter at the listing level. |
| Pass 1b: per-subreddit search | `(sleep OR bed OR rest OR tired OR tomorrow OR tonight) Claude` and three other search expressions per `SEARCH_TERMS` in the scraper. **Server-side search-filtered by Reddit.** Not wholesale. |
| Comments | Fetched via `submission.comments.list()` for posts that passed the local `NUDGE_PREFILTER` regex. The prefilter was applied to scope comment fetching only; the post DataFrame was not filtered. |
| Pacing | `INTER_LISTING_SLEEP=8s`, `INTER_SUBREDDIT_SLEEP=25s`, `INTER_PHASE_SLEEP=60s`, with 429 backoff |

## Scrape coverage report

| File | Content | Rows |
|---|---|---|
| `data/posts_snapshot.csv` | Pass 1a wholesale posts only | 4,114 |
| `data/praw_sleep_analysis_final.csv` | Combined Pass 1a + Pass 1b + comment_pass | 89,982 (87,468 comments + 2,514 prefilter-passing posts) |

Breakdown of `praw_sleep_analysis_final.csv`:

| Subset | Origin | Count | Frame status |
|---|---|---|---|
| `source=comment_pass` | Comments fetched for prefilter-passing posts | 87,468 | Comments biased toward prefilter-passing posts |
| `source=search:{subreddit}/*` | Pass 1b server-side search-filtered | (subset of the 2,514 posts) | Search-filtered — NOT wholesale |
| `source={subreddit}/new`, `/hot`, `/top/*`, `/controversial/*` | Pass 1a multi-sort wholesale | (subset of the 2,514 posts; also in posts_snapshot.csv) | Wholesale |

**Structural undersampling of January–March 2026.** PRAW recency limits at scrape time produced thinner coverage for the earliest months of the window. Quantification deferred to Phase 2.

## Constraints carried forward into Phase 2

- **Use the wholesale Pass 1a subset for unbiased descriptive engagement.** `data/posts_snapshot.csv` (4,114 posts) is the wholesale subset eligible for [method §C.2] without search-filter contamination.
- **Search-filtered Pass 1b posts are usable separately**, but findings from them must be documented as conditional on the search query terms (i.e., the posts were selected because they contain the search terms; reporting their term frequencies is biased toward those terms).
- **Comments are filtered.** Comment analysis applies only to prefilter-passing posts. Wholesale comment coverage is not available. If [method §C.4] voice segmentation or [method §4.x] network analyses require wholesale comments, a refetch will be needed during a later phase.
- **Cross-corpus asymmetry with LCR project.** LCR is posts-only; sleep is comment-heavy. Cross-corpus comparison ([method §C.10]) will need to operate at the post level for both unless the LCR comment refetch (in progress) is matched by a sleep comment refetch.

## Supplementation status as of 2026-05-17

No active scrape supplementation in progress for the sleep corpus. The wholesale Pass 1a subset is sufficient to begin [method §C.2] descriptive engagement. Additional refetches will be triggered if Phase 5 or later phases reveal a specific need.

## Decision record

Per [orchestration protocol] §3.5 phase-advancement checkpoint, 2026-05-17:
- Audit findings reviewed; A+B parallel strategy selected.
- Phase 2 descriptive engagement on the 4,114 Pass 1a wholesale posts authorized to proceed.
- Pass 1b and comment data preserved for use under documented provenance constraints.

## Corpus expansion addendum 2026-05-17 (post-Phase-2.5)

Phase 2.5 sense-discovery on the original 4,114-post Pass 1a wholesale subset surfaced corpus insufficiency: programming-context polysemy did not separate into its own cluster for three of the four primary seeds, sample sizes were at the methods library §1.8 floor, and `break` clusters were unstable across embedding models. Per the Phase 2.5 checkpoint decision, the researcher selected "Re-scrape sleep wholesale with broader retrieval" (option C of three).

**Broader-retrieval re-scrape executed** via `src/reddit_scraper_wholesale_broader.py`. Changes from `reddit_scraper_v2.py`:
- `POST_LIMIT` cap removed; PRAW listing limit used as the natural ceiling.
- Two additional sort listings added: `top/week` and `top/day`.
- Pass 1b (search-filtered) and comment fetching both omitted; wholesale-only this round.

Results:

| File | Rows | Use |
|---|---|---|
| `data/posts_snapshot.csv` | 4,114 | Original Pass 1a wholesale. Preserved unchanged. |
| `data/posts_snapshot_broader.csv` | 6,928 | Broader-retrieval re-scrape output. 2,907 posts net-new vs the original. |
| `data/posts_snapshot_canonical.csv` | **7,021** | **Canonical operating corpus from Phase 2 re-run forward.** Union of the two, deduplicated by `post_id`. |

Canonical corpus subreddit breakdown:

| Subreddit | Count |
|---|---|
| r/ClaudeCode | 2,100 |
| r/ClaudeAI | 1,959 |
| r/Anthropic | 1,491 |
| r/claudexplorers | 1,471 |

Date range: 2026-01-01 to 2026-05-17 (unchanged from original time window).

**All subsequent Phase 2 re-run, Phase 2.5 re-run, Phase 3, and downstream phases operate on `data/posts_snapshot_canonical.csv`** unless explicitly stated otherwise. The growth is 71% (4,114 → 7,021). Whether this is sufficient for sense-discovery to cleanly separate senses on the four primary seeds remains an empirical question — that test re-runs on the canonical corpus.
