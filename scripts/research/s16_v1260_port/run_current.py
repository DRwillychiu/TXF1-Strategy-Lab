"""S16 v1.26.0 現行 build 260825（.pla 預設值）Python 回測：錨點核對＋到最新資料的逐年表。

用法：python -I scripts/research/s16_v1260_port/run_current.py <1分K> <輸出資料夾>
輸出：<輸出資料夾>/s16_v1260_b260825_trades_<迄日>.csv 與螢幕摘要（全部是 Python 推論，不是 MC）。
"""
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import load_bars  # noqa: E402


def fmt(s):
    return (f"{s['trades']:>4} 筆  淨利 {s['net']:>12,.0f}  PF {s['pf']:.4f}  "
            f"平倉回撤 {s['mdd_closed']:>10,.0f}  最長連虧 {s['max_loss_streak']}  勝率 {s['win_rate']:.1%}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    params = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    bars = load_bars(data, datetime(2019, 12, 31))
    last = bars[-1].dt
    res = s16.run(bars, params, hol)
    tr = res.trades

    # MC 錨點的實際視窗：首筆 2020-02-26 17:10、末次平倉 2026-08-07 22:35（資料到 8/22）
    anchor = [t for t in tr if t.exit_dt <= datetime(2026, 8, 7, 22, 35)]
    print(f"資料 {bars[0].dt} ～ {last}，5 分 K {len(bars)} 根")
    print("錨點區間（末次平倉 ≤ 2026-08-07 22:35）:", fmt(s16.summarize(anchor)))
    print("  存檔錨點（MC，8/22 版資料）: 176 筆  淨利 2,474,800  PF 1.9797  最大策略虧損 -505,600")
    mc_year = {2020: (32, 160400), 2021: (17, -55600), 2022: (24, -5200), 2023: (4, -27600),
               2024: (19, 263600), 2025: (27, 321200), 2026: (53, 1818000)}
    print("  逐年對照（Python 筆數/淨利 vs MC 存檔表）:")
    for y, (n, v) in mc_year.items():
        py = [t for t in anchor if t.entry_dt.year == y]
        pv = sum(t.net_ntd for t in py)
        mark = "相同" if (len(py), pv) == (n, v) else f"差 {len(py) - n:+d} 筆 {pv - v:+,.0f}"
        print(f"    {y}: {len(py):>3} / {pv:>11,.0f}   MC {n:>3} / {v:>11,.0f}   {mark}")
    print("全期:", fmt(s16.summarize(tr)))
    by = defaultdict(list)
    for t in tr:
        by[t.entry_dt.year].append(t)
    for y in sorted(by):
        print(f"  {y}:", fmt(s16.summarize(by[y])))
    seen = [t for t in tr if datetime(2026, 8, 1) <= t.entry_dt < datetime(2026, 8, 23)]
    print("2026-08-01～08-22（研究資料已含，8/24 定版時看得到）:", fmt(s16.summarize(seen)) if seen else "0 筆")
    oos = [t for t in tr if t.entry_dt >= datetime(2026, 8, 23)]
    print("2026-08-23 起（定版後從未見過的資料＝樣本外）:", fmt(s16.summarize(oos)) if oos else "0 筆")
    print("2026-08-01 起逐筆:")
    oos = seen + oos
    for t in oos:
        print(f"    {t.entry_dt:%Y-%m-%d %H:%M} {t.entry_label:<17} {t.entry_px:>7.0f} → "
              f"{t.exit_dt:%Y-%m-%d %H:%M} {t.exit_label:<20} {t.exit_px:>7.0f}  {t.net_ntd:>9,.0f}")

    p = out / f"s16_v1260_b260825_trades_{last:%Y%m%d}.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_ntd"])
        for k, t in enumerate(tr, 1):
            w.writerow([k, f"{t.entry_dt:%Y-%m-%d %H:%M}", t.entry_label, t.entry_px,
                        f"{t.exit_dt:%Y-%m-%d %H:%M}", t.exit_label, t.exit_px, round(t.net_ntd)])
    print("交易清單:", p)


if __name__ == "__main__":
    main()
