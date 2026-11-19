"""S16_S v1.26.0 移植考題（2026-11-16）。

快測：MC 設定頁參數向量 ↔ .pla inputs 一一對應；5 分 K 聚合與 txfcore 通用聚合器一致。
慢測：設 TXF1_MIN_DATA（MC 匯出 1 分 K，需涵蓋 2019-12-31～2026-08-01）才跑：
      Python 對 MC12 報表（build 260820、ReEntry_Filt_Mode=1）161 筆逐筆相同。
"""
import csv
import os
from datetime import datetime
from pathlib import Path

import pytest

from txfcore.strategies import s16_s_v1_26 as s16

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_trades.csv"
SET = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260820_re1_settings.txt"


def _mc_vector() -> str:
    return [ln.split("\t", 1)[1] for ln in SET.read_text(encoding="utf-8").splitlines()
            if ln.startswith("策略參數")][0]


def test_mc_vector_maps_to_pla_inputs():
    p = s16.params_from_mc_vector(s16.PLA_260820, _mc_vector())
    d = s16.pla_params(s16.PLA_260820)
    assert len(p) == len(d) == 91
    diff = {k for k in d if p[k] != d[k]}
    assert diff == {"ReEntry_Filt_Mode"} and p["ReEntry_Filt_Mode"] == 1 and p["Build_ID"] == 260820


def test_current_build_defaults():
    d = s16.pla_params(s16.PLA_260825)
    assert d["Build_ID"] == 260825 and d["KB_Entry_Mode"] == 0 and d["BullExit_Mode"] == 0
    assert s16.holiday_tail(s16.PLA_260825) == s16.holiday_tail(s16.PLA_260820)
    assert len(s16.holiday_tail(s16.PLA_260820)) == 63


def test_aggregate_matches_generic_aggregator():
    from txfcore.quotes.bars import aggregate_bars
    from txfcore.types.bar import Bar
    mins, t = [], datetime(2026, 6, 1, 8, 46)
    raw = [(2026, 6, 1, 8, 46), (2026, 6, 1, 8, 50), (2026, 6, 1, 8, 51), (2026, 6, 1, 13, 45),
           (2026, 6, 1, 15, 1), (2026, 6, 1, 23, 56), (2026, 6, 2, 0, 0), (2026, 6, 2, 0, 1),
           (2026, 6, 2, 5, 0)]
    for k, (y, mo, d, hh, mm) in enumerate(raw):
        mins.append(Bar(mc_date=(y - 1900) * 10000 + mo * 100 + d, mc_time=hh * 100 + mm,
                        open=100 + k, high=110 + k, low=90 + k, close=105 + k, volume=1, tick_count=None))
    mine = [(b.mc_date, b.mc_time, b.o, b.h, b.l, b.c) for b in s16.aggregate_5m(mins)]
    gen = [(b.mc_date, b.mc_time, b.open, b.high, b.low, b.close) for b in aggregate_bars(mins, 5)]
    assert mine == gen


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


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_matches_mc_260825_current_to_20261116():
    """現行版（Willy 11/16 跑，build 260825 預設值、資料到 2026-11-16 12:20）：192 筆逐筆相同。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv"
    st = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_settings.txt"
    vec = [ln.split("\t", 1)[1] for ln in st.read_text(encoding="utf-8").splitlines()
           if ln.startswith("策略參數")][0]
    p = s16.params_from_mc_vector(s16.PLA_260825, vec)
    assert p == s16.pla_params(s16.PLA_260825)  # MC 跑的就是檔案預設值
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 12, 31), datetime(2026, 11, 16, 12, 20))
    res = s16.run(bars, p, s16.holiday_tail(s16.PLA_260825))
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    assert len(res.trades) == len(mc) == 192
    for t, m in zip(res.trades, mc):
        assert (t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.exit_dt.strftime("%Y-%m-%d %H:%M"),
                t.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(t.net_ntd - float(m["net_ntd"])) < 1
    assert sum(t.net_ntd for t in res.trades) == 3232800


def test_candidate_v1270_params_are_260825_plus_vol_gate():
    """v1.27.0 候選（研究，2026-11-18）：只多 Vol_Gate_Pct（預設 0.20），其餘與 260825 相同。"""
    c = s16.pla_params(s16.PLA_261118)
    b = s16.pla_params(s16.PLA_260825)
    assert c["Build_ID"] == 261118 and c["Vol_Gate_Pct"] == 0.20
    assert set(c) - set(b) == {"Vol_Gate_Pct"}
    assert {k for k in b if c[k] != b[k]} == {"Build_ID"}


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_candidate_v1270_gate_off_equals_mc_260825_and_gate_on_is_locked():
    """門檻 0 ＝ MC 260825 的 192 筆；門檻 0.20 的 Python 結果鎖定（85 筆、3,582,800，推論，待 MC）。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv"
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 12, 31), datetime(2026, 11, 16, 12, 20))
    p = s16.pla_params(s16.PLA_261118)
    hol = s16.holiday_tail(s16.PLA_261118)
    off = s16.run(bars, {**p, "Vol_Gate_Pct": 0}, hol)
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    assert [(t.entry_dt.strftime("%Y-%m-%d %H:%M"), round(t.net_ntd)) for t in off.trades] == \
        [(m["entry_dt"], round(float(m["net_ntd"]))) for m in mc]
    on = s16.run(bars, p, hol)
    assert len(on.trades) == 85 and round(sum(t.net_ntd for t in on.trades)) == 3582800


