"""IS/OOS split test for all strategies in _temp_portfolio_pnl.json."""
import json
import math
from pathlib import Path

INPUT = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
OUTPUT = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_is_oos.md")


def compute_metrics(pnls):
    """Return dict of metrics for a list of daily PnL values."""
    n = len(pnls)
    if n == 0:
        return None
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = sum(pnls)
    avg = total / n
    wr = len(wins) / n if n else 0.0
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    if gross_loss == 0:
        pf = float("inf") if gross_win > 0 else 0.0
    else:
        pf = gross_win / gross_loss
    # Sharpe on daily PnL (no risk-free; daily) annualized x sqrt(252)
    if n > 1:
        mean = avg
        var = sum((p - mean) ** 2 for p in pnls) / (n - 1)
        sd = math.sqrt(var)
        sharpe = (mean / sd) * math.sqrt(252) if sd > 0 else 0.0
    else:
        sharpe = 0.0
    return {
        "n": n,
        "total_pnl": total,
        "avg_daily_pnl": avg,
        "wr": wr,
        "pf": pf,
        "sharpe": sharpe,
        "gross_win": gross_win,
        "gross_loss": gross_loss,
        "wins": len(wins),
        "losses": len(losses),
    }


def safe_ratio(a, b):
    if b == 0:
        return float("inf") if a > 0 else (0.0 if a == 0 else float("-inf"))
    # signs matter
    return a / b


def wfe_classification(wfe_pnl, is_avg, oos_avg):
    """Classify based on WFE_pnl, but flag sign flip specially."""
    # If IS is negative we can't really treat ratios normally
    if is_avg <= 0 and oos_avg <= 0:
        return "BOTH_NEGATIVE"
    if is_avg <= 0 < oos_avg:
        return "IS_NEG_OOS_POS"
    if is_avg > 0 >= oos_avg:
        return "OOS_NEG_DEGRADED"
    # both positive
    if wfe_pnl > 0.7:
        return "ROBUST"
    if wfe_pnl > 0.5:
        return "ACCEPTABLE"
    if wfe_pnl > 0.3:
        return "WARNING"
    return "SEVERE_OVERFIT"


def split_metrics(sorted_items, frac_is):
    """sorted_items is list of (date, pnl) chronologically. frac_is is 0..1."""
    n = len(sorted_items)
    cut = max(1, int(round(n * frac_is)))
    is_p = [p for _, p in sorted_items[:cut]]
    oos_p = [p for _, p in sorted_items[cut:]]
    return compute_metrics(is_p), compute_metrics(oos_p), cut, n - cut


def fmt(v, kind="num"):
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if math.isinf(v):
            return "inf"
        if kind == "pct":
            return f"{v*100:.1f}%"
        if kind == "money":
            return f"{v:,.0f}"
        if kind == "ratio":
            return f"{v:.2f}"
        return f"{v:.2f}"
    return str(v)


def analyze_strategy(name, day_map):
    items = sorted(day_map.items())  # chronological
    # 70/30 main
    is_m, oos_m, n_is, n_oos = split_metrics(items, 0.70)

    # WFE
    wfe_pnl = safe_ratio(oos_m["avg_daily_pnl"], is_m["avg_daily_pnl"])
    wfe_pf = safe_ratio(oos_m["pf"], is_m["pf"])
    wfe_sharpe = safe_ratio(oos_m["sharpe"], is_m["sharpe"])
    verdict = wfe_classification(wfe_pnl, is_m["avg_daily_pnl"], oos_m["avg_daily_pnl"])

    splits = {}
    for frac in [0.50, 0.60, 0.70, 0.80]:
        is_alt, oos_alt, ni, no = split_metrics(items, frac)
        wfe_alt = safe_ratio(oos_alt["avg_daily_pnl"], is_alt["avg_daily_pnl"])
        verd_alt = wfe_classification(wfe_alt, is_alt["avg_daily_pnl"], oos_alt["avg_daily_pnl"])
        splits[frac] = {
            "is": is_alt,
            "oos": oos_alt,
            "n_is": ni,
            "n_oos": no,
            "wfe_pnl": wfe_alt,
            "verdict": verd_alt,
        }

    return {
        "name": name,
        "n_total": len(items),
        "date_start": items[0][0],
        "date_end": items[-1][0],
        "is": is_m,
        "oos": oos_m,
        "n_is": n_is,
        "n_oos": n_oos,
        "wfe_pnl": wfe_pnl,
        "wfe_pf": wfe_pf,
        "wfe_sharpe": wfe_sharpe,
        "verdict": verdict,
        "splits": splits,
    }


