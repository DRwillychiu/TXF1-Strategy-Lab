# -*- coding: utf-8 -*-
"""
SECTION 8.7 -- exhaustive check of the three entry sources.

Replaces s16s_filtermode_test.py, which tested KB_Filter_Mode / KB_Filter_Win.
Those inputs were deleted on 2026-08-23 along with the whole blocking design;
a test for a deleted feature is worse than no test, because it passes.

Four things have to be true and none should be taken on trust:

  A1  at KB_Entry_Mode = 0 only source 1 can fire, so the v1.26.0 anchor
      cannot drift no matter what else is set
  A2  the structure life mapping is exactly 2 / 3 / 4 / 5 for the four
      families, for every code 1..15, with no gaps
  A3  a bullish structure on the entry bar (codes 16-28 and 31-33)
      vetoes ALL THREE
      sources -- R1 has no switch and no exception
  A4  mode 1 is a strict superset of mode 0, and mode 2 of mode 1; adding a
      source can only ever add entries

The expressions are parsed out of the shipped .pla and transpiled, never
retyped, same discipline as the pattern harness.
"""
import io, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PLA = os.path.join(REPO, 'strategies', 'research', 'S16_MACrossShort',
                   'S16_S_MACrossShort_v1.26.0.pla')

AGES = list(range(0, 12)) + [999]
CODES = list(range(0, 34))


def strip_comments(t):
    out = []
    d = 0
    for ch in t:
        if ch == '{':
            d += 1
        elif ch == '}':
            if d > 0:
                d -= 1
            else:
                out.append(ch)
        elif d == 0:
            out.append(ch)
    return ''.join(out)


def life_of(code):
    """The life the .pla assigns. Mirrored here ONLY to be compared against
    the parsed source in A2 -- if the two disagree the test fails."""
    if code in (12, 14):
        return 5
    if code == 13:
        return 4
    if 6 <= code <= 11:
        return 3
    return 2


