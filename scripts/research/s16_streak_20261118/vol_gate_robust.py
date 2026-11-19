"""前幾名門檻的穩健性檢查（全資料 2000 起）：
  1. 同時段正規化（tod）視窗高原：40／60／90／120 日 × p60／p70
  2. 2001–2019（這次比對沒用到的期間）是否同方向
  3. 2026/10 起每筆死亡交叉放行與否（加入 tod60d）
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_robust.py <1min.txt> <out.md>
"""
import bisect
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, rolling_pct_veto, s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats, ewma_series  # noqa: E402


def tod_veto(bars, ap, slot_idx, days, q):
    def veto(i, _t):
        lst = slot_idx[(bars[i].dt.hour, bars[i].dt.minute)]
        pos = bisect.bisect_left(lst, i)
        hist = sorted(ap[j] for j in lst[max(0, pos - days):pos])
        if len(hist) < days // 2:
            return False
        # 11/19：+1e-9 讓 90×0.70 取 63（與 MC 相同）；11/18 的報表是用舊寫法（取 62）算的
        return ap[i] < hist[min(len(hist) - 1, int(len(hist) * q + 1e-9))]
    return veto


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), datetime(2026, 11, 16, 12, 20))
    ap = atr_pct_series(bars)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    slot_idx = defaultdict(list)
    for i, b in enumerate(bars):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)
    vetoes = {"base": None, "pct60d_p70": rolling_pct_veto(ap, 60, 0.70), "pct60d_p80": rolling_pct_veto(ap, 60, 0.80)}
    ew = ewma_series(ap, 20)
    vetoes["ewma20d_k1.25"] = lambda i, _t: ap[i] < 1.25 * ew[i]
    for d in (40, 60, 90, 120):
        for q in (0.6, 0.7):
            vetoes[f"tod{d}d_p{int(q*100)}"] = tod_veto(bars, ap, slot_idx, d, q)
    runs = {}
    for k, v in vetoes.items():
        runs[k] = s16.run(bars, dict(p), hol, veto=v).trades
        print("done", k, flush=True)
    runs["fixed0.20"] = s16.run(bars, dict(p, Vol_Gate_Pct=0.20), hol).trades
    segs = [("2023 起（主）", datetime(2023, 1, 1), datetime(2099, 1, 1), 3.876),
            ("2020 起", datetime(2020, 1, 1), datetime(2099, 1, 1), 6.876),
            ("2001–2019（未參與這次比對）", datetime(2001, 1, 1), datetime(2020, 1, 1), 19.0)]
    out = ["# S16 門檻穩健性檢查（推論，Python；2 口微台、資金 140,200）", ""]
    for sname, a, b, yrs in segs:
        out += [f"## {sname}", "", "| 方法 | 筆數 | 淨利 | 年化 | 每筆期望值 | PF | 最大回撤（佔資金） | 最長連虧（筆／金額） |",
                "|---|---|---|---|---|---|---|---|"]
        for k, tr in runs.items():
            x = full_stats([micro_net(t) for t in tr if a <= t.exit_dt < b], yrs)
            out.append(f"| {k} | {x['n']} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | {x['pf']:.2f} | "
                       f"{x['mdd']:,.0f}（{x['mdd']/CAP*100:.1f}%） | {x['streak']}／{x['streak_amt']:,.0f} |")
        out.append("")
    idx = {b.dt: i for i, b in enumerate(bars)}
    keys = ["pct60d_p70", "tod60d_p60", "tod60d_p70", "tod90d_p60"]
    out += ["## 2026/10 起現行版每筆死亡交叉：放行（✓）或擋（✗）", "",
            "| 進場 | 損益（元） | 當下 ATR14（點） | " + " | ".join(keys) + " |", "|---" * (len(keys) + 3) + "|"]
    for t in runs["base"]:
        if t.entry_dt >= datetime(2026, 10, 1) and t.entry_label == "SE_MA_DeathCross":
            i = idx[t.entry_dt] - 1
            out.append(f"| {t.entry_dt:%m/%d %H:%M} | {micro_net(t):,.0f} | {ap[i]*bars[i].c/100:.0f} | "
                       + " | ".join("✗" if vetoes[k](i, []) else "✓" for k in keys) + " |")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
