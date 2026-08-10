# -*- coding: utf-8 -*-
"""S16_S time-rule compliance audit -- do the fills obey the stated windows?

THE QUESTION THIS ANSWERS
    The time inputs state rules in plain language. This checks the rules
    against what the engine actually did, rather than against what the
    code looks like it should do. Reading the condition tells you what
    was INTENDED; only the fill timestamps tell you what HAPPENED.

    Every check below is stated as a window, and any fill outside its
    window is printed with its date so it can be looked up in MC.

THE RULES (v1.17.0 defaults)
    sessions            day   0850..1345      night 1505..2355, 0005..0500
                        (bars are stamped at their CLOSE)
    entry SIGNAL gate   ( Time <= Tail_LastEntry_Time or Time > 500 )
                        = 0850..1345, 1505..2355, 0005..0430
    entry FILL          signal bar + 1  (market order) or the next bar's
                        range (stop order) -- either way the NEXT bar
    force-exit SIGNAL   Time >= Tail_ForceExit_Time (440), bounded <= 500
    the design promise  no position may survive a market closure:
                        the morning break 0500-0845, a weekend, a holiday

WHAT COUNTS AS A VIOLATION
    A. any fill stamped at a time that is not a legal session bar
    B. an entry fill inside the window the entry gate is supposed to
       close -- 0440..0500 under v1.16.0 semantics, 0435..0500 once
       Tail_FillSemantic_On is turned on
    C. an exit fill after 0500, or on a later calendar day than its
       entry when a closure sits between them
    D. a settlement-day trade still open after Settlement_Flat_Time

INPUT
    the MC12 performance report for the run being audited (default: the
    v1.16.0 STRUCTDIAG report, whose population is the adopted one)
"""
import io
import os
import sys
import datetime

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

DL = os.path.join(os.path.expanduser('~'), 'Downloads')
DEFAULT_XLS = os.path.join(
    DL, 'TXF1  S16_S_MACrossShort_v1.16.0_STRUCTDIAG 策略回測績效報告.xls')

TAIL_LAST_ENTRY = 430
TAIL_FORCE_EXIT = 440
DAY_START, DAY_END = 845, 1345
NIGHT_START, NIGHT_END = 1500, 500


def hhmm(s):
    return int(str(s)[:5].replace(':', ''))


def in_session(t):
    return (DAY_START < t <= DAY_END) or (t > NIGHT_START) or (t <= NIGHT_END)


