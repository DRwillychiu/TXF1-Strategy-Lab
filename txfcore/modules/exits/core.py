"""出場模組（空單版本）。"""
from __future__ import annotations

from dataclasses import dataclass

from txfcore.indicators.core import highest
from txfcore.types.mctime import DayOfWeek, day_of_week


def forced_exit(prefix: str, kill: bool, registry_expired: bool, holiday: bool,
                settlement: bool, mc_time: int, holiday_time: int, settle_time: int) -> str | None:
    """優先序 0：Kill → 登錄表到期 → 假日尾盤（時間到）→ 結算日（時間到）。回傳委託名稱或 None。"""
    if kill:
        return f"{prefix}_Kill"
    if registry_expired:
        return f"{prefix}_RegistryEnd"
    if holiday and mc_time >= holiday_time:
        return f"{prefix}_Holiday"
    if settlement and mc_time >= settle_time:
        return f"{prefix}_Settlement"
    return None


@dataclass(slots=True)
class PeakGivebackShort:
    """峰值回吐保護：獲利（以收盤計）達門檻後，停利價 ＝ 進場價 − 峰值獲利×(1 − 回吐%)。"""
    peak: float = 0.0
    price: float = 0.0

    def update(self, entry: float, close: float, threshold: float, giveback_pct: float) -> float:
        profit = entry - close
        if profit >= threshold:
            self.peak = max(self.peak, profit)
            self.price = entry - self.peak * (1 - giveback_pct / 100)
        return self.price

    def reset(self) -> None:
        self.peak = self.price = 0.0


def structure_tp_short(close: float, closes, n: int) -> bool:
    """結構停利：收盤高於前 N 根最高收盤（空單反轉訊號）。"""
    return close > highest(closes, n, offset=1)


def retrace_tp_short(entry: float, lowest_close: float, close: float, atr: float,
                     min_atr: float, rebound_pct: float) -> bool:
    """回抽停利：波段獲利 ≥ min_atr×ATR，且收盤反彈超過最低收盤 rebound%。"""
    return entry - lowest_close >= atr * min_atr and close > lowest_close * (1 + rebound_pct / 100)


def tp1_price_short(entry: float, box_btm: float, room_pct: float) -> float:
    """TP1 價：進場價 − (進場價 − 箱底)×room%。不成立回 0。"""
    if room_pct > 0 and entry > box_btm > 0:
        return entry - (entry - box_btm) * room_pct / 100
    return 0.0


def time_exit(bars_since_entry: int, n: int) -> bool:
    """持倉滿 n 根；n ≤ 0 ＝ 關（L2 暴跌單 .pla 708）。"""
    return n > 0 and bars_since_entry >= n


def time_exit_raw(bars_since_entry: int, n: int) -> bool:
    """持倉滿 n 根，沒有 0 ＝ 關的例外（L4 .pla 482：n ＝ 0 時每根成立）。"""
    return bars_since_entry >= n


def breakeven_floor_short(entry: float, offset: float) -> float:
    """保本停損價：進場價 − offset。"""
    return entry - offset


def retain_floor_short(entry: float, peak: float, retain_pct: float) -> float:
    """保留 retain% 峰值獲利的停損價（以收盤峰值計）。"""
    return entry - peak * (1 - retain_pct / 100)


def weekly_exit_short(enabled: bool, mc_date: int, mc_time: int, close: float,
                      wk_ready: bool, wk_sma: float, sample_time: int = 1245) -> bool:
    """L2 週線出場：週五 12:45 那根收盤站上週均線。"""
    return (enabled and day_of_week(mc_date) is DayOfWeek.FRI and mc_time == sample_time
            and wk_ready and close > wk_sma)


def box_break_exit_short(box_active: bool, data2_close: float, locked_top: float) -> bool:
    """L4 箱體失效出場：箱子已失效且 60 分收盤高於進場時鎖定的箱頂（只認向上）。"""
    return not box_active and data2_close > locked_top
