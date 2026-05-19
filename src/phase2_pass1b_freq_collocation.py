"""
Phase 2 Pass 1b — Frequency / N-gram / Collocation Analysis
Sleep-Nudge Project

Input:  data/pass1b_canonical.csv  (773 rows: 242 posts + 531 comments)
Output: deliverables/phase_2_pass1b/sleep_freq_collocation/

Data-quality fixes carried forward from canonical re-run:
  - Strip preview.redd.it and similar URL fragments before tokenization
  - Minimum token length 3 (resolves `wa` curly-apostrophe artifact)
  - PMI minimum co-occurrence floor of 5 for collocations

Tasks:
  1. Raw frequency tables (unigram, bigram, trigram) x 4 preprocessing variants, top 500
  2. Stratify by `type` (post vs comment)
  3. Stratify by `retrieval_provenance` (3 source groups)
  4. Domain stop-word candidates (top-50 inspection)
  5. Collocations around all seed terms (Phase 1 + Round 2), windows 5/10/20, PMI min-cooc 5, top 50
  6. N-grams n=2,3,4 top 200; skipgrams skip-dist 1 and 2 top 200
  7. Comparison to prior passes (wholesale 4,114 and canonical 7,021)
  8. Summary written to audit_trail
"""

import re
import os
import csv
import json
import math
import random
import itertools
import collections
from pathlib import Path

import pandas as pd

# ---- NLTK lemmatizer only (avoids corpus-path security issue in Claude sandbox) ----
# Stopword list is hardcoded to avoid the NLTK corpus path validation bug when running
# inside the Claude Code sandbox environment (which adds its own path to nltk.data.path
# before we can pin it, causing a security violation on the corpus root check).
import nltk
nltk.data.path = ["C:/Users/drhea/AppData/Roaming/nltk_data"]
from nltk.stem import WordNetLemmatizer

# ---- paths ----
REPO = Path("C:/Users/drhea/repos/claude-sleep-analysis")
DATA_DIR = REPO / "data"
OUT_DIR = REPO / "deliverables/phase_2_pass1b/sleep_freq_collocation"
AUDIT_DIR = REPO / "notebooks/audit_trail"
PRIOR_PHASE2_DIR = REPO / "deliverables/phase_2/sleep_freq_collocation"
PRIOR_RERUN_DIR = REPO / "deliverables/phase_2_rerun/sleep_freq_collocation"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- load corpus ----
df = pd.read_csv(DATA_DIR / "pass1b_canonical.csv")
print(f"Loaded {len(df)} rows: {dict(df['type'].value_counts())}")

# ---- URL strip (same regex as canonical re-run) ----
URL_RE = re.compile(
    r"(?:https?://\S+)|(?:www\.\S+)|(?:\[.*?\]\(.*?\))",
    re.IGNORECASE
)

def strip_urls(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return URL_RE.sub(" ", text)

# ---- tokenizer ----
TOKEN_RE = re.compile(r"\b[a-z]{3,}\b")   # alpha-only, min length 3

# NLTK English stopwords hardcoded (standard list) to avoid Claude sandbox
# path validation issue that prevents loading from the nltk corpus reader.
# Also includes known WordNetLemmatizer artifacts: "wa" (from "was"),
# "ha" (from "has"), "doe" (from "does") -- these must be filtered post-lemma.
EN_STOPS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","yourselves","he","him","his","himself","she","her","hers",
    "herself","it","its","itself","they","them","their","theirs","themselves",
    "what","which","who","whom","this","that","these","those","am","is","are",
    "was","were","be","been","being","have","has","had","having","do","does",
    "did","doing","a","an","the","and","but","if","or","because","as","until",
    "while","of","at","by","for","with","about","against","between","into",
    "through","during","before","after","above","below","to","from","up","down",
    "in","out","on","off","over","under","again","further","then","once","here",
    "there","when","where","why","how","all","both","each","few","more","most",
    "other","some","such","no","nor","not","only","own","same","so","than","too",
    "very","s","t","can","will","just","don","should","now","d","ll","m","o",
    "re","ve","y","ain","aren","couldn","didn","doesn","hadn","hasn","haven",
    "isn","ma","mightn","mustn","needn","shan","shouldn","wasn","weren","won",
    "wouldn","also","however","would","could","may","might","shall","must",
    "need","ought","dare","any","every","its","let",
    # WordNetLemmatizer artifacts (lemmatized forms of common words that survive
    # the 3-char floor but are noise):
    "wa",   # was -> wa
    "ha",   # has -> ha
    "doe",  # does -> doe
    "wo",   # won't -> wo (2 chars, caught by floor, but listed for completeness)
}
lemmatizer = WordNetLemmatizer()

