# -*- coding: utf-8 -*-
"""S16_S entry-side decomposition from the v1.16.0 STRUCTDIAG run.

WHY THIS EXISTS
    The 2026-08-08 re-entry failure-test document compared the two entry
    legs per-trade and got it wrong twice, in opposite directions:

        doc section 4      8,240 / 23,085 = 35.7%   asymmetric -- the
                                                    outlier was removed
                                                    from one leg only
        commit a63b0f6     8,240 / 12,913 = 63.8%   not reproducible

    Neither number can be checked by eye, so this script recomputes the
    split from the raw diagnostic join and asserts the anchor first. If
    the anchor does not reproduce, nothing downstream is trustworthy and
    the script stops rather than printing plausible garbage.

    It also answers two entry-side questions the same join can settle
    without another backtest:
      - which fills Tail_FillSemantic_On would remove, and for how much
      - which entry signals still sit on a session's first bar, where
        v_Slope is computed across the session boundary

INPUTS (both produced by S16_S_MACrossShort_v1.16.0_STRUCTDIAG.pla)
    S16S_struct_diag.csv                     -- per-fill diagnostic rows
    TXF1  ..._v1.16.0_STRUCTDIAG ....xls     -- MC12 performance report

ANCHOR
    119 trades / 3,141,200. Asserted, not assumed.
"""
import csv
import io
import os
import sys
import collections

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

DL = os.path.join(os.path.expanduser('~'), 'Downloads')
CSV = os.path.join(DL, 'S16S_struct_diag.csv')
XLS = os.path.join(DL, 'TXF1  S16_S_MACrossShort_v1.16.0_STRUCTDIAG '
                       '策略回測績效報告.xls')

ANCHOR_TRADES = 119
ANCHOR_NET = 3141200

# Column order emitted by Section 10.9 of the diagnostic .pla.
COLS = ['fd', 'ft', 'fpx', 'sd', 'st', 'isre', 'h1', 'h2', 'hbar',
        'l1', 'l2', 'lbar', 'cnt', 'sep', 'slope', 'kb', 'sclose', 'cbar']


def money(v):
    return format(int(round(v)), ',')


