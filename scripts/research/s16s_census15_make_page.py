# -*- coding: utf-8 -*-
"""The census page for the fifteen patterns still unstudied.

Willy's process: this group keeps its OWN page while under discussion and
joins the master only once closed -- the same route the broadening family,
the gap group, the diamond and the pivot group took.

He then asked for the thirteen to carry their full logic AND a real chart to
check it against.  That is the right demand: a definition nobody can compare
to real bars is a definition nobody can disagree with, which is worse than a
wrong one.  Writing them out already caught two faults -- the cup's left rim
was a high INSIDE the cup, and the tower top carried a condition that never
changed the answer.

Run:  python scripts/research/s16s_census15_scan.py
      python scripts/research/s16s_census15_pick.py
      python scripts/research/s16s_census15_make_page.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()
D = json.load(open(os.path.join(HERE, 's16s_census15.json'), encoding='utf-8'))
EX = json.load(open(os.path.join(HERE, 's16s_census15_example.json'),
                    encoding='utf-8'))
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_census15_diagram.html'))
ROWS = D['rows']
MEAS = [r for r in ROWS if r['n'] is not None]
SKIP = [r for r in ROWS if r['n'] is None]

LT, GT, GE, LE = '&lt;', '&gt;', '&ge;', '&le;'

# 代號: (樞紐序列, [逐條定義], 附註)
LOGIC = {
 'P26': ('H L H L H L H L H', [
   'PH1 %s PH2 %s PH3 %s PH4 %s PH5' % (LT, LT, GT, GT),
   '(PH2 − PH1) %s (PH3 − PH2)　<i>上升步幅遞減</i>' % GT,
   '(PH3 − PH4) %s (PH4 − PH5)　<i>下降步幅遞增</i>' % LT,
   '四個低點<b>不設條件</b>'],
   '只讀高點。「圓」的意思就是<b>越接近頂越走不動、離開頂越走越快</b>，'
   '不需要曲率門檻。'
   '<br>本例的高點步幅是 <b>+45 → +6</b> 然後 <b>−7 → −26</b>，'
   '頂部三個高點只差 7 點 —— 那個「圓」是這個尺度下該有的樣子。'),
 'P32': ('H L H L H L H L H', [
   'PH1 %s PH2 %s PH3 %s PH4 %s PH5' % (LT, LT, GT, GT),
   '(PH2 − PH1) %s (PH3 − PH2)　<i>上升步幅遞增</i>' % LT,
   '(PH3 − PH4) %s (PH4 − PH5)　<i>下降步幅遞減</i>' % GT,
   '四個低點<b>不設條件</b>'],
   '與 P26 <b>用完全同樣的五個高點</b>，只有兩條步幅不等式方向相反 —— '
   '所以兩者<b>互斥，不會重複計數</b>。'
   '<br><b>本例的第一步只有 1 點</b>（17754 → 17755）。'
   '步幅是兩個差值的嚴格比大小，差值小的時候就是一個 tick 在決定 —— '
   '見下方「定義健壯度」。'),
 'P27': ('L H L H L H L H L', [
   'PL1 %s PL2 %s PL3 %s PL4 %s PL5' % (GT, GT, LT, LT),
   '(PL1 − PL2) %s (PL2 − PL3)　<i>下降步幅遞減</i>' % GT,
   '(PL4 − PL3) %s (PL5 − PL4)　<i>上升步幅遞增</i>' % LT,
   '四個高點<b>不設條件</b>'],
   'P26 的鏡像，只讀低點。'),
 'P63': ('L H L H L H L H L', [
   'PL1 %s PL2 %s PL3 %s PL4 %s PL5' % (GT, GT, LT, LT),
   '(PL1 − PL2) %s (PL2 − PL3)　<i>下降步幅遞增</i>' % LT,
   '(PL4 − PL3) %s (PL5 − PL4)　<i>上升步幅遞減</i>' % GT,
   '四個高點<b>不設條件</b>'],
   'P27 的尖底版本，兩者互斥。'),
 'P66': ('L H L H L H L H L', [
   'PL1 %s PL2' % GT,
   'PL5 %s PL4' % GT,
   'min(PL2, PL4) %s PL3 %s max(PL2, PL4)　<b>區間裝置</b>' % (LE, LE)],
   '底部三個低點<b>互相落在彼此的區間內</b>就算平 —— '
   '容差就是 |PL2 − PL4|，由型態自己給，'
   '不需要「幾點以內算相等」這種外來數字。'
   '<br><b>我一度懷疑這條是空的</b>：PL3 在時間上夾在 PL2 與 PL4 之間，'
   '而三個數的中間那個本來就常常落在外兩個之間。'
   '<b>查了 —— 它排掉 50%（12,676 → 6,303），不是空的。</b>'),
 'P28': ('H L H L H L H L H L H L', [
   '碗：PL1 %s PL2 %s PL3 %s PL4 %s PL5，步幅條件同 P27' % (GT, GT, LT, LT),
   '左杯緣 ＝ <b>PH1</b>（下跌開始<u>之前</u>的高點）',
   '右杯緣 ＝ <b>PH6</b>',
   'min(PH1, PH6) %s PL6 %s max(PH1, PH6)　<b>柄低點在兩杯緣之間</b>'
   % (LE, LE)],
   '<b>這裡原本錯了。</b>第一版把「左杯緣」取成杯子<u>裡面</u>的第一個高點，'
   '那個點在碗內不在緣上，區間整個偏低。'
   '寫這段邏輯給你看的時候才發現 —— 母體從 164 修正為 <b>134</b>。'),
 'P64': ('L H L H L H L H L H L H', [
   '穹頂：PH1 %s PH2 %s PH3 %s PH4 %s PH5，步幅條件同 P26' % (LT, LT, GT, GT),
   '左緣 ＝ <b>PL1</b>，右緣 ＝ <b>PL6</b>',
   'min(PL1, PL6) %s PH6 %s max(PL1, PL6)　<b>柄高點在兩緣之間</b>'
   % (LE, LE)],
   'P28 的鏡像，母體同步修正為 <b>149</b>。'),
 'P59': ('H L H L H L H', [
   'PL1 %s PL2 %s PL3　<i>碗</i>' % (GT, LT),
   '(PL1 − PL2) %s (PL3 − PL2)　<i>左側比右側深</i>' % GT,
   'PH4 %s PH1　<b>右側高點超過左側高點，J 完成</b>' % GT],
   '<b>要講清楚我少做了什麼。</b>教科書的「<u>下降</u>穿越型態」還要求'
   '連續數個穿越逐一走低，那需要一個跨型態的參考框架 —— '
   '<b>本次沒有實作</b>，量到的是<b>單一個 J</b>。'),
 'P24': ('L H L H L H', [
   'PH1 %s PL1　<i>旗桿</i>' % GT,
   'PH2 %s PH1，PH3 %s PH2　<i>高點遞降</i>' % (LT, LT),
   'PL3 %s PL2　<i>低點遞降，旗面平行下傾</i>' % LT,
   'PL1 %s PL2 %s PH1 且 PL1 %s PL3 %s PH1　<b>旗面留在旗桿區間內</b>'
   % (LE, LE, LE, LE)],
   '「旗面要多小」用<b>旗桿自己的區間</b>回答，'
   '不需要「回撤不超過幾成」這種數字。'),
 'P25': ('L H L H L H', [
   'PH1 %s PL1　<i>旗桿</i>' % GT,
   'PH2 %s PH1，PH3 %s PH2　<i>高點遞降</i>' % (LT, LT),
   'PL3 %s PL2　<b>低點遞升 —— 收斂</b>' % GT,
   'PL1 %s PL2 %s PH1 且 PL1 %s PL3 %s PH1' % (LE, LE, LE, LE)],
   '與 P24 只差第三條的方向：<b>遞降是旗形、遞升是三角旗</b>，兩者互斥。'),
 'P56': ('H L H L', [
   'PL1 %s PH1　<i>下跌</i>' % LT,
   'PL1 %s PH2 %s PH1　<b>反彈落在跌幅區間內</b>' % (LE, LE),
   'PL2 %s PL1　<i>續跌破前低</i>' % LT],
   '「反彈只有一部分」用<b>跌幅本身的區間</b>回答。'
   '真正在篩的是第三條 —— 前兩條在交替樞紐鏈上幾乎必然成立。'),
 'P65': ('L H L', [
   'PH1 %s PL1　<i>上漲腿</i>' % GT,
   'PL2 %s PL1　<b>完全回吐</b>' % LT,
   '下跌腿 K 棒數 %s 上漲腿 K 棒數　<b>跌得比漲得快</b>' % LE],
   '<b>原本還有一條「跌幅 %s 漲幅」，是完全冗餘的</b> —— '
   '它可由「完全回吐」推得，加不加都是 8,386。'
   '已移除：寫著一條永遠成立的條件，'
   '會讓讀的人以為有東西在被檢查。' % GE),
 'P72': ('H L H', [
   'PL1 %s PH1' % LT,
   'PH2 %s PH1　<b>結構突破</b>' % GT],
   'PL1 就是突破前<b>最後一個反向樞紐</b>。'
   '我原本以為第一條在交替鏈上恆真 —— <b>查了，不是</b>：'
   '只留第二條會變成 25,199，第一條實際排掉 <b>492</b> 個。'),
}

SCH = {
 'P26': [(0, 78), (14, 40), (28, 20), (42, 12), (56, 22), (70, 44), (84, 80)],
 'P32': [(0, 82), (14, 62), (28, 34), (42, 10), (56, 36), (70, 62), (84, 82)],
 'P27': [(0, 20), (14, 58), (28, 78), (42, 86), (56, 76), (70, 54), (84, 18)],
 'P63': [(0, 16), (14, 36), (28, 64), (42, 88), (56, 62), (70, 36), (84, 16)],
 'P66': [(0, 22), (14, 62), (28, 80), (42, 80), (56, 80), (70, 60), (84, 20)],
 'P28': [(0, 12), (12, 52), (24, 76), (36, 86), (48, 72), (60, 46), (72, 14),
         (80, 40), (88, 16)],
 'P64': [(0, 88), (12, 48), (24, 24), (36, 14), (48, 28), (60, 54), (72, 86),
         (80, 60), (88, 84)],
 'P59': [(0, 34), (16, 66), (32, 84), (48, 60), (64, 26), (80, 14)],
 'P24': [(0, 86), (20, 14), (36, 34), (52, 22), (68, 44), (84, 32)],
 'P25': [(0, 86), (20, 14), (36, 36), (52, 24), (68, 32), (84, 28)],
 'P56': [(0, 14), (26, 76), (52, 44), (84, 90)],
 'P65': [(0, 82), (34, 12), (68, 90)],
 'P72': [(0, 60), (30, 84), (60, 22)],
 'P55': [(0, 76), (22, 62), (44, 20), (66, 46), (88, 82)],
 'P60': [(0, 92), (22, 10), (44, 26), (66, 18), (88, 24)],
}

W, HH, PL_, PR, PT, PB = 520.0, 178.0, 8.0, 8.0, 12.0, 12.0


def sch(cid):
    pts = SCH[cid]
    return ('<svg viewBox="-6 0 100 104" role="img">'
            '<line class="ax" x1="-4" y1="98" x2="94" y2="98"/>'
            '<polyline class="plot" points="%s"/>%s</svg>'
            % (' '.join('%d,%d' % p for p in pts),
               ''.join('<circle class="pv" cx="%d" cy="%d" r="2.6"/>' % p
                       for p in pts)))


def real(cid):
    """The real instance: candles with the pattern's own pivots ringed."""
    d = EX[cid]
    bars, pv = d['bars'], d['piv']
    n = len(bars)
    lo = min(b['l'] for b in bars)
    hi = max(b['h'] for b in bars)
    rng = (hi - lo) or 1.0

    def X(i):
        return PL_ + (W - PL_ - PR) * (i + .5) / n

    def Y(v):
        return PT + (HH - PT - PB) * (hi - v) / rng

    bw = max((W - PL_ - PR) / float(n) * 0.56, 2.0)
    o = []
    idx = [p[0] for p in pv]
    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
             % (X(min(idx)) - bw, PT - 5,
                X(max(idx)) - X(min(idx)) + 2 * bw, HH - PT - PB + 10))
    for i, b in enumerate(bars):
        c = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (c, x, Y(b['h']), x, Y(b['l'])))
        t, bt = Y(max(b['o'], b['c'])), Y(min(b['o'], b['c']))
        if bt - t < 1.2:
            m = (t + bt) / 2.0
            t, bt = m - .6, m + .6
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" '
                 'height="%.1f"/>' % (c, x - bw / 2, t, bw, bt - t))
    for i, k in pv:
        v = bars[i]['h'] if k == 'H' else bars[i]['l']
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="3.6"/>'
                 % ('ph' if k == 'H' else 'pl', X(i), Y(v)))
    return ('<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>'
            % (W, HH, ''.join(o)))


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
.cen th:nth-child(-n+3){text-align:left}
.cen td{padding:9px 10px 9px 0;border-bottom:1px solid var(--line);
 text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.cen td:nth-child(2),.cen td:nth-child(3){text-align:left;font-family:var(--sans)}
.cen td:nth-child(1){text-align:left;color:var(--ink)}
.cen td:nth-child(2){color:var(--ink);font-weight:500}
.cen tr.sh td{color:var(--brk)}
.dir{font-size:11px;padding:1px 7px;border:1px solid var(--line2);
 border-radius:2px;color:var(--ink3)}
.dir.b{color:var(--dn);border-color:var(--dn)}
.dir.u{color:var(--up);border-color:var(--up)}
.pat{border:1px solid var(--line);background:var(--card);margin:0 0 -1px;
 padding:17px 19px 19px}
.pat .ph{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:0 0 4px}
.pat .ph .id{font-family:var(--mono);color:var(--ph);font-size:13px}
.pat .ph h3{margin:0;font-size:17px;font-family:var(--serif)}
.pat .ph .en{font-size:11.5px;color:var(--ink3);font-style:italic}
.pat .st{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);
 font-size:11.5px;font-variant-numeric:tabular-nums;color:var(--ink3);
 margin:0 0 13px}
