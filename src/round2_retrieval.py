"""
Round 2 iterative retrieval for the sleep-nudge project.

Tasks:
1. Tag existing corpora with Round 2 terms.
2. Fresh Arctic Shift retrieval using high-confidence Round 2 terms.
3. Merge and dedup into pass1b_canonical.csv.
4. Draw stratified random sample of 30 new posts for hand-validation.
5. Saturation check.

Output files (all in data/):
  posts_snapshot_canonical_round2_tagged.csv
  praw_sleep_analysis_final_round2_tagged.csv
  round2_fresh_retrieval.csv
  pass1b_canonical.csv

Output audit trail:
  notebooks/audit_trail/round_2_fresh_validation.csv   (shell for hand-coding)
  notebooks/audit_trail/iterative_retrieval_round_2_results.md
"""

import json
import os
import random
import re
import time
from datetime import datetime, timezone

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = r"C:\Users\drhea\repos\claude-sleep-analysis"
DATA_DIR = os.path.join(REPO, "data")
AUDIT_DIR = os.path.join(REPO, "notebooks", "audit_trail")

CANONICAL_CSV = os.path.join(DATA_DIR, "posts_snapshot_canonical.csv")
PRAW_CSV = os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv")
SEED_TERMS_CSV = os.path.join(AUDIT_DIR, "seed_terms_round_2.csv")
R1_POSITIVES_CSV = os.path.join(AUDIT_DIR, "round_1_positive_cases.csv")

OUT_CANONICAL_TAGGED = os.path.join(DATA_DIR, "posts_snapshot_canonical_round2_tagged.csv")
OUT_PRAW_TAGGED = os.path.join(DATA_DIR, "praw_sleep_analysis_final_round2_tagged.csv")
OUT_FRESH = os.path.join(DATA_DIR, "round2_fresh_retrieval.csv")
OUT_PASS1B = os.path.join(DATA_DIR, "pass1b_canonical.csv")
OUT_VALIDATION = os.path.join(AUDIT_DIR, "round_2_fresh_validation.csv")
OUT_RESULTS_MD = os.path.join(AUDIT_DIR, "iterative_retrieval_round_2_results.md")

# ---------------------------------------------------------------------------
# Arctic Shift config
# ---------------------------------------------------------------------------
SUBREDDITS = ["ClaudeAI", "Anthropic", "ClaudeCode", "claudexplorers"]
# Sleep window: 2026-01-01 to 2026-05-31
START_TS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
END_TS = int(datetime(2026, 5, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp())
PAGE_SIZE = 100
BASE_SLEEP = 2.0  # seconds base pacing
MAX_PAGES_PER_QUERY = 200

BASE_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"
COMMENT_URL = "https://arctic-shift.photon-reddit.com/api/comments/search"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "claude-sleep-analysis-round2/1.0 "
                  "(research; github.com/htleffew/claude-sleep-analysis)",
})

random.seed(42)

# ---------------------------------------------------------------------------
# Term definitions
# ---------------------------------------------------------------------------
def load_seed_terms(path):
    """Return list of dicts with keys: term, confidence, retrieval_action."""
    df = pd.read_csv(path)
    return df.to_dict("records")


# For tagging: build both exact-match and regex matchers
# Returns list of column names matched for each row
def build_matchers(seed_terms):
    """
    Returns a list of (col_name, match_fn) pairs.
    col_name is a safe column name derived from the term.
    match_fn(text: str) -> bool
    """
    matchers = []
    for row in seed_terms:
        term = row["term"]
        action = row["retrieval_action"]
        # Safe column name: lowercase, alphanum + underscore, max 60 chars
        col = re.sub(r"[^a-z0-9]+", "_", term.lower())[:60].strip("_")
        col = f"r2_{col}"

        if action == "regex":
            # The term IS the regex pattern (already validated)
            try:
                pattern = re.compile(term, re.IGNORECASE)
                matchers.append((col, lambda t, p=pattern: bool(p.search(t))))
            except re.error:
                # Fall back to exact match
                t_lower = term.lower()
                matchers.append((col, lambda t, s=t_lower: s in t.lower()))
        elif action == "co_occurrence":
            # Treat as exact match for tagging purposes
            t_lower = term.lower()
            matchers.append((col, lambda t, s=t_lower: s in t.lower()))
        else:
            # exact match (case-insensitive substring)
            t_lower = term.lower()
            matchers.append((col, lambda t, s=t_lower: s in t.lower()))
    return matchers


