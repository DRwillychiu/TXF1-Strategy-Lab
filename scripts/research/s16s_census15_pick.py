# -*- coding: utf-8 -*-
"""One real instance per pattern, for the census page.

Willy: the thirteen need their logic written out AND a real chart to compare
it against.  A definition nobody can check against real bars is a definition
nobody can disagree with, which is worse than a wrong one.

Selection rules, both learned the hard way:

  MEDIAN amplitude, never the maximum.  Picking the largest instance of
  P51 once produced a 1,819-point example that spanned a session handover --
  spectacular, and nothing like what the pattern normally looks like.

  Never across a session.  Pivot detection cannot span the 13:45 close, so an
  example that straddles it shows a shape the detector could not have found.

Run:  python scripts/research/s16s_census15_pick.py
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join('scripts', 'research'))
# the scan module installs a utf-8 stdout on import; wrapping it again here
# closes the buffer the first wrapper owns, which kills every later print
import s16s_census15_scan as S                                   # noqa: E402

HERE = os.path.join('scripts', 'research')
OUT = os.path.join(HERE, 's16s_census15_example.json')
PAD = 3


def load():
    rows = list(csv.DictReader(open(S.CSV, encoding='utf-8')))
    return rows


def main():
    rows = load()
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    SS = [int(r['bars_in_sess']) for r in rows]
    pv, _ = S.chain()
    out = {}
    for spec in S.SPEC:
        cid, need, first, fn = spec[0], spec[4], spec[5], spec[6]
        cand = []
        for a in range(len(pv) - need):
            if pv[a][2] != first:
                continue
            sl = pv[a:a + need]
            if not fn(sl):
                continue
            b0, b1 = sl[0][0], sl[-1][0]
            # one session only: bars_in_sess never restarts inside the window
            if any(SS[i + 1] < SS[i] for i in range(b0 - PAD, b1 + PAD)):
                continue
            if b0 - PAD < 0 or b1 + PAD >= len(rows):
                continue
            amp = max(H[b0:b1 + 1]) - min(L[b0:b1 + 1])
            cand.append((amp, a, b0, b1))
        if not cand:
            print('  %-5s 沒有不跨時段的案例' % cid)
            continue
        cand.sort()
        amp, a, b0, b1 = cand[len(cand) // 2]                    # MEDIAN
        s0, s1 = b0 - PAD, b1 + PAD
        bars = [{'t': '%s %s' % (rows[i]['ymd'], rows[i]['hhmm']),
                 'o': float(rows[i]['open']), 'h': H[i], 'l': L[i],
                 'c': float(rows[i]['close'])} for i in range(s0, s1 + 1)]
        piv = [[p[0] - s0, 'H' if p[2] == 1 else 'L'] for p in pv[a:a + need]]
        out[cid] = {'n': len(cand), 'amp': amp, 'span': b1 - b0,
                    'bars': bars, 'piv': piv,
                    'd0': int(rows[b0]['ymd']),
                    't0': int(rows[b0]['hhmm']), 't1': int(rows[b1]['hhmm'])}
        print('  %-5s %s  %s %s-%s  振幅 %.0f 點  跨 %d 根  候選 %s'
              % (cid, '案例', rows[b0]['ymd'], rows[b0]['hhmm'],
                 rows[b1]['hhmm'], amp, b1 - b0, format(len(cand), ',')))
    json.dump(out, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('\n  -> %s   %d 個案例' % (OUT, len(out)))


if __name__ == '__main__':
    main()
