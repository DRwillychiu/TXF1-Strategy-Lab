"""依 docs/research/basis_criteria_20261120.md 四條通過條件，逐組判定研究 C1。
Usage: python -I scripts/research/calspread_20261120/judge_c.py docs/research/basis_study_20261120.md
"""
import sys

GRID_N, GRID_K, GRID_H = (3, 5, 10), (2, 3, 4, 6), (30, 60, 120)


def table(lines, header_start):
    i = next(i for i, l in enumerate(lines) if l.startswith(header_start))
    rows = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        rows.append([c.strip() for c in l.strip("|").split("|")])
    return rows


def main():
    lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
    g = {}
    for r in table(lines, "| N | K | 持有上限 | 筆數 | 勝率"):
        k = (int(r[0]), float(r[1]), int(r[2]))
        g[k] = dict(n=int(r[3]), gross=float(r[5]), bas=float(r[6]), net=float(r[8]), r95=float(r[10]))
    for r in table(lines, "| N | K | 持有上限 | 2020"):
        k = (int(r[0]), float(r[1]), int(r[2]))
        ys = [float(x) for x in r[3:10]]
        g[k]["pos_years"], g[k]["y2026"] = sum(v > 0 for v in ys), ys[-1]

    def c1(k):
        return g[k]["net"] > 0 and g[k]["net"] > g[k]["r95"]

    def c2(k):
        return g[k]["pos_years"] >= 5 and g[k]["y2026"] > 0

    def c4(k):
        return g[k]["gross"] > 0 and g[k]["bas"] >= 0.5 * g[k]["gross"]

    def neigh(k):
        N, K, H = k
        out = []
        for grid, idx in ((GRID_N, 0), (GRID_K, 1), (GRID_H, 2)):
            p = grid.index(k[idx])
            for q in (p - 1, p + 1):
                if 0 <= q < len(grid):
                    nk = list(k)
                    nk[idx] = grid[q]
                    out.append(tuple(nk))
        return out

    def c3(k):
        return all(g[nk]["net"] > 0 for nk in neigh(k))

    print("| N | K | 持有 | 筆數 | 每筆淨利 | 隨機95% | 正年數 | 2026 | 條件1 | 條件2 | 條件3 | 條件4 | 判定 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    passed = []
    for N in GRID_N:
        for K in GRID_K:
            for H in GRID_H:
                k = (N, float(K), H)
                kk = (N, K, H)
                r = g[k]
                cs = [c1(k), c2(k), c3((N, K, H)) , c4(k)]
                ok = all(cs)
                if ok:
                    passed.append(kk)
                m = lambda b: "✓" if b else "✗"
                print(f"| {N} | {K} | {H} | {r['n']} | {r['net']:.2f} | {r['r95']:.2f} | {r['pos_years']} | {r['y2026']:.0f} | "
                      f"{m(cs[0])} | {m(cs[1])} | {m(cs[2])} | {m(cs[3])} | {'通過' if ok else '—'} |")
    print()
    print(f"四條全過：{len(passed)} 組 {passed}")


if __name__ == "__main__":
    g = None
    main()
