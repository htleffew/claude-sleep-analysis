# Broader Wholesale Re-scrape — Job Status Record

**Decision trigger:** Phase 2.5 checkpoint, 2026-05-17  
**Scraper:** `src/reddit_scraper_wholesale_broader.py`  
**Output:** `data/posts_snapshot_broader.csv` (does NOT overwrite `data/posts_snapshot.csv`)

---

## Test run (r/claudexplorers only)

| Metric | Value |
|---|---|
| Mode | `--test` (r/claudexplorers only) |
| Test timestamp | 2026-05-17T13:33:09 |
| Test duration | 2 min 15 s |
| Rows collected | 1,466 |
| Date range observed | 2026-01-01 to 2026-05-17 |
| Pre-March-1 rows | 250 |
| Pre-Feb-1 rows | 102 |
| Already in existing corpus | 869 |
| Net-new vs existing | 597 |
| Status | PASSED |

---

## Full run

| Field | Value |
|---|---|
| Shell ID | `b8mksdosw` |
| Launch timestamp | 2026-05-17T13:35:30 |
| Estimated completion | 2026-05-17T14:15:00 (approx. 40 min; based on 4 subreddits x 8 listings x ~1.5 min/listing + inter-subreddit sleeps) |
| stdout log | `notebooks/audit_trail/sleep_rescrape_broader_stdout.log` |
| Status | RUNNING |

---

## Parameters used

| Parameter | Value |
|---|---|
| Subreddits | ClaudeAI, Anthropic, ClaudeCode, claudexplorers |
| Date window | 2026-01-01 to 2026-05-31 |
| POST_LIMIT | 1,000 per listing call (no 500 cap) |
| Sort plan | new, hot, top/day, top/week, top/month, top/year, top/all, controversial/year |
| Pass 1b (search) | SKIPPED |
| Comment fetching | SKIPPED |
| INTER_LISTING_SLEEP | 8 s |
| INTER_SUBREDDIT_SLEEP | 25 s |

---

## Post-run update

(To be filled in when Shell ID `b8mksdosw` completes.)

- Total rows:
- Net-new vs existing corpus:
- Status:
