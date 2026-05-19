"""
voice_segmentation_v2.py
Phase 4 — Voice Segmentation  [method §C.4]
Sleep-nudge Pass 1b canonical corpus

Purpose
-------
Separate model-attributed speech from user speech in 773 rows of unstructured
Reddit discourse.  Outputs a three-way voice label per row:

    Direct_Quote_Of_Model   — user is quoting the model's words verbatim
    Paraphrase_Of_Model     — user is summarising or paraphrasing model output
    User_Original_Content   — user is speaking in their own voice only

plus a confidence tag (high / medium / low) that feeds the §C.4 decision rule.

Changes from v1
---------------
v1 used claude-haiku-4-5 via the Anthropic SDK as the LLM fallback.  All 100
fallback calls failed because ANTHROPIC_API_KEY was not set in the execution
environment.  v2 replaces that fallback with Gemini CLI 0.42.0
(model: gemini-3.1-flash-lite), invoked via subprocess.run with a 60-second
timeout per call.  The regex layer (Layers 1a, 1b, 1c) is reproduced verbatim
from v1.  Outputs are saved to separate v2 filenames; v1 outputs are preserved
for provenance.

Architecture
------------
Layer 1a — Strong-signal regex (§9.1): explicit markers (blockquotes, attribution
            phrases with quotation marks, speaker-label conventions).  Any match
            here assigns high confidence.

Layer 1b — Paraphrase-signal regex (§9.1 extended): corpus-specific paraphrase
            vocabulary derived from KWIC inspection of the Pass 1b Phase 2 notes
            and the Round 1 positive cases.  Matches assign medium confidence.

Layer 1c — Weak-signal heuristic: low-confidence patterns for the regex residual.

Layer 2  — Gemini CLI fallback (§9.2): targets a STRATIFIED RANDOM SAMPLE of the
            low-confidence tail (rows where Layer 1 did not fire decisively, i.e.,
            voice_confidence == low from regex layer).  Budget: <= 100 calls.
            Rows already labeled high or medium confidence by the regex layer are
            skipped.
            Model: gemini-3.1-flash-lite via Gemini CLI 0.42.0.
            Invocation: echo "<prompt>" | gemini.cmd -m gemini-3.1-flash-lite
            Rows not selected for LLM review default to User_Original_Content/low.

LLM call budget tracking
-------------------------
Every Gemini call is logged to:
  deliverables/phase_4_voice_segmentation/llm_call_log_v2.jsonl
with fields: row_id, model, cli_version, prompt_text, raw_response,
             assigned_label, assigned_confidence, elapsed_seconds,
             timestamp, call_number.
The log is the audit-trail record of the LLM's role (tool, not validator).

Design date: 2026-05-18

Usage
-----
    python src/voice_segmentation_v2.py

Outputs (all relative to repo root)
-------------------------------------
    data/pass1b_canonical_voice_segmented_v2.csv
    deliverables/phase_4_voice_segmentation/llm_call_log_v2.jsonl
    deliverables/phase_4_voice_segmentation/confidence_distribution_v2.csv
    notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v2.csv
    notebooks/audit_trail/phase_4_v1_vs_v2_label_shifts.csv
"""

import csv
import json
import re
import random
import datetime
import subprocess
import time
from pathlib import Path
from typing import Tuple, List, Dict
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV   = REPO_ROOT / "data" / "pass1b_canonical.csv"
OUTPUT_CSV  = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented_v2.csv"
V1_CSV      = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented.csv"

DELIVERABLES_DIR = REPO_ROOT / "deliverables" / "phase_4_voice_segmentation"
LLM_LOG   = DELIVERABLES_DIR / "llm_call_log_v2.jsonl"
CONF_DIST = DELIVERABLES_DIR / "confidence_distribution_v2.csv"

