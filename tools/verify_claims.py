#!/usr/bin/env python3
"""重現我引用過的每一個數字。

**目的**：讓你自己驗證，而不是相信我的轉述。

輸出的每一項都對應到我在對話裡說過的某個數字。對不上就是我錯了。

用法：
    python tools/verify_claims.py "data\\mc_export\\TXF1 1 分鐘.txt"

第一次約 3–5 分鐘（聚合 210 萬列），之後有快取只要幾十秒。
"""
from __future__ import annotations

import argparse
import collections
import pickle
import statistics
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from txfcore.engine.fill_mc12 import CANDIDATE_POLICIES
from txfcore.instruments.spec import TXF
from txfcore.metrics.drawdown import compute
from txfcore.quotes.bars import aggregate_bars
from txfcore.quotes.continuous import spans_rollover
from txfcore.quotes.history import MC12MinuteSource
from txfcore.runtime.backtest import BacktestRunner
from txfcore.runtime.multi import MultiStreamRunner
from txfcore.strategies.l2_trendshort import L2TrendShort
from txfcore.strategies.l3_consollong import L3ConsolLong
from txfcore.strategies.l4_consolshort import L4ConsolShort
from txfcore.tradecal.settlement import SETTLEMENT_CLOSE, SETTLEMENT_SET
from txfcore.types.bar import Bar
from txfcore.types.mctime import mc_date_to_date, trading_day

FROM = 1191216   # 2019-12-16，L1 的基準起點


def hdr(n: int, title: str) -> None:
    print(f"\n{'='*70}\n{n}. {title}\n{'='*70}")


def claim(label: str, got, said) -> None:
    ok = "✓" if str(got) == str(said) else "✗"
    print(f"  {ok} {label:<34} 實得 {str(got):<16} 我說過 {said}")


def daily(mins):
    b: dict = {}
    for m in mins:
        b.setdefault(trading_day(m.mc_date, m.mc_time), []).append(m)
    out = []
    for d in sorted(b):
        g = b[d]
        last = g[-1]
        out.append(Bar(last.mc_date, last.mc_time, g[0].open,
                       max(x.high for x in g), min(x.low for x in g),
                       g[-1].close, sum(x.volume for x in g), len(g)))
    return out


def cached(cd: Path, name: str, build):
    f = cd / f"cache_{name}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    v = build()
    f.write_bytes(pickle.dumps(v))
    return v


