"""結算日遞延表（2026-11-20，Willy「把 2027-09-16 結算日缺口先修掉。包含最新的L6策略。」）

L1–L5 V0.1.0 ＝ 上架版 V1.1.0 ＋ 兩行遞延表；L6 V0.1.0 ＝ L6 V1.0.0 ＋ 同樣兩行（tests/test_l6_v010_settle.py）。
獨立檢查，不讀產生腳本：
1. 去註解後逐詞比對 V1.1.0：只多兩句 `if Date = ... then v_Settlement_Day = ...;`，緊接在第三個週三規則之後
2. 六支的遞延表 ＝ data/taifex_market_closures.json 從 2027 年起、到檔案 Registry_Valid_Until 那一年，所有
   「第 3 個週三休市」→ 下一個營業日。上架檔另有提醒閘：下一個順延結算日前 45 天起（2027-08-02），
   上架檔沒有遞延表就失敗（verify.bat 擋推送）；以後換 2028 年假日表時，同一道閘會要求 2028 年的遞延日
3. Python 行事曆：2027-09-16 是結算日、2027-09-15 不是；2027 年以前每一天的判定和舊規則相同（歷史交易不變）
4. ASCII、.txt ＝ .pla、行尾與底版相同、標頭版號、G1 規範全過
"""
import datetime as dt
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verify_static", ROOT / "tools" / "verify_static.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

R = ROOT / "strategies/research"
NAMES = ["L1_TrendLong", "L2_TrendShort", "L3_ConsolidationLong", "L4_ConsolidationShort", "L5_BreakoutLong"]
L6_DEV = R / "L6_MACrossShort/L6_v0.1.0/L6_MACrossShort_v0.1.0.pla"
SKIP_RE = re.compile(r"if Date = (\d{7}) then v_Settlement_Day = False;")
ADD_RE = re.compile(r"if Date = (\d{7}) then v_Settlement_Day = True;")
TOKEN = re.compile(r'"[^"]*"|[A-Za-z_]\w*|\d+\.?\d*|\.\d+|<>|<=|>=|\S')
RULE_END = ["DayOfMonth", "(", "Date", ")", "<=", "21", ")", ";"]


def pla(name, ver):
    code = name.split("_")[0]
    return R / name / f"{code}_{ver}" / f"{name}_{ver}.pla"


def tokens(path):
    return TOKEN.findall(vs.strip_comments(path.read_bytes().decode("ascii")))


