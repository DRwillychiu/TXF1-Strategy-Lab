"""v1.28.1 預設（B）Python 逐筆交易 → CSV，資料起點可選（比對 MC 用）。
Usage: python -I scripts/research/s16_streak_20261118/py_v1281_trades.py <1min.txt> <out.csv> <start YYYY-MM-DD> [TOD_Gate_Days]
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime.fromisoformat(sys.argv[3]), datetime(2026, 11, 16, 12, 20))
    p = s16.pla_params(s16.PLA_2611191)
    if len(sys.argv) > 4:
        p["TOD_Gate_Days"] = float(sys.argv[4])
    tr = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611191)).trades
    with open(sys.argv[2], "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_ntd", "micro_net"])
        for n, t in enumerate(tr, 1):
            w.writerow([n, f"{t.entry_dt:%Y-%m-%d %H:%M}", t.entry_label, t.entry_px, f"{t.exit_dt:%Y-%m-%d %H:%M}",
                        t.exit_label, t.exit_px, round(t.net_ntd), round(micro_net(t))])
    print(sys.argv[3], len(tr), round(sum(t.net_ntd for t in tr)))


if __name__ == "__main__":
    main()
