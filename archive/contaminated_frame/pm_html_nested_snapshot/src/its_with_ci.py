"""
Interrupted time series with Newey-West HAC standard errors.

Re-runs the ITS analysis from discourse_features_analysis.py with proper
autocorrelation-consistent inference (Newey & West, 1987).
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

DELIV = "deliverables/"
OPUS_CUTOFF = pd.Timestamp("2026-04-03")


def newey_west_se(X, residuals, lags):
    """Heteroskedasticity- and autocorrelation-consistent covariance.

    Returns standard errors for each coefficient.
    """
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)

    # White (HC0) base
    S0 = np.zeros((k, k))
    for i in range(n):
        S0 += residuals[i] ** 2 * np.outer(X[i], X[i])

    # Add Newey-West correction
    S = S0.copy()
    for L in range(1, lags + 1):
        weight = 1.0 - L / (lags + 1)
        SL = np.zeros((k, k))
        for i in range(L, n):
            SL += residuals[i] * residuals[i - L] * (
                np.outer(X[i], X[i - L]) + np.outer(X[i - L], X[i])
            )
        S += weight * SL

    V = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(V))


def its_with_inference(daily_df, cutoff, value_col, lags=7):
    df = daily_df.copy().sort_values("Date").reset_index(drop=True)
    df["t"] = (df["Date"] - df["Date"].min()).dt.days
    df["post"] = (df["Date"] >= cutoff).astype(int)
    cutoff_t = (cutoff - df["Date"].min()).days
    df["t_post"] = df["post"] * (df["t"] - cutoff_t)

    X = np.column_stack([
        np.ones(len(df)),
        df["t"].values,
        df["post"].values,
        df["t_post"].values,
    ])
    y = df[value_col].values
    n = len(df)
    if n < 10:
        return None

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta

    se = newey_west_se(X, residuals, lags=lags)
    t_stats = beta / se
    df_resid = n - X.shape[1]
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df_resid))

    ci_low = beta - 1.96 * se
    ci_high = beta + 1.96 * se

    return {
        "series": value_col,
        "n_days": n,
        "cutoff": cutoff.date(),
        "intercept": (beta[0], se[0], ci_low[0], ci_high[0], p_values[0]),
        "pre_slope": (beta[1], se[1], ci_low[1], ci_high[1], p_values[1]),
        "level_shift": (beta[2], se[2], ci_low[2], ci_high[2], p_values[2]),
        "slope_change": (beta[3], se[3], ci_low[3], ci_high[3], p_values[3]),
    }


def main():
    daily_path = os.path.join(DELIV, "daily_aggregates.csv")
    daily = pd.read_csv(daily_path)
    daily["Date"] = pd.to_datetime(daily["Date"])

    rows = []
    series_to_test = [
        "Nudge_Rate",
        "AffectiveMean",
        "TemporalMean",
        "FirstPersonMean",
    ]
    for col in series_to_test:
        result = its_with_inference(daily, OPUS_CUTOFF, col, lags=7)
        if result is None:
            continue
        for param in ["intercept", "pre_slope", "level_shift", "slope_change"]:
            est, se, lo, hi, p = result[param]
            rows.append({
                "series": result["series"],
                "n_days": result["n_days"],
                "cutoff": result["cutoff"],
                "parameter": param,
                "estimate": round(est, 6),
                "newey_west_se": round(se, 6),
                "ci_95_low": round(lo, 6),
                "ci_95_high": round(hi, 6),
                "p_value": round(p, 4),
                "significant_at_05": bool(p < 0.05),
            })

    out_df = pd.DataFrame(rows)
    out_path = os.path.join(DELIV, "its_results_with_ci.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Saved {len(out_df)} rows to {out_path}\n")
    print(out_df.to_string(index=False))


if __name__ == "__main__":
    main()
