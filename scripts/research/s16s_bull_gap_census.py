# -*- coding: utf-8 -*-
"""
多頭母體的三個缺口 -- 它們到底出現多少次，會不會動到 172 筆錨點？

問題很具體，因為 R1（進場那根帶多頭結構就不下單）是**常駐、沒有開關**的。
新增任何多頭型態都會直接改變錨點，這不是加開關就能迴避的事，必須先量。

三個缺口的判定式是既有空方型態的鏡像，逐條對照 .pla 寫出，零自由參數：

  多頭 Hikkake  D47 的鏡像，五根。內含線 -> 向**下**假突破 -> 向上穿越內含線高點
  家鴿          D48 下降之鷹的鏡像，兩根。兩根都黑，第二根實體被前根包含且更小
  三明治        Nison 多方獨有，三根。黑/白/黑，第一與第三**完全相同**收盤

沒有損益欄。次數而已。
"""
import io, os, re, sys, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from s16s_kbar_unittest import (load_source, extract_section, strip_comments,
                                parse_inputs, parse_rules, parse_helpers, transpile)
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

CACHE = os.path.join(HERE, 's16s_5min.csv')

# body top / bottom / size helpers, same names the .pla uses
NEW = {
    # A -- exact mirror of the shipped D47, which tests the EXTREME only
    'BULL_HIKKAKE': (5, "( H[3] <= H[4] ) and ( L[3] >= L[4] ) "
                        "and ( H[2] < H[3] ) and ( L[2] < L[3] ) "
                        "and ( H > H[3] )"),
    # B -- the same shape but requiring a CLOSE beyond the inside bar's high.
    # 2026-04-08 21:55 fires variant A on a bar that opened 35335 and closed
    # 35212 -- 123 points DOWN. Calling that bullish, and flattening a short
    # on it, is indefensible. D47 has the same hole on its own side.
    'BULL_HIKKAKE_C': (5, "( H[3] <= H[4] ) and ( L[3] >= L[4] ) "
                          "and ( H[2] < H[3] ) and ( L[2] < L[3] ) "
                          "and ( C > H[3] )"),
    'STICK_SANDWICH_C': (3, "( C[2] < O[2] ) and ( C[1] > O[1] ) and ( C < O ) "
                            "and ( C = C[2] ) and ( C[1] > C[2] )"),
    'HOMING_PIGEON': (2, "( C[1] < O[1] ) and ( C < O ) "
                         "and ( v_KB_T0 <= O[1] ) and ( v_KB_M0 >= C[1] ) "
                         "and ( v_KB_B0 < v_KB_B1 )"),
    'STICK_SANDWICH': (3, "( C[2] < O[2] ) and ( C[1] > O[1] ) and ( C < O ) "
                          "and ( C = C[2] ) and ( C[1] > C[2] )"),
}
BARS_NEEDED = {'BULL_HIKKAKE': 5, 'BULL_HIKKAKE_C': 5, 'HOMING_PIGEON': 2,
               'STICK_SANDWICH': 3, 'STICK_SANDWICH_C': 3}
# variant B is the one measured for the anchor; A is shown for contrast
VARIANT_B = ('BULL_HIKKAKE_C',)   # 三明治完成棒依定義為黑,不進出場集合


