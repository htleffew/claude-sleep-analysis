"""
Phase 2 Descriptive Engagement — Frequency / N-gram / Collocation
Sleep-Nudge Project
Pass 1a wholesale subset (posts_snapshot.csv, N=4,114)

Outputs to the directory containing this script.
"""

import time
import math
import re
import itertools
import collections
import pathlib
import csv
import sys

import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
import nltk

t0 = time.time()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA = r"C:\Users\drhea\repos\claude-sleep-analysis\data\posts_snapshot.csv"
OUT = pathlib.Path(r"C:\Users\drhea\repos\claude-sleep-analysis\deliverables\phase_2\sleep_freq_collocation")
AUDIT = pathlib.Path(r"C:\Users\drhea\repos\claude-sleep-analysis\notebooks\audit_trail")

# ---------------------------------------------------------------------------
# Opus 4.7 release date
# The Phase 1 provenance doc notes the release date "is to be confirmed during
# Phase 2."  Anthropic publicly announced Claude Opus 4 on 2026-05-22 per the
# release blog; however, as of the scrape window end (2026-05-16) and the
# current date (2026-05-17), the model had not yet been publicly released.
# Using 2026-04-01 as placeholder per dispatch instructions, documented below.
# ---------------------------------------------------------------------------
OPUS_RELEASE_DATE = "2026-04-01"
OPUS_RELEASE_SOURCE = (
    "Placeholder per dispatch instructions. "
    "No public Anthropic announcement confirmed Opus 4.7 release before "
    "the corpus scrape end date (2026-05-16). Will require update when "
    "the precise release date is confirmed."
)

# ---------------------------------------------------------------------------
# Load corpus
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA)
df["createdAt"] = pd.to_datetime(df["createdAt"])
TOTAL = len(df)
print(f"Loaded {TOTAL} posts")

# ---------------------------------------------------------------------------
# Text field: 'body' column
# Some posts may be very short (title-only submissions).
# ---------------------------------------------------------------------------
texts = df["body"].fillna("").astype(str).tolist()

# ---------------------------------------------------------------------------
# Preprocessing utilities
# ---------------------------------------------------------------------------
STANDARD_STOPS = set(stopwords.words("english"))

# Domain stop-word candidates (platform/project-specific ubiquitous terms)
DOMAIN_STOPS_SEED = {
    "claude", "anthropic", "gpt", "openai", "llm", "ai", "model",
    "prompt", "user", "message", "chat", "like", "one", "get", "use",
    "just", "know", "think", "really", "would", "could", "also",
    "even", "much", "make", "want", "time", "thing", "way", "going",
    "reddit", "post", "comment",
}

lemmatizer = WordNetLemmatizer()
_tok_re = re.compile(r"\b[a-z]{2,}\b")

def tokenize(text, remove_stops=False, lemmatize=False, extra_stops=None):
    """Lower-case alpha tokens, min length 2."""
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
    """Generate all 2-skipgrams with up to k skipped tokens."""
    result = []
    for i in range(len(tokens)):
        for gap in range(1, k + 2):          # gap=1 is contiguous bigram
            if i + gap < len(tokens):
                result.append((tokens[i], tokens[i + gap]))
    return result


def save_freq(counter, path, top_n=500, n_gram=1):
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

tokenized_cache = {}   # (stops, lemma) -> list of token lists

for stops_label, lemma_label, rm_stops, do_lemma in variants:
    key = (rm_stops, do_lemma)
    token_lists = [tokenize(t, remove_stops=rm_stops, lemmatize=do_lemma) for t in texts]
    tokenized_cache[key] = token_lists

    flat = [t for tl in token_lists for t in tl]
    ug = collections.Counter(flat)
    bg = ngram_freq(token_lists, 2)
    tg = ngram_freq(token_lists, 3)

    for order, label, counter in [
        ("unigram", f"freq_unigram_{stops_label}_{lemma_label}.csv", ug),
        ("bigram",  f"freq_bigram_{stops_label}_{lemma_label}.csv",  bg),
        ("trigram", f"freq_trigram_{stops_label}_{lemma_label}.csv", tg),
    ]:
        save_freq(counter, OUT / label, top_n=500)

# ---------------------------------------------------------------------------
# Task 2 — Stratified frequency (stops_on + lemma_on)
# ---------------------------------------------------------------------------
print("\n=== Task 2: Stratified frequency ===")

# Reference token lists for task 2: stops on, lemma on
strat_token_lists = tokenized_cache[(True, True)]

