"""S16 被洗出場後再進場：只動 .pla 現有輸入（ReEntry_*），依事先寫死的標準判定。
標準：docs/ops/S16_boss_20261120/S16_reentry_opt_criteria_20261119.md（看結果前寫死）。
Python 引擎（B 上＝MC v1281c 逐筆），結果標推論。2 口微台淨額、資金 140,200。

Usage: python -I scripts/research/s16_streak_20261118/s16_reentry_opt.py <1min.txt> <out.md>
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net  # noqa: E402
from s16_crash_opt import metrics, crash_days, CUT  # noqa: E402

LIMIT = 21_030
CANDS = [
    ("B（現行）", {}),
    ("R0 關掉再進場", {"ReEntry_On": 0}),
    ("R1 不要求急跌那一根", {"ReEntry_Slope_Gate": 0}),
    ("R2 已在原進場價下也可再空", {"ReEntry_Close_Gate": 0}),
    ("R3 R1＋R2", {"ReEntry_Slope_Gate": 0, "ReEntry_Close_Gate": 0}),
    ("R4 不檢查結構（確認用）", {"ReEntry_Structure_Gate": 0}),
]


def judge(x, b):
    return [x["net"] >= b["net"] * 1.05,
            x["mdd"] >= -LIMIT and x["mdd"] >= b["mdd"] * 1.2,
            x["streak"] <= max(b["streak"] + 2, 9),
            all(x["yr"][y] >= b["yr"][y] for y in (2024, 2025, 2026)) and x["yr"][2023] >= b["yr"][2023] - 2000,
            x["exp"] >= b["exp"],
            x["val"] >= b["val"] - 5000]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    base = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    cdays = crash_days(bars)
    res = []
    for name, extra in CANDS:
        q = dict(base); q.update(extra)
        tr = s16.run(bars, q, hol).trades
        res.append((name, extra, metrics(tr, cdays), tr))
    b = res[0][2]
    out = ["# S16 被洗出場後再進場：結果（2023-01～2026-11-16；推論：Python 引擎，B＝MC 逐筆）", "",
           "標準看結果前寫死：`S16_reentry_opt_criteria_20261119.md`。2 口微台淨額、資金 140,200。", "",
           "| 版本 | 筆數 | 再進場筆數 | 再進場淨利 | 淨利 | 變化 | 每筆期望值 | 回撤 | 連虧 | 2023 | 2024 | 2025 | 2026 | 2020–22 | (a)(b)(c)(d)(e)(f) | 判定 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, extra, x, tr in res:
        re_n, re_p = x["lab"].get("SE_MA_ReEntry", [0, 0.0])
        c = judge(x, b)
        verdict = "對照" if not extra else ("通過" if all(c) else "不通過")
        out.append(f"| {name} | {x['n']} | {re_n} | {re_p:,.0f} | {x['net']:,.0f} | {(x['net'] / b['net'] - 1) * 100:+.1f}% | "
                   f"{x['exp']:,.0f} | {x['mdd']:,.0f} | {x['streak']} | "
                   + " | ".join(f"{x['yr'][y]:,.0f}" for y in range(2023, 2027))
                   + f" | {x['val']:,.0f} | {''.join('O' if k else 'X' for k in c)} | {verdict} |")
    # 再進場逐筆（2020 起），每個版本
    for name, extra, x, tr in res:
        rows = [t for t in tr if t.entry_label == "SE_MA_ReEntry" and datetime(2020, 1, 1) <= t.exit_dt <= CUT]
        if not rows:
            continue
        w = sum(1 for t in rows if micro_net(t) > 0)
        out += ["", f"## {name}：再進場 2020 起 {len(rows)} 筆、勝 {w} 筆、合計 {sum(micro_net(t) for t in rows):,.0f}", "",
                "| 進場 | 價 | 出場 | 出場方式 | 淨額 |", "|---|---|---|---|---|"]
        for t in rows[:60]:
            out.append(f"| {t.entry_dt:%Y-%m-%d %H:%M} | {t.entry_px:,.0f} | {t.exit_dt:%m-%d %H:%M} | {t.exit_label} | {micro_net(t):,.0f} |")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:14]))


if __name__ == "__main__":
    main()
