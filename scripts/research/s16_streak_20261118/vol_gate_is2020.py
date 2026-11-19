"""S16 波動門檻：樣本內拉長到 2020（Willy 11/18：「多重比較偏誤，那就把樣本內的時間周期拉長至2020」）。

1. 45 種門檻在 2020-01-01～2026-11-16 重新排名（四項目標：年化、每筆期望值、最大回撤、最長連虧）
2. 逐年（2020–2026）看 base、A（tod60d_p70）、B（tod90d_p70）與前幾名
3. 過度擬合檢定（全部只用 2020 起的日損益）：
   a. CSCV 的 PBO（Bailey, Borwein, López de Prado & Zhu 2017）：日損益切 16 段，C(16,8)=12,870 種切法；
      每種切法用一半挑「夏普最高」的門檻，看它在另一半的名次；PBO＝挑出來的在另一半落到後半段的機率
   b. Deflated Sharpe Ratio（Bailey & López de Prado 2014）：試驗數 N＝45（另列 N＝100 敏感度）
   c. 前段選、後段驗：2020–2022 年化排名 vs 2023 起年化排名的 Spearman 相關；2020–2022 前五名在 2023 起的表現
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_is2020.py <1min.txt> <out.md> <daily.csv>
"""
import itertools
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import NormalDist, fmean, pstdev

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats, make_vetoes  # noqa: E402
from vol_gate_robust import tod_veto  # noqa: E402

IS_START = datetime(2020, 1, 1)
SPLIT = datetime(2023, 1, 1)
END = datetime(2026, 11, 16, 12, 20)
A, B = "tod60d_p70", "tod90d_p70"
EULER = 0.5772156649015329
Z = NormalDist()
S_BLOCKS = 16


def session_date(dt):
    """夜盤凌晨（08:00 前）算前一個交易日。"""
    return (dt - timedelta(days=1)).date() if dt.hour < 8 else dt.date()


def sharpe_from(agg, blocks):
    n = sum(agg[b][0] for b in blocks)
    s = sum(agg[b][1] for b in blocks)
    ss = sum(agg[b][2] for b in blocks)
    m = s / n
    v = ss / n - m * m
    return m / math.sqrt(v) if v > 0 else 0.0


def moments(r):
    m = fmean(r)
    sd = pstdev(r)
    g3 = sum((x - m) ** 3 for x in r) / len(r) / sd ** 3
    g4 = sum((x - m) ** 4 for x in r) / len(r) / sd ** 4
    return m / sd, g3, g4


def dsr(sr, g3, g4, T, n_trials, v_sr):
    sr0 = math.sqrt(v_sr) * ((1 - EULER) * Z.inv_cdf(1 - 1 / n_trials)
                             + EULER * Z.inv_cdf(1 - 1 / (n_trials * math.e)))
    den = math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr * sr)
    return sr0, Z.cdf((sr - sr0) * math.sqrt(T - 1) / den), Z.cdf(sr * math.sqrt(T - 1) / den)


def ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    for pos, i in enumerate(order):
        r[i] = pos + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = fmean(rx), fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return num / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), END)
    ap = atr_pct_series(bars)
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    slot_idx = defaultdict(list)
    for i, b in enumerate(bars):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)
    vetoes = {"base": None}
    vetoes.update(make_vetoes(bars, ap))
    for d in (40, 90, 120):
        for q in (0.6, 0.7):
            vetoes[f"tod{d}d_p{int(q*100)}"] = tod_veto(bars, ap, slot_idx, d, q)
    runs = {}
    for k, v in vetoes.items():
        runs[k] = [t for t in s16.run(bars, dict(p), hol, veto=v).trades if t.exit_dt >= IS_START]
        print("done", k, flush=True)
    runs["fixed0.20"] = [t for t in s16.run(bars, dict(p, Vol_Gate_Pct=0.20), hol).trades if t.exit_dt >= IS_START]
    names = list(runs)
    N = len(names)

    def seg(k, a, b, yrs):
        return full_stats([micro_net(t) for t in runs[k] if a <= t.exit_dt < b], yrs)

    full = {k: seg(k, IS_START, datetime(2099, 1, 1), 6.876) for k in names}
    early = {k: seg(k, IS_START, SPLIT, 3.0) for k in names}
    late = {k: seg(k, SPLIT, datetime(2099, 1, 1), 3.876) for k in names}
    b0 = full["base"]

    def wins(x):
        return [x["ann"] > b0["ann"], x["exp"] > b0["exp"], x["mdd"] > b0["mdd"], x["streak"] < b0["streak"]]

    out = ["# S16 門檻：樣本內拉長到 2020（推論，Python；2 口微台、資金 140,200）", "",
           f"樣本內＝2020-01-01～2026-11-16（6.876 年）；門檻種類 N＝{N}（含 base、固定 0.20%）。",
           "年化＝單利（淨利 ÷ 140,200 ÷ 年數，固定 2 口）；四項＝年化↑、每筆期望值↑、最大回撤↓、最長連虧↓，逐項和 base 比。", "",
           "## 1. 2020 起排名（依年化）", "",
           "| 名次 | 方法 | 筆數 | 淨利 | 年化 | 每筆期望值 | PF | 最大回撤（佔資金） | 最長連虧（筆／金額） | 四項勝 base |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    order = sorted(names, key=lambda k: -full[k]["ann"])
    for r, k in enumerate(order, 1):
        x = full[k]
        w = wins(x)
        tag = f"**{k}**" if k in (A, B, "base") else k
        out.append(f"| {r} | {tag} | {x['n']} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | {x['pf']:.2f} | "
                   f"{x['mdd']:,.0f}（{x['mdd']/CAP*100:.1f}%） | {x['streak']}／{x['streak_amt']:,.0f} | "
                   f"{sum(w)}/4 |")
    all4 = [k for k in order if all(wins(full[k]))]
    out += ["", f"四項全勝 base 的有 {len(all4)} 種：" + "、".join(all4), ""]

    # 逐年
    show = ["base", A, B] + [k for k in order if k not in ("base", A, B)][:4]
    years = list(range(2020, 2027))
    out += ["## 2. 逐年淨利（元；括號為筆數）", "", "| 年 | " + " | ".join(show) + " |", "|---" * (len(show) + 1) + "|"]
    for y in years:
        cells = []
        for k in show:
            v = [micro_net(t) for t in runs[k] if t.exit_dt.year == y]
            cells.append(f"{sum(v):,.0f}（{len(v)}）")
        out.append(f"| {y} | " + " | ".join(cells) + " |")
    out.append("")
    out += ["逐年最大回撤（佔資金 %）", "", "| 年 | " + " | ".join(show) + " |", "|---" * (len(show) + 1) + "|"]
    for y in years:
        cells = []
        for k in show:
            x = full_stats([micro_net(t) for t in runs[k] if t.exit_dt.year == y], 1.0)
            cells.append(f"{x['mdd']/CAP*100:.1f}%")
        out.append(f"| {y} | " + " | ".join(cells) + " |")
    out.append("")

    # 日損益矩陣
    days = sorted({session_date(b.dt) for b in bars if b.dt >= IS_START})
    di = {d: j for j, d in enumerate(days)}
    daily = {k: [0.0] * len(days) for k in names}
    for k in names:
        for t in runs[k]:
            daily[k][di[session_date(t.exit_dt)]] += micro_net(t)
    with open(sys.argv[3], "w", encoding="utf-8", newline="") as f:
        f.write("date," + ",".join(names) + "\n")
        for j, d in enumerate(days):
            f.write(f"{d}," + ",".join(f"{daily[k][j]:.0f}" for k in names) + "\n")

    # CSCV PBO
    T = len(days)
    edges = [round(T * s / S_BLOCKS) for s in range(S_BLOCKS + 1)]
    agg = {}
    for k in names:
        r = [x / CAP for x in daily[k]]
        agg[k] = [(edges[s + 1] - edges[s], sum(r[edges[s]:edges[s + 1]]),
                   sum(x * x for x in r[edges[s]:edges[s + 1]])) for s in range(S_BLOCKS)]
    lam, chosen, oos_neg, oos_beats_base = [], defaultdict(int), 0, 0
    allb = set(range(S_BLOCKS))
    for c in itertools.combinations(range(S_BLOCKS), S_BLOCKS // 2):
        ins, oos = c, tuple(allb - set(c))
        best = max(names, key=lambda k: sharpe_from(agg[k], ins))
        chosen[best] += 1
        o = {k: sharpe_from(agg[k], oos) for k in names}
        rk = sum(1 for k in names if o[k] < o[best]) + 0.5 * (sum(1 for k in names if o[k] == o[best]) - 1) + 1
        w = rk / (N + 1)
        lam.append(math.log(w / (1 - w)))
        oos_neg += o[best] < 0
        oos_beats_base += o[best] > o["base"]
    ncomb = len(lam)
    pbo = sum(1 for x in lam if x <= 0) / ncomb
    out += ["## 3. 過度擬合檢定", "",
            f"### a. PBO（CSCV，{S_BLOCKS} 段 × C({S_BLOCKS},{S_BLOCKS//2})＝{ncomb:,} 種切法，選法＝日損益夏普最高）", "",
            f"- PBO（挑出的門檻在另一半落到中位數以下的機率）：**{pbo*100:.1f}%**",
            f"- 挑出的門檻在另一半夏普 < 0 的比例：{oos_neg/ncomb*100:.1f}%",
            f"- 挑出的門檻在另一半贏過 base 的比例：{oos_beats_base/ncomb*100:.1f}%",
            f"- 挑出的門檻在另一半的名次（logit λ）中位數：{sorted(lam)[ncomb//2]:.2f}（> 0 表示落在前半）",
            "- 最常被挑中的門檻：" + "、".join(f"{k} {v/ncomb*100:.0f}%" for k, v in
                                       sorted(chosen.items(), key=lambda kv: -kv[1])[:6]), ""]

    # DSR
    srs = {}
    for k in names:
        r = [x / CAP for x in daily[k]]
        srs[k] = moments(r)
    v_sr = pstdev([srs[k][0] for k in names]) ** 2
    out += [f"### b. Deflated Sharpe Ratio（日報酬，T＝{T} 個交易日；試驗間夏普變異 V＝{v_sr:.3e}）", "",
            "| 方法 | 年化夏普 | PSR（對 0） | 門檻夏普 SR0（N=45→年化） | DSR（N=45） | DSR（N=100） |", "|---|---|---|---|---|---|"]
    best_sr = max(names, key=lambda k: srs[k][0])
    for k in dict.fromkeys(["base", A, B, best_sr]):
        sr, g3, g4 = srs[k]
        sr0, d45, psr = dsr(sr, g3, g4, T, N, v_sr)
        _, d100, _ = dsr(sr, g3, g4, T, 100, v_sr)
        out.append(f"| {k} | {sr*math.sqrt(252):.2f} | {psr*100:.1f}% | {sr0*math.sqrt(252):.2f} | "
                   f"{d45*100:.1f}% | {d100*100:.1f}% |")
    out += ["", "DSR ≥ 95% ＝ 扣掉「試了很多種才挑到」的運氣後，夏普仍顯著大於 0。", ""]

    # 前段選、後段驗
    rho = spearman([early[k]["ann"] for k in names], [late[k]["ann"] for k in names])
    top_e = sorted(names, key=lambda k: -early[k]["ann"])
    out += ["### c. 前段選、後段驗（2020–2022 選 → 2023 起驗）", "",
            f"- 45 種門檻的年化排名，前段 vs 後段 Spearman 相關：**{rho:.2f}**",
            "", "| 前段名次 | 方法 | 2020–2022 年化 | 2023 起年化 | 2023 起期望值 | 2023 起回撤 | 2023 起連虧 | 2023 起名次 |",
            "|---|---|---|---|---|---|---|---|"]
    late_rank = {k: r for r, k in enumerate(sorted(names, key=lambda k: -late[k]["ann"]), 1)}
    for r, k in enumerate(top_e, 1):
        if r <= 5 or k in ("base", A, B):
            e, l = early[k], late[k]
            out.append(f"| {r} | {k} | {e['ann']:.1f}% | {l['ann']:.1f}% | {l['exp']:,.0f} | "
                       f"{l['mdd']/CAP*100:.1f}% | {l['streak']} | {late_rank[k]} |")
    out.append("")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
