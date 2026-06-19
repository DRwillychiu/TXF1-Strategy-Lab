#!/usr/bin/env python3
"""Compute portfolio-level Sharpe ratios under different weightings."""
import json
import math
from collections import defaultdict
from datetime import datetime

INPUT_JSON = r"C:\Users\User\Desktop\TXF1-Strategy-Lab\scripts\_temp_portfolio_pnl.json"
OUTPUT_MD = r"C:\Users\User\Desktop\TXF1-Strategy-Lab\scripts\_temp_sharpe_analysis.md"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

strategies = list(data.keys())
print(f"Strategies: {strategies}")

# Aggregate to monthly P&L per strategy
def to_monthly(daily_pnl: dict) -> dict:
    monthly = defaultdict(float)
    for date_str, pnl in daily_pnl.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        key = (dt.year, dt.month)
        monthly[key] += pnl
    return dict(monthly)

monthly_per_strat = {s: to_monthly(data[s]) for s in strategies}

# Union of months across all strategies, then back-fill with zero for any
# month a strategy didn't trade in (still in study period)
all_months_set = set()
for s in strategies:
    all_months_set.update(monthly_per_strat[s].keys())
all_months = sorted(all_months_set)
print(f"Total months in union: {len(all_months)}")

# Build matrix: rows = months, cols = strategy
def aligned_monthly(strategy: str) -> list:
    m = monthly_per_strat[strategy]
    return [m.get(month, 0.0) for month in all_months]

matrix = {s: aligned_monthly(s) for s in strategies}
n_months = len(all_months)

# Statistics helpers
def mean(xs):
    return sum(xs) / len(xs)

def stdev(xs, ddof=1):
    if len(xs) <= ddof:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - ddof)
    return math.sqrt(var)

def sharpe_annual_monthly(xs):
    s = stdev(xs)
    if s == 0:
        return float('nan')
    return mean(xs) / s * math.sqrt(12)

def variance(xs, ddof=1):
    return stdev(xs, ddof) ** 2

def covariance(xs, ys, ddof=1):
    if len(xs) != len(ys) or len(xs) <= ddof:
        return 0.0
    mx, my = mean(xs), mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - ddof)

# Per-strategy stats
ind_stats = {}
for s in strategies:
    xs = matrix[s]
    ind_stats[s] = {
        "mean_monthly": mean(xs),
        "std_monthly": stdev(xs),
        "sharpe_annual": sharpe_annual_monthly(xs),
        "total_pnl": sum(xs),
        "n_active_months": sum(1 for x in xs if x != 0),
    }

# Build covariance matrix
cov = {(s1, s2): covariance(matrix[s1], matrix[s2]) for s1 in strategies for s2 in strategies}

def port_monthly(weights: dict):
    # weights: strategy -> weight (sum = 1)
    return [sum(weights[s] * matrix[s][i] for s in strategies) for i in range(n_months)]

def port_sharpe(weights: dict):
    p = port_monthly(weights)
    return sharpe_annual_monthly(p)

def port_variance(weights: dict):
    # var = sum_i sum_j w_i w_j cov_ij
    total = 0.0
    for s1 in strategies:
        for s2 in strategies:
            total += weights[s1] * weights[s2] * cov[(s1, s2)]
    return total

# 2) Equal weight
eq_w = {s: 1.0 / len(strategies) for s in strategies}
eq_monthly = port_monthly(eq_w)
eq_sharpe = sharpe_annual_monthly(eq_monthly)
eq_mean = mean(eq_monthly)
eq_std = stdev(eq_monthly)

# 3) Best-Sharpe portfolio via grid search (0.1 step, weights >= 0, sum = 1)
def enumerate_weights(n: int, step: float = 0.1):
    """Enumerate non-neg integer weights w_i in 0..N s.t. sum = N (N = 1/step)."""
    N = int(round(1.0 / step))
    res = []
    def rec(remaining_slots, remaining_total, current):
        if remaining_slots == 1:
            current.append(remaining_total)
            res.append(tuple(current))
            current.pop()
            return
        for k in range(0, remaining_total + 1):
            current.append(k)
            rec(remaining_slots - 1, remaining_total - k, current)
            current.pop()
    rec(n, N, [])
    return [tuple(w / N for w in t) for t in res]

print("Generating weight grid (this can be large)...")
grid = enumerate_weights(len(strategies), step=0.1)
print(f"Grid size: {len(grid)}")

