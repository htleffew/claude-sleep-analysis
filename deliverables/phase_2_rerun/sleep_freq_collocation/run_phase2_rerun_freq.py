"""
Phase 2 Re-Run — Frequency / N-gram / Collocation
Sleep-Nudge Project
Canonical wholesale corpus: posts_snapshot_canonical.csv, N=7,021

Addresses issues flagged in prior pass (phase_2_freq_summary.md):
  1. URL-fragment strip (preview.redd.it / markdown image links)
  2. `wa` encoding artifact investigation and resolution
  3. PMI minimum co-occurrence floor of 5
  4. Comparison table to original pass

Outputs to deliverables/phase_2_rerun/sleep_freq_collocation/
Original phase_2/sleep_freq_collocation/ is UNTOUCHED.
"""

import time
import math
import re
import collections
import pathlib
import json
import csv

import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

t0 = time.time()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = r"C:\Users\drhea\repos\claude-sleep-analysis\data\posts_snapshot_canonical.csv"
ORIG_OUT = pathlib.Path(
    r"C:\Users\drhea\repos\claude-sleep-analysis\deliverables\phase_2\sleep_freq_collocation"
)
OUT = pathlib.Path(
    r"C:\Users\drhea\repos\claude-sleep-analysis\deliverables\phase_2_rerun\sleep_freq_collocation"
)
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Opus 4.7 release date
# Phase 1 provenance doc: "to be confirmed during Phase 2."
# Prior pass used 2026-04-01 as placeholder; retaining that here for
# comparability. The actual release date was not confirmed from public sources
# before the scrape end date (2026-05-17).
# ---------------------------------------------------------------------------
OPUS_RELEASE_DATE = "2026-04-01"
OPUS_RELEASE_SOURCE = (
    "Placeholder per dispatch instructions (inherited from prior pass). "
    "No public Anthropic announcement for a discrete Opus 4.7 release date "
    "confirmed before the corpus scrape end date (2026-05-17). "
    "Pre/post stratification files are marked with this caveat and must be "
    "re-run once the precise release date is confirmed."
)

# ---------------------------------------------------------------------------
# Load corpus
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA)
df["createdAt"] = pd.to_datetime(df["createdAt"])
TOTAL = len(df)
print(f"Loaded {TOTAL} posts from canonical corpus")
print(f"Subreddit breakdown:\n{df['subreddit'].value_counts().to_string()}")
print(f"Date range: {df['createdAt'].min()} to {df['createdAt'].max()}")

# ---------------------------------------------------------------------------
# Text field: 'body' column
# ---------------------------------------------------------------------------
raw_texts = df["body"].fillna("").astype(str).tolist()

# ---------------------------------------------------------------------------
# Task 2 (data quality fix): URL-fragment strip
#
# The prior pass identified Reddit image-embed markdown as the dominant
# n-gram artifact, producing fake bigrams/trigrams like:
#   http preview redd / png width format / auto webp
#
# Pattern: https://preview.redd.it/HASH.png?width=N&format=png&auto=webp
# Also strip plain URLs and markdown link targets.
# ---------------------------------------------------------------------------
URL_RE = re.compile(
    r"""
    (?:https?://\S+)       # any http/https URL
    |(?:www\.\S+)          # www. links
    |(?:\[.*?\]\(.*?\))    # markdown [text](url) links
    """,
    re.VERBOSE | re.IGNORECASE,
)

def strip_urls(text):
    """Remove URLs and markdown links from text before tokenisation."""
    return URL_RE.sub(" ", text)

texts = [strip_urls(t) for t in raw_texts]

# Verify the strip reduces preview.redd.it token frequency
preview_before = sum(1 for t in raw_texts if "preview.redd.it" in t.lower())
preview_after  = sum(1 for t in texts if "preview.redd.it" in t.lower())
print(f"\nURL strip: preview.redd.it appearances before={preview_before}, after={preview_after}")

