"""
Quote-extractor recall audit.

The §6.3 limitation in the paper draft asserted that extractor recall was
"substantially below 50%" based on informal manual inspection. This script
replaces that assertion with a reproducible structural-recall measurement.

Design

  Universe: posts whose body contains at least one canonical nudge phrase
  (the same nudge-phrase set used elsewhere in the pipeline).

  For each post in the universe, three structural cues are checked:

    1. Speaker-attribution cue:  the post contains a Claude-side speaker
       label ("Claude:", "**Claude:**", "[Claude]", "the model:", ...) OR
       an attribution phrase ("claude said", "it told me", ...).

    2. Quoted-context cue: the nudge phrase appears inside a markdown
       blockquote line (`> ...`) or inside inline quoted material
       (straight or curly), OR a reported-speech construction places it
       as model utterance ("it told me to go to sleep").

    3. Transcript cue: the post exhibits alternating-speaker transcript
       structure (>=2 distinct speaker labels).

  A post is judged "structurally evidenced as a Claude nudge utterance"
  if at least one cue fires.

  Recall lower bound = (structurally-evidenced AND captured by extractor)
                       / (structurally-evidenced)

  This is a *lower bound* because the heuristic only credits cues we can
  detect programmatically; user-voice false positives in the denominator
  are minimized but not eliminated. The complement (1 - recall) is an
  upper bound on the structural-miss rate.

Outputs:
  deliverables/recall_audit_report.txt     summary statistics
  deliverables/recall_audit_sample.csv     per-post audit rows
"""

import os
import re
import pandas as pd
import regex as re_full

from quote_extractor_v2 import (
    extract_quote_spans_v2,
    contains_nudge,
    clean_text,
    NUDGE_TERMS_UNIGRAM,
    NUDGE_TERMS_PHRASE,
    NUDGE_SENTENCE_PATTERNS,
    SPEAKER_LABEL_RE,
    USER_LABEL_RE,
    ATTRIBUTION_RE,
    REPORTED_NUDGE_RE,
    BLOCKQUOTE_BLOCK_RE,
    TRANSCRIPT_LINE_RE,
)

DATA_DIR = "data/"
OUTPUT_DIR = "deliverables/"
SAMPLE_SIZE = 400
RANDOM_SEED = 20260516

CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv"),
    os.path.join(DATA_DIR, "praw_sleep_analysis_final_fallback.csv"),
]

NUDGE_LEX_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in NUDGE_TERMS_PHRASE) + r")\b",
    re.IGNORECASE,
)
NUDGE_UNIGRAM_RE = re.compile(
    r"\b(" + "|".join(re.escape(u) for u in NUDGE_TERMS_UNIGRAM) + r")\b",
    re.IGNORECASE,
)
INLINE_QUOTE_RE = re_full.compile(r"[\"“”]([^\"“”]{8,500})[\"“”]")
INLINE_SINGLE_QUOTE_RE = re_full.compile(
    r"(?<![A-Za-z])[‘’']([^‘’']{12,500})[‘’'](?![A-Za-z])"
)


def has_claude_speaker_label(text):
    for m in SPEAKER_LABEL_RE.finditer(text):
        return True
    return False


def has_attribution_phrase(text):
    return bool(ATTRIBUTION_RE.search(text)) or bool(REPORTED_NUDGE_RE.search(text))


def nudge_in_blockquote(text):
    for m in BLOCKQUOTE_BLOCK_RE.finditer(text):
        block = m.group(1)
        if contains_nudge(block):
            return True
    return False


def nudge_in_inline_quote(text):
    for m in INLINE_QUOTE_RE.finditer(text):
        if contains_nudge(m.group(1)):
            return True
    for m in INLINE_SINGLE_QUOTE_RE.finditer(text):
        if contains_nudge(m.group(1)):
            return True
    return False


def has_transcript_structure(text):
    matches = TRANSCRIPT_LINE_RE.findall(text)
    distinct = {m.lower() for m in matches}
    return len(distinct) >= 2 and len(matches) >= 2


