# -*- coding: utf-8 -*-
"""P51-P54 broadening-wedge family: the picture, before the discussion.

Willy's rule, 2026-08-27: produce the HTML BEFORE researching or discussing a
formation, because judging a shape from prose does not work.

So this page is deliberately not a conclusion. It shows the four shapes, one
real instance of each, and the two counting problems the scan found -- and then
stops at the two rulings those problems force. Nothing here says whether the
formations are useful; nothing has been tested for return.
"""
import io, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_P51_P54_diagram.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

W, HH = 480.0, 260.0
PL, PR, PT, PB = 34.0, 34.0, 26.0, 40.0


def mk(xs, ys, w=W, h=HH, pl=PL, pr=PR, pt=PT, pb=PB):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (w - pl - pr) / float(max(x1 - x0, 1e-9))
    sy = (h - pt - pb) / float(max(y1 - y0, 1e-9))
    return (lambda x: pl + (x - x0) * sx, lambda y: h - pb - (y - y0) * sy)


# ---- schematics: six alternating pivots, edge behaviour is the only variable --
SCH = {
    'P51': dict(hi=[72, 86, 100], lo=[40, 46, 52]),      # both rise, top faster
    'P52': dict(hi=[100, 94, 88], lo=[68, 54, 40]),      # both fall, bottom faster
    'P53': dict(hi=[100, 100, 100], lo=[70, 55, 40]),    # flat top
    'P54': dict(hi=[70, 85, 100], lo=[40, 40, 40]),      # flat bottom
}


def schematic(key):
    d = SCH[key]
    xh = [14, 44, 74]
    xl = [28, 58, 88]
    pts, pv = [], []
    for j in range(3):
        pts.append((xh[j], d['hi'][j]))
        pv.append(('PH%d' % (3 - j), xh[j], d['hi'][j]))
        pts.append((xl[j], d['lo'][j]))
        pv.append(('PL%d' % (3 - j), xl[j], d['lo'][j]))
    pts = [(4, (d['hi'][0] + d['lo'][0]) / 2)] + pts + [(96, (d['hi'][2] + d['lo'][2]) / 2)]
    X, Y = mk([p[0] for p in pts], [p[1] for p in pts] + [34, 106])
    o = []

    def ln(a, b, cls):
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(a[0]), Y(a[1]), X(b[0]), Y(b[1])))

    ln((xh[0], d['hi'][0]), (xh[2], d['hi'][2]), 'tlu solid')
    ln((xl[0], d['lo'][0]), (xl[2], d['lo'][2]), 'tld solid')
    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts))
    for k, x, y in pv:
        cls = 'ph' if k[1] == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.4"/>' % (cls, X(x), Y(y)))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s</text>'
                 % (cls, X(x), Y(y) + (-11 if cls == 'ph' else 18), k))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


def real(key, d):
    bars, piv = d['bars'], d['piv']
    n = len(bars)
    X, Y = mk(list(range(n)), [b['h'] for b in bars] + [b['l'] for b in bars])
    bw = max((W - PL - PR) / float(n) * 0.56, 2.2)
    o = []
    idx = [p[0] for p in piv]
    hs = [p[0] for p in piv if p[1] == 'H']
    ls = [p[0] for p in piv if p[1] == 'L']
    pa, pb = min(idx), max(idx)
    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
             % (X(pa) - bw, PT - 4, X(pb) - X(pa) + 2 * bw, HH - PT - PB + 10))

    def ln(a, b, va, vb, cls):
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(a), Y(va), X(b), Y(vb)))

    ln(hs[0], hs[2], bars[hs[0]]['h'], bars[hs[2]]['h'], 'tlu solid')
    ln(ls[0], ls[2], bars[ls[0]]['l'], bars[ls[2]]['l'], 'tld solid')
    for i, b in enumerate(bars):
        cls = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, x, Y(b['h']), x, Y(b['l'])))
        t, bt = Y(max(b['o'], b['c'])), Y(min(b['o'], b['c']))
        if bt - t < 1.2:
            m = (t + bt) / 2.0
            t, bt = m - .6, m + .6
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (cls, x - bw / 2, t, bw, bt - t))
    for i, k in piv:
        v = bars[i]['h'] if k == 'H' else bars[i]['l']
        cls = 'ph' if k == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="3.6"/>' % (cls, X(i), Y(v)))
    o.append('<text class="ax" x="%.1f" y="%.1f">%s</text>'
             % (X(0), HH - PB + 20, bars[0]['t'][-4:]))
    o.append('<text class="ax" x="%.1f" y="%.1f">%s</text>'
             % (X(n - 1), HH - PB + 20, bars[n - 1]['t'][-4:]))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))



