"""回撤指標。定義見規劃書「風險指標」一節。

每日動態回撤  如果我在最高淨值當天進場，到今天為止虧了幾 %
MDD           每日動態回撤曲線中的最高點
組合 MDD      五支每日損益逐日相加，合成一條組合損益曲線，再做一次 MDD 計算

## 金額跟著百分比走（裁決 2026-09-08）

`max_drawdown_amount` 是**最大百分比那一點的金額**，不是最大絕對金額。

理由：MDD 的定義是「每日動態回撤曲線中的最高點」——那是**一個時點**，
而那個時點的金額只有一個。兩個獨立的最大值並列時極易誤讀。

最大絕對金額仍然保留為 `peak_to_valley_amount`，**但它衡量的是規模不是風險**：
固定口數下，權益成長後晚期的絕對金額必然更大。

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
    max_drawdown: float          # 百分比。**MDD 的定義**
    max_drawdown_amount: float   # **最大百分比那一點的金額**
    max_drawdown_index: int      # 最大百分比發生的索引
    drawdown_duration: int       # 峰值到回復峰值的最長期數
    underwater_ratio: float      # 處於回撤中的期數 / 總期數
    # 最大絕對金額。**可能發生在完全不同的時點**——固定口數下，
    # 權益成長後晚期的絕對金額必然更大，所以它衡量的是規模不是風險。
    # 2026-09-08 實測（組合 ③ 曲線）：
    #   最大百分比 14.84% 於 2021-03-10，金額 704,970
    #   最大金額 1,290,274 於 2026-06-12，佔比僅 7.06%
    #   相差 1,920 天、585,304 元
    peak_to_valley_amount: float = 0.0
    peak_to_valley_index: int = 0


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
    ptv_amt = 0.0
    ptv_idx = 0

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
            # **金額跟著百分比走**（裁決 2026-09-08，選項 A）。
            # MDD 的定義是「每日動態回撤曲線中的最高點」——那是一個時點，
            # 而那個時點的金額只有一個。
            max_amt = amount
        if amount > ptv_amt:
            ptv_amt = amount
            ptv_idx = i

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
        peak_to_valley_amount=ptv_amt,
        peak_to_valley_index=ptv_idx,
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
