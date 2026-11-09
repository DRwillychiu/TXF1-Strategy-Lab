"""L4 v14.10 移植：考題轉回歸測試（2026-10-07）。

快測：29 個 input ＝ .pla。
慢測：TXF1_MIN_DATA 有設才跑，Python（MC 相容模式、日線＝收盤日歸屬）對 T8 報表 135 列逐列相同。
"""
import csv, datetime as dt, os, re
from pathlib import Path

import pytest

from txfcore.strategies.l4_consolshort_v14_10 import DEFAULT_PARAMS, L4ConsolShortV1410

ROOT = Path(__file__).resolve().parent.parent
PLA = ROOT / "strategies/research/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla"
FIX = ROOT / "tests/fixtures/mc_L4_T8_trades.csv"


def test_inputs_match_pla():
    from txfcore.config.loader import check_against_pla, load_strategy, pla_inputs
    cfg = load_strategy("L4_v14.10", check=False)
    assert len(pla_inputs(cfg["pla"])) == 29 == len(DEFAULT_PARAMS)
    assert check_against_pla(cfg) == []

@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA）")
def test_matches_mc_t8_row_by_row():
    from txfcore.profiles import mc_compat
    from txfcore.instruments.spec import TXF
    from txfcore.quotes.bars import aggregate_bars
    from txfcore.quotes.daily import NIGHT_FIRST, build
    from txfcore.quotes.history import MC12MinuteSource
    from txfcore.types.mctime import mc_date_to_date

    mins = [m for m in MC12MinuteSource(os.environ["TXF1_MIN_DATA"]).stream() if m.mc_date <= 1260924]
    res = mc_compat.multi_runner(L4ConsolShortV1410()).run(
        list(aggregate_bars(mins, 15)), list(aggregate_bars(mins, 60)), build(mins, NIGHT_FIRST))
    ts = lambda d, t: dt.datetime.combine(mc_date_to_date(d), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")
    mc = list(csv.DictReader(FIX.open()))
    py = [t for t in res.trades if ts(t.entry_date, t.entry_time) >= mc[0]["entry_dt"]]
    # MC 圖表起算日前 Python 多出的交易（MC 沒有資料，不比）。數量寫死，變動即紅燈（審查 M1）
    assert len(res.trades) - len(py) == 18
    key = lambda e, el, x, xl, q: (e, el, x, "Stop Loss" if xl == "ENGINE_STOP" else xl, int(q))
    got = sorted(key(ts(t.entry_date, t.entry_time), t.entry_label, ts(t.exit_date, t.exit_time),
                     t.exit_label, t.quantity) + (round(t.net_ntd(TXF)),) for t in py)
    exp = sorted(key(m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"], m["qty"])
                 + (round(float(m["net_ntd"])),) for m in mc)
    assert got == exp and len(exp) == 135
