"""連虧控制。L2 與 L4 的語意不同，各一個類別（規則手冊 R3）。

共同點：用 TotalTrades 變化偵測平倉，用 NetProfit 差額判斷輸贏（含成本，滑價設定會影響結果）。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SkipNextRun:
    """L2 方案 B：連虧 N 筆（只算計入的交易）→ 跳過下一段訊號（一整段連續訊號都不做）。

    mode 0 為舊版暫停：暫停到濾網關閉或滿 pause_bars 根。
    假日、結算、Kill 擋下的訊號不消耗跳過次數。
    """
    last_tt: int = 0
    last_np: float = 0.0
    loss_cnt: int = 0
    pause_active: bool = False
    pause_start_bar: int = 0
    skip_left: int = 0
    skip_run: bool = False

    def count(self, total_trades: int, net_profit: float, counts: bool,
              n: int, mode: int, skip_k: int, bar_no: int) -> None:
        if total_trades == self.last_tt:
            return
        if counts:
            self.loss_cnt = self.loss_cnt + 1 if net_profit - self.last_np < 0 else 0
            if n > 0 and self.loss_cnt >= n:
                if mode == 0:
                    self.pause_active = True
                    self.pause_start_bar = bar_no
                else:
                    self.skip_left = skip_k
                self.loss_cnt = 0
        self.last_tt = total_trades
        self.last_np = net_profit

    def release_pause(self, filter_ok: bool, pause_bars: int, bar_no: int) -> None:
        if self.pause_active and (not filter_ok or (
                pause_bars > 0 and bar_no - self.pause_start_bar > pause_bars)):
            self.pause_active = False

    def allow(self, signal: bool, gates_ok: bool, flat: bool) -> bool:
        """回傳本根訊號是否可進場（暫停與跳過之外的條件由呼叫端判斷）。"""
        if not signal:
            self.skip_run = False
        if signal and gates_ok and flat and not self.skip_run and self.skip_left > 0:
            self.skip_left -= 1
            self.skip_run = True
        return not self.pause_active and not self.skip_run


@dataclass(slots=True)
class StreakSkip:
    """L4 R1：空手時結算上一筆部位損益；連虧 N 筆 → 下一個進場訊號不做（只跳一次）。

    State_Start_Date > 0 時，該日之前的交易不計入。n ≤ 0 為關閉。
    """
    np_base: float = 0.0
    prev_tt: int = 0
    loss_run: int = 0
    skip_next: bool = False

    def update(self, flat: bool, total_trades: int, net_profit: float,
               mc_date: int, n: int, start_date: int = 0) -> None:
        if flat:
            if total_trades != self.prev_tt:
                last = net_profit - self.np_base
                if start_date == 0 or mc_date >= start_date:
                    self.loss_run = self.loss_run + 1 if last < 0 else 0
                    if n > 0 and self.loss_run >= n:
                        self.skip_next = True
                        self.loss_run = 0
            self.np_base = net_profit
        self.prev_tt = total_trades
        if n <= 0:
            self.skip_next = False

    def consume(self) -> bool:
        """有訊號時呼叫：回傳 True ＝ 本次跳過。"""
        if self.skip_next:
            self.skip_next = False
            return True
        return False
