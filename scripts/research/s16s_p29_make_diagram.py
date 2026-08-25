# -*- coding: utf-8 -*-
"""P29 diagram -- schematic, a REAL instance, the variants, and the spec gap.

Four panels rather than one, because a schematic alone cannot show what the
rule actually picks up. Panel 2 renders a genuine P29 out of the 421,513-bar
series with its real pivots and its real close-based break; panel 4 carries
the requirement cascade that drawing panel 2 uncovered.
"""
import io, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_P29_diagram.html'))

W, HH = 1000.0, 470.0
PAD_L, PAD_R, PAD_T, PAD_B = 58.0, 132.0, 34.0, 62.0

# ---------------- schematic: alternating pivots, midpoint drifting down ------
SCH = [(4, 102), (12, 112), (22, 96), (34, 118), (45, 84),
       (58, 124), (70, 68), (80, 82), (90, 50), (97, 42)]
PV = {'PH3': (12, 112), 'PH2': (34, 118), 'PH1': (58, 124),
      'PL3': (22, 96), 'PL2': (45, 84), 'PL1': (70, 68)}
BRK = (90, 50)


def mk(xs, ys, w=W, h=HH):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (w - PAD_L - PAD_R) / float(x1 - x0)
    sy = (h - PAD_T - PAD_B) / float(y1 - y0)
    return (lambda x: PAD_L + (x - x0) * sx,
            lambda y: h - PAD_B - (y - y0) * sy)


def schematic():
    xs = [p[0] for p in SCH] + [97]
    ys = [p[1] for p in SCH] + [136, 40]
    X, Y = mk(xs, ys)
    o = []

    def line(a, b, cls, x_to=None):
        (ax, ay), (bx, by) = a, b
        sl = (by - ay) / float(bx - ax)
        ex = x_to if x_to is not None else bx
        ey = ay + sl * (ex - ax)
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(ax), Y(ay), X(ex), Y(ey)))

    # trendlines, extrapolated to the right edge (E1: through the last two)
    line(PV['PH2'], PV['PH1'], 'tlu', 97)
    line(PV['PL2'], PV['PL1'], 'tld', 97)
    # the segment of each line that is "confirmed" (pivot to pivot) drawn solid
    line(PV['PH3'], PV['PH1'], 'tlu solid')
    line(PV['PL3'], PV['PL1'], 'tld solid')
    # midpoint drift
    mo = (PV['PH3'][1] + PV['PL3'][1]) / 2.0
    mn = (PV['PH1'][1] + PV['PL1'][1]) / 2.0
    o.append('<line class="mid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (X(17), Y(mo), X(64), Y(mn)))
    for x, y, t in ((17, mo, '中點舊'), (64, mn, '中點新')):
        o.append('<circle class="midpt" cx="%.1f" cy="%.1f" r="3.4"/>' % (X(x), Y(y)))
    o.append('<text class="lbl mid-l" x="%.1f" y="%.1f">中點下移 = 下降擴散</text>'
             % (X(64) + 9, Y(mn) + 4))
    # price map: the two trigger levels available BEFORE the third pivot
    for lvl, tag in ((PV['PH1'][1], '向上觸發位 = PH1'), (PV['PL1'][1], '向下觸發位 = PL1')):
        o.append('<line class="map" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (X(58) if lvl > 100 else X(70), Y(lvl), W - PAD_R + 96, Y(lvl)))
        o.append('<text class="lbl map-l" x="%.1f" y="%.1f">%s</text>'
                 % (W - PAD_R + 8, Y(lvl) - 6, tag))
    # price path
    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in SCH))
    # pivots
    for k, (x, y) in PV.items():
        cls = 'ph' if k[1] == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="5"/>' % (cls, X(x), Y(y)))
        dy = -12 if cls == 'ph' else 19
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s</text>'
                 % (cls, X(x), Y(y) + dy, k))
    # breakout
    o.append('<circle class="brk" cx="%.1f" cy="%.1f" r="7"/>' % (X(BRK[0]), Y(BRK[1])))
    o.append('<circle class="brkr" cx="%.1f" cy="%.1f" r="12"/>' % (X(BRK[0]), Y(BRK[1])))
    # life span arrow
    yb = HH - PAD_B + 30
    o.append('<line class="span" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
             'marker-start="url(#aL)" marker-end="url(#aR)"/>'
             % (X(12), yb, X(58), yb))
    o.append('<text class="lbl span-l" x="%.1f" y="%.1f">有效期 = 形成所花的根數</text>'
             % ((X(12) + X(58)) / 2, yb - 9))
    # numbered badges
    for n, (x, y, ox, oy) in ((1, (12, 112, -26, 22)), (2, (58, 124, 26, -14)),
                              (3, (40, (mo + mn) / 2, -4, -20)), (4, (70, 68, -26, 20)),
                              (5, (90, 50, 22, 12)), (6, (35, 0, 0, 0))):
        if n == 6:
            cx, cy = (X(12) + X(58)) / 2, yb
        else:
            cx, cy = X(x) + ox, Y(y) + oy
        o.append('<circle class="bg" cx="%.1f" cy="%.1f" r="11"/>' % (cx, cy))
        o.append('<text class="bgt" x="%.1f" y="%.1f">%d</text>' % (cx, cy + 4, n))
    return ('<svg viewBox="0 0 %.0f %.0f" role="img" aria-label="P29 示意圖">'
            '%s%s</svg>' % (W, HH, DEFS, ''.join(o)))


