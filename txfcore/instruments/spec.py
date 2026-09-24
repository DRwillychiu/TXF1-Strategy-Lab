"""商品主檔。

`BigPointValue` `TickSize` `MinMove` `PriceScale` 是**商品屬性，不是策略屬性**。
同一支策略跑大台或微台，這些值不同但策略邏輯不變 —— 所以它們不能掛在
StrategyConfig 上。

**資金不在這裡。** 資金配置是 `instruments/capital.py` 的事（裁決 2026-09-08：
名目每支 · 雙帳戶 · 三商品等比例）。

> 2026-09-10 移除 `backtest_capital` 欄位。它是 9/6 的舊裁決，
> 與 capital.py 並存導致**同一份資料跑不同工具會得到不同的百分比**。
> 單一來源，不可能再岔開。

手續費（2026-09-10 確認為券商實際費率）：
    TXF 32 · MXF 15 · TMF 12　元/口/邊
期交稅由 `costs/fees.py` 依契約金額計算，不在這裡。
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
    fee_per_side: float      # 每口每邊手續費。**券商實際費率，2026-09-10 確認**
    default_lots: int        # 回測固定口數

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
    fee_per_side=32.0, default_lots=2,
)

MXF = Instrument(
    code="MXF", name="小型台指",
    big_point_value=50.0, min_move=1, price_scale=1,
    fee_per_side=15.0, default_lots=2,
)

TMF = Instrument(
    code="TMF", name="微型台指",
    big_point_value=10.0, min_move=1, price_scale=1,
    fee_per_side=12.0, default_lots=2,
)

INSTRUMENTS: dict[str, Instrument] = {i.code: i for i in (TXF, MXF, TMF)}


def get(code: str) -> Instrument:
    if code not in INSTRUMENTS:
        raise KeyError(f"未知商品 {code!r}，已知：{sorted(INSTRUMENTS)}")
    return INSTRUMENTS[code]