# ---------------------------------------------------------------- data ------
# Every number below is produced by a script in this folder, all of them
# counts-only.  Sources named in the footer.

META = [
 ('P51', '上升擴散楔形', 'Ascending Broadening Wedge',
  '兩條線同步走高，但彼此越拉越開', '高遞增 ＋ 低遞增 ＋ 高的升幅較大', 1669, 218.5),
 ('P52', '下降擴散楔形', 'Descending Broadening Wedge',
  '兩條線同步走低，但彼此越拉越開', '高遞減 ＋ 低遞減 ＋ 低的跌幅較大', 1717, 224.7),
 ('P53', '右角擴散（上）', 'Right-Angled Ascending Broadening',
  '頂部水平、底部一路走低', '高完全相等 ＋ 低遞減', 7, 0.9),
 ('P54', '右角擴散（下）', 'Right-Angled Descending Broadening',
  '底部水平、頂部一路走高', '低完全相等 ＋ 高遞增', 8, 1.0),
]

# high-triple direction x low-triple direction over all 32,094 frames
CONT = [('遞增', 3729, 203, 8, 2727, 6667),
        ('遞減', 462, 3106, 7, 4264, 7839),
        ('完全相等', 15, 7, 2, 38, 62),
        ('非單調', 4415, 2689, 27, 10395, 17526)]
EXPECT = [('高增 × 低減', 'P29 擴散', 203, 1247.4, 0.16, True),
          ('高減 × 低增', '收斂（對照）', 462, 2105.7, 0.22, True),
          ('高增 × 低增', 'P51 母集', 3729, 1790.9, 2.08, False),
          ('高減 × 低減', 'P52 母集', 3106, 1466.7, 2.12, False)]

# break outcome under ruling C: close through the formation's own horizontal extreme
BRK = [('P29', '擴散三角（對照）', 203, 0.561, 37, 43, 19),
       ('P51', '上升擴散楔形', 1669, 0.797, 13, 55, 31),
       ('P52', '下降擴散楔形', 1717, 0.238, 52, 14, 35),
       ('P53', '右角擴散（上）', 7, None, 57, 43, 0),
       ('P54', '右角擴散（下）', 8, None, 12, 62, 25)]

STRAT = [('Q1 最靠底', 46, 74, 50, 24), ('Q2', 39, 46, 50, -4),
         ('Q3', 12, 17, 19, -2), ('Q4 最靠頂', 8, 25, 11, 14)]
CROSS = [('起算最靠底的 1/4', 71, 28, 72), ('起算最靠頂的 1/4', 13, 3, 32)]
NULLT = [('排列（先高／先低）', 25.78, '&lt; 0.0001', '33pp，但見下'),
         ('M2 方向', 2.98, '0.5742', '無'),
         ('六格（排列 × M2）', 28.64, '0.0001', '比排列僅多 2.86'),
         ('S1 粗尺度分數', 15.55, '0.1035', '不過 Bonferroni 0.0125')]

# feasibility of coding: span against MaxBarsBack 100, and concurrency
FEAS = [('P29', 203, 12, 43, 0.0, 1.1, 3), ('P51', 1669, 12, 39, 0.0, 7.7, 7),
        ('P52', 1717, 12, 32, 0.0, 7.5, 9), ('P53', 7, 11, 16, 0.0, 0.03, 3),
        ('P54', 8, 10, 17, 0.0, 0.03, 2)]

TOL = [(0, 7, 8, True), (1, 29, 42, False), (2, 102, 96, False),
       (5, 437, 403, False), (10, 1133, 1065, False)]
YEARS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
YR = {'P29': [9, 15, 18, 31, 24, 31, 42, 33],
      'P51': [93, 214, 187, 220, 176, 290, 259, 230],
      'P52': [95, 172, 229, 267, 169, 258, 304, 223],
      'P53': [4, 1, 0, 0, 1, 0, 1, 0],
      'P54': [1, 1, 0, 4, 2, 0, 0, 0]}

