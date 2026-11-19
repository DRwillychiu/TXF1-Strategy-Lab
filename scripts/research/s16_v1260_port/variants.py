"""build 260825 單一開關敏感度（到 2026-08-07 05:00），用來對照存檔錨點 176 筆 / 2,474,800。"""
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import load_bars  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
bars = load_bars(sys.argv[1], datetime(2019, 12, 31), datetime(2026, 8, 7, 5, 0))
hol = s16.holiday_tail(s16.PLA_260825)
base = s16.pla_params(s16.PLA_260825)
for name, over in [("default", {}), ("KB_Gap_Pat=0", {"KB_Gap_Pat": 0}),
                   ("Sess_GapReset_On=0", {"Sess_GapReset_On": 0})]:
    tr = s16.run(bars, {**base, **over}, hol).trades
    s = s16.summarize(tr)
    yrs = Counter(t.entry_dt.year for t in tr)
    net = {y: sum(t.net_ntd for t in tr if t.entry_dt.year == y) for y in sorted(yrs)}
    print(f"{name:<20} {s['trades']} 筆 淨利 {s['net']:,.0f} PF {s['pf']:.4f}")
    print("   ", {y: (yrs[y], int(net[y])) for y in sorted(yrs)})
    print("    出場", dict(Counter(t.exit_label for t in tr)))
