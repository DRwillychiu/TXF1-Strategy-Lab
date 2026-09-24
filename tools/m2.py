#!/usr/bin/env python3
r"""M2　交易統計　—— 五支 × 14 指標 × 多空拆分 × 年月表 × MAE/MFE。

```powershell
python tools\m2.py "data\mc_export\TXF1 1 分鐘.txt"
python tools\m2.py "data\mc_export\TXF1 1 分鐘.txt" --slippage       # 含 5 點滑價
python tools\m2.py "data\mc_export\TXF1 1 分鐘.txt" --only L3        # 只看一支
```

**每個數字都對應 `docs/specs/M2_TRADE_STATS.md` 的一項定案。**
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from txfcore.costs.slippage import OFF, STRESS
from txfcore.instruments.capital import allocation
from txfcore.instruments.spec import MXF, TMF, TXF
from txfcore.metrics.trades import by_direction, compute, excursion, periodical, rows
from txfcore.parity.windows import BACKTEST_END, split
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.daily import DAY_FIRST, NIGHT_FIRST, build as build_daily
from txfcore.quotes.guard import banner, check
from txfcore.quotes.history import MC12MinuteSource
from txfcore.runtime.backtest import BacktestRunner
from txfcore.runtime.multi import MultiStreamRunner
from txfcore.strategies.l1_trendlong import L1TrendLong
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.strategies.l3_consollong import L3ConsolLong
from txfcore.strategies.l4_consolshort import L4ConsolShort
from txfcore.strategies.l5_breakoutlong import L5BreakoutLong
from txfcore.types.bar import Bar
from txfcore.types.mctime import DayOfWeek, day_of_week, mc_date_to_date


def weekly_bars(dd):
    wk, buf = [], []
    for x in dd:
        buf.append(x)
        if day_of_week(x.mc_date) is DayOfWeek.FRI:
            wk.append(Bar(x.mc_date, x.mc_time, buf[0].open, max(y.high for y in buf),
                          min(y.low for y in buf), x.close,
                          sum(y.volume for y in buf), len(buf)))
            buf = []
    if buf:
        x = buf[-1]
        wk.append(Bar(x.mc_date, x.mc_time, buf[0].open, max(y.high for y in buf),
                      min(y.low for y in buf), x.close,
                      sum(y.volume for y in buf), len(buf)))
    return wk


def cached(cd, name, fn):
    f = Path(cd) / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = fn()
    f.write_bytes(pickle.dumps(v))
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    ap.add_argument("--instrument", default="TMF", choices=("TMF", "MXF", "TXF"))
    ap.add_argument("--slippage", action="store_true", help="含 5 點滑價")
    ap.add_argument("--only", default=None, help="只看某一支，例如 L3")
    args = ap.parse_args()
    cd = args.cache_dir
    inst = {"TMF": TMF, "MXF": MXF, "TXF": TXF}[args.instrument]
    alloc = allocation(args.instrument)
    slip = STRESS if args.slippage else OFF
    slip_pts = slip.points(inst, __import__("txfcore.types.orders", fromlist=["OrderType"]).OrderType.MARKET)

    print(banner(args.data))
    check(args.data)
    print("讀取與聚合…")
    mins = list(MC12MinuteSource(args.data).stream())
    midx = {(b.mc_date, b.mc_time): i for i, b in enumerate(mins)}
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m45 = cached(cd, "45m", lambda: list(aggregate_bars(mins, 45)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: build_daily(mins, DAY_FIRST))
    mdn = cached(cd, "dn", lambda: build_daily(mins, NIGHT_FIRST))
    mw = cached(cd, "w", lambda: weekly_bars(md))
    mwn = cached(cd, "wn", lambda: weekly_bars(mdn))

    period = (mc_date_to_date(mins[0].mc_date), mc_date_to_date(BACKTEST_END))
    cap = alloc.per_strategy_nominal
    print(f"\n{inst.name}　名目每支 {cap:,.0f}　滑價 {slip.name}"
          f"　回測期間 {period[0]} ~ {period[1]}")

    spec = (("L1", L1TrendLong, m45, md, mw, m45),
            ("L2", L2TrendShort, m60, None, None, m60),
            ("L3", L3ConsolLong, m15, m60, md, m15),
            ("L4", L4ConsolShort, m15, m60, md, m15),
            ("L5", L5BreakoutLong, m15, mdn, mwn, m15))
    for k, cls, d1, d2, d3, bars in spec:
        if args.only and k != args.only:
            continue
        s = cls()
        r = (BacktestRunner(s, inst, slippage=slip).run(d1) if d2 is None
             else MultiStreamRunner(s, inst, warmup_bars=200,
                                    slippage=slip).run(d1, d2, d3))
        ins, _, _ = split(r.trades)
        bidx = {(b.mc_date, b.mc_time): i for i, b in enumerate(bars)}
        print(f"\n{'═'*70}\n{k}　{s.config.name}　樣本內 {len(ins)} 筆\n{'═'*70}")

        st = compute(ins, inst, cap, bidx, slip_pts, period)
        for key, val in rows(st, inst):
            print(f"  {key:<26}{val:>28}" if val else f"\n  {key}")

        print("\n  ── 多空拆分 ──")
        print(f"  {'':8}{'筆數':>6}{'PF':>8}{'勝率':>8}{'淨利':>11}{'賺賠比':>8}")
        for nm, d in by_direction(ins, inst, cap, bidx, slip_pts, period).items():
            print(f"  {nm:<8}{d.n_trades:>6}{d.profit_factor:>8.3f}"
                  f"{d.win_rate:>7.1f}%{d.net_profit:>11,.0f}{d.payoff_ratio:>8.3f}")

        print("\n  ── 年度損益 ──")
        for y, n, v in periodical(ins, inst, "year"):
            print(f"  {y}  {n:>4} 筆  {v:>10,.0f}")

        e = excursion(ins, inst, mins, midx)
        print(f"\n  ── MAE / MFE（{e.sampling}，點）──")
        print(f"  {'':10}{'MAE':>7}{'MFE':>7}")
        print(f"  {'獲利單':<10}{e.win_mae:>7.0f}{e.win_mfe:>7.0f}   回吐 {e.giveback_pct:.0f}%")
        print(f"  {'虧損單':<10}{e.loss_mae:>7.0f}{e.loss_mfe:>7.0f}")
        print(f"  n = {e.n_win} + {e.n_loss}（缺 K 棒對應的略過）")

    print(f"\n{'═'*70}")
    print("★ 平手用毛損益定義　·　持倉時間以日曆分鐘為主　·　MAE/MFE 用 1 分 K")
    print("★ CAGR 用回測期間日曆年　·　口數從交易紀錄讀")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
