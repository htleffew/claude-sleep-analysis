"""
voice_segmentation_v1.py
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

Architecture
------------
Layer 1a — Strong-signal regex (§9.1): explicit markers (blockquotes, attribution
            phrases with quotation marks, speaker-label conventions).  Any match
            here assigns high confidence.

Layer 1b — Paraphrase-signal regex (§9.1 extended): corpus-specific paraphrase
            vocabulary derived from KWIC inspection of the Pass 1b Phase 2 notes
            and the Round 1 positive cases.  Matches assign medium confidence.

Layer 2  — LLM-assisted fallback (§9.2): targets a STRATIFIED RANDOM SAMPLE of
            the regex-residual rows.  Budget: <= 100 calls total.  The sample is
            drawn before the loop so the budget is allocated across the full
            corpus rather than exhausted on the first ambiguous rows.
            Model: claude-haiku-4-5 via the Anthropic SDK.
            Rows not selected for LLM review default to User_Original_Content/low.

Stratification (Phase 3 decision)
----------------------------------
The Phase 3 unit decision requires segmentation to respect the post / comment
stratum.  `type` is carried through untouched.  Confidence distribution tables
are reported per stratum.  LLM budget is allocated proportionally between
posts (242) and comments (531).

LLM call budget tracking
-------------------------
Every LLM call is logged to:
  deliverables/phase_4_voice_segmentation/llm_call_log.jsonl
with fields: row_id, model, prompt_system, prompt_user, raw_response,
             assigned_label, assigned_confidence, timestamp, call_number.
The log is the audit-trail record of the LLM's role (tool, not validator).

LLM model used
--------------
    claude-haiku-4-5  (cheapest Anthropic hosted Haiku; appropriate for
    ternary classification on short texts under single-operator budget)
Design date: 2026-05-17

Usage
-----
    python src/voice_segmentation_v1.py

Outputs (all relative to repo root)
-------------------------------------
    data/pass1b_canonical_voice_segmented.csv
    deliverables/phase_4_voice_segmentation/llm_call_log.jsonl
    deliverables/phase_4_voice_segmentation/confidence_distribution.csv
"""

import csv
import json
import re
import random
import datetime
from pathlib import Path
from typing import Tuple, Optional, List, Dict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV  = REPO_ROOT / "data" / "pass1b_canonical.csv"
OUTPUT_CSV = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented.csv"
DELIVERABLES_DIR = REPO_ROOT / "deliverables" / "phase_4_voice_segmentation"
LLM_LOG   = DELIVERABLES_DIR / "llm_call_log.jsonl"
CONF_DIST = DELIVERABLES_DIR / "confidence_distribution.csv"

DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)

# Clear any previous LLM log before a fresh run
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

LLM_BUDGET = 100     # hard cap on total fallback calls for the run
LLM_MODEL  = "claude-haiku-4-5"

# ---------------------------------------------------------------------------
# Layer 1a — Strong-signal regex (direct quote markers)
# ---------------------------------------------------------------------------
# Each entry: (compiled_regex, label, confidence, pattern_note)
# These fire first; any match returns high confidence.

