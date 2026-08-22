# -*- coding: ascii -*-
"""
S16_S K-bar pattern selector -- third-party verification harness.

The point of this file is that it does NOT retype the pattern conditions.
It PARSES them out of the shipped .pla and mechanically transpiles the
PowerLanguage boolean expressions into Python. Retyping them by hand would
only reproduce the same reading twice; parsing the shipped file means the
thing under test is the thing that runs in MC12.

Four tests:
  T1 positive   each pattern fires on a hand-built bar sequence taken from
                the SPEC TEXT, not from the code
  T2 clause     every top-level AND clause of every condition is True on
                that pattern's own fixture -- proves no clause is vacuous
  T3 cross      full 28x28 matrix: which patterns fire on which fixtures.
                catches conditions that are broader than they look
  T4 sensitivity  perturb one price by one tick and confirm the pattern
                stops firing -- proves the fixture sits on the boundary the
                condition claims to test

Run:  python scripts/research/s16s_kbar_unittest.py
"""
import io, os, re, sys, hashlib, itertools

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='replace')

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLA = os.path.join(REPO, 'strategies', 'research', 'S16_MACrossShort',
                   'S16_S_MACrossShort_v1.26.0.pla')

# ---------------------------------------------------------------- 1. parse

def load_source():
    raw = open(PLA, 'rb').read()
    print('source   %s' % os.path.relpath(PLA, REPO))
    print('bytes    %d' % len(raw))
    print('md5      %s' % hashlib.md5(raw).hexdigest())
    return raw.decode('ascii')


def extract_section(src):
    a = src.index('{ SECTION 8.6 - K-BAR PATTERN SELECTOR')
    b = src.index('{ SECTION 8.7 -')
    return src[a:b]


def strip_comments(t):
    return re.sub(r'\{[^{}]*\}', ' ', t)


def parse_inputs(src):
    """Pull the KB_Pat_* threshold defaults straight out of the inputs block."""
    d = {}
    for m in re.finditer(r'^\s*(KB_Pat_\w+)\s*\(\s*([-\d.]+)\s*\)', src, re.M):
        d[m.group(1)] = float(m.group(2))
    return d


def parse_rules(sec):
    """Every 'if v_KB_Code = 0 and <cond> then v_KB_Code = N;' in source order."""
    pat = re.compile(
        r'if\s+v_KB_Code\s*=\s*0\s+and\s+(.*?)\s+then\s*\n?\s*v_KB_Code\s*=\s*(\d+)\s*;',
        re.S)
    out = []
    for m in pat.finditer(sec):
        out.append((int(m.group(2)), ' '.join(m.group(1).split())))
    return out


def parse_helpers(sec):
    """Helper assignments v_KB_xx = <expr>;  in source order."""
    pat = re.compile(r'^\s*(v_KB_[A-Z]\d)\s*=\s*(.+?);', re.S | re.M)
    out = []
    for m in pat.finditer(sec):
        out.append((m.group(1), ' '.join(m.group(2).split())))
    return out

# ----------------------------------------------------------- 2. transpile

def transpile(expr):
    """PowerLanguage boolean/arithmetic expression -> Python source."""
    e = expr
    e = e.replace('>=', '@GE@').replace('<=', '@LE@').replace('<>', '@NE@')
    e = re.sub(r'\bAbsValue\s*\(', 'abs(', e)
    e = re.sub(r'\bMaxList\s*\(', 'max(', e)
    e = re.sub(r'\bMinList\s*\(', 'min(', e)
    # bare O H L C -> index 0
    e = re.sub(r'\b([OHLC])\b(?!\s*\[)', r'\1[0]', e)
    e = re.sub(r'=\s*True\b', '== True', e)
    e = re.sub(r'=\s*False\b', '== False', e)
    e = re.sub(r'(?<![<>!=])=(?!=)', '==', e)
    e = e.replace('@GE@', '>=').replace('@LE@', '<=').replace('@NE@', '!=')
    return e