best_sharpe = -float('inf')
best_w_sharpe = None
min_var = float('inf')
best_w_var = None

for wt in grid:
    wd = {s: w for s, w in zip(strategies, wt)}
    sh = port_sharpe(wd)
    if sh != sh:  # nan
        continue
    if sh > best_sharpe:
        best_sharpe = sh
        best_w_sharpe = wd
    var = port_variance(wd)
    if var < min_var and var > 0:
        min_var = var
        best_w_var = wd

best_sharpe_monthly = port_monthly(best_w_sharpe)
best_sharpe_mean = mean(best_sharpe_monthly)
best_sharpe_std = stdev(best_sharpe_monthly)

min_var_monthly = port_monthly(best_w_var)
min_var_sharpe = sharpe_annual_monthly(min_var_monthly)
min_var_mean = mean(min_var_monthly)
min_var_std = stdev(min_var_monthly)

# 5) Naive risk parity
inv_std = {s: (1.0 / ind_stats[s]["std_monthly"]) if ind_stats[s]["std_monthly"] > 0 else 0 for s in strategies}
tot = sum(inv_std.values())
rp_w = {s: inv_std[s] / tot for s in strategies}
rp_monthly = port_monthly(rp_w)
rp_sharpe = sharpe_annual_monthly(rp_monthly)
rp_mean = mean(rp_monthly)
rp_std = stdev(rp_monthly)

# Sum of individual Sharpe vs equal-weight portfolio Sharpe
sum_ind_sharpe = sum(ind_stats[s]["sharpe_annual"] for s in strategies)
diversification_ratio = eq_sharpe / sum_ind_sharpe if sum_ind_sharpe != 0 else float('nan')

# 7) Drop-one analysis (equal-weight among remaining 5)
drop_one = {}
for drop in strategies:
    remaining = [s for s in strategies if s != drop]
    w = {s: 1.0 / len(remaining) for s in remaining}
    # build monthly with only remaining
    p = [sum(w[s] * matrix[s][i] for s in remaining) for i in range(n_months)]
    sh = sharpe_annual_monthly(p)
    drop_one[drop] = {
        "sharpe_without": sh,
        "marginal_value": eq_sharpe - sh,  # positive = strategy improves portfolio
    }

# Correlation matrix
def correlation(s1, s2):
    sd1 = ind_stats[s1]["std_monthly"]
    sd2 = ind_stats[s2]["std_monthly"]
    if sd1 == 0 or sd2 == 0:
        return float('nan')
    return cov[(s1, s2)] / (sd1 * sd2)

corr_matrix = {(s1, s2): correlation(s1, s2) for s1 in strategies for s2 in strategies}

# ---- Build markdown report ----
lines = []
lines.append("# Portfolio Sharpe Analysis (Multi-Weight)\n")
lines.append(f"- Source data: `{INPUT_JSON}`")
lines.append(f"- Strategies analyzed: {', '.join(strategies)}  (n = {len(strategies)})")
lines.append(f"- Time grid: {n_months} months from {all_months[0][0]}-{all_months[0][1]:02d} to {all_months[-1][0]}-{all_months[-1][1]:02d}")
lines.append(f"- Annualization: monthly stats x sqrt(12)")
lines.append(f"- Missing months filled with zero PnL (strategy idle)\n")

# Section 1
lines.append("## 1. Individual Strategy Sharpe (Annual)\n")
lines.append("| Strategy | Mean Monthly NTD | Std Monthly NTD | Annual Sharpe | Total PnL | Active Months |")
lines.append("|---|---:|---:|---:|---:|---:|")
for s in strategies:
    d = ind_stats[s]
    lines.append(f"| {s} | {d['mean_monthly']:,.0f} | {d['std_monthly']:,.0f} | {d['sharpe_annual']:.3f} | {d['total_pnl']:,.0f} | {d['n_active_months']} |")
lines.append("")

# Section 2
lines.append("## 2. Sum of Individual Sharpe\n")
lines.append(f"- Sum of individual annual Sharpe: **{sum_ind_sharpe:.3f}**")
lines.append("- Note: this is *not* the achievable portfolio Sharpe — it's a benchmark for diversification analysis.\n")

# Section 3
lines.append("## 3. Equal-Weight Portfolio (1/6 each)\n")
lines.append(f"- Mean monthly: **{eq_mean:,.0f} NTD**")
lines.append(f"- Std monthly: **{eq_std:,.0f} NTD**")
lines.append(f"- Annual Sharpe: **{eq_sharpe:.3f}**\n")

