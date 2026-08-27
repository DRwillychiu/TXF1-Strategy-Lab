# -*- coding: utf-8 -*-
"""P29 diagram -- both orderings, a real instance, and the defects drawing found.

Panel 1 draws BOTH pivot orderings because the user asked what happens when
PL3 comes first. The answer is not "everything shifts": the two orderings end
on different pivot types, which changes which trigger level arrives next, and
-- as panel 4 shows -- mechanically determines the three-way split.

Panel 4 carries two definition defects that drawing this exposed. Neither was
visible in the spec text.
"""
import io, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_P29_diagram.html'))

W, HH = 1000.0, 430.0
PAD_L, PAD_R, PAD_T, PAD_B = 54.0, 150.0, 32.0, 56.0

# ordering A: H first, ENDS on a pivot low -> midpoint dragged DOWN
A_PATH = [(4, 102), (12, 112), (22, 96), (34, 118), (45, 84),
          (58, 124), (70, 68), (80, 82), (90, 50), (97, 42)]
A_PV = [('PH3', 12, 112), ('PL3', 22, 96), ('PH2', 34, 118),
        ('PL2', 45, 84), ('PH1', 58, 124), ('PL1', 70, 68)]
A_BRK = (90, 50)

# ordering B: L first, ENDS on a pivot high -> midpoint dragged UP
B_PATH = [(4, 92), (12, 84), (24, 104), (36, 76), (48, 116),
          (60, 70), (72, 128), (84, 84), (92, 56), (97, 48)]
B_PV = [('PL3', 12, 84), ('PH3', 24, 104), ('PL2', 36, 76),
        ('PH2', 48, 116), ('PL1', 60, 70), ('PH1', 72, 128)]
B_BRK = (92, 56)

DEFS = ('<defs>'
        '<marker id="aR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9" class="ah"/></marker>'
        '<marker id="aL" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto"><path d="M9,1 L1,5 L9,9" class="ah"/></marker>'
        '</defs>')


def mk(xs, ys, w=W, h=HH, pl=PAD_L, pr=PAD_R, pt=PAD_T, pb=PAD_B):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (w - pl - pr) / float(x1 - x0)
    sy = (h - pt - pb) / float(y1 - y0)
    return (lambda x: pl + (x - x0) * sx, lambda y: h - pb - (y - y0) * sy)


def schematic(path, pvs, brk, badges=True):
    P = dict((k, (x, y)) for k, x, y in pvs)
    X, Y = mk([p[0] for p in path] + [97],
              [p[1] for p in path] + [136, 38])
    o = []

    def line(a, b, cls, to=None):
        (ax, ay), (bx, by) = a, b
        sl = (by - ay) / float(bx - ax)
        ex = to if to is not None else bx
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(ax), Y(ay), X(ex), Y(ay + sl * (ex - ax))))

    line(P['PH2'], P['PH1'], 'tlu', 97)
    line(P['PL2'], P['PL1'], 'tld', 97)
    line(P['PH3'], P['PH1'], 'tlu solid')
    line(P['PL3'], P['PL1'], 'tld solid')

    mo = (P['PH3'][1] + P['PL3'][1]) / 2.0
    mn = (P['PH1'][1] + P['PL1'][1]) / 2.0
    mx0 = (P['PH3'][0] + P['PL3'][0]) / 2.0
    mx1 = (P['PH1'][0] + P['PL1'][0]) / 2.0
    o.append('<line class="mid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (X(mx0), Y(mo), X(mx1), Y(mn)))
    for x, y in ((mx0, mo), (mx1, mn)):
        o.append('<circle class="midpt" cx="%.1f" cy="%.1f" r="3.4"/>' % (X(x), Y(y)))
    o.append('<text class="lbl mid-l" x="%.1f" y="%.1f">中點%s</text>'
             % (X(mx1) + 9, Y(mn) + 4, '下移' if mn < mo else '上移'))

    for lvl, tag in ((P['PH1'][1], '向上觸發位 = PH1'),
                     (P['PL1'][1], '向下觸發位 = PL1')):
        sx = X(P['PH1'][0]) if lvl > 100 else X(P['PL1'][0])
        o.append('<line class="map" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (sx, Y(lvl), W - PAD_R + 114, Y(lvl)))
        o.append('<text class="lbl map-l" x="%.1f" y="%.1f">%s</text>'
                 % (W - PAD_R + 6, Y(lvl) - 6, tag))

    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in path))

    for n, (k, x, y) in enumerate(pvs):
        cls = 'ph' if k[1] == 'H' else 'pl'
        last = (n == 5)
        o.append('<circle class="pv %s%s" cx="%.1f" cy="%.1f" r="%s"/>'
                 % (cls, ' lastpv' if last else '', X(x), Y(y), '7' if last else '5'))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s</text>'
                 % (cls, X(x), Y(y) + (-14 if cls == 'ph' else 21), k))
        o.append('<text class="ord" x="%.1f" y="%.1f">%d</text>'
                 % (X(x), Y(y) + (-27 if cls == 'ph' else 34), n + 1))

    o.append('<circle class="brkr" cx="%.1f" cy="%.1f" r="12"/>' % (X(brk[0]), Y(brk[1])))
    o.append('<circle class="brk" cx="%.1f" cy="%.1f" r="7"/>' % (X(brk[0]), Y(brk[1])))

    yb = HH - PAD_B + 28
    xa, xb = X(pvs[0][1]), X(pvs[5][1])
    o.append('<line class="span" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
             'marker-start="url(#aL)" marker-end="url(#aR)"/>' % (xa, yb, xb, yb))
    o.append('<text class="lbl span-l" x="%.1f" y="%.1f">有效期 = 形成所花的根數</text>'
             % ((xa + xb) / 2, yb - 9))

    if badges:
        for n, cx, cy in ((1, X(P['PH3'][0]) - 27, Y(P['PH3'][1]) + 22),
                          (2, X(P['PH1'][0]) + 28, Y(P['PH1'][1]) - 12),
                          (3, X(mx0) - 8, Y((mo + mn) / 2) - 22),
                          (4, X(P['PL1'][0]) - 28, Y(P['PL1'][1]) + 22),
                          (5, X(brk[0]) + 23, Y(brk[1]) + 14),
                          (6, (xa + xb) / 2, yb)):
            o.append('<circle class="bg" cx="%.1f" cy="%.1f" r="11"/>' % (cx, cy))
            o.append('<text class="bgt" x="%.1f" y="%.1f">%d</text>' % (cx, cy + 4, n))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s%s</svg>' % (W, HH, DEFS, ''.join(o))