_DQ_PATTERNS = [
    # Reddit blockquote lines (> at line start)
    (re.compile(r'(?:^|\n)[ \t]*(?:>|&gt;)\s*\S', re.M),
     LABEL_DIRECT, CONF_HIGH, "blockquote_marker"),

    # Explicit attribution + open quotation mark
    # e.g.  Claude said "go to bed"  /  it told me "you must rest"
    (re.compile(
        r'(?:claude|the\s+model|it|the\s+ai|the\s+assistant|claude\s+code)\s+'
        r'(?:said|wrote|replied|responded|told\s+me|told\s+us|stated|added)\s*'
        r'(?:something\s+like\s*)?["""‘’“”]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_open_quote"),

    # Speaker label on its own line: "Claude:" or "AI:" or "Model:"
    (re.compile(r'(?im)^(?:claude|model|ai|assistant)\s*:\s*\S'),
     LABEL_DIRECT, CONF_HIGH, "standalone_speaker_label"),

    # Inline colon-style attribution: "Claude: go to bed"
    (re.compile(r'(?i)claude\s*:["""“]'),
     LABEL_DIRECT, CONF_HIGH, "speaker_label_colon_quote"),

    # Quoted block with prior attribution (up to 200 chars in quotes)
    (re.compile(
        r'(?:claude|the\s+model|the\s+ai|it)\s+'
        r'(?:said|told\s+me|wrote|replied|responded)\s+'
        r'["""“][^"""”]{5,200}["""”]',
        re.IGNORECASE),
     LABEL_DIRECT, CONF_HIGH, "attribution_phrase_quoted_block"),
]

# ---------------------------------------------------------------------------
# Layer 1b — Paraphrase-signal regex (corpus-specific vocabulary)
# ---------------------------------------------------------------------------
# Derived from:
#   - KWIC Phase 2 notes (sleep, bed, rest, break, tired, tomorrow seeds)
#   - Round 1 positive cases (PC-01 through PC-25)
#   - Observed language in the low-confidence sample inspection
#
# Confidence is MED unless the signal is unusually specific (then HIGH).
# Order matters: more specific patterns first.

_PM_PATTERNS = [
    # "my claude tell/tells/told me" — very specific corpus pattern
    (re.compile(r'(?i)my\s+claude\s+(?:tells?|told)\s+me', re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "my_claude_tells_me"),

    # "mine is/keeps telling me" (Reddit idiom: "mine is telling me to go to bed")
    (re.compile(r'(?i)mine\s+(?:is\s+)?(?:telling|told|keeps?\s+telling)', re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "mine_is_telling"),

    # "it kept/keeps telling me to" / "it kept saying"
    (re.compile(
        r'(?:it|claude|the\s+model|the\s+ai)\s+'
        r'(?:kept|keeps|kept\s+on|keeps\s+on)\s+'
        r'(?:telling|saying|repeating|insisting|asking)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "kept_telling_me"),

    # Third-person model self-attribution:
    # "Claude said it needs to rest" / "it claimed it was tired"
    (re.compile(
        r'(?:claude|the\s+model|the\s+ai|the\s+assistant)\s+'
        r'(?:said|claimed|told\s+me|insisted|suggested)\s+'
        r'(?:it|she|he)\s+'
        r'(?:needs?|needed|was|is|had\s+to|wanted|couldn\'t?|would)\b',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "third_person_self_attribution"),

    # "Claude basically said/told" — hedged paraphrase marker
    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:basically|essentially|kind\s+of|sort\s+of|practically|literally)\s+'
        r'(?:said|told\s+me|told\s+us|suggested|implied|stated|informed\s+me)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "basically_said"),

    # "it sent me to bed" / "claude put me to bed" / "sending me to bed"
    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:sent|put|pushed|forced|made|sending|putting|getting)\s+me\s+'
        r'(?:to\s+)?(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "sent_me_to_bed"),

    # Corpus-specific directive phrases attributed to model (no quotes needed)
    # Covers patterns like "claude told me to go to bed", "it said go to sleep"
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

    # "claude is like" / "claude was like" (Reddit reported-speech idiom)
    (re.compile(
        r'(?:claude|the\s+model|the\s+ai)\s+(?:is|was|were)\s+like\b',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "is_like_reported_speech"),

    # "and then it said" / "at which point claude said" — narrative reconstruction
    (re.compile(
        r'(?:and\s+then|then|after\s+that|at\s+which\s+point|so|whereupon)\s+'
        r'(?:claude|it|the\s+model|the\s+ai)\s+'
        r'(?:said|told|replied|responded|wrote|suggested|asked)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "narrative_reconstruction"),

    # "it decided I'm/I was procrastinating" — model judgment attribution
    (re.compile(
        r'(?:it|claude|the\s+model)\s+decides?\s+(?:I\'?m|I\s+was|that)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "model_judgment_attribution"),

    # "claude would" + model-behavior verb (repeated behavior paraphrase)
    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|the\s+assistant)\s+'
        r'(?:would|will|does|doesn\'t?|won\'t|wouldn\'t)\s+'
        r'(?:say|tell\s+me|suggest|insist|refuse|push|encourage|prompt|ask)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "would_say"),

    # Corpus-specific phrases directly attested in PC-01 through PC-25
    # and KWIC samples: "asking me to go to sleep", "tells you to go to bed", etc.
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

    # Tells you/me to go to sleep/bed (common community report phrasing)
    (re.compile(
        r'(?:tells?\s+(?:you|me|us)\s+to\s+go\s+to\s+(?:bed|sleep)|'
        r'telling\s+(?:you|me|us)\s+to\s+go\s+to\s+(?:bed|sleep)|'
        r'told\s+(?:me|us|you)\s+to\s+go\s+to\s+(?:bed|sleep))',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "tells_me_to_go_to_bed"),

    # "claude telling its users to" (meta-report phrasing, PC-05/PC-06)
    (re.compile(
        r'claude\s+telling\s+(?:its\s+)?users?\s+to',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_HIGH, "claude_telling_users"),

    # "get some rest" / "go to bed" / "you should sleep" in reported speech
    # without explicit attribution — medium confidence (may be user quoting self)
    (re.compile(
        r'(?:constantly|keeps?|kept|always|again)\s+'
        r'(?:telling|saying|asking|suggesting|reminding)\s+'
        r'(?:me|us|you)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "repeated_attribution_adverb"),

    # "I asked claude to X and it Y" pattern
    (re.compile(
        r'(?:I\s+asked\s+(?:claude|it|the\s+model))\s+.{0,60}'
        r'(?:and\s+(?:it|claude|the\s+model))\s+'
        r'(?:said|told|replied|responded|wrote|suggested)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_MED, "i_asked_and_it_said"),
]

# ---------------------------------------------------------------------------
# Layer 1c — Weak-signal heuristic for corpus-specific patterns not covered above
# ---------------------------------------------------------------------------
# These patterns fire only on the regex residual (after 1a and 1b fail).
# Confidence is always LOW because these are present-tense or bare-assertion
# patterns with higher false-positive risk.
#
# Corpus evidence: many "ambiguous" rows contain patterns like:
#   "Claude always tries to put me to bed"
#   "it tells me to go to sleep"
#   "claude is always trying to X"
# which are paraphrase but don't match the more structural patterns above.

_WEAK_PM_PATTERNS = [
    # Present-tense habitual attribution (weak — may be user generalising,
    # not reporting a specific model utterance)
    (re.compile(
        r'(?:claude|it|the\s+model|the\s+ai|claude\s+code)\s+'
        r'(?:always|constantly|often|sometimes|never|still|just)\s+'
        r'(?:tries?\s+to|tells?\s+me\s+to|wants?\s+to|says?\s+to|asks?\s+me\s+to|'
        r'suggests?\s+|insists?\s+|refuses?\s+to)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_habitual_attribution"),

    # Bare "tells me/you to go to bed/sleep" without leading attribution marker
    (re.compile(
        r'(?:tells?\s+(?:me|you|us)|told\s+(?:me|you|us))\s+'
        r'to\s+go\s+to\s+(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_tells_me_go_to_bed"),

    # "goes to bed" / "going to sleep" idiom in model-behavior context
    (re.compile(
        r'(?:wants?\s+(?:me|you|us)\s+to|trying\s+to\s+(?:get|send|put)\s+'
        r'(?:me|you|us)\s+to)\s+(?:go\s+to\s+)?(?:bed|sleep)',
        re.IGNORECASE),
     LABEL_PARAPHRASE, CONF_LOW, "weak_wants_me_to_sleep"),

    # Reconstructed dialogue without attribution tag
    # e.g. "It's like 9am and Claude is like 'shut the laptop and go to bed'"
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

    Layer order:
      1a — strong-signal direct-quote markers (high confidence)
      1b — paraphrase-signal regex (high/medium confidence)
      1c — weak corpus-specific signals (low confidence; better than default)
    """
    # Layer 1a: strong direct-quote signals
    for pattern, label, conf, note in _DQ_PATTERNS:
        if pattern.search(text):
            return label, conf, note

    # Layer 1b: paraphrase signals
    for pattern, label, conf, note in _PM_PATTERNS:
        if pattern.search(text):
            return label, conf, note

    # Layer 1c: weak signals (low confidence)
    for pattern, label, conf, note in _WEAK_PM_PATTERNS:
        if pattern.search(text):
            return label, conf, note

    return "ambiguous", CONF_LOW, "no_match"


# ---------------------------------------------------------------------------
# Layer 2 — LLM-assisted fallback
# ---------------------------------------------------------------------------

LLM_SYSTEM_PROMPT = (
    "You are a discourse analyst classifying Reddit post or comment text by "
    "whether it contains model-attributed speech (i.e., language attributed to "
    "Claude or another AI model). You must pick exactly one label and one "
    "confidence level. Do not explain. Output valid JSON only, no markdown.\n\n"
    "Labels:\n"
    "  Direct_Quote_Of_Model — the author appears to be quoting the model's "
    "words verbatim (with or without quotation marks, including reconstructed "
    "dialogue).\n"
    "  Paraphrase_Of_Model — the author is summarising or paraphrasing what the "
    "model said or did, without verbatim quotation. Third-person attributions "
    "count (e.g. 'Claude told me to go to bed').\n"
    "  User_Original_Content — the text is entirely in the user's own voice; "
    "no model speech is attributed.\n\n"
    "Confidence levels:\n"
    "  high — clear signal, little room for doubt.\n"
    "  medium — plausible but some ambiguity remains.\n"
    "  low — genuinely ambiguous; the label is a best guess.\n\n"
    'Output format (JSON only): {"label": "<label>", "confidence": "<confidence>"}'
)

LLM_USER_TEMPLATE = (
    "Classify this Reddit text. Is the author quoting or paraphrasing an AI "
    "model, or is this the user's own voice?\n\n---\n{text}\n---\n\nJSON only."
)

llm_call_count = 0


def _call_llm(text: str, row_id: str) -> Tuple[str, str]:
    """
    Call claude-haiku-4-5 fallback.  Returns (label, confidence).
    Logs every call.  On any error returns (User_Original_Content, low).
    """
    global llm_call_count
    try:
        import anthropic
        client = anthropic.Anthropic()
        user_text = text[:2000]
        message = client.messages.create(
            model=LLM_MODEL,
            max_tokens=64,
            system=LLM_SYSTEM_PROMPT,
            messages=[{"role": "user",
                       "content": LLM_USER_TEMPLATE.format(text=user_text)}],
        )
        raw = message.content[0].text.strip()
        parsed = json.loads(raw)
        label = parsed.get("label", LABEL_USER)
        confidence = parsed.get("confidence", CONF_LOW)
        if label not in {LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER}:
            label = LABEL_USER
            confidence = CONF_LOW
        if confidence not in {CONF_HIGH, CONF_MED, CONF_LOW}:
            confidence = CONF_LOW
    except Exception as e:
        label = LABEL_USER
        confidence = CONF_LOW
        raw = f"ERROR: {e}"

    llm_call_count += 1
    log_entry = {
        "row_id": row_id,
        "model": LLM_MODEL,
        "prompt_system": LLM_SYSTEM_PROMPT,
        "prompt_user": LLM_USER_TEMPLATE.format(text=(text or "")[:500]),
        "raw_response": raw if isinstance(raw, str) else json.dumps(raw),
        "assigned_label": label,
        "assigned_confidence": confidence,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "call_number": llm_call_count,
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
      Pass 1 — Layer 1 regex on all rows.  Record which are ambiguous.
      Pass 2 — LLM fallback on a STRATIFIED RANDOM SAMPLE of ambiguous rows
               (proportional post/comment allocation, budget <= 100).
               Remaining ambiguous rows default to User_Original_Content/low.
      Write output CSV with voice_label and voice_confidence columns.
    """
    with open(input_path, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    n = len(rows)
    print(f"Loaded {n} rows from {input_path.name}")

    # --- Pass 1: regex ---
    results = {}  # index -> (label, confidence, note, source)
    ambiguous_indices = []

    for i, row in enumerate(rows):
        text = row.get("body", "") or ""
        label, conf, note = _apply_layer1(text)
        if label == "ambiguous":
            ambiguous_indices.append(i)
            results[i] = (LABEL_USER, CONF_LOW, note, "regex_default")
        else:
            results[i] = (label, conf, note, "regex")

    n_ambig = len(ambiguous_indices)
    n_regex_hit = n - n_ambig
    print(f"  Regex coverage: {n_regex_hit}/{n} rows ({100*n_regex_hit/n:.1f}%)")
    print(f"  Ambiguous (regex miss): {n_ambig} rows")
    print(f"  LLM budget: {LLM_BUDGET} calls")

    # --- Stratified sample of ambiguous rows for LLM ---
    if n_ambig > 0 and LLM_BUDGET > 0:
        ambig_posts = [i for i in ambiguous_indices if rows[i]["type"] == "post"]
        ambig_comments = [i for i in ambiguous_indices if rows[i]["type"] == "comment"]
        # Proportional allocation
        prop_posts = len(ambig_posts) / n_ambig
        n_posts_llm = max(1, round(LLM_BUDGET * prop_posts)) if ambig_posts else 0
        n_comments_llm = LLM_BUDGET - n_posts_llm
        if n_posts_llm > len(ambig_posts):
            n_posts_llm = len(ambig_posts)
            n_comments_llm = min(LLM_BUDGET - n_posts_llm, len(ambig_comments))
        if n_comments_llm > len(ambig_comments):
            n_comments_llm = len(ambig_comments)

        random.seed(42)
        llm_indices = set(
            random.sample(ambig_posts, n_posts_llm) +
            random.sample(ambig_comments, n_comments_llm)
        )
        print(f"  LLM sample: {len(llm_indices)} rows "
              f"({n_posts_llm} posts, {n_comments_llm} comments)")
    else:
        llm_indices = set()

    # --- Pass 2: LLM on sample ---
    for i in sorted(llm_indices):
        row = rows[i]
        text = row.get("body", "") or ""
        row_id = row.get("post_id", "") + "|" + row.get("comment_id", "")
        label, conf = _call_llm(text, row_id)
        results[i] = (label, conf, "llm_fallback", "llm")

    # --- Write output ---
    out_fieldnames = fieldnames + ["voice_label", "voice_confidence", "voice_source"]
    with open(output_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=out_fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows):
            label, conf, note, source = results[i]
            row["voice_label"] = label
            row["voice_confidence"] = conf
            row["voice_source"] = source
            writer.writerow(row)

    print(f"\nSegmentation complete.  LLM calls used: {llm_call_count}")
    print(f"Output: {output_path}")

    # Reload for downstream use
    with open(output_path, newline="", encoding="utf-8") as f:
        rows_out = list(csv.DictReader(f))
    return rows_out


def compute_confidence_distribution(rows_out: List[Dict], output_path: Path):
    """Stratified confidence distribution table (type x voice_label x confidence)."""
    from collections import Counter
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

    # Print summary
    print("\n--- Confidence distribution (stratified) ---")
    from collections import defaultdict
    conf_totals: Dict = defaultdict(int)
    label_totals: Dict = defaultdict(int)
    type_totals: Dict = defaultdict(int)
    llm_totals: Dict = defaultdict(int)

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

    # Per-stratum breakdown of voice label
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
        lbl = row.get("voice_label")
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
            rid = row["post_id"] + "|" + row.get("comment_id", "")
            body = (row.get("body", "") or "").replace("\n", " | ")
            writer.writerow({
                "row_id": rid,
                "post_id": row["post_id"],
                "type": row["type"],
                "retrieval_provenance": row.get("retrieval_provenance", ""),
                "full_text": body,
                "predicted_voice_label": row["voice_label"],
                "predicted_confidence": row["voice_confidence"],
                "researcher_label": "",
                "researcher_notes": "",
            })

    n_dq = sum(1 for r in sample_rows if r["voice_label"] == LABEL_DIRECT)
    n_pm = sum(1 for r in sample_rows if r["voice_label"] == LABEL_PARAPHRASE)
    n_uc = sum(1 for r in sample_rows if r["voice_label"] == LABEL_USER)
    n_lc = sum(1 for r in sample_rows if r["voice_confidence"] == CONF_LOW)
    print(f"\nValidation sample: {len(sample_rows)} items")
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

    validation_path = (REPO_ROOT / "notebooks" / "audit_trail" /
                       "phase_4_voice_segmentation_validation_sample.csv")
    prepare_validation_sample(rows_out, validation_path)

    print("\nPhase 4 voice segmentation complete.")
    print(f"  Segmented corpus : {OUTPUT_CSV}")
    print(f"  Confidence dist  : {CONF_DIST}")
    print(f"  Validation sample: {validation_path}")
    print(f"  LLM call log     : {LLM_LOG}")
    print(f"  Reliable fraction: {high_med}/{total} "
          f"({100*high_med/total:.1f}%) at high+medium confidence")
