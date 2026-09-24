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


def is_settlement_day(mc_date: int, use_data: bool = True) -> bool:
    """結算日判定。

    `.pla` 用靜態規則：`DayOfWeek = 3 and DayOfMonth in [15, 21]`。
    **2026-09-07 用 208 萬列 1 分 K 實測：那條規則漏標 2 天**
    （2023-01-30 · 2026-02-23，皆為農曆年後遞延），誤標 0 天。

    > **2026-09-08 修正**：我建了 `tradecal/settlement.py` 的資料反推日曆，
    > **卻從來沒有接上這裡**——`evaluate()` 一直在用靜態規則。
    > 那兩天策略不知道是結算日，**實盤上不會強制平倉**。
    > 典型的孤兒模組：寫好了、更準、沒人用。

    `use_data = False` 時回到靜態規則，供 `mc12` 模式重現 MC 的行為。
    """
    if use_data:
        from txfcore.tradecal.settlement import is_settlement_day as derived
        return derived(mc_date)
    return static_settlement_rule(mc_date)


def static_settlement_rule(mc_date: int) -> bool:
    """`.pla` 的原始判定。保留供 mc12 模式重現。"""
    return (
        day_of_week(mc_date) is DayOfWeek.WED
        and 15 <= day_of_month(mc_date) <= 21
    )


def evaluate(
    mc_date: int,
    mc_time: int,
    registry_valid_until: int = REGISTRY_VALID_UNTIL,
    use_data_settlement: bool = True,
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
        settlement_day=is_settlement_day(mc_date, use_data_settlement),
    )