def real():
    d = json.load(open(os.path.join(HERE, 's16s_p29_example.json'), encoding='utf-8'))
    bars, piv, brk, lo = d['bars'], d['piv'], d['brk'], d['lo']
    n = len(bars)
    X, Y = mk(list(range(n)), [b['h'] for b in bars] + [b['l'] for b in bars])
    bw = max((W - PAD_L - PAD_R) / float(n) * 0.56, 3.0)
    o = []
    KEY = {'PH3': 'h3', 'PH2': 'h2', 'PH1': 'h1', 'PL3': 'l3', 'PL2': 'l2', 'PL1': 'l1'}
    P = dict((k, piv[v] - lo) for k, v in KEY.items())
    pa, pb = min(P.values()), max(P.values())

    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
             % (X(pa) - bw, PAD_T - 4, X(pb) - X(pa) + 2 * bw, HH - PAD_T - PAD_B + 10))
    o.append('<text class="zt" x="%.1f" y="%.1f">型態形成區間　%s ~ %s　共 %d 根</text>'
             % ((X(pa) + X(pb)) / 2, PAD_T + 8,
                bars[pa]['t'][-4:], bars[pb]['t'][-4:], pb - pa + 1))

    def ln(k2, k1, cls, to=None):
        a, b = P[k2], P[k1]
        va = bars[a]['h'] if k2[1] == 'H' else bars[a]['l']
        vb = bars[b]['h'] if k1[1] == 'H' else bars[b]['l']
        sl = (vb - va) / float(b - a)
        e = to if to is not None else b
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(a), Y(va), X(e), Y(va + sl * (e - a))))

    ln('PH2', 'PH1', 'tlu', n - 1)
    ln('PL2', 'PL1', 'tld', n - 1)
    ln('PH3', 'PH1', 'tlu solid')
    ln('PL3', 'PL1', 'tld solid')
    for i, b in enumerate(bars):
        cls = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, x, Y(b['h']), x, Y(b['l'])))
        t, bt = Y(max(b['o'], b['c'])), Y(min(b['o'], b['c']))
        if bt - t < 1.4:
            m = (t + bt) / 2.0
            t, bt = m - .7, m + .7
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (cls, x - bw / 2, t, bw, bt - t))
    for rank, (k, i) in enumerate(sorted(P.items(), key=lambda kv: kv[1])):
        b = bars[i]
        v = b['h'] if k[1] == 'H' else b['l']
        cls = 'ph' if k[1] == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.8"/>' % (cls, X(i), Y(v)))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s %.0f</text>'
                 % (cls, X(i), Y(v) + (-11 if cls == 'ph' else 18), k, v))
        o.append('<text class="ord" x="%.1f" y="%.1f">%d</text>'
                 % (X(i), Y(v) + (-24 if cls == 'ph' else 31), rank + 1))
    bi = brk - lo
    o.append('<circle class="brkr" cx="%.1f" cy="%.1f" r="11"/>' % (X(bi), Y(bars[bi]['c'])))
    o.append('<circle class="brk" cx="%.1f" cy="%.1f" r="6"/>' % (X(bi), Y(bars[bi]['c'])))
    o.append('<text class="lbl brk-l" x="%.1f" y="%.1f">%s 收盤 %.0f 跌破下緣</text>'
             % (X(bi) + 14, Y(bars[bi]['c']) + 4, bars[bi]['t'][-4:], bars[bi]['c']))
    step = max(n // 9, 1)
    for i in list(range(0, n, step)) + [n - 1]:
        o.append('<text class="ax" x="%.1f" y="%.1f">%s</text>'
                 % (X(i), HH - PAD_B + 22, bars[i]['t'][-4:]))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o)), d


