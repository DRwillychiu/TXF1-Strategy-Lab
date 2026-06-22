"""Overfit detection script - statistical tests on portfolio PnL.

Tests:
1. Bootstrap robustness (1000 resamples)
2. Probabilistic Sharpe Ratio (simplified)
3. Streak analysis
4. Profit concentration (Gini)
5. Combined overfit-risk score
"""

import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev

random.seed(42)

DATA_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
OUT_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_overfit_check.md")

# ---------- helpers ----------
def normal_cdf(x: float) -> float:
    """Standard normal CDF using erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bootstrap_pnl(pnl_list, n_iter=1000):
    n = len(pnl_list)
    totals = []
    for _ in range(n_iter):
        s = 0.0
        for _i in range(n):
            s += pnl_list[random.randrange(n)]
        totals.append(s)
    totals.sort()
    p5 = totals[int(0.05 * n_iter)]
    p50 = totals[int(0.50 * n_iter)]
    p95 = totals[int(0.95 * n_iter)]
    robustness = sum(1 for t in totals if t > 0) / n_iter
    return {
        "p5": p5,
        "p50": p50,
        "p95": p95,
        "robustness": robustness,
    }


def psr_simplified(pnl_list):
    n = len(pnl_list)
    if n < 2:
        return 0.0, 0.0
    mu = mean(pnl_list)
    sd = pstdev(pnl_list)
    if sd == 0:
        return 0.0, 0.0
    sharpe = mu / sd
    psr = normal_cdf(sharpe * math.sqrt(n - 1))
    return sharpe, psr


def streak_analysis(pnl_list):
    """Max consecutive losing days, max consecutive winning days, longest losing streak length."""
    max_loss_streak = 0
    cur_loss_streak = 0
    max_win_streak = 0
    cur_win_streak = 0
    for p in pnl_list:
        if p < 0:
            cur_loss_streak += 1
            cur_win_streak = 0
            max_loss_streak = max(max_loss_streak, cur_loss_streak)
        elif p > 0:
            cur_win_streak += 1
            cur_loss_streak = 0
            max_win_streak = max(max_win_streak, cur_win_streak)
        else:
            cur_loss_streak = 0
            cur_win_streak = 0
    wins = sum(1 for p in pnl_list if p > 0)
    losses = sum(1 for p in pnl_list if p < 0)
    return {
        "max_loss_streak": max_loss_streak,
        "max_win_streak": max_win_streak,
        "wins": wins,
        "losses": losses,
        "loss_streak_vs_wins_ratio": (max_loss_streak / wins) if wins else float('inf'),
    }


def gini_concentration(pnl_list):
    """Gini coefficient on absolute positive PnLs (lottery-dependency measure)."""
    pos = sorted([p for p in pnl_list if p > 0])
    n = len(pos)
    if n == 0:
        return 0.0
    cum = 0.0
    total = sum(pos)
    if total == 0:
        return 0.0
    # Standard Gini formula
    s = 0.0
    for i, v in enumerate(pos, start=1):
        s += (2 * i - n - 1) * v
    gini = s / (n * total)
    return gini


def top_pct_share(pnl_list, top_pct=0.10):
    pos = [p for p in pnl_list if p > 0]
    if not pos:
        return 0.0
    pos_sorted = sorted(pos, reverse=True)
    top_n = max(1, int(round(top_pct * len(pos_sorted))))
    return sum(pos_sorted[:top_n]) / sum(pos_sorted)


# ---------- main ----------
def analyze(strategy_id, pnl_map):
    items = sorted(pnl_map.items())  # by date
    pnl = [v for _d, v in items]
    n = len(pnl)
    total = sum(pnl)

    boot = bootstrap_pnl(pnl, n_iter=1000)
    sharpe, psr = psr_simplified(pnl)
    streak = streak_analysis(pnl)
    gini = gini_concentration(pnl)
    top10 = top_pct_share(pnl, 0.10)

    return {
        "id": strategy_id,
        "n": n,
        "total": total,
        "mean": mean(pnl) if pnl else 0,
        "sd": pstdev(pnl) if n > 1 else 0,
        "sharpe": sharpe,
        "psr": psr,
        "boot": boot,
        "streak": streak,
        "gini": gini,
        "top10_share": top10,
    }


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    results = {sid: analyze(sid, pmap) for sid, pmap in data.items()}

    # Combined overfit-risk score (0=robust, 10=overfit)
    # weights: robustness (low robustness => risk), PSR (low PSR => risk), Gini (high => risk),
    # loss_streak_vs_wins (high => risk), top10 share (high => risk)
    def overfit_score(r):
        score = 0.0
        # robustness: 1.0 = perfect; <0.95 risky
        score += max(0.0, (0.95 - r["boot"]["robustness"]) * 10.0)  # up to 9.5
        # PSR: <0.95 = risky
        score += max(0.0, (0.95 - r["psr"]) * 10.0) * 0.3            # weight 0.3
        # Gini: >0.6 risky
        if r["gini"] > 0.6:
            score += (r["gini"] - 0.6) * 10.0
        # loss streak vs wins
        if r["streak"]["loss_streak_vs_wins_ratio"] > 0.5:
            score += (r["streak"]["loss_streak_vs_wins_ratio"] - 0.5) * 5.0
        # top 10% share > 0.5 risky
        if r["top10_share"] > 0.5:
            score += (r["top10_share"] - 0.5) * 5.0
        return round(score, 2)

    for sid, r in results.items():
        r["overfit_score"] = overfit_score(r)
        if r["overfit_score"] < 1.0:
            r["verdict"] = "ROBUST"
        elif r["overfit_score"] < 3.0:
            r["verdict"] = "WATCH"
        else:
            r["verdict"] = "OVERFIT_RISK"

    # Build markdown
    lines = []
    lines.append("# Overfit Detection Report")
    lines.append("")
    lines.append("Statistical overfit / robustness tests on per-strategy daily PnL series.")
    lines.append(f"Source: `_temp_portfolio_pnl.json`  -  Strategies: {', '.join(results.keys())}")
    lines.append("")

    # 1. Methodology
    lines.append("## 1. Methodology")
    lines.append("")
    lines.append("**Bootstrap robustness (1000 iterations, seed=42)**")
    lines.append("- Each strategy's daily PnL series is resampled with replacement 1000 times.")
    lines.append("- For each resample, the total PnL is computed.")
    lines.append("- `Robustness Score` = fraction of bootstrap resamples whose total PnL > 0.")
    lines.append("- `p5` = 5th percentile of bootstrap total PnL (worst-case lucky).")
    lines.append("- If `p5 < 0`, the observed track record could plausibly have been a losing one given random reordering of trades.")
    lines.append("")
    lines.append("**Probabilistic Sharpe Ratio (simplified)**")
    lines.append("- `Sharpe = mean(daily PnL) / stdev(daily PnL)` (raw, not annualised, no risk-free rate).")
    lines.append("- `PSR ~= Phi(Sharpe * sqrt(N-1))` where `Phi` is standard normal CDF and N = number of trade days.")
    lines.append("- This is a coarse estimate of P(true Sharpe > 0).")
    lines.append("- Threshold: `PSR < 0.95` = not statistically significant at 95% confidence.")
    lines.append("")
    lines.append("**Streak analysis**")
    lines.append("- `max_loss_streak` = longest run of consecutive losing days.")
    lines.append("- `loss_streak_vs_wins_ratio = max_loss_streak / total winning days`.")
    lines.append("- Threshold: ratio > 0.5 = high tail risk (one bad run could wipe out most winners).")
    lines.append("")
    lines.append("**Profit concentration (Gini)**")
    lines.append("- Gini computed on the distribution of positive-PnL days only.")
    lines.append("- 0 = profits evenly distributed; 1 = one trade holds all profit.")
    lines.append("- Threshold: Gini > 0.6 = lottery-dependency (a few outliers carry the strategy).")
    lines.append("- Also reported: `top10_share` = % of total positive PnL contributed by top-10% winning days.")
    lines.append("")
    lines.append("**Combined overfit-risk score** (heuristic, lower = better)")
    lines.append("- Penalties stack from: (0.95 - robustness), (0.95 - PSR)*0.3, max(0, Gini-0.6), max(0, ratio-0.5)*5, max(0, top10-0.5)*5.")
    lines.append("- Verdict bands: `< 1.0 ROBUST`, `1.0-3.0 WATCH`, `>= 3.0 OVERFIT_RISK`.")
    lines.append("")

    # 2. Bootstrap robustness ranked
    lines.append("## 2. Bootstrap Robustness Ranked")
    lines.append("")
    lines.append("| Rank | Strategy | N days | Total PnL | Bootstrap p5 | Bootstrap p50 | Bootstrap p95 | Robustness |")
    lines.append("|---:|:---|---:|---:|---:|---:|---:|---:|")
    boot_ranked = sorted(results.values(), key=lambda r: -r["boot"]["robustness"])
    for i, r in enumerate(boot_ranked, 1):
        b = r["boot"]
        lines.append(
            f"| {i} | {r['id']} | {r['n']} | {r['total']:>+,.0f} | {b['p5']:>+,.0f} | {b['p50']:>+,.0f} | {b['p95']:>+,.0f} | {b['robustness']*100:.1f}% |"
        )
    lines.append("")
    weak = [r['id'] for r in boot_ranked if r['boot']['p5'] < 0]
    if weak:
        lines.append(f"Strategies with `p5 < 0` (could be lucky): **{', '.join(weak)}**")
    else:
        lines.append("All strategies have bootstrap p5 > 0 (no strategy looks purely lucky).")
    lines.append("")

    # 3. PSR ranked
    lines.append("## 3. Probabilistic Sharpe Ratio Ranked")
    lines.append("")
    lines.append("| Rank | Strategy | N | Sharpe (per-day) | PSR | Significant (>= 0.95)? |")
    lines.append("|---:|:---|---:|---:|---:|:---:|")
    psr_ranked = sorted(results.values(), key=lambda r: -r["psr"])
    for i, r in enumerate(psr_ranked, 1):
        sig = "YES" if r["psr"] >= 0.95 else "NO"
        lines.append(f"| {i} | {r['id']} | {r['n']} | {r['sharpe']:.4f} | {r['psr']:.4f} | {sig} |")
    lines.append("")
    not_sig = [r['id'] for r in psr_ranked if r['psr'] < 0.95]
    if not_sig:
        lines.append(f"PSR < 0.95 (not statistically significant): **{', '.join(not_sig)}**")
    else:
        lines.append("All strategies have PSR >= 0.95.")
    lines.append("")

    # 4. Streak analysis ranked (sorted by risk — highest ratio worst)
    lines.append("## 4. Streak Analysis Ranked")
    lines.append("")
    lines.append("| Rank | Strategy | Wins | Losses | Max Win Streak | Max Loss Streak | LossStreak / Wins |")
    lines.append("|---:|:---|---:|---:|---:|---:|---:|")
    streak_ranked = sorted(results.values(), key=lambda r: -r["streak"]["loss_streak_vs_wins_ratio"])
    for i, r in enumerate(streak_ranked, 1):
        s = r["streak"]
        lines.append(
            f"| {i} | {r['id']} | {s['wins']} | {s['losses']} | {s['max_win_streak']} | {s['max_loss_streak']} | {s['loss_streak_vs_wins_ratio']*100:.1f}% |"
        )
    lines.append("")
    tail_risk = [r['id'] for r in streak_ranked if r['streak']['loss_streak_vs_wins_ratio'] > 0.5]
    if tail_risk:
        lines.append(f"High tail risk (loss-streak > 50% of total winners): **{', '.join(tail_risk)}**")
    else:
        lines.append("No strategy exceeds the 50% loss-streak-to-wins ratio threshold.")
    lines.append("")

    # 5. Gini ranked (worst first)
    lines.append("## 5. Profit Concentration (Gini) Ranked")
    lines.append("")
    lines.append("| Rank | Strategy | Gini (positive PnL) | Top-10% share | Lottery? |")
    lines.append("|---:|:---|---:|---:|:---:|")
    gini_ranked = sorted(results.values(), key=lambda r: -r["gini"])
    for i, r in enumerate(gini_ranked, 1):
        flag = "YES" if r["gini"] > 0.6 else "NO"
        lines.append(f"| {i} | {r['id']} | {r['gini']:.3f} | {r['top10_share']*100:.1f}% | {flag} |")
    lines.append("")
    lottery = [r['id'] for r in gini_ranked if r["gini"] > 0.6]
    if lottery:
        lines.append(f"Gini > 0.6 (lottery dependency): **{', '.join(lottery)}**")
    else:
        lines.append("No strategy exceeds the Gini > 0.6 lottery-dependency threshold.")
    lines.append("")

    # 6. Combined score
    lines.append("## 6. Combined Overfit-Risk Score")
    lines.append("")
    lines.append("| Rank | Strategy | Robustness | PSR | Gini | LossStreak/Wins | Top10% | Score | Verdict |")
    lines.append("|---:|:---|---:|---:|---:|---:|---:|---:|:---:|")
    combined_ranked = sorted(results.values(), key=lambda r: r["overfit_score"])
    for i, r in enumerate(combined_ranked, 1):
        lines.append(
            f"| {i} | {r['id']} | {r['boot']['robustness']*100:.1f}% | {r['psr']:.3f} | {r['gini']:.3f} | {r['streak']['loss_streak_vs_wins_ratio']*100:.1f}% | {r['top10_share']*100:.1f}% | {r['overfit_score']:.2f} | {r['verdict']} |"
        )
    lines.append("")

    # 7. Verdict per strategy
    lines.append("## 7. Verdict Per Strategy")
    lines.append("")
    for sid in sorted(results.keys()):
        r = results[sid]
        lines.append(f"### {sid} — **{r['verdict']}** (score {r['overfit_score']:.2f})")
        lines.append(
            f"- Trades/days: **{r['n']}** | Total PnL: **{r['total']:+,.0f}** | per-day mean: {r['mean']:+,.0f}, sd: {r['sd']:,.0f}"
        )
        lines.append(
            f"- Bootstrap: robustness **{r['boot']['robustness']*100:.1f}%**, p5 {r['boot']['p5']:+,.0f}, p50 {r['boot']['p50']:+,.0f}, p95 {r['boot']['p95']:+,.0f}"
        )
        lines.append(f"- Sharpe(per-day): {r['sharpe']:.4f} | PSR: **{r['psr']:.4f}**")
        s = r["streak"]
        lines.append(
            f"- Streaks: wins {s['wins']}, losses {s['losses']}, max win {s['max_win_streak']}, max loss **{s['max_loss_streak']}** (ratio {s['loss_streak_vs_wins_ratio']*100:.1f}%)"
        )
        lines.append(f"- Gini(positive PnL): **{r['gini']:.3f}** | Top-10% share: {r['top10_share']*100:.1f}%")
        # rationale
        flags = []
        if r["boot"]["robustness"] < 0.95:
            flags.append(f"bootstrap robustness {r['boot']['robustness']*100:.1f}% < 95%")
        if r["boot"]["p5"] < 0:
            flags.append("bootstrap p5 < 0 (could be lucky)")
        if r["psr"] < 0.95:
            flags.append(f"PSR {r['psr']:.3f} < 0.95")
        if r["gini"] > 0.6:
            flags.append(f"Gini {r['gini']:.3f} > 0.6 (lottery-dependent)")
        if r["streak"]["loss_streak_vs_wins_ratio"] > 0.5:
            flags.append(f"loss-streak/wins {r['streak']['loss_streak_vs_wins_ratio']*100:.1f}% > 50%")
        if r["top10_share"] > 0.5:
            flags.append(f"top-10% days carry {r['top10_share']*100:.1f}% of positive PnL")
        if flags:
            lines.append("- Flags: " + "; ".join(flags))
        else:
            lines.append("- Flags: none")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    # also dump summary for stdout
    print("=== SUMMARY ===")
    for sid in sorted(results.keys()):
        r = results[sid]
        print(
            f"{sid}: n={r['n']} total={r['total']:+,.0f} robustness={r['boot']['robustness']*100:.1f}% "
            f"PSR={r['psr']:.3f} Gini={r['gini']:.3f} LossStreak/Wins={r['streak']['loss_streak_vs_wins_ratio']*100:.1f}% "
            f"top10={r['top10_share']*100:.1f}% score={r['overfit_score']:.2f} -> {r['verdict']}"
        )

    return results


if __name__ == "__main__":
    main()
