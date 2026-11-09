"""進場閘門：行事曆、Kill、時段、冷卻。全部是純函式或極小狀態，五支共用。"""
from __future__ import annotations

from dataclasses import dataclass

from txfcore.tradecal.gates import evaluate


def calendar_flags(mc_date: int, mc_time: int, registry_valid_until: int,
                   static_settlement: bool = True) -> tuple[bool, bool, bool]:
    """回傳（假日尾盤封鎖, 登錄表到期, 結算日）。

    假日表只有一份，在 `tradecal/registry.py`。登錄表到期時假日封鎖同時為真（五份 .pla 一致）。
    MC 相容：結算日用 .pla 的靜態規則（第三個週三，15–21 日）。
    """
    c = evaluate(mc_date, mc_time, registry_valid_until,
                 use_data_settlement=not static_settlement)
    return c.holiday_block, c.registry_expired, c.settlement_day


def is_killed(param_value: bool, config_flag: bool) -> bool:
    """Kill：.pla 的 Manual_Kill_Switch 或執行器的停機旗標，任一為真即擋進場並平倉。"""
    return bool(param_value) or bool(config_flag)


def in_window(mc_time: int, start: int, end: int) -> bool:
    """K 棒收盤戳落在 [start, end)。例：L4 深夜封鎖 200–500。"""
    return start <= mc_time < end


def in_closed_window(mc_time: int, start: int, end: int) -> bool:
    """K 棒收盤戳落在 [start, end]。例：L2 日盤停損窗 845–1245。"""
    return start <= mc_time <= end


@dataclass(slots=True)
class Cooldown:
    """出場後冷卻計數（需要 MarketPosition[1]）。持倉中為 0，出場那根為 1，之後每根加 1。"""
    bars_since_exit: int = 999

    def update(self, flat: bool, prev_flat: bool) -> int:
        if not flat:
            self.bars_since_exit = 0
        elif not prev_flat:
            self.bars_since_exit = 1
        else:
            self.bars_since_exit += 1
        return self.bars_since_exit
