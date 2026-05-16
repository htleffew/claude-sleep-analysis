"""
Figure generation for Leffew (2026a), "Care Without Consent."

Three figures, each aligned to a load-bearing claim in the paper:

  Figure 1  its_nudge_rate.png   - segmented regression at the Opus 4.7 cutoff
                                   (Section 4.4); the paper argues about the
                                   nudge *rate*, so we plot the rate, not raw
                                   counts.

  Figure 2  violation_types.png  - distribution of the n=60 *confirmed*
                                   role-violations (Section 4.5 / Table 4).
                                   not_violation is excluded by design - it
                                   is the coding outcome, not a violation
                                   type, and including it crushes the scale.

  Figure 3  pmi_lift.png         - directional PMI lift across disclosure
                                   lexicons (Sections 4.2 / 4.3 / Table 1).
                                   Strongest empirical signal in the paper;
                                   previously unvisualized.

Run from the repository root:
    python src/generate_figures.py
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

os.makedirs("figures", exist_ok=True)

# Shared style
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "-",
        "grid.linewidth": 0.5,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }
)

INK = "#2c3e50"
ACCENT = "#c0392b"
ACCENT_SOFT = "#e74c3c"
MUTED = "#7f8c8d"
BAND = "#f4d6cf"

CUTOFF = pd.Timestamp("2026-04-03")


# ---------------------------------------------------------------------------
# Figure 1: ITS on the nudge rate
# ---------------------------------------------------------------------------

df_daily = pd.read_csv("deliverables/daily_aggregates.csv")
df_daily["Date"] = pd.to_datetime(df_daily["Date"])
df_daily = df_daily.sort_values("Date").reset_index(drop=True)

# The ITS in Table 3 was fitted on the 136-day window ending May 16, 2026,
# starting 2026-01-01 (the full series). We replicate the same window.
df_its = df_daily.copy()
df_its["t"] = (df_its["Date"] - df_its["Date"].min()).dt.days
df_its["post"] = (df_its["Date"] >= CUTOFF).astype(int)
t_cut = int((CUTOFF - df_its["Date"].min()).days)
df_its["t_post"] = (df_its["t"] - t_cut).clip(lower=0)

its = pd.read_csv("deliverables/its_results_with_ci.csv")
its = its[its["series"] == "Nudge_Rate"].set_index("parameter")["estimate"]
b0 = float(its.loc["intercept"])
b1 = float(its.loc["pre_slope"])
b2 = float(its.loc["level_shift"])
b3 = float(its.loc["slope_change"])

df_its["fit"] = b0 + b1 * df_its["t"] + b2 * df_its["post"] + b3 * df_its["t_post"]

roll = df_its["Nudge_Rate"].rolling(window=7, min_periods=3, center=True).mean()

fig, ax = plt.subplots(figsize=(9.5, 4.8))

ax.axvspan(CUTOFF, df_its["Date"].max(), color=BAND, alpha=0.4, zorder=0,
           label="Opus 4.7 era")
ax.scatter(df_its["Date"], df_its["Nudge_Rate"], s=10, color=MUTED, alpha=0.45,
           label="Daily rate", zorder=1)
ax.plot(df_its["Date"], roll, color=INK, lw=1.6, label="7-day rolling mean",
        zorder=2)

pre = df_its[df_its["post"] == 0]
post = df_its[df_its["post"] == 1]
ax.plot(pre["Date"], pre["fit"], color=ACCENT, lw=2.2, label="ITS fit (pre)",
        zorder=3)
ax.plot(post["Date"], post["fit"], color=ACCENT, lw=2.2, ls="--",
        label="ITS fit (post)", zorder=3)

ax.axvline(CUTOFF, color=ACCENT, lw=1.0, ls=":", zorder=2)
ax.set_xlabel("Date")
ax.set_ylabel("P(nudge | post)")
ax.set_ylim(0, 0.075)
ax.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=2)

ax.annotate(
    "Opus 4.7 release\nApril 3, 2026",
    xy=(CUTOFF, 0.067),
    xytext=(8, 0),
    textcoords="offset points",
    fontsize=8.5,
    color=ACCENT,
    ha="left",
    va="top",
)

ax.set_title(
    "Nudge rate rose under Sonnet 4.x, attenuated after Opus 4.7\n"
    "Pre-slope $+$0.00013/day (95% CI [$+$0.00003, $+$0.00023], $p=.011$); "
    "level shift $-$0.0065 ($p=.077$)",
    loc="left",
)
ax.text(
    0.01, -0.18,
    "N = 136 days (Jan 1 – May 16, 2026). Newey-West HAC SEs, lag = 7. "
    "Source: deliverables/daily_aggregates.csv, deliverables/its_results_with_ci.csv.",
    transform=ax.transAxes, fontsize=7.5, color=MUTED,
)

plt.savefig("figures/its_nudge_rate.png")
plt.close()


# ---------------------------------------------------------------------------
# Figure 2: confirmed-violation type distribution
# ---------------------------------------------------------------------------

df_coded = pd.read_csv("deliverables/cases_coded_combined.csv")
# Confirmed = code_role_violation == "yes" (n=60). Excludes 110 "no" and 10
# "borderline" rows. Matches the paper's Section 4.5 / Table 4.
confirmed = df_coded[df_coded["code_role_violation"].astype(str).str.lower() == "yes"]
counts = confirmed["code_violation_type"].value_counts().sort_values()

labels = {
    "sleep_nudge": "Sleep nudge",
    "soft_directive": "Soft directive",
    "wellness_checkin": "Wellness check-in",
    "psychiatric": "Psychiatric framing",
    "break_recommendation": "Break recommendation",
    "context_warning": "Context warning",
    "off_topic": "Off-topic",
}
display = [labels.get(k, k.replace("_", " ").title()) for k in counts.index]
n_total = int(counts.sum())
pct = counts / n_total

fig, ax = plt.subplots(figsize=(9.0, 4.4))
bars = ax.barh(display, counts.values, color=INK, alpha=0.85)
# Highlight the top two
for i, b in enumerate(bars):
    if i >= len(bars) - 2:
        b.set_color(ACCENT)

for i, (c, p) in enumerate(zip(counts.values, pct.values)):
    ax.text(
        c + max(counts.values) * 0.012, i,
        f"{c}  ({p:.0%})",
        va="center", fontsize=9, color=INK,
    )

top2_pct = (counts.values[-1] + counts.values[-2]) / n_total
ax.set_title(
    f"Sleep nudge and soft directive account for {top2_pct:.0%} of confirmed violations\n"
    f"Hand-coded role-violations from the n={n_total}-case confirmed subset",
    loc="left",
)
ax.set_xlabel("Cases")
ax.set_xlim(0, max(counts.values) * 1.18)
ax.set_axisbelow(True)
ax.grid(axis="y", visible=False)
ax.text(
    0.01, -0.20,
    f"n = {n_total} confirmed (code_role_violation = yes). "
    "110 not-violation and 10 borderline cases excluded. "
    "Source: deliverables/cases_coded_combined.csv.",
    transform=ax.transAxes, fontsize=7.5, color=MUTED,
)

plt.savefig("figures/violation_types.png")
plt.close()


# ---------------------------------------------------------------------------
# Figure 3: directional PMI lift
# ---------------------------------------------------------------------------

pmi = pd.read_csv("deliverables/pmi_disclosure_nudge.csv")
# Compute lift (P(nudge|lex) / P(nudge))
p_base = pmi["N_with_nudge"].iloc[0] / pmi["N_posts"].iloc[0]
pmi["lift"] = pmi["P_nudge_given_lexicon"] / p_base
pmi = pmi.sort_values("lift")

label_map = {
    "temporal": "Temporal",
    "session": "Session length",
    "affective": "Affective",
    "work_context": "Work context",
}
pmi["label"] = pmi["Disclosure_Lexicon"].map(label_map).fillna(pmi["Disclosure_Lexicon"])

fig, ax = plt.subplots(figsize=(9.0, 3.8))
y = np.arange(len(pmi))

ax.hlines(y, 1.0, pmi["lift"], color=INK, lw=1.4, alpha=0.5)
colors = [ACCENT if v >= 2.0 else INK for v in pmi["lift"]]
ax.scatter(pmi["lift"], y, s=110, color=colors, zorder=3)

for yi, (lift, n_lex) in enumerate(zip(pmi["lift"], pmi["N_with_lexicon"])):
    ax.text(
        lift + 0.12, yi,
        f"{lift:.2f}x  (n={n_lex:,})",
        va="center", fontsize=9, color=INK,
    )

ax.axvline(1.0, color=MUTED, lw=1.0, ls=":")
ax.text(1.02, -0.55, "baseline\nP(nudge) = 2.5%", fontsize=8, color=MUTED)

ax.set_yticks(y)
ax.set_yticklabels(pmi["label"])
ax.set_xlim(0, max(pmi["lift"]) * 1.25)
top_lift = float(pmi["lift"].max())
bot_lift = float(pmi["lift"].min())
ax.set_xlabel("Lift over baseline P(nudge)")
ax.set_title(
    f"Temporal disclosure raises nudge probability {top_lift:.1f}x; "
    f"work-context only {bot_lift:.1f}x\n"
    "Conditional-probability lift across the four user-disclosure lexicons",
    loc="left",
)
ax.set_axisbelow(True)
ax.grid(axis="y", visible=False)
ax.text(
    0.01, -0.28,
    "N = 89,982 posts. Source: deliverables/pmi_disclosure_nudge.csv.",
    transform=ax.transAxes, fontsize=7.5, color=MUTED,
)

plt.savefig("figures/pmi_lift.png")
plt.close()


# ---------------------------------------------------------------------------
# Back-compat: regenerate the old daily_volume.png path as the new ITS plot,
# so any external link continues to resolve to the corrected figure.
# ---------------------------------------------------------------------------
import shutil

shutil.copyfile("figures/its_nudge_rate.png", "figures/daily_volume.png")

print("Generated 3 sleep figures in figures/:")
print("  its_nudge_rate.png  (also mirrored as daily_volume.png)")
print("  violation_types.png")
print("  pmi_lift.png")
