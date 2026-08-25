# -*- coding: utf-8 -*-
"""P29 broadening formation -- census on the FULL bar population.

Two things this script exists to settle, both raised by Willy on 2026-08-25:

  1. Pivots on bar extremes (H/L) or on the close?  Measured both ways here
     rather than assumed, because the answer changes what a "swing" even is.

  2. P29 is not one shape.  A megaphone whose centre drifts up is a different
     market state from one whose centre drifts down.  Split three ways.

Counts only.  No P&L column -- the shape is catalogued on how often it occurs
and on whether it needs a knob, never on what it earned.  Same discipline as
the candlestick census.

Population is every bar, NOT the 187 signal bars and NOT the 7,703 death
crosses.  The .pla evaluates structures on every bar (v_KB_SupAge counts from
the bar the structure forms, on any bar) and lets the death cross arrive
later, so conditioning the census on death crosses measures an architecture
the strategy does not have.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
CACHE = os.path.join(HERE, 's16s_5min.csv')


def pivots(hi, lo, sess, N):
    """Fractal pivots.  i-1, i, i+1 must sit in the same session: the test is
    adjacency-dependent, so a 75-minute or 3h45m gap breaks its meaning the
    same way it breaks an engulfing (fixed 2026-08-21)."""
    ph, pl = [], []
    for i in range(1, N - 1):
        if sess[i] < 2 or sess[i + 1] < 2:      # i-1..i+1 same session
            continue
        if hi[i] > hi[i - 1] and hi[i] > hi[i + 1]:
            ph.append(i)
        if lo[i] < lo[i - 1] and lo[i] < lo[i + 1]:
            pl.append(i)
    return ph, pl


def census(label, hi, lo, sess, N, require_interleave):
    ph, pl = pivots(hi, lo, sess, N)

    # last two pivot highs / lows as of each bar; a pivot at i is only KNOWN
    # at i+1, so it enters the record one bar later -- no look-ahead.
    lastH = [None] * N
    lastL = [None] * N
    hs, ls = [], []
    ih = il = 0
    for i in range(N):
        while ih < len(ph) and ph[ih] + 1 <= i:
            hs.append(ph[ih]); ih += 1
        while il < len(pl) and pl[il] + 1 <= i:
            ls.append(pl[il]); il += 1
        lastH[i] = tuple(hs[-2:]) if len(hs) >= 2 else None
        lastL[i] = tuple(ls[-2:]) if len(ls) >= 2 else None

    up = dn = flat = 0
    total = 0
    for i in range(N):
        a, b = lastH[i], lastL[i]
        if not a or not b:
            continue
        h2, h1 = hi[a[0]], hi[a[1]]        # older, newer
        l2, l1 = lo[b[0]], lo[b[1]]
        if not (h1 > h2 and l1 < l2):       # P29: highs out, lows out
            continue
        if require_interleave:
            # the four pivots must alternate H L H L or L H L H in time
            seq = sorted([(a[0], 'H'), (a[1], 'H'), (b[0], 'L'), (b[1], 'L')])
            tags = ''.join(t for _, t in seq)
            if tags not in ('HLHL', 'LHLH'):
                continue
        total += 1
        m2 = (h2 + l2) / 2.0
        m1 = (h1 + l1) / 2.0
        if m1 > m2:
            up += 1
        elif m1 < m2:
            dn += 1
        else:
            flat += 1

    print('  %-34s pivots %6d H / %6d L' % (label, len(ph), len(pl)))
    print('      P29 bars %7d  (%.3f%% of %d)' % (total, 100.0 * total / N, N))
    if total:
        print('      up %6d (%5.2f%%)   down %6d (%5.2f%%)   flat %5d (%5.2f%%)'
              % (up, 100.0 * up / total, dn, 100.0 * dn / total,
                 flat, 100.0 * flat / total))
    print('')
    return total, up, dn, flat


def main():
    rows = list(csv.DictReader(open(CACHE, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    print('bars %d   %s -> %s' % (N, rows[0]['ymd'], rows[-1]['ymd']))
    print('')

    print('PIVOT BASIS = BAR EXTREMES (high / low)')
    census('no interleave requirement', H, L, S, N, False)
    census('pivots must alternate', H, L, S, N, True)

    print('PIVOT BASIS = CLOSE (close used for both)')
    census('no interleave requirement', C, C, S, N, False)
    census('pivots must alternate', C, C, S, N, True)


if __name__ == '__main__':
    main()
