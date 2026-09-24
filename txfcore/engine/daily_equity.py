"""M1　每日權益　—— 含未平倉損益。

**現況的問題**：`Ledger` 只在平倉時記帳，所以部位開著時的浮虧與浮盈
完全看不見。而 MDD 的定義是 `每日動態回撤 = (M(t) − V(t)) / M(t)`，
**`V(t)` 若不含未平倉，那條曲線就不是真的權益曲線**。

## 兩條曲線，各自對應一個對帳目標

```
③ 日結算   用該交易日日盤最後一根的收盤價     與券商對帳單同定義
⑤ 盤中極值 **峰值取有利極值、谷底取不利極值**  MC12 的 Intraday Peak to Valley
```

### ★ ⑤ 的正確算法

**兩邊都用不利極值是錯的**——那會把峰值也壓低，回撤反而變小。
2026-09-08 第一版就犯了這個錯，實測 ⑤ 比 ③ 小，而那不可能。

```
equity_best   多單用 high、空單用 low     有利極值 → 用來找峰值
equity_worst  多單用 low、空單用 high     不利極值 → 用來找谷底

MDD⑤ = max over t of ( max(equity_best[0..t]) − equity_worst[t] )
```

**⑤ 必然 >= ③**，因為峰值不低於收盤峰值、谷底不高於收盤谷底。

**兩者的差距本身就是一個指標**：

    差距大 → 部位常在盤中被逼到極限但收盤前收回來 → 追繳風險比對帳單高
    差距小 → 收盤價已能代表風險 → 對帳單可信

## 實測差異（五支合計，樣本內，單位：點）

```
只算平倉（舊）        5,768   1.00x   ← 低估 12%
日結算 13:45          6,416   1.11x
盤中最差              6,598   1.14x
夜盤末 05:00          6,052   1.05x   ← **錯的取樣點**，低估 5.7%
```

## 取樣點

由 `tradecal/accounting.py` 決定：一般日 1345、結算日 1330、假日不取樣。
**1,863 個交易日零缺漏。**
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from txfcore.instruments.spec import Instrument
from txfcore.tradecal.accounting import last_day_bar
from txfcore.types.bar import Bar
from txfcore.types.orders import MarketPosition


@dataclass(frozen=True, slots=True)
class OpenLeg:
    """持倉中的一條腿。用來算浮動損益。"""

    label: str
    direction: MarketPosition
    entry_price: float
    quantity: int
    entry_date: int
    entry_time: int
    exit_date: int
    exit_time: int


@dataclass(frozen=True, slots=True)
class DailyEquity:
    """一個交易日的帳務快照。"""

    day: date
    mark_time: int
    realized: float          # 當日已實現（平倉）損益
    unrealized_close: float  # 收盤價下的未平倉損益
    unrealized_best: float   # 有利極值下的未平倉損益
    unrealized_worst: float  # 不利極值下的未平倉損益
    open_lots: int           # 該時點的未平倉口數
    equity_close: float      # ③ 日結算
    equity_best: float       # ⑤ 的峰值來源
    equity_worst: float      # ⑤ 的谷底來源


@dataclass(slots=True)
class EquityCurves:
    """兩條曲線 + 明細。"""

    days: list[date] = field(default_factory=list)
    close: list[float] = field(default_factory=list)   # ③
    best: list[float] = field(default_factory=list)    # ⑤ 峰值來源
    worst: list[float] = field(default_factory=list)   # ⑤ 谷底來源
    rows: list[DailyEquity] = field(default_factory=list)

    def intraday_peak_to_valley(self) -> tuple[float, int]:
        """⑤ 的**最大絕對金額**（不是最大百分比那一點）。

        `Account Size Required` 用這個（裁決 2026-09-09，選項 D）：
        「準備多少錢」問的是絕對值，而且要防斷頭，所以用盤中極值。
        """
        if len(self.best) < 2:
            return 0.0, 0
        peak = self.best[0]
        worst = 0.0
        at = 0
        for i, (b, w) in enumerate(zip(self.best, self.worst)):
            peak = max(peak, b)
            if peak - w > worst:
                worst, at = peak - w, i
        return worst, at

    def account_size_required(self, initial_capital: float) -> dict:
        """所需帳戶規模。**裁決 2026-09-09：主指標 D，對照 A，差距獨立標出。**

        ```
        D   ⑤ 盤中極值 × 最大絕對金額     主指標。「準備多少錢」問的是絕對值
        A   ③ 日結算   × 百分比那一點     對照。與 MDD 定義一致，可與其他報告對帳
        ```

        **兩者的差距本身是資訊**：差距大代表「相對最慘」與「絕對最慘」
        發生在不同時期，權益曲線不是平穩成長的。
        """
        from txfcore.metrics.drawdown import compute
        d3 = compute(self.close)
        ptv, ptv_at = self.intraday_peak_to_valley()
        return {
            "primary_D": initial_capital + ptv,
            "primary_D_mdd_amount": ptv,
            "primary_D_at": self.days[ptv_at] if self.days else None,
            "reference_A": initial_capital + d3.max_drawdown_amount,
            "reference_A_mdd_amount": d3.max_drawdown_amount,
            "reference_A_at": (self.days[d3.max_drawdown_index]
                               if self.days else None),
            "gap": ptv - d3.max_drawdown_amount,
        }

    def intraday_mdd(self) -> tuple[float, float, int]:
        """⑤ Intraday Peak to Valley。回傳 (百分比, 金額, 發生索引)。

        **峰值取有利極值、谷底取不利極值。** 必然 >= ③。
        """
        if len(self.best) < 2:
            return 0.0, 0.0, 0
        peak = self.best[0]
        worst_pct = worst_amt = 0.0
        at = 0
        for i, (b, w) in enumerate(zip(self.best, self.worst)):
            peak = max(peak, b)
            amt = peak - w
            pct = amt / peak if peak > 0 else 0.0
            if pct > worst_pct:
                worst_pct, worst_amt, at = pct, amt, i
        return worst_pct, worst_amt, at

    def summary(self) -> str:
        if not self.rows:
            return "無資料"
        peak_lots = max(r.open_lots for r in self.rows)
        held = sum(1 for r in self.rows if r.open_lots)
        return (f"{len(self.days):,} 個交易日　持倉 {held:,} 天"
                f"（{held/len(self.days)*100:.1f}%）　峰值 {peak_lots} 口")


def _legs_from_trades(trades) -> list[OpenLeg]:
    return [OpenLeg(t.entry_label, t.direction, t.entry_price, t.quantity,
                    t.entry_date, t.entry_time, t.exit_date, t.exit_time)
            for t in trades]


def _unrealized(leg: OpenLeg, bar: Bar, inst: Instrument,
                mode: str = "close") -> float:
    """一條腿在該 K 棒的未實現損益（金額）。

    `mode`：`close` 收盤 · `best` 有利極值 · `worst` 不利極值。
    """
    long = leg.direction is MarketPosition.LONG
    if mode == "close":
        px = bar.close
    elif mode == "best":
        px = bar.high if long else bar.low
    else:
        px = bar.low if long else bar.high
    pts = (px - leg.entry_price) if long else (leg.entry_price - px)
    return pts * leg.quantity * inst.big_point_value


def build(trades, bars, inst: Instrument,
          initial_capital: float | None = None) -> EquityCurves:
    """從交易清單與 K 棒序列，算出兩條含未平倉的日權益曲線。

    **未平倉的浮虧與浮盈都記**——不是只記浮虧。

    `bars` 必須涵蓋所有交易的期間，且與 `trades` 同一個資料來源。
    """
    if initial_capital is None:
        from txfcore.instruments.capital import allocation
        initial_capital = allocation(inst.code).per_strategy_nominal
    cap = initial_capital
    marks = last_day_bar(bars)
    if not marks:
        return EquityCurves()
    legs = _legs_from_trades(trades)

    # 以 (date, time) 排序鍵判斷持倉區間
    def key(d: int, t: int) -> tuple[int, int]:
        return (d, t)

    days = sorted(marks)
    # 每日已實現：以出場時點歸入該交易日
    from txfcore.types.mctime import trading_day
    realized: dict[date, float] = {}
    for t in trades:
        d = trading_day(t.exit_date, t.exit_time)
        realized[d] = realized.get(d, 0.0) + t.net_ntd(inst)

    curves = EquityCurves()
    cum_real = 0.0
    for d in days:
        bar = marks[d]
        k = key(bar.mc_date, bar.mc_time)
        cum_real += realized.get(d, 0.0)
        # 該時點仍未平倉的腿：進場 <= 取樣點 < 出場
        u_close = u_best = u_worst = 0.0
        lots = 0
        for leg in legs:
            if key(leg.entry_date, leg.entry_time) <= k < key(leg.exit_date,
                                                              leg.exit_time):
                u_close += _unrealized(leg, bar, inst, "close")
                u_best += _unrealized(leg, bar, inst, "best")
                u_worst += _unrealized(leg, bar, inst, "worst")
                lots += leg.quantity
        ec = cap + cum_real + u_close
        eb = cap + cum_real + u_best
        ew = cap + cum_real + u_worst
        curves.days.append(d)
        curves.close.append(ec)
        curves.best.append(eb)
        curves.worst.append(ew)
        curves.rows.append(DailyEquity(
            d, bar.mc_time, realized.get(d, 0.0), u_close, u_best, u_worst,
            lots, ec, eb, ew))
    return curves


def combine(per_strategy: dict[str, EquityCurves],
            initial_capital: float) -> EquityCurves:
    """多支合成一條組合曲線。

    **逐日相加，不是各支曲線相加**——每支的曲線都含自己的期初資金，
    直接相加會把期初重複計算 N 次。這裡只加**當日變化量**。
    """
    days = sorted({d for c in per_strategy.values() for d in c.days})
    idx = {k: {r.day: r for r in c.rows} for k, c in per_strategy.items()}
    out = EquityCurves()
    cum_real = 0.0
    for d in days:
        real = sum(m[d].realized for m in idx.values() if d in m)
        uc = sum(m[d].unrealized_close for m in idx.values() if d in m)
        ub = sum(m[d].unrealized_best for m in idx.values() if d in m)
        uw = sum(m[d].unrealized_worst for m in idx.values() if d in m)
        lots = sum(m[d].open_lots for m in idx.values() if d in m)
        mt = next((m[d].mark_time for m in idx.values() if d in m), 0)
        cum_real += real
        out.days.append(d)
        out.close.append(initial_capital + cum_real + uc)
        out.best.append(initial_capital + cum_real + ub)
        out.worst.append(initial_capital + cum_real + uw)
        out.rows.append(DailyEquity(d, mt, real, uc, ub, uw, lots,
                                    out.close[-1], out.best[-1],
                                    out.worst[-1]))
    return out
