"""
Discourse features analysis for the sleep-nudge phenomenon.

Complements sleep_discourse_analysis.py by adding the feature engineering
needed to test mirroring vs LCR-Zombie vs time-anchoring hypotheses.

Outputs (in deliverables/):
    quote_spans.csv                 - Extracted Claude utterances per post
    discourse_features.csv          - Per-post feature vectors
    disclosure_lexicons.json        - Lexicons used (reproducibility)
    pmi_disclosure_nudge.csv        - PMI/NMPI/LogDice between disclosure and nudge terms
    pmi_disclosure_nudge_directional.csv - Directional (disclosure precedes nudge)
    ngrams_4_5_top.csv              - 4-grams and 5-grams (idiomatic patterns)
    skipgrams_top.csv               - Skip-grams (templates with gaps)
    nrc_emotion_scores.csv          - NRC emotion category counts per post
    imperative_quotes.csv           - Imperative-mood quoted spans
    temporal_expressions.csv        - Extracted temporal references
    feature_clusters.csv            - KMeans clustering on feature space
    pmi_weekly_timeseries.csv       - Weekly PMI for the main associations
    its_results.csv                 - Interrupted time series at Opus 4.7 cutoff
    discourse_features_report.txt   - Human-readable summary

Run from Claude_Sleep_Analysis_V2/ directory.
"""

import argparse
import json
import math
import os
import re
import sys
import warnings
from collections import Counter, defaultdict
from datetime import datetime

# Use the improved V2 extractor for quote-span and transcript detection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quote_extractor_v2 import (
    extract_quote_spans_v2 as _extract_quote_spans_v2,
    has_transcript_structure_v2 as _has_transcript_structure_v2,
)

import numpy as np
import pandas as pd
import regex
import spacy
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------
# Paths & constants
# --------------------------------------------------------------------------

DATA_DIR = "data/"
OUTPUT_DIR = "deliverables/"

CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "praw_sleep_analysis_final_fallback_cleaned.csv"),
    os.path.join(DATA_DIR, "praw_sleep_analysis_final_fallback.csv"),
    os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv"),
]

OUTPUT_SUFFIX = ""  # set by CLI; appended to every output filename

# Opus 4.7 release. User reported April 1 or April 3. Default to April 3 (the
# later/more conservative choice). Change OPUS_CUTOFF to test sensitivity.
OPUS_CUTOFF = pd.Timestamp("2026-04-03")
FORTUNE_DATE = pd.Timestamp("2026-05-14")

# --------------------------------------------------------------------------
# Lexicons
# --------------------------------------------------------------------------

# The nudge target: what we're trying to detect Claude saying.
NUDGE_TERMS_UNIGRAM = {
    "sleep", "rest", "bed", "bedtime", "nap", "tomorrow", "morning",
    "break", "goodnight", "asleep", "tonight",
}
NUDGE_TERMS_PHRASE = [
    "call it a night", "call it a day", "get some rest", "get some sleep",
    "go to bed", "go to sleep", "try again tomorrow", "take a break",
    "step away", "needs rest", "need rest", "needs sleep", "need sleep",
    "good night", "have a good night", "see you tomorrow",
]

# Disclosure lexicons. Each tests a different trigger hypothesis.
TEMPORAL_DISCLOSURE = {
    "late", "night", "midnight", "am", "pm", "hour", "hours", "evening",
    "morning", "tonight", "overnight", "2am", "3am", "4am", "5am",
    "1am", "12am", "11pm", "10pm", "dawn", "wee", "afterhours",
}
TEMPORAL_DISCLOSURE_PHRASE = [
    "all day", "all night", "after midnight", "past midnight", "this morning",
    "last night", "this evening", "stayed up", "up late", "working late",
    "in the middle of the night", "way past", "wee hours",
]

AFFECTIVE_DISCLOSURE = {
    "tired", "exhausted", "frustrated", "stressed", "overwhelmed",
    "burned", "burnt", "fed", "struggling", "stuck", "dying",
    "spiraling", "spiral", "drained", "depleted", "wrecked",
    "broken", "fried", "done", "ugh", "annoyed",
}
AFFECTIVE_DISCLOSURE_PHRASE = [
    "burned out", "burnt out", "fed up", "losing it", "going crazy",
    "pulling my hair", "tired of", "can't think", "cant think",
    "brain fried", "brain dead", "running on fumes",
]

SESSION_DISCLOSURE = {
    "marathon", "forever", "hours", "ages", "all-nighter", "allnighter",
}
SESSION_DISCLOSURE_PHRASE = [
    "been working", "been at this", "for hours", "hours now", "deep into",
    "long session", "this whole", "too long", "really long", "all day",
    "all night", "since this morning", "since yesterday", "the whole day",
]

WORK_CONTEXT = {
    "coding", "debugging", "writing", "brainstorming", "vibing",
    "hyperfocused", "building", "designing", "analyzing", "researching",
    "studying", "reviewing", "refactoring", "shipping", "deploying",
    "crunching", "grinding", "iterating", "implementing", "vibecoding",
    "vibecode", "code", "bug", "feature",
}

# Mental-state verbs (signal first-person disclosure)
MENTAL_STATE_VERBS = {
    "think", "feel", "feeling", "felt", "know", "knew", "want", "wanted",
    "need", "needed", "hope", "wish", "believe", "fear", "worry",
    "worried", "struggle", "struggling", "miss", "love", "hate",
    "doubt", "afraid", "scared", "anxious",
}

