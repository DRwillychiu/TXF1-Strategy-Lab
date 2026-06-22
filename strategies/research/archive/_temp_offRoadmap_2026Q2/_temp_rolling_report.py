"""Render rolling stats to a markdown report."""
import math
import pickle


def fmt(v, nd=3):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if math.isnan(v):
            return "n/a"
        if math.isinf(v):
            return "inf"
        return f"{v:.{nd}f}"
    return str(v)


def main():
    with open('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_rolling_cache.pkl', 'rb') as f:
        results = pickle.load(f)

    out_path = 'C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_rolling_stats.md'
    lines = []
    lines.append("# Rolling-Window Stability Analysis — TXF1 Strategy Portfolio")
    lines.append("")
    lines.append("Generated: 2026-06-19  ")
    lines.append("Source: `scripts/_temp_portfolio_pnl.json` (per-strategy daily PnL)")
    lines.append("")

    # 1. Methodology
    lines.append("## 1. Methodology")
    lines.append("")
    lines.append("**Data shape.** Each strategy's PnL is supplied as a sparse mapping of trade-day → daily PnL (TWD). "
                 "Non-trade days are filled with 0 to build a continuous calendar-day series spanning each strategy's "
                 "first to last trade.")
    lines.append("")
    lines.append("**Rolling windows.** Three window lengths are used: **180**, **360**, and **720 calendar days**, stepped daily.")
    lines.append("A strategy must have at least `window` calendar days of history to produce a window of that length.")
    lines.append("")
    lines.append("**Profit Factor (PF).** Within each window:")
    lines.append("")
    lines.append("```")
    lines.append("PF = sum(positive daily PnL) / |sum(negative daily PnL)|")
    lines.append("```")
    lines.append("")
    lines.append("If the window has no losing days, PF is reported as `inf` (excluded from variance stats but kept for fail-rate). "
                 "If the window has no trades at all, PF is `nan`.")
    lines.append("")
    lines.append("**Annualized Sharpe.** Computed on trade-day-only returns inside the window "
                 "(zero-PnL days excluded, otherwise std collapses to a sub-quoted floor):")
    lines.append("")
    lines.append("```")
    lines.append("Sharpe = (mean(daily_PnL) / std(daily_PnL, ddof=1)) * sqrt(252)")
    lines.append("```")
    lines.append("")
    lines.append("Requires at least 2 trade days inside the window; otherwise `nan`.")
    lines.append("")
    lines.append("**Instability scores** (from the 360-day series):")
    lines.append("")
    lines.append("- `PF instability = std(rolling_360_PF) / mean(rolling_360_PF)`  (finite values only)")
    lines.append("- `Sharpe instability = std(rolling_360_Sharpe) / |mean(rolling_360_Sharpe)|`")
    lines.append("")
    lines.append("**Failure-window rate.** Share of rolling 360-day windows whose PF is below 1.0 "
                 "(i.e. the strategy lost money over a full calendar year of trailing performance).")
    lines.append("")
    lines.append("**Flagging rules** (per user spec):")
    lines.append("")
    lines.append("- Failure-window rate (360d) > 30%  → **unstable**")
    lines.append("- PF instability > 0.5             → **unstable**")
    lines.append("- Any 720-day window with PF < 1.0 → **severe overfitting risk**")
    lines.append("")
    lines.append("**Verdict.** `STABLE` = no flags. `UNSTABLE` = any 720d PF<1 OR two-or-more flags. `WATCH` = single non-720 flag.")
    lines.append("")
    lines.append("> **Caveat on sparse strategies.** L2 (78 trade days over 5.3 yrs) and L4 (76 trade days over 5.2 yrs) "
                 "trade so infrequently that many short windows contain zero or one trade, producing PF=0/nan/inf and "
                 "extreme Sharpe variance. Their 720-day numbers are the only ones with sufficient sample density to take seriously.")
    lines.append("")

    # 2. Per-strategy rolling-window table
    lines.append("## 2. Per-strategy rolling-window table")
    lines.append("")
    lines.append("PF and Sharpe — mean | std | min | max — at each window length. `n` = number of rolling windows.")
    lines.append("")
    for strat in ['L1', 'L2', 'L3', 'L4', 'L5', 'S1']:
        r = results[strat]
        lines.append(f"### {strat}  ({r['n_trade_days']} trade days, {r['first_date']} → {r['last_date']}, {r['total_calendar_days']} calendar days)")
        lines.append("")
        lines.append("| Window | n | PF mean | PF std | PF min | PF max | Sharpe mean | Sharpe std | Sharpe min | Sharpe max | Fail-rate (PF<1) |")
        lines.append("|--------|---|---------|--------|--------|--------|-------------|------------|------------|------------|------------------|")
        for w in [180, 360, 720]:
            rw = r['rolling'][w]
            if rw['n_windows'] == 0:
                lines.append(f"| {w}d | 0 | — | — | — | — | — | — | — | — | insufficient data |")
                continue
            lines.append(
                f"| {w}d | {rw['n_windows']} | {fmt(rw['pf_mean'])} | {fmt(rw['pf_std'])} | "
                f"{fmt(rw['min_pf'])} | {fmt(rw['max_pf'])} | "
                f"{fmt(rw['sharpe_mean'])} | {fmt(rw['sharpe_std'])} | "
                f"{fmt(rw['min_sharpe'])} | {fmt(rw['max_sharpe'])} | "
                f"{fmt(rw['fail_rate_pct'], 1)}% |"
            )
        lines.append("")

    # 3. Instability scores ranked
    lines.append("## 3. Instability scores (ranked, 360-day basis)")
    lines.append("")
    lines.append("Lower = more consistent. PF instability is the dispersion of rolling-360 PF normalized by its own mean. "
                 "Sharpe instability uses `|mean|` so a small Sharpe magnifies the score (correctly — small-Sharpe systems "
                 "with high variance are not robust).")
    lines.append("")
    lines.append("| Rank | Strategy | PF instability (360d) | Sharpe instability (360d) |")
    lines.append("|------|----------|-----------------------|---------------------------|")
    pf_rank = sorted(results.items(), key=lambda kv: (float('inf') if math.isnan(kv[1]['pf_instability']) else kv[1]['pf_instability']))
    for i, (s, r) in enumerate(pf_rank, 1):
        marker = " (flag)" if (not math.isnan(r['pf_instability']) and r['pf_instability'] > 0.5) else ""
        lines.append(f"| {i} | {s} | {fmt(r['pf_instability'])}{marker} | {fmt(r['sharpe_instability'])} |")
    lines.append("")

    # 4. Failure-window rate ranked
    lines.append("## 4. Failure-window rate (ranked, 360-day basis)")
    lines.append("")
    lines.append("Share of rolling 360-day windows with PF < 1.0. >30% triggers the unstable flag.")
    lines.append("")
    lines.append("| Rank | Strategy | Fail-rate 360d (PF<1) | Fail-rate 180d | Fail-rate 720d | Worst 360d PF | Worst 720d PF (date) |")
    lines.append("|------|----------|-----------------------|----------------|----------------|---------------|----------------------|")
    fr_rank = sorted(results.items(), key=lambda kv: (float('inf') if math.isnan(kv[1]['rolling'][360]['fail_rate_pct']) else kv[1]['rolling'][360]['fail_rate_pct']))
    for i, (s, r) in enumerate(fr_rank, 1):
        fr360 = r['rolling'][360]['fail_rate_pct']
        fr180 = r['rolling'][180]['fail_rate_pct']
        fr720 = r['rolling'][720]['fail_rate_pct']
        marker = " (flag)" if (not math.isnan(fr360) and fr360 > 30) else ""
        worst720 = f"{fmt(r['worst_720_pf'])} ({r['worst_720_date']})" if r['worst_720_date'] else "n/a"
        lines.append(f"| {i} | {s} | {fmt(fr360, 1)}%{marker} | {fmt(fr180, 1)}% | {fmt(fr720, 1)}% | {fmt(r['rolling'][360]['min_pf'])} | {worst720} |")
    lines.append("")

    # 5. Verdict per strategy
    lines.append("## 5. Verdict per strategy")
    lines.append("")
    lines.append("| Strategy | Verdict | Flags triggered | Notes |")
    lines.append("|----------|---------|-----------------|-------|")
    notes_map = {
        'L1': "720d PF stays >0.886 — the dip is shallow and brief (early-2023 chop). Otherwise solid: PF instab 0.25, 360d fail-rate only 13.5%. The 720d PF<1 flag is the only thing keeping it out of STABLE. Realistically: **WATCH**.",
        'L2': "Sparse trader (78 trades in 5.3 yrs) and the numbers reflect it — PF instability 1.23, Sharpe instab 4.99, 720d worst PF 0.684. With this trade density, conclusions are weak but every reliable metric is bad.",
        'L3': "Persistent edge-of-breakeven behaviour: 720d fail-rate 36.8%, 360d mean PF only 1.09. Even the smoothest window length shows the strategy losing money in over a third of trailing-2yr periods. Marginal economics.",
        'L4': "Worst of the set. 360d fail-rate 55%, 720d fail-rate 76%, 720d mean PF 0.95 (< 1!), worst 720d PF 0.439. Two-year windows mostly lose money. Strong candidate for retirement.",
        'L5': "Cleanest by every measure: 360d fail-rate 13%, all 1005 720d windows PF >= 1.084, PF instab 0.37, Sharpe instab 0.86, Sharpe mean ~2.1. Only ~4.7 yrs of history is the lone caveat.",
        'S1': "Largest sample (594 trades), but 360d fail-rate 36.3% and 720d PF dropped to 0.834 in early-2024. Edge exists in aggregate (PF mean 1.33) but has multi-quarter holes.",
    }
    for strat in ['L1', 'L2', 'L3', 'L4', 'L5', 'S1']:
        r = results[strat]
        flags_str = ", ".join(r['flags']) if r['flags'] else "none"
        lines.append(f"| {strat} | **{r['verdict']}** | {flags_str} | {notes_map[strat]} |")
    lines.append("")

    lines.append("### Summary ranking (best → worst stability)")
    lines.append("")
    lines.append("1. **L5** — STABLE.  Lowest fail-rate, no 720d failure, modest Sharpe instab.")
    lines.append("2. **L1** — UNSTABLE by the letter of the rule (one shallow 720d dip to 0.886), but otherwise the second-best system.")
    lines.append("3. **S1** — UNSTABLE.  Two flags. Edge exists, but the failure-window rate is too high for full size.")
    lines.append("4. **L3** — UNSTABLE.  Marginal long-run PF, fails in >1/3 of windows at every length.")
    lines.append("5. **L2** — UNSTABLE.  Three flags. Sparse trader, very high variance.")
    lines.append("6. **L4** — UNSTABLE.  Three flags. 720d PF<1 on average — the system has *negative* expectancy across most two-year periods.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/_temp_rolling_calc.py` + `scripts/_temp_rolling_report.py`.*")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('Wrote', out_path)


if __name__ == '__main__':
    main()
