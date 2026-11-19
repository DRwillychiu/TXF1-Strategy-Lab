"""2027 假日登錄表候選版（2026-11-19）：每個候選檔 ＝ 底版 ＋ 2027 假日 11 列 ＋ Registry_Valid_Until 1271231。

這是獨立檢查，不讀產生腳本（scripts/research/registry_2027_20261119/build_candidates.py）：
1. 從期交所 116 年休市日（台期交字第1150003597號，2026-11-10）用 2026 同一條規則推 2027 尾段日期
   （尾段 ＝ 休市前最後交易日 ＋ 1 曆日 ＝ 夜盤過午夜 K 棒的日期），必須等於檔案新增的 11 列。
2. 去掉註解後逐句比對底版：只差 Registry_Valid_Until 預設值與緊接在 [63] 後面的 11 句賦值。
3. ASCII、.txt ＝ .pla、標頭版號 ＝ 資料夾 ＝ 檔名、陣列 80 格且迴圈掃到 80、G1 規範全過。
4. L3–L5 的底版 ＝ strategies/live 上架檔（逐位元組；換版後 ＝ V1.1.0）。11/19 Willy：實盤 L1 V3.8、L2 v5.12，
   第二次上架測試加 2027 假日表後五支版號一律 V1.1.0（第一次實戰測試 ＝ V1.0）。
5. 2027 第三個星期三落在休市日的只有 9/15（結算日規則的已知缺口，候選版沒有改，見報告）。
"""
import datetime as dt
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verify_static", ROOT / "tools" / "verify_static.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

R = "strategies/research"
SNAP = "strategies/live_machine_snapshot/20261119"      # Willy 11/19 從上架機匯出的五支原碼（原始證據）
# 候選檔、底版、上架檔（None ＝ L1，實盤版本待確認）、標頭載入名
CANDIDATES = [
    # 11/19 Willy：實盤 L1 V3.8、L2 v5.12（第二次上架測試）；加 2027 假日表後五支版號一律 V1.1.0。
    # L1、L2 的 repo 上架檔從沒同步成實盤版（L1 是 V3.1 內容、L2 是 v5.11），所以不比對上架檔（None）。
    (f"{R}/L1_TrendLong/L1_v1.1.0/L1_TrendLong_v1.1.0.pla",
     f"{R}/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla", None, "WILLY_ATR_LONG_60M"),
    (f"{R}/L2_TrendShort/L2_v1.1.0/L2_TrendShort_v1.1.0.pla",          # 底版 ＝ 上架機原碼（Reb_On 預設 1）
     f"{SNAP}/L2_TrendShort_live.txt", None, "Trendbearish_V1"),
    (f"{R}/L3_ConsolidationLong/L3_v1.1.0/L3_ConsolidationLong_v1.1.0.pla",
     f"{R}/L3_ConsolidationLong/L3_v18.4/L3_ConsolidationLong_v18.4.pla",
     "strategies/live/L3_ConsolidationLong/L3_ConsolidationLong.pla", "STRATEGY_WILLY_LONG_C"),
    (f"{R}/L4_ConsolidationShort/L4_v1.1.0/L4_ConsolidationShort_v1.1.0.pla",
     f"{R}/L4_ConsolidationShort/L4_v14.10/L4_ConsolidationShort_v14.10.pla",
     "strategies/live/L4_ConsolidationShort/L4_ConsolidationShort.pla", "STRATEGY_WILLY_SHORT_CTEST2"),
    (f"{R}/L5_BreakoutLong/L5_v1.1.0/L5_BreakoutLong_v1.1.0.pla",
     f"{R}/L5_BreakoutLong/L5_v19.20/L5_BreakoutLong_v19.20.pla",
     "strategies/live/L5_BreakoutLong/L5_BreakoutLong.pla", "STRATEGY_WILLY_LONG_BREAKOUT_C"),
]
IDS = [Path(c).stem for c, *_ in CANDIDATES]
# 和上架機原碼相比，Willy 另外決定改的預設值：(input, 上架機原碼, V1.1.0)
INPUT_CHANGES = {"L2_TrendShort": [("Reb_On", "1", "0")]}     # 11/19 Willy「關掉」（＝ 11/16 13:34 決定）


# ---- 期交所 116 年休市日（台期交字第1150003597號）----
def _d(m, d):
    return dt.date(2027, m, d)


CLOSED_2027 = ({_d(1, 1)} | {_d(2, d) for d in range(2, 11)} |
               {_d(3, 1), _d(4, 5), _d(4, 6), _d(4, 30), _d(6, 9), _d(9, 15), _d(9, 28),
                _d(10, 11), _d(10, 25), _d(12, 24), _d(12, 31)})
