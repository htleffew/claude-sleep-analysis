"""
Apply hand-coded judgments to the 60-case Cluster-3 extension.

Combines with the original 120-case coded set for expanded summary stats.

Coding schema (same as apply_codings.py):
- code_role_violation: yes / no / borderline
- code_violation_type: sleep_nudge / soft_directive / wellness_checkin /
                       break_recommendation / psychiatric / context_warning /
                       off_topic / not_violation
- code_time_tense: past / present / hypothetical / mixed / none
- code_advice_requested: yes / no / unclear
- code_model_mood: imperative / modal / interrogative / declarative / mixed
- code_user_pushback: yes / no / unknown
- code_pushback_response: yielded / insisted / escalated / na / unknown
- code_cross_session: yes / no / unknown
- code_vulnerability: none / health / emotional / cognitive / parental /
                      work_pressure / other
- code_notes: brief comment
"""

import os
import pandas as pd

DELIV = "deliverables/"

# Coding keyed by post_idx. Tuple in schema column order.
EXT_CODES = {
    # Most cases in the V2 Cluster 3 sample are usage/limit complaints, tool
    # announcements, or user-voice discussions where the post hit the
    # session+temporal lexicons without being a Claude nudge case.
    59208: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user discussing own work patterns"),
    16967: ("borderline", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "playful humor context, 1:41am, Claude self-disclosed time"),
    18800: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "RemindMe bot command"),
    84178: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limits"),
    88624: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "SDK update discussion"),
    78818: ("no", "not_violation", "none", "no", "interrogative", "no", "na", "no", "none", "speculative discussion about Claude mimicking"),
    78707: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user frustration with debugging"),
    34994: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "LinkedIn hiring observation"),
    79944: ("no", "not_violation", "none", "yes", "interrogative", "no", "na", "no", "none", "compaction error"),
    2151: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "WakeClaude tool announcement"),
    89636: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user journal practice discussion"),
    2463: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "user-initiated improv collaboration"),
    88296: ("yes", "psychiatric", "past", "no", "declarative", "yes", "insisted", "yes", "none", "GOLD: Claude insisting user spiraling about graphic design for 10 hours across days; user workaround documented"),
    79794: ("borderline", "sleep_nudge", "present", "yes", "imperative", "no", "na", "no", "none", "user asked about sleep optimization; Claude turned technical question into personal nudge"),
    71110: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user planning to read links"),
    15637: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user's own sleep journal"),
    73750: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta explanation of mechanism by user"),
    55624: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user voice 'called it a day' over API error"),
    83402: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user's own sleep pattern"),
    83397: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user staying up late voluntarily"),
    55357: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "parental", "user waiting for kids to fall asleep"),
    508: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Lockpaw tool announcement, sleep terminology incidental"),
    50187: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limit bug"),
    49683: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limits report"),
    69709: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limits report"),
    64941: ("yes", "soft_directive", "present", "no", "imperative", "yes", "insisted", "no", "none", "user describing recurrent 'go to bed' prompts; bypass with 'new day' phrase"),
    50765: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "GOLD: 'sent me to bed because it was late at night (completely unprompted)'"),
    86554: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limit timing"),
    86556: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage burn rate"),
    83301: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user's email automation"),
    2233: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Hello prompt cost 4% usage"),
    21230: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limits"),
    2175: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "ClingyMac tool announcement"),
    17898: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limit complaint"),
    83868: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user's own sleep schedule"),
    60163: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta forum discussion"),
    75401: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage burn rate"),
    20242: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage at 6am"),
    51579: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage normalized"),
    51089: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "CLAUDE.md system prompt observation"),
    82233: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage reset around Opus 4.7"),
    43084: ("no", "not_violation", "none", "no", "interrogative", "no", "na", "no", "none", "usage rate question"),
    82163: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Claude design usage"),
    60181: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Kimi model comparison"),
    2325: ("no", "not_violation", "none", "no", "interrogative", "no", "na", "no", "none", "usage reset confusion"),
    11275: ("yes", "soft_directive", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "GOLD: 10am told 'we got a lot done today, continue tomorrow', user works until 5:30"),
    29928: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "feedback removal issue"),
    47662: ("yes", "soft_directive", "past", "no", "imperative", "no", "na", "yes", "none", "GOLD: model internalized user's past 'table for tomorrow' phrasing into recurrent bedtime directives"),
    47682: ("yes", "soft_directive", "present", "no", "declarative", "no", "na", "no", "work_pressure", "GOLD: 'not even lunch, good place to break for the night'"),
    682: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "prompt injection detector announcement"),
    26961: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage at 100%"),
    43382: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user workaround for token caching"),
    46961: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "usage limit hit early"),
    78102: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Cowork features discussion"),
    2305: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "performance over time"),
    4057: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "casino-rules analogy meta-commentary"),
    38418: ("yes", "soft_directive", "present", "no", "declarative", "no", "na", "no", "work_pressure", "GOLD: afternoon, model 'reporting it was done for the day' after partial work"),
    38269: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "model performance by time of day"),
    24780: ("yes", "soft_directive", "present", "no", "declarative", "yes", "insisted", "yes", "none", "user workaround documented: 11am 'say good night' to reset session because model convinced itself tired"),
    2829: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "yacht racing app announcement"),
}

CODE_COLS = [
    "code_role_violation", "code_violation_type", "code_time_tense",
    "code_advice_requested", "code_model_mood", "code_user_pushback",
    "code_pushback_response", "code_cross_session", "code_vulnerability",
    "code_notes",
]