def tokenize(text: str, remove_stops: bool = False, lemmatize: bool = False) -> list:
    clean = strip_urls(text).lower()
    tokens = TOKEN_RE.findall(clean)
    if lemmatize:
        tokens = [lemmatizer.lemmatize(t) for t in tokens]
    if remove_stops:
        tokens = [t for t in tokens if t not in EN_STOPS]
    return tokens

# ============================
#  SECTION 1 — SEED TERMS
# ============================

# Phase 1 seed anchors (distinct single-token anchors from seed term list)
PHASE1_SEEDS = [
    "sleep", "rest", "bed", "break", "tired", "exhausted", "fatigued",
    "late", "tonight", "tomorrow", "midnight", "paternalistic", "patronizing",
    "lecturing", "moralizing", "scolding", "bedtime"
]

# Round 2 seeds (from seed_terms_round_2.csv) -- compound phrases kept as-is for phrase matching
ROUND2_SEEDS_PHRASES = [
    "go to bed", "go to sleep", "now sleep", "get some rest", "sleep for real",
    "you are tired", "you must go to sleep", "take a break", "it needs some rest",
    "claude said it needs to rest", "take the rest of the night off",
    "call it a day", "call it a night", "go get some rest", "go sleep",
    "we can work on this later", "too tired to continue", "that's a good place to leave",
    "we have done enough in this session", "you did enough today",
    "pick this up tomorrow", "i suggest we pause here and continue tomorrow",
    "the responsible thing is to stop", "well rested",
    "sending me to bed", "put me to bed", "sent me to bed",
    "told me to go to bed", "nanny", "nagging", "unsolicited parenting",
    "who asked", "spiraling", "bedtime", "long session", "nudge",
    "enough for today", "finish this then sleep", "you need to eat"
]

# Single-token anchors derived from Round 2 seed phrases (for collocation analysis)
ROUND2_SINGLE_ANCHORS = [
    "nanny", "nagging", "spiraling", "nudge"
]

# Combined anchor list for collocations
ALL_SEED_ANCHORS = sorted(set(PHASE1_SEEDS + ROUND2_SINGLE_ANCHORS))

# Phrase anchors for phrase-search collocations (multi-word)
PHRASE_ANCHORS = [
    "go to bed", "go to sleep", "get some rest", "take a break",
    "call it a night", "call it a day", "pick this up tomorrow",
    "put me to bed", "sent me to bed", "told me to go to bed",
    "unsolicited parenting", "long session"
]

# ============================
#  HELPER FUNCTIONS
# ============================

