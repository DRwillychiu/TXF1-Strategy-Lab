"""停損模組（目前為空單版本；多單版本在 L1／L3／L5 移植時補，方向相反不能共用同一式）。"""
from __future__ import annotations

from dataclasses import dataclass

from txfcore.indicators.core import lowest


def engine_stop_distance(anchor: float, close: float, pct: float = 0.0, max_pts: float = 0.0) -> float:
    """MC SetStopLoss 的距離（每口點數）：|錨點 − 訊號根收盤|，再取 % 上限與點數上限中較小者。

    錨點：L2 ＝ 通道下緣＋1.1 ATR；L4 ＝ 箱頂＋2 ATR。距離取小 ＝ 停損較緊。
    """
    d = abs(anchor - close)
    if pct > 0:
        d = min(d, close * pct / 100)
    if max_pts > 0:
        d = min(d, max_pts)
    return d


def cap_short(level: float, entry: float, pct: float = 0.0, max_pts: float = 0.0) -> float:
    """空單停損價上限：不得高於 進場價×(1+pct%) 與 進場價＋max_pts（價格取小 ＝ 較緊）。"""
    if pct > 0:
        level = min(level, entry + entry * pct / 100)
    if max_pts > 0:
        level = min(level, entry + max_pts)
    return level


def initial_stop_short(channel_low: float, atr: float, ratio: float, entry: float,
                       pct: float = 0.0, max_pts: float = 0.0) -> float:
    """L2 凍結初始停損：通道下緣＋ratio×ATR，再套上限。進場當根算一次後鎖定。"""
    return cap_short(channel_low + atr * ratio, entry, pct, max_pts)


def hard_stop_short(entry: float, max_pts: float) -> float:
    """硬停損：進場價＋N 點，每根都掛，獨立於出場鏈。"""
    return entry + max_pts


def ratchet_lowest_low_short(prev_level: float, lowest_low: float, atr: float, mult: float) -> float:
    """最低低點＋mult×ATR，只往下（L4 追蹤、L2 暴跌單停損共用；兩者語意相同）。"""
    return min(prev_level, lowest_low + mult * atr)


def accel_newlow_bar(open_: float, close: float, atr: float, accel_m: float, closes, nlow_n: int) -> bool:
    """加速新低 K：實體 > accel_m×ATR 的黑 K，且收盤創 N 根新低。"""
    return (open_ - close) > atr * accel_m and close < open_ and close < lowest(closes, nlow_n, offset=1)


@dataclass(slots=True)
class TwoBarArm:
    """連續兩根條件成立、且持倉滿 min_bars 根 → 啟動（只啟動一次）。"""
    cur: bool = False
    prev: bool = False
    armed: bool = False

    def update(self, cond: bool, bars_since_entry: int, min_bars: int) -> None:
        self.prev, self.cur = self.cur, cond
        if not self.armed and self.cur and self.prev and bars_since_entry >= min_bars:
            self.armed = True

    def reset(self) -> None:
        self.cur = self.prev = self.armed = False


@dataclass(slots=True)
class LowestCloseTrail:
    """L2 追蹤停損：線 ＝ 前 K 根最低收盤＋m×ATR（只往下）；生效停損 ＝ 線＋ratio×ATR。

    生效時與凍結初始停損比較：線 < 初始停損 → 用追蹤（src 1），否則用初始（src 2）。
    （照 .pla：比的是線、用的是線＋ratio×ATR。）
    """
    line: float = 0.0

    def active_stop(self, armed: bool, closes, k: int, m: float, atr: float,
                    ratio: float, initial: float) -> tuple[float, int]:
        if not armed:
            self.line = 0.0
            return initial, 2
        new = lowest(closes, k, offset=1) + atr * m
        self.line = new if self.line == 0 else min(self.line, new)
        if self.line < initial:
            return self.line + atr * ratio, 1
        return initial, 2

    def reset(self) -> None:
        self.line = 0.0
