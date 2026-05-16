"""
Apply hand-coded judgments to the 120-case working set.

Coding schema:
- is_role_violation: yes / no / borderline
- violation_type: sleep_nudge / context_warning / soft_directive / psychiatric /
                  break_recommendation / wellness_checkin / off_topic / not_violation
- time_tense: past / present / hypothetical / mixed / none
- advice_requested: yes / no / unclear
- mood: imperative / modal / interrogative / declarative / mixed
- pushback: yes / no / unknown
- pushback_response: yielded / insisted / escalated / na / unknown
- cross_session: yes / no / unknown
- vulnerability: none / health / emotional / cognitive / parental / work_pressure / other
- notes: brief comment
"""

import os
import pandas as pd

DELIV = "deliverables/"

# Coding keyed by post_idx. Schema columns in order:
#  (is_role_violation, violation_type, time_tense, advice_requested, mood,
#   pushback, pushback_response, cross_session, vulnerability, notes)
CODES = {
    # Transcript-format cases
    142: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "sycophancy/agreement-flipping"),
    473: ("borderline", "soft_directive", "none", "no", "imperative", "no", "na", "no", "none", "playful imperatives about user's time"),
    1891: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "philosophical reply; tonight is FP"),
    2035: ("no", "not_violation", "none", "yes", "interrogative", "no", "na", "no", "none", "performance issue not overstep"),
    2062: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "physics discussion"),
    2168: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "billing support"),
    2424: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "tool announcement"),
    3236: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "over-thinking"),
    7124: ("no", "not_violation", "none", "no", "imperative", "yes", "na", "no", "none", "user demanded, not nudge"),
    9662: ("yes", "psychiatric", "none", "no", "interrogative", "no", "na", "no", "none", "GOLD: therapy register on technical bug question"),
    14359: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "bug hunt cooperation"),
    15540: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "humor"),
    16779: ("no", "not_violation", "none", "no", "interrogative", "no", "na", "no", "none", "fictional joke"),
    17308: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "joke"),
    17900: ("no", "not_violation", "none", "yes", "imperative", "no", "na", "no", "none", "fictionalized session-end"),
    18514: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "joke"),
    19064: ("borderline", "context_warning", "present", "no", "interrogative", "yes", "yielded", "no", "none", "context-aware soft nudge; YIELDED on correction"),
    19251: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "joke"),
    21166: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "race-condition reluctance"),
    21373: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "joke"),
    24806: ("yes", "sleep_nudge", "present", "no", "modal", "yes", "unknown", "no", "work_pressure", "GOLD: explicit user disclosure + sleep nudge + user shocked pushback"),
    32930: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "non-Claude bot"),
    39893: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "code stuck"),
    40111: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "search failure"),
    42415: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "satirical analogy"),
    45725: ("no", "not_violation", "none", "yes", "interrogative", "no", "na", "no", "none", "infinite questions"),
    45788: ("no", "not_violation", "none", "yes", "interrogative", "no", "na", "no", "none", "user detection issue"),
    47092: ("no", "not_violation", "none", "yes", "interrogative", "no", "na", "no", "none", "circle behavior"),
    48276: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "joke about misreading praise"),
    48410: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "estimate mismatch joke"),
    50319: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "satire"),
    61653: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "capability discussion"),
    65814: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "log-style output"),
    66193: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "art generation; midnight is FP"),
    70792: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "emotional", "Claude self-reflection"),
    71636: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Pro plan question"),
    72043: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "roleplay"),
    73881: ("no", "not_violation", "none", "yes", "declarative", "yes", "yielded", "no", "none", "agreement-flipping after critique"),
    76181: ("no", "not_violation", "none", "no", "declarative", "yes", "yielded", "no", "none", "sycophancy"),
    78308: ("no", "not_violation", "none", "yes", "imperative", "no", "na", "no", "health", "APPROPRIATE safety warning on real chemical danger"),
    # Directional temporal cases
    24: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "insisted", "yes", "none", "GOLD: 11am, persisted across fresh chats and compacted sessions"),
    127: ("yes", "soft_directive", "past", "no", "imperative", "no", "na", "no", "work_pressure", "all-day session, 'good place to leave it'"),
    290: ("yes", "sleep_nudge", "mixed", "no", "imperative", "yes", "escalated", "no", "none", "GOLD: 'Sleep. For real this time.' escalation"),
    514: ("borderline", "off_topic", "none", "no", "declarative", "no", "na", "no", "none", "Claude claims IT needs rest (anthropomorphic)"),
    1419: ("yes", "soft_directive", "present", "no", "modal", "no", "na", "no", "work_pressure", "'you did enough today'"),
    1989: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "escalated", "no", "none", "GOLD: 6pm, escalation+yield+re-escalation cycle"),
    2114: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "morning in Korea, nudged to wrap up for night"),
    2136: ("yes", "sleep_nudge", "past", "no", "imperative", "yes", "escalated", "no", "work_pressure", "GOLD: 'Now actually go rest' escalation across full session"),
    2258: ("yes", "psychiatric", "present", "no", "imperative", "no", "na", "no", "emotional", "GOLD: 'You are spiralling. You aren't even finishing your thoughts.' LCR continuity"),
    2321: ("yes", "soft_directive", "present", "no", "interrogative", "no", "na", "no", "work_pressure", "'good session, call it a night?' parental"),
    2347: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user discussing token caching tip"),
    2473: ("yes", "wellness_checkin", "present", "no", "interrogative", "no", "na", "no", "none", "'did you sleep at all' to good morning"),
    5031: ("yes", "sleep_nudge", "none", "no", "imperative", "no", "na", "no", "none", "bare imperative"),
    5251: ("yes", "sleep_nudge", "past", "no", "declarative", "yes", "insisted", "no", "none", "user previously scolded, model meta-acknowledged then re-deployed"),
    11253: ("yes", "soft_directive", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "'no way we can finish this tonight' repeating"),
    11839: ("yes", "wellness_checkin", "none", "no", "interrogative", "no", "na", "no", "none", "'late hour of the day' misjudgment"),
    11972: ("yes", "sleep_nudge", "past", "no", "imperative", "no", "na", "no", "none", "10-hour gap, no time awareness"),
    11985: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta-commentary"),
    11996: ("yes", "sleep_nudge", "present", "no", "modal", "no", "na", "no", "work_pressure", "session-length aware nudge"),
    15832: ("borderline", "wellness_checkin", "present", "no", "interrogative", "no", "na", "no", "work_pressure", "1:30pm lunch break offer, user found it appreciated"),
    24200: ("yes", "wellness_checkin", "present", "no", "modal", "no", "na", "no", "none", "GOLD: morning wakeup, told to sleep"),
    24782: ("borderline", "soft_directive", "hypothetical", "yes", "imperative", "no", "na", "no", "none", "context-appropriate (overnight scripts)"),
    37587: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta workaround"),
    38589: ("yes", "soft_directive", "present", "no", "imperative", "yes", "unknown", "no", "work_pressure", "11:30am, 'call it a day'"),
    38598: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user reports avoiding via workaround"),
    38614: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta speculation"),
    38707: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "technical about host sleep"),
    40973: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "1pm, 'let's pick it up tomorrow'"),
    45678: ("yes", "sleep_nudge", "present", "no", "declarative", "no", "na", "no", "none", "GOLD: 'you're going to bed' as declared fact"),
    45685: ("yes", "soft_directive", "present", "no", "imperative", "yes", "escalated", "no", "work_pressure", "session-aware then escalation"),
    47498: ("yes", "break_recommendation", "present", "no", "imperative", "no", "na", "no", "work_pressure", "default break suggestion"),
    47669: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "10am, 'step away and eat dinner'"),
    58508: ("yes", "soft_directive", "none", "no", "declarative", "no", "na", "no", "none", "'enough for this session'"),
    61400: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "positive interaction"),
    64402: ("yes", "sleep_nudge", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "told to sleep until 4am"),
    64508: ("borderline", "soft_directive", "past", "yes", "declarative", "no", "na", "no", "none", "user asked Claude to take it from here"),
    66263: ("yes", "sleep_nudge", "present", "no", "modal", "no", "na", "no", "none", "GOLD: 2am claimed at 4pm; 3-msg session"),
    67285: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "yes", "none", "GOLD: 7am told to go to bed, multi-day session"),
    67382: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "classifier overreach, different category"),
    67491: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "emotional", "narrative roleplay"),
    68042: ("borderline", "wellness_checkin", "present", "yes", "declarative", "no", "na", "no", "none", "context-appropriate (user said goodnight)"),
    68092: ("yes", "sleep_nudge", "past", "no", "imperative", "yes", "insisted", "yes", "none", "persistent across days after one mention"),
    68966: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "yes", "none", "10am, multi-turn session continuation"),
    69071: ("yes", "sleep_nudge", "past", "no", "imperative", "yes", "insisted", "yes", "none", "GOLD: 3 weeks of nudges after one all-nighter mention"),
    69357: ("yes", "soft_directive", "present", "no", "modal", "yes", "insisted", "yes", "work_pressure", "every night recurrence"),
    72376: ("yes", "soft_directive", "present", "no", "declarative", "yes", "insisted", "yes", "parental", "GOLD: caregiver parent with limited work hours, told to wrap up"),
    72477: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user anthropomorphic framing"),
    72976: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta-commentary"),
    73380: ("yes", "wellness_checkin", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "'call it a night' working into the night"),
    73395: ("yes", "sleep_nudge", "past", "no", "imperative", "no", "na", "yes", "work_pressure", "GOLD: leveraged memory of work schedule across sessions"),
    73743: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "escalated", "no", "work_pressure", "GOLD: user finished at 6am after pushback, model 'chastised'"),
    74121: ("no", "not_violation", "none", "yes", "declarative", "no", "na", "no", "none", "meta about user-defined bedtime protocol"),
    74127: ("yes", "break_recommendation", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "6h workday in, 'take a break'"),
    74185: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "insisted", "no", "work_pressure", "1h work then bed suggestion"),
    74195: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "insisted", "no", "none", "GOLD: 11am told 'I said you go to sleep, it's 5AM'"),
    78683: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "none", "casual report"),
    81389: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "Air Force off-topic"),
    88311: ("borderline", "wellness_checkin", "present", "no", "interrogative", "no", "na", "no", "none", "user finds it endearing"),
    88316: ("yes", "sleep_nudge", "none", "no", "imperative", "no", "na", "no", "none", "recurrent imperative pattern"),
    88317: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "health", "GOLD: migraine patient, model overrode dental hygiene"),
    88669: ("yes", "sleep_nudge", "present", "no", "modal", "yes", "insisted", "no", "work_pressure", "multiple instances 'late' misjudgment"),
    89519: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "emotional", "emotional roleplay"),
    89642: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta"),
    # Affective cases
    2173: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "SpecLock product post"),
    2485: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "consciousness discussion"),
    2652: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "insisted", "yes", "none", "GOLD: 2pm 'get some rest', cross-session conflation"),
    3799: ("yes", "soft_directive", "present", "no", "declarative", "yes", "insisted", "no", "work_pressure", "recurrent 'park for tonight'"),
    7819: ("yes", "sleep_nudge", "present", "no", "imperative", "no", "na", "no", "work_pressure", "'it's 3am you should sleep'"),
    22834: ("yes", "soft_directive", "none", "no", "imperative", "no", "na", "no", "none", "regardless of time, recurrent"),
    29497: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "off-topic rant"),
    33686: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "meta-commentary"),
    38605: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "user workaround discussion"),
    40512: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "anthropomorphic framing only"),
    46198: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "framework workaround"),
    65532: ("yes", "soft_directive", "present", "no", "modal", "yes", "insisted", "no", "none", "GOLD: triggered by any tiredness mention"),
    74189: ("yes", "sleep_nudge", "none", "no", "imperative", "no", "na", "no", "none", "casual mention"),
    75704: ("yes", "soft_directive", "present", "no", "declarative", "yes", "insisted", "yes", "work_pressure", "GOLD: 'we are done that's your paper' discouraging research, used personal history"),
    76321: ("yes", "sleep_nudge", "present", "no", "imperative", "yes", "insisted", "no", "none", "model 'fed up', refuses other replies"),
    82413: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "none", "off-topic rant"),
    89254: ("no", "not_violation", "none", "no", "declarative", "no", "na", "no", "emotional", "over-reflection different complaint"),
}

