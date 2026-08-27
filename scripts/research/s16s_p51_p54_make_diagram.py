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


META = [
 ('P51', '上升擴散楔形', 'Ascending Broadening Wedge', '空',
  '兩條線同步走高，但彼此越拉越開', '高遞增 ＋ 低遞增 ＋ 高的升幅較大', 1669, 218.5),
 ('P52', '下降擴散楔形', 'Descending Broadening Wedge', '多',
  '兩條線同步走低，但彼此越拉越開', '高遞減 ＋ 低遞減 ＋ 低的跌幅較大', 1717, 224.7),
 ('P53', '右角擴散（上）', 'Right-Angled Ascending Broadening', '空',
  '頂部水平、底部一路走低', '高**完全相等** ＋ 低遞減', 7, 0.9),
 ('P54', '右角擴散（下）', 'Right-Angled Descending Broadening', '多',
  '底部水平、頂部一路走高', '低**完全相等** ＋ 高遞增', 8, 1.0),
]

TOL = [(0, 7, 8, True), (1, 29, 42, False), (2, 102, 96, False),
       (5, 437, 403, False), (10, 1133, 1065, False)]

YEARS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
YR = {
 'P29': [9, 15, 18, 31, 24, 31, 42, 33],
 'P51': [93, 214, 187, 220, 176, 290, 259, 230],
 'P52': [95, 172, 229, 267, 169, 258, 304, 223],
 'P53': [4, 1, 0, 0, 1, 0, 1, 0],
 'P54': [1, 1, 0, 4, 2, 0, 0, 0],
}


EX = json.load(open(os.path.join(HERE, 's16s_p51_p54_example.json'), encoding='utf-8'))

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
.rule{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;margin-top:4px}
.ro{background:var(--card);padding:12px 15px;display:flex;gap:12px;align-items:flex-start}
.ro .tag{flex:0 0 auto;font-family:var(--mono);font-size:11px;padding:2px 7px;
  border-radius:3px;border:1px solid var(--ink3);color:var(--ink3)}