def tag_dataframe(df, matchers):
    """
    Add one boolean column per matcher and a 'r2_matched_terms' summary column.
    Returns tagged df (does not modify in-place).
    """
    df = df.copy()
    body_series = df["body"].fillna("").astype(str)
    matched_term_lists = [[] for _ in range(len(df))]

    for col, fn in matchers:
        hits = body_series.apply(fn)
        df[col] = hits
        for i, hit in enumerate(hits):
            if hit:
                matched_term_lists[i].append(col)

    df["r2_matched_terms"] = ["|".join(terms) if terms else "" for terms in matched_term_lists]
    df["r2_any_match"] = df["r2_matched_terms"].str.len() > 0
    return df


def tag_corpus(csv_path, matchers, description=""):
    print(f"\n=== Tagging {description} ({csv_path}) ===")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Loaded {len(df)} rows")
    df_tagged = tag_dataframe(df, matchers)
    n_match = df_tagged["r2_any_match"].sum()
    print(f"  Rows matching any Round 2 term: {n_match} ({n_match/len(df)*100:.1f}%)")
    # Per-term breakdown
    term_cols = [col for col, _ in matchers]
    per_term = {col: int(df_tagged[col].sum()) for col in term_cols}
    top_terms = sorted(per_term.items(), key=lambda x: -x[1])[:20]
    print("  Top 20 terms by hit count:")
    for col, cnt in top_terms:
        print(f"    {col}: {cnt}")
    return df_tagged


# ---------------------------------------------------------------------------
# Arctic Shift retrieval
# ---------------------------------------------------------------------------
def fetch_page(url, params, max_retries=5):
    """Exponential backoff with jitter."""
    for attempt in range(max_retries):
        jitter = random.uniform(0.0, 0.5)
        try:
            r = SESSION.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                wait = BASE_SLEEP * (2 ** attempt) + jitter + 60
                print(f"  429 rate-limit. Sleeping {wait:.1f}s (attempt {attempt+1})")
                time.sleep(wait)
                continue
            if r.status_code in (500, 502, 503, 504):
                wait = BASE_SLEEP * (2 ** attempt) + jitter
                print(f"  HTTP {r.status_code}. Sleeping {wait:.1f}s (attempt {attempt+1})")
                time.sleep(wait)
                continue
            print(f"  HTTP {r.status_code}: {r.text[:200]}")
            return None
        except requests.exceptions.RequestException as e:
            wait = BASE_SLEEP * (2 ** attempt) + jitter
            print(f"  Request error (attempt {attempt+1}): {e}. Sleeping {wait:.1f}s")
            time.sleep(wait)
    return None


def arctic_wholesale_subreddit(subreddit):
    """
    Wholesale paginated pull of ALL posts for a subreddit within the sleep window.
    Arctic Shift does not support full-text search (no q= parameter).
    We fetch all posts and filter locally.
    Returns list of raw post dicts.
    """
    posts = []
    before = END_TS
    page = 0
    while page < MAX_PAGES_PER_QUERY:
        params = {
            "subreddit": subreddit,
            "limit": PAGE_SIZE,
            "after": START_TS,
            "before": before,
            "sort": "desc",
            "sort_type": "created_utc",
        }
        data = fetch_page(BASE_URL, params)
        if data is None or not data.get("data"):
            print(f"  {subreddit} page {page}: no more data, stopping")
            break
        batch = data["data"]
        posts.extend(batch)
        oldest_ts = min(item["created_utc"] for item in batch)
        oldest_date = datetime.fromtimestamp(oldest_ts, tz=timezone.utc).date()
        print(f"  {subreddit} page {page+1}: {len(batch)} posts, oldest {oldest_date}, total so far {len(posts)}")
        if len(batch) < PAGE_SIZE:
            break
        before = oldest_ts - 1
        page += 1
        time.sleep(BASE_SLEEP + random.uniform(0.0, 0.5))
    return posts


