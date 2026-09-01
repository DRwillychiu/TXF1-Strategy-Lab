# -*- coding: utf-8 -*-
"""The eleven, as CODED -- one schematic per pattern, asserted against the
real predicate.

Willy's standing rule (memory feedback_pattern_logic_diagram): every time a
pattern's logic is settled, draw the picture and mark which part of the
spec is which part of the picture.  A page of prose about shapes is not a
discussion of shapes.

WHY THE ASSERTIONS

  A hand-drawn schematic is a CLAIM about the predicate, and hand-drawn
  claims drift from the code they illustrate.  So every example below is
  run through the SAME predicate the .pla implements; if the drawing stops
  satisfying its own definition the page refuses to build.

  This is the device from s16s_seven_make_diagram.py, reused deliberately.

Numbers are the LAPTOP's csv, md5 47e4054ff31b086df392bb3022e90e03.
See S16S_CSV_DIVERGENCE_20260901.md -- the desktop's differ.

Run:  python scripts/research/s16s_eleven_make_logic_page.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')
OUT = os.path.join('docs', 'research', 'S16S_eleven_logic.html')


# --------------------------------------------------------------------------
# the predicates, written once, used both to ASSERT and to describe
# --------------------------------------------------------------------------

def rng(b, i):
    return b[i][1] - b[i][2]


def upper(b, i):
    return b[i][1] - max(b[i][0], b[i][3])


def body(b, i):
    return abs(b[i][3] - b[i][0])


def p41(b, i):
    return all(rng(b, i) > rng(b, i - d) for d in (1, 2, 3))


def p42(b, i):
    return all(rng(b, i) > rng(b, i - d) for d in range(1, 7))


def p43(b, i):
    return b[i][1] > b[i - 1][1] and b[i][3] < b[i - 1][2]


def p45(b, i, lo):
    return b[i][3] < lo


def p47(b, i):
    a, c = i - 2, i
    return (upper(b, a) > body(b, a) and upper(b, c) > body(b, c)
            and b[a][1] > b[a + 1][1] and b[c][1] > b[a + 1][1]
            and abs(b[a][1] - b[c][1]) < min(upper(b, a), upper(b, c)))


def p48(b, i):
    a, c = i - 1, i
    return (upper(b, a) > body(b, a) and upper(b, c) > body(b, c)
            and b[a][1] > b[a - 1][1] and b[c][1] > b[c + 1][1]
            and abs(b[a][1] - b[c][1]) < min(upper(b, a), upper(b, c)))


def flag(b, pole, last):
    """Replay the pole through the drift bars.  Returns (P13, P14)."""
    h, l = b[pole][1], b[pole][2]
    n, conv, prev = 0, True, rng(b, pole)
    for i in range(pole + 1, last + 1):
        if b[i][1] > h:
            return False, False
        if b[i][3] < l:
            return n >= 1, (n >= 1 and conv)
        conv = conv and rng(b, i) < prev
        prev = rng(b, i)
        n += 1
    return False, False


def p33(b, i, lvl):
    return b[i][1] > lvl and b[i][3] < lvl


def p35(b, i, lvl):
    return b[i][3] < lvl


def piv_hi(b, i):
    return b[i][1] > b[i - 1][1] and b[i][1] > b[i + 1][1]


def piv_lo(b, i):
    return b[i][2] < b[i - 1][2] and b[i][2] < b[i + 1][2]


# --------------------------------------------------------------------------
# the eleven, each with a worked example that must satisfy its own predicate
# bars are (open, high, low, close)
# --------------------------------------------------------------------------

WR4 = [(100, 102, 99, 101), (101, 103, 100, 102), (102, 104, 101, 103),
       (103, 105, 95, 96)]

P = []


def add(**kw):
    P.append(kw)


add(id='P41', zh='WR4 最近四根最寬', en='Widest of 4', dr='中性', sk='bar',
    n=82258, row=1, span='4 根',
    one='這一根的高低差，比前面三根每一根都大。',
    why='這是 NR4「最近四根最窄」的鏡像。NR4 在 IND_S16S_CONV6 裡是第 1 列，'
        'WR4 在這裡也是第 1 列 —— 同一個排名裝置，方向相反。'
        'N=4 是 Crabel 的常數，2026-08-31 裁示接受，記錄為<b>借用</b>而非推導。',
    edge='<b>嚴格大於</b>。平手不算，因為 WR 沒有「內含線」那種幾何理由可以'
         '把平手納入 —— 那個理由只存在於 NR 那一邊，而 NR 的平手處置至今待裁示。',
    bars=WR4, hit=3, chk=lambda b: p41(b, 3),
    lvl=None, note='第 3 根區間 10，前三根都是 3 ── 嚴格大於，四根裡最寬。')

add(id='P42', zh='WR7 最近七根最寬', en='Widest of 7', dr='中性', sk='bar',
    n=44455, row=2, span='7 根',
    one='這一根的高低差，比前面六根每一根都大。',
    why='跟 P41 同一個裝置，只是視窗換成 Crabel 的第二個常數 N=7。'
        '<b>P42 在邏輯上是 P41 的子集</b>（前六根含前三根），'
        '所以兩列會有大量重疊，這是定義本身決定的，不是 bug。',
    edge='同 P41，嚴格大於。時段內至少 8 根才起算。',
    bars=[(100, 102, 99, 101), (101, 103, 100, 102), (102, 105, 101, 103),
          (103, 105, 102, 104), (104, 106, 103, 105), (105, 108, 104, 106),
          (106, 111, 101, 102)],
    hit=6, chk=lambda b: p42(b, 6),
    lvl=None, note='第 6 根區間 10，前六根最大的是 4 ── 七根裡最寬。')

add(id='P13', zh='空方旗形', en='Bear Flag', dr='空', sk='bar',
    n=12041, row=3, span='中位 3 根',
    one='一根寬而收黑的旗桿之後，價格在旗桿的高低之間橫走，最後收破旗桿的低點。',
    why='<b>旗形沒有根數。</b>圖鑑通常寫「飄移 5 到 20 根」，那是一個要調的參數。'
        '這裡改成「跑到分出勝負為止」：飄移一直跑，直到收盤跌破旗桿低（成立）'
        '或高點被穿越（作廢）。<b>「旗形要多長」這個問題從此不會被問到。</b>'
        '<br><br>旗桿的定義直接借 P41 —— WR4 而且收黑。不另發明。',
    edge='高點先判、低點後判：<b>同一根既穿過旗桿高、又收破旗桿低，算作廢，不算成立。</b>'
         '這個先後順序是定義的一部分。<br>'
         '飄移至少 1 根（<code>n &gt;= 1</code>），旗桿當根收破不算。<br>'
         '<b>旗形會跨時段</b> —— 母體裡 419 個（3.48%）真的跨。原腳本有一條'
         '「時段結束旗形」的分支，實測走到 0 次，是死碼；本頁與指標照程式碼，不照註解。',
    bars=[(100, 102, 99, 101), (101, 103, 100, 102), (102, 104, 101, 103),
          (103, 105, 95, 96), (96, 99, 95.5, 98), (98, 100, 96, 97),
          (97, 99, 93, 94)],
    hit=6, pole=3, chk=lambda b: flag(b, 3, 6)[0],
    lvl=None, band=(95, 105),
    note='旗桿 = 第 3 根（WR4 且收黑），高 105 低 95。'
         '飄移兩根都待在帶內，第 6 根收 94 跌破 95 ── 旗形成立。'
         '第 5 根區間 4 大於第 4 根的 3.5，收斂中斷，所以這個例子<b>是 P13 不是 P14</b>。')

add(id='P43', zh='關鍵反轉（空）', en='Key Reversal, Bearish', dr='空', sk='bar',
    n=8308, row=4, span='2 根',
    one='創了前一根的新高，卻收在前一根的最低之下。',
    why='這是「外包吞噬」的一種寫法，但兩端都用<b>比較</b>而不是幅度門檻：'
        '高要更高、收要低於前低。沒有「至少幾點」「至少幾趴」這種可調的東西。',
    edge='兩端都是<b>嚴格</b>。碰到前低不算，要收在它之下。'
         '看的是 <b>Close 對 Low</b>，不是 Low 對 Low —— 影線刺破不算，要收進去。',
    bars=[(100, 104, 100, 103), (103, 105, 98, 99)],
    hit=1, chk=lambda b: p43(b, 1),
    lvl=None, note='第 1 根高 105 > 前高 104，收 99 < 前低 100。')

add(id='P14', zh='空方三角旗', en='Bear Pennant', dr='空', sk='bar',
    n=5883, row=5, span='中位 2 根',
    one='跟空方旗形完全一樣，額外要求飄移期間每一根都比前一根窄。',
    why='<b>P14 是 P13 的真子集</b>，唯一的差別是收斂旗。這也是為什麼兩列'
        '並排放：看得到哪些旗形是收斂的、哪些不是，比例一眼可讀'
        '（5,883 / 12,041 ＝ 48.9%）。',
    edge='收斂是<b>嚴格遞減</b>，而且<b>一旦中斷就永不恢復</b> —— '
         '中間有一根沒有變窄，這個旗桿之後就只能是 P13。'
         '收破那一根<b>不參與</b>收斂判定。',
    bars=[(100, 102, 99, 101), (101, 103, 100, 102), (102, 104, 101, 103),
          (103, 105, 95, 96), (96, 99, 95.5, 98), (98, 99, 96.5, 97),
          (97, 98, 93, 94)],
    hit=6, pole=3, chk=lambda b: flag(b, 3, 6)[1],
    lvl=None, band=(95, 105),
    note='同一個旗桿，但飄移區間 10 → 3.5 → 2.5 一路變窄，'
         '所以這一次<b>P13 與 P14 同時成立</b>。')

add(id='P47', zh='號角頂', en='Horn Top', dr='空', sk='bar',
    n=5020, row=6, span='3 根',
    one='兩根長上影線的高點差不多齊，中間隔著一根較低的高點 —— 像兩支角。',
    why='「長上影線」與「差不多齊」原本都是門檻。這裡兩個都改寫成<b>比較</b>：'
        '<br>長上影線 → <b>上影線比實體長</b>；'
        '<br>差不多齊 → <b>兩個高點的差距，小於兩根上影線中較短的那一根</b>。'
        '<br><br>第二條是關鍵：容忍度<b>由 K 棒自己提供</b>。'
        '震幅變大時影線跟著變長，容忍度自動放寬 —— '
        '這正是 2026-08-31「改成尺度不變」裁示要的效果。',
    edge='中間那根只看<b>高點</b>要比兩支角都低，不看它的影線或實體。'
         '兩支角之間<b>剛好隔一根</b>，不多不少。',
    bars=[(100, 110, 99, 101), (102, 104, 101, 102), (102, 109.5, 101, 103)],
    hit=2, chk=lambda b: p47(b, 2),
    lvl=None,
    note='兩支角高 110 與 109.5，差 0.5；上影線 9 與 6.5，取短的 6.5。'
         '0.5 &lt; 6.5 ── 算齊。中間那根高 104，比兩支都低。')

add(id='P48', zh='管狀頂', en='Pipe Top', dr='空', sk='bar',
    n=4973, row=7, span='2 根',
    one='兩根<b>相鄰</b>的長上影線，高點差不多齊，而且這一對是局部高點。',
    why='跟號角頂共用同一組裝置，唯一差別是兩支角<b>貼在一起</b>而不是隔一根。'
        '所以這兩個型態不會互相汙染母體。',
    edge='「這一對是局部高點」寫成兩個條件：<b>第一根的高要高過它前一根</b>、'
         '<b>第二根的高要高過它後一根</b>。'
         '<br><br>後面那一根就是<b>整支指標必須落後一根</b>的原因 —— '
         '管狀頂在它自己的第二根上不可判定，要等下一根才知道。',
    bars=[(100, 104, 99, 103), (105, 112, 104, 106), (106, 111.5, 105, 105),
          (105, 107, 103, 104)],
    hit=2, chk=lambda b: p48(b, 2),
    lvl=None,
    note='兩根高 112 與 111.5，差 0.5 &lt; 短影線 5.5。'
         '左邊 104、右邊 107 都比這一對低 ── 這一對是局部高點。')

add(id='P45', zh='破前時段低', en='Prior Session Low Break', dr='空', sk='bar',
    n=1463, row=8, span='1 根',
    one='收盤跌破<b>上一個時段</b>的最低點。',
    why='這是十一種裡唯一一個跨時段的型態，也是唯一一個<b>每個時段最多算一次</b>的。'
        '第一次收破就登記，然後那個位階作廢，同一個時段不會重複計。',
    edge='用 <b>Close</b> 不是 Low ── 影線刺破不算。'
         '<br>「上一個時段」是日盤與夜盤各自算一段（日 08:45-13:45、夜 15:00-05:00），'
         '不是一個交易日。'
         '<br><b>這是唯一一個鏡像倍率明顯偏離 1 的：0.78</b>'
         '（破前低 1,463 對 破前高 1,880）── 也就是說台指<b>破前時段高'
         '比破前時段低更常見</b>，跟指數長期偏多一致。',
    bars=[(100, 101, 99, 100), (100, 101, 98, 99), (99, 100, 96, 96.5)],
    hit=2, chk=lambda b: p45(b, 2, 97),
    lvl=('前時段低 97', 97),
    note='虛線 97 是上一個時段的最低。第 2 根收 96.5，收在它之下。')

add(id='P35', zh='結構破壞（向下）', en='Break of Structure, Down', dr='空',
    sk='pivot', n=24132, row=9, span='3 根',
    one='收盤跌破<b>目前站著的那個樞紐低</b>。',
    why='<b>這不是「低更低」原語。</b>兩者差很多：'
        '收破站著的樞紐低發生 24,132 次，而「下一個樞紐低印得更低」發生 34,116 次。'
        '<br><br>差的那 9,984 次，全是<b>價格戳到下面又收回來</b>的情形 —— '
        '而那正是這個型態要排除的東西。所以它沒有被化約掉，'
        '不像 P39（三個下降峰）被化約成頭頭降原語。',
    edge='用 <b>Close</b>。<b>每個樞紐低只被破一次</b>：'
         '破過就解除武裝，要等下一個樞紐低印出來才重新上膛。'
         '<br>樞紐用碎形定義（<code>L[i] &lt; L[i±1]</code>），'
         '所以它<b>晚一根才確認</b> —— 破位比對的一定是「這一根之前就站著」的位階。',
    bars=[(104, 105, 98, 99), (99, 100, 96, 97), (97, 99, 97, 98),
          (98, 99, 94, 95)],
    hit=3, chk=lambda b: piv_lo(b, 1) and p35(b, 3, 96),
    lvl=('樞紐低 96', 96),
    note='第 1 根是樞紐低（96 低於左右兩根）。第 3 根收 95，收破 96。')

add(id='P33', zh='上衝回落', en='Upthrust / Liquidity Sweep', dr='空',
    sk='pivot', n=18003, row=10, span='3 根',
    one='高點衝過站著的樞紐高，收盤卻收回它下面。',
    why='「掃流動性」這個說法要成立，必須<b>同一根</b>又穿又收回 —— '
        '穿了就走是突破，穿了收回才是掃單。所以兩個條件綁在同一根上：'
        '<code>High &gt; 位階</code> 且 <code>Close &lt; 位階</code>。',
    edge='跟 P35 對稱：<b>每個樞紐高只被掃一次</b>。'
         '<br>高點用 <b>High</b>（要真的穿過去），收盤用 <b>Close</b>。'
         '<br>鏡像倍率 1.01 ── <b>上衝回落與下探回升一樣常見</b>，'
         '這個形狀本身不帶方向資訊，方向來自它掃的是哪一邊。',
    bars=[(100, 108, 99, 107), (107, 110, 106, 109), (106, 107, 104, 105),
          (105, 112, 104, 108)],
    hit=3, chk=lambda b: piv_hi(b, 1) and p33(b, 3, 110),
    lvl=('樞紐高 110', 110),
    note='第 1 根是樞紐高 110。第 3 根衝到 112 穿過去，卻收 108 回到下面。')

add(id='P37', zh='性格轉變（向下）', en='Change of Character, Down', dr='空',
    sk='pivot', n=12675, row=11, span='3 根',
    one='<b>在一次向上突破之後</b>，第一次收破樞紐低。',
    why='P37 是 P35 的真子集，多了一個記憶：<b>上一次結構性事件是往上的</b>。'
        '<br><br>它捕捉的是「趨勢方向翻面的那一刻」，'
        '而不是「下跌途中又破一個低」—— 後者是 P35 的大多數。'
        '12,675 / 24,132 ＝ <b>52.5% 的結構破壞同時是性格轉變</b>。',
    edge='只認<b>第一次</b>：登記之後 upLast 立刻清掉，'
         '要等下一次收上樞紐高才重新武裝。'
         '<br>「向上」的定義是<b>收盤高過站著的樞紐高</b>（不需要是樞紐、不需要回落）。',
    bars=[(100, 108, 99, 107), (107, 110, 106, 109), (106, 107, 104, 105),
          (105, 112, 104, 111), (111, 112, 100, 101), (101, 103, 97, 98),
          (98, 101, 98, 100), (100, 101, 94, 95)],
    hit=7, chk=lambda b: (piv_hi(b, 1) and b[3][3] > 110
                          and piv_lo(b, 5) and p35(b, 7, 97)),
    lvl=('樞紐高 110 / 樞紐低 97', 110),
    lvl2=('樞紐低 97', 97),
    note='第 3 根收 111 站上樞紐高 110 ── 記下「上一次是往上」。'
         '第 5 根是樞紐低 97（要等第 6 根低點更高才確認得了），'
         '第 7 根收 95 破掉它 ── 這一次的結構破壞<b>同時是性格轉變</b>。'
         '<br><b>第 6 根不能省</b>：樞紐要有右肩才成立，'
         '而收破那一根的收盤永遠 &gt;= 它自己的低，做不了右肩。')


# --------------------------------------------------------------------------
def svg(p):
    """One schematic.  Candles, level lines, the marked bar highlighted."""
    b = p['bars']
    W, H = 60 + len(b) * 56, 240
    lo = min(x[2] for x in b)
    hi = max(x[1] for x in b)
    if p.get('lvl'):
        lo, hi = min(lo, p['lvl'][1]), max(hi, p['lvl'][1])
    if p.get('band'):
        lo, hi = min(lo, p['band'][0]), max(hi, p['band'][1])
    pad = (hi - lo) * 0.16 or 1
    lo, hi = lo - pad, hi + pad

    def y(v):
        return 26 + (hi - v) / (hi - lo) * (H - 62)

    a = ['<svg viewBox="0 0 %d %d" role="img" aria-label="%s %s 示意">'
         % (W, H, p['id'], p['zh'])]
    if p.get('band'):
        a.append('<rect x="30" y="%.1f" width="%d" height="%.1f" '
                 'fill="var(--accw)" opacity=".16"/>'
                 % (y(p['band'][1]), W - 46, y(p['band'][0]) - y(p['band'][1])))
    for key in ('lvl', 'lvl2'):
        if p.get(key):
            t, v = p[key]
            a.append('<line x1="30" y1="%.1f" x2="%d" y2="%.1f" '
                     'stroke="var(--ink3)" stroke-width="1.4" '
                     'stroke-dasharray="5 4"/>' % (y(v), W - 16, y(v)))
            if key == 'lvl':
                a.append('<text x="%d" y="%.1f" class="lv" '
                         'text-anchor="end">%s</text>'
                         % (W - 18, y(v) - 6, t.split(' / ')[0]))
    for i, (o, h, l, c) in enumerate(b):
        x = 44 + i * 56
        mark = (i == p['hit'])
        pole = (i == p.get('pole', -1))
        col = ('var(--acc)' if mark else
               'var(--accw)' if pole else
               'var(--dn)' if c < o else 'var(--up)')
        a.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" '
                 'stroke-width="1.6"/>' % (x, y(h), x, y(l), col))
        t, bt = max(o, c), min(o, c)
        a.append('<rect x="%d" y="%.1f" width="20" height="%.1f" fill="%s" '
                 'rx="1.5"/>' % (x - 10, y(t), max(y(bt) - y(t), 2.2), col))
        if mark or pole:
            a.append('<text x="%d" y="%d" class="bl" text-anchor="middle">%s'
                     '</text>' % (x, H - 12, '旗桿' if pole else '成立'))
    a.append('</svg>')
    return '\n'.join(a)


def main():
    for p in P:                       # the drawing must satisfy the predicate
        assert p['chk'](p['bars']), '%s 的示意圖不滿足自己的定義' % p['id']
    assert len(P) == 11, '不是十一種'
    assert sorted(x['row'] for x in P) == list(range(1, 12)), '色帶列號不連續'

    A = []
    w = A.append
    w('<title>十一種的編碼邏輯</title>')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:'
      'wght@500;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;'
      'family=JetBrains+Mono:wght@500;600&amp;display=swap" rel="stylesheet">')
    w('''<style>
:root{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --up:#c8302e;--dn:#17795e;--acc:#7a5cc4;--accw:#b9a5e8;
 --serif:'Noto Serif TC',Georgia,serif;
 --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
 --mono:'JetBrains Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --up:#e8564e;--dn:#3ec08d;--acc:#a98ce8;--accw:#6d5aa0}}
:root[data-theme="dark"]{--ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --up:#e8564e;--dn:#3ec08d;--acc:#a98ce8;--accw:#6d5aa0}
:root[data-theme="light"]{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --up:#c8302e;--dn:#17795e;--acc:#7a5cc4;--accw:#b9a5e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 line-height:1.62}
.wrap{max-width:1140px;margin:0 auto;padding:44px 20px 84px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
h1{font-family:var(--serif);font-size:34px;font-weight:700;margin:0 0 12px;
 letter-spacing:-.01em;text-wrap:balance}
.lede{font-size:16px;color:var(--ink2);max-width:64ch;margin:0 0 30px}
h2{font-family:var(--serif);font-size:22px;font-weight:700;margin:44px 0 14px;
 padding-top:24px;border-top:1px solid var(--line)}
p{margin:0 0 12px;font-size:14.5px;color:var(--ink2);max-width:70ch}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:10px 0 20px;
 font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line2);
 vertical-align:top}
th{font-size:11.5px;letter-spacing:.06em;color:var(--ink3);font-weight:600;
 text-transform:uppercase;border-bottom:1px solid var(--line)}
td.n,th.n{text-align:right;font-family:var(--mono)}
code{font-family:var(--mono);font-size:12.5px;background:var(--line2);
 padding:1px 5px;border-radius:3px}
.pat{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:24px 26px;margin:20px 0}
.hd{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px;
 margin-bottom:4px}
.hd .id{font-family:var(--mono);font-size:13px;font-weight:600;
 color:var(--acc)}
.hd h3{margin:0;font-size:19px;font-weight:700;font-family:var(--serif)}
.hd .en{font-size:12.5px;color:var(--ink3);font-family:var(--mono)}
.meta{display:flex;flex-wrap:wrap;gap:18px;font-size:12px;color:var(--ink3);
 font-family:var(--mono);margin-bottom:16px}
.one{font-family:var(--serif);font-size:17px;font-weight:500;color:var(--ink);
 border-left:3px solid var(--acc);padding-left:15px;margin:0 0 18px;
 max-width:64ch}
.grid{display:grid;grid-template-columns:minmax(300px,1fr) minmax(280px,1fr);
 gap:22px;align-items:start}
@media (max-width:820px){.grid{grid-template-columns:1fr}}
.fig{overflow-x:auto}
svg{display:block;max-width:100%;height:auto}
.cap{font-size:12.5px;color:var(--ink3);margin-top:6px;max-width:60ch}
h4{margin:0 0 5px;font-size:12px;font-weight:700;letter-spacing:.06em;
 text-transform:uppercase;color:var(--ink3)}
.blk{margin-bottom:15px}
.blk p{font-size:14px;margin:0}
.lv{font:600 11px 'JetBrains Mono',monospace;fill:var(--ink3)}
.bl{font:600 11px 'Noto Sans TC',sans-serif;fill:var(--ink3)}
.note{background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--ink3);border-radius:10px;padding:18px 20px;
 margin:22px 0;font-size:14px;color:var(--ink2)}
.note b{color:var(--ink)}
.note h3{margin:0 0 8px;font-size:15px;color:var(--ink)}
</style>''')
    w('<div class="wrap">')
    w('<div class="eyebrow">S16_S · IND_S16S_ELEVEN · Build 260913</div>')
    w('<h1>十一種的編碼邏輯</h1>')
    w('<p class="lede">型態層的最後十一種，逐條寫成程式碼之後的樣子。'
      '每一張示意圖都被它自己的述詞斷言過 —— '
      '畫出來的形狀若不滿足定義，這一頁就生不出來。</p>')

    w('<h2>一、為什麼是副圖色帶，不是主圖標籤</h2>')
    tot = sum(x['n'] for x in P)
    top = max(P, key=lambda x: x['n'])
    w('<p>十一種合計 <b>%s 個標記</b>，比逼出第一條色帶的收斂六種'
      '（148,748）還密。%s 一個就 %s —— <b>每 %.1f 根 K 棒就有一根</b>。</p>'
      % ('{:,}'.format(tot), top['id'], '{:,}'.format(top['n']),
         421506.0 / top['n']))
    w('<p>那個密度下文字標籤會在<b>寬度</b>上互撞，不是高度，所以車道救不了。'
      '每個標記做成<b>一根 K 棒寬</b>、各佔一列，密的那列自然讀成一條帶子，'
      '而帶子本身就是資訊 —— 它顯示壓縮或擴張聚在哪裡。</p>')
    w('<table><thead><tr><th class="n">列</th><th>代號</th><th>名稱</th>'
      '<th>骨架</th><th class="n">母體</th><th class="n">每幾根一次</th>'
      '</tr></thead><tbody>')
    for p in sorted(P, key=lambda x: -x['row']):
        w('<tr><td class="n">%d</td><td><code>%s</code></td><td>%s</td>'
          '<td>%s</td><td class="n">%s</td><td class="n">%.1f</td></tr>'
          % (p['row'], p['id'], p['zh'],
             '樞紐' if p['sk'] == 'pivot' else 'K 棒',
             '{:,}'.format(p['n']), 421506.0 / p['n']))
    w('</tbody></table>')
    w('<p>列的排法先分<b>骨架</b>再分密度：下面八列直接讀 OHLC，'
      '上面三列讀<b>樞紐位階</b>，是唯三帶「結構」而不只是「形狀」的。'
      '每一組裡最密的擺最下面，跟 CONV6 與標籤車道同一個慣例。</p>')

    w('<h2>二、四個裝置，全部零參數</h2>')
    w('<table><thead><tr><th>裝置</th><th>原本會是門檻的地方</th>'
      '<th>改寫成什麼</th></tr></thead><tbody>')
    for a, b_, c in (
        ('排名', '「區間夠大／夠小」', '比前 N 根每一根都大（P41 P42）'),
        ('影線 vs 實體', '「長上影線」＝ 影線 &gt; 實體的幾倍？',
         '上影線比實體長，就這樣（P47 P48）'),
        ('差距 vs 影線', '「兩個高點差不多齊」＝ 差幾點以內？',
         '差距小於兩根上影線裡較短的那一根 —— <b>容忍度由 K 棒自己提供</b>'),
        ('跑到分出勝負', '「旗形飄移 5 到 20 根」', '跑到收破旗桿低或穿越旗桿高'
         ' —— <b>「多長」這個問題不會被問到</b>（P13 P14）'),
    ):
        w('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (a, b_, c))
    w('</tbody></table>')
    w('<p>唯一的自由參數是 <b>N = 4 與 N = 7</b>，Crabel 的常數，'
      '2026-08-31 裁示接受並記錄為<b>借用</b>而非推導。'
      '其餘九種一個參數都沒有。</p>')

    w('<h2>三、十一條，逐條對照圖</h2>')
    for p in sorted(P, key=lambda x: x['row']):
        w('<div class="pat">')
        w('<div class="hd"><span class="id">%s</span><h3>%s</h3>'
          '<span class="en">%s</span></div>' % (p['id'], p['zh'], p['en']))
        w('<div class="meta"><span>方向 %s</span><span>骨架 %s</span>'
          '<span>跨度 %s</span><span>母體 %s</span>'
          '<span>色帶第 %d 列</span></div>'
          % (p['dr'], '樞紐' if p['sk'] == 'pivot' else 'K 棒', p['span'],
             '{:,}'.format(p['n']), p['row']))
        w('<p class="one">%s</p>' % p['one'])
        w('<div class="grid">')
        w('<div><div class="fig">%s</div>'
          '<p class="cap">%s</p></div>' % (svg(p), p['note']))
        w('<div>')
        w('<div class="blk"><h4>為什麼這樣定義</h4><p>%s</p></div>' % p['why'])
        w('<div class="blk"><h4>釘死的邊界</h4><p>%s</p></div>' % p['edge'])
        w('</div></div></div>')

    w('<h2>四、整支指標落後一根，而那是對的</h2>')
    w('<p>定義這十一種的腳本，會<b>跳過任何一根「下一根就開新時段」的 K 棒</b>，'
      '因為碎形樞紐的判定需要下一根。這代表一根 K 棒的分類'
      '<b>在它自己身上不可判定</b> —— 這支程式不行，坐在螢幕前的人也不行。</p>')
    w('<p>所以指標分類的是 <code>[1]</code>，標記畫在 <code>[0]</code>。'
      '<b>一個標記的意思是「在這裡被確認」，不是「形狀在這裡結束」。</b>'
      'P48 管狀頂把這件事講得最清楚：它的第二根要比<b>再下一根</b>高，'
      '所以在第二根當下根本不知道自己是不是管狀頂。</p>')
    w('<p>這跟 IND_S16S_P29 的樞紐鏈一直以來用的是同一個慣例，'
      '而且是實盤唯一守得住的慣例。</p>')

    w('<h2>五、旗桿清單：四槽，而不是「應該夠了」</h2>')
    w('<p>同一時間可以有好幾根旗桿活著。<b>實測整條序列最深是三根</b>'
      '（深度 3 出現 181 次，深度 2 出現 5,862 次），所以四槽是一格餘裕，'
      '第五根會去累加 <code>v_Ovf</code>，而那個數字印在驗收行上。</p>')
    w('<p><b>安靜的上限，是母體安靜地不再是母體的方式。</b></p>')

    w('<div class="note"><h3>兩件必須講明的事</h3>'
      '<b>一、順序錯了。</b>專案規範是「五段總整理 → 對照圖 → HTML → 才程式碼化」，'
      '而 2026-09-01 我是先寫進 <code>.pla</code> 才回頭補這一頁。'
      '內容補齊了，順序沒有補回來。'
      '<br><br><b>二、Build 260913 尚未在 MC12 編譯或執行。</b>'
      '本頁的母體數字來自 <code>s16s_eleven_pla_model.py</code> —— '
      '它用這支 .pla 真正的視窗（7 根暖身、狀態機從第 8 根空著起跑、一根落後）'
      '重放述詞，再與定義腳本<b>逐根對，11 種零分歧</b>。'
      '那是預測，不是結果。</div>')

    w('<div class="note"><h3>誠實聲明</h3>'
      '1. 十一張示意圖的座標都經過真實述詞斷言，斷言在 '
      '<code>s16s_eleven_make_logic_page.py</code> 的 <code>main()</code>。'
      '<br>2. 母體數字是<b>筆電</b>的 CSV（md5 47e4054f…）。'
      '桌機同一支腳本得到不同數字，見 '
      '<code>S16S_CSV_DIVERGENCE_20260901.md</code>。'
      '<br>3. <b>沒有任何報酬檢定。</b>本頁只講形狀怎麼被定義與偵測。'
      '<br>4. P13「旗形跨時段」是照<b>程式碼</b>寫的，'
      '定義腳本的註解說的是相反的事，那條分支實測走到 0 次。'
      '<br>5. 本文由 Claude 產出，未經第二方審查。</div>')
    w('</div>')
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(A))
    print('wrote %s' % OUT)
    print('  11 個型態，11 張示意圖，全部通過自我斷言')
    print('  合計母體 %s' % '{:,}'.format(sum(x['n'] for x in P)))


if __name__ == '__main__':
    main()
