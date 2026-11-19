"""老闆版數字改用 MC 實證：0825（MC 11/16 報表）vs B（MC v1281c 報表），換算 2 口微台、資金 140,200。
兩份 MC 報表都只取平倉 ≤ 2026-11-16 12:20（同一段資料）；B 報表 11/17 以後的交易另列。
Usage: python -I scripts/research/s16_streak_20261118/mc_boss_stats.py <0825_trades.csv> <B_trades.csv> <out.md> <daily.csv>
"""
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from vol_gate_is2020 import session_date  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        out.append(SimpleNamespace(entry_dt=datetime.fromisoformat(r["entry_dt"]), entry_label=r["entry_label"],
                                   entry_px=float(r["entry_px"]), exit_dt=datetime.fromisoformat(r["exit_dt"]),
                                   exit_label=r["exit_label"], exit_px=float(r["exit_px"]), net_ntd=float(r["net_ntd"])))
    return out


def st(tr, a, yrs):
    pn = [micro_net(t) for t in tr if a <= t.exit_dt <= CUT]
    x = full_stats(pn, yrs)
    x["mdd_pct"] = x["mdd"] / CAP * 100
    x["worst"] = min(pn)
    x["per_year"] = x["n"] / yrs
    return x


def chg(v, b, mag=False):
    if mag:
        v, b = abs(v), abs(b)
    return f"{(v - b) / abs(b) * 100:+.1f}%" if b else "—"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base, B = load(sys.argv[1]), load(sys.argv[2])
    out = ["# S16 老闆版數字：MC 實證（0825 vs B；2 口微台、資金 140,200；平倉至 2026-11-16 12:20）", "",
           "來源：0825＝MC 11/16 報表（tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv）；",
           "B＝MC v1281c 報表（Willy 11/19，data/research_s16_20261118/mc_v1281c_trades.csv）。", ""]
    rows = [("筆數", "n", "{:,.0f}", False), ("淨利（元）", "net", "{:,.0f}", False), ("年化（單利）", "ann", "{:.1f}%", False),
            ("每筆期望值（元）", "exp", "{:,.0f}", False), ("獲利因子 PF", "pf", "{:.2f}", False), ("勝率", "win", "{:.1%}", False),
            ("最大回撤（元）", "mdd", "{:,.0f}", True), ("最大回撤佔資金", "mdd_pct", "{:.1f}%", True),
            ("最長連虧（筆）", "streak", "{:.0f}", False), ("最長連虧金額（元）", "streak_amt", "{:,.0f}", True),
            ("單筆最大虧損（元）", "worst", "{:,.0f}", True), ("每年筆數", "per_year", "{:.1f}", False)]
    for title, a, yrs in (("2020-01～2026-11", datetime(2020, 1, 1), 6.876), ("2023-01～2026-11", datetime(2023, 1, 1), 3.876)):
        b0, b1 = st(base, a, yrs), st(B, a, yrs)
        out += [f"## {title}", "", "| 指標 | 0825 | B | 變化率 |", "|---|---|---|---|"]
        for lab, k, fmt, mag in rows:
            out.append(f"| {lab} | {fmt.format(b0[k])} | {fmt.format(b1[k])} | {chg(b1[k], b0[k], mag)} |")
        out.append("")
    out += ["## 逐年淨利（元；括號為筆數）", "", "| 年 | 0825 | B | B 多賺 |", "|---|---|---|---|"]
    for y in range(2020, 2027):
        v0 = [micro_net(t) for t in base if t.exit_dt.year == y and t.exit_dt <= CUT]
        v1 = [micro_net(t) for t in B if t.exit_dt.year == y and t.exit_dt <= CUT]
        out.append(f"| {y} | {sum(v0):,.0f}（{len(v0)}） | {sum(v1):,.0f}（{len(v1)}） | {sum(v1) - sum(v0):+,.0f} |")
    after = [t for t in B if t.exit_dt > CUT]
    out += ["", f"## B 在 11/16 12:20 以後的 MC 交易（{len(after)} 筆；Python 1 分 K 只到 11/16，尚未逐筆核對）", "",
            "| 進場 | 出場 | 出場原因 | 微台 2 口損益 |", "|---|---|---|---|"]
    for t in after:
        out.append(f"| {t.entry_dt:%m/%d %H:%M} | {t.exit_dt:%m/%d %H:%M} | {t.exit_label} | {micro_net(t):,.0f} |")
    out.append(f"| 合計 | | | {sum(micro_net(t) for t in after):,.0f} |")
    Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8")
    # 給 boss_charts.py 的日損益（欄名沿用 base／tod90d_p70）
    days = defaultdict(lambda: [0.0, 0.0])
    for j, tr in enumerate((base, B)):
        for t in tr:
            if datetime(2020, 1, 1) <= t.exit_dt <= CUT:
                days[session_date(t.exit_dt)][j] += micro_net(t)
    with open(sys.argv[4], "w", encoding="utf-8", newline="") as f:
        f.write("date,base,tod90d_p70\n")
        for d in sorted(days):
            f.write(f"{d},{days[d][0]:.0f},{days[d][1]:.0f}\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
