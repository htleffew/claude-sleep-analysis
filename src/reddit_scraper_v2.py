"""
Reddit scraper V3.1 for the sleep-nudge / role-violation analysis.

V3.1 changes from V3:
- Two-pass design: posts first (no comments), then comments only for posts that
  contain sleep/temporal lexicon hits. Cuts request volume by ~75x.
- Explicit rate-limit handling: praw.Reddit(ratelimit_seconds=600) plus manual
  sleeps between listings and subreddits. Backoff on 429.
- Reduced per-listing limit (500) and removed redundant global-all search.
- Conservative pacing throughout. Runtime is longer; the scrape actually finishes.
"""

import os
import re
import html
import json
import time
import logging
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import praw
import prawcore
from tqdm import tqdm

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.getLogger("praw").setLevel(logging.WARNING)
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

OUTPUT_DIR = "data/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get(
    "REDDIT_USER_AGENT",
    "claude-sleep-analysis/1.0 (research; contact via GitHub issues)",
)

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError(
        "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in your environment. "
        "Register a Reddit application at https://www.reddit.com/prefs/apps "
        "to obtain credentials."
    )

print("Initializing Reddit API...")
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    ratelimit_seconds=600,  # PRAW will wait up to 10 minutes on 429
)
print("Reddit API initialized.")

# --------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------

SUBREDDITS = ["ClaudeAI", "Anthropic", "ClaudeCode", "claudexplorers"]

SEARCH_TERMS = [
    "(sleep OR bed OR rest OR tired OR tomorrow OR tonight) Claude",
    "Claude (told OR telling) (sleep OR bed OR rest OR break)",
    "Claude (paternalistic OR patronizing OR scolding OR lecturing OR moralizing)",
    "long conversation reminder Claude",
]

START_DATE = pd.Timestamp("2026-01-01")
END_DATE = pd.Timestamp("2026-05-31")

POST_LIMIT = 500
COMMENT_LIMIT = 50

SORT_PLAN = [
    ("new", None),
    ("hot", None),
    ("top", "month"),
    ("top", "year"),
    ("top", "all"),
    ("controversial", "year"),
]

SEARCH_SORT_PLAN = [
    ("new", "all"),
    ("top", "year"),
    ("relevance", "year"),
]

# Pacing
INTER_LISTING_SLEEP = 8
INTER_SUBREDDIT_SLEEP = 25
INTER_PHASE_SLEEP = 60

# Lexicons used to pre-filter posts for comment fetching
NUDGE_PREFILTER = re.compile(
    r"\b(sleep|bed|bedtime|rest|tired|exhausted|nap|tomorrow|tonight|"
    r"late|night|midnight|break|claude|sonnet|opus|anthropic|lcr|"
    r"reminder|paternal|patroniz|scold|lectur|moraliz)\b",
    re.IGNORECASE,
)

device = "cpu"
seen_post_ids = set()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def safe_iter(listing, label, max_retries=3):
    """Materialize a PRAW listing with retry on transient errors."""
    for attempt in range(max_retries):
        try:
            return list(listing)
        except prawcore.exceptions.TooManyRequests:
            wait = 60 * (attempt + 1)
            print(f"    [{label}] 429 rate limit. Sleeping {wait}s...")
            time.sleep(wait)
        except prawcore.exceptions.ServerError:
            time.sleep(15)
        except Exception as e:
            logging.error(f"Listing error {label}: {e}")
            return []
    return []


def post_in_window(post):
    try:
        d = pd.to_datetime(post.created_utc, unit="s")
        return START_DATE <= d <= END_DATE, d
    except Exception:
        return False, None


def harvest_posts(listing, label, collected):
    """Pass 1: harvest posts only. No comments."""
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
    print(f"    [{label:55s}] new={n_new:4d} oldest_seen={oldest_str}")
    return n_new


def fetch_comments_for(post_ids, collected):
    """Pass 2: pull comments for the set of post_ids that pre-filtered as relevant."""
    print(f"\n--- Pass 2: fetching comments for {len(post_ids)} pre-filtered posts ---")
    pbar = tqdm(post_ids, desc="Comments")
    n_comments = 0
    for pid in pbar:
        try:
            submission = reddit.submission(id=pid)
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:COMMENT_LIMIT]:
                try:
                    cdate = pd.to_datetime(comment.created_utc, unit="s")
                except Exception:
                    continue
                if not (START_DATE <= cdate <= END_DATE):
                    continue
                collected.append({
                    "post_id": pid,
                    "body": comment.body,
                    "createdAt": cdate,
                    "subreddit": getattr(comment.subreddit, "display_name", ""),
                    "type": "comment",
                    "comment_id": comment.id,
                    "parent_id": comment.parent_id,
                    "source": "comment_pass",
                })
                n_comments += 1
        except prawcore.exceptions.TooManyRequests:
            print("\n    429 in comment pass. Sleeping 120s...")
            time.sleep(120)
        except Exception as e:
            logging.error(f"Comment fetch error for {pid}: {e}")
        time.sleep(0.6)  # gentle rate limiter
    print(f"  Pulled {n_comments} comments.")


def passes_prefilter(body):
    return bool(NUDGE_PREFILTER.search(body or ""))


def collect_subreddit_pass1(subreddit_name, collected):
    sr = reddit.subreddit(subreddit_name)
    for sort_name, time_filter in SORT_PLAN:
        label = f"{subreddit_name}/{sort_name}" + (f"/{time_filter}" if time_filter else "")
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
                continue
        except Exception as e:
            logging.error(f"Listing init error {label}: {e}")
            continue
        harvest_posts(listing, label, collected)
        time.sleep(INTER_LISTING_SLEEP)


