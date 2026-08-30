# -*- coding: utf-8 -*-
"""The census page for the fifteen patterns still unstudied.

Willy's process: this group gets its OWN page while it is being discussed,
and only joins the master page once it is closed -- the same route the
broadening family, the gap group, the diamond and the pivot group took.

The page has to carry the census AND the two devices the definitions rest
on, because the definitions are the part he will want to argue with, and
"a shape occurred 608 times" means nothing until the reader can see what
shape was being counted.

Run:  python scripts/research/s16s_census15_make_page.py
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 's16s_census15.json')
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_census15_diagram.html'))

D = json.load(open(DATA, encoding='utf-8'))
ROWS = D['rows']
MEAS = [r for r in ROWS if r['n'] is not None]
SKIP = [r for r in ROWS if r['n'] is None]

# schematic: (points, caption) per pattern, drawn from the definition itself
SCH = {
    'P26': ([(0, 78), (14, 40), (28, 20), (42, 12), (56, 22), (70, 44),
             (84, 80)], '步幅遞減進場、遞增離場 —— 穹頂'),
    'P32': ([(0, 82), (14, 62), (28, 34), (42, 10), (56, 36), (70, 62),
             (84, 82)], '步幅遞增進場、遞減離場 —— 尖峰'),
    'P27': ([(0, 20), (14, 58), (28, 78), (42, 86), (56, 76), (70, 54),
             (84, 18)], '碗底'),
    'P63': ([(0, 16), (14, 36), (28, 64), (42, 88), (56, 62), (70, 36),
             (84, 16)], '尖底'),
    'P66': ([(0, 22), (14, 62), (28, 80), (42, 80), (56, 80), (70, 60),
             (84, 20)], '底部三點落在彼此的區間內 —— 平底'),
    'P28': ([(0, 18), (12, 56), (24, 78), (36, 86), (48, 74), (60, 50),
             (72, 18), (80, 38), (88, 20)], '碗 ＋ 柄，柄低點在兩杯緣之間'),
    'P64': ([(0, 82), (12, 44), (24, 22), (36, 14), (48, 26), (60, 50),
             (72, 82), (80, 62), (88, 80)], '穹頂 ＋ 柄'),
    'P59': ([(0, 34), (16, 66), (32, 84), (48, 60), (64, 26), (80, 14)],
            'J 形：右側高點超過左側高點'),
    'P24': ([(0, 86), (20, 14), (36, 34), (52, 22), (68, 44), (84, 32)],
            '旗桿 ＋ 平行下傾旗面，整面留在旗桿區間內'),
    'P25': ([(0, 86), (20, 14), (36, 36), (52, 24), (68, 32), (84, 28)],
            '旗桿 ＋ 收斂旗面'),
    'P56': ([(0, 14), (26, 76), (52, 44), (84, 90)],
            '跌 ＋ 部分反彈（在跌幅區間內）＋ 續跌破前低'),
    'P65': ([(0, 82), (34, 12), (68, 90)], '跌得比漲得快，K 棒數不多於上漲腿'),
    'P72': ([(0, 60), (30, 84), (60, 22)], '結構轉折前的最後一個反向樞紐'),
    'P55': ([(0, 76), (22, 62), (44, 20), (66, 46), (88, 82)],
            '三條趨勢線 ＋ 角度門檻'),
    'P60': ([(0, 92), (22, 10), (44, 26), (66, 18), (88, 24)],
            '旗桿漲幅「接近翻倍」'),
}


def poly(pts, cls):
    return ('<polyline class="%s" points="%s"/>'
            % (cls, ' '.join('%d,%d' % p for p in pts)))


def svg(cid):
    pts, cap = SCH[cid]
    dots = ''.join('<circle class="pv" cx="%d" cy="%d" r="2.6"/>' % p
                   for p in pts)
    return ('<svg viewBox="-6 0 100 104" role="img" aria-label="%s">'
            '<line class="ax" x1="-4" y1="98" x2="94" y2="98"/>'
            '%s%s</svg>' % (cap, poly(pts, 'plot'), dots))


def band(v, lo, hi):
    return 'z' if lo <= v <= hi else ''


HEAD = ('<title>十五種母體普查</title>\n'
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
.cen th:nth-child(1),.cen th:nth-child(2),.cen th:nth-child(3){text-align:left}
.cen td{padding:9px 10px 9px 0;border-bottom:1px solid var(--line);
 text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.cen td:nth-child(1),.cen td:nth-child(2),.cen td:nth-child(3){
 text-align:left;font-family:var(--sans)}
.cen td:nth-child(1){font-family:var(--mono);color:var(--ink)}
.cen td:nth-child(2){color:var(--ink);font-weight:500}
.cen tr.sh td{color:var(--brk)}
.cen .dir{font-size:11px;padding:1px 7px;border:1px solid var(--line2);
 border-radius:2px;color:var(--ink3)}
.cen .dir.b{color:var(--dn);border-color:var(--dn)}
.cen .dir.u{color:var(--up);border-color:var(--up)}
.grid15{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 grid-template-columns:repeat(auto-fit,minmax(268px,1fr));margin:6px 0 0}
.c15{background:var(--card);padding:15px 16px 17px}
.c15 h4{margin:0 0 3px;font-size:14px;font-family:var(--serif)}
.c15 h4 .id{font-family:var(--mono);color:var(--ph);margin-right:7px;
 font-size:12px}
.c15 .en{font-size:11px;color:var(--ink3);font-style:italic;margin:0 0 9px}
.c15 svg{width:100%;height:106px;display:block;margin:2px 0 9px}
.c15 .plot{fill:none;stroke:var(--ink2);stroke-width:1.6;
 stroke-linejoin:round;stroke-linecap:round}
.c15 .pv{fill:var(--ph);stroke:none}
.c15 .ax{stroke:var(--line2);stroke-width:1}
.c15 p{margin:0;font-size:12.5px;color:var(--ink3);line-height:1.62}
.c15 .num{display:flex;gap:14px;margin:9px 0 0;font-family:var(--mono);
 font-size:12px;font-variant-numeric:tabular-nums}
.c15 .num b{color:var(--ink)}
.c15 .num i{font-style:normal;color:var(--ink3)}
.c15.no{background:var(--bg)}
.c15.no p{color:var(--ink2)}
''' + '</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S 型態層 · 母體普查 · 2026-08-30</div>'
       '<h1>十五種母體普查</h1>'
       '<p class="sub">型態層剩下的最後 15 種。裁示 C：'
       '<b>先把母體一次量完，再決定多方型態怎麼處理</b> —— '
       '母體是 0 或爆量的那些，不管裁示怎麼走都是同一個結論。</p>'
       '<div class="kpi">'
       '<span><b>13</b>可零參數定義</span>'
       '<span><b>2</b>定不出來</span>'
       '<span><b>0.89–1.08x</b>鏡像倍率全距</span>'
       '<span><b>0</b>具方向性</span>'
       '</div></header>')

HEADLINE = (
    '<section class="panel"><div class="ph2"><h2>一、一句話結論</h2>'
    '<span class="tag">13 個全部落在同一格</span></div>'
    '<div class="warn"><b>十三個型態的鏡像倍率全部落在 0.89x 到 1.08x 之間。</b>'
    '沒有任何一個偏好某個方向。</div>'
    '<p class="cap">對照樞紐型 A 組：P18 三重頂 <b>10.19x</b>、'
    'P68 雙頂 <b>6.75x</b>、P57 測量移動 <b>2.33x</b>。'
    '這裡最高的是 P63 V 型底的 <b>1.08x</b> —— 差了一個數量級。</p>'
    '<div class="big"><p>這正是<b>三類條件</b>裡的第二類：<b>峰谷形狀</b>。'
    '把價格上下顛倒之後，同一個判定<b>通過的次數幾乎一模一樣</b>，'
    '所以形狀本身不含方向資訊。這也正是 P15 頭肩頂與 P16 頭肩底'
    '被排除的同一個理由。</p>'
    '<small><b>要講清楚這個測試沒有證明什麼。</b>'
    '鏡像倍率測的是<b>方向偏好</b>，不是<b>是否含資訊</b>。'
    '一個型態可以完全對稱、卻仍然比隨機常見（或罕見）—— '
    'P29 擴散三角的獨立性比就是 0.16x，遠低於隨機，但它照樣是有用的結構。'
    '<b>獨立性比與區塊局部置換對照組都還沒跑</b>，'
    '如果你要留下其中任何一個，那才是下一步。</small></div></section>')


def census_table():
    tr = []
    for r in MEAS:
        rat = r['ratio']
        short = r['span'] <= 10
        tr.append(
            '<tr%s><td>%s</td><td>%s</td>'
            '<td><span class="dir %s">%s</span></td>'
            '<td>%s</td><td>%s</td><td class="%s">%.2fx</td>'
            '<td class="%s">%d 根</td></tr>'
            % (' class="sh"' if short else '', r['id'], r['zh'],
               'b' if r['dir'] == '空' else 'u' if r['dir'] == '多' else '',
               r['dir'], format(r['n'], ','), format(r['mirror'], ','),
               band(rat, 0.85, 1.15), rat,
               'z' if short else '', r['span']))
    return ''.join(tr)


P2 = ('<section class="panel"><div class="ph2">'
      '<h2>二、母體普查</h2>'
      '<span class="tag">只有次數，沒有損益</span></div>'
      '<table class="cen"><thead><tr><th>代號</th><th>名稱</th><th>方向</th>'
      '<th>母體</th><th>鏡像</th><th>倍率</th><th>跨度中位</th>'
      '</tr></thead><tbody>' + census_table() + '</tbody></table>'
      '<p class="cap"><b>倍率</b> ＝ 母體 ÷ 鏡像母體。1.00x 代表把價格上下顛倒後'
      '出現次數一樣，也就是形狀不含方向。'
      '<b>橘色那三列的跨度中位 ≤ 10 根</b> —— 視窗 1 每 2.8 根就認一個樞紐，'
      '10 根只夠三四個樞紐，那是 K 棒尺度不是圖形尺度。</p></section>')

P3 = ('<section class="panel"><div class="ph2">'
      '<h2>三、十三個零參數定義</h2>'
      '<span class="tag">先看定義，再看數字</span></div>'
      '<div class="grid15">'
      + ''.join(
          '<div class="c15"><h4><span class="id">%s</span>%s</h4>'
          '<p class="en">%s</p>%s<p>%s</p>'
          '<div class="num"><span><i>母體</i> <b>%s</b></span>'
          '<span><i>鏡像</i> %s</span><span><i>倍率</i> <b>%.2fx</b></span>'
          '<span><i>跨度</i> %d 根</span></div></div>'
          % (r['id'], r['zh'], r['en'], svg(r['id']), r['note'],
             format(r['n'], ','), format(r['mirror'], ','),
             r['ratio'], r['span'])
          for r in MEAS)
      + '</div></section>')

P4 = ('<section class="panel"><div class="ph2">'
      '<h2>四、兩個定不出零參數版本的</h2>'
      '<span class="tag">不硬編一個定義來湊數</span></div>'
      '<div class="grid15">'
      + ''.join(
          '<div class="c15 no"><h4><span class="id">%s</span>%s</h4>'
          '<p class="en">%s</p>%s<p>%s</p></div>'
          % (r['id'], r['zh'], r['en'], svg(r['id']), r['note'])
          for r in SKIP)
      + '</div>'
      '<p class="cap">硬湊一個定義出來，量到的數字只會反映我挑的門檻，'
      '不會反映市場 —— <b>P07 布林帶寬就是這樣：週期從 20 改成 30，'
      '只剩 18.4% 是同一批 K 棒</b>。所以這兩個留白等裁示。</p></section>')

P5 = ('<section class="panel"><div class="ph2">'
      '<h2>五、定義用到的兩個裝置</h2>'
      '<span class="tag">都不花參數</span></div>'
      '<div class="two">'
      '<div class="vf"><h3>步幅單調</h3>'
      '<p>「圓」和「V」的差別是<b>曲率</b>，曲率一般需要門檻。這裡不需要：'
      '<b>比較相鄰兩步的大小</b>就好。穹頂進場時步幅遞減、離場時遞增；'
      '尖峰完全相反。純序數，沒有任何東西可以調。</p>'
      '<p class="cap">所以 P26 圓弧頂與 P32 V 型反轉<b>用同樣的五個高點</b>，'
      '只差在步幅的方向 —— 兩者互斥，不會重複計數。</p></div>'
      '<div class="vf"><h3>區間裝置</h3>'
      '<p>兩點定義區間、第三點受測：<code>min(A,B) ≤ C ≤ max(A,B)</code>。'
      '<b>容差由型態自身推導</b>，順序因果正確，而且免疫於衰減律。</p>'
      '<p class="cap">杯柄的柄低點落在<b>左右兩個杯緣之間</b>；'
      '平底鍋底的中間低點落在<b>左右兩個低點之間</b>；'
      '旗形的旗面必須留在<b>旗桿的區間內</b>。'
      '全都不需要「回撤不超過幾成」這種數字。</p></div>'
      '</div></section>')

P6 = ('<section class="panel"><div class="ph2">'
      '<h2>六、待裁示</h2>'
      '<span class="tag">三題</span></div>'
      '<table><thead><tr><th>題目</th><th style="text-align:left">說明</th>'
      '</tr></thead><tbody>'
      '<tr><td>13 個怎麼處理</td><td style="text-align:left">'
      '全部鏡像倍率 0.89–1.08x，<b>與 P15／P16 同一個理由</b>。'
      '建議<b>整組結案</b>，型態層歸零。'
      '若要留任何一個，下一步是跑獨立性比與區塊局部置換對照組</td></tr>'
      '<tr><td>P55 駝峰反轉</td><td style="text-align:left">'
      '三條趨勢線 ＋ 角度門檻，與 P58／P71 同類。'
      '你 08-30 的範疇裁示<b>看起來直接涵蓋它</b>，但我不替你決定</td></tr>'
      '<tr><td>P60 高位緊密旗形</td><td style="text-align:left">'
      '「翻倍」是外來常數。它是 P24 加一個幅度門檻，'
      '<b>P24 的 1,758 就是它的上限</b>，而 P24 本身倍率 0.89x</td></tr>'
      '</tbody></table>'
      '<p class="cap">如果三題都照建議走，<b>型態層 72 種全部處理完畢</b>，'
      '接下來就是訊號層。</p></section>')

FOOT = ('<footer class="foot">'
        '普查 <code>scripts/research/s16s_census15_scan.py</code>，'
        '本頁 <code>scripts/research/s16s_census15_make_page.py</code>，'
        '資料 <code>s16s_census15.json</code>。'
        '母體 421,513 根 5 分 K，視窗 1 樞紐 106,283 個。'
        '<b>本頁無損益欄。</b></footer></div>')

DOC = HEAD + TOP + HEADLINE + P2 + P3 + P4 + P5 + P6 + FOOT

# A script that assembles structure has to check the structure it assembled.
# P2 shipped once without its closing </section> and every later panel nested
# inside it, which no amount of reading the source would have caught.
import re
for tag in ('section', 'div', 'p', 'table', 'tbody', 'thead', 'tr', 'td',
            'th', 'svg'):
    # the boundary matters: a bare '<p' also matches '<polyline', and a check
    # that cries wolf is a check that gets switched off
    op = len(re.findall(r'<%s(?=[\s>/])' % tag, DOC))
    cl = len(re.findall(r'</%s\s*>' % tag, DOC))
    assert op == cl, '%s: %d open, %d close' % (tag, op, cl)
print('  標籤平衡  OK')

open(OUT, 'w', encoding='utf-8').write(DOC)
print('wrote %s' % OUT)
print('  型態卡 %d 張（%d 已量 ＋ %d 未量）'
      % (len(ROWS), len(MEAS), len(SKIP)))
rat = [r['ratio'] for r in MEAS]
print('  鏡像倍率 %.2f – %.2f' % (min(rat), max(rat)))
assert len(ROWS) == 15, 'census must cover all fifteen'
assert all(r['id'] in SCH for r in ROWS), 'every pattern needs a schematic'