def write_csv(path: Path, rows: list, fieldnames: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def freq_table(tokens: list, top_n: int = 500) -> list:
    counter = collections.Counter(tokens)
    return [{"term": t, "count": c} for t, c in counter.most_common(top_n)]

def ngram_freq(tokens: list, n: int, top_n: int = 200) -> list:
    ngrams = [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
    counter = collections.Counter(ngrams)
    return [{"ngram": ng, "n": n, "count": c} for ng, c in counter.most_common(top_n)]

def skipgram_freq(tokens: list, n: int = 2, skip: int = 1, top_n: int = 200) -> list:
    """Generate skipgrams of length n with `skip` tokens allowed between positions."""
    results = []
    for i in range(len(tokens)):
        for combo in itertools.combinations(range(i, min(i + n + n*skip, len(tokens))), n):
            if max(combo) - min(combo) <= n + (n-1)*skip:
                results.append(" ".join(tokens[j] for j in combo))
    counter = collections.Counter(results)
    return [{"skipgram": sg, "skip_dist": skip, "count": c} for sg, c in counter.most_common(top_n)]

def compute_pmi(word1: str, word2: str, cooc_count: int, freq1: int, freq2: int, total_tokens: int) -> float:
    if cooc_count == 0 or freq1 == 0 or freq2 == 0 or total_tokens == 0:
        return float("-inf")
    p_xy = cooc_count / total_tokens
    p_x = freq1 / total_tokens
    p_y = freq2 / total_tokens
    return math.log2(p_xy / (p_x * p_y))

def collocation_window(texts: list, anchor: str, window: int, min_cooc: int = 5,
                       top_n: int = 50) -> list:
    """
    Compute collocates of `anchor` within `window` tokens on each side.
    `anchor` may be multi-word; match as substring of joined-token stream.
    Returns list of {collocate, co_occurrences, pmi} sorted by PMI desc.
    """
    anchor_tokens = anchor.lower().split()
    anchor_len = len(anchor_tokens)

    cooc_counter = collections.Counter()
    anchor_count = 0
    term_counter = collections.Counter()
    total_tokens = 0

    for text in texts:
        tokens = tokenize(text, remove_stops=False, lemmatize=False)
        total_tokens += len(tokens)
        for t in tokens:
            term_counter[t] += 1

        # Find anchor positions
        for i in range(len(tokens) - anchor_len + 1):
            if tokens[i:i+anchor_len] == anchor_tokens:
                anchor_count += 1
                left = max(0, i - window)
                right = min(len(tokens), i + anchor_len + window)
                context = tokens[left:i] + tokens[i+anchor_len:right]
                for ct in context:
                    if ct not in EN_STOPS and len(ct) >= 3 and ct not in anchor_tokens:
                        cooc_counter[ct] += 1

    if anchor_count == 0:
        return []

    rows = []
    for collocate, cooc in cooc_counter.most_common():
        if cooc < min_cooc:
            break
        pmi = compute_pmi(anchor, collocate, cooc, anchor_count,
                          term_counter.get(collocate, 0), total_tokens)
        rows.append({"collocate": collocate, "co_occurrences": cooc, "pmi": round(pmi, 4)})

    rows.sort(key=lambda r: r["pmi"], reverse=True)
    return rows[:top_n]


# ============================
#  SECTION 2 — PREPROCESSING VARIANTS
# ============================

VARIANTS = [
    ("stops_off_lemma_off",  False, False),
    ("stops_off_lemma_on",   False, True),
    ("stops_on_lemma_off",   True,  False),
    ("stops_on_lemma_on",    True,  True),
]

def compute_freq_tables(texts: list, label: str, out_prefix: str):
    """Compute unigram/bigram/trigram for all 4 variants, save top-500 each."""
    for suffix, rm_stops, do_lemma in VARIANTS:
        all_tokens = []
        for t in texts:
            all_tokens.extend(tokenize(t, remove_stops=rm_stops, lemmatize=do_lemma))

        # Unigram
        uni = freq_table(all_tokens, top_n=500)
        write_csv(
            OUT_DIR / f"freq_unigram_{label}_{suffix}.csv",
            uni, ["term", "count"]
        )

        # Bigram
        bi_tokens = all_tokens  # already preprocessed
        bi = ngram_freq(bi_tokens, n=2, top_n=500)
        write_csv(
            OUT_DIR / f"freq_bigram_{label}_{suffix}.csv",
            bi, ["ngram", "n", "count"]
        )

        # Trigram
        tri = ngram_freq(bi_tokens, n=3, top_n=500)
        write_csv(
            OUT_DIR / f"freq_trigram_{label}_{suffix}.csv",
            tri, ["ngram", "n", "count"]
        )

        print(f"  [{label} | {suffix}] unigram top-1: {uni[0] if uni else 'none'}")


# ============================
#  MAIN ANALYSIS RUNS
# ============================

all_texts = df["body"].tolist()

print("\n=== Task 1: Full corpus frequency tables ===")
compute_freq_tables(all_texts, "full", "full")

print("\n=== Task 2: Stratify by type (post vs comment) ===")
for type_val in ["post", "comment"]:
    subset = df[df["type"] == type_val]["body"].tolist()
    print(f"  type={type_val}: {len(subset)} texts")
    compute_freq_tables(subset, f"type_{type_val}", f"type_{type_val}")

print("\n=== Task 3: Stratify by retrieval_provenance ===")
# Group provenance values into 3 categories per the saturation report §3
def provenance_group(prov: str) -> str:
    if isinstance(prov, float):
        return "unknown"
    if "arctic_shift:round2_fresh" in prov and "canonical:round2_match" not in prov and "praw:round2_match" not in prov:
        return "arctic_shift_only"
    if "canonical:round2_match" in prov and "arctic_shift:round2_fresh" not in prov and "praw:round2_match" not in prov:
        return "canonical_only"
    if "praw:round2_match" in prov and "arctic_shift:round2_fresh" not in prov and "canonical:round2_match" not in prov:
        return "praw_only"
    return "multi_source"

df["provenance_group"] = df["retrieval_provenance"].apply(provenance_group)
prov_counts = df["provenance_group"].value_counts()
print(f"  Provenance groups: {dict(prov_counts)}")

for grp in df["provenance_group"].unique():
    subset = df[df["provenance_group"] == grp]["body"].tolist()
    print(f"  provenance_group={grp}: {len(subset)} texts")
    compute_freq_tables(subset, f"prov_{grp}", f"prov_{grp}")

print("\n=== Task 4: Domain stop-word candidates (top-50 inspection) ===")
# Use stops_off, lemma_on on full corpus
all_tokens_raw = []
for t in all_texts:
    all_tokens_raw.extend(tokenize(t, remove_stops=False, lemmatize=True))
top50_raw = collections.Counter(all_tokens_raw).most_common(50)
domain_candidates = []
for rank, (term, count) in enumerate(top50_raw, 1):
    total_tokens = len(all_tokens_raw)
    pct = round(count / total_tokens * 100, 3)
    is_stop = term in EN_STOPS
    domain_candidates.append({
        "rank": rank,
        "term": term,
        "count": count,
        "pct_of_tokens": pct,
        "in_nltk_stops": is_stop
    })
write_csv(OUT_DIR / "domain_stopword_candidates.csv", domain_candidates,
          ["rank", "term", "count", "pct_of_tokens", "in_nltk_stops"])
print(f"  Top-50 written. Top-10: {[r['term'] for r in domain_candidates[:10]]}")

print("\n=== Task 5: Collocations around all seed terms ===")
for anchor in ALL_SEED_ANCHORS + PHRASE_ANCHORS:
    safe = anchor.replace(" ", "_").replace("'", "").replace(",", "")
    for w in [5, 10, 20]:
        rows = collocation_window(all_texts, anchor, window=w, min_cooc=5, top_n=50)
        fpath = OUT_DIR / f"collocation_{safe}_w{w}.csv"
        write_csv(fpath, rows, ["collocate", "co_occurrences", "pmi"])
        print(f"  {anchor} | w={w}: {len(rows)} collocates (floor=5)")

print("\n=== Task 6: N-grams and skipgrams ===")
# Use stops_on + lemma_on for n-gram/skipgram tables (same as prior passes)
tokens_on_on = []
for t in all_texts:
    tokens_on_on.extend(tokenize(t, remove_stops=True, lemmatize=True))

for n in [2, 3, 4]:
    rows = ngram_freq(tokens_on_on, n=n, top_n=200)
    write_csv(OUT_DIR / f"ngram_n{n}_stops_on_lemma_on.csv", rows, ["ngram", "n", "count"])
    print(f"  n={n}: {len(rows)} rows. Top: {rows[0] if rows else 'none'}")

for skip in [1, 2]:
    rows = skipgram_freq(tokens_on_on, n=2, skip=skip, top_n=200)
    write_csv(OUT_DIR / f"skipgram_skip{skip}_stops_on_lemma_on.csv", rows,
              ["skipgram", "skip_dist", "count"])
    print(f"  skip={skip}: {len(rows)} rows. Top: {rows[0] if rows else 'none'}")


print("\n=== Task 7: Comparison to prior passes ===")

def load_prior_freq(path: Path) -> dict:
    """Load a prior freq CSV into {term: count}."""
    result = {}
    if not path.exists():
        return result
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result[row.get("term", row.get("ngram", ""))] = int(row.get("count", 0))
    return result

# Load pass1b unigram (stops_on lemma_on) — this pass uses a "full_" label prefix
pass1b_uni = load_prior_freq(OUT_DIR / "freq_unigram_full_stops_on_lemma_on.csv")

# Load prior passes (wholesale 4,114 and canonical 7,021)
# Prior pass filenames do NOT have a corpus label prefix (saved as-is by the prior scripts)
prior_4114 = load_prior_freq(PRIOR_PHASE2_DIR / "freq_unigram_stops_on_lemma_on.csv")
prior_7021 = load_prior_freq(PRIOR_RERUN_DIR / "freq_unigram_stops_on_lemma_on.csv")
print(f"  Pass1b terms loaded: {len(pass1b_uni)}")
print(f"  Prior 4114 terms loaded: {len(prior_4114)}")
print(f"  Prior 7021 terms loaded: {len(prior_7021)}")

# Check what files actually exist in prior dirs
print(f"  Prior phase2 dir files: {list(PRIOR_PHASE2_DIR.glob('freq_unigram*.csv'))[:5]}")
print(f"  Prior rerun dir files: {list(PRIOR_RERUN_DIR.glob('freq_unigram*.csv'))[:5]}")

# Build comparison for top-100 terms across all three corpora
all_terms = set(list(pass1b_uni.keys())[:100]) | set(list(prior_4114.keys())[:100]) | set(list(prior_7021.keys())[:100])

# Corpus sizes for normalization
n_pass1b = sum(pass1b_uni.values()) or 1
n_4114   = sum(prior_4114.values()) or 1
n_7021   = sum(prior_7021.values()) or 1

comparison_rows = []
for term in sorted(all_terms):
    c1b = pass1b_uni.get(term, 0)
    c4k = prior_4114.get(term, 0)
    c7k = prior_7021.get(term, 0)
    comparison_rows.append({
        "term": term,
        "pass1b_773_count": c1b,
        "pass1b_773_per1k": round(c1b / n_pass1b * 1000, 4),
        "wholesale_4114_count": c4k,
        "wholesale_4114_per1k": round(c4k / n_4114 * 1000, 4),
        "canonical_7021_count": c7k,
        "canonical_7021_per1k": round(c7k / n_7021 * 1000, 4),
        "ratio_pass1b_vs_4114": round((c1b / n_pass1b) / max(c4k / n_4114, 1e-9), 4),
        "ratio_pass1b_vs_7021": round((c1b / n_pass1b) / max(c7k / n_7021, 1e-9), 4),
    })

# Sort by pass1b per1k desc
comparison_rows.sort(key=lambda r: r["pass1b_773_per1k"], reverse=True)

write_csv(
    OUT_DIR / "comparison_wholesale_vs_pass1b.csv",
    comparison_rows,
    ["term", "pass1b_773_count", "pass1b_773_per1k",
     "wholesale_4114_count", "wholesale_4114_per1k",
     "canonical_7021_count", "canonical_7021_per1k",
     "ratio_pass1b_vs_4114", "ratio_pass1b_vs_7021"]
)
print(f"  Comparison table: {len(comparison_rows)} terms")

# ---- grab top-20 from each for the summary ----
top20_pass1b = [(r["term"], r["pass1b_773_per1k"]) for r in comparison_rows[:20]]
print(f"  Top-20 pass1b terms (per-1k): {top20_pass1b}")

# ---- terms dramatically elevated in pass1b vs wholesale ----
elevated = [r for r in comparison_rows if r["ratio_pass1b_vs_7021"] >= 3.0 and r["pass1b_773_count"] >= 5]
elevated.sort(key=lambda r: r["ratio_pass1b_vs_7021"], reverse=True)
print(f"  Elevated terms (ratio>=3x, n>=5): {[(r['term'], r['ratio_pass1b_vs_7021']) for r in elevated[:20]]}")


print("\n=== Saving summary data JSON ===")
# Collect key stats for the summary doc
summary_data = {
    "corpus_size": len(df),
    "posts": int((df["type"] == "post").sum()),
    "comments": int((df["type"] == "comment").sum()),
    "provenance_groups": dict(df["provenance_group"].value_counts()),
    "top20_unigrams_full_stops_on_lemma_on": [
        {"rank": i+1, "term": r["term"], "count": r["pass1b_773_count"]}
        for i, r in enumerate(comparison_rows[:20])
    ],
    "domain_stopword_candidates_top10": domain_candidates[:10],
    "elevated_terms_vs_wholesale": elevated[:15],
    "collocation_anchors_run": ALL_SEED_ANCHORS + PHRASE_ANCHORS,
    "windows_run": [5, 10, 20],
    "pmi_min_cooc_floor": 5,
    "ngram_n_values": [2, 3, 4],
    "skipgram_skip_distances": [1, 2],
}
def _json_safe(obj):
    """Recursively convert numpy int64/float64 to native Python types."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.int64, np.int32, np.integer)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32, np.floating)):
        return float(obj)
    return obj

with open(OUT_DIR / "_summary_data.json", "w", encoding="utf-8") as f:
    json.dump(_json_safe(summary_data), f, indent=2)

print("\nDone. All outputs written to:", OUT_DIR)
