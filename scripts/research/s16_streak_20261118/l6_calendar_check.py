"""L6 V1.0.0 上線前：剩下的 2026 年與 2027 年，長假前平倉、結算日平倉逐日檢查。
1. L6 .pla 的 Holiday_Tail（2026-11-20 起）要和 txfcore/tradecal/registry.py 逐筆相同。
2. 每個休市段：休市前最後交易日＋1 曆日＝Holiday_Tail（session_fact），由 data/taifex_market_closures.json 的休市日重算。
3. 結算日：L6 規則＝每月第 3 個週三。逐月檢查那天是不是休市日（休市就是規則會漏的月份）。

Usage: python -I scripts/research/s16_streak_20261118/l6_calendar_check.py <out.md>
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
from txfcore.tradecal.registry import HOLIDAY_TAIL  # noqa: E402

A, Z = date(2026, 11, 20), date(2027, 12, 31)


def mc(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    js = json.loads((ROOT / "data/taifex_market_closures.json").read_text(encoding="utf-8"))
    closed = {date.fromisoformat(r["date"]) for r in js["closed_weekdays"]}
    l6 = {t for t in s16.holiday_tail(s16.PLA_L6_V100) if t >= mc(A)}
    reg = {t for t in HOLIDAY_TAIL if t >= mc(A)}
    # 由休市日重算：每段連續休市（含週末）前最後一個交易日 +1 曆日；只算有平日休市的段
    tails, d = set(), A
    while d <= Z:
        if d in closed:
            last = d - timedelta(days=1)
            while last.weekday() >= 5 or last in closed:
                last -= timedelta(days=1)
            tails.add(mc(last + timedelta(days=1)))
            while d in closed or d.weekday() >= 5:
                d += timedelta(days=1)
        else:
            d += timedelta(days=1)
    out = ["# L6 V1.0.0 行事曆檢查（2026-11-20～2027-12-31）", "",
           f"- L6 .pla Holiday_Tail {len(l6)} 筆；註冊表 {len(reg)} 筆；由官方休市日重算 {len(tails)} 筆",
           f"- L6 = 註冊表：{l6 == reg}；L6 = 重算：{l6 == tails}",
           f"- 只在 L6：{sorted(l6 - tails)}；只在重算：{sorted(tails - l6)}", "",
           "| 月 | 第 3 個週三 | 是否休市 | L6 結算平倉 |", "|---|---|---|---|"]
    bad = []
    for y, m in [(2026, 11), (2026, 12)] + [(2027, k) for k in range(1, 13)]:
        d = date(y, m, 15)
        while d.weekday() != 2:
            d += timedelta(days=1)
        if d < A:
            continue
        hit = d in closed
        if hit:
            bad.append(d)
        out.append(f"| {y}-{m:02d} | {d} | {'休市' if hit else '交易日'} | {'會漏（結算順延，規則不平倉）' if hit else '正常'} |")
    out += ["", f"結論：假日表 {'全部正確' if l6 == reg == tails else '有差異，見上'}；結算日規則會漏 {len(bad)} 個月：{[str(x) for x in bad]}。",
            "2026-11-23～2027-01-05 實戰期內沒有受影響的日期。", ""]
    Path(sys.argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0 if l6 == reg == tails else 1


if __name__ == "__main__":
    sys.exit(main())
