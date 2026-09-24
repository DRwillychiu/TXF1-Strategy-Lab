"""層間依賴的機械檢查。

規劃書層 0 列的「層間依賴 CI 檢查」就是這一支。

鐵則是「回測與即時跑同一份策略碼，只有三顆插頭不同」。若策略層能
直接抓報價或直接下單，那份程式碼就綁死在某一端，換插頭就不再是換插頭。
靠紀律維持會失效 —— 所以寫成會叫的東西。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "txfcore"

LAYER0 = {
    "contracts", "types", "instruments", "costs", "metrics",
    "journal", "timing", "state", "lineage", "obs",
}
SUPPORT = {"indicators", "tradecal", "engine"}

# 每個套件允許依賴的套件集合
# 層 0 內部有次序：types 是最內圈的純資料，其餘層 0 套件可依賴它。
# 這不是環，是正確的地基分層。2026-09-06 由本檢查抓出並修正規則。
LAYER0_CORE = {"types"}

ALLOWED: dict[str, set[str]] = {}
for pkg in LAYER0:
    ALLOWED[pkg] = set(LAYER0_CORE) - {pkg}                # 層 0 只准依賴 types
ALLOWED["types"] = set()                                   # 最內圈，誰都不依賴
ALLOWED["costs"] = {"instruments", "types"}      # 成本需要商品規格
# metrics 的損益指標要把點數換算成金額，同樣需要商品規格。
# 2026-09-08 由本檢查抓出。instruments 不依賴 metrics，無環。
# 2026-09-10 再加 costs：M2 的「手續費總額 / 期交稅總額」要拆兩項，需要費率表。
# costs 不依賴 metrics，無環。與上面 instruments 那條同型。
ALLOWED["metrics"] = {"instruments", "costs", "types"}
for pkg in SUPPORT:
    ALLOWED[pkg] = set(LAYER0)
# engine -> tradecal 是**具體的一條邊**。
# 理由：帳務層要知道「每日結算在哪一刻」——一般日 1345、結算日 1330。
# 那是行事曆的事實，不是引擎的假設。tradecal 不依賴 engine，無環。
# 2026-09-08 由本檢查抓出，與下面 quotes 那條同型。
ALLOWED["engine"] = ALLOWED["engine"] | {"tradecal"}

# quotes -> tradecal 是**具體的一條邊**，不是放寬整層。
# 理由：網格切分需要知道結算日（日盤 285 分而非 300 分），
# 而結算行事曆是市場的參考資料。tradecal 不依賴 quotes，無環。
# 2026-09-06 由本檢查抓出並記錄。
ALLOWED["quotes"] = set(LAYER0) | {"tradecal"}
ALLOWED["strategies"] = set(LAYER0) | SUPPORT              # 不含 quotes/notify/broker
ALLOWED["risk"] = set(LAYER0) | SUPPORT
ALLOWED["parity"] = set(LAYER0) | SUPPORT | {"strategies"}
ALLOWED["notify"] = set(LAYER0)
ALLOWED["broker"] = set(LAYER0)
# 組裝根：唯一允許 import 全部層的地方
ALLOWED["runtime"] = set(LAYER0) | SUPPORT | {
    "quotes", "strategies", "risk", "parity", "notify", "broker",
}

ALL_PACKAGES = set(ALLOWED)


def _imported_packages(path: Path) -> set[str]:
    """抓出這支檔案 import 了哪些 txfcore 子套件。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        parts: list[str] = []
        if isinstance(node, ast.Import):
            parts = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = [node.module]
        for name in parts:
            bits = name.split(".")
            if bits[0] == "txfcore" and len(bits) > 1:
                found.add(bits[1])
    return found


def _modules() -> list[tuple[str, Path]]:
    out = []
    for pkg in sorted(ALL_PACKAGES):
        d = ROOT / pkg
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            out.append((pkg, f))
    return out


@pytest.mark.parametrize("pkg,path", _modules(), ids=lambda x: getattr(x, "name", x))
def test_module_respects_layer_boundary(pkg: str, path: Path) -> None:
    imported = _imported_packages(path)
    illegal = imported - ALLOWED[pkg] - {pkg}
    assert not illegal, (
        f"{path.relative_to(ROOT.parent)} 違反分層依賴：{pkg} 不得 import {sorted(illegal)}。"
        f"允許的是 {sorted(ALLOWED[pkg])}。規則見 txfcore/LAYERS.md"
    )


def test_strategies_never_touch_the_two_plugs() -> None:
    """最重要的一條：策略層不得碰報價來源與訂單去向。

    碰了就等於把策略綁死在某一端，鐵則失效。
    """
    forbidden = {"quotes", "notify", "broker"}
    for f in sorted((ROOT / "strategies").glob("*.py")):
        bad = _imported_packages(f) & forbidden
        assert not bad, f"strategies/{f.name} import 了 {sorted(bad)}，違反三插頭鐵則"