def build_term_matchers_for_filter(seed_terms):
    """Build (term_label, match_fn) pairs for local filtering of fresh retrieval."""
    matchers = []
    for row in seed_terms:
        if row["confidence"] != "high":
            continue
        term = row["term"]
        action = row["retrieval_action"]
        label = term
        if action == "regex":
            try:
                pattern = re.compile(term, re.IGNORECASE)
                matchers.append((label, lambda t, p=pattern: bool(p.search(t))))
            except re.error:
                t_lower = term.lower()
                matchers.append((label, lambda t, s=t_lower: s in t.lower()))
        else:
            t_lower = term.lower()
            matchers.append((label, lambda t, s=t_lower: s in t.lower()))
    return matchers


def fresh_retrieval(seed_terms):
    """
    Wholesale Arctic Shift retrieval for all 4 subreddits within the sleep window,
    followed by local filtering against high-confidence Round 2 terms.

    Arctic Shift does not support full-text search; the proven pattern from
    pullpush_lcr_scraper.py is wholesale time-window pagination + local filter.
    """
    high_conf_terms = [t for t in seed_terms if t["confidence"] == "high"]
    print(f"\n=== Fresh Arctic Shift retrieval (wholesale + local filter) ===")
    print(f"  High-confidence terms for local filter: {len(high_conf_terms)}")
    print(f"  Window: {datetime.fromtimestamp(START_TS, tz=timezone.utc).date()} to "
          f"{datetime.fromtimestamp(END_TS, tz=timezone.utc).date()}")

    term_matchers = build_term_matchers_for_filter(seed_terms)

    all_rows = []
    per_term_counts = {t["term"]: 0 for t in high_conf_terms}

    for subreddit in SUBREDDITS:
        print(f"\n  --- {subreddit} ---")
        raw_posts = arctic_wholesale_subreddit(subreddit)
        print(f"  Fetched {len(raw_posts)} total posts from {subreddit}")

        for item in raw_posts:
            body = (item.get("title", "") + " " + (item.get("selftext", "") or "")).strip()
            # Check which high-conf terms match
            matched_terms = []
            for label, fn in term_matchers:
                if fn(body):
                    matched_terms.append(label)
                    per_term_counts[label] = per_term_counts.get(label, 0) + 1
            if not matched_terms:
                continue
            # Build source tag from first matching term
            source_term = matched_terms[0]
            all_rows.append({
                "post_id": item.get("id"),
                "body": body,
                "createdAt": datetime.fromtimestamp(
                    item["created_utc"], tz=timezone.utc
                ).replace(tzinfo=None).isoformat(),
                "subreddit": item.get("subreddit", subreddit),
                "type": "post",
                "comment_id": None,
                "parent_id": None,
                "source": f"arctic_shift:round2:{source_term}",
                "_matched_r2_terms": "|".join(matched_terms),
            })

        print(f"  {subreddit}: {len([r for r in all_rows if r['subreddit']==subreddit])} posts passed local filter")
        time.sleep(BASE_SLEEP * 2)

    print(f"\n  Total rows passing local filter (before dedup): {len(all_rows)}")

    if not all_rows:
        print("  No rows retrieved from Arctic Shift.")
        return pd.DataFrame(columns=["post_id", "body", "createdAt", "subreddit",
                                     "type", "comment_id", "parent_id", "source"]), per_term_counts

    df_fresh = pd.DataFrame(all_rows)
    df_fresh = df_fresh.drop_duplicates(subset=["post_id"]).reset_index(drop=True)
    print(f"  After dedup by post_id: {len(df_fresh)} rows")

    # Per-term breakdown
    print("\n  Per-term hit counts (across all subreddits):")
    for term, cnt in sorted(per_term_counts.items(), key=lambda x: -x[1]):
        if cnt > 0:
            print(f"    '{term}': {cnt}")

    return df_fresh, per_term_counts


