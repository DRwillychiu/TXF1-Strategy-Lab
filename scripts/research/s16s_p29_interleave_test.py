# -*- coding: utf-8 -*-
"""How much does P29 survive if the pivots must ALTERNATE?

Found 2026-08-25 while drawing a real instance for the diagram. Sec 2 of the
spec asks for three rising pivot highs and three falling pivot lows and stops
there. It never says the six pivots have to alternate H L H L H L in time, nor
that the lows must sit below the highs. Without those, a "broadening" can be
returned whose lower trendline sits ABOVE its upper one -- the lines cross and
the shape is not a broadening at all.

This measures, on all 421,513 bars, what each extra requirement costs. Counts
only. No P&L column.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


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
    print('bars %d   pivots %d H / %d L' % (N, len(PH), len(PL)))
    print()

    base = mono = alt = below = sess = 0
    spans = []
    for k in range(2, len(PH)):
        h3, h2, h1 = PH[k - 2], PH[k - 1], PH[k]
        lows = [x for x in PL if x < h1]
        if len(lows) < 3:
            continue
        l3, l2, l1 = lows[-3], lows[-2], lows[-1]
        base += 1
        if not (H[h3] < H[h2] < H[h1] and L[l3] > L[l2] > L[l1]):
            continue
        mono += 1
        pts = sorted([h3, h2, h1, l3, l2, l1])
        kind = dict([(x, 'H') for x in (h3, h2, h1)] + [(x, 'L') for x in (l3, l2, l1)])
        seq = [kind[x] for x in pts]
        if any(seq[i] == seq[i + 1] for i in range(5)):
            continue
        alt += 1
        if not (L[l3] < H[h3] and L[l1] < H[h1]):
            continue
        below += 1
        a, b = pts[0], pts[-1]
        if any(S[t] == 1 for t in range(a + 1, b + 1)):
            continue
        sess += 1
        spans.append(b - a)

    print('=' * 74)
    print(' 每加一個要求，還剩下多少（三個樞紐高為單位）')
    print('=' * 74)
    T = [('0  有三高三低可用', base),
         ('1  + 單調外擴 3+3（現行 Sec2）', mono),
         ('2  + 樞紐必須交替 H L H L H L', alt),
         ('3  + 低點必須在高點下方', below),
         ('4  + 整個型態同一時段', sess)]
    prev = None
    for lab, n in T:
        pct = '' if prev is None else '  剩 %5.1f%%' % (100.0 * n / prev if prev else 0)
        print('  %-32s %8s%s' % (lab, format(n, ','), pct))
        prev = n
    print()
    print('  相對第 1 步（現行規格）：交替 %.1f%% ／ +低於高 %.1f%% ／ +同時段 %.1f%%'
          % (100.0 * alt / mono, 100.0 * below / mono, 100.0 * sess / mono))
    if spans:
        spans.sort()
        print('  通過全部四項者跨度：中位數 %d 根，最短 %d，最長 %d'
              % (spans[len(spans) // 2], spans[0], spans[-1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