# First-person markers
FIRST_PERSON = {
    "i", "me", "my", "mine", "myself", "im", "i'm", "ive", "i've",
    "id", "i'd", "ill", "i'll", "we", "us", "our", "ours",
}

# Soft directive / modal-imperative patterns
MODAL_DIRECTIVES = [
    r"\byou should\b", r"\byou might\b", r"\byou could\b",
    r"\bmaybe you\b", r"\bperhaps you\b", r"\bit's time to\b",
    r"\bit might be time\b", r"\bwhy don'?t you\b", r"\bhow about\b",
    r"\bconsider\b", r"\bi'?d suggest\b", r"\bi suggest\b",
    r"\bworth taking\b",
]

# Imperative-mood sentence starters (verb-initial)
IMPERATIVE_STARTERS = {
    "go", "get", "take", "try", "call", "stop", "step", "rest",
    "sleep", "close", "shut", "pause", "have", "let",
}

# Standard topic-modeling stopwords (filler that drags clustering toward
# incoherence). Layered on top of spaCy's default.
TOPIC_STOPWORDS = {
    "claude", "anthropic", "ai", "like", "just", "im", "dont", "tell",
    "tells", "told", "reddit", "post", "edit", "https", "model", "use",
    "thing", "way", "really", "actually", "basically", "kind", "sort",
    "time", "lately", "later", "interesting", "good", "great", "yeah",
    "youre", "thats", "people", "stuff", "lot", "bit",
}

# Disclosure-pass stopword set: KEEPS first-person, mental-state, modals.
# Strips only true filler so disclosure signal survives.
DISCLOSURE_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "at", "for", "with",
    "and", "or", "but", "if", "as", "by", "from", "into",
    "this", "that", "these", "those", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
}

# NRC fallback. Used only if NRCLex is unavailable. Hand-curated subset
# focused on fatigue/stress vocabulary relevant to this analysis.
NRC_FALLBACK = {
    "fear": {"afraid", "scared", "anxious", "worried", "panic", "dread",
             "nervous", "terror", "fright"},
    "anger": {"angry", "mad", "furious", "rage", "annoyed", "irritated",
              "frustrated", "pissed", "livid"},
    "anticipation": {"hope", "expect", "wait", "tomorrow", "soon",
                     "future", "plan", "ahead", "coming"},
    "trust": {"trust", "believe", "honest", "loyal", "faith", "confident",
              "rely", "safe"},
    "surprise": {"surprise", "wow", "shock", "unexpected", "sudden",
                 "amazed", "astonished", "gasp"},
    "sadness": {"sad", "depressed", "down", "blue", "lonely", "miserable",
                "heartbreaking", "cry", "tears", "grief"},
    "joy": {"happy", "joy", "great", "love", "wonderful", "delighted",
            "excited", "thrilled", "cheerful"},
    "disgust": {"disgust", "gross", "awful", "horrible", "nasty",
                "revolting", "sick"},
    "positive": {"good", "great", "amazing", "wonderful", "love", "happy",
                 "awesome", "best", "perfect"},
    "negative": {"bad", "awful", "terrible", "hate", "worst", "horrible",
                 "sad", "wrong", "broken", "tired", "exhausted"},
}

# --------------------------------------------------------------------------
# spaCy & NRC setup
# --------------------------------------------------------------------------

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

try:
    from nrclex import NRCLex  # type: ignore
    HAS_NRCLEX = True
except Exception:
    HAS_NRCLEX = False

SPACY_STOPWORDS = set(spacy.lang.en.stop_words.STOP_WORDS)

# --------------------------------------------------------------------------
# Loading & cleaning
# --------------------------------------------------------------------------

def pick_input_csv():
    for c in CSV_CANDIDATES:
        if os.path.exists(c):
            return c
    return None


def load_data(path=None):
    path = path or pick_input_csv()
    if path is None or not os.path.exists(path):
        return pd.DataFrame(), None
    df = pd.read_csv(path)
    df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
    df = df.dropna(subset=["body", "createdAt"]).reset_index(drop=True)
    return df, path


def clean_for_features(text):
    """Lightweight cleaning that preserves structural markers (>, ```, ")."""
    if pd.isna(text):
        return ""
    text = str(text)
    # Strip URLs but keep markers
    text = regex.sub(r"https?://\S+", " ", text)
    text = regex.sub(r"\r\n", "\n", text)
    return text


# --------------------------------------------------------------------------
# Quote-span extraction
# --------------------------------------------------------------------------

ATTRIBUTION_RE = re.compile(
    r"(?:claude|sonnet|opus|the model|the bot|it|he|she)\s+"
    r"(?:said|told\s+me|told\s+us|replied|responded|wrote|says|tells|writes|"
    r"answered|kept\s+saying)\s*[:,]?\s*",
    re.IGNORECASE,
)
ATTRIBUTION_LINE_RE = re.compile(
    r"^\s*(?:claude|sonnet|opus|bot|assistant|model|ai)\s*[:>\-–]\s*",
    re.IGNORECASE | re.MULTILINE,
)
BLOCKQUOTE_RE = re.compile(r"(?m)^\s*>\s?(.+)$")
CODEFENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_QUOTE_RE = re.compile(r"[\"“”]([^\"“”]{12,400})[\"“”]")