AUDIT_DIR = REPO_ROOT / "notebooks" / "audit_trail"
VALIDATION_SAMPLE_V2 = AUDIT_DIR / "phase_4_voice_segmentation_validation_sample_v2.csv"
LABEL_SHIFTS_CSV     = AUDIT_DIR / "phase_4_v1_vs_v2_label_shifts.csv"

DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Clear any previous v2 LLM log before a fresh run
if LLM_LOG.exists():
    LLM_LOG.unlink()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LABEL_DIRECT    = "Direct_Quote_Of_Model"
LABEL_PARAPHRASE = "Paraphrase_Of_Model"
LABEL_USER      = "User_Original_Content"

CONF_HIGH = "high"
CONF_MED  = "medium"
CONF_LOW  = "low"

LLM_BUDGET   = 100
GEMINI_CMD   = "gemini.cmd"          # Windows npm-installed binary
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_CLI_VERSION = "0.42.0"
CALL_TIMEOUT = 60                    # seconds per call

# ---------------------------------------------------------------------------
# Gemini prompt template
# ---------------------------------------------------------------------------
# Tight classification prompt: examples of each class, label-only response,
# then the row text.

GEMINI_PROMPT_TEMPLATE = """\
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or User_Original_Content.

Direct_Quote_Of_Model: author quotes AI verbatim. Example: 'Claude: go to bed' or '> Now go to sleep' or it said "that is a good place to leave"
Paraphrase_Of_Model: author paraphrases/reports what AI said or did. Example: 'Claude told me to go to bed' or 'it kept insisting I take a break' or 'my Claude tells me to stop'
User_Original_Content: no AI speech at all. Example: 'I worked all night' or 'anyone else notice this?' or just general commentary

If negated attribution (e.g. 'it never told me to sleep'), choose User_Original_Content.
Reply with ONLY the label name, no other text.

Text: {text}"""

