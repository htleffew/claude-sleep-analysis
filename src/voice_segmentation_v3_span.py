"""
voice_segmentation_v3_span.py
Phase 4 — Voice Segmentation  [method §C.4]
Sleep-nudge Pass 1b canonical corpus

Purpose
-------
Produce SPAN-LEVEL voice annotations for 773 rows of unstructured Reddit
discourse.  For each row the segmenter emits a list of contiguous, non-
overlapping spans covering the full row text, each with a label, confidence,
and source.  This replaces the deprecated row-level v1 and v2 outputs.

Output schema (§9.0 of methods_library.md)
-------------------------------------------
Each span record carries:
    span_start  — character offset (0-based, inclusive)
    span_end    — character offset (0-based, exclusive)
    label       — one of: Direct_Quote_Of_Model, Paraphrase_Of_Model,
                  User_Original_Content, Unclassifiable
    confidence  — high, medium, or low
    source      — regex, llm:gemini-3.1-flash-lite, floor

Spans must cover the entire row text contiguously with no gaps and no
overlaps.  User_Original_Content is the floor default, not an active assertion.

Architecture: three layers
--------------------------
Layer 1 (regex): scan each row for all regex match offsets.  For every match
    emit a span at those offsets.  Patterns are the same set as v2 (DQ, PM,
    and weak patterns) but applied to extract SPAN positions, not a row label.

Layer 2 (LLM fallback): for each unclassified interval between Layer 1 spans,
    invoke Gemini CLI on the interval text.  Budget: 100 calls across all rows.
    Reuses v2 prompt design adapted for span/interval text.  Unicode fix:
    encoding='utf-8', errors='replace'.

Layer 3 (floor): any remaining unclassified character range is assigned
    User_Original_Content / low.

After all three layers, merge adjacent spans sharing the same label.

Resume-safe
-----------
Before processing each row the script checks whether pass1b_canonical_voice_spans.csv
already contains spans for that row_id.  If yes, the row is skipped.  Re-running
from an interrupted state picks up where it left off.

LLM-as-tool log
---------------
Appends to notebooks/llm_tool_log.md.  Per-call JSONL log written to
deliverables/phase_4_voice_segmentation/llm_call_log_v3_span.jsonl.

Design date: 2026-05-18

Usage
-----
    python src/voice_segmentation_v3_span.py

Outputs (all relative to repo root)
-------------------------------------
    data/pass1b_canonical_voice_spans.csv
    notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3_span.csv
    notebooks/audit_trail/phase_4_voice_segmentation_v3_span_summary.md
    deliverables/phase_4_voice_segmentation/llm_call_log_v3_span.jsonl
    notebooks/llm_tool_log.md  (appended)

Files NOT touched
-----------------
    data/pass1b_canonical.csv                           — input, read-only
    data/pass1b_canonical_voice_segmented.csv           — v1 row-level, preserved
    data/pass1b_canonical_voice_segmented_v2.csv        — v2 row-level, preserved
"""

import csv
import json
import re
import random
import datetime
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

INPUT_CSV     = REPO_ROOT / "data" / "pass1b_canonical.csv"
OUTPUT_SPANS  = REPO_ROOT / "data" / "pass1b_canonical_voice_spans.csv"

DELIVERABLES_DIR = REPO_ROOT / "deliverables" / "phase_4_voice_segmentation"
LLM_LOG_V3       = DELIVERABLES_DIR / "llm_call_log_v3_span.jsonl"

AUDIT_DIR         = REPO_ROOT / "notebooks" / "audit_trail"
VALIDATION_SAMPLE = AUDIT_DIR / "phase_4_voice_segmentation_validation_sample_v3_span.csv"
SUMMARY_MD        = AUDIT_DIR / "phase_4_voice_segmentation_v3_span_summary.md"
LLM_TOOL_LOG      = REPO_ROOT / "notebooks" / "llm_tool_log.md"

DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LABEL_DIRECT     = "Direct_Quote_Of_Model"
LABEL_PARAPHRASE = "Paraphrase_Of_Model"
LABEL_USER       = "User_Original_Content"
LABEL_UNCLEAR    = "Unclassifiable"

CONF_HIGH = "high"
CONF_MED  = "medium"
CONF_LOW  = "low"

SOURCE_REGEX = "regex"
SOURCE_FLOOR = "floor"

LLM_BUDGET       = 0  # 2026-05-19 patch: Gemini CLI FM-3f timeout (100% on LCR v3-span); budget zeroed to produce regex + floor only.
GEMINI_CMD        = "gemini.cmd"
GEMINI_MODEL      = "gemini-3.1-flash-lite"
GEMINI_CLI_VER    = "0.42.0"
CALL_TIMEOUT      = 60   # seconds per call

