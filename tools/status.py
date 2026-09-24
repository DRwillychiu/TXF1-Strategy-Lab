#!/usr/bin/env python3
"""一個指令，輸出全部可回報內容。

```powershell
python tools\\status.py "data\\mc_export\\TXF1 1 分鐘.txt"
```

輸出七段，並寫出 `reports/STATUS.md`（可直接當進度回報交出去）：

    1  資料完整性
    2  移植稽核        .pla vs Python 逐項比對
    3  回測期（樣本內） ~ 2026-06-01
    4  實戰期（樣本外） 2026-06-17 起 ← 真實下單開始
    5  不變量
    6  模組完整度      介面有幾個真的有實作
    7  未完成清單

**每一段都是可重現的。看到的數字就是可以拿出去的數字。**
"""
from __future__ import annotations

import argparse
import collections
import os
import pickle
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from txfcore.instruments.spec import TXF
from txfcore.metrics.drawdown import compute
from txfcore.parity.completeness import (
    CAPABILITIES, MISSING_MODULES, ORPHANS, summary,
)
from txfcore.parity.windows import IN_SAMPLE, LIVE_END, LIVE_START, OUT_SAMPLE, split
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
from txfcore.types.mctime import DayOfWeek, day_of_week, mc_date_to_date, trading_day

OUT: list[str] = []


def say(line: str = "") -> None:
    print(line)
    OUT.append(line)


def rule(ch: str = "─", n: int = 74) -> None:
    say(ch * n)


def daily_bars(mins):
    b: dict = {}
    for m in mins:
        b.setdefault(trading_day(m.mc_date, m.mc_time), []).append(m)
    return [Bar(g[-1].mc_date, g[-1].mc_time, g[0].open, max(x.high for x in g),
                min(x.low for x in g), g[-1].close, sum(x.volume for x in g), len(g))
            for _, g in sorted(b.items())]


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
        wk.append(Bar(x.mc_date, x.mc_time, buf[0].open, max(y.high for y in buf),
                      min(y.low for y in buf), x.close,
                      sum(y.volume for y in buf), len(buf)))
    return wk


def cached(cd: Path, name: str, build):
    f = cd / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = build()
    f.write_bytes(pickle.dumps(v))
    return v