def variant(rise, fall, label, pct, sub):
    pts = [(4, 100), (14, 100 + rise * .3), (26, 100 - fall * .3),
           (40, 100 + rise * .65), (54, 100 - fall * .65),
           (70, 100 + rise), (84, 100 - fall), (94, 100 - fall * .55)]
    X, Y = mk([p[0] for p in pts], [p[1] for p in pts], 260, 132, 16, 16, 12, 12)
    mo = (100 + rise * .3 + 100 - fall * .3) / 2.0
    mn = (100 + rise + 100 - fall) / 2.0
    return ('<figure class="vf"><svg viewBox="0 0 260 132">'
            '<line class="mid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '<polyline class="px" points="%s"/>'
            '<line class="tlu" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '<line class="tld" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/></svg>'
            '<figcaption><b>%s</b><span>%s</span></figcaption>'
            '<div class="vsub">%s</div></figure>'
            % (X(20), Y(mo), X(77), Y(mn),
               ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts),
               X(14), Y(100 + rise * .3), X(70), Y(100 + rise),
               X(26), Y(100 - fall * .3), X(84), Y(100 - fall),
               label, pct, sub))


LEG = [
 (1, '§1 樞紐定義', '綠點 ＝ 樞紐高，橘點 ＝ 樞紐低。小數字 ＝ 出現順序',
  '純分形：<code>H[i] &gt; H[i-1]</code> 且 <code>H[i] &gt; H[i+1]</code>。'
  'i-1／i／i+1 須同時段，<b>不加 ATR 門檻</b>。'
  'S1 雙尺度：同一型態在視窗 1 與視窗 2 都成立才算穩健（<b>尚未實測</b>）。'),
 (2, '§2 型態成立', '兩條線向外張開，粗線＝已確認段，虛線＝外推段',
  '三個樞紐高單調墊高、三個樞紐低單調下移，<b>對稱 3+3</b>。'
  '2026-08-25 新增：<b>六個樞紐必須在時間上交替</b>，且低點須在高點下方 —— '
  '不加這兩條，九成抓到的東西兩條線會交叉。'),
 (3, '§3 三向細分', '灰色點線 ＝ 中點連線',
  '<code>中點 = (PH+PL)/2</code>。'
  '<b>⚠️ 已證實為定義假象</b>：方向由「型態以哪種樞紐收尾」機械決定，'
  '不是市場資訊。見第四面板。'),
 (4, '§4 事前價位地圖', '紫色水平虛線',
  '型態<b>未完成前</b>就算得出來：下一個樞紐要越過 <code>PH1</code>／<code>PL1</code> '
  '才會完成 P29。同一組狀態同時算得出下降三角、上升三角、對稱三角、箱型、'
  '下降通道的觸發位。<b>兩種排列的下一個觸發位不同</b>：'
  '以低收尾者下一個等的是高，反之亦然。'),
 (5, '§5 突破確認', '紅色大點',
  'E1 外推（通過最後兩個樞紐低）＋ <b>收盤價</b>跌破。'
  '單根、嚴格小於、影線不算、無幅度門檻、假突破不撤銷確認。'),
 (6, '§6 有效期', '底部雙箭頭',
  '有效期 ＝ 型態自己形成所花的根數。<b>自我指涉，沒有可調的 N。</b>'
  '乾淨定義下跨度中位數 <b>11 根</b>。'),
]

