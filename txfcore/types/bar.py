"""K 棒與序列型別。

規劃書層 1 的核心要求：**未來資料不是被測出來的，是寫不出來的。**

`Series[i]` 的語意與 PowerLanguage 相同：i = 0 是當根，i = 1 是前一根。
負數索引會拋 `FutureDataError`，所以「讀取尚未發生的 K 棒」在型別上不可能，
不需要靠不變量在事後抓。這把不變量 #13（決策時可計算性）從斷言升級為保證。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class FutureDataError(LookupError):
    """試圖讀取決策當下尚不存在的資料。"""


@dataclass(frozen=True, slots=True)
class Bar:
    """一根已收盤的 K 棒。

    mc_date / mc_time 為 MC 戳記（見 types.mctime）。
    三戳記中的 event_time 即 (mc_date, mc_time)；receipt_time 與
    decision_time 由報價層填入，回測時三者相等。
    """

    mc_date: int
    mc_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    # 由幾筆 tick 合成。回測讀 MC 匯出的 1 分 K 時為 None。
    tick_count: int | None = None
    # 是否為斷線後回補的 K 棒（規劃書層 1 要求可區分）。
    is_backfilled: bool = False

    @property
    def range(self) -> float:
        return self.high - self.low


class Series:
    """唯讀的反向索引序列。index 0 = 最新（當根）。

    內部以「舊到新」的 list 儲存，對外以 PowerLanguage 的偏移語意存取。
    """

    __slots__ = ("_data",)

    def __init__(self, data: Sequence[float] | None = None) -> None:
        self._data: list[float] = list(data) if data else []

    def push(self, value: float) -> None:
        self._data.append(value)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, offset: int) -> float:
        if offset < 0:
            raise FutureDataError(
                f"offset={offset} 指向未來資料。PowerLanguage 的偏移只能 >= 0，"
                f"0 = 當根、1 = 前一根。"
            )
        if offset >= len(self._data):
            raise LookupError(
                f"offset={offset} 超出可用歷史（目前 {len(self._data)} 根）。"
                f"這通常代表指標預熱期不足。"
            )
        return self._data[-1 - offset]

    def available(self, offset: int) -> bool:
        return 0 <= offset < len(self._data)

    def window(self, length: int, offset: int = 0) -> list[float]:
        """取 offset 起算、往回 length 根。window(3, 1) = [1], [2], [3]。"""
        if length <= 0:
            raise ValueError("length 必須 > 0")
        return [self[offset + i] for i in range(length)]


class BarSeries:
    """一條 K 棒流（對應 MC 的 Data1 / Data2 / Data3）。

    同時維護 O/H/L/C 四條 Series，讓指標可以直接吃。
    """

    __slots__ = ("name", "bars", "open", "high", "low", "close")

    def __init__(self, name: str) -> None:
        self.name = name
        self.bars: list[Bar] = []
        self.open = Series()
        self.high = Series()
        self.low = Series()
        self.close = Series()

    def push(self, bar: Bar) -> None:
        self.bars.append(bar)
        self.open.push(bar.open)
        self.high.push(bar.high)
        self.low.push(bar.low)
        self.close.push(bar.close)

    def __len__(self) -> int:
        return len(self.bars)

    def __getitem__(self, offset: int) -> Bar:
        if offset < 0:
            raise FutureDataError(f"offset={offset} 指向未來 K 棒。")
        if offset >= len(self.bars):
            raise LookupError(f"offset={offset} 超出可用歷史（{len(self.bars)} 根）。")
        return self.bars[-1 - offset]

    @property
    def current(self) -> Bar:
        return self[0]