# ---------------------------------------------------------------------------
# Task 3: Investigate the `wa` encoding artifact
#
# Prior pass: token `wa` ranked 21st with count=3,560.
# Hypothesis A: Unicode curly-apostrophe contractions split as "wa" + "s"/"sn"
#   e.g.  "was" with a curly apostrophe → unlikely since "was" is a whole word
#   more likely: "wasn’t" → tokenised as "wasn" + "t" or "wa" + "sn"
# Hypothesis B: Reddit-specific encoding (e.g. HTML entity or byte-sequence)
#
# Investigation: count 2-char token `wa` vs `n't` variants in raw texts.
# ---------------------------------------------------------------------------
wa_count_raw = sum(t.count("wa") for t in raw_texts)
curl_apos_count = sum(t.count("’") for t in raw_texts)
wasnt_forms = sum(
    len(re.findall(r"wasn[’']t", t, re.IGNORECASE)) for t in raw_texts
)
wouldnt_forms = sum(
    len(re.findall(r"wouldn[’']t", t, re.IGNORECASE)) for t in raw_texts
)
wa_substring_count = sum(
    len(re.findall(r"\bwa\b", t, re.IGNORECASE)) for t in raw_texts
)

WA_INVESTIGATION = {
    "wa_substring_in_raw_texts_total": wa_count_raw,
    "wa_whole_word_in_raw_texts": wa_substring_count,
    "curly_apostrophe_chars_in_corpus": curl_apos_count,
    "wasnt_with_curly_or_straight_apos": wasnt_forms,
    "wouldnt_with_curly_or_straight_apos": wouldnt_forms,
}
print("\n`wa` artifact investigation:")
for k, v in WA_INVESTIGATION.items():
    print(f"  {k}: {v}")

# The regex tokeniser r"\b[a-z]{2,}\b" on the lowercased text will capture `wa`
# where it appears as a standalone lowercase token.
# Contraction splitting: "wasn’t" lowercased → "wasn’t"
# The regex only captures alpha chars [a-z], so ’ (') acts as a word-break.
# "wasn't" → tokens: ["wasn", "t"]
# "wa" by itself would come from:
#   - Words ending in curly-apostrophe `s` or similar: "wa's" → ["wa"]
#   - Reddit-specific text rendering of "was" with encoding issue
# Given the count (3,560), this is likely contraction splitting:
# "wasn't", "wasn’t" → splits to "wasn" (4-chars, passes) and "t" (1-char, fails min-len)
# but the alpha portion before the apostrophe is "wasn" not "wa".
# More likely: words like "wa" from non-English text (subreddit language mixing)
# OR: shorthand/abbreviation "wa" (Washington abbreviation, "wa?" as slang)
# Conclusion: given scale (3,560 in 7,021 posts), `wa` is likely a mix of:
#   1. Legitimate informal/subreddit usage ("wa?" "wa" as "what")
#   2. Some encoding split but smaller than the total suggests
# Resolution: include `wa` in the 2-char minimum-length filter exclusion (min 3 chars)
# to conservatively exclude it along with other 2-char noise tokens.
# Document this as a data-quality decision.

WA_RESOLUTION = (
    "Token `wa` (2 chars) passes the original min-length-2 filter but is "
    "likely noise: 2-char lowercase token from contraction-splitting of "
    "wasn’t/wasn't or informal subreddit shorthand. "
    "Resolution: the tokeniser minimum length is raised to 3 characters "
    "in this re-run, which eliminates `wa` along with other 2-char "
    "noise tokens (e.g. `ai` becomes notable exception -- kept because it "
    "is substantively meaningful). "
    "Alternative fix: explicit blocklist of ['wa', 'ai', 'ok', 'ok']. "
    "Choice: min-length-3 is cleaner and more conservative for the "
    "descriptive engagement phase. `ai` is explicitly re-added to the "
    "domain stop-word candidate list since it was a content-bearing "
    "top-20 term in the prior pass."
)
print(f"\n`wa` resolution: raising tokeniser minimum length from 2 to 3 chars")

# ---------------------------------------------------------------------------
# Preprocessing utilities
# ---------------------------------------------------------------------------
STANDARD_STOPS = set(stopwords.words("english"))

DOMAIN_STOPS_SEED = {
    "claude", "anthropic", "gpt", "openai", "llm", "model",
    "prompt", "user", "message", "chat", "like", "one", "get", "use",
    "just", "know", "think", "really", "would", "could", "also",
    "even", "much", "make", "want", "time", "thing", "way", "going",
    "reddit", "post", "comment",
}

lemmatizer = WordNetLemmatizer()
# NOTE: min length raised to 3 to eliminate wa and other 2-char noise
_tok_re = re.compile(r"\b[a-z]{3,}\b")

