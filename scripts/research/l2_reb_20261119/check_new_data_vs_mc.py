"""新 1 分 K（2000 起）是否仍能逐筆重現 MC 報表：L2 v5.10/v5.11 96 筆、L4 T8 135 列（2026-11-19）。

用法：python scripts/research/l2_reb_20261119/check_new_data_vs_mc.py <1分K檔>
和 tests/test_port_l2_v5_11.py、tests/test_port_l4_v14_10.py 同一套比對，只是資料從 2019-01-02 起
（舊資料檔的起點；新檔從 2000 起，測試裡「MC 起算日前多出幾筆」的寫死數字因此不同）。
"""
import csv, datetime as dt, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from txfcore.instruments.spec import TXF                                 # noqa: E402
from txfcore.profiles import mc_compat                                   # noqa: E402
from txfcore.quotes.bars import aggregate_bars                           # noqa: E402
from txfcore.quotes.daily import NIGHT_FIRST, build                      # noqa: E402
from txfcore.quotes.history import MC12MinuteSource                      # noqa: E402
from txfcore.strategies.l2_trendshort_v5_11 import L2TrendShortV511      # noqa: E402
from txfcore.strategies.l4_consolshort_v14_10 import L4ConsolShortV1410  # noqa: E402
from txfcore.types.mctime import mc_date_to_date                         # noqa: E402

ts = lambda d, t: dt.datetime.combine(mc_date_to_date(d), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")
FIX = os.path.join(ROOT, "tests", "fixtures")


def main(path):
    allm = [m for m in MC12MinuteSource(path).stream() if m.mc_date <= 1260924]
    ok = True
    for start in (1190102, allm[0].mc_date):
        mins = [m for m in allm if m.mc_date >= start]
        # L2
        res = mc_compat.single_runner(L2TrendShortV511()).run(list(aggregate_bars(mins, 60)))
        mc = list(csv.DictReader(open(os.path.join(FIX, "mc_L2_v5.10_trades.csv"))))
        py = [t for t in res.trades if ts(t.entry_date, t.entry_time) >= mc[0]["entry_dt"]]
        got = [(ts(t.entry_date, t.entry_time), t.entry_label, ts(t.exit_date, t.exit_time), round(t.net_ntd(TXF))) for t in py]
        exp = [(m["entry_dt"], m["entry_label"], m["exit_dt"], round(float(m["net_ntd"]))) for m in mc]
        same = sum(1 for a in got if a in exp)
        print(f"起點 {ts(start, 0)[:10]}  L2 v5.11 對 MC v5.10：MC {len(exp)} 筆、Python {len(got)} 筆、相同 {same}；"
              f"完全相同 {sorted(got) == sorted(exp)}")
        ok &= sorted(got) == sorted(exp) if start == 1190102 else True
        # L4
        res = mc_compat.multi_runner(L4ConsolShortV1410()).run(
            list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)), build(mins, NIGHT_FIRST))
        mc = list(csv.DictReader(open(os.path.join(FIX, "mc_L4_T8_trades.csv"))))
        py = [t for t in res.trades if ts(t.entry_date, t.entry_time) >= mc[0]["entry_dt"]]
        key = lambda e, el, x, xl, q: (e, el, x, "Stop Loss" if xl == "ENGINE_STOP" else xl, int(q))
        got = sorted(key(ts(t.entry_date, t.entry_time), t.entry_label, ts(t.exit_date, t.exit_time),
                         t.exit_label, t.quantity) + (round(t.net_ntd(TXF)),) for t in py)
        exp = sorted(key(m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"], m["qty"])
                     + (round(float(m["net_ntd"])),) for m in mc)
        same = sum(1 for a in got if a in exp)
        print(f"起點 {ts(start, 0)[:10]}  L4 v14.10 對 MC T8：MC {len(exp)} 列、Python {len(got)} 列、相同 {same}；完全相同 {got == exp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