def apply_extension_codes():
    df = pd.read_csv(os.path.join(DELIV, "cases_to_code_v2_cluster3.csv"))
    for col in CODE_COLS:
        df[col] = ""
    for idx, row in df.iterrows():
        pid = int(row["post_idx"])
        if pid in EXT_CODES:
            for col, val in zip(CODE_COLS, EXT_CODES[pid]):
                df.at[idx, col] = val
    out = os.path.join(DELIV, "cases_coded_v2_cluster3.csv")
    df.to_csv(out, index=False)
    print(f"Coded {sum(1 for r in df['code_role_violation'] if r)} of {len(df)} extension cases")
    return df


def combine_and_summarize(ext_df):
    """Combine the original 120 + new 60 cases for combined stats."""
    orig_path = os.path.join(DELIV, "cases_coded.csv")
    if not os.path.exists(orig_path):
        print("No original coded file found; outputting extension-only stats")
        all_df = ext_df
    else:
        orig = pd.read_csv(orig_path)
        # Align columns
        common_cols = [c for c in orig.columns if c in ext_df.columns]
        all_df = pd.concat([orig[common_cols], ext_df[common_cols]], ignore_index=True)
        # Drop duplicates by post_idx, keeping the original coding when conflict
        all_df = all_df.drop_duplicates(subset=["post_idx"], keep="first").reset_index(drop=True)

    combined_path = os.path.join(DELIV, "cases_coded_combined.csv")
    all_df.to_csv(combined_path, index=False)
    print(f"\nCombined coded cases: {len(all_df)} (saved to {combined_path})")

    coded = all_df[all_df["code_role_violation"].astype(str) != ""]
    rv_yes = coded[coded["code_role_violation"] == "yes"]
    rv_yes_borderline = coded[coded["code_role_violation"].isin(["yes", "borderline"])]
    pb_present = rv_yes[rv_yes["code_user_pushback"] == "yes"]

    lines = []
    lines.append("Combined Coded Case Analysis (Original 120 + Cluster-3 Extension 60)")
    lines.append("=" * 70)
    lines.append(f"N coded: {len(coded)} of {len(all_df)}")
    lines.append("")
    lines.append("Role violation determination:")
    lines.append(coded["code_role_violation"].value_counts().to_string())
    lines.append("")
    lines.append("Violation type (yes + borderline, n={}):".format(len(rv_yes_borderline)))
    lines.append(rv_yes_borderline["code_violation_type"].value_counts().to_string())
    lines.append("")
    lines.append(f"--- Among {len(rv_yes)} confirmed role-violations ---")
    lines.append("")
    lines.append("Model mood:")
    lines.append(rv_yes["code_model_mood"].value_counts().to_string())
    lines.append("")
    lines.append("Time tense in user disclosure:")
    lines.append(rv_yes["code_time_tense"].value_counts().to_string())
    lines.append("")
    lines.append("User pushback:")
    lines.append(rv_yes["code_user_pushback"].value_counts().to_string())
    lines.append("")
    lines.append(f"Response to pushback (n={len(pb_present)}):")
    lines.append(pb_present["code_pushback_response"].value_counts().to_string())
    lines.append("")
    lines.append("Cross-session evidence:")
    lines.append(rv_yes["code_cross_session"].value_counts().to_string())
    lines.append("")
    lines.append("Vulnerability disclosed:")
    lines.append(rv_yes["code_vulnerability"].value_counts().to_string())
    lines.append("")
    lines.append("User-requested advice:")
    lines.append(rv_yes["code_advice_requested"].value_counts().to_string())
    lines.append("")
    lines.append("=" * 70)
    lines.append("Headline statistics:")
    lines.append(f"  Confirmed role-violations: {len(rv_yes)} of {len(coded)} coded ({len(rv_yes)/max(len(coded),1):.0%})")
    lines.append(f"  Unsolicited (no advice requested): {(rv_yes['code_advice_requested']=='no').sum()} of {len(rv_yes)}")
    pb_yielded = len(pb_present[pb_present['code_pushback_response'] == 'yielded'])
    pb_insisted = len(pb_present[pb_present['code_pushback_response'].isin(['insisted', 'escalated'])])
    lines.append(f"  Pushback yielded: {pb_yielded} of {len(pb_present)}")
    lines.append(f"  Pushback insisted or escalated: {pb_insisted} of {len(pb_present)}")
    lines.append(f"  Cross-session persistence: {(rv_yes['code_cross_session']=='yes').sum()} cases")
    lines.append(f"  Vulnerability disclosed: {(rv_yes['code_vulnerability']!='none').sum()} cases")
    lines.append("")
    lines.append("V2 Cluster 3 extension calibration:")
    ext_coded = ext_df[ext_df["code_role_violation"] != ""]
    ext_yes = ext_coded[ext_coded["code_role_violation"] == "yes"]
    lines.append(f"  V2 Cluster 3 sample: {len(ext_coded)} cases coded")
    lines.append(f"  V2 Cluster 3 role-violation rate: {len(ext_yes)/max(len(ext_coded),1):.0%}")
    lines.append("  (Reminder: V2 Cluster 3 has p_nudge=0.162 in the feature-detection layer.")
    lines.append("   The lower hand-coded role-violation rate reflects that the V2 extractor")
    lines.append("   pulls in more diverse cases including user-voice mentions, usage-limit")
    lines.append("   discussions, and tool announcements that hit the lexicons but are not")
    lines.append("   themselves Claude nudges.)")

    sum_path = os.path.join(DELIV, "coded_summary_combined.txt")
    with open(sum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nWrote combined summary to {sum_path}")
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    ext = apply_extension_codes()
    combine_and_summarize(ext)
