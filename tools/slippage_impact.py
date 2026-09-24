#!/usr/bin/env python3
r"""滑價影響對照。

```powershell
python tools\slippage_impact.py "data\mc_export\TXF1 1 分鐘.txt"
```

**兩組並排：關閉 vs 5 點/邊/口。**

裁決 2026-09-09：
```
點數  5 tick = 5 點，三商品皆同
方向  一律不利
單型  全部含限價（壓力測試：流動性極差時仍是否賺錢）
開關  預設關閉，做成可對照
```
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
from txfcore.metrics.drawdown import compute, equity_curve
from txfcore.parity.windows import split
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
from txfcore.types.mctime import DayOfWeek, day_of_week


def weekly_bars(dd):
    wk, buf = [], []
    for x in dd:
        buf.append(x)
        if day_of_week(x.mc_date) is DayOfWeek.FRI:
            wk.append(Bar(x.mc_date, x.mc_time, buf[0].open,
                          max(y.high for y in buf), min(y.low for y in buf),
                          x.close, sum(y.volume for y in buf), len(buf)))
            buf = []
    if buf:
        x = buf[-1]
        wk.append(Bar(x.mc_date, x.mc_time, buf[0].open,
                      max(y.high for y in buf), min(y.low for y in buf),
                      x.close, sum(y.volume for y in buf), len(buf)))
    return wk


def cached(cd, name, fn):
    f = Path(cd) / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = fn()
    f.write_bytes(pickle.dumps(v))
    return v


def stats(x, inst):
    if not x:
        return dict(n=0, net=0.0, pf=0.0, wr=0.0, avg=0.0)
    p = [t.net_ntd(inst) for t in x]
    w = [v for v in p if v > 0]
    l = [v for v in p if v < 0]
    return dict(n=len(x), net=sum(p),
                pf=sum(w) / -sum(l) if l else 0.0,
                wr=len(w) / len(p) * 100, avg=sum(p) / len(p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    ap.add_argument("--instrument", default="TMF", choices=("TMF", "MXF", "TXF"))
    args = ap.parse_args()
    cd = args.cache_dir
    inst = {"TMF": TMF, "MXF": MXF, "TXF": TXF}[args.instrument]
    alloc = allocation(args.instrument)

    print(banner(args.data))
    check(args.data)
    print("讀取與聚合…")
    mins = list(MC12MinuteSource(args.data).stream())
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m45 = cached(cd, "45m", lambda: list(aggregate_bars(mins, 45)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: build_daily(mins, DAY_FIRST))
    mdn = cached(cd, "dn", lambda: build_daily(mins, NIGHT_FIRST))
    mw = cached(cd, "w", lambda: weekly_bars(md))
    mwn = cached(cd, "wn", lambda: weekly_bars(mdn))

    print(f"\n滑價影響　{inst.name}　5 點/邊/口　名目每支 "
          f"{alloc.per_strategy_nominal:,.0f}")
    print(f"  來回 {STRESS.round_trip_points(inst, inst.default_lots):.0f} 點"
          f" = {STRESS.round_trip_money(inst, inst.default_lots):,.0f} 元"
          f"（{inst.default_lots} 口）\n")
    print(f"  {'':4}{'筆數':>13}{'淨利':>21}{'PF':>15}{'平均/筆':>17}")
    print(f"  {'':4}{'off':>6}{'5pt':>7}{'off':>10}{'5pt':>11}"
          f"{'off':>7}{'5pt':>8}{'off':>8}{'5pt':>9}")
    print("  " + "-" * 68)

    spec = (("L1", L1TrendLong, m45, md, mw),
            ("L2", L2TrendShort, m60, None, None),
            ("L3", L3ConsolLong, m15, m60, md),
            ("L4", L4ConsolShort, m15, m60, md),
            ("L5", L5BreakoutLong, m15, mdn, mwn))
    tot = {"off": 0.0, "on": 0.0}
    curves = {"off": {}, "on": {}}
    for k, cls, d1, d2, d3 in spec:
        row = {}
        for tag, sl in (("off", OFF), ("on", STRESS)):
            s = cls()
            r = (BacktestRunner(s, inst, slippage=sl).run(d1) if d2 is None
                 else MultiStreamRunner(s, inst, warmup_bars=200,
                                        slippage=sl).run(d1, d2, d3))
            ins, _, _ = split(r.trades)
            row[tag] = stats(ins, inst)
            curves[tag][k] = sorted(ins, key=lambda t: (t.exit_date, t.exit_time))
            tot[tag] += row[tag]["net"]
        print(f"  {k:4}{row['off']['n']:>6}{row['on']['n']:>7}"
              f"{row['off']['net']:>10,.0f}{row['on']['net']:>11,.0f}"
              f"{row['off']['pf']:>7.3f}{row['on']['pf']:>8.3f}"
              f"{row['off']['avg']:>8,.0f}{row['on']['avg']:>9,.0f}")
    print("  " + "-" * 68)
    d = (tot["on"] - tot["off"]) / abs(tot["off"]) * 100 if tot["off"] else 0
    print(f"  {'合計':4}{'':>13}{tot['off']:>10,.0f}{tot['on']:>11,.0f}"
          f"{'':>15}   淨利變化 {d:+.1f}%")

    print("\n  【總體 MDD】分母 = 總本金 " + f"{alloc.total:,.0f}")
    for tag, label in (("off", "滑價關閉"), ("on", "滑價 5 點")):
        allt = sorted([t for v in curves[tag].values() for t in v],
                      key=lambda t: (t.exit_date, t.exit_time))
        dd = compute(equity_curve(alloc.total,
                                  [t.net_ntd(inst) for t in allt]))
        print(f"    {label:<10}{len(allt):>5} 筆"
              f"　MDD {dd.max_drawdown*100:>6.2f}%"
              f" = {dd.max_drawdown_amount:>9,.0f}")

    print("\n" + "=" * 74)
    print("★ 筆數會變 —— 滑價改變成交價 → 改變部位 → 改變後續訊號。")
    print("  **這是連鎖效應，不是單純的成本扣減。**")
    print("★ 滑價標為 assumed（設定值），不是 measured。")
    print("  真實值要從實戰紀錄量：訊號價 vs 成交價。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
