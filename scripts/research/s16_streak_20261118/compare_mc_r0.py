"""v1.28.1 R0（TOD_Gate_Days=0）MC 報表 vs 0825 MC 報表（11/16）：同一段資料逐筆必須相同；
並把 11/16 12:20 以後兩份都有的交易（R0 vs B）並排，看新版在最新 3 天擋掉哪些。
Usage: python -I scripts/research/s16_streak_20261118/compare_mc_r0.py <r0_trades.csv> <0825_trades.csv> <B_trades.csv>
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mc_boss_stats import load  # noqa: E402
from vol_gate_years import micro_net  # noqa: E402

CUT = "2026-11-16 12:20"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    r0 = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    b825 = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
    r0_in = [m for m in r0 if m["exit_dt"] <= CUT]
    key = lambda m: (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19], round(float(m["net_ntd"])))
    same = [key(m) for m in r0_in] == [key(m) for m in b825]
    print(f"R0 至 {CUT}：{len(r0_in)} 筆、{sum(float(m['net_ntd']) for m in r0_in):,.0f}；"
          f"0825 報表 {len(b825)} 筆、{sum(float(m['net_ntd']) for m in b825):,.0f}；逐筆相同：{'是' if same else '否'}")
    if not same:
        for a, b in zip(r0_in, b825):
            if key(a) != key(b):
                print("  第一筆不同：", key(a), "｜", key(b))
                break
    R0 = [t for t in load(sys.argv[1]) if t.exit_dt.strftime("%Y-%m-%d %H:%M") > CUT]
    B = {t.entry_dt: t for t in load(sys.argv[3]) if t.exit_dt.strftime("%Y-%m-%d %H:%M") > CUT}
    print("11/16 12:20 以後（微台 2 口）：進場｜0825 規則（R0）｜新版 B")
    for t in R0:
        b = B.get(t.entry_dt)
        print(f"  {t.entry_dt:%m/%d %H:%M} {t.exit_label:<22} {micro_net(t):>8,.0f} ｜ "
              + (f"{micro_net(b):,.0f}" if b else "擋掉"))
    extra = [b for d, b in B.items() if d not in {t.entry_dt for t in R0}]
    for b in extra:
        print(f"  只有 B：{b.entry_dt:%m/%d %H:%M} {micro_net(b):,.0f}")
    print(f"合計：R0 {sum(micro_net(t) for t in R0):,.0f}｜B {sum(micro_net(b) for b in B.values()):,.0f}")


if __name__ == "__main__":
    main()
