"""S16 波動門檻：多種「基準」方法的回測比對（Willy 11/18）。

問題：60 日百分位基準在大波動後被拉高，之後最長約 60 天門檻偏高、交易變稀疏（11 月就是例子）。
比對的方法（全部只用當下以前的資料，沒有偷看未來）：
  base        260825 現行，不設門檻
  fixed       ATR14/收盤 >= 0.20%
  pct{N}d_q   ATR% >= 過去 N 天所有 5 分 K 的第 q 百分位（11/18 的自適應版本）
  ewma{H}_k   ATR% >= k × 指數加權平均 ATR%（半衰期 H 天；RiskMetrics 式，舊的大波動按指數遺忘）
  har_k       ATR% >= k × HAR 基準（1 日、5 日、22 日平均 ATR% 的等權平均；Corsi 2009 的多週期概念）
  tod{N}d_q   ATR% >= 同一時段（同一個 HH:MM）過去 N 天的第 q 百分位（去除盤中時段季節性；
              Andersen & Bollerslev 1997）
  ratio1d_k   ATR% >= k × 過去 1 日平均 ATR%（短期擴張）
  cost_k      ATR14 點數 >= k × 來回成本（約 14 點：滑價 10＋手續費 2.4＋期交稅約 1.7）

指標：最長連虧（筆）、最長連虧金額、最大回撤（佔 140,200）、年化報酬（單利，固定 2 口）、每筆期望值。
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_methods.py <1min.txt> <out.md> [start=2019-01-01]
"""
import bisect
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, rolling_pct_veto, s16, load_bars, micro_net, CAP, BARS_PER_DAY  # noqa: E402

COST_PTS = 14.0


def full_stats(pnls, years):
    eq = peak = mdd = 0.0
    run = longest = 0
    run_amt = worst_amt = 0.0
    for x in pnls:
        eq += x
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
        if x < 0:
            run += 1; run_amt += x
        else:
            run = 0; run_amt = 0.0
        longest = max(longest, run)
        worst_amt = min(worst_amt, run_amt)
    n = len(pnls)
    gp = sum(x for x in pnls if x > 0); gl = -sum(x for x in pnls if x < 0)
    net = sum(pnls)
    return dict(n=n, net=net, pf=gp / gl if gl else float("inf"), mdd=mdd, streak=longest, streak_amt=worst_amt,
                ann=net / CAP / years * 100, exp=net / n if n else 0.0, win=sum(x > 0 for x in pnls) / n if n else 0)


def ewma_series(ap, half_life_days):
    hl = half_life_days * BARS_PER_DAY
    a = 1 - 0.5 ** (1 / hl)
    out, m = [], ap[0]
    for x in ap:
        out.append(m)            # 只到上一根
        m = m + a * (x - m)
    return out


def prefix(ap):
    ps = [0.0]
    for x in ap:
        ps.append(ps[-1] + x)
    return ps


def mean_before(ps, i, n):
    lo = max(0, i - n)
    return (ps[i] - ps[lo]) / (i - lo) if i > lo else 0.0


