# -*- coding: utf-8 -*-
"""One real instance per pattern, for the eleven-pattern page.

Instances come straight from the scan's own pass rather than being re-derived.
A second implementation is a second thing to disagree with the first, and this
project has already paid for that once -- the 2026-08-30 census ran on a chain
the indicator has never used.

Selection: MEDIAN amplitude, never the maximum, and never across a session.
Both learned from the P51 example that turned out to be an 1,819-point outlier
spanning a session handover.

Run:  python scripts/research/s16s_eleven_pick.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join('scripts', 'research'))
import s16s_eleven_scan as S                                     # noqa: E402

OUT = os.path.join('scripts', 'research', 's16s_eleven_example.json')
PAD = 4


def main():
    rows, O, H, L, C, SS = S.load()
    hit = S.scan(O, H, L, C, SS)
    out = {}
    for cid, zh, en, d, sk in S.NAMES:
        cand = []
        for b0, b1 in hit[cid]:
            if b0 - PAD < 0 or b1 + PAD >= len(rows):
                continue
            if any(SS[i + 1] < SS[i] for i in range(b0 - PAD, b1 + PAD)):
                continue
            cand.append((max(H[b0:b1 + 1]) - min(L[b0:b1 + 1]), b0, b1))
        if not cand:
            print('  %-5s 沒有不跨時段的案例（母體 %d）' % (cid, len(hit[cid])))
            continue
        cand.sort(key=lambda x: x[0])
        amp, b0, b1 = cand[len(cand) // 2]
        s0, s1 = b0 - PAD, b1 + PAD
        out[cid] = {
            'n': len(cand), 'amp': amp, 'span': b1 - b0,
            'i0': b0 - s0, 'i1': b1 - s0,
            'bars': [{'t': '%s %s' % (rows[i]['ymd'], rows[i]['hhmm']),
                      'o': O[i], 'h': H[i], 'l': L[i], 'c': C[i]}
                     for i in range(s0, s1 + 1)],
            'd0': int(rows[b0]['ymd']),
            't0': int(rows[b0]['hhmm']), 't1': int(rows[b1]['hhmm'])}
        print('  %-5s %s %s-%s  振幅 %.0f 點  跨 %d 根  可用 %s / 母體 %s'
              % (cid, rows[b0]['ymd'], rows[b0]['hhmm'], rows[b1]['hhmm'],
                 amp, b1 - b0, format(len(cand), ','),
                 format(len(hit[cid]), ',')))
    json.dump(out, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print('\n  -> %s   %d 個案例' % (OUT, len(out)))


if __name__ == '__main__':
    main()
