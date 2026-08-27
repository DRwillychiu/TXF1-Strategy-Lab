# -*- coding: utf-8 -*-
"""Pick one real instance of each of P51-P54 for the diagram.

Selection is by SHAPE only -- span, pivots not clumped, amplitude large enough
to render. No P&L column and no ranking by outcome, same rule the P29 example
was picked under: choosing the instance that made money would make the picture
a lie.
"""
import io, os, sys, csv, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
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

    frames = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        frames.append((w[0][1], hs, ls, [x[0] for x in w]))

    rise = lambda a: a[0] < a[1] < a[2]
    fall = lambda a: a[0] > a[1] > a[2]
    flat = lambda a: a[0] == a[1] == a[2]
    hv = lambda hs: [H[i] for i in hs]
    lv = lambda ls: [L[i] for i in ls]

    DEF = {
        'P51': lambda hs, ls: (rise(hv(hs)) and rise(lv(ls))
                               and (H[hs[2]] - H[hs[0]]) > (L[ls[2]] - L[ls[0]])),
        'P52': lambda hs, ls: (fall(hv(hs)) and fall(lv(ls))
                               and abs(L[ls[2]] - L[ls[0]]) > abs(H[hs[2]] - H[hs[0]])),
        'P53': lambda hs, ls: flat(hv(hs)) and fall(lv(ls)),
        'P54': lambda hs, ls: rise(hv(hs)) and flat(lv(ls)),
    }

    out = {}
    for name, fn in DEF.items():
        hit = [f for f in frames if fn(f[1], f[2])]
        cand = []
        for f in hit:
            ix = f[3]
            a, b = ix[0], ix[-1]
            span = b - a
            if span < 8 or span > 40:
                continue
            if min(ix[j + 1] - ix[j] for j in range(5)) < 1:
                continue
            amp = max(H[i] for i in f[1]) - min(L[i] for i in f[2])
            cand.append((amp, f))
        if not cand:                       # P53 / P54 are rare; relax the span
            for f in hit:
                ix = f[3]
                amp = max(H[i] for i in f[1]) - min(L[i] for i in f[2])
                cand.append((amp, f))
        # take the MEDIAN by amplitude, not the maximum. Sorting descending
        # picked a 1,819-point P51 spanning the night-to-day handover -- real,
        # but the most extreme instance in eight years is the wrong thing to
        # put in front of someone forming a judgement about the typical case.
        cand.sort(key=lambda t: t[0])
        amp, f = cand[len(cand) // 2]
        ix = f[3]
        lo = max(ix[0] - 5, 0)
        hi = min(ix[-1] + 7, N - 1)
        out[name] = dict(
            n=len(hit),
            kind=f[0],
            bars=[dict(t=rows[i]['ymd'] + ' ' + rows[i]['hhmm'],
                       o=O[i], h=H[i], l=L[i], c=C[i]) for i in range(lo, hi + 1)],
            piv=[[i - lo, ('H' if i in f[1] else 'L')] for i in ix],
            lo=lo, amp=amp, span=ix[-1] - ix[0],
        )
        print('%s  母體 %5d   選中 %s ~ %s   跨度 %d 根   振幅 %.0f 點'
              % (name, len(hit), rows[ix[0]]['ymd'] + ' ' + rows[ix[0]]['hhmm'],
                 rows[ix[-1]]['ymd'] + ' ' + rows[ix[-1]]['hhmm'],
                 ix[-1] - ix[0], amp))

    p = os.path.join(HERE, 's16s_p51_p54_example.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n  wrote %s' % p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