def split_top_and(expr):
    """Split on top-level ' and ' (depth 0 only)."""
    out, depth, cur, i = [], 0, [], 0
    toks = re.split(r'(\(|\)|\band\b)', expr)
    for t in toks:
        if t == '(':
            depth += 1; cur.append(t)
        elif t == ')':
            depth -= 1; cur.append(t)
        elif t == 'and' and depth == 0:
            out.append(''.join(cur).strip()); cur = []
        else:
            cur.append(t)
    if ''.join(cur).strip():
        out.append(''.join(cur).strip())
    return [c for c in out if c]

# --------------------------------------------------------------- 3. engine

class Env(object):
    """Holds O/H/L/C arrays (index 0 = current) and evaluates the helpers."""

    def __init__(self, bars, thresholds):
        # bars: oldest -> newest list of (O,H,L,C); reverse for [0]=current
        b = list(reversed(bars))
        self.O = [x[0] for x in b]
        self.H = [x[1] for x in b]
        self.L = [x[2] for x in b]
        self.C = [x[3] for x in b]
        self.n = len(b)
        self.g = dict(thresholds)
        self.g.update(dict(O=self.O, H=self.H, L=self.L, C=self.C,
                           abs=abs, max=max, min=min, True_=True))
        self.g['v_Bars_In_Sess'] = self.n

    def run_helpers(self, helpers):
        for name, expr in helpers:
            try:
                self.g[name] = eval(transpile(expr), {'__builtins__': {}}, self.g)
            except (IndexError, KeyError, ZeroDivisionError, TypeError):
                self.g[name] = None

    def ev(self, expr):
        try:
            return eval(transpile(expr), {'__builtins__': {}}, self.g)
        except (IndexError, KeyError, ZeroDivisionError, TypeError):
            return None

# ------------------------------------------------------------- 4. fixtures
# Built from the SPEC TEXT in docs/research/S16S_kbar_pattern_spec_20260816.md,
# deliberately NOT from the .pla, so a disagreement between the two shows up
# as a failing test rather than as agreement by construction.
#
# bars are (O, H, L, C) oldest -> newest; the pattern completes on the last.
# break_ is (bar_index_from_oldest, field, delta) -- one tick that should kill it.

