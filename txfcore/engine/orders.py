"""訂單生命週期狀態機。

**外部借鑑：NautilusTrader 的訂單流。** 其文件描述的順序是：
RiskEngine 先做盤前檢查（部位上限、名目上限、下單速率），檢查失敗時
**策略會收到 OrderDenied，訂單根本到不了交易所**；通過後 ExecutionEngine
路由給 ExecutionClient 送出，之後 Accepted / Filled / Canceled / Rejected /
Expired 等事件逐一回流，更新狀態並交給策略的 handler。

我們原本的模型是 `OrderIntent → Fill`，**中間什麼都沒有**。後果：

    1. 風險層攔截後，策略不知道 —— 它以為單送出去了
    2. 部分成交表達不出來 —— 而 L5 的 Stage 2/3 判定完全靠 CurrentContracts
    3. 拒單、逾時、重複回報沒有型別可以承載

`mc12` 對帳模式下狀態機會退化成 `SUBMITTED → FILLED` 兩步（MC 沒有拒單、
沒有部分成交），但**型別必須先存在**，否則接券商時要回頭改所有層。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from txfcore.types.orders import OrderIntent, SizedOrder


class OrderStatus(str, Enum):
    """訂單狀態。轉移規則見 `ALLOWED`。"""

    INITIALIZED = "initialized"      # 策略產生意圖，尚未經風險層
    DENIED = "denied"                # 風險層攔截，**從未送達交易所**
    SUBMITTED = "submitted"          # 已送出，等待交易所確認
    ACCEPTED = "accepted"            # 交易所已接受，掛單中
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"            # 交易所拒絕（與 DENIED 不同：這是對方拒的）
    EXPIRED = "expired"

    @property
    def is_terminal(self) -> bool:
        return self in _TERMINAL

    @property
    def is_open(self) -> bool:
        return self in (OrderStatus.SUBMITTED, OrderStatus.ACCEPTED,
                        OrderStatus.PARTIALLY_FILLED)


_TERMINAL = frozenset({
    OrderStatus.DENIED, OrderStatus.FILLED, OrderStatus.CANCELED,
    OrderStatus.REJECTED, OrderStatus.EXPIRED,
})

ALLOWED: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.INITIALIZED: frozenset({OrderStatus.DENIED, OrderStatus.SUBMITTED}),
    OrderStatus.SUBMITTED: frozenset({
        OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.FILLED,
        OrderStatus.PARTIALLY_FILLED, OrderStatus.CANCELED,
    }),
    OrderStatus.ACCEPTED: frozenset({
        OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED,
        OrderStatus.CANCELED, OrderStatus.EXPIRED,
    }),
    OrderStatus.PARTIALLY_FILLED: frozenset({
        OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED,
        OrderStatus.CANCELED, OrderStatus.EXPIRED,
    }),
}


class InvalidTransition(ValueError):
    """非法狀態轉移。**不做寬鬆處理** —— 狀態機亂了比停下來危險。"""


class EventKind(str, Enum):
    DENIED = "denied"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    FILL = "fill"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class OrderEvent:
    """回流給策略的事件。

    **`DENIED` 也是事件。** 風險層攔截後策略必須知道——
    否則它會以為單送出去了，而那個誤解會累積成錯誤的部位認知。
    """

    kind: EventKind
    idem_key: str
    at: datetime
    quantity: int = 0
    price: float | None = None
    reason: str = ""


@dataclass(slots=True)
class ManagedOrder:
    """一張訂單的完整生命。

    `filled_qty` 累加，`leaves_qty` 是還沒成交的部分——
    L5 的 Stage 判定需要它。
    """

    order: SizedOrder
    status: OrderStatus = OrderStatus.INITIALIZED
    filled_qty: int = 0
    avg_fill_price: float = 0.0
    events: list[OrderEvent] = field(default_factory=list)
    venue_order_id: str = ""

    @property
    def idem_key(self) -> str:
        return self.order.idem_key

    @property
    def intent(self) -> OrderIntent:
        return self.order.intent

    @property
    def leaves_qty(self) -> int:
        return max(self.order.quantity - self.filled_qty, 0)

    def _transition(self, to: OrderStatus) -> None:
        allowed = ALLOWED.get(self.status, frozenset())
        if to not in allowed:
            raise InvalidTransition(
                f"{self.idem_key}: {self.status.value} -> {to.value} 非法。"
                f"允許的是 {sorted(x.value for x in allowed)}"
            )
        self.status = to

    # ---- 事件套用 ----
    def deny(self, at: datetime, reason: str) -> OrderEvent:
        self._transition(OrderStatus.DENIED)
        e = OrderEvent(EventKind.DENIED, self.idem_key, at, reason=reason)
        self.events.append(e)
        return e

    def submit(self, at: datetime) -> OrderEvent:
        self._transition(OrderStatus.SUBMITTED)
        e = OrderEvent(EventKind.SUBMITTED, self.idem_key, at)
        self.events.append(e)
        return e

    def accept(self, at: datetime, venue_order_id: str = "") -> OrderEvent:
        self._transition(OrderStatus.ACCEPTED)
        self.venue_order_id = venue_order_id
        e = OrderEvent(EventKind.ACCEPTED, self.idem_key, at)
        self.events.append(e)
        return e

    def fill(self, at: datetime, qty: int, price: float) -> OrderEvent:
        if qty <= 0:
            raise ValueError("成交口數必須 > 0")
        if qty > self.leaves_qty:
            raise InvalidTransition(
                f"{self.idem_key}: 成交 {qty} 口但只剩 {self.leaves_qty} 口未成交"
            )
        total = self.filled_qty + qty
        self.avg_fill_price = (
            self.avg_fill_price * self.filled_qty + price * qty
        ) / total
        self.filled_qty = total
        self._transition(
            OrderStatus.FILLED if self.leaves_qty == 0 else OrderStatus.PARTIALLY_FILLED
        )
        e = OrderEvent(EventKind.FILL, self.idem_key, at, qty, price)
        self.events.append(e)
        return e

    def cancel(self, at: datetime, reason: str = "") -> OrderEvent:
        self._transition(OrderStatus.CANCELED)
        e = OrderEvent(EventKind.CANCELED, self.idem_key, at, reason=reason)
        self.events.append(e)
        return e

    def reject(self, at: datetime, reason: str) -> OrderEvent:
        self._transition(OrderStatus.REJECTED)
        e = OrderEvent(EventKind.REJECTED, self.idem_key, at, reason=reason)
        self.events.append(e)
        return e

    def expire(self, at: datetime) -> OrderEvent:
        self._transition(OrderStatus.EXPIRED)
        e = OrderEvent(EventKind.EXPIRED, self.idem_key, at)
        self.events.append(e)
        return e


class OrderBook:
    """在途訂單簿。冪等去重在這裡，不在通知層。

    OCO：一張成交後撤銷同組其他張。L3 的 bracket（TP limit + SL stop）
    與 L5 的每腿訂單集合都需要它。
    """

    def __init__(self) -> None:
        self._orders: dict[str, ManagedOrder] = {}
        self._groups: dict[str, list[str]] = {}

    def place(self, order: SizedOrder, oco_group: str = "") -> tuple[ManagedOrder, bool]:
        """回傳 (訂單, 是否為新單)。同 idem_key 重送視為同一筆。"""
        key = order.idem_key
        if key in self._orders:
            return self._orders[key], False
        mo = ManagedOrder(order=order)
        self._orders[key] = mo
        if oco_group:
            self._groups.setdefault(oco_group, []).append(key)
        return mo, True

    def get(self, idem_key: str) -> ManagedOrder | None:
        return self._orders.get(idem_key)

    def open_orders(self) -> list[ManagedOrder]:
        return [o for o in self._orders.values() if o.status.is_open]

    def cancel_group_except(
        self, oco_group: str, keep: str, at: datetime
    ) -> list[OrderEvent]:
        """OCO：一張成交，同組其他張撤銷。"""
        out: list[OrderEvent] = []
        for key in self._groups.get(oco_group, []):
            if key == keep:
                continue
            o = self._orders.get(key)
            if o and o.status.is_open:
                out.append(o.cancel(at, reason=f"OCO {oco_group}"))
        return out

    def purge_terminal(self) -> int:
        """清掉終態訂單。回傳清掉幾張。"""
        dead = [k for k, o in self._orders.items() if o.status.is_terminal]
        for k in dead:
            del self._orders[k]
        for g in self._groups.values():
            g[:] = [k for k in g if k in self._orders]
        return len(dead)
