"""逐筆對帳。

**完成定義拆三層**（規格表的裁決）：

    DECISION      時間 / 方向 / 單型 / 口數  → 零差異。MC 是有效判官
    FILL          成交價                      → 容許差異但須歸因到成交假設
    PERFORMANCE   績效數字                    → **不設標準，MC 不是判官**

照原本「彙總指標零差異」會花大量時間去追那些本來就不該相同的數字。

**兩個守門機制：**

一、血緣雜湊不同即**拒絕比較**，而不是印出一堆無法解釋的差異。
    L3 那類「基準線自己從 360 變 361」的事故因此結構上不可能發生。

二、報告開頭印出**本次使用的容差與其 commit**。
    容差事後被放寬是最常見的自欺，印出來讓它無所遁形。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from txfcore.lineage.stamp import Lineage, LineageMismatch, require_match


class Tier(str, Enum):
    DECISION = "decision"
    FILL = "fill"
    PERFORMANCE = "performance"


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """兩邊共用的比對單位。MC 報告與 Python 回測都轉成這個型別。"""

    entry_date: int
    entry_time: int
    exit_date: int
    exit_time: int
    direction: int          # 1 = 多、-1 = 空
    quantity: int
    entry_price: float
    exit_price: float
    entry_label: str = ""
    exit_label: str = ""

    @property
    def decision_key(self) -> tuple:
        """決策層的比對鍵。**不含價格**——那是成交層的事。"""
        return (self.entry_date, self.entry_time, self.direction)


def merge_split_exits(trades: Sequence[TradeRecord]) -> list[TradeRecord]:
    """合併分批出場。

    **這正是 2026-08-25 那個事故**：對帳工具沒有合併分批出場，
    當場印「通過」而實際上兩邊的交易筆數不同。

    實戰紀錄裡同樣的缺陷還在——9 組 18 筆，佔 30.5%。

    合併鍵：進場時間 + 方向。出場價取加權平均，口數相加。
    """
    groups: dict[tuple, list[TradeRecord]] = {}
    for t in trades:
        groups.setdefault((t.entry_date, t.entry_time, t.direction), []).append(t)

    out: list[TradeRecord] = []
    for key, g in groups.items():
        if len(g) == 1:
            out.append(g[0])
            continue
        qty = sum(x.quantity for x in g)
        wexit = sum(x.exit_price * x.quantity for x in g) / qty
        wentry = sum(x.entry_price * x.quantity for x in g) / qty
        last = max(g, key=lambda x: (x.exit_date, x.exit_time))
        out.append(TradeRecord(
            entry_date=g[0].entry_date, entry_time=g[0].entry_time,
            exit_date=last.exit_date, exit_time=last.exit_time,
            direction=g[0].direction, quantity=qty,
            entry_price=wentry, exit_price=wexit,
            entry_label=g[0].entry_label, exit_label=last.exit_label,
        ))
    out.sort(key=lambda t: (t.entry_date, t.entry_time))
    return out


@dataclass(frozen=True, slots=True)
class Tolerance:
    """容差。**必須在看到 diff 之前登記。**

    `commit` 是這組門檻來自哪個 commit。報告開頭會印出來——
    事後放寬容差是最常見的自欺，印出來讓它無所遁形。
    """

    tier: Tier
    max_diff_trades: int = 0
    max_price_diff_pts: float | None = None
    commit: str = "UNREGISTERED"

    def __post_init__(self) -> None:
        if self.commit == "UNREGISTERED":
            # 不擋，但報告會標明未登記
            pass


@dataclass(slots=True)
class ParityResult:
    tier: Tier
    passed: bool
    ours_count: int
    theirs_count: int
    matched: int
    only_ours: list[TradeRecord] = field(default_factory=list)
    only_theirs: list[TradeRecord] = field(default_factory=list)
    field_diffs: list[tuple[TradeRecord, TradeRecord, list[str]]] = field(default_factory=list)
    tolerance: Tolerance | None = None
    lineage: Lineage | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def diff_count(self) -> int:
        return len(self.only_ours) + len(self.only_theirs) + len(self.field_diffs)

    def report(self) -> str:
        tol = self.tolerance
        head = [
            f"對帳層級   {self.tier.value}",
            f"容差       max_diff_trades={tol.max_diff_trades if tol else '?'}"
            f"   commit={tol.commit if tol else '?'}",
            f"血緣       {self.lineage.short if self.lineage else '未附'}",
            f"筆數       ours={self.ours_count}  theirs={self.theirs_count}"
            f"  matched={self.matched}",
            f"差異       {self.diff_count}   →   {'PASS' if self.passed else 'FAIL'}",
        ]
        if tol and tol.commit == "UNREGISTERED":
            head.append("⚠ 容差未登記 commit。事前登記是判官 (4) 的核心。")
        if self.notes:
            head += ["", *(f"  · {n}" for n in self.notes)]
        return "\n".join(head)


DECISION_FIELDS = ("entry_date", "entry_time", "exit_date", "exit_time",
                   "direction", "quantity")
FILL_FIELDS = ("entry_price", "exit_price")


def compare(
    ours: Sequence[TradeRecord],
    theirs: Sequence[TradeRecord],
    tier: Tier,
    tolerance: Tolerance,
    ours_lineage: Lineage | None = None,
    theirs_lineage: Lineage | None = None,
    merge_splits: bool = True,
) -> ParityResult:
    """比對兩份交易清單。

    `merge_splits` 預設開啟——分批出場未合併是已發生過的事故。
    關掉它只在測試「工具本身抓不抓得到」時使用。
    """
    notes: list[str] = []

    if ours_lineage is not None and theirs_lineage is not None:
        try:
            require_match(ours_lineage, theirs_lineage)
        except LineageMismatch as e:
            raise LineageMismatch(
                f"{e}\n拒絕比較。與其印出無法解釋的差異，不如說「你在比兩個不同的東西」。"
            ) from None

    a = list(ours)
    b = list(theirs)
    if merge_splits:
        ma, mb = merge_split_exits(a), merge_split_exits(b)
        if len(ma) != len(a) or len(mb) != len(b):
            notes.append(
                f"合併分批出場：ours {len(a)}→{len(ma)}　theirs {len(b)}→{len(mb)}"
            )
        a, b = ma, mb

    if tier is Tier.PERFORMANCE:
        return ParityResult(
            tier=tier, passed=True, ours_count=len(a), theirs_count=len(b),
            matched=0, tolerance=tolerance, lineage=ours_lineage,
            notes=[*notes, "績效層不設標準——MC 不是判官，它的成交假設從未被檢驗。"],
        )

    fields = DECISION_FIELDS if tier is Tier.DECISION else FILL_FIELDS
    idx_b: dict[tuple, list[TradeRecord]] = {}
    for t in b:
        idx_b.setdefault(t.decision_key, []).append(t)

    only_ours: list[TradeRecord] = []
    field_diffs: list[tuple[TradeRecord, TradeRecord, list[str]]] = []
    matched = 0
    used: set[int] = set()

    for t in a:
        cands = idx_b.get(t.decision_key, [])
        pick = next((c for c in cands if id(c) not in used), None)
        if pick is None:
            only_ours.append(t)
            continue
        used.add(id(pick))
        matched += 1
        bad = []
        for f in fields:
            x, y = getattr(t, f), getattr(pick, f)
            if tier is Tier.FILL and tolerance.max_price_diff_pts is not None:
                if abs(x - y) > tolerance.max_price_diff_pts:
                    bad.append(f)
            elif x != y:
                bad.append(f)
        if bad:
            field_diffs.append((t, pick, bad))

    only_theirs = [t for t in b if id(t) not in used]
    total = len(only_ours) + len(only_theirs) + len(field_diffs)

    return ParityResult(
        tier=tier, passed=total <= tolerance.max_diff_trades,
        ours_count=len(a), theirs_count=len(b), matched=matched,
        only_ours=only_ours, only_theirs=only_theirs, field_diffs=field_diffs,
        tolerance=tolerance, lineage=ours_lineage, notes=notes,
    )
