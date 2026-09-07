#!/usr/bin/env python3
"""自我稽核 —— 跑會失敗的檢查，報告發現。

**這不是 pytest。** pytest 檢查「我的程式符合我的理解」；
本工具檢查「我的理解是否自洽、資料是否如我假設」。

輸出是**資訊**，不是通過與否。看到「零違反」才有意義，
看到數字變大不代表進度。

用法：
    python tools/audit.py <1分K路徑> [--cache-dir .]
"""
from __future__ import annotations

import argparse
import collections
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from txfcore.engine.fill_mc12 import MC12FillModel
from txfcore.engine.position import PositionBook
from txfcore.instruments.spec import TXF
from txfcore.parity.invariants import InvariantLog, L2Invariants, L4Invariants
from txfcore.quotes.align import MultiStream
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.history import MC12MinuteSource
from txfcore.strategies.base import MarketView, PositionView
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.strategies.l4_consolshort import L4ConsolShort
from txfcore.tradecal.gates import evaluate
from txfcore.tradecal.settlement import SETTLEMENT_SET, static_rule
from txfcore.types.mctime import mc_date_to_date, trading_day
from txfcore.types.orders import Side, SizedOrder

FM = MC12FillModel()


def _cache(dirpath: Path, name: str, build):
    f = dirpath / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    out = build()
    f.write_bytes(pickle.dumps(out))
    return out


def run_invariants(strategy, inv_cls, d1, d2=None, d3=None, warmup=40) -> InvariantLog:
    log = InvariantLog()
    inv = inv_cls(log)
    s = strategy
    st = s.initial_state()
    name = s.config.name
    bk = PositionBook()
    ms = MultiStream()
    for b in (d2 or []):
        ms.feed_slow("data2", b)
    for b in (d3 or []):
        ms.feed_slow("data3", b)
    pending: list[SizedOrder] = []
    prot = None
    for bar in d1:
        pos = bk.get(name)
        pos.advance_bar()
        if pending or prot:
            fills = FM.fill(pending, bar)
            if prot and not pos.is_flat:
                px = pos.entry_price + prot.distance
                ef = FM.engine_stop_fill(px, Side.BUY_TO_COVER,
                                         pos.current_contracts, bar, name)
                if ef and not any(
                    f.order.intent.side in (Side.SELL, Side.BUY_TO_COVER) for f in fills
                ):
                    fills = [ef]
            for f in fills:
                if f.order.intent.side in (Side.BUY, Side.SELL_SHORT):
                    if pos.is_flat:
                        pos.open_leg(f.order.intent.label, f.price, f.quantity,
                                     bar.mc_date, bar.mc_time, f.order.intent.side)
                elif not pos.is_flat:
                    pos.close(min(f.quantity, pos.current_contracts))
                break
            pending = []
        ms.push_driver(bar)
        if len(ms.driver) < warmup:
            continue
        if d2 and not ms.all_ready("data2", "data3"):
            continue
        v = MarketView(
            data1=ms.driver,
            data2=ms.slow("data2").series if d2 else None,
            data3=ms.slow("data3").series if d3 else None,
            position=PositionView(
                market_position=pos.direction, entry_price=pos.entry_price,
                bars_since_entry=pos.bars_since_entry,
                prev_market_position=st.prev_market_position,
                prev_position_profit=pos.prev_position_profit,
                current_contracts=pos.current_contracts,
                max_contracts=pos.max_contracts),
            calendar=evaluate(bar.mc_date, bar.mc_time),
            mc_date=bar.mc_date, mc_time=bar.mc_time)
        st, dec = s.on_bar(v, st)
        inv.check(v, st)
        if dec.protective is not None:
            prot = dec.protective
        pending = [SizedOrder(intent=o, quantity=TXF.default_lots) for o in dec.orders]
    return log


def data_anomalies(m60, m15) -> list[str]:
    out = []
    for name, bars, expect in (("60M", m60, 19), ("15M", m15, 76)):
        cnt = collections.Counter()
        for b in bars:
            cnt[trading_day(b.mc_date, b.mc_time)] += 1
        odd = sorted(d for d, n in cnt.items() if n < expect * 0.5)
        if odd:
            out.append(f"{name} 缺過半 K 棒的交易日 {len(odd)} 天："
                       f"{[str(d) for d in odd[:5]]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    args = ap.parse_args()
    cd = Path(args.cache_dir)

    # 資料版本守門。不一致立刻停 —— 結算日曆是從特定版本反推的。
    from txfcore.quotes.guard import banner, check
    print(banner(args.data))
    check(args.data)
    print("讀取與聚合…")
    mins = list(MC12MinuteSource(args.data).stream())
    m15 = _cache(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m60 = _cache(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = _cache(cd, "d", lambda: _daily(mins))
    print(f"  1分K {len(mins):,}   15M {len(m15):,}   60M {len(m60):,}   D {len(md):,}\n")

    print("=" * 66)
    print("一 資料異常")
    print("=" * 66)
    an = data_anomalies(m60, m15)
    print("\n".join(f"  ▲ {x}" for x in an) if an else "  零異常")

    print("\n" + "=" * 66)
    print("二 結算日曆 vs 靜態規則")
    print("=" * 66)
    missed = sorted(d for d in SETTLEMENT_SET if not static_rule(d))
    print(f"  資料反推 {len(SETTLEMENT_SET)} 天，靜態規則漏標 {len(missed)} 天")
    for d in missed:
        print(f"     {mc_date_to_date(d)} ({mc_date_to_date(d).strftime('%a')})")

    print("\n" + "=" * 66)
    print("三 不變量（判官 2）")
    print("=" * 66)
    print("--- L2 ---")
    print(run_invariants(L2TrendShort(), L2Invariants, m60).report())
    print("\n--- L4 ---")
    print(run_invariants(L4ConsolShort(), L4Invariants, m15, m60, md, warmup=200).report())

    print("\n" + "=" * 66)
    print("★ ○ 標記者為規格表已記錄的落差，照抄的，不算失敗")
    print("★ ✗ 標記者為未預期的違反 —— 那才是要查的")
    print("★ 本工具不證明「符合 MC」。那需要 MC 報告做逐筆 diff。")
    return 0


def _daily(mins):
    from txfcore.types.bar import Bar
    buckets: dict = {}
    for m in mins:
        buckets.setdefault(trading_day(m.mc_date, m.mc_time), []).append(m)
    out = []
    for d in sorted(buckets):
        g = buckets[d]
        last = g[-1]
        out.append(Bar(last.mc_date, last.mc_time, g[0].open,
                       max(x.high for x in g), min(x.low for x in g),
                       g[-1].close, sum(x.volume for x in g), len(g)))
    return out


if __name__ == "__main__":
    raise SystemExit(main())
