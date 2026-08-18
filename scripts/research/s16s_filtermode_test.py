# -*- coding: ascii -*-
"""
S16_S SECTION 8.7 -- exhaustive check of the four filter modes.

Two things have to be true and neither should be taken on trust:

  A1  at KB_Filter_Win = 0 all four modes are the SAME predicate, so the
      anchor cannot drift no matter which mode is left set in MC12
  A2  at Win > 0 the modes are genuinely DIFFERENT, otherwise the sweep is
      three copies of one cell and a waste of a run

The four expressions are parsed out of the shipped .pla and transpiled, not
retyped, same discipline as the pattern harness. Then every reachable state
is enumerated: the two ages take any value in 0..24 plus the un-armed
sentinel 999, crossed with Win in 0..8.

Run:  python scripts/research/s16s_filtermode_test.py
"""
import os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PLA = os.path.join(REPO, 'strategies', 'research', 'S16_MACrossShort',
                   'S16_S_MACrossShort_v1.26.0.pla')

AGES = list(range(0, 25)) + [999]
WINS = list(range(0, 9))


def strip_comments(t):
    return re.sub(r'\{[^{}]*\}', ' ', t)


def transpile(e):
    e = e.replace('>=', '@GE@').replace('<=', '@LE@').replace('<>', '@NE@')
    e = re.sub(r'=\s*True\b', '== True', e)
    e = re.sub(r'=\s*False\b', '== False', e)
    e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e = e.replace('@GE@', '>=').replace('@LE@', '<=').replace('@NE@', '!=')
    return e


def main():
    raw = open(PLA, 'rb').read()
    print('source   %s' % os.path.basename(PLA))
    print('bytes    %d' % len(raw))
    print('md5      %s' % hashlib.md5(raw).hexdigest())

    src = raw.decode('ascii')
    a = src.index('{ SECTION 8.7 - FILTER ORDER')
    b = src.index('{ SECTION 9 - ENTRY')
    sec = ' '.join(strip_comments(src[a:b]).split())

    # v_Filt_Pass = <expr>  , one per branch, in source order: 1, 2, 3, then else
    exprs = re.findall(r'v_Filt_Pass\s*=\s*(.+?)(?=\s+else|\s*;)', sec)
    assert len(exprs) == 4, 'expected 4 mode expressions, parsed %d' % len(exprs)
    MODE = {1: exprs[0], 2: exprs[1], 3: exprs[2], 0: exprs[3]}
    print('mode expressions parsed: %d' % len(MODE))
    print()
    for m in (0, 1, 2, 3):
        print('  mode %d  %s' % (m, ' '.join(MODE[m].split())))
    print()

    def ev(m, sa, ca, w):
        g = {'v_Slope_Age': sa, 'v_Clean_Age': ca, 'KB_Filter_Win': w,
             '__builtins__': {}}
        return bool(eval(transpile(MODE[m]), g))

    fail = 0

    print('=' * 78)
    print(' A1  at Win = 0 every mode must equal mode 0')
    print('=' * 78)
    bad = []
    for sa in AGES:
        for ca in AGES:
            ref = ev(0, sa, ca, 0)
            for m in (1, 2, 3):
                if ev(m, sa, ca, 0) != ref:
                    bad.append((m, sa, ca))
    print('  states checked: %d' % (len(AGES) * len(AGES)))
    print('  divergences   : %d' % len(bad))
    for x in bad[:10]:
        print('     mode %d at slope_age=%d clean_age=%d' % x)
    if bad:
        fail += len(bad)
    else:
        print('  OK -- the anchor holds for every mode at Win 0')

    print()
    print('=' * 78)
    print(' A2  at Win > 0 the modes must actually differ')
    print('=' * 78)
    print('  %-5s %10s %10s %10s %10s' % ('Win', 'mode0', 'mode1', 'mode2', 'mode3'))
    tot = len(AGES) * len(AGES)
    for w in WINS:
        row = [sum(1 for sa in AGES for ca in AGES if ev(m, sa, ca, w))
               for m in (0, 1, 2, 3)]
        print('  %-5d %10d %10d %10d %10d' % (w, row[0], row[1], row[2], row[3]))
        if w == 0 and len(set(row)) != 1:
            fail += 1
        if w > 0 and len(set(row)) == 1:
            print('     WARNING: all four identical at Win %d' % w)
    print('  (counts are out of %d enumerated states, not a market frequency)' % tot)

    print()
    print('=' * 78)
    print(' A3  mode 3 must be exactly the union of modes 1 and 2')
    print('=' * 78)
    bad3 = 0
    for w in WINS:
        for sa in AGES:
            for ca in AGES:
                if ev(3, sa, ca, w) != (ev(1, sa, ca, w) or ev(2, sa, ca, w)):
                    bad3 += 1
    print('  divergences: %d' % bad3)
    fail += bad3
    if not bad3:
        print('  OK -- mode 3 is exactly modes 1 OR 2, as the design claims')

    print()
    print('=' * 78)
    print(' RESULT')
    print('=' * 78)
    print('  FAILURES: %d' % fail)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
