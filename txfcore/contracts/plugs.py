"""三顆插頭 —— 全案唯一的鐵則寫成程式碼。

    回測與即時跑同一份策略碼、同一份風控碼。
    只有「報價從哪來」「訂單往哪去」「時間從哪來」不同。

原鐵則只寫了兩顆，第三顆（時鐘）是後來補的：回測讀 K 棒時間戳、
即時讀系統時鐘，若策略層直接呼叫 datetime.now() 就綁死在即時端。

這三個 Protocol 定義在層 0，因為插頭的**實作**在層 1 與層 5，而
**使用者**是 runtime 的組裝根。兩邊都要 import 它，所以它必須在地基。
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterator, Protocol, runtime_checkable

from txfcore.types.bar import Bar
from txfcore.types.orders import ProtectiveStop, SizedOrder


@runtime_checkable
class Clock(Protocol):
    """插頭三：時間從哪來。

    回測：回傳當前 K 棒的收盤時刻。
    即時：回傳系統時鐘（需經 NTP 漂移檢查）。

    策略層**永不**直接讀系統時間 —— 那會讓同一份程式碼在兩端行為不同。
    """

    def now(self) -> datetime: ...

    def mc_stamp(self) -> tuple[int, int]:
        """(Date, Time) 的 MC 戳記。"""
        ...


@runtime_checkable
class QuoteSource(Protocol):
    """插頭一：報價從哪來。

    回測 adapter：讀 MC12 匯出的 1 分 K，聚合成目標週期。
    即時 adapter：讀凱基 QuoteCom tick，合成 K 棒。

    兩者產出同一種 Bar，且都必須填三戳記。回補的 K 棒必須標
    `is_backfilled`，否則重放時無法重現「當時看不到那幾根」的狀態。
    """

    @property
    def name(self) -> str: ...

    def stream(self) -> Iterator[Bar]:
        """依序吐出已收盤的 K 棒。"""
        ...


class SubmitStatus(str):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"   # 冪等鍵重複，視為同一筆


@runtime_checkable
class OrderSink(Protocol):
    """插頭二：訂單往哪去。

    回測 adapter：交易記錄器，不發任何通知。
    即時 adapter（訊號）：Email / Telegram。
    即時 adapter（自動）：券商 API。

    `submit` 必須是冪等的 —— 同一個 idem_key 重送視為同一筆，
    回傳 DUPLICATE 而不是重複下單。
    """

    @property
    def name(self) -> str: ...

    def submit(self, order: SizedOrder) -> str:
        """回傳 SubmitStatus。實作必須以 order.idem_key 去重。

        收的是 SizedOrder 不是 OrderIntent —— 沒經過風險層決定口數的東西
        送不出去，這一點由型別保證。
        """
        ...

    def set_protective(self, stop: ProtectiveStop) -> None:
        """設定引擎層級停損（MC 的 SetStopLoss + SetStopContract）。

        L5 實測：引擎停損可以在沒有任何出場單的情況下平倉。
        所以這條路徑必須被記成一種獨立的出場類型，否則對帳會出現
        「有平倉但找不到對應出場單」。
        """
        ...