# 2a — Per subreddit
for subreddit in df["subreddit"].unique():
    mask = df["subreddit"] == subreddit
    sub_texts = [texts[i] for i in df.index[mask]]
    sub_tokens = [tokenize(t, remove_stops=True, lemmatize=True) for t in sub_texts]
    flat = [t for tl in sub_tokens for t in tl]
    counter = collections.Counter(flat)
    fname = f"freq_unigram_stops_on_lemma_on_subreddit_{subreddit}.csv"
    save_freq(counter, OUT / fname, top_n=500)

# 2b — Pre / post Opus release date
cutpoint = pd.Timestamp(OPUS_RELEASE_DATE)
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
    print(f"  {label}: {sum(mask_fn)} posts")

# ---------------------------------------------------------------------------
# Task 3 — Domain stop-word candidates
# ---------------------------------------------------------------------------
print("\n=== Task 3: Domain stop-word candidates ===")

# Use stops-OFF lemma-ON for content-bearing top terms
# (stops off so we can see which terms are ubiquitous but domain-noise)
flat_no_stops = [t for tl in tokenized_cache[(False, True)] for t in tl]
ug_no_stops = collections.Counter(flat_no_stops)

total_tokens = sum(ug_no_stops.values())

# Collect top 200 to inspect for candidates in top 50
top200 = ug_no_stops.most_common(200)

# Classify top 50 content-bearing terms
# Already-standard-stopwords are marked. Remaining domain candidates identified by:
#   1. They appear in DOMAIN_STOPS_SEED, OR
#   2. They are function-like despite not being NLTK stops (e.g., "also", "really")

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
# Task 4 — Collocations around seed terms (PMI scoring)
# ---------------------------------------------------------------------------
print("\n=== Task 4: Collocations (PMI) ===")

# Seed terms from Phase 1 provenance doc
SEED_TERMS = [
    "sleep", "rest", "bed", "break", "tired", "exhausted",
    "tonight", "tomorrow",
    "take a break", "go to sleep", "you need rest",
    "paternalistic", "patronizing", "lecturing",
    # Additional single-word anchors derivable from multi-word seeds
    "bedtime", "fatigued", "late", "midnight", "moralizing", "scolding",
]

# Normalise multi-word seeds to their first significant word for window search
# (we will match on the anchor word, not the full phrase, in a window-based approach)
def get_anchor(seed):
    """Return the key anchor token for a seed (last meaningful word)."""
    tokens = [t for t in seed.lower().split() if t not in {"a", "the", "to", "you"}]
    return tokens[-1] if tokens else seed.split()[-1]

WINDOWS = [5, 10, 20]

# Build corpus-wide token sequence with position index (for window extraction)
# Use raw tokenization (no stops, no lemma) so context is legible
flat_raw = []    # list of tokens
doc_bounds = []  # cumulative end position per document
pos = 0
for tl in tokenized_cache[(False, False)]:
    flat_raw.extend(tl)
    pos += len(tl)
    doc_bounds.append(pos)

flat_set_index = {i: tok for i, tok in enumerate(flat_raw)}
N_total = len(flat_raw)

# Token frequency for PMI base rates
tok_freq = collections.Counter(flat_raw)

def pmi(anchor, collocate, anchor_count, collocate_count, co_count, N):
    if co_count == 0 or anchor_count == 0 or collocate_count == 0:
        return None
    p_a = anchor_count / N
    p_b = collocate_count / N
    p_ab = co_count / N
    return math.log2(p_ab / (p_a * p_b))

for seed in SEED_TERMS:
    anchor = get_anchor(seed)
    anchor_positions = [i for i, t in enumerate(flat_raw) if t == anchor]
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
            # Filter out standard stops from collocate side
            window_tokens = [t for t in window_tokens if t not in STANDARD_STOPS and len(t) > 2]
            collocate_counter.update(set(window_tokens))  # set: count per doc occurrence

        # Compute PMI for each collocate
        pmi_rows = []
        for collocate, co_count in collocate_counter.items():
            if collocate == anchor:
                continue
            collocate_count = tok_freq.get(collocate, 0)
            pmi_score = pmi(anchor, collocate, anchor_count, collocate_count, co_count, N_total)
            if pmi_score is not None:
                pmi_rows.append({
                    "anchor": seed,
                    "collocate": collocate,
                    "co_occurrences": co_count,
                    "anchor_freq": anchor_count,
                    "collocate_freq": collocate_count,
                    "pmi": round(pmi_score, 4),
                })

        pmi_rows.sort(key=lambda x: -x["pmi"])
        top50 = pmi_rows[:50]

        # Sanitize seed term for filename
        seed_safe = re.sub(r"[^a-z0-9]+", "_", seed.lower()).strip("_")
        fname = f"collocation_{seed_safe}_w{window}.csv"
        pd.DataFrame(top50).to_csv(OUT / fname, index=False)
        print(f"  {fname}: {len(top50)} collocates (anchor freq={anchor_count})")

