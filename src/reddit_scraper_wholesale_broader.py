"""
Reddit wholesale broader-retrieval scraper for the sleep-nudge project.

Phase 2.5 checkpoint decision 2026-05-17: broader Pass 1a corpus.

Changes from reddit_scraper_v2.py:
- Removes POST_LIMIT=500 cap; uses PRAW listing limit=1000 (true Reddit max).
- Adds top/week and top/day to SORT_PLAN to surface posts missed by longer windows.
- Skips Pass 1b entirely (no keyword search).
- Skips comment fetching entirely (posts-only).
- Writes to posts_snapshot_broader.csv (never overwrites posts_snapshot.csv).
- At end: deduplicates by post_id against existing posts_snapshot.csv and reports
  how many additional unique posts were obtained.
- --test flag: runs against r/claudexplorers only for quick validation.
"""

import os
import re
import html
import sys
import time
import logging
import argparse
import warnings
from datetime import datetime

import pandas as pd
import praw
import prawcore

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logging.getLogger("praw").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(DATA_DIR, "posts_snapshot_broader.csv")
EXISTING_PATH = os.path.join(DATA_DIR, "posts_snapshot.csv")

# --------------------------------------------------------------------------
# Reddit credentials
# --------------------------------------------------------------------------

CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get(
    "REDDIT_USER_AGENT",
    "claude-sleep-analysis/2.0-broader (research; contact via GitHub issues)",
)

_missing = [v for v, val in [("REDDIT_CLIENT_ID", CLIENT_ID), ("REDDIT_CLIENT_SECRET", CLIENT_SECRET)] if not val]
if _missing:
    raise RuntimeError(
        f"Missing required environment variable(s): {', '.join(_missing)}. "
        "Register a Reddit application at https://www.reddit.com/prefs/apps "
        "to obtain credentials, then set those variables in your environment."
    )

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------

SUBREDDITS_ALL = ["ClaudeAI", "Anthropic", "ClaudeCode", "claudexplorers"]
SUBREDDITS_TEST = ["claudexplorers"]  # smallest; used with --test

START_DATE = pd.Timestamp("2026-01-01")
END_DATE = pd.Timestamp("2026-05-31")

# No POST_LIMIT cap: use Reddit's true per-call max.
# PRAW accepts limit=1000 but Reddit may return fewer; we take whatever we get.
POST_LIMIT = 1000

# Broader sort plan: adds top/week and top/day beyond the v2 plan.
SORT_PLAN = [
    ("new", None),
    ("hot", None),
    ("top", "day"),
    ("top", "week"),
    ("top", "month"),
    ("top", "year"),
    ("top", "all"),
    ("controversial", "year"),
]

# Pacing: identical to v2.
INTER_LISTING_SLEEP = 8
INTER_SUBREDDIT_SLEEP = 25

# --------------------------------------------------------------------------
# Global state
# --------------------------------------------------------------------------

seen_post_ids: set[str] = set()


# --------------------------------------------------------------------------
# Reddit client (initialized after credential check)
# --------------------------------------------------------------------------

