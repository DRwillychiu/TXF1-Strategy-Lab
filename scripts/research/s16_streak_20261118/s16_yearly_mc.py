"""S16 逐年績效、每 1 萬元期望值、獲利來源（全部用 MC 報表交易，2 口微台、資金 140,200）。
Usage: python -I scripts/research/s16_streak_20261118/s16_yearly_mc.py <0825_trades.csv> <B_trades.csv> <out.md>
"""
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mc_boss_stats import load  # noqa: E402
from s16_prelive import today_net  # noqa: E402
from vol_gate_years import micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
YF_2026 = (date(2026, 11, 16) - date(2026, 1, 1)).days / 365


def yr_stats(pn, yrs):
    x = full_stats(pn, yrs)
    gp = sum(v for v in pn if v > 0); gl = -sum(v for v in pn if v < 0)
    x["pf"] = gp / gl if gl else float("inf")
    return x


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base = [t for t in load(sys.argv[1]) if t.exit_dt <= CUT]
    B = [t for t in load(sys.argv[2]) if t.exit_dt <= CUT]
    out = ["# S16 逐年績效（MC 實證；2 口微台、資金 140,200；平倉至 2026-11-16 12:20）", "",
           "報酬率＝當年淨利 ÷ 140,200（2026 年換算成全年）。每 1 萬元＝÷ 140,200 × 10,000。", ""]
    for name, tr in (("現行 0825", base), ("新版 B", B)):
        out += [f"## {name}", "", "| 年 | 筆數 | 淨利 | 報酬率 | 每筆期望值 | 每 1 萬元每筆 | 每 1 萬元全年 | 勝率 | PF | 年內最大回撤 | 年內最長連虧 |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for y in range(2020, 2027):
            pn = [micro_net(t) for t in tr if t.exit_dt.year == y]
            yrs = YF_2026 if y == 2026 else 1.0
            x = yr_stats(pn, yrs)
            tag = "（至 11/16，換算全年）" if y == 2026 else ""
            out.append(f"| {y}{tag} | {x['n']} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | "
                       f"{x['exp']/CAP*10000:,.0f} | {x['ann']*100:,.0f} | {x['win']*100:.0f}% | {x['pf']:.2f} | "
                       f"{x['mdd']/CAP*100:.1f}% | {x['streak']} |")
        out.append("")
    out += ["## 不同區段的年化（新版 B；同一份 MC 交易，只換起點）", "",
            "| 區段 | 年數 | 筆數 | 年化（固定資金） | 年化（換算今天指數位階） | 每 1 萬元每筆 | 每 1 萬元每年 | 最大回撤 |", "|---|---|---|---|---|---|---|---|"]
    for lab, a in (("2020 起", date(2020, 1, 1)), ("2023 起", date(2023, 1, 1)), ("2024 起", date(2024, 1, 1)),
                   ("2025 起", date(2025, 1, 1)), ("2026 年", date(2026, 1, 1))):
        yrs = (date(2026, 11, 16) - a).days / 365
        sel = [t for t in B if t.exit_dt.date() >= a]
        x = full_stats([micro_net(t) for t in sel], yrs)
        xt = full_stats([today_net(t) for t in sel], yrs)
        out.append(f"| {lab} | {yrs:.2f} | {x['n']} | {x['ann']:.1f}% | {xt['ann']:.1f}% | {x['exp']/CAP*10000:,.0f} | "
                   f"{x['ann']*100:,.0f} | {x['mdd']/CAP*100:.1f}% |")
    out.append("")
    # 獲利來源
    by = defaultdict(list)
    for t in B:
        by[t.exit_label].append(micro_net(t))
    out += ["## 新版 B 賺在哪裡：依出場原因（2020 起）", "", "| 出場原因 | 筆數 | 淨利 | 平均 | 勝率 |", "|---|---|---|---|---|"]
    for k, v in sorted(by.items(), key=lambda kv: -sum(kv[1])):
        out.append(f"| {k} | {len(v)} | {sum(v):,.0f} | {sum(v)/len(v):,.0f} | {sum(1 for x in v if x > 0)/len(v)*100:.0f}% |")
    pn = sorted((micro_net(t) for t in B), reverse=True)
    tot = sum(pn)
    top = max(1, len(pn) // 10)
    hold = sorted((t.exit_dt - t.entry_dt).total_seconds() / 60 for t in B)
    over = sum(1 for t in B if (t.exit_dt - t.entry_dt).total_seconds() / 3600 > 8)
    out += ["", f"- 獲利最大的 10%（{top} 筆）合計 {sum(pn[:top]):,.0f}，佔總淨利 {sum(pn[:top])/tot*100:.0f}%；"
            f"其餘 {len(pn)-top} 筆合計 {sum(pn[top:]):,.0f}。",
            f"- 持倉時間中位數 {hold[len(hold)//2]:.0f} 分鐘；最長 {hold[-1]/60:.1f} 小時；持倉超過 8 小時（跨盤）的有 {over} 筆。",
            f"- 最大單筆獲利 {pn[0]:,.0f}；最大單筆虧損 {pn[-1]:,.0f}。", ""]
    Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