.ro .tag.rec{border-color:var(--ph);color:var(--ph);font-weight:600}
.ro p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.ro b{color:var(--ink)}
"""

sc = ''.join(
    '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
    '<i class="tg dir%s">%s</i><span class="en">%s</span></div>'
    '%s<div class="qd">%s</div>'
    '<div class="qr">%s　·　<b>%s</b> 個　年均 <b>%.1f</b>%s</div></figure>'
    % (cid, zh, {'空': 'b', '多': 'u'}[d], d, en, schematic(cid), desc,
       geo.replace('**', ''), format(n, ','), yr,
       '　<span class="bad">← 密度異常</span>' if n > 1000 else
       ('　<span class="bad">← 近乎不出現</span>' if n < 20 else ''))
    for cid, zh, en, d, desc, geo, n, yr in META)

rc = ''.join(
    '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
    '<span class="en">%s ~ %s</span></div>%s'
    '<div class="qr">跨度 <b>%d</b> 根　振幅 <b>%.0f</b> 點　'
    '排列 %s　<span style="color:var(--ink3)">中位振幅樣本</span></div></figure>'
    % (cid, zh, EX[cid]['bars'][0]['t'], EX[cid]['bars'][-1]['t'][-4:],
       real(cid, EX[cid]), EX[cid]['span'], EX[cid]['amp'],
       '先高' if EX[cid]['kind'] == 'H' else '先低')
    for cid, zh, en, d, desc, geo, n, yr in META)

tol = ''.join(
    '<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
    % (' class="good"' if z else '', ('%d 點' % t) if t else '0（現行慣例）',
       format(a, ','), format(b, ','),
       '零自由參數' if z else '<span class="bad">引進自由參數</span>')
    for t, a, b, z in TOL)

yr = ''.join(
    '<tr><td%s>%s</td>%s</tr>'
    % (' style="color:var(--brk)"' if k in ('P53', 'P54') else '', k,
       ''.join('<td%s>%d</td>' % (' class="z"' if v == 0 else '', v) for v in vs))
    for k, vs in YR.items())

HEAD = ('<title>P51-P54 擴散楔形家族</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA
        + '\n.z{color:var(--brk);font-weight:600}\n'
        '.tg{font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid;'
        'font-style:normal;white-space:nowrap}\n'
        '.tg.dirb{color:var(--dn);border-color:var(--dn)}\n'
        '.tg.diru{color:var(--up);border-color:var(--up)}\n</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S 圖形型態 · 擴散家族 · 2026-08-27</div>'
       '<h1>P51-P54 擴散楔形家族</h1>'
       '<p class="sub">P29 的四個變體。<b>六樞紐交替、低在高下、樞紐同時段</b> —— '
       '這些條件一行不改，<b>唯一的差別是兩條邊怎麼走</b>。'
       '所有數字量自 421,513 根 5 分 K，2019-01-02 ~ 2026-08-22。</p>'
       '<div class="kpi">'
       '<span><b>32,094</b>六樞紐交替框架</span>'
       '<span><b>203</b>P29 對照（年均 26.6）</span>'
       '<span><b>3,386</b>P51 ＋ P52</span>'
       '<span><b>15</b>P53 ＋ P54（八年）</span>'
       '</div>'
       '<p class="warn">⚠️ <b>本頁不是結論。</b>四個型態的報酬<b>一次都沒有檢定過</b>，'
       '本頁只呈現形狀、真實案例與計數。'
       '依用戶 2026-08-27 裁示：<b>先出圖，再討論。</b></p>'
       '</header>')

P1 = ('<section class="panel"><div class="ph2"><h2>一、四個變體的形狀</h2>'
      '<span class="tag">綠點＝樞紐高　橘點＝樞紐低　實線＝兩條邊</span></div>'
      '<div class="quad">' + sc + '</div>'
      '<p class="cap">P29 是<b>高遞增 ＋ 低遞減</b>（兩邊往相反方向擴）。'
      'P51／P52 改成<b>兩邊同向</b>但速度不同；P53／P54 改成<b>一邊水平</b>。</p>'
      '</section>')

P2 = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
      '<span class="tag">從 421,513 根裡由程式選出，取中位振幅樣本</span></div>'
      '<div class="quad">' + rc + '</div>'
      '<p class="warn">選取依據<b>只有形狀</b>（跨度、樞紐不擠在一起、振幅取中位數），'
      '<b>無損益欄、不依報酬排序</b>。'
      '第一次選取用「振幅最大」，選到 1,819 點、跨夜盤到日盤的極端案例 —— '
      '真實但不具代表性，已改為中位數。</p></section>')

P3 = ('<section class="panel"><div class="ph2">'
      '<h2>三、★ 兩個問題，方向相反</h2>'
      '<span class="tag">先量再談</span></div>'
      '<p class="warn"><b>問題一：P51／P52 是 P29 的 8 倍。</b>'
      '年均 218 與 225，等於<b>每 1.5 個交易日就有一個</b>。'
      '「高低同升、高的升幅較大」比「高升低降」寬鬆太多 —— '
      '那幾乎是在描述<b>任何區間放大的上升趨勢</b>，不是一個可辨識的型態。</p>'
      '<p class="warn"><b>問題二：P53／P54 被「完全相等」殺死。</b>'
      '八年 7 個與 8 個，<b>各有四年掛零</b>。編出來也沒有任何檢定力。</p>'
      '<table><thead><tr><th>「水平」的容差</th><th>P53</th><th>P54</th>'
      '<th>代價</th></tr></thead><tbody>' + tol + '</tbody></table>'
      '<p class="cap"><b>容差表是給裁示依據，不是建議採用非零值。</b>'
      '任何非零容差都會是這個專案<b>第一個掃出來的門檻</b> —— '
      'P29 到目前為止七段全部零自由參數。</p></section>')

P4 = ('<section class="panel"><div class="ph2"><h2>四、逐年分布</h2>'
      '<span class="tag">紅色 0 ＝ 整年掛零</span></div>'
      '<table><thead><tr><th>型態</th>'
      + ''.join('<th>%s</th>' % y for y in YEARS) +
      '</tr></thead><tbody>' + yr + '</tbody></table>'
      '<p class="cap">P29 逐年 9 ~ 42，沒有掛零。'
      'P53／P54 各有四年完全沒有出現 —— <b>跨期驗證在這種分布上做不了。</b></p>'
      '</section>')

P5 = ('<section class="panel"><div class="ph2">'
      '<h2>五、待裁示</h2><span class="tag">批次問，不一次一題</span></div>'
      '<div class="rule">'
      '<div class="ro"><span class="tag">A1</span><p>'
      '<b>P51／P52 維持現定義</b> —— 承認它就是高頻的（218／年），'
      '當「區間放大的趨勢」用，不當型態用。</p></div>'
      '<div class="ro"><span class="tag">A2</span><p>'
      '<b>加上「發散幅度」的相對要求</b> —— 能壓低數量，'
      '但<b>發散多少算數是自由參數</b>。</p></div>'
      '<div class="ro"><span class="tag rec">A3　建議</span><p>'
      '<b>放棄 P51／P52</b> —— 承認它在 5 分 K 上不是可辨識的型態。'
      '每 1.5 個交易日一個，訊號密度已經超過策略能承受的範圍。</p></div>'
      '</div>'
      '<div class="rule">'
      '<div class="ro"><span class="tag rec">B1　建議</span><p>'
      '<b>維持完全相等</b> —— 承認 P53／P54 在 5 分 K 上幾乎不存在（8 年 15 個），'
      '<b>編碼但標記為「近乎不出現」</b>，不投入後續研究。</p></div>'
      '<div class="ro"><span class="tag">B2</span><p>'
      '<b>給固定點數容差</b> —— 引進自由參數，違反本專案至今的零旋鈕原則。</p></div>'
      '<div class="ro"><span class="tag">B3</span><p>'
      '<b>用自我指涉的相等定義</b>（例如三個高點極差 ≤ 該型態自身振幅的某比例）'
      '—— 仍是參數，但至少不是從外面帶進來的常數。</p></div>'
      '</div>'
      '<p class="warn">建議 <b>A3 ＋ B1</b>：擴散家族以 <b>P29／P49／P50 三個結案</b>。'
      '這是誠實的結果，不是失敗 —— '
      '<b>把兩個不可辨識與兩個不存在的型態排除，母體才乾淨。</b></p>'
      '</section>')

FOOT = ('<footer class="foot">'
        '掃描 <code>scripts/research/s16s_p51_p54_scan.py</code>　·　'
        '案例選取 <code>s16s_p51_p54_pick.py</code>　·　'
        '本頁 <code>s16s_p51_p54_make_diagram.py</code>　·　'
        '樣式與 P29 示意圖共用 <code>_diagram.css</code>。'
        '全部<b>無損益欄</b>。P29 對照數字取自 <code>s16s_p29_clean.json</code>（203 筆）。'
        '</footer></div>')

open(OUT, 'w', encoding='utf-8').write(HEAD + TOP + P1 + P2 + P3 + P4 + P5 + FOOT)
print('wrote %s' % OUT)