def main():
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    results = {name: analyze_strategy(name, dm) for name, dm in data.items()}

    lines = []
    lines.append("# IS/OOS Split Test Analysis")
    lines.append("")
    lines.append("**Generated:** 2026-06-19  ")
    lines.append("**Source:** `scripts/_temp_portfolio_pnl.json`  ")
    lines.append(f"**Strategies:** {', '.join(results.keys())}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Methodology
    lines.append("## 1. Methodology")
    lines.append("")
    lines.append("**Input granularity.** Each strategy is a dict of `date → daily realized PnL (NTD)`. ")
    lines.append("These are daily PnL events (not individual trades), already including round-trip slippage 1,000 NTD per the project spec.")
    lines.append("")
    lines.append("**Procedure for each strategy:**")
    lines.append("")
    lines.append("1. Sort all daily PnL records chronologically by date.")
    lines.append("2. Cut at index `floor(N * frac_IS)` — first segment is **In-Sample (IS)**, remainder is **Out-of-Sample (OOS)**.")
    lines.append("3. Compute on each segment: trade count `N`, total PnL, average daily PnL, win-rate `WR`, profit factor `PF = gross_win / |gross_loss|`, and annualised Sharpe `= mean(daily) / stdev(daily) * sqrt(252)`.")
    lines.append("4. Walk-Forward Efficiency ratios:")
    lines.append("   - `WFE_pnl = OOS_avg_daily_pnl / IS_avg_daily_pnl`")
    lines.append("   - `WFE_pf  = OOS_PF / IS_PF`")
    lines.append("   - `WFE_sharpe = OOS_Sharpe / IS_Sharpe`")
    lines.append("5. Repeat across **four splits** for stability: 50/50, 60/40, 70/30, 80/20.")
    lines.append("")
    lines.append("**Institutional verdict thresholds on `WFE_pnl` (with both IS and OOS positive):**")
    lines.append("")
    lines.append("| WFE_pnl | Verdict |")
    lines.append("|---|---|")
    lines.append("| > 0.7 | ROBUST |")
    lines.append("| 0.5 – 0.7 | ACCEPTABLE |")
    lines.append("| 0.3 – 0.5 | WARNING (likely overfit) |")
    lines.append("| < 0.3 | SEVERE OVERFIT |")
    lines.append("")
    lines.append("**Edge cases:**")
    lines.append("- `IS_NEG_OOS_POS` — IS lost money but OOS made money. Ratio is mathematically meaningless; treated as *non-overfit but historically weak* (real-money OOS evidence > backtest).")
    lines.append("- `OOS_NEG_DEGRADED` — IS was profitable but OOS is flat/negative. Treated as **SEVERE_OVERFIT-equivalent**: the IS edge has died.")
    lines.append("- `BOTH_NEGATIVE` — both halves lose; strategy is broken regardless of WFE.")
    lines.append("")
    lines.append("**Caveats:**")
    lines.append("- These are *daily aggregates*, not per-trade records, so PF/WR are at the day level (a day can contain multiple intraday trades). This biases PF mildly downward vs trade-level PF (offsetting trades within a day net out).")
    lines.append("- Sample sizes vary widely (L4 has 75 days; S1 has 460 days). Smaller samples ⇒ wider error bars on WFE.")
    lines.append("- A naive chronological split assumes stationarity of the market regime within each half — which is exactly what we're testing against.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. Per-strategy 70/30 table
    lines.append("## 2. Per-Strategy 70/30 IS/OOS Metrics")
    lines.append("")
    lines.append("| Strategy | N(IS) | IS total | IS avg/day | IS WR | IS PF | IS Sharpe | N(OOS) | OOS total | OOS avg/day | OOS WR | OOS PF | OOS Sharpe |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name in sorted(results.keys()):
        r = results[name]
        is_m = r["is"]; oos_m = r["oos"]
        lines.append(
            f"| {name} | {r['n_is']} | {fmt(is_m['total_pnl'],'money')} | {fmt(is_m['avg_daily_pnl'],'money')} | "
            f"{fmt(is_m['wr'],'pct')} | {fmt(is_m['pf'],'ratio')} | {fmt(is_m['sharpe'],'ratio')} | "
            f"{r['n_oos']} | {fmt(oos_m['total_pnl'],'money')} | {fmt(oos_m['avg_daily_pnl'],'money')} | "
            f"{fmt(oos_m['wr'],'pct')} | {fmt(oos_m['pf'],'ratio')} | {fmt(oos_m['sharpe'],'ratio')} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # 3. WFE ranking
    lines.append("## 3. WFE Scores (70/30 split) — Ranked")
    lines.append("")
    lines.append("Sorted by `WFE_pnl` descending (with sign-flip cases shown separately).")
    lines.append("")
    lines.append("| Rank | Strategy | WFE_pnl | WFE_pf | WFE_sharpe | Verdict |")
    lines.append("|---:|---|---:|---:|---:|---|")
    ranked = sorted(
        results.items(),
        key=lambda kv: (kv[1]["verdict"] not in ("IS_NEG_OOS_POS",), -kv[1]["wfe_pnl"] if not math.isinf(kv[1]["wfe_pnl"]) else float("-inf")),
    )
    # Simpler: numeric rank by wfe_pnl with special handling
    def sort_key(item):
        _, r = item
        v = r["wfe_pnl"]
        if r["verdict"] == "IS_NEG_OOS_POS":
            return (-1e9, )  # sort at top because OOS is actually good
        if math.isinf(v):
            return (-1e8 if v > 0 else 1e8, )
        return (-v, )
    ranked = sorted(results.items(), key=sort_key)
    for i, (name, r) in enumerate(ranked, 1):
        lines.append(
            f"| {i} | {name} | {fmt(r['wfe_pnl'],'ratio')} | {fmt(r['wfe_pf'],'ratio')} | "
            f"{fmt(r['wfe_sharpe'],'ratio')} | {r['verdict']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # 4. Split stability
    lines.append("## 4. Split-Stability Test (4 Splits per Strategy)")
    lines.append("")
    lines.append("For each strategy, show `WFE_pnl` and verdict across all four cut points. Consistency across splits is the real overfit test — a robust strategy survives every cut, an overfit one survives only the cut where the lucky trades land in IS.")
    lines.append("")
    for name in sorted(results.keys()):
        r = results[name]
        lines.append(f"### {name} (N = {r['n_total']}, {r['date_start']} → {r['date_end']})")
        lines.append("")
        lines.append("| Split (IS/OOS) | N(IS) | N(OOS) | IS avg/day | OOS avg/day | IS PF | OOS PF | WFE_pnl | Verdict |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for frac in [0.50, 0.60, 0.70, 0.80]:
            s = r["splits"][frac]
            label = f"{int(frac*100)}/{int((1-frac)*100)}"
            lines.append(
                f"| {label} | {s['n_is']} | {s['n_oos']} | "
                f"{fmt(s['is']['avg_daily_pnl'],'money')} | {fmt(s['oos']['avg_daily_pnl'],'money')} | "
                f"{fmt(s['is']['pf'],'ratio')} | {fmt(s['oos']['pf'],'ratio')} | "
                f"{fmt(s['wfe_pnl'],'ratio')} | {s['verdict']} |"
            )
        lines.append("")
    lines.append("---")
    lines.append("")

    # 5. Verdicts
    lines.append("## 5. Per-Strategy Verdict")
    lines.append("")
    for name in sorted(results.keys()):
        r = results[name]
        verdicts_across_splits = [r["splits"][f]["verdict"] for f in [0.50, 0.60, 0.70, 0.80]]
        wfes_across = [r["splits"][f]["wfe_pnl"] for f in [0.50, 0.60, 0.70, 0.80]]
        # stability: count of robust/acceptable
        good = sum(1 for v in verdicts_across_splits if v in ("ROBUST", "ACCEPTABLE", "IS_NEG_OOS_POS"))
        bad = sum(1 for v in verdicts_across_splits if v in ("SEVERE_OVERFIT", "OOS_NEG_DEGRADED", "BOTH_NEGATIVE"))
        warn = sum(1 for v in verdicts_across_splits if v == "WARNING")

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **70/30 primary verdict:** `{r['verdict']}`  (WFE_pnl = {fmt(r['wfe_pnl'],'ratio')}, WFE_pf = {fmt(r['wfe_pf'],'ratio')}, WFE_sharpe = {fmt(r['wfe_sharpe'],'ratio')})")
        lines.append(f"- **Stability across 4 splits:** {good} good · {warn} warning · {bad} bad → verdicts = {verdicts_across_splits}")
        lines.append(f"- **WFE_pnl across splits:** {[round(x,2) if not math.isinf(x) else 'inf' for x in wfes_across]}")
        # interpretation
        interp = []
        if all(v in ("ROBUST","ACCEPTABLE") for v in verdicts_across_splits):
            interp.append("Every split passes — true edge, deploy with confidence at sized position.")
        elif all(v in ("SEVERE_OVERFIT","OOS_NEG_DEGRADED","BOTH_NEGATIVE") for v in verdicts_across_splits):
            interp.append("Every split fails — the historical edge has died; **do not size up; consider retirement or full rework**.")
        elif verdicts_across_splits.count("IS_NEG_OOS_POS") >= 2:
            interp.append("Multiple splits show IS-loss / OOS-profit — recent regime is favourable to this strategy; the backtest understates current edge. Treat as *opportunistic*, not validated.")
        elif bad >= 2:
            interp.append("Majority of splits fail — likely overfit; downsize or move back to research.")
        elif warn + bad >= good:
            interp.append("Verdicts unstable across splits — edge is fragile or regime-dependent; keep sizing minimum until OOS continues to deliver.")
        else:
            interp.append("Mostly passing with isolated weak splits — acceptable, but monitor OOS month-over-month.")
        lines.append(f"- **Interpretation:** {interp[0]}")
        lines.append("")

    # Final summary block
    lines.append("---")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Strategy | Primary verdict | Splits passing | Splits failing | Action |")
    lines.append("|---|---|---:|---:|---|")
    for name in sorted(results.keys()):
        r = results[name]
        vs = [r["splits"][f]["verdict"] for f in [0.50, 0.60, 0.70, 0.80]]
        good = sum(1 for v in vs if v in ("ROBUST", "ACCEPTABLE", "IS_NEG_OOS_POS"))
        bad = sum(1 for v in vs if v in ("SEVERE_OVERFIT", "OOS_NEG_DEGRADED", "BOTH_NEGATIVE"))
        # action
        if good == 4:
            action = "Deploy / size up"
        elif bad == 4:
            action = "Retire or rework"
        elif bad >= 2:
            action = "Downsize / re-research"
        elif "IS_NEG_OOS_POS" in vs:
            action = "Opportunistic only"
        else:
            action = "Monitor OOS closely"
        lines.append(f"| {name} | {r['verdict']} | {good}/4 | {bad}/4 | {action} |")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")

    # also print compact summary for STDOUT
    print("\nCompact summary:")
    for name in sorted(results.keys()):
        r = results[name]
        vs = [r["splits"][f]["verdict"] for f in [0.50, 0.60, 0.70, 0.80]]
        print(f"  {name}: 70/30 {r['verdict']} | WFE_pnl={r['wfe_pnl']:.2f} | splits={vs}")


if __name__ == "__main__":
    main()
