# -*- coding: utf-8 -*-
"""Is the pivot window too fine for shapes that are supposed to be large?

Willy, 2026-08-28: "圖形型態，本質其實可以是非常多根 K 棒組合而成。
這件事情你有意識到?"

Partly, and not where it mattered.  The window-1 fractal was settled during
P29 and I carried it into every pattern since without re-asking whether a
shape that is supposed to be LARGE can be built from it.  It cannot:

    35.9% of all bars are pivots -- one every 2.8 bars
    adjacent pivots sit a median of 2 bars apart
    the "double top" spans a median of THREE bars

Three bars is a high, a bar, and a high.  That is not a double top.

WHAT A COARSER WINDOW WOULD GIVE

    w   pivots   one per   P29 n   P29 span   double top n   span
    1  151,147     2.8      203       12          1,365        3
    2   88,079     4.8      125       19            514        6
    3   61,617     6.8      101       30            275        8
    5   37,900    11.1       69       44             94       11
    8   23,322    18.1       41       70             35       17

WHAT CAPS IT

MaxBarsBack is 100, and a pattern needs its span twice over -- formation plus
its own validity window -- plus w bars of confirmation delay:

    w=1   0% exceed 99      w=3   4% exceed
    w=2   1% exceed         w=5  39%      w=8  93%

So window 3 is the practical ceiling: a 30-bar median span, half a day
session, with a 3-bar (15 minute) confirmation delay.

WHY THE EXISTING WORK IS STILL GOOD

Changing the window voids every population measured so far, so the decision
turns on whether the CONCLUSIONS are scale-invariant.  They are:

                       w=1        w=2        w=3
    P29 diverging     0.16x      0.18x      0.20x
    diamond           0.80x      0.78x      0.81x
    hourglass mirror  0.80x      0.79x      0.77x
    H&S peak:trough  0.958:1    0.981:1    0.944:1

Every verdict holds at every scale.  P29 stays strongly suppressed, the
diamond stays indistinguishable from its mirror, head and shoulders stays at
parity.  Only the counts and the spans move.

So nothing has to be re-derived.  What is at stake is whether the DETECTOR
should run coarser, so that the shapes drawn on the chart are what they claim
to be.  That is Willy's ruling, and the cheapest way to make it is to expose
the window as an input and look at both.

Counts only.  No P&L column.
"""
import io, os, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)

    def pivots(w):
        PH, PL = [], []
        for i in range(w, N - w):
            if S[i] < w + 1 or any(S[t] == 1 for t in range(i - w + 1, i + w + 1)):
                continue
            if all(H[i] > H[i - k] and H[i] > H[i + k] for k in range(1, w + 1)):
                PH.append(i)
            if all(L[i] < L[i - k] and L[i] < L[i + k] for k in range(1, w + 1)):
                PL.append(i)
        return sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])

    def shp(a):
        if a[0] < a[1] < a[2]:
            return 'rise'
        if a[0] > a[1] > a[2]:
            return 'fall'
        if a[0] < a[1] > a[2]:
            return 'peak'
        if a[0] > a[1] < a[2]:
            return 'trough'
        return 'other'

    print('=' * 84)
    print(' 1. 尺度、母體、跨度')
    print('=' * 84)
    print('  %-5s %10s %9s %8s %9s %11s %8s %11s'
          % ('視窗', '樞紐總數', '每N根', '中位間隔', 'P29母體', 'P29跨度中位',
             '雙頂母體', '雙頂跨度中位'))
    print('  ' + '-' * 78)
    keep = {}
    for w in (1, 2, 3, 5, 8):
        piv = pivots(w)
        keep[w] = piv
        gp = sorted(piv[i + 1][0] - piv[i][0] for i in range(len(piv) - 1))
        f6, dt = [], []
        for s in range(len(piv) - 5):
            x = piv[s:s + 6]
            if any(x[j][1] == x[j + 1][1] for j in range(5)):
                continue
            hs = [t[0] for t in x if t[1] == 'H']
            ls = [t[0] for t in x if t[1] == 'L']
            if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
                continue
            if H[hs[0]] < H[hs[1]] < H[hs[2]] and L[ls[0]] > L[ls[1]] > L[ls[2]]:
                f6.append(x[-1][0] - x[0][0])
        for s in range(len(piv) - 2):
            x = piv[s:s + 3]
            if x[0][1] == 'H' and x[1][1] == 'L' and x[2][1] == 'H' \
               and H[x[0][0]] == H[x[2][0]]:
                dt.append(x[2][0] - x[0][0])
        f6.sort()
        dt.sort()
        print('  %-5d %10s %9.1f %8d %9s %11d %8s %11d'
              % (w, format(len(piv), ','), N / float(len(piv)), gp[len(gp) // 2],
                 format(len(f6), ','), f6[len(f6) // 2],
                 format(len(dt), ','), dt[len(dt) // 2] if dt else 0))
    print()
    print('  日盤 08:45-13:45 ＝ 60 根 5 分 K。視窗 1 的雙頂中位 3 根 ——')
    print('  一根高、中間一根、再一根高。那不是雙頂。')

    print()
    print('=' * 84)
    print(' 2. ★ 結論是否隨尺度改變')
    print('=' * 84)
    print('  %-18s %10s %10s %10s' % ('判定', '視窗 1', '視窗 2', '視窗 3'))
    print('  ' + '-' * 52)
    res = collections.defaultdict(dict)
    for w in (1, 2, 3):
        piv = keep[w]
        fr = []
        for s in range(len(piv) - 5):
            x = piv[s:s + 6]
            if any(x[j][1] == x[j + 1][1] for j in range(5)):
                continue
            hs = [t[0] for t in x if t[1] == 'H']
            ls = [t[0] for t in x if t[1] == 'L']
            if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
                continue
            fr.append(([H[i] for i in hs], [L[i] for i in ls]))
        T = len(fr)
        hc, lc, jc = collections.Counter(), collections.Counter(), collections.Counter()
        for hv, lv in fr:
            a, b = shp(hv), shp(lv)
            hc[a] += 1
            lc[b] += 1
            jc[(a, b)] += 1

        def rat(a, b):
            e = hc[a] * lc[b] / float(T)
            return jc[(a, b)] / e if e else 0

        f5 = []
        for s in range(len(piv) - 4):
            x = piv[s:s + 5]
            if any(x[j][1] == x[j + 1][1] for j in range(4)):
                continue
            if x[0][1] == 'H':
                f5.append([t[0] for t in x])
        pk = sum(1 for f in f5 if H[f[0]] < H[f[2]] > H[f[4]])
        tr = sum(1 for f in f5 if H[f[0]] > H[f[2]] < H[f[4]])
        res['P29 擴散'][w] = '%.2fx' % rat('rise', 'fall')
        res['鑽石'][w] = '%.2fx' % rat('peak', 'trough')
        res['沙漏（鏡像）'][w] = '%.2fx' % rat('trough', 'peak')
        res['頭肩 峰:谷'][w] = '%.3f : 1' % (pk / float(tr))
        res['六樞紐框架'][w] = format(T, ',')
    for k in ('六樞紐框架', 'P29 擴散', '鑽石', '沙漏（鏡像）', '頭肩 峰:谷'):
        print('  %-18s %10s %10s %10s' % (k, res[k][1], res[k][2], res[k][3]))
    print()
    print('  三個判定在三種尺度下一致 -> 結論與尺度無關，至今的分析不必重做。')
    print('  變的只有母體數字與跨度。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
