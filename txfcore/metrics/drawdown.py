"""回撤指標。定義見規劃書「風險指標」一節。

每日動態回撤  如果我在最高淨值當天進場，到今天為止虧了幾 %
MDD           每日動態回撤曲線中的最高點
組合 MDD      五支每日損益逐日相加，合成一條組合損益曲線，再做一次 MDD 計算

分母一律是**當下的滾動峰值**，不是期初資金 —— 用期初資金會讓百分比
突破 100%（原本那個 106.3% 就是這樣來的）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class DrawdownResult:
    equity: list[float]
    peak: list[float]
    drawdown: list[float]        # 每日動態回撤，值域 0-1
    max_drawdown: float          # 百分比
    max_drawdown_amount: float   # 金額
    max_drawdown_index: int
    drawdown_duration: int       # 峰值到回復峰值的最長期數
    underwater_ratio: float      # 處於回撤中的期數 / 總期數


def equity_curve(initial_capital: float, pnl: Iterable[float]) -> list[float]:
    """V(t) = 期初資金 + 截至 t 的累積損益（含未平倉）。"""
    out = [float(initial_capital)]
    running = float(initial_capital)
    for x in pnl:
        running += x
        out.append(running)
    return out


def compute(equity: Sequence[float]) -> DrawdownResult:
    if not equity:
        raise ValueError("equity 不得為空")

    peak: list[float] = []
    dd: list[float] = []
    running_peak = equity[0]
    max_dd = 0.0
    max_amt = 0.0
    max_idx = 0

    longest = 0
    current = 0
    underwater = 0

    for i, v in enumerate(equity):
        if v > running_peak:
            running_peak = v
        peak.append(running_peak)

        amount = running_peak - v
        ratio = amount / running_peak if running_peak != 0 else 0.0
        dd.append(ratio)

        if ratio > max_dd:
            max_dd = ratio
            max_idx = i
        if amount > max_amt:
            max_amt = amount

        if ratio > 0:
            current += 1
            underwater += 1
            longest = max(longest, current)
        else:
            current = 0

    return DrawdownResult(
        equity=list(equity),
        peak=peak,
        drawdown=dd,
        max_drawdown=max_dd,
        max_drawdown_amount=max_amt,
        max_drawdown_index=max_idx,
        drawdown_duration=longest,
        underwater_ratio=underwater / len(equity),
    )


def portfolio_mdd(
    initial_capital: float, per_strategy_daily_pnl: Sequence[Sequence[float]]
) -> DrawdownResult:
    """組合 MDD。

    先逐日相加成一條組合損益曲線，再做一次 MDD 計算。
    **不可將各策略的 MDD 相加** —— 各支的最深回撤發生在不同時間點，
    相加等於假設所有策略同時觸底。76 天實戰實測：相加 158,088 vs
    組合 99,944，高估 58%。
    """
    if not per_strategy_daily_pnl:
        raise ValueError("至少要有一支策略")
    length = len(per_strategy_daily_pnl[0])
    for s in per_strategy_daily_pnl:
        if len(s) != length:
            raise ValueError("各策略的每日損益序列長度必須相同（逐日對齊）")
    combined = [sum(s[i] for s in per_strategy_daily_pnl) for i in range(length)]
    return compute(equity_curve(initial_capital, combined))


def calmar(annual_return: float, result: DrawdownResult) -> float:
    """年化報酬 / max_drawdown。分子分母必須用同一資金基準。"""
    if result.max_drawdown == 0:
        raise ZeroDivisionError("max_drawdown = 0，Calmar 無定義")
    return annual_return / result.max_drawdown