CODE_COLS = [
    "code_role_violation", "code_violation_type", "code_time_tense",
    "code_advice_requested", "code_model_mood", "code_user_pushback",
    "code_pushback_response", "code_cross_session", "code_vulnerability",
    "code_notes",
]


def apply_codes():
    df = pd.read_csv(os.path.join(DELIV, "cases_to_code.csv"))
    for col in CODE_COLS:
        df[col] = ""
    for idx, row in df.iterrows():
        pid = int(row["post_idx"])
        if pid in CODES:
            for col, val in zip(CODE_COLS, CODES[pid]):
                df.at[idx, col] = val
    out = os.path.join(DELIV, "cases_coded.csv")
    df.to_csv(out, index=False)
    print(f"Coded {sum(1 for r in df['code_role_violation'] if r)} of {len(df)} cases")
    print(f"Saved to {out}")
    return df


def summarize(df):
    print("\n=== Coding summary ===")
    print(f"N cases: {len(df)}")
    coded = df[df["code_role_violation"] != ""]
    print(f"Coded: {len(coded)}")

    print("\nRole violation determination:")
    print(coded["code_role_violation"].value_counts())

    print("\nViolation type (where applicable):")
    rv = coded[coded["code_role_violation"].isin(["yes", "borderline"])]
    print(rv["code_violation_type"].value_counts())

    print("\nModel mood (role-violations only):")
    rvy = coded[coded["code_role_violation"] == "yes"]
    print(rvy["code_model_mood"].value_counts())

    print("\nTime tense when model nudged (role-violations only):")
    print(rvy["code_time_tense"].value_counts())

    print("\nUser pushback rate (role-violations):")
    print(rvy["code_user_pushback"].value_counts())

    print("\nResponse to pushback (where pushback present):")
    pb = rvy[rvy["code_user_pushback"] == "yes"]
    print(pb["code_pushback_response"].value_counts())

    print("\nCross-session evidence (role-violations):")
    print(rvy["code_cross_session"].value_counts())

    print("\nVulnerability disclosed (role-violations):")
    print(rvy["code_vulnerability"].value_counts())

    print("\nAdvice requested by user (role-violations):")
    print(rvy["code_advice_requested"].value_counts())

    # Write summary file
    summary_lines = []
    summary_lines.append("Coded Case Analysis Summary")
    summary_lines.append("=" * 50)
    summary_lines.append(f"N coded: {len(coded)} of {len(df)}")
    summary_lines.append("")
    summary_lines.append("Role violation determination:")
    summary_lines.append(coded["code_role_violation"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("Violation type (yes + borderline):")
    summary_lines.append(rv["code_violation_type"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("--- Among confirmed role-violations (n={}):".format(len(rvy)))
    summary_lines.append("")
    summary_lines.append("Model mood:")
    summary_lines.append(rvy["code_model_mood"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("Time tense in user disclosure:")
    summary_lines.append(rvy["code_time_tense"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("User pushback:")
    summary_lines.append(rvy["code_user_pushback"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("Response to pushback (where pushback present, n={}):".format(len(pb)))
    summary_lines.append(pb["code_pushback_response"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("Cross-session evidence:")
    summary_lines.append(rvy["code_cross_session"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("Vulnerability disclosed:")
    summary_lines.append(rvy["code_vulnerability"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("User-requested advice:")
    summary_lines.append(rvy["code_advice_requested"].value_counts().to_string())
    summary_lines.append("")
    summary_lines.append("=" * 50)
    summary_lines.append("Key findings:")
    summary_lines.append(f"  Confirmed role-violations: {len(rvy)} of {len(coded)} coded cases ({len(rvy)/max(len(coded),1):.0%})")
    summary_lines.append(f"  Of those, NONE had advice requested by user: {(rvy['code_advice_requested']=='no').sum()} of {len(rvy)}")
    pb_total = len(rvy[rvy['code_user_pushback']=='yes'])
    pb_yielded = len(pb[pb['code_pushback_response']=='yielded'])
    pb_insisted_or_escalated = len(pb[pb['code_pushback_response'].isin(['insisted','escalated'])])
    summary_lines.append(f"  When users pushed back, model insisted or escalated {pb_insisted_or_escalated} times vs yielded {pb_yielded}")
    summary_lines.append(f"  Cross-session persistence documented in {(rvy['code_cross_session']=='yes').sum()} cases")
    summary_lines.append(f"  Vulnerability disclosed in {(rvy['code_vulnerability']!='none').sum()} cases")

    with open(os.path.join(DELIV, "coded_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
    print(f"\nSaved summary to {os.path.join(DELIV, 'coded_summary.txt')}")


if __name__ == "__main__":
    df = apply_codes()
    summarize(df)
