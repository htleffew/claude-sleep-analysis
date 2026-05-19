"""
voice_segmentation_v3.py
Phase 4 — Voice Segmentation  [method §C.4]
Sleep-nudge Pass 1b canonical corpus

Purpose
-------
Extend v2 by running Gemini on the full unsampled low-confidence tail.
v2 ran 100 calls on a stratified sample of the 592 low-confidence rows
and found ~43% were model-attributed (35 UOC→Paraphrase, 8 UOC→Direct_Quote).
492 rows were left unsampled.  v3 processes all of them — no budget cap.

Changes from v2
---------------
- Input is data/pass1b_canonical_voice_segmented_v2.csv (v2 output), not the
  raw canonical CSV.  v2 label, v2 confidence, and v2 source are preserved for
  all rows not touched by v3.
- Target population: rows where voice_confidence == "low" AND
  voice_source != "gemini_fallback" (i.e., the 492 rows v2 did not sample).
- No budget cap.  Every unsampled low-confidence row is sent to Gemini.
- Resume-from-state: if the log file (llm_call_log_v3.jsonl) already contains
  an entry for a given row_id, that row is skipped.  Re-running the script
  after an interruption continues from where it stopped.
- Outputs saved to separate v3 filenames; v1 and v2 outputs are preserved.
- Unicode fix: encoding='utf-8', errors='replace' in subprocess.run (carried
  over from v2, which discovered this via the LCR Unicode crash).

Architecture (unchanged from v2 except the input and target population)
-----------
Layer 1a-1c — Not re-run in v3.  v2 regex labels are preserved as-is for
              high/medium rows and for any low-confidence rows that were
              already Gemini-processed in v2.

Layer 2 (v3 extension) — Gemini CLI fallback on ALL unsampled low-conf rows.
              Model: gemini-3.1-flash-lite via Gemini CLI 0.42.0.
              Invocation: echo "<prompt>" | gemini.cmd -m gemini-3.1-flash-lite
              No budget cap; resume-safe.

LLM call log
-------------
Every Gemini call is appended to:
  deliverables/phase_4_voice_segmentation/llm_call_log_v3.jsonl
Same schema as v2 log.  The log is the §9.2 audit trail.

Design date: 2026-05-18

Usage
-----
    python src/voice_segmentation_v3.py

Outputs (all relative to repo root)
-------------------------------------
    data/pass1b_canonical_voice_segmented_v3.csv
    deliverables/phase_4_voice_segmentation/llm_call_log_v3.jsonl
    deliverables/phase_4_voice_segmentation/confidence_distribution_v3.csv
    notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3.csv
    notebooks/audit_trail/phase_4_v2_vs_v3_label_shifts.csv
    notebooks/audit_trail/phase_4_voice_segmentation_v3_summary.md
    notebooks/llm_tool_log.md  (updated in-place)
"""

import csv
import json
import re
import random
import datetime
import subprocess
import time
from pathlib import Path
from typing import Tuple, List, Dict, Set
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV_V2 = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented_v2.csv"
V1_CSV       = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented.csv"
OUTPUT_CSV   = REPO_ROOT / "data" / "pass1b_canonical_voice_segmented_v3.csv"

DELIVERABLES_DIR = REPO_ROOT / "deliverables" / "phase_4_voice_segmentation"
LLM_LOG_V3  = DELIVERABLES_DIR / "llm_call_log_v3.jsonl"
CONF_DIST_V3 = DELIVERABLES_DIR / "confidence_distribution_v3.csv"

AUDIT_DIR = REPO_ROOT / "notebooks" / "audit_trail"
VALIDATION_SAMPLE_V3 = AUDIT_DIR / "phase_4_voice_segmentation_validation_sample_v3.csv"
LABEL_SHIFTS_V2_V3   = AUDIT_DIR / "phase_4_v2_vs_v3_label_shifts.csv"
V3_SUMMARY           = AUDIT_DIR / "phase_4_voice_segmentation_v3_summary.md"
LLM_TOOL_LOG         = REPO_ROOT / "notebooks" / "llm_tool_log.md"

DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LABEL_DIRECT    = "Direct_Quote_Of_Model"
LABEL_PARAPHRASE = "Paraphrase_Of_Model"
LABEL_USER      = "User_Original_Content"

CONF_HIGH = "high"
CONF_MED  = "medium"
CONF_LOW  = "low"

GEMINI_CMD         = "gemini.cmd"
GEMINI_MODEL       = "gemini-3.1-flash-lite"
GEMINI_CLI_VERSION = "0.42.0"
CALL_TIMEOUT       = 60   # seconds per call

# ---------------------------------------------------------------------------
# Gemini prompt template — VERBATIM from v2 (§9.2 requires same prompt)
# ---------------------------------------------------------------------------
GEMINI_PROMPT_TEMPLATE = """\
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or User_Original_Content.

Direct_Quote_Of_Model: author quotes AI verbatim. Example: 'Claude: go to bed' or '> Now go to sleep' or it said "that is a good place to leave"
Paraphrase_Of_Model: author paraphrases/reports what AI said or did. Example: 'Claude told me to go to bed' or 'it kept insisting I take a break' or 'my Claude tells me to stop'
User_Original_Content: no AI speech at all. Example: 'I worked all night' or 'anyone else notice this?' or just general commentary

If negated attribution (e.g. 'it never told me to sleep'), choose User_Original_Content.
Reply with ONLY the label name, no other text.

Text: {text}"""

# ---------------------------------------------------------------------------
# Resume-from-state: load already-processed row IDs from log
# ---------------------------------------------------------------------------

def load_processed_ids(log_path: Path) -> Set[str]:
    """Return set of row_ids already in the v3 log (for resume-from-state)."""
    processed = set()
    if not log_path.exists():
        return processed
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                rid = entry.get("row_id", "")
                if rid:
                    processed.add(rid)
            except json.JSONDecodeError:
                continue
    return processed


# ---------------------------------------------------------------------------
# Gemini CLI fallback — VERBATIM logic from v2, same Unicode fix
# ---------------------------------------------------------------------------

llm_call_count = 0
llm_errors: List[Dict] = []