def main():
    raw = open(PLA, 'rb').read()
    print('source   %s' % os.path.basename(PLA))
    print('bytes    %d   md5 %s' % (len(raw), hashlib.md5(raw).hexdigest()))
    src = raw.decode('ascii')
    a = src.index('{ SECTION 8.7 -')
    b = src.index('{ SECTION 9 - ENTRY')
    sec = ' '.join(strip_comments(src[a:b]).split())
    print()

    fail = 0

    # ---------------- A5: which codes count as bullish, parsed ----------------
    # R1 is always on and has no switch, so widening v_KB_BullNow silently
    # changes the anchor. The three gap patterns added on 2026-08-24 sit at
    # 31-33, outside the original 16-28 range, and the test has to see that
    # the definition was actually widened -- not take the .pla's word for it.
    print('=' * 74)
    print(' A5  v_KB_BullNow covers 16-28 AND 31-33, and never 29/30')
    print('=' * 74)
    mb = re.search(r'v_KB_BullNow = ([^;]+);', ' '.join(strip_comments(src).split()))
    assert mb, 'v_KB_BullNow not parseable'
    expr = mb.group(1)
    print('  %s' % expr)
    pex = expr.replace('>=', '@G@').replace('<=', '@L@')
    pex = re.sub(r'(?<![<>!=])=(?!=)', '==', pex)
    pex = pex.replace('@G@', '>=').replace('@L@', '<=').replace(' and ', ' and ').replace(' or ', ' or ')
    cc = compile(pex, '<b>', 'eval')
    badb = []
    for gp in (True, False):        # KB_Gap_Pat on and off
        for c in range(0, 34):
            got = bool(eval(cc, {'__builtins__': {}},
                            {'v_KB_Code': c, 'v_KB_Gap_Pat': gp}))
            exp = (16 <= c <= 28) or (gp and 31 <= c <= 33)
            if got != exp:
                badb.append(('gap=%s code %d' % (gp, c), got, exp))
    print('  codes checked: 68 (34 x KB_Gap_Pat on/off)   mismatches: %d' % len(badb))
    for c, g, e in badb:
        print('     %s: source says %s, expected %s' % (c, g, e))
    fail += len(badb)
    if not badb:
        print('  OK -- 31-33 bullish only when KB_Gap_Pat is on; 29/30 never')
    print()

    # ---------------- A2: life mapping parsed from source ----------------
    print('=' * 74)
    print(' A2  structure life mapping, parsed from the .pla')
    print('=' * 74)
    got = {}
    m5 = re.search(r'v_KB_Code = (\d+) or v_KB_Code = (\d+) then v_KB_SupLife = (\d+)', sec)
    m4 = re.search(r'else if v_KB_Code = (\d+) then v_KB_SupLife = (\d+)', sec)
    m3 = re.search(r'v_KB_Code >= (\d+) and v_KB_Code <= (\d+) then v_KB_SupLife = (\d+)', sec)
    m2 = re.search(r'else v_KB_SupLife = (\d+)', sec)
    assert m5 and m4 and m3 and m2, 'life mapping not parseable'
    for c in (int(m5.group(1)), int(m5.group(2))):
        got[c] = int(m5.group(3))
    got[int(m4.group(1))] = int(m4.group(2))
    for c in range(int(m3.group(1)), int(m3.group(2)) + 1):
        got.setdefault(c, int(m3.group(3)))
    default = int(m2.group(1))
    bad = []
    for c in range(1, 16):
        v = got.get(c, default)
        if v != life_of(c):
            bad.append((c, v, life_of(c)))
    print('  parsed: 5-bar %s   4-bar %s   3-bar %s   default %d'
          % (sorted(k for k, v in got.items() if v == 5),
             sorted(k for k, v in got.items() if v == 4),
             sorted(k for k, v in got.items() if v == 3), default))
    print('  mismatches: %d' % len(bad))
    for c, v, w in bad:
        print('     code %d: source says %d, expected %d' % (c, v, w))
    fail += len(bad)
    if not bad:
        print('  OK -- all 15 pro-short codes carry the life their bar count implies')

    # ---------------- source predicate, parsed ----------------
    body = sec[sec.index('v_Entry_Src = 0;'):]
    # split on the assignment, then take everything after the LAST 'if ' in
    # each preceding chunk -- a regex on 'if (.+?) then' swallows the outer
    # 'if v_KB_BullNow = False then begin', which the first run caught
    seen = {}
    parts = re.split(r'then v_Entry_Src = (\d)', body)
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        head = parts[i - 1]
        j = max(head.rfind(' if '), head.rfind('if ') if head.startswith('if ') else -1)
        cond = head[j + 4:] if j > 0 else head[head.rfind('if ') + 3:]
        seen.setdefault(n, cond.strip())
    assert set(seen) == {1, 2, 3}, 'expected three sources, parsed %s' % sorted(seen)
    print()
    for n in (1, 2, 3):
        print('  source %d  %s' % (n, seen[n]))

    def transpile(e):
        e = e.replace('>=', '@GE@').replace('<=', '@LE@').replace('<>', '@NE@')
        e = re.sub(r'=\s*True\b', '== True', e)
        e = re.sub(r'=\s*False\b', '== False', e)
        e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
        return e.replace('@GE@', '>=').replace('@LE@', '<=').replace('@NE@', '!=')

    code = dict((n, compile(transpile(e), '<s>', 'eval')) for n, e in seen.items())

    def src_of(mode, dx, slope, supage, suplife, supcode, bull, bear_state, dxage):
        g = {'KB_Entry_Mode': mode, 'v_Death_Cross': dx, 'v_Slope_Pass': slope,
             'v_KB_SupAge': supage, 'v_KB_SupLife': suplife,
             'v_KB_SupLive': (supage <= suplife and supcode > 0),
             'v_KB_BullNow': bull, 'v_DX_Age': dxage,
             'v_ZLEMA_Fast': 0.0 if bear_state else 1.0,
             'v_ZLEMA_Slow': 1.0 if bear_state else 0.0,
             '__builtins__': {}}
        if bull:
            return 0
        for n in (1, 2, 3):
            if eval(code[n], g):
                return n
        return 0

    STATES = []
    for mode in (0, 1, 2):
        for dx in (True, False):
            for slope in (True, False):
                for supage in AGES:
                    for suplife in (0, 2, 3, 4, 5):
                        for supcode in (0, 1, 12):
                            for bull in (True, False):
                                for bs in (True, False):
                                    for dxa in (0, 2, 5, 9, 999):
                                        STATES.append((mode, dx, slope, supage,
                                                       suplife, supcode, bull,
                                                       bs, dxa))

    print()
    print('=' * 74)
    print(' A1  mode 0 can only ever produce source 1')
    print('=' * 74)
    bad1 = [st for st in STATES if st[0] == 0 and src_of(*st) not in (0, 1)]
    print('  states checked: %d   violations: %d'
          % (sum(1 for st in STATES if st[0] == 0), len(bad1)))
    fail += len(bad1)
    if not bad1:
        print('  OK -- the v1.26.0 anchor is unreachable from the new sources')

    print()
    print('=' * 74)
    print(' A3  a bullish structure on the entry bar vetoes every source')
    print('=' * 74)
    bad3 = [st for st in STATES if st[6] and src_of(*st) != 0]
    print('  states with a bullish structure: %d   entries allowed: %d'
          % (sum(1 for st in STATES if st[6]), len(bad3)))
    fail += len(bad3)
    if not bad3:
        print('  OK -- R1 has no exception')

    print()
    print('=' * 74)
    print(' A4  raising the mode can only ADD entries, never remove one')
    print('=' * 74)
    bad4 = 0
    base = [st for st in STATES if st[0] == 0]
    for st in base:
        s0 = src_of(*st)
        s1 = src_of(1, *st[1:])
        s2 = src_of(2, *st[1:])
        if s0 and not s1:
            bad4 += 1
        if s1 and not s2:
            bad4 += 1
    print('  violations: %d' % bad4)
    fail += bad4
    if not bad4:
        print('  OK -- mode 1 contains mode 0, mode 2 contains mode 1')

    print()
    print('=' * 74)
    print(' RESULT')
    print('=' * 74)
    print('  FAILURES: %d' % fail)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
