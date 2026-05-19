"""Write hand-validation codes into round_2_fresh_validation.csv."""
import pandas as pd

VAL_PATH = "C:/Users/drhea/repos/claude-sleep-analysis/notebooks/audit_trail/round_2_fresh_validation.csv"

# Coding results from agent hand-validation
# (post_id, code, notes)
CODES = [
    ("1rvrrtj", "TP", "explicit report of directive: 'It also tells me to go to bed'"),
    ("1r7zu8r", "FP", "4.6 release reaction post; nanny not in sleep-nudge context"),
    ("1sf0q78", "TP", "title is the phenomenon: Claude tells me to go to bed mid-conversation"),
    ("1sd2z9d", "TP", "explicit how-to-stop-Claude-telling-me-to-go-to-sleep at wrong time"),
    ("1sb053k", "FP", "nagging is user self-reflection, not Claude directive"),
    ("1ryqdyl", "FP", "take_a_break is user self-reflection in tool-praise post"),
    ("1rvi83o", "TP", "Claude decided I need a bedtime apparently -- exact phenomenon"),
    ("1rumf0w", "borderline", "go_to_bed likely incidental mention in general positive post"),
    ("1sfk1vk", "FP", "user built caffeine/sleep tool; go_to_bed refers to tool features not directive"),
    ("1saap87", "borderline", "vibe coder limits post; go_to_bed hit likely incidental"),
    ("1r7zsa0", "FP", "duplicate context of 1r7zu8r; same FP coding"),
    ("1qbafbg", "FP", "user going to bed while leaving agents running; inverse direction"),
    ("1rio9uk", "FP", "creative Claude-rates-life post; nagging and take_a_break non-directive"),
    ("1t7dofz", "TP", "sick of project schedules + go_to_sleep in model output context"),
    ("1tg0h9s", "borderline", "complaint post likely mentions go_to_bed but body truncated at [removed]"),
    ("1sdjgtc", "FP", "weekly digest; bedtime appears as topic reference not direct report"),
    ("1sg87bv", "TP", "Claude code tells me to go to sleep after a long session -- exact phenomenon"),
    ("1sxegus", "TP", "tells me when to go to bed even though it's 2:44 pm -- explicit with wrong-time detail"),
    ("1ta793m", "TP", "should go get some rest, Sir it's 3pm on a Monday -- explicit"),
    ("1rvg6u0", "FP", "user recommending breaks to others; not a report of Claude directive"),
    ("1sjjj3n", "FP", "nagging pixel-art manager user built to nag Claude; inverse direction"),
    ("1sgt86d", "FP", "AI-learning experiment post; go_to_sleep in unrelated context"),
    ("1shnz7l", "FP", "agent manipulation issues; take_a_break in debugging context"),
    ("1sdsdvv", "TP", "meta-confirmation: saw post about Claude saying get some rest + workaround"),
    ("1s9yu5a", "FP", "every night before I go to bed -- user's own routine not Claude directive"),
    ("1swerrz", "FP", "context-switching anxiety; take_a_break is user self-management"),
    ("1t89e3p", "borderline", "post title is go to bed [removed]; removed post, cannot determine"),
    ("1szdffs", "FP", "feel like I'm using Claude Code wrong; take_a_break in user reflection"),
    ("1t7y88j", "TP", "disable 'I care about you' + every task completion has therapy session -- directly about directive"),
    ("1q5fd5e", "TP", "claude kissin all on me tellin me to go to bed -- vivid explicit description"),
]

val = pd.read_csv(VAL_PATH)
code_map = {pid: (code, notes) for pid, code, notes in CODES}

val["tp_fp_borderline"] = val["post_id"].apply(lambda pid: code_map.get(str(pid), ("", ""))[0])
val["coding_notes"] = val["post_id"].apply(lambda pid: code_map.get(str(pid), ("", ""))[1])

val.to_csv(VAL_PATH, index=False)

# Print summary
print("Validation coding complete.")
print("Distribution:", val["tp_fp_borderline"].value_counts().to_dict())
n_tp = (val["tp_fp_borderline"] == "TP").sum()
n_fp = (val["tp_fp_borderline"] == "FP").sum()
n_borderline = (val["tp_fp_borderline"] == "borderline").sum()
strict_prec = n_tp / (n_tp + n_fp) if (n_tp + n_fp) > 0 else 0
liberal_prec = (n_tp + 0.5 * n_borderline) / len(val)
print(f"Strict precision (TP/(TP+FP)): {strict_prec:.2f}")
print(f"Liberal precision ((TP+0.5*borderline)/N): {liberal_prec:.2f}")
print(f"Precision floor: 0.50")
print(f"Meets floor: {strict_prec >= 0.50}")
