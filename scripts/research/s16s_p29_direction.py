# -*- coding: utf-8 -*-
"""Three candidate direction measures for P29, judged by ORDERING BALANCE.

Ruling 2026-08-25: keep the three-way split (a broadening genuinely comes in
up / down / horizontal forms), but the current measure has to go -- midpoint
drift reports which pivot type ENDS the pattern, not where the market went.

The test is simple and does not need returns: a measure that describes the
market must give the SAME distribution whether the pattern happens to start on
a high or on a low. The old one gives 63.7% down vs 32.1% down -- a 31.6
percentage-point gap that is pure bookkeeping.

  M1  midpoint drift                       current, kept as the control
  M2  mean of the two trendline slopes     per-bar, so time-normalised
  M3  midpoint compared over the SHARED    both edges interpolated onto the
      time window                          same two timestamps
  M4  three ADJACENT pivot couples         each couple holds one high and one
                                          low, so neither edge is sampled late

Counts only. No P&L column.
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
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])

    hits = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        idx = [x[0] for x in w]
        if any(S[t] == 1 for t in range(idx[0] + 1, idx[-1] + 1)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (H[hs[0]] < H[hs[1]] < H[hs[2]]):
            continue
        if not (L[ls[0]] > L[ls[1]] > L[ls[2]]):
            continue
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        hits.append((w[0][1], hs, ls, idx, [x[1] for x in w]))
    print('乾淨 P29 %d 個' % len(hits))

    def m1(hs, ls, ix=None, tp=None):
        """midpoint drift -- the current measure"""
        return ((H[hs[2]] + L[ls[2]]) - (H[hs[0]] + L[ls[0]])) / 2.0

    def m2(hs, ls, ix=None, tp=None):
        """mean of the two trendline slopes, per bar"""
        su = (H[hs[2]] - H[hs[0]]) / float(hs[2] - hs[0])
        sl = (L[ls[2]] - L[ls[0]]) / float(ls[2] - ls[0])
        return (su + sl) / 2.0

    def m3(hs, ls, ix=None, tp=None):
        """midpoint over the SHARED window: interpolate both edges onto the
        same two timestamps, so neither edge gets extra time to travel."""
        t0 = max(hs[0], ls[0])
        t1 = min(hs[2], ls[2])
        if t1 <= t0:
            return 0.0
        su = (H[hs[2]] - H[hs[0]]) / float(hs[2] - hs[0])
        sl = (L[ls[2]] - L[ls[0]]) / float(ls[2] - ls[0])
        up0 = H[hs[0]] + su * (t0 - hs[0])
        up1 = H[hs[0]] + su * (t1 - hs[0])
        lo0 = L[ls[0]] + sl * (t0 - ls[0])
        lo1 = L[ls[0]] + sl * (t1 - ls[0])
        return ((up1 + lo1) - (up0 + lo0)) / 2.0

    def m4(hs, ls, ix, tp):
        """pair the six pivots into three ADJACENT couples. Whatever the
        ordering, each couple holds exactly one high and one low, so neither
        edge is sampled over a later window than the other. Direction is the
        sign of (third couple midpoint - first couple midpoint)."""
        v = []
        for j in (0, 2, 4):
            a, b = ix[j], ix[j + 1]
            pa = H[a] if tp[j] == 'H' else L[a]
            pb = H[b] if tp[j + 1] == 'H' else L[b]
            v.append((pa + pb) / 2.0)
        return v[2] - v[0]

    print()
    print('=' * 84)
    print(' 判準：描述市場的量法，兩種排列的分布必須一致')
    print('=' * 84)
    print('%-28s %-10s %7s %7s %7s %9s' % ('量法', '排列', '上升', '下降', '水平', '上升差距'))
    print('-' * 84)
    best = None
    for name, fn in (('M1 中點漂移（現行）', m1),
                     ('M2 兩條趨勢線斜率平均', m2),
                     ('M3 共同時間窗中點', m3),
                     ('M4 相鄰配對中點（對稱）', m4)):
        res = {}
        for kind, lab in (('H', '先出現高'), ('L', '先出現低')):
            sub = [(hs, ls, ix, tp) for k, hs, ls, ix, tp in hits if k == kind]
            n = len(sub)
            v = [fn(hs, ls, ix, tp) for hs, ls, ix, tp in sub]
            up = sum(1 for x in v if x > 1e-9)
            dn = sum(1 for x in v if x < -1e-9)
            res[kind] = (n, 100.0 * up / n, 100.0 * dn / n, 100.0 * (n - up - dn) / n)
        gap = abs(res['H'][1] - res['L'][1])
        for kind, lab in (('H', '先出現高'), ('L', '先出現低')):
            n, u, d, f = res[kind]
            print('%-28s %-10s %6.1f%% %6.1f%% %6.1f%%   %s'
                  % (name if kind == 'H' else '', lab, u, d, f,
                     ('%.1f pp' % gap) if kind == 'H' else ''))
        allv = [fn(hs, ls, ix, tp) for _, hs, ls, ix, tp in hits]
        au = sum(1 for x in allv if x > 1e-9)
        ad = sum(1 for x in allv if x < -1e-9)
        print('%-28s %-10s %6.1f%% %6.1f%% %6.1f%%'
              % ('', '合計', 100.0 * au / len(allv), 100.0 * ad / len(allv),
                 100.0 * (len(allv) - au - ad) / len(allv)))
        print('-' * 84)
        if best is None or gap < best[1]:
            best = (name, gap)
    print()
    print('  ★ 排列差距最小者：%s（%.1f pp）' % best)
    print('    差距愈小 = 這個量法描述的是市場，不是「哪種樞紐收尾」。')

    # how much do the three measures actually disagree with each other?
    print()
    print('=' * 84)
    print(' 三個量法彼此的一致率')
    print('=' * 84)
    sg = lambda x: (1 if x > 1e-9 else (-1 if x < -1e-9 else 0))
    pairs = [('M1 vs M2', m1, m2), ('M1 vs M4', m1, m4), ('M2 vs M4', m2, m4)]
    for lab, fa, fb in pairs:
        same = sum(1 for _, hs, ls, ix, tp in hits
                   if sg(fa(hs, ls, ix, tp)) == sg(fb(hs, ls, ix, tp)))
        print('  %-10s %5.1f%%  (%d / %d 同號)'
              % (lab, 100.0 * same / len(hits), same, len(hits)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
