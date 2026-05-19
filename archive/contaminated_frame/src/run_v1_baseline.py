"""
Regenerate the V1 quote-extractor baseline file.

The V1 extractor (the legacy `extract_quote_spans` function in
discourse_features_analysis.py) is no longer called by the main pipeline,
which now uses V2 for both production output and the canonical
quote_spans.csv file. This script runs V1 directly so the V1 baseline
file referenced in the supplementary materials genuinely contains V1
output.

Output:
    deliverables/quote_spans_v1.csv     V1 baseline spans
"""

import os
import pandas as pd
import discourse_features_analysis as dfa

DATA_DIR = "data/"
OUTPUT_DIR = "deliverables/"

CSV_CANDIDATES = [
    os.path.join(DATA_DIR, "praw_sleep_analysis_final.csv"),
    os.path.join(DATA_DIR, "praw_sleep_analysis_final_fallback.csv"),
]


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

    rows = []
    method_counter = {}
    for idx, row in df.iterrows():
        body = "" if pd.isna(row["body"]) else str(row["body"])
        if not body.strip():
            continue
        _, _, sources = dfa.extract_quote_spans(body)
        for method, span in sources:
            rows.append({
                "post_idx": idx,
                "createdAt": row.get("createdAt", ""),
                "subreddit": row.get("subreddit", ""),
                "method": method,
                "span": span[:500],
                "span_length": len(span),
            })
            method_counter[method] = method_counter.get(method, 0) + 1

    out = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "quote_spans_v1.csv")
    out.to_csv(out_path, index=False)
    print(f"Wrote {len(out)} V1 spans to {out_path}")
    print()
    print("V1 method breakdown:")
    for method, count in sorted(method_counter.items(), key=lambda x: -x[1]):
        print(f"  {method:24s} {count:6d}")
    print()
    print(f"Distinct posts with V1 spans: {out['post_idx'].nunique()}")


if __name__ == "__main__":
    main()
