"""滑價模型。

**裁決 2026-09-09：**

```
點數       5 tick = 5 點/邊/口。三商品皆同
           大台 5 點 = 1,000 元，與 CLAUDE.md 的「1,000 NTD/邊/口」吻合
           所以原意確實是點數，1,000 只是它在大台的金額表示
方向       一律不利方向
單型       **全部單型都加，含限價單**
開關       做成可切換，預設關閉，讓兩組數字可並排對照
```

## 為什麼限價單也加

限價單理論上不會有不利滑價——要嘛成交在限價，要嘛不成交。
**但這裡刻意加，理由是壓力測試**：

> 假設市場流動性非常差的嚴苛情況下，策略是否仍然賺錢。

**在最嚴苛的假設下仍然賺錢，才是可信的。**

## 成本量級

```
來回 = 5 點 × 2 邊 × 2 口 = 20 點

TMF     200 元/來回
MXF   1,000 元/來回
TXF   4,000 元/來回
```

對照實測的平均獲利：**L5 139 點（滑價佔 14%）· L3 159 點（12.6%）**。
**這會顯著改變所有績效數字，所以必須可切換、可對照。**

## 這是設定值，不是量測值

`is_measured = False`。真實滑價要從實戰紀錄量（訊號價 vs 成交價），
量到之前，**任何用它算出的數字都要標註**。
"""

from __future__ import annotations

from dataclasses import dataclass

from txfcore.instruments.spec import Instrument
from txfcore.types.orders import OrderType, Side

DEFAULT_TICKS = 5           # 5 tick = 5 點。三商品皆同


@dataclass(frozen=True, slots=True)
class SlippageModel:
    """滑價設定。**做成函數不寫死，之後可用實測值替換。**"""

    enabled: bool = False           # 預設關閉，讓兩組數字可對照
    ticks_per_side: float = DEFAULT_TICKS
    apply_to_limit: bool = True     # **限價單也加**（壓力測試）
    is_measured: bool = False       # 目前是設定值，不是量測值

    @property
    def name(self) -> str:
        if not self.enabled:
            return "slip=off"
        return (f"slip={self.ticks_per_side:g}tick"
                f"{'|limit' if self.apply_to_limit else '|nolimit'}"
                f"{'|measured' if self.is_measured else '|assumed'}")

    def points(self, inst: Instrument, order_type: OrderType) -> float:
        """該筆訂單的滑價點數。**回傳正數，方向由 `adjust` 決定。**"""
        if not self.enabled:
            return 0.0
        if order_type is OrderType.LIMIT and not self.apply_to_limit:
            return 0.0
        return self.ticks_per_side * inst.tick_size

    def adjust(self, price: float, side: Side, inst: Instrument,
               order_type: OrderType) -> float:
        """把訊號價調整成含滑價的成交價。**一律不利方向。**

        ```
        買進（BUY / BUY_TO_COVER）   成交價 = 訊號價 + 滑價
        賣出（SELL / SELL_SHORT）    成交價 = 訊號價 − 滑價
        ```
        """
        p = self.points(inst, order_type)
        if p == 0.0:
            return price
        buying = side in (Side.BUY, Side.BUY_TO_COVER)
        return price + p if buying else price - p

    def round_trip_points(self, inst: Instrument, lots: int = 1) -> float:
        """來回總滑價點數（兩邊 × 口數）。"""
        return self.points(inst, OrderType.MARKET) * 2 * lots

    def round_trip_money(self, inst: Instrument, lots: int = 1) -> float:
        return self.round_trip_points(inst, lots) * inst.big_point_value


OFF = SlippageModel(enabled=False)
STRESS = SlippageModel(enabled=True, ticks_per_side=DEFAULT_TICKS,
                       apply_to_limit=True)

# 對照組。**兩組都跑，並排顯示影響。**
CANDIDATES: tuple[SlippageModel, ...] = (OFF, STRESS)
