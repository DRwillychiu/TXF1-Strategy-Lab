#!/usr/bin/env python3
"""策略流程驗證　進場 → 部位口數 → 出場 → 風險管理。

```powershell
python tools\\flow_check.py "data\\mc_export\\TXF1 1 分鐘.txt"
```

**每一支逐段追蹤四個環節，任一環斷掉就報錯。**

    環節 1　進場    誰決定方向與價格？閘門有幾道？實際觸發幾次？
    環節 2　口數    誰決定？進場口數 vs 出場口數的分工對不對？
    環節 3　出場    有幾條路徑？每條的觸發次數與勝率？有沒有死路徑？
    環節 4　風險    引擎停損有沒有設？保護器有沒有被呼叫？

**死路徑是重點。** 一條出場路徑觸發 0 次，可能是：
    設計如此（開關關閉）        → 合理
    條件永遠不成立              → **像 L4 v18 的零觸發事故**
    我移植錯了                  → 缺陷
三者的輸出必須分得開。
"""
from __future__ import annotations

import argparse
import collections
import pickle
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from txfcore.instruments.spec import TXF
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
from txfcore.types.orders import OrderType, Side

# 每支的完整標籤清單（來自 audit_port 對 .pla 的比對，不是我列的）
EXPECTED_LABELS = {
    "L1": {"TL_Entry", "TL_ReEntry", "TL_SL", "TL_SP", "TL_TP", "TL_TSL",
           "TL_SL_Gap", "TL_SP_Gap", "TL_RegistryEnd", "TL_Holiday",
           "TL_Settlement", "TL_Kill"},
    "L2": {"TS_Entry", "TS_ReEntry", "TS_WeeklyExit", "TS_StructureTP", "TS_TTP",
           "TS_StopProfit", "TS_InitSL_D", "TS_InitSL_N", "TS_TSL_D", "TS_TSL_N",
           "TS_RegistryEnd", "TS_Holiday", "TS_Settlement", "TS_Kill"},
    "L3": {"CL_Entry", "CL_ReEntry", "CL_TP", "CL_SL", "CL_BE", "CL_BreakExit",
           "CL_RegistryEnd", "CL_Holiday", "CL_Settlement", "CL_Kill"},
    "L4": {"CS_Entry", "CS_ReEntry", "CS_SL", "CS_BE", "CS_SP", "CS_BreakExit",
           "CS_TimeExit", "CS_RegistryEnd", "CS_Holiday", "CS_Settlement",
           "CS_Kill"},
    "L5": {"BL_Entry_Bot", "BL_Entry_Mid", "BL_TP_Bot", "BL_TP_Mid",
           "BL_SL_Bot", "BL_SL_Mid", "BL_SP_Bot", "BL_SP_Mid",
           "BL_BE_Bot", "BL_BE_Mid", "BL_Trail_Bot", "BL_Trail_Mid",
           "BL_TimeExit_Bot", "BL_TimeExit_Mid", "BL_BreakExit_Bot",
           "BL_BreakExit_Mid", "BL_Kill_Bot", "BL_Kill_Mid",
           "BL_RegistryEnd_Bot", "BL_RegistryEnd_Mid",
           "BL_Holiday_Bot", "BL_Holiday_Mid",
           "BL_Settlement_Bot", "BL_Settlement_Mid"},
}

# 已知的關閉開關 → 對應的死路徑。**這些 0 次是合理的。**
KNOWN_OFF = {
    "L1": {"TL_ReEntry": "ReEntry_On = 0（出貨即關閉）"},
    "L3": {"CL_BE": "BE_Trigger_Pts = 0（v13.2D A/B 失敗，100 筆全 0% 勝率）"},
    "L4": {"CS_BE": "BE_Trigger_Pts = 0（A/B 淨 −345K，砍掉前十大贏家中的 4 筆）",
           "CS_SP": "SP_Trigger_Pts = 0（CS_SL 從 +1,019K 掉到 +619K）"},
    "L5": {"BL_SP_Bot": "SP_Trigger_Pts = 0（PERMANENT，五個變體全失敗）",
           "BL_SP_Mid": "SP_Trigger_Pts = 0"},
}
# Kill 與 RegistryEnd 在回測中本來就不會觸發
NEVER_IN_BACKTEST = {"Kill", "RegistryEnd"}

