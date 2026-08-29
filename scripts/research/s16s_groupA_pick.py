# -*- coding: utf-8 -*-
"""Pick one real instance of each group-A pattern for the page.

Willy, 2026-08-28: "但我認為在 HTML 也是需要個別給真實案例."

Selection by SHAPE only -- span in a readable range, pivots not clumped,
MEDIAN amplitude.  No P&L column and no ranking by outcome, the same rule
every earlier page was picked under.  Taking the largest instance would make
the picture flatter the pattern; P51's diagram made that mistake once.
"""
import io, os, sys, csv, json

HERE = os.path.join('scripts', 'research')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
O = [float(r['open']) for r in rows]
H = [float(r['high']) for r in rows]
L = [float(r['low']) for r in rows]
C = [float(r['close']) for r in rows]
S = [int(r['bars_in_sess']) for r in rows]
N = len(rows)
PH = [i for i in range(1, N - 1)
      if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
PL = [i for i in range(1, N - 1)
      if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PL])


def fr(k, first=None):
    o = []
    for s in range(len(piv) - k + 1):
        w = piv[s:s + k]
        if any(w[j][1] == w[j + 1][1] for j in range(k - 1)):
            continue
        if first and w[0][1] != first:
            continue
        o.append(w)
    return o


f3t, f5t, f5b = fr(3, 'H'), fr(5, 'H'), fr(5, 'L')
f6 = []
for s in range(len(piv) - 5):
    w = piv[s:s + 6]
    if any(w[j][1] == w[j + 1][1] for j in range(5)):
        continue
    hs = [x[0] for x in w if x[1] == 'H']
    ls = [x[0] for x in w if x[1] == 'L']
    if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
        continue
    f6.append(w)

inb = lambda a, b, t: min(a, b) <= t <= max(a, b)
ri = lambda a: a[0] < a[1] < a[2]


def hi(w):
    return [x[0] for x in w if x[1] == 'H']


def lo(w):
    return [x[0] for x in w if x[1] == 'L']


SEL = {
    'P15': (f5t, lambda w: H[w[0][0]] < H[w[2][0]] > H[w[4][0]]),
    'P16': (f5b, lambda w: L[w[0][0]] > L[w[2][0]] < L[w[4][0]]),
    'P18': (f5t, lambda w: inb(H[w[0][0]], H[w[2][0]], H[w[4][0]])),
    'P23': (f5b, lambda w: inb(L[w[0][0]], L[w[2][0]], L[w[4][0]])),
    'P68': (f3t, lambda w: H[w[0][0]] == H[w[2][0]]),
    'P57': (f5t, lambda w: H[w[2][0]] < H[w[0][0]] and L[w[3][0]] < L[w[1][0]]
            and (H[w[0][0]] - L[w[1][0]]) == (H[w[2][0]] - L[w[3][0]])),
    'P21': (f6, lambda w: ri([H[i] for i in hi(w)]) and ri([L[i] for i in lo(w)])
            and inb(H[hi(w)[0]] - L[lo(w)[0]], H[hi(w)[1]] - L[lo(w)[1]],
                    H[hi(w)[2]] - L[lo(w)[2]])),
}
SPAN = {'P68': (3, 14), 'P18': (8, 26), 'P23': (8, 26), 'P57': (8, 26),
        'P21': (10, 30), 'P15': (8, 26), 'P16': (8, 26)}

out = {}
for k, (pool, fn) in SEL.items():
    lo_s, hi_s = SPAN[k]
    cand = []
    for w in pool:
        if not fn(w):
            continue
        ix = [x[0] for x in w]
        sp = ix[-1] - ix[0]
        if not (lo_s <= sp <= hi_s):
            continue
        if min(ix[j + 1] - ix[j] for j in range(len(ix) - 1)) < 1:
            continue
        amp = max(H[i] for i in ix) - min(L[i] for i in ix)
        cand.append((amp, w))
    cand.sort(key=lambda t: t[0])
    amp, w = cand[len(cand) // 2]
    ix = [x[0] for x in w]
    a = max(ix[0] - 4, 0)
    b = min(ix[-1] + 5, N - 1)
    out[k] = dict(
        n=len(cand), amp=amp, span=ix[-1] - ix[0],
        bars=[dict(t=rows[i]['ymd'] + ' ' + rows[i]['hhmm'],
                   o=O[i], h=H[i], l=L[i], c=C[i]) for i in range(a, b + 1)],
        piv=[[i - a, kk] for i, kk in w],
        d0=rows[ix[0]]['ymd'], t0=rows[ix[0]]['hhmm'], t1=rows[ix[-1]]['hhmm'])
    print('  %-5s 候選 %5d   選中 %s %s ~ %s   跨度 %2d 根   振幅 %.0f 點'
          % (k, len(cand), out[k]['d0'], out[k]['t0'], out[k]['t1'],
             out[k]['span'], amp))

p = os.path.join(HERE, 's16s_groupA_example.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('\n  wrote %s' % p)