def make_vetoes(bars, ap):
    v = {}
    for days in (10, 20, 40, 60):
        for q in (0.6, 0.7, 0.8):
            v[f"pct{days}d_p{int(q*100)}"] = rolling_pct_veto(ap, days, q)
    for hl in (5, 10, 20):
        ew = ewma_series(ap, hl)
        for k in (1.0, 1.25, 1.5):
            v[f"ewma{hl}d_k{k}"] = (lambda ew, k: lambda i, _t: ap[i] < k * ew[i])(ew, k)
    ps = prefix(ap)
    for k in (1.0, 1.25, 1.5):
        def har(i, _t, k=k):
            base = (mean_before(ps, i, BARS_PER_DAY) + mean_before(ps, i, 5 * BARS_PER_DAY)
                    + mean_before(ps, i, 22 * BARS_PER_DAY)) / 3
            return ap[i] < k * base
        v[f"har_k{k}"] = har
    for k in (1.25, 1.5, 2.0):
        v[f"ratio1d_k{k}"] = (lambda k: lambda i, _t: ap[i] < k * mean_before(ps, i, BARS_PER_DAY))(k)
    slot_idx = defaultdict(list)
    for i, b in enumerate(bars):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)
    for days in (20, 60):
        for q in (0.6, 0.7, 0.8):
            def tod(i, _t, days=days, q=q):
                lst = slot_idx[(bars[i].dt.hour, bars[i].dt.minute)]
                pos = bisect.bisect_left(lst, i)
                hist = sorted(ap[j] for j in lst[max(0, pos - days):pos])
                if len(hist) < days // 2:
                    return False
                # 11/19：+1e-9 與 MC 的 IntPortion 結果相同（見 vol_gate_robust.tod_veto）
                return ap[i] < hist[min(len(hist) - 1, int(len(hist) * q + 1e-9))]
            v[f"tod{days}d_p{int(q*100)}"] = tod
    for k in (2, 3, 4, 5):
        v[f"cost_k{k}"] = (lambda k: lambda i, _t: ap[i] * bars[i].c / 100 < k * COST_PTS)(k)
    return v


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    start = datetime.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime(2019, 1, 1)
    bars = load_bars(sys.argv[1], start, datetime(2026, 11, 16, 12, 20))
    ap = atr_pct_series(bars)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    runs = {"base": s16.run(bars, dict(p), hol).trades,
            "fixed0.20": s16.run(bars, dict(p, Vol_Gate_Pct=0.20), hol).trades}
    for name, veto in make_vetoes(bars, ap).items():
        runs[name] = s16.run(bars, dict(p), hol, veto=veto).trades
        print("done", name, flush=True)
    segs = [("2023 起（主）", datetime(2023, 1, 1), 3.876), ("2020 起", datetime(2020, 1, 1), 6.876)]
    rows = {}
    for name, tr in runs.items():
        rows[name] = [full_stats([micro_net(t) for t in tr if t.exit_dt >= a], yrs) for _, a, yrs in segs]
    out = ["# S16 波動門檻方法比對（推論，Python；2 口微台、資金 140,200、含滑價＋手續費 12＋期交稅）", "",
           "年化＝單利（淨利 ÷ 140,200 ÷ 年數，固定 2 口）。期望值＝每筆平均淨利（元）。", ""]
    for si, (sname, _, _) in enumerate(segs):
        out += [f"## {sname}（依「2023 起」年化排序）" if si == 0 else f"## {sname}", "",
                "| 方法 | 筆數 | 淨利 | 年化 | 每筆期望值 | PF | 最大回撤（佔資金） | 最長連虧（筆／金額） | 勝率 |",
                "|---|---|---|---|---|---|---|---|---|"]
        order = sorted(rows, key=lambda k: -rows[k][0]["ann"])
        for k in order:
            x = rows[k][si]
            out.append(f"| {k} | {x['n']} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | {x['pf']:.2f} | "
                       f"{x['mdd']:,.0f}（{x['mdd']/CAP*100:.1f}%） | {x['streak']}／{x['streak_amt']:,.0f} | "
                       f"{x['win']*100:.0f}% |")
        out.append("")
    # 11 月個案：base 在 2026-10-01 之後的死亡交叉進場，各方法擋不擋
    vetoes = make_vetoes(bars, ap)
    idx = {b.dt: i for i, b in enumerate(bars)}
    oct_ = [t for t in runs["base"] if t.entry_dt >= datetime(2026, 10, 1) and t.entry_label == "SE_MA_DeathCross"]
    keys = ["pct60d_p70", "pct20d_p70", "pct10d_p70", "ewma5d_k1.0", "ewma10d_k1.25", "har_k1.25", "tod20d_p70", "cost_k3"]
    out += ["## 2026/10 起現行版的每一筆死亡交叉：各方法是否放行（✓ 放行／✗ 擋）", "",
            "| 進場 | 損益（元） | 當下 ATR14（點） | " + " | ".join(keys) + " |", "|---" * (len(keys) + 3) + "|"]
    for t in oct_:
        i = idx[t.entry_dt] - 1
        out.append(f"| {t.entry_dt:%m/%d %H:%M} | {micro_net(t):,.0f} | {ap[i]*bars[i].c/100:.0f} | "
                   + " | ".join("✗" if vetoes[k](i, []) else "✓" for k in keys) + " |")
    out.append("")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
