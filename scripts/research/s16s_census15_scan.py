# -*- coding: utf-8 -*-
"""Population census of the fifteen patterns, on the chain the INDICATOR uses.

THE FIRST VERSION USED THE WRONG CHAIN.  It merged: when two pivots of the
same type arrived in a row it replaced the last one with the more extreme,
keeping the alternation.  The .pla does not do that -- it WIPES the chain:

    if v_Chain > 0 and v_PvTyp[v_Chain - 1] = v_k then v_Chain = 0;

and 27.4% of raw pivots repeat the previous type, so the two chains are not
close.  Measured on the three patterns with exact MC12 references:

                     reset chain    merged chain    MC12 verified
    P18 triple top   6,352          16,718          6,352
    P57 measured mv  255            512             255
    P68 double top   1,365          1,560           1,365

The reset chain reproduces MC12 exactly.  Every count on the census page was
therefore computed against a chain the indicator has never used, and the cup
in particular fell from 134 instances to 7.

Counting is now done the same way the .pla runs: push by push, testing the
last N slots after every push, inside the equivalent of `if v_Push`.  One
twelve-slot chain serves every pattern -- the diamond reads its last ten, the
cup all twelve, bump-and-run its last seven.

Each definition is zero-parameter.  Two devices do the work a threshold would:

  step monotonicity   "round" versus "V" is curvature, which normally needs a
                      threshold.  Compare the SIZE OF CONSECUTIVE STEPS
                      instead: a dome decelerates into its peak and
                      accelerates out; a spike does the opposite.  Ordinal.

  the band device     min(A,B) <= C <= max(A,B).  Willy's device; the
                      tolerance comes from the pattern itself.

Every pattern is also counted on the MIRROR of the bar series -- H' = -L and
L' = -H, a true reflection rather than a relabelled chain, which is what the
first mirror attempt got wrong.  A shape whose mirror occurs as often carries
no direction.

Counts only.  No P&L column.

Run:  python scripts/research/s16s_census15_scan.py
"""
import csv
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.join('scripts', 'research')
CSV = os.path.join(HERE, 's16s_5min.csv')
OUT = os.path.join(HERE, 's16s_census15.json')
CAP = 12                       # one chain for every pattern: 12 >= 10 >= 7


def bars():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    return (rows,
            [float(r['high']) for r in rows],
            [float(r['low']) for r in rows],
            [int(r['bars_in_sess']) for r in rows])


# --------------------------------------------------------------------------
# the predicates.  each takes a slice of consecutive pivots as
# (bar, price, type) and the type the slice must start with.
# --------------------------------------------------------------------------
def dome(a, b, c, d, e):
    """Rises then falls, decelerating in and accelerating out."""
    return (a < b < c > d > e
            and (b - a) > (c - b)
            and (c - d) < (d - e))


def spike(a, b, c, d, e):
    """Rises then falls, accelerating in and decelerating out -- a peak."""
    return (a < b < c > d > e
            and (b - a) < (c - b)
            and (c - d) > (d - e))


def inband(x, p, q):
    return min(p, q) <= x <= max(p, q)


def P26(s):                                   # rounding top, 5 highs
    return dome(*[s[i][1] for i in (0, 2, 4, 6, 8)])


def P32(s):                                   # V top -- the sharp version
    return spike(*[s[i][1] for i in (0, 2, 4, 6, 8)])


def P27(s):                                   # rounding bottom, 5 lows
    return dome(*[-s[i][1] for i in (0, 2, 4, 6, 8)])


def P63(s):                                   # V bottom
    return spike(*[-s[i][1] for i in (0, 2, 4, 6, 8)])


def P66(s):                                   # frypan: bowl on a flat base
    l = [s[i][1] for i in (0, 2, 4, 6, 8)]
    return l[0] > l[1] and l[4] > l[3] and inband(l[2], l[1], l[3])


def P28(s):
    # H L H L H L H L H L H L -- rim, five lows, rim, handle.  The left rim
    # must be the high BEFORE the decline; taking the first high INSIDE the
    # cup put the band too low and tested something undrawable.
    if not dome(*[-s[i][1] for i in (1, 3, 5, 7, 9)]):
        return False
    return inband(s[11][1], s[0][1], s[10][1])


