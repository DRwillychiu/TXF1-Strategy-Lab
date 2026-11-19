"""2023 起（Willy 11/18：以 2023–2026 近期為主）的門檻比較，並列出自適應門檻在各時點的實際數值。
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_2023.py <1min.txt>
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, rolling_pct_veto, s16, load_bars, micro_net, stats, CAP, BARS_PER_DAY  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), datetime(2026, 11, 16, 12, 20))
    ap = atr_pct_series(bars)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    variants = {"現行 260825": (dict(p), None), "固定 0.20%": (dict(p, Vol_Gate_Pct=0.20), None)}
    for d, q in ((60, 0.60), (60, 0.65), (60, 0.70), (60, 0.75), (40, 0.70), (90, 0.70)):
        variants[f"自適應 {d}日 p{int(q*100)}"] = (dict(p), rolling_pct_veto(ap, d, q))
    print("== 2023-01-01 起（2 口微台、資金 140,200）")
    print("版本 | 筆數 | 淨利 | PF | 最大回撤 | 佔資金 | 最長連虧 | 勝率")
    for name, (prm, veto) in variants.items():
        tr = s16.run(bars, prm, hol, veto=veto).trades
        x = stats([micro_net(t) for t in tr if t.exit_dt >= datetime(2023, 1, 1)])
        print(f"{name} | {x['n']} | {x['net']:,.0f} | {x['pf']:.2f} | {x['mdd']:,.0f} | {x['mdd']/CAP*100:.1f}% | "
              f"{x['streak']} | {x['win']*100:.0f}%")
    print("\n== 自適應 60日 p70 的門檻在各時點的實際數值（只用該時點以前 60 天的資料）")
    print("時點 | 收盤 | 當下 ATR14 點數 | 當下 ATR% | 門檻 ATR% | 門檻換成點數 | 固定0.20%換成點數")
    win = 60 * BARS_PER_DAY
    for when in ("2023-06-30 13:45", "2024-06-28 13:45", "2025-06-30 13:45", "2026-03-31 13:45",
                 "2026-06-30 13:45", "2026-11-13 13:45"):
        t = datetime.fromisoformat(when)
        i = max(k for k, b in enumerate(bars) if b.dt <= t)
        hist = sorted(ap[max(0, i - win):i])
        thr = hist[int(len(hist) * 0.70)]
        c = bars[i].c
        print(f"{bars[i].dt:%Y-%m-%d %H:%M} | {c:,.0f} | {ap[i]*c/100:.1f} | {ap[i]:.3f} | {thr:.3f} | "
              f"{thr*c/100:.1f} | {0.20*c/100:.1f}")


if __name__ == "__main__":
    main()