.pat .st b{color:var(--ink)}
.seq{font-family:var(--mono);font-size:12px;letter-spacing:.22em;
 color:var(--ph);background:var(--zone);padding:5px 9px;display:inline-block;
 margin:0 0 10px}
.pat ol{margin:0 0 12px;padding:0 0 0 20px}
.pat ol li{font-size:13px;color:var(--ink2);margin:0 0 5px;line-height:1.6;
 font-family:var(--mono);font-variant-numeric:tabular-nums}
.pat ol li i{font-style:normal;color:var(--ink3);font-family:var(--sans);
 font-size:12px}
.pat ol li b{color:var(--ink)}
.pat .fp{font-size:12px;color:var(--ink3);margin:0 0 13px}
.pat .fp b{color:var(--ph)}
.pat .nt{font-size:12.5px;color:var(--ink3);line-height:1.68;margin:13px 0 0;
 border-left:2px solid var(--line2);padding-left:12px}
.pat .nt b{color:var(--ink)}
.pat .nt u{text-decoration:underline;text-underline-offset:2px}
.figs{display:grid;grid-template-columns:184px 1fr;gap:16px;align-items:start}
.figs figure{margin:0}
.figs figcaption{font-size:11px;color:var(--ink3);margin:5px 0 0;
 font-family:var(--mono)}