# ---------------------------------------------------------------------------
# Regex patterns — identical to v2 for reproducibility
# ---------------------------------------------------------------------------
# Layer 1a — Strong-signal direct-quote patterns
_DQ_PATTERNS = [
    (re.compile(r'(?:^|\n)[ \t]*(?:>|&gt;)\s*\S', re.M),
     LABEL_DIRECT, CONF_HIGH, "blockquote_marker"),

    (re.compile(
        r'(?:claude|the\s+model|it|the\s+ai|the\s+assistant|claude\s+code)\s+'
        r'(?:said|wrote|replied|responded|told\s+me|told\s+us|stated|added)\s*'
        r'(?:something\s+like\s*)?["""“”‘’""]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_open_quote"),

    (re.compile(r'(?im)^(?:claude|model|ai|assistant)\s*:\s*\S'),
     LABEL_DIRECT, CONF_HIGH, "standalone_speaker_label"),

    (re.compile(r'(?i)claude\s*:["""“”"]'),
     LABEL_DIRECT, CONF_HIGH, "speaker_label_colon_quote"),

    (re.compile(
        r'(?:claude|the\s+model|the\s+ai|it)\s+'
        r'(?:said|told\s+me|wrote|replied|responded)\s+'
        r'["""“”"][^""""“”]{5,200}["""“”"]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_quoted_block"),
]

# Layer 1b — Paraphrase-signal patterns (corpus-specific vocabulary)
_PM_PATTERNS = [
    (re.compile(r'(?i)my\s+claude\s+(?:tells?|told)\s+me', re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "my_claude_tells_me"),

    (re.compile(r'(?i)mine\s+(?:is\s+)?(?:telling|told|keeps?\s+telling)', re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "mine_is_telling"),

    (re.compile(
        r'(?:it|claude|the\s+model|the\s+ai)\s+'
        r'(?:kept|keeps|kept\s+on|keeps\s+on)\s+'
        r'(?:telling|saying|repeating|insisting|asking)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "kept_telling_me"),

    (re.compile(
        r'(?:claude|the\s+model|the\s+ai|the\s+assistant)\s+'
        r'(?:said|claimed|told\s+me|insisted|suggested)\s+'
        r'(?:it|she|he)\s+'
        r'(?:needs?|needed|was|is|had\s+to|wanted|couldn\'t?|would)\b',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "third_person_self_attribution"),

    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:basically|essentially|kind\s+of|sort\s+of|practically|literally)\s+'
        r'(?:said|told\s+me|told\s+us|suggested|implied|stated|informed\s+me)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "basically_said"),

    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:sent|put|pushed|forced|made|sending|putting|getting)\s+me\s+'
        r'(?:to\s+)?(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "sent_me_to_bed"),

    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|the\s+assistant|claude\s+code)\s+'
        r'(?:told\s+me\s+to|told\s+us\s+to|told\s+me\s+that|told\s+us\s+that|'
        r'said\s+(?:I|we|to)\s+should|said\s+to|'
        r'suggested\s+(?:I|we)\s+|suggested\s+that\s+(?:I|we)\s+|'
        r'insisted\s+(?:I|we)\s+|insisted\s+that|'
        r'asked\s+(?:me|us)\s+to|'
        r'refused\s+to|'
        r'decided\s+(?:it\s+was|that\s+it\s+was|to)|'
        r'kept\s+saying|'
        r'would\s+(?:say|tell\s+me|ask)\s+)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "attribution_verb_directive"),

    (re.compile(
        r'(?:claude|the\s+model|the\s+ai)\s+(?:is|was|were)\s+like\b',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "is_like_reported_speech"),

    (re.compile(
        r'(?:and\s+then|then|after\s+that|at\s+which\s+point|so|whereupon)\s+'
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:said|told|replied|responded|wrote|suggested|asked)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "narrative_reconstruction"),

    (re.compile(
        r'(?:it|claude|the\s+model)\s+decides?\s+(?:I\'?m|I\s+was|that)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "model_judgment_attribution"),

    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|the\s+assistant)\s+'
        r'(?:would|will|does|doesn\'t?|won\'t|wouldn\'t)\s+'
        r'(?:say|tell\s+me|suggest|insist|refuse|push|encourage|prompt|ask)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "would_say"),

    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|claude\s+code)\s+'
        r'(?:wants?\s+(?:me|us)\s+to|'
        r'asks?\s+(?:me|us)\s+to|'
        r'suggests?\s+(?:I|we)\s+|'
        r'encourages?\s+(?:me|us)\s+to|'
        r'prompts?\s+(?:me|us)\s+to)\s+'
        r'(?:go\s+to\s+(?:bed|sleep)|rest|take\s+a\s+break|stop)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "asks_me_to_sleep"),

    (re.compile(
        r'(?:tells?\s+(?:you|me|us)\s+to\s+go\s+to\s+(?:bed|sleep)|'
        r'telling\s+(?:you|me|us)\s+to\s+go\s+to\s+(?:bed|sleep)|'
        r'told\s+(?:me|us|you)\s+to\s+go\s+to\s+(?:bed|sleep))',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "tells_me_to_go_to_bed"),

    (re.compile(
        r'claude\s+telling\s+(?:its\s+)?users?\s+to',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "claude_telling_users"),

    (re.compile(
        r'(?:constantly|keeps?|kept|always|again)\s+'
        r'(?:telling|saying|asking|suggesting|reminding)\s+'
        r'(?:me|us|you)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "repeated_attribution_adverb"),

    (re.compile(
        r'(?:I\s+asked\s+(?:claude|it|the\s+model))\s+.{0,60}'
        r'(?:and\s+(?:it|claude|the\s+model))\s+'
        r'(?:said|told|replied|responded|wrote|suggested)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "i_asked_and_it_said"),
]

# Layer 1c — Weak-signal heuristics
_WEAK_PATTERNS = [
    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|claude\s+code)\s+'
        r'(?:always|constantly|often|sometimes|never|still|just)\s+'
        r'(?:tries?\s+to|tells?\s+me\s+to|wants?\s+to|says?\s+to|asks?\s+me\s+to|'
        r'suggests?\s+|insists?\s+|refuses?\s+to)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_habitual_attribution"),

    (re.compile(
        r'(?:tells?\s+(?:me|you|us)|told\s+(?:me|you|us))\s+'
        r'to\s+go\s+to\s+(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_tells_me_go_to_bed"),

    (re.compile(
        r'(?:wants?\s+(?:me|you|us)\s+to|trying\s+to\s+(?:get|send|put)\s+'
        r'(?:me|you|us)\s+to)\s+(?:go\s+to\s+)?(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_wants_me_to_sleep"),

    (re.compile(
        r'(?:claude|it|the\s+model)\s+(?:is|was)\s+like\s+["""“”"]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_LOW, "weak_is_like_with_quote"),
]

ALL_PATTERNS = _DQ_PATTERNS + _PM_PATTERNS + _WEAK_PATTERNS

# ---------------------------------------------------------------------------
# Negation pre-screen (FM-1c mitigation)
# If the sentence containing the match begins with a negation, downgrade or skip.
# ---------------------------------------------------------------------------
_NEGATION_RE = re.compile(
    r'\b(?:never|hasn\'t|haven\'t|didn\'t|doesn\'t|don\'t|not|no\s+one|nobody'
    r'|zero\s+concept|without)\b',
    re.IGNORECASE,
)


def _sentence_containing(text: str, start: int, end: int) -> str:
    """Return the sentence (heuristic: delimited by '. ', '\n', or start/end)
    that contains character positions [start, end)."""
    sent_start = max(0, text.rfind('\n', 0, start))
    if sent_start == 0 and text[0] != '\n':
        sent_start = 0
    # walk back for period+space
    period_pos = text.rfind('. ', 0, start)
    if period_pos > sent_start:
        sent_start = period_pos + 2
    sent_end = text.find('\n', end)
    if sent_end == -1:
        sent_end = len(text)
    period_pos2 = text.find('. ', end)
    if period_pos2 != -1 and period_pos2 < sent_end:
        sent_end = period_pos2 + 1
    return text[sent_start:sent_end]


def _is_negated(text: str, match_start: int, match_end: int) -> bool:
    """Return True if the match appears inside a negated sentence fragment."""
    sentence = _sentence_containing(text, match_start, match_end)
    # Check the part of the sentence BEFORE the matched phrase
    pre = sentence[:match_start - max(0, text.rfind('\n', 0, match_start))]
    return bool(_NEGATION_RE.search(pre)) or bool(_NEGATION_RE.search(sentence[:30]))


# ---------------------------------------------------------------------------
# Span data structure
# ---------------------------------------------------------------------------

class Span:
    """A half-open character interval [start, end) with label and metadata."""
    __slots__ = ("start", "end", "label", "confidence", "source", "pattern_note")

    def __init__(self, start: int, end: int, label: str, confidence: str,
                 source: str, pattern_note: str = ""):
        self.start = start
        self.end   = end
        self.label = label
        self.confidence = confidence
        self.source = source
        self.pattern_note = pattern_note

    def __repr__(self):
        return (f"Span({self.start}:{self.end} {self.label[:6]}"
                f" {self.confidence} {self.source})")


def _merge_adjacent(spans: List[Span]) -> List[Span]:
    """Merge consecutive spans that share the same label."""
    if not spans:
        return spans
    merged = [spans[0]]
    for s in spans[1:]:
        prev = merged[-1]
        if (s.start == prev.end and s.label == prev.label
                and s.confidence == prev.confidence):
            # Extend previous span
            merged[-1] = Span(prev.start, s.end, prev.label,
                               prev.confidence, prev.source,
                               prev.pattern_note)
        else:
            merged.append(s)
    return merged


# ---------------------------------------------------------------------------
# Layer 1: regex span extraction
# ---------------------------------------------------------------------------

def _regex_spans(text: str) -> List[Span]:
    """
    Scan text with all regex patterns.  For each match, emit a Span covering
    the sentence (heuristic) that contains the match.  Multiple overlapping
    sentences may be merged later; at this stage we store per-match spans.

    Span boundaries are expanded to the nearest sentence boundary (newline or
    '. ') so that the label describes the sentence-level unit, not just the
    triggering token.

    Returns list of Span objects, unsorted, possibly overlapping.
    Negation pre-screen (FM-1c): if the sentence containing the match starts
    with a negation marker, skip the match.
    """
    raw_spans = []

    for pattern, label, conf, note in ALL_PATTERNS:
        for m in pattern.finditer(text):
            ms, me = m.start(), m.end()

            # Expand to sentence-level boundaries
            # Find start: walk left to newline or '. '
            s_start = ms
            nl = text.rfind('\n', 0, ms)
            if nl != -1:
                s_start = nl + 1
            else:
                s_start = 0
            period = text.rfind('. ', 0, ms)
            if period != -1 and period + 2 > s_start:
                s_start = period + 2

            # Find end: walk right to newline or '. '
            s_end = me
            nl2 = text.find('\n', me)
            period2 = text.find('. ', me)
            if nl2 == -1 and period2 == -1:
                s_end = len(text)
            elif nl2 == -1:
                s_end = period2 + 1
            elif period2 == -1:
                s_end = nl2
            else:
                s_end = min(nl2, period2 + 1)

            # Clamp to text length
            s_start = max(0, s_start)
            s_end   = min(len(text), s_end)

            # Skip if the span is degenerate
            if s_start >= s_end:
                continue

            # Negation pre-screen: if negated, skip this match
            if _is_negated(text, ms, me):
                continue

            raw_spans.append(Span(s_start, s_end, label, conf, SOURCE_REGEX, note))

    return raw_spans


def _resolve_overlaps(spans: List[Span], text_len: int) -> List[Span]:
    """
    Given potentially overlapping spans, produce a non-overlapping cover of
    [0, text_len).

    Priority: higher confidence wins; among equal confidence, DQ > PM > UC.
    Remaining intervals become floor spans (User_Original_Content / low).

    Algorithm:
    1. Sort by start; for ties, prefer higher confidence then earlier end.
    2. Use a greedy interval cover: process spans in priority order, fill in
       only uncovered characters.
    """
    if not spans:
        return []

    conf_order = {CONF_HIGH: 3, CONF_MED: 2, CONF_LOW: 1}
    label_order = {LABEL_DIRECT: 3, LABEL_PARAPHRASE: 2, LABEL_USER: 1, LABEL_UNCLEAR: 0}

    # Sort by (conf desc, label desc, start asc, length desc)
    priority = sorted(
        spans,
        key=lambda s: (
            -conf_order.get(s.confidence, 0),
            -label_order.get(s.label, 0),
            s.start,
            -(s.end - s.start),
        ),
    )

    # Greedy fill: maintain a coverage bitmap as a list of (start, end, span) tuples
    covered: List[Tuple[int, int, Span]] = []

    for s in priority:
        # Check if any portion of [s.start, s.end) is uncovered
        # We only add the uncovered portions
        sub_start = s.start
        sub_end   = s.end

        # Find existing covered segments that overlap [sub_start, sub_end)
        overlapping = [(cs, ce, csp) for cs, ce, csp in covered
                       if cs < sub_end and ce > sub_start]

        if not overlapping:
            # Entire range is uncovered — add whole span
            covered.append((sub_start, sub_end, s))
        else:
            # Add uncovered sub-ranges within [sub_start, sub_end)
            # Build sorted coverage within the target range
            ov_sorted = sorted(overlapping, key=lambda t: t[0])
            pos = sub_start
            for cs, ce, _ in ov_sorted:
                if pos < cs:
                    covered.append((pos, cs, s))
                pos = max(pos, ce)
            if pos < sub_end:
                covered.append((pos, sub_end, s))

    # Now sort covered intervals
    covered.sort(key=lambda t: t[0])

    # Fill gaps with floor spans
    result = []
    pos = 0
    for (cs, ce, sp) in covered:
        if pos < cs:
            result.append(Span(pos, cs, LABEL_USER, CONF_LOW, SOURCE_FLOOR, "floor"))
        result.append(Span(cs, ce, sp.label, sp.confidence, sp.source, sp.pattern_note))
        pos = ce
    if pos < text_len:
        result.append(Span(pos, text_len, LABEL_USER, CONF_LOW, SOURCE_FLOOR, "floor"))

    return result


# ---------------------------------------------------------------------------
# LLM fallback infrastructure (Layer 2)
# ---------------------------------------------------------------------------

SPAN_PROMPT_TEMPLATE = """\
You are classifying a TEXT FRAGMENT extracted from a Reddit post or comment about Claude AI.
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or User_Original_Content.

Direct_Quote_Of_Model: the fragment quotes Claude/AI verbatim.
  Examples: "> Now go to sleep", "Claude: that is a good place to leave", it said "you should rest"
Paraphrase_Of_Model: the fragment reports or paraphrases what Claude/AI said or did.
  Examples: "Claude told me to go to bed", "it kept insisting I take a break", "my Claude tells me to stop"
User_Original_Content: the fragment contains no AI speech at all.
  Examples: "I worked all night", "anyone else notice this?", general commentary, questions to other users

If the fragment contains negated attribution (e.g., "it never told me to sleep"), choose User_Original_Content.
Reply with ONLY the label name, no other text.

Text fragment: {text}"""

_llm_call_count = 0
_llm_errors: List[Dict] = []


def _call_gemini_span(text_fragment: str, row_id: str,
                      span_start: int, span_end: int) -> Tuple[str, str]:
    """
    Call Gemini CLI to classify a text fragment (span interval).
    Returns (label, confidence).
    Unicode fix: encoding='utf-8', errors='replace' (from v2).
    """
    global _llm_call_count

    excerpt = (text_fragment or "")[:2000]
    prompt  = SPAN_PROMPT_TEMPLATE.format(text=excerpt)
    t_start = time.monotonic()

    try:
        result = subprocess.run(
            [GEMINI_CMD, "-m", GEMINI_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CALL_TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
        raw_stdout = result.stdout.strip() if result.stdout else ""

        # Filter startup noise
        noise_kw = [
            "true-color", "ripgrep", "mcp", "schema", "warning", "info:",
            "debug:", "note:", "loaded", "connecting", "initializ",
        ]
        clean_lines = []
        for line in raw_stdout.splitlines():
            ll = line.lower().strip()
            if any(kw in ll for kw in noise_kw):
                continue
            if line.strip():
                clean_lines.append(line.strip())
        raw_clean = " ".join(clean_lines).strip() if clean_lines else raw_stdout

        valid_labels = {LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER}
        label = None
        for candidate in valid_labels:
            if candidate.lower() in raw_clean.lower():
                label = candidate
                break

        if label is None:
            label = LABEL_USER
            confidence = CONF_LOW
            err_note = f"no_valid_label: '{raw_clean[:100]}'"
            _llm_errors.append({"row_id": row_id, "span_start": span_start,
                                 "span_end": span_end, "error": err_note,
                                 "call_number": _llm_call_count + 1})
        else:
            stripped = raw_clean.strip().rstrip(".")
            confidence = CONF_HIGH if stripped == label else CONF_MED

        elapsed = round(time.monotonic() - t_start, 2)
        error_flag = ""

    except subprocess.TimeoutExpired:
        elapsed    = CALL_TIMEOUT
        label      = LABEL_USER
        confidence = CONF_LOW
        raw_clean  = "TIMEOUT"
        error_flag = "timeout"
        _llm_errors.append({"row_id": row_id, "span_start": span_start,
                             "span_end": span_end, "error": "timeout",
                             "call_number": _llm_call_count + 1})

    except Exception as exc:
        elapsed    = round(time.monotonic() - t_start, 2)
        label      = LABEL_USER
        confidence = CONF_LOW
        raw_clean  = f"ERROR: {exc}"
        error_flag = str(exc)
        _llm_errors.append({"row_id": row_id, "span_start": span_start,
                             "span_end": span_end, "error": str(exc),
                             "call_number": _llm_call_count + 1})

    _llm_call_count += 1

    source_str = f"llm:{GEMINI_MODEL}"
    log_entry = {
        "call_number":        _llm_call_count,
        "row_id":             row_id,
        "span_start":         span_start,
        "span_end":           span_end,
        "tool":               "Gemini CLI",
        "cli_version":        GEMINI_CLI_VER,
        "model":              GEMINI_MODEL,
        "prompt_excerpt":     prompt[:500],
        "input_fragment":     excerpt[:200],
        "raw_response":       raw_clean[:500],
        "assigned_label":     label,
        "assigned_confidence": confidence,
        "elapsed_seconds":    elapsed,
        "error":              error_flag or None,
        "timestamp":          datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(LLM_LOG_V3, "a", encoding="utf-8") as flog:
        flog.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return label, confidence


# ---------------------------------------------------------------------------
# Per-row span segmentation
# ---------------------------------------------------------------------------

def _segment_row(text: str, row_id: str,
                 llm_budget_remaining: int) -> Tuple[List[Span], int]:
    """
    Run all three layers for a single row.

    Returns (spans, llm_calls_used_this_row).
    Spans are sorted, contiguous, non-overlapping, covering [0, len(text)).
    """
    if not text:
        # Empty text: single floor span of length 0
        return [Span(0, 0, LABEL_USER, CONF_LOW, SOURCE_FLOOR, "empty_text")], 0

    text_len = len(text)

    # --- Layer 1: regex ---
    raw_regex_spans = _regex_spans(text)
    # Resolve overlaps → get a partial coverage (with floors already filled)
    layer1_spans = _resolve_overlaps(raw_regex_spans, text_len)
    # layer1_spans already covers [0, text_len) fully thanks to _resolve_overlaps

    # --- Layer 2: LLM fallback on floor spans ---
    # Identify floor spans that are large enough to be worth an LLM call.
    # Only send if budget allows.
    MIN_LLM_SPAN_CHARS = 30  # ignore trivial whitespace-only gaps
    llm_calls_used = 0
    upgraded_spans: List[Span] = []

    for sp in layer1_spans:
        if (sp.source == SOURCE_FLOOR and
                llm_budget_remaining > 0 and
                (sp.end - sp.start) >= MIN_LLM_SPAN_CHARS):
            fragment = text[sp.start:sp.end]
            label, conf = _call_gemini_span(fragment, row_id, sp.start, sp.end)
            llm_budget_remaining -= 1
            llm_calls_used += 1
            upgraded_spans.append(
                Span(sp.start, sp.end, label, conf,
                     f"llm:{GEMINI_MODEL}", "llm_fallback")
            )
        else:
            upgraded_spans.append(sp)

    # --- Layer 3: floor for any remaining unclassified (already handled by
    # _resolve_overlaps, but re-assert here for any spans not upgraded) ---
    # At this point upgraded_spans already covers the full text.

    # Merge adjacent same-label spans
    final = _merge_adjacent(sorted(upgraded_spans, key=lambda s: s.start))
    return final, llm_calls_used


# ---------------------------------------------------------------------------
# Resume-safe row ID tracking
# ---------------------------------------------------------------------------

def _load_done_row_ids(output_path: Path) -> set:
    """Return set of row_ids already written to the output CSV."""
    done = set()
    if not output_path.exists():
        return done
    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and "row_id" in reader.fieldnames:
            for row in reader:
                done.add(row["row_id"])
    return done


# ---------------------------------------------------------------------------
# Main segmentation loop
# ---------------------------------------------------------------------------

SPANS_FIELDNAMES = [
    "row_id", "span_index", "span_start", "span_end",
    "label", "confidence", "source", "span_text",
]


def run_v3_span_segmentation() -> List[Dict]:
    """
    Segment all 773 rows.  Resume-safe: skips rows already in OUTPUT_SPANS.
    Returns list of all span dicts (new and previously written).
    """
    global _llm_call_count

    # Load input rows
    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        rows = list(reader)
    n_rows = len(rows)
    print(f"Loaded {n_rows} rows from {INPUT_CSV.name}")

    # Check resume state
    done_row_ids = _load_done_row_ids(OUTPUT_SPANS)
    n_already_done = len(done_row_ids)
    if n_already_done > 0:
        print(f"  Resume: {n_already_done} rows already in output; skipping them.")

    # Prepare output file (append mode if resuming, write header if new)
    write_header = not OUTPUT_SPANS.exists() or n_already_done == 0
    out_mode = "w" if write_header else "a"

    # Compute per-row row_id key (matches v2 convention: post_id|comment_id)
    def row_key(row: Dict) -> str:
        return row.get("post_id", "") + "|" + row.get("comment_id", "")

    # Budget: how many LLM calls remain
    llm_remaining = LLM_BUDGET - _llm_call_count

    all_span_dicts: List[Dict] = []

    # If resuming, we need to reconstruct existing span dicts from file
    if done_row_ids:
        with open(OUTPUT_SPANS, newline="", encoding="utf-8") as f:
            for d in csv.DictReader(f):
                all_span_dicts.append(d)

    with open(OUTPUT_SPANS, out_mode, newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=SPANS_FIELDNAMES)
        if write_header:
            writer.writeheader()

        for i, row in enumerate(rows):
            rid = row_key(row)
            if rid in done_row_ids:
                continue

            text = row.get("body", "") or ""

            spans, calls_used = _segment_row(text, rid, llm_remaining)
            llm_remaining -= calls_used

            for j, sp in enumerate(spans):
                d = {
                    "row_id":      rid,
                    "span_index":  j,
                    "span_start":  sp.start,
                    "span_end":    sp.end,
                    "label":       sp.label,
                    "confidence":  sp.confidence,
                    "source":      sp.source,
                    "span_text":   text[sp.start:sp.end].replace("\n", " | "),
                }
                writer.writerow(d)
                all_span_dicts.append(d)

            if (i + 1) % 50 == 0:
                print(f"  Processed {i+1}/{n_rows} rows "
                      f"(LLM calls used: {_llm_call_count})")

    print(f"\nSegmentation complete.")
    print(f"  Total span records : {len(all_span_dicts)}")
    print(f"  Gemini calls used  : {_llm_call_count}")
    if _llm_errors:
        print(f"  LLM errors         : {len(_llm_errors)}")
    return all_span_dicts


# ---------------------------------------------------------------------------
# Validation sample (50 rows, stratified by type and char-count quartile)
# ---------------------------------------------------------------------------

def prepare_validation_sample(rows_input: List[Dict],
                               all_span_dicts: List[Dict],
                               output_path: Path,
                               seed: int = 42) -> None:
    """
    50-item stratified random sample at the ROW level.
    Stratification: type (post/comment) x character-count quartile.
    For each sampled row: row_id, type, subreddit, retrieval_provenance,
    full_text, span_breakdown_serialized (JSON), researcher_corrections (empty),
    researcher_notes (empty).
    """
    random.seed(seed)

    # Build span index by row_id
    spans_by_row: Dict[str, List[Dict]] = defaultdict(list)
    for d in all_span_dicts:
        spans_by_row[d["row_id"]].append(d)

    def row_key(row: Dict) -> str:
        return row.get("post_id", "") + "|" + row.get("comment_id", "")

    # Compute char counts
    annotated = []
    for row in rows_input:
        rid  = row_key(row)
        text = row.get("body", "") or ""
        annotated.append({
            "row": row,
            "rid": rid,
            "text": text,
            "char_count": len(text),
        })

    # Char-count quartile boundaries
    char_counts = sorted(a["char_count"] for a in annotated)
    n = len(char_counts)
    q1 = char_counts[n // 4]
    q2 = char_counts[n // 2]
    q3 = char_counts[3 * n // 4]

    def quartile(cc: int) -> int:
        if cc <= q1: return 1
        if cc <= q2: return 2
        if cc <= q3: return 3
        return 4

    for a in annotated:
        a["quartile"] = quartile(a["char_count"])

    # Build strata: type x quartile -> list of items
    strata: Dict[Tuple, List] = defaultdict(list)
    for a in annotated:
        key = (a["row"]["type"], a["quartile"])
        strata[key].append(a)

    # Target: 50 rows.  Allocate proportionally across strata.
    total_items = len(annotated)
    TARGET = 50
    allocations: Dict[Tuple, int] = {}
    residual = TARGET
    strata_keys = sorted(strata.keys())

    for idx, key in enumerate(strata_keys):
        proportion = len(strata[key]) / total_items
        alloc = round(TARGET * proportion)
        # Clamp to at least 1 if stratum is non-empty, max to stratum size
        alloc = max(1, min(alloc, len(strata[key])))
        allocations[key] = alloc

    # Adjust total to exactly TARGET
    current_total = sum(allocations.values())
    diff = TARGET - current_total
    # Add/subtract from the largest strata first
    sorted_by_size = sorted(strata_keys, key=lambda k: -len(strata[k]))
    for key in sorted_by_size:
        if diff == 0:
            break
        if diff > 0:
            max_add = len(strata[key]) - allocations[key]
            add = min(diff, max_add)
            allocations[key] += add
            diff -= add
        else:
            max_sub = allocations[key] - 1
            sub = min(-diff, max_sub)
            allocations[key] -= sub
            diff += sub

    # Sample
    sampled = []
    sampled_rids: set = set()
    for key in strata_keys:
        pool = [a for a in strata[key] if a["rid"] not in sampled_rids]
        n_take = min(allocations.get(key, 0), len(pool))
        chosen = random.sample(pool, n_take)
        for a in chosen:
            sampled_rids.add(a["rid"])
            sampled.append(a)

    sampled.sort(key=lambda a: (a["row"]["type"], a["quartile"]))

    SAMPLE_FIELDS = [
        "row_id", "type", "subreddit", "retrieval_provenance",
        "full_text", "span_breakdown_serialized",
        "researcher_corrections", "researcher_notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_FIELDS)
        writer.writeheader()
        for a in sampled:
            row   = a["row"]
            rid   = a["rid"]
            text  = a["text"]
            spans = sorted(spans_by_row.get(rid, []),
                           key=lambda d: int(d.get("span_index", 0)))
            span_breakdown = [
                {
                    "span_index":  d["span_index"],
                    "span_start":  d["span_start"],
                    "span_end":    d["span_end"],
                    "label":       d["label"],
                    "confidence":  d["confidence"],
                    "source":      d["source"],
                    "span_text":   d["span_text"][:200],
                }
                for d in spans
            ]
            writer.writerow({
                "row_id":                  rid,
                "type":                    row.get("type", ""),
                "subreddit":               row.get("subreddit", ""),
                "retrieval_provenance":    row.get("retrieval_provenance", ""),
                "full_text":               text.replace("\n", " | "),
                "span_breakdown_serialized": json.dumps(span_breakdown,
                                                         ensure_ascii=False),
                "researcher_corrections":  "",
                "researcher_notes":        "",
            })

    print(f"\nValidation sample: {len(sampled)} rows → {output_path.name}")
    strata_repr = ", ".join(
        f"{k[0]}/Q{k[1]}={allocations.get(k, 0)}" for k in strata_keys
    )
    print(f"  Strata allocation: {strata_repr}")


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def compute_summary(rows_input: List[Dict],
                    all_span_dicts: List[Dict]) -> Dict:
    """
    Compute statistics for the summary markdown.
    Returns a dict with all key metrics.
    """
    def row_key(row: Dict) -> str:
        return row.get("post_id", "") + "|" + row.get("comment_id", "")

    # Build lookup: rid -> row
    row_by_rid: Dict[str, Dict] = {row_key(r): r for r in rows_input}

    # Total spans
    total_spans = len(all_span_dicts)

    # Label distribution by span count and char count
    label_span_counts:  Counter = Counter()
    label_char_counts:  Counter = Counter()
    conf_span_counts:   Counter = Counter()
    conf_char_counts:   Counter = Counter()
    source_span_counts: Counter = Counter()

    type_label_spans:   Dict = defaultdict(Counter)
    type_conf_spans:    Dict = defaultdict(Counter)

    total_chars = 0

    for d in all_span_dicts:
        label = d["label"]
        conf  = d["confidence"]
        src   = d["source"]
        try:
            start = int(d["span_start"])
            end   = int(d["span_end"])
        except (ValueError, TypeError):
            start, end = 0, 0
        char_count = max(0, end - start)

        rid  = d["row_id"]
        rtype = row_by_rid.get(rid, {}).get("type", "unknown")

        label_span_counts[label]   += 1
        label_char_counts[label]   += char_count
        conf_span_counts[conf]     += 1
        conf_char_counts[conf]     += char_count
        source_span_counts[src]    += 1
        type_label_spans[rtype][label] += 1
        type_conf_spans[rtype][conf]   += 1
        total_chars += char_count

    # Reliable-segmentation fraction (§C.4 metric):
    # sum of high+medium confidence spans' char counts / total corpus char count
    reliable_chars = conf_char_counts.get(CONF_HIGH, 0) + conf_char_counts.get(CONF_MED, 0)
    reliable_fraction = reliable_chars / total_chars if total_chars > 0 else 0.0

    # Per-type breakdown
    post_rows    = [r for r in rows_input if r.get("type") == "post"]
    comment_rows = [r for r in rows_input if r.get("type") == "comment"]

    return {
        "total_spans":         total_spans,
        "total_chars":         total_chars,
        "label_span_counts":   dict(label_span_counts),
        "label_char_counts":   dict(label_char_counts),
        "conf_span_counts":    dict(conf_span_counts),
        "conf_char_counts":    dict(conf_char_counts),
        "source_span_counts":  dict(source_span_counts),
        "reliable_chars":      reliable_chars,
        "reliable_fraction":   reliable_fraction,
        "type_label_spans":    {k: dict(v) for k, v in type_label_spans.items()},
        "type_conf_spans":     {k: dict(v) for k, v in type_conf_spans.items()},
        "n_posts":             len(post_rows),
        "n_comments":          len(comment_rows),
        "n_rows_total":        len(rows_input),
        "llm_calls_used":      _llm_call_count,
        "llm_errors":          len(_llm_errors),
    }


# ---------------------------------------------------------------------------
# Write summary markdown
# ---------------------------------------------------------------------------

def write_summary_md(stats: Dict, output_path: Path) -> None:
    """Write the §C.4 audit trail summary markdown."""
    rf = stats["reliable_fraction"]
    threshold_met = rf >= 0.70
    threshold_verdict = ("MEETS" if threshold_met
                         else "DOES NOT MEET")

    label_counts  = stats["label_span_counts"]
    label_chars   = stats["label_char_counts"]
    conf_counts   = stats["conf_span_counts"]
    conf_chars    = stats["conf_char_counts"]
    source_counts = stats["source_span_counts"]
    total_spans   = stats["total_spans"]
    total_chars   = stats["total_chars"]
    type_label    = stats["type_label_spans"]
    type_conf     = stats["type_conf_spans"]

    def pct(n, d):
        return f"{100*n/d:.1f}%" if d > 0 else "n/a"

    lines = [
        "# Phase 4 Voice Segmentation — v3 Span-Level Summary",
        "",
        f"**Date:** 2026-05-18",
        f"**Script:** `src/voice_segmentation_v3_span.py`",
        f"**Corpus:** `data/pass1b_canonical.csv` — "
        f"{stats['n_rows_total']} rows "
        f"({stats['n_posts']} posts, {stats['n_comments']} comments)",
        f"**Method:** [method §C.4]; [methods_library §9.0, §9.1, §9.2, §9.3]",
        "",
        "---",
        "",
        "## 1. Total spans produced",
        "",
        f"**{total_spans}** spans across {stats['n_rows_total']} rows.",
        f"Total corpus character count: {total_chars:,}",
        "",
        "---",
        "",
        "## 2. Distribution by label (span count and character count)",
        "",
        "| Label | Spans | % of spans | Characters | % of chars |",
        "|---|---|---|---|---|",
    ]

    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER, LABEL_UNCLEAR]:
        sc = label_counts.get(label, 0)
        cc = label_chars.get(label, 0)
        lines.append(
            f"| {label} | {sc} | {pct(sc, total_spans)} "
            f"| {cc:,} | {pct(cc, total_chars)} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 3. Distribution by confidence",
        "",
        "| Confidence | Spans | % of spans | Characters | % of chars |",
        "|---|---|---|---|---|",
    ]

    for conf in [CONF_HIGH, CONF_MED, CONF_LOW]:
        sc = conf_counts.get(conf, 0)
        cc = conf_chars.get(conf, 0)
        lines.append(
            f"| {conf} | {sc} | {pct(sc, total_spans)} "
            f"| {cc:,} | {pct(cc, total_chars)} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. §C.4 reliable-segmentation fraction (70% threshold)",
        "",
        "The §C.4 threshold is computed as:",
        "> sum of high + medium confidence spans' character counts ÷ total corpus character count",
        "",
        f"- High-confidence character count : {conf_chars.get(CONF_HIGH, 0):,}",
        f"- Medium-confidence character count: {conf_chars.get(CONF_MED, 0):,}",
        f"- High + medium total              : {stats['reliable_chars']:,}",
        f"- Total corpus characters          : {total_chars:,}",
        f"- **Reliable-segmentation fraction : {rf:.3f} ({rf*100:.1f}%)**",
        "",
        f"**§C.4 threshold determination: {threshold_verdict} the 70% threshold.**",
        "",
        "---",
        "",
        "## 5. Per-type stratification (post vs comment)",
        "",
        "### 5a. Span label distribution",
        "",
        "| Type | Direct_Quote | Paraphrase | User_Content | Unclassifiable |",
        "|---|---|---|---|---|",
    ]

    for rtype in ["post", "comment"]:
        lc = type_label.get(rtype, {})
        dq = lc.get(LABEL_DIRECT, 0)
        pm = lc.get(LABEL_PARAPHRASE, 0)
        uc = lc.get(LABEL_USER, 0)
        un = lc.get(LABEL_UNCLEAR, 0)
        lines.append(f"| {rtype} | {dq} | {pm} | {uc} | {un} |")

    lines += [
        "",
        "### 5b. Confidence distribution by type",
        "",
        "| Type | High | Medium | Low |",
        "|---|---|---|---|",
    ]

    for rtype in ["post", "comment"]:
        cc = type_conf.get(rtype, {})
        h  = cc.get(CONF_HIGH, 0)
        m  = cc.get(CONF_MED, 0)
        lo = cc.get(CONF_LOW, 0)
        lines.append(f"| {rtype} | {h} | {m} | {lo} |")

    lines += [
        "",
        "---",
        "",
        "## 6. Source distribution",
        "",
        "| Source | Spans |",
        "|---|---|",
    ]

    for src, cnt in sorted(source_counts.items(), key=lambda t: -t[1]):
        lines.append(f"| {src} | {cnt} |")

    lines += [
        "",
        f"LLM calls used: {stats['llm_calls_used']} / {LLM_BUDGET} budget",
        f"LLM call errors: {stats['llm_errors']}",
        "",
        "---",
        "",
        "## 7. Comparison to v2 row-level: §C.4 threshold under corrected schema",
        "",
        "**v2 (row-level, deprecated):** the §C.4 reliable-segmentation fraction was",
        "computed as the proportion of *rows* with high or medium confidence labels.",
        "That measure treated a 10-character row identically to a 10,000-character row.",
        "",
        "**v3 (span-level, corrected):** the fraction is computed as",
        "*character-count-weighted* coverage of high + medium confidence spans.",
        "This is the correct operationalization per §9.0 of methods_library.md.",
        "",
        "v2's row-level fraction over-counted rows where a single clause triggered",
        "a high-confidence regex match but the surrounding paragraphs were floor-",
        "defaulted User_Original_Content.  v3 correctly weights those surrounding",
        "paragraphs at their actual character count, which lowers the threshold",
        "metric relative to v2's count-based report.",
        "",
        "---",
        "",
        "## 8. v3-span-specific failure modes observed",
        "",
        "| ID | Mode | Direction | Span-level impact |",
        "|---|---|---|---|",
        "| FM-SB1 | Sentence-boundary expansion over-labels adjacent neutral text | FP | Sentence that contains the trigger phrase is labeled entirely, dragging neutral clauses into model-attribution spans |",
        "| FM-SB2 | Very short floor gaps (< 30 chars) skip LLM; assigned floor | FN | Connective phrases, punctuation, and transition words between attributed sentences default to User_Original_Content/low rather than being promoted |",
        "| FM-SB3 | Multi-sentence narrative reconstructions span several sentences; regex captures only the triggering sentence | FN | Text before and after the matching sentence may be part of the same attributed narration but falls into floor spans |",
        "| FM-1a | Reddit `>` as list, not blockquote (inherited from v2) | FP | Blockquote pattern labels the entire '>'-prefixed sentence as Direct_Quote |",
        "| FM-1c | Negated attribution (inherited; negation pre-screen partially mitigates) | FP | Negation pre-screen fires on a 30-char window before the match; negations located after the match are missed |",
        "| FM-2c | Screenshot-only posts: no text to segment | FN | Entire body defaults to floor User_Original_Content/low |",
        "",
        "---",
        "",
        "*Validation sample:* 50 rows at",
        "`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3_span.csv`.",
        "Researcher review of `span_breakdown_serialized` column constitutes the §9.3",
        "hand-validation step.  The §C.4 70% threshold determination above is provisional",
        "pending that review.",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nSummary written to {output_path.name}")


# ---------------------------------------------------------------------------
# LLM tool log update (§4.3 compliance)
# ---------------------------------------------------------------------------

def append_llm_tool_log() -> None:
    """Append a v3_span entry to notebooks/llm_tool_log.md."""
    entry = f"""
---

## Entry 002 — Phase 4 Voice Segmentation Fallback (v3_span)

| Field | Value |
|---|---|
| Tool | Gemini CLI {GEMINI_CLI_VER} (`gemini.cmd`) |
| Model | `{GEMINI_MODEL}` |
| Date | 2026-05-18 |
| Role | Phase 4 span-level voice-segmentation fallback: classifies unclassified span intervals between Layer 1 regex hits |
| Budget | {LLM_BUDGET} calls (hard cap enforced in script) |
| Calls used | {_llm_call_count} |
| Errors | {len(_llm_errors)} |
| Script | `src/voice_segmentation_v3_span.py` |
| Per-call log | `deliverables/phase_4_voice_segmentation/llm_call_log_v3_span.jsonl` |
| Output corpus | `data/pass1b_canonical_voice_spans.csv` |

### Invocation pattern

```python
result = subprocess.run(
    ["gemini.cmd", "-m", "{GEMINI_MODEL}"],
    input=prompt,
    capture_output=True,
    text=True,
    timeout=60,
    encoding="utf-8",
    errors="replace",
)
```

Prompt passed via stdin.  stderr discarded.  Response compared against three
valid label strings (stripped); exact match → `high` confidence; label present
with extra text → `medium`; no valid label → interval defaults to
`User_Original_Content / low`.

### Prompt template (verbatim)

```
You are classifying a TEXT FRAGMENT extracted from a Reddit post or comment
about Claude AI.
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or
User_Original_Content.

Direct_Quote_Of_Model: the fragment quotes Claude/AI verbatim.
  Examples: "> Now go to sleep", "Claude: that is a good place to leave"
Paraphrase_Of_Model: the fragment reports or paraphrases what Claude/AI said.
  Examples: "Claude told me to go to bed", "it kept insisting I take a break"
User_Original_Content: the fragment contains no AI speech at all.
  Examples: "I worked all night", "anyone else notice this?"

If negated attribution (e.g. "it never told me to sleep"), choose
User_Original_Content.
Reply with ONLY the label name, no other text.

Text fragment: {{text}}
```

### Scope

Applied only to floor-defaulted span intervals (those not reached by the Layer 1
regex) that are >= 30 characters in length.  Short gaps (punctuation, whitespace)
are not sent to Gemini.  The {LLM_BUDGET}-call budget is applied sequentially
across rows in corpus order until exhausted.

### §9.2 compliance note

Gemini output is treated as tool output subject to §9.3 hand-validation.  A 50-item
stratified row-level validation sample was produced at
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3_span.csv`.
Downstream construct claims must not be drawn from v3 output before the researcher
completes hand-validation of the span breakdowns.
"""

    with open(LLM_TOOL_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"LLM tool log updated: {LLM_TOOL_LOG.name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 4 Voice Segmentation — v3 Span-Level")
    print("=" * 60)

    # Run segmentation
    all_span_dicts = run_v3_span_segmentation()

    # Load input rows for downstream analysis
    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as fin:
        rows_input = list(csv.DictReader(fin))

    # Compute statistics
    stats = compute_summary(rows_input, all_span_dicts)

    # Write validation sample
    prepare_validation_sample(rows_input, all_span_dicts, VALIDATION_SAMPLE)

    # Write summary markdown
    write_summary_md(stats, SUMMARY_MD)

    # Update LLM tool log
    append_llm_tool_log()

    # Console report
    rf = stats["reliable_fraction"]
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Total spans produced : {stats['total_spans']}")
    print(f"  Total corpus chars   : {stats['total_chars']:,}")
    print(f"  Label distribution:")
    for lbl in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER, LABEL_UNCLEAR]:
        sc = stats['label_span_counts'].get(lbl, 0)
        cc = stats['label_char_counts'].get(lbl, 0)
        pct = f"{100*cc/stats['total_chars']:.1f}%" if stats['total_chars'] else "n/a"
        print(f"    {lbl}: {sc} spans, {cc:,} chars ({pct})")
    print(f"  Reliable-segmentation fraction: {rf:.3f} ({rf*100:.1f}%)")
    threshold_str = "MEETS" if rf >= 0.70 else "DOES NOT MEET"
    print(f"  §C.4 threshold (70%): {threshold_str}")
    print(f"  Gemini calls used    : {_llm_call_count}")
    print(f"\n  Output spans CSV     : {OUTPUT_SPANS}")
    print(f"  Validation sample    : {VALIDATION_SAMPLE}")
    print(f"  Summary markdown     : {SUMMARY_MD}")
    print(f"  LLM call log         : {LLM_LOG_V3}")
