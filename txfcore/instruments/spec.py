"""商品主檔。

`BigPointValue` `TickSize` `MinMove` `PriceScale` 是**商品屬性，不是策略屬性**。
同一支策略跑大台或微台，這些值不同但策略邏輯不變 —— 所以它們不能掛在
StrategyConfig 上。

回測資金基準（裁決 2026-09-06）：
    微台 2 口 -> 300,000
    大台 2 口 -> 2,000,000
兩者的曝險比 = 點值比 = 20 倍，資金比 6.67 倍。
**同一份回測跑兩個商品，MDD 百分比會不同，這是設計上的，不是 bug。**
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Instrument:
    code: str
    name: str
    big_point_value: float   # MC 的 BigPointValue，每點新台幣
    min_move: int            # MC 的 MinMove
    price_scale: int         # MC 的 PriceScale
    fee_per_side: float      # 每口每邊手續費
    default_lots: int        # 回測固定口數
    backtest_capital: float  # 回測期初資金（MDD 百分比的分母基準）

    @property
    def tick_size(self) -> float:
        """L5 的 v_TickSize = MinMove / PriceScale。"""
        return self.min_move / self.price_scale

    def points_to_ntd(self, points: float, lots: int = 1) -> float:
        return points * self.big_point_value * lots

    def contract_value(self, price: float) -> float:
        return price * self.big_point_value


TXF = Instrument(
    code="TXF", name="台指期（大台）",
    big_point_value=200.0, min_move=1, price_scale=1,
    fee_per_side=32.0, default_lots=2, backtest_capital=2_000_000.0,
)

MXF = Instrument(
    code="MXF", name="小型台指",
    big_point_value=50.0, min_move=1, price_scale=1,
    fee_per_side=15.0, default_lots=2, backtest_capital=500_000.0,
)

TMF = Instrument(
    code="TMF", name="微型台指",
    big_point_value=10.0, min_move=1, price_scale=1,
    fee_per_side=12.0, default_lots=2, backtest_capital=300_000.0,
)

INSTRUMENTS: dict[str, Instrument] = {i.code: i for i in (TXF, MXF, TMF)}


def get(code: str) -> Instrument:
    if code not in INSTRUMENTS:
        raise KeyError(f"未知商品 {code!r}，已知：{sorted(INSTRUMENTS)}")
    return INSTRUMENTS[code]