.figs figcaption b{color:var(--ink)}
.figs .plot{fill:none;stroke:var(--ink2);stroke-width:1.6;
 stroke-linejoin:round;stroke-linecap:round}
.figs .ax{stroke:var(--line2);stroke-width:1}
.figs svg{width:100%;display:block}
.figs figure:first-child svg{height:104px}
@media (max-width:720px){.figs{grid-template-columns:1fr}}
.grid15{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 grid-template-columns:repeat(auto-fit,minmax(268px,1fr));margin:6px 0 0}
.c15{background:var(--bg);padding:15px 16px 17px}
.c15 h4{margin:0 0 3px;font-size:14px;font-family:var(--serif)}
.c15 h4 .id{font-family:var(--mono);color:var(--ph);margin-right:7px;font-size:12px}
.c15 .en{font-size:11px;color:var(--ink3);font-style:italic;margin:0 0 9px}
.c15 svg{width:100%;height:104px;display:block;margin:2px 0 9px}
.c15 .plot{fill:none;stroke:var(--ink3);stroke-width:1.6;
 stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:3 3}
.c15 .pv{fill:var(--ink3)}
.c15 .ax{stroke:var(--line2);stroke-width:1}
.c15 p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.62}
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
       '<span><b>0.89–1.11x</b>鏡像倍率全距</span>'
       '<span><b>0</b>具方向性</span>'
       '</div></header>')

