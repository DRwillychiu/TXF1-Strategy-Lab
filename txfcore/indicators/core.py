"""共用指標。五支策略都吃這一份。

全部採「全量重算」而非遞迴累積 —— 規劃書層 2 的要求：
停損是 >= 比較，遞迴累積的浮點誤差會在小數點第四位翻轉單筆交易成敗。
"""

from __future__ import annotations

from txfcore.types.bar import BarSeries, Series


def highest(series: Series, length: int, offset: int = 0) -> float:
    """MC 的 Highest(x, n)[offset]。"""
    return max(series.window(length, offset))


def lowest(series: Series, length: int, offset: int = 0) -> float:
    """MC 的 Lowest(x, n)[offset]。"""
    return min(series.window(length, offset))


def average(series: Series, length: int, offset: int = 0) -> float:
    """MC 的 Average(x, n) = 簡單移動平均。"""
    w = series.window(length, offset)
    return sum(w) / length


def true_range(bars: BarSeries, offset: int = 0) -> float:
    """單根真實區間。第一根無前收，退化為 High - Low。"""
    b = bars[offset]
    if not bars.close.available(offset + 1):
        return b.high - b.low
    prev_close = bars.close[offset + 1]
    return max(
        b.high - b.low,
        abs(b.high - prev_close),
        abs(b.low - prev_close),
    )


def avg_true_range(bars: BarSeries, length: int, offset: int = 0) -> float:
    """MC 的 AvgTrueRange(n) —— 真實區間的簡單移動平均。

    注意 MC 的 AvgTrueRange 用的是 Average(TrueRange, n)，
    不是 Wilder 平滑。兩者差異很大，不可混用。
    """
    total = 0.0
    for i in range(length):
        total += true_range(bars, offset + i)
    return total / length


def xaverage(series: Series, length: int, prev_ema: float | None) -> float:
    """MC 的 XAverage(x, n) = 指數移動平均。

    MC 的種子行為：第一次呼叫時 prev_ema 不存在，直接取當根值。
    之後 EMA = prev + k * (value - prev)，k = 2 / (n + 1)。
    """
    value = series[0]
    if prev_ema is None:
        return value
    k = 2.0 / (length + 1.0)
    return prev_ema + k * (value - prev_ema)


def zlema_comp_price(series: Series, lag: int) -> float:
    """ZLEMA 的合成價：2 * Close - Close[lag]。"""
    return 2.0 * series[0] - series[lag]


def crosses_over(series: Series, level_now: float, level_prev: float) -> bool:
    """MC 的 Crosses Over：前一根在下、當根在上。

    只有 L1 用到（Close Crosses Over Breakout_Level）。
    """
    return series[1] <= level_prev and series[0] > level_now