# Section 4
lines.append("## 4. Optimized-Weight Portfolio (Max Sharpe, grid 0.1 step)\n")
lines.append(f"- Annual Sharpe: **{best_sharpe:.3f}**")
lines.append(f"- Mean monthly: {best_sharpe_mean:,.0f} NTD")
lines.append(f"- Std monthly: {best_sharpe_std:,.0f} NTD")
lines.append("- Weights:")
for s in strategies:
    lines.append(f"  - {s}: {best_w_sharpe[s]*100:.0f}%")
lines.append("")

# Section 5
lines.append("## 5. Min-Variance Portfolio (grid 0.1 step)\n")
lines.append(f"- Annual Sharpe: **{min_var_sharpe:.3f}**")
lines.append(f"- Mean monthly: {min_var_mean:,.0f} NTD")
lines.append(f"- Std monthly: {min_var_std:,.0f} NTD")
lines.append(f"- Monthly variance: {min_var:,.0f}")
lines.append("- Weights:")
for s in strategies:
    lines.append(f"  - {s}: {best_w_var[s]*100:.0f}%")
lines.append("")

# Section 5b: Risk-parity
lines.append("## 5b. Naive Risk-Parity Portfolio (w_i proportional to 1/std_i)\n")
lines.append(f"- Annual Sharpe: **{rp_sharpe:.3f}**")
lines.append(f"- Mean monthly: {rp_mean:,.0f} NTD")
lines.append(f"- Std monthly: {rp_std:,.0f} NTD")
lines.append("- Weights:")
for s in strategies:
    lines.append(f"  - {s}: {rp_w[s]*100:.1f}%")
lines.append("")

# Section 6
lines.append("## 6. Diversification Benefit\n")
lines.append("| Metric | Value |")
lines.append("|---|---:|")
lines.append(f"| Sum of individual annual Sharpe | {sum_ind_sharpe:.3f} |")
lines.append(f"| Equal-weight portfolio Sharpe | {eq_sharpe:.3f} |")
lines.append(f"| Max-Sharpe portfolio Sharpe | {best_sharpe:.3f} |")
lines.append(f"| Min-Variance portfolio Sharpe | {min_var_sharpe:.3f} |")
lines.append(f"| Risk-parity portfolio Sharpe | {rp_sharpe:.3f} |")
lines.append(f"| Diversification ratio (EW / Sum-of-Sharpe) | {diversification_ratio:.3f} |")
lines.append(f"| Diversification ratio (MaxSharpe / Sum-of-Sharpe) | {best_sharpe/sum_ind_sharpe:.3f} |")
lines.append("")
lines.append("**Interpretation:** Because individual Sharpe values do *not* add (Sharpe scales with mean/sigma and sigma is sub-additive when correlations < 1), a diversification ratio >> 1 indicates the portfolio is materially more efficient than the average of its parts.\n")

# Correlation matrix
lines.append("### 6b. Correlation Matrix (monthly PnL)\n")
header = "| | " + " | ".join(strategies) + " |"
sep = "|---|" + "|".join("---:" for _ in strategies) + "|"
lines.append(header)
lines.append(sep)
for s1 in strategies:
    row = [s1] + [f"{corr_matrix[(s1, s2)]:.2f}" for s2 in strategies]
    lines.append("| " + " | ".join(row) + " |")
lines.append("")

# Section 7
lines.append("## 7. Drop-One Marginal Contribution (vs. Equal-Weight)\n")
lines.append("For each strategy, recompute equal-weight Sharpe on the remaining 5. The drop in Sharpe = that strategy's marginal value.\n")
lines.append("| Dropped Strategy | Sharpe Without | Marginal Value (EW - Without) | Verdict |")
lines.append("|---|---:|---:|---|")
ranked = sorted(strategies, key=lambda s: drop_one[s]["marginal_value"], reverse=True)
for s in strategies:
    mv = drop_one[s]["marginal_value"]
    sh_wo = drop_one[s]["sharpe_without"]
    if mv > 0.10:
        verdict = "ESSENTIAL (large drop without it)"
    elif mv > 0.02:
        verdict = "Valuable"
    elif mv > -0.02:
        verdict = "Roughly neutral"
    else:
        verdict = "Disposable (portfolio improves without it)"
    lines.append(f"| {s} | {sh_wo:.3f} | {mv:+.3f} | {verdict} |")
