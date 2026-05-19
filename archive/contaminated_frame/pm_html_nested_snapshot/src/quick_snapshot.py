"""
Quick snapshot scraper: posts only, two sort orders per subreddit.

Used for running preliminary analysis while the main scraper completes its
comment-fetch pass in the background. Writes to data/posts_snapshot.csv.
"""

import os
import re
import html
import time
import logging
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import praw
import prawcore

warnings.filterwarnings("ignore")
logging.getLogger("praw").setLevel(logging.WARNING)

OUTPUT_DIR = "data/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "efJtPzmC4XNGafp1LTfD9g")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "muwZML3TpuE0isIjaII7c-iP-K8WIg")
USER_AGENT = "QuickSnapshot_RoleViolation by DrShadowMonsta"

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    ratelimit_seconds=600,
)

SUBREDDITS = ["ClaudeAI", "Anthropic", "ClaudeCode", "claudexplorers"]
START_DATE = pd.Timestamp("2026-01-01")
END_DATE = pd.Timestamp("2026-05-31")
POST_LIMIT = 500
INTER_LISTING_SLEEP = 12

SORTS = [
    ("top", "year"),
    ("new", None),
    ("top", "month"),
]

rows = []
seen = set()


def safe_iter(listing, label, max_retries=3):
    for attempt in range(max_retries):
        try:
            return list(listing)
        except prawcore.exceptions.TooManyRequests:
            wait = 90 * (attempt + 1)
            print(f"  [{label}] 429. Sleeping {wait}s...")
            time.sleep(wait)
        except Exception as e:
            logging.error(f"{label}: {e}")
            return []
    return []


def harvest(listing, label):
    items = safe_iter(listing, label)
    n_new = 0
    oldest = None
    for post in items:
        try:
            pid = str(post.id)
            pdate = pd.to_datetime(post.created_utc, unit="s")
        except Exception:
            continue
        if oldest is None or pdate < oldest:
            oldest = pdate
        if not (START_DATE <= pdate <= END_DATE):
            continue
        if pid in seen:
            continue
        seen.add(pid)
        body = (post.title or "") + " " + (post.selftext or "")
        rows.append({
            "post_id": pid,
            "body": body,
            "createdAt": pdate,
            "subreddit": getattr(post.subreddit, "display_name", ""),
            "type": "post",
            "comment_id": None,
            "parent_id": None,
            "source": label,
        })
        n_new += 1
    odate = oldest.date().isoformat() if oldest is not None else "n/a"
    print(f"  [{label:30s}] new={n_new:4d} oldest_seen={odate}")


start = datetime.now()
print(f"Snapshot start: {start}")

for sub in SUBREDDITS:
    sr = reddit.subreddit(sub)
    for sort_name, tf in SORTS:
        label = f"{sub}/{sort_name}" + (f"/{tf}" if tf else "")
        try:
            if sort_name == "top":
                listing = sr.top(time_filter=tf, limit=POST_LIMIT)
            elif sort_name == "new":
                listing = sr.new(limit=POST_LIMIT)
            else:
                continue
        except Exception as e:
            logging.error(f"Init {label}: {e}")
            continue
        harvest(listing, label)
        time.sleep(INTER_LISTING_SLEEP)

df = pd.DataFrame(rows)
df["body"] = df["body"].apply(
    lambda x: html.unescape(re.sub(r"\\", "", str(x))) if pd.notna(x) else ""
)
df = df[df["body"].str.len() > 30].reset_index(drop=True)

out = os.path.join(OUTPUT_DIR, "posts_snapshot.csv")
df.to_csv(out, index=False, encoding="utf-8-sig")

print(f"\nSaved {len(df)} posts to {out}")
print(f"Date range: {pd.to_datetime(df['createdAt']).min().date()} to "
      f"{pd.to_datetime(df['createdAt']).max().date()}")
df_dates = pd.to_datetime(df["createdAt"])
print(f"Pre-April-3: {(df_dates < pd.Timestamp('2026-04-03')).sum()}")
print(f"Pre-March-1: {(df_dates < pd.Timestamp('2026-03-01')).sum()}")
print(f"Pre-Feb-1:   {(df_dates < pd.Timestamp('2026-02-01')).sum()}")
print(f"Elapsed: {datetime.now() - start}")