DEFS = ('<defs>'
        '<marker id="aR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto"><path d="M0,1 L9,5 L0,9" class="ah"/></marker>'
        '<marker id="aL" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto"><path d="M9,1 L1,5 L9,9" class="ah"/></marker>'
        '</defs>')


# ---------------- panel 2: the real instance --------------------------------
def real():
    d = json.load(open(os.path.join(HERE, 's16s_p29_example.json'), encoding='utf-8'))
    bars, piv, brk, lo = d['bars'], d['piv'], d['brk'], d['lo']
    n = len(bars)
    xs = list(range(n))
    ys = [b['h'] for b in bars] + [b['l'] for b in bars]
    X, Y = mk(xs, ys)
    bw = max((W - PAD_L - PAD_R) / float(n) * 0.56, 3.0)
    o = []
    # the json uses h3/h2/h1/l3/l2/l1; the drawing code speaks PH3..PL1
    KEY = {'PH3': 'h3', 'PH2': 'h2', 'PH1': 'h1',
           'PL3': 'l3', 'PL2': 'l2', 'PL1': 'l1'}
    P = dict((k, piv[v] - lo) for k, v in KEY.items())

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
    for k, i in P.items():
        b = bars[i]
        v = b['h'] if k[1] == 'H' else b['l']
        cls = 'ph' if k[1] == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.6"/>' % (cls, X(i), Y(v)))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s %.0f</text>'
                 % (cls, X(i), Y(v) + (-11 if cls == 'ph' else 18), k, v))
    bi = brk - lo
    o.append('<circle class="brk" cx="%.1f" cy="%.1f" r="6"/>' % (X(bi), Y(bars[bi]['c'])))
    o.append('<circle class="brkr" cx="%.1f" cy="%.1f" r="11"/>' % (X(bi), Y(bars[bi]['c'])))
    o.append('<text class="lbl brk-l" x="%.1f" y="%.1f">收盤 %.0f 跌破下緣</text>'
             % (X(bi) + 15, Y(bars[bi]['c']) + 4, bars[bi]['c']))
    for i in (0, n - 1):
        o.append('<text class="ax" x="%.1f" y="%.1f">%s</text>'
                 % (X(i), HH - PAD_B + 26, bars[i]['t'][-4:]))
    return ('<svg viewBox="0 0 %.0f %.0f" role="img" aria-label="P29 真實案例">%s</svg>'
            % (W, HH, ''.join(o))), d


# ---------------- panel 3: the three variants -------------------------------
def variant(hi_rise, lo_fall, label, pct):
    pts = [(4, 100), (14, 100 + hi_rise * .3), (26, 100 - lo_fall * .3),
           (40, 100 + hi_rise * .65), (54, 100 - lo_fall * .65),
           (70, 100 + hi_rise), (84, 100 - lo_fall), (94, 100 - lo_fall * .55)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    X, Y = mk(xs, ys, 260, 150)
    mo = (100 + hi_rise * .3 + 100 - lo_fall * .3) / 2.0
    mn = (100 + hi_rise + 100 - lo_fall) / 2.0
    return ('<figure class="vf"><svg viewBox="0 0 260 150">'
            '<line class="mid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '<polyline class="px" points="%s"/>'
            '<line class="tlu" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '<line class="tld" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
            '</svg><figcaption><b>%s</b><span>%s</span></figcaption></figure>'
            % (X(14), Y(mo), X(70), Y(mn),
               ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts),
               X(14), Y(100 + hi_rise * .3), X(70), Y(100 + hi_rise),
               X(26), Y(100 - lo_fall * .3), X(84), Y(100 - lo_fall),
               label, pct))