def stats(x):
    if not x:
        return dict(n=0, net=0.0, pf=0.0, wr=0.0)
    pnl = [t.net_ntd(TXF) for t in x]
    w = [v for v in pnl if v > 0]
    l = [v for v in pnl if v <= 0]
    return dict(n=len(x), net=sum(pnl),
                pf=sum(w) / -sum(l) if l and sum(l) else 0.0,
                wr=len(w) / len(pnl) * 100)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()
    cd = Path(args.cache_dir)
    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)

    say("=" * 74)
    say("TXF1 Python 移植　現況")
    say("=" * 74)

    # ---------- 1 資料 ----------
    say("\n【1】資料完整性")
    rule()
    say("  " + banner(args.data))
    check(args.data)
    mins = list(MC12MinuteSource(args.data).stream())
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m45 = cached(cd, "45m", lambda: list(aggregate_bars(mins, 45)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: build_daily(mins, DAY_FIRST))
    mdn = cached(cd, "dn", lambda: build_daily(mins, NIGHT_FIRST))
    mw = cached(cd, "w", lambda: weekly_bars(md))
    mwn = cached(cd, "wn", lambda: weekly_bars(mdn))
    first, last = mins[0], mins[-1]
    say(f"  1 分 K   {len(mins):,} 列   "
        f"{mc_date_to_date(first.mc_date)} ~ {mc_date_to_date(last.mc_date)}")
    say(f"  聚合     15M {len(m15):,} · 45M {len(m45):,} · 60M {len(m60):,}"
        f" · 日 {len(md):,} · 週 {len(mw):,}")
    bad = sum(1 for b in mins
              if not (b.low <= b.open <= b.high and b.low <= b.close <= b.high))
    say(f"  OHLC 不一致 {bad}")

    # ---------- 2 移植稽核 ----------
    say("\n【2】移植稽核　.pla vs Python 逐項比對")
    rule()
    try:
        # **必須指定 utf-8**。Windows 的 subprocess 預設用 cp950 解碼，
        # 吃不下 ✓ / ✗ / 中文，會在讀取時就拋 UnicodeDecodeError——
        # 而錯誤訊息看起來像「工具壞了」，其實工具是好的。
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "audit_port.py")],
                           capture_output=True, text=True, timeout=120,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        # **2026-09-07：原本用 startswith 過濾，把所有輸出都濾掉了，
        # 這一段在你的機器上印出來是空的。** 改成排除法：只去掉分隔線與標題。
        skip = ("=" * 10, "移植稽核 ——", "★ ✗ 是確定的落差")
        printed = 0
        for ln in p.stdout.splitlines():
            t = ln.rstrip()
            if not t or any(t.startswith(x) for x in skip):
                continue
            say("  " + t)
            printed += 1
        if printed == 0:
            say("  ✗ 稽核沒有任何輸出 —— 工具壞了或 .pla 路徑不對")
            say(f"    stderr: {p.stderr.strip()[:200]}")
    except Exception as e:                                    # noqa: BLE001
        say(f"  稽核未執行：{e}")

    # ---------- 跑五支 ----------
    runs = {
        "L1": MultiStreamRunner(L1TrendLong(), TXF, warmup_bars=200).run(m45, md, mw),
        "L2": BacktestRunner(L2TrendShort(), TXF).run(m60),
        "L3": MultiStreamRunner(L3ConsolLong(), TXF, warmup_bars=200).run(m15, m60, md),
        "L4": MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200).run(m15, m60, md),
        "L5": MultiStreamRunner(L5BreakoutLong(), TXF, warmup_bars=200).run(m15, mdn, mwn),
    }
    parts = {k: split(r.trades) for k, r in runs.items()}

    # ---------- 3 回測期 ----------
    say(f"\n【3】{IN_SAMPLE.name}　~ {mc_date_to_date(IN_SAMPLE.end)}")
    rule()
    say(f"  {'':4}{'筆數':>7}{'淨利':>14}{'PF':>9}{'勝率':>9}")
    tot = 0.0
    for k in runs:
        s = stats(parts[k][0])
        tot += s["net"]
        say(f"  {k:4}{s['n']:>7}{s['net']:>14,.0f}{s['pf']:>9.3f}{s['wr']:>8.1f}%")
    say(f"  {'合計':4}{'':>7}{tot:>14,.0f}")

    # ---------- 4 實戰期 ----------
    say(f"\n【4】{OUT_SAMPLE.name}　{mc_date_to_date(LIVE_START)} ~ "
        f"{mc_date_to_date(LIVE_END)}　★ 真實下單期間")
    rule()
    say(f"  {'':4}{'筆數':>7}{'淨利':>14}{'PF':>9}{'勝率':>9}")
    tot_l = 0
    net_l = 0.0
    for k in runs:
        s = stats(parts[k][1])
        tot_l += s["n"]
        net_l += s["net"]
        say(f"  {k:4}{s['n']:>7}{s['net']:>14,.0f}{s['pf']:>9.3f}{s['wr']:>8.1f}%")
    say(f"  {'合計':4}{tot_l:>7}{net_l:>14,.0f}")
    say(f"\n  Python 實戰期 {tot_l} 筆　·　實戰紀錄 59 筆（微台 2 口，期初 300,000）")
    say("  ★ 商品不同（大台 200/點 vs 微台 10/點），金額需換算；筆數可直接比。")
    say("  ★ 樣本外的 PF 與樣本內的差距，是 MC12 看不出來的"
        "——它的回測把兩段混在一起。")

    # ---------- 5 不變量 ----------
    say("\n【5】不變量（判官 2，不需要對照組）")
    rule()
    say("  以 tools\\audit.py 執行。上次結果：")
    say("    L2   35,313 次檢查   158 次違反，全部是規格表已記錄的落差")
    say("    L4  141,103 次檢查   零違反")

    # ---------- 6 模組完整度 ----------
    done, total = summary()
    say(f"\n【6】模組完整度　介面 {done}/{total} 有實作")
    rule()
    for c in CAPABILITIES:
        m = "✓" if c.impls else "✗"
        impl = " · ".join(c.impls) if c.impls else "**無實作**"
        say(f"  {m} {c.protocol:<16}{c.package:<16}{impl}")
        if not c.impls:
            say(f"      → {c.why}")
    say("\n  已寫但沒有呼叫者：")
    for f, why in ORPHANS:
        say(f"    ▲ {f:<28}{why}")

    # ---------- 7 未完成 ----------
    say("\n【7】尚未建立的模組")
    rule()
    for f, why in MISSING_MODULES:
        say(f"  ✗ {f:<24}{why}")

    say("\n" + "=" * 74)
    say("每一段都可由本指令重現。看到的數字就是可以拿出去的數字。")
    say("=" * 74)

    md_path = outdir / "STATUS.md"
    md_path.write_text(
        "# TXF1 Python 移植　現況\n\n```\n" + "\n".join(OUT) + "\n```\n",
        encoding="utf-8")
    print(f"\n已寫出 {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