FIX = [
 (1,  'A01 bearish engulfing',   [(100,111, 99,110),(112,113, 97, 98)],            (1,'O',-3)),
 (2,  'A05 bearish harami',      [(100,121, 99,120),(115,116,104,105)],            (0,'O',10)),
 (3,  'A07 bearish harami cross',[(100,121, 99,120),(110,112,108,110)],            (1,'C', 3)),
 (4,  'A18 tweezer top',         [(100,112, 99,110),(109,112,100,101)],            (1,'H', 1)),
 (5,  'A20 matching high',       [(100,121, 99,120),(110,121,109,120)],            (1,'C', 1)),
 (6,  'B25 three black crows',   [(120,121, 99,100),(115,116, 94, 95),(110,111, 89, 90)], (2,'O',-25)),
 (7,  'B27 three inside down',   [(100,121, 99,120),(115,116,104,105),(106,107, 99,100)], (2,'C', 8)),
 (8,  'B29 three outside down',  [(100,111, 99,110),(112,113, 97, 98),( 99,100, 94, 95)], (1,'C', 5)),
 (9,  'B34 three identical crows',[(120,121, 99,100),(100,101, 79, 80),( 80, 81, 59, 60)],(2,'O', 1)),
 (10, 'B35 advance block',       [(100,121, 99,120),(118,133,117,130),(128,140,127,134)], (2,'H',-8)),
 (11, 'B36 deliberation',        [(100,121, 99,120),(120,141,119,140),(140,146,139,145)], (2,'C',10)),
 (12, 'C41 falling three methods',
      [(120,121, 99,100),(104,109,103,108),(107,112,106,111),(110,115,109,114),(115,116, 94, 95)], (4,'C',8)),
 (13, 'C45 bearish three-line strike',
      [(100,111, 99,110),(105,116,104,115),(110,121,109,120),(122,123, 97, 98)],    (3,'C',5)),
 (14, 'D47 bearish hikkake',
      [(100,115, 95,110),(105,112, 98,108),(110,120,105,118),(117,119,110,112),(111,113, 95, 96)], (1,'H', 5)),
 (15, 'D48 descending hawk',   [(100,121, 99,120),(105,116,104,115)],            (0,'C',-10)),

 (16, 'A02 bullish engulfing',   [(110,111, 99,100),( 98,113, 97,112)],            (1,'O', 3)),
 (17, 'A06 bullish harami',      [(120,121, 99,100),(105,116,104,115)],            (0,'C',10)),
 (18, 'A08 bullish harami cross',[(120,121, 99,100),(110,112,108,110)],            (1,'C', 3)),
 (19, 'A19 tweezer bottom',      [(110,111, 98,100),(101,110, 98,109)],            (1,'L', 1)),
 (20, 'A21 matching low',        [(120,121, 99,100),(110,111, 99,100)],            (1,'C', 1)),
 (21, 'B26 three white soldiers',[(100,121, 99,120),(105,126,104,125),(110,131,109,130)], (2,'O',20)),
 (22, 'B28 three inside up',     [(120,121, 99,100),(105,116,104,115),(114,121,113,120)], (2,'C',-6)),
 (23, 'B30 three outside up',    [(110,111, 99,100),( 98,113, 97,112),(113,119,112,118)], (1,'C',-5)),
 (24, 'B37 three stars in south',[(120,121, 90,100),(115,116, 95,105),(112,114,100,108)], (1,'L',-6)),
 (25, 'B38 unique three river bottom',
      [(120,121, 99,100),(115,116, 95,105),(100,104, 99,103)],                     (2,'C', 4)),
 (26, 'C42 rising three methods',
      [(100,121, 99,120),(116,117,111,112),(113,114,108,109),(110,111,105,106),(105,126,104,125)], (4,'C',-6)),
 (27, 'C43 ladder bottom',
      [(120,121, 99,100),(115,116, 94, 95),(110,111, 89, 90),( 92,100, 87, 88),( 95,106, 94,105)], (4,'O',-4)),
 (28, 'C46 bullish three-line strike',
      [(110,111, 99,100),(105,106, 94, 95),(100,101, 89, 90),( 88,113, 87,112)],   (3,'C',-3)),

 (29, 'A09 inside bar',          [(100,115, 95,110),(105,112, 98,108)],            (1,'H', 4)),
 (30, 'A10 outside bar',         [(105,112, 98,108),(100,115, 95,110)],            (1,'H',-4)),
]
FIELD = {'O': 0, 'H': 1, 'L': 2, 'C': 3}


def perturb(bars, spec):
    i, f, d = spec
    out = [list(b) for b in bars]
    out[i][FIELD[f]] += d
    return [tuple(b) for b in out]


# ------------------------------------------------------------------- main

