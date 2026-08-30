# -*- coding: utf-8 -*-
"""Group D: measure the three claims that can be measured.

The four patterns were pencilled in as "not worth the effort" on reasoning
alone.  Reasoning is how a pattern gets ONTO the list, not how it comes off
it, so three of the four claims are tested here against the same 5-minute
data every other pattern was measured on.

  P70  Fibonacci retracement
       The claim is that 0.382 / 0.5 / 0.618 are FOREIGN constants -- numbers
       brought to the market rather than found in it.  That is falsifiable:
       if retracements really cluster there, the bins at those ratios stand
       above their neighbours.  Measured as a local-peak test, because the
       retracement distribution is smooth and unimodal on its own.

  P07  Bollinger BandWidth squeeze
       The claim is that the squeeze is a function of its knobs.  Two things
       are checked: how much the count moves, and -- the part that matters --
       whether the SAME BARS are picked.  A pattern that names a different
       set of bars when a knob moves is not one object seen at two settings.

  P69  Elliott five-wave
       The claim is that the count is arguable.  Tested as scale dependence:
       count impulses at pivot window 1, 2 and 3 and see whether they land in
       the same places.

  P71  Gann angles cannot be measured here and are not pretended to be.  A
       1x1 line means one price unit per time unit, so it has no meaning
       until price units per bar are fixed.  The decay law already measured
       that: median swing went from 9 points in 2019 to 90 in 2026, so any
       fixed points-per-bar angle is right for at most one year of the eight.

Run:  python scripts/research/s16s_groupD_scan.py
"""
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.join('scripts', 'research')
CSV = os.path.join(HERE, 's16s_5min.csv')

FIB = [0.236, 0.382, 0.5, 0.618, 0.786]
NB = 50                      # 0.02-wide bins over [0, 1]


def load():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    return ([float(r['high']) for r in rows],
            [float(r['low']) for r in rows],
            [float(r['close']) for r in rows],
            [int(r['bars_in_sess']) for r in rows])


def pivots(H, L, S, w):
    """Alternating pivot chain at window w.  Detection never crosses a
    session, which is why bars_in_sess gates it."""
    out = []
    n = len(H)
    for i in range(w, n - w):
        if S[i] < w + 1 or S[i + w] < S[i]:
            continue
        hi = lo = True
        for d in range(1, w + 1):
            if H[i] <= H[i - d] or H[i] <= H[i + d]:
                hi = False
            if L[i] >= L[i - d] or L[i] >= L[i + d]:
                lo = False
        if hi:
            if out and out[-1][2] == 1:
                out[-1] = (i, H[i], 1) if H[i] > out[-1][1] else out[-1]
            else:
                out.append((i, H[i], 1))
        elif lo:
            if out and out[-1][2] == 2:
                out[-1] = (i, L[i], 2) if L[i] < out[-1][1] else out[-1]
            else:
                out.append((i, L[i], 2))
    return out


def p70(pv):
    """Do retracements pile up on the Fibonacci ratios?"""
    hist = [0] * NB
    tot = 0
    for a in range(len(pv) - 2):
        (_, p0, t0), (_, p1, _), (_, p2, _) = pv[a], pv[a + 1], pv[a + 2]
        leg = abs(p1 - p0)
        if leg <= 0:
            continue
        r = abs(p1 - p2) / leg
        if not 0.0 < r < 1.0:
            continue
        hist[min(NB - 1, int(r * NB))] += 1
        tot += 1

    print('  P70  費波那契回撤')
    print('       回撤樣本 %s 個（視窗 1，僅取 0 < 比例 < 1）' % format(tot, ','))
    print('       %-8s %-9s %-11s %s' % ('比例', '該格', '鄰格平均', '倍率'))
    worst = 0.0
    for f in FIB:
        b = min(NB - 1, int(f * NB))
        near = [hist[j] for j in (b - 3, b - 2, b + 2, b + 3)
                if 0 <= j < NB]
        exp = sum(near) / len(near)
        rat = hist[b] / exp if exp else 0.0
        worst = max(worst, rat)
        print('       %-8s %-9s %-11.0f %.2fx' % (f, format(hist[b], ','),
                                                  exp, rat))
    print('       最高倍率 %.2fx  ->  %s' % (
        worst,
        '有聚集，本判定不成立' if worst >= 1.25 else
        '沒有任何一格高過鄰居，比例是平滑分布'))
    return worst


