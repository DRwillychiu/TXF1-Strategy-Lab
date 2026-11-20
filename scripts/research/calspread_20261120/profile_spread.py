"""跨月價差資料檢查（只描述資料，不含任何進出場規則）。
價差 = TXF2 收盤 - TXF1 收盤，同一分鐘兩邊都有成交才算；只看日盤 08:46-13:30。
結算日 = TXF1 日盤最後一根 <= 13:30 的那天（由資料反推）。
Usage: python -I scripts/research/calspread_20261120/profile_spread.py <TXF1 1分.txt> <TXF2 1分.txt> <out.md> [起始年=2020]
"""
import sys, statistics as st
from collections import defaultdict

def load(path, y0):
    d = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        next(f)
        for ln in f:
            p = ln.split(",")
            if int(p[0].split("/")[0]) < y0:
                continue
            t = p[1][:5]
            if "08:46" <= t <= "13:45":
                d[(p[0], t)] = (float(p[5]), int(p[8]))
    return d

def dkey(s):
    y, m, dd = s.split("/")
    return (int(y), int(m), int(dd))

def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]

def main():
    f1, f2, out = sys.argv[1:4]
    y0 = int(sys.argv[4]) if len(sys.argv) > 4 else 2020
    a, b = load(f1, y0), load(f2, y0)
    days = sorted({k[0] for k in a}, key=dkey)
    last1 = defaultdict(str)
    for (d, t) in a:
        last1[d] = max(last1[d], t)
    settle = [d for d in days if last1[d] <= "13:30" and sum(1 for k in a if k[0] == d) > 200]
    sset = set(settle)
    # 距離結算還有幾個交易日（結算日 = 0）
    dts, nxt = {}, None
    for d in reversed(days):
        if d in sset:
            nxt = 0
        dts[d] = nxt
        if nxt is not None:
            nxt += 1
    by_year, by_month, by_dts = defaultdict(list), defaultdict(list), defaultdict(list)
    cov, vol2 = defaultdict(list), defaultdict(list)
    n2, v2 = defaultdict(int), defaultdict(int)
    for (d, t), (c2, vv) in b.items():
        if t > "13:30" or (d, t) not in a:
            continue
        c1 = a[(d, t)][0]
        sp = c2 - c1
        y, m, _ = dkey(d)
        by_year[y].append((sp, sp / c1 * 100))
        by_month[m].append(sp / c1 * 100)
        if dts.get(d) is not None:
            by_dts[min(dts[d], 20)].append(sp / c1 * 100)
        n2[d] += 1
        v2[d] += vv
    for d in days:
        k = dts.get(d)
        if k is not None:
            cov[min(k, 20)].append(n2[d])
            vol2[min(k, 20)].append(v2[d])
    L = [f"# 跨月價差資料檢查（{y0} 起；日盤 08:46-13:30）", "",
         f"- 交易日 {len(days)} 天；由資料反推的結算日 {len(settle)} 個（最後 3 個：{', '.join(settle[-3:])}）",
         f"- 兩邊同一分鐘都有成交的分鐘數：{sum(len(v) for v in by_year.values()):,}",
         "- 價差 = 次月 - 近月；百分比 = 價差 / 近月價", "",
         "## 逐年", "| 年 | 分鐘數 | 中位數（點） | 5% | 95% | 中位數（%） | 5%（%） | 95%（%） |", "|---|---|---|---|---|---|---|---|"]
    for y in sorted(by_year):
        p = [x[0] for x in by_year[y]]; r = [x[1] for x in by_year[y]]
        L.append(f"| {y} | {len(p):,} | {st.median(p):.0f} | {q(p,.05):.0f} | {q(p,.95):.0f} | {st.median(r):.2f} | {q(r,.05):.2f} | {q(r,.95):.2f} |")
    L += ["", "## 逐月份（全期合併，看除息季）", "| 月 | 中位數（%） | 5%（%） | 95%（%） |", "|---|---|---|---|"]
    for m in sorted(by_month):
        r = by_month[m]
        L.append(f"| {m} | {st.median(r):.2f} | {q(r,.05):.2f} | {q(r,.95):.2f} |")
    L += ["", "## 依距離結算的交易日數（0 = 結算日）", "| 距結算 | 天數 | 次月每天有成交的分鐘數（中位） | 次月日盤成交口數（中位） | 價差中位（%） | 5%（%） | 95%（%） |", "|---|---|---|---|---|---|---|"]
    for k in sorted(cov):
        r = by_dts.get(k, [0])
        lab = f"{k}" if k < 20 else "20 以上"
        L.append(f"| {lab} | {len(cov[k])} | {st.median(cov[k]):.0f} | {st.median(vol2[k]):.0f} | {st.median(r):.2f} | {q(r,.05):.2f} | {q(r,.95):.2f} |")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L))

if __name__ == "__main__":
    main()