HEADLINE = (
 '<section class="panel"><div class="ph2"><h2>一、一句話結論</h2>'
 '<span class="tag">13 個全部落在同一格</span></div>'
 '<div class="warn"><b>十三個型態的鏡像倍率全部落在 0.89x 到 1.11x 之間。</b>'
 '沒有任何一個偏好某個方向。</div>'
 '<p class="cap">對照樞紐型 A 組：P18 三重頂 <b>10.19x</b>、'
 'P68 雙頂 <b>6.75x</b>、P57 測量移動 <b>2.33x</b>。'
 '這裡最高的是 P64 倒置杯柄的 <b>1.11x</b> —— 差了一個數量級。</p>'
 '<div class="big"><p>這正是<b>三類條件</b>裡的第二類：<b>峰谷形狀</b>。'
 '把價格上下顛倒之後，同一個判定<b>通過的次數幾乎一模一樣</b>，'
 '所以形狀本身不含方向資訊。這也正是 P15 頭肩頂與 P16 頭肩底'
 '被排除的同一個理由。</p>'
 '<small><b>要講清楚這個測試沒有證明什麼。</b>'
 '鏡像倍率測的是<b>方向偏好</b>，不是<b>是否含資訊</b>。'
 '一個型態可以完全對稱、卻仍然比隨機常見或罕見 —— '
 'P29 擴散三角的獨立性比是 0.16x，遠低於隨機，但它照樣是有用的結構。'
 '<b>獨立性比與區塊局部置換對照組都還沒跑</b>，'
 '要留下其中任何一個，那才是下一步。</small></div></section>')


