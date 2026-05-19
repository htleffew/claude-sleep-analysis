"""
Pull 60 additional cases from V2 high-yield cluster for the coding extension.

V1's Cluster 4 (n=484, p_nudge=1.0) reshuffled into V2's Cluster 3
(n=3,327, p_nudge=0.162) after the V2 extractor pulled in more diverse
expressions of the behavior. We sample from Cluster 3's confirmed-nudge
subset (n ~ 539), exclude post_idx already in the original 120-case set,
and target 60 new cases for hand-coding under the same 9-dimension schema.
"""

import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DELIV = "deliverables/"
features_path = os.path.join(DELIV, "discourse_features.csv")
original_coded_path = os.path.join(DELIV, "cases_coded.csv")

df = pd.read_csv(features_path)
df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")

# Re-run the same clustering as in discourse_features_analysis.py so we can
# identify which posts fall into each cluster. The pipeline mutates an
# in-memory copy but does not persist feature_cluster to the CSV.
feature_cols = [
    "temporal_disclosure_count",
    "affective_disclosure_count",
    "session_disclosure_count",
    "work_context_count",
    "first_person_density",
    "mental_state_density",
    "n_imperative_quotes",
    "n_modal_directives",
    "n_temporal_expressions",
    "code_prose_ratio",
    "has_transcript_structure",
] + [f"nrc_{c}" for c in [
    "fear", "anger", "anticipation", "trust", "surprise",
    "sadness", "joy", "disgust", "positive", "negative",
]]
X = df[feature_cols].fillna(0).values
Xs = StandardScaler().fit_transform(X)
km = KMeans(n_clusters=8, random_state=42, n_init=10)
df["feature_cluster"] = km.fit_predict(Xs)

cluster_stats = (
    df.groupby("feature_cluster")
      .agg(n=("has_nudge_in_target", "count"),
           p_nudge=("has_nudge_in_target", "mean"))
      .reset_index()
)
print("Cluster summary:")
print(cluster_stats.to_string(index=False))

# Pick the high-yield cluster: highest p_nudge with n >= 200
candidates = cluster_stats[cluster_stats["n"] >= 200]
high_yield = candidates.sort_values("p_nudge", ascending=False).iloc[0]
target_cluster = int(high_yield["feature_cluster"])
print(f"\nTarget cluster: {target_cluster} "
      f"(n={int(high_yield['n'])}, p_nudge={high_yield['p_nudge']:.3f})")

# Get confirmed-nudge members of that cluster
cluster_members = df[
    (df["feature_cluster"] == target_cluster) &
    (df["has_nudge_in_target"] == 1)
].copy()
print(f"Confirmed-nudge members of target cluster: {len(cluster_members)}")

# Exclude post_idx already coded
already_coded_idx = set()
if os.path.exists(original_coded_path):
    coded = pd.read_csv(original_coded_path)
    already_coded_idx = set(coded["post_idx"].astype(int).tolist())
print(f"Already coded post_idx count: {len(already_coded_idx)}")

cluster_members = cluster_members[~cluster_members["post_idx"].isin(already_coded_idx)]
print(f"Remaining un-coded candidates: {len(cluster_members)}")

# Sample 60. Stratify roughly across the date range for representativeness.
n_target = min(60, len(cluster_members))
sample = cluster_members.sample(n=n_target, random_state=2026)

# Order by createdAt for readability
sample = sample.sort_values("createdAt").reset_index(drop=True)
sample["selection_reason"] = "cluster3_v2_high_yield"

# Keep only useful columns
out_cols = [
    "post_idx", "createdAt", "subreddit", "selection_reason",
    "has_nudge_in_target",
    "n_quote_spans", "has_transcript_structure",
    "temporal_disclosure_count", "affective_disclosure_count",
    "session_disclosure_count", "work_context_count",
    "first_person_density", "n_imperative_quotes", "n_modal_directives",
    "body_clean", "quoted_text", "narration_text",
]
out_cols = [c for c in out_cols if c in sample.columns]
sample = sample[out_cols]

# Blank coding columns matching the original schema
coding_cols = [
    "code_role_violation", "code_violation_type", "code_time_tense",
    "code_advice_requested", "code_model_mood", "code_user_pushback",
    "code_pushback_response", "code_cross_session", "code_vulnerability",
    "code_notes",
]
for col in coding_cols:
    sample[col] = ""

out_path = os.path.join(DELIV, "cases_to_code_v2_cluster3.csv")
sample.to_csv(out_path, index=False)
print(f"\nSaved {len(sample)} cases to {out_path}")

# Also dump a readable text file for the coder
out_lines = []
for i, row in sample.iterrows():
    out_lines.append(
        f"=== CASE {i} (post_idx={row['post_idx']}, sub={row['subreddit']}, "
        f"created={row['createdAt'].date()}) ==="
    )
    out_lines.append(str(row["body_clean"])[:1800])
    out_lines.append("")

read_path = os.path.join(DELIV, "cluster3_cases_to_read.txt")
with open(read_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print(f"Wrote readable dump to {read_path}")