CASCADE = [('有三高三低可用', '75,125', '', 0),
           ('＋ 單調外擴 3+3（原 §2）', '1,119', '1.5%', 0),
           ('＋ 樞紐必須交替 H L H L …', '111', '剩 9.9%', 1),
           ('＋ 低點必須在高點下方', '103', '92.8%', 0),
           ('＋ 整個型態同一時段', '85', '82.5%', 0),
           ('★ 改為對稱掃描後（兩種排列都抓）', '172', '＋102%', 2)]


# shared with s16s_p51_p54_make_diagram.py -- one stylesheet, so the two
# pages cannot drift apart
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

rl, d = real()
b0, b1 = d['bars'][0], d['bars'][-1]
DATE = b0['t'][:8]
DATE_F = '%s-%s-%s' % (DATE[:4], DATE[4:6], DATE[6:8])

leg = ''.join('<div class="li"><div class="n">%d</div><div class="bd2">'
              '<h3>%s</h3><div class="vis">%s</div><p>%s</p></div></div>'
              % (n, t, v, p) for n, t, v, p in LEG)

rowsc = ''.join('<tr%s><td>%s</td><td>%s</td><td>%s</td></tr>'
                % ('' if f == 0 else (' class="hit"' if f == 1 else ' class="good"'),
                   a, b, c) for a, b, c, f in CASCADE)

HEAD = ('<title>P29 擴散三角 — 規格示意圖</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + '</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S_MACrossShort v1.26.0 · Build_ID 260825 · 2026-08-25</div>'
       '<h1>P29 擴散三角 — 規格示意圖</h1>'
       '<p class="sub">高點一個比一個高、低點一個比一個低，<b>波動整段向外擴張</b>。'
       '跟三角形正好相反：三角是兩條線往中間收，擴散是往外開。'
       '所有數字量自 <b>421,513 根 5 分 K，2019-01-02 ~ 2026-08-22</b>。</p>'
       '<div class="kpi">'
       '<span><b>0</b>自由參數</span>'
       '<span><b>172</b>乾淨定義下的實例（8 年）</span>'
       '<span><b>11</b>跨度中位數（根）</span>'
       '<span><b>22.5</b>年均個數</span>'
       '<span><b>421,513</b>母體 5 分 K</span>'
       '</div></header>')

P1 = ('<section class="panel"><div class="ph2"><h2>一、示意圖 — 兩種排列</h2>'
      '<span class="tag">編號 1-6 ＝ 規格段落；樞紐旁小數字 ＝ 出現順序</span></div>'
      '<div class="two">'
      '<div class="sc"><p class="sct">排列 A：先出現樞紐高'
      '<em>H L H L H L　·　以樞紐低收尾　·　91 個 / 52.9%</em></p>'
      '<div class="plot">' + schematic(A_PATH, A_PV, A_BRK) + '</div></div>'
      '<div class="sc"><p class="sct">排列 B：先出現樞紐低'
      '<em>L H L H L H　·　以樞紐高收尾　·　81 個 / 47.1%</em></p>'
      '<div class="plot">' + schematic(B_PATH, B_PV, B_BRK, badges=False) + '</div></div>'
      '</div>'
      '<p class="warn"><b>不是單純把 PH3/2/1 往後推移。</b>'
      '兩種排列<b>收尾的樞紐型別不同</b>：排列 A 以樞紐低收尾，'
      '所以下一個要等的是樞紐高；排列 B 反過來。'
      '這決定 §4 哪個觸發位先到、§5 哪條線是當下的操作線 —— '
      '而且如第四面板所示，它<b>機械性地決定了 §3 的方向判讀</b>。</p></section>')

P2 = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
      '<span class="tag">從 421,513 根裡由程式選出，不是示意</span></div>'
      '<p class="cap"><b>日期</b> %s（夜盤）　'
      '<b>顯示區間</b> %s ~ %s，共 %d 根 5 分 K　'
      '<b>型態形成區間</b> 紫框處　'
      '<b>價格範圍</b> %.0f ~ %.0f</p>'
      '<div class="plot">%s</div>'
      '<p class="warn">每一根都是真實 K 棒，六個樞紐、兩條趨勢線、突破那一根'
      '全部由程式判定，非人工挑點。'
      '<b>上緣擴 22 點、下緣擴 24 點</b> —— 這是 P29 在 5 分 K 上的真實振幅，'
      '示意圖為了看得清楚放大了比例。'
      '選取依據只有形狀（跨度、樞紐不擠在一起、有無突破），'
      '<b>無損益欄、不依報酬排序</b>。</p></section>'
      % (DATE_F, b0['t'][-4:], b1['t'][-4:], len(d['bars']),
         min(b['l'] for b in d['bars']), max(b['h'] for b in d['bars']), rl))

