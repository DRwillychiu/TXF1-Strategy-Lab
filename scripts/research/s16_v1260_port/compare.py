"""S16 v1.26.0 Python 對 MC 報表逐筆比對（研究用；正式考題在 tests/test_port_s16_v1_26.py）。

用法：python -I scripts/research/s16_v1260_port/compare.py <1分K> [起始 YYYY-MM-DD]
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import load_bars  # noqa: E402

FIX = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_trades.csv"
SET = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_settings.txt"


def mc_params():
    vec = [ln.split("\t", 1)[1] for ln in SET.read_text(encoding="utf-8").splitlines()
           if ln.startswith("策略參數")][0]
    return s16.params_from_mc_vector(s16.PLA_260820, vec)


def main():
    start = datetime.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime(2019, 12, 31)
    bars = load_bars(sys.argv[1], start, datetime(2026, 8, 1, 5, 0))
    res = s16.run(bars, mc_params(), s16.holiday_tail(s16.PLA_260820))
    mc = list(csv.DictReader(FIX.open(encoding="utf-8")))
    py = [t for t in res.trades if t.entry_dt.strftime("%Y-%m-%d %H:%M") >= mc[0]["entry_dt"]]
    print(f"bars {len(bars)}  py trades {len(res.trades)} (from MC start {len(py)})  mc {len(mc)}")
    same = 0
    for k, (p, m) in enumerate(zip(py, mc)):
        ok = (p.entry_dt.strftime("%Y-%m-%d %H:%M") == m["entry_dt"] and p.entry_label == m["entry_label"]
              and p.exit_dt.strftime("%Y-%m-%d %H:%M") == m["exit_dt"]
              and p.exit_label[:19] == m["exit_label"][:19]
              and abs(p.entry_px - float(m["entry_px"])) < .5 and abs(p.exit_px - float(m["exit_px"])) < .5
              and abs(p.net_ntd - float(m["net_ntd"])) < 1)
        if not ok:
            print(f"FIRST MISMATCH #{k + 1}")
            print("  py", p.entry_dt, p.entry_label, p.entry_px, p.exit_dt, p.exit_label, p.exit_px, p.net_ntd)
            print("  mc", m["entry_dt"], m["entry_label"], m["entry_px"], m["exit_dt"], m["exit_label"],
                  m["exit_px"], m["net_ntd"])
            break
        same += 1
    print(f"match {same}/{len(mc)}")
    print(s16.summarize(py))


if __name__ == "__main__":
    main()