LEG = [
 (1, '§1 樞紐定義', '綠點 ＝ 樞紐高，橘點 ＝ 樞紐低',
  '純分形：<code>H[i] &gt; H[i-1]</code> 且 <code>H[i] &gt; H[i+1]</code>。'
  'i-1／i／i+1 須同時段，<b>不加 ATR 門檻</b>。'
  'S1 雙尺度：同一型態在視窗 1 與視窗 2 都成立才算穩健。'),
 (2, '§2 型態成立', '兩條線向外張開',
  '三個樞紐高單調墊高 <code>PH3&lt;PH2&lt;PH1</code>，'
  '三個樞紐低單調下移 <code>PL3&gt;PL2&gt;PL1</code>。'
  '<b>對稱 3+3，不是 Bulkowski 的 3+2</b> —— 3+2 報 75.5% 上升，'
  '鏡像的 2+3 立刻報 76.9% 下降，那是定義不對稱造出來的假象。'),
 (3, '§3 三向細分', '灰色點線 ＝ 中點連線',
  '<code>中點 = (PH+PL)/2</code>。往下走＝下降擴散 50.4%，'
  '往上＝上升 47.1%，完全相等＝水平 2.5%。'
  '<b>頻率上是硬幣，細分沒有集中任何東西。</b>'),
 (4, '§4 事前價位地圖', '紫色水平虛線',
  '型態<b>未完成前</b>就算得出來：手上有兩個樞紐高低時，'
  '下一個樞紐要越過 <code>PH1</code>／<code>PL1</code> 才會完成 P29。'
  '同一組狀態同時算得出下降三角、上升三角、對稱三角、箱型、下降通道的觸發位。'),
 (5, '§5 突破確認', '紅色大點',
  'E1 外推（通過最後兩個樞紐低）＋ <b>收盤價</b>跌破。'
  '單根、嚴格小於、影線不算、無幅度門檻、假突破不撤銷確認。'),
 (6, '§6 有效期', '底部雙箭頭',
  '有效期 ＝ 型態自己形成所花的根數。<b>自我指涉，沒有可調的 N。</b>'
  '震盪盤形成得慢，有效期自動變長。'),
]

CASCADE = [('有三高三低可用', 75125, ''),
           ('＋ 單調外擴 3+3（<b>現行 §2</b>）', 1119, '1.5%'),
           ('＋ <b>樞紐必須交替 H L H L H L</b>', 111, '<b>剩 9.9%</b>'),
           ('＋ 低點必須在高點下方', 103, '92.8%'),
           ('＋ 整個型態同一時段', 85, '82.5%')]