def census_table():
    tr = []
    for r in MEAS:
        short = r['span'] <= 10
        tr.append(
            '<tr%s><td>%s</td><td>%s</td>'
            '<td><span class="dir %s">%s</span></td>'
            '<td>%s</td><td>%s</td><td class="%s">%.2fx</td>'
            '<td class="%s">%d 根</td></tr>'
            % (' class="sh"' if short else '', r['id'], r['zh'],
               'b' if r['dir'] == '空' else 'u' if r['dir'] == '多' else '',
               r['dir'], format(r['n'], ','), format(r['mirror'], ','),
               'z' if 0.85 <= r['ratio'] <= 1.15 else '', r['ratio'],
               'z' if short else '', r['span']))
    return ''.join(tr)


P2 = ('<section class="panel"><div class="ph2">'
      '<h2>二、母體普查</h2><span class="tag">只有次數，沒有損益</span></div>'
      '<table class="cen"><thead><tr><th>代號</th><th>名稱</th><th>方向</th>'
      '<th>母體</th><th>鏡像</th><th>倍率</th><th>跨度中位</th>'
      '</tr></thead><tbody>' + census_table() + '</tbody></table>'
      '<p class="cap"><b>倍率</b> ＝ 母體 ÷ 鏡像母體。1.00x 代表把價格上下顛倒後'
      '出現次數一樣，也就是形狀不含方向。'
      '<b>橘色那三列的跨度中位 ≤ 10 根</b> —— 視窗 1 每 2.8 根就認一個樞紐，'
      '10 根只夠三四個樞紐，那是 K 棒尺度不是圖形尺度。</p></section>')


def pat_block(r):
    cid = r['id']
    seq, lines, note = LOGIC[cid]
    d = EX[cid]
    return (
        '<div class="pat">'
        '<div class="ph"><span class="id">%s</span><h3>%s</h3>'
        '<span class="en">%s</span><span class="dir %s">%s</span></div>'
        '<div class="st"><span>母體 <b>%s</b></span><span>鏡像 %s</span>'
        '<span>倍率 <b>%.2fx</b></span>'
        '<span>跨度中位 <b>%d</b> 根</span></div>'
        '<div class="seq">%s</div><ol>%s</ol>'
        '<p class="fp">自由參數 <b>0</b> —— '
        '上面每一個數字都來自型態自己的樞紐，沒有一個是我挑的。</p>'
        '<div class="figs">'
        '<figure>%s<figcaption>示意</figcaption></figure>'
        '<figure>%s<figcaption>真實案例　%s　%04d–%04d　振幅 %.0f 點　'
        '跨 %d 根　候選 %s 個中取<b>中位振幅</b></figcaption></figure>'
        '</div><p class="nt">%s</p></div>'
        % (cid, r['zh'], r['en'],
           'b' if r['dir'] == '空' else 'u' if r['dir'] == '多' else '',
           r['dir'], format(r['n'], ','), format(r['mirror'], ','),
           r['ratio'], r['span'], seq,
           ''.join('<li>%s</li>' % x for x in lines),
           sch(cid), real(cid), d['d0'], d['t0'], d['t1'],
           d['amp'], d['span'], format(d['n'], ','), note))