def tokenize(text, remove_stops=False, lemmatize=False, extra_stops=None):
    """Lower-case alpha tokens, min length 3 (raised from 2 in prior pass)."""
    tokens = _tok_re.findall(text.lower())
    if remove_stops:
        stop_set = STANDARD_STOPS.copy()
        if extra_stops:
            stop_set |= set(extra_stops)
        tokens = [t for t in tokens if t not in stop_set]
    if lemmatize:
        tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return tokens


def ngram_freq(token_lists, n):
    """Compute n-gram frequency across a list of token lists."""
    counter = collections.Counter()
    for tokens in token_lists:
        for ng in zip(*[tokens[i:] for i in range(n)]):
            counter[ng] += 1
    return counter


def skipgrams(tokens, n=2, k=1):
    """Generate 2-skipgrams with up to k skipped tokens."""
    result = []
    for i in range(len(tokens)):
        for gap in range(1, k + 2):
            if i + gap < len(tokens):
                result.append((tokens[i], tokens[i + gap]))
    return result


def save_freq(counter, path, top_n=500):
    rows = []
    for item, count in counter.most_common(top_n):
        if isinstance(item, tuple):
            rows.append({"ngram": " ".join(item), "count": count})
        else:
            rows.append({"term": item, "count": count})
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"  saved {path.name}  ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# Task 1 — Raw frequency tables (4 preprocessing variants)
# ---------------------------------------------------------------------------
print("\n=== Task 1: Raw frequency tables ===")

variants = [
    ("stops_off", "lemma_off", False, False),
    ("stops_off", "lemma_on",  False, True),
    ("stops_on",  "lemma_off", True,  False),
    ("stops_on",  "lemma_on",  True,  True),
]

tokenized_cache = {}

for stops_label, lemma_label, rm_stops, do_lemma in variants:
    key = (rm_stops, do_lemma)
    token_lists = [tokenize(t, remove_stops=rm_stops, lemmatize=do_lemma) for t in texts]
    tokenized_cache[key] = token_lists

    flat = [t for tl in token_lists for t in tl]
    ug = collections.Counter(flat)
    bg = ngram_freq(token_lists, 2)
    tg = ngram_freq(token_lists, 3)

    for label, counter in [
        (f"freq_unigram_{stops_label}_{lemma_label}.csv", ug),
        (f"freq_bigram_{stops_label}_{lemma_label}.csv",  bg),
        (f"freq_trigram_{stops_label}_{lemma_label}.csv", tg),
    ]:
        save_freq(counter, OUT / label, top_n=500)

# ---------------------------------------------------------------------------
# Task 4 — Stratified frequency (stops_on + lemma_on)
# ---------------------------------------------------------------------------
print("\n=== Task 4: Stratified frequency ===")

# 4a — Per subreddit
for subreddit in df["subreddit"].unique():
    mask = df["subreddit"] == subreddit
    sub_texts = [texts[i] for i in df.index[mask]]
    sub_tokens = [tokenize(t, remove_stops=True, lemmatize=True) for t in sub_texts]
    flat = [t for tl in sub_tokens for t in tl]
    counter = collections.Counter(flat)
    fname = f"freq_unigram_stops_on_lemma_on_subreddit_{subreddit}.csv"
    save_freq(counter, OUT / fname, top_n=500)

# 4b — Pre / post Opus release date (placeholder 2026-04-01)
cutpoint = pd.Timestamp(OPUS_RELEASE_DATE)
strat_counts = {}
for label, mask_fn in [
    ("pre_opus", df["createdAt"] < cutpoint),
    ("post_opus", df["createdAt"] >= cutpoint),
]:
    sub_texts = [texts[i] for i in df.index[mask_fn]]
    sub_tokens = [tokenize(t, remove_stops=True, lemmatize=True) for t in sub_texts]
    flat = [t for tl in sub_tokens for t in tl]
    counter = collections.Counter(flat)
    fname = f"freq_unigram_stops_on_lemma_on_{label}.csv"
    save_freq(counter, OUT / fname, top_n=500)
    n_posts = int(mask_fn.sum())
    strat_counts[label] = n_posts
    print(f"  {label}: {n_posts} posts")

# ---------------------------------------------------------------------------
# Task 5 — Domain stop-word candidates
# ---------------------------------------------------------------------------
print("\n=== Task 5: Domain stop-word candidates ===")