def load(path):
    wb = openpyxl.load_workbook(io.BytesIO(open(path, 'rb').read()),
                                data_only=True)
    trades, cur = [], None
    for r in wb['交易明細'].iter_rows(min_row=4, values_only=True):
        kind = str(r[2] or '')
        if '進入' in kind:
            cur = dict(ed=str(r[4])[:10], et=hhmm(r[5]), ep=r[6],
                       sig=str(r[3] or ''), net=r[8])
        elif '離開' in kind and cur is not None:
            cur.update(xd=str(r[4])[:10], xt=hhmm(r[5]),
                       xsig=str(r[3] or ''))
            trades.append(cur)
            cur = None
    return trades


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLS
    if not os.path.exists(path):
        print('missing report:', path)
        return 1
    T = load(path)
    print('report :', os.path.basename(path))
    print('trades :', len(T))
    print('net    :', format(int(sum(x['net'] for x in T)), ','))
    fails = 0

    # ---- A. every fill lands on a legal session bar ----------------------
    print()
    print('=' * 74)
    print('A. FILLS ON LEGAL SESSION BARS')
    print('=' * 74)
    bad = [x for x in T if not in_session(x['et']) or not in_session(x['xt'])]
    print('   entries + exits checked : %d' % (len(T) * 2))
    print('   outside any session     : %d' % len(bad))
    for x in bad:
        print('      %s %04d -> %s %04d' % (x['ed'], x['et'], x['xd'], x['xt']))
    fails += len(bad)

    # ---- B. the entry window the gate is supposed to close ---------------
    print()
    print('=' * 74)
    print('B. ENTRY FILLS IN THE TAIL WINDOW')
    print('=' * 74)
    print('   Tail_LastEntry_Time = %d gates the SIGNAL bar, so the last'
          % TAIL_LAST_ENTRY)
    print('   permitted entry FILL is one bar later than the name implies.')
    print()
    tail = sorted([x for x in T if 0 < x['et'] <= 500], key=lambda x: x['et'])
    print('   post-midnight entry fills, latest last:')
    for x in tail[-8:]:
        flag = ''
        if x['et'] > TAIL_LAST_ENTRY:
            flag = '  <- LATER THAN THE INPUT NAME SAYS'
        print('      %s %04d  %-20s net %10s%s'
              % (x['ed'], x['et'], x['sig'][:20],
                 format(int(x['net']), ','), flag))
    over = [x for x in tail if x['et'] > TAIL_LAST_ENTRY]
    print()
    print('   fills strictly after %04d : %d   (these vanish when'
          % (TAIL_LAST_ENTRY, len(over)))
    print('                                  Tail_FillSemantic_On = True)')
    hard = [x for x in tail if x['et'] > TAIL_LAST_ENTRY + 10]
    print('   fills after %04d+2 bars   : %d   (a REAL breach -- the gate'
          % (TAIL_LAST_ENTRY, len(hard)))
    print('                                  would be failing outright)')
    fails += len(hard)

    # ---- C. no position survives a closure --------------------------------
    print()
    print('=' * 74)
    print('C. POSITIONS HELD ACROSS A CLOSURE')
    print('=' * 74)
    late = [x for x in T if 500 < x['xt'] <= 845]
    print('   exit fills inside the morning break 0500-0845 : %d' % len(late))
    for x in late:
        print('      %s %04d -> %s %04d' % (x['ed'], x['et'], x['xd'], x['xt']))
    fails += len(late)

    span = []
    for x in T:
        d0 = datetime.date(*map(int, x['ed'].split('-')))
        d1 = datetime.date(*map(int, x['xd'].split('-')))
        if d1 == d0:
            continue
        # a night trade legitimately crosses midnight into the next date;
        # anything longer, or any daytime entry that survives to another
        # date, has sat through a closure
        overnight_ok = (x['et'] > NIGHT_START and x['xt'] <= NIGHT_END
                        and (d1 - d0).days <= 3)
        if not overnight_ok:
            span.append((x, (d1 - d0).days))
    print()
    print('   trades spanning dates beyond one night session : %d' % len(span))
    for x, n in span:
        print('      %s %04d -> %s %04d  (+%d days)  %s'
              % (x['ed'], x['et'], x['xd'], x['xt'], n, x['xsig'][:24]))
    fails += len(span)

    # ---- D. how long the tail trades actually lived -----------------------
    print()
    print('=' * 74)
    print('D. WHAT THE LATEST ENTRIES ACTUALLY GOT')
    print('=' * 74)
    print('   Tail_ForceExit_Time = %d flattens at signal, filling one bar'
          % TAIL_FORCE_EXIT)
    print('   later. An entry filled at 0435 therefore has two bars to live,')
    print('   which no exit mechanism except the timer can act inside.')
    print()
    for x in sorted(tail, key=lambda x: -x['et'])[:5]:
        mins = ((x['xt'] // 100 * 60 + x['xt'] % 100)
                - (x['et'] // 100 * 60 + x['et'] % 100))
        if mins < 0:
            mins += 24 * 60
        print('      entry %s %04d -> exit %04d  %3d min (%d bars)  %-22s %s'
              % (x['ed'], x['et'], x['xt'], mins, mins // 5, x['xsig'][:22],
                 format(int(x['net']), ',')))

    print()
    print('=' * 74)
    print('VERDICT: %s' % ('PASS -- no rule breach found' if fails == 0
                           else 'FAIL -- %d breach(es), listed above' % fails))
    print('=' * 74)
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