def P64(s):                                   # inverted cup and handle
    if not dome(*[s[i][1] for i in (1, 3, 5, 7, 9)]):
        return False
    return inband(s[11][1], s[0][1], s[10][1])


def P59(s):                                   # one completed J
    h0, l1, l2, l3, h4 = s[0][1], s[1][1], s[3][1], s[5][1], s[6][1]
    return l1 > l2 < l3 and (l1 - l2) > (l3 - l2) and h4 > h0


def P24(s):                                   # bull flag
    l0, h1, l1, h2, l2, h3 = [x[1] for x in s[:6]]
    return (h1 > l0 and h2 < h1 and h3 < h2 and l2 < l1
            and inband(l1, l0, h1) and inband(l2, l0, h1))


def P25(s):                                   # bull pennant -- converging
    l0, h1, l1, h2, l2, h3 = [x[1] for x in s[:6]]
    return (h1 > l0 and h2 < h1 and h3 < h2 and l2 > l1
            and inband(l1, l0, h1) and inband(l2, l0, h1))


def P56(s):                                   # dead-cat bounce
    h0, l1, h1, l2 = [x[1] for x in s[:4]]
    return l1 < h0 and inband(h1, l1, h0) and l2 < l1


def P65(s):                                   # tower top
    # "the fall is at least the rise" lived here and is COMPLETELY redundant;
    # it reduces to what the retrace test already says.  Same count either way.
    l0, h1, l1 = [x[1] for x in s[:3]]
    ub, db = s[1][0] - s[0][0], s[2][0] - s[1][0]
    return h1 > l0 and l1 < l0 and db <= ub


def P72(s):                                   # order block
    h0, l1, h1 = [x[1] for x in s[:3]]
    return h1 > h0 and l1 < h0


def P55(s):
    """Bump-and-run top.  Two lows fix the lead-in line, the next leg must be
    steeper, and price must fall back below that line extended -- comparison
    and projection only, no degrees."""
    b1, p1 = s[0][0], s[0][1]
    b2, p2 = s[2][0], s[2][1]
    b3, p3 = s[4][0], s[4][1]
    b4, p4 = s[6][0], s[6][1]
    if b2 <= b1 or b3 <= b2 or b4 <= b3:
        return False
    lead = (p2 - p1) / float(b2 - b1)
    if lead <= 0:
        return False
    if (p3 - p2) / float(b3 - b2) <= lead:     # the bump must accelerate
        return False
    return p4 < p1 + lead * (b4 - b1)


def P60(s):
    """High and tight flag: P24 whose pole is the largest leg in its own
    window.  Rank instead of "roughly doubles"."""
    if not P24(s):
        return False
    legs = [abs(s[i + 1][1] - s[i][1]) for i in range(5)]
    return all(legs[0] > x for x in legs[1:])


SPEC = [
    ('P26', '圓弧頂', 'Rounding Top', '空', 9, 1, P26,
     '五個高點成穹頂：上升時<b>步幅遞減</b>、下降時<b>步幅遞增</b>'),
    ('P27', '圓弧底', 'Rounding Bottom', '多', 9, 2, P27,
     '五個低點成碗底：下降步幅遞減、上升步幅遞增'),
    ('P32', 'V 型反轉（頂）', 'V Reversal', '空', 9, 1, P32,
     '與圓弧頂同樣的五個高點，但<b>步幅方向相反</b>'),
    ('P63', 'V 型底', 'V Bottom', '多', 9, 2, P63,
     '五個低點的尖底：下降加速、上升減速'),
    ('P66', '平底鍋底', 'Frypan Bottom', '多', 9, 2, P66,
     '碗底但底部是平的：中間那個低點落在左右兩個低點的<b>區間內</b>'),
    ('P28', '杯柄', 'Cup and Handle', '多', 12, 1, P28,
     '碗底 ＋ 柄：柄的低點落在<b>左右兩個杯緣構成的區間內</b>'),
    ('P64', '倒置杯柄', 'Inverted Cup and Handle', '空', 12, 2, P64,
     '穹頂 ＋ 柄，杯柄的鏡像'),
    ('P59', '穿越型態', 'Descending Scallop', '空', 7, 1, P59,
     'J 形：碗底之後的高點<b>超過碗左邊那個高點</b>'),
    ('P24', '多方旗形', 'Bull Flag', '多', 6, 2, P24,
     '單腿旗桿 ＋ 平行下傾旗面；<b>旗面必須留在旗桿的區間內</b>'),
    ('P25', '多方三角旗', 'Bull Pennant', '多', 6, 2, P25,
     '同旗桿，但旗面<b>收斂</b>（高更低、低更高）'),
    ('P56', '死貓反彈', 'Dead-Cat Bounce', '空', 4, 1, P56,
     '下跌 ＋ 部分反彈（<b>落在跌幅區間內</b>）＋ 續跌破前低'),
    ('P65', '塔形頂', 'Tower Top', '空', 3, 2, P65,
     '<b>跌得比漲得快</b>：完全回吐，且下跌用的 K 棒不多於上漲腿'),
    ('P72', '訂單塊', 'Order Block', '中', 3, 1, P72,
     '結構轉折前的最後一個反向樞紐'),
    ('P55', '駝峰反轉', 'Bump-and-Run', '空', 7, 2, P55,
     '兩個低點定引導線 → 下一段<b>更陡</b> → 價格跌回線下'),
    ('P60', '高位緊密旗形', 'High and Tight Flag', '多', 6, 2, P60,
     'P24 旗形，且<b>旗桿是視窗內五段中最大的一段</b>'),
]


