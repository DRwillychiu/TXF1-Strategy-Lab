# -*- coding: utf-8 -*-
"""Why is P29 rare and P51 common?  Decompose the 32,094-frame population.

Willy's question, 2026-08-27: "P29 / P49 / P50 -- what factors were added to
bring the signal frequency down?"

The premise deserves testing rather than answering, because P29 does not in
fact carry an extra factor.  P51 has MORE conditions than P29 (it adds
spanH > spanL) and is still eight times as common.  So whatever makes P29 rare
is not a filter that was bolted on -- it is in the geometry itself.

This script builds the 3x3 contingency table of (high-triple direction) x
(low-triple direction) over every frame, and compares it against what
independence would predict.  Counts only.  No P&L column.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LAB = ['遞增', '遞減', '完全相等', '非單調']


def cls(a):
    if a[0] < a[1] < a[2]:
        return 0
    if a[0] > a[1] > a[2]:
        return 1
    if a[0] == a[1] == a[2]:
        return 2
    return 3


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)

    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])

    frames = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        frames.append(([H[i] for i in hs], [L[i] for i in ls]))
    T = len(frames)
    print('六樞紐交替且低在高下的框架  %s 個\n' % format(T, ','))

    tab = [[0] * 4 for _ in range(4)]
    for hv, lv in frames:
        tab[cls(hv)][cls(lv)] += 1
    rm = [sum(r) for r in tab]
    cm = [sum(tab[i][j] for i in range(4)) for j in range(4)]

    print('=' * 78)
    print(' 高點三元組（列） x 低點三元組（欄）  ---  實際觀測')
    print('=' * 78)
    print('  %-10s %10s %10s %10s %10s %12s' % ('高\\低', *LAB, '列合計'))
    for i in range(4):
        print('  %-10s %10s %10s %10s %10s %12s'
              % (LAB[i], *[format(tab[i][j], ',') for j in range(4)], format(rm[i], ',')))
    print('  %-10s %10s %10s %10s %10s %12s'
          % ('欄合計', *[format(c, ',') for c in cm], format(T, ',')))

    print()
    print('=' * 78)
    print(' 若高、低方向彼此獨立，該有幾個？ ---  觀測 / 期望')
    print('=' * 78)
    print('  %-24s %10s %10s %8s' % ('組合', '觀測', '獨立期望', '倍率'))
    print('  ' + '-' * 56)
    show = [('高遞增 x 低遞減   ← P29 擴散', 0, 1),
            ('高遞減 x 低遞增   ← 收斂（對照）', 1, 0),
            ('高遞增 x 低遞增   ← P51 母集', 0, 0),
            ('高遞減 x 低遞減   ← P52 母集', 1, 1),
            ('高完全相等 x 低遞減 ← P53', 2, 1),
            ('高遞增 x 低完全相等 ← P54', 0, 2)]
    for name, i, j in show:
        exp = rm[i] * cm[j] / float(T)
        obs = tab[i][j]
        print('  %-24s %10s %10.1f %7.2fx'
              % (name, format(obs, ','), exp, (obs / exp) if exp else 0))

    same = tab[0][0] + tab[1][1]
    opp = tab[0][1] + tab[1][0]
    print()
    print('  兩邊都單調的框架中，同向 %s 個 / 反向 %s 個  =  %.1f : 1'
          % (format(same, ','), format(opp, ','), same / float(opp)))

    print()
    print('=' * 78)
    print(' P51 / P52 那個「發散較快」的附加條件，砍掉多少？')
    print('=' * 78)
    n51 = sum(1 for hv, lv in frames
              if cls(hv) == 0 and cls(lv) == 0 and (hv[2] - hv[0]) > (lv[2] - lv[0]))
    n52 = sum(1 for hv, lv in frames
              if cls(hv) == 1 and cls(lv) == 1 and abs(lv[2] - lv[0]) > abs(hv[2] - hv[0]))
    print('  高遞增 x 低遞增  %s  --加上 spanH > spanL-->  %s   (保留 %.1f%%)'
          % (format(tab[0][0], ','), format(n51, ','), 100.0 * n51 / tab[0][0]))
    print('  高遞減 x 低遞減  %s  --加上 spanL > spanH-->  %s   (保留 %.1f%%)'
          % (format(tab[1][1], ','), format(n52, ','), 100.0 * n52 / tab[1][1]))
    print()
    print('  P29 的條件數：2（高遞增、低遞減）')
    print('  P51 的條件數：3（高遞增、低遞增、發散較快）')
    print('  --> P51 條件比 P29 多，數量卻是 P29 的 %.1f 倍。'
          % (n51 / float(tab[0][1])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
