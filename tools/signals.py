#!/usr/bin/env python3
"""當前訊號 —— 五支跑到資料最後一根，輸出「下一根要下什麼單」。

**這是專案終點的另一半（詳細訊號通知）的第一步，也是 L1 平行前向驗證的機制。**

它回答三個問題：

    1. 每支現在是空手還是持倉？進場價多少？進場幾根了？
    2. 下一根有哪些掛單？標籤、方向、單型、價格。
    3. **沒有進場的，是哪一道閘門擋住的？**

第三項是「詳細」的意思。只說「今天沒訊號」沒有用；
說「箱體有效但週線濾網為假」才能跟 MC 對照。

用法：
    python tools/signals.py "data\\mc_export\\TXF1 1 分鐘.txt"
    python tools/signals.py <資料> --asof 1260901     只跑到某日

**驗證方式**：拿輸出跟 MC12 當天實際下的單比。
連續 N 天一致，才談得上切換。
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from txfcore.engine.fill_mc12 import MC12FillModel
from txfcore.engine.position import PositionBook
from txfcore.instruments.spec import TXF
from txfcore.quotes.align import MultiStream
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.daily import DAY_FIRST, NIGHT_FIRST, build as build_daily
from txfcore.quotes.guard import banner, check
from txfcore.quotes.history import MC12MinuteSource
from txfcore.strategies.base import MarketView, PositionView
from txfcore.strategies.l1_trendlong import L1TrendLong
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.strategies.l3_consollong import L3ConsolLong
from txfcore.strategies.l4_consolshort import L4ConsolShort
from txfcore.strategies.l5_breakoutlong import L5BreakoutLong
from txfcore.tradecal.gates import evaluate
from txfcore.types.bar import Bar, BarSeries
from txfcore.types.mctime import (
    DayOfWeek, day_of_week, mc_date_to_date, trading_day,
)
from txfcore.types.orders import MarketPosition, Side, SizedOrder

FM = MC12FillModel()


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


def daily_bars(mins):
    b: dict = {}
    for m in mins:
        b.setdefault(trading_day(m.mc_date, m.mc_time), []).append(m)
    return [Bar(g[-1].mc_date, g[-1].mc_time, g[0].open,
                max(x.high for x in g), min(x.low for x in g),
                g[-1].close, sum(x.volume for x in g), len(g))
            for _, g in sorted(b.items())]


def cached(cd: Path, name: str, build):
    f = cd / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = build()
    f.write_bytes(pickle.dumps(v))
    return v


def run_to_end(strategy, d1, d2=None, d3=None, warmup=200):
    """跑到最後一根，回傳 (最終狀態, 最後一根的決策, 部位, 最後一根 K 棒)。"""
    s = strategy
    st = s.initial_state()
    name = s.config.name
    bk = PositionBook()
    ms = MultiStream()
    for b in (d2 or []):
        ms.feed_slow("data2", b)
    for b in (d3 or []):
        ms.feed_slow("data3", b)
    single = BarSeries("data1")
    pending: list[SizedOrder] = []
    prot = None
    last_view = None
    last_dec = None
    for bar in d1:
        pos = bk.get(name)
        pos.advance_bar()
        if pending:
            fills = FM.fill(pending, bar)
            for f in fills:
                if f.order.intent.side in (Side.BUY, Side.SELL_SHORT):
                    if pos.is_flat or pos.legs and any(
                        l.entry_date == bar.mc_date and l.entry_time == bar.mc_time
                        for l in pos.legs
                    ):
                        pos.open_leg(f.order.intent.label, f.price, f.quantity,
                                     bar.mc_date, bar.mc_time, f.order.intent.side)
                elif not pos.is_flat:
                    # **綁到不存在的腿時該單作廢，不能 break** ——
                    # 否則後面綁對腿的那筆永遠處理不到。
                    # 2026-09-07 由本工具抓到：L5 的部位掛了 3416 根，
                    # 而 Time_Stop_Bars 是 31。
                    if f.order.intent.from_entry:
                        leg = pos.leg(f.order.intent.from_entry)
                        if leg is None:
                            continue
                        qty = min(f.quantity, leg.quantity)
                    else:
                        qty = min(f.quantity, pos.current_contracts)
                    pos.close(qty, from_entry=f.order.intent.from_entry)
                    if pos.is_flat:
                        break
            pending = []
        if d2 is not None:
            ms.push_driver(bar)
            data1 = ms.driver
            ready = ms.all_ready("data2", "data3")
        else:
            single.push(bar)
            data1 = single
            ready = True
        if len(data1) < warmup or not ready:
            continue
        view = MarketView(
            data1=data1,
            data2=ms.slow("data2").series if d2 is not None else None,
            data3=ms.slow("data3").series if d3 is not None else None,
            position=PositionView(
                market_position=pos.direction, entry_price=pos.entry_price,
                bars_since_entry=pos.bars_since_entry,
                prev_market_position=st.prev_market_position,
                prev_position_profit=pos.prev_position_profit,
                current_contracts=pos.current_contracts,
                max_contracts=pos.max_contracts),
            calendar=evaluate(bar.mc_date, bar.mc_time,
                              s.config.registry_valid_until),
            mc_date=bar.mc_date, mc_time=bar.mc_time)
        st, dec = s.on_bar(view, st)
        last_view, last_dec = view, dec
        pending = [SizedOrder(intent=o, quantity=TXF.default_lots)
                   for o in dec.orders]
    return st, last_dec, bk.get(name), last_view


def gate_report(key: str, st, view) -> list[str]:
    """**沒有進場時，說出是哪一道閘門擋住的。**

    只說「今天沒訊號」沒有用；說「箱體有效但週線濾網為假」才能跟 MC 對照。
    """
    if view is None:
        return ["資料不足"]
    ps = st.per_session
    cal = view.calendar
    out = []
    mark = lambda ok, txt: f"{'✓' if ok else '✗'} {txt}"
    out.append(mark(not cal.holiday_block, "非假日尾盤"))
    out.append(mark(not cal.settlement_day, "非結算日"))
    out.append(mark(not cal.registry_expired, "註冊表未過期"))
    if key == "L2":
        out.append(mark(ps.filter_ok, f"週線濾網（已存 {ps.wk_bar_count} 週）"))
    if key in ("L3", "L4", "L5"):
        out.append(mark(ps.in_consolidation,
                        f"箱體有效（頂 {ps.box_top:.0f} 底 {ps.box_btm:.0f}）"))
    if key == "L3":
        out.append(mark(ps.trend_dir == 1, "60M 多方"))
        out.append(mark(ps.daily_filter, "日線 OR 濾網"))
    if key == "L4":
        out.append(mark(ps.trend_dir == -1, "60M 空方"))
        out.append(mark(not ps.macro_block, "非強多環境"))
        out.append(mark(ps.in_trap_zone, f"誘多區（計數 {ps.trap_counter}）"))
        out.append(mark(ps.bars_since_exit >= 8, f"冷卻期滿（{ps.bars_since_exit}）"))
    if key == "L5":
        out.append(mark(ps.trend_dir == 1, "日線多方"))
        out.append(mark(ps.weekly_filter, "週線 AND 濾網"))
    if key == "L1":
        out.append(mark(ps.weekly_filter, "週線 OR 濾網"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    ap.add_argument("--asof", type=int, default=0, help="只跑到此日（民國年 YYYMMDD）")
    args = ap.parse_args()
    cd = Path(args.cache_dir)

    print(banner(args.data))
    check(args.data)
    print("讀取與聚合…")
    mins = list(MC12MinuteSource(args.data).stream())
    if args.asof:
        mins = [m for m in mins if m.mc_date <= args.asof]
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m45 = cached(cd, "45m", lambda: list(aggregate_bars(mins, 45)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: build_daily(mins, DAY_FIRST))
    mdn = cached(cd, "dn", lambda: build_daily(mins, NIGHT_FIRST))
    mw = cached(cd, "w", lambda: weekly_bars(md))
    mwn = cached(cd, "wn", lambda: weekly_bars(mdn))
    if args.asof:
        cut = lambda xs: [b for b in xs if b.mc_date <= args.asof]
        m15, m45, m60, md, mw = map(cut, (m15, m45, m60, md, mw))

    last = m15[-1]
    print(f"\n{'='*70}")
    print(f"資料最後一根 15M   {mc_date_to_date(last.mc_date)} {last.mc_time:04d}"
          f"   收 {last.close:.0f}")
    print(f"{'='*70}")

    specs = (
        ("L1", L1TrendLong(), m45, md, mw),
        ("L2", L2TrendShort(), m60, None, None),
        ("L3", L3ConsolLong(), m15, m60, md),
        ("L4", L4ConsolShort(), m15, m60, md),
        ("L5", L5BreakoutLong(), m15, md, mw),
    )
    for key, strat, d1, d2, d3 in specs:
        st, dec, pos, view = run_to_end(strat, d1, d2, d3)
        b = d1[-1]
        print(f"\n─── {key} {strat.config.name} ───")
        print(f"  最後評估   {mc_date_to_date(b.mc_date)} {b.mc_time:04d}"
              f"   收 {b.close:.0f}")
        if pos.is_flat:
            print("  部位       空手")
        else:
            side = "多" if pos.direction is MarketPosition.LONG else "空"
            legs = " · ".join(f"{l.entry_label}@{l.entry_price:.0f}×{l.quantity}"
                              for l in pos.legs)
            print(f"  部位       {side} {pos.current_contracts} 口"
                  f"   均價 {pos.entry_price:.0f}"
                  f"   已 {pos.bars_since_entry} 根")
            print(f"             {legs}")
        orders = dec.orders if dec else []
        if orders:
            print("  下一根掛單")
            for o in orders:
                px = f"@{o.price:.0f}" if o.price is not None else "市價"
                fe = f"  from {o.from_entry}" if o.from_entry else ""
                print(f"    {o.label:<22}{o.side.value:<14}"
                      f"{o.order_type.value:<8}{px:>10}{fe}")
        else:
            print("  下一根掛單   無")
        if dec and dec.protective:
            print(f"  引擎停損   距離 {dec.protective.distance:.1f} 點"
                  f"（per contract）")
        print("  閘門狀態   " + "   ".join(gate_report(key, st, view)))

    print(f"\n{'='*70}")
    print("★ 驗證方式：拿上面的掛單跟 MC12 當天實際下的單比。")
    print("★ 這不是下單。層 5（notify / broker）尚未實作。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