def mc(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def expected_table(last=None):
    """(skip, add)：closures 檔裡 2027 年起（到 last 年）每個月的第 3 個週三若休市 → 順延到下一個非週末、非休市日。"""
    closed = {x["date"] for x in json.loads((ROOT / "data/taifex_market_closures.json")
                                            .read_text(encoding="utf-8"))["closed_weekdays"]}
    last = last or max(int(d[:4]) for d in closed)
    skip, add = set(), set()
    for y in range(2027, last + 1):
        for m in range(1, 13):
            wed = next(dt.date(y, m, k) for k in range(15, 22) if dt.date(y, m, k).weekday() == 2)
            if str(wed) in closed:
                nxt = wed + dt.timedelta(1)
                while nxt.weekday() > 4 or str(nxt) in closed:
                    nxt += dt.timedelta(1)
                skip.add(mc(wed)); add.add(mc(nxt))
    return skip, add


def table_of(path):
    code = vs.strip_comments(path.read_bytes().decode("ascii"))
    return {int(x) for x in SKIP_RE.findall(code)}, {int(x) for x in ADD_RE.findall(code)}


def registry_year(path):
    """檔案 Registry_Valid_Until 預設值的西元年：遞延表只需要涵蓋到這一年。"""
    v = vs.inputs_block(vs.strip_comments(path.read_bytes().decode("ascii")))["Registry_Valid_Until"]
    return int(float(v)) // 10000 + 1900


def test_expected_table_is_2027_09_16_only():
    assert expected_table(2027) == ({1270915}, {1270916})


@pytest.mark.parametrize("name", NAMES)
def test_code_is_v110_plus_two_statements_after_the_rule(name):
    new, old = tokens(pla(name, "v0.1.0")), tokens(pla(name, "v1.1.0"))
    skip, add = expected_table(registry_year(pla(name, "v0.1.0")))
    ins = []
    for w, n in zip(sorted(skip), sorted(add)):
        ins += ["if", "Date", "=", str(w), "then", "v_Settlement_Day", "=", "False", ";",
                "if", "Date", "=", str(n), "then", "v_Settlement_Day", "=", "True", ";"]
    at = [i for i in range(len(new)) if new[i:i + len(ins)] == ins]
    assert len(at) == 1, f"{name}: table found {len(at)} times"
    i = at[0]
    assert new[i - len(RULE_END):i] == RULE_END, f"{name}: table is not right after the 3rd-Wednesday rule"
    assert new[:i] + new[i + len(ins):] == old, f"{name}: code differs from V1.1.0 beyond the table"


@pytest.mark.parametrize("path", [pla(n, "v0.1.0") for n in NAMES] + [L6_DEV], ids=NAMES + ["L6_MACrossShort"])
def test_table_equals_closures_registry(path):
    if not path.exists():
        pytest.skip(f"{path.name} not built")
    assert registry_year(path) == 2027
    assert table_of(path) == expected_table(registry_year(path))


LIVE = ["L1_TrendLong", "L2_TrendShort", "L3_ConsolidationLong", "L4_ConsolidationShort", "L5_BreakoutLong",
        "L6_MACrossShort"]


@pytest.mark.parametrize("name", LIVE)
def test_live_file_has_the_table_before_the_next_deferred_settlement(name):
    """提醒閘：下一個順延結算日前 45 天起，上架檔必須已有遞延表（第一個是 2027-09-16 → 2027-08-02 起擋推送）。"""
    p = ROOT / "strategies/live" / name / f"{name}.pla"
    skip, add = expected_table(registry_year(p))
    if not add:
        pytest.skip("no deferred settlement inside the registry")
    first = min(add)
    deadline = dt.date(first // 10000 + 1900, first // 100 % 100, first % 100) - dt.timedelta(days=45)
    if dt.date.today() < deadline:
        pytest.skip(f"settlement deferral table due in strategies/live by {deadline} (switch to the V0.1.0 code)")
    got = table_of(p)
    assert got[1] >= add and got[0] >= skip, f"{name}: live file misses the settlement deferral table {sorted(add)}"


@pytest.mark.parametrize("name", NAMES)
def test_file_hygiene_and_header(name):
    p = pla(name, "v0.1.0")
    b, base = p.read_bytes(), pla(name, "v1.1.0").read_bytes()
    assert max(b) < 128
    assert p.with_suffix(".txt").read_bytes() == b
    assert (b"\r\n" in b) == (b"\r\n" in base)
    head = b.decode("ascii").split("}", 1)[0]
    assert "-  V0.1.0 DEV  (2026-11-20; logic = " in head and "Known gap" not in head
    assert "2027-09-15 -> 2027-09-16" in head
    bad = [r for r in vs.check(p) if not r[1]]
    assert not bad, bad


def test_python_calendar_follows_the_table():
    from txfcore.tradecal import settlement as st
    from txfcore.tradecal.gates import evaluate, static_settlement_rule
    assert (set(st.SETTLE_SKIP), set(st.SETTLE_ADD)) == expected_table(2027)
    assert evaluate(1270916, 1230).settlement_day is True             # 資料範圍外：.pla 規則＋遞延表
    assert evaluate(1270915, 1230).settlement_day is False
    assert static_settlement_rule(1270916) is True                    # mc12 模式 ＝ V0.1.0 .pla
    assert evaluate(1270915, 1230, use_data_settlement=False).settlement_day is False
    d = dt.date(2019, 1, 1)
    while d.year < 2027:                                              # 2027 年以前：與舊規則逐日相同
        assert st.pla_rule(mc(d)) == st.static_rule(mc(d)), d
        d += dt.timedelta(1)
