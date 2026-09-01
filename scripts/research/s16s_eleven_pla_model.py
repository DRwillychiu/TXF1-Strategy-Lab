# -*- coding: utf-8 -*-
"""What IND_S16S_ELEVEN will print, derived the way the .pla actually runs.

The scan (s16s_eleven_scan.py) walks i from 1 and peeks at i+1.  MC12 cannot:
its deepest static reference here is High[7], so bar 1 of the indicator sits
seven bars in, and every state machine -- pivot levels, session lows, live
flag poles -- starts EMPTY there rather than at the top of the file.

So this model runs the identical predicates on the identical CSV, but with
the .pla's window and the .pla's one-bar lag, and its output is the
acceptance table.  Guessing the edge cases one at a time is how the 203
phantom happened on 2026-08-30.

Run:  python scripts/research/s16s_eleven_pla_model.py
"""
import csv
import hashlib
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')
CSV = os.path.join('scripts', 'research', 's16s_5min.csv')
WARM = 7                      # deepest reference the .pla makes: High[7]
MAXPOLE = 4                   # measured deepest live-pole list is 3


def main():
    r = list(csv.DictReader(open(CSV, encoding='utf-8')))
    O = [float(x['open']) for x in r]
    H = [float(x['high']) for x in r]
    L = [float(x['low']) for x in r]
    C = [float(x['close']) for x in r]
    S = [int(x['bars_in_sess']) for x in r]
    n = len(H)

    c = {k: [] for k in ('P33', 'P35', 'P37', 'P13', 'P14', 'P41',
                         'P42', 'P43', 'P45', 'P47', 'P48')}
    hiPv = loPv = None
    armHi = armLo = upLast = False
    sessLo = curLo = None
    poles = []
    ovf = 0
    nbars = 0

    def up(k):
        return H[k] - max(O[k], C[k])

    def bd(k):
        return abs(C[k] - O[k])

    # t is the .pla's current bar; the logical bar it classifies is i = t - 1.
    for t in range(WARM, n):
        nbars += 1
        i = t - 1

        # session low tracking runs on every bar, ahead of the guard
        if S[i] < S[i - 1]:
            sessLo, curLo = curLo, L[i]
        elif curLo is None or L[i] < curLo:
            curLo = L[i]

        if not (S[i] >= 2 and S[t] >= S[i]):
            continue

        # ---- pivot level patterns ----
        if hiPv is not None and armHi and H[i] > hiPv and C[i] < hiPv:
            c['P33'].append(i)
            armHi = False
        if loPv is not None and armLo and C[i] < loPv:
            c['P35'].append(i)
            if upLast:
                c['P37'].append(i)
            upLast = False
            armLo = False
        if hiPv is not None and C[i] > hiPv:
            upLast = True

        # ---- bar level patterns ----
        rng = H[i] - L[i]
        if S[i] >= 5:
            if all(rng > H[i - d] - L[i - d] for d in (1, 2, 3)):
                c['P41'].append(i)
            if S[i] >= 8 and all(rng > H[i - d] - L[i - d]
                                 for d in range(1, 7)):
                c['P42'].append(i)
        if S[i] >= 3 and H[i] > H[i - 1] and C[i] < L[i - 1]:
            c['P43'].append(i)
        if sessLo is not None and S[i] >= 2 and C[i] < sessLo:
            c['P45'].append(i)
            sessLo = None
        if S[i] >= 4:
            a, b = i - 2, i
            if (up(a) > bd(a) and up(b) > bd(b)
                    and H[a] > H[a + 1] and H[b] > H[a + 1]
                    and abs(H[a] - H[b]) < min(up(a), up(b))):
                c['P47'].append(i)
            a, b = i - 1, i
            if (up(a) > bd(a) and up(b) > bd(b)
                    and H[a] > H[a - 1] and H[b] > H[b + 1]
                    and abs(H[a] - H[b]) < min(up(a), up(b))):
                c['P48'].append(i)

        # ---- bear flag / pennant ----
        alive = []
        for p in poles:
            if H[i] > p['h']:
                continue
            if C[i] < p['l']:
                if p['n'] >= 1:
                    c['P13'].append(i)
                    if p['conv']:
                        c['P14'].append(i)
                continue
            p['conv'] = p['conv'] and rng < p['last']
            p['last'] = rng
            p['n'] += 1
            alive.append(p)
        poles = alive
        if S[i] >= 5 and C[i] < O[i] and all(
                rng > H[i - d] - L[i - d] for d in (1, 2, 3)):
            if len(poles) < MAXPOLE:
                poles.append(dict(h=H[i], l=L[i], n=0, conv=True, last=rng))
            else:
                ovf += 1

        # ---- push the pivot for logical bar i, at the END, as the scan does
        if H[i] > H[i - 1] and H[i] > H[t]:
            hiPv, armHi = H[i], True
        if L[i] < L[i - 1] and L[i] < L[t]:
            loPv, armLo = L[i], True

    h = hashlib.md5()
    with open(CSV, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    print('CSV %d rows  md5 %s' % (n, h.hexdigest()))
    print()
    print('ELEVEN TALLY  bars= %d   pole_overflow= %d' % (nbars, ovf))
    print('  P33 %6d  P35 %6d  P37 %6d  P13 %6d  P14 %6d  P41 %6d'
          % tuple(len(c[k]) for k in
             ('P33', 'P35', 'P37', 'P13', 'P14', 'P41')))
    print('  P42 %6d  P43 %6d  P45 %6d  P47 %6d  P48 %6d'
          % tuple(len(c[k]) for k in
             ('P42', 'P43', 'P45', 'P47', 'P48')))
    return c


if __name__ == '__main__':
    main()
