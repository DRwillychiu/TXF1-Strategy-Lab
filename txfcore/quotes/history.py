"""MC12 匯出的 1 分 K 讀取器（回測 adapter，實作 QuoteSource）。

**格式由實際檔案確認（2026-09-06，TXF1_1_分鐘.txt，2,087,650 列）：**

    <Date>, <Time>, <Open>, <High>, <Low>, <Close>, <Volume>
    2019/1/2,08:46:00.000,9760,9762,9745,9750,2997

    日期    2019/1/2       月日不補零
    時間    08:46:00.000   HH:MM:SS.mmm
    換行    CRLF
    期間    2019/1/2 ~ 2026/8/22

**戳記語意 = 收盤。** 日盤 08:45 開盤，第一根戳 08:46。

    日盤   08:46 → 13:45   300 根
    夜盤   15:01 → 05:00   840 根（跨日，00:00 戳記屬隔一曆日）
    合計   唯一戳記 1140 = 300 + 840

**缺漏分鐘是常態，不是異常。** 全檔 OHLC 零不一致、零成交量筆數為 0
——代表無成交的分鐘**直接省略**，不是補成量 0 的 K 棒。
例：2026/6/1 夜盤跳過 19:23。聚合器必須容忍，並記錄每根由幾根合成。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Iterator

from txfcore.types.bar import Bar
from txfcore.types.mctime import date_to_mc_date, time_to_mc_time

EXPECTED_HEADER_FIELDS = ("date", "time", "open", "high", "low", "close", "volume")


class ExportFormatError(ValueError):
    """匯出格式與預期不符。**寬鬆解析是禁止的**——格式變了要停，不要猜。"""


@dataclass(frozen=True, slots=True)
class RawMinute:
    dt: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_bar(self) -> Bar:
        return Bar(
            mc_date=date_to_mc_date(self.dt.date()),
            mc_time=time_to_mc_time(self.dt.time()),
            open=self.open, high=self.high, low=self.low, close=self.close,
            volume=float(self.volume),
            tick_count=None,      # 匯出檔沒有 tick 數
        )


def _parse_header(line: str) -> None:
    fields = [f.strip().strip("<>").lower() for f in line.strip().split(",")]
    if tuple(fields) != EXPECTED_HEADER_FIELDS:
        raise ExportFormatError(
            f"欄位不符。預期 {EXPECTED_HEADER_FIELDS}，實得 {tuple(fields)}。"
            f"格式變了就停下來，不做寬鬆解析。"
        )


def _parse_line(line: str, lineno: int) -> RawMinute:
    parts = line.rstrip("\r\n").split(",")
    if len(parts) != 7:
        raise ExportFormatError(f"第 {lineno} 行欄位數 {len(parts)}，預期 7：{line[:80]!r}")
    d, t, o, h, l, c, v = parts
    try:
        y, mo, dy = (int(x) for x in d.split("/"))
        hh, mi = int(t[0:2]), int(t[3:5])
        dt = datetime.combine(date(y, mo, dy), time(hh, mi))
        return RawMinute(dt, float(o), float(h), float(l), float(c), int(v))
    except (ValueError, IndexError) as e:
        raise ExportFormatError(f"第 {lineno} 行無法解析：{line[:80]!r}") from e


class MC12MinuteSource:
    """實作 `contracts.plugs.QuoteSource`。串流讀取，不整檔載入。

    106 MB / 208 萬列，整檔進記憶體沒有必要。
    """

    def __init__(self, path: str | Path, validate: bool = True) -> None:
        self.path = Path(path)
        self.validate = validate

    @property
    def name(self) -> str:
        return f"mc12_1min:{self.path.name}"

    def stream(self) -> Iterator[Bar]:
        with self.path.open(encoding="utf-8", errors="strict", newline="") as fh:
            _parse_header(fh.readline())
            prev: datetime | None = None
            for lineno, line in enumerate(fh, start=2):
                if not line.strip():
                    continue
                m = _parse_line(line, lineno)
                if self.validate:
                    if not (m.low <= m.open <= m.high and m.low <= m.close <= m.high):
                        raise ExportFormatError(f"第 {lineno} 行 OHLC 不一致")
                    if prev is not None and m.dt < prev:
                        raise ExportFormatError(
                            f"第 {lineno} 行時間倒退：{prev} -> {m.dt}"
                        )
                    prev = m.dt
                yield m.to_bar()

    def stream_between(self, start: date, end: date) -> Iterator[Bar]:
        """依曆日過濾。注意夜盤跨日——邊界的交易日歸屬由 trading_day() 決定。"""
        for bar in self.stream():
            from txfcore.types.mctime import mc_date_to_date
            d = mc_date_to_date(bar.mc_date)
            if d < start:
                continue
            if d > end:
                break
            yield bar
