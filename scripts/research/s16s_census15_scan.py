# -*- coding: utf-8 -*-
"""Population census of the fifteen patterns still unstudied.

Willy chose C: measure every population first, then rule on the bullish
question.  The reasoning is that a pattern whose population is zero or
absurd dies the same way whichever ruling wins, so only the middle band
needs a decision -- and past experience is that measuring the population
kills most of them (three gap patterns, two diamonds, all closed the day
they were counted).

Each definition below is PROVISIONAL and zero-parameter.  Two devices do the
work that a threshold would otherwise do:

  step monotonicity   "round" versus "V" is curvature, and curvature normally
                      needs a threshold.  It does not here: compare the SIZE
                      OF CONSECUTIVE STEPS.  A dome decelerates into its peak
                      and accelerates out of it; a spike does the opposite.
                      Purely ordinal, nothing to tune.

  the band device     two points define a zone and the third is tested,
                      min(A,B) <= C <= max(A,B).  Willy's device from the
                      pivot group; the tolerance comes from the pattern.

Every pattern is also counted on the MIRROR chain -- prices negated, highs
becoming lows.  A shape whose mirror occurs just as often carries no
direction, which is what killed P15 and P16.  That test costs one more pass
and settles a question that would otherwise need its own study.

Two patterns are NOT counted, and saying so is the point:

  P55 bump-and-run    three trendlines with an angle threshold.  That is the
                      same kind of object as P58 and P71, which Willy ruled
                      outside graphical-pattern research on 2026-08-30.  It
                      needs his ruling, not a definition from me.
  P60 high and tight  "the pole roughly doubles" is an outside constant, and
                      no rank or geometry in the pattern supplies it.  It is
                      P24 plus a magnitude threshold, so P24's count is its
                      upper bound.

Counts only.  No P&L column: this measures how often a shape occurs, not
whether trading it makes money, and mixing the two is how a census turns
into a backtest nobody asked for.

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


# --------------------------------------------------------------------------
# the pivot chain, window 1, never crossing a session
# --------------------------------------------------------------------------
def chain():
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    pv = []
    for i in range(1, len(H) - 1):
        if S[i] < 2 or S[i + 1] < S[i]:
            continue
        hi = H[i] > H[i - 1] and H[i] > H[i + 1]
        lo = L[i] < L[i - 1] and L[i] < L[i + 1]
        if hi:
            if pv and pv[-1][2] == 1:
                if H[i] > pv[-1][1]:
                    pv[-1] = (i, H[i], 1)
            else:
                pv.append((i, H[i], 1))
        elif lo:
            if pv and pv[-1][2] == 2:
                if L[i] < pv[-1][1]:
                    pv[-1] = (i, L[i], 2)
            else:
                pv.append((i, L[i], 2))
    return pv, len(rows)


def mirror(pv):
    """Negating price turns every high into a low and vice versa."""
    return [(b, -p, 1 if t == 2 else 2) for b, p, t in pv]


# --------------------------------------------------------------------------
# the predicates.  each takes a slice of consecutive pivots and the type the
# slice must start with; each returns True or False and nothing else.
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
    h = [s[i][1] for i in (0, 2, 4, 6, 8)]
    return dome(*h)


def P32(s):                                   # V top -- the sharp version
    h = [s[i][1] for i in (0, 2, 4, 6, 8)]
    return spike(*h)


def P27(s):                                   # rounding bottom, 5 lows
    l = [-s[i][1] for i in (0, 2, 4, 6, 8)]
    return dome(*l)


def P63(s):                                   # V bottom
    l = [-s[i][1] for i in (0, 2, 4, 6, 8)]
    return spike(*l)


def P66(s):                                   # frypan: bowl on a flat base
    l = [s[i][1] for i in (0, 2, 4, 6, 8)]
    return (l[0] > l[1] and l[4] > l[3]
            and inband(l[2], l[1], l[3]))


def P28(s):                                   # cup and handle
    # H L H L H L H L H L H L -- rim, five lows, rim, handle.
    # The left rim must be the high BEFORE the decline; taking the first high
    # INSIDE the cup put the band too low and tested something undrawable.
    l = [-s[i][1] for i in (1, 3, 5, 7, 9)]
    if not dome(*l):
        return False
    return inband(s[11][1], s[0][1], s[10][1])


def P64(s):                                   # inverted cup and handle
    h = [s[i][1] for i in (1, 3, 5, 7, 9)]
    if not dome(*h):
        return False
    return inband(s[11][1], s[0][1], s[10][1])


def P59(s):                                   # descending scallop, one J
    h0, l1, l2, l3, h4 = s[0][1], s[1][1], s[3][1], s[5][1], s[6][1]
    return (l1 > l2 < l3 and (l1 - l2) > (l3 - l2)
            and h4 > h0)


def P24(s):                                   # bull flag
    l0, h1, l1, h2, l2, h3 = (s[0][1], s[1][1], s[2][1],
                              s[3][1], s[4][1], s[5][1])
    return (h1 > l0
            and h2 < h1 and h3 < h2
            and l2 < l1
            and inband(l1, l0, h1) and inband(l2, l0, h1))


def P25(s):                                   # bull pennant -- converging
    l0, h1, l1, h2, l2, h3 = (s[0][1], s[1][1], s[2][1],
                              s[3][1], s[4][1], s[5][1])
    return (h1 > l0
            and h2 < h1 and h3 < h2
            and l2 > l1
            and inband(l1, l0, h1) and inband(l2, l0, h1))


def P56(s):                                   # dead-cat bounce
    h0, l1, h1, l2 = s[0][1], s[1][1], s[2][1], s[3][1]
    return (l1 < h0 and inband(h1, l1, h0) and l2 < l1)


def P65(s):                                   # tower top: falls faster than it rose
    # "the fall is at least the rise" was in here and is COMPLETELY redundant
    # -- it reduces to l1 <= l0, which the retrace test already says.  Same
    # 8,386 either way.  A condition that never changes the answer tells the
    # reader something is being tested when nothing is.
    l0, h1, l1 = s[0][1], s[1][1], s[2][1]
    ub, db = s[1][0] - s[0][0], s[2][0] - s[1][0]
    return (h1 > l0 and l1 < l0 and db <= ub)


def P72(s):                                   # order block: last low before BOS
    h0, l1, h1 = s[0][1], s[1][1], s[2][1]
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
    bump = (p3 - p2) / float(b3 - b2)
    if bump <= lead:                       # the bump must accelerate
        return False
    return p4 < p1 + lead * (b4 - b1)      # and price returns under the line


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
     '與圓弧頂同樣的五個高點，但<b>步幅方向相反</b> —— 上升加速、下降減速'),
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
     '<b>跌得比漲得快</b>：下跌腿的價格不小於上漲腿，且用的 K 棒不多於它'),
    ('P72', '訂單塊', 'Order Block', '中', 3, 1, P72,
     '結構轉折前的最後一個反向樞紐'),
    ('P55', '駝峰反轉', 'Bump-and-Run', '空', 7, 2, P55,
     '兩個低點定引導線 → 下一段<b>更陡</b> → 價格跌回線下'),
    ('P60', '高位緊密旗形', 'High and Tight Flag', '多', 6, 2, P60,
     'P24 旗形，且<b>旗桿是視窗內五段中最大的一段</b>'),
]

SKIP = [
    ('__P55_old', '駝峰反轉', 'Bump-and-Run', '空',
     '原始定義是<b>三條趨勢線加一個角度門檻</b>。那與 P58 扇形原則、'
     'P71 江恩角度線是同一類物件 —— 2026-08-30 已被裁示為'
     '<b>不屬於圖形型態探討的範疇</b>。<b>需要用戶裁示，我不自己定義。</b>'),
    ('__P60_old', '高位緊密旗形', 'High and Tight Flag', '多',
     '定義是「旗桿漲幅接近翻倍」。<b>「翻倍」是外來常數</b>，'
     '型態本身沒有任何排名或幾何可以推導出它。'
     '它是 P24 多方旗形<b>加一個幅度門檻</b>，'
     '所以 <b>P24 的母體就是它的上限</b>。'),
]


def count(pv, spec):
    """One pass per pattern; span recorded because a five-bar cup is not
    a cup -- window 1 calls a pivot every 2.8 bars."""
    n, need, first, fn = len(pv), spec[4], spec[5], spec[6]
    hits, spans = 0, []
    for a in range(n - need):
        if pv[a][2] != first:
            continue
        s = pv[a:a + need]
        if fn(s):
            hits += 1
            spans.append(s[-1][0] - s[0][0])
    spans.sort()
    med = spans[len(spans) // 2] if spans else 0
    return hits, med


def main():
    pv, bars = chain()
    mv = mirror(pv)
    print('=' * 78)
    print('  十五種母體普查   %s 根 5 分 K   視窗 1 樞紐 %s 個'
          % (format(bars, ','), format(len(pv), ',')))
    print('=' * 78)
    print('  %-6s %-14s %-4s %-10s %-10s %-8s %s'
          % ('代號', '名稱', '方向', '母體', '鏡像', '倍率', '跨度中位'))
    print('  ' + '-' * 74)
    out = []
    for spec in SPEC:
        cid, zh, en, d = spec[0], spec[1], spec[2], spec[3]
        c, med = count(pv, spec)
        m, _ = count(mv, spec)
        r = (c / m) if m else float('inf') if c else 0.0
        out.append({'id': cid, 'zh': zh, 'en': en, 'dir': d, 'n': c,
                    'mirror': m, 'ratio': round(r, 3) if m else None,
                    'span': med, 'note': spec[7]})
        print('  %-6s %-14s %-4s %-10s %-10s %-8s %d 根'
              % (cid, zh, d, format(c, ','), format(m, ','),
                 ('%.2fx' % r) if m else '-', med))
    print('  ' + '-' * 74)
    for cid, zh, en, d, why in []:            # both now measured
        out.append({'id': cid, 'zh': zh, 'en': en, 'dir': d, 'n': None,
                    'mirror': None, 'ratio': None, 'span': None, 'note': why})
        print('  %-6s %-14s %-4s %s' % (cid, zh, d, '未量 —— 見說明'))
    json.dump({'bars': bars, 'pivots': len(pv), 'rows': out},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n  -> %s' % OUT)
    print('=' * 78)


if __name__ == '__main__':
    main()
