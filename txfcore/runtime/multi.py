"""多資料流回測驅動器。

L3 / L4 / L5 需要 Data1 + Data2 + Data3。L1 也是（45M / Daily / Weekly）。
只有 L2 是單流，用 `runtime/backtest.py` 即可。

**對齊規則**：Data2 / Data3 只暴露已收盤的 K 棒（見 `quotes/align.py`）。
L3 / L4 的標頭都沒說明 MC 的實際規則，最快的驗證方式是跑完看筆數。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from txfcore.engine.accounting import ClosedTrade, Ledger, trade_cost
from txfcore.engine.fill_mc12 import DEFAULT_POLICY, FillPolicy, MC12FillModel
from txfcore.engine.position import PositionBook
from txfcore.instruments.spec import Instrument
from txfcore.lineage.stamp import Lineage
from txfcore.quotes.align import AlignPolicy, MultiStream, bar_close_dt
from txfcore.runtime.backtest import BacktestResult, FixedLotRiskGate
from txfcore.strategies.base import MarketView, PositionView, Strategy
from txfcore.timing.clock import BarClock
from txfcore.tradecal.gates import evaluate
from txfcore.types.bar import Bar
from txfcore.types.orders import MarketPosition, Side, SizedOrder


class MultiStreamRunner:
    """Data1 驅動，Data2 / Data3 跟隨。"""

    def __init__(
        self,
        strategy: Strategy,
        instrument: Instrument,
        policy: FillPolicy = DEFAULT_POLICY,
        lineage: Lineage | None = None,
        warmup_bars: int = 100,
        align_policy: str = AlignPolicy.CLOSED_ONLY,
    ) -> None:
        self.strategy = strategy
        self.instrument = instrument
        self.fill_model = MC12FillModel(policy)
        self.risk = FixedLotRiskGate(instrument.default_lots)
        self.lineage = lineage
        self.warmup_bars = warmup_bars
        self.align_policy = align_policy

    def run(
        self, d1: list[Bar], d2: list[Bar], d3: list[Bar]
    ) -> BacktestResult:
        s = self.strategy
        name = s.config.name
        state = s.initial_state()
        ms = MultiStream(self.align_policy)
        for b in d2:
            ms.feed_slow("data2", b)
        for b in d3:
            ms.feed_slow("data3", b)

        book = PositionBook()
        clock = BarClock()
        ledger = Ledger(self.instrument)
        res = BacktestResult(strategy=name, ledger=ledger, lineage=self.lineage,
                             policy=self.fill_model.policy.name)

        pending: list[SizedOrder] = []
        protective = None
        entry_leg: tuple[str, float, int, int] | None = None
        entry_bar: tuple[int, int] | None = None   # 本輪部位是哪一根開的

        for bar in d1:
            clock.advance_to(bar_close_dt(bar))
            pos = book.get(name)
            pos.advance_bar()          # 必須在撮合之前，見 test_runner_ages_position_before_filling

            if pending or protective:
                fills = self.fill_model.fill(pending, bar)
                if protective and not pos.is_flat:
                    side = (Side.SELL if pos.direction is MarketPosition.LONG
                            else Side.BUY_TO_COVER)
                    sign = -1 if pos.direction is MarketPosition.LONG else 1
                    stop_px = pos.entry_price + sign * protective.distance
                    ef = self.fill_model.engine_stop_fill(
                        stop_px, side, pos.current_contracts, bar, name)
                    has_custom_exit = any(
                        f.order.intent.side in (Side.SELL, Side.BUY_TO_COVER)
                        for f in fills
                    )
                    if ef and (self.fill_model.policy.engine_stop_first
                               or not has_custom_exit):
                        fills = [ef]
                        res.engine_stop_exits += 1

                # **OCO 語意**：L3 常態同時掛 TP 限價 + SL 停價，
                # L5 每腿各一組。一張成交，同組其餘作廢。
                #
                # L2 / L4 靠 ExitFired 保證單根單張，所以這段對它們沒有影響
                # （fills 最多一張）。但 L3 / L5 需要它。
                #
                # 成交順序由 FillPolicy.intrabar 決定 —— MC 從 OHLC 推不出
                # 誰先，所以那是可切換的假設，不是常數。
                closed_this_bar = False
                for f in fills:
                    side = f.order.intent.side
                    if side in (Side.BUY, Side.SELL_SHORT):
                        # **L5 的雙腿**：Bot 與 Mid 都在空手時掛出，
                        # 所以同一根 K 棒可以兩張都成交。允許同根加腿，
                        # 但不允許跨根加倉（那不是任何一支的行為）。
                        same_bar = entry_bar == (bar.mc_date, bar.mc_time)
                        if not pos.is_flat and not same_bar:
                            continue
                        pos.open_leg(f.order.intent.label, f.price, f.quantity,
                                     bar.mc_date, bar.mc_time, side)
                        if entry_leg is None or not same_bar:
                            entry_leg = (f.order.intent.label, f.price,
                                         bar.mc_date, bar.mc_time)
                        entry_bar = (bar.mc_date, bar.mc_time)
                    else:
                        if pos.is_flat or entry_leg is None or closed_this_bar:
                            continue          # OCO：同根已成交過出場單
                        lbl, epx, ed, et = entry_leg
                        qty = min(f.quantity, pos.current_contracts)
                        if f.order.intent.from_entry:
                            leg = pos.leg(f.order.intent.from_entry)
                            if leg is None:
                                continue          # 該腿不存在，此單作廢
                            qty = min(qty, leg.quantity)
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
                        res.oco_cancelled += len(fills) - 1 if len(fills) > 1 else 0
                        closed_this_bar = True
                        if pos.is_flat:
                            entry_leg = None
                            entry_bar = None
                pending = []
                entry_leg, protective = self._same_bar_stop(
                    bar, pos, entry_leg, protective, ledger, res, name)

            ms.push_driver(bar)
            res.bars_processed += 1
            if len(ms.driver) < self.warmup_bars or not ms.all_ready("data2", "data3"):
                continue

            view = MarketView(
                data1=ms.driver,
                data2=ms.slow("data2").series,
                data3=ms.slow("data3").series,
                position=PositionView(
                    market_position=pos.direction, entry_price=pos.entry_price,
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

    def _same_bar_stop(self, bar, pos, entry_leg, protective, ledger, res, name):
        """進場那根立刻被停損打掉。

        **MC 允許這件事** —— L1 的 V2.9 取證明確記錄了 12 筆 same-bar deaths。

        我原本的 runner 讓它**結構上不可能**：引擎停損檢查發生在進場填入之前，
        所以新開的部位在同一根裡永遠不會被檢查。後果是部位跑得比 MC 久、
        PF 偏高 —— 而實測我的 PF 在 L2 與 L4 都高於 MC。

        由 `FillPolicy.allow_same_bar_exit` 控制。關掉即回到舊行為。
        """
        if not self.fill_model.policy.allow_same_bar_exit:
            return entry_leg, protective
        if protective is None or pos.is_flat or entry_leg is None:
            return entry_leg, protective
        lbl, epx, ed, et = entry_leg
        # 只處理「本根才進場」的部位
        if (ed, et) != (bar.mc_date, bar.mc_time):
            return entry_leg, protective
        side = (Side.SELL if pos.direction is MarketPosition.LONG
                else Side.BUY_TO_COVER)
        sign = -1 if pos.direction is MarketPosition.LONG else 1
        stop_px = pos.entry_price + sign * protective.distance
        ef = self.fill_model.engine_stop_fill(
            stop_px, side, pos.current_contracts, bar, name)
        if ef is None:
            return entry_leg, protective
        qty = pos.current_contracts
        direction = pos.direction
        pos.close(qty)
        t = ClosedTrade(
            strategy=name, entry_label=lbl, exit_label=ef.label,
            direction=direction, quantity=qty,
            entry_price=epx, exit_price=ef.price,
            entry_date=ed, entry_time=et,
            exit_date=bar.mc_date, exit_time=bar.mc_time,
            cost=trade_cost(self.instrument, epx, ef.price, qty),
        )
        res.trades.append(t)
        ledger.record(t)
        res.engine_stop_exits += 1
        res.same_bar_exits = getattr(res, "same_bar_exits", 0) + 1
        pos.prev_position_profit = t.net_ntd(self.instrument)
        return None, protective
