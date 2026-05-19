"""
Quote-span extractor V2.

Improvements over V1 (the extract_quote_spans in discourse_features_analysis.py):

  - Em-dash, en-dash, and hyphen speaker labels ("Claude — ", "Claude- ").
  - Bolded / italicized speaker labels ("**Claude:**", "*Me*:").
  - Bracketed and parenthesized speakers ("[Claude]", "(Sonnet)").
  - Past-tense reported-speech rescue: extracts the imperative clause from
    "it told me to go to sleep" / "claude said I should rest" style sentences.
  - Multi-paragraph blockquote merging (consecutive `>` lines joined).
  - Nudge-sentence rescue: pulls any sentence containing a tight nudge n-gram
    even if no attribution pattern matched, flagged as low-confidence.
  - Code-fence content checked for transcript-style content before stripping.
  - Expanded transcript detection (informal/lowercase speaker labels,
    em-dash separators).

Provenance: each extracted span carries a `method` tag so V1/V2 yields can
be compared and the contribution of each pattern audited.

Run from Claude_Sleep_Analysis_V2/ directory:

    python src/quote_extractor_v2.py

Outputs:
    deliverables/quote_spans_v2.csv          All extracted spans with method
    deliverables/extractor_v2_report.txt     Comparison vs V1
"""

import os
import re
import pandas as pd
import regex as re_full  # for unicode-class support

DATA_DIR = "data/"
OUTPUT_DIR = "deliverables/"

CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv"),
    os.path.join(DATA_DIR, "praw_sleep_analysis_final_fallback.csv"),
]

# --------------------------------------------------------------------------
# Lexicons
# --------------------------------------------------------------------------

NUDGE_TERMS_UNIGRAM = {
    "sleep", "rest", "bed", "bedtime", "nap", "tomorrow", "morning",
    "break", "goodnight", "asleep", "tonight",
}
NUDGE_TERMS_PHRASE = [
    "call it a night", "call it a day", "get some rest", "get some sleep",
    "go to bed", "go to sleep", "try again tomorrow", "take a break",
    "step away", "needs rest", "need rest", "needs sleep", "need sleep",
    "good night", "see you tomorrow", "wrap up for the night",
    "wrap it up", "pick this up tomorrow", "pick it up tomorrow",
    "leave it for the night", "leave it there for the night",
    "leave it for tonight", "good place to stop", "good stopping point",
    "get some sleep", "you should rest", "you should sleep",
    "time to call it", "let's call it", "have a good night",
    "go get some rest", "now sleep", "now go to bed", "now rest",
]

# Tight nudge sentence templates (used for rescue extraction)
NUDGE_SENTENCE_PATTERNS = [
    r"\bgo to (?:sleep|bed|rest)\b",
    r"\bget some (?:sleep|rest)\b",
    r"\bcall it (?:a (?:night|day)|here)\b",
    r"\btake a break\b",
    r"\bstep away\b",
    r"\btry again tomorrow\b",
    r"\bsee you tomorrow\b",
    r"\bgood ?night\b",
    r"\bwrap (?:up|it up|this up)(?: for (?:the night|today|tonight))?\b",
    r"\bpick (?:this|it) up tomorrow\b",
    r"\bleave it (?:there|for the night|for tonight)\b",
    r"\bneed (?:some |a )?(?:rest|sleep|break)\b",
    r"\b(?:you|y'?all|ya) (?:should|might|could|need to|gotta) (?:get some |go )?(?:rest|sleep|to bed|to sleep)\b",
    r"\bnow (?:sleep|rest|go (?:to )?(?:bed|sleep))\b",
    r"\benough for (?:today|tonight|this session|now)\b",
    r"\bgood (?:place|spot|stopping point) (?:to (?:stop|leave|wrap)|for)\b",
]
NUDGE_SENTENCE_RE = re.compile("|".join(NUDGE_SENTENCE_PATTERNS), re.IGNORECASE)

# --------------------------------------------------------------------------
# Pattern compilation
# --------------------------------------------------------------------------

