# -*- coding: utf-8 -*-
"""Why the exact-equality patterns are disappearing, and the two errors it fixed.

Willy asked on 2026-08-28 why triple top and triple bottom cannot be used when
double top, ascending channel and measured move can.  Answering it properly
exposed a mistake of mine and then produced a clean law.

ERROR 1.  My group-A permutation test for P18 was written as

    (H[f[0]] - H[f[2]], H[f[2]] - H[f[4]])

which counts frames where H1-H2 equals H2-H3 -- an ARITHMETIC PROGRESSION,
true of 80/75/70 as much as of 80/80/80.  That is not a triple top.  It
returned 419 instances at 0.92x and I reported the pattern as indistinguishable
from chance.

Corrected to all-three-equal against the same block-local control:

    P18  43 observed against 0.50 expected   85.3x   p 0.0005   PASSES
    P23  33 observed against 0.49 expected   66.9x   p 0.0005   PASSES

So triple top does not fail the test.  It has the STRONGEST effect in group A,
which stands to reason -- hitting one exact level three times is far less
likely by chance than twice, so the excess over chance is proportionally
larger.

ERROR 2, in the framing rather than the code.  "Passes" was never "usable".
Every mirror passes too (P23 66.9x, double bottom 6.4x, descending channel
2.34x), so the tests measure price revisitation, not direction.

THE LAW.  The real reason triple top cannot be used is that it no longer
occurs: 12, 8, 5, 6, 6, 5, 1, 0 by year.  That looks like a phenomenon dying,
and it is not.  TXF1's tick is fixed at one point while the median swing inside
a double-top frame went from 9 points in 2019 to 90 in 2026.  If a swing spans
S ticks, two swings land on the same integer with probability about 1/S -- so
the hit rate should fall as 1/swing, and it does:

    year  hit rate (per mille)  median swing  product
    2019        82.35                 9          741
    2020        46.74                17          795
    2021        30.42                20          608
    2022        33.10                24          794
    2023        38.36                17          652
    2024        24.17                32          773
    2025        23.29                32          745
    2026         9.44                90          850

The product is flat across eight years while the rate falls nine-fold.  The
market has not changed; the arithmetic opportunity has shrunk.

And it predicts which patterns are safe: the monotone family requires no exact
match, so it should NOT decay.  P29 by year runs 8, 15, 18, 31, 24, 31, 42, 33
-- rising, not falling.  Confirmed.

Counts only.  No P&L column.
"""
import io, os, sys, csv, random, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
random.seed(20260828)
NP, BLK = 2000, 200


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

    def fr(k, first):
        o = []
        for s in range(len(piv) - k + 1):
            w = piv[s:s + k]
            if any(w[j][1] == w[j + 1][1] for j in range(k - 1)):
                continue
            if w[0][1] != first:
                continue
            o.append([x[0] for x in w])
        return o

    f5t, f5b, f3t, f3b = fr(5, 'H'), fr(5, 'L'), fr(3, 'H'), fr(3, 'L')

    def block_shuffle(cols):
        n = len(cols[0])
        out = []
        for c in cols:
            c = c[:]
            for s in range(0, n, BLK):
                seg = c[s:s + BLK]
                random.shuffle(seg)
                c[s:s + BLK] = seg
            out.append(c)
        return out

    def test(name, cols):
        n = len(cols[0])
        obs = sum(1 for t in zip(*cols) if len(set(t)) == 1)
        cnt = []
        for _ in range(NP):
            sh = [cols[0]] + block_shuffle(cols[1:])
            cnt.append(sum(1 for t in zip(*sh) if len(set(t)) == 1))
        exp = sum(cnt) / float(NP)
        p = (sum(1 for c in cnt if c >= obs) + 1) / float(NP + 1)
        print('  %-16s n=%-7s 觀測 %-6s 期望 %8.2f   倍率 %7.2fx   p=%.5f   %s'
              % (name, format(n, ','), format(obs, ','), exp,
                 obs / exp if exp else 0, p,
                 '通過' if p < 0.001 and exp and obs / exp > 1.5 else '與隨機無異'))

    print('=' * 78)
    print(' 1. 更正後的三重頂／三重底（三高全等，非等差）')
    print('=' * 78)
    test('P18 三重頂', [[H[f[0]] for f in f5t], [H[f[2]] for f in f5t],
                     [H[f[4]] for f in f5t]])
    test('P23 三重底', [[L[f[0]] for f in f5b], [L[f[2]] for f in f5b],
                     [L[f[4]] for f in f5b]])
    test('P68 雙頂（對照）', [[H[f[0]] for f in f3t], [H[f[2]] for f in f3t]])
    test('   雙底（對照）', [[L[f[0]] for f in f3b], [L[f[2]] for f in f3b]])

    print()
    print('=' * 78)
    print(' 2. ★ 命中率 x 擺幅 ~ 常數 —— 衰減是算術，不是市場')
    print('=' * 78)
    by = collections.defaultdict(list)
    for f in f3t:
        by[rows[f[0]]['ymd'][:4]].append(f)
    print('  %-6s %9s %8s %10s %11s %11s' %
          ('年', '框架數', '雙頂數', '命中率‰', '中位擺幅', '乘積'))
    print('  ' + '-' * 60)
    prod = []
    for y in sorted(by):
        g = by[y]
        hit = sum(1 for f in g if H[f[0]] == H[f[2]])
        sw = sorted(H[f[0]] - L[f[1]] for f in g)[len(g) // 2]
        rate = 1000.0 * hit / len(g)
        prod.append(rate * sw)
        print('  %-6s %9s %8d %10.2f %11.0f %11.0f'
              % (y, format(len(g), ','), hit, rate, sw, rate * sw))
    print('  乘積 %.0f ~ %.0f，平均 %.0f -- 命中率與擺幅成反比'
          % (min(prod), max(prod), sum(prod) / len(prod)))

    print()
    print('=' * 78)
    print(' 3. 對照：不需要「相等」的單調類沒有衰減')
    print('=' * 78)
    f6 = []
    for s in range(len(piv) - 5):
        w = piv[s:s + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        f6.append((hs, ls, w[0][0]))
    c29 = collections.Counter(
        rows[b]['ymd'][:4] for hs, ls, b in f6
        if H[hs[0]] < H[hs[1]] < H[hs[2]] and L[ls[0]] > L[ls[1]] > L[ls[2]])
    ys = sorted(c29)
    print('  P29 擴散（高遞增 ＋ 低遞減，無相等條件）逐年：')
    print('    %s' % '  '.join('%s=%d' % (y, c29[y]) for y in ys))
    print('  -> 上升趨勢，與精確相等類完全相反。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
