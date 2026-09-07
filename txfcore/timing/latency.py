"""延遲模型。

**外部借鑑：hftbacktest。** 它把延遲分成兩類分別建模——feed latency
（行情到達）與 order latency（下單往返）——並且**從實盤錄下真實延遲，
在回測時重放**（`intp_order_latency` 吃的就是實盤錄的延遲檔）。
其 roadmap 更進一步：下單、改單、撤單、回報、成交、部位推送
各自可以有不同的延遲。

我們原本三戳記（event / receipt / decision）型別上定義了，
**但沒有任何東西在填它們**。這個模組把它們接上。

**為什麼對我們也重要**，即使我們不是 HFT：

    mc12 模式    延遲 = 0。MC 的 next bar at market 就是在下一根開盤成交
    live 模式    「立即下單」到底是多久？沒有模型，這句話無法驗證
    v2  模式     若要縮短觸發到下單的距離，得先知道現在是多少

**而且我們有辦法量到真實值** —— MC12 正在實盤自動下單，
下單時刻與成交回報時刻的差就是 order latency。
這與 hftbacktest 的做法完全相同：**從實盤錄，回測時重放。**
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class LatencyModel(Protocol):
    """延遲來源。回測與實盤各有實作。"""

    @property
    def name(self) -> str: ...

    def feed_latency(self, event_time: datetime) -> timedelta:
        """行情從交易所發出到本地收到。決定策略「何時看得到」。"""
        ...

    def order_latency(self, sent_at: datetime) -> timedelta:
        """下單送出到交易所接受。決定「訊號到掛單」的距離。"""
        ...

    def response_latency(self, sent_at: datetime) -> timedelta:
        """交易所回報回到本地。決定「成交到系統知道」的距離。"""
        ...


@dataclass(frozen=True, slots=True)
class ZeroLatency:
    """mc12 對帳模式。**必須是零**——MC 沒有延遲概念，加了就對不上帳。"""

    name: str = "zero"

    def feed_latency(self, event_time: datetime) -> timedelta:
        return timedelta(0)

    def order_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(0)

    def response_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(0)


@dataclass(frozen=True, slots=True)
class FixedLatency:
    """live 模式的粗略近似。**在量到真實值之前的暫用品。**

    預設值是猜的，不是量的——所以 `is_measured` 為 False，
    任何用它算出來的風險數字都應標註為未經量測。
    """

    feed_ms: float = 50.0
    order_ms: float = 120.0
    response_ms: float = 80.0
    name: str = "fixed"
    is_measured: bool = False

    def feed_latency(self, event_time: datetime) -> timedelta:
        return timedelta(milliseconds=self.feed_ms)

    def order_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(milliseconds=self.order_ms)

    def response_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(milliseconds=self.response_ms)


@dataclass(slots=True)
class MeasuredLatency:
    """從實盤錄下的延遲，回測時依時間內插重放。

    這是 hftbacktest 的做法：延遲不是常數，會隨時段、負載、
    網路狀況變動。用固定值會系統性低估最壞情況。

    **資料來源**：MC12 正在實盤自動下單，下單時刻與回報時刻的差
    就是樣本。錄下來就能用。
    """

    samples: list[tuple[datetime, float, float, float]] = field(default_factory=list)
    name: str = "measured"
    is_measured: bool = True

    def __post_init__(self) -> None:
        self.samples.sort(key=lambda s: s[0])
        self._keys = [s[0] for s in self.samples]

    _keys: list[datetime] = field(default_factory=list, repr=False)

    def add(self, at: datetime, feed_ms: float, order_ms: float, resp_ms: float) -> None:
        self.samples.append((at, feed_ms, order_ms, resp_ms))
        self.samples.sort(key=lambda s: s[0])
        self._keys = [s[0] for s in self.samples]

    def _nearest(self, at: datetime) -> tuple[float, float, float]:
        if not self.samples:
            raise LookupError("沒有延遲樣本。未量測前不得用於風險判斷。")
        i = bisect.bisect_left(self._keys, at)
        if i == 0:
            _, f, o, r = self.samples[0]
        elif i >= len(self.samples):
            _, f, o, r = self.samples[-1]
        else:
            before, after = self.samples[i - 1], self.samples[i]
            take = before if (at - before[0]) <= (after[0] - at) else after
            _, f, o, r = take
        return f, o, r

    def feed_latency(self, event_time: datetime) -> timedelta:
        return timedelta(milliseconds=self._nearest(event_time)[0])

    def order_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(milliseconds=self._nearest(sent_at)[1])

    def response_latency(self, sent_at: datetime) -> timedelta:
        return timedelta(milliseconds=self._nearest(sent_at)[2])

    def percentile(self, which: str, q: float) -> float:
        """延遲分布的分位數。風險判斷要用 p99，不是平均。"""
        idx = {"feed": 1, "order": 2, "response": 3}[which]
        vals = sorted(s[idx] for s in self.samples)
        if not vals:
            raise LookupError("沒有延遲樣本")
        k = min(int(q * (len(vals) - 1)), len(vals) - 1)
        return vals[k]


def stamps_with_latency(
    event_time: datetime, model: LatencyModel
) -> tuple[datetime, datetime]:
    """(receipt_time, decision_time)。

    策略只能看到 `receipt_time <= decision_time` 的資料——
    這條在 `types/bar.Series` 已經由型別保證，本函數負責產生正確的戳記。
    """
    receipt = event_time + model.feed_latency(event_time)
    return receipt, receipt