EX = json.load(open(os.path.join(HERE, 's16s_p51_p54_example.json'), encoding='utf-8'))

# ---------------------------------------------------------------- render ---
EXTRA = """
.quad{display:grid;gap:13px;grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.qf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:13px 14px;display:flex;flex-direction:column;gap:7px}
.qf svg{width:100%;height:auto;display:block}
.qh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.qh b{font-family:var(--serif);font-size:15px}
.qh .cid{font-family:var(--mono);font-size:11px;color:var(--bg);background:var(--ink3);
  border-radius:2px;padding:1px 5px}
.qh .en{font-size:10.5px;color:var(--ink3);font-style:italic}
.qd{font-size:12.5px;color:var(--ink2);line-height:1.5}
.qr{font-family:var(--mono);font-size:11.5px;color:var(--ink3);
  font-variant-numeric:tabular-nums;border-top:1px solid var(--line2);padding-top:7px}
.qr b{color:var(--ink)}
.bad{color:var(--brk);font-weight:600}
.z{color:var(--brk);font-weight:600}
.rule{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;margin-top:4px}
.ro{background:var(--card);padding:13px 15px;display:flex;gap:12px;align-items:flex-start}
.ro .tag{flex:0 0 auto;font-family:var(--mono);font-size:11px;padding:2px 7px;
  border-radius:3px;border:1px solid var(--ph);color:var(--ph);font-weight:600}
.ro p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.6}
.ro b{color:var(--ink)}
.big{border-left:3px solid var(--ph);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:6px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:17px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
.two{display:grid;gap:13px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
"""

sc = ''.join(
    '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
    '<span class="en">%s</span></div>%s<div class="qd">%s</div>'
    '<div class="qr">%s　·　<b>%s</b> 個　年均 <b>%.1f</b></div></figure>'
    % (cid, zh, en, schematic(cid), desc, geo, format(n, ','), yr)
    for cid, zh, en, desc, geo, n, yr in META)

rc = ''.join(
    '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
    '<span class="en">%s ~ %s</span></div>%s'
    '<div class="qr">跨度 <b>%d</b> 根　振幅 <b>%.0f</b> 點　排列 %s　'
    '<span style="color:var(--ink3)">中位振幅樣本</span></div></figure>'
    % (cid, zh, EX[cid]['bars'][0]['t'], EX[cid]['bars'][-1]['t'][-4:],
       real(cid, EX[cid]), EX[cid]['span'], EX[cid]['amp'],
       '先高' if EX[cid]['kind'] == 'H' else '先低')
    for cid, zh, en, desc, geo, n, yr in META)

HEAD = ('<title>P51-P54 擴散楔形家族</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S 圖形型態 · 擴散家族 · 結案 2026-08-27</div>'
       '<h1>P51-P54 擴散楔形家族</h1>'
       '<p class="sub">P29 的四個變體，<b>六樞紐交替、低在高下</b> 一行不改，'
       '唯一的差別是兩條邊怎麼走。裁示 <b>A1 ／ B1 ／ C</b> 已定，'
       '<b>自由參數 0 個</b>。所有數字量自 421,513 根 5 分 K，2019-01-02 ~ 2026-08-22，'
       '<b>無任何損益欄</b>。</p>'
       '<div class="kpi">'
       '<span><b>32,094</b>六樞紐交替框架</span>'
       '<span><b>10.3 : 1</b>高低同向 : 反向</span>'
       '<span><b>0.16x</b>P29 相對獨立性期望</span>'
       '<span><b>96.5%</b>斜線版 P51 假跌破率</span>'
       '</div></header>')

P0 = ('<section class="panel"><div class="ph2"><h2>裁示結果</h2>'
      '<span class="tag">2026-08-27</span></div><div class="rule">'
      '<div class="ro"><span class="tag">A1</span><p>'
      '<b>P51／P52 維持現定義，角色 ＝ 屬性，不是濾網。</b>'
      '218 與 225 個／年，每 1.5 個交易日一個，不可能當進場濾網；'
      '當「市場正在同向擴張」的狀態標籤使用。'
      '前例：S1 粗尺度穩健性（裁示 9）同樣是數量問題，同樣改為屬性、不設門檻。</p></div>'
      '<div class="ro"><span class="tag">B1</span><p>'
      '<b>P53／P54 維持「完全相等」，不引進容差。</b>'
      '八年 15 個、各四年掛零，無檢定力。編碼但標記「近乎不出現」，不投入後續研究。'
      '任何非零容差都會是本專案<b>第一個掃出來的門檻</b>。</p></div>'
      '<div class="ro"><span class="tag">C</span><p>'
      '<b>破的判準 ＝ 收盤價穿越型態自身的水平極值線。</b>'
      '起算 ＝ 最後一個樞紐確認後下一根；視窗 ＝ 型態自身跨越的根數；'
      '<b>無緩衝點數、無 N 根確認</b>。自由參數 0 個。</p></div>'
      '</div></section>')