def extract_quote_spans(text):
    """Pull candidate Claude-utterance spans out of a post.

    Returns:
        quoted_text   - concatenated extracted spans
        narration     - rest of the post (user narration)
        sources       - list of (method, span) tuples for inspection
    """
    if not text:
        return "", "", []

    sources = []
    spans_to_remove = []

    # 1. Blockquotes
    for m in BLOCKQUOTE_RE.finditer(text):
        sources.append(("blockquote", m.group(1).strip()))
        spans_to_remove.append((m.start(), m.end()))

    # 2. Attribution prefix: "Claude said: <rest of sentence or next line>"
    for m in ATTRIBUTION_RE.finditer(text):
        tail = text[m.end():m.end() + 400]
        # Take up to the next double newline or quote close
        tail_cut = re.split(r"\n\n|(?<=[.!?])\s+(?=[A-Z])", tail, maxsplit=1)[0]
        tail_cut = tail_cut.strip()
        if 5 < len(tail_cut) < 400:
            sources.append(("attribution", tail_cut))
            spans_to_remove.append((m.start(), m.end() + len(tail_cut)))

    # 3. Inline-attribution lines: "Claude: ..."
    for m in ATTRIBUTION_LINE_RE.finditer(text):
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        span = text[m.end():line_end].strip()
        if len(span) > 5:
            sources.append(("speaker_label", span))
            spans_to_remove.append((m.start(), line_end))

    # 4. Inline quoted material that contains imperative/nudge content
    for m in INLINE_QUOTE_RE.finditer(text):
        inner = m.group(1).strip()
        low = inner.lower()
        if any(t in low for t in NUDGE_TERMS_UNIGRAM) or \
           any(p in low for p in NUDGE_TERMS_PHRASE):
            sources.append(("inline_quote", inner))
            spans_to_remove.append((m.start(), m.end()))

    quoted_text = " | ".join(s for _, s in sources)

    # Build narration by removing the matched spans
    spans_to_remove.sort()
    narration_parts = []
    cursor = 0
    for start, end in spans_to_remove:
        if start > cursor:
            narration_parts.append(text[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(text):
        narration_parts.append(text[cursor:])
    narration = " ".join(narration_parts)

    # Also strip code fences from narration so they don't pollute
    narration = CODEFENCE_RE.sub(" ", narration)

    return quoted_text, narration, sources


# --------------------------------------------------------------------------
# Lexicon hits
# --------------------------------------------------------------------------

def count_lexicon_hits(text, unigrams, phrases):
    if not text:
        return 0
    low = text.lower()
    tokens = re.findall(r"[a-zA-Z']+", low)
    token_hits = sum(1 for t in tokens if t in unigrams)
    phrase_hits = sum(low.count(p) for p in phrases)
    return token_hits + phrase_hits


def has_lexicon_hit(text, unigrams, phrases):
    return count_lexicon_hits(text, unigrams, phrases) > 0


def count_first_person(text):
    if not text:
        return 0
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return sum(1 for t in tokens if t in FIRST_PERSON)


def count_mental_state(text):
    if not text:
        return 0
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return sum(1 for t in tokens if t in MENTAL_STATE_VERBS)


def code_prose_ratio(text):
    if not text:
        return 0.0
    code_chars = sum(len(m.group(0)) for m in re.finditer(r"```.*?```", text, re.DOTALL))
    code_chars += sum(len(m.group(0)) for m in re.finditer(r"(?m)^    .+$", text))
    code_chars += sum(len(m.group(0)) for m in re.finditer(r"`[^`]+`", text))
    return code_chars / max(len(text), 1)


def has_transcript_structure(text):
    if not text:
        return False
    speaker_lines = len(re.findall(
        r"(?im)^\s*(me|you|user|claude|opus|sonnet|assistant|ai|bot|prompt|response)\s*[:>\-]",
        text,
    ))
    return speaker_lines >= 2


# --------------------------------------------------------------------------
# Modality / mood detection
# --------------------------------------------------------------------------

def detect_imperatives(text):
    """Return list of imperative-mood sentences in `text`."""
    if not text:
        return []
    out = []
    doc = nlp(text[:5000])  # cap for speed
    for sent in doc.sents:
        tokens = [t for t in sent if not t.is_space]
        if not tokens:
            continue
        first = tokens[0]
        if first.lower_ in IMPERATIVE_STARTERS and first.pos_ in {"VERB", "AUX"}:
            out.append(sent.text.strip())
            continue
        # General imperative: root is verb, no nsubj appears before root
        root = sent.root
        if root.pos_ in {"VERB", "AUX"}:
            has_subject_before = any(
                t.dep_ in {"nsubj", "nsubjpass"} and t.i < root.i for t in sent
            )
            if not has_subject_before and first.pos_ in {"VERB", "AUX"}:
                out.append(sent.text.strip())
    return out


def count_modal_directives(text):
    if not text:
        return 0
    low = text.lower()
    return sum(len(re.findall(p, low)) for p in MODAL_DIRECTIVES)


# --------------------------------------------------------------------------
# Temporal expression extraction
# --------------------------------------------------------------------------

TIME_REGEX = re.compile(
    r"\b("
    r"\d{1,2}\s?(?:am|pm)|"
    r"\d{1,2}:\d{2}(?:\s?(?:am|pm))?|"
    r"(?:mid)?night|noon|dawn|dusk|"
    r"all\s+(?:day|night)|"
    r"past\s+midnight|after\s+midnight|"
    r"(?:this|last|tomorrow|yesterday)\s+(?:morning|evening|night|afternoon)"
    r")\b",
    re.IGNORECASE,
)


def extract_temporal_expressions(text):
    if not text:
        return []
    out = []
    # spaCy NER for TIME/DATE
    doc = nlp(text[:5000])
    for ent in doc.ents:
        if ent.label_ in {"TIME", "DATE"}:
            out.append(ent.text.strip())
    # Regex augmentation
    for m in TIME_REGEX.finditer(text):
        out.append(m.group(0))
    return out


# --------------------------------------------------------------------------
# NRC emotion scoring
# --------------------------------------------------------------------------

NRC_CATEGORIES = [
    "fear", "anger", "anticipation", "trust", "surprise",
    "sadness", "joy", "disgust", "positive", "negative",
]


def nrc_scores(text):
    if not text:
        return {c: 0 for c in NRC_CATEGORIES}
    if HAS_NRCLEX:
        try:
            obj = NRCLex(text)
            counts = obj.raw_emotion_scores
            return {c: counts.get(c, 0) for c in NRC_CATEGORIES}
        except Exception:
            pass
    # Fallback: lexicon match
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    counts = {c: 0 for c in NRC_CATEGORIES}
    for tok in tokens:
        for cat in NRC_CATEGORIES:
            if tok in NRC_FALLBACK[cat]:
                counts[cat] += 1
    return counts


# --------------------------------------------------------------------------
# N-grams and skip-grams
# --------------------------------------------------------------------------

def tokenize_for_ngrams(text, stopwords):
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


def generate_ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def generate_skipgrams(tokens, gap_range=(1, 2)):
    """Bigram-style skip-grams allowing a 1 or 2 word gap."""
    out = []
    for gap in range(gap_range[0], gap_range[1] + 1):
        for i in range(len(tokens) - gap - 1):
            out.append(f"{tokens[i]} _ {tokens[i + gap + 1]}")
    return out


# --------------------------------------------------------------------------
# PMI / collocation
# --------------------------------------------------------------------------

def compute_pmi_table(df, lexicons, nudge_check_col, window_col, log=True):
    """Compute association between each disclosure lexicon and the nudge.

    df is per-post. nudge_check_col is a binary col (has a Claude nudge).
    window_col names a column with the user-side text used for disclosure.
    """
    n = len(df)
    if n == 0:
        return pd.DataFrame()

    rows = []
    n_nudge = int(df[nudge_check_col].sum())
    p_nudge = n_nudge / n if n else 0

    for lex_name, (unigrams, phrases) in lexicons.items():
        has_col = df[window_col].apply(
            lambda t: has_lexicon_hit(t, unigrams, phrases)
        ).astype(int)
        n_lex = int(has_col.sum())
        n_both = int(((df[nudge_check_col] == 1) & (has_col == 1)).sum())

        p_lex = n_lex / n
        p_both = n_both / n
        if p_lex == 0 or p_nudge == 0 or p_both == 0:
            pmi = 0.0
            nmpi = 0.0
        else:
            pmi = math.log2(p_both / (p_lex * p_nudge))
            nmpi = pmi / -math.log2(p_both)
        # LogDice on counts
        if n_lex + n_nudge > 0:
            logdice = 14 + math.log2((2 * n_both) / (n_lex + n_nudge)) if n_both > 0 else 0
        else:
            logdice = 0

        # Conditional probabilities (more interpretable than PMI alone)
        p_nudge_given_lex = n_both / n_lex if n_lex else 0
        p_lex_given_nudge = n_both / n_nudge if n_nudge else 0

        rows.append({
            "Disclosure_Lexicon": lex_name,
            "N_posts": n,
            "N_with_lexicon": n_lex,
            "N_with_nudge": n_nudge,
            "N_with_both": n_both,
            "P_nudge_given_lexicon": round(p_nudge_given_lex, 4),
            "P_lexicon_given_nudge": round(p_lex_given_nudge, 4),
            "PMI": round(pmi, 4),
            "NMPI": round(nmpi, 4),
            "LogDice": round(logdice, 4),
        })

    return pd.DataFrame(rows).sort_values("PMI", ascending=False)


def compute_pmi_directional(df, lexicons):
    """Directional: does disclosure precede the nudge in narration?

    Heuristic: split each post's full body at the first quoted span; if
    disclosure terms appear before the split and nudge appears in the quoted
    portion, count as directional.
    """
    rows = []
    n_total = len(df)
    if n_total == 0:
        return pd.DataFrame()

    for lex_name, (unigrams, phrases) in lexicons.items():
        n_directional = 0
        n_disclosure_present = 0
        for _, row in df.iterrows():
            body = row["body_clean"]
            quoted = row["quoted_text"]
            narration = row["narration_text"]
            has_nudge_in_quote = has_lexicon_hit(
                quoted, NUDGE_TERMS_UNIGRAM, NUDGE_TERMS_PHRASE
            )
            has_disc_in_narration = has_lexicon_hit(narration, unigrams, phrases)
            if has_disc_in_narration:
                n_disclosure_present += 1
            if has_disc_in_narration and has_nudge_in_quote:
                n_directional += 1
        p_dir_given_disc = n_directional / n_disclosure_present if n_disclosure_present else 0
        rows.append({
            "Disclosure_Lexicon": lex_name,
            "N_with_disclosure_in_narration": n_disclosure_present,
            "N_directional_nudge_in_quote": n_directional,
            "P_nudge_quote_given_disclosure_narration": round(p_dir_given_disc, 4),
        })
    return pd.DataFrame(rows).sort_values(
        "P_nudge_quote_given_disclosure_narration", ascending=False
    )


# --------------------------------------------------------------------------
# Interrupted time series
# --------------------------------------------------------------------------

def interrupted_ts(daily_df, cutoff, value_col="Nudge_Rate"):
    """Estimate level shift and slope change at cutoff via OLS."""
    df = daily_df.copy()
    df["t"] = (df["Date"] - df["Date"].min()).dt.days
    df["post"] = (df["Date"] >= cutoff).astype(int)
    df["t_post"] = df["post"] * (df["t"] - (cutoff - df["Date"].min()).days)

    X = np.column_stack([
        np.ones(len(df)),
        df["t"].values,
        df["post"].values,
        df["t_post"].values,
    ])
    y = df[value_col].values
    if len(df) < 5:
        return None
    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except np.linalg.LinAlgError:
        return None
    return {
        "intercept": float(beta[0]),
        "pre_slope": float(beta[1]),
        "level_shift": float(beta[2]),
        "slope_change": float(beta[3]),
    }


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------

RELEVANCE_PREFILTER = re.compile(
    r"\b(claude|sonnet|opus|anthropic|sleep|bed|rest|tired|exhausted|nap|"
    r"tomorrow|tonight|late|night|midnight|break|llm|model|bot|reminder|"
    r"paternal|patroniz|scold|lectur|moraliz|frustrated|stressed|burned|"
    r"goodnight|asleep|2am|3am|4am|am\b|pm\b|hour)\b",
    re.IGNORECASE,
)


def build_post_features(df):
    """Build per-post feature vector. Returns enriched DataFrame.

    Posts that fail the relevance prefilter skip the expensive spaCy passes
    (imperative detection, temporal NER). They still get cheap lexicon and
    regex features, so corpus-level base rates remain accurate.
    """
    rows = []
    quote_rows = []
    imperative_rows = []
    temporal_rows = []

    for idx, row in df.iterrows():
        body = clean_for_features(row["body"])
        relevant = bool(RELEVANCE_PREFILTER.search(body))
        quoted, narration, sources = _extract_quote_spans_v2(body)

        # Record extracted quote spans
        for method, span in sources:
            quote_rows.append({
                "post_idx": idx,
                "createdAt": row["createdAt"],
                "subreddit": row.get("subreddit", ""),
                "method": method,
                "span": span,
            })

        # Nudge presence (in quoted span; falls back to whole body if no quote)
        target_text = quoted if quoted else body
        has_nudge = has_lexicon_hit(target_text, NUDGE_TERMS_UNIGRAM, NUDGE_TERMS_PHRASE)

        # Disclosure counts (in narration; falls back to whole body if no split)
        narr_for_disclosure = narration if narration.strip() else body

        temp_count = count_lexicon_hits(narr_for_disclosure,
                                        TEMPORAL_DISCLOSURE,
                                        TEMPORAL_DISCLOSURE_PHRASE)
        affect_count = count_lexicon_hits(narr_for_disclosure,
                                          AFFECTIVE_DISCLOSURE,
                                          AFFECTIVE_DISCLOSURE_PHRASE)
        session_count = count_lexicon_hits(narr_for_disclosure,
                                           SESSION_DISCLOSURE,
                                           SESSION_DISCLOSURE_PHRASE)
        work_count = count_lexicon_hits(narr_for_disclosure, WORK_CONTEXT, [])

        # First-person and mental-state density
        narr_tokens = re.findall(r"[a-zA-Z']+", narr_for_disclosure.lower())
        n_tok = max(len(narr_tokens), 1)
        fp_count = count_first_person(narr_for_disclosure)
        ms_count = count_mental_state(narr_for_disclosure)

        # NRC scores (on whole body)
        nrc = nrc_scores(body)

        # Imperative detection (on quoted span); skip spaCy on irrelevant posts
        imperatives = detect_imperatives(target_text) if (has_nudge and relevant) else []
        for imp in imperatives:
            imperative_rows.append({
                "post_idx": idx,
                "createdAt": row["createdAt"],
                "imperative": imp,
            })
        n_modals = count_modal_directives(target_text)

        # Temporal expressions; skip spaCy on irrelevant posts
        time_exprs = extract_temporal_expressions(narr_for_disclosure) if relevant else []
        for te in time_exprs:
            temporal_rows.append({
                "post_idx": idx,
                "createdAt": row["createdAt"],
                "expression": te,
            })

        # Structural
        cratio = code_prose_ratio(body)
        transcript = _has_transcript_structure_v2(body)

        rows.append({
            "post_idx": idx,
            "createdAt": row["createdAt"],
            "subreddit": row.get("subreddit", ""),
            "type": row.get("type", ""),
            "body_clean": body,
            "quoted_text": quoted,
            "narration_text": narration,
            "n_quote_spans": len(sources),
            "has_nudge_in_target": int(has_nudge),
            "temporal_disclosure_count": temp_count,
            "affective_disclosure_count": affect_count,
            "session_disclosure_count": session_count,
            "work_context_count": work_count,
            "first_person_count": fp_count,
            "mental_state_count": ms_count,
            "first_person_density": round(fp_count / n_tok * 100, 3),
            "mental_state_density": round(ms_count / n_tok * 100, 3),
            "n_imperative_quotes": len(imperatives),
            "n_modal_directives": n_modals,
            "n_temporal_expressions": len(time_exprs),
            "code_prose_ratio": round(cratio, 4),
            "has_transcript_structure": int(transcript),
            "post_length_tokens": n_tok,
            **{f"nrc_{c}": nrc[c] for c in NRC_CATEGORIES},
        })

    return (
        pd.DataFrame(rows),
        pd.DataFrame(quote_rows),
        pd.DataFrame(imperative_rows),
        pd.DataFrame(temporal_rows),
    )


def write_lexicons():
    payload = {
        "nudge_unigrams": sorted(NUDGE_TERMS_UNIGRAM),
        "nudge_phrases": NUDGE_TERMS_PHRASE,
        "temporal_disclosure": sorted(TEMPORAL_DISCLOSURE),
        "temporal_disclosure_phrases": TEMPORAL_DISCLOSURE_PHRASE,
        "affective_disclosure": sorted(AFFECTIVE_DISCLOSURE),
        "affective_disclosure_phrases": AFFECTIVE_DISCLOSURE_PHRASE,
        "session_disclosure": sorted(SESSION_DISCLOSURE),
        "session_disclosure_phrases": SESSION_DISCLOSURE_PHRASE,
        "work_context": sorted(WORK_CONTEXT),
        "mental_state_verbs": sorted(MENTAL_STATE_VERBS),
        "first_person": sorted(FIRST_PERSON),
        "modal_directive_patterns": MODAL_DIRECTIVES,
        "imperative_starters": sorted(IMPERATIVE_STARTERS),
        "topic_stopwords": sorted(TOPIC_STOPWORDS),
        "disclosure_stopwords": sorted(DISCLOSURE_STOPWORDS),
    }
    with open(os.path.join(OUTPUT_DIR, "disclosure_lexicons.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_ngram_outputs(features_df):
    """4-grams, 5-grams, and skip-grams. Both stopword regimes."""
    topic_sw = SPACY_STOPWORDS | TOPIC_STOPWORDS
    disc_sw = DISCLOSURE_STOPWORDS

    out_rows = []
    for label, sw in [("topic", topic_sw), ("disclosure", disc_sw)]:
        all_4 = Counter()
        all_5 = Counter()
        all_sk = Counter()
        for txt in features_df["narration_text"].fillna(""):
            tokens = tokenize_for_ngrams(txt, sw)
            all_4.update(generate_ngrams(tokens, 4))
            all_5.update(generate_ngrams(tokens, 5))
            all_sk.update(generate_skipgrams(tokens, (1, 2)))

        for term, count in all_4.most_common(50):
            out_rows.append({"Stopword_Regime": label, "Type": "4-gram", "Term": term, "Count": count})
        for term, count in all_5.most_common(50):
            out_rows.append({"Stopword_Regime": label, "Type": "5-gram", "Term": term, "Count": count})
        for term, count in all_sk.most_common(50):
            out_rows.append({"Stopword_Regime": label, "Type": "skip-gram", "Term": term, "Count": count})

    pd.DataFrame(out_rows).to_csv(
        os.path.join(OUTPUT_DIR, "ngrams_4_5_top.csv"), index=False
    )

    # Also do quoted-span specific n-grams (nudge templates)
    quoted_rows = []
    quoted_4 = Counter()
    quoted_5 = Counter()
    quoted_sk = Counter()
    for txt in features_df["quoted_text"].fillna(""):
        tokens = tokenize_for_ngrams(txt, disc_sw)
        quoted_4.update(generate_ngrams(tokens, 4))
        quoted_5.update(generate_ngrams(tokens, 5))
        quoted_sk.update(generate_skipgrams(tokens, (1, 2)))

    for term, count in quoted_4.most_common(40):
        quoted_rows.append({"Source": "quoted_spans", "Type": "4-gram", "Term": term, "Count": count})
    for term, count in quoted_5.most_common(40):
        quoted_rows.append({"Source": "quoted_spans", "Type": "5-gram", "Term": term, "Count": count})
    for term, count in quoted_sk.most_common(40):
        quoted_rows.append({"Source": "quoted_spans", "Type": "skip-gram", "Term": term, "Count": count})

    pd.DataFrame(quoted_rows).to_csv(
        os.path.join(OUTPUT_DIR, "skipgrams_top.csv"), index=False
    )


def write_nrc_summary(features_df):
    cols = [f"nrc_{c}" for c in NRC_CATEGORIES]
    summary = features_df.groupby(
        features_df["has_nudge_in_target"]
    )[cols].mean().reset_index()
    summary.to_csv(os.path.join(OUTPUT_DIR, "nrc_emotion_scores.csv"), index=False)


def write_feature_clusters(features_df, k=8):
    feature_cols = [
        "temporal_disclosure_count",
        "affective_disclosure_count",
        "session_disclosure_count",
        "work_context_count",
        "first_person_density",
        "mental_state_density",
        "n_imperative_quotes",
        "n_modal_directives",
        "n_temporal_expressions",
        "code_prose_ratio",
        "has_transcript_structure",
    ] + [f"nrc_{c}" for c in NRC_CATEGORIES]

    X = features_df[feature_cols].fillna(0).values
    if len(X) < k + 1:
        return None
    Xs = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(Xs)
    features_df["feature_cluster"] = labels

    # Describe each cluster by centroid magnitudes
    centers = km.cluster_centers_
    cluster_summary = []
    for i in range(k):
        # Top 5 features by absolute centroid score
        sorted_idx = np.argsort(-np.abs(centers[i]))[:6]
        top_feats = [(feature_cols[j], round(float(centers[i][j]), 3))
                     for j in sorted_idx]
        members = features_df[features_df["feature_cluster"] == i]
        rep = ""
        if len(members):
            # Highest disclosure+nudge member as representative
            score = (members["temporal_disclosure_count"]
                     + members["affective_disclosure_count"]
                     + members["session_disclosure_count"]
                     + 3 * members["has_nudge_in_target"])
            rep_idx = score.idxmax()
            rep = features_df.loc[rep_idx, "body_clean"][:240]
        cluster_summary.append({
            "feature_cluster": i,
            "size": int((labels == i).sum()),
            "n_with_nudge": int(members["has_nudge_in_target"].sum()),
            "p_nudge": round(members["has_nudge_in_target"].mean(), 3) if len(members) else 0,
            "top_features": "; ".join(f"{n}({v})" for n, v in top_feats),
            "representative_excerpt": rep,
        })
    pd.DataFrame(cluster_summary).to_csv(
        os.path.join(OUTPUT_DIR, "feature_clusters.csv"), index=False
    )
    return cluster_summary


def write_weekly_pmi(features_df, lexicons):
    """Weekly-stratified PMI for the temporal-shift analysis."""
    fdf = features_df.copy()
    fdf["week"] = fdf["createdAt"].dt.to_period("W").apply(lambda x: x.start_time)
    out_rows = []
    for week, group in fdf.groupby("week"):
        if len(group) < 10:
            continue
        n = len(group)
        n_nudge = int(group["has_nudge_in_target"].sum())
        for lex_name, (uni, phr) in lexicons.items():
            has = group["narration_text"].apply(
                lambda t: has_lexicon_hit(t, uni, phr)
            ).astype(int)
            n_lex = int(has.sum())
            n_both = int(((group["has_nudge_in_target"] == 1) & (has == 1)).sum())
            if n == 0 or n_lex == 0 or n_nudge == 0 or n_both == 0:
                pmi = 0.0
            else:
                p_both = n_both / n
                p_lex = n_lex / n
                p_nudge = n_nudge / n
                pmi = math.log2(p_both / (p_lex * p_nudge))
            out_rows.append({
                "week": week,
                "lexicon": lex_name,
                "n": n,
                "n_nudge": n_nudge,
                "n_lex": n_lex,
                "n_both": n_both,
                "pmi": round(pmi, 4),
            })
    pd.DataFrame(out_rows).to_csv(
        os.path.join(OUTPUT_DIR, "pmi_weekly_timeseries.csv"), index=False
    )


def write_its(features_df):
    daily = features_df.copy()
    daily["Date"] = daily["createdAt"].dt.normalize()
    agg = daily.groupby("Date").agg(
        N=("has_nudge_in_target", "count"),
        Nudges=("has_nudge_in_target", "sum"),
        AffectiveMean=("affective_disclosure_count", "mean"),
        TemporalMean=("temporal_disclosure_count", "mean"),
        FirstPersonMean=("first_person_density", "mean"),
    ).reset_index()
    agg["Nudge_Rate"] = agg["Nudges"] / agg["N"].replace(0, 1)

    results = []
    for col in ["Nudge_Rate", "AffectiveMean", "TemporalMean", "FirstPersonMean"]:
        est = interrupted_ts(agg, OPUS_CUTOFF, value_col=col)
        if est is None:
            continue
        results.append({"series": col, "cutoff": OPUS_CUTOFF.date(), **est})
    pd.DataFrame(results).to_csv(
        os.path.join(OUTPUT_DIR, "its_results.csv"), index=False
    )
    # Also drop the daily aggregate for downstream plotting
    agg.to_csv(os.path.join(OUTPUT_DIR, "daily_aggregates.csv"), index=False)


def write_report(features_df, pmi_df, pmi_dir_df, cluster_summary, its_summary_path):
    lines = []
    lines.append("Discourse Features Analysis Report")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append(f"N posts analyzed: {len(features_df)}")
    lines.append(f"Posts with detected Claude nudge in target span: "
                 f"{int(features_df['has_nudge_in_target'].sum())} "
                 f"({features_df['has_nudge_in_target'].mean():.1%})")
    lines.append(f"Posts with extracted quote spans: "
                 f"{int((features_df['n_quote_spans'] > 0).sum())}")
    lines.append(f"Posts with transcript structure: "
                 f"{int(features_df['has_transcript_structure'].sum())}")
    lines.append("")
    lines.append("--- Means by nudge presence ---")
    nudge_grouped = features_df.groupby("has_nudge_in_target")[[
        "temporal_disclosure_count",
        "affective_disclosure_count",
        "session_disclosure_count",
        "work_context_count",
        "first_person_density",
        "mental_state_density",
        "n_temporal_expressions",
        "code_prose_ratio",
        "has_transcript_structure",
    ]].mean()
    lines.append(nudge_grouped.to_string())
    lines.append("")
    lines.append("--- PMI / association between disclosure lexicons and Claude nudge ---")
    lines.append(pmi_df.to_string(index=False))
    lines.append("")
    lines.append("--- Directional: disclosure in user narration -> nudge in quoted span ---")
    lines.append(pmi_dir_df.to_string(index=False))
    lines.append("")
    lines.append("--- Feature-space cluster summary ---")
    if cluster_summary:
        for c in cluster_summary:
            lines.append(
                f"Cluster {c['feature_cluster']} (n={c['size']}, "
                f"p_nudge={c['p_nudge']}): {c['top_features']}"
            )
            lines.append(f"  Example: {c['representative_excerpt']}")
            lines.append("")
    lines.append("")
    lines.append(f"Interrupted time series results saved to {its_summary_path}")
    lines.append(f"Opus cutoff used: {OPUS_CUTOFF.date()}")
    lines.append(f"Fortune publication date: {FORTUNE_DATE.date()} "
                 f"(treat as media-induced spike)")
    lines.append("")
    lines.append("=== Interpretation guide ===")
    lines.append(
        "Largest PMI / P(nudge|lexicon) tells you which user-disclosed context "
        "most strongly predicts a Claude sleep-nudge.\n"
        "  - If 'affective' wins: model is mirroring user-disclosed state "
        "(mirroring hypothesis).\n"
        "  - If 'temporal' wins: model is anchoring on time references "
        "(time-anchoring hypothesis).\n"
        "  - If 'session' wins: model is responding to length cues "
        "(LCR Zombie hypothesis).\n"
        "  - If 'work_context' wins: model is mis-categorizing technical work as fatigue.\n"
        "Directional table tells you whether the disclosure precedes the nudge "
        "in the visible exchange (stronger evidence than co-occurrence alone)."
    )
    with open(os.path.join(OUTPUT_DIR, "discourse_features_report.txt"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    global OUTPUT_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None, help="Path to CSV input")
    parser.add_argument("--output-subdir", default=None,
                        help="Subdir under deliverables/ for outputs")
    args = parser.parse_args()

    if args.output_subdir:
        OUTPUT_DIR = os.path.join("deliverables", args.output_subdir)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Loading data...")
    df, used_path = load_data(args.input)
    if df.empty:
        print("No data found. Run reddit_scraper_v2.py first.")
        return
    print(f"Loaded {len(df)} rows from {used_path}")
    print(f"Output dir: {OUTPUT_DIR}")

    print("Writing lexicons...")
    write_lexicons()

    print("Building per-post features (this is the slow step)...")
    features_df, quote_df, imp_df, temp_df = build_post_features(df)

    print(f"  {len(features_df)} posts processed")
    print(f"  {len(quote_df)} candidate Claude utterances extracted")
    print(f"  {int(features_df['has_nudge_in_target'].sum())} posts with detected nudge")

    features_df.to_csv(os.path.join(OUTPUT_DIR, "discourse_features.csv"), index=False)
    quote_df.to_csv(os.path.join(OUTPUT_DIR, "quote_spans.csv"), index=False)
    imp_df.to_csv(os.path.join(OUTPUT_DIR, "imperative_quotes.csv"), index=False)
    temp_df.to_csv(os.path.join(OUTPUT_DIR, "temporal_expressions.csv"), index=False)

    print("Writing n-grams (4, 5, skip)...")
    write_ngram_outputs(features_df)

    print("Writing NRC emotion summary...")
    write_nrc_summary(features_df)
    if not HAS_NRCLEX:
        print("  (using fallback NRC lexicon; install `nrclex` for full coverage)")

    print("Computing PMI between disclosure lexicons and Claude nudge...")
    lexicons = {
        "temporal": (TEMPORAL_DISCLOSURE, TEMPORAL_DISCLOSURE_PHRASE),
        "affective": (AFFECTIVE_DISCLOSURE, AFFECTIVE_DISCLOSURE_PHRASE),
        "session": (SESSION_DISCLOSURE, SESSION_DISCLOSURE_PHRASE),
        "work_context": (WORK_CONTEXT, []),
    }
    pmi_df = compute_pmi_table(
        features_df, lexicons,
        nudge_check_col="has_nudge_in_target",
        window_col="narration_text",
    )
    pmi_df.to_csv(os.path.join(OUTPUT_DIR, "pmi_disclosure_nudge.csv"), index=False)

    print("Computing directional PMI (disclosure precedes nudge)...")
    pmi_dir_df = compute_pmi_directional(features_df, lexicons)
    pmi_dir_df.to_csv(
        os.path.join(OUTPUT_DIR, "pmi_disclosure_nudge_directional.csv"),
        index=False,
    )

    print("Computing weekly-stratified PMI...")
    write_weekly_pmi(features_df, lexicons)

    print("Computing interrupted time series at Opus 4.7 cutoff...")
    write_its(features_df)

    print("Re-clustering on feature space...")
    cluster_summary = write_feature_clusters(features_df, k=8)

    print("Writing summary report...")
    its_path = os.path.join(OUTPUT_DIR, "its_results.csv")
    write_report(features_df, pmi_df, pmi_dir_df, cluster_summary, its_path)

    print("Done.")
    print(f"Outputs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