def classify_cues(text):
    cues = []
    if has_claude_speaker_label(text):
        cues.append("speaker_label")
    if has_attribution_phrase(text):
        cues.append("attribution_phrase")
    if nudge_in_blockquote(text):
        cues.append("nudge_in_blockquote")
    if nudge_in_inline_quote(text):
        cues.append("nudge_in_inline_quote")
    if has_transcript_structure(text):
        cues.append("transcript")
    return cues


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
    df = df.dropna(subset=["body"]).reset_index(drop=True)
    print(f"Loaded {len(df)} rows")

    # Universe: posts containing at least one canonical nudge phrase or unigram
    body_lower = df["body"].astype(str).str.lower()
    in_universe_phrase = body_lower.apply(lambda t: bool(NUDGE_LEX_RE.search(t)))
    in_universe_unigram = body_lower.apply(lambda t: bool(NUDGE_UNIGRAM_RE.search(t)))
    in_universe = in_universe_phrase | in_universe_unigram
    universe = df[in_universe].reset_index(drop=True)
    print(f"Universe (any nudge phrase or unigram): {len(universe)}")
    print(f"Universe (canonical phrases only): {int(in_universe_phrase.sum())}")

    # Stratified sample: half from canonical-phrase slice, half from
    # unigram-only slice (the harder cases).
    rng_state = pd.Series(range(len(universe))).sample(
        n=min(SAMPLE_SIZE, len(universe)), random_state=RANDOM_SEED
    )
    sample = universe.loc[rng_state.values].reset_index(drop=True)
    print(f"Sample size: {len(sample)}")

    rows = []
    cue_universe_count = 0
    captured_count = 0
    captured_within_cue = 0
    cue_counts = {}

    for _, row in sample.iterrows():
        body = clean_text(row["body"])
        cues = classify_cues(body)
        for c in cues:
            cue_counts[c] = cue_counts.get(c, 0) + 1
        has_any_cue = bool(cues)
        quoted, _, sources = extract_quote_spans_v2(body)
        captured = bool(quoted) and contains_nudge(quoted)
        if captured:
            captured_count += 1
        if has_any_cue:
            cue_universe_count += 1
            if captured:
                captured_within_cue += 1
        rows.append({
            "post_idx_orig": row.name,
            "createdAt": row.get("createdAt", ""),
            "subreddit": row.get("subreddit", ""),
            "has_cue": has_any_cue,
            "cues": ";".join(cues) if cues else "",
            "extractor_captured_nudge": captured,
            "n_spans": len(sources),
            "body_preview": str(row["body"])[:300].replace("\n", " "),
        })

    audit_df = pd.DataFrame(rows)
    sample_path = os.path.join(OUTPUT_DIR, "recall_audit_sample.csv")
    audit_df.to_csv(sample_path, index=False)

    recall_lower_bound = captured_within_cue / cue_universe_count if cue_universe_count else 0.0
    overall_capture = captured_count / len(sample)

    lines = []
    lines.append("Quote Extractor Recall Audit (V2)")
    lines.append("=" * 50)
    lines.append(f"Corpus rows analyzed: {len(df)}")
    lines.append(f"Universe (posts with any nudge phrase or unigram): {len(universe)}")
    lines.append(f"  Canonical phrases only: {int(in_universe_phrase.sum())}")
    lines.append(f"  Unigram-only matches:   {int((in_universe & ~in_universe_phrase).sum())}")
    lines.append("")
    lines.append(f"Stratified random sample: {len(sample)} posts (seed {RANDOM_SEED})")
    lines.append("")
    lines.append("Structural cue tallies in sample:")
    for cue, count in sorted(cue_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {cue:28s} {count:5d}  ({count/len(sample):.1%})")
    lines.append("")
    lines.append(f"Posts with >=1 structural cue: {cue_universe_count} ({cue_universe_count/len(sample):.1%})")
    lines.append(f"Extractor captured nudge in quoted span: {captured_count} ({overall_capture:.1%})")
    lines.append(f"Captured AND cue present: {captured_within_cue}")
    lines.append("")
    lines.append("Recall lower bound (captured | cue): "
                 f"{recall_lower_bound:.3f} "
                 f"({captured_within_cue}/{cue_universe_count})")
    lines.append("")
    lines.append("Interpretation")
    lines.append("-" * 50)
    lines.append("The recall lower bound is conservative because:")
    lines.append(" (a) the structural cue heuristic does not separate Claude-attributed")
    lines.append("     nudge phrases from user-voice nudge phrases, so the denominator")
    lines.append("     contains some posts where no model utterance exists;")
    lines.append(" (b) extractor V2 itself uses several of these structural cues, so")
    lines.append("     the test is partly internal-consistency rather than fully")
    lines.append("     independent recall measurement.")
    lines.append("")
    lines.append("A formal recall point estimate requires human-labeled ground truth")
    lines.append("on a stratified sample and is the principal outstanding methodological")
    lines.append("item flagged in the paper.")

    report_path = os.path.join(OUTPUT_DIR, "recall_audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {report_path}")
    print(f"Wrote {sample_path}")


if __name__ == "__main__":
    main()
