"""趨勢濾網。語意不同的各自一個類別（規則手冊 R3），不用參數硬湊。"""
from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.indicators.core import average
from txfcore.types.mctime import DayOfWeek, day_of_week


@dataclass(slots=True)
class WeeklySmaFilter:
    """L2：每週五 12:45 那根 60 分 K 收盤存一筆，算 N 週均線。

    觸發點是「週五 12:45 之後的第一根」，存的是 Close[1]。暖機未滿 N 週時 ok = False。
    """
    n: int
    sample_time: int = 1245
    closes: list[float] = field(default_factory=lambda: [0.0] * 21)
    count: int = 0
    total: float = 0.0
    ok: bool = False

    def update(self, bars) -> None:
        if len(bars) < 2:
            return
        prev = bars[1]
        if not (prev.mc_time == self.sample_time and day_of_week(prev.mc_date) is DayOfWeek.FRI):
            return
        n = self.n
        if len(self.closes) < n + 1:
            self.closes.extend([0.0] * (n + 1 - len(self.closes)))
        for i in range(n, 1, -1):
            self.closes[i] = self.closes[i - 1]
        self.closes[1] = prev.close
        if self.count < n:
            self.count += 1
        self.total = sum(self.closes[1:self.count + 1])
        self.ok = self.count >= n and self.closes[1] < self.total / n

    @property
    def ready(self) -> bool:
        return self.count >= self.n

    @property
    def sma(self) -> float:
        return self.total / self.n


@dataclass(slots=True)
class DailyMaBlock:
    """L4：日線趨勢向上就不做空。A ＝ 收盤 > MA慢 且 MA慢 不比「上一根 15 分 K 時」低；B ＝ MA快 > MA慢。

    F6（照 .pla 保留）：MA慢[1] 是上一根 15 分 K 計算時的值，不是前一根日 K。
    mode：0 ＝ A 或 B；1 ＝ A 且 B；2 ＝ 只看 A；3 ＝ 不封鎖。
    """
    slow: float = 0.0
    slow_prev: float = 0.0

    def update(self, daily_close, fast_len: int, slow_len: int, mode: int = 0) -> bool:
        fast = average(daily_close, fast_len)
        self.slow_prev = self.slow
        self.slow = average(daily_close, slow_len)
        a = daily_close[0] > self.slow and self.slow >= self.slow_prev
        b = fast > self.slow
        if mode == 1:
            return a and b
        if mode == 2:
            return a
        if mode == 3:
            return False
        return a or b


def below_ma(close_series, length: int) -> bool:
    """收盤在 N 根均線之下（L4 的 60 分趨勢方向 ＝ -1）。"""
    return close_series[0] < average(close_series, length)