print("Initializing Reddit API...", flush=True)
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    ratelimit_seconds=600,
)
print("Reddit API initialized.", flush=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def safe_iter(listing, label: str, max_retries: int = 3) -> list:
    """Materialize a PRAW listing with retry on transient errors."""
    for attempt in range(max_retries):
        try:
            return list(listing)
        except prawcore.exceptions.TooManyRequests:
            wait = 60 * (attempt + 1)
            print(f"    [{label}] 429 rate limit. Sleeping {wait}s...", flush=True)
            time.sleep(wait)
        except prawcore.exceptions.ServerError:
            print(f"    [{label}] Server error. Sleeping 15s...", flush=True)
            time.sleep(15)
        except Exception as e:
            logging.error(f"Listing error [{label}]: {e}")
            return []
    return []


def post_in_window(post):
    """Return (in_window: bool, date: Timestamp|None)."""
    try:
        d = pd.to_datetime(post.created_utc, unit="s")
        return START_DATE <= d <= END_DATE, d
    except Exception:
        return False, None


def harvest_posts(listing, label: str, collected: list) -> int:
    """
    Iterate listing, collect posts within the date window.
    Deduplicates by post_id within the current run (seen_post_ids set).
    Logs one line per listing to stdout.
    Returns count of new rows added this listing.
    """
    items = safe_iter(listing, label)
    n_new = 0
    oldest_seen = None

    for post in items:
        try:
            pid = str(post.id)
        except Exception:
            continue

        in_window, post_date = post_in_window(post)

        if oldest_seen is None or (post_date is not None and post_date < oldest_seen):
            oldest_seen = post_date

        if not in_window or pid in seen_post_ids:
            continue

        seen_post_ids.add(pid)

        try:
            body = (post.title or "") + " " + (post.selftext or "")
        except Exception:
            body = ""

        collected.append({
            "post_id": pid,
            "body": body,
            "createdAt": post_date,
            "subreddit": getattr(post.subreddit, "display_name", ""),
            "type": "post",
            "comment_id": None,
            "parent_id": None,
            "source": label,
        })
        n_new += 1

    oldest_str = oldest_seen.date().isoformat() if oldest_seen is not None else "n/a"
    total_returned = len(items)
    print(
        f"    [{label:60s}] returned={total_returned:4d}  new_in_window={n_new:4d}  oldest_seen={oldest_str}",
        flush=True,
    )
    return n_new


def collect_subreddit(subreddit_name: str, collected: list):
    """Run all listings in SORT_PLAN for one subreddit."""
    sr = reddit.subreddit(subreddit_name)
    for sort_name, time_filter in SORT_PLAN:
        label = (
            f"{subreddit_name}/{sort_name}"
            + (f"/{time_filter}" if time_filter else "")
        )
        try:
            if sort_name == "new":
                listing = sr.new(limit=POST_LIMIT)
            elif sort_name == "hot":
                listing = sr.hot(limit=POST_LIMIT)
            elif sort_name == "top":
                listing = sr.top(time_filter=time_filter, limit=POST_LIMIT)
            elif sort_name == "controversial":
                listing = sr.controversial(time_filter=time_filter, limit=POST_LIMIT)
            else:
                logging.warning(f"Unknown sort '{sort_name}' — skipping.")
                continue
        except Exception as e:
            logging.error(f"Listing init error [{label}]: {e}")
            continue

        harvest_posts(listing, label, collected)
        time.sleep(INTER_LISTING_SLEEP)


def report_coverage(df: pd.DataFrame, label: str):
    if df.empty:
        print(f"{label}: (empty dataframe)", flush=True)
        return
    df_dates = pd.to_datetime(df["createdAt"])
    print(f"\n{label}", flush=True)
    print(f"  Total rows     : {len(df)}", flush=True)
    print(f"  Date range     : {df_dates.min().date()} to {df_dates.max().date()}", flush=True)
    print(f"  Subreddit breakdown:", flush=True)
    for sub, count in df["subreddit"].value_counts().items():
        print(f"    {sub}: {count}", flush=True)
    print(f"  Pre-April-3 rows : {(df_dates < pd.Timestamp('2026-04-03')).sum()}", flush=True)
    print(f"  Pre-March-1 rows : {(df_dates < pd.Timestamp('2026-03-01')).sum()}", flush=True)
    print(f"  Pre-Feb-1 rows   : {(df_dates < pd.Timestamp('2026-02-01')).sum()}", flush=True)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Wholesale broader-retrieval scraper for the sleep-nudge Reddit corpus."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run against r/claudexplorers only (quick validation).",
    )
    args = parser.parse_args()

    subreddits = SUBREDDITS_TEST if args.test else SUBREDDITS_ALL

    start_run = datetime.now()
    mode_label = "TEST (r/claudexplorers only)" if args.test else "FULL (all four subreddits)"
    print(f"\nRun start  : {start_run.isoformat()}", flush=True)
    print(f"Mode       : {mode_label}", flush=True)
    print(f"Date window: {START_DATE.date()} to {END_DATE.date()}", flush=True)
    print(f"Sort plan  : {SORT_PLAN}", flush=True)
    print(f"POST_LIMIT : {POST_LIMIT} (per listing call)", flush=True)
    print(f"Output     : {OUTPUT_PATH}", flush=True)

    post_rows: list[dict] = []

    print("\n========== PASS 1a: wholesale multi-sort (broader) ==========", flush=True)
    for sub in subreddits:
        print(f"\n--- {sub} ---", flush=True)
        collect_subreddit(sub, post_rows)
        print(f"  Cumulative posts so far: {len(post_rows)}", flush=True)
        if sub != subreddits[-1]:
            time.sleep(INTER_SUBREDDIT_SLEEP)

    # Build DataFrame
    df = pd.DataFrame(post_rows)
    print(f"\nCollection complete. {len(df)} posts collected.", flush=True)

    if df.empty:
        print("WARNING: No posts collected. Exiting without writing output.", flush=True)
        sys.exit(1)

    report_coverage(df, "Newly collected (before dedup against existing)")

    # --------------------------------------------------------------------------
    # Dedup against existing posts_snapshot.csv
    # --------------------------------------------------------------------------
    existing_ids: set[str] = set()
    if os.path.exists(EXISTING_PATH):
        try:
            existing_df = pd.read_csv(EXISTING_PATH, usecols=["post_id"], dtype=str)
            existing_ids = set(existing_df["post_id"].dropna().tolist())
            print(f"\nExisting corpus ({EXISTING_PATH}): {len(existing_ids)} unique post_ids.", flush=True)
        except Exception as e:
            print(f"WARNING: Could not read existing corpus for dedup: {e}", flush=True)
    else:
        print(f"\nNo existing corpus found at {EXISTING_PATH}. All posts are new.", flush=True)

    df["post_id"] = df["post_id"].astype(str)
    mask_new = ~df["post_id"].isin(existing_ids)
    n_already_in_existing = (~mask_new).sum()
    n_additional_unique = mask_new.sum()

    print(f"\nDedup report:", flush=True)
    print(f"  Posts in this run            : {len(df)}", flush=True)
    print(f"  Already in existing corpus   : {n_already_in_existing}", flush=True)
    print(f"  Net-new (not in existing)    : {n_additional_unique}", flush=True)

    # --------------------------------------------------------------------------
    # Write output (ALL posts from this run, not just the net-new ones;
    # the full file is the broader corpus; downstream analysis can join/diff).
    # --------------------------------------------------------------------------
    try:
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print(f"\nSaved: {OUTPUT_PATH} ({len(df)} rows)", flush=True)
    except PermissionError:
        fallback = OUTPUT_PATH.replace(".csv", "_fallback.csv")
        df.to_csv(fallback, index=False, encoding="utf-8-sig")
        print(f"\nPermissionError on primary path. Saved fallback: {fallback}", flush=True)

    elapsed = datetime.now() - start_run
    print(f"\nRun complete: {elapsed} elapsed", flush=True)
    print(f"  Mode              : {mode_label}", flush=True)
    print(f"  Total rows        : {len(df)}", flush=True)
    print(f"  Net-new vs existing: {n_additional_unique}", flush=True)


if __name__ == "__main__":
    main()
