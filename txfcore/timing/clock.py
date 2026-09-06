"""第三顆插頭：時鐘。

回測讀 K 棒時間戳，即時讀系統時鐘。
**策略層永不直接讀系統時間**——那會讓同一份程式碼在兩端行為不同。

三戳記：
    event_time    交易所時間（K 棒收盤時刻 / tick 的交易所戳記）
    receipt_time  系統收到的時間
    decision_time 策略讀取的時間

策略只能看到 receipt_time <= decision_time 的資料。回測時三者相等。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from txfcore.types.mctime import date_to_mc_date, time_to_mc_time


@dataclass(frozen=True, slots=True)
class Stamps:
    event_time: datetime
    receipt_time: datetime
    decision_time: datetime

    @property
    def latency_ms(self) -> float:
        return (self.receipt_time - self.event_time).total_seconds() * 1000

    def visible_at(self, now: datetime) -> bool:
        return self.receipt_time <= now


class BarClock:
    """回測時鐘。時間由 K 棒推動，不由牆上時鐘推動。"""

    def __init__(self) -> None:
        self._now: datetime | None = None

    def advance_to(self, dt: datetime) -> None:
        if self._now is not None and dt < self._now:
            raise ValueError(f"時鐘不得倒退：{self._now} -> {dt}")
        self._now = dt

    def now(self) -> datetime:
        if self._now is None:
            raise RuntimeError("時鐘尚未被任何 K 棒推動")
        return self._now

    def mc_stamp(self) -> tuple[int, int]:
        n = self.now()
        return date_to_mc_date(n.date()), time_to_mc_time(n.time())

    def stamps(self, event_time: datetime) -> Stamps:
        return Stamps(event_time, event_time, event_time)


class SystemClock:
    """即時時鐘。附 NTP 漂移檢查——漂移超門檻即應停止新進場。"""

    def __init__(self, max_drift_ms: float = 500.0) -> None:
        self.max_drift_ms = max_drift_ms
        self._reference_offset = timedelta(0)

    def now(self) -> datetime:
        return datetime.now() + self._reference_offset

    def mc_stamp(self) -> tuple[int, int]:
        n = self.now()
        return date_to_mc_date(n.date()), time_to_mc_time(n.time())

    def drift_ok(self, exchange_time: datetime) -> bool:
        drift = abs((self.now() - exchange_time).total_seconds() * 1000)
        return drift <= self.max_drift_ms

    def stamps(self, event_time: datetime) -> Stamps:
        now = self.now()
        return Stamps(event_time, now, now)