def p07(C):
    """Does the squeeze name the same bars when a knob moves?"""
    def bw(period):
        out = [None] * len(C)
        s = s2 = 0.0
        for i, c in enumerate(C):
            s += c
            s2 += c * c
            if i >= period:
                s -= C[i - period]
                s2 -= C[i - period] * C[i - period]
            if i >= period - 1:
                m = s / period
                v = max(0.0, s2 / period - m * m)
                out[i] = (v ** 0.5) / m if m else 0.0
        return out

    def squeeze(period, look):
        b = bw(period)
        hit = set()
        for i in range(period + look, len(C)):
            x = b[i]
            if x is None:
                continue
            if all(b[j] is None or x <= b[j] for j in range(i - look, i)):
                hit.add(i)
        return hit

    base = squeeze(20, 120)
    print('\n  P07  布林帶寬擠壓')
    print('       標準差倍數 k 完全不影響判定：BandWidth = 2k*SD/SMA，')
    print('       k 只是等比放大，N 根最小值仍落在同一根 K 棒。真正的旋鈕是')
    print('       週期與回看長度兩個。')
    print('       基準 (週期 20, 回看 120) = %s 根' % format(len(base), ','))
    print('       %-18s %-9s %-9s %s' % ('設定', '根數', '倍率', '與基準重疊'))
    for per, look in [(10, 120), (30, 120), (50, 120), (20, 60), (20, 240)]:
        h = squeeze(per, look)
        j = len(h & base) / len(h | base) if (h | base) else 0.0
        print('       週期 %-3d 回看 %-4d %-9s %-9.2f %.1f%%'
              % (per, look, format(len(h), ','),
                 len(h) / len(base) if base else 0, 100 * j))
    return base


def p69(H, L, S):
    """Is a five-wave impulse the same object at three pivot scales?"""
    def impulses(w):
        pv = pivots(H, L, S, w)
        out = []
        for a in range(len(pv) - 5):
            seg = pv[a:a + 6]
            if seg[0][2] != 2:
                continue
            l0, h1, l2, h3, l4, h5 = [x[1] for x in seg]
            if not (h1 < h3 and h3 < h5):
                continue
            if not (l2 > l0 and l4 > l2):
                continue
            if (h3 - l2) <= (h1 - l0) and (h3 - l2) <= (h5 - l4):
                continue          # wave 3 may not be the shortest
            out.append((seg[0][0], seg[5][0]))
        return out

    print('\n  P69  艾略特 5 波（推動波，多方）')
    print('       %-8s %-11s %s' % ('視窗', '數量', '有視窗 1 對應（時間重疊）'))
    base = impulses(1)
    bset = base
    for w in (1, 2, 3):
        got = impulses(w)
        if w == 1:
            print('       %-8d %-11s %s' % (w, format(len(got), ','), '-'))
            continue
        ov = 0
        for s0, s1 in got:
            if any(not (e1 < s0 or e0 > s1) for e0, e1 in bset):
                ov += 1
        print('       %-8d %-11s %d / %d  = %.0f%%'
              % (w, format(len(got), ','), ov, len(got),
                 100 * ov / len(got) if got else 0))
    return len(base)


def main():
    H, L, C, S = load()
    print('=' * 74)
    print('  D 組實測   %s 根 5 分 K' % format(len(H), ','))
    print('=' * 74)
    pv = pivots(H, L, S, 1)
    print('  視窗 1 樞紐 %s 個\n' % format(len(pv), ','))
    p70(pv)
    p07(C)
    p69(H, L, S)
    print('\n' + '=' * 74)


if __name__ == '__main__':
    main()
