"""L2 v5.11 移植：考題轉回歸測試（2026-10-07）。

快測：41 個 input 名稱與預設值 ＝ .pla。
慢測：設環境變數 TXF1_MIN_DATA（MC 匯出 1 分 K，迄 2026/09/24）才跑，
      Python（MC 相容模式）對 MC v5.10 單圖報表 96 筆逐筆相同。
"""
import csv, datetime as dt, os, re
from pathlib import Path

import pytest

from txfcore.strategies.l2_trendshort_v5_11 import DEFAULT_PARAMS, L2TrendShortV511

ROOT = Path(__file__).resolve().parent.parent
PLA = ROOT / "strategies/research/L2_TrendShort/L2_v5.11/L2_TrendShort_v5.11.pla"
FIX = ROOT / "tests/fixtures/mc_L2_v5.10_trades.csv"




def test_inputs_match_pla():
    from txfcore.config.loader import check_against_pla, load_strategy, pla_inputs
    cfg = load_strategy("L2_v5.11", check=False)
    assert len(pla_inputs(cfg["pla"])) == 41 == len(DEFAULT_PARAMS)
    assert check_against_pla(cfg) == []

@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA）")
def test_matches_mc_v510_trade_by_trade():
    from txfcore.profiles import mc_compat
    from txfcore.instruments.spec import TXF
    from txfcore.quotes.bars import aggregate_bars
    from txfcore.quotes.history import MC12MinuteSource
    from txfcore.types.mctime import mc_date_to_date

    mins = [m for m in MC12MinuteSource(os.environ["TXF1_MIN_DATA"]).stream() if m.mc_date <= 1260924]
    m60 = list(aggregate_bars(mins, 60))
    res = mc_compat.single_runner(L2TrendShortV511()).run(m60)
    ts = lambda d, t: dt.datetime.combine(mc_date_to_date(d), dt.time(t // 100, t % 100)).strftime("%Y-%m-%d %H:%M")
    mc = list(csv.DictReader(FIX.open()))
    py = [t for t in res.trades if ts(t.entry_date, t.entry_time) >= mc[0]["entry_dt"]]
    # MC 圖表起算日前 Python 多出的交易（MC 沒有資料，不比）。數量寫死，變動即紅燈（審查 M1）
    assert len(res.trades) - len(py) == 10
    assert len(py) == len(mc) == 96
    for p, m in zip(py, mc):
        assert ts(p.entry_date, p.entry_time) == m["entry_dt"] and p.entry_label == m["entry_label"]
        assert ts(p.exit_date, p.exit_time) == m["exit_dt"]
        assert abs(p.entry_price - float(m["entry_px"])) < 0.5 and abs(p.exit_price - float(m["exit_px"])) < 0.5
        assert abs(p.net_ntd(TXF) - float(m["net_ntd"])) < 1
        assert p.exit_label == m["exit_label"] or (p.exit_label == "ENGINE_STOP" and m["exit_label"] == "Stop Loss")