def test_risk_never_touches_notify_or_broker() -> None:
    d = ROOT / "risk"
    if not d.is_dir():
        pytest.skip("risk/ 尚未建立")
    for f in sorted(d.glob("*.py")):
        bad = _imported_packages(f) & {"notify", "broker", "quotes"}
        assert not bad, f"risk/{f.name} import 了 {sorted(bad)}"


def test_layer0_has_no_upward_dependency() -> None:
    """層 0 是地基。一旦有向上的依賴，依賴圖就出現環。"""
    for pkg in sorted(LAYER0):
        d = ROOT / pkg
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            bad = _imported_packages(f) - {pkg} - ALLOWED[pkg]
            assert not bad, (
                f"{pkg}/{f.name} 依賴了 {sorted(bad)}。"
                f"層 0 只准依賴 types（最內圈），不得橫向依賴其他層 0 套件"
            )


def test_every_declared_package_exists() -> None:
    """LAYERS.md 宣告的套件必須都存在，即使是空的。

    空目錄本身是資訊：它讓「還沒做」在檔案樹上看得見，
    而不是靠人記得。
    """
    missing = [p for p in sorted(ALL_PACKAGES) if not (ROOT / p).is_dir()]
    assert not missing, f"以下套件在 LAYERS.md 宣告但不存在：{missing}"


def test_completeness_inventory() -> None:
    """完成度清單。此測試永遠通過，只是把現況印出來。

    用 `pytest -s` 看輸出。
    """
    layers = [
        ("層 0 基礎設施", sorted(LAYER0)),
        ("共用支撐層", sorted(SUPPORT)),
        ("層 1 報價", ["quotes"]),
        ("層 2 策略", ["strategies"]),
        ("層 3 風險", ["risk"]),
        ("層 5 通知下單", ["notify", "broker"]),
        ("旁路 對帳", ["parity"]),
        ("組裝根", ["runtime"]),
    ]
    print()
    done = total = 0
    for label, pkgs in layers:
        print(f"\n{label}")
        for p in pkgs:
            total += 1
            mods = sorted(
                f.name for f in (ROOT / p).glob("*.py") if f.name != "__init__.py"
            )
            if mods:
                done += 1
                print(f"   ✓ {p:<12} {', '.join(mods)}")
            else:
                print(f"   ○ {p:<12} 空")
    print(f"\n完成度 {done}/{total} 套件有內容")


# ======================================================================
# 介面完整性：每個空套件都必須有對應的 Protocol，那就是它的驗收標準
# ======================================================================

def test_every_plug_is_a_protocol() -> None:
    """三顆插頭必須是 Protocol，不是具體類別。

    是 Protocol 才能有兩組 adapter（回測 / 即時），
    鐵則才不是紀律而是型別。
    """
    from typing import Protocol

    from txfcore.contracts import plugs

    for name in ("Clock", "QuoteSource", "OrderSink"):
        cls = getattr(plugs, name)
        assert Protocol in cls.__mro__, f"{name} 必須是 Protocol"


def test_every_empty_package_has_a_contract() -> None:
    """空套件不是「還沒想」，是「介面已定、實作未填」。

    這兩件事必須分得開：前者是規劃缺口，後者只是進度。
    """
    from txfcore.contracts import plugs, ports

    required = {
        "journal": ["Journal"],
        "timing": ["Clock"],
        "state": ["StateStore", "KillSwitch"],
        "lineage": ["Lineage"],
        "obs": ["Observer", "TriggerMonitor"],
        "engine": ["FillModel", "PositionBook"],
        "quotes": ["QuoteSource"],
        "risk": ["RiskGate"],
        "notify": ["OrderSink"],
        "broker": ["OrderSink"],
        "parity": ["ParityChecker"],
    }
    missing = []
    for pkg, names in required.items():
        for n in names:
            if not (hasattr(ports, n) or hasattr(plugs, n)):
                missing.append(f"{pkg} -> {n}")
    assert not missing, f"以下套件沒有對應介面：{missing}"


def test_runtime_is_the_only_composition_root() -> None:
    """只有 runtime 可以同時 import 兩端的插頭實作。"""
    both_ends = {"quotes", "notify", "broker"}
    for pkg in sorted(ALL_PACKAGES - {"runtime"}):
        d = ROOT / pkg
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            touched = _imported_packages(f) & both_ends
            assert len(touched) < 2, (
                f"{pkg}/{f.name} 同時碰了 {sorted(touched)}，"
                f"只有 runtime 可以做組裝"
            )