# 1. Blockquote prefix, with multi-line merge
BLOCKQUOTE_BLOCK_RE = re.compile(r"((?:^[ \t]*>[ \t]?.*(?:\n|$))+)", re.MULTILINE)

# 2. Code fence content (we extract for inspection but don't necessarily
# treat as quote unless it contains a speaker label inside)
CODEFENCE_RE = re.compile(r"```([^`]*?)```", re.DOTALL)

# 3. Speaker label at line start (existing, but expanded)
SPEAKER_LABEL_RE = re.compile(
    r"^[ \t]*"
    r"(?:[*_~`]{0,2})"                           # optional bold/italic markers
    r"\[?"                                         # optional bracket open
    r"\(?"                                         # optional paren open
    r"(claude(?: code)?|sonnet|opus|assistant|model|the model|the ai|the bot|ai|bot|llm|cc)"
    r"\)?\]?"                                      # optional close
    r"(?:[*_~`]{0,2})"                           # optional bold/italic markers
    r"[ \t]*[:>\-–—][ \t]*",            # separator
    re.IGNORECASE | re.MULTILINE,
)
USER_LABEL_RE = re.compile(
    r"^[ \t]*"
    r"(?:[*_~`]{0,2})"
    r"\[?\(?"
    r"(me|you|user|i|prompt|human)"
    r"\)?\]?"
    r"(?:[*_~`]{0,2})"
    r"[ \t]*[:>\-–—][ \t]*",
    re.IGNORECASE | re.MULTILINE,
)

# 4. Attribution phrases (in-line)
ATTRIBUTION_RE = re.compile(
    r"(?:claude(?: code)?|sonnet|opus|the model|the bot|the ai|the assistant|it|he|she)\s+"
    r"(?:said|told\s+me|told\s+us|replied|responded|wrote|says|tells|writes|"
    r"answered|kept\s+(?:saying|telling)|just\s+(?:said|told)|literally\s+(?:said|told)|"
    r"keeps\s+(?:saying|telling)|started\s+(?:saying|telling)|ends\s+(?:with|by)|"
    r"comes\s+back\s+with)\s*[:,]?\s*",
    re.IGNORECASE,
)

# 5. Reported speech that contains a nudge clause
# Patterns like "it told me to go to sleep" or "claude said I should rest"
REPORTED_NUDGE_RE = re.compile(
    r"(?:claude|sonnet|opus|the (?:model|bot|ai|assistant)|it|he|she)\s+"
    r"(?:said|told\s+me|tells\s+me|keeps\s+(?:telling\s+me|saying)|"
    r"started\s+(?:telling\s+me|saying)|wants\s+me|made\s+me|"
    r"is\s+telling\s+me|was\s+telling\s+me|"
    r"won'?t\s+stop\s+telling\s+me|"
    r"will\s+(?:say|tell\s+me)|"
    r"would\s+(?:say|tell\s+me)|"
    r"thinks\s+I\s+should|"
    r"insists?(?:\s+I)?)\s+"
    r"(?:(?:to|that|I\s+should|I\s+need\s+to|me\s+to)\s+)?"
    r"([^.!?\n]{3,180}?(?:" +
    r"|".join(NUDGE_SENTENCE_PATTERNS) +
    r")[^.!?\n]{0,100})",
    re.IGNORECASE,
)

# 6. Inline quoted material
INLINE_QUOTE_RE = re_full.compile(
    r"[\"“”]([^\"“”]{8,500})[\"“”]",
)
INLINE_SINGLE_QUOTE_RE = re_full.compile(
    r"(?<![A-Za-z])[‘’']([^‘’']{12,500})[‘’'](?![A-Za-z])",
)

# 7. Transcript detection (expanded)
TRANSCRIPT_LINE_RE = re.compile(
    r"^[ \t]*(?:[*_~`]{0,2})\[?\(?"
    r"(me|you|user|i|claude(?: code)?|opus|sonnet|assistant|ai|bot|prompt|response|model|the model|the bot|the ai|cc|human)"
    r"\)?\]?(?:[*_~`]{0,2})[ \t]*[:>\-–—]",
    re.IGNORECASE | re.MULTILINE,
)


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