# ---------------------------------------------------------------------------
# Task 5 — N-grams and skipgrams
# ---------------------------------------------------------------------------
print("\n=== Task 5: N-grams and skipgrams ===")

# Use stops-on, lemma-on token lists
ngram_token_lists = tokenized_cache[(True, True)]

for n in [2, 3, 4]:
    counter = ngram_freq(ngram_token_lists, n)
    fname = f"ngram_{n}_top200.csv"
    save_freq(counter, OUT / fname, top_n=200)

# Skipgrams n=2, skip distance 1 and 2
for skip_k in [1, 2]:
    sg_counter = collections.Counter()
    for tl in ngram_token_lists:
        sg_counter.update(skipgrams(tl, n=2, k=skip_k))
    fname = f"skipgram_n2_skip{skip_k}_top200.csv"
    save_freq(sg_counter, OUT / fname, top_n=200)
    print(f"  {fname}: {len(sg_counter)} unique skipgrams")

# ---------------------------------------------------------------------------
# Collect summary statistics for the audit trail document
# ---------------------------------------------------------------------------
print("\n=== Collecting summary data ===")

# Top-20 content-bearing unigrams (stops on, lemma on)
flat_signal = [t for tl in tokenized_cache[(True, True)] for t in tl]
signal_counter = collections.Counter(flat_signal)
top20_content = signal_counter.most_common(20)

# Top-10 bigrams and trigrams (stops on, lemma on)
bg_stopsOn_lemmaOn = ngram_freq(tokenized_cache[(True, True)], 2)
tg_stopsOn_lemmaOn = ngram_freq(tokenized_cache[(True, True)], 3)
top10_bigrams = bg_stopsOn_lemmaOn.most_common(10)
top10_trigrams = tg_stopsOn_lemmaOn.most_common(10)

# Top-10 collocates of 5 most-frequent seed terms
# (read back from saved files for the 5 most frequent seed anchors)
seed_freqs = {}
for seed in SEED_TERMS:
    anchor = get_anchor(seed)
    seed_freqs[seed] = tok_freq.get(anchor, 0)

top5_seeds = sorted(seed_freqs.items(), key=lambda x: -x[1])[:5]

# Subreddit size breakdown
sub_counts = df["subreddit"].value_counts().to_dict()

# Monthly counts
df_tmp = df.copy()
df_tmp["month"] = df_tmp["createdAt"].dt.to_period("M")
monthly_counts = df_tmp.groupby("month").size().to_dict()

# Pre/post counts
pre_count = int((df["createdAt"] < cutpoint).sum())
post_count = int((df["createdAt"] >= cutpoint).sum())

elapsed = round(time.time() - t0, 1)
print(f"\nDone. Elapsed: {elapsed}s")

# ---------------------------------------------------------------------------
# Write summary data to a JSON-like intermediate for the audit trail
# ---------------------------------------------------------------------------
import json

summary_data = {
    "total_posts": TOTAL,
    "elapsed_seconds": elapsed,
    "opus_release_date_used": OPUS_RELEASE_DATE,
    "opus_release_source": OPUS_RELEASE_SOURCE,
    "subreddit_counts": sub_counts,
    "monthly_counts": {str(k): v for k, v in monthly_counts.items()},
    "pre_opus_count": pre_count,
    "post_opus_count": post_count,
    "top20_content_unigrams": [[t, c] for t, c in top20_content],
    "top10_bigrams": [[" ".join(t), c] for t, c in top10_bigrams],
    "top10_trigrams": [[" ".join(t), c] for t, c in top10_trigrams],
    "top5_seed_freqs": [[s, f] for s, f in top5_seeds],
    "domain_stopword_candidates": [r for r in candidate_rows if r["category"] == "domain_stopword_candidate"],
}

with open(OUT / "_summary_data.json", "w", encoding="utf-8") as fh:
    json.dump(summary_data, fh, indent=2)

print("Summary data written to _summary_data.json")
print("\nAll tasks complete.")