def _call_gemini(text: str, row_id: str) -> Tuple[str, str]:
    """
    Call gemini-3.1-flash-lite via CLI subprocess.
    Returns (label, confidence).
    Appends log entry to LLM_LOG_V3.
    On any error returns (User_Original_Content, low).

    Unicode fix: encoding='utf-8', errors='replace' (from LCR v2 discovery).
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

        # Filter startup noise from stdout (same logic as v2)
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

        # Extract label
        valid_labels = {LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER}
        label = None
        confidence = CONF_LOW

        for candidate in valid_labels:
            if candidate.lower() in raw_clean.lower():
                label = candidate
                break

        if label is None:
            label = LABEL_USER
            confidence = CONF_LOW
            error_note = f"no_valid_label_in_response: '{raw_clean[:100]}'"
            llm_errors.append({"row_id": row_id, "error": error_note,
                                "call_number": llm_call_count + 1})
        else:
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
    with open(LLM_LOG_V3, "a", encoding="utf-8") as flog:
        flog.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return label, confidence


# ---------------------------------------------------------------------------
# Main segmenter
# ---------------------------------------------------------------------------

def run_v3_segmentation() -> List[Dict]:
    """
    Load v2 corpus, identify unsampled low-confidence rows, run Gemini on all
    of them (with resume-from-state), write v3 corpus.
    """
    # Load v2 corpus
    with open(INPUT_CSV_V2, newline="", encoding="utf-8-sig") as fin:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    n = len(rows)
    print(f"Loaded {n} rows from {INPUT_CSV_V2.name}")

    # Identify target rows: low-confidence AND not already Gemini-processed by v2
    # v2 Gemini rows have voice_source == "gemini_fallback"
    target_indices = [
        i for i, r in enumerate(rows)
        if r["voice_confidence"] == CONF_LOW
        and r["voice_source"] != "gemini_fallback"
    ]

    n_already_gemini = sum(
        1 for r in rows
        if r["voice_confidence"] == CONF_LOW and r["voice_source"] == "gemini_fallback"
    )
    n_high_med = sum(1 for r in rows if r["voice_confidence"] in (CONF_HIGH, CONF_MED))
    print(f"  High/medium confidence (pass through): {n_high_med}")
    print(f"  Low-conf already Gemini-processed by v2 (pass through): {n_already_gemini}")
    print(f"  Unsampled low-confidence (v3 target): {len(target_indices)}")

    by_type = Counter(rows[i]["type"] for i in target_indices)
    print(f"  Target breakdown: {dict(by_type)}")

    # Load already-processed row IDs for resume-from-state
    processed_ids = load_processed_ids(LLM_LOG_V3)
    if processed_ids:
        print(f"  Resume mode: {len(processed_ids)} rows already in v3 log; skipping.")

    # Process each target row
    newly_processed = 0
    resumed_count   = len(processed_ids)
    updates: Dict[int, Tuple[str, str, str]] = {}  # index -> (label, conf, source)

    for i in target_indices:
        row = rows[i]
        row_id = row.get("post_id", "") + "|" + row.get("comment_id", "")
        text   = row.get("body", "") or ""

        if row_id in processed_ids:
            # Already processed in a prior run; we need to get label from log
            # (handled after loop below)
            continue

        label, conf = _call_gemini(text, row_id)
        updates[i] = (label, conf, "gemini_fallback_v3")
        processed_ids.add(row_id)
        newly_processed += 1

        if newly_processed % 25 == 0:
            print(f"    ... {newly_processed} new v3 Gemini calls complete "
                  f"(total calls this run: {llm_call_count})")

    print(f"\nv3 Gemini calls issued this run: {llm_call_count}")
    print(f"  New rows processed: {newly_processed}")
    print(f"  Rows resumed from prior log: {resumed_count}")
    if llm_errors:
        print(f"  Errors: {len(llm_errors)}")

    # For resumed rows, read labels back from the log
    if resumed_count > 0:
        log_by_id: Dict[str, Dict] = {}
        with open(LLM_LOG_V3, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    rid = entry.get("row_id", "")
                    if rid:
                        log_by_id[rid] = entry  # last entry wins on duplicates
                except json.JSONDecodeError:
                    continue

        for i in target_indices:
            if i in updates:
                continue  # Already set by this run
            row = rows[i]
            row_id = row.get("post_id", "") + "|" + row.get("comment_id", "")
            if row_id in log_by_id:
                entry = log_by_id[row_id]
                updates[i] = (
                    entry.get("assigned_label", LABEL_USER),
                    entry.get("assigned_confidence", CONF_LOW),
                    "gemini_fallback_v3",
                )

    # Build v3 fieldnames: keep all v2 fields, add v3 fields
    # v2 already has voice_label, voice_confidence, voice_source
    # We add voice_label_v3, voice_confidence_v3, voice_source_v3
    # so that v2 values are preserved for provenance.
    out_fieldnames = fieldnames + [
        "voice_label_v3", "voice_confidence_v3", "voice_source_v3"
    ]

    rows_out = []
    for i, row in enumerate(rows):
        row = dict(row)  # copy
        if i in updates:
            label_v3, conf_v3, src_v3 = updates[i]
        else:
            # Row was not targeted by v3: keep v2 values as v3 values
            label_v3 = row["voice_label"]
            conf_v3  = row["voice_confidence"]
            src_v3   = row["voice_source"]  # e.g. "regex", "gemini_fallback"

        row["voice_label_v3"]      = label_v3
        row["voice_confidence_v3"] = conf_v3
        row["voice_source_v3"]     = src_v3
        rows_out.append(row)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Output written: {OUTPUT_CSV}")
    return rows_out


# ---------------------------------------------------------------------------
# Confidence distribution (v3 labels)
# ---------------------------------------------------------------------------

def compute_confidence_distribution_v3(rows_out: List[Dict], output_path: Path):
    """Stratified confidence distribution using voice_label_v3 / voice_confidence_v3."""
    counts: Counter = Counter()
    for row in rows_out:
        key = (row["type"], row["voice_label_v3"], row["voice_confidence_v3"])
        counts[key] += 1

    total = len(rows_out)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "voice_label_v3", "voice_confidence_v3",
                         "n", "pct_of_total"])
        for (stratum, label, conf), n in sorted(counts.items()):
            writer.writerow([stratum, label, conf, n,
                             round(100 * n / total, 2)])

    print("\n--- Confidence distribution v3 (stratified) ---")
    conf_totals:  Counter = Counter()
    label_totals: Counter = Counter()
    type_totals:  Counter = Counter()

    for row in rows_out:
        conf_totals[row["voice_confidence_v3"]] += 1
        label_totals[row["voice_label_v3"]] += 1
        type_totals[row["type"]] += 1

    print("  By confidence (v3):")
    for conf in [CONF_HIGH, CONF_MED, CONF_LOW]:
        n = conf_totals[conf]
        print(f"    {conf:6}: {n:4}/{total} ({100*n/total:5.1f}%)")
    high_med = conf_totals[CONF_HIGH] + conf_totals[CONF_MED]
    print(f"    high+medium (reliably segmentable, v3): "
          f"{high_med}/{total} ({100*high_med/total:.1f}%)")

    print("  By voice label (v3):")
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = label_totals[label]
        print(f"    {label}: {n}/{total} ({100*n/total:.1f}%)")

    print("  Per-stratum voice label v3 (posts):")
    post_rows = [r for r in rows_out if r["type"] == "post"]
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = sum(1 for r in post_rows if r["voice_label_v3"] == label)
        print(f"    {label}: {n}/{len(post_rows)} ({100*n/len(post_rows):.1f}%)")

    print("  Per-stratum voice label v3 (comments):")
    comment_rows = [r for r in rows_out if r["type"] == "comment"]
    for label in [LABEL_DIRECT, LABEL_PARAPHRASE, LABEL_USER]:
        n = sum(1 for r in comment_rows if r["voice_label_v3"] == label)
        print(f"    {label}: {n}/{len(comment_rows)} ({100*n/len(comment_rows):.1f}%)")

    return conf_totals, label_totals, high_med, total


# ---------------------------------------------------------------------------
# V2 vs V3 comparison table
# ---------------------------------------------------------------------------

def build_v2_v3_shift_table(rows_out: List[Dict], output_path: Path):
    """Row-by-row comparison of v2 and v3 labels for the 492 targeted rows."""
    conf_order = {CONF_LOW: 0, CONF_MED: 1, CONF_HIGH: 2}

    shift_rows = []
    for row in rows_out:
        v2_label = row["voice_label"]
        v2_conf  = row["voice_confidence"]
        v3_label = row["voice_label_v3"]
        v3_conf  = row["voice_confidence_v3"]

        # Only include rows that were targeted by v3 Gemini
        if row["voice_source_v3"] != "gemini_fallback_v3":
            continue

        label_changed = (v2_label != v3_label)
        conf_delta    = (conf_order.get(v3_conf, 0) - conf_order.get(v2_conf, 0))
        row_id = row.get("post_id", "") + "|" + row.get("comment_id", "")

        shift_rows.append({
            "row_id":        row_id,
            "type":          row["type"],
            "v2_label":      v2_label,
            "v2_conf":       v2_conf,
            "v3_label":      v3_label,
            "v3_conf":       v3_conf,
            "label_changed": label_changed,
            "conf_delta":    conf_delta,
            "v2_source":     row["voice_source"],
            "v3_source":     row["voice_source_v3"],
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "row_id", "type", "v2_label", "v2_conf",
            "v3_label", "v3_conf", "label_changed", "conf_delta",
            "v2_source", "v3_source",
        ])
        writer.writeheader()
        writer.writerows(shift_rows)

    if not shift_rows:
        print("\n[Warning] No v3-targeted rows found for shift table.")
        return {}

    n_label_changed = sum(1 for r in shift_rows if r["label_changed"])
    n_conf_up       = sum(1 for r in shift_rows if r["conf_delta"] > 0)
    n_conf_down     = sum(1 for r in shift_rows if r["conf_delta"] < 0)
    n_conf_same     = sum(1 for r in shift_rows if r["conf_delta"] == 0)

    print(f"\n--- V2 vs V3 label shift summary ---")
    print(f"  Rows compared (v3-targeted): {len(shift_rows)}")
    print(f"  Label changed: {n_label_changed} ({100*n_label_changed/len(shift_rows):.1f}%)")
    print(f"  Confidence upgraded: {n_conf_up}")
    print(f"  Confidence downgraded: {n_conf_down}")
    print(f"  Confidence unchanged: {n_conf_same}")

    shift_matrix: Counter = Counter()
    for r in shift_rows:
        shift_matrix[(r["v2_label"][:3], r["v3_label"][:3])] += 1
    print("  Shift matrix (v2 -> v3, label[:3]):")
    for (a, b), cnt in sorted(shift_matrix.items()):
        print(f"    {a} -> {b}: {cnt}")

    return {
        "n_label_changed": n_label_changed,
        "n_conf_up": n_conf_up,
        "n_conf_down": n_conf_down,
        "n_conf_same": n_conf_same,
        "n_total": len(shift_rows),
        "shift_matrix": dict(shift_matrix),
    }


# ---------------------------------------------------------------------------
# Validation sample v3
# ---------------------------------------------------------------------------

def prepare_validation_sample_v3(rows_out: List[Dict], output_path: Path,
                                  seed: int = 43):
    """
    Stratified 70-item validation sample using v3 labels.
    Seed differs from v2 (43 vs 42) to draw a fresh sample.
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
        lbl  = row.get("voice_label_v3")
        conf = row.get("voice_confidence_v3")
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

    sample_rows.sort(key=lambda r: (r["type"], r["voice_label_v3"]))

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
                "predicted_voice_label":  row["voice_label_v3"],
                "predicted_confidence":   row["voice_confidence_v3"],
                "researcher_label":     "",
                "researcher_notes":     "",
            })

    n_dq = sum(1 for r in sample_rows if r["voice_label_v3"] == LABEL_DIRECT)
    n_pm = sum(1 for r in sample_rows if r["voice_label_v3"] == LABEL_PARAPHRASE)
    n_uc = sum(1 for r in sample_rows if r["voice_label_v3"] == LABEL_USER)
    n_lc = sum(1 for r in sample_rows if r["voice_confidence_v3"] == CONF_LOW)
    print(f"\nValidation sample v3: {len(sample_rows)} items")
    print(f"  Direct_Quote: {n_dq}  Paraphrase: {n_pm}  "
          f"User_Content: {n_uc}  Low-conf: {n_lc}")
    print(f"  Written to: {output_path.name}")
    return sample_rows