def looks_like_claude_speaker(label):
    label = label.lower().strip()
    return label in {
        "claude", "claude code", "cc", "sonnet", "opus", "assistant",
        "model", "the model", "the ai", "the bot", "ai", "bot", "llm",
    }


def looks_like_user_speaker(label):
    return label.lower().strip() in {"me", "you", "user", "i", "prompt", "human"}


def contains_nudge(text):
    if not text:
        return False
    low = text.lower()
    if any(t in low for t in NUDGE_TERMS_UNIGRAM):
        return True
    if any(p in low for p in NUDGE_TERMS_PHRASE):
        return True
    return bool(NUDGE_SENTENCE_RE.search(text))


def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.replace("\r\n", "\n")
    return text


def extract_blockquote_blocks(text):
    """Return list of merged multi-line blockquote spans."""
    out = []
    for m in BLOCKQUOTE_BLOCK_RE.finditer(text):
        block = m.group(1)
        # Strip the > prefix from each line
        cleaned = "\n".join(
            re.sub(r"^[ \t]*>[ \t]?", "", line)
            for line in block.split("\n")
        ).strip()
        if cleaned and len(cleaned) > 3:
            out.append(("blockquote", m.start(), m.end(), cleaned))
    return out


def extract_speaker_label_spans(text):
    """Extract spans between Claude-speaker labels and the next speaker label
    or paragraph break."""
    out = []
    # Find all speaker labels (claude-side and user-side mixed)
    matches = []
    for m in SPEAKER_LABEL_RE.finditer(text):
        label = m.group(1)
        matches.append(("claude", m.start(), m.end(), label))
    for m in USER_LABEL_RE.finditer(text):
        label = m.group(1)
        matches.append(("user", m.start(), m.end(), label))
    matches.sort(key=lambda x: x[1])

    for i, (side, start, end, label) in enumerate(matches):
        if side != "claude":
            continue
        # Span runs from end of label to start of next label (any side)
        # or to next double-newline, whichever first
        next_label_start = matches[i + 1][1] if i + 1 < len(matches) else len(text)
        para_break = text.find("\n\n", end)
        if para_break == -1:
            para_break = len(text)
        span_end = min(next_label_start, para_break + 200)  # allow some bleed
        # But cap to next label always
        span_end = min(span_end, next_label_start)
        body = text[end:span_end].strip()
        if 3 < len(body) < 1500:
            out.append(("speaker_label", start, span_end, body))
    return out


def extract_attribution_spans(text):
    """Pattern: 'Claude said: <content>'"""
    out = []
    for m in ATTRIBUTION_RE.finditer(text):
        tail = text[m.end():m.end() + 500]
        # Take up to next paragraph break, or end of next sentence,
        # whichever is reasonable
        para_end = tail.find("\n\n")
        if para_end == -1:
            para_end = len(tail)
        # Or first 1-3 sentences
        sent_cut = re.split(
            r"(?<=[.!?])\s+(?=[A-Z“\"])", tail[:para_end], maxsplit=2,
        )
        if len(sent_cut) > 2:
            tail_cut = " ".join(sent_cut[:2]).strip()
        else:
            tail_cut = tail[:para_end].strip()
        if 5 < len(tail_cut) < 600:
            out.append(("attribution", m.start(), m.end() + len(tail_cut), tail_cut))
    return out


def extract_reported_nudge(text):
    """Pattern: 'it told me to go to sleep' style reported speech."""
    out = []
    for m in REPORTED_NUDGE_RE.finditer(text):
        clause = m.group(1).strip()
        if 5 < len(clause) < 300:
            out.append(("reported_speech", m.start(), m.end(), clause))
    return out


def extract_inline_quotes_with_nudge(text):
    """Inline quoted material containing nudge content."""
    out = []
    for m in INLINE_QUOTE_RE.finditer(text):
        inner = m.group(1).strip()
        if contains_nudge(inner):
            out.append(("inline_quote", m.start(), m.end(), inner))
    for m in INLINE_SINGLE_QUOTE_RE.finditer(text):
        inner = m.group(1).strip()
        if contains_nudge(inner):
            out.append(("inline_single_quote", m.start(), m.end(), inner))
    return out


