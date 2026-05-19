import pandas as pd

REPO = "C:/Users/drhea/repos/claude-sleep-analysis"

fresh = pd.read_csv(f"{REPO}/data/round2_fresh_retrieval.csv")
print("round2_fresh_retrieval:", len(fresh), "rows,", fresh["post_id"].nunique(), "unique post_ids")
print("  subreddits:", fresh["subreddit"].value_counts().to_dict())
print()

pass1b = pd.read_csv(f"{REPO}/data/pass1b_canonical.csv", low_memory=False)
print("pass1b_canonical:", len(pass1b), "rows")
print("  type breakdown:", pass1b["type"].value_counts().to_dict())
print("  provenance:", pass1b["retrieval_provenance"].value_counts().to_dict())
print()

val = pd.read_csv(f"{REPO}/notebooks/audit_trail/round_2_fresh_validation.csv")
print("round_2_fresh_validation:", len(val), "rows")
print("  subreddits:", val["subreddit"].value_counts().to_dict())
print("  matched_terms sample:")
for _, row in val.head(5).iterrows():
    print("   ", row["post_id"], "|", row["r2_matched_terms"][:60], "|", str(row["body"])[:80])
print()

canonical = pd.read_csv(f"{REPO}/data/posts_snapshot_canonical.csv")
praw = pd.read_csv(f"{REPO}/data/praw_sleep_analysis_final.csv")
existing_ids = set(canonical["post_id"].dropna().astype(str)) | set(praw["post_id"].dropna().astype(str))
fresh_ids = set(fresh["post_id"].dropna().astype(str))
net_new = fresh_ids - existing_ids
pass1b_posts = pass1b[pass1b["type"] == "post"]
print("Net-new post_ids in fresh retrieval (not in canonical or PRAW):", len(net_new))
print("Fraction of fresh that is net-new:", round(len(net_new)/len(fresh_ids)*100, 1), "%")
print("Pass1b posts count:", len(pass1b_posts))
if len(pass1b_posts) > 0:
    print("Net-new as fraction of pass1b posts:", round(len(net_new)/len(pass1b_posts)*100, 1), "%")

# Show the results MD
print("\n=== Results MD ===")
with open(f"{REPO}/notebooks/audit_trail/iterative_retrieval_round_2_results.md") as f:
    print(f.read()[:3000])