# ---------------------------------------------------------------------------
# Layer 1a — Strong-signal regex (direct quote markers)
# VERBATIM from voice_segmentation_v1.py
# ---------------------------------------------------------------------------
_DQ_PATTERNS = [
    (re.compile(r'(?:^|\n)[ \t]*(?:>|&gt;)\s*\S', re.M),
     LABEL_DIRECT, CONF_HIGH, "blockquote_marker"),

    (re.compile(
        r'(?:claude|the\s+model|it|the\s+ai|the\s+assistant|claude\s+code)\s+'
        r'(?:said|wrote|replied|responded|told\s+me|told\s+us|stated|added)\s*'
        r'(?:something\s+like\s*)?["""''""]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_open_quote"),

    (re.compile(r'(?im)^(?:claude|model|ai|assistant)\s*:\s*\S'),
     LABEL_DIRECT, CONF_HIGH, "standalone_speaker_label"),

    (re.compile(r'(?i)claude\s*:[""""]'),
     LABEL_DIRECT, CONF_HIGH, "speaker_label_colon_quote"),

    (re.compile(
        r'(?:claude|the\s+model|the\s+ai|it)\s+'
        r'(?:said|told\s+me|wrote|replied|responded)\s+'
        r'[""""][^""""]{5,200}[""""]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_quoted_block"),
]

# ---------------------------------------------------------------------------
# Layer 1b — Paraphrase-signal regex (corpus-specific vocabulary)
# VERBATIM from voice_segmentation_v1.py
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Layer 1c — Weak-signal heuristic
# VERBATIM from voice_segmentation_v1.py
# ---------------------------------------------------------------------------
_WEAK_PM_PATTERNS = [
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
        r'(?:claude|it|the\s+model)\s+(?:is|was)\s+like\s+[""""]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_LOW, "weak_is_like_with_quote"),
]

# ---------------------------------------------------------------------------
# Utility: apply Layer 1 patterns
# ---------------------------------------------------------------------------

def _apply_layer1(text: str) -> Tuple[str, str, str]:
    """
    Returns (label, confidence, pattern_note).
    Returns ("ambiguous", "low", "no_match") if no pattern fires.
    """
    for pattern, label, conf, note in _DQ_PATTERNS:
        if pattern.search(text):
            return label, conf, note
    for pattern, label, conf, note in _PM_PATTERNS:
        if pattern.search(text):
            return label, conf, note
    for pattern, label, conf, note in _WEAK_PM_PATTERNS:
        if pattern.search(text):
            return label, conf, note
    return "ambiguous", CONF_LOW, "no_match"


# ---------------------------------------------------------------------------
# Layer 2 — Gemini CLI fallback
# ---------------------------------------------------------------------------

llm_call_count = 0
llm_errors = []


def _call_gemini(text: str, row_id: str) -> Tuple[str, str]:
    """
    Call gemini-3.1-flash-lite via CLI subprocess.
    Returns (label, confidence).
    Logs every call.  On any error returns (User_Original_Content, low).

    Invocation: echo <prompt> | gemini.cmd -m gemini-3.1-flash-lite
    Startup noise (true-color warnings, MCP schema messages, ripgrep messages)
    is suppressed via stderr=subprocess.DEVNULL.  Clean label extraction strips
    whitespace and validates against the three allowed labels.
    """
    global llm_call_count

    text_excerpt = (text or "")[:2000]
    prompt = GEMINI_PROMPT_TEMPLATE.format(text=text_excerpt)
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
        raw_stderr = result.stderr.strip() if result.stderr else ""

        # Filter startup noise from stdout (lines that are warning/info messages)
        # Gemini CLI sometimes emits warnings to stdout on Windows
        noise_patterns = [
            "true-color", "ripgrep", "mcp", "schema", "warning", "info:",
            "debug:", "note:", "loaded", "connecting", "initializ"
        ]
        clean_lines = []
        for line in raw_stdout.splitlines():
            line_lower = line.lower().strip()
            if any(np in line_lower for np in noise_patterns):
                continue
            if line.strip():
                clean_lines.append(line.strip())
        raw_clean = " ".join(clean_lines).strip() if clean_lines else raw_stdout

        # Extract label: find first occurrence of a valid label token
        valid_labels = {LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER}
        label = None
        confidence = CONF_LOW

        for candidate in valid_labels:
            if candidate.lower() in raw_clean.lower():
                label = candidate
                break

        if label is None:
            # No valid label found; default to UC/low
            label = LABEL_USER
            confidence = CONF_LOW
            error_note = f"no_valid_label_in_response: '{raw_clean[:100]}'"
            llm_errors.append({"row_id": row_id, "error": error_note,
                                "call_number": llm_call_count + 1})
        else:
            # Assign confidence based on how clean the response is:
            # If the response is exactly the label (or label + punctuation), high.
            # If label is present but surrounded by other text, medium.
            stripped = raw_clean.strip().rstrip(".")
            if stripped == label:
                confidence = CONF_HIGH
            else:
                confidence = CONF_MED

        elapsed = round(time.monotonic() - t_start, 2)
        error_flag = ""

    except subprocess.TimeoutExpired:
        elapsed = CALL_TIMEOUT
        label = LABEL_USER
        confidence = CONF_LOW
        raw_clean = "TIMEOUT"
        error_flag = "timeout"
        llm_errors.append({"row_id": row_id, "error": "timeout",
                            "call_number": llm_call_count + 1})

    except Exception as e:
        elapsed = round(time.monotonic() - t_start, 2)
        label = LABEL_USER
        confidence = CONF_LOW
        raw_clean = f"ERROR: {e}"
        error_flag = str(e)
        llm_errors.append({"row_id": row_id, "error": str(e),
                            "call_number": llm_call_count + 1})

    llm_call_count += 1

    log_entry = {
        "call_number": llm_call_count,
        "row_id": row_id,
        "tool": "Gemini CLI",
        "cli_version": GEMINI_CLI_VERSION,
        "model": GEMINI_MODEL,
        "prompt_text_excerpt": prompt[:500],
        "input_text_excerpt": (text or "")[:200],
        "raw_response": raw_clean[:500],
        "assigned_label": label,
        "assigned_confidence": confidence,
        "elapsed_seconds": elapsed,
        "error": error_flag if error_flag else None,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(LLM_LOG, "a", encoding="utf-8") as flog:
        flog.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return label, confidence


# ---------------------------------------------------------------------------
# Main segmenter
# ---------------------------------------------------------------------------

def run_segmentation(input_path: Path, output_path: Path) -> List[Dict]:
    """
    Two-pass segmentation:
      Pass 1 — Layer 1 regex on all rows.  Record which are low-confidence.
      Pass 2 — Gemini CLI fallback on a STRATIFIED RANDOM SAMPLE of low-conf rows
               (proportional post/comment allocation, budget <= 100).
               Rows already labeled high or medium confidence are skipped.
               Remaining low-conf rows default to User_Original_Content/low.
      Write output CSV with voice_label, voice_confidence, voice_source columns.
    """
    with open(input_path, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    n = len(rows)
    print(f"Loaded {n} rows from {input_path.name}")

    # --- Pass 1: regex ---
    results = {}  # index -> (label, confidence, note, source)
    low_conf_indices = []  # eligible for LLM fallback

    for i, row in enumerate(rows):
        text = row.get("body", "") or ""
        label, conf, note = _apply_layer1(text)
        if label == "ambiguous":
            low_conf_indices.append(i)
            results[i] = (LABEL_USER, CONF_LOW, note, "regex_default")
        elif conf == CONF_LOW:
            # Layer 1c fired but with low confidence — eligible for upgrade
            low_conf_indices.append(i)
            results[i] = (label, conf, note, "regex_low")
        else:
            # High or medium confidence from regex — skip LLM
            results[i] = (label, conf, note, "regex")

    n_low = len(low_conf_indices)
    n_regex_high_med = n - n_low
    print(f"  Regex high/medium coverage: {n_regex_high_med}/{n} rows ({100*n_regex_high_med/n:.1f}%)")
    print(f"  Low-confidence (eligible for LLM): {n_low} rows")
    print(f"  LLM budget: {LLM_BUDGET} calls")

    # --- Stratified sample of low-conf rows for Gemini fallback ---
    if n_low > 0 and LLM_BUDGET > 0:
        low_posts    = [i for i in low_conf_indices if rows[i]["type"] == "post"]
        low_comments = [i for i in low_conf_indices if rows[i]["type"] == "comment"]
        prop_posts   = len(low_posts) / n_low if n_low > 0 else 0
        n_posts_llm  = max(1, round(LLM_BUDGET * prop_posts)) if low_posts else 0
        n_comments_llm = LLM_BUDGET - n_posts_llm

        if n_posts_llm > len(low_posts):
            n_posts_llm = len(low_posts)
            n_comments_llm = min(LLM_BUDGET - n_posts_llm, len(low_comments))
        if n_comments_llm > len(low_comments):
            n_comments_llm = len(low_comments)
            n_posts_llm = min(LLM_BUDGET - n_comments_llm, len(low_posts))

        random.seed(42)
        llm_sample_posts    = random.sample(low_posts,    n_posts_llm)
        llm_sample_comments = random.sample(low_comments, n_comments_llm)
        llm_indices = set(llm_sample_posts + llm_sample_comments)

        print(f"  LLM sample: {len(llm_indices)} rows "
              f"({n_posts_llm} posts, {n_comments_llm} comments)")
    else:
        llm_indices = set()
        print("  No low-confidence rows to send to LLM.")

    # --- Pass 2: Gemini CLI on sample ---
    for call_num, i in enumerate(sorted(llm_indices), 1):
        row  = rows[i]
        text = row.get("body", "") or ""
        row_id = row.get("post_id", "") + "|" + row.get("comment_id", "")

        if llm_call_count >= LLM_BUDGET:
            print(f"  [Budget cap reached at {LLM_BUDGET} calls; halting LLM fallback]")
            break

        label, conf = _call_gemini(text, row_id)
        # Determine source string to distinguish from regex-only rows
        prev_source = results[i][3]
        new_source = f"gemini_fallback"
        results[i] = (label, conf, "gemini_fallback", new_source)

        if call_num % 10 == 0:
            print(f"    ... {call_num} Gemini calls complete ({llm_call_count} total)")

    print(f"\nSegmentation complete.  Gemini calls used: {llm_call_count}")
    if llm_errors:
        print(f"  Errors: {len(llm_errors)} call(s) errored or timed out")
    print(f"Output: {output_path}")

    # --- Write output ---
    out_fieldnames = fieldnames + ["voice_label", "voice_confidence", "voice_source"]
    with open(output_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=out_fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows):
            label, conf, note, source = results[i]
            row["voice_label"]      = label
            row["voice_confidence"] = conf
            row["voice_source"]     = source
            writer.writerow(row)

    # Reload for downstream use
    with open(output_path, newline="", encoding="utf-8") as f:
        rows_out = list(csv.DictReader(f))
    return rows_out


# ---------------------------------------------------------------------------
# Confidence distribution
# ---------------------------------------------------------------------------

def compute_confidence_distribution(rows_out: List[Dict], output_path: Path):
    """Stratified confidence distribution table (type x voice_label x confidence)."""
    counts: Counter = Counter()
    for row in rows_out:
        key = (row["type"], row["voice_label"], row["voice_confidence"])
        counts[key] += 1

    total = len(rows_out)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "voice_label", "voice_confidence",
                         "n", "pct_of_total"])
        for (stratum, label, conf), n in sorted(counts.items()):
            writer.writerow([stratum, label, conf, n,
                             round(100 * n / total, 2)])

    print("\n--- Confidence distribution v2 (stratified) ---")
    conf_totals: Dict = defaultdict(int)
    label_totals: Dict = defaultdict(int)
    type_totals:  Dict = defaultdict(int)

    for row in rows_out:
        conf_totals[row["voice_confidence"]] += 1
        label_totals[row["voice_label"]] += 1
        type_totals[row["type"]] += 1

    print("  By confidence:")
    for conf in [CONF_HIGH, CONF_MED, CONF_LOW]:
        n = conf_totals[conf]
        print(f"    {conf:6}: {n:4}/{total} ({100*n/total:5.1f}%)")
    high_med = conf_totals[CONF_HIGH] + conf_totals[CONF_MED]
    print(f"    high+medium (reliably segmentable): "
          f"{high_med}/{total} ({100*high_med/total:.1f}%)")

    print("  By voice label:")
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = label_totals[label]
        print(f"    {label}: {n}/{total} ({100*n/total:.1f}%)")

    print("  By stratum:")
    for stratum in ["post", "comment"]:
        n = type_totals[stratum]
        print(f"    {stratum}: {n} rows")

    print("  Per-stratum voice label (posts):")
    post_rows = [r for r in rows_out if r["type"] == "post"]
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = sum(1 for r in post_rows if r["voice_label"] == label)
        print(f"    {label}: {n}/{len(post_rows)} ({100*n/len(post_rows):.1f}%)")

    print("  Per-stratum voice label (comments):")
    comment_rows = [r for r in rows_out if r["type"] == "comment"]
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = sum(1 for r in comment_rows if r["voice_label"] == label)
        print(f"    {label}: {n}/{len(comment_rows)} ({100*n/len(comment_rows):.1f}%)")

    return conf_totals, label_totals, high_med, total


# ---------------------------------------------------------------------------
# V1 vs V2 comparison table
# ---------------------------------------------------------------------------

def build_label_shift_table(v1_path: Path, v2_rows: List[Dict],
                             output_path: Path):
    """
    Row-by-row comparison of v1 and v2 labels.
    Uses post_id + comment_id as join key.
    """
    if not v1_path.exists():
        print(f"  [Warning] v1 output not found at {v1_path}; skipping shift table.")
        return {}

    # Load v1 keyed by row identifier
    v1_by_key = {}
    with open(v1_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = row.get("post_id", "") + "|" + row.get("comment_id", "")
            v1_by_key[key] = row

    conf_order = {CONF_LOW: 0, CONF_MED: 1, CONF_HIGH: 2}

    shift_rows = []
    for row in v2_rows:
        key = row.get("post_id", "") + "|" + row.get("comment_id", "")
        v1 = v1_by_key.get(key)
        if not v1:
            continue
        v1_label = v1.get("voice_label", "")
        v1_conf  = v1.get("voice_confidence", "")
        v2_label = row.get("voice_label", "")
        v2_conf  = row.get("voice_confidence", "")
        label_changed = (v1_label != v2_label)
        conf_delta = (conf_order.get(v2_conf, 0) -
                      conf_order.get(v1_conf,  0))
        shift_rows.append({
            "row_id":      key,
            "type":        row.get("type", ""),
            "v1_label":    v1_label,
            "v1_conf":     v1_conf,
            "v2_label":    v2_label,
            "v2_conf":     v2_conf,
            "label_changed": label_changed,
            "conf_delta":  conf_delta,
            "v1_source":   v1.get("voice_source", ""),
            "v2_source":   row.get("voice_source", ""),
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "row_id", "type", "v1_label", "v1_conf",
            "v2_label", "v2_conf", "label_changed", "conf_delta",
            "v1_source", "v2_source",
        ])
        writer.writeheader()
        writer.writerows(shift_rows)

    # Aggregate stats
    n_label_changed = sum(1 for r in shift_rows if r["label_changed"])
    n_conf_up   = sum(1 for r in shift_rows if r["conf_delta"] > 0)
    n_conf_down = sum(1 for r in shift_rows if r["conf_delta"] < 0)
    n_conf_same = sum(1 for r in shift_rows if r["conf_delta"] == 0)

    print(f"\n--- V1 vs V2 label shift summary ---")
    print(f"  Rows compared: {len(shift_rows)}")
    print(f"  Label changed: {n_label_changed} ({100*n_label_changed/len(shift_rows):.1f}%)")
    print(f"  Confidence upgraded: {n_conf_up}")
    print(f"  Confidence downgraded: {n_conf_down}")
    print(f"  Confidence unchanged: {n_conf_same}")

    # Detailed label-shift matrix
    shift_matrix: Counter = Counter()
    for r in shift_rows:
        shift_matrix[(r["v1_label"][:3], r["v2_label"][:3])] += 1
    print("  Shift matrix (v1 -> v2, label[:3]):")
    for (a, b), cnt in sorted(shift_matrix.items()):
        print(f"    {a} -> {b}: {cnt}")

    return {"n_label_changed": n_label_changed, "n_conf_up": n_conf_up,
            "n_conf_down": n_conf_down, "n_conf_same": n_conf_same,
            "n_total": len(shift_rows)}


# ---------------------------------------------------------------------------
# Validation sample v2
# ---------------------------------------------------------------------------

def prepare_validation_sample(rows_out: List[Dict], output_path: Path,
                               seed: int = 42):
    """
    Stratified hand-validation sample (§9.3).  70 items total:
      20 Direct_Quote_Of_Model
      20 Paraphrase_Of_Model
      20 User_Original_Content
      10 low-confidence (any label, de-duplicated from above)
    Each class is stratified by type (post/comment).
    """
    random.seed(seed)

    def stratum_sample(pool, n):
        if not pool or n <= 0:
            return []
        posts    = [r for r in pool if r["type"] == "post"]
        comments = [r for r in pool if r["type"] == "comment"]
        if not posts:
            return random.sample(comments, min(n, len(comments)))
        if not comments:
            return random.sample(posts, min(n, len(posts)))
        n_posts = max(1, round(n * len(posts) / len(pool)))
        n_comments = n - n_posts
        if n_posts > len(posts):
            n_posts = len(posts)
            n_comments = min(n - n_posts, len(comments))
        if n_comments > len(comments):
            n_comments = len(comments)
            n_posts = min(n - n_comments, len(posts))
        return (random.sample(posts, n_posts) +
                random.sample(comments, n_comments))

    by_label = {LABEL_DIRECT: [], LABEL_PARAPHRASE: [], LABEL_USER: []}
    low_conf = []
    for row in rows_out:
        lbl  = row.get("voice_label")
        conf = row.get("voice_confidence")
        if lbl in by_label:
            by_label[lbl].append(row)
        if conf == CONF_LOW:
            low_conf.append(row)

    sampled_ids: set = set()
    sample_rows = []

    def add_pool(pool, n):
        chosen = stratum_sample(pool, n)
        for r in chosen:
            rid = r["post_id"] + "|" + r.get("comment_id", "")
            if rid not in sampled_ids:
                sampled_ids.add(rid)
                sample_rows.append(r)

    add_pool(by_label[LABEL_DIRECT],    20)
    add_pool(by_label[LABEL_PARAPHRASE], 20)
    add_pool(by_label[LABEL_USER],       20)
    add_pool(low_conf,                   10)

    sample_rows.sort(key=lambda r: (r["type"], r["voice_label"]))

    out_fieldnames = [
        "row_id", "post_id", "type", "retrieval_provenance", "full_text",
        "predicted_voice_label", "predicted_confidence",
        "researcher_label", "researcher_notes",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        for row in sample_rows:
            rid  = row["post_id"] + "|" + row.get("comment_id", "")
            body = (row.get("body", "") or "").replace("\n", " | ")
            writer.writerow({
                "row_id":               rid,
                "post_id":              row["post_id"],
                "type":                 row["type"],
                "retrieval_provenance": row.get("retrieval_provenance", ""),
                "full_text":            body,
                "predicted_voice_label":   row["voice_label"],
                "predicted_confidence":    row["voice_confidence"],
                "researcher_label":     "",
                "researcher_notes":     "",
            })

    n_dq = sum(1 for r in sample_rows if r["voice_label"] == LABEL_DIRECT)
    n_pm = sum(1 for r in sample_rows if r["voice_label"] == LABEL_PARAPHRASE)
    n_uc = sum(1 for r in sample_rows if r["voice_label"] == LABEL_USER)
    n_lc = sum(1 for r in sample_rows if r["voice_confidence"] == CONF_LOW)
    print(f"\nValidation sample v2: {len(sample_rows)} items")
    print(f"  Direct_Quote: {n_dq}  Paraphrase: {n_pm}  "
          f"User_Content: {n_uc}  Low-conf: {n_lc}")
    print(f"  Written to: {output_path.name}")
    return sample_rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rows_out = run_segmentation(INPUT_CSV, OUTPUT_CSV)
    conf_totals, label_totals, high_med, total = \
        compute_confidence_distribution(rows_out, CONF_DIST)

    shift_stats = build_label_shift_table(V1_CSV, rows_out, LABEL_SHIFTS_CSV)

    prepare_validation_sample(rows_out, VALIDATION_SAMPLE_V2)

    print("\nPhase 4 v2 voice segmentation complete.")
    print(f"  Segmented corpus : {OUTPUT_CSV}")
    print(f"  Confidence dist  : {CONF_DIST}")
    print(f"  Validation sample: {VALIDATION_SAMPLE_V2}")
    print(f"  LLM call log     : {LLM_LOG}")
    print(f"  Label shift table: {LABEL_SHIFTS_CSV}")
    print(f"  Reliable fraction: {high_med}/{total} "
          f"({100*high_med/total:.1f}%) at high+medium confidence")
    print(f"  Gemini calls used: {llm_call_count}")
    if llm_errors:
        print(f"  Call errors:       {len(llm_errors)}")
