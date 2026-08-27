# -*- coding: utf-8 -*-
"""The exit, not the formation.  Which way does each broadening variant break?

Willy, 2026-08-27: "aren't we researching SHORT setups?  You have only studied
the formation -- what about the break down and the break up?"

He is right, and the gap covers P29/P49/P50 too: the indicator has states
0/1/2/3 but "break" was never defined.  A formation is not tradeable; the exit
from it is.

Zero-parameter definition, every knob killed by derivation:

  formation completes  at the confirmation bar of the last pivot (p_last + 1)
  evaluation starts    the bar AFTER that -- strictly no look-ahead
  evaluation window    = the bar span the formation itself took (self-referential,
                         the same convention P29's validity period uses)
  lower line           through (PL1, its low) and (PL3, its low), extended
  upper line           through (PH1, its high) and (PH3, its high), extended
  break down           price goes under the lower line
  break up             price goes over the upper line
  buffer               NONE.  a point buffer or an N-bar confirmation would be
                       the first free parameter in this project.

Two rulings still open, so both are measured rather than assumed:
  (C) close-through vs wick-through
  (D) sloped trendline vs horizontal line at the extreme pivot

STILL THE PATTERN LAYER.  This counts which side breaks and how often.  It does
NOT measure return -- no P&L column, nothing about what happens after the break.
That is the signal layer, which Willy has deferred until the pattern layer is
finished.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
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
        frames.append((hs, ls, [x[0] for x in w]))

    rise = lambda a: a[0] < a[1] < a[2]
    fall = lambda a: a[0] > a[1] > a[2]
    flat = lambda a: a[0] == a[1] == a[2]
    hv = lambda hs: [H[i] for i in hs]
    lvv = lambda ls: [L[i] for i in ls]

    DEF = [
        ('P29 擴散三角', lambda hs, ls: rise(hv(hs)) and fall(lvv(ls))),
        ('P51 上升擴散楔形', lambda hs, ls: (rise(hv(hs)) and rise(lvv(ls))
                                       and (H[hs[2]] - H[hs[0]]) > (L[ls[2]] - L[ls[0]]))),
        ('P52 下降擴散楔形', lambda hs, ls: (fall(hv(hs)) and fall(lvv(ls))
                                       and abs(L[ls[2]] - L[ls[0]]) > abs(H[hs[2]] - H[hs[0]]))),
        ('P53 右角擴散（上）', lambda hs, ls: flat(hv(hs)) and fall(lvv(ls))),
        ('P54 右角擴散（下）', lambda hs, ls: rise(hv(hs)) and flat(lvv(ls))),
    ]

    def outcome(hs, ls, ix, use_close, sloped):
        a, b = ix[0], ix[-1]
        span = b - a
        start = b + 2                      # last pivot confirms at b+1; act at b+2
        stop = min(start + span, N - 1)
        if start > stop:
            return None
        if sloped:
            dl = (L[ls[2]] - L[ls[0]]) / float(ls[2] - ls[0])
            du = (H[hs[2]] - H[hs[0]]) / float(hs[2] - hs[0])
            lo_at = lambda t: L[ls[0]] + dl * (t - ls[0])
            up_at = lambda t: H[hs[0]] + du * (t - hs[0])
        else:
            flr, cei = min(L[i] for i in ls), max(H[i] for i in hs)
            lo_at = lambda t: flr
            up_at = lambda t: cei
        for t in range(start, stop + 1):
            dn = (C[t] < lo_at(t)) if use_close else (L[t] < lo_at(t))
            up = (C[t] > up_at(t)) if use_close else (H[t] > up_at(t))
            if dn and up:
                return 'both'              # same bar -- ambiguous, counted apart
            if dn:
                return 'down'
            if up:
                return 'up'
        return 'none'

    for use_close, sloped, title in [
            (True, True, 'C1 收盤價  x  D1 斜趨勢線   <-- 最嚴格'),
            (False, True, 'C2 最低價  x  D1 斜趨勢線'),
            (True, False, 'C1 收盤價  x  D2 水平線（取極值樞紐）'),
            (False, False, 'C2 最低價  x  D2 水平線   <-- 最寬鬆')]:
        print('=' * 82)
        print(' ' + title)
        print('=' * 82)
        print('  %-20s %8s %9s %9s %9s %9s' %
              ('型態', '母體', '跌破先', '突破先', '同根', '都沒破'))
        print('  ' + '-' * 70)
        for name, fn in DEF:
            hit = [f for f in frames if fn(f[0], f[1])]
            c = {'down': 0, 'up': 0, 'both': 0, 'none': 0}
            for hs, ls, ix in hit:
                o = outcome(hs, ls, ix, use_close, sloped)
                if o:
                    c[o] += 1
            tot = sum(c.values())
            if not tot:
                continue
            print('  %-20s %8s %6d %2.0f%% %6d %2.0f%% %6d %2.0f%% %6d %2.0f%%'
                  % (name, format(tot, ','),
                     c['down'], 100.0 * c['down'] / tot,
                     c['up'], 100.0 * c['up'] / tot,
                     c['both'], 100.0 * c['both'] / tot,
                     c['none'], 100.0 * c['none'] / tot))
        print()
    print('提醒：以上只有「往哪邊破」，沒有任何報酬。破完之後怎麼走是訊號層的問題。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
