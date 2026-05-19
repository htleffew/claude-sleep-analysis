"""
Pull cases worth hand-coding into a single working file.

Selection:
- All transcript-format posts (high-evidence with both sides)
- All directional cases (temporal disclosure in narration + nudge in quoted span)
- A sample of cluster-4 confirmed-nudge cases (cleaner gold cases)

Output: deliverables/cases_to_code.csv with the columns needed for coding
plus blank coding columns for the schema.
"""

import os
import pandas as pd

DELIV = "deliverables/"
features_path = os.path.join(DELIV, "discourse_features.csv")

df = pd.read_csv(features_path)
df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")

print(f"Loaded {len(df)} feature rows")

# Subset 1: transcript-format posts
transcript = df[df["has_transcript_structure"] == 1].copy()
transcript["selection_reason"] = "transcript_structure"
print(f"Transcript-format: {len(transcript)}")

# Subset 2: directional - nudge in quoted span AND temporal disclosure in narration
directional = df[
    (df["has_nudge_in_target"] == 1) &
    (df["n_quote_spans"] > 0) &
    (df["temporal_disclosure_count"] > 0)
].copy()
directional["selection_reason"] = "directional_temporal"
print(f"Directional (temporal): {len(directional)}")

# Subset 3: directional - nudge in quoted span AND affective disclosure
directional_affect = df[
    (df["has_nudge_in_target"] == 1) &
    (df["n_quote_spans"] > 0) &
    (df["affective_disclosure_count"] > 0)
].copy()
directional_affect["selection_reason"] = "directional_affective"
print(f"Directional (affective): {len(directional_affect)}")

# Subset 4: cluster 4 (the p_nudge=1.0 cluster). Sample if needed.
if "feature_cluster" in df.columns:
    cluster4 = df[df["feature_cluster"] == 4].copy()
    # Sample to make manageable
    if len(cluster4) > 60:
        cluster4 = cluster4.sample(60, random_state=42)
    cluster4["selection_reason"] = "cluster_4_gold"
    print(f"Cluster-4 sampled: {len(cluster4)}")
else:
    cluster4 = pd.DataFrame()

# Combine and dedupe by post_idx, keeping the first selection_reason for each
combined = pd.concat([transcript, directional, directional_affect, cluster4], ignore_index=True)
combined = combined.drop_duplicates(subset=["post_idx"], keep="first").reset_index(drop=True)

# Keep only what's useful for coding
out_cols = [
    "post_idx", "createdAt", "subreddit", "selection_reason",
    "has_nudge_in_target",
    "n_quote_spans", "has_transcript_structure",
    "temporal_disclosure_count", "affective_disclosure_count",
    "session_disclosure_count", "work_context_count",
    "first_person_density", "n_imperative_quotes", "n_modal_directives",
    "body_clean", "quoted_text", "narration_text",
]
out_cols = [c for c in out_cols if c in combined.columns]
combined = combined[out_cols]

# Add blank coding columns
combined["code_time_tense"] = ""        # past / present / hypothetical / none
combined["code_advice_requested"] = ""  # yes / no
combined["code_model_mood"] = ""        # imperative / modal / interrogative / declarative / mixed
combined["code_user_pushback"] = ""     # yes / no / unknown
combined["code_pushback_response"] = "" # yielded / insisted / escalated / na
combined["code_cross_session"] = ""     # yes / no / unknown
combined["code_vulnerability"] = ""     # none / health / emotional / cognitive / other
combined["code_notes"] = ""             # free text

out_path = os.path.join(DELIV, "cases_to_code.csv")
combined.to_csv(out_path, index=False)
print(f"\nSaved {len(combined)} unique cases to {out_path}")
print(f"  Selection breakdown:")
for reason, count in combined["selection_reason"].value_counts().items():
    print(f"    {reason}: {count}")