def stats(trades):
    net = sum(t.net_ntd(TXF) for t in trades)
    w = [t for t in trades if t.net_ntd(TXF) > 0]
    gp = sum(t.net_ntd(TXF) for t in w)
    gl = -sum(t.net_ntd(TXF) for t in trades if t.net_ntd(TXF) <= 0)
    return net, len(w) / len(trades) * 100 if trades else 0, gp / gl if gl else 0


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
    m15 = cached(cd, "15m", lambda: list(aggregate_bars(mins, 15)))
    m60 = cached(cd, "60m", lambda: list(aggregate_bars(mins, 60)))
    md = cached(cd, "d", lambda: daily(mins))
    claim("1 分 K 列數", f"{len(mins):,}", "2,098,922")
    claim("15M 根數", f"{len(m15):,}", "141,302")
    claim("60M 根數", f"{len(m60):,}", "35,352")
    claim("日線根數", f"{len(md):,}", "1,864")

    # ---------------------------------------------------------------
    hdr(1, "L2 回測（2019-12-16 起）")
    r2 = BacktestRunner(L2TrendShort(), TXF).run(m60)
    t2 = [t for t in r2.trades if t.entry_date >= FROM]
    net, wr, pf = stats(t2)
    claim("筆數", len(t2), 80)
    claim("淨利", f"{net:,.0f}", "3,039,115")
    claim("PF", f"{pf:.3f}", "3.111")
    claim("勝率", f"{wr:.1f}%", "40.0%")
    claim("全期筆數", r2.trade_count, 92)
    claim("2025-06-03 之後", len(r2.trades_after(1250603)), 0)

    print("\n  虧損出場標籤（標頭：22 InitSL_D · 18 InitSL_N · 4 engine · 1 TSL_N）")
    lose = collections.Counter(t.exit_label for t in t2 if t.net_ntd(TXF) <= 0)
    for k, said in (("TS_InitSL_D", 23), ("TS_InitSL_N", 19),
                    ("ENGINE_STOP", 5), ("TS_TSL_N", 1)):
        claim(f"  {k}", lose.get(k, 0), said)
    nonstop = sum(v for k, v in lose.items()
                  if k not in ("TS_InitSL_D", "TS_InitSL_N", "TS_TSL_D",
                               "TS_TSL_N", "ENGINE_STOP"))
    claim("  非停損類虧損出場", nonstop, 0)

    # ---------------------------------------------------------------
    hdr(2, "L4 回測（2019-12-16 起）")
    r4 = MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200).run(m15, m60, md)
    t4 = [t for t in r4.trades if t.entry_date >= FROM]
    net, wr, pf = stats(t4)
    claim("筆數", len(t4), 83)
    claim("淨利", f"{net:,.0f}", "1,399,503")
    claim("PF", f"{pf:.4f}", "1.9221")
    claim("勝率", f"{wr:.2f}%", "43.37%")
    claim("全期筆數", r4.trade_count, 95)

    print("\n  出場標籤與勝率（標頭 v14.1：CS_BreakExit 0% 勝率）")
    g = collections.defaultdict(list)
    for t in t4:
        g[t.exit_label].append(t.net_ntd(TXF))
    for k in ("CS_SL", "CS_BreakExit", "CS_TimeExit", "ENGINE_STOP"):
        v = g.get(k, [])
        w = sum(1 for x in v if x > 0)
        print(f"      {k:<16}{len(v):>4} 筆   勝率 {w/len(v)*100 if v else 0:>5.1f}%"
              f"   淨 {sum(v):>12,.0f}")
    bw = g.get("CS_BreakExit", [])
    claim("  CS_BreakExit 勝率", f"{sum(1 for x in bw if x>0)/len(bw)*100:.1f}%" if bw else "—", "0.0%")

    # ---------------------------------------------------------------
    hdr(3, "L3 回測（2026-09-07 移植）")
    from txfcore.parity.anchors import ANCHORS, window
    r3 = MultiStreamRunner(L3ConsolLong(), TXF, warmup_bars=200).run(m15, m60, md)
    a3 = ANCHORS["L3"]
    t3 = window(r3.trades, a3)          # 2020-05-12 ~ 2026-07-25，標頭明載
    net, wr, pf = stats(t3)
    print(f"  視窗 {a3.backtest_start} ~ {a3.backtest_end}（v14.1 標頭明載）")
    claim("筆數", len(t3), 379)
    claim("與 MC 376 的差", len(t3) - 376, 3)
    claim("PF", f"{pf:.3f}", "1.319")
    claim("勝率", f"{wr:.1f}%", "45.9%")
    e3 = collections.Counter(t.entry_label for t in t3)
    claim("CL_ReEntry", e3["CL_ReEntry"], 50)
    lo, hi = L3ConsolLong().expected_reentry_range()
    claim("re-entry 在登記區間 20-115", "是" if lo <= e3["CL_ReEntry"] <= hi else "否", "是")
    print("  出場:", dict(collections.Counter(t.exit_label for t in t3).most_common()))

    print("\n  ★ 視窗的影響（同程式碼同資料）")
    for start, lbl in ((1191216, "2019-12-16 我原本用的"), (1200512, "2020-05-12 標頭明載")):
        x = [t for t in r3.trades if start <= t.entry_date <= a3.backtest_end]
        print(f"    {lbl:<24}{len(x):>4} 筆   與 MC 376 差 {len(x)-376:+d}")

    # ---------------------------------------------------------------
    hdr(4, "★ 對 repo 內的真實 anchor（2026-09-07 挖出）")
    from txfcore.parity.anchors import check_window_effect
    for key, tl in (("L2", t2), ("L4", t4)):
        a = ANCHORS[key]
        ent = collections.Counter(t.entry_label for t in tl)
        ext = collections.Counter(t.exit_label for t in tl)
        print(f"\n  --- {a.strategy} {a.version} ---   {a.source_doc}")
        print(f"  {'項目':<20}{'我的':>8}{'MC':>8}{'差':>7}")
        print(f"  {'-'*45}")
        print(f"  {'總筆數':<20}{len(tl):>8}{a.total_trades:>8}{len(tl)-a.total_trades:>+7}")
        for lbl, n in a.entry_labels.items():
            print(f"  {lbl:<20}{ent.get(lbl,0):>8}{n:>8}{ent.get(lbl,0)-n:>+7}")
        if a.exit_labels:
            # 引擎停損在 MC 報告裡併入 CS_SL
            merged = dict(ext)
            if "ENGINE_STOP" in merged and "CS_SL" in a.exit_labels:
                merged["CS_SL"] = merged.get("CS_SL", 0) + merged.pop("ENGINE_STOP")
            for lbl, n in a.exit_labels.items():
                print(f"  {lbl:<20}{merged.get(lbl,0):>8}{n:>8}{merged.get(lbl,0)-n:>+7}")
            extra = {k: v for k, v in merged.items() if k not in a.exit_labels}
            if extra:
                print(f"  {'我多出的出場標籤':<20}{str(extra)}")
        w = check_window_effect(tl, a)
        claim(f"  {key} 匯出日之後的交易", len(w), 0)
    claim("  L4 總筆數差", len(t4) - ANCHORS["L4"].total_trades, 1)
    claim("  L2 總筆數差", len(t2) - ANCHORS["L2"].total_trades, 3)

    # ---------------------------------------------------------------
    hdr(5, "成交假設掃描（L2 全期）")
    print("  ★ 七組全部 92 筆 —— **沒有任何成交開關改變 L2 的交易筆數**")
    print("     所以 80 vs 77–78 不可能是成交假設造成的。H3 對筆數完全排除。")
    counts = set()
    for p in CANDIDATE_POLICIES:
        rr = BacktestRunner(L2TrendShort(), TXF, policy=p).run(m60)
        n, _, f = stats(rr.trades)
        counts.add(rr.trade_count)
        print(f"    {p.name:<38}{rr.trade_count:>4} 筆   {n:>12,.0f}   PF {f:>6.3f}")
    claim("  七組的筆數是否全部相同", "是" if len(counts) == 1 else "否", "是")

    # ---------------------------------------------------------------
    hdr(6, "換月跳空")
    roll = [b.open - a.close for a, b in zip(m60, m60[1:])
            if a.mc_time == SETTLEMENT_CLOSE and a.mc_date in SETTLEMENT_SET]
    norm = [b.open - a.close for a, b in zip(m60, m60[1:]) if a.mc_time == 1345]
    claim("換月點次數", len(roll), 92)
    claim("換月跳空絕對值中位", f"{statistics.median(abs(x) for x in roll):.1f}", "60.5")
    claim("一般日跳空絕對值中位", f"{statistics.median(abs(x) for x in norm):.1f}", "11.0")

    print("\n  結構性檢查：五支不可能跨越換月點（Flat 1230 < 換月 1330）")
    for nm, ts in (("L2", t2), ("L4", t4)):
        se = sum(1 for t in ts if t.entry_date in SETTLEMENT_SET)
        cr = sum(1 for t in ts
                 if spans_rollover(t.entry_date, t.entry_time, t.exit_date, t.exit_time))
        claim(f"  {nm} 結算日進場", se, 0)
        claim(f"  {nm} 跨越換月點", cr, 0)

    # ---------------------------------------------------------------
    hdr(7, "同根出場（2026-09-06 修正的結構缺口）")
    print("  MC 允許進場那根立刻被停損打掉（L1 的 V2.9 取證記錄 12 筆 same-bar deaths）")
    print("  我原本的 runner 讓它結構上不可能。已修正，但**不解釋筆數差異**。")
    from txfcore.engine.fill_mc12 import FillPolicy
    for nm, mk in (("L2", lambda p: BacktestRunner(L2TrendShort(), TXF, policy=p).run(m60)),
                   ("L4", lambda p: MultiStreamRunner(L4ConsolShort(), TXF, policy=p,
                                                      warmup_bars=200).run(m15, m60, md))):
        for sb in (False, True):
            rr = mk(FillPolicy(allow_same_bar_exit=sb))
            ts = [t for t in rr.trades if t.entry_date >= FROM]
            n, wr, pf = stats(ts)
            print(f"    {nm} sb={str(sb):<5}  {len(ts):>3} 筆   {n:>12,.0f}   "
                  f"PF {pf:>6.4f}   同根出場 {getattr(rr, 'same_bar_exits', 0)}")
    print("\n  L2 全歷史 2x2（虧損出場標籤對 MC 的 L1 距離）")
    MC_LOSE = {"TS_InitSL_D": 22, "TS_InitSL_N": 18, "ENGINE_STOP": 4, "TS_TSL_N": 1}
    best = None
    for sb in (False, True):
        for ef in (False, True):
            rr = BacktestRunner(L2TrendShort(), TXF, policy=FillPolicy(
                allow_same_bar_exit=sb, engine_stop_first=ef)).run(m60)
            ts = [t for t in rr.trades if t.entry_date >= FROM]
            lo = collections.Counter(t.exit_label for t in ts if t.net_ntd(TXF) <= 0)
            vec = [lo.get(k, 0) for k in MC_LOSE]
            dist = sum(abs(v - MC_LOSE[k]) for v, k in zip(vec, MC_LOSE))
            print(f"    sb={str(sb):<5} ef={str(ef):<5}  {vec}   距離 {dist}")
            if best is None or dist < best[0]:
                best = (dist, sb, ef)
    print(f"    MC                    {list(MC_LOSE.values())}   距離 0")
    claim("  最佳 sb", best[1], "False")
    claim("  最佳 ef", best[2], "False")
    claim("  最佳距離", best[0], 3)

    print("\n  死設定檢查：policy 的四個欄位是否都真的被讀取")
    import inspect
    from txfcore.engine import fill_mc12
    from txfcore.runtime import backtest as bt_mod, multi as mu_mod
    src = (inspect.getsource(fill_mc12) + inspect.getsource(bt_mod)
           + inspect.getsource(mu_mod))
    for field in ("intrabar", "gap", "allow_same_bar_exit", "engine_stop_first"):
        used = src.count(f"policy.{field}")
        claim(f"  policy.{field} 被讀取", "是" if used else "否（死設定）", "是")

    # ---------------------------------------------------------------
    hdr(8, "H5 對齊規則（2026-09-07）")
    from txfcore.quotes.align import AlignPolicy
    print("  MC 的 of Data2 對齊規則沒有文件。做成可切換的假設，用筆數判定。")
    for pol in (AlignPolicy.CLOSED_ONLY, AlignPolicy.INCLUDE_FORMING):
        rr = MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200,
                               align_policy=pol).run(m15, m60, md)
        ts = [t for t in rr.trades if t.entry_date >= FROM]
        n, wr, pf = stats(ts)
        print(f"    {pol:<18}{len(ts):>4} 筆   {n:>12,.0f}   PF {pf:>6.4f}"
              f"   與 MC 79 筆差 {len(ts)-79:+d}")
    rc = MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200,
                           align_policy=AlignPolicy.CLOSED_ONLY).run(m15, m60, md)
    rf = MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200,
                           align_policy=AlignPolicy.INCLUDE_FORMING).run(m15, m60, md)
    claim("  closed_only 筆數", len([t for t in rc.trades if t.entry_date >= FROM]), 83)
    claim("  include_forming 筆數", len([t for t in rf.trades if t.entry_date >= FROM]), 44)
    print("  → H5 排除。保守對齊（只暴露已收盤）遠比寬鬆對齊接近 MC。")

    # ---------------------------------------------------------------
    hdr(9, "H6 排除四天異常資料")
    from datetime import date as _d
    BAD = {_d(2019, 4, 2), _d(2021, 9, 1), _d(2021, 9, 2), _d(2021, 9, 3)}
    kp = lambda bars: [b for b in bars
                       if trading_day(b.mc_date, b.mc_time) not in BAD]
    r2c = BacktestRunner(L2TrendShort(), TXF).run(kp(m60))
    r4c = MultiStreamRunner(L4ConsolShort(), TXF, warmup_bars=200).run(
        kp(m15), kp(m60), kp(md))
    n2 = len([t for t in r2c.trades if t.entry_date >= FROM])
    n4 = len([t for t in r4c.trades if t.entry_date >= FROM])
    near2 = sum(1 for t in t2 if trading_day(t.entry_date, t.entry_time) in BAD
                or trading_day(t.exit_date, t.exit_time) in BAD)
    near4 = sum(1 for t in t4 if trading_day(t.entry_date, t.entry_time) in BAD
                or trading_day(t.exit_date, t.exit_time) in BAD)
    claim("  那四天的 L2 交易", near2, 0)
    claim("  那四天的 L4 交易", near4, 0)
    claim("  L2 排除後筆數", n2, 81)
    claim("  L4 排除後筆數", n4, 83)
    print("  → H6 排除。異常日不解釋筆數差異。")

    # ---------------------------------------------------------------
    hdr(10, "窗口敏感度（L2）")
    print("  我說過：窗口移動 2.5 個月就差 4 筆")
    for start in (1190101, 1191216, 1200301):
        ts = [t for t in r2.trades if t.entry_date >= start]
        n, wr, pf = stats(ts)
        print(f"    {mc_date_to_date(start)}   {len(ts):>3} 筆   {n:>12,.0f}   PF {pf:.3f}")

    print(f"\n{'='*70}")
    print("✓ 表示與我說過的一致    ✗ 表示我錯了或環境不同")
    print("本工具不證明「符合 MC」。那需要 MC 報告做逐筆 diff。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