def main():
    src = load_source()
    sec = strip_comments(extract_section(src))
    thr = parse_inputs(src)
    rules = parse_rules(sec)
    helpers = parse_helpers(sec)
    print('thresholds parsed from inputs block: %s'
          % ', '.join('%s=%g' % (k, v) for k, v in sorted(thr.items())))
    print('rules parsed from SECTION 8.6:      %d' % len(rules))
    print('helper assignments parsed:          %d' % len(helpers))
    print()

    codes = [c for c, _ in rules]
    assert codes == list(range(1, 31)), 'codes not 1..28 in order: %s' % codes
    assert [c for c, _, _, _ in FIX] == list(range(1, 31)), 'fixture codes out of order'
    COND = dict(rules)

    def fires(bars, code):
        e = Env(bars, thr)
        e.run_helpers(helpers)
        return e.ev(COND[code])

    fail = 0

    print('=' * 78)
    print(' T1 positive firing   +   T2 every top-level clause is load-bearing')
    print('=' * 78)
    for code, name, bars, _ in FIX:
        e = Env(bars, thr)
        e.run_helpers(helpers)
        whole = e.ev(COND[code])
        clauses = split_top_and(COND[code])
        bad = [c for c in clauses if e.ev(c) is not True]
        ok = (whole is True) and not bad
        if not ok:
            fail += 1
        print('  %-4s %-2d %-34s  fires=%-5s  clauses %d/%d'
              % ('OK' if ok else 'FAIL', code, name,
                 whole, len(clauses) - len(bad), len(clauses)))
        for c in bad:
            print('           clause not True: %s  -> %r' % (c, e.ev(c)))

    print()
    print('=' * 78)
    print(' T4 one-tick sensitivity -- perturbed fixture must STOP firing')
    print('=' * 78)
    for code, name, bars, br in FIX:
        after = fires(perturb(bars, br), code)
        ok = (after is not True)
        if not ok:
            fail += 1
        print('  %-4s %-2d %-34s  bar[%d].%s %+d  ->  fires=%s'
              % ('OK' if ok else 'FAIL', code, name, br[0], br[1], br[2], after))

    print()
    print('=' * 78)
    print(' T3 cross matrix -- which OTHER patterns fire on each fixture')
    print('=' * 78)
    overlaps = []
    for code, name, bars, _ in FIX:
        hit = [c for c in range(1, 31) if fires(bars, c) is True]
        others = [c for c in hit if c != code]
        if others:
            overlaps.append((code, name, others))
        print('  %-2d %-34s  hits: %s' % (code, name, ' '.join(str(h) for h in hit)))

    # -------- T5 priority masking --------
    # The gate only asks whether the code is non-zero, so masking cannot change
    # a block/allow decision. It CAN silently mislabel which pattern did it,
    # and that is what the v_KB_Code diagnostic is for.
    print()
    print('=' * 78)
    print(' T5 priority masking -- is this code the one REPORTED on its own fixture?')
    print('=' * 78)
    GROUP = {}
    for c in range(1, 31):
        GROUP[c] = 'SUP' if c <= 13 else ('OPP' if c <= 26 else 'NEU')
    masked = []
    for code, name, bars, _ in FIX:
        hit = [c for c in range(1, 31) if fires(bars, c) is True]
        # cascade order is group block order (SUP, OPP, NEU) then code order
        rank = {'SUP': 0, 'OPP': 1, 'NEU': 2}
        winner = sorted(hit, key=lambda c: (rank[GROUP[c]], c))[0]
        ok = (winner == code)
        if not ok:
            masked.append((code, name, winner))
        print('  %-4s %-2d %-34s  reported as %-2d %s'
              % ('OK' if ok else 'MASK', code, name, winner,
                 '' if ok else '<-- ' + dict((c, n) for c, n, _, _ in FIX)[winner]))

    print()
    print('=' * 78)
    print(' RESULT')
    print('=' * 78)
    n1 = sum(1 for c, n, b, _ in FIX if fires(b, c) is True)
    n4 = sum(1 for c, n, b, br in FIX if fires(perturb(b, br), c) is not True)
    print('  T1  %d/30 patterns fire on their own fixture' % n1)
    print('  T4  %d/30 die on a one-tick perturbation' % n4)
    print('  T3  %d fixtures also trigger another pattern' % len(overlaps))
    print('  T5  %d patterns are MASKED -- they fire but a lower code reports first'
          % len(masked))
    if masked:
        print()
        print('      masked on their canonical fixture. Whether the masking is UNIVERSAL')
        print('      needs the real-data census -- none of these conditions IMPLIES')
        print('      the masking one, so a differently-shaped instance may report itself.')
        for c, n, w in masked:
            print('        %-2d %-34s  reported as %d instead' % (c, n, w))
    print()
    print('  FAILURES: %d' % fail)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
