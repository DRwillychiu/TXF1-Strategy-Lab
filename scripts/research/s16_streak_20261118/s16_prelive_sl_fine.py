"""停損價格上限細格（SL_Pct 0.75–1.0，ATR 倍數 4）：看 0.8 是不是在高原邊緣。
Usage: python -I scripts/research/s16_streak_20261118/s16_prelive_sl_fine.py <1min.txt> <out.md>
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s16_prelive import END, IS_START, L23, today_net, stats, s16, load_bars  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), END)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    out = ["# S16 B 停損價格上限細格（ATR 倍數 4；推論）", "",
           "| SL_Pct | 筆數 | 原始年化 | 原始期望值 | 原始回撤 | 今日價位年化 | 今日價位期望值 | 今日價位回撤 | 今日價位單筆最大虧損 | 2023 起今日價位回撤 | 停損出場筆數 |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for slp in (0.75, 0.8, 0.85, 0.9, 0.95, 1.0):
        tr = [t for t in s16.run(bars, dict(p, SL_Pct=slp), hol).trades if t.exit_dt >= IS_START]
        r, t_ = stats(tr, IS_START, 6.876), stats(tr, IS_START, 6.876, today_net)
        t23 = stats(tr, L23, 3.876, today_net)
        nstop = sum(1 for t in tr if "Stop" in t.exit_label or "SL" in t.exit_label)
        out.append(f"| {slp} | {r['n']} | {r['ann']:.1f}% | {r['exp']:,.0f} | {r['mdd_pct']:.1f}% | {t_['ann']:.1f}% | "
                   f"{t_['exp']:,.0f} | {t_['mdd_pct']:.1f}% | {t_['worst']:,.0f} | {t23['mdd_pct']:.1f}% | {nstop} |")
        print(out[-1], flush=True)
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
