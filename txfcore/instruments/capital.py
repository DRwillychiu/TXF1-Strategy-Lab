"""資金配置　—— 雙帳戶結構。

**2026-09-08 定案。**

```
帳戶 A（多）  L1 · L3 · L5   最大 6 口
帳戶 B（空）  L2 · L4        最大 4 口
```

## 微台（實戰用）

```
總本金        300,000
帳戶 A（多）  200,000
帳戶 B（空）  100,000
名目每支       60,000   = 總 / 5
```

> **「每支 6 萬」是名目分攤**，用來算單支的 MDD 百分比。
> 保證金在帳戶層級共用，不是每支真的隔離持有 6 萬。
>
> 注意名目分攤與帳戶配置**不一致**：
> 帳戶 A 有 3 支但只有 200,000（名目應為 180,000），
> 帳戶 B 有 2 支卻只有 100,000（名目應為 120,000）。
> 這是刻意的——**多單出手機率高**，所以多分配資金給多單帳戶。

## 三商品等比例

點值比 `TMF : MXF : TXF = 10 : 50 : 200 = 1 : 5 : 20`。
資金按同一比例，**三者的「可承受點數」才會相同**（各 3,000 點）。

```
商品   點值   每支本金     帳戶 A       帳戶 B       總本金
TMF     10     60,000     200,000     100,000     300,000
MXF     50    300,000   1,000,000     500,000   1,500,000
TXF    200  1,200,000   4,000,000   2,000,000   6,000,000
```

> **2026-09-08 修正**：原規劃小台 240,000，比例是 1 : 4 : 20，
> 可承受點數只有 2,400，比另外兩個少 20%。

## MDD 的分母

**同一組交易，三種分母三個答案。三個都報，各自標明。**

```
單支 MDD%     分母 = 名目每支
帳戶 MDD%     分母 = 該帳戶本金
總體 MDD%     分母 = 總本金
```
"""

from __future__ import annotations

from dataclasses import dataclass

LONG_STRATEGIES = ("L1", "L3", "L5")
SHORT_STRATEGIES = ("L2", "L4")
ALL_STRATEGIES = LONG_STRATEGIES + SHORT_STRATEGIES

LONG_ACCOUNT = "A_LONG"
SHORT_ACCOUNT = "B_SHORT"

# 微台的基準配置。其餘商品按點值比例放大。
_BASE_TOTAL = 300_000
_BASE_LONG = 200_000
_BASE_SHORT = 100_000
_BASE_POINT_VALUE = 10          # 微台

# 點值。與 instruments/spec.py 一致，這裡重列是為了讓本模組可獨立閱讀。
POINT_VALUE = {"TMF": 10, "MXF": 50, "TXF": 200}
LOTS_PER_STRATEGY = 2


@dataclass(frozen=True, slots=True)
class Allocation:
    instrument: str
    total: float
    long_account: float
    short_account: float
    per_strategy_nominal: float
    point_value: int
    lots: int

    @property
    def scale(self) -> float:
        return self.point_value / _BASE_POINT_VALUE

    @property
    def points_of_cushion(self) -> float:
        """名目每支能承受幾點的不利走勢。**三商品必須相同。**"""
        return self.per_strategy_nominal / (self.point_value * self.lots)

    def account_capital(self, account: str) -> float:
        return self.long_account if account == LONG_ACCOUNT else self.short_account

    def rows(self) -> list[tuple[str, str]]:
        return [
            ("總本金", f"{self.total:,.0f}"),
            ("帳戶 A（多）L1·L3·L5", f"{self.long_account:,.0f}"),
            ("帳戶 B（空）L2·L4", f"{self.short_account:,.0f}"),
            ("名目每支", f"{self.per_strategy_nominal:,.0f}"),
            ("可承受點數", f"{self.points_of_cushion:,.0f}"),
        ]


def allocation(instrument: str = "TMF") -> Allocation:
    """該商品的資金配置。**按點值等比例放大，不是自訂數字。**"""
    if instrument not in POINT_VALUE:
        raise ValueError(f"未知商品 {instrument!r}，可用 {sorted(POINT_VALUE)}")
    pv = POINT_VALUE[instrument]
    k = pv / _BASE_POINT_VALUE
    return Allocation(
        instrument=instrument,
        total=_BASE_TOTAL * k,
        long_account=_BASE_LONG * k,
        short_account=_BASE_SHORT * k,
        per_strategy_nominal=_BASE_TOTAL / len(ALL_STRATEGIES) * k,
        point_value=pv,
        lots=LOTS_PER_STRATEGY,
    )


def account_of(strategy_key: str) -> str:
    """L1 → A_LONG，L2 → B_SHORT。"""
    if strategy_key in LONG_STRATEGIES:
        return LONG_ACCOUNT
    if strategy_key in SHORT_STRATEGIES:
        return SHORT_ACCOUNT
    raise ValueError(f"未知策略 {strategy_key!r}")


def max_lots(account: str) -> int:
    """該帳戶的最大口數（全部策略同時開倉）。"""
    n = len(LONG_STRATEGIES if account == LONG_ACCOUNT else SHORT_STRATEGIES)
    return n * LOTS_PER_STRATEGY


# MC12 的回測設定。**與我們的等比例配置不同，僅用於 anchor 對帳。**
# CLAUDE.md：單一策略 2,000,000 本金、2 口大台。
MC_BACKTEST_CAPITAL = 2_000_000
MC_INSTRUMENT = "TXF"