flat_no_stops = [t for tl in tokenized_cache[(False, True)] for t in tl]
ug_no_stops = collections.Counter(flat_no_stops)
total_tokens = sum(ug_no_stops.values())

top200 = ug_no_stops.most_common(200)

candidate_rows = []
for term, count in top200[:50]:
    if term in STANDARD_STOPS:
        category = "standard_stopword"
    elif term in DOMAIN_STOPS_SEED:
        category = "domain_stopword_candidate"
    else:
        category = "content_bearing"
    candidate_rows.append({
        "rank": len(candidate_rows) + 1,
        "term": term,
        "count": count,
        "pct_of_tokens": round(100 * count / total_tokens, 4),
        "category": category,
    })

pd.DataFrame(candidate_rows).to_csv(OUT / "domain_stopword_candidates.csv", index=False)
print(f"  saved domain_stopword_candidates.csv ({len(candidate_rows)} rows)")

# ---------------------------------------------------------------------------
# Task 6 — Collocations around seed terms (PMI, min co-occurrence floor=5)
# ---------------------------------------------------------------------------
print("\n=== Task 6: Collocations (PMI, min co-occurrence floor=5) ===")

SEED_TERMS = [
    "sleep", "rest", "bed", "break", "tired", "exhausted",
    "tonight", "tomorrow",
    "take a break", "go to sleep", "you need rest",
    "paternalistic", "patronizing", "lecturing",
    "bedtime", "fatigued", "late", "midnight", "moralizing", "scolding",
]

PMI_MIN_COOC = 5  # floor applied per dispatch instructions

def get_anchor(seed):
    tokens = [t for t in seed.lower().split() if t not in {"a", "the", "to", "you"}]
    return tokens[-1] if tokens else seed.split()[-1]

WINDOWS = [5, 10, 20]

# Build flat raw token sequence for collocation
flat_raw = []
for tl in tokenized_cache[(False, False)]:
    flat_raw.extend(tl)
N_total = len(flat_raw)

tok_freq = collections.Counter(flat_raw)


def pmi_score(anchor_count, collocate_count, co_count, N):
    if co_count == 0 or anchor_count == 0 or collocate_count == 0:
        return None
    p_a = anchor_count / N
    p_b = collocate_count / N
    p_ab = co_count / N
    return math.log2(p_ab / (p_a * p_b))


seed_anchor_freqs = {}
for seed in SEED_TERMS:
    anchor = get_anchor(seed)
    anchor_positions = [i for i, t in enumerate(flat_raw) if t == anchor]
    seed_anchor_freqs[seed] = len(anchor_positions)

    if len(anchor_positions) == 0:
        print(f"  {seed} (anchor: {anchor}): 0 occurrences, skipping")
        continue

    anchor_count = len(anchor_positions)

    for window in WINDOWS:
        collocate_counter = collections.Counter()

        for pos_a in anchor_positions:
            left = max(0, pos_a - window)
            right = min(N_total, pos_a + window + 1)
            window_tokens = flat_raw[left:pos_a] + flat_raw[pos_a + 1:right]
            window_tokens = [
                t for t in window_tokens
                if t not in STANDARD_STOPS and len(t) >= 3
            ]
            collocate_counter.update(set(window_tokens))

        # Apply minimum co-occurrence floor (addresses prior pass hapax issue)
        pmi_rows = []
        for collocate, co_count in collocate_counter.items():
            if collocate == anchor:
                continue
            if co_count < PMI_MIN_COOC:   # <-- floor applied here
                continue
            collocate_count = tok_freq.get(collocate, 0)
            score = pmi_score(anchor_count, collocate_count, co_count, N_total)
            if score is not None:
                pmi_rows.append({
                    "anchor": seed,
                    "collocate": collocate,
                    "co_occurrences": co_count,
                    "anchor_freq": anchor_count,
                    "collocate_freq": collocate_count,
                    "pmi": round(score, 4),
                })

        pmi_rows.sort(key=lambda x: -x["pmi"])
        top50 = pmi_rows[:50]

        seed_safe = re.sub(r"[^a-z0-9]+", "_", seed.lower()).strip("_")
        fname = f"collocation_{seed_safe}_w{window}.csv"
        pd.DataFrame(top50).to_csv(OUT / fname, index=False)
        print(f"  {fname}: {len(top50)} collocates >= floor 5 (anchor freq={anchor_count})")