def test_candidate_v1280_params_are_260825_plus_tod_gate():
    """v1.28.0 候選（研究，2026-11-18）：260825 ＋ Vol_Gate_Pct（預設 0＝關）＋ TOD_Gate_Days 60／TOD_Gate_Q 0.70。"""
    c = s16.pla_params(s16.PLA_2611181)
    b = s16.pla_params(s16.PLA_260825)
    assert c["Build_ID"] == 2611181 and c["Vol_Gate_Pct"] == 0
    assert c["TOD_Gate_Days"] == 60 and c["TOD_Gate_Q"] == 0.70
    assert set(c) - set(b) == {"Vol_Gate_Pct", "TOD_Gate_Days", "TOD_Gate_Q"}
    assert {k for k in b if c[k] != b[k]} == {"Build_ID"}
    assert s16.holiday_tail(s16.PLA_2611181) == s16.holiday_tail(s16.PLA_260825)
    raw = s16.PLA_2611181.read_bytes()
    assert max(raw) < 128, "MC 只吃 ASCII"
    assert raw == s16.PLA_2611181.with_suffix(".txt").read_bytes(), ".txt 閱讀版必須與 .pla 相同"


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_candidate_v1280_gate_off_equals_mc_260825_and_sets_are_locked():
    """同時段門檻關 ＝ MC 260825 的 192 筆；A（60 日 p70）、B（90 日 p70）結果鎖定（推論，待 MC）。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv"
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 12, 31), datetime(2026, 11, 16, 12, 20))
    p = s16.pla_params(s16.PLA_2611181)
    hol = s16.holiday_tail(s16.PLA_2611181)
    off = s16.run(bars, {**p, "TOD_Gate_Days": 0}, hol)
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    assert [(t.entry_dt.strftime("%Y-%m-%d %H:%M"), round(t.net_ntd)) for t in off.trades] == \
        [(m["entry_dt"], round(float(m["net_ntd"]))) for m in mc]
    a = s16.run(bars, p, hol)
    assert len(a.trades) == 131 and round(sum(t.net_ntd for t in a.trades)) == 3652000
    b = s16.run(bars, {**p, "TOD_Gate_Days": 90}, hol)
    # 11/19 百分位索引改成數學取整（+1e-9）後：138 筆、4,015,600（資料 2019-12-31 起，暖機不足少 2020-04-09 一筆）
    assert len(b.trades) == 138 and round(sum(t.net_ntd for t in b.trades)) == 4015600


# 期交所 116 年行事曆（台期交字第 1150003597 號，2026-11-10）依 2026 同一規則推出的尾日
HOLIDAY_TAIL_2027 = {1270202, 1270227, 1270403, 1270430, 1270609, 1270915, 1270928,
                     1271009, 1271023, 1271224, 1271231}


def test_candidate_v1281_is_v1280_with_b_default_and_2027_registry():
    """v1.28.1：只改 Build_ID、TOD_Gate_Days 預設 90、Registry_Valid_Until 1271231、補 2027 假日 11 筆。"""
    c = s16.pla_params(s16.PLA_2611191)
    o = s16.pla_params(s16.PLA_2611181)
    assert set(c) == set(o)
    assert {k for k in o if c[k] != o[k]} == {"Build_ID", "TOD_Gate_Days", "Registry_Valid_Until"}
    assert c["Build_ID"] == 2611191 and c["TOD_Gate_Days"] == 90 and c["Registry_Valid_Until"] == 1271231
    assert s16.holiday_tail(s16.PLA_2611191) == s16.holiday_tail(s16.PLA_2611181) | HOLIDAY_TAIL_2027
    raw = s16.PLA_2611191.read_bytes()
    assert max(raw) < 128, "MC 只吃 ASCII"
    assert raw == s16.PLA_2611191.with_suffix(".txt").read_bytes(), ".txt 閱讀版必須與 .pla 相同"
    assert raw.count(b"Holiday_Tail[") - 1 <= 80, "Holiday_Tail 陣列只有 80 格"


def test_mc_v1281c_gate_off_equals_mc_260825():
    """MC 對 MC：v1.28.1 設 TOD_Gate_Days 0（R0，Willy 11/19）與 0825 報表（11/16）同一段資料逐筆相同。"""
    fx = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_R0_to20261119_trades.csv"
    st = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_R0_to20261119_settings.txt"
    base = ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv"
    vec = [ln.split("\t", 1)[1] for ln in st.read_text(encoding="utf-8").splitlines() if ln.startswith("策略參數")][0]
    p = s16.params_from_mc_vector(s16.PLA_2611191, vec)
    assert {k for k in p if p[k] != s16.pla_params(s16.PLA_2611191)[k]} == {"TOD_Gate_Days"} and p["TOD_Gate_Days"] == 0
    key = lambda m: (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19], round(float(m["net_ntd"])))
    r0 = [key(m) for m in csv.DictReader(fx.open(encoding="utf-8")) if m["exit_dt"] <= "2026-11-16 12:20"]
    assert r0 == [key(m) for m in csv.DictReader(base.open(encoding="utf-8"))] and len(r0) == 192


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_candidate_v1281_default_matches_mc_v1281c_trade_by_trade():
    """v1.28.1 預設（B）對 Willy 11/19 的 MC v1281c 報表：平倉 ≤ 2026-11-16 12:20 的 139 筆逐筆相同、4,006,400。
    MC 的同時段歷史比 2019-12-31 早就開始累積，所以 Python 資料從 2019-01-01 起（暖機足夠）。
    這一題抓到百分位索引的浮點問題：90×0.70＝62.999…，MC 取 63（2021-05-25 12:15 那筆）。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_trades.csv"
    st = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_settings.txt"
    vec = [ln.split("\t", 1)[1] for ln in st.read_text(encoding="utf-8").splitlines() if ln.startswith("策略參數")][0]
    p = s16.params_from_mc_vector(s16.PLA_2611191, vec)
    assert p == s16.pla_params(s16.PLA_2611191)  # MC 跑的就是檔案預設值（B）
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 1, 1), datetime(2026, 11, 16, 12, 20))
    res = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611191))
    mc = [m for m in csv.DictReader(fx.open(encoding="utf-8")) if m["exit_dt"] <= "2026-11-16 12:20"]
    assert len(res.trades) == len(mc) == 139
    for t, m in zip(res.trades, mc):
        assert (t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.exit_dt.strftime("%Y-%m-%d %H:%M"),
                t.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(t.net_ntd - float(m["net_ntd"])) < 1
    assert round(sum(t.net_ntd for t in res.trades)) == 4006400


CRASH_KEYS = {"Crash30_Pct", "Crash60_Pct", "DayTrend_Pct", "CrashDay_Pct", "ContRe_On", "Crash_Struct"}


def test_candidate_v1290_is_v1281_plus_crash_inputs():
    """v1.29.0 候選（大殺盤，Build 2611192）＝ v1.28.1 ＋ 6 個新 input；其餘 input、假日表完全相同；ASCII、.txt 相同。"""
    a, b = s16.pla_params(s16.PLA_2611191), s16.pla_params(s16.PLA_2611192)
    assert set(b) - set(a) == CRASH_KEYS and not set(a) - set(b)
    assert {k: v for k, v in b.items() if k not in CRASH_KEYS | {"Build_ID"}} == \
           {k: v for k, v in a.items() if k != "Build_ID"}
    assert b["Build_ID"] == 2611192
    assert s16.holiday_tail(s16.PLA_2611192) == s16.holiday_tail(s16.PLA_2611191)
    raw = s16.PLA_2611192.read_bytes()
    assert all(c < 128 for c in raw) and raw == s16.PLA_2611192.with_suffix(".txt").read_bytes()


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-16）")
def test_candidate_v1290_crash_off_matches_mc_v1281c():
    """v1.29.0 六個新 input 全 0 → 和 MC v1281c 報表逐筆相同（139 筆、4,006,400）：引擎新增的路徑關閉時不影響原策略。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_trades.csv"
    p = s16.pla_params(s16.PLA_2611192)
    p.update({k: 0.0 for k in CRASH_KEYS})
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 1, 1), datetime(2026, 11, 16, 12, 20))
    res = s16.run(bars, p, s16.holiday_tail(s16.PLA_2611192))
    mc = [m for m in csv.DictReader(fx.open(encoding="utf-8")) if m["exit_dt"] <= "2026-11-16 12:20"]
    assert len(res.trades) == len(mc) == 139
    for t, m in zip(res.trades, mc):
        assert (t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.exit_dt.strftime("%Y-%m-%d %H:%M"),
                t.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(t.net_ntd - float(m["net_ntd"])) < 1