P3 = ('<section class="panel"><div class="ph2">'
      '<h2>三、十三個定義，逐條列出</h2>'
      '<span class="tag">左邊是我想的，右邊是市場真的長的樣子</span></div>'
      '<p class="cap">每一個都附一個<b>真實案例</b>：圈起來的是型態自己的樞紐，'
      '底色區間是型態的範圍。'
      '<b>案例取中位振幅、且不跨時段</b> —— 取最大振幅曾經挑出橫跨換盤的 '
      '1,819 點離群值，那不是型態平常的樣子。</p>'
      + ''.join(pat_block(r) for r in MEAS) + '</section>')

P4 = ('<section class="panel"><div class="ph2">'
      '<h2>四、兩個定不出零參數版本的</h2>'
      '<span class="tag">不硬編一個定義來湊數</span></div>'
      '<div class="grid15">'
      + ''.join('<div class="c15"><h4><span class="id">%s</span>%s</h4>'
                '<p class="en">%s</p>%s<p>%s</p></div>'
                % (r['id'], r['zh'], r['en'], sch(r['id']), r['note'])
                for r in SKIP)
      + '</div>'
      '<p class="cap">硬湊一個定義出來，量到的數字只會反映我挑的門檻，'
      '不會反映市場 —— <b>P07 布林帶寬就是這樣：週期從 20 改成 30，'
      '只剩 18.4% 是同一批 K 棒</b>。所以這兩個留白等裁示。</p></section>')

P5 = ('<section class="panel"><div class="ph2">'
      '<h2>五、定義用到的兩個裝置</h2><span class="tag">都不花參數</span></div>'
      '<div class="two">'
      '<div class="vf"><h3>步幅單調</h3>'
      '<p>「圓」和「V」的差別是<b>曲率</b>，曲率一般需要門檻。這裡不需要：'
      '<b>比較相鄰兩步的大小</b>就好。穹頂進場時步幅遞減、離場時遞增；'
      '尖峰完全相反。純序數，沒有任何東西可以調。</p>'
      '<p class="cap">所以 P26／P32 用同樣五個高點、P27／P63 用同樣五個低點，'
      '只差步幅方向 —— <b>兩兩互斥，不會重複計數</b>。</p></div>'
      '<div class="vf"><h3>區間裝置</h3>'
      '<p>兩點定義區間、第三點受測：<code>min(A,B) ≤ C ≤ max(A,B)</code>。'
      '<b>容差由型態自身推導</b>，順序因果正確，而且免疫於衰減律。</p>'
      '<p class="cap">杯柄的柄低點落在<b>左右兩個杯緣之間</b>；'
      '平底鍋底的中間低點落在<b>左右兩個低點之間</b>；'
      '旗形的旗面必須留在<b>旗桿的區間內</b>。'
      '全都不需要「回撤不超過幾成」這種數字。</p></div></div>'
      '<div class="big"><p><b>寫這 13 條邏輯的過程本身抓出兩個錯。</b></p>'
      '<small><b>P28 杯柄</b>：「左杯緣」被我取成杯子<u>裡面</u>的第一個高點 —— '
      '那個點在碗內不在緣上，區間整個偏低，母體 164 修正為 <b>134</b>。'
      '<br><b>P65 塔形頂</b>：「跌幅 ≥ 漲幅」<u>完全冗餘</u>，'
      '可由「完全回吐」推得，加不加都是 8,386，已移除。'
      '<br>兩個都是<b>把定義寫成句子給人看的時候</b>才發現的 —— '
      '這正是「先畫出來才知道哪裡有問題」。</small></div>'
      '<div class="ph2" style="margin-top:22px"><h2>定義健壯度</h2>'
      '<span class="tag">自己找碴，找到的都寫出來</span></div>'
      '<p class="cap">寫完邏輯後我對自己的定義有兩個疑慮，兩個都量了，'
      '<b>兩個都比我擔心的輕，而且其中一個我猜錯了</b>。'
      '只報「確認有問題」的自查不是自查。</p>'
      '<table><thead><tr><th>疑慮</th>'
      '<th style="text-align:left">結果</th></tr></thead><tbody>'
      '<tr><td>P66 的區間條件是空的？</td><td style="text-align:left">'
      '<b>不是。</b>PL3 在時間上夾在 PL2 與 PL4 中間，我以為三個數的中間那個'
      '本來就常落在外兩個之間 —— 實測<b>排掉 50%</b>'
      '（12,676 → 6,303）。<b>我猜錯了。</b></td></tr>'
      '<tr><td>步幅裝置會不會被一個 tick 決定？</td>'
      '<td style="text-align:left"><b>部分會。</b>'
      '判定邊際中位是 <b>7–9 點</b>，但 <b>17–22% 的案例邊際 ≤ 2 點</b>'
      '（P26 22%、P32 20%、P27 21%、P63 17%）。'
      '<br>這是<b>衰減律打到步幅裝置</b>：區間裝置的容差會隨市場長大，'
      '步幅裝置的嚴格不等式不會。'
      '<b>要留下這四個的話，這一項必須先處理。</b></td></tr>'
      '</tbody></table></section>')