P1 = ('<section class="panel"><div class="ph2"><h2>一、四個變體的形狀</h2>'
      '<span class="tag">綠點＝樞紐高　橘點＝樞紐低　實線＝兩條邊</span></div>'
      '<div class="quad">' + sc + '</div>'
      '<p class="cap">P29 是<b>高遞增 ＋ 低遞減</b>（兩邊往相反方向擴）。'
      'P51／P52 改成<b>兩邊同向</b>但速度不同；P53／P54 改成<b>一邊水平</b>。</p>'
      '</section>')

P2 = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
      '<span class="tag">從 421,513 根裡由程式選出，取中位振幅樣本</span></div>'
      '<div class="quad">' + rc + '</div>'
      '<p class="cap">選取依據<b>只有形狀</b>，無損益欄、不依報酬排序。'
      '第一次選取用「振幅最大」，選到 1,819 點、跨夜盤到日盤的極端案例 —— '
      '真實但不具代表性，已改為中位數。</p></section>')

cont = ''.join(
    '<tr><td>%s</td>%s<td>%s</td></tr>'
    % (r[0], ''.join('<td%s>%s</td>'
                     % (' class="z"' if (r[0] == '遞增' and j == 1) else '', format(v, ','))
                     for j, v in enumerate(r[1:5])), format(r[5], ','))
    for r in CONT)
exp = ''.join(
    '<tr><td>%s</td><td>%s</td><td>%s</td><td>%.1f</td><td%s>%.2fx</td></tr>'
    % (a, b, format(o, ','), e, ' class="z"' if rare else '', r)
    for a, b, o, e, r, rare in EXPECT)

P3 = ('<section class="panel"><div class="ph2">'
      '<h2>三、為什麼 P29 稀有、P51 常見</h2>'
      '<span class="tag">前提是錯的：P29 沒有加濾網</span></div>'
      '<p class="cap">P29 的條件有 <b>2 個</b>（高遞增、低遞減）；'
      'P51 有 <b>3 個</b>（高遞增、低遞增、發散較快）。'
      '<b>條件多的那個反而多 8.2 倍。</b>頻率差不是濾網造成的。</p>'
      '<table><thead><tr><th>高＼低</th><th>遞增</th><th>遞減</th>'
      '<th>完全相等</th><th>非單調</th><th>列合計</th></tr></thead>'
      '<tbody>' + cont + '</tbody></table>'
      '<p class="cap">兩邊都單調的框架裡，<b>同向 6,835 : 反向 665 ＝ 10.3 : 1</b>。'
      '高點與低點強烈同向共動。</p>'
      '<table><thead><tr><th>組合</th><th></th><th>觀測</th>'
      '<th>獨立期望</th><th>倍率</th></tr></thead><tbody>' + exp + '</tbody></table>'
      '<p class="warn"><b>P29 的稀有性完全來自幾何本身逆著行情結構。</b>'
      '要求兩條邊往反方向走，實際只有隨機的 1/6。'
      '收斂型（高減 × 低增）也被壓到 0.22x —— '
      '這證明<b>是「反向」本身稀有，不是 P29 定義特殊</b>。'
      '另：<code>spanH &gt; spanL</code> 只砍掉 55%（3,729 → 1,669），'
      '要把 P51 壓到 P29 的量級還得再砍 88%，那需要強濾網 ＝ 強自由參數。</p>'
      '</section>')

