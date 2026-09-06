"""其餘跨層介面。

每一個空套件在這裡都有一個對應的 Protocol —— 那就是它的驗收標準。
「還沒做」與「做錯了」因此可以分開：前者是沒有實作，後者是實作不符介面。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from txfcore.types.orders import MarketPosition, OrderIntent, SizedOrder


# ======================================================================
# journal/  事件日誌
# ======================================================================

class EventKind(str, Enum):
    BAR = "bar"
    TICK = "tick"
    CLOCK = "clock"
    CALENDAR = "calendar"
    ORDER_INTENT = "order_intent"
    ORDER_ACK = "order_ack"
    FILL = "fill"
    BROKER_REPORT = "broker_report"
    INVARIANT_FAILURE = "invariant_failure"
    STATE_SNAPSHOT = "state_snapshot"


@dataclass(frozen=True, slots=True)
class Event:
    seq: int
    kind: EventKind
    event_time: str      # 交易所時間，ISO 8601
    receipt_time: str    # 系統收到的時間
    payload: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Journal(Protocol):
    """append-only 事件日誌，帶序號。

    重放的**唯一**輸入。實盤出事時要重現的是「那天系統看到的市場」，
    不是「那天的市場」—— 用歷史資料重建會把當時的觀測缺陷抹掉。
    """

    def append(self, kind: EventKind, event_time: str,
               receipt_time: str, payload: dict[str, Any]) -> int:
        """回傳寫入的序號。序號必須嚴格遞增且無缺號。"""
        ...

    def replay(self, from_seq: int = 0) -> Iterator[Event]: ...

    def last_seq(self) -> int: ...


# ======================================================================
# state/  持久化與復原
# ======================================================================

@runtime_checkable
class StateStore(Protocol):
    """持久化狀態是**唯一權威**，券商是校驗來源。

    重啟後若無有效快照，預設動作是「停止所有交易並告警」，不是重建。
    v_Frozen_SL 這類值拿不回來，猜一個比停下來危險。
    """

    def save(self, strategy: str, snapshot: dict[str, Any], seq: int) -> None: ...

    def load(self, strategy: str) -> tuple[dict[str, Any], int] | None:
        """回傳 (快照, 對應的日誌序號)；無有效快照時回傳 None。"""
        ...


@runtime_checkable
class KillSwitch(Protocol):
    """實盤第一個功能，不是最後一個。必須納入每日自動測試。"""

    def is_engaged(self) -> bool: ...
    def engage(self, reason: str) -> None: ...
    def release(self, operator: str, reason: str) -> None:
        """必須人工釋放。不自動恢復 —— 否則間歇性問題會反覆觸發又反覆恢復。"""
        ...


# ======================================================================
# lineage/  血緣雜湊
# ======================================================================

@dataclass(frozen=True, slots=True)
class Lineage:
    """每份結果攜帶產生它的全部上游雜湊。

    加了這個，L3 那類「基準線自己從 360 變 361」的事故在結構上就
    不可能發生 —— 新舊結果的雜湊不同，diff 工具會直接拒絕比較。
    """

    code_hash: str
    config_hash: str
    data_hash: str
    calendar_hash: str

    def matches(self, other: "Lineage") -> bool:
        return self == other


# ======================================================================
# obs/  可觀測性
# ======================================================================

@runtime_checkable
class Observer(Protocol):
    """心跳、指標、告警。層 0 基礎設施，不是層 5 的附屬品。

    心跳內容必須包含**最後處理的 K 棒時間戳**，只回「我還在」的心跳
    無法區分「系統正常」與「策略迴圈卡死」。
    """

    def heartbeat(self, last_bar_date: int, last_bar_time: int) -> None: ...
    def metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None: ...
    def alert(self, severity: str, message: str, context: dict[str, Any]) -> None: ...


@runtime_checkable
class TriggerMonitor(Protocol):
    """觸發次數監控 —— 判官 (4) 的實作。

    L2 停擺 443 天、L4 v18 零觸發，都是因為沒有人登記過預期頻率。
    偏離登記區間即告警。
    """

    def register(self, strategy: str, expected_range: tuple[int, int], window_days: int) -> None: ...
    def observe(self, strategy: str, count: int, window_days: int) -> bool:
        """回傳是否在登記區間內。False 即應告警。"""
        ...


# ======================================================================
# engine/  執行層
# ======================================================================

@dataclass(frozen=True, slots=True)
class Fill:
    intent_idem_key: str
    price: float
    quantity: int
    mc_date: int
    mc_time: int
    is_engine_stop: bool = False   # 引擎停損路徑，無對應出場單


@runtime_checkable
class FillModel(Protocol):
    """成交模型。

    **兩個獨立實作，永不互相 import：**
      fill_mc12   複製 MC 的樂觀假設（觸價即成交、零滑價）—— 對帳專用
      reality     從實盤資料量出來的真實成本 —— 風險判斷專用

    混在同一個檔案，等於永遠不會問「真實滑價下 MDD 是多少」。
    """

    @property
    def name(self) -> str: ...

    def fill(self, intent: OrderIntent, next_bar: Any) -> Fill | None:
        """回傳成交，或 None（本根未觸發）。"""
        ...


@runtime_checkable
class PositionBook(Protocol):
    """部位帳。L5 需要多腿 + 部分口數，其餘四支單一部位即可。"""

    def market_position(self, strategy: str) -> MarketPosition: ...
    def entry_price(self, strategy: str) -> float: ...
    def current_contracts(self, strategy: str) -> int: ...
    def max_contracts(self, strategy: str) -> int: ...
    def bars_since_entry(self, strategy: str) -> int: ...


# ======================================================================
# risk/  風險層
# ======================================================================

class RiskAction(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"
    HALT = "halt"          # 停止全部交易，需人工釋放


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """風險層的輸出。**口數在這裡才被決定**（裁決 2026-09-06）。

    ALLOW 時 order 必定非 None；REJECT / HALT 時為 None。
    """

    action: RiskAction
    order: SizedOrder | None = None
    reason: str = ""


@runtime_checkable
class RiskGate(Protocol):
    """層 3。**無 MC 錨點** —— MC 一次只跑一支、一個帳戶、固定口數，
    從未回答過五支同時發訊號、總曝險上限、斷線時該不該下單。

    驗證方式：不變量 + 情境重放 + 故障注入，三法各自事前登記通過標準。
    """

    def size(self, intent: OrderIntent) -> RiskDecision:
        """決定口數並放行，或攔截。

        mc12 對帳模式下必須回傳與 MC 相同的固定口數（instrument.default_lots），
        否則對不上帳。真正的 sizing 邏輯只在 live / v2 模式生效。
        """
        ...

    def reconcile(self, broker_positions: dict[str, int]) -> RiskDecision:
        """券商部位對帳迴路。不一致即 HALT，且**不自動修正** ——
        不知道哪一邊對，自動修正可能讓情況更糟。"""
        ...


# ======================================================================
# parity/  對帳（旁路，不在資料流上）
# ======================================================================

class ParityTier(str, Enum):
    """規格表的裁決：完成定義拆三層，只有第一層設零差異標準。"""

    DECISION = "decision"        # 時間 / 方向 / 單型 / 口數 → 零差異
    FILL = "fill"                # 成交價 → 容許差異但須歸因到成交假設
    PERFORMANCE = "performance"  # 績效數字 → 不設標準，MC 不是判官


@dataclass(frozen=True, slots=True)
class ParityResult:
    tier: ParityTier
    passed: bool
    diff_count: int
    tolerance_commit: str        # 本次使用的門檻來自哪個 commit
    lineage: Lineage | None = None
    notes: Sequence[str] = ()


@runtime_checkable
class ParityChecker(Protocol):
    """判官 (1)。它自己也需要判官 —— 對帳工具出過事故且當場印「通過」。

    黃金測試集必須先抓得到五個已知歷史事故，才准去驗證新東西。
    """

    def compare(self, ours: Sequence[Any], theirs: Sequence[Any],
                tier: ParityTier) -> ParityResult: ...
