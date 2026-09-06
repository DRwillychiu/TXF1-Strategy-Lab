"""行事曆閘門：假日尾盤、結算日、註冊表過期。

五份 .pla 的偵測邏輯逐字相同，所以這裡是真正的共用實作。
不共用的是 Holiday_Flat_Time（每支不同，屬 config）與強制平倉
的下單區塊（四種不同結構，留在各自的策略檔）。
"""

from __future__ import annotations

from dataclasses import dataclass

from txfcore.tradecal.registry import HOLIDAY_TAIL_SET, REGISTRY_VALID_UNTIL
from txfcore.types.mctime import DayOfWeek, day_of_month, day_of_week

NIGHT_TAIL_SCAN_END = 500  # 只在 Time <= 500 掃描，與 .pla 一致


@dataclass(frozen=True, slots=True)
class CalendarState:
    holiday_block: bool
    registry_expired: bool
    settlement_day: bool


def is_holiday_tail(mc_date: int, mc_time: int) -> bool:
    """該 K 棒是否落在假日前最後夜盤的 00:00-05:00 尾段。"""
    if mc_time > NIGHT_TAIL_SCAN_END:
        return False
    return mc_date in HOLIDAY_TAIL_SET


def is_settlement_day(mc_date: int) -> bool:
    """月結算日 = 每月第三個週三。

    .pla 的判定：DayOfWeek = 3 (Wed) and DayOfMonth in [15, 21]。
    已知風險：第三個週三若適逢休市，實際結算日會移動，此靜態規則會標錯。
    """
    return (
        day_of_week(mc_date) is DayOfWeek.WED
        and 15 <= day_of_month(mc_date) <= 21
    )


def evaluate(
    mc_date: int,
    mc_time: int,
    registry_valid_until: int = REGISTRY_VALID_UNTIL,
) -> CalendarState:
    """一根 K 棒上的行事曆狀態。

    註冊表過期時同時把 holiday_block 設為 True —— 這與五份 .pla 一致：
    走出已驗證的地圖之外必須 fail safe，不是 fail silent。
    """
    holiday = is_holiday_tail(mc_date, mc_time)
    expired = mc_date > registry_valid_until
    if expired:
        holiday = True
    return CalendarState(
        holiday_block=holiday,
        registry_expired=expired,
        settlement_day=is_settlement_day(mc_date),
    )