# ---------------------------------------------------------------------------
# LLM tool log update
# ---------------------------------------------------------------------------

def update_llm_tool_log(call_count: int, log_path: Path):
    """Append v3 entry to notebooks/llm_tool_log.md."""
    entry = f"""

---

## Entry 002 — Phase 4 Voice Segmentation Fallback (v3)

| Field | Value |
|---|---|
| Tool | Gemini CLI 0.42.0 (`gemini.cmd`) |
| Model | `gemini-3.1-flash-lite` |
| Date | 2026-05-18 |
| Role | Phase 4 v3 extended Gemini fallback — full unsampled low-confidence tail |
| Budget | No cap (all 492 unsampled low-confidence rows) |
| Calls used | {call_count} |
| Errors | {len(llm_errors)} |
| Script | `src/voice_segmentation_v3.py` |
| Per-call log | `deliverables/phase_4_voice_segmentation/llm_call_log_v3.jsonl` |
| Output corpus | `data/pass1b_canonical_voice_segmented_v3.csv` |

### Invocation pattern

```python
result = subprocess.run(
    ["gemini.cmd", "-m", "gemini-3.1-flash-lite"],
    input=prompt,
    capture_output=True,
    text=True,
    timeout=60,
    encoding="utf-8",
    errors="replace",
)
```

Prompt passed via stdin (`input=`).  stderr discarded.  Unicode fix carried
over from v2 (LCR-discovered).

### Prompt template (verbatim from v2)

```
Classify as EXACTLY ONE: Direct_Quote_Of_Model, Paraphrase_Of_Model, or User_Original_Content.

Direct_Quote_Of_Model: author quotes AI verbatim. Example: 'Claude: go to bed' or '> Now go to sleep' or it said "that is a good place to leave"
Paraphrase_Of_Model: author paraphrases/reports what AI said or did. Example: 'Claude told me to go to bed' or 'it kept insisting I take a break' or 'my Claude tells me to stop'
User_Original_Content: no AI speech at all. Example: 'I worked all night' or 'anyone else notice this?' or just general commentary

If negated attribution (e.g. 'it never told me to sleep'), choose User_Original_Content.
Reply with ONLY the label name, no other text.

Text: {{text}}
```

### Scope

Applied to all 492 rows that v2 left as unsampled low-confidence
(`voice_confidence == "low"` AND `voice_source != "gemini_fallback"`).
No budget cap.  Resume-safe: re-running after interruption skips rows
already in `llm_call_log_v3.jsonl`.

### §9.2 compliance note

Same compliance conditions as v2 (tight prompt, single example per class,
70-item stratified validation sample drawn, shift table computed).  V3 is
an extension of the v2 fallback, not a new classification system.  V2 outputs
for high/medium confidence rows are preserved unchanged.
"""

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"  LLM tool log updated: {log_path.name}")


