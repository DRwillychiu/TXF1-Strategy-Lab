# -*- coding: utf-8 -*-
"""One real instance per pattern, for the census page.

Willy: the definitions need a real chart to be checked against.  A definition
nobody can hold up against real bars is one nobody can disagree with.

The instances come straight from the scan's own push loop rather than being
re-derived here.  A second implementation of the chain is a second thing to
disagree with the first, and this project has already paid for that once --
the census was built on a merged chain while the indicator resets.

Selection rules, both learned the hard way:

  MEDIAN amplitude, never the maximum.  The largest P51 instance was an
  1,819-point outlier spanning a session handover: spectacular, and nothing
  like what the pattern normally looks like.

  Never across a session.  Pivot detection cannot span the 13:45 close, so an
  example that straddles it shows a shape the detector could not have found.

Run:  python scripts/research/s16s_census15_pick.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join('scripts', 'research'))
# the scan module installs a utf-8 stdout on import; wrapping it again here
# closes the buffer the first wrapper owns, which kills every later print
import s16s_census15_scan as S                                   # noqa: E402

OUT = os.path.join('scripts', 'research', 's16s_census15_example.json')
PAD = 3


def main():
    rows, H, L, SS = S.bars()
    hits, _ = S.push_scan(H, L, SS)
    out = {}
    for spec in S.SPEC:
        cid = spec[0]
        cand = []
        for b0, b1, piv in hits[cid]:
            if b0 - PAD < 0 or b1 + PAD >= len(rows):
                continue
            if any(SS[i + 1] < SS[i] for i in range(b0 - PAD, b1 + PAD)):
                continue
            cand.append((max(H[b0:b1 + 1]) - min(L[b0:b1 + 1]), b0, b1, piv))
        if not cand:
            print('  %-5s 沒有不跨時段的案例（母體 %d）' % (cid, len(hits[cid])))
            continue
        cand.sort(key=lambda x: x[0])
        amp, b0, b1, piv = cand[len(cand) // 2]                  # MEDIAN
        s0, s1 = b0 - PAD, b1 + PAD
        out[cid] = {
            'n': len(cand), 'amp': amp, 'span': b1 - b0,
            'bars': [{'t': '%s %s' % (rows[i]['ymd'], rows[i]['hhmm']),
                      'o': float(rows[i]['open']), 'h': H[i], 'l': L[i],
                      'c': float(rows[i]['close'])} for i in range(s0, s1 + 1)],
            'piv': [[b - s0, k] for b, k in piv],
            'd0': int(rows[b0]['ymd']),
            't0': int(rows[b0]['hhmm']), 't1': int(rows[b1]['hhmm'])}
        print('  %-5s %s %s-%s  振幅 %.0f 點  跨 %d 根  可用案例 %s / 母體 %s'
              % (cid, rows[b0]['ymd'], rows[b0]['hhmm'], rows[b1]['hhmm'],
                 amp, b1 - b0, format(len(cand), ','),
                 format(len(hits[cid]), ',')))
    json.dump(out, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('\n  -> %s   %d 個案例' % (OUT, len(out)))


if __name__ == '__main__':
    main()
