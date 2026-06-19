"""
Rolling correlation analysis for P0-1 flagged pairs.
Investigates whether Pearson correlations are fat-tail driven artifacts.
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Load PnL data
pnl_path = Path("C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
with open(pnl_path, "r", encoding="utf-8") as f:
    raw = json.load(f)

# Build daily DataFrame for all strategies
strategies = list(raw.keys())
print(f"Strategies found: {strategies}")

# Convert to DataFrame
df_dict = {}
for strat in strategies:
    s = pd.Series(raw[strat])
    s.index = pd.to_datetime(s.index)
    df_dict[strat] = s

daily = pd.DataFrame(df_dict).fillna(0.0)
daily = daily.sort_index()
print(f"Daily shape: {daily.shape}")
print(f"Date range: {daily.index.min()} ~ {daily.index.max()}")

# Aggregate to monthly
monthly = daily.resample("ME").sum()
print(f"Monthly shape: {monthly.shape}")


def spearman_corr(s1, s2):
    """Spearman = Pearson on ranks (no scipy needed)."""
    df = pd.concat([s1, s2], axis=1).dropna()
    if len(df) < 3:
        return float("nan")
    r1 = df.iloc[:, 0].rank()
    r2 = df.iloc[:, 1].rank()
    return r1.corr(r2, method="pearson")

# Define flagged pairs
pairs = [
    ("L2", "L4"),
    ("L1", "L5"),
    ("L5", "S1"),
    ("L1", "S1"),
]

# Filter to available
pairs = [(a, b) for a, b in pairs if a in monthly.columns and b in monthly.columns]
print(f"Pairs to analyze: {pairs}")

# Container for results
results = {}

for a, b in pairs:
    pair_key = f"{a}-{b}"
    print(f"\n=== {pair_key} ===")

    # Full-sample correlations
    full_pearson = monthly[a].corr(monthly[b], method="pearson")
    full_spearman = spearman_corr(monthly[a], monthly[b])

    # Rolling 12-month
    roll12 = monthly[a].rolling(12).corr(monthly[b])
    # Rolling 6-month
    roll6 = monthly[a].rolling(6).corr(monthly[b])

    # Stats on rolling
    r12_valid = roll12.dropna()
    r6_valid = roll6.dropna()

    r12_median = r12_valid.median()
    r12_mean = r12_valid.mean()
    r12_std = r12_valid.std()
    r12_min = r12_valid.min()
    r12_max = r12_valid.max()

    r6_median = r6_valid.median()
    r6_std = r6_valid.std()
    r6_min = r6_valid.min()
    r6_max = r6_valid.max()

    # Sign flip detection
    n_pos = (r12_valid > 0.1).sum()
    n_neg = (r12_valid < -0.1).sum()
    n_zero = ((r12_valid >= -0.1) & (r12_valid <= 0.1)).sum()

    # Stability score
    if abs(r12_median) > 1e-6:
        stability = r12_std / abs(r12_median)
    else:
        stability = float("inf")

    # Top 5 fat-tail months (joint magnitude = |a| * |b|)
    joint_mag = (monthly[a].abs() * monthly[b].abs()).sort_values(ascending=False)
    top5_months = joint_mag.head(5)

    # Recompute Pearson WITHOUT those 5 months
    keep_idx = monthly.index.difference(top5_months.index)
    monthly_clean = monthly.loc[keep_idx]
    clean_pearson = monthly_clean[a].corr(monthly_clean[b], method="pearson")
    clean_spearman = spearman_corr(monthly_clean[a], monthly_clean[b])

    # Per-month detail for top5
    top5_detail = []
    for dt in top5_months.index:
        top5_detail.append({
            "month": dt.strftime("%Y-%m"),
            f"{a}_pnl": float(monthly.loc[dt, a]),
            f"{b}_pnl": float(monthly.loc[dt, b]),
            "joint_mag": float(joint_mag.loc[dt]),
        })

    # Verdict heuristic — ordered by strength of evidence
    pearson_collapse_pct = (full_pearson - clean_pearson) / abs(full_pearson) if abs(full_pearson) > 1e-6 else 0
    # Sign flip in rolling: meaningful positive AND negative regimes
    rolling_sign_flip = n_pos >= 5 and n_neg >= 5
    # Outlier sign flip: full-sample and clean Pearson have opposite signs
    outlier_sign_flip = (full_pearson * clean_pearson < 0)
    severe_collapse = abs(pearson_collapse_pct) > 0.5

    # Priority 1: if removing 5 outliers flips the sign AND clean Pearson is small → ARTIFACT
    # Even if rolling oscillates, the headline number itself is fake.
    if outlier_sign_flip and abs(clean_pearson) < 0.25:
        verdict = "ARTIFACT"
    # Priority 2: severe magnitude collapse → ARTIFACT
    elif severe_collapse and abs(clean_pearson) < 0.20:
        verdict = "ARTIFACT"
    # Priority 3: rolling sign-flips with stable-ish magnitude → TIME-VARYING
    elif rolling_sign_flip and stability > 1.0:
        verdict = "TIME-VARYING"
    # Priority 4: low stability + no rolling flips → STRUCTURAL
    elif stability < 1.0 and not rolling_sign_flip:
        verdict = "STRUCTURAL"
    else:
        # Mixed signals
        if rolling_sign_flip:
            verdict = "TIME-VARYING"
        elif severe_collapse:
            verdict = "ARTIFACT"
        else:
            verdict = "STRUCTURAL"

    # Save rolling series snapshots (key months only)
    r12_series_pts = []
    for dt, val in r12_valid.items():
        r12_series_pts.append({"month": dt.strftime("%Y-%m"), "r12": float(val)})

    results[pair_key] = {
        "full_pearson": float(full_pearson),
        "full_spearman": float(full_spearman),
        "roll12_median": float(r12_median),
        "roll12_mean": float(r12_mean),
        "roll12_std": float(r12_std),
        "roll12_min": float(r12_min),
        "roll12_max": float(r12_max),
        "roll12_n_pos": int(n_pos),
        "roll12_n_neg": int(n_neg),
        "roll12_n_zero": int(n_zero),
        "roll12_n_total": int(len(r12_valid)),
        "roll6_median": float(r6_median),
        "roll6_std": float(r6_std),
        "roll6_min": float(r6_min),
        "roll6_max": float(r6_max),
        "stability_score": float(stability),
        "top5_months": top5_detail,
        "clean_pearson": float(clean_pearson),
        "clean_spearman": float(clean_spearman),
        "pearson_collapse_pct": float(pearson_collapse_pct),
        "verdict": verdict,
        "r12_series": r12_series_pts,
    }

    print(f"  Full Pearson : {full_pearson:+.3f}")
    print(f"  Full Spearman: {full_spearman:+.3f}")
    print(f"  Rolling-12 median: {r12_median:+.3f}, std: {r12_std:.3f}")
    print(f"  Rolling-12 range : [{r12_min:+.3f}, {r12_max:+.3f}]")
    print(f"  Rolling-12 pos/neg/zero: {n_pos}/{n_neg}/{n_zero} (of {len(r12_valid)})")
    print(f"  Stability score   : {stability:.3f}")
    print(f"  Clean Pearson (-5): {clean_pearson:+.3f} (collapse {pearson_collapse_pct:+.1%})")
    print(f"  Verdict: {verdict}")

# Save raw results JSON
out_json = Path("C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_rolling_corr_raw.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults JSON saved: {out_json}")

# Generate Markdown report
md_lines = []
md_lines.append("# P0-1 Rolling Correlation Analysis (Fat-Tail Verification)")
md_lines.append("")
md_lines.append(f"_Generated: 2026-06-19_")
md_lines.append("")
md_lines.append("---")
md_lines.append("")
md_lines.append("## 1. Methodology")
md_lines.append("")
md_lines.append("**Question**: For pairs where Pearson and Spearman disagree (esp. L2-L4 Pearson +0.614 vs Spearman -0.174),")
md_lines.append("is the Pearson correlation a genuine structural link or an artifact driven by a handful of fat-tail months?")
md_lines.append("")
md_lines.append("**Data**:")
md_lines.append(f"- Daily PnL from `_temp_portfolio_pnl.json`")
md_lines.append(f"- Date range: {daily.index.min().date()} ~ {daily.index.max().date()}")
md_lines.append(f"- Aggregated to monthly sums (N = {len(monthly)} months)")
md_lines.append("")
md_lines.append("**Tests per pair**:")
md_lines.append("1. **Rolling 12-month Pearson correlation** — monthly series, 12-month window")
md_lines.append("2. **Rolling 6-month Pearson correlation** — faster sensitivity to regime shifts")
md_lines.append("3. **Top-5 fat-tail months** — ranked by joint magnitude `|pnl_A| * |pnl_B|`")
md_lines.append("4. **Outlier-removal Pearson** — recompute correlation after dropping those 5 months")
md_lines.append("5. **Stability score** = `std(rolling_12mo_corr) / |median(rolling_12mo_corr)|`")
md_lines.append("   - <0.5: very stable; 0.5-1.0: stable; 1.0-2.0: unstable; >2.0: regime-dependent")
md_lines.append("")
md_lines.append("**Verdict logic**:")
md_lines.append("- **STRUCTURAL**: rolling correlation stable, sign doesn't flip, outlier removal preserves Pearson")
md_lines.append("- **ARTIFACT**: full-sample Pearson collapses (>50% magnitude loss or sign flip) when 5 outliers removed")
md_lines.append("- **TIME-VARYING**: rolling correlation crosses zero with meaningful positive AND negative regimes (each >2 months at |r|>0.1)")
md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Section 2: per-pair rolling stats
md_lines.append("## 2. Per-Pair Rolling Correlation Series")
md_lines.append("")
md_lines.append("| Pair | Full Pearson | Full Spearman | Roll-12 Median | Roll-12 Std | Roll-12 Min | Roll-12 Max | Roll-6 Median | Roll-6 Std | Stability |")
md_lines.append("|------|-------------:|--------------:|---------------:|------------:|------------:|------------:|--------------:|-----------:|----------:|")
for pair_key, r in results.items():
    md_lines.append(
        f"| **{pair_key}** | {r['full_pearson']:+.3f} | {r['full_spearman']:+.3f} | "
        f"{r['roll12_median']:+.3f} | {r['roll12_std']:.3f} | "
        f"{r['roll12_min']:+.3f} | {r['roll12_max']:+.3f} | "
        f"{r['roll6_median']:+.3f} | {r['roll6_std']:.3f} | "
        f"{r['stability_score']:.2f} |"
    )
md_lines.append("")

md_lines.append("### Rolling-12 regime distribution")
md_lines.append("")
md_lines.append("How many 12-month windows show positive (>+0.1), neutral, or negative (<-0.1) correlation:")
md_lines.append("")
md_lines.append("| Pair | Pos windows | Neutral | Neg windows | Total | Sign-flip? |")
md_lines.append("|------|------------:|--------:|------------:|------:|:----------:|")
for pair_key, r in results.items():
    flip = "YES" if (r["roll12_n_pos"] > 2 and r["roll12_n_neg"] > 2) else "no"
    md_lines.append(
        f"| **{pair_key}** | {r['roll12_n_pos']} | {r['roll12_n_zero']} | "
        f"{r['roll12_n_neg']} | {r['roll12_n_total']} | {flip} |"
    )
md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Section 3: outlier removal
md_lines.append("## 3. Outlier-Month Removal Test")
md_lines.append("")
md_lines.append("For each pair, the 5 months with highest joint magnitude `|pnl_A| * |pnl_B|` are dropped.")
md_lines.append("If full-sample Pearson collapses, the original number was fat-tail driven (artifact).")
md_lines.append("")
md_lines.append("| Pair | Full Pearson | Clean Pearson (-5 outliers) | Collapse % | Clean Spearman | Diagnosis |")
md_lines.append("|------|-------------:|----------------------------:|-----------:|---------------:|:----------|")
for pair_key, r in results.items():
    diag = ""
    if abs(r["full_pearson"]) > 1e-6:
        ratio = r["clean_pearson"] / r["full_pearson"]
        if r["full_pearson"] * r["clean_pearson"] < 0:
            diag = "Sign FLIPPED — strong artifact"
        elif abs(ratio) < 0.3:
            diag = "Severe collapse"
        elif abs(ratio) < 0.6:
            diag = "Moderate collapse"
        else:
            diag = "Stable across outlier removal"
    md_lines.append(
        f"| **{pair_key}** | {r['full_pearson']:+.3f} | {r['clean_pearson']:+.3f} | "
        f"{r['pearson_collapse_pct']:+.1%} | {r['clean_spearman']:+.3f} | {diag} |"
    )
md_lines.append("")

# Top 5 fat-tail months per pair
md_lines.append("### Top-5 joint-magnitude months per pair")
md_lines.append("")
for pair_key, r in results.items():
    a, b = pair_key.split("-")
    md_lines.append(f"#### {pair_key}")
    md_lines.append("")
    md_lines.append(f"| Month | {a} PnL | {b} PnL | Joint magnitude | Same sign? |")
    md_lines.append("|-------|--------:|--------:|----------------:|:----------:|")
    for row in r["top5_months"]:
        a_pnl = row[f"{a}_pnl"]
        b_pnl = row[f"{b}_pnl"]
        same = "YES" if (a_pnl * b_pnl > 0) else "no (opposing)"
        md_lines.append(
            f"| {row['month']} | {a_pnl:+,.0f} | {b_pnl:+,.0f} | "
            f"{row['joint_mag']:,.0f} | {same} |"
        )
    md_lines.append("")
md_lines.append("---")
md_lines.append("")

# Section 4: verdicts
md_lines.append("## 4. Verdict Per Pair")
md_lines.append("")
md_lines.append("| Pair | Full Pearson | Clean Pearson | Roll-12 Stability | Verdict |")
md_lines.append("|------|-------------:|--------------:|------------------:|:--------|")
for pair_key, r in results.items():
    md_lines.append(
        f"| **{pair_key}** | {r['full_pearson']:+.3f} | {r['clean_pearson']:+.3f} | "
        f"{r['stability_score']:.2f} | **{r['verdict']}** |"
    )
md_lines.append("")

# Per-pair narrative
for pair_key, r in results.items():
    md_lines.append(f"### {pair_key} → {r['verdict']}")
    md_lines.append("")
    md_lines.append(f"- Full-sample Pearson: **{r['full_pearson']:+.3f}**, Spearman: **{r['full_spearman']:+.3f}** (delta {r['full_pearson']-r['full_spearman']:+.3f})")
    md_lines.append(f"- Rolling-12 median: **{r['roll12_median']:+.3f}**, range `[{r['roll12_min']:+.3f}, {r['roll12_max']:+.3f}]`, std {r['roll12_std']:.3f}")
    md_lines.append(f"- After removing top-5 fat-tail months: Pearson **{r['clean_pearson']:+.3f}** ({r['pearson_collapse_pct']:+.1%} change)")
    md_lines.append(f"- Sign-flip windows: {r['roll12_n_pos']} positive / {r['roll12_n_neg']} negative")
    md_lines.append("")

md_lines.append("---")
md_lines.append("")
md_lines.append("## 5. Implication for L4 Keep-or-Cut Decision")
md_lines.append("")

# L2-L4 specific
l2l4 = results.get("L2-L4")
l1l5 = results.get("L1-L5")
l5s1 = results.get("L5-S1")
l1s1 = results.get("L1-S1")

if l2l4:
    md_lines.append(f"### L2-L4 finding (verdict: **{l2l4['verdict']}**)")
    md_lines.append("")
    md_lines.append(f"- The headline Pearson **{l2l4['full_pearson']:+.3f}** vs Spearman **{l2l4['full_spearman']:+.3f}** divergence is now explained.")
    if l2l4["verdict"] == "ARTIFACT":
        md_lines.append(f"- After removing 5 joint fat-tail months, Pearson collapses to **{l2l4['clean_pearson']:+.3f}**, ")
        md_lines.append("  confirming the +0.614 was driven by a few overlapping crisis windows where both shorts (L2, L4) ")
        md_lines.append("  fired together. In normal months they are uncorrelated or mildly negative.")
        md_lines.append("- **Implication**: L4's diversification penalty against L2 is overstated by Pearson. ")
        md_lines.append("  The portfolio benefit of keeping L4 may be larger than the Pearson-based correlation matrix suggests.")
    elif l2l4["verdict"] == "TIME-VARYING":
        md_lines.append(f"- Rolling-12 correlation oscillates: {l2l4['roll12_n_pos']} positive windows, {l2l4['roll12_n_neg']} negative.")
        md_lines.append("- **Implication**: Their relationship is regime-dependent. The diversification benefit varies with market state.")
    else:
        md_lines.append(f"- Rolling-12 correlation is stable at median {l2l4['roll12_median']:+.3f}.")
        md_lines.append(f"- **Implication**: The structural overlap is real; L4 does add concentration risk to the short book.")
    md_lines.append("")

if l1l5:
    md_lines.append(f"### L1-L5 finding (verdict: **{l1l5['verdict']}**)")
    md_lines.append("")
    md_lines.append(f"- Daily 0.00 vs Monthly +0.524 was the largest day-month delta. Rolling-12 median **{l1l5['roll12_median']:+.3f}**.")
    md_lines.append(f"- Outlier-clean Pearson: **{l1l5['clean_pearson']:+.3f}**")
    md_lines.append(f"- Both are long strategies, so monthly co-movement is expected. The L4 decision is unaffected by this pair.")
    md_lines.append("")

if l5s1:
    md_lines.append(f"### L5-S1 finding (verdict: **{l5s1['verdict']}**)")
    md_lines.append("")
    md_lines.append(f"- Full Pearson +0.504 / clean Pearson **{l5s1['clean_pearson']:+.3f}** / rolling-12 median **{l5s1['roll12_median']:+.3f}**.")
    md_lines.append(f"- Both L5 (breakout long) and S1 (night momentum) are momentum-flavored; modest persistent overlap is plausible.")
    md_lines.append("")

if l1s1:
    md_lines.append(f"### L1-S1 hedge (verdict: **{l1s1['verdict']}**)")
    md_lines.append("")
    md_lines.append(f"- Bear-regime correlation was {-0.129:+.3f}; full-sample Pearson here **{l1s1['full_pearson']:+.3f}**, clean **{l1s1['clean_pearson']:+.3f}**.")
    md_lines.append(f"- Rolling-12 median **{l1s1['roll12_median']:+.3f}**, range `[{l1s1['roll12_min']:+.3f}, {l1s1['roll12_max']:+.3f}]`.")
    if l1s1["verdict"] == "STRUCTURAL" and l1s1["roll12_median"] < 0.2:
        md_lines.append("- **Hedge is real and reasonably stable** — keep S1 alongside L1 for downside diversification.")
    elif l1s1["verdict"] == "TIME-VARYING":
        md_lines.append("- **Hedge holds in some regimes, breaks in others** — monitor; do not assume it always protects.")
    else:
        md_lines.append("- **Caution**: the hedge depends on outlier months; do not over-rely on it for risk budgeting.")
    md_lines.append("")

md_lines.append("### Bottom line for L4 keep-or-cut")
md_lines.append("")
if l2l4 and l2l4["verdict"] == "ARTIFACT":
    md_lines.append("- The L2-L4 +0.614 Pearson is an **ARTIFACT** of a handful of joint fat-tail months. Spearman -0.174 is closer to the truth.")
    md_lines.append("- **Recommendation**: do NOT cut L4 on correlation grounds alone. The diversification penalty Pearson signaled is overstated.")
    md_lines.append("- The L4 decision should pivot back to standalone-merit criteria (PF, MDD, sample size, WFE) rather than the inflated Pearson.")
elif l2l4 and l2l4["verdict"] == "TIME-VARYING":
    md_lines.append("- L2-L4 correlation is regime-dependent. Use **Spearman / rolling median** rather than full-sample Pearson for the cross-correlation matrix.")
    md_lines.append("- The cut/keep call needs to consider when the high-correlation regimes occur (likely crash months — both shorts cluster).")
else:
    md_lines.append("- L2-L4 overlap appears structural. Concentration risk in the short book is real; L4 should be re-justified on standalone merit.")

md_lines.append("")
md_lines.append("**Action**: Recompute the portfolio correlation matrix using either Spearman or outlier-trimmed Pearson before making cut decisions.")
md_lines.append("")

# Write output
out_md = Path("C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_rolling_corr.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"\nMarkdown report saved: {out_md}")
print(f"Lines: {len(md_lines)}")
