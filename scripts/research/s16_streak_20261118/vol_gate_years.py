"""S16 波動門檻逐年分析（Willy 11/18：只用 ATR 固定門檻，遇到波動放大又縮小會不會失焦？重點看 2025–2026）。

比較三種門檻（全部 2 口微台、含滑價＋手續費 12＋期交稅）：
  base     260825 現行（不設門檻）
  fixed    固定門檻：ATR14/收盤 >= 0.20%（v1.27.0 候選）
  adapt    自適應門檻：ATR14/收盤 >= 自己過去 N 個交易日（5 分 K）的第 q 百分位
           （看的是「相對自己近期」的波動，不受長期波動水準漂移影響）
另列每年 5 分 K 的 ATR% 分布，看固定門檻在各年份放行比例。

Usage: python -I scripts/research/s16_streak_20261118/vol_gate_years.py <1min.txt> <out.md>
"""
import bisect
import sys
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/research/s16_v1260_port"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
from data import load_bars  # noqa: E402
from common import CAP, micro_net, stats  # noqa: E402

BARS_PER_DAY = 228  # 日盤 60 ＋ 夜盤 168 根 5 分 K（近似，只用來換算視窗長度）


def atr_pct_series(bars, n=14):
    out, trs = [], deque()
    s = 0.0
    for i, b in enumerate(bars):
        tr = b.h - b.l if i == 0 else max(b.h, bars[i - 1].c) - min(b.l, bars[i - 1].c)
        trs.append(tr); s += tr
        if len(trs) > n:
            s -= trs.popleft()
        out.append((s / len(trs)) / b.c * 100 if b.c else 0.0)
    return out


def rolling_pct_veto(ap, days, q):
    """回傳 veto(i, trades)：ATR%(i) 低於過去 days 天的第 q 百分位就擋（只用 i 以前的資料）。"""
    win = days * BARS_PER_DAY
    cache = {}

    def veto(i, _trades):
        if i in cache:
            return cache[i]
        lo = max(0, i - win)
        hist = sorted(ap[lo:i])
        if len(hist) < win // 2:
            cache[i] = False
            return False
        thr = hist[min(len(hist) - 1, int(len(hist) * q))]
        cache[i] = ap[i] < thr
        return cache[i]
    return veto


def yearly(trades):
    by = defaultdict(list)
    for t in trades:
        by[t.exit_dt.year].append(micro_net(t))
    return by


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), datetime(2026, 11, 16, 12, 20))
    ap = atr_pct_series(bars)
    base_p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    runs = {"base": s16.run(bars, dict(base_p), hol).trades,
            "fixed0.20": s16.run(bars, dict(base_p, Vol_Gate_Pct=0.20), hol).trades}
    for days, q in ((20, 0.5), (60, 0.5), (60, 0.6), (60, 0.7)):
        runs[f"adapt{days}d_p{int(q*100)}"] = s16.run(bars, dict(base_p), hol,
                                                       veto=rolling_pct_veto(ap, days, q)).trades
    lines = ["# S16 波動門檻逐年分析（推論，Python；2 口微台、資金 140,200）", ""]
    lines += ["## 1. 每年 5 分 K 的 ATR14/收盤（%）分布：固定 0.20% 門檻在各年放行多少", "",
              "| 年 | 中位數 | 75 分位 | 90 分位 | ≥0.20% 的 K 棒比例 |", "|---|---|---|---|---|"]
    yb = defaultdict(list)
    for b, a in zip(bars, ap):
        yb[b.dt.year if hasattr(b, "dt") else int(str(b.mc_date)[:3]) + 1900].append(a)
    for y in sorted(yb):
        v = sorted(yb[y]); n = len(v)
        lines.append(f"| {y} | {v[n//2]:.3f} | {v[int(n*.75)]:.3f} | {v[int(n*.9)]:.3f} | "
                     f"{sum(1 for x in v if x >= 0.20)/n*100:.1f}% |")
    names = list(runs)
    lines += ["", "## 2. 逐年淨利（元）", "", "| 年 | " + " | ".join(names) + " |", "|---" * (len(names) + 1) + "|"]
    ys = {k: yearly(v) for k, v in runs.items()}
    allyears = sorted({y for d in ys.values() for y in d})
    for y in allyears:
        lines.append(f"| {y} | " + " | ".join(f"{sum(ys[k].get(y, [])):,.0f} ({len(ys[k].get(y, []))})"
                                               for k in names) + " |")
    lines += ["", "（括號內為筆數）", "", "## 3. 分段總表", "",
              "| 區段 | 版本 | 筆數 | 淨利 | PF | 最大回撤 | 佔 140,200 | 最長連虧 |", "|---|---|---|---|---|---|---|---|"]
    segs = [("2001–2019", "2001", "2019-12-31 23:59"), ("2020–2024", "2020", "2024-12-31 23:59"),
            ("2025–2026（重點）", "2025", "2099"), ("2020 起全期", "2020", "2099")]
    for sname, a, b in segs:
        for k in names:
            p = [micro_net(t) for t in runs[k] if a <= t.exit_dt.strftime("%Y-%m-%d %H:%M") <= b]
            s = stats(p)
            lines.append(f"| {sname} | {k} | {s['n']} | {s['net']:,.0f} | {s['pf']:.2f} | {s['mdd']:,.0f} | "
                         f"{s['mdd']/CAP*100:.1f}% | {s['streak']} |")
    Path(sys.argv[2]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
