# -*- coding: utf-8 -*-
"""The page for the eleven patterns that still had to go through the process.

Its own page while under discussion; it joins the master once closed -- the
route the broadening family, the gap group, the diamond, the pivot group and
the fifteen all took.

Eight of the eleven are BAR patterns, so the schematics are candles, not
polylines.  A polyline sketch of "the upper shadow is longer than the body"
would not show the thing being tested.

Run:  python scripts/research/s16s_eleven_scan.py
      python scripts/research/s16s_eleven_pick.py
      python scripts/research/s16s_eleven_make_page.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()
D = json.load(open(os.path.join(HERE, 's16s_eleven.json'), encoding='utf-8'))
EX = json.load(open(os.path.join(HERE, 's16s_eleven_example.json'),
                    encoding='utf-8'))
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_eleven_diagram.html'))
ROWS = D['rows']
LT, GT, LE = '&lt;', '&gt;', '&le;'

# 代號: (骨架序列, [逐條定義], 附註)
LOGIC = {
 'P33': ('樞紐高 ＋ 一根 K 棒', [
   '存在一個成立的<b>樞紐高 PH</b>',
   'High %s PH　<i>掃過去</i>' % GT,
   'Close %s PH　<b>收回它下面</b>' % LT,
   '每個樞紐高<b>只掃一次</b>（掃過即解除武裝）'],
   '純比較，零參數。「掃過又收回」是兩個不等式，不需要「超過幾點才算掃」。'),
 'P35': ('樞紐低 ＋ 一根 K 棒', [
   '存在一個成立的<b>樞紐低 PL</b>',
   'Close %s PL　<b>收盤實質跌破</b>' % LT,
   '每個樞紐低<b>只破一次</b>'],
   '<b>這一條差點被我化約掉。</b>「收盤跌破前一個樞紐低」看起來就是'
   '「底底降」原語 —— <b>實測不是</b>：收盤穿越 24,129 次，'
   '下一個樞紐低更低 34,116 次。差額全是<b>低點戳破但收盤沒破</b>的情況，'
   '而那正是這個型態要排除的。'),
 'P37': ('樞紐低 ＋ 狀態位元', [
   'P35 的<b>全部條件</b>',
   '且<b>上一次結構事件是向上突破</b>（Close %s 樞紐高）' % GT,
   '＝ 一段走高之後的<b>第一次</b>向下破壞'],
   'P35 的子集，多出來的只有一個狀態位元。'
   '12,673 對 24,129 —— <b>剛好一半</b>，代表向上與向下的結構事件在長期是交替的。'),
 'P13': ('一根旗桿棒 ＋ 不定根數飄移', [
   '旗桿：收黑，且<b>振幅是最近四根最寬</b>（WR4 排名）',
   '飄移：後續每根 High %s 旗桿 High　<i>高點始終沒被突破</i>' % LE,
   '結束：Close %s 旗桿 Low　<b>先跌破旗桿底</b>' % LT,
   '若 High 先突破旗桿頂，<b>作廢不計</b>'],
   '<b>飄移沒有根數。</b>教科書的旗形要問「整理幾根」—— 那是自由參數。'
   '這裡讓它<b>跑到分出勝負為止</b>：先破底算成立、先過頂算作廢，'
   '「旗形要多長」這個問題根本不會被問到。'),
 'P14': ('同 P13 ＋ 收斂', [
   'P13 的<b>全部條件</b>',
   '飄移期間<b>每根振幅都比前一根小</b>　<i>逐根收斂</i>'],
   '與 P13 只差一條純序數的條件，兩者是<b>子集關係</b>不是互斥：'
   '5,884 是 12,038 的一部分。'),
 'P41': ('四根 K 棒', [
   '當根振幅 %s 前三根<b>每一根</b>的振幅' % GT],
   '<b>排名，不是門檻。</b>N=4 是 Crabel 的常數，'
   '2026-08-31 裁示 5 明確記為「借用」而非「推導」。'),
 'P42': ('七根 K 棒', [
   '當根振幅 %s 前六根<b>每一根</b>的振幅' % GT],
   '同上，N=7。'),
 'P43': ('兩根 K 棒', [
   'High %s High[1]　<i>創前一根新高</i>' % GT,
   'Close %s Low[1]　<b>卻收在前一根的最低之下</b>' % LT],
   '兩個不等式，零參數。這是全組<b>最短</b>的型態 —— 跨度就是 1 根。'),
 'P45': ('前一時段的低 ＋ 一根 K 棒', [
   'Close %s <b>前一個交易時段的最低價</b>' % LT,
   '每個時段<b>只記一次</b>'],
   '<b>時段邊界由交易所定，不是我挑的</b> —— 這是全組唯一'
   '不需要任何裝置就零參數的定義。'),
 'P47': ('三根 K 棒（隔一根的兩支角）', [
   '第 1 根與第 3 根：<b>上影 %s 實體</b>' % GT,
   '兩根的 High 都 %s 中間那根的 High　<i>中間凹下去</i>' % GT,
   '|H1 − H3| %s min(上影1, 上影3)　<b>差距小於影線本身</b>' % LT],
   '<b>「長上影」原本是門檻，改寫成比較就不是了</b>：上影比實體長。'
   '<br>「兩個高點差不多高」也一樣 —— 容差取<b>影線自己的長度</b>，'
   '由 K 棒給，不是我給。'),
 'P48': ('兩根相鄰 K 棒', [
   '兩根都：<b>上影 %s 實體</b>' % GT,
   '第 1 根 High %s 前一根 High，第 2 根 High %s 後一根 High　<i>成局部頂</i>'
   % (GT, GT),
   '|H1 − H2| %s min(上影1, 上影2)' % LT],
   '與 P47 同樣的兩個裝置，差別只在<b>相鄰</b>而不是隔一根。'),
}

# 示意圖：K 棒 (o, h, l, c)，座標 0-100，另可加水平線與註記
SCH = {
 'P33': ([(42, 52, 36, 40), (40, 50, 32, 46), (46, 78, 42, 44)], [62], 'PH'),
 'P35': ([(58, 64, 48, 52), (52, 58, 44, 50), (50, 54, 22, 30)], [42], 'PL'),
 'P37': ([(30, 62, 26, 58), (58, 66, 50, 54), (54, 58, 24, 32)], [42, 64],
         'PL / PH'),
 'P13': ([(80, 84, 30, 34), (36, 44, 32, 40), (40, 46, 34, 38),
          (38, 42, 18, 24)], [30], '旗桿 Low'),
 'P14': ([(80, 84, 30, 34), (36, 48, 32, 42), (42, 46, 36, 40),
          (40, 43, 20, 26)], [30], '旗桿 Low'),
 'P41': ([(50, 56, 44, 48), (48, 54, 42, 46), (46, 52, 40, 44),
          (44, 76, 18, 66)], [], ''),
 'P42': ([(52, 56, 48, 50), (50, 55, 46, 48), (48, 53, 44, 46),
          (46, 51, 42, 44), (44, 49, 40, 42), (42, 47, 38, 40),
          (40, 74, 16, 62)], [], ''),
 'P43': ([(46, 58, 40, 54), (56, 72, 30, 34)], [40], 'Low[1]'),
 'P45': ([(52, 58, 44, 48), (48, 54, 40, 44), (44, 48, 20, 26)], [38],
         '前時段低'),
 'P47': ([(38, 76, 34, 42), (40, 48, 34, 38), (36, 74, 32, 40)], [], ''),
 'P48': ([(38, 78, 34, 42), (42, 76, 36, 40)], [], ''),
}

W, HH, PL_, PR, PT, PB = 520.0, 172.0, 8.0, 8.0, 12.0, 12.0


def candles(cs, lines, lab, w, h, pad=10):
    lo = min(min(c[2] for c in cs), *(lines or [999]))
    hi = max(max(c[1] for c in cs), *(lines or [-999]))
    rng = (hi - lo) or 1.0

    def X(i):
        return pad + (w - 2 * pad) * (i + .5) / len(cs)

    def Y(v):
        return pad + (h - 2 * pad) * (hi - v) / rng

    bw = max((w - 2 * pad) / len(cs) * 0.5, 3)
    o = []
    for v in lines:
        o.append('<line class="lvl" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (pad * .4, Y(v), w - pad * .4, Y(v)))
    for i, (op, hg, lw, cl) in enumerate(cs):
        k = 'up' if cl >= op else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (k, x, Y(hg), x, Y(lw)))
        t, b = Y(max(op, cl)), Y(min(op, cl))
        if b - t < 1.6:
            m = (t + b) / 2
            t, b = m - .8, m + .8
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" '
                 'height="%.1f"/>' % (k, x - bw / 2, t, bw, b - t))
    if lab and lines:
        o.append('<text class="lvt" x="%.1f" y="%.1f">%s</text>'
                 % (pad * .4, Y(lines[0]) - 4, lab))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (w, h, ''.join(o))


def sch(cid):
    cs, lines, lab = SCH[cid]
    return candles(cs, lines, lab, 190.0, 118.0, 12)


def real(cid):
    d = EX[cid]
    bars, i0, i1 = d['bars'], d['i0'], d['i1']
    n = len(bars)
    lo = min(b['l'] for b in bars)
    hi = max(b['h'] for b in bars)
    rng = (hi - lo) or 1.0

    def X(i):
        return PL_ + (W - PL_ - PR) * (i + .5) / n

    def Y(v):
        return PT + (HH - PT - PB) * (hi - v) / rng

    bw = max((W - PL_ - PR) / float(n) * 0.54, 3)
    o = ['<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
         % (X(i0) - bw, PT - 5, X(i1) - X(i0) + 2 * bw, HH - PT - PB + 10)]
    for i, b in enumerate(bars):
        k = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (k, x, Y(b['h']), x, Y(b['l'])))
        t, bt = Y(max(b['o'], b['c'])), Y(min(b['o'], b['c']))
        if bt - t < 1.4:
            m = (t + bt) / 2
            t, bt = m - .7, m + .7
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" '
                 'height="%.1f"/>' % (k, x - bw / 2, t, bw, bt - t))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


HEAD = ('<title>十一種型態的完整流程</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700'
        '&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + '''
.cen{width:100%;border-collapse:collapse;font-size:13.5px;margin:6px 0 0}
.cen th{text-align:right;font-size:11px;letter-spacing:.08em;color:var(--ink3);
 font-weight:500;border-bottom:1px solid var(--ink);padding:0 10px 7px 0}
.cen th:nth-child(-n+4){text-align:left}
.cen td{padding:9px 10px 9px 0;border-bottom:1px solid var(--line);
 text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.cen td:nth-child(-n+4){text-align:left}
.cen td:nth-child(2){color:var(--ink);font-weight:500;font-family:var(--sans)}
.cen tr.vac td{color:var(--ink3)}
.dir{font-size:11px;padding:1px 7px;border:1px solid var(--line2);
 border-radius:2px;color:var(--ink3)}
.dir.b{color:var(--dn);border-color:var(--dn)}
.sk{font-family:var(--mono);font-size:11px;color:var(--ink3)}
.pat{border:1px solid var(--line);background:var(--card);margin:0 0 -1px;
 padding:17px 19px 19px}
.pat .ph{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:0 0 4px}
.pat .ph .id{font-family:var(--mono);color:var(--ph);font-size:13px}
.pat .ph h3{margin:0;font-size:17px;font-family:var(--serif)}
.pat .ph .en{font-size:11.5px;color:var(--ink3);font-style:italic}
.pat .st{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);
 font-size:11.5px;font-variant-numeric:tabular-nums;color:var(--ink3);margin:0 0 12px}
.pat .st b{color:var(--ink)}
.seq{font-family:var(--mono);font-size:12px;color:var(--ph);
 background:var(--zone);padding:5px 9px;display:inline-block;margin:0 0 10px}
.pat ol{margin:0 0 12px;padding:0 0 0 20px}
.pat ol li{font-size:13px;color:var(--ink2);margin:0 0 5px;line-height:1.6;
 font-family:var(--mono);font-variant-numeric:tabular-nums}
.pat ol li i{font-style:normal;color:var(--ink3);font-family:var(--sans);font-size:12px}
.pat ol li b{color:var(--ink)}
.pat .fp{font-size:12px;color:var(--ink3);margin:0 0 13px}
.pat .fp b{color:var(--ph)}
.pat .nt{font-size:12.5px;color:var(--ink3);line-height:1.68;margin:13px 0 0;
 border-left:2px solid var(--line2);padding-left:12px}
.pat .nt b{color:var(--ink)}
.figs{display:grid;grid-template-columns:196px 1fr;gap:16px;align-items:start}
.figs figure{margin:0}
.figs figcaption{font-size:11px;color:var(--ink3);margin:5px 0 0;font-family:var(--mono)}
.figs figcaption b{color:var(--ink)}
.figs svg{width:100%;display:block}
.lvl{stroke:var(--ph);stroke-width:1.2;stroke-dasharray:4 3}
.lvt{fill:var(--ph);font-family:var(--mono);font-size:9px}
@media (max-width:720px){.figs{grid-template-columns:1fr}}
''' + '</style>\n')


def table():
    tr = []
    for r in ROWS:
        vac = r['id'] in ('P41', 'P42')
        tr.append(
            '<tr%s><td>%s</td><td>%s</td>'
            '<td><span class="dir %s">%s</span></td><td class="sk">%s</td>'
            '<td>%s</td><td>%s</td><td class="%s">%s</td><td>%d 根</td></tr>'
            % (' class="vac"' if vac else '', r['id'], r['zh'],
               'b' if r['dir'] == '空' else '', r['dir'],
               '樞紐' if r['sk'] == 'pivot' else 'K 棒',
               format(r['n'], ','), format(r['mirror'], ','),
               '' if vac else 'z',
               ('%.2fx' % r['ratio']) if not vac else '結構上無效',
               r['span']))
    return ''.join(tr)


def block(r):
    cid = r['id']
    seq, lines, note = LOGIC[cid]
    d = EX[cid]
    return (
        '<div class="pat"><div class="ph"><span class="id">%s</span>'
        '<h3>%s</h3><span class="en">%s</span>'
        '<span class="dir %s">%s</span></div>'
        '<div class="st"><span>母體 <b>%s</b></span><span>鏡像 %s</span>'
        '<span>倍率 <b>%s</b></span><span>跨度中位 <b>%d</b> 根</span>'
        '<span>骨架 %s</span></div>'
        '<div class="seq">%s</div><ol>%s</ol>'
        '<p class="fp">自由參數 <b>%s</b></p>'
        '<div class="figs"><figure>%s<figcaption>示意</figcaption></figure>'
        '<figure>%s<figcaption>真實案例　%s　%04d–%04d　振幅 %.0f 點　'
        '跨 %d 根　可用 %s 個中取<b>中位振幅</b></figcaption></figure></div>'
        '<p class="nt">%s</p></div>'
        % (cid, r['zh'], r['en'], 'b' if r['dir'] == '空' else '', r['dir'],
           format(r['n'], ','), format(r['mirror'], ','),
           ('%.2fx' % r['ratio']) if cid not in ('P41', 'P42') else '—',
           r['span'], '樞紐' if r['sk'] == 'pivot' else 'K 棒',
           seq, ''.join('<li>%s</li>' % x for x in lines),
           '0（N=4／7 為 Crabel 借用常數）' if cid in ('P41', 'P42') else '0',
           sch(cid), real(cid), d['d0'], d['t0'], d['t1'], d['amp'],
           d['span'], format(d['n'], ','), note))


DOC = (HEAD
 + '<div class="wrap"><header class="top">'
   '<div class="eyebrow">S16_S 型態層 · 最後一組 · 2026-08-31</div>'
   '<h1>十一種型態的完整流程</h1>'
   '<p class="sub">型態層最後要走完整流程的一組。'
   '進來的時候是 12 種，<b>P39 三下降峰在寫定義之前就被化約掉了</b>。</p>'
   '<div class="kpi"><span><b>11</b>種</span>'
   '<span><b>0.78–1.02x</b>鏡像倍率全距</span>'
   '<span><b>0</b>具空方傾向</span>'
   '<span><b>1–6</b>跨度中位（根）</span></div></header>'

 + '<section class="panel"><div class="ph2"><h2>一、先化約，再定義</h2>'
   '<span class="tag">12 → 11</span></div>'
   '<div class="warn"><b>P39 三下降峰 ＝ 頭頭降原語，逐字相同（5,280 對 5,280）。</b>'
   '它對低點完全不設條件，所以同時橫跨 2×2 的兩格，不是在指名一格。</div>'
   '<p class="cap">另外兩個化約候選<b>都活下來了</b>：</p>'
   '<table><thead><tr><th>候選</th><th style="text-align:left">結果</th>'
   '</tr></thead><tbody>'
   '<tr><td>P35 ＝ 底底降？</td><td style="text-align:left"><b>不是。</b>'
   '收盤穿越 <b>24,129</b> 次，下一個樞紐低更低 <b>34,116</b> 次。'
   '差額是<b>低點戳破但收盤沒破</b>的情況 —— 那正是這個型態要排除的</td></tr>'
   '<tr><td>P13／P14 沿用圖鑑定義？</td><td style="text-align:left">'
   '<b>不能。</b>圖鑑給 20,938 與 4,634，沒有任何 WR4 骨架接近，'
   '代表當初量的是別的東西。<b>重新定義</b></td></tr>'
   '</tbody></table></section>'

 + '<section class="panel"><div class="ph2"><h2>二、一句話結論</h2>'
   '<span class="tag">與前一組同一個結果</span></div>'
   '<div class="warn"><b>十一個的鏡像倍率全部落在 0.78x 到 1.02x。'
   '沒有一個偏好空方。</b></div>'
   '<p class="cap">對照樞紐型 A 組：P18 三重頂 <b>10.19x</b>、'
   'P17 雙頂 <b>6.75x</b> —— 差一個數量級。</p>'
   '<div class="big"><p><b>而三個過得了門檻的，方向全部相反。</b></p>'
   '<table><thead><tr><th>代號</th><th>空方</th><th>多方鏡像</th>'
   '<th>空方占比</th><th>z</th></tr></thead><tbody>'
   '<tr><td>P35 結構破壞</td><td>24,129</td><td>26,016</td><td>48.1%</td>'
   '<td class="z">−8.43</td></tr>'
   '<tr><td>P45 破前時段低</td><td>1,477</td><td>1,894</td><td>43.8%</td>'
   '<td class="z">−7.18</td></tr>'
   '<tr><td>P48 管狀頂</td><td>4,973</td><td>5,343</td><td>48.2%</td>'
   '<td class="z">−3.64</td></tr></tbody></table>'
   '<small>十一次檢定的 Bonferroni 門檻是 |z| ≥ 2.86。這三個都過了，'
   '<b>但空方版都比多方版「少」</b> —— 那是台指偏多 regime 的漂移，'
   '不是型態的邊。<b>它不能拿來當作這些型態有效的證據。</b></small></div>'
   '<p class="cap"><b>★ 而 P41／P42 的鏡像測試結構上是空的。</b>'
   '振幅 |H − L| 在鏡射下不變，所以兩邊必然相同（82,209 與 44,403，'
   '一個不差）。<b>那不是發現，是算術</b>，不可引為證據。</p></section>'

 + '<section class="panel"><div class="ph2"><h2>三、母體普查</h2>'
   '<span class="tag">只有次數，沒有損益</span></div>'
   '<table class="cen"><thead><tr><th>代號</th><th>名稱</th><th>方向</th>'
   '<th>骨架</th><th>母體</th><th>鏡像</th><th>倍率</th><th>跨度中位</th>'
   '</tr></thead><tbody>' + table() + '</tbody></table>'
   '<p class="cap"><b>跨度中位 1–6 根。</b>視窗 1 下每 2.8 根就認一個樞紐，'
   '所以這整組都在<b>K 棒尺度</b>，不是圖形尺度 —— 與 8/29 樞紐尺度那一頁'
   '的結論一致。</p></section>'

 + '<section class="panel"><div class="ph2"><h2>四、十一個定義，逐條列出</h2>'
   '<span class="tag">左邊是我想的，右邊是市場真的長的樣子</span></div>'
   '<p class="cap">八個是 <b>K 棒骨架</b>，所以示意圖畫的是 K 棒不是折線 —— '
   '「上影比實體長」用折線畫不出來。'
   '真實案例<b>取中位振幅、不跨時段</b>，底色是型態自己的範圍。</p>'
   + ''.join(block(r) for r in ROWS) + '</section>'

 + '<section class="panel"><div class="ph2"><h2>五、用到的四個裝置</h2>'
   '<span class="tag">全部零參數</span></div><div class="two">'
   '<div class="vf"><h3>排名</h3><p>「最近 N 根最寬」不是門檻是<b>排名</b>。'
   'N=4 與 N=7 是 Crabel 的常數，2026-08-31 裁示 5 明確記為'
   '<b>「借用」而非「推導」</b> —— 這是全專案唯一被承認的外來常數。</p></div>'
   '<div class="vf"><h3>影線 vs 實體</h3><p>「<b>長</b>上影」是門檻，'
   '「<b>上影比實體長</b>」是比較。同一句話換個寫法就不花參數了。</p></div>'
   '<div class="vf"><h3>差距 vs 影線</h3><p>「兩個高點差不多高」需要容差 —— '
   '<b>K 棒自己給</b>：差距小於較短的那根影線。與區間裝置同一個精神，'
   '容差由型態推導。</p></div>'
   '<div class="vf"><h3>跑到分出勝負</h3><p>旗形的飄移<b>沒有根數</b>：'
   '先破旗桿底算成立、先過旗桿頂算作廢。'
   '<b>「旗形要多長」這個問題根本不會被問到。</b></p></div>'
   '</div></section>'

 + '<section class="panel"><div class="ph2"><h2>六、待裁示</h2>'
   '<span class="tag">兩題</span></div>'
   '<table><thead><tr><th>題目</th><th style="text-align:left">說明</th>'
   '</tr></thead><tbody>'
   '<tr><td>11 個怎麼處理</td><td style="text-align:left">'
   '鏡像倍率 0.78–1.02x，<b>與前一組同一個理由</b>。'
   '但依你 08-31 的落地標準（<b>落地 ＝ 畫得到</b>），'
   '「沒有方向」不是不畫的理由 —— <b>建議全部編碼上圖</b>，'
   '型態層就 100% 落地</td></tr>'
   '<tr><td>P39 三下降峰</td><td style="text-align:left">'
   '已證實等於頭頭降原語。<b>骨架已經畫在圖上</b>（2×2 家族），'
   '建議<b>不另外編碼</b>，比照 P24／P25</td></tr>'
   '</tbody></table></section>'

 + '<footer class="foot">'
   '化約 <code>s16s_twelve_reduce.py</code>、普查 <code>s16s_eleven_scan.py</code>、'
   '案例 <code>s16s_eleven_pick.py</code>、本頁 <code>s16s_eleven_make_page.py</code>。'
   '母體 421,513 根 5 分 K，重置鏈。<b>本頁無損益欄。</b></footer></div>')

for tag in ('section', 'div', 'p', 'ol', 'li', 'table', 'tbody', 'thead',
            'tr', 'td', 'th', 'svg', 'figure', 'figcaption', 'header'):
    op = len(re.findall(r'<%s(?=[\s>/])' % tag, DOC))
    cl = len(re.findall(r'</%s\s*>' % tag, DOC))
    assert op == cl, '%s: %d open, %d close' % (tag, op, cl)
assert len(ROWS) == 11
assert all(r['id'] in LOGIC and r['id'] in SCH and r['id'] in EX for r in ROWS)
print('  標籤平衡 OK')
open(OUT, 'w', encoding='utf-8').write(DOC)
print('wrote %s' % OUT)
print('  11 個逐條邏輯 ＋ 11 個真實案例   %.0f KB'
      % (len(DOC.encode('utf-8')) / 1024))
