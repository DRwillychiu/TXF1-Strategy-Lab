"""Compute per-strategy yearly metrics from _temp_portfolio_pnl.json."""
import json
import statistics
from collections import defaultdict
from pathlib import Path

DATA_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
OUT_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_yearly_metrics.md")

YEARS = [2020, 2021, 2022, 2023, 2024, 2025]


def compute_year_metrics(trades):
    """trades is a sorted list of (date_str, pnl)."""
    if not trades:
        return None
    pnls = [p for _, p in trades]
    n = len(pnls)
    net = sum(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    wr = len(wins) / n if n > 0 else 0.0
    # intra-year drawdown (running equity from 0)
    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    for p in pnls:
        eq += p
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd
    best = max(pnls)
    worst = min(pnls)
    return {
        "n": n,
        "net": net,
        "pf": pf,
        "wr": wr,
        "max_dd": max_dd,
        "best": best,
        "worst": worst,
    }


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    strategies = list(data.keys())
    # build per-strategy per-year trades
    per_strat_year = {}  # strat -> year -> list of (date, pnl) sorted
    for strat, trades_dict in data.items():
        year_map = defaultdict(list)
        for ds, pnl in trades_dict.items():
            year = int(ds.split("-")[0])
            year_map[year].append((ds, pnl))
        for y in year_map:
            year_map[y].sort(key=lambda x: x[0])
        per_strat_year[strat] = year_map

    # compute per-strategy per-year metrics
    metrics = {}  # strat -> year -> metric dict (or None)
    for strat in strategies:
        metrics[strat] = {}
        for y in YEARS:
            metrics[strat][y] = compute_year_metrics(per_strat_year[strat].get(y, []))

    # derived analytics
    losing_years = {}      # strat -> [year, ...]
    stability = {}         # strat -> std/abs(mean) of yearly net (across years with trades)
    lottery = {}           # strat -> [(year, best, net, ratio), ...]

    for strat in strategies:
        nets = []
        loss_years = []
        lot_list = []
        for y in YEARS:
            m = metrics[strat][y]
            if m is None:
                continue
            nets.append(m["net"])
            if m["net"] < 0:
                loss_years.append(y)
            if m["net"] > 0 and m["best"] > 0:
                ratio = m["best"] / m["net"]
                if ratio > 0.30:
                    lot_list.append((y, m["best"], m["net"], ratio))
        losing_years[strat] = loss_years
        if len(nets) >= 2:
            mean_net = statistics.mean(nets)
            std_net = statistics.stdev(nets)
            stab = std_net / abs(mean_net) if mean_net != 0 else float("inf")
        else:
            stab = float("nan")
        stability[strat] = stab
        lottery[strat] = lot_list

    # write markdown
    lines = []
    lines.append("# TXF1 Strategy Lab — Yearly Metrics Analysis (2020-2025)\n")
    lines.append("Source: `scripts/_temp_portfolio_pnl.json`  ")
    lines.append("Years analysed: 2020, 2021, 2022, 2023, 2024, 2025 (2019 / 2026 partial-year data excluded from this report).\n")
    lines.append("\n---\n")

    # Section 1: per-strategy grid
    lines.append("## 1. Per-strategy 6-year metrics grid\n")
    for strat in strategies:
        lines.append(f"### Strategy {strat}\n")
        lines.append("| Year | Trades | Net PnL | PF | WR | Intra-yr MaxDD | Best | Worst |")
        lines.append("|------|-------:|--------:|---:|---:|---------------:|-----:|------:|")
        for y in YEARS:
            m = metrics[strat][y]
            if m is None:
                lines.append(f"| {y} | 0 | — | — | — | — | — | — |")
            else:
                pf_str = f"{m['pf']:.2f}" if m["pf"] != float("inf") else "inf"
                lines.append(
                    f"| {y} | {m['n']} | {m['net']:,.0f} | {pf_str} | "
                    f"{m['wr']*100:.1f}% | {m['max_dd']:,.0f} | "
                    f"{m['best']:,.0f} | {m['worst']:,.0f} |"
                )
        # totals
        totals_n = sum(metrics[strat][y]["n"] for y in YEARS if metrics[strat][y])
        totals_net = sum(metrics[strat][y]["net"] for y in YEARS if metrics[strat][y])
        lines.append(f"| **6Y total** | **{totals_n}** | **{totals_net:,.0f}** | | | | | |\n")

    # Section 2: losing-years ranked
    lines.append("\n---\n")
    lines.append("## 2. Losing-years count (ranked worst -> best)\n")
    lines.append("| Strategy | # Losing years | Years | Years traded | Loss rate |")
    lines.append("|----------|---------------:|-------|-------------:|----------:|")
    rows = []
    for strat in strategies:
        traded = sum(1 for y in YEARS if metrics[strat][y] is not None)
        loss_n = len(losing_years[strat])
        rate = (loss_n / traded * 100) if traded > 0 else 0
        years_str = ", ".join(str(y) for y in losing_years[strat]) if losing_years[strat] else "—"
        rows.append((strat, loss_n, years_str, traded, rate))
    rows.sort(key=lambda r: (-r[1], -r[4]))
    for strat, loss_n, years_str, traded, rate in rows:
        lines.append(f"| {strat} | {loss_n} | {years_str} | {traded} | {rate:.0f}% |")

    # Section 3: year-stability ranked
    lines.append("\n---\n")
    lines.append("## 3. Year-to-year stability (std/abs(mean) of yearly net, ranked most volatile first)\n")
    lines.append("Lower = more stable. `> 1.0` flagged as highly volatile.\n")
    lines.append("| Strategy | Yearly nets (2020-2025) | Mean | Std | Stability (std/|mean|) |")
    lines.append("|----------|--------------------------|-----:|----:|----------------------:|")
    stab_rows = []
    for strat in strategies:
        nets = []
        for y in YEARS:
            m = metrics[strat][y]
            nets.append(m["net"] if m else 0)
        nz = [n for n in nets if n != 0]
        mean_n = statistics.mean(nz) if nz else 0
        std_n = statistics.stdev(nz) if len(nz) >= 2 else float("nan")
        stab_rows.append((strat, nets, mean_n, std_n, stability[strat]))
    stab_rows.sort(key=lambda r: -(r[4] if r[4] == r[4] else -1))  # NaN last
    for strat, nets, mean_n, std_n, stab in stab_rows:
        nets_str = " / ".join(f"{n:,.0f}" for n in nets)
        std_str = f"{std_n:,.0f}" if std_n == std_n else "—"
        stab_str = f"{stab:.2f}" if stab == stab else "—"
        lines.append(f"| {strat} | {nets_str} | {mean_n:,.0f} | {std_str} | {stab_str} |")

    # Section 4: lottery dependency
    lines.append("\n---\n")
    lines.append("## 4. Lottery-dependency analysis\n")
    lines.append("Years where the single best trade > 30% of that year's net PnL (only counts profitable years).\n")
    lines.append("| Strategy | Lottery years count | Detail (year: best / net = ratio) |")
    lines.append("|----------|--------------------:|-----------------------------------|")
    lot_rows = []
    for strat in strategies:
        lot = lottery[strat]
        detail = "; ".join(
            f"{y}: {best:,.0f}/{net:,.0f} = {ratio*100:.0f}%"
            for y, best, net, ratio in lot
        ) if lot else "—"
        lot_rows.append((strat, len(lot), detail))
    lot_rows.sort(key=lambda r: -r[1])
    for strat, n, detail in lot_rows:
        lines.append(f"| {strat} | {n} | {detail} |")

    # Section 5: verdict
    lines.append("\n---\n")
    lines.append("## 5. Verdict per strategy\n")
    lines.append("Flags applied:\n")
    lines.append("- **UNRELIABLE**: 3+ losing years in the 6-year window")
    lines.append("- **HIGHLY VOLATILE**: yearly stability std/|mean| > 1.0")
    lines.append("- **LUCK-BASED**: lottery-dependency in 2+ years\n")
    lines.append("| Strategy | Losing yrs | Stability | Lottery yrs | Flags | Verdict |")
    lines.append("|----------|-----------:|----------:|------------:|-------|---------|")
    flagged = set()
    verdicts = {}
    for strat in strategies:
        flags = []
        loss_n = len(losing_years[strat])
        stab = stability[strat]
        lot_n = len(lottery[strat])
        if loss_n >= 3:
            flags.append("UNRELIABLE")
        if stab == stab and stab > 1.0:
            flags.append("HIGHLY VOLATILE")
        if lot_n >= 2:
            flags.append("LUCK-BASED")
        if flags:
            flagged.add(strat)
        verdict = "PASS — broadly robust" if not flags else " + ".join(flags)
        stab_str = f"{stab:.2f}" if stab == stab else "—"
        verdicts[strat] = (loss_n, stab, lot_n, flags, verdict)
        lines.append(f"| {strat} | {loss_n} | {stab_str} | {lot_n} | {', '.join(flags) if flags else '—'} | {verdict} |")

    # quick narrative
    lines.append("\n### Narrative\n")
    for strat in strategies:
        loss_n, stab, lot_n, flags, verdict = verdicts[strat]
        traded = sum(1 for y in YEARS if metrics[strat][y] is not None)
        nets = [metrics[strat][y]["net"] for y in YEARS if metrics[strat][y]]
        total = sum(nets)
        line = (
            f"- **{strat}** — traded {traded}/6 yrs, 6Y net {total:,.0f}, "
            f"losing yrs={loss_n}, stability={('%.2f'%stab) if stab==stab else 'n/a'}, lottery yrs={lot_n}. "
            f"{'Verdict: ' + verdict + '.'}"
        )
        lines.append(line)

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    # also dump summary JSON for caller
    summary = {
        "strategies": strategies,
        "metrics": {
            s: {
                str(y): metrics[s][y]
                for y in YEARS
            } for s in strategies
        },
        "losing_years": losing_years,
        "stability": {s: (stability[s] if stability[s] == stability[s] else None) for s in strategies},
        "lottery": {s: lottery[s] for s in strategies},
        "flagged": sorted(flagged),
    }
    Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_yearly_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print("Wrote:", OUT_PATH)
    print("Flagged strategies:", sorted(flagged))
    for s in strategies:
        loss_n, stab, lot_n, flags, verdict = verdicts[s]
        print(f"  {s}: loss={loss_n}, stab={stab:.2f if stab==stab else 0}, lot={lot_n}, flags={flags}")


if __name__ == "__main__":
    main()
