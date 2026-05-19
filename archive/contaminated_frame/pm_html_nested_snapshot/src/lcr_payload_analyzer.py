"""
LCR-payload analyzer for cross-corpus replication.

Runs the same feature-engineering pipeline as discourse_features_analysis.py
but substitutes the sleep-nudge target lexicon with a LCR-pathologizing
target lexicon. The disclosure lexicons (temporal, affective, session,
work_context) are identical to the main analysis, providing a controlled
test of whether the same predictive features operate across both payloads.

If the PMI rank order across disclosures is similar across both corpora,
the cross-version continuity claim is empirically supported. If different,
the trigger features differ across payloads even though the structural
output properties (unsolicited, directive, rigid under pushback) hold.

Outputs in deliverables/lcr/:
  lcr_features.csv               per-post features with LCR-payload target
  lcr_pmi_disclosure_payload.csv PMI for LCR payload vs each disclosure
  lcr_quote_spans.csv            quoted Claude utterances containing LCR content
  lcr_comparison_report.txt      side-by-side comparison vs sleep-nudge results
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

import numpy as np
import pandas as pd
import regex

warnings.filterwarnings("ignore")

# Reuse the V2 quote extractor and the disclosure lexicons from the main
# pipeline. We swap only the target (nudge -> LCR payload).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quote_extractor_v2 import (
    extract_quote_spans_v2,
    has_transcript_structure_v2,
)
from discourse_features_analysis import (
    TEMPORAL_DISCLOSURE,
    TEMPORAL_DISCLOSURE_PHRASE,
    AFFECTIVE_DISCLOSURE,
    AFFECTIVE_DISCLOSURE_PHRASE,
    SESSION_DISCLOSURE,
    SESSION_DISCLOSURE_PHRASE,
    WORK_CONTEXT,
    has_lexicon_hit,
    count_lexicon_hits,
    clean_for_features,
)

DATA_DIR = "data/"
OUTPUT_DIR = "deliverables/lcr/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# LCR payload lexicons (the new target)
# --------------------------------------------------------------------------

# Psychiatric attributions
LCR_PSYCHIATRIC_UNIGRAMS = {
    "manic", "mania", "psychosis", "psychotic", "spiraling", "spiralling",
    "spiral", "dissociation", "dissociative", "dissociating", "hypomanic",
    "hypomania", "delusional", "paranoid", "fragmenting", "fragmented",
    "episode", "compulsive", "obsessive", "rumination",
}
LCR_PSYCHIATRIC_PHRASES = [
    "manic episode", "psychotic break", "dissociative episode",
    "mental health crisis", "having an episode", "in crisis",
    "concerning patterns", "concerning behavior",
]

# Treatment / help directives
LCR_HELP_DIRECTIVE_UNIGRAMS = {
    "therapist", "psychiatrist", "psychologist", "counselor", "professional",
}
LCR_HELP_DIRECTIVE_PHRASES = [
    "seek help", "professional help", "mental health professional",
    "talk to someone", "talk to a therapist", "talk to a professional",
    "crisis line", "crisis hotline", "suicide hotline", "support hotline",
    "please reach out", "please consider reaching out",
    "important to talk to", "important to seek", "consider talking to",
    "speak with a professional", "see a therapist", "see a doctor",
    "consult a professional", "trained professional",
]

# Concern framing
LCR_CONCERN_UNIGRAMS = {
    "worried", "concerned", "concerning", "wellbeing", "well-being",
}
LCR_CONCERN_PHRASES = [
    "i'm concerned", "i am concerned", "i'm worried", "i am worried",
    "this is concerning", "concerning to me", "concerned for you",
    "concerned about you", "worried about you",
    "your wellbeing", "your well-being", "your safety",
    "want to make sure you're", "want to make sure you are",
    "checking in on you", "want to check in", "are you safe",
    "are you okay", "are you alright",
]

# Soft directives that pair with the LCR payload
LCR_SOFT_DIRECTIVE_PHRASES = [
    "take a step back", "ground yourself", "ground you", "step away from",
    "talk to someone you trust", "reach out to someone",
    "important to pause", "important to take care",
    "consider taking a break from this", "pausing this conversation",
    "ending this conversation",
]

# Combined LCR payload (union of all four categories)
LCR_ALL_UNIGRAMS = (
    LCR_PSYCHIATRIC_UNIGRAMS
    | LCR_HELP_DIRECTIVE_UNIGRAMS
    | LCR_CONCERN_UNIGRAMS
)
LCR_ALL_PHRASES = (
    LCR_PSYCHIATRIC_PHRASES
    + LCR_HELP_DIRECTIVE_PHRASES
    + LCR_CONCERN_PHRASES
    + LCR_SOFT_DIRECTIVE_PHRASES
)


def has_lcr_payload(text):
    return has_lexicon_hit(text, LCR_ALL_UNIGRAMS, LCR_ALL_PHRASES)


def count_lcr_payload(text):
    return count_lexicon_hits(text, LCR_ALL_UNIGRAMS, LCR_ALL_PHRASES)


# Relevance prefilter for the LCR analysis (skip expensive ops on irrelevant posts)
LCR_RELEVANCE_PREFILTER = re.compile(
    r"\b(claude|sonnet|opus|anthropic|lcr|reminder|spiral|manic|psych|"
    r"dissoc|crisis|therapist|professional|concerned|worried|wellbeing|"
    r"ground yourself|step back|pathologiz|lectur|moraliz|patroniz)\b",
    re.IGNORECASE,
)

DISCLOSURE_LEXICONS = {
    "temporal": (TEMPORAL_DISCLOSURE, TEMPORAL_DISCLOSURE_PHRASE),
    "affective": (AFFECTIVE_DISCLOSURE, AFFECTIVE_DISCLOSURE_PHRASE),
    "session": (SESSION_DISCLOSURE, SESSION_DISCLOSURE_PHRASE),
    "work_context": (WORK_CONTEXT, []),
}


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def build_lcr_features(df):
    rows = []
    quote_rows = []
    for idx, row in df.iterrows():
        body = clean_for_features(row["body"])
        relevant = bool(LCR_RELEVANCE_PREFILTER.search(body))
        quoted, narration, sources = extract_quote_spans_v2(body)

        for method, span in sources:
            quote_rows.append({
                "post_idx": idx,
                "createdAt": row["createdAt"],
                "subreddit": row.get("subreddit", ""),
                "method": method,
                "span": span[:500],
            })

        target_text = quoted if quoted else body
        has_payload = int(has_lcr_payload(target_text))
        narr = narration if narration.strip() else body

        feature_row = {
            "post_idx": idx,
            "createdAt": row["createdAt"],
            "subreddit": row.get("subreddit", ""),
            "type": row.get("type", ""),
            "body_clean": body,
            "quoted_text": quoted,
            "narration_text": narr,
            "n_quote_spans": len(sources),
            "has_lcr_payload_in_target": has_payload,
            "has_transcript_structure": int(has_transcript_structure_v2(body)),
        }

        for lex_name, (uni, phr) in DISCLOSURE_LEXICONS.items():
            feature_row[f"{lex_name}_disclosure_count"] = count_lexicon_hits(narr, uni, phr)

        # Sub-payload counts so we can see which LCR variant dominates
        feature_row["psychiatric_count"] = count_lexicon_hits(
            target_text, LCR_PSYCHIATRIC_UNIGRAMS, LCR_PSYCHIATRIC_PHRASES
        )
        feature_row["help_directive_count"] = count_lexicon_hits(
            target_text, LCR_HELP_DIRECTIVE_UNIGRAMS, LCR_HELP_DIRECTIVE_PHRASES
        )
        feature_row["concern_framing_count"] = count_lexicon_hits(
            target_text, LCR_CONCERN_UNIGRAMS, LCR_CONCERN_PHRASES
        )
        feature_row["soft_directive_count"] = count_lexicon_hits(
            target_text, set(), LCR_SOFT_DIRECTIVE_PHRASES
        )

        rows.append(feature_row)

    return pd.DataFrame(rows), pd.DataFrame(quote_rows)


def compute_pmi_table(df, payload_col, narration_col, label):
    n = len(df)
    if n == 0:
        return pd.DataFrame()
    rows = []
    n_pay = int(df[payload_col].sum())
    p_pay = n_pay / n
    for lex_name, (uni, phr) in DISCLOSURE_LEXICONS.items():
        has_col = df[narration_col].apply(
            lambda t: has_lexicon_hit(t, uni, phr)
        ).astype(int)
        n_lex = int(has_col.sum())
        n_both = int(((df[payload_col] == 1) & (has_col == 1)).sum())
        p_lex = n_lex / n
        p_both = n_both / n
        if p_lex == 0 or p_pay == 0 or p_both == 0:
            pmi = 0.0
            nmpi = 0.0
        else:
            pmi = math.log2(p_both / (p_lex * p_pay))
            nmpi = pmi / -math.log2(p_both)
        rows.append({
            "corpus": label,
            "Disclosure_Lexicon": lex_name,
            "N_posts": n,
            "N_with_lexicon": n_lex,
            "N_with_payload": n_pay,
            "N_with_both": n_both,
            "P_payload_given_lexicon": round(n_both / max(n_lex, 1), 4),
            "P_lexicon_given_payload": round(n_both / max(n_pay, 1), 4),
            "Lift": round((n_both / max(n_lex, 1)) / max(p_pay, 1e-9), 3),
            "PMI": round(pmi, 4),
            "NMPI": round(nmpi, 4),
        })
    return pd.DataFrame(rows).sort_values("PMI", ascending=False)


def load_corpus(path):
    df = pd.read_csv(path)
    df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
    df = df.dropna(subset=["body", "createdAt"]).reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lcr-corpus",
        default=os.path.join(DATA_DIR, "lcr_corpus.csv"),
        help="Path to the LCR-era corpus",
    )
    parser.add_argument(
        "--main-corpus",
        default=os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv"),
        help="Path to the main (current) corpus for comparison",
    )
    args = parser.parse_args()

    if not os.path.exists(args.lcr_corpus):
        print(f"LCR corpus not found at {args.lcr_corpus}. Run the scraper first.")
        return

    print(f"Loading LCR corpus from {args.lcr_corpus}...")
    lcr_df = load_corpus(args.lcr_corpus)
    print(f"  {len(lcr_df)} rows")

    print("\nBuilding LCR-payload features...")
    lcr_features, lcr_quotes = build_lcr_features(lcr_df)
    lcr_features.to_csv(os.path.join(OUTPUT_DIR, "lcr_features.csv"), index=False)
    lcr_quotes.to_csv(os.path.join(OUTPUT_DIR, "lcr_quote_spans.csv"), index=False)
    print(f"  features written: {len(lcr_features)} rows")
    print(f"  posts with LCR payload detected: {int(lcr_features['has_lcr_payload_in_target'].sum())} "
          f"({lcr_features['has_lcr_payload_in_target'].mean():.1%})")

    # Sub-payload composition
    print("\nSub-payload composition (mean per post, among payload-positive):")
    payload_pos = lcr_features[lcr_features["has_lcr_payload_in_target"] == 1]
    for col in ["psychiatric_count", "help_directive_count", "concern_framing_count", "soft_directive_count"]:
        if len(payload_pos):
            print(f"  {col:25s} mean={payload_pos[col].mean():.2f}  "
                  f"any={int((payload_pos[col]>0).sum())}/{len(payload_pos)}")

    print("\nComputing PMI for LCR payload vs disclosure lexicons...")
    lcr_pmi = compute_pmi_table(
        lcr_features, "has_lcr_payload_in_target", "narration_text", "LCR-era (Aug-Dec 2025)"
    )
    lcr_pmi.to_csv(os.path.join(OUTPUT_DIR, "lcr_pmi_disclosure_payload.csv"), index=False)
    print(lcr_pmi.to_string(index=False))

    # Comparison: load main corpus PMI table for side-by-side
    main_pmi_path = "deliverables/pmi_disclosure_nudge.csv"
    if os.path.exists(main_pmi_path):
        main_pmi = pd.read_csv(main_pmi_path)
        main_pmi["corpus"] = "Current (Jan-May 2026)"
        main_pmi["Disclosure_Lexicon"] = main_pmi["Disclosure_Lexicon"].astype(str)

        # Side-by-side
        merged = main_pmi[["Disclosure_Lexicon", "P_nudge_given_lexicon", "PMI"]].rename(
            columns={"P_nudge_given_lexicon": "P_target_given_lex_MAIN",
                     "PMI": "PMI_MAIN"}
        )
        lcr_subset = lcr_pmi[["Disclosure_Lexicon", "P_payload_given_lexicon", "PMI"]].rename(
            columns={"P_payload_given_lexicon": "P_target_given_lex_LCR",
                     "PMI": "PMI_LCR"}
        )
        compare = merged.merge(lcr_subset, on="Disclosure_Lexicon", how="outer")
        compare = compare.sort_values("PMI_MAIN", ascending=False)
        compare.to_csv(os.path.join(OUTPUT_DIR, "lcr_vs_main_comparison.csv"), index=False)
        print("\nSide-by-side PMI comparison (main = sleep-nudge, LCR = pathologizing payload):")
        print(compare.to_string(index=False))

        # Rank-order test
        main_order = main_pmi.sort_values("PMI", ascending=False)["Disclosure_Lexicon"].tolist()
        lcr_order = lcr_pmi.sort_values("PMI", ascending=False)["Disclosure_Lexicon"].tolist()
        print(f"\nMain corpus PMI rank order: {main_order}")
        print(f"LCR  corpus PMI rank order: {lcr_order}")
        if main_order == lcr_order:
            print("==> SAME rank order. Same disclosure lexicons predict both payloads.")
        else:
            print("==> Rank order differs. The payloads have partly distinct triggers.")

    # Write a report
    lines = []
    lines.append("LCR Cross-Corpus Replication Report")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("Corpus: " + args.lcr_corpus)
    lines.append(f"N rows: {len(lcr_df)}")
    lines.append(f"Date range: {pd.to_datetime(lcr_df['createdAt']).min().date()} to "
                 f"{pd.to_datetime(lcr_df['createdAt']).max().date()}")
    lines.append("")
    lines.append("LCR payload detection:")
    lines.append(f"  Posts with LCR payload in target span: "
                 f"{int(lcr_features['has_lcr_payload_in_target'].sum())} "
                 f"({lcr_features['has_lcr_payload_in_target'].mean():.1%})")
    lines.append("")
    lines.append("Sub-payload composition (among payload-positive posts):")
    for col in ["psychiatric_count", "help_directive_count", "concern_framing_count", "soft_directive_count"]:
        if len(payload_pos):
            lines.append(f"  {col:25s} mean={payload_pos[col].mean():.2f}  "
                         f"any={int((payload_pos[col]>0).sum())}/{len(payload_pos)}")
    lines.append("")
    lines.append("PMI for LCR payload vs disclosure lexicons:")
    lines.append(lcr_pmi.to_string(index=False))
    lines.append("")
    if os.path.exists(main_pmi_path):
        lines.append("Cross-corpus comparison (main = sleep-nudge, LCR = pathologizing):")
        lines.append(compare.to_string(index=False))
        lines.append("")
        lines.append("Main corpus PMI rank: " + str(main_order))
        lines.append("LCR  corpus PMI rank: " + str(lcr_order))
        lines.append("")
        if main_order == lcr_order:
            lines.append("==> Same rank order across both payloads.")
            lines.append("    The same disclosure features predict both the sleep-nudge")
            lines.append("    payload and the LCR pathologizing payload. This is the strongest")
            lines.append("    form of cross-version continuity support: not only do the")
            lines.append("    structural properties of the behavior persist, but the same")
            lines.append("    user-disclosure features trigger them.")
        else:
            lines.append("==> Rank order differs across payloads.")
            lines.append("    The structural properties hold but the trigger features")
            lines.append("    differ across payloads. This refines rather than supports")
            lines.append("    the simple continuity claim and is itself an empirically")
            lines.append("    interesting finding.")
    report_path = os.path.join(OUTPUT_DIR, "lcr_comparison_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
