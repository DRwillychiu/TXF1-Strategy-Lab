"""MC12 成交模型。

**核心認知（2026-09-06 寫這支時發現）：MC 的成交規則無法從 OHLC 推出。**

    K 棒範圍  Low 19800 ── High 20200
    掛單      停損 19900 · 停利 20100
    兩個價位都在範圍內。哪一個先成交？

OHLC 沒有路徑資訊。MC 必須用一個假設，而那個假設**沒有文件、我們沒有證據**。

所以本模組不寫死規則，而是把假設做成**具名、可切換的 policy**，
讓對帳的 diff 告訴我們哪一組對得上。

> **這改變了對帳的定義**：對帳的一部分工作，是反推 MC 用了哪一組假設。
> 把未知變成參數，而不是把猜測寫死。

同一個歧義有五種面貌：

    同根同時觸停損與停利      L3 bracket · L5
    跳空穿過觸發價            全部
    同根進場又出場            L1（V2.9 記錄 12 筆 same-bar deaths）
    引擎停損 vs 自訂停損同根  全部
    兩條進場腿同根觸發        L5（影響 MaxContracts）
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from txfcore.types.bar import Bar
from txfcore.types.orders import OrderType, Side, SizedOrder


class IntrabarPolicy(str, Enum):
    """一根 K 棒內多個事件的先後順序假設。

    WORST_FIRST   假設對持倉最不利者先發生（業界慣例，也是保守估計）
    BEST_FIRST    假設最有利者先發生（樂觀上界，用來量測假設的影響幅度）
    OPEN_PROXIMITY 依觸發價與開盤價的距離排序，近者先（最貼近真實路徑）
    """

    WORST_FIRST = "worst_first"
    BEST_FIRST = "best_first"
    OPEN_PROXIMITY = "open_proximity"


class GapPolicy(str, Enum):
    """開盤已越過觸發價時的成交價假設。

    AT_OPEN       成交在開盤價（MC 的一般行為，對停損不利、對限價有利）
    AT_TRIGGER    成交在觸發價（樂觀，會低估跳空損失）
    """

    AT_OPEN = "at_open"
    AT_TRIGGER = "at_trigger"


@dataclass(frozen=True, slots=True)
class FillPolicy:
    """一組完整的成交假設。對帳時逐組試，看哪一組對得上。"""

    intrabar: IntrabarPolicy = IntrabarPolicy.WORST_FIRST
    gap: GapPolicy = GapPolicy.AT_OPEN
    # 進場那根是否可以立即被停損打掉。
    #
    # 2026-09-06 發現：這個欄位原本是**死設定**，宣告了卻沒有任何地方讀它，
    # 而且它出現在 policy 名稱裡（sb=1），等於報告一直在宣稱一個沒有作用的設定。
    # 更嚴重的是 runner 的順序讓同根出場**結構上不可能**——
    # 引擎停損檢查發生在進場填入之前。已接上並修正 runner。
    #
    # **但 L2 的證據指向 False。** 見下方 ef 的 2x2 表。
    # **L1 的 V2.9 取證記錄了 12 筆 same-bar deaths**，所以 L1 可能需要 True——
    # 移植 L1 時要重跑這個 2x2。
    allow_same_bar_exit: bool = False
    # 引擎停損（SetStopLoss）與自訂停損同根觸發時，誰先。
    #
    # 原本是死設定，runner 硬寫成「自訂出場優先」。接上開關後立刻產生對帳證據：
    #
    # L2 全歷史 2x2（虧損出場標籤向量對 MC 的 L1 距離）：
    #
    #     sb     ef      InitSL_D  InitSL_N  ENGINE  TSL_N   距離
    #     False  False       23        19        5      1      3   ← 最佳
    #     True   False       21        17        9      1      7
    #     False  True        21        13       13      1     15
    #     True   True        21        13       13      1     15
    #     MC                 22        18        4      1      0
    #
    # **兩者皆 False 最接近，每個標籤各差 +1。**
    # 引擎停損在 MC 裡是罕見路徑（45 筆虧損出場中只有 4 筆），
    # ef=True 會讓它變成 13 筆。
    #
    # 這是逐筆對帳之外，第一個能判定成交假設的訊號 ——
    # 而它來自一個我原本以為只是死碼的欄位。
    engine_stop_first: bool = False

    @property
    def name(self) -> str:
        return (f"{self.intrabar.value}|{self.gap.value}"
                f"|sb={int(self.allow_same_bar_exit)}"
                f"|ef={int(self.engine_stop_first)}")


DEFAULT_POLICY = FillPolicy()

# 對帳時要逐一試的候選組合
CANDIDATE_POLICIES: tuple[FillPolicy, ...] = (
    FillPolicy(IntrabarPolicy.WORST_FIRST, GapPolicy.AT_OPEN),
    FillPolicy(IntrabarPolicy.BEST_FIRST, GapPolicy.AT_OPEN),
    FillPolicy(IntrabarPolicy.WORST_FIRST, GapPolicy.AT_TRIGGER),
    FillPolicy(IntrabarPolicy.OPEN_PROXIMITY, GapPolicy.AT_OPEN),
    # 同根出場。L1 的 V2.9 取證記錄 12 筆 same-bar deaths，
    # 所以移植 L1 時要重跑這一組。L2 的證據指向 False。
    FillPolicy(IntrabarPolicy.WORST_FIRST, GapPolicy.AT_OPEN,
               allow_same_bar_exit=True),
    # 引擎停損優先。L2 的證據指向 False（ef=True 讓 ENGINE_STOP 從 5 變 13）。
    FillPolicy(IntrabarPolicy.WORST_FIRST, GapPolicy.AT_OPEN,
               engine_stop_first=True),
    FillPolicy(IntrabarPolicy.WORST_FIRST, GapPolicy.AT_OPEN,
               allow_same_bar_exit=True, engine_stop_first=True),
)


@dataclass(frozen=True, slots=True)
class Fill:
    order: SizedOrder
    price: float
    quantity: int
    mc_date: int
    mc_time: int
    # 引擎停損路徑：無對應的出場單。
    # L5 實測 171 筆中有 1 筆走這條，出場側標籤永遠標不到它。
    is_engine_stop: bool = False
    policy: str = ""

    @property
    def label(self) -> str:
        return "ENGINE_STOP" if self.is_engine_stop else self.order.intent.label


def _triggers_long(order_type: OrderType, side: Side, price: float, bar: Bar) -> bool:
    """該價位在這根 K 棒是否被觸及。"""
    buying = side in (Side.BUY, Side.BUY_TO_COVER)
    if order_type is OrderType.STOP:
        # 買停損：價格向上碰到；賣停損：價格向下碰到
        return bar.high >= price if buying else bar.low <= price
    if order_type is OrderType.LIMIT:
        # 買限價：價格向下碰到；賣限價：價格向上碰到
        return bar.low <= price if buying else bar.high >= price
    return True  # MARKET


def _fill_price(order: SizedOrder, bar: Bar, policy: FillPolicy) -> float:
    ot = order.intent.order_type
    if ot is OrderType.MARKET:
        return bar.open

    trigger = order.intent.price
    assert trigger is not None
    buying = order.intent.side in (Side.BUY, Side.BUY_TO_COVER)

    # 開盤已越過觸發價
    gapped = (bar.open >= trigger) if (buying and ot is OrderType.STOP) else False
    if ot is OrderType.STOP and not buying:
        gapped = bar.open <= trigger
    if ot is OrderType.LIMIT and buying:
        gapped = bar.open <= trigger
    if ot is OrderType.LIMIT and not buying:
        gapped = bar.open >= trigger

    if gapped:
        return bar.open if policy.gap is GapPolicy.AT_OPEN else trigger
    return trigger


def _adversity(order: SizedOrder, bar: Bar) -> float:
    """對持倉的不利程度。數字越大越不利，用於 WORST_FIRST 排序。

    出場單的不利 = 成交價離開盤價越遠越糟（對多單是越低越糟）。
    """
    price = order.intent.price if order.intent.price is not None else bar.open
    side = order.intent.side
    if side in (Side.SELL, Side.BUY_TO_COVER):
        # 平多：成交越低越糟；平空：成交越高越糟
        return (bar.open - price) if side is Side.SELL else (price - bar.open)
    return 0.0


def _sort_key(order: SizedOrder, bar: Bar, policy: FillPolicy):
    if policy.intrabar is IntrabarPolicy.WORST_FIRST:
        return -_adversity(order, bar)
    if policy.intrabar is IntrabarPolicy.BEST_FIRST:
        return _adversity(order, bar)
    # OPEN_PROXIMITY：觸發價離開盤價近者先
    price = order.intent.price if order.intent.price is not None else bar.open
    return abs(price - bar.open)


class MC12FillModel:
    """對帳專用。複製 MC 的樂觀假設：觸價即成交、零滑價、無部分成交、無拒單。

    **絕不 import `engine/reality.py`，反之亦然。** 兩者是兩套假設，
    混在一起等於永遠不會問「真實滑價下 MDD 是多少」。
    """

    name = "fill_mc12"

    def __init__(self, policy: FillPolicy = DEFAULT_POLICY) -> None:
        self.policy = policy

    def fill(self, orders: list[SizedOrder], bar: Bar) -> list[Fill]:
        """對「下一根」K 棒撮合這批掛單。

        回傳依成交順序排列。呼叫端負責處理「一張成交後其餘撤銷」（OCO）——
        本模型只回答「這根 K 棒裡誰觸發、成交在哪、順序如何」。
        """
        hit = [
            o for o in orders
            if _triggers_long(o.intent.order_type, o.intent.side, 
                              o.intent.price if o.intent.price is not None else bar.open, bar)
        ]
        hit.sort(key=lambda o: _sort_key(o, bar, self.policy))
        return [
            Fill(
                order=o,
                price=_fill_price(o, bar, self.policy),
                quantity=o.quantity,
                mc_date=bar.mc_date,
                mc_time=bar.mc_time,
                policy=self.policy.name,
            )
            for o in hit
        ]

    def engine_stop_fill(
        self, stop_price: float, side: Side, quantity: int, bar: Bar, strategy: str
    ) -> Fill | None:
        """引擎停損（SetStopLoss）。

        它可以在**沒有任何出場單**的情況下平倉——L5 實測 171 筆中有 1 筆。
        所以它必須是一種獨立的出場類型，否則對帳會出現
        「有平倉但找不到對應出場單」。
        """
        from txfcore.types.orders import OrderIntent

        buying = side in (Side.BUY, Side.BUY_TO_COVER)
        touched = bar.high >= stop_price if buying else bar.low <= stop_price
        if not touched:
            return None
        gapped = bar.open >= stop_price if buying else bar.open <= stop_price
        price = (
            bar.open if (gapped and self.policy.gap is GapPolicy.AT_OPEN) else stop_price
        )
        intent = OrderIntent(
            strategy=strategy, label="ENGINE_STOP", side=side,
            order_type=OrderType.STOP, price=stop_price,
            signal_date=bar.mc_date, signal_time=bar.mc_time,
        )
        return Fill(
            order=SizedOrder(intent=intent, quantity=quantity, sized_by="engine"),
            price=price, quantity=quantity,
            mc_date=bar.mc_date, mc_time=bar.mc_time,
            is_engine_stop=True, policy=self.policy.name,
        )
