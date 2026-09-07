"""回撤家族的其餘風險度量。

**外部借鑑：skfolio。** 它的風險度量清單包含 CVaR、CDaR（條件回撤風險值）、
EDaR、Ulcer Index、平均回撤、最壞實現值等等。

我們的 `metrics/drawdown.py` 只回答「最壞的一次有多深」。
**那是單點統計，對長尾分布特別不可靠。**

    max_drawdown        最壞的一次     ← 已有
    average_drawdown    平常有多深     ← 新增
    cdar                最壞 5% 有多深 ← 新增。比 MDD 穩定
    ulcer_index         痛苦的累積量   ← 新增
    cvar                最壞 5% 的日損 ← 新增
    worst_realization   最壞的單日     ← 新增

**為什麼對我們重要**：76 天實戰紀錄的 `underwater_ratio` 是 96.7%——
幾乎全程在水下。單看 `max_drawdown 31.53%` 完全看不出這件事。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from txfcore.metrics.drawdown import DrawdownResult


@dataclass(frozen=True, slots=True)
class RiskProfile:
    """一組完整的風險度量。單一數字會騙人，一組不會。"""

    max_drawdown: float          # 最壞的一次
    average_drawdown: float      # 平常有多深
    cdar_95: float               # 最壞 5% 的回撤平均
    ulcer_index: float           # 回撤的均方根，痛苦的累積量
    cvar_95: float               # 最壞 5% 期間的平均損失（比例）
    worst_realization: float     # 最壞的單期損失（比例）
    underwater_ratio: float      # 處於回撤中的期數比例
    drawdown_duration: int       # 最長回撤持續期數

    def summary(self) -> str:
        return (
            f"max_dd {self.max_drawdown*100:6.2f}%   "
            f"avg_dd {self.average_drawdown*100:6.2f}%   "
            f"CDaR95 {self.cdar_95*100:6.2f}%   "
            f"Ulcer {self.ulcer_index*100:6.2f}%\n"
            f"CVaR95 {self.cvar_95*100:6.2f}%   "
            f"最壞單期 {self.worst_realization*100:6.2f}%   "
            f"水下比例 {self.underwater_ratio*100:5.1f}%   "
            f"最長回撤 {self.drawdown_duration} 期"
        )


def _tail_mean(values: Sequence[float], q: float, worst_is_max: bool) -> float:
    """最壞 (1-q) 尾部的平均。q = 0.95 表示取最壞 5%。"""
    if not values:
        return 0.0
    s = sorted(values, reverse=worst_is_max)
    k = max(1, int(round(len(s) * (1 - q))))
    return sum(s[:k]) / k


def average_drawdown(dd: Sequence[float]) -> float:
    """平均回撤。`max_drawdown` 說最壞的一次，這個說平常有多深。"""
    return sum(dd) / len(dd) if dd else 0.0


def cdar(dd: Sequence[float], confidence: float = 0.95) -> float:
    """條件回撤風險值。最壞 (1-confidence) 的回撤平均。

    比 `max_drawdown` 穩定——單一極端值不會主導它。
    """
    return _tail_mean(dd, confidence, worst_is_max=True)


def ulcer_index(dd: Sequence[float]) -> float:
    """回撤的均方根。同時懲罰**深度**與**持續時間**。

    兩條權益曲線可以有相同的 max_drawdown，但一條很快回復、
    一條拖了兩年。Ulcer Index 分得出來，MDD 分不出來。
    """
    if not dd:
        return 0.0
    return math.sqrt(sum(x * x for x in dd) / len(dd))


def period_returns(equity: Sequence[float]) -> list[float]:
    """逐期報酬率。"""
    return [
        (equity[i] - equity[i - 1]) / equity[i - 1]
        for i in range(1, len(equity))
        if equity[i - 1] != 0
    ]


def cvar(returns: Sequence[float], confidence: float = 0.95) -> float:
    """條件風險值。最壞 (1-confidence) 期間的平均損失。回傳正數。"""
    if not returns:
        return 0.0
    return -_tail_mean(returns, confidence, worst_is_max=False)


def worst_realization(returns: Sequence[float]) -> float:
    """最壞的單期損失。回傳正數。

    對日內停損上限的設定直接相關——若最壞單日超過上限，
    那個上限從來沒有生效過。
    """
    return -min(returns) if returns else 0.0


def profile(result: DrawdownResult, confidence: float = 0.95) -> RiskProfile:
    """從 `drawdown.compute()` 的結果算出完整風險輪廓。"""
    rets = period_returns(result.equity)
    return RiskProfile(
        max_drawdown=result.max_drawdown,
        average_drawdown=average_drawdown(result.drawdown),
        cdar_95=cdar(result.drawdown, confidence),
        ulcer_index=ulcer_index(result.drawdown),
        cvar_95=cvar(rets, confidence),
        worst_realization=worst_realization(rets),
        underwater_ratio=result.underwater_ratio,
        drawdown_duration=result.drawdown_duration,
    )
