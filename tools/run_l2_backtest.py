#!/usr/bin/env python3
"""L2 全歷史回測 + 對帳前置檢查。

用法：
    python tools/run_l2_backtest.py <1分K檔案路徑> [--period 60] [--cache PATH]

會先跑黃金測試集（G2 kill gate）。判官不合格就不往下做。
"""
from __future__ import annotations

import argparse
import collections
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from txfcore.instruments.spec import TXF, get
from txfcore.lineage.stamp import Lineage, code_hash, sha256_file, sha256_obj
from txfcore.metrics.drawdown import compute
from txfcore.parity.golden import run_golden
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.history import MC12MinuteSource
from txfcore.runtime.backtest import BacktestRunner
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.tradecal import calendar_hash
from txfcore.types.mctime import mc_date_to_date


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--period", type=int, default=60)
    ap.add_argument("--instrument", default="TXF")
    ap.add_argument("--cache", default="")
    ap.add_argument("--from-date", type=int, default=0, help="民國年 YYYMMDD")
    args = ap.parse_args()

    # ---- G2 kill gate ----
    ok, report = run_golden()
    print(report)
    if not ok:
        print("\n★ 判官不合格，中止。")
        return 1
    print()

    # ---- 聚合（可快取）----
    cache = Path(args.cache) if args.cache else None
    if cache and cache.exists():
        bars = pickle.loads(cache.read_bytes())
        print(f"由快取載入 {len(bars):,} 根 {args.period}M")
    else:
        bars = list(aggregate_bars(MC12MinuteSource(args.data).stream(), args.period))
        print(f"聚合 {len(bars):,} 根 {args.period}M")
        if cache:
            cache.write_bytes(pickle.dumps(bars))

    inst = get(args.instrument)
    s = L2TrendShort()
    lg = Lineage(code=code_hash(Path(__file__).resolve().parent.parent / "txfcore"),
                 config=sha256_obj(s.config.params),
                 data=sha256_file(args.data),
                 calendar=calendar_hash())

    r = BacktestRunner(s, inst, lineage=lg).run(bars)
    trades = [t for t in r.trades if t.entry_date >= args.from_date]

    print(f"\n血緣  {lg.short}")
    print(f"成交假設  {r.policy}")
    print(f"K 棒 {r.bars_processed:,}   訂單意圖 {r.orders_emitted}   成交 {len(trades)} 筆")
    if not trades:
        print("零交易")
        return 0

    net = sum(t.net_ntd(inst) for t in trades)
    wins = [t for t in trades if t.net_ntd(inst) > 0]
    gp = sum(t.net_ntd(inst) for t in wins)
    gl = -sum(t.net_ntd(inst) for t in trades if t.net_ntd(inst) <= 0)
    d = compute(r.ledger.equity())
    print(f"淨利 {net:,.0f}   勝率 {len(wins)/len(trades)*100:.1f}%"
          f"   PF {gp/gl if gl else 0:.3f}")
    print(f"max_drawdown {d.max_drawdown*100:.2f}%   金額 {d.max_drawdown_amount:,.0f}")
    print(f"回撤持續 {d.drawdown_duration} 期   水下比例 {d.underwater_ratio*100:.1f}%")
    print("\n出場標籤:", dict(collections.Counter(t.exit_label for t in trades).most_common()))
    print("進場標籤:", dict(collections.Counter(t.entry_label for t in trades).most_common()))
    print(f"期間 {mc_date_to_date(trades[0].entry_date)} ~ {mc_date_to_date(trades[-1].entry_date)}")

    lo, hi = s.expected_trigger_range()
    inside = lo <= len(trades) <= hi
    print(f"\n★ 事前登記的觸發區間 {lo}–{hi}   實得 {len(trades)}   "
          f"{'在區間內' if inside else '超出區間'}")
    after = [t for t in trades if t.entry_date >= 1250603]
    print(f"★ 2025-06-03 之後（應為 0）：{len(after)} 筆   "
          f"{'通過' if not after else '未通過'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