# **已查證原因的零觸發。** 2026-09-08 逐一量測後登記。
# 登記在此表示「已知為什麼是 0」，不是「忽略它」。
DIAGNOSED = {
    "TS_Settlement":
        "跨越結算日僅 4 筆，且都在 12:30 前出場。L3 有 3 筆證明機制能觸發",
    "CS_Settlement":
        "跨越結算日僅 2 筆，且都在 12:30 前出場",
    "BL_Settlement_Bot":
        "跨越結算日僅 4 筆，且都在 12:30 前出場",
    "BL_Settlement_Mid":
        "跨越結算日僅 4 筆，且都在 12:30 前出場",
    "TS_WeeklyExit":
        "**已量測**：357 個週五樣本點中僅 16 根持倉，"
        "而收盤在週線 SMA13 之上者 0 根。空單遇趨勢翻多時停損先觸發——"
        "是機制間的競爭，不是缺陷",
    "TL_SP_Gap":
        "跳空分支本身觸發 35 次（全落在虧損側 TL_SL_Gap）。"
        "獲利側跳空需「收盤跌破一個高於進場價的停損線」，6.5 年零次",
    "BL_BE_Bot": "需 Stage 2/3 且價格回到進場價。分批僅 10 組",
    "BL_BE_Mid": "需 Stage 2/3 且價格回到進場價。分批僅 10 組",
    "BL_Trail_Bot":
        "Bot 腿 59 筆 vs Mid 181 筆，且需 Stage 2/3 + 追蹤啟動。"
        "BL_Trail_Mid 有 4 筆證明機制能觸發",
    "BL_Holiday_Bot": "Bot 腿 + 假日尾盤持倉，兩個罕見條件相乘",
}


@dataclass
class Flow:
    key: str
    name: str
    # 環節 1
    entry_labels: dict = field(default_factory=dict)
    entry_order_types: set = field(default_factory=set)
    # 環節 2
    entry_qty: collections.Counter = field(default_factory=collections.Counter)
    exit_qty: collections.Counter = field(default_factory=collections.Counter)
    partial_exits: int = 0
    sized_by: collections.Counter = field(default_factory=collections.Counter)
    # 環節 3
    exit_labels: dict = field(default_factory=dict)
    emitted_labels: set = field(default_factory=set)
    # 環節 4
    protective_set: int = 0
    bars: int = 0
    problems: list = field(default_factory=list)


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


def cached(cd, name, build):
    f = Path(cd) / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = build()
    f.write_bytes(pickle.dumps(v))
    return v


def trace(key, strategy, d1, d2, d3):
    """跑一次，攔截每一根的決策。"""
    f = Flow(key, strategy.config.name)
    cls = type(strategy)
    orig = cls.on_bar

    def patched(self, view, state):
        st, dec = orig(self, view, state)
        f.bars += 1
        if dec.protective is not None:
            f.protective_set += 1
        for o in dec.orders:
            f.emitted_labels.add(o.label)
            if o.is_entry:
                f.entry_order_types.add(o.order_type.value)
            if o.exit_quantity is not None:
                f.exit_qty[o.exit_quantity] += 1
        return st, dec

    cls.on_bar = patched
    try:
        r = (BacktestRunner(strategy, TXF).run(d1) if d2 is None
             else MultiStreamRunner(strategy, TXF, warmup_bars=200).run(d1, d2, d3))
    finally:
        cls.on_bar = orig

    ins, _, _ = split(r.trades)
    f.entry_labels = dict(collections.Counter(t.entry_label for t in ins))
    ex = collections.defaultdict(list)
    for t in ins:
        ex[t.exit_label].append(t.net_ntd(TXF))
    f.exit_labels = {k: (len(v), sum(1 for x in v if x > 0) / len(v) * 100, sum(v))
                     for k, v in ex.items()}
    f.entry_qty = collections.Counter(t.quantity for t in ins)
    grp = collections.Counter((t.entry_date, t.entry_time) for t in ins)
    f.partial_exits = sum(1 for v in grp.values() if v > 1)
    return f, r


