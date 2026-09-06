"""1 分 K 聚合成任意週期。

**規則由 L2 標頭與實際檔案雙重確認：**

    網格   各時段從開盤各自起算，不連續
    戳記   收盤時刻
    歸屬   1 分 K 戳記 T 屬於 open_at < T <= close_at 的那一格

驗證：60M 日盤 → 09:45 / 10:45 / 11:45 / 12:45 / 13:45
      60M 夜盤 → 16:00 … 05:00
與 L2 標頭「day 09:45-13:45, night 16:00-05:00」逐字相符。

**缺漏容忍**：匯出檔的無成交分鐘直接省略（實測 2026/6/1 夜盤跳過 19:23）。
所以每根聚合 K 棒都記錄 `tick_count` = 由幾根 1 分 K 合成，
低於門檻者標記為低信度——這是規劃書層 1 要求的 K 棒品質標記。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Iterator

from txfcore.quotes.session import GridBar, session_grid
from txfcore.types.bar import Bar
from txfcore.types.mctime import mc_date_to_date, mc_time_to_time


@dataclass(frozen=True, slots=True)
class QualityFlag:
    """K 棒品質。規劃書層 1 的要求。"""

    expected_minutes: int
    actual_minutes: int
    max_gap_minutes: int

    @property
    def completeness(self) -> float:
        return self.actual_minutes / self.expected_minutes if self.expected_minutes else 0.0

    def is_low_confidence(self, min_completeness: float = 0.8) -> bool:
        return self.completeness < min_completeness


def _dt_of(bar: Bar) -> datetime:
    return datetime.combine(mc_date_to_date(bar.mc_date), mc_time_to_time(bar.mc_time))


def _grid_for(d: date, period: int) -> list[GridBar]:
    return session_grid(d, period)


def aggregate(
    minutes: Iterable[Bar], period: int, min_completeness: float = 0.8
) -> Iterator[tuple[Bar, QualityFlag]]:
    """把 1 分 K 串流聚合成指定週期。

    輸入必須依時間遞增。輸出每根帶品質旗標。

    邊界規則：1 分 K 戳記 T 屬於 `open_at < T <= close_at` 的那一格。
    因為兩邊都是收盤戳記，這個半開半閉區間才對得上——
    日盤第一根戳 08:46，屬於 08:45 開盤的那一格。
    """
    grids: dict[date, list[GridBar]] = {}
    cur: GridBar | None = None
    buf: list[Bar] = []

    def flush() -> tuple[Bar, QualityFlag] | None:
        if cur is None or not buf:
            return None
        stamp_d, stamp_t = cur.mc_stamp
        stamps = sorted(_dt_of(b) for b in buf)
        max_gap = max(
            (int((b - a).total_seconds() // 60) for a, b in zip(stamps, stamps[1:])),
            default=1,
        )
        bar = Bar(
            mc_date=stamp_d, mc_time=stamp_t,
            open=buf[0].open,
            high=max(b.high for b in buf),
            low=min(b.low for b in buf),
            close=buf[-1].close,
            volume=sum(b.volume for b in buf),
            tick_count=len(buf),
        )
        return bar, QualityFlag(cur.minutes, len(buf), max_gap)

    for m in minutes:
        t = _dt_of(m)
        # 找出它屬於哪一格。夜盤跨日，所以要試當日與前一日的網格。
        found: GridBar | None = None
        for base in (t.date(), t.date() - timedelta(days=1)):
            if base not in grids:
                grids[base] = _grid_for(base, period)
            for g in grids[base]:
                if g.open_at < t <= g.close_at:
                    found = g
                    break
            if found:
                break
        if found is None:
            continue  # 落在時段之外（不應發生，但不讓它炸掉整條串流）

        if cur is not None and found is not cur and found.close_at != cur.close_at:
            out = flush()
            if out:
                yield out
            buf = []
        cur = found
        buf.append(m)

    out = flush()
    if out:
        yield out


def aggregate_bars(minutes: Iterable[Bar], period: int) -> Iterator[Bar]:
    """只要 K 棒，不要品質旗標。"""
    for bar, _ in aggregate(minutes, period):
        yield bar
