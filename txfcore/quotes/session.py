"""交易時段與 K 棒網格。

**網格規則由 L2 標頭實證確認**：

    Timeframe : 60-Minute (Day + Night Sessions, grid verified
                vs Excel timestamps: day 09:45-13:45, night
                16:00-05:00 hourly close stamps)

反推：日盤自 08:45 起算 → 09:45 / 10:45 / 11:45 / 12:45 / 13:45（5 根）
      夜盤自 15:00 起算 → 16:00 … 05:00（14 根）

結論：**各時段從開盤各自起算，不連續。** 待決清單的「日夜盤各自或連續」結案。

整除性（本模組實測，見 tests）：

    15M   日 20 根   夜 56 根   整除
    60M   日  5 根   夜 14 根   整除
    45M   日  6 根 + 30 分殘棒   夜 18 根 + 30 分殘棒   ← 只有 L1 有殘棒
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum

from txfcore.types.mctime import date_to_mc_date, time_to_mc_time

DAY_OPEN = time(8, 45)
DAY_CLOSE = time(13, 45)
NIGHT_OPEN = time(15, 0)
NIGHT_CLOSE = time(5, 0)

DAY_MINUTES = 300   # 08:45 -> 13:45（一般日）
SETTLEMENT_DAY_MINUTES = 285  # 08:45 -> 13:30（結算日，近月合約提前停止交易）
NIGHT_MINUTES = 840  # 15:00 -> 05:00（跨日）


class Session(str, Enum):
    DAY = "day"
    NIGHT = "night"


@dataclass(frozen=True, slots=True)
class GridBar:
    """網格上的一格。時間戳為**收盤時刻**，與 MC 一致。"""

    session: Session
    open_at: datetime
    close_at: datetime
    is_residual: bool = False   # 不足一個完整週期的殘棒

    @property
    def minutes(self) -> int:
        return int((self.close_at - self.open_at).total_seconds() // 60)

    @property
    def mc_stamp(self) -> tuple[int, int]:
        """MC 戳記 (Date, Time)。取收盤時刻的曆日與時刻。

        夜盤 00:00-05:00 的收盤時刻已跨日，所以日期戳自然是隔天——
        這正是 L1 Holiday_Tail「最後交易日 + 1 曆日」的來源。
        """
        return date_to_mc_date(self.close_at.date()), time_to_mc_time(self.close_at.time())


def _grid(open_dt: datetime, total_minutes: int, period: int) -> list[GridBar]:
    session = Session.DAY if open_dt.time() == DAY_OPEN else Session.NIGHT
    bars: list[GridBar] = []
    full, rem = divmod(total_minutes, period)
    cursor = open_dt
    for _ in range(full):
        nxt = cursor + timedelta(minutes=period)
        bars.append(GridBar(session, cursor, nxt))
        cursor = nxt
    if rem:
        bars.append(GridBar(session, cursor, cursor + timedelta(minutes=rem), True))
    return bars


def day_grid(d: date, period: int) -> list[GridBar]:
    """某交易日的日盤網格。

    **結算日的日盤在 13:30 收，不是 13:45。**
    2026-09-06 用 208 萬列 1 分 K 實測：92 個結算日全部如此，零例外。
    所以 60M 在結算日會產生一根 45 分鐘的殘棒（戳 1330）。
    """
    from txfcore.tradecal.settlement import day_minutes
    from txfcore.types.mctime import date_to_mc_date

    return _grid(
        datetime.combine(d, DAY_OPEN), day_minutes(date_to_mc_date(d)), period
    )


def night_grid(d: date, period: int) -> list[GridBar]:
    """某交易日的夜盤網格。15:00 開盤，跨日到隔天 05:00。"""
    return _grid(datetime.combine(d, NIGHT_OPEN), NIGHT_MINUTES, period)


def session_grid(d: date, period: int) -> list[GridBar]:
    """一個完整交易日 = 日盤 + 夜盤。"""
    return day_grid(d, period) + night_grid(d, period)


def residual_count(period: int, settlement: bool = False) -> int:
    """一個交易日有幾根殘棒。

    一般日：45M 是 2（日夜盤各一），15M 與 60M 是 0。
    結算日：日盤 285 分鐘，60M 與 45M 都會多出殘棒。
    """
    dm = SETTLEMENT_DAY_MINUTES if settlement else DAY_MINUTES
    return int(dm % period != 0) + int(NIGHT_MINUTES % period != 0)


def bars_per_day(period: int, settlement: bool = False) -> int:
    dm = SETTLEMENT_DAY_MINUTES if settlement else DAY_MINUTES
    full_d, rem_d = divmod(dm, period)
    full_n, rem_n = divmod(NIGHT_MINUTES, period)
    return full_d + int(rem_d > 0) + full_n + int(rem_n > 0)


def is_day_bar(mc_time: int) -> bool:
    """L2 SECTION 4 的判定，逐字照抄。

    上限 1245 使 **13:45 那根落在夜盤**（規格表 D-6）。
    下限 845 永不生效——60M 網格上沒有 845..944 的戳記。
    """
    return 845 <= mc_time <= 1245


def last_n_bar_stamps(d: date, period: int, n: int) -> set[tuple[int, int]]:
    """各時段最後 n 根的戳記。

    LIVE 模式的「收盤前兩根禁止進場」用它。
    mc12 模式不使用——MC 沒有這條規則，套用會對不上帳。
    """
    out: set[tuple[int, int]] = set()
    for grid in (day_grid(d, period), night_grid(d, period)):
        for b in grid[-n:]:
            out.add(b.mc_stamp)
    return out
