"""自適應門檻的相鄰參數檢查（60 日視窗，百分位 0.55–0.85）。只看分段總表。
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_plateau.py <1min.txt>
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, rolling_pct_veto, s16, load_bars, micro_net, stats, CAP  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), datetime(2026, 11, 16, 12, 20))
    ap = atr_pct_series(bars)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    segs = [("2001-2019", "2001", "2019-12-31 23:59"), ("2020-2024", "2020", "2024-12-31 23:59"),
            ("2025-2026", "2025", "2099"), ("2020起", "2020", "2099")]
    print("days q    | " + " | ".join(f"{s[0]}: n net mdd% streak" for s in segs))
    for days in (40, 60, 90):
        for q in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85):
            tr = s16.run(bars, dict(p), hol, veto=rolling_pct_veto(ap, days, q)).trades
            cells = []
            for _, a, b in segs:
                x = stats([micro_net(t) for t in tr if a <= t.exit_dt.strftime("%Y-%m-%d %H:%M") <= b])
                cells.append(f"{x['n']:>3} {x['net']:>9,.0f} {x['mdd']/CAP*100:>6.1f}% {x['streak']:>2}")
            print(f"{days:>3}d {q:.2f} | " + " | ".join(cells), flush=True)


if __name__ == "__main__":
    main()