CSS = """
:root{
  --ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
  --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
  --up:#c8302e;--dn:#17795e;
  --ph:#0f9d76;--pl:#d97528;--brk:#d1382f;--map:#7a5cc4;--midc:#8a93a3;
  --serif:'Noto Serif TC',Georgia,'Songti TC',serif;
  --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
  --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
  --up:#e8564e;--dn:#3ec08d;
  --ph:#3ecfa0;--pl:#f0a04b;--brk:#ff6b5e;--map:#a98ce8;--midc:#79828f;
}}
:root[data-theme="dark"]{
  --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
  --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
  --up:#e8564e;--dn:#3ec08d;
  --ph:#3ecfa0;--pl:#f0a04b;--brk:#ff6b5e;--map:#a98ce8;--midc:#79828f;
}
:root[data-theme="light"]{
  --ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
  --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
  --up:#c8302e;--dn:#17795e;
  --ph:#0f9d76;--pl:#d97528;--brk:#d1382f;--map:#7a5cc4;--midc:#8a93a3;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:46px 20px 84px;
  display:flex;flex-direction:column;gap:38px}
.top{display:flex;flex-direction:column;gap:9px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.12em;
  color:var(--ink3);text-transform:uppercase}
h1{font-family:var(--serif);font-weight:700;margin:0;
  font-size:clamp(26px,4vw,38px);letter-spacing:-.01em;text-wrap:balance}
.sub{margin:0;color:var(--ink2);font-size:15px;max-width:70ch}
.sub b{color:var(--ink);font-weight:700}
.kpi{display:flex;flex-wrap:wrap;gap:9px;margin-top:4px}
.kpi span{display:flex;flex-direction:column;gap:1px;padding:8px 14px;
  border:1px solid var(--line);border-radius:4px;background:var(--card);
  font-size:12px;color:var(--ink3)}
.kpi b{font-family:var(--mono);font-size:17px;color:var(--ink);font-weight:500;
  font-variant-numeric:tabular-nums}
.panel{background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding:20px 22px;display:flex;flex-direction:column;gap:12px}
.ph2{display:flex;align-items:baseline;gap:11px;flex-wrap:wrap;margin:0}
.ph2 h2{font-family:var(--serif);font-size:18px;font-weight:700;margin:0}
.ph2 .tag{font-family:var(--mono);font-size:11px;color:var(--ink3)}
.plot{width:100%;overflow-x:auto}
.plot svg{width:100%;min-width:660px;height:auto;display:block}
.px{fill:none;stroke:var(--ink2);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.tlu,.tld{stroke-width:1.5;stroke-dasharray:5 3.5;fill:none;opacity:.9}
.tlu{stroke:var(--ph)}.tld{stroke:var(--pl)}
.tlu.solid,.tld.solid{stroke-dasharray:none;stroke-width:2.2;opacity:1}
.mid{stroke:var(--midc);stroke-width:1.4;stroke-dasharray:1.5 3;stroke-linecap:round}
.midpt{fill:var(--midc)}
.map{stroke:var(--map);stroke-width:1.3;stroke-dasharray:4 3;opacity:.85}
.pv{stroke:var(--card);stroke-width:2}
.pv.ph{fill:var(--ph)}.pv.pl{fill:var(--pl)}
.pvl{font-family:var(--mono);font-size:11px;text-anchor:middle;font-weight:500}
.pvl.ph{fill:var(--ph)}.pvl.pl{fill:var(--pl)}
.brk{fill:var(--brk)}
.brkr{fill:none;stroke:var(--brk);stroke-width:1.6;opacity:.5}
.lbl{font-family:var(--sans);font-size:11.5px;fill:var(--ink3)}
.map-l{fill:var(--map);font-family:var(--mono);font-size:11px}
.mid-l{fill:var(--midc)}
.brk-l{fill:var(--brk);font-weight:600}
.span{stroke:var(--ink3);stroke-width:1.2}
.ah{fill:var(--ink3)}
.span-l{text-anchor:middle;fill:var(--ink3)}
.ax{font-family:var(--mono);font-size:10.5px;fill:var(--ink3);text-anchor:middle}
.bg{fill:var(--ink);opacity:.9}
.bgt{fill:var(--card);font-family:var(--mono);font-size:12px;font-weight:600;
  text-anchor:middle}
.wk{stroke-width:1.3}.wk.up{stroke:var(--up)}.wk.dn{stroke:var(--dn)}
.bd.up{fill:var(--card);stroke:var(--up);stroke-width:1.3}
.bd.dn{fill:var(--dn);stroke:var(--dn);stroke-width:1.3}
.legend{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;grid-template-columns:repeat(auto-fit,minmax(430px,1fr))}
.li{background:var(--card);padding:14px 16px;display:flex;gap:12px}
.li .n{flex:0 0 24px;height:24px;border-radius:50%;background:var(--ink);
  color:var(--card);font-family:var(--mono);font-size:12px;font-weight:600;
  display:flex;align-items:center;justify-content:center;margin-top:1px}
.li .bd2{display:flex;flex-direction:column;gap:2px}
.li h3{margin:0;font-family:var(--serif);font-size:14.5px;font-weight:700}
.li .vis{font-size:11px;color:var(--ink3);font-family:var(--mono)}
.li p{margin:3px 0 0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.li b{color:var(--ink);font-weight:700}
.vars{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.vf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:10px;display:flex;flex-direction:column;gap:6px}
.vf svg{width:100%;height:auto}
.vf figcaption{display:flex;align-items:baseline;gap:8px}
.vf b{font-family:var(--serif);font-size:13.5px}
.vf span{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--ink3);
  font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:9px 12px;border-bottom:1px solid var(--line2);text-align:right}
th:first-child,td:first-child{text-align:left}
th{font-size:11px;color:var(--ink3);font-weight:600;letter-spacing:.03em;
  border-bottom:1px solid var(--line)}
td{font-family:var(--mono);font-variant-numeric:tabular-nums;color:var(--ink2)}
td:first-child{font-family:var(--sans);color:var(--ink)}
tr.hit td{background:rgba(209,56,47,.08);color:var(--brk)}
tr.hit td:first-child{color:var(--brk)}
.warn{border-left:3px solid var(--brk);padding:2px 0 2px 13px;margin:0;
  font-size:13px;color:var(--ink2)}
.warn b{color:var(--ink)}
code{font-family:var(--mono);font-size:.9em;color:var(--ink2)}
.foot{border-top:1px solid var(--line);padding-top:16px;color:var(--ink3);
  font-size:12px;max-width:88ch}
"""

sch = schematic()
rl, d = real()
b0, b1 = d['bars'][0], d['bars'][-1]

