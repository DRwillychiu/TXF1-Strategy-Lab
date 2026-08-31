# -*- coding: utf-8 -*-
"""The eleven patterns that still have to go through the full process.

Twelve went in; P39 came out first.  "The last three pivot highs each lower
than the one before" is PH1 > PH2 > PH3 and nothing else -- byte-identical to
the falling-highs primitive at 5,280 against 5,280 -- and it sets no condition
on the lows at all, so it straddles two cells of the 2x2 rather than naming
one.  Same ground that collapsed P24 and P25.

The other two reduction candidates survived:

  P35 is NOT the falling-lows primitive.  A CLOSE through the standing pivot
      low happens 24,129 times; the next pivot low printing LOWER happens
      34,116.  The gap is every case where price pokes under and closes back
      above, and that gap is the whole point of the pattern.

  P13 / P14 cannot inherit the atlas definition.  The atlas gives them 20,938
      and 4,634; no WR4-based pole comes near that, so whatever was counted
      then was something else.  Defined fresh here.

TWO SKELETONS, and they are not interchangeable:

  pivot   P33 P35 P37     read the chain the indicator builds
  bar     P13 P14 P41 P42 P43 P45 P47 P48   read OHLC directly

Devices used, all zero-parameter:

  rank              "widest of the last N" -- Crabel's N=4 and N=7, borrowed
                    constants Willy accepted on 2026-08-31 and recorded as
                    borrowed rather than derived.
  shadow vs body    "long upper shadow" is a threshold until it is written as
                    a COMPARISON: upper shadow greater than the body.  Nothing
                    to tune.
  gap vs shadow     "two highs at a similar level" needs a tolerance, and the
                    bars supply one: the difference between the highs smaller
                    than the shorter of the two shadows.
  resolution        the bear flag has no bar count.  The drift runs until one
                    side gives -- close below the pole's low, or the pole's
                    high exceeded -- so "how long is a flag" never gets asked.

Every pattern is also counted on the mirrored bar series (H' = -L, L' = -H).
A shape whose mirror occurs as often carries no direction.

Counts only.  No P&L.

Run:  python scripts/research/s16s_eleven_scan.py
"""
import csv
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.join('scripts', 'research')
CSV = os.path.join(HERE, 's16s_5min.csv')
OUT = os.path.join(HERE, 's16s_eleven.json')
CAP = 12


def load():
    r = list(csv.DictReader(open(CSV, encoding='utf-8')))
    return (r, [float(x['open']) for x in r], [float(x['high']) for x in r],
            [float(x['low']) for x in r], [float(x['close']) for x in r],
            [int(x['bars_in_sess']) for x in r])


def body(O, C, i):
    return abs(C[i] - O[i])


def upper(O, H, C, i):
    return H[i] - max(O[i], C[i])


