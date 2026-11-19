"""因子分析：只用設計期（2000–2019）找，驗證期（2020–2026/8/22）看方向是否一致。

標籤（每個死亡交叉事件，即實際進場的那筆）：
  qs   ＝ 以快速停損出場（連續小虧的來源）
  ret  ＝ 該筆淨報酬佔名目（%，與指數水準無關）
統計：五分位表、Spearman、置換檢定 p 值（2,000 次）、Benjamini–Hochberg 校正、驗證期方向一致性。
"""
from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import seg_of  # noqa: E402

FEATS = ["slope", "spread_atr", "dist_slow_atr", "natr", "atr_rank", "er12", "er48", "er144",
         "ret12_atr", "ret48_atr", "relvol", "cross_n60", "cross_n240", "bars_since_cross", "body_atr",
         "d_ma20", "d_ma60", "d_r5", "hour", "night", "weekday", "settle_week"]


def rank(x):
    o = sorted(range(len(x)), key=lambda k: x[k])
    r = [0.0] * len(x)
    k = 0
    while k < len(o):
        j = k
        while j + 1 < len(o) and x[o[j + 1]] == x[o[k]]:
            j += 1
        for m in range(k, j + 1):
            r[o[m]] = (k + j) / 2
        k = j + 1
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra)); vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return cov / (va * vb) if va and vb else 0.0


def perm_p(a, b, n=2000, seed=3):
    obs = abs(spearman(a, b))
    rnd = random.Random(seed)
    bb = b[:]
    hit = 0
    ra = rank(a)
    for _ in range(n):
        rnd.shuffle(bb)
        rb = rank(bb)
        m = len(a); ma = sum(ra) / m; mb = sum(rb) / m
        cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
        va = math.sqrt(sum((x - ma) ** 2 for x in ra)); vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
        hit += abs(cov / (va * vb)) >= obs - 1e-12
    return (hit + 1) / (n + 1)


def quint(xs, ys, cuts=None):
    if cuts is None:
        s = sorted(xs)
        cuts = [s[int(len(s) * q / 5)] for q in (1, 2, 3, 4)]
    bins = [[] for _ in range(5)]
    for x, y in zip(xs, ys):
        k = sum(x >= c for c in cuts)
        bins[k].append(y)
    return cuts, bins


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    ev = list(csv.DictReader(open(d / "events.csv", encoding="utf-8")))
    tr = {int(t["sig_i"]): t for t in csv.DictReader(open(d / "trades_base.csv", encoding="utf-8"))}
    rows = []
    for e in ev:
        i = int(e["i"])
        if i not in tr:
            continue
        t = tr[i]
        r = dict(seg=seg_of(e["dt"]), qs=int(t["exit_label"].startswith("SX_MA_QuickStop")),
                 ret=float(t["net_micro2"]) / (float(t["entry_px"]) * 20) * 100)
        ok = True
        for f in FEATS:
            v = e[f]
            if v in ("", "nan"):
                ok = False
                break
            r[f] = float(v)
        if ok:
            rows.append(r)
    D = [r for r in rows if r["seg"] == "design"]
    V = [r for r in rows if r["seg"] == "valid"]
    print(f"事件：設計期 {len(D)}、驗證期 {len(V)}（只算實際進場的死亡交叉；缺值剔除）")
    print(f"設計期快速停損率 {sum(r['qs'] for r in D) / len(D):.1%}，驗證期 {sum(r['qs'] for r in V) / len(V):.1%}\n")
    res = []
    for f in FEATS:
        x = [r[f] for r in D]
        rho_q = spearman(x, [r["qs"] for r in D])
        rho_r = spearman(x, [r["ret"] for r in D])
        p = perm_p(x, [r["qs"] for r in D])
        xv = [r[f] for r in V]
        rho_qv = spearman(xv, [r["qs"] for r in V])
        res.append((f, rho_q, p, rho_r, rho_qv))
    # Benjamini–Hochberg（FDR 10%）
    m = len(res)
    order = sorted(range(m), key=lambda k: res[k][2])
    passed = set()
    for rnk, k in enumerate(order, 1):
        if res[k][2] <= 0.10 * rnk / m:
            passed = set(order[:rnk])
    print(f"{'因子':<18}{'ρ(快停)設計':>12}{'置換p':>8}{'BH通過':>7}{'ρ(報酬)設計':>12}{'ρ(快停)驗證':>12}{'方向一致':>8}")
    for k, (f, rq, p, rr, rqv) in enumerate(res):
        same = (rq > 0) == (rqv > 0)
        print(f"{f:<18}{rq:>12.3f}{p:>8.3f}{('是' if k in passed else ''):>7}{rr:>12.3f}{rqv:>12.3f}{('是' if same else '否'):>8}")
    print("\n== BH 通過且驗證期方向一致的因子：五分位（切點取自設計期）")
    for k, (f, rq, p, rr, rqv) in enumerate(res):
        if k in passed and (rq > 0) == (rqv > 0):
            cuts, bd = quint([r[f] for r in D], [r["qs"] for r in D])
            _, bdr = quint([r[f] for r in D], [r["ret"] for r in D], cuts)
            _, bv = quint([r[f] for r in V], [r["qs"] for r in V], cuts)
            _, bvr = quint([r[f] for r in V], [r["ret"] for r in V], cuts)
            print(f"  {f}  切點 {[round(c, 4) for c in cuts]}")
            for q in range(5):
                def avg(a): return sum(a) / len(a) if a else float("nan")
                print(f"    Q{q + 1}: 設計 n={len(bd[q]):>3} 快停率 {avg(bd[q]):.0%} 平均報酬 {avg(bdr[q]):+.3f}%"
                      f" ｜ 驗證 n={len(bv[q]):>3} 快停率 {avg(bv[q]):.0%} 平均報酬 {avg(bvr[q]):+.3f}%")


if __name__ == "__main__":
    main()
