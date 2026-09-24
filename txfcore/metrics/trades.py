"""M2　交易統計層 —— 14 個定案指標。

**每一個定義都在 `docs/specs/M2_TRADE_STATS.md` 定案過。** 本模組只是把它們寫成程式碼。

## 定案摘要（2026-09-09）

```
平手        單獨一類，用毛損益定義（淨損益不可能恰為 0，稅隨價變）
Avg Bars    根數與分鐘都報，以分鐘為主
MAE/MFE     1 分 K 取樣，2×2 四格，單位點數
年化        CAGR，日曆年；交易日數獨立輸出
帳戶規模    主 D（⑤×最大絕對）· 對照 A（③×百分比點）  ← 在 daily_equity
單支分母    名目每支
多空拆分    Total / Long / Short 三欄
```

## 未來會有加減碼

資金效率三項（資金報酬率 · CAGR · 最大持有口數）**不假設固定口數**——
口數從交易紀錄讀，不從設定讀。
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field
from datetime import date

from txfcore.instruments.spec import Instrument
from txfcore.types.mctime import mc_date_to_date, trading_day
from txfcore.types.orders import MarketPosition

FLAT_EPS = 1e-9   # 毛損益 |x| < 這個值 = 平手


# ---------------------------------------------------------------------------
# 資料結構
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Stats:
    """一組交易的 14 個指標。**欄位順序對齊 M2_TRADE_STATS.md 的分組。**"""

    # 判斷賺不賺
    profit_factor: float = 0.0
    win_rate: float = 0.0            # %，**平手不算贏也不算輸**
    # 判斷賺賠結構
    avg_win: float = 0.0
    avg_loss: float = 0.0            # 負數
    payoff_ratio: float = 0.0        # |avg_win / avg_loss|
    # 判斷撐不撐得住
    max_consec_losses: int = 0
    # （所需帳戶規模在 daily_equity，需要權益曲線）
    # 判斷交易頻率
    n_trades: int = 0
    n_wins: int = 0
    n_losses: int = 0
    n_flat: int = 0                  # **平手單獨一類**
    # 判斷成本侵蝕
    total_commission: float = 0.0    # 手續費
    total_tax: float = 0.0           # 期交稅
    total_slippage_points: float = 0.0   # 滑價，點數（含滑價模式時才有值）
    # 判斷資金效率
    net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    return_on_capital: float = 0.0   # 淨利 / 期初
    cagr: float = 0.0                # 日曆年
    calendar_years: float = 0.0
    trading_days: int = 0            # 獨立事實
    max_contracts_held: int = 0      # 從交易紀錄讀，不從設定讀
    # 持倉時間
    avg_bars_win: float = 0.0        # 各支自己的 K 棒根數（對 MC 用）
    avg_bars_loss: float = 0.0
    avg_minutes_win: float = 0.0     # **主指標。日曆時間，含夜盤空檔與週末**
    avg_minutes_loss: float = 0.0    #   — 那才是真正暴露的時間
    cagr_defined: bool = True        # 總報酬 <= -100% 時為 False
    period_is_backtest: bool = False # 年數是否用回測期間（否則是首末筆）


@dataclass(frozen=True, slots=True)
class Excursion:
    """MAE / MFE 的 2×2。單位：點。**1 分 K 取樣。**

    ```
    獲利單 MAE   贏的單曾經虧多深   → 停損不能再緊的界線
    獲利單 MFE   贏的單最多賺過     → 與實際均賺比 = 回吐
    虧損單 MAE   輸的單虧到多深     → 停損有沒有真的生效
    虧損單 MFE   輸的單曾經賺過     → 停利設太遠的證據
    ```

    **1 分 K 仍略微高估**（進場那一分鐘含進場前的價格），真正精確要 tick。
    """

    win_mae: float = 0.0
    win_mfe: float = 0.0
    loss_mae: float = 0.0
    loss_mfe: float = 0.0
    n_win: int = 0
    n_loss: int = 0
    giveback_pct: float = 0.0        # 1 − 實際均賺 / 獲利單 MFE
    sampling: str = "1min"           # 標註取樣來源


# ---------------------------------------------------------------------------
# 分類
# ---------------------------------------------------------------------------

def classify(t) -> str:
    """**平手用毛損益定義。** 回傳 'win' / 'loss' / 'flat'。"""
    g = t.gross_points
    if abs(g) < FLAT_EPS:
        return "flat"
    return "win" if g > 0 else "loss"


def _consecutive_losses(trades) -> int:
    """最長連續虧損。**平手不中斷也不累加。**"""
    best = cur = 0
    for t in trades:
        c = classify(t)
        if c == "loss":
            cur += 1
            best = max(best, cur)
        elif c == "win":
            cur = 0
        # flat：略過
    return best


def _bar_count(t, index: dict | None) -> int:
    """持倉幾根該支自己的 K 棒。沒給 index 就回 0。"""
    if not index:
        return 0
    i = index.get((t.entry_date, t.entry_time))
    j = index.get((t.exit_date, t.exit_time))
    return (j - i) if (i is not None and j is not None and j >= i) else 0


def _minutes(t) -> float:
    """持倉分鐘數（日曆時間）。**跨支可比的主指標。**"""
    from datetime import datetime
    from txfcore.types.mctime import mc_time_to_time
    a = datetime.combine(mc_date_to_date(t.entry_date), mc_time_to_time(t.entry_time))
    b = datetime.combine(mc_date_to_date(t.exit_date), mc_time_to_time(t.exit_time))
    return max((b - a).total_seconds() / 60.0, 0.0)


# ---------------------------------------------------------------------------
# 主計算
# ---------------------------------------------------------------------------

def compute(trades, inst: Instrument, initial_capital: float,
            bar_index: dict | None = None,
            slippage_points_per_side: float = 0.0,
            period: tuple[date, date] | None = None) -> Stats:
    """14 個指標。

    `bar_index`：{(mc_date, mc_time): i}，該支自己的 Data1，用來算根數。
    `slippage_points_per_side`：含滑價模式時傳入，用來算滑價總額。
    `period`：**回測期間**（起, 迄）。CAGR 的年數用它，不用第一筆到最後一筆——
    策略閒置的那一年，資金一樣被綁著。沒給就退回第一筆到最後一筆並標註。
    """
    if not trades:
        return Stats()
    seq = sorted(trades, key=lambda t: (t.exit_date, t.exit_time))
    pnl = [t.net_ntd(inst) for t in seq]
    cls = [classify(t) for t in seq]
    wins = [p for p, c in zip(pnl, cls) if c == "win"]
    losses = [p for p, c in zip(pnl, cls) if c == "loss"]
    n_flat = sum(1 for c in cls if c == "flat")
    gp, gl = sum(wins), sum(losses)
    net = sum(pnl)

    # 成本拆分
    from txfcore.costs.fees import tax as tax_fn
    comm = sum(inst.fee_per_side * 2 * t.quantity for t in seq)
    tx = sum((tax_fn(inst, t.entry_price) + tax_fn(inst, t.exit_price)) * t.quantity
             for t in seq)
    slip = slippage_points_per_side * 2 * sum(t.quantity for t in seq)

    # 年化。**年數用回測期間**，不是第一筆到最後一筆
    if period:
        d0, d1 = period
    else:
        d0 = trading_day(seq[0].entry_date, seq[0].entry_time)
        d1 = trading_day(seq[-1].exit_date, seq[-1].exit_time)
    years = (d1 - d0).days / 365.25
    tdays = len({trading_day(t.exit_date, t.exit_time) for t in seq})
    roc = net / initial_capital if initial_capital else 0.0
    # CAGR 無定義的兩種情況：權益歸零（roc <= -1）、期間不滿一天。
    # **標為無定義，不拋錯也不靜默給怪數字。**
    cagr_ok = roc > -1.0 and years >= 1 / 365.25
    cagr = ((1 + roc) ** (1 / years) - 1) if cagr_ok else -1.0
    years = max(years, 0.0)

    # 持倉
    bw = [_bar_count(t, bar_index) for t, c in zip(seq, cls) if c == "win"]
    bl = [_bar_count(t, bar_index) for t, c in zip(seq, cls) if c == "loss"]
    mw = [_minutes(t) for t, c in zip(seq, cls) if c == "win"]
    ml = [_minutes(t) for t, c in zip(seq, cls) if c == "loss"]
    avg = lambda v: sum(v) / len(v) if v else 0.0

    return Stats(
        profit_factor=gp / abs(gl) if gl else 0.0,
        win_rate=len(wins) / len(seq) * 100,
        avg_win=avg(wins), avg_loss=avg(losses),
        payoff_ratio=abs(avg(wins) / avg(losses)) if losses and avg(losses) else 0.0,
        max_consec_losses=_consecutive_losses(seq),
        n_trades=len(seq), n_wins=len(wins), n_losses=len(losses), n_flat=n_flat,
        total_commission=comm, total_tax=tx, total_slippage_points=slip,
        net_profit=net, gross_profit=gp, gross_loss=gl,
        return_on_capital=roc, cagr=cagr, calendar_years=years,
        trading_days=tdays,
        max_contracts_held=max(t.quantity for t in seq),
        avg_bars_win=avg(bw), avg_bars_loss=avg(bl),
        avg_minutes_win=avg(mw), avg_minutes_loss=avg(ml),
        cagr_defined=cagr_ok,
        period_is_backtest=period is not None,
    )


def by_direction(trades, inst: Instrument, initial_capital: float,
                 bar_index: dict | None = None,
                 slippage_points_per_side: float = 0.0,
                 period: tuple[date, date] | None = None) -> dict[str, Stats]:
    """Total / Long / Short 三欄。**全部明確標示。**"""
    longs = [t for t in trades if t.direction is MarketPosition.LONG]
    shorts = [t for t in trades if t.direction is MarketPosition.SHORT]
    kw = dict(bar_index=bar_index, slippage_points_per_side=slippage_points_per_side,
              period=period)
    return {
        "Total": compute(trades, inst, initial_capital, **kw),
        "Long": compute(longs, inst, initial_capital, **kw),
        "Short": compute(shorts, inst, initial_capital, **kw),
    }


def periodical(trades, inst: Instrument, by: str = "month"
               ) -> list[tuple[str, int, float]]:
    """年 / 月損益表。[(期間, 筆數, 淨損益)]。

    切點用 `trading_day()`——**與 K 棒層同一個定義**，否則夜盤損益歸錯月份。
    """
    b: dict[str, list[float]] = collections.defaultdict(list)
    for t in trades:
        d = trading_day(t.exit_date, t.exit_time)
        key = f"{d:%Y}" if by == "year" else f"{d:%Y-%m}"
        b[key].append(t.net_ntd(inst))
    return [(k, len(v), sum(v)) for k, v in sorted(b.items())]


def excursion(trades, inst: Instrument, minute_bars, minute_index: dict
              ) -> Excursion:
    """MAE / MFE 的 2×2，**1 分 K 取樣**，單位點數。

    `minute_bars` 與 `minute_index` 必須是 1 分 K——
    用 Data1 會高估 MAE（L1 實測高估 27%）。
    """
    W = dict(mae=[], mfe=[], pnl=[])
    Lo = dict(mae=[], mfe=[], pnl=[])
    for t in trades:
        c = classify(t)
        if c == "flat":
            continue
        i = minute_index.get((t.entry_date, t.entry_time))
        j = minute_index.get((t.exit_date, t.exit_time))
        if i is None or j is None or j < i:
            continue
        seg = minute_bars[i:j + 1]
        hi = max(b.high for b in seg)
        lo = min(b.low for b in seg)
        long = t.direction is MarketPosition.LONG
        mfe = (hi - t.entry_price) if long else (t.entry_price - lo)
        mae = (t.entry_price - lo) if long else (hi - t.entry_price)
        d = W if c == "win" else Lo
        d["mae"].append(max(mae, 0.0))
        d["mfe"].append(max(mfe, 0.0))
        d["pnl"].append(abs(t.gross_points))
    avg = lambda v: sum(v) / len(v) if v else 0.0
    wm = avg(W["mfe"])
    return Excursion(
        win_mae=avg(W["mae"]), win_mfe=wm,
        loss_mae=avg(Lo["mae"]), loss_mfe=avg(Lo["mfe"]),
        n_win=len(W["mae"]), n_loss=len(Lo["mae"]),
        giveback_pct=(1 - avg(W["pnl"]) / wm) * 100 if wm else 0.0,
        sampling="1min",
    )


def rows(s: Stats, inst: Instrument) -> list[tuple[str, str]]:
    """給報告用。**順序對齊 M2_TRADE_STATS.md 的分組。**"""
    return [
        ("── 判斷賺不賺 ──", ""),
        ("Profit Factor", f"{s.profit_factor:.4f}"),
        ("勝率", f"{s.win_rate:.2f}%"),
        ("── 判斷賺賠結構 ──", ""),
        ("平均獲利", f"{s.avg_win:,.0f}"),
        ("平均虧損", f"{s.avg_loss:,.0f}"),
        ("賺賠比", f"{s.payoff_ratio:.3f}"),
        ("── 判斷撐不撐得住 ──", ""),
        ("最大連續虧損", f"{s.max_consec_losses}"),
        ("── 判斷交易頻率 ──", ""),
        ("總交易筆數", f"{s.n_trades}"),
        ("　贏 / 輸 / 平手", f"{s.n_wins} / {s.n_losses} / {s.n_flat}"),
        ("── 判斷成本侵蝕 ──", ""),
        ("手續費總額", f"{s.total_commission:,.0f}"),
        ("期交稅總額", f"{s.total_tax:,.0f}"),
        ("滑價總額（點）", f"{s.total_slippage_points:,.0f}"),
        ("── 判斷資金效率 ──", ""),
        ("淨利", f"{s.net_profit:,.0f}"),
        ("資金報酬率", f"{s.return_on_capital*100:.2f}%"),
        ("年化 CAGR", f"{s.cagr*100:.2f}%" if s.cagr_defined else "無定義（≤−100%）"),
        ("　日曆年數", f"{s.calendar_years:.2f}"
                     + ("（回測期間）" if s.period_is_backtest else "（首末筆，未給期間）")),
        ("　交易日數", f"{s.trading_days}"),
        ("最大持有口數", f"{s.max_contracts_held}"),
        ("── 持倉時間 ──", ""),
        ("獲利單平均日曆時間", f"{s.avg_minutes_win:,.0f} 分（{s.avg_minutes_win/60:.1f} 小時）"),
        ("虧損單平均日曆時間", f"{s.avg_minutes_loss:,.0f} 分（{s.avg_minutes_loss/60:.1f} 小時）"),
        ("獲利單平均根數（對 MC）", f"{s.avg_bars_win:.1f}"),
        ("虧損單平均根數（對 MC）", f"{s.avg_bars_loss:.1f}"),
    ]