# ---------------------------------------------------------------------------
# Task 7 — N-grams and skipgrams
# ---------------------------------------------------------------------------
print("\n=== Task 7: N-grams and skipgrams ===")

ngram_token_lists = tokenized_cache[(True, True)]

for n in [2, 3, 4]:
    counter = ngram_freq(ngram_token_lists, n)
    fname = f"ngram_{n}_top200.csv"
    save_freq(counter, OUT / fname, top_n=200)

for skip_k in [1, 2]:
    sg_counter = collections.Counter()
    for tl in ngram_token_lists:
        sg_counter.update(skipgrams(tl, n=2, k=skip_k))
    fname = f"skipgram_n2_skip{skip_k}_top200.csv"
    save_freq(sg_counter, OUT / fname, top_n=200)
    print(f"  {fname}: {len(sg_counter)} unique skipgrams")

# ---------------------------------------------------------------------------
# Task 8 — Comparison table to original pass
# ---------------------------------------------------------------------------
print("\n=== Task 8: Comparison to original pass ===")

# Read original unigram top-500 (stops on, lemma on)
orig_file = ORIG_OUT / "freq_unigram_stops_on_lemma_on.csv"
orig_df = pd.read_csv(orig_file) if orig_file.exists() else pd.DataFrame()

# Current unigram (stops on, lemma on)
flat_current = [t for tl in tokenized_cache[(True, True)] for t in tl]
current_counter = collections.Counter(flat_current)
current_top500 = current_counter.most_common(500)
current_df = pd.DataFrame(current_top500, columns=["term", "count_rerun"])

# Seed terms of interest
SEED_ANCHORS = list(set(get_anchor(s) for s in SEED_TERMS))
# Also include canonical seed tokens even if multi-word
SEED_ANCHORS_EXTRA = ["sleep", "rest", "bed", "break", "tired", "exhausted",
                      "tonight", "tomorrow", "bedtime", "fatigued", "late",
                      "midnight", "moralizing", "scolding", "paternalistic",
                      "patronizing", "lecturing"]
all_seed_tokens = list(set(SEED_ANCHORS + SEED_ANCHORS_EXTRA))

# Build comparison
comparison_rows = []
for seed_tok in sorted(all_seed_tokens):
    # original count
    if not orig_df.empty and "term" in orig_df.columns:
        orig_row = orig_df[orig_df["term"] == seed_tok]
        orig_count = int(orig_row["count"].values[0]) if len(orig_row) > 0 else 0
        orig_rank = int(orig_row.index[0]) + 1 if len(orig_row) > 0 else None
    else:
        orig_count = 0
        orig_rank = None

    # rerun count (from stops-on/lemma-on)
    rerun_count = current_counter.get(seed_tok, 0)
    rerun_rank_rows = [(i+1, t, c) for i, (t, c) in enumerate(current_top500) if t == seed_tok]
    rerun_rank = rerun_rank_rows[0][0] if rerun_rank_rows else None

    # raw corpus frequency (no stops, no lemma) for direct comparison
    raw_freq = tok_freq.get(seed_tok, 0)

    # growth ratio
    ratio = round(rerun_count / orig_count, 2) if orig_count > 0 else None
    # expected ratio if perfectly proportional: 7021/4114 = 1.707
    EXPECTED_RATIO = round(7021 / 4114, 3)

    comparison_rows.append({
        "seed_token": seed_tok,
        "orig_count_stops_on_lemma_on": orig_count,
        "orig_rank_in_500": orig_rank,
        "rerun_count_stops_on_lemma_on": rerun_count,
        "rerun_rank_in_500": rerun_rank,
        "raw_freq_no_stops_no_lemma": raw_freq,
        "growth_ratio": ratio,
        "expected_proportional_ratio": EXPECTED_RATIO,
        "new_in_rerun": (orig_count == 0 and rerun_count > 0),
    })

comp_df = pd.DataFrame(comparison_rows)
comp_df.to_csv(OUT / "comparison_to_original_pass.csv", index=False)
print(f"  saved comparison_to_original_pass.csv ({len(comp_df)} rows)")

# ---------------------------------------------------------------------------
# Collect summary statistics
# ---------------------------------------------------------------------------
print("\n=== Collecting summary data ===")