leg = ''.join('<div class="li"><div class="n">%d</div><div class="bd2">'
              '<h3>%s</h3><div class="vis">%s</div><p>%s</p></div></div>'
              % (n, t, v, p) for n, t, v, p in LEG)

vs = (variant(9, 34, '下降擴散', '50.4%')
      + variant(34, 9, '上升擴散', '47.1%')
      + variant(22, 22, '水平擴散', '2.5%'))

rowsc = ''.join('<tr%s><td>%s</td><td>%s</td><td>%s</td></tr>'
                % (' class="hit"' if '交替' in a else '', a, format(b, ','), c)
                for a, b, c in CASCADE)

HEAD = ('<title>P29 擴散三角 — 規格示意圖</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + '</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S_MACrossShort v1.26.0 · Build_ID 260825 · 2026-08-25</div>'
       '<h1>P29 擴散三角 — 規格示意圖</h1>'
       '<p class="sub">高點一個比一個高、低點一個比一個低，'
       '<b>波動整段向外擴張</b>。跟三角形正好相反：三角是兩條線往中間收，'
       '擴散是往外開。下圖編號對應規格六段。</p>'
       '<div class="kpi">'
       '<span><b>0</b>自由參數</span>'
       '<span><b>6,238</b>成立根數 · 1.480%</span>'
       '<span><b>17</b>跨度中位數（根）</span>'
       '<span><b>421,513</b>母體 5 分 K</span>'
       '</div></header>')

P1 = ('<section class="panel"><div class="ph2"><h2>一、示意圖</h2>'
      '<span class="tag">下降擴散，含突破。編號對應規格段落</span></div>'
      '<div class="plot">' + sch + '</div></section>')

P2 = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
      '<span class="tag">%s ~ %s ／ %d 根 ／ 從 421,513 根裡抓出來，不是示意</span>'
      '</div><div class="plot">%s</div>'
      '<p class="warn">每一根都是真實 K 棒，六個樞紐、兩條趨勢線、突破那一根'
      '全部由程式判定，非人工挑點。'
      '<b>上緣擴 22 點、下緣擴 24 點</b> —— 這是 P29 在 5 分 K 上的真實振幅，'
      '示意圖為了看得清楚放大了比例。</p></section>'
      % (b0['t'], b1['t'], len(d['bars']), rl))

P3 = ('<section class="panel"><div class="ph2"><h2>三、三向細分</h2>'
      '<span class="tag">依中點連線走向分類</span></div>'
      '<div class="vars">' + vs + '</div>'
      '<p class="warn"><b>頻率上是硬幣（47 / 50 / 2.5）。</b>'
      '細分在頻率上沒有集中任何東西，報酬未測，'
      '現在下任何方向結論都會是樣本內選擇。</p></section>')

P4 = ('<section class="panel"><div class="ph2">'
      '<h2>四、★ 畫圖時發現的規格缺口</h2>'
      '<span class="tag">2026-08-25</span></div>'
      '<p class="warn">規格 §2 只要求「三高遞增、三低遞減」，'
      '<b>沒有要求六個樞紐在時間上交替出現</b>，也沒要求低點在高點下方。'
      '結果會抓到「下緣線在上緣線之上」的形狀 —— 兩條線交叉，'
      '那不是任何人會叫做喇叭形的東西。</p>'
      '<table><thead><tr><th>每加一個要求</th><th>剩下</th><th>存活率</th></tr>'
      '</thead><tbody>' + rowsc + '</tbody></table>'
      '<p class="warn"><b>現行 §2 抓到的 1,119 個裡，只有 9.9% 的樞紐真的交替。'
      '四項全通過的，八年只有 85 個。</b>'
      '這是「先畫出來」才會發現的事，待你裁示是否寫進 §2。</p></section>')

FOOT = ('<section><div class="legend">' + leg + '</div></section>'
        '<footer class="foot">示意圖由 '
        '<code>scripts/research/s16s_p29_make_diagram.py</code> 產生；'
        '真實案例由 <code>s16s_p29_find_example.py</code> 自 421,513 根中選出，'
        '選取依據僅為形狀（跨度、樞紐不擠在一起、有無突破），'
        '<b>無損益欄、不依報酬排序</b>。'
        '要求層級表由 <code>s16s_p29_interleave_test.py</code> 產生。'
        '規格全文 <code>docs/research/S16S_P29_logic_spec_20260825.md</code>。'
        '</footer></div>')

open(OUT, 'w', encoding='utf-8').write(HEAD + TOP + P1 + P2 + P3 + P4 + FOOT)
print('wrote %s' % OUT)
