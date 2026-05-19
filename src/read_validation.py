import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

val = pd.read_csv("C:/Users/drhea/repos/claude-sleep-analysis/notebooks/audit_trail/round_2_fresh_validation.csv")
print("Validation sample:", len(val), "rows")
print()
for i, row in val.iterrows():
    body_preview = str(row['body'])[:200].encode('ascii', errors='replace').decode('ascii')
    matched = str(row['r2_matched_terms'])
    print(f"{i+1}. post_id={row['post_id']} [{row['subreddit']}]")
    print(f"   matched: {matched}")
    print(f"   body: {body_preview}")
    print()
