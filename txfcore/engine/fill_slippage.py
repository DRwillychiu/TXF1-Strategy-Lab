"""滑價包裝層。

**`fill_mc12` 的身分是「MC 的樂觀假設：觸價即成交、零滑價」。
把滑價塞進去會污染它的定位**——它就不再是 MC 的複製品，
而對帳的基準也就消失了。

所以滑價是**套在外面的一層**：

```
MC12FillModel          回答「誰觸發、成交在哪、順序如何」
  └ SlippageFill       把成交價往不利方向推 N 點
```

兩層各自可切換，而且 `policy` 名稱會同時顯示兩層的設定，
**報告上看得出這份數字是哪一組假設跑出來的**。
"""

from __future__ import annotations

from dataclasses import replace

from txfcore.costs.slippage import OFF, SlippageModel
from txfcore.engine.fill_mc12 import Fill, MC12FillModel
from txfcore.instruments.spec import Instrument
from txfcore.types.bar import Bar
from txfcore.types.orders import OrderType, Side, SizedOrder


class SlippageFill:
    """把任一成交模型包起來，對成交價加上不利滑價。

    **引擎停損（`is_engine_stop`）也要加**——它同樣是一張真實的單，
    在流動性差的時候一樣會滑。
    """

    def __init__(self, inner: MC12FillModel, inst: Instrument,
                 model: SlippageModel = OFF) -> None:
        self.inner = inner
        self.inst = inst
        self.model = model

    @property
    def policy(self):
        return self.inner.policy

    @property
    def name(self) -> str:
        return f"{self.inner.name}+{self.model.name}"

    def _slip(self, f: Fill) -> Fill:
        if not self.model.enabled:
            return f
        px = self.model.adjust(f.price, f.order.intent.side, self.inst,
                               f.order.intent.order_type)
        if px == f.price:
            return f
        return replace(f, price=px,
                       policy=f"{f.policy}+{self.model.name}")

    def fill(self, orders: list[SizedOrder], bar: Bar) -> list[Fill]:
        return [self._slip(f) for f in self.inner.fill(orders, bar)]

    def engine_stop_fill(self, stop_price: float, side: Side, qty: int,
                         bar: Bar, strategy: str) -> Fill | None:
        f = self.inner.engine_stop_fill(stop_price, side, qty, bar, strategy)
        return None if f is None else self._slip(f)
