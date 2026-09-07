"""日線的兩種定義。

**2026-09-07 實測：兩支策略需要不同的定義，而且差異極大。**

```
定義              L5 筆數   L3 筆數   L4 筆數
DAY_FIRST  (A)      169       379       83
NIGHT_FIRST(B)      162       357       84
MC anchor           162       376       82
```

`NIGHT_FIRST` 讓 L5 **逐位命中 162**，但讓 L3 從 +3 掉到 −19。

## 為什麼會不同

MultiCharts 的**每一張圖各有自己的 session 設定**。而且：

    L5   Data2 = Daily 是**箱體本身**   → 對定義極度敏感
    L3   Data3 = Daily 只算 MA 濾網     → 敏感度低

## 哪一個「對」

`NIGHT_FIRST` 符合 TAIFEX 的官方定義：盤後交易時段 15:00–次日 05:00
**屬於次一交易日**。所以 B 在制度上是對的。

但 L3/L4 用 A 才接近 anchor。這代表**要嘛 MC 各張圖設定不同，
要嘛 L3/L4 還有別的補償性誤差**。

**所以做成每支可設定，並把不確定性寫在這裡，而不是全域猜一個。**
"""

from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from txfcore.types.bar import Bar
from txfcore.types.mctime import is_night_tail, mc_date_to_date

DAY_FIRST = "day_first"      # 日盤 + 隨後夜盤（開盤 08:45，收盤次日 05:00）
NIGHT_FIRST = "night_first"  # 前一夜盤 + 日盤（開盤前日 15:00，收盤 13:45）


def build(mins: Iterable[Bar], mode: str = DAY_FIRST) -> list[Bar]:
    """把 1 分 K 聚合成日線。

    `mode` 決定夜盤歸屬哪一個交易日。**這不是細節，是第一級參數。**
    """
    if mode not in (DAY_FIRST, NIGHT_FIRST):
        raise ValueError(f"未知的日線定義 {mode!r}")
    buckets: dict = {}
    for m in mins:
        d = mc_date_to_date(m.mc_date)
        if mode == DAY_FIRST:
            key = d - timedelta(days=1) if is_night_tail(m.mc_time) else d
        else:
            key = d + timedelta(days=1) if m.mc_time >= 1500 else d
        buckets.setdefault(key, []).append(m)
    out = []
    for _, g in sorted(buckets.items()):
        last = g[-1]
        out.append(Bar(last.mc_date, last.mc_time, g[0].open,
                       max(x.high for x in g), min(x.low for x in g),
                       g[-1].close, sum(x.volume for x in g), len(g)))
    return out


# 每支策略的日線定義。**由對帳結果決定，不是猜的。**
#
#   L5   NIGHT_FIRST 讓筆數逐位命中 162（A 是 169）
#   L3   DAY_FIRST 是 +3，NIGHT_FIRST 是 -19
#   L4   兩者差 1 筆，沿用 DAY_FIRST 與 L3 一致
#   L1   Data2 只算 Daily ATR 上限，敏感度低
PER_STRATEGY: dict[str, str] = {
    "L1_TrendLong": DAY_FIRST,
    "L3_ConsolLong": DAY_FIRST,
    "L4_ConsolShort": DAY_FIRST,
    "L5_BreakoutLong": NIGHT_FIRST,
}


def for_strategy(name: str) -> str:
    return PER_STRATEGY.get(name, DAY_FIRST)