lines.append("")
lines.append("Ranked by marginal value (highest = most essential):")
for s in ranked:
    lines.append(f"- {s}: {drop_one[s]['marginal_value']:+.3f}")
lines.append("")

# Section 8: recommended weights
lines.append("## 8. Recommended Weights\n")

# Heuristic recommendation: blend Max-Sharpe with floor on each strategy
# We construct a "sensible" portfolio: Max-Sharpe but with min 5% per kept strategy
# To avoid putting >50% in one strategy.
# But just present the analytical alternatives clearly.

lines.append("### Three plausible allocations\n")
lines.append("| Strategy | Max-Sharpe | Min-Variance | Risk-Parity | Equal-Weight |")
lines.append("|---|---:|---:|---:|---:|")
for s in strategies:
    lines.append(f"| {s} | {best_w_sharpe[s]*100:.0f}% | {best_w_var[s]*100:.0f}% | {rp_w[s]*100:.1f}% | {1/len(strategies)*100:.1f}% |")
lines.append(f"| **Sharpe** | **{best_sharpe:.3f}** | **{min_var_sharpe:.3f}** | **{rp_sharpe:.3f}** | **{eq_sharpe:.3f}** |")
lines.append("")

# Recommendation block
disposable = [s for s in strategies if drop_one[s]["marginal_value"] < -0.02]
essential = [s for s in strategies if drop_one[s]["marginal_value"] > 0.10]

lines.append("### Discussion\n")
lines.append(f"- **Essential strategies** (dropping them hurts the portfolio significantly): {', '.join(essential) if essential else 'None at the +0.10 threshold'}")
lines.append(f"- **Disposable strategies** (portfolio Sharpe actually improves without them): {', '.join(disposable) if disposable else 'None — every strategy adds value'}")
lines.append("")
lines.append("**Recommended live allocation (operator's judgment, blending Max-Sharpe with diversification floor):**\n")

# Build a recommended weight: keep weights >= 5% floor on every strategy unless drop-one shows negative
# Practical recommendation: Max-Sharpe weights are the math optimum; risk-parity is the
# operational default.
lines.append("- For **maximum risk-adjusted return** under this dataset: use the **Max-Sharpe** weights above.")
lines.append("- For **lower drawdown / steadier equity curve**: use **Min-Variance** weights.")
lines.append("- For a **balanced, robust** allocation that doesn't depend on one strategy's edge holding up: use **Risk-Parity** weights — it gives each strategy similar risk contribution and is less prone to overfitting.\n")

# Flagged pairs
lines.append("### Flagged high-correlation pairs (|rho| > 0.30)\n")
flagged = []
for i, s1 in enumerate(strategies):
    for s2 in strategies[i+1:]:
        c = corr_matrix[(s1, s2)]
        if abs(c) > 0.30:
            flagged.append((s1, s2, c))
            lines.append(f"- {s1} vs {s2}: rho = {c:+.2f}")
if not flagged:
    lines.append("- No pairs above 0.30. All strategy pairs are low-correlation, supporting strong diversification.")
lines.append("")

# Write output
with open(OUTPUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nWritten: {OUTPUT_MD}")
print(f"\nKey numbers:")
print(f"  Sum of individual Sharpe: {sum_ind_sharpe:.3f}")
print(f"  Equal-weight Sharpe: {eq_sharpe:.3f}")
print(f"  Max-Sharpe Sharpe: {best_sharpe:.3f}")
print(f"  Min-Var Sharpe: {min_var_sharpe:.3f}")
print(f"  Risk-Parity Sharpe: {rp_sharpe:.3f}")
print(f"\nMax-Sharpe weights:")
for s in strategies:
    print(f"  {s}: {best_w_sharpe[s]*100:.0f}%")
print(f"\nMin-Var weights:")
for s in strategies:
    print(f"  {s}: {best_w_var[s]*100:.0f}%")
print(f"\nDrop-one marginal values:")
for s in strategies:
    print(f"  drop {s}: Sharpe -> {drop_one[s]['sharpe_without']:.3f}  (marginal {drop_one[s]['marginal_value']:+.3f})")
print(f"\nFlagged pairs (|rho|>0.30):")
for s1, s2, c in flagged:
    print(f"  {s1} vs {s2}: {c:+.2f}")
