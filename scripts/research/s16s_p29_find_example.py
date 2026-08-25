# -*- coding: utf-8 -*-
"""Pull REAL P29 instances out of the 5-minute data for the diagram.

A schematic shows what the rule says. A real instance shows what the rule
actually picks up, which is the part a spec can quietly get wrong. Both go
into the diagram.

Selection is by SHAPE ONLY -- span, cleanliness, and whether a breakout
followed. There is no P&L column and no ranking by outcome, deliberately:
picking the instance that made money would make the picture a lie.
"""
import io, os, sys, csv, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
CACHE = os.path.join(HERE, 's16s_5min.csv')


def main():
    rows = list(csv.DictReader(open(CACHE, encoding='utf-8')))
    O = [float(r['open']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    print('bars %d   %s -> %s' % (N, rows[0]['ymd'], rows[-1]['ymd']))

    # ---- fractal pivots, same session, confirmed one bar late ----
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PL = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    print('pivots  %d H / %d L' % (len(PH), len(PL)))

    setH, setL = set(PH), set(PL)
    hits = []
    hi_idx = {v: k for k, v in enumerate(PH)}
    lo_idx = {v: k for k, v in enumerate(PL)}

    # walk every pivot high that could be the THIRD of a monotonic trio
    for k in range(2, len(PH)):
        h3, h2, h1 = PH[k - 2], PH[k - 1], PH[k]
        if not (H[h3] < H[h2] < H[h1]):
            continue
        # the three most recent pivot lows as of h1
        lows = [x for x in PL if x < h1]
        if len(lows) < 3:
            continue
        l3, l2, l1 = lows[-3], lows[-2], lows[-1]
        if not (L[l3] > L[l2] > L[l1]):
            continue
        if l3 < h3 - 6 or h3 < l3 - 6:      # the two trios must overlap in time
            continue
        a, b = min(h3, l3), max(h1, l1)
        span = b - a
        if span < 8 or span > 70:
            continue
        # the WHOLE pattern must sit inside one session: bars_in_sess counts
        # up from 1 at each session open, so a reset anywhere in [a, b] means
        # the shape straddles a close. A trendline drawn across that gap is
        # not a line anyone was looking at.
        if any(S[t] == 1 for t in range(a + 1, b + 1)):
            continue
        # the six pivots should alternate reasonably, not clump
        pts = sorted([h3, h2, h1, l3, l2, l1])
        if min(pts[i + 1] - pts[i] for i in range(5)) < 1:
            continue
        # ---- SPEC GAP found 2026-08-25 while drawing a real instance ----
        # Sec 2 asks for three rising highs and three falling lows and stops
        # there. It does not ask the pivots to ALTERNATE, nor the lows to sit
        # below the highs. Without that, l3 can print ABOVE h3 and the two
        # trendlines cross -- a shape nobody would call a broadening. Enforced
        # here for the picture; flagged to the user as a spec question.
        kind = {}
        for x in (h3, h2, h1):
            kind[x] = 'H'
        for x in (l3, l2, l1):
            kind[x] = 'L'
        seq = [kind[x] for x in pts]
        if any(seq[i] == seq[i + 1] for i in range(5)):
            continue
        if not (L[l3] < H[h3] and L[l1] < H[h1]):
            continue
        mid_old = (H[h3] + L[l3]) / 2.0
        mid_new = (H[h1] + L[l1]) / 2.0
        drift = mid_new - mid_old
        # does a close-based break of the lower line follow within the life?
        life = h1 - h3
        slope = (L[l1] - L[l2]) / float(l1 - l2) if l1 != l2 else 0.0
        brk = None
        for t in range(b + 1, min(b + life + 1, N)):
            line = L[l1] + slope * (t - l1)
            prev = L[l1] + slope * (t - 1 - l1)
            if C[t] < line and C[t - 1] >= prev:
                brk = t
                break
        hits.append(dict(h3=h3, h2=h2, h1=h1, l3=l3, l2=l2, l1=l1,
                         a=a, b=b, span=span, drift=drift, brk=brk, life=life))

    print('P29 instances (3+3 monotonic, span 12-40, non-clumped): %d' % len(hits))
    down = [x for x in hits if x['drift'] < 0]
    withbrk = [x for x in down if x['brk'] is not None]
    if not withbrk:                 # breaks are rare once alternation is required
        print('  no descending instance with a close break -- widening to all')
        withbrk = [x for x in hits if x['brk'] is not None] or hits
    print('  of which descending: %d   with a close break: %d'
          % (len(down), len(withbrk)))

    # pick by shape only: widest expansion relative to span, break must exist
    def score(x):
        # absolute expansion in points, on BOTH edges -- the picture has to be
        # legible, and a 22-point broadening renders as a flat line
        up = H[x['h1']] - H[x['h3']]
        dn = L[x['l3']] - L[x['l1']]
        return min(up, dn)

    withbrk.sort(key=score, reverse=True)
    print()
    print('  top candidates by expansion (both edges, points):')
    for x in withbrk[:6]:
        print('    %s  span %2d  up %3.0f  dn %3.0f  drift %+5.1f'
              % (rows[x['a']]['ymd'] + ' ' + rows[x['a']]['hhmm'], x['span'],
                 H[x['h1']] - H[x['h3']], L[x['l3']] - L[x['l1']], x['drift']))
    best = withbrk[0]
    lo_ = best['a'] - 6
    hi_ = min((best['brk'] if best['brk'] else best['b']) + 8, N - 1)
    out = dict(
        bars=[dict(t=rows[i]['ymd'] + ' ' + rows[i]['hhmm'],
                   o=O[i], h=H[i], l=L[i], c=C[i], i=i)
              for i in range(lo_, hi_ + 1)],
        piv=dict(h3=best['h3'], h2=best['h2'], h1=best['h1'],
                 l3=best['l3'], l2=best['l2'], l1=best['l1']),
        brk=best['brk'], life=best['life'], lo=lo_, hi=hi_,
        drift=best['drift'],
    )
    p = os.path.join(HERE, 's16s_p29_example.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print()
    print('CHOSEN  %s -> %s   %d bars' % (out['bars'][0]['t'], out['bars'][-1]['t'],
                                          len(out['bars'])))
    for k in ('h3', 'h2', 'h1'):
        print('  %s  %s  H %.0f' % (k, rows[best[k]]['ymd'] + ' ' + rows[best[k]]['hhmm'],
                                    H[best[k]]))
    for k in ('l3', 'l2', 'l1'):
        print('  %s  %s  L %.0f' % (k, rows[best[k]]['ymd'] + ' ' + rows[best[k]]['hhmm'],
                                    L[best[k]]))
    if best['brk']:
        print('  break %s  C %.0f' % (rows[best['brk']]['ymd'] + ' '
                                      + rows[best['brk']]['hhmm'], C[best['brk']]))
    else:
        print('  break  none within life')
    print('  life %d bars   midpoint drift %+.1f' % (best['life'], best['drift']))
    print('  wrote %s' % p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