def scan(O, H, L, C, S):
    """One pass.  Pivot patterns ride the indicator's chain; bar patterns read
    OHLC.  Every hit records (first bar, last bar) so a real case can be cut
    later without a second implementation of anything."""
    n = len(H)
    hit = {k: [] for k in
           ('P33', 'P35', 'P37', 'P13', 'P14', 'P41', 'P42', 'P43', 'P45',
            'P47', 'P48')}
    px = [0.0] * CAP
    bar = [0] * CAP
    typ = [0] * CAP
    ch = 0
    hiPv = None                 # standing pivot high, and the bar it sits on
    hiBar = 0
    loPv = None
    loBar = 0
    armedHi = False             # each level is swept / broken at most once
    armedLo = False
    upLast = False              # the last structural break was upward
    sessLo = None               # previous session's low
    curLo = None
    poles = []                  # live bear-flag poles

    for i in range(1, n - 1):
        newsess = S[i] < S[i - 1]
        if newsess:
            sessLo = curLo
            curLo = L[i]
        elif curLo is None or L[i] < curLo:
            curLo = L[i]
        if S[i] < 2 or S[i + 1] < S[i]:
            continue

        # ---- pivot-level patterns ------------------------------------
        if hiPv is not None and armedHi and H[i] > hiPv and C[i] < hiPv:
            hit['P33'].append((hiBar, i))          # swept and closed back under
            armedHi = False
        if loPv is not None and armedLo and C[i] < loPv:
            hit['P35'].append((loBar, i))
            if upLast:
                hit['P37'].append((loBar, i))      # the FIRST one after an up
            upLast = False
            armedLo = False
        if hiPv is not None and C[i] > hiPv:
            upLast = True

        # ---- bar-level patterns --------------------------------------
        rng = H[i] - L[i]
        if S[i] >= 5:
            if all(rng > H[i - d] - L[i - d] for d in (1, 2, 3)):
                hit['P41'].append((i - 3, i))
            if S[i] >= 8 and all(rng > H[i - d] - L[i - d]
                                 for d in range(1, 7)):
                hit['P42'].append((i - 6, i))
        if S[i] >= 3 and H[i] > H[i - 1] and C[i] < L[i - 1]:
            hit['P43'].append((i - 1, i))
        if sessLo is not None and S[i] >= 2 and C[i] < sessLo:
            hit['P45'].append((i - 1, i))
            sessLo = None                          # once per session
        # horn: two spikes one bar apart, both shadow-dominant, dip between
        if S[i] >= 4:
            a, b = i - 2, i
            if (upper(O, H, C, a) > body(O, C, a)
                    and upper(O, H, C, b) > body(O, C, b)
                    and H[a] > H[a + 1] and H[b] > H[a + 1]
                    and abs(H[a] - H[b]) < min(upper(O, H, C, a),
                                               upper(O, H, C, b))):
                hit['P47'].append((a, b))
        # pipe: two ADJACENT spikes, same test for "similar"
        if S[i] >= 4:
            a, b = i - 1, i
            if (upper(O, H, C, a) > body(O, C, a)
                    and upper(O, H, C, b) > body(O, C, b)
                    and H[a] > H[a - 1] and H[b] > H[b + 1]
                    and abs(H[a] - H[b]) < min(upper(O, H, C, a),
                                               upper(O, H, C, b))):
                hit['P48'].append((a, b))

        # ---- bear flag / pennant: pole, drift, resolution -------------
        alive = []
        for p in poles:
            if S[i] < S[i - 1]:
                continue                            # a session ends the flag
            if H[i] > p['h']:
                continue                            # pole high taken out
            if C[i] < p['l']:
                if p['n'] >= 1:
                    hit['P13'].append((p['i'], i))
                    if p['conv']:
                        hit['P14'].append((p['i'], i))
                continue
            p['conv'] = p['conv'] and (H[i] - L[i]) < p['last']
            p['last'] = H[i] - L[i]
            p['n'] += 1
            alive.append(p)
        poles = alive
        if S[i] >= 5 and C[i] < O[i] and all(
                rng > H[i - d] - L[i - d] for d in (1, 2, 3)):
            poles.append(dict(i=i, h=H[i], l=L[i], n=0, conv=True, last=rng))

        # ---- push the pivot chain ------------------------------------
        for k in (1, 2):
            if k == 1 and not (H[i] > H[i - 1] and H[i] > H[i + 1]):
                continue
            if k == 2 and not (L[i] < L[i - 1] and L[i] < L[i + 1]):
                continue
            if ch > 0 and typ[ch - 1] == k:
                ch = 0
            if ch >= CAP:
                for j in range(CAP - 1):
                    px[j] = px[j + 1]
                    bar[j] = bar[j + 1]
                    typ[j] = typ[j + 1]
                ch = CAP - 1
            px[ch] = H[i] if k == 1 else L[i]
            bar[ch] = i
            typ[ch] = k
            ch += 1
            if k == 1:
                hiPv, hiBar, armedHi = H[i], i, True
            else:
                loPv, loBar, armedLo = L[i], i, True
    return hit


NAMES = [
    ('P33', '上衝回落', 'Upthrust / Liquidity Sweep', '空', 'pivot'),
    ('P35', '結構破壞（向下）', 'Break of Structure, Down', '空', 'pivot'),
    ('P37', '性格轉變（向下）', 'Change of Character, Down', '空', 'pivot'),
    ('P13', '空方旗形', 'Bear Flag', '空', 'bar'),
    ('P14', '空方三角旗', 'Bear Pennant', '空', 'bar'),
    ('P41', 'WR4 最近四根最寬', 'Widest of 4', '中性', 'bar'),
    ('P42', 'WR7 最近七根最寬', 'Widest of 7', '中性', 'bar'),
    ('P43', '關鍵反轉（空）', 'Key Reversal, Bearish', '空', 'bar'),
    ('P45', '破前時段低', 'Prior Session Low Break', '空', 'bar'),
    ('P47', '號角頂', 'Horn Top', '空', 'bar'),
    ('P48', '管狀頂', 'Pipe Top', '空', 'bar'),
]


def main():
    rows, O, H, L, C, S = load()
    a = scan(O, H, L, C, S)
    b = scan([-x for x in O], [-x for x in L], [-x for x in H],
             [-x for x in C], S)                    # a true reflection
    print('=' * 76)
    print('  十一種母體普查   %s 根 5 分 K   重置鏈' % format(len(rows), ','))
    print('=' * 76)
    print('  %-6s %-18s %-5s %-6s %-10s %-10s %-8s %s'
          % ('代號', '名稱', '方向', '骨架', '母體', '鏡像', '倍率', '跨度中位'))
    print('  ' + '-' * 72)
    out = []
    for cid, zh, en, d, sk in NAMES:
        n, m = len(a[cid]), len(b[cid])
        sp = sorted(y - x for x, y in a[cid])
        med = sp[len(sp) // 2] if sp else 0
        r = (n / float(m)) if m else None
        out.append({'id': cid, 'zh': zh, 'en': en, 'dir': d, 'sk': sk,
                    'n': n, 'mirror': m,
                    'ratio': round(r, 3) if r else None, 'span': med})
        print('  %-6s %-18s %-5s %-6s %-10s %-10s %-8s %d 根'
              % (cid, zh, d, sk, format(n, ','), format(m, ','),
                 ('%.2fx' % r) if r else '-', med))
    json.dump({'bars': len(rows), 'rows': out},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n  -> %s' % OUT)
    print('=' * 76)


if __name__ == '__main__':
    main()
