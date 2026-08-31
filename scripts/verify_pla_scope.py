# -*- coding: utf-8 -*-
"""Check WHERE a counter lives, not just what it computes.

Build 260870 shipped P18 / P57 / P17 with the right arithmetic in the wrong
place.  The tests sat after the `for v_k = 1 to 2` pivot-push loop instead of
inside it, so they ran once per BAR rather than once per PUSH.  A pivot arrives
every 2.8 bars and the chain does not change in between, so every formation was
recounted until the next pivot: P18 read 16,565 against a true 6,352.

The Python reference that was supposed to catch this returned 6,352 exactly --
because the port put the test inside the loop while the .pla put it outside.
It verified the ALGORITHM and never the PLACEMENT.  A simulation written from
the intent cannot detect that the code disagrees with the intent.

So this checks the one thing that port structurally cannot: that each counter
sits at the scope its meaning requires.

  per push   a pattern is a fact about the pivot chain, so it is settled the
             moment a pivot enters and must be counted there.  An outside bar
             pushes twice, a high then a low, and both need testing -- which is
             why a "did a pivot arrive this bar" guard is not equivalent.

             The block that means this is `if v_Push`, NOT the `for v_k` loop
             around it: the loop body runs twice per bar with or without a
             pivot.  260871 sat between the two and counted twice per bar --
             P18 37,662 against a true 6,352 -- and an earlier version of this
             checker PASSED it, because it asked the loop question instead of
             the push question.

  per bar    break and expiry are facts about price against a formed pattern,
             so they are judged every bar and belong outside the loop.

Usage:  python scripts/verify_pla_scope.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET = os.path.join('strategies', 'research', 'S16_MACrossShort',
                      'indicators', 'IND_S16S_P29.pla')
if len(sys.argv) > 1:          # a path lets the fixed build be checked against
    TARGET = sys.argv[1]       # the broken one -- a checker that cannot fail
                               # proves nothing.
PUSH = 'if v_Push then begin'   # NOT `for v_k = 1 to 2 begin`: that loop runs
                                # twice on EVERY bar whether a pivot exists or
                                # not, so "inside the loop" is a WEAKER claim
                                # than "only on a push".  Checking the weaker
                                # one passed Build 260871, which was wrong.

# 260890: SECTION 6e 的七個計數與其餘同層 -- 在 if v_Push 內、每次推入一次。
# 這支驗證器就是為了 260871 那個「每根跑兩次」的 bug 而寫的，
# 新增計數不納入清單，等於把它關掉。
# 260910: 3x3 格新增的四個計數與四個全等子集計數，同層。
PER_PUSH = ['v_Cnt11', 'v_Cnt10', 'v_Cnt08', 'v_Cnt22',
            'v_Ex53', 'v_Ex54', 'v_Ex08', 'v_Ex22',
            'v_C15', 'v_C26', 'v_C32', 'v_C56', 'v_C59', 'v_C65', 'v_C72',
            'v_Cnt29', 'v_Cnt51', 'v_Cnt52', 'v_Cnt53', 'v_Cnt54', 'v_CntForm',
            'v_Seq49', 'v_Seq50', 'v_Seq30', 'v_Seq61',
            'v_Cnt18', 'v_Cnt57', 'v_Cnt17',
            'v_Cnt28', 'v_Cnt64', 'v_Cnt55']
PER_BAR = ['v_CntExp', 'v_CntDn', 'v_CntUp']


def strip_noise(lines):
    """Blank out { } comments and "..." strings, keeping line numbers intact."""
    out, in_c = [], False
    for ln in lines:
        buf, in_s = [], False
        for ch in ln:
            if in_c:
                buf.append(' ')
                if ch == '}':
                    in_c = False
            elif in_s:
                buf.append(' ')
                if ch == '"':
                    in_s = False
            elif ch == '{':
                in_c = True
                buf.append(' ')
            elif ch == '"':
                in_s = True
                buf.append(' ')
            else:
                buf.append(ch)
        out.append(''.join(buf))
    return out


def loop_span(clean):
    """First and last line of the push block, matching begin against end."""
    start = next(i for i, x in enumerate(clean) if x.strip() == PUSH)
    depth = 0
    for i in range(start, len(clean)):
        for w in re.findall(r'\b(begin|end)\b', clean[i]):
            depth += 1 if w == 'begin' else -1
        if depth == 0:
            return start, i
    raise SystemExit('  FAIL  push loop never closes')


def main():
    lines = open(TARGET, encoding='utf-8').read().split('\n')
    clean = strip_noise(lines)
    lo, hi = loop_span(clean)
    print('=' * 78)
    print('  %s' % TARGET)
    print('  if v_Push  %d .. %d' % (lo + 1, hi + 1))
    print('-' * 78)

    bad = 0
    for want, names in (('per push', PER_PUSH), ('per bar', PER_BAR)):
        for n in names:
            pat = re.compile(r'\b%s\s*=\s*%s\s*\+\s*1\b' % (n, n))
            hits = [i for i, x in enumerate(clean) if pat.search(x)]
            if not hits:
                print('  MISS   %-10s  %s 沒有遞增' % (n, want))
                bad += 1
                continue
            for i in hits:
                inside = lo < i < hi
                ok = inside if want == 'per push' else not inside
                if not ok:
                    bad += 1
                print('  %s  %-10s  line %-5d  %s  (要求 %s)'
                      % ('ok   ' if ok else 'FAIL ', n, i + 1,
                         '推入區塊內' if inside else '區塊外', want))

    print('-' * 78)
    if bad:
        print('  %d 個計數放在錯誤的 scope' % bad)
    else:
        print('  全部 %d 個計數的 scope 正確'
              % (len(PER_PUSH) + len(PER_BAR)))
    print('=' * 78)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