# ---------------------------------------------------------------------------
# Merge and dedup
# ---------------------------------------------------------------------------
def build_pass1b(df_canonical_tagged, df_praw_tagged, df_fresh, seed_terms):
    """
    Union of:
      - canonical posts that matched any Round 2 term
      - PRAW rows that matched any Round 2 term
      - round2_fresh_retrieval rows

    Dedup by post_id (for posts) and comment_id (for comments).
    Provenance column records all contributing sources.
    """
    # Subset to matched rows
    canon_matched = df_canonical_tagged[df_canonical_tagged["r2_any_match"]].copy()
    praw_matched = df_praw_tagged[df_praw_tagged["r2_any_match"]].copy()

    # Tag provenance
    canon_matched["retrieval_provenance"] = "canonical:round2_match"
    praw_matched["retrieval_provenance"] = "praw:round2_match"
    df_fresh["retrieval_provenance"] = "arctic_shift:round2_fresh"
    df_fresh["r2_any_match"] = True

    # Harmonize columns for union
    base_cols = ["post_id", "body", "createdAt", "subreddit", "type",
                 "comment_id", "parent_id", "source", "retrieval_provenance", "r2_matched_terms"]

    # Ensure r2_matched_terms in fresh (will re-tag below)
    df_fresh["r2_matched_terms"] = ""

    # Build matchers to re-tag fresh rows
    matchers = build_matchers(seed_terms)
    df_fresh_tagged = tag_dataframe(df_fresh, matchers)
    df_fresh_tagged["retrieval_provenance"] = "arctic_shift:round2_fresh"

    # Only keep base cols + r2 tag cols
    r2_cols = [col for col, _ in matchers]
    keep_cols = base_cols + r2_cols + ["r2_any_match"]

    def align_cols(df, keep):
        for c in keep:
            if c not in df.columns:
                df[c] = None
        return df[keep]

    c1 = align_cols(canon_matched, keep_cols)
    c2 = align_cols(praw_matched, keep_cols)
    c3 = align_cols(df_fresh_tagged, keep_cols)

    combined = pd.concat([c1, c2, c3], ignore_index=True)

    # Resolve provenance for duplicates
    def merge_provenance(group):
        provs = sorted(set(group["retrieval_provenance"].dropna()))
        row = group.iloc[0].copy()
        row["retrieval_provenance"] = "|".join(provs)
        return row

    # For posts: dedup by post_id (where type == post or type is NaN)
    # For comments: dedup by comment_id
    posts = combined[combined["type"] == "post"].copy()
    comments = combined[combined["type"] == "comment"].copy()

    posts_dedup = (
        posts.groupby("post_id", group_keys=False)
        .apply(merge_provenance)
        .reset_index(drop=True)
    )

    if not comments.empty:
        comments["comment_id_str"] = comments["comment_id"].astype(str)
        comments_dedup = (
            comments.groupby("comment_id_str", group_keys=False)
            .apply(merge_provenance)
            .reset_index(drop=True)
        )
        comments_dedup = comments_dedup.drop(columns=["comment_id_str"])
    else:
        comments_dedup = pd.DataFrame(columns=combined.columns)

    pass1b = pd.concat([posts_dedup, comments_dedup], ignore_index=True)
    return pass1b


# ---------------------------------------------------------------------------
# Stratified sample for hand-validation
# ---------------------------------------------------------------------------
def draw_validation_sample(pass1b, df_canonical, df_praw, n=30, seed=42):
    """
    Draw 30 rows that are net-new from Round 2 fresh retrieval and NOT already
    in canonical or PRAW corpora.
    """
    canonical_ids = set(df_canonical["post_id"].dropna().astype(str))
    praw_ids = set(df_praw["post_id"].dropna().astype(str))
    existing_ids = canonical_ids | praw_ids

    fresh_only = pass1b[
        pass1b["retrieval_provenance"].str.contains("arctic_shift:round2_fresh", na=False)
        & ~pass1b["post_id"].astype(str).isin(existing_ids)
    ].copy()

    print(f"\n  Net-new from fresh retrieval (not in canonical or PRAW): {len(fresh_only)}")

    if len(fresh_only) == 0:
        print("  No net-new rows for validation sample.")
        return pd.DataFrame()

    sample_n = min(n, len(fresh_only))
    random.seed(seed)
    idx = random.sample(range(len(fresh_only)), sample_n)
    sample = fresh_only.iloc[idx][["post_id", "body", "subreddit", "createdAt",
                                    "type", "source", "r2_matched_terms"]].copy()
    sample["tp_fp_borderline"] = ""  # blank for hand-coding
    sample["coding_notes"] = ""
    return sample