def el_to_iso(v):
    """EasyLanguage date (YYYY-1900)*10000+MMDD -> ISO."""
    v = int(v)
    return '%04d-%02d-%02d' % (1900 + v // 10000, (v % 10000) // 100, v % 100)


def load_diag(path):
    rows = []
    with open(path, newline='', encoding='utf-8', errors='replace') as fh:
        for r in csv.reader(fh):
            r = [x.strip() for x in r if x.strip() != '']
            if len(r) < len(COLS):
                continue
            try:
                rows.append(dict(zip(COLS, [float(x) for x in r[:len(COLS)]])))
            except ValueError:
                continue
    return rows


def load_trades(path):
    """Entry rows paired with their exit, from the MC12 report."""
    wb = openpyxl.load_workbook(io.BytesIO(open(path, 'rb').read()),
                                data_only=True)
    out, cur = [], None
    for r in wb['交易明細'].iter_rows(min_row=4, values_only=True):
        if r[0] in (None, ''):
            if cur is not None and '離開' in str(r[2] or ''):
                out.append(cur)
                cur = None
            continue
        if '進入' not in str(r[2] or ''):
            continue
        cur = dict(d=str(r[4])[:10],
                   t=int(str(r[5])[:5].replace(':', '')),
                   net=r[8])
    return out


def main():
    for p in (CSV, XLS):
        if not os.path.exists(p):
            print('missing input:', p)
            print('re-run S16_S_MACrossShort_v1.16.0_STRUCTDIAG.pla first.')
            return 1

    diag = load_diag(CSV)
    trades = load_trades(XLS)

    print('=' * 74)
    print('0. ANCHOR')
    print('=' * 74)
    net = sum(x['net'] for x in trades)
    print('   trades %d (need %d)   net %s (need %s)'
          % (len(trades), ANCHOR_TRADES, money(net), money(ANCHOR_NET)))
    if len(trades) != ANCHOR_TRADES or int(net) != ANCHOR_NET:
        print('   *** ANCHOR FAILED -- the report is not the v1.16.0 '
              'population. Stopping. ***')
        return 1

    idx = {(el_to_iso(r['fd']), int(r['ft'])): r for r in diag}
    joined, unjoined = [], []
    for x in trades:
        k = (x['d'], x['t'])
        if k in idx:
            joined.append((x, idx[k]))
        else:
            unjoined.append(x)
    print('   joined %d / %d   unjoined %d' % (len(joined), len(trades),
                                               len(unjoined)))
    if unjoined:
        print('   *** join incomplete -- the split below would be partial. '
              'Stopping. ***')
        return 1
    print('   ANCHOR PASS')

    # ---- 1. the two legs -------------------------------------------------
    re_leg = [x['net'] for x, r in joined if r['isre'] == 1]
    dc_leg = [x['net'] for x, r in joined if r['isre'] != 1]

    print()
    print('=' * 74)
    print('1. PER-TRADE BY LEG')
    print('=' * 74)
    print('   %-38s %5s %14s %12s' % ('', 'n', 'total', 'per trade'))
    for name, v in (('re-entry', re_leg), ('death cross', dc_leg)):
        print('   %-38s %5d %14s %12s'
              % (name, len(v), money(sum(v)), money(sum(v) / len(v))))

    print()
    print('   each leg minus its OWN best trade -- the symmetric form:')
    sym = {}
    for name, v in (('re-entry', re_leg), ('death cross', dc_leg)):
        w = sorted(v)[:-1]
        sym[name] = sum(w) / len(w)
        print('   %-38s %5d %14s %12s   (best %s)'
              % (name, len(w), money(sum(w)), money(sym[name]),
                 money(max(v))))

    print()
    print('   symmetric   re-entry / death cross : %.1f%%   <- correct'
          % (sym['re-entry'] / sym['death cross'] * 100))
    print('   asymmetric  (doc section 4)        : %.1f%%   <- denominator '
          'keeps its outlier'
          % (sym['re-entry'] / (sum(dc_leg) / len(dc_leg)) * 100))

    # ---- 2. Tail_FillSemantic_On -----------------------------------------
    print()
    print('=' * 74)
    print('2. WHAT Tail_FillSemantic_On = True WOULD REMOVE')
    print('=' * 74)
    print('   The switch moves the last permitted SIGNAL from 0430 to 0425,')
    print('   so every fill stamped 0435 disappears.')
    hit = [(x, r) for x, r in joined if int(r['ft']) == 435]
    for x, r in hit:
        print('   fill %s 04:35  signal %s %04d  net %s  (%s)'
              % (x['d'], el_to_iso(r['sd']), int(r['st']), money(x['net']),
                 're-entry' if r['isre'] == 1 else 'death cross'))
    lost = sum(x['net'] for x, _ in hit)
    print('   removes %d trade(s) worth %s' % (len(hit), money(lost)))
    print('   PREDICTED MC12 result with the switch ON: %d trades / %s'
          % (len(trades) - len(hit), money(net - lost)))
    print('   (a prediction from the trade file -- still needs the A/B run)')

    # ---- 3. session-first-bar signals ------------------------------------
    print()
    print('=' * 74)
    print('3. ENTRY SIGNALS STILL SITTING ON A SESSION FIRST BAR')
    print('=' * 74)
    print('   v_Slope = v_ZLEMA_Fast[1] - v_ZLEMA_Fast, and on a session')
    print('   first bar [1] is the previous session\'s last bar, so the')
    print('   overnight gap enters the slope as one bar of momentum.')
    print('   The gap filter only blocks these when the gap was <= 0 AND')
    print('   the first bar closed at or above its open, so the rest pass.')
    print()
    first = [(x, r) for x, r in joined if int(r['st']) in (850, 1505)]
    all_slopes = sorted(r['slope'] for _, r in joined)
    med = all_slopes[len(all_slopes) // 2]
    print('   %-12s %-6s %-12s %-6s %12s %10s'
          % ('signal date', 'time', 'fill date', 'time', 'net', 'slope'))
    for x, r in first:
        print('   %-12s %-6d %-12s %-6d %12s %10.1f'
              % (el_to_iso(r['sd']), int(r['st']), x['d'], x['t'],
                 money(x['net']), r['slope']))
    print('   %d trades, subtotal %s'
          % (len(first), money(sum(x['net'] for x, _ in first))))
    print('   median slope over all %d trades: %.1f' % (len(joined), med))
    print('   -- slopes well above that median on these bars are the')
    print('      signature of the gap being read as momentum.')

    # ---- 4. K-bar reach ---------------------------------------------------
    print()
    print('=' * 74)
    print('4. K-BAR TYPE COVERAGE')
    print('=' * 74)
    kb = collections.Counter(int(r['kb']) for _, r in joined)
    print('   trades with no classification (type 0): %d / %d'
          % (kb.get(0, 0), len(joined)))
    print('   distinct types present                : %d'
          % len([k for k in kb if k]))
    print('   NOTE: v_KB_* is computed inside "if v_Sess_First", so this')
    print('   classifies the SESSION OPENING bar, not the signal bar.')
    print('   Nothing in the entry or exit chain reads v_KB_Type.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
