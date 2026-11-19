"""老闆版只放 2023–2026（Willy 11/19）：用 MC 報表交易重算 2023 起的今日價位回撤、2026 佔比、逐年差，
並用 2023 起的交易重跑實戰期／一年期模擬（取代原本用 2020 起交易的估計）。
Usage: python -I scripts/research/s16_streak_20261118/s16_boss_2023.py <0825_trades.csv> <B_trades.csv> <out.md>
"""
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mc_boss_stats import load  # noqa: E402
from vol_gate_years import micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from s16_prelive import today_net, sim, pct, SIMS, HOLI, GO_LIVE, D3_END, LIMIT  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
A = datetime(2023, 1, 1)
YRS = (CUT - A).days / 365


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base = [t for t in load(sys.argv[1]) if A <= t.exit_dt <= CUT]
    B = [t for t in load(sys.argv[2]) if A <= t.exit_dt <= CUT]
    out = ["# S16 老闆版 2023–2026 補充數字（MC 報表交易；模擬為估計）", ""]
    for name, tr in (("現行 0825", base), ("新版 B", B)):
        x = full_stats([micro_net(t) for t in tr], YRS)
        xt = full_stats([today_net(t) for t in tr], YRS)
        out.append(f"- {name}：固定資金年化 {x['ann']:.1f}%、回撤 {x['mdd']/CAP*100:.1f}%；"
                   f"換算今天指數位階年化 {xt['ann']:.1f}%、回撤 {xt['mdd']:,.0f}（{xt['mdd']/CAP*100:.1f}%）、最長連虧 {xt['streak']}")
    nb = {y: sum(micro_net(t) for t in B if t.exit_dt.year == y) for y in range(2023, 2027)}
    n0 = {y: sum(micro_net(t) for t in base if t.exit_dt.year == y) for y in range(2023, 2027)}
    tot = sum(nb.values())
    out += [f"- B 淨利 {tot:,.0f}，2026 年佔 {nb[2026]/tot*100:.1f}%。",
            "- 逐年 B − 0825：" + "、".join(f"{y} {nb[y]-n0[y]:+,.0f}" for y in nb), ""]
    rng = random.Random(20261119)
    tdays = sum(1 for k in range((D3_END - GO_LIVE).days + 1)
                if (GO_LIVE + timedelta(days=k)).weekday() < 5 and (GO_LIVE + timedelta(days=k)) not in HOLI)
    pool_all = [today_net(t) for t in B]
    pool_26 = [today_net(t) for t in B if t.exit_dt.year == 2026]
    rate_all = len(B) / (YRS * 250)
    rate_26 = len(pool_26) / (date(2026, 11, 16) - date(2026, 1, 1)).days * 365 / 250
    out += [f"## 實戰期模擬（{GO_LIVE}～{D3_END}，{tdays} 個交易日；今日價位；{SIMS:,} 次自助抽樣）", "",
            "| 假設 | 預期筆數 | 賺錢機率 | 回撤 ≥ 15% 機率 |", "|---|---|---|---|"]
    for name, pool, rate in (("像 2026 年（高波動）", pool_26, rate_26), ("像 2023 起平均", pool_all, rate_all)):
        t_, m_, s_ = sim(pool, rate * tdays, SIMS, rng)
        out.append(f"| {name} | {rate*tdays:.1f} | {sum(1 for x in t_ if x > 0)/SIMS*100:.0f}% | "
                   f"{sum(1 for x in m_ if x <= -LIMIT)/SIMS*100:.1f}% |")
    out += ["", "## 一年期（今日價位）", "", "| 假設 | 一年筆數 | 回撤 95% 分位 | 連虧 95% 分位 | 一年內回撤 ≥ 15% 機率 | 一年內連虧 ≥ 8 機率 | 連虧 ≥ 10 機率 |",
            "|---|---|---|---|---|---|---|"]
    for name, pool, rate in (("像 2026 年（高波動）", pool_26, rate_26), ("像 2023 起平均", pool_all, rate_all)):
        t_, m_, s_ = sim(pool, rate * 250, SIMS, rng)
        m = [-x for x in m_]
        out.append(f"| {name} | {rate*250:.0f} | {pct(m, .95):,.0f} | {pct(s_, .95)} | {sum(1 for x in m if x >= LIMIT)/SIMS*100:.1f}% | "
                   f"{sum(1 for x in s_ if x >= 8)/SIMS*100:.1f}% | {sum(1 for x in s_ if x >= 10)/SIMS*100:.1f}% |")
    out.append("")
    Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
