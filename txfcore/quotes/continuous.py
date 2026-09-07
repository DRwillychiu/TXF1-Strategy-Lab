"""連續近月合約的換月標記。

TXF1 是連續近月序列。結算日 13:30 近月停止交易後，序列切換到次月——
**兩個合約的價差（基差）會產生一個人為跳空。**

實測（2019-01 ~ 2026-09，92 個換月點）：

    結算日 13:30 → 16:00   絕對值中位 60.5 點   標準差 141.1   最大 511
    一般日 13:45 → 16:00   絕對值中位 11.0 點   標準差  57.1

**換月跳空的中位數是一般隔夜跳空的 5.5 倍**，而策略完全不知道那是換月——
它看到的就是價格跳了。

## 但五支策略在結構上不可能碰到它

    Settlement_Flat_Time = 1230   強制平倉在 12:30
    換月點                 1330   近月停止交易
    v_Settlement_Day       整個結算日封鎖進場

**12:30 < 13:30，而且整天不進場。** 實測 L2 / L4 全歷史：

    結算日進場          0 筆
    跨越 13:30 換月點    0 筆

**這不是「觀察不到聚集」，是「結構上不可能」——更強的結論。**

> 2026-09-06 由用戶指出：「結算日當天夜盤跳空肯定有，
> 也因此針對策略上，完全沒有結算日當天留倉。」實測確認。
>
> 我原本的 `span_days=1` 窗口把「結算日的隔一天」也算進去，
> 誤標了兩筆與換月無關的交易（L4 +192,359 於 2026-08-20、
> L2 −84,891 於 2025-04-17）。**已修正為只認真正跨越 13:30 的。**

## 仍然保留這個模組，理由

一、**它是可能失敗而沒失敗的檢查。** 若日後有策略改掉
    `Settlement_Flat_Time`，`spans_rollover` 會立刻回報非零。

二、對帳時若差異集中在換月日，那本身是線索。

三、跳空的量值（60.5 點中位、511 點最大）本身是有用的參考數字。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from txfcore.tradecal.settlement import SETTLEMENT_CLOSE, SETTLEMENT_SET
from txfcore.types.mctime import mc_date_to_date, trading_day

# 實測值。資料換版時應重算。
ROLLOVER_GAP_MEDIAN_ABS = 60.5
ROLLOVER_GAP_STDEV = 141.1
NORMAL_GAP_MEDIAN_ABS = 11.0


@dataclass(frozen=True, slots=True)
class RolloverMark:
    is_rollover_window: bool
    spans_rollover: bool     # 進場在換月前、出場在換月後
    settlement_day: date | None


def is_rollover_point(mc_date: int, mc_time: int) -> bool:
    """該 K 棒是否**就是**換月那一根（結算日 13:30 之後的第一根）。"""
    return mc_date in SETTLEMENT_SET and mc_time > SETTLEMENT_CLOSE


def in_rollover_window(mc_date: int, mc_time: int, span_days: int = 1) -> bool:
    """該 K 棒是否落在換月窗口內。

    窗口 = 結算日 13:30 之後，到 span_days 個交易日之後。
    """
    td = trading_day(mc_date, mc_time)
    settle_dates = {mc_date_to_date(d) for d in SETTLEMENT_SET}
    for k in range(span_days + 1):
        if td - timedelta(days=k) in settle_dates:
            if k == 0 and mc_time <= SETTLEMENT_CLOSE:
                return False
            return True
    return False


def spans_rollover(
    entry_date: int, entry_time: int, exit_date: int, exit_time: int
) -> bool:
    """該筆交易是否**真正跨越換月點**：進場在結算日 13:30 之前、出場在之後。

    **五支策略在結構上不可能為真**（Settlement_Flat_Time = 1230
    早於換月點 1330，且整個結算日封鎖進場）。實測全歷史為 0。

    保留這個檢查的理由：**它可能失敗而沒失敗。**
    若日後有策略改掉 Settlement_Flat_Time，這裡會立刻回報非零。
    """
    if entry_date not in SETTLEMENT_SET or entry_time > SETTLEMENT_CLOSE:
        return False
    return exit_date > entry_date or exit_time > SETTLEMENT_CLOSE


def mark_trade(
    entry_date: int, entry_time: int, exit_date: int, exit_time: int,
    span_days: int = 1,
) -> RolloverMark:
    """標記一筆交易與換月的關係。

    `is_rollover_window` 是寬鬆的鄰近判定（含結算日隔一天），
    只供分組統計用。**判斷基差汙染要看 `spans_rollover`。**
    """
    ent = in_rollover_window(entry_date, entry_time, span_days)
    ext = in_rollover_window(exit_date, exit_time, span_days)
    td = trading_day(exit_date, exit_time)
    settle_dates = {mc_date_to_date(d) for d in SETTLEMENT_SET}
    sd = next((td - timedelta(days=k) for k in range(span_days + 1)
               if td - timedelta(days=k) in settle_dates), None)
    return RolloverMark(
        is_rollover_window=ent or ext,
        spans_rollover=spans_rollover(entry_date, entry_time, exit_date, exit_time),
        settlement_day=sd,
    )
