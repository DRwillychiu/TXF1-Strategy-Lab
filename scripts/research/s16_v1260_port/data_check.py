"""同一個 build 260825 在兩份 1 分 K 上跑到 2026-08-07 05:00，比較交易是否相同（排除資料差異）。"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import load_bars  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
end = datetime(2026, 8, 7, 5, 0)
runs = []
for f in sys.argv[1:]:
    bars = load_bars(f, datetime(2019, 12, 31), end)
    tr = s16.run(bars, s16.pla_params(s16.PLA_260825), s16.holiday_tail(s16.PLA_260825)).trades
    runs.append([(t.entry_dt, t.exit_dt, t.entry_px, t.exit_px, t.exit_label) for t in tr])
    print(Path(f).name, s16.summarize(tr))
a, b = runs
diff = sorted(set(a) ^ set(b))
print("差異筆數", len(diff))
for x in diff[:10]:
    print(" ", "A" if x in a else "B", x)
