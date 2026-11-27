"""封存（2026-11-27，md_audit）：原在 tests/test_port_s16_v1_26.py。
封存原因：4 題都要 build 260820 的原始 .pla（S16_S_MACrossShort_v1.26.0.pla.bak_20260821），
該檔被 .gitignore 擋在 repo 外，任何電腦 clone 下來都只能跳過；上架版已是 v1.28.1。
檔名不以 test_ 開頭，pytest 不會收進來。要復活：把 .bak 用 git add -f 補進 repo，再把函式搬回原檔。
"""
import csv
import os
from datetime import datetime
from pathlib import Path

import pytest

from txfcore.strategies import s16_s_v1_26 as s16

ROOT = Path(__file__).resolve().parents[4]
FIX = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_trades.csv"
SET = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_settings.txt"


def _mc_vector() -> str:
    return [ln.split("	", 1)[1] for ln in SET.read_text(encoding="utf-8").splitlines()
            if ln.startswith("策略參數")][0]


# build 260820 的原始 .pla（*.bak_20260821）被 .gitignore 的 *.bak_* 擋掉，只存在產生它的那台電腦。
# 其他電腦沒有這個檔，這兩題跳過而不是失敗；要在這台跑，先在那台用 git add -f 把檔案補進 repo。
_NEED_260820 = pytest.mark.skipif(not s16.PLA_260820.exists(),
                                  reason="缺 build 260820 原始 .pla（*.bak_20260821 未進 git）")


@_NEED_260820
def test_mc_vector_maps_to_pla_inputs():
    p = s16.params_from_mc_vector(s16.PLA_260820, _mc_vector())
    d = s16.pla_params(s16.PLA_260820)
    assert len(p) == len(d) == 91
    diff = {k for k in d if p[k] != d[k]}
    assert diff == {"ReEntry_Filt_Mode"} and p["ReEntry_Filt_Mode"] == 1 and p["Build_ID"] == 260820


@_NEED_260820
def test_current_build_defaults():
    d = s16.pla_params(s16.PLA_260825)
    assert d["Build_ID"] == 260825 and d["KB_Entry_Mode"] == 0 and d["BullExit_Mode"] == 0
    assert s16.holiday_tail(s16.PLA_260825) == s16.holiday_tail(s16.PLA_260820)
    assert len(s16.holiday_tail(s16.PLA_260820)) == 63

@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA）")
def test_matches_mc_260820_trade_by_trade():
    from txfcore.quotes.history import MC12MinuteSource
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 12, 31), datetime(2026, 8, 1, 5, 0))
    res = s16.run(bars, s16.params_from_mc_vector(s16.PLA_260820, _mc_vector()),
                  s16.holiday_tail(s16.PLA_260820))
    mc = list(csv.DictReader(FIX.open(encoding="utf-8")))
    assert len(res.trades) == len(mc) == 161
    for p, m in zip(res.trades, mc):
        assert p.entry_dt.strftime("%Y-%m-%d %H:%M") == m["entry_dt"] and p.entry_label == m["entry_label"]
        assert p.exit_dt.strftime("%Y-%m-%d %H:%M") == m["exit_dt"]
        assert p.exit_label[:19] == m["exit_label"][:19]
        assert abs(p.entry_px - float(m["entry_px"])) < .5 and abs(p.exit_px - float(m["exit_px"])) < .5
        assert abs(p.net_ntd - float(m["net_ntd"])) < 1
    assert sum(t.net_ntd for t in res.trades) == 2769200


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_matches_mc_260820_re0_to_20261116():
    """第二份 MC 報表（Willy 11/16 跑，build 260820、ReEntry_Filt_Mode=0、資料到 2026-11-16 12:20）。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re0_to20261116_trades.csv"
    st = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re0_to20261116_settings.txt"
    vec = [ln.split("\t", 1)[1] for ln in st.read_text(encoding="utf-8").splitlines()
           if ln.startswith("策略參數")][0]
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 12, 31), datetime(2026, 11, 16, 12, 20))
    res = s16.run(bars, s16.params_from_mc_vector(s16.PLA_260820, vec), s16.holiday_tail(s16.PLA_260820))
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    assert len(res.trades) == len(mc) == 172
    for p, m in zip(res.trades, mc):
        assert (p.entry_dt.strftime("%Y-%m-%d %H:%M"), p.entry_label, p.exit_dt.strftime("%Y-%m-%d %H:%M"),
                p.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(p.net_ntd - float(m["net_ntd"])) < 1
    assert sum(t.net_ntd for t in res.trades) == 3414000