P4 = ('<section class="panel"><div class="ph2">'
      '<h2>四、★ 斜趨勢線會製造假訊號</h2>'
      '<span class="tag">裁示 C 否決它的量化依據</span></div>'
      '<p class="warn">若把「破」定義成<b>穿越斜趨勢線</b>，'
      'P51 會回報<b>跌破先 78%</b> —— 看起來是完美的空方訊號。'
      '但其中 <b class="bad">96.5%</b> 是在價格<b>仍高於型態自身最低點</b>時觸發的，'
      '中位高出 <b>43 點</b>。P51 的下緣遞增，'
      '<b>是那條線從價格底下爬走了，不是價格跌破。</b></p>'
      '<table><thead><tr><th>型態</th><th>下緣走勢</th><th>斜線判跌破</th>'
      '<th>其中價格仍在型態底之上</th><th>假訊號率</th></tr></thead><tbody>'
      '<tr><td>P29</td><td>遞減</td><td>48</td><td>0</td><td>0.0%</td></tr>'
      '<tr><td>P52</td><td>遞減</td><td>243</td><td>0</td><td>0.0%</td></tr>'
      '<tr><td class="z">P51</td><td>遞增</td><td>1,301</td><td>1,256</td>'
      '<td class="z">96.5%</td></tr>'
      '</tbody></table>'
      '<p class="cap">命中率<b>完全由邊的斜率決定</b>，所以斜線版的 78% 與 24% '
      '不能拿來比較哪個型態比較適合空。水平極值線是唯一跨變體意義一致的定義，'
      '而且同樣零參數。</p></section>')

brk = ''.join(
    '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
    '<td>%d%%</td><td>%d%%</td><td>%d%%</td></tr>'
    % (c, z, format(n, ','), ('%.3f' % p) if p is not None else '—', d, u, o)
    for c, z, n, p, d, u, o in BRK)
strat = ''.join(
    '<tr><td>%s</td><td>%d</td><td>%d%%</td><td>%d%%</td><td%s>%+dpp</td></tr>'
    % (a, n, h, l, ' class="z"' if abs(g) < 10 else '', g)
    for a, n, h, l, g in STRAT)
cross = ''.join('<tr><td>%s</td><td>%d%%</td><td>%d%%</td><td>%d%%</td></tr>'
                % r for r in CROSS)
nul = ''.join('<tr><td>%s</td><td>%.2f</td><td>%s</td><td>%s</td></tr>' % r for r in NULLT)

P5 = ('<section class="panel"><div class="ph2">'
      '<h2>五、破位結果 —— 以及它測到的其實是距離</h2>'
      '<span class="tag">裁示 C 定義下</span></div>'
      '<table><thead><tr><th>型態</th><th></th><th>母體</th>'
      '<th>中位起算位置</th><th>跌破先</th><th>突破先</th><th>都沒破</th>'
      '</tr></thead><tbody>' + brk + '</tbody></table>'
      '<p class="cap">起算位置：<b>0 ＝ 貼型態底，1 ＝ 貼型態頂</b>。'
      '型態最後一根收在哪，就決定它往哪邊破 —— 0.797 對 13%，0.238 對 52%，'
      '0.561 對 37%。</p>'
      '<div class="two">'
      '<div><p class="cap" style="margin-top:0"><b>P29 子分類，排列檢定 20,000 次</b></p>'
      '<table><thead><tr><th>分類</th><th>chi2</th><th>p</th><th>判定</th></tr></thead>'
      '<tbody>' + nul + '</tbody></table></div>'
      '<div><p class="cap" style="margin-top:0">'
      '<b>排列的 33pp，控制起算位置後</b></p>'
      '<table><thead><tr><th>位置四分位</th><th>n</th><th>先高</th><th>先低</th>'
      '<th>差距</th></tr></thead><tbody>' + strat + '</tbody></table></div>'
      '</div>'
      '<p class="cap">先高以樞紐<b>低</b>收尾，中位起算位置 0.283（貼底）；'
      '先低以樞紐<b>高</b>收尾，0.766（貼頂）。'
      '分層後<b>中間兩層歸零</b>，效應不一致 → 不是真的。'
      '與 M1 中點漂移同類，檢查表第 12 條。</p>'
      '<table><thead><tr><th></th><th>P29</th><th>P51</th><th>P52</th>'
      '</tr></thead><tbody>' + cross + '</tbody></table>'
      '<p class="cap">控制起算位置後，<b>P29 與 P52 幾乎相同（71% vs 72%）</b>，'
      'P51 差很遠。P29 與 P52 的共同點是<b>低點遞減</b>，P51 是低點遞增 —— '
      '殘差測到的是低點方向延續，而「低點遞減」的定義本身就是「連續往下破」。</p>'
      '<div class="big"><p>破位方向 ＝ 起算位置 ＋ 低點方向延續。'
      '兩者都不是型態資訊。</p>'
      '<small>適用於之後每一個型態。研究新型態時<b>不必再測「它往哪邊破」</b>。'
      '若型態有價值，價值必然在「破了之後走多遠」—— 那是訊號層。</small></div>'
      '</section>')