def collect_subreddit_search_pass1(subreddit_name, collected):
    sr = reddit.subreddit(subreddit_name)
    for term in SEARCH_TERMS:
        for sort_name, time_filter in SEARCH_SORT_PLAN:
            label = f"search:{subreddit_name}/{sort_name}/{time_filter}"
            try:
                listing = sr.search(term, sort=sort_name, time_filter=time_filter, limit=POST_LIMIT)
            except Exception as e:
                logging.error(f"Search init {label}: {e}")
                continue
            harvest_posts(listing, label, collected)
            time.sleep(INTER_LISTING_SLEEP)


def clean_dedup(df):
    df["body"] = df["body"].apply(
        lambda x: html.unescape(re.sub(r"\\", "", str(x))) if pd.notna(x) else ""
    )
    df = df[~df["body"].str.contains(
        r"ads?|sponsor|promot|youtube\.com|youtu\.be|vimeo|video",
        case=False, na=False,
    )]
    df = df[df["body"].str.len() > 30]
    df = df.reset_index(drop=True)

    if not df.empty and len(df) > 1:
        model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        embeddings = model.encode(
            df["body"].fillna("").tolist(),
            batch_size=64,
            show_progress_bar=False,
        )
        sim_matrix = cosine_similarity(embeddings)
        np.fill_diagonal(sim_matrix, 0)
        to_drop = set()
        for i in range(len(sim_matrix)):
            matches = np.where(sim_matrix[i] > 0.95)[0]
            to_drop.update(matches[matches > i])
        df = df.drop(index=list(to_drop)).reset_index(drop=True)
    return df


def report_coverage(df, label):
    if df.empty:
        print(f"{label}: empty")
        return
    df_dates = pd.to_datetime(df["createdAt"])
    print(f"\n{label}")
    print(f"  Total rows: {len(df)}")
    print(f"  Date range: {df_dates.min().date()} to {df_dates.max().date()}")
    print(f"  Subreddit breakdown:")
    for sub, count in df["subreddit"].value_counts().head(10).items():
        print(f"    {sub}: {count}")
    print(f"  Pre-April-3 rows: {(df_dates < pd.Timestamp('2026-04-03')).sum()}")
    print(f"  Pre-March-1 rows: {(df_dates < pd.Timestamp('2026-03-01')).sum()}")
    print(f"  Pre-Feb-1 rows: {(df_dates < pd.Timestamp('2026-02-01')).sum()}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

start_run = datetime.now()
print(f"Run start: {start_run}")

post_rows = []

# Pass 1a: per-subreddit multi-sort
print("\n========== PASS 1a: subreddit multi-sort ==========")
for sub in SUBREDDITS:
    print(f"\n--- {sub} ---")
    collect_subreddit_pass1(sub, post_rows)
    print(f"  Cumulative posts so far: {len(post_rows)}")
    time.sleep(INTER_SUBREDDIT_SLEEP)

# Pass 1b: per-subreddit search
print(f"\nSleeping {INTER_PHASE_SLEEP}s between phases...")
time.sleep(INTER_PHASE_SLEEP)
print("\n========== PASS 1b: subreddit-scoped search ==========")
for sub in SUBREDDITS:
    print(f"\n--- {sub} search ---")
    collect_subreddit_search_pass1(sub, post_rows)
    print(f"  Cumulative posts so far: {len(post_rows)}")
    time.sleep(INTER_SUBREDDIT_SLEEP)

posts_df = pd.DataFrame(post_rows)
print(f"\nPass 1 complete. {len(posts_df)} posts collected.")
report_coverage(posts_df, "After pass 1 (posts only)")

# Pre-filter posts for pass 2 (comment fetching)
print(f"\nSleeping {INTER_PHASE_SLEEP}s before pass 2...")
time.sleep(INTER_PHASE_SLEEP)
mask = posts_df["body"].apply(passes_prefilter)
relevant_post_ids = posts_df.loc[mask, "post_id"].dropna().unique().tolist()
print(f"{len(relevant_post_ids)} of {len(posts_df)} posts passed the lexicon prefilter.")

comment_rows = []
fetch_comments_for(relevant_post_ids, comment_rows)
comments_df = pd.DataFrame(comment_rows)

# Combine
full_df = pd.concat([posts_df, comments_df], ignore_index=True)
print(f"\nCombined posts+comments: {len(full_df)} rows.")

# Clean and dedup
print("\nCleaning and deduplicating...")
full_df = clean_dedup(full_df)
print(f"After clean+dedup: {len(full_df)} rows.")

# Cross-cycle dedup
full_df["dedup_key"] = full_df.apply(
    lambda r: r["comment_id"] if r["type"] == "comment" else str(r.get("post_id", "")) + str(r["createdAt"]),
    axis=1,
)
full_df = full_df.drop_duplicates(subset=["dedup_key"]).drop(columns=["dedup_key"]).reset_index(drop=True)

# Save
final_path = os.path.join(OUTPUT_DIR, "praw_sleep_analysis_final.csv")
try:
    full_df.to_csv(final_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved final CSV: {final_path}")
except PermissionError:
    fallback = os.path.join(OUTPUT_DIR, "praw_sleep_analysis_final_fallback.csv")
    full_df.to_csv(fallback, index=False, encoding="utf-8-sig")
    print(f"\nSaved fallback CSV: {fallback}")

report_coverage(full_df, "FINAL")
print(f"\nRun complete: {datetime.now() - start_run} elapsed")