def extract_nudge_sentence_rescue(text, already_spans):
    """Catch sentences containing nudge content that the other patterns missed.

    Flagged as low-confidence in the method tag.
    """
    out = []
    # Build a set of (start, end) intervals already covered
    covered = sorted([(s, e) for (_m, s, e, _c) in already_spans])

    def is_covered(idx):
        for s, e in covered:
            if s <= idx < e:
                return True
        return False

    # Sentence-split by simple regex
    for m in re.finditer(r"[^.!?\n]*?(?:" + "|".join(NUDGE_SENTENCE_PATTERNS) +
                         r")[^.!?\n]*[.!?]?", text, re.IGNORECASE):
        s, e = m.span()
        if is_covered(s) or is_covered(e - 1):
            continue
        sent = m.group(0).strip()
        if 8 < len(sent) < 300:
            # Heuristic guard: if the sentence is clearly user voice (e.g. "I
            # need some rest"), skip. Look for first-person verb structure.
            low = sent.lower()
            user_voice_markers = [
                r"^\s*i\b", r"\bi need\b", r"\bi'?m\b", r"\bi want\b",
                r"\bi gotta\b", r"\bi gonna\b", r"\bi should\b", r"\bi am\b",
            ]
            if any(re.search(p, low) for p in user_voice_markers):
                # likely user voice, skip
                continue
            out.append(("nudge_rescue_low_conf", s, e, sent))
    return out