feas = ''.join(
    '<tr><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%.1f%%</td>'
    '<td>%.1f%%</td><td%s>%d</td></tr>'
    % (c, format(n, ','), md, mx, ov, cov, ' class="z"' if k >= 7 else '', k)
    for c, n, md, mx, ov, cov, k in FEAS)

P6 = ('<section class="panel"><div class="ph2">'
      '<h2>六、能不能程式碼化</h2>'
      '<span class="tag">MaxBarsBack 100 ＝ 回看不得超過 99 根</span></div>'
      '<table><thead><tr><th>型態</th><th>母體</th><th>中位跨度</th><th>最大跨度</th>'
      '<th>形成＋有效期 &gt; 99</th><th>覆蓋 K 棒</th><th>最多同時重疊</th>'
      '</tr></thead><tbody>' + feas + '</tbody></table>'
      '<p class="cap"><b>MaxBarsBack 沒有問題</b> —— 最大跨度 43 根，'
      '形成＋有效期超過 99 根的比例是 <b>0.0%</b>。'
      '擋路的是<b>並發度</b>：現行指標一次只追蹤一個型態，'
      'P51 最多 7 個、P52 最多 9 個同時重疊，'
      '要全部畫出來得改成<b>陣列式多實例追蹤</b> —— 那是架構改動。</p>'
      '<p class="warn"><b>而裁示 A1 已經讓這個問題消失：</b>'
      'P51／P52 是<b>屬性</b>，屬性只需要一個布林「現在是否在型態內」，'
      '不需要逐個實例追蹤。<b>便宜很多，而且是對的做法。</b></p>'
      '</section>')

tol = ''.join(
    '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
    % (('%d 點' % t) if t else '0（已裁示採用）', format(a, ','), format(b, ','),
       '零自由參數' if z else '<span class="bad">引進自由參數</span>')
    for t, a, b, z in TOL)
yr = ''.join(
    '<tr><td%s>%s</td>%s</tr>'
    % (' style="color:var(--brk)"' if k in ('P53', 'P54') else '', k,
       ''.join('<td%s>%d</td>' % (' class="z"' if v == 0 else '', v) for v in vs))
    for k, vs in YR.items())

P7 = ('<section class="panel"><div class="ph2"><h2>七、母體與逐年分布</h2>'
      '<span class="tag">紅色 0 ＝ 整年掛零</span></div>'
      '<table><thead><tr><th>型態</th>'
      + ''.join('<th>%s</th>' % y for y in YEARS) +
      '</tr></thead><tbody>' + yr + '</tbody></table>'
      '<p class="cap">P29 逐年 9 ~ 42，沒有掛零。'
      'P53／P54 各有四年完全沒有出現 —— 跨期驗證在這種分布上做不了，'
      '這是裁示 B1 的依據。</p>'
      '<table><thead><tr><th>「水平」的容差</th><th>P53</th><th>P54</th>'
      '<th>代價</th></tr></thead><tbody>' + tol + '</tbody></table>'
      '</section>')

FOOT = ('<footer class="foot">'
        '掃描 <code>s16s_p51_p54_scan.py</code>　·　'
        '案例 <code>s16s_p51_p54_pick.py</code>　·　'
        '母體拆解 <code>s16s_frame_decompose.py</code>　·　'
        '破位 <code>s16s_break_outcome.py</code>　·　'
        '虛無對照 <code>s16s_p29_break_split.py</code>　·　'
        '本頁 <code>s16s_p51_p54_make_diagram.py</code>，'
        '樣式與 P29 示意圖共用 <code>_diagram.css</code>。'
        '<b>全部無損益欄。</b>'
        '結案文件 <code>docs/research/S16S_BROADENING_FAMILY_CLOSED_20260827.md</code>。'
        '</footer></div>')

open(OUT, 'w', encoding='utf-8').write(
    HEAD + TOP + P0 + P1 + P2 + P3 + P4 + P5 + P6 + P7 + FOOT)
print('wrote %s' % OUT)
