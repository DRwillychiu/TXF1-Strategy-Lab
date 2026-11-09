"""進場訊號模組。

- 通道跌破＋ZLEMA（L2 空頭）
- 暴跌腿（L2）
- 收盤失效型箱體（L4 的 60 分箱；L3／L5 的箱體語意不同，另立）
- 誘多區與跌回觸發（L4 S_Spring）
"""
from __future__ import annotations

from dataclasses import dataclass, field

from txfcore.indicators.core import highest, lowest, xaverage, zlema_comp_price
from txfcore.types.bar import Series


def channel_breakdown(close: float, channel_low: float, atr: float, k: float) -> bool:
    """收盤跌破通道下緣再減 k 倍 ATR。"""
    return close < channel_low - atr * k


@dataclass(slots=True)
class Zlema:
    """ZLEMA 與同長度 EMA（MC XAverage 種子：第一次取當根值）。"""
    comp: Series = field(default_factory=Series)
    val: float = 0.0
    prev: float = 0.0
    ema: float = 0.0
    seeded: bool = False

    def update(self, closes, length: int, lag: int) -> None:
        self.comp.push(zlema_comp_price(closes, lag))
        self.prev = self.val
        self.val = xaverage(self.comp, length, self.val if self.seeded else None)
        self.ema = xaverage(closes, length, self.ema if self.seeded else None)
        self.seeded = True

    @property
    def falling(self) -> bool:
        return self.val < self.prev

    @property
    def below_ema(self) -> bool:
        return self.val < self.ema


@dataclass(slots=True)
class CrashLeg:
    """L2 暴跌腿：ATR 佔比、距 N 根高點跌幅、長黑實體三條件；每一腿最多進 leg_max 次。

    一腿在 High 回到腿高（或滿 reset_bars 根）時結束。觸發時同時算出暴跌單的停損距離。
    """
    leg_active: bool = False
    leg_hh: float = 0.0
    leg_n: int = 0
    leg_bar: int = 0
    dist: float = 0.0

    def update_leg(self, high: float, bar_no: int, reset_bars: int) -> None:
        if self.leg_active and (high >= self.leg_hh or (
                reset_bars > 0 and bar_no - self.leg_bar >= reset_bars)):
            self.leg_active = False
            self.leg_n = 0

    def check(self, eligible: bool, close: float, open_: float, atr: float, highs,
              lookback: int, drop_pct: float, body_atr: float, atr_pct_min: float,
              sl_pct: float, max_pts: float, leg_max: int, bar_no: int) -> bool:
        hh = highest(highs, lookback)          # .pla：Highest() 每根都要算
        if not eligible or close <= 0:
            return False
        if (hh > 0 and atr / close * 100 >= atr_pct_min
                and (1 - close / hh) * 100 >= drop_pct
                and (open_ - close) >= body_atr * atr
                and (leg_max == 0 or not self.leg_active or self.leg_n < leg_max)):
            if not self.leg_active:
                self.leg_active, self.leg_hh, self.leg_bar = True, hh, bar_no
            self.leg_n += 1
            self.dist = close * sl_pct / 100
            if max_pts > 0:
                self.dist = min(self.dist, max_pts)
            return True
        return False


@dataclass(slots=True)
class CloseInvalidatedBox:
    """L4 的 60 分箱：當根落在前 N 根區間內、且振幅 ≤ 該區間的 shrink 倍 → 成箱；收盤離開箱子 → 失效。"""
    active: bool = False
    top: float = 0.0
    btm: float = 0.0

    def update(self, bars, lookback: int, shrink: float) -> None:
        ref_high = highest(bars.high, lookback, offset=1)
        ref_low = lowest(bars.low, lookback, offset=1)
        ref_rng = ref_high - ref_low
        if bars.high[0] <= ref_high and bars.low[0] >= ref_low:
            if ref_rng > 0 and (bars.high[0] - bars.low[0]) / ref_rng <= shrink:
                self.active, self.top, self.btm = True, ref_high, ref_low
        if self.active and (bars.close[0] > self.top or bars.close[0] < self.btm):
            self.active = False

    @property
    def valid(self) -> bool:
        return self.active and self.top > self.btm


@dataclass(slots=True)
class TrapZone:
    """誘多區：High 穿過箱頂即開啟（計數歸零），存活 limit 根。"""
    active: bool = False
    n: int = 0

    def update(self, high: float, box_top: float, limit: int) -> None:
        if high > box_top:
            self.active, self.n = True, 0
        if self.active:
            self.n += 1
            if self.n > limit:
                self.active = False


def spring_trigger(close: float, box_top: float, atr: float, buffer_atr: float) -> bool:
    """跌回箱頂下方 buffer 倍 ATR。"""
    return close < box_top - atr * buffer_atr
