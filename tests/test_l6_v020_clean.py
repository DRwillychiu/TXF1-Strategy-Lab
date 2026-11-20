"""L6_MACrossShort_v0.2.0（開發版，Willy 11/20「L6只保留現階段定案的參數以及程式碼就好」）＝ v0.1.0 去掉關閉的功能。
保留的 input 與 v0.1.0 值完全相同；刪掉的 input 全部是「關閉」或「固定模式」的值；交易逐筆相同。"""
import csv
import os
import re
from datetime import datetime
from pathlib import Path

import pytest

from txfcore.strategies import s16_s_v1_26 as s16

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "strategies/research/L6_MACrossShort/L6_v0.2.0"
PLA = DIR / "L6_MACrossShort_v0.2.0.pla"

# 刪掉的 input 與它們在 v0.1.0 的值（關閉＝0，或固定模式）
REMOVED = {
    "MinSlope": 28, "Slope_Form": 2, "Slope_Require_Adjacent": 0, "Vol_Gate_Pct": 0,
    "ML_On": 0, "ML_ActivationPct": 20, "ML_ScoreTrigger": 60, "ML_MinCategories": 3, "ML_VolAvgLen": 15,
    "ML_VolSpikeMult": 2.0, "ML_MA_ShortLen": 10, "ML_ATR_ShortLen": 3, "ML_ATR_LongLen": 90, "ML_ATR_Ratio": 2.5,
    "Trail_On": 0, "Trail_Trigger_Pct": 2.0, "Trail_Giveback_Pct": 40,
    "Tier2_On": 0, "Tier2_Trigger_Pct": 2.0, "Tier2_Giveback_Pct": 40,
    "Struct_UseClose": 1, "M8_Form": 2, "KB_Entry_Mode": 0, "BullExit_Mode": 0, "KB_Gap_Pat": 1, "Gap_KB_Group": 1,
    "UpGap_Gate_On": 0, "UpGap_Mode": 1, "UpGap_Min_Pct": 0.1, "UpGap_Bar1_Pct": 0.2, "UpGap_Scope_Bars": 3,
    "UpGap_Relax_Mult": 0.5,
}
GONE_ORDERS = ["SE_MA_StructLead", "SE_MA_StructLate", "SX_MA_BullStruct", "SX_MA_ML_Exit", "SX_MA_Trail"]


def _params():
    """引擎用：v0.2.0 的 input ＋ 刪掉的（關閉值）。"""
    return {**{k: float(v) for k, v in REMOVED.items()}, **s16.pla_params(PLA)}


def test_v020_inputs_are_v010_minus_off_features():
    old, new = s16.pla_params(s16.PLA_L6_V010), s16.pla_params(PLA)
    assert {k: old[k] for k in old if k not in new} == {k: float(v) for k, v in REMOVED.items()}
    assert set(new) <= set(old)
    assert new["Build_ID"] == 2611202
    assert {k: v for k, v in new.items() if k != "Build_ID"} == \
        {k: old[k] for k in new if k != "Build_ID"}


def test_v020_file_format_calendar_and_orders():
    pla = PLA.read_bytes()
    assert (DIR / "L6_MACrossShort_v0.2.0.txt").read_bytes() == pla
    assert all(c < 128 for c in pla) and pla.count(b"\r\n") == pla.count(b"\n")
    txt = pla.decode("ascii")
    assert txt.count("{") == txt.count("}")
    code = re.sub(r"\{[^}]*\}", "", txt)
    for name in list(REMOVED) + GONE_ORDERS + ["v_KB_Bull3", "v_Entry_Src"]:
        assert not re.search(rf"\b{name}\b", code), name
    for prefix in ["v_ML_", "v_Trail", "v_UpGap"]:
        assert prefix not in code, prefix
    assert s16.holiday_tail(PLA) == s16.holiday_tail(s16.PLA_L6_V010)
    assert s16.settle_shift(PLA) == ({1270915}, {1270916})
    old = re.sub(r"\{[^}]*\}", "", s16.PLA_L6_V010.read_text(encoding="ascii"))
    names = lambda s: sorted(re.findall(r'\(\s*"(S[EX]_MA_\w+)"\s*\)', s))
    assert names(code) == sorted(n for n in names(old) if n not in GONE_ORDERS)


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-19）")
def test_v020_history_equals_v010_and_mc():
    """2019 起：v0.2.0 參數跑出的交易＝v0.1.0 逐筆相同；對 MC v1281c 報表 144 筆相同。"""
    from txfcore.quotes.history import MC12MinuteSource
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 1, 1), datetime(2026, 11, 19, 13, 45))
    new = s16.run(bars, _params(), s16.holiday_tail(PLA), settle_shift=s16.settle_shift(PLA)).trades
    old = s16.run(bars, s16.pla_params(s16.PLA_L6_V010), s16.holiday_tail(s16.PLA_L6_V010),
                  settle_shift=s16.settle_shift(s16.PLA_L6_V010)).trades
    key = lambda t: (t.entry_dt, t.entry_label, t.exit_dt, t.exit_label, round(t.net_ntd, 6))
    assert [key(t) for t in new] == [key(t) for t in old]
    fx = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_trades.csv"
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    got = [t for t in new if t.entry_dt.strftime("%Y-%m-%d %H:%M") >= mc[0]["entry_dt"]]
    assert len(got) == len(mc) == 144
    for t, m in zip(got, mc):
        assert (t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.exit_dt.strftime("%Y-%m-%d %H:%M"),
                t.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(t.net_ntd - float(m["net_ntd"])) < 1