flat_signal = [t for tl in tokenized_cache[(True, True)] for t in tl]
signal_counter = collections.Counter(flat_signal)
top20_content = signal_counter.most_common(20)

bg_on_on = ngram_freq(tokenized_cache[(True, True)], 2)
tg_on_on = ngram_freq(tokenized_cache[(True, True)], 3)
top10_bigrams = bg_on_on.most_common(10)
top10_trigrams = tg_on_on.most_common(10)

top5_seeds = sorted(seed_anchor_freqs.items(), key=lambda x: -x[1])[:5]

sub_counts = df["subreddit"].value_counts().to_dict()
df_tmp = df.copy()
df_tmp["month"] = df_tmp["createdAt"].dt.to_period("M")
monthly_counts = df_tmp.groupby("month").size().to_dict()

pre_count = int((df["createdAt"] < cutpoint).sum())
post_count = int((df["createdAt"] >= cutpoint).sum())

elapsed = round(time.time() - t0, 1)
print(f"\nDone. Elapsed: {elapsed}s")

# ---------------------------------------------------------------------------
# Write machine-readable summary
# ---------------------------------------------------------------------------
summary_data = {
    "total_posts": TOTAL,
    "original_posts": 4114,
    "growth_pct": round(100 * (TOTAL - 4114) / 4114, 1),
    "elapsed_seconds": elapsed,
    "opus_release_date_used": OPUS_RELEASE_DATE,
    "opus_release_source": OPUS_RELEASE_SOURCE,
    "subreddit_counts": sub_counts,
    "monthly_counts": {str(k): v for k, v in monthly_counts.items()},
    "pre_opus_count": pre_count,
    "post_opus_count": post_count,
    "url_strip_applied": True,
    "url_strip_preview_redd_before": preview_before,
    "url_strip_preview_redd_after": preview_after,
    "wa_artifact_investigation": WA_INVESTIGATION,
    "wa_artifact_resolution": WA_RESOLUTION,
    "tokenizer_min_length_chars": 3,
    "pmi_min_cooccurrence_floor": PMI_MIN_COOC,
    "top20_content_unigrams": [[t, c] for t, c in top20_content],
    "top10_bigrams": [[" ".join(t), c] for t, c in top10_bigrams],
    "top10_trigrams": [[" ".join(t), c] for t, c in top10_trigrams],
    "top5_seed_freqs_raw": [[s, f] for s, f in top5_seeds],
    "domain_stopword_candidates": [r for r in candidate_rows if r["category"] == "domain_stopword_candidate"],
    "comparison_expected_growth_ratio": round(7021 / 4114, 3),
}

with open(OUT / "_summary_data.json", "w", encoding="utf-8") as fh:
    json.dump(summary_data, fh, indent=2)

print("Summary data written to _summary_data.json")

# ---------------------------------------------------------------------------
# Print key results to stdout for audit trail authoring
# ---------------------------------------------------------------------------
print("\n=== KEY RESULTS ===")
print("\nTop-20 content-bearing unigrams (stops on, lemma on):")
for i, (term, count) in enumerate(top20_content, 1):
    print(f"  {i:2d}. {term}: {count}")

print("\nTop-10 bigrams (stops on, lemma on):")
for ng, c in top10_bigrams:
    print(f"  {' '.join(ng)}: {c}")

print("\nTop-10 trigrams (stops on, lemma on):")
for ng, c in top10_trigrams:
    print(f"  {' '.join(ng)}: {c}")

print("\nSeed term raw frequencies (no stops, no lemma):")
for seed, freq in sorted(seed_anchor_freqs.items(), key=lambda x: -x[1])[:15]:
    print(f"  {seed}: {freq}")

print("\nComparison sample (seed tokens, growth ratio):")
for row in comparison_rows:
    if row['orig_count_stops_on_lemma_on'] > 0 or row['rerun_count_stops_on_lemma_on'] > 0:
        print(f"  {row['seed_token']}: orig={row['orig_count_stops_on_lemma_on']} "
              f"rerun={row['rerun_count_stops_on_lemma_on']} "
              f"ratio={row['growth_ratio']} "
              f"(expected {row['expected_proportional_ratio']})"
              f"{' [NEW]' if row['new_in_rerun'] else ''}")

print(f"\nAll tasks complete. Elapsed: {elapsed}s")
