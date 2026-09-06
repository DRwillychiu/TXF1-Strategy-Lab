"""訂單型別。

裁決 2026-09-06：**口數由風險層決定，策略層不輸出口數。**

所以這裡有兩個型別而不是一個：

    OrderIntent   策略層輸出。方向 / 單型 / 價格 / 標籤。**沒有口數。**
    SizedOrder    風險層輸出。OrderIntent + 口數。送得出去的東西。

策略層輸出口數的話，風險層只能否決不能調整 —— 那是機構把 alpha 與
sizing 分層的原因。分開之後，「五支同時發訊號」這種 MC 從未回答過的
問題，才有地方可以回答。

schema 住在層 0，不住在 notify/ —— 放通知層等於訂單有第二個定義。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(str, Enum):
    BUY = "buy"                    # 開多
    SELL = "sell"                  # 平多
    SELL_SHORT = "sell_short"      # 開空
    BUY_TO_COVER = "buy_to_cover"  # 平空


class OrderType(str, Enum):
    MARKET = "market"
    STOP = "stop"
    LIMIT = "limit"


class MarketPosition(int, Enum):
    """MC 的 MarketPosition：1 = 多、0 = 空手、-1 = 空。"""

    LONG = 1
    FLAT = 0
    SHORT = -1


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """策略層的唯一輸出。**不含口數。**

    「同一根 K 棒 + 同一組狀態 -> 完全確定的輸出」這條不變量，
    靠的是本型別為 frozen 且策略函數為純函數。
    """

    strategy: str
    label: str            # MC 的訂單名稱，例如 TS_Entry / TS_InitSL_D
    side: Side
    order_type: OrderType
    price: float | None = None      # MARKET 為 None
    signal_date: int = 0
    signal_time: int = 0
    from_entry: str | None = None   # 腿綁定，只有 L5 用得到
    seq: int = 0

    def __post_init__(self) -> None:
        if self.order_type is OrderType.MARKET and self.price is not None:
            raise ValueError("市價單不得帶價格")
        if self.order_type is not OrderType.MARKET and self.price is None:
            raise ValueError(f"{self.order_type} 必須帶價格")

    @property
    def idem_key(self) -> str:
        """冪等鍵。重送同鍵視為同一筆。"""
        return (
            f"{self.strategy}|{self.signal_date}|{self.signal_time}"
            f"|{self.label}|{self.seq}"
        )

    @property
    def is_entry(self) -> bool:
        return self.side in (Side.BUY, Side.SELL_SHORT)


@dataclass(frozen=True, slots=True)
class SizedOrder:
    """風險層輸出。口數在這裡才被決定。

    mc12 對帳模式下，風險層必須回傳與 MC 相同的固定口數（2），
    否則對不上帳。真正的 sizing 邏輯只在 live / v2 模式生效。
    """

    intent: OrderIntent
    quantity: int
    sized_by: str = "risk"   # 誰決定的，供對帳歸因

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity 必須 > 0")

    @property
    def idem_key(self) -> str:
        return self.intent.idem_key


@dataclass(frozen=True, slots=True)
class ProtectiveStop:
    """引擎層級停損（MC 的 SetStopLoss + SetStopContract）。

    L5 標頭實測：SL_Pct = 1.0 時，引擎停損可以在**沒有任何 Sell 語句**
    的情況下平倉（171 筆中有 1 筆）。出場側標籤永遠標不到這條路徑，
    所以 Python 版必須把它記成一種獨立的出場類型。
    """

    strategy: str
    distance: float            # 點數距離
    per_contract: bool = True  # SetStopContract = True
    signal_date: int = 0
    signal_time: int = 0

    def amount(self, big_point_value: float) -> float:
        return self.distance * big_point_value


@dataclass(slots=True)
class Decision:
    """策略在一根 K 棒上的完整輸出。

    orders 可能有多張 —— L3 是 TP limit + SL stop 的 bracket，
    L1 一根最多三張市價單（J-3，標頭自承未修）。
    只有 L2 / L4 靠 ExitFired 保證單根單張。
    """

    orders: list[OrderIntent] = field(default_factory=list)
    protective: ProtectiveStop | None = None
    notes: list[str] = field(default_factory=list)

    def add(self, order: OrderIntent) -> None:
        self.orders.append(order)