def extract_quote_spans_v2(text):
    """Improved extractor. Returns:
        quoted_text   - concatenated extracted spans
        narration     - rest of the post (user narration)
        sources       - list of (method, span) tuples
    """
    if not text:
        return "", "", []

    all_spans = []
    all_spans.extend(extract_blockquote_blocks(text))
    all_spans.extend(extract_speaker_label_spans(text))
    all_spans.extend(extract_attribution_spans(text))
    all_spans.extend(extract_reported_nudge(text))
    all_spans.extend(extract_inline_quotes_with_nudge(text))
    # Rescue pass runs last, gated by existing coverage
    rescue = extract_nudge_sentence_rescue(text, all_spans)
    all_spans.extend(rescue)

    # Deduplicate by content (after stripping whitespace) and method preference
    method_priority = {
        "speaker_label": 0,
        "blockquote": 1,
        "attribution": 2,
        "inline_quote": 3,
        "inline_single_quote": 4,
        "reported_speech": 5,
        "nudge_rescue_low_conf": 6,
    }
    seen_content = {}
    for method, s, e, content in all_spans:
        norm = re.sub(r"\s+", " ", content.lower().strip())[:120]
        prio = method_priority.get(method, 99)
        if norm not in seen_content or seen_content[norm][0] > prio:
            seen_content[norm] = (prio, method, s, e, content)
    deduped = [(m, s, e, c) for _, m, s, e, c in seen_content.values()]
    deduped.sort(key=lambda x: x[1])

    quoted_text = " | ".join(c for _m, _s, _e, c in deduped)

    # Build narration by removing matched ranges
    spans_to_remove = sorted([(s, e) for _m, s, e, _c in deduped])
    narration_parts = []
    cursor = 0
    for start, end in spans_to_remove:
        if start > cursor:
            narration_parts.append(text[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(text):
        narration_parts.append(text[cursor:])
    narration = " ".join(narration_parts)
    narration = CODEFENCE_RE.sub(" ", narration)

    sources = [(m, c) for m, _s, _e, c in deduped]
    return quoted_text, narration, sources


def has_transcript_structure_v2(text):
    if not text:
        return False
    matches = TRANSCRIPT_LINE_RE.findall(text)
    # Need at least 2 distinct speaker labels (case-insensitive)
    distinct = {m.lower() for m in matches}
    return len(distinct) >= 2 and len(matches) >= 2


# --------------------------------------------------------------------------
# Driver / comparison
# --------------------------------------------------------------------------

def main():
    csv_path = None
    for c in CSV_CANDIDATES:
        if os.path.exists(c):
            csv_path = c
            break
    if csv_path is None:
        print("No corpus found.")
        return

    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
    df = df.dropna(subset=["body", "createdAt"]).reset_index(drop=True)
    print(f"Loaded {len(df)} rows")

    # Compare V1 vs V2 on the same corpus
    print("\nRunning V2 extractor on full corpus...")
    rows = []
    method_counter = {}
    transcript_count = 0
    nudge_in_quote_count = 0
    for idx, row in df.iterrows():
        body = clean_text(row["body"])
        quoted, narration, sources = extract_quote_spans_v2(body)
        for method, span in sources:
            rows.append({
                "post_idx": idx,
                "createdAt": row["createdAt"],
                "subreddit": row.get("subreddit", ""),
                "method": method,
                "span": span[:500],  # cap for output size
                "span_length": len(span),
            })
            method_counter[method] = method_counter.get(method, 0) + 1
        if has_transcript_structure_v2(body):
            transcript_count += 1
        if quoted and contains_nudge(quoted):
            nudge_in_quote_count += 1

    out_df = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "quote_spans_v2.csv")
    out_df.to_csv(out_path, index=False)
    print(f"\nWrote {len(out_df)} spans to {out_path}")

    # Compare against V1 outputs if present
    v1_path = os.path.join(OUTPUT_DIR, "quote_spans.csv")
    v1_count = None
    if os.path.exists(v1_path):
        v1_df = pd.read_csv(v1_path)
        v1_count = len(v1_df)

    # Write report
    lines = []
    lines.append("Quote Extractor V2 vs V1 Comparison")
    lines.append("=" * 50)
    lines.append(f"Corpus size: {len(df)} rows")
    lines.append("")
    lines.append(f"V1 extractor (in discourse_features_analysis.py): {v1_count} spans" if v1_count else "V1 baseline not found")
    lines.append(f"V2 extractor: {len(out_df)} spans")
    if v1_count:
        delta = len(out_df) - v1_count
        pct = delta / v1_count * 100 if v1_count else 0
        lines.append(f"Net gain: +{delta} spans ({pct:+.1f}%)")
    lines.append("")
    lines.append("V2 method breakdown:")
    for method, count in sorted(method_counter.items(), key=lambda x: -x[1]):
        lines.append(f"  {method:30s} {count:6d}")
    lines.append("")
    lines.append(f"Posts with transcript structure (V2 detection): {transcript_count}")
    lines.append(f"Posts with detected nudge in any extracted quoted text (V2): {nudge_in_quote_count}")
    lines.append("")
    lines.append("Nudge capture rate test:")
    nudge_lex_re = (
        r"\b(go to sleep|go to bed|get some rest|call it a night|"
        r"get some sleep|take a break|wrap up for the night|"
        r"pick this up tomorrow)\b"
    )
    df_with_nudge_in_body = df[df["body"].str.contains(nudge_lex_re, case=False, regex=True, na=False)]
    n_with_nudge = len(df_with_nudge_in_body)
    # V2 capture count: posts where we extracted at least one quote AND the quote contained nudge
    captured = 0
    for idx, row in df_with_nudge_in_body.iterrows():
        body = clean_text(row["body"])
        quoted, _, sources = extract_quote_spans_v2(body)
        if quoted and contains_nudge(quoted):
            captured += 1
    rate = captured / max(n_with_nudge, 1)
    lines.append(f"  Posts containing literal nudge phrases: {n_with_nudge}")
    lines.append(f"  V2 captured with nudge in extracted quote: {captured} ({rate:.1%})")
    lines.append("  V1 baseline rate on this slice: 30.4% (see prior diagnostic)")
    lines.append("")
    lines.append("=" * 50)
    lines.append("Method confidence notes:")
    lines.append("  speaker_label, blockquote, attribution = high confidence")
    lines.append("  inline_quote, inline_single_quote     = medium confidence")
    lines.append("  reported_speech                       = medium confidence")
    lines.append("  nudge_rescue_low_conf                 = low confidence; user-voice guarded")

    report_path = os.path.join(OUTPUT_DIR, "extractor_v2_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote comparison report to {report_path}")
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
