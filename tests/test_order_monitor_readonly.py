"""下單回報監控：唯讀保證。tools/order_monitor 底下任何程式都不得呼叫凱基下單、刪改單、出金方法。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tools" / "order_monitor"

# TradeCom 下單／刪改單／出金類方法（依凱基《TradeCom 說明文件-期權》）
FORBIDDEN = re.compile(
    r"\b(Order|OrderNew|SendOrder|FutureNew|OptionNew|OrderCancel|OrderReplace|ChangeOrder|"
    r"CancelOrder|ReplaceOrder|DeleteOrder|OrderChange|OrderDelete|ApplyWithdraw|Withdraw)\s*\(",
    re.IGNORECASE,
)
# 註解裡提到的字不算
COMMENT = re.compile(r"(#.*$)|(//.*$)", re.MULTILINE)


def _sources():
    return [p for p in ROOT.rglob("*") if p.suffix.lower() in {".ps1", ".py", ".cs", ".bat"}]


def test_sources_exist():
    assert _sources(), "tools/order_monitor 沒有程式"


def test_no_order_methods():
    bad = []
    for p in _sources():
        code = COMMENT.sub("", p.read_text(encoding="utf-8-sig"))
        for m in FORBIDDEN.finditer(code):
            bad.append(f"{p.name}: {m.group(0)}")
    assert not bad, f"發現下單類呼叫: {bad}"


def test_no_hardcoded_secrets():
    for p in _sources():
        code = p.read_text(encoding="utf-8-sig")
        assert not re.search(r"(?<!\d)761\d{4}(?!\d)", code), f"{p.name} 含帳號"
        assert not re.search(r"\b[A-Z][12]\d{8}\b", code), f"{p.name} 含身分證"


def test_detector_catches_order_call(tmp_path):
    assert FORBIDDEN.search('$com.FutureNew($a)')
    assert FORBIDDEN.search('tfcom.Order(x)')
    assert not FORBIDDEN.search('$com.LoginDirect(h,p,i)')
    assert not FORBIDDEN.search('$com.RetrivePositionDetail(a)')