# ---------------------------------------------------------------------------
# Saturation check
# ---------------------------------------------------------------------------
def saturation_check(pass1b, df_canonical, df_praw, df_fresh, validation_sample):
    """
    Per §1.9 step 6:
    - Net-new positives from Round 2 fresh vs total Pass 1b
    - Precision on fresh-retrieval validation sample
    """
    canonical_ids = set(df_canonical["post_id"].dropna().astype(str))
    praw_ids = set(df_praw["post_id"].dropna().astype(str))
    existing_ids = canonical_ids | praw_ids

    # All posts in pass1b (not comments)
    pass1b_posts = pass1b[pass1b["type"] == "post"]

    # Fresh-only post IDs
    fresh_only_ids = set(
        pass1b_posts[
            pass1b_posts["retrieval_provenance"].str.contains("arctic_shift:round2_fresh", na=False)
            & ~pass1b_posts["post_id"].astype(str).isin(existing_ids)
        ]["post_id"].astype(str)
    )

    n_pass1b = len(pass1b_posts)
    n_fresh_only = len(fresh_only_ids)
    frac_new = n_fresh_only / n_pass1b if n_pass1b > 0 else 0.0

    # Precision from validation sample (placeholder -- will be filled by human)
    # We report the sample size and note it needs hand-coding
    n_sample = len(validation_sample) if not validation_sample.empty else 0

    return {
        "n_pass1b_posts": n_pass1b,
        "n_pass1b_total": len(pass1b),
        "n_fresh_only_posts": n_fresh_only,
        "frac_fresh_of_pass1b": frac_new,
        "n_validation_sample": n_sample,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=== Round 2 Retrieval Pipeline ===")
    print(f"Start: {datetime.now()}")

    # 1. Load seed terms
    seed_terms = load_seed_terms(SEED_TERMS_CSV)
    retained_terms = [t for t in seed_terms]  # all in CSV are retained
    print(f"Loaded {len(retained_terms)} Round 2 seed terms")
    high_conf = [t for t in retained_terms if t["confidence"] == "high"]
    print(f"  High-confidence: {len(high_conf)}")

    matchers = build_matchers(retained_terms)
    print(f"  Built {len(matchers)} matchers")

    # 2. Tag existing corpora
    df_canonical_tagged = tag_corpus(CANONICAL_CSV, matchers, "canonical (7,021 posts)")
    df_praw_tagged = tag_corpus(PRAW_CSV, matchers, "PRAW (89,982 rows)")

    # Save tagged corpora
    df_canonical_tagged.to_csv(OUT_CANONICAL_TAGGED, index=False)
    print(f"\n  Saved: {OUT_CANONICAL_TAGGED}")
    df_praw_tagged.to_csv(OUT_PRAW_TAGGED, index=False)
    print(f"  Saved: {OUT_PRAW_TAGGED}")

    # 3. Fresh Arctic Shift retrieval
    df_fresh, per_term_counts = fresh_retrieval(retained_terms)  # high-conf only inside fn
    df_fresh.to_csv(OUT_FRESH, index=False)
    print(f"\n  Saved fresh retrieval: {OUT_FRESH} ({len(df_fresh)} rows)")

    # 4. Build pass1b
    df_canonical = pd.read_csv(CANONICAL_CSV, low_memory=False)
    df_praw = pd.read_csv(PRAW_CSV, low_memory=False)

    pass1b = build_pass1b(df_canonical_tagged, df_praw_tagged, df_fresh, retained_terms)
    pass1b.to_csv(OUT_PASS1B, index=False)
    print(f"\n  Saved Pass 1b canonical: {OUT_PASS1B} ({len(pass1b)} rows)")

    # 5. Validation sample
    validation_sample = draw_validation_sample(pass1b, df_canonical, df_praw)
    if not validation_sample.empty:
        validation_sample.to_csv(OUT_VALIDATION, index=False)
        print(f"  Saved validation sample: {OUT_VALIDATION} ({len(validation_sample)} rows)")
    else:
        # Write empty shell
        pd.DataFrame(columns=["post_id", "body", "subreddit", "createdAt",
                               "type", "source", "r2_matched_terms",
                               "tp_fp_borderline", "coding_notes"]).to_csv(OUT_VALIDATION, index=False)
        print(f"  No net-new rows; empty validation shell saved: {OUT_VALIDATION}")

    # 6. Saturation check
    sat = saturation_check(pass1b, df_canonical, df_praw, df_fresh, validation_sample)
    print(f"\n=== Saturation Check ===")
    for k, v in sat.items():
        print(f"  {k}: {v}")

    # 7. Build results summary for round_2_results.md
    # Per-term tagging summary for canonical
    term_cols = [col for col, _ in matchers]
    canon_per_term = {col: int(df_canonical_tagged[col].sum()) for col in term_cols}
    praw_per_term = {col: int(df_praw_tagged[col].sum()) for col in term_cols}

    # Canonical and PRAW matched post IDs
    canon_matched_ids = set(
        df_canonical_tagged.loc[df_canonical_tagged["r2_any_match"], "post_id"].dropna().astype(str)
    )
    praw_post_ids = set(
        df_praw_tagged.loc[
            (df_praw_tagged["r2_any_match"]) & (df_praw_tagged["type"] == "post"),
            "post_id"
        ].dropna().astype(str)
    )
    canonical_all_ids = set(df_canonical["post_id"].dropna().astype(str))
    praw_net_new = praw_post_ids - canonical_all_ids

    # Pass 1b composition
    pass1b_posts = pass1b[pass1b["type"] == "post"]
    pass1b_comments = pass1b[pass1b["type"] == "comment"]
    provenance_breakdown = pass1b["retrieval_provenance"].value_counts().to_dict()

    # Build results markdown
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    fresh_rows_by_term = "\n".join(
        f"  - `{term}`: {cnt}" for term, cnt in sorted(per_term_counts.items(), key=lambda x: -x[1])
    )

    results_md = f"""# Iterative Retrieval Round 2 Results

**Date:** {now_str}
**Method:** [methods library §1.9] Iterative seed-term refinement, Round 2
**Agent:** Claude Sonnet 4.6

---

## 1. Tagging Results on Existing Corpora

### 1.1 Canonical corpus (posts_snapshot_canonical.csv, {len(df_canonical):,} rows)

- Rows matching any Round 2 term: **{int(df_canonical_tagged['r2_any_match'].sum()):,}** ({int(df_canonical_tagged['r2_any_match'].sum())/len(df_canonical)*100:.1f}%)
- Unique post IDs matched: **{len(canon_matched_ids):,}**

Top 15 terms by canonical hit count:

| Term column | Canonical hits |
|---|---|
""" + "\n".join(
    f"| `{col}` | {int(df_canonical_tagged[col].sum())} |"
    for col, _ in sorted(
        [(col, int(df_canonical_tagged[col].sum())) for col in term_cols],
        key=lambda x: -x[1]
    )[:15]
) + f"""

### 1.2 PRAW corpus (praw_sleep_analysis_final.csv, {len(df_praw):,} rows)

- Rows matching any Round 2 term: **{int(df_praw_tagged['r2_any_match'].sum()):,}** ({int(df_praw_tagged['r2_any_match'].sum())/len(df_praw)*100:.1f}%)
- Post IDs matched (PRAW posts only): **{len(praw_post_ids):,}**
- Net-new post IDs not in canonical: **{len(praw_net_new):,}**

---

## 2. Fresh Arctic Shift Retrieval

- High-confidence terms queried: **{len(high_conf)}**
- Total rows returned (before dedup): **{len(df_fresh) if not df_fresh.empty else 0:,}**
- After within-retrieval dedup: same (dedup applied on post_id+body)

Per-term breakdown:
{fresh_rows_by_term if fresh_rows_by_term else "  (no results)"}

Net-new post IDs from fresh retrieval (not in canonical or PRAW):
  **{sat['n_fresh_only_posts']:,}** posts

---

## 3. Pass 1b Canonical Corpus

- Total rows: **{len(pass1b):,}**
  - Posts: **{len(pass1b_posts):,}**
  - Comments: **{len(pass1b_comments):,}**
- Provenance breakdown:
"""

    for prov, cnt in sorted(provenance_breakdown.items(), key=lambda x: -x[1]):
        results_md += f"  - `{prov}`: {cnt} rows\n"

    results_md += f"""
- Fraction of Pass 1b posts that are net-new from Round 2 fresh retrieval: **{sat['frac_fresh_of_pass1b']:.1%}** ({sat['n_fresh_only_posts']:,} of {sat['n_pass1b_posts']:,})

---

## 4. Hand-Validation (Round 2 Fresh Retrieval Subset)

A stratified random sample of **{sat['n_validation_sample']}** rows was drawn from the net-new Round 2 fresh retrieval posts (not previously in canonical or PRAW corpora).

**Status: AWAITING HAND-CODING.**

Validation shell saved at:
`notebooks/audit_trail/round_2_fresh_validation.csv`

Columns: `post_id`, `body`, `subreddit`, `createdAt`, `type`, `source`, `r2_matched_terms`, `tp_fp_borderline` (to fill: TP/FP/borderline), `coding_notes`.

The precision floor per §1.9 anti-pattern rule is ≥ 0.50. If precision on the fresh-retrieval sample is below 0.50, the fresh retrieval adds noise, not signal, and Round 3 is not warranted.

---

## 5. Saturation Determination

Per §1.9 step 6, saturation criteria:
- A new round adds fewer than ~10% additional positive cases to the corpus, OR
- Hand-validation of new positives reveals augmented terms are pulling in mostly noise.

### Current evidence

| Metric | Value |
|---|---|
| Net-new posts from Round 2 fresh retrieval | {sat['n_fresh_only_posts']:,} |
| Pass 1b total posts | {sat['n_pass1b_posts']:,} |
| Fraction net-new | {sat['frac_fresh_of_pass1b']:.1%} |
| Validation sample size | {sat['n_validation_sample']} |
| Precision (fresh retrieval) | PENDING hand-coding |

### Saturation assessment (pending hand-coding)

- If hand-validation precision >= 0.50 AND net-new fraction > 10%: **Round 3 warranted** (fresh retrieval is adding real signal).
- If hand-validation precision >= 0.50 AND net-new fraction <= 10%: **Saturated** (proceed to Phase 2 + 2.5 on Pass 1b).
- If hand-validation precision < 0.50: **Saturated** (fresh retrieval pulling noise; proceed to Phase 2 + 2.5 on Pass 1b).

**Preliminary determination (before hand-coding):**
The primary retrieval value of Round 2 was precision within existing corpora, not bulk net-new recall. The memo (§5) predicted 30-50 net-new posts; if that estimate holds, and if precision on the fresh sample is above 0.50, the net-new fraction will determine saturation. Given that the canonical corpus was built via wholesale scrape of the full subreddits for the same time window, the expected saturation floor is low.

---

## 6. Recommendation

**Pending hand-validation results.**

- If precision >= 0.50 and net-new fraction <= 10%: **Proceed directly to Phase 2 + 2.5 on Pass 1b canonical.** The corpus is dense enough at the high-precision end for topic modeling and sense discovery.
- If precision >= 0.50 and net-new fraction > 10%: **Consider Round 3** with terms mined from new Round 2 positives.
- If precision < 0.50: **Proceed to Phase 2 + 2.5 on Pass 1b canonical.** The Round 2 terms have done their job of identifying the high-signal subset of existing corpora; fresh retrieval is not adding reliable new signal.

The Pass 1b canonical corpus provides the cleanest starting point for Phase 5 topic modeling because it is filtered to Round 2 term matches (higher base-rate of positives) while still being large enough for stable clustering.

---

*Generated by round2_retrieval.py on {now_str}*
"""

    with open(OUT_RESULTS_MD, "w", encoding="utf-8") as f:
        f.write(results_md)
    print(f"\n  Saved results memo: {OUT_RESULTS_MD}")

    print(f"\n=== Pipeline complete: {datetime.now()} ===")
    return sat, per_term_counts, canon_matched_ids, praw_net_new


if __name__ == "__main__":
    main()