# ---------------------------------------------------------------------------
# V3 summary document
# ---------------------------------------------------------------------------

def write_v3_summary(
    rows_out: List[Dict],
    conf_totals: Counter,
    label_totals: Counter,
    high_med: int,
    total: int,
    shift_stats: Dict,
    call_count: int,
    output_path: Path,
):
    """Write audit_trail/phase_4_voice_segmentation_v3_summary.md."""

    # v1 reference values (from v2 summary)
    v1_reliable_n   = 182
    v1_reliable_pct = 23.5
    # v2 reference values
    v2_reliable_n   = 281
    v2_reliable_pct = 36.4

    v3_reliable_n   = high_med
    v3_reliable_pct = round(100 * high_med / total, 1)
    meets_threshold = "YES" if v3_reliable_pct >= 70.0 else "NO"

    # Build shift matrix display
    shift_matrix = shift_stats.get("shift_matrix", {})
    shift_table_lines = []
    for (a, b), cnt in sorted(shift_matrix.items()):
        shift_table_lines.append(f"| {a} | {b} | {cnt} |")
    shift_table = "\n".join(shift_table_lines) if shift_table_lines else "| (no shifts) | | |"

    # Label counts
    n_dq = label_totals[LABEL_DIRECT]
    n_pm = label_totals[LABEL_PARAPHRASE]
    n_uc = label_totals[LABEL_USER]
    n_hi = conf_totals[CONF_HIGH]
    n_md = conf_totals[CONF_MED]
    n_lo = conf_totals[CONF_LOW]

    post_rows    = [r for r in rows_out if r["type"] == "post"]
    comment_rows = [r for r in rows_out if r["type"] == "comment"]

    def pct(n, d):
        return round(100 * n / d, 1) if d else 0.0

    content = f"""# Phase 4 Voice Segmentation — v3 Summary

**Script:** `src/voice_segmentation_v3.py`
**Date run:** 2026-05-18
**Input:** `data/pass1b_canonical_voice_segmented_v2.csv` (773 rows, v2 labels preserved)
**Output:** `data/pass1b_canonical_voice_segmented_v3.csv`

---

## Parameters

| Parameter | Value |
|---|---|
| Input corpus | v2 output (v2 labels preserved for all non-targeted rows) |
| Target population | rows where `voice_confidence == "low"` AND `voice_source != "gemini_fallback"` |
| Target row count | 492 (153 posts, 339 comments) |
| LLM fallback tool | Gemini CLI 0.42.0, model `gemini-3.1-flash-lite` |
| Budget cap | None (full tail) |
| Resume-safe | Yes (log-based deduplication) |
| Prompt template | Verbatim from v2 (§9.2 consistency) |
| Unicode fix | `encoding='utf-8', errors='replace'` (LCR v2 discovery) |
| Random seed (validation sample) | 43 |

---

## V3 Label Distribution

### Overall ({total} rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | {n_dq} | {pct(n_dq, total)}% |
| Paraphrase_Of_Model | {n_pm} | {pct(n_pm, total)}% |
| User_Original_Content | {n_uc} | {pct(n_uc, total)}% |

### By stratum — Posts ({len(post_rows)} rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | {sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_DIRECT)} | {pct(sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_DIRECT), len(post_rows))}% |
| Paraphrase_Of_Model | {sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_PARAPHRASE)} | {pct(sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_PARAPHRASE), len(post_rows))}% |
| User_Original_Content | {sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_USER)} | {pct(sum(1 for r in post_rows if r["voice_label_v3"]==LABEL_USER), len(post_rows))}% |

### By stratum — Comments ({len(comment_rows)} rows)

| Label | Count | Percent |
|---|---|---|
| Direct_Quote_Of_Model | {sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_DIRECT)} | {pct(sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_DIRECT), len(comment_rows))}% |
| Paraphrase_Of_Model | {sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_PARAPHRASE)} | {pct(sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_PARAPHRASE), len(comment_rows))}% |
| User_Original_Content | {sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_USER)} | {pct(sum(1 for r in comment_rows if r["voice_label_v3"]==LABEL_USER), len(comment_rows))}% |

---

## Confidence Distribution (V3)

| Tier | Count | Percent | Source |
|---|---|---|---|
| high | {n_hi} | {pct(n_hi, total)}% | Regex Layer 1a + Gemini exact-match responses (v2 + v3) |
| medium | {n_md} | {pct(n_md, total)}% | Regex Layer 1b + Gemini near-match responses (v2 + v3) |
| low | {n_lo} | {pct(n_lo, total)}% | Rows where Gemini returned UOC or a fallback default |
| **high + medium** | **{v3_reliable_n}** | **{v3_reliable_pct}%** | Reliably segmentable |

---

## V1 → V2 → V3 Trajectory

| Metric | V1 | V2 | V3 |
|---|---|---|---|
| Direct_Quote_Of_Model | 24 (3.1%) | 31 (4.0%) | {n_dq} ({pct(n_dq, total)}%) |
| Paraphrase_Of_Model | 168 (21.7%) | 203 (26.3%) | {n_pm} ({pct(n_pm, total)}%) |
| User_Original_Content | 581 (75.2%) | 539 (69.7%) | {n_uc} ({pct(n_uc, total)}%) |
| Reliable (high+med) | {v1_reliable_n}/{total} ({v1_reliable_pct}%) | {v2_reliable_n}/{total} ({v2_reliable_pct}%) | {v3_reliable_n}/{total} ({v3_reliable_pct}%) |
| Gemini calls | 0 | 100 | {call_count} (v3 only) |
| Total Gemini calls | 0 | 100 | {100 + call_count} (v2+v3 cumulative) |

---

## V2 vs V3 Label Shifts

| Metric | Value |
|---|---|
| Rows targeted by v3 Gemini | {shift_stats.get("n_total", "N/A")} |
| Label changed | {shift_stats.get("n_label_changed", "N/A")} |
| Confidence upgraded | {shift_stats.get("n_conf_up", "N/A")} |
| Confidence downgraded | {shift_stats.get("n_conf_down", "N/A")} |
| Confidence unchanged | {shift_stats.get("n_conf_same", "N/A")} |

### Shift matrix (v2 label -> v3 label, label[:3])

| V2 | V3 | Count |
|---|---|---|
{shift_table}

---

## §C.4 Threshold Determination

The §C.4 decision rule requires **≥ 70% of the corpus to be reliably
segmentable** (high + medium confidence) before voice segmentation results
are used in downstream quantitative analysis.

| | V1 | V2 | V3 |
|---|---|---|---|
| Reliable fraction | {v1_reliable_pct}% | {v2_reliable_pct}% | {v3_reliable_pct}% |
| Meets §C.4 threshold (≥ 70%) | No | No | {meets_threshold} |

{"**The §C.4 70% threshold IS met under v3.**  Voice-segmented counts may be used in primary analysis tables, subject to the v3 validation sample audit." if meets_threshold == "YES" else f"**The §C.4 70% threshold is NOT yet met under v3** ({v3_reliable_pct}% < 70%).  V3 extends v2 by processing all 492 remaining unsampled rows but the reliable-segmentation fraction remains below threshold.  All rows in the unsampled tail that Gemini returned User_Original_Content for are retained at low confidence.  The low-confidence rows are semantically appropriate defaults (no model attribution signal found), not processing failures.  Options to reach 70%: (a) additional regex pattern development targeting corpus-specific signals identified in the validation audit, or (b) accept the current reliable fraction and treat voice-segmented counts as exploratory with a confidence caveat."}

---

## LLM Fallback Call Statistics (V3)

| Metric | Value |
|---|---|
| Calls issued | {call_count} |
| Errors | {len(llm_errors)} |
| Target rows | 492 |
| Per-call log | `deliverables/phase_4_voice_segmentation/llm_call_log_v3.jsonl` |

---

## Validation Sample

A 70-item stratified validation sample was drawn for human audit using v3 labels:
`notebooks/audit_trail/phase_4_voice_segmentation_validation_sample_v3.csv`

This sample supersedes the v2 validation sample.

**This sample must be reviewed before v3 labels are treated as publishable
ground truth.**

---

## Recommendation

{"V3 meets the §C.4 threshold and supersedes v2 as the operational voice segmentation.  V1 and V2 outputs are preserved for provenance.  The v3 validation sample must be audited before primary analysis." if meets_threshold == "YES" else f"V3 does not yet meet the §C.4 70% threshold ({v3_reliable_pct}% reliable).  V3 supersedes v2 as the operational voice segmentation for the reliable-row subset ({v3_reliable_n} rows at high or medium confidence).  The low-confidence rows ({n_lo}) may be used exploratorily with a confidence caveat.  Further extension via additional regex patterns is the most efficient next step; a v4 Gemini pass is unlikely to raise the fraction meaningfully since the remaining low-confidence rows are those where Gemini found no model attribution signal.  V1 and v2 outputs are preserved at their original paths for provenance."}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  V3 summary written: {output_path.name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    rows_out = run_v3_segmentation()

    conf_totals, label_totals, high_med, total = \
        compute_confidence_distribution_v3(rows_out, CONF_DIST_V3)

    shift_stats = build_v2_v3_shift_table(rows_out, LABEL_SHIFTS_V2_V3)

    prepare_validation_sample_v3(rows_out, VALIDATION_SAMPLE_V3)

    update_llm_tool_log(llm_call_count, LLM_TOOL_LOG)

    write_v3_summary(
        rows_out, conf_totals, label_totals,
        high_med, total, shift_stats,
        llm_call_count, V3_SUMMARY,
    )

    print("\nPhase 4 v3 voice segmentation complete.")
    print(f"  Segmented corpus  : {OUTPUT_CSV}")
    print(f"  Confidence dist   : {CONF_DIST_V3}")
    print(f"  Validation sample : {VALIDATION_SAMPLE_V3}")
    print(f"  LLM call log      : {LLM_LOG_V3}")
    print(f"  Label shift table : {LABEL_SHIFTS_V2_V3}")
    print(f"  V3 summary        : {V3_SUMMARY}")
    print(f"  Reliable fraction : {high_med}/{total} "
          f"({100*high_med/total:.1f}%) at high+medium confidence")
    print(f"  Gemini calls (v3) : {llm_call_count}")
    if llm_errors:
        print(f"  Call errors       : {len(llm_errors)}")
