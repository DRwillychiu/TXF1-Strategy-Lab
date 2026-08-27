# -*- coding: utf-8 -*-
"""P29 breaks 37% down / 43% up -- a coin.  Does any sub-classification split it?

If P29 is to be usable by a short-only strategy, the tilt has to come from a
sub-class, because the formation alone carries almost no directional
information.  The candidates already exist and cost nothing new: arrangement
(which pivot type opens the formation), M2 (the adopted direction measure), the
six-cell cross of the two, and S1 (the 0-6 coarse-scale robustness score).

With n=203 split six ways, cells land near 30 and a binomial swing of +-9pp is
ordinary.  So every split here is run against a PERMUTATION NULL: shuffle the
outcomes among the 203 patterns 20,000 times and see how big a chi-square the
same table produces by chance.  Discipline 13 of the checklist -- without a
null there is no way to tell a finding from bookkeeping, and the direction work
already burned this project once (18-32pp gaps that looked huge until the null
came back at 2-9pp).

Break definition: horizontal line at the formation's extreme pivot, close
through, window = the formation's own span, starting the bar after the last
pivot confirms.  That is the only definition that means the same thing across
variants -- the sloped-line version fires on P51 while price is still 43 points
above the formation's floor.

Counts and break direction only.  No P&L column.
"""
import io, os, sys, csv, json, random, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(20260827)
NPERM = 20000


def chi2(tab):
    """Pearson chi-square of a rows x cols contingency table."""
    rm = [sum(r) for r in tab]
    cm = [sum(tab[i][j] for i in range(len(tab))) for j in range(len(tab[0]))]
    n = float(sum(rm))
    s = 0.0
    for i in range(len(tab)):
        for j in range(len(tab[0])):
            e = rm[i] * cm[j] / n
            if e > 0:
                s += (tab[i][j] - e) ** 2 / e
    return s


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    N = len(rows)
    pats = json.load(open(os.path.join(HERE, 's16s_p29_clean.json'), encoding='utf-8'))
    print('P29 母體 %d 個' % len(pats))

    recs = []
    for p in pats:
        hs, ls = p['hs'], p['ls']
        b = max(hs + ls)
        a = min(hs + ls)
        span = b - a
        st, sp = b + 2, min(b + 2 + span, N - 1)
        if st > sp:
            continue
        flr, cei = min(L[i] for i in ls), max(H[i] for i in hs)
        o = 'none'
        for t in range(st, sp + 1):
            if C[t] < flr:
                o = 'down'
                break
            if C[t] > cei:
                o = 'up'
                break
        recs.append((p, o))

    n = len(recs)
    base = collections.Counter(o for _, o in recs)
    print('整體  跌破 %d (%.0f%%)   突破 %d (%.0f%%)   沒破 %d (%.0f%%)\n'
          % (base['down'], 100.0 * base['down'] / n, base['up'], 100.0 * base['up'] / n,
             base['none'], 100.0 * base['none'] / n))

    def m2dir(v):
        if v > 0:
            return '上'
        if v < 0:
            return '下'
        return '平'

    SPLITS = [
        ('排列（先高／先低）', lambda p: '先高' if p['k'] == 'H_first' else '先低'),
        ('M2 方向', lambda p: m2dir(p['m2'])),
        ('六格（排列 x M2）', lambda p: ('先高' if p['k'] == 'H_first' else '先低') + m2dir(p['m2'])),
        ('S1 粗尺度分數', lambda p: 'S1=%d' % p['s1']),
    ]

    OUT = ['down', 'up', 'none']
    for title, keyfn in SPLITS:
        cells = sorted({keyfn(p) for p, _ in recs})
        idx = {c: i for i, c in enumerate(cells)}
        tab = [[0] * 3 for _ in cells]
        for p, o in recs:
            tab[idx[keyfn(p)]][OUT.index(o)] += 1
        obs = chi2(tab)

        labels = [o for _, o in recs]
        keys = [idx[keyfn(p)] for p, _ in recs]
        worse = 0
        for _ in range(NPERM):
            random.shuffle(labels)
            t = [[0] * 3 for _ in cells]
            for k, o in zip(keys, labels):
                t[k][OUT.index(o)] += 1
            if chi2(t) >= obs:
                worse += 1
        pval = (worse + 1) / float(NPERM + 1)

        print('=' * 74)
        print(' %s' % title)
        print('=' * 74)
        print('  %-10s %7s %14s %14s %14s' % ('分類', '個數', '跌破', '突破', '沒破'))
        for c in cells:
            r = tab[idx[c]]
            tot = sum(r)
            print('  %-10s %7d %8d %4.0f%% %8d %4.0f%% %8d %4.0f%%'
                  % (c, tot, r[0], 100.0 * r[0] / tot, r[1], 100.0 * r[1] / tot,
                     r[2], 100.0 * r[2] / tot))
        verdict = '★ 通過虛無對照' if pval < 0.05 else '與隨機打散無法區分'
        print('  chi2 = %.2f    排列檢定 p = %.4f    %s' % (obs, pval, verdict))
        print()

    print('提醒：以上只有破位方向，沒有報酬。p 值未做多重比較校正 ——')
    print('本輪 4 次檢定，Bonferroni 門檻應為 0.05/4 = 0.0125。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
