"""Python S16 (build 260820 logic) vs ANY MC report export, trade by trade, using that report's own inputs.

Usage: python -I scripts/research/s16_v1260_port/compare_report.py <1min.txt> <trades.csv> <settings.txt> [end YYYY-MM-DDTHH:MM]
trades.csv / settings.txt come from extract_mc_trades.py.
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

KEY = lambda e, el, ep, x, xl, xp, n: (e, el, round(float(ep)), x, xl[:19], round(float(xp)), round(float(n)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data, tr, st = sys.argv[1:4]
    end = datetime.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else datetime(2026, 12, 31)
    vec = [ln.split("\t", 1)[1] for ln in Path(st).read_text(encoding="utf-8").splitlines()
           if ln.startswith("策略參數")][0]
    res = s16.run(load_bars(data, datetime(2019, 12, 31), end),
                  s16.params_from_mc_vector(s16.PLA_260820, vec), s16.holiday_tail(s16.PLA_260820))
    mc = list(csv.DictReader(open(tr, encoding="utf-8")))
    py = [t for t in res.trades if t.entry_dt.strftime("%Y-%m-%d %H:%M") >= mc[0]["entry_dt"]]
    f = "%Y-%m-%d %H:%M"
    pk = [KEY(t.entry_dt.strftime(f), t.entry_label, t.entry_px, t.exit_dt.strftime(f), t.exit_label,
              t.exit_px, t.net_ntd) for t in py]
    mk = [KEY(m["entry_dt"], m["entry_label"], m["entry_px"], m["exit_dt"], m["exit_label"],
              m["exit_px"], m["net_ntd"]) for m in mc]
    same = sum(1 for a, b in zip(pk, mk) if a == b)
    print(f"py {len(pk)} trades / {sum(k[-1] for k in pk):,}   mc {len(mk)} / {sum(k[-1] for k in mk):,}")
    print(f"positional match {same}/{len(mk)}")
    only_py, only_mc = sorted(set(pk) - set(mk)), sorted(set(mk) - set(pk))
    print(f"only in python: {len(only_py)}   only in mc: {len(only_mc)}")
    for k in only_py[:10]:
        print("  PY ", k)
    for k in only_mc[:10]:
        print("  MC ", k)


if __name__ == "__main__":
    main()
