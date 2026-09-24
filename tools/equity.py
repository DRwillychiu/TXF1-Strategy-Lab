#!/usr/bin/env python3
r"""M1 每日權益　—— 三種 MDD 並排驗證。

```powershell
python tools\equity.py "data\mc_export\TXF1 1 分鐘.txt"
```

輸出：

    取樣點分布     一般日 1345 · 結算日 1330 · 缺漏數
    三種 MDD       ① 只算平倉　③ 日結算　⑤ 盤中極值
    浮動損益極值   浮盈與浮虧都列
    組合 vs 相加   證明「各支 MDD 相加」是錯的

**⑤ 必然 >= ③。若不成立，工具會報錯。**
"""
from __future__ import annotations

import argparse
import collections
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from txfcore.engine.daily_equity import build, combine
from txfcore.instruments.capital import (
    LONG_ACCOUNT, SHORT_ACCOUNT, account_of, allocation, max_lots)
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
from txfcore.tradecal.accounting import last_day_bar, missing_mark_days
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    # **預設微台**（裁決 2026-09-08）——實戰用微台，回測要能對得上。
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

    print("\n【帳務取樣點】")
    marks = last_day_bar(m15)
    miss = missing_mark_days(m15)
    dist = collections.Counter(b.mc_time for b in marks.values())
    print(f"  取樣棒 {len(marks):,} 天　缺漏 {len(miss)} 天")
    for t, n in sorted(dist.items()):
        kind = "結算日" if t == 1330 else "一般日"
        print(f"    戳記 {t}　{kind}　{n:,} 天")
    if miss:
        print(f"    ✗ 缺漏：{[str(d) for d in miss[:5]]}")

    cap = alloc.per_strategy_nominal
    print(f"\n【資金配置】{args.instrument}　點值 {alloc.point_value}"
          f"　固定 {alloc.lots} 口")
    for k, v in alloc.rows():
        print(f"  {k:<22}{v:>14}")
    print(f"  帳戶 A 最大 {max_lots(LONG_ACCOUNT)} 口"
          f"　帳戶 B 最大 {max_lots(SHORT_ACCOUNT)} 口")
    spec = (("L1", L1TrendLong(), m45, md, mw, m45),
            ("L2", L2TrendShort(), m60, None, None, m60),
            ("L3", L3ConsolLong(), m15, m60, md, m15),
            ("L4", L4ConsolShort(), m15, m60, md, m15),
            ("L5", L5BreakoutLong(), m15, mdn, mwn, m15))
    curves, trades = {}, {}
    print(f"\n【三種 MDD　單支】分母 = 名目每支 {cap:,.0f}")
    print(f"  {'':4}{'筆數':>6}{'① 只算平倉':>13}{'③ 日結算':>12}"
          f"{'⑤ 盤中極值':>13}{'⑤−③':>9}")
    print("  " + "-" * 58)
    bad = []
    ratios: dict[str, float] = {}   # ③ / ① 的倍數，供結語使用
    for k, s, d1, d2, d3, bars in spec:
        r = (BacktestRunner(s, inst).run(d1) if d2 is None
             else MultiStreamRunner(s, inst, warmup_bars=200).run(d1, d2, d3))
        ins, _, _ = split(r.trades)
        trades[k] = ins
        cv = build(ins, bars, inst, cap)
        curves[k] = cv
        seq = sorted(ins, key=lambda t: (t.exit_date, t.exit_time))
        d1m = compute(equity_curve(cap, [t.net_ntd(inst) for t in seq]))
        d3m = compute(cv.close)
        p5, a5, _ = cv.intraday_mdd()
        if p5 < d3m.max_drawdown - 1e-12:
            bad.append(k)
        if d1m.max_drawdown > 0:
            ratios[k] = d3m.max_drawdown / d1m.max_drawdown
        print(f"  {k:4}{len(ins):>6}{d1m.max_drawdown*100:>12.2f}%"
              f"{d3m.max_drawdown*100:>11.2f}%{p5*100:>12.2f}%"
              f"{(p5-d3m.max_drawdown)*100:>8.2f}%")
    print("  " + "-" * 58)

    # ---- 雙帳戶 ----
    print(f"\n【雙帳戶】")
    accounts = {}
    for acct, label, keys, acap in (
        (LONG_ACCOUNT, "A 多　L1·L3·L5", ("L1", "L3", "L5"), alloc.long_account),
        (SHORT_ACCOUNT, "B 空　L2·L4", ("L2", "L4"), alloc.short_account),
    ):
        sub = {k: curves[k] for k in keys}
        pa = combine(sub, acap)
        accounts[acct] = (pa, acap, label)
        d3a = compute(pa.close)
        p5a, a5a, ata = pa.intraday_mdd()
        pk = max(x.open_lots for x in pa.rows) if pa.rows else 0
        if p5a < d3a.max_drawdown - 1e-12:
            bad.append(label)
        print(f"  {label:<18}本金 {acap:>11,.0f}"
              f"　③ {d3a.max_drawdown*100:>6.2f}%"
              f"　⑤ {p5a*100:>6.2f}%"
              f"　峰值 {pk} / {max_lots(acct)} 口")
        print(f"  {'':18}③ 金額 {d3a.max_drawdown_amount:>11,.0f}"
              f"　發生於 {pa.days[d3a.max_drawdown_index]}")

    # ---- 總體 ----
    p = combine(curves, alloc.total)
    d3m = compute(p.close)
    p5, a5, at = p.intraday_mdd()
    allt = sorted([t for v in trades.values() for t in v],
                  key=lambda t: (t.exit_date, t.exit_time))
    d1m = compute(equity_curve(alloc.total,
                               [t.net_ntd(inst) for t in allt]))
    if p5 < d3m.max_drawdown - 1e-12:
        bad.append("總體")
    print(f"\n【總體】分母 = 總本金 {alloc.total:,.0f}")
    print(f"  {len(allt)} 筆　① {d1m.max_drawdown*100:.2f}%"
          f"　③ {d3m.max_drawdown*100:.2f}%　⑤ {p5*100:.2f}%")
    print(f"  ③ 金額 {d3m.max_drawdown_amount:,.0f}"
          f"　發生於 {p.days[d3m.max_drawdown_index]}")
    print(f"  ⑤ 金額 {a5:,.0f}　發生於 {p.days[at]}")
    print(f"  {p.summary()}")

    # ---- 分散效果：總體 MDD 當日的各支貢獻 ----
    #
    # **不用「各支 MDD 相加 vs 組合 MDD」。**
    # 各支的 MDD 各自發生在不同日子，把五個不同日子的最壞值相加，
    # 本來就不會等於任何一天的值——那個差距**大部分來自時點不同，
    # 不是分散效果**。
    #
    # 真正的證據是：在總體 MDD 那一天，五支各自貢獻了多少。
    mi = d3m.max_drawdown_index
    mday = p.days[mi]
    peak_i = max(range(mi + 1), key=lambda i: p.close[i])
    # ---- 所需帳戶規模（裁決 2026-09-09：主 D、對照 A）----
    print(f"\n【所需帳戶規模】主指標 D（⑤ × 最大絕對）· 對照 A（③ × 百分比點）")
    for nm, (pa, acap, label) in (("A 多", accounts[LONG_ACCOUNT]),
                                  ("B 空", accounts[SHORT_ACCOUNT])):
        r = pa.account_size_required(acap)
        print(f"  {label:<18}期初 {acap:>9,.0f}"
              f"　D {r['primary_D']:>9,.0f}（+{r['primary_D_mdd_amount']/acap*100:.1f}%）"
              f"　A {r['reference_A']:>9,.0f}"
              f"　差距 {r['gap']:>7,.0f}")
    r = p.account_size_required(alloc.total)
    print(f"  {'總體':<18}期初 {alloc.total:>9,.0f}"
          f"　D {r['primary_D']:>9,.0f}（+{r['primary_D_mdd_amount']/alloc.total*100:.1f}%）"
          f"　A {r['reference_A']:>9,.0f}"
          f"　差距 {r['gap']:>7,.0f}")
    print(f"  D 發生於 {r['primary_D_at']}　A 發生於 {r['reference_A_at']}")
    print("  ★ 差距大 = 「相對最慘」與「絕對最慘」在不同時期，權益曲線不是平穩成長")

    print(f"\n【分散效果】總體 MDD 當日的各支貢獻")
    print(f"  峰值日 {p.days[peak_i]} → 谷底日 {mday}"
          f"　共 {(mday - p.days[peak_i]).days} 天")
    print(f"  {'':6}{'峰值日權益':>13}{'谷底日權益':>13}{'貢獻':>13}")
    print("  " + "-" * 46)
    total_c = 0.0
    for k in sorted(curves):
        rows = {r.day: r for r in curves[k].rows}
        pv = rows.get(p.days[peak_i])
        vv = rows.get(mday)
        if pv is None or vv is None:
            continue
        # 該支從峰值日到谷底日的權益變化（含未平倉）
        delta = vv.equity_close - pv.equity_close
        total_c += delta
        tag = "up" if delta > 0 else "dn"
        print(f"  {k:6}{pv.equity_close:>13,.0f}{vv.equity_close:>13,.0f}"
              f"{delta:>13,.0f}")
    print("  " + "-" * 46)
    print(f"  {'合計':6}{'':>13}{'':>13}{total_c:>13,.0f}"
          f"　（總體回撤 {-d3m.max_drawdown_amount:,.0f}）")
    print("  ★ 有支數為正 = 該支在總體回撤當下是賺的，**那才是分散效果**")

    print(f"\n【浮動損益（總體）】")
    print(f"  收盤　　最大浮盈 {max(x.unrealized_close for x in p.rows):>12,.0f}"
          f"　最大浮虧 {min(x.unrealized_close for x in p.rows):>12,.0f}")
    print(f"  不利極值　最大浮虧 {min(x.unrealized_worst for x in p.rows):>12,.0f}")
    print(f"  有利極值　最大浮盈 {max(x.unrealized_best for x in p.rows):>12,.0f}")

    print("\n" + "=" * 70)
    if bad:
        print(f"✗ {bad} 的 ⑤ < ③ —— **那不可能，實作有錯**")
        return 1
    print("✓ 五支與組合的 ⑤ 全部 >= ③")
    # **從資料算，不寫死。**
    # 2026-09-08：結語原本硬編碼一個倍數，那是大台 200 萬時算出來的；
    # 換成微台後表格的倍數變了，而結語沒跟著變——
    # 與死設定同一類缺陷：數字寫在文字裡，資料變了它不會跟著變。
    # 修正後測試會掃整個檔案，**連註解裡的數字都不允許**。
    if ratios:
        worst_k, worst_r = max(ratios.items(), key=lambda kv: kv[1])
        print(f"★ ① 只算平倉會低估。{worst_k} 差 {worst_r:.2f} 倍"
              f"——它的浮虧遠大於已實現虧損。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
