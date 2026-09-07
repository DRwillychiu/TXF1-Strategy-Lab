"""樣本內外的切分。

**2026-09-07 發現：先前所有回測都跑到 2026-09-05，涵蓋了實戰期。**
樣本內外被混在一起，樣本外的衰退完全看不出來。

    回測期（樣本內）   ~ 2026-06-16
    實戰期（樣本外）    2026-06-17 起 ← 真實下單開始

**不留空窗**（2026-09-07 會議裁決：回測至 06/17 為止，之後是實戰）。

實戰起點 2026-06-17 由實戰紀錄檔名確認（`260617開始`）。

**這個切分是第一級參數，不是報告時才過濾。**
所有工具都必須用同一份定義，否則兩份報告會給出不同的數字而沒人發現。
"""

from __future__ import annotations

from dataclasses import dataclass

# 民國年 YYYMMDD
BACKTEST_END = 1260616
LIVE_START = 1260617
LIVE_END = 1260905          # 資料截止。重新匯出時要更新


@dataclass(frozen=True, slots=True)
class Window:
    name: str
    start: int
    end: int

    def holds(self, mc_date: int) -> bool:
        return self.start <= mc_date <= self.end


IN_SAMPLE = Window("回測期（樣本內）", 0, BACKTEST_END)
OUT_SAMPLE = Window("實戰期（樣本外）", LIVE_START, LIVE_END)


def split(trades):
    """回傳 (樣本內, 樣本外, 空窗)。"""
    ins, out, gap = [], [], []
    for t in trades:
        if IN_SAMPLE.holds(t.entry_date):
            ins.append(t)
        elif OUT_SAMPLE.holds(t.entry_date):
            out.append(t)
        else:
            gap.append(t)
    return ins, out, gap