def main():
    src = load_source()
    sec = strip_comments(extract_section(src))
    inputs = parse_inputs(src)          # the inputs block sits OUTSIDE 8.7
    # slope gate defaults, parsed the same way and never retyped
    for nm in ('MinSlope_Rate',):
        m = re.search(r'^\s*%s\s*\(\s*([-\d.]+)\s*\)' % nm, src, re.M)
        assert m, '%s not found in inputs' % nm
        inputs[nm] = float(m.group(1))
    helpers = parse_helpers(sec)
    rules = parse_rules(sec)
    assert [c for c, _ in rules] == list(range(1, 31)), 'cascade damaged'

    rows = list(csv.DictReader(open(CACHE, encoding='utf-8')))
    print('bars %d   %s -> %s' % (len(rows), rows[0]['ymd'], rows[-1]['ymd']))

    O = [float(r['open']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    SESS = [int(r['bars_in_sess']) for r in rows]
    FAST = [float(r['zlema_f']) for r in rows]
    SLOW = [float(r['zlema_s']) for r in rows]

    hcode = [compile(transpile(e), '<h>', 'eval') for _, e in helpers]
    hname = [n for n, _ in helpers]
    ncode = dict((k, compile(transpile(v[1]), '<n>', 'eval')) for k, v in NEW.items())
    rcode = [(c, compile(transpile(e), '<r>', 'eval')) for c, e in rules]

    def ser(a, i):
        return _S(a, i)

    cnt = collections.Counter()
    which = {}
    bull_now = [False] * len(rows)
    bull3_now = [False] * len(rows)
    bull3_old = [False] * len(rows)
    for i in range(5, len(rows)):
        if SESS[i] < 2:
            continue
        g = {'O': _S(O, i), 'H': _S(H, i), 'L': _S(L, i), 'C': _S(C, i),
             'v_Bars_In_Sess': SESS[i],
             '__builtins__': {'max': max, 'min': min, 'abs': abs}}
        for k, v in list(inputs.items()):
            g[k] = v
        for nm, cd in zip(hname, hcode):
            g[nm] = eval(cd, g)
        # existing cascade: what does this bar report, and is it bullish?
        code = 0
        for c, cd in rcode:
            need = 5 if c in (12, 14, 26) else (4 if c in (13, 28) else
                                                (3 if 6 <= c <= 11 or 21 <= c <= 27 else 2))
            if SESS[i] < need:
                continue
            if eval(cd, g) is True:      # no bare except -- see the C46 bug
                code = c
                break
        bull_now[i] = (16 <= code <= 28)
        b3h = _bull3_old(rcode, g, SESS[i])
        bull3_old[i] = bool(b3h)
        for c in b3h:                    # independent counts, not first-match
            cnt['B3_%d' % c] += 1
            if C[i] > O[i]:
                cnt['B3W_%d' % c] += 1
        for k, cd in ncode.items():
            if SESS[i] < BARS_NEEDED[k]:
                continue
            if eval(cd, g) is True:
                cnt[k] += 1
                if BARS_NEEDED[k] >= 3 and k in VARIANT_B:
                    bull3_now[i] = True
                which[i] = which.get(i, '') + k + ' '
                if k in ('BULL_HIKKAKE', 'STICK_SANDWICH') and C[i] < O[i]:
                    cnt[k + '_BLACKBAR'] += 1
                if k == 'HOMING_PIGEON' or BARS_NEEDED[k] >= 3:
                    cnt[k + '_BULLSTATE'] += (FAST[i] < SLOW[i])

    print()
    print('=' * 74)
    print(' 1. 三個缺口在 %d 根 K 棒上出現幾次' % len(rows))
    print('=' * 74)
    for k in NEW:
        n = cnt[k]
        print('  %-16s %4d bars  %7d 次  %6.3f%%  (空頭狀態下 %d 次)'
              % (k, BARS_NEEDED[k], n, 100.0 * n / len(rows), cnt[k + '_BULLSTATE']))

    print()
    print('=' * 74)
    print(' 1b. 出場觸發面積 -- BullExit 讀的是 3 根以上多頭結構')
    print('=' * 74)
    b3_old = sum(1 for i in range(len(rows)) if bull3_old[i])
    b3_add = sum(1 for i in range(len(rows)) if bull3_now[i] and not bull3_old[i])
    print('  現行 8 種（代碼 21-28）        %7d 次  %5.2f%%' % (b3_old, 100.0 * b3_old / len(rows)))
    print('  加上 Hikkake + 三明治後 **新增** %7d 次  %5.2f%%' % (b3_add, 100.0 * b3_add / len(rows)))
    print('  合計                           %7d 次  %5.2f%%  (擴大 %.0f%%)'
          % (b3_old + b3_add, 100.0 * (b3_old + b3_add) / len(rows),
             100.0 * b3_add / max(b3_old, 1)))

    print()
    print('=' * 74)
    print(' 1c. 現行 8 種的完成棒是紅是黑 -- 用戶要的是「非常強勢的反轉多頭結構」')
    print('=' * 74)
    B3N = {21: 'B26 三白兵', 22: 'B28 三內部上漲', 23: 'B30 三外部上漲',
           24: 'B37 南方三星', 25: 'B38 獨特三河床', 26: 'C42 上升三法',
           27: 'C43 梯底', 28: 'C46 三線打擊(漲)'}
    tw = tn = 0
    for c in range(21, 29):
        n, w = cnt['B3_%d' % c], cnt['B3W_%d' % c]
        tn = tn
        tw += w
        print('  %-2d %-18s %6d 次   完成棒紅 %6d (%5.1f%%)'
              % (c, B3N[c], n, w, 100.0 * w / max(n, 1)))
    tn = sum(1 for i in range(len(rows)) if bull3_old[i])
    print('  %-21s %6d 根 K 棒至少中一種（OR，非相加）' % ('合計', tn))

    # ---- 2. 錨點風險：這些型態有沒有落在實際進場訊號棒上 ----
    print()
    print('=' * 74)
    print(' 2. 錨點風險 -- 有沒有落在「死叉 + 斜率」的進場訊號棒上')
    print('=' * 74)
    # transcribed from the .pla, lines 677-678 and 796-807:
    #   v_Death_Cross = fast[1] >= slow[1] and fast < slow
    #   v_Slope_Rate  = ((C[1] - C) / C * 100) / elapsed_minutes
    #   v_Slope_Pass  = v_Slope_Rate > MinSlope_Rate
    thr = inputs['MinSlope_Rate']
    MIN = [int(r['hhmm'][:2]) * 60 + int(r['hhmm'][2:]) for r in rows]
    dx = veto_old = veto_new = 0
    hits = collections.Counter()
    for i in range(5, len(rows)):
        if SESS[i] < 2:
            continue
        if not (FAST[i] < SLOW[i] and FAST[i - 1] >= SLOW[i - 1]):
            continue
        el = MIN[i] - MIN[i - 1]
        if el <= 0:
            el += 1440
        if el <= 0 or C[i] == 0:
            continue
        if not (((C[i - 1] - C[i]) / C[i] * 100.0) / el > thr):
            continue
        dx += 1
        if bull_now[i]:
            veto_old += 1
        elif bull3_now[i]:
            veto_new += 1
            hits[i] = 1
            print('    %s %s   %s  O%.0f H%.0f L%.0f C%.0f'
                  % (rows[i]['ymd'], rows[i]['hhmm'], which.get(i, '?'),
                     O[i], H[i], L[i], C[i]))
    print('  死叉 + 斜率通過的訊號棒            %d' % dx)
    print('  其中現行 R1 已否決（代碼 16-28）    %d' % veto_old)
    print('  新增三型態會**額外**否決            %d   <-- 這個數字就是錨點位移'
          % veto_new)
    if veto_new == 0:
        print()
        print('  => 錨點不動。三個型態可以直接補上，172 筆 / 2,265,200 不受影響。')
    else:
        print()
        print('  => 錨點會動 %d 筆。必須加開關，預設關閉。' % veto_new)
    print()
    print('  參考：極值版在**黑棒**上觸發的次數  Hikkake %d / %d，三明治 %d / %d'
          % (cnt['BULL_HIKKAKE_BLACKBAR'], cnt['BULL_HIKKAKE'],
             cnt['STICK_SANDWICH_BLACKBAR'], cnt['STICK_SANDWICH']))
    return 0


def _bull3_old(rcode, g, sess):
    hit = []
    """Does ANY of codes 21-28 fire on this bar, masking aside? This is what
    v_KB_Bull3 reads in the .pla, so the census has to read it the same way."""
    for c, cd in rcode:
        if not (21 <= c <= 28):
            continue
        need = 5 if c == 26 else (4 if c == 28 else 3)
        if sess < need:
            continue
        if eval(cd, g) is True:
            hit.append(c)
    return hit


class _S(object):
    """PowerLanguage series indexing: X[n] is n bars ago."""
    __slots__ = ('a', 'i')

    def __init__(self, a, i):
        self.a = a
        self.i = i

    def __getitem__(self, n):
        return self.a[self.i - n]

    def __lt__(self, o):
        return self.a[self.i] < o

    def __gt__(self, o):
        return self.a[self.i] > o

    def __le__(self, o):
        return self.a[self.i] <= o

    def __ge__(self, o):
        return self.a[self.i] >= o

    def __eq__(self, o):
        return self.a[self.i] == o

    def __ne__(self, o):
        return self.a[self.i] != o

    def __sub__(self, o):
        return self.a[self.i] - o

    def __rsub__(self, o):
        return o - self.a[self.i]

    def __add__(self, o):
        return self.a[self.i] + o

    def __radd__(self, o):
        return o + self.a[self.i]

    def __truediv__(self, o):
        return self.a[self.i] / o

    def __mul__(self, o):
        return self.a[self.i] * o

    def __float__(self):
        return float(self.a[self.i])


if __name__ == '__main__':
    sys.exit(main())
