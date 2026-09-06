"""回測組裝根。

**回測不是一層，是一種組裝。** 它做的事就是把三顆插頭換成歷史版本：

    報價來源   MC12 匯出的 1 分 K，聚合成目標週期
    訂單去向   交易記錄器，不發任何通知
    時鐘       BarClock，時間由 K 棒推動

中間的層 2、層 3 一個字都不動。`runtime/` 是**唯一允許 import 全部層**
的地方——把它獨立出來，其他每一層才維持得住嚴格單向依賴。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from txfcore.engine.accounting import ClosedTrade, Ledger, trade_cost
from txfcore.engine.fill_mc12 import DEFAULT_POLICY, FillPolicy, MC12FillModel
from txfcore.engine.position import PositionBook
from txfcore.instruments.spec import Instrument
from txfcore.lineage.stamp import Lineage
from txfcore.strategies.base import MarketView, PositionView, Strategy
from txfcore.timing.clock import BarClock
from txfcore.tradecal.gates import evaluate
from txfcore.types.bar import Bar, BarSeries
from txfcore.types.mctime import mc_date_to_date, mc_time_to_time
from txfcore.types.orders import (
    MarketPosition, OrderIntent, OrderType, ProtectiveStop, Side, SizedOrder,
)


@dataclass(slots=True)
class BacktestResult:
    strategy: str
    trades: list[ClosedTrade] = field(default_factory=list)
    ledger: Ledger | None = None
    bars_processed: int = 0
    orders_emitted: int = 0
    engine_stop_exits: int = 0
    lineage: Lineage | None = None
    policy: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def trade_count(self) -> int:
        return len(self.trades)

    def trades_after(self, mc_date: int) -> list[ClosedTrade]:
        """驗收用。例：L2 自 2025-06-03 起應為零觸發。"""
        return [t for t in self.trades if t.entry_date >= mc_date]


class FixedLotRiskGate:
    """mc12 對帳模式的風險層：固定口數，不攔截。

    口數由風險層決定（裁決 2026-09-06），但對帳時必須回傳與 MC 相同的
    固定口數，否則對不上帳。真正的 sizing 只在 live / v2 模式生效。
    """

    def __init__(self, lots: int) -> None:
        self.lots = lots

    def size(self, intent: OrderIntent) -> SizedOrder:
        return SizedOrder(intent=intent, quantity=self.lots, sized_by="fixed_lot")


class BacktestRunner:
    """把 K 棒串流餵給策略，撮合，記帳。

    **訂單在下一根成交**——MC 的 `next bar at ...` 語意。
    所以本輪產出的意圖，要等下一根 K 棒才撮合。
    """

    def __init__(
        self,
        strategy: Strategy,
        instrument: Instrument,
        policy: FillPolicy = DEFAULT_POLICY,
        lineage: Lineage | None = None,
        warmup_bars: int = 40,
    ) -> None:
        self.strategy = strategy
        self.instrument = instrument
        self.fill_model = MC12FillModel(policy)
        self.risk = FixedLotRiskGate(instrument.default_lots)
        self.lineage = lineage
        self.warmup_bars = warmup_bars

    def run(self, bars) -> BacktestResult:
        s = self.strategy
        name = s.config.name
        state = s.initial_state()
        series = BarSeries("data1")
        book = PositionBook()
        clock = BarClock()
        ledger = Ledger(self.instrument)
        res = BacktestResult(strategy=name, ledger=ledger,
                             lineage=self.lineage, policy=self.fill_model.policy.name)

        pending: list[SizedOrder] = []
        protective: ProtectiveStop | None = None
        entry_leg: tuple[str, float, int, int] | None = None  # label, price, date, time

        for bar in bars:
            clock.advance_to(
                datetime.combine(mc_date_to_date(bar.mc_date), mc_time_to_time(bar.mc_time))
            )
            pos = book.get(name)

            # ---- 0. 既有部位先老化一根 ----
            # 必須在撮合之前。否則本根成交的新腿會被立刻 +1，
            # 策略永遠看不到 BarsSinceEntry == 0，而 L2 的 S8 初始停損鎖定
            # 與 S11 的 lowest_close 初始化都掛在那個 0 上。
            pos.advance_bar()

            # ---- 1. 撮合上一根產生的掛單（next bar 語意）----
            if pending or protective:
                fills = self.fill_model.fill(pending, bar)
                # 引擎停損：可在沒有任何出場單的情況下平倉（L5 實測 171 筆中 1 筆）
                if protective and not pos.is_flat:
                    side = Side.SELL if pos.direction is MarketPosition.LONG else Side.BUY_TO_COVER
                    sign = -1 if pos.direction is MarketPosition.LONG else 1
                    stop_px = pos.entry_price + sign * protective.distance
                    ef = self.fill_model.engine_stop_fill(
                        stop_px, side, pos.current_contracts, bar, name
                    )
                    if ef and not any(
                        f.order.intent.side in (Side.SELL, Side.BUY_TO_COVER) for f in fills
                    ):
                        fills = [ef]
                        res.engine_stop_exits += 1

                for f in fills:
                    side = f.order.intent.side
                    if side in (Side.BUY, Side.SELL_SHORT):
                        if not pos.is_flat:
                            continue          # 已有部位，忽略重複進場
                        pos.open_leg(f.order.intent.label, f.price, f.quantity,
                                     bar.mc_date, bar.mc_time, side)
                        entry_leg = (f.order.intent.label, f.price,
                                     bar.mc_date, bar.mc_time)
                    else:
                        if pos.is_flat or entry_leg is None:
                            continue
                        lbl, epx, ed, et = entry_leg
                        qty = min(f.quantity, pos.current_contracts)
                        direction = pos.direction
                        pos.close(qty, from_entry=f.order.intent.from_entry)
                        t = ClosedTrade(
                            strategy=name, entry_label=lbl, exit_label=f.label,
                            direction=direction, quantity=qty,
                            entry_price=epx, exit_price=f.price,
                            entry_date=ed, entry_time=et,
                            exit_date=bar.mc_date, exit_time=bar.mc_time,
                            cost=trade_cost(self.instrument, epx, f.price, qty),
                        )
                        res.trades.append(t)
                        ledger.record(t)
                        pos.prev_position_profit = t.net_ntd(self.instrument)
                        if pos.is_flat:
                            entry_leg = None
                    break                     # 一根只成交一筆（L2/L4 的 ExitFired 語意）
                pending = []

            # ---- 2. 推進 K 棒，跑策略 ----
            series.push(bar)
            res.bars_processed += 1
            if len(series) < self.warmup_bars:
                continue

            view = MarketView(
                data1=series,
                position=PositionView(
                    market_position=pos.direction,
                    entry_price=pos.entry_price,
                    bars_since_entry=pos.bars_since_entry,
                    prev_market_position=state.prev_market_position,
                    prev_position_profit=pos.prev_position_profit,
                    current_contracts=pos.current_contracts,
                    max_contracts=pos.max_contracts,
                ),
                calendar=evaluate(bar.mc_date, bar.mc_time,
                                  s.config.registry_valid_until),
                mc_date=bar.mc_date, mc_time=bar.mc_time,
            )
            state, decision = s.on_bar(view, state)
            if decision.protective is not None:
                protective = decision.protective
            pending = [self.risk.size(o) for o in decision.orders]
            res.orders_emitted += len(pending)

        return res
