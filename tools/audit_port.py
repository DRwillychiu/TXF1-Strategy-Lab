#!/usr/bin/env python3
"""移植稽核 —— 直接讀 `.pla`，逐項對照 Python 模組。

**不是我說有沒有漏，是機器比。**

檢查四項：

    1. inputs      每個 input 的名稱與預設值，是否都出現在 DEFAULT_PARAMS
    2. 訂單標籤     每個 Buy("...") / Sell("...") 的標籤，是否都出現在 Python
    3. from Entry   綁定數量是否一致（L5 應為 28，其餘四支應為 0）
    4. 關鍵運算子   Crosses Over / MaxList / MinList / SetStopContract 等

用法：
    python tools/audit_port.py

輸出 `✗` 的都是**確定的落差**，不是推測。
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# .pla 路徑 -> Python 模組
PAIRS = (
    ("L1", "strategies/research/L1_TrendLong/L1_v3.2/L1_TrendLong_v3.2.pla",
     "txfcore/strategies/l1_trendlong.py"),
    ("L2", "strategies/research/L2_TrendShort/L2_v5.4/L2_TrendShort_v5.4.pla",
     "txfcore/strategies/l2_trendshort.py"),
    ("L3", "strategies/research/L3_ConsolidationLong/L3_v15.1/"
           "L3_ConsolidationLong_v15.1.pla",
     "txfcore/strategies/l3_consollong.py"),
    ("L4", "strategies/research/L4_ConsolidationShort/L4_v14.7/"
           "L4_ConsolidationShort_v14.7.pla",
     "txfcore/strategies/l4_consolshort.py"),
    ("L5", "strategies/research/L5_BreakoutLong/L5_v19.9_R1/"
           "L5_BreakoutLong_v19.9_R1.pla",
     "txfcore/strategies/l5_breakoutlong.py"),
)

# 這些 input 屬於 MC 平台或視覺化，不需要移植
NOT_PORTED = {
    "Debug_Entry_Log",           # L5 的 Print 開關
    "Registry_Valid_Until",      # 在 StrategyConfig
    "Manual_Kill_Switch",        # 在 StrategyConfig（mc_manual_kill_switch）
    "Holiday_Flat_Time",         # 在 StrategyConfig
    "Settlement_Flat_Time",      # 在 StrategyConfig
}

# 這些標籤在 Python 是別的形式
def strip_comments(src: str) -> str:
    r"""移除 PowerLanguage 註解，才不會誤抓註解裡的字串。

    兩種註解：`{ ... }` 區塊、`// ...` 行尾。

    **2026-09-07 修正**：原本用 `\{[^{}]*\}`，只要註解裡出現一個
    `{` 或 `}` 就整塊比對失敗，那塊註解就會被當成程式碼。
    實測後果：L5 的 `from Entry` 算出 30 處，實際下單只有 28 處，
    多的 2 處來自沒剝乾淨的註解。

    PowerLanguage 的區塊註解**不能巢狀**，所以非貪婪的 `\{.*?\}`
    才是正確語意——第一個 `}` 就結束。
    """
    src = re.sub(r"\{.*?\}", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return src


def parse_inputs(src: str) -> dict[str, str]:
    m = re.search(r"\binputs?\s*:(.*?);", src, flags=re.S | re.I)
    if not m:
        return {}
    body = m.group(1)
    out = {}
    for name, val in re.findall(r"(\w+)\s*\(\s*([^()]*?)\s*\)", body):
        out[name] = val.strip()
    return out


# **四個下單動詞，不是兩個。**
# 2026-09-07：原本只寫 Buy|Sell，於是 `SellShort (` 與 `BuyToCover (` 都不匹配
# （Sell 後面接的是 Short 不是空白或括號）。後果：**L2 與 L4 的標籤數是 0，
# 工具對兩支策略印了 ✓，而它連看都沒看。** 這正是「判官不判」的失敗模式。
ORDER_VERBS = r"(?:BuyToCover|SellShort|Buy|Sell)"


def parse_labels(src: str) -> set[str]:
    """四個下單動詞的標籤。`from Entry (...)` 的引用不算。"""
    out = set()
    for m in re.finditer(ORDER_VERBS + r"\s*\(\s*\"([^\"]+)\"\s*\)", src, re.I):
        out.add(m.group(1))
    return out


def parse_from_entry(src: str) -> int:
    return len(re.findall(r"from\s+Entry\s*\(", src, re.I))


OPERATORS = {
    "Crosses Over": r"Crosses\s+Over",
    "MaxList": r"\bMaxList\b",
    "MinList": r"\bMinList\b",
    "SetStopContract": r"\bSetStopContract\b",
    "SetStopLoss": r"\bSetStopLoss\b",
    "IntrabarOrderGeneration=true": r"IntrabarOrderGeneration\s*=\s*true",
    "IntraBarPersist": r"IntraBarPersist",
    "BarStatus": r"\bBarStatus\s*\(",
    "of Data2": r"of\s+Data2",
    "of Data3": r"of\s+Data3",
    "PositionProfit": r"\bPositionProfit\s*\(",
    "CurrentContracts": r"\bCurrentContracts\b",
    "MaxContracts": r"\bMaxContracts\b",
    "MinMove": r"\bMinMove\b",
}

PY_EQUIV = {
    "Crosses Over": ("crosses_over",),
    "MaxList": ("max(",),
    "MinList": ("min(",),
    "SetStopContract": ("per_contract=True",),
    "SetStopLoss": ("ProtectiveStop",),
    "IntrabarOrderGeneration=true": ("已知限制", "BarStatus"),
    "IntraBarPersist": ("IntraBarPersist", "收盤評估"),
    "BarStatus": ("BarStatus", "收盤評估"),
    "of Data2": ("d2.", "(d2,", "d2,"),
    "of Data3": ("d3.", "(d3,", "d3,"),
    "PositionProfit": ("prev_position_profit",),
    "CurrentContracts": ("current_contracts",),
    "MaxContracts": ("max_contracts",),
    "MinMove": ("tick_size",),
}


@dataclass
class Finding:
    key: str
    kind: str
    detail: str
    severity: str = "FAIL"


@dataclass
class Result:
    key: str
    pla: Path
    py: Path
    findings: list[Finding] = field(default_factory=list)
    n_inputs: int = 0
    n_labels: int = 0
    n_from_entry: int = 0

    def add(self, kind: str, detail: str, sev: str = "FAIL") -> None:
        self.findings.append(Finding(self.key, kind, detail, sev))


def audit_one(key: str, pla_rel: str, py_rel: str) -> Result | None:
    pla = ROOT / pla_rel
    py = ROOT / py_rel
    if not pla.exists():
        print(f"  ✗ {key}  找不到 .pla：{pla_rel}")
        return None
    if not py.exists():
        print(f"  ✗ {key}  找不到 Python：{py_rel}")
        return None

    raw = pla.read_text(encoding="utf-8", errors="replace")
    src = strip_comments(raw)
    pysrc = py.read_text(encoding="utf-8")
    r = Result(key, pla, py)

    # --- 1. inputs ---
    ins = parse_inputs(src)
    r.n_inputs = len(ins)
    for name, default in ins.items():
        if name in NOT_PORTED:
            continue
        if f'"{name}"' not in pysrc:
            r.add("input", f"{name}({default}) 未出現在 Python")
        else:
            # 預設值比對（只比數字）
            m = re.search(rf'"{re.escape(name)}"\s*:\s*([^,\n]+)', pysrc)
            if m:
                got = m.group(1).strip().rstrip(",")
                try:
                    if abs(float(got) - float(default)) > 1e-9:
                        r.add("input", f"{name} 預設值 .pla={default} Python={got}")
                except ValueError:
                    if default.lower() in ("true", "false"):
                        want = default.capitalize()
                        if want not in got:
                            r.add("input",
                                  f"{name} 預設值 .pla={default} Python={got}")

    # --- 2. 訂單標籤 ---
    labels = parse_labels(src)
    r.n_labels = len(labels)
    # **標籤數 0 一定是解析失敗，不是策略沒下單。**
    # 2026-09-07：正規式漏了 SellShort / BuyToCover，L2 與 L4 報 0 卻印 ✓。
    if not labels:
        r.add("parser", "解析出 0 個訂單標籤 —— 策略不可能不下單，是解析器壞了")
    for lb in sorted(labels):
        if f'"{lb}"' not in pysrc:
            r.add("label", f'訂單標籤 "{lb}" 未出現在 Python')

    # --- 3. from Entry ---
    r.n_from_entry = parse_from_entry(src)
    # 標頭若自報 grep 數，與實測比對。不符代表標頭過時或解析器有誤。
    claimed = re.search(r"grep count is (\d+)", raw)
    if claimed and int(claimed.group(1)) != r.n_from_entry:
        # 不符時把行號印出來，才看得出多的那幾處是不是在註解裡
        lines = [i + 1 for i, ln in enumerate(src.splitlines())
                 if re.search(r"from\s+Entry\s*\(", ln, re.I)]
        r.add("binding",
              f"標頭自報 from Entry {claimed.group(1)} 處，實測 {r.n_from_entry} 處"
              f"　行號 {lines}", "WARN")
    # Python 端用呼叫點計數（`_sell(..., leg, ...)`），不是宣告點
    py_fe = pysrc.count("from_entry=") + pysrc.count("BOT,") + pysrc.count("MID,")
    if r.n_from_entry > 0 and py_fe == 0:
        r.add("binding", f".pla 有 {r.n_from_entry} 處 from Entry，Python 零處")
    if r.n_from_entry == 0 and "from_entry=" in pysrc and key != "L5":
        r.add("binding", "Python 用了 from_entry 但 .pla 沒有綁定", "WARN")

    # --- 4. 關鍵運算子 ---
    for op, pat in OPERATORS.items():
        if re.search(pat, src, re.I):
            hints = PY_EQUIV.get(op, ())
            if not any(h in pysrc for h in hints):
                r.add("operator", f"{op} 在 .pla 有用，Python 找不到對應")
    return r


def main() -> int:
    print("=" * 74)
    print("移植稽核 —— .pla vs Python，逐項機器比對")
    print("=" * 74)
    results = []
    for key, pla_rel, py_rel in PAIRS:
        res = audit_one(key, pla_rel, py_rel)
        if res:
            results.append(res)

    total = 0
    for r in results:
        fails = [f for f in r.findings if f.severity == "FAIL"]
        warns = [f for f in r.findings if f.severity == "WARN"]
        total += len(fails)
        mark = "✓" if not fails else "✗"
        print(f"\n{mark} {r.key}   inputs {r.n_inputs}   訂單標籤 {r.n_labels}"
              f"   from Entry {r.n_from_entry}"
              f"   落差 {len(fails)}" + (f"（+{len(warns)} 警告）" if warns else ""))
        for f in r.findings:
            m = "✗" if f.severity == "FAIL" else "▲"
            print(f"    {m} [{f.kind}] {f.detail}")

    print("\n" + "=" * 74)
    print(f"合計 {total} 項落差")
    print("★ ✗ 是確定的落差，不是推測。每一項都要有處置：修、或寫進已知落差。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