def report(f: Flow) -> None:
    print(f"\n{'='*74}")
    print(f"{f.key}　{f.name}")
    print("=" * 74)

    print("\n環節 1　進場")
    print(f"  單型          {sorted(f.entry_order_types) or '—'}")
    for lb, n in sorted(f.entry_labels.items()):
        print(f"  {lb:<22}{n:>6} 筆")
    if not f.entry_labels:
        f.problems.append("零進場 —— 進場鏈斷了")

    print("\n環節 2　部位口數")
    print(f"  進場口數分布   {dict(f.entry_qty)}")
    if f.exit_qty:
        print(f"  出場口數（策略指定） {dict(f.exit_qty)}")
        print(f"  分批出場組數   {f.partial_exits}")
    else:
        print("  出場口數       未指定 → 平掉該腿全部（L1–L4 皆如此）")
    if f.key == "L5":
        if not f.exit_qty:
            f.problems.append("**L5 應有 40% 分批，但沒有任何出場單指定口數**")
        elif f.partial_exits == 0:
            f.problems.append("**L5 指定了分批口數，但沒有一筆真的分批成交**")

    print("\n環節 3　出場")
    expect = EXPECTED_LABELS.get(f.key, set())
    exits = {x for x in expect if not any(
        x.startswith(p) or p in x for p in ("Entry",))}
    for lb in sorted(exits):
        n, wr, pnl = f.exit_labels.get(lb, (0, 0.0, 0.0))
        if n:
            print(f"  ✓ {lb:<22}{n:>5} 筆   勝率 {wr:>5.1f}%   {pnl:>13,.0f}")
        else:
            emitted = lb in f.emitted_labels
            off = KNOWN_OFF.get(f.key, {}).get(lb)
            skip = any(t in lb for t in NEVER_IN_BACKTEST)
            diag = DIAGNOSED.get(lb)
            if off:
                print(f"  ○ {lb:<22}    0 筆   已知關閉：{off}")
            elif skip:
                print(f"  ○ {lb:<22}    0 筆   回測中本就不觸發")
            elif diag:
                print(f"  ● {lb:<22}    0 筆   已查證：{diag}")
            elif emitted:
                print(f"  ▲ {lb:<22}    0 筆   **有發單但從未成交，原因未查**")
                f.problems.append(f"{lb} 有發單但從未成交")
            else:
                print(f"  ✗ {lb:<22}    0 筆   **從未發出，原因未查**")
                f.problems.append(f"{lb} 從未發出 —— 像 L4 v18 的零觸發事故")

    print("\n環節 4　風險管理")
    pct = f.protective_set / f.bars * 100 if f.bars else 0
    print(f"  引擎停損設定   {f.protective_set:,} / {f.bars:,} 根（{pct:.1f}%）")
    if f.protective_set == 0:
        f.problems.append("**引擎停損從未設定** —— SetStopLoss 沒接上")
    print("  組合層保護器   ✗ 未接上（risk/protections.py 存在但無呼叫者）")

    if f.problems:
        print(f"\n★ {len(f.problems)} 個問題")
        for p in f.problems:
            print(f"    ✗ {p}")
    else:
        print("\n★ 四個環節都完整")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--cache-dir", default=".")
    args = ap.parse_args()
    cd = args.cache_dir

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

    total = 0
    for key, s, d1, d2, d3 in (
        ("L1", L1TrendLong(), m45, md, mw),
        ("L2", L2TrendShort(), m60, None, None),
        ("L3", L3ConsolLong(), m15, m60, md),
        ("L4", L4ConsolShort(), m15, m60, md),
        ("L5", L5BreakoutLong(), m15, mdn, mwn),
    ):
        f, _ = trace(key, s, d1, d2, d3)
        report(f)
        total += len(f.problems)

    print(f"\n{'='*74}")
    print(f"五支合計 {total} 個問題")
    print("★ ○ = 已知關閉　● = 已查證原因　▲ = 有發單沒成交，未查　"
          "✗ = 從未發出，未查")
    print("★ **只有 ▲ 與 ✗ 需要處理。● 代表已經量測過為什麼是 0。**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
