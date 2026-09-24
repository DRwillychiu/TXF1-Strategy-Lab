"""帳務日曆　—— 每日結算的取樣點。

**這與策略用的日線是兩件事，不可共用。**

```
策略用的日線   各支不同（L5 用 NIGHT_FIRST，其餘 DAY_FIRST）
               → 策略「看到」的市場
帳務用的取樣   一律日盤最後一根
               → 帳戶「結算」的時點
```

## 取樣點規則

```
一般日   1345
結算日   1330    近月合約在 13:30 停止交易
假日     不存在於交易日清單，自然不取樣
```

**2026-09-08 用 141,302 根 15M 實測，零例外：**

```
結算日   92 天    末根戳記全部 1330      100%
一般日 1,771 天   末根戳記全部 1345      100%
連假     57 次    交易日自然不在清單中
```

> 因為結算日的 1330 就是那天最後一根，
> **「取該交易日日盤最後一根」這個規則同時涵蓋兩種情況——不需要特判。**

## 為什麼不能用夜盤末 05:00

TAIFEX 的每日結算在**日盤 13:45**，夜盤屬於**次一交易日**。

實測：用 05:00 取樣，組合 MDD 是 6,052 點；用 13:45 是 6,416 點。
**低估 5.7%**——因為把次日的行情算進了今天。
"""

from __future__ import annotations

from datetime import date

from txfcore.tradecal.settlement import is_settlement_day
from txfcore.types.mctime import date_to_mc_date, trading_day

NORMAL_MARK_TIME = 1345      # 一般日的日盤收盤
SETTLEMENT_MARK_TIME = 1330  # 結算日近月停止交易
DAY_SESSION_START = 846      # 日盤第一根（08:45 開盤，08:46 收盤）


def mark_time(day: date) -> int:
    """該交易日的帳務取樣時刻。"""
    return (SETTLEMENT_MARK_TIME if is_settlement_day(date_to_mc_date(day))
            else NORMAL_MARK_TIME)


def is_mark_bar(mc_date: int, mc_time: int) -> bool:
    """這根 K 棒是不是該交易日的帳務取樣點。

    **等價於「日盤最後一根」**，但寫成顯式規則，
    因為資料若缺了那一根，用「最後一根」會靜默取到別的時刻。
    """
    if not (DAY_SESSION_START <= mc_time <= NORMAL_MARK_TIME):
        return False
    return mc_time == mark_time(trading_day(mc_date, mc_time))


def last_day_bar(bars) -> dict:
    """從 K 棒序列取出每個交易日的帳務取樣棒。

    回傳 {交易日: bar}。**缺漏的交易日不會出現在結果裡**，
    呼叫端必須自己決定要不要補——不靜默補值。
    """
    out: dict = {}
    for b in bars:
        if is_mark_bar(b.mc_date, b.mc_time):
            out[trading_day(b.mc_date, b.mc_time)] = b
    return out


def missing_mark_days(bars) -> list[date]:
    """有日盤資料、卻沒有帳務取樣棒的交易日。

    **資料異常的偵測點。** 2021-09-01~03 那三天無夜盤，
    但日盤完整，所以不會出現在這裡；
    真的缺 1345/1330 那一根才會被抓到。
    """
    have_day: dict = {}
    for b in bars:
        if DAY_SESSION_START <= b.mc_time <= NORMAL_MARK_TIME:
            d = trading_day(b.mc_date, b.mc_time)
            have_day.setdefault(d, []).append(b.mc_time)
    marks = set(last_day_bar(bars))
    return sorted(d for d in have_day if d not in marks)