P6 = ('<section class="panel"><div class="ph2">'
      '<h2>六、待裁示</h2><span class="tag">三題</span></div>'
      '<table><thead><tr><th>題目</th><th style="text-align:left">說明</th>'
      '</tr></thead><tbody>'
      '<tr><td>13 個怎麼處理</td><td style="text-align:left">'
      '全部鏡像倍率 0.89–1.11x，<b>與 P15／P16 同一個理由</b>。'
      '建議<b>整組結案</b>。若要留任何一個，'
      '下一步是跑獨立性比與區塊局部置換對照組</td></tr>'
      '<tr><td>P55 駝峰反轉</td><td style="text-align:left">'
      '三條趨勢線 ＋ 角度門檻，與 P58／P71 同類。'
      '你 08-30 的範疇裁示<b>看起來直接涵蓋它</b>，但我不替你決定</td></tr>'
      '<tr><td>P60 高位緊密旗形</td><td style="text-align:left">'
      '「翻倍」是外來常數。它是 P24 加一個幅度門檻，'
      '<b>P24 的 1,758 就是它的上限</b>，而 P24 本身 0.89x</td></tr>'
      '</tbody></table>'
      '<p class="cap">如果三題都照建議走，<b>型態層 72 種全部處理完畢</b>，'
      '接下來就是訊號層。</p></section>')

FOOT = ('<footer class="foot">'
        '普查 <code>s16s_census15_scan.py</code>、'
        '案例 <code>s16s_census15_pick.py</code>、'
        '本頁 <code>s16s_census15_make_page.py</code>。'
        '母體 421,513 根 5 分 K，視窗 1 樞紐 106,283 個。'
        '<b>本頁無損益欄。</b></footer></div>')

DOC = HEAD + TOP + HEADLINE + P2 + P3 + P4 + P5 + P6 + FOOT

# A script that assembles structure has to check the structure it assembled.
# P2 once shipped without its closing </section>, every later panel nested
# inside it, and the document collapsed to 599px.  The lookahead matters: a
# bare '<p' also matches '<polyline', and a check that cries wolf gets
# switched off.
for tag in ('section', 'div', 'p', 'ol', 'li', 'table', 'tbody', 'thead',
            'tr', 'td', 'th', 'svg', 'figure', 'figcaption'):
    op = len(re.findall(r'<%s(?=[\s>/])' % tag, DOC))
    cl = len(re.findall(r'</%s\s*>' % tag, DOC))
    assert op == cl, '%s: %d open, %d close' % (tag, op, cl)
print('  標籤平衡  OK')

assert len(MEAS) == 13 and len(SKIP) == 2
assert all(r['id'] in LOGIC for r in MEAS), '每個已量型態都要有逐條邏輯'
assert all(r['id'] in EX for r in MEAS), '每個已量型態都要有真實案例'
assert all(r['id'] in SCH for r in ROWS), '每個型態都要有示意圖'

open(OUT, 'w', encoding='utf-8').write(DOC)
print('wrote %s' % OUT)
print('  13 個逐條邏輯 ＋ 13 個真實案例 ＋ 2 個留白   %.0f KB'
      % (len(DOC.encode('utf-8')) / 1024))