P3 = ('<section class="panel"><div class="ph2"><h2>三、三向細分</h2>'
      '<span class="tag">母體 421,513 根 · 2019-01-02 ~ 2026-08-22 · '
      '乾淨定義下 n = 172</span></div>'
      '<div class="vars">'
      + variant(9, 34, '下降擴散', '48.8%', '中點往下漂。以樞紐低收尾者佔 63.7%')
      + variant(34, 9, '上升擴散', '48.3%', '中點往上漂。以樞紐高收尾者佔 65.4%')
      + variant(22, 22, '水平擴散', '2.9%', '中點完全不動。兩種排列都約 3%')
      + '</div>'
      '<p class="warn"><b>⚠️ 這個細分已被證實是定義假象，不是市場資訊。</b>'
      '中點新 ＝（最後一個高 ＋ 最後一個低）/ 2。'
      '以樞紐低收尾時，最後一點必然是整段最低的低，中點被機械性拉下；'
      '以樞紐高收尾時反之。<b>方向由排列決定，不由行情決定</b> —— '
      '和 Bulkowski 3+2 那個陷阱是同一類錯誤。</p></section>')

P4 = ('<section class="panel"><div class="ph2">'
      '<h2>四、★ 畫圖才發現的兩個規格缺陷</h2>'
      '<span class="tag">2026-08-25</span></div>'
      '<p class="warn"><b>缺陷一：§2 沒有要求樞紐交替。</b>'
      '原文只說「三高遞增、三低遞減」，'
      '所以會抓到<b>下緣線在上緣線之上</b>的形狀 —— 兩條線交叉，'
      '那不是任何人會叫做喇叭形的東西。</p>'
      '<p class="warn"><b>缺陷二：偵測器本身不對稱。</b>'
      '舊寫法錨定「最近三個樞紐高」，低點一律取在 PH1 之前，'
      '<b>只找得到以樞紐高收尾的型態</b>，另外 91 個被系統性漏掉。'
      '改成在時間序上掃描任何六個連續交替樞紐後，總數 85 → <b>172</b>。'
      '這是用戶問「先出現 PL3 會怎樣」才被翻出來的。</p>'
      '<table><thead><tr><th>每加一個要求</th><th>剩下</th><th>變化</th></tr>'
      '</thead><tbody>' + rowsc + '</tbody></table>'
      '<p class="warn ok"><b>先畫出來，才會知道哪裡有問題。</b>'
      '這兩個缺陷在規格文字上完全看不出來，'
      '是把圖畫出來、發現第一個實例的下緣在上緣之上，才被抓到的。'
      '兩者都待你裁示是否寫進 §2。</p></section>')

P5 = ('<section class="panel"><div class="ph2"><h2>五、分布</h2>'
      '<span class="tag">乾淨定義 n = 172</span></div>'
      '<table><thead><tr><th>面向</th><th>數值</th><th>備註</th></tr></thead><tbody>'
      '<tr><td>逐年</td><td>7 / 9 / 14 / 28 / 18 / 27 / 36 / 33</td>'
      '<td>2019 → 2026</td></tr>'
      '<tr><td>跨度</td><td>中位數 11 根</td><td>最短 5，最長 43</td></tr>'
      '<tr class="hit"><td>時段</td><td>日盤 23 ／ 夜盤 149</td>'
      '<td>母體本身 1 : 2.80，型態 1 : 6.48 → <b>夜盤超額 2.3 倍</b></td></tr>'
      '<tr><td>年均</td><td>22.5 個</td><td>8 年 172 個</td></tr>'
      '</tbody></table>'
      '<p class="warn">夜盤超額 2.3 倍是新發現，尚未解釋。'
      '合理猜測是夜盤流動性較薄、來回掃動較多，'
      '但<b>這只是猜測，未經檢定</b>。</p></section>')

FOOT = ('<section><div class="legend">' + leg + '</div></section>'
        '<footer class="foot">'
        '示意圖 <code>s16s_p29_make_diagram.py</code>　·　'
        '真實案例 <code>s16s_p29_find_example.py</code>　·　'
        '要求層級 <code>s16s_p29_interleave_test.py</code>　·　'
        '對稱掃描與分布 <code>s16s_p29_clean.py</code>　·　'
        '全部<b>無損益欄</b>。'
        '規格全文 <code>docs/research/S16S_P29_logic_spec_20260825.md</code>，'
        '五段總整理 <code>S16S_P29_SUMMARY_20260825.md</code>。'
        '</footer></div>')

open(OUT, 'w', encoding='utf-8').write(HEAD + TOP + P1 + P2 + P3 + P4 + P5 + FOOT)
print('wrote %s' % OUT)
