"""L2 v5.12 研究版（2026-11-16：v5.11＋三項極端日出場）。

快測：.pla 的 input 名稱與預設值；三項全關時，出場段落和 v5.11 只差新增的三張單。
慢測（需 TXF1_MIN_DATA）：Python 三項全關 ＝ v5.11 逐筆相同（R0 回歸）。
"""
import os, re, subprocess, sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PLA = ROOT / "strategies/research/L2_TrendShort/L2_v5.12/L2_TrendShort_v5.12.pla"
OLD = ROOT / "strategies/research/L2_TrendShort/L2_v5.11/L2_TrendShort_v5.11.pla"
NEW_INPUTS = {"SP_Tier_Pts": "2500", "SP_Tier_Keep": "70", "LimitDn_On": "1",
              "LimitDn_Pct": "9.8", "Reb_On": "0", "Reb_Pct": "8.0"}   # Reb_On 0：Willy 11/16 13:34


def _inputs(path):
    body = path.read_text(encoding="ascii")
    block = body[body.index("Inputs:"):body.index("Variables:")]
    block = re.sub(r"\{.*?\}", "", block, flags=re.S)
    return dict(re.findall(r"(\w+)\s*\(\s*([^)]+?)\s*\)", block))


def test_new_inputs_and_old_ones_unchanged():
    new, old = _inputs(PLA), _inputs(OLD)
    assert {k: new[k] for k in NEW_INPUTS} == NEW_INPUTS
    assert {k: v for k, v in new.items() if k not in NEW_INPUTS} == old


def test_only_three_new_order_names():
    names = lambda p: set(re.findall(r'BuyToCover\(\s*"(\w+)"', p.read_text(encoding="ascii")))
    assert names(PLA) - names(OLD) == {"TS_SPTier", "TS_LimitDn", "TS_Rebound"}
    assert names(OLD) <= names(PLA)


def test_no_entry_block():
    body = PLA.read_text(encoding="ascii")
    assert "Reb_Block_Entry" not in body and "Exit_Mode" not in body   # Willy 11/16：當天不進場關掉；盤中觸價取最緊不採用


@pytest.mark.skipif(not os.environ.get("TXF1_MIN_DATA"), reason="需要 1 分 K（TXF1_MIN_DATA）")
def test_r0_all_off_equals_v511():
    out = subprocess.run([sys.executable, str(ROOT / "scripts/research/l2_v5_12_20261116/predict.py"),
                          os.environ["TXF1_MIN_DATA"], "260924"], capture_output=True, text=True, check=True).stdout
    assert "R0 三項全關 == v5.11 逐筆： True 筆數 96" in out
