"""多資料流對齊 —— `of Data2` / `of Data3` 的語意。

L3 / L4 讀 `Highest(High, 15)[1] of Data2`：在 15M 的 K 棒上，
讀 60M 流的「前一根」。問題是**哪一根算前一根**。

```
60M 網格    09:45   10:45   11:45   12:45   13:45
15M 網格    0900 0915 0930 0945 1000 1015 1030 1045 ...
```

在 15M 的 09:00，60M 的 09:45 那根**還在形成中**。

**本模組採最保守的規則：Data2 只暴露已收盤的 K 棒。**

    Data2 當根 = 最後一根 close_at <= 當前 Data1 的 close_at

所以 15M 的 09:00 看到的 Data2 當根是夜盤 05:00 那根，`[1]` 是 04:00。
到了 15M 的 09:45（與 60M 的 09:45 同時收盤），Data2 當根才變成 09:45。

**為什麼保守**：任何比這更寬鬆的規則都會讀到尚未收盤的 K 棒，
那是未來函數。若 MC 的行為更寬鬆，對帳會顯示筆數不同——
**那是可觀測的，比默默讀到未來資料安全。**

> L3 / L4 的標頭都沒說明對齊規則。
> 最快的驗證方式是跑完看筆數（L4 應為 79 筆），不是猜。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from txfcore.types.bar import Bar, BarSeries
from txfcore.types.mctime import mc_date_to_date, mc_time_to_time


def bar_close_dt(bar: Bar) -> datetime:
    return datetime.combine(mc_date_to_date(bar.mc_date), mc_time_to_time(bar.mc_time))


class AlignPolicy:
    """對齊規則。**MC 的實際規則未知**，所以做成可切換的。

    CLOSED_ONLY   只暴露已收盤的 K 棒。最保守，任何更寬鬆的都會讀到未形成的
    INCLUDE_FORMING   把形成中的那一根也當成當根。等同 MC 的 `of Data2` 若
                      MC 允許讀取尚未收盤的較慢流 K 棒
    """

    CLOSED_ONLY = "closed_only"
    INCLUDE_FORMING = "include_forming"


@dataclass(slots=True)
class AlignedStream:
    """一條較慢的資料流，對齊到較快的驅動流。

    `CLOSED_ONLY` 下 `series` 只包含**已收盤**的 K 棒，
    所以策略讀 `[0]` 就是 MC 的 `of Data2` 當根，讀 `[1]` 就是前一根。
    尚未收盤的那一根放在 `forming`，策略讀不到它。

    `INCLUDE_FORMING` 下形成中的那一根會被暫時推入 series，
    下一次 `advance_to` 時撤回再重推。**實測顯示這是錯的規則**——
    L4 從 83 筆掉到 44 筆，而 MC 是 79 筆。
    """

    name: str
    series: BarSeries = field(default_factory=lambda: BarSeries("aligned"))
    forming: Bar | None = None
    policy: str = AlignPolicy.CLOSED_ONLY
    _pending: list[Bar] = field(default_factory=list)
    _forming_pushed: bool = False

    def feed(self, bar: Bar) -> None:
        """收到一根較慢流的 K 棒。先進待決區，等驅動流推進才放行。"""
        self._pending.append(bar)

    def advance_to(self, driver_close: datetime) -> int:
        """驅動流推進到 `driver_close`。放行所有已收盤的較慢流 K 棒。

        回傳這次放行了幾根。
        """
        released = 0
        if self._forming_pushed:
            self.series.pop()          # 撤回上一根暫定的形成中 K 棒
            self._forming_pushed = False
        while self._pending and bar_close_dt(self._pending[0]) <= driver_close:
            self.series.push(self._pending.pop(0))
            released += 1
        self.forming = self._pending[0] if self._pending else None
        if self.policy == AlignPolicy.INCLUDE_FORMING and self.forming is not None:
            self.series.push(self.forming)
            self._forming_pushed = True
        return released

    @property
    def ready(self) -> bool:
        return len(self.series) > 0

    def __len__(self) -> int:
        return len(self.series)


class MultiStream:
    """Data1 驅動，Data2 / Data3 跟隨。

    用法：

        ms = MultiStream()
        ms.feed_slow("data2", bar60)      # 較慢流先餵進來（可亂序時間但需遞增）
        ms.feed_slow("data3", barD)
        ms.push_driver(bar15)              # 驅動流推進，自動對齊
        view_d2 = ms.slow("data2").series  # 只含已收盤的
    """

    def __init__(self, policy: str = AlignPolicy.CLOSED_ONLY) -> None:
        self.driver = BarSeries("data1")
        self.policy = policy
        self._slow: dict[str, AlignedStream] = {}

    def register(self, name: str) -> AlignedStream:
        if name not in self._slow:
            self._slow[name] = AlignedStream(name, policy=self.policy)
        return self._slow[name]

    def feed_slow(self, name: str, bar: Bar) -> None:
        self.register(name).feed(bar)

    def push_driver(self, bar: Bar) -> dict[str, int]:
        """推進驅動流一根。回傳各較慢流這次放行了幾根。"""
        self.driver.push(bar)
        close = bar_close_dt(bar)
        return {n: s.advance_to(close) for n, s in self._slow.items()}

    def slow(self, name: str) -> AlignedStream:
        return self.register(name)

    def all_ready(self, *names: str) -> bool:
        """全部較慢流都有至少一根已收盤的 K 棒。暖機判斷用。"""
        return all(self.register(n).ready for n in names)
