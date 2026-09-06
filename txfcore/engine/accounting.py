"""Fill → 部位 → 權益曲線。

規劃書指出的斷裂：

    Fill  →  ???  →  metrics/drawdown.equity_curve()

`equity_curve()` 吃一串數字，但沒有模組把成交轉成那串數字。
本模組補上，並處理「含未平倉損益」需要的 mark-to-market。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from txfcore.costs.fees import round_trip_cost
from txfcore.instruments.spec import Instrument
from txfcore.types.mctime import trading_day
from txfcore.types.orders import MarketPosition


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    strategy: str
    entry_label: str
    exit_label: str
    direction: MarketPosition
    quantity: int
    entry_price: float
    exit_price: float
    entry_date: int
    entry_time: int
    exit_date: int
    exit_time: int
    cost: float

    @property
    def gross_points(self) -> float:
        sign = 1 if self.direction is MarketPosition.LONG else -1
        return (self.exit_price - self.entry_price) * sign

    def gross_ntd(self, inst: Instrument) -> float:
        return inst.points_to_ntd(self.gross_points, self.quantity)

    def net_ntd(self, inst: Instrument) -> float:
        return self.gross_ntd(inst) - self.cost


@dataclass(slots=True)
class Ledger:
    """一支策略的帳。逐日結算成權益曲線。"""

    instrument: Instrument
    initial_capital: float = 0.0
    trades: list[ClosedTrade] = field(default_factory=list)
    _daily: dict[date, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.initial_capital == 0.0:
            # 裁決：微台 2 口 30 萬、大台 2 口 200 萬
            self.initial_capital = self.instrument.backtest_capital

    def record(self, t: ClosedTrade) -> None:
        self.trades.append(t)
        d = trading_day(t.exit_date, t.exit_time)
        self._daily[d] = self._daily.get(d, 0.0) + t.net_ntd(self.instrument)

    def mark_open(self, d: date, unrealised_ntd: float) -> None:
        """未平倉市值。權益曲線含未平倉損益，取該交易日最後一筆成交價。

        只算已實現的話，浮虧部位在砍掉之前完全看不出來，
        但期間承受的風險是真實的。
        """
        self._daily[d] = self._daily.get(d, 0.0) + unrealised_ntd

    def daily_pnl(self) -> tuple[list[date], list[float]]:
        """逐日損益，依交易日排序。組合曲線就是把五支的這個逐日相加。"""
        days = sorted(self._daily)
        return days, [self._daily[d] for d in days]

    def equity(self) -> list[float]:
        _, pnl = self.daily_pnl()
        out = [self.initial_capital]
        run = self.initial_capital
        for x in pnl:
            run += x
            out.append(run)
        return out


def trade_cost(inst: Instrument, entry_price: float, exit_price: float, lots: int) -> float:
    """手續費 + 期交稅，進出場分開算。

    稅按契約金額課，隨價格變動——不是常數。
    實戰試算表用固定 42 是扁平近似值。
    """
    return round_trip_cost(inst, entry_price, exit_price, lots)
