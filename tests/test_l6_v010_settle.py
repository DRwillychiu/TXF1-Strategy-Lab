"""L6_MACrossShort_v0.1.0（開發版）＝v1.0.0＋結算日遞延表（2027-09-15 中秋休市 → 結算順延 2027-09-16）。"""
import csv
import math
import os
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from txfcore.strategies import s16_s_v1_26 as s16

ROOT = Path(__file__).resolve().parents[1]
V010_DIR = ROOT / "strategies/research/L6_MACrossShort/L6_v0.1.0"


def test_v010_is_v100_plus_settle_table_only():
    """去註解後：只差 Build_ID 與兩行遞延表；純 ASCII、CRLF、.txt＝.pla；假日表與參數不變。"""
    pla, txt, old = (s16.PLA_L6_V010.read_bytes(), (V010_DIR / "L6_MACrossShort_v0.1.0.txt").read_bytes(),
                     s16.PLA_L6_V100.read_bytes())
    assert txt == pla
    assert all(c < 128 for c in pla) and pla.count(b"\r\n") == pla.count(b"\n")
    strip = lambda b: re.sub(r"\{[^}]*\}", "", b.decode("ascii"))
    table = ("\r\nif Date = 1270915 then v_Settlement_Day = False;  \r\n"
             "if Date = 1270916 then v_Settlement_Day = True;   \r\n")
    new = strip(pla).replace("2611201", "2611193")
    assert new.count(table) == 1 and new.replace(table, "") == strip(old)
    p, q = s16.pla_params(s16.PLA_L6_V010), s16.pla_params(s16.PLA_L6_V100)
    assert p["Build_ID"] == 2611201 and {k: v for k, v in p.items() if k != "Build_ID"} == \
        {k: v for k, v in q.items() if k != "Build_ID"}
    assert s16.holiday_tail(s16.PLA_L6_V010) == s16.holiday_tail(s16.PLA_L6_V100)
    assert s16.settle_shift(s16.PLA_L6_V010) == ({1270915}, {1270916})
    assert s16.settle_shift(s16.PLA_L6_V100) == (set(), set())


def test_settle_table_equals_closure_registry_2027():
    """遞延表＝data/taifex_market_closures.json 算出的 2027 年第 3 週三休市月份。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "b", ROOT / "scripts/research/s16_streak_20261118/build_l6_v010.py")
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    d = b.settle_deferrals(2027)
    assert d == [(date(2027, 9, 15), date(2027, 9, 16))]
    assert s16.settle_shift(s16.PLA_L6_V010) == ({b.mc(w) for w, _ in d}, {b.mc(n) for _, n in d})


def _bars_2027_09():
    """合成 5 分 K：2027-08-02 起緩漲，09-14 09:30 一根急殺後續跌（死亡交叉放空），09-15 休市，跑到 09-16 收盤。"""
    out, d, px, k = [], date(2027, 8, 2), 30000.0, 0
    down = datetime(2027, 9, 14, 9, 30)
    while d <= date(2027, 9, 16):
        if d.weekday() < 5 and d != date(2027, 9, 15):
            t = datetime.combine(d, time(8, 50))
            while t.time() <= time(13, 45):
                k += 1
                step = 2.0 if t < down else (-400.0 if t == down else -40.0)
                nxt = px + step + 3 * math.sin(k)
                out.append(s16.Bar5(t, px, max(px, nxt) + 2, min(px, nxt) - 2, nxt, 100))
                px = nxt
                t += timedelta(minutes=5)
        d += timedelta(1)
    return out


def test_20270916_triggers_settlement_flat():
    """空單從 09-14 抱過 09-15 休市：v0.1.0 在 09-16 12:30 後以 SX_MA_Settlement 平倉；v1.0.0 不會（已知缺口）。
    為了讓部位留到結算，只關掉會先出場的時間／保本／結構出場與門檻（結算判定本身不動）。"""
    bars = _bars_2027_09()
    over = dict(TOD_Gate_Days=0, MaxHoldingBars=9999, MaxHold_Pct=99, QuickStop_On=0, Struct_On=0,
                BE_On=0, Gap_Filter_On=0)
    got = {}
    for pla in (s16.PLA_L6_V100, s16.PLA_L6_V010):
        p = s16.pla_params(pla); p.update(over)
        got[pla] = s16.run(bars, p, s16.holiday_tail(pla), settle_shift=s16.settle_shift(pla)).trades
    new = got[s16.PLA_L6_V010]
    assert [(t.entry_dt, t.exit_dt, t.exit_label) for t in new] == \
        [(datetime(2027, 9, 14, 9, 35), datetime(2027, 9, 16, 12, 35), "SX_MA_Settlement")]
    assert not any(t.exit_label == "SX_MA_Settlement" for t in got[s16.PLA_L6_V100])


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA，到 2026-11-19）")
def test_v010_history_equals_mc_v1281c_to_20261119():
    """2020 至今：v0.1.0（含遞延表）對 MC v1281c 報表逐筆相同，144 筆＝v1.0.0。"""
    from txfcore.quotes.history import MC12MinuteSource
    fx = ROOT / "tests/fixtures/mc_S16_v1.28.1_b2611191_to20261119_trades.csv"
    bars = s16.aggregate_5m(MC12MinuteSource(os.environ["TXF1_MIN_DATA"], validate=False).stream(),
                            datetime(2019, 1, 1), datetime(2026, 11, 19, 13, 45))
    pla = s16.PLA_L6_V010
    res = s16.run(bars, s16.pla_params(pla), s16.holiday_tail(pla), settle_shift=s16.settle_shift(pla))
    old = s16.run(bars, s16.pla_params(s16.PLA_L6_V100), s16.holiday_tail(s16.PLA_L6_V100))
    key = lambda t: (t.entry_dt, t.entry_label, t.exit_dt, t.exit_label, round(t.net_ntd, 6))
    assert [key(t) for t in res.trades] == [key(t) for t in old.trades]
    mc = list(csv.DictReader(fx.open(encoding="utf-8")))
    got = [t for t in res.trades if t.entry_dt.strftime("%Y-%m-%d %H:%M") >= mc[0]["entry_dt"]]
    assert len(got) == len(mc) == 144
    for t, m in zip(got, mc):
        assert (t.entry_dt.strftime("%Y-%m-%d %H:%M"), t.entry_label, t.exit_dt.strftime("%Y-%m-%d %H:%M"),
                t.exit_label[:19]) == (m["entry_dt"], m["entry_label"], m["exit_dt"], m["exit_label"][:19])
        assert abs(t.net_ntd - float(m["net_ntd"])) < 1