CLOSED = CLOSED_2027 | {dt.date(2026, 12, 25)}          # 2026 年最後一次休市（115 年曆）
NEW_2027 = {1270202, 1270227, 1270403, 1270430, 1270609, 1270915, 1270928,
            1271009, 1271023, 1271224, 1271231}


def mc(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def trading(d):
    return d.weekday() < 5 and d not in CLOSED


def derived_tails():
    out = set()
    for d in sorted(CLOSED_2027):
        if d.weekday() >= 5:
            continue
        t = d - dt.timedelta(days=1)
        while not trading(t):
            t -= dt.timedelta(days=1)
        out.add(mc(t + dt.timedelta(days=1)))
    return out


def test_rule_on_116_calendar_gives_the_11_new_tails():
    assert derived_tails() == NEW_2027 | {1270101}        # 1270101 已在 2026 表裡（[63]）


def test_2027_third_wednesday_on_a_holiday_is_only_sep15():
    third_wed = [_d(m, day) for m in range(1, 13) for day in range(15, 22) if _d(m, day).weekday() == 2]
    assert len(third_wed) == 12
    assert [d for d in third_wed if d in CLOSED_2027] == [_d(9, 15)]
    nxt = _d(9, 16)
    assert trading(nxt)                                    # 結算順延到 9/16（星期四），「第三個星期三」規則抓不到


# ---- 候選檔逐句比對 ----
ROW_RE = re.compile(r"^Holiday_Tail\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)$")
REG_RE = re.compile(r"Registry_Valid_Until\s*\(\s*(\d+)\s*\)")


def stmts(path):
    code = vs.strip_comments(path.read_bytes().decode("ascii"))
    return [re.sub(r"\s+", " ", s).strip() for s in code.split(";") if s.strip()]


@pytest.mark.parametrize("cand,base,live,load", CANDIDATES, ids=IDS)
def test_code_differs_from_base_only_in_registry(cand, base, live, load):
    new, old = stmts(ROOT / cand), stmts(ROOT / base)
    pos = {i: s for i, s in enumerate(new) if (m := ROW_RE.match(s)) and int(m.group(1)) >= 64}
    added = {int(ROW_RE.match(s).group(1)): int(ROW_RE.match(s).group(2)) for s in pos.values()}
    assert added == dict(zip(range(64, 75), sorted(NEW_2027)))
    first = min(pos)
    assert sorted(pos) == list(range(first, first + 11)), "11 列要連續"
    assert ROW_RE.match(new[first - 1]).groups() == ("63", "1270101"), "要緊接在 [63] 後面（同一個初始化區塊）"
    rest = "\n".join(s for i, s in enumerate(new) if i not in pos)
    base_text = "\n".join(old)
    assert REG_RE.findall(base_text) == ["1270101"]
    assert REG_RE.findall(rest) == ["1271231"]
    # 唯一允許的其他差異：Willy 決定的預設值（L2 回升保本關，11/19「關掉」）
    for name, a, b in INPUT_CHANGES.get(cand.split("/")[2], []):
        pat = re.compile(rf"\b{name} \( ([^)]+) \)")
        assert pat.findall(base_text) == [a] and pat.findall(rest) == [b], f"{name} 應由 {a} 改成 {b}"
        base_text = pat.sub(f"{name} ( {b} )", base_text)
    assert REG_RE.sub("R", rest) == REG_RE.sub("R", base_text), "除了登錄表（與上面列的預設值），程式碼要逐句相同"


@pytest.mark.parametrize("cand,base,live,load", CANDIDATES, ids=IDS)
def test_file_hygiene(cand, base, live, load):
    p = ROOT / cand
    raw = p.read_bytes()
    assert max(raw) < 128, "MC 只吃 ASCII"
    assert raw == p.with_suffix(".txt").read_bytes(), ".txt 閱讀版必須與 .pla 相同"
    braw = (ROOT / base).read_bytes()
    assert (b"\r\n" in raw) == (b"\r\n" in braw), "換行格式跟底版一樣"
    ver = p.parent.name.split("_", 1)[1]                   # e.g. v1.1.0
    assert p.stem.endswith("_" + ver)
    head = raw.decode("ascii").splitlines()[:12]
    assert any(re.search(r"(?<![\w.])[vV]" + re.escape(ver[1:]) + r"(?![\w.])", h) for h in head), "標頭版號 ＝ 資料夾"
    assert re.search(r"MC\s+Load\s+Name\s*:\s*" + re.escape(load) + r"(\s|$)", "\n".join(head))
    code = vs.strip_comments(raw.decode("ascii"))
    assert re.search(r"Holiday_Tail\s*\[\s*80\s*\]\s*\(\s*0\s*\)", code), "陣列 80 格"
    assert re.search(r"for\s+h?idx\s*=\s*1\s+to\s+80\b", code, re.I), "迴圈要掃到 80（74 筆才看得到）"
    assert all(ok for _, ok, _ in vs.check(p)), [r for r in vs.check(p) if not r[1]]


@pytest.mark.parametrize("cand,base,live,load", [c for c in CANDIDATES if c[2]], ids=[i for i, c in zip(IDS, CANDIDATES) if c[2]])
def test_l2_to_l5_base_is_the_live_file(cand, base, live, load):
    # 換版前：上架檔 ＝ 底版；switch_live_registry_2027.py 換完後：上架檔 ＝ 候選檔
    assert (ROOT / live).read_bytes() in ((ROOT / base).read_bytes(), (ROOT / cand).read_bytes())


@pytest.mark.parametrize("cand,base,live,load", CANDIDATES, ids=IDS)
def test_base_is_the_live_machine_code(cand, base, live, load):
    """V1.1.0 ＝ 上架機正在跑的原碼 ＋ 假日表：底版和 11/19 上架機匯出檔逐行相同（換行、行尾空白不計）。"""
    name = cand.split("/")[2]                              # e.g. L2_TrendShort
    snap = (ROOT / SNAP / f"{name}_live.txt").read_bytes().decode("ascii")
    norm = lambda s: [l.rstrip() for l in s.replace("\r\n", "\n").rstrip("\n").split("\n")]
    assert norm((ROOT / base).read_bytes().decode("ascii")) == norm(snap)


def test_live_machine_export_holds_the_five_snapshots():
    """匯出檔（UTF-16 XML、程式 base64）解出來 ＝ 存下的五個 .txt，證明 .txt 沒被改過。"""
    import base64
    t = (ROOT / SNAP / "live_export_20261119.pla").read_bytes().decode("utf-16")
    codes = [base64.b64decode(c) for c in re.findall(r'<NodeText Encoded="1">(.*?)</NodeText>', t, re.S)]
    assert len(codes) == 5
    files = sorted((ROOT / SNAP).glob("L*_live.txt"))
    assert sorted(codes) == sorted(f.read_bytes() for f in files)


# ---- 三份假日表要一致：期交所年曆（data/taifex_market_closures.json）＝ Python ＝ 五支上架候選 .pla ----
# 11/19 Willy 指定的上架版：L1 V3.8、L2 v5.12、L3 v18.4、L4 v14.10、L5 v19.20 → 五支 V1.1.0
DEPLOY = [c for c, *_ in CANDIDATES]


def _calendar_module():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("taifex_calendar", ROOT / "scripts" / "taifex_calendar.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_closures_json_2027_equals_taifex_116_calendar():
    tc = _calendar_module()
    doc, closed = tc.load_source()
    assert {d for d in closed if d.year == 2027} == {d for d in CLOSED_2027 if d.weekday() < 5}
    lo, hi = tc.coverage(doc)
    assert hi == dt.date(2027, 12, 31)
    tails = {tc.to_mc(t["tail"]) for t in tc.holiday_tails(closed, lo, hi)}
    assert {t for t in tails if t >= 1270101} == NEW_2027 | {1270101}


def test_python_registry_equals_deploy_candidates():
    from txfcore.strategies.base import StrategyConfig
    from txfcore.tradecal.registry import HOLIDAY_TAIL, REGISTRY_VALID_UNTIL
    assert HOLIDAY_TAIL[-11:] == tuple(sorted(NEW_2027))
    assert REGISTRY_VALID_UNTIL == 1271231
    assert StrategyConfig(name="x").registry_valid_until == REGISTRY_VALID_UNTIL
    assert len(DEPLOY) == 5
    for c in DEPLOY:
        code = vs.strip_comments((ROOT / c).read_bytes().decode("ascii"))
        rows = {int(i): int(v) for i, v in re.findall(r"Holiday_Tail\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)", code)}
        assert [rows[i] for i in sorted(rows)] == list(HOLIDAY_TAIL), c
        assert sorted(rows) == list(range(1, 75)), c
        assert REG_RE.findall(code) == [str(REGISTRY_VALID_UNTIL)], c