def push_scan(H, L, S):
    """Exactly the .pla's loop: a repeated type wipes the chain, a full chain
    shifts by one, and every pattern is tested on the last N slots after each
    push -- inside the equivalent of `if v_Push`, never once per bar."""
    px = [0.0] * CAP
    bar = [0] * CAP
    typ = [0] * CAP
    ch = 0
    hits = {s[0]: [] for s in SPEC}
    npv = 0
    for i in range(1, len(H) - 1):
        if S[i] < 2 or S[i + 1] < S[i]:
            continue
        for k in (1, 2):
            if k == 1 and not (H[i] > H[i - 1] and H[i] > H[i + 1]):
                continue
            if k == 2 and not (L[i] < L[i - 1] and L[i] < L[i + 1]):
                continue
            npv += 1
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
            for cid, zh, en, d, need, first, fn, note in SPEC:
                if ch < need:
                    continue
                a = ch - need
                if typ[a] != first:
                    continue
                sl = [(bar[a + t], px[a + t], typ[a + t]) for t in range(need)]
                if fn(sl):
                    # keep the pivot positions too: the example picker needs
                    # to ring them, and re-deriving them would be a second
                    # implementation of the chain to disagree with this one
                    hits[cid].append((bar[a], bar[a + need - 1],
                                      [(b, 'H' if t == 1 else 'L')
                                       for b, _, t in sl]))
    return hits, npv


def main():
    rows, H, L, S = bars()
    hit, npv = push_scan(H, L, S)
    mir, _ = push_scan([-x for x in L], [-x for x in H], S)   # a true mirror
    print('=' * 78)
    print('  十五種母體普查   %s 根 5 分 K   原始樞紐 %s 個'
          % (format(len(rows), ','), format(npv, ',')))
    print('  ★ 重置鏈（指標實際使用的那一條）')
    print('=' * 78)
    print('  %-6s %-14s %-4s %-9s %-9s %-8s %s'
          % ('代號', '名稱', '方向', '母體', '鏡像', '倍率', '跨度中位'))
    print('  ' + '-' * 72)
    out = []
    for cid, zh, en, d, need, first, fn, note in SPEC:
        n, m = len(hit[cid]), len(mir[cid])
        sp = sorted(b - a for a, b, _ in hit[cid])
        med = sp[len(sp) // 2] if sp else 0
        r = (n / float(m)) if m else None
        out.append({'id': cid, 'zh': zh, 'en': en, 'dir': d, 'n': n,
                    'mirror': m, 'ratio': round(r, 3) if r else None,
                    'span': med, 'note': note})
        print('  %-6s %-14s %-4s %-9s %-9s %-8s %d 根'
              % (cid, zh, d, format(n, ','), format(m, ','),
                 ('%.2fx' % r) if r else '-', med))
    json.dump({'bars': len(rows), 'pivots': npv, 'rows': out},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n  -> %s' % OUT)
    print('=' * 78)


if __name__ == '__main__':
    main()
