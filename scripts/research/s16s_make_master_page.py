# -*- coding: utf-8 -*-
"""Assemble the eleven pattern-research pages into one, grouped by family.

Willy: "把他們製作成分業形式的總圖形型態研究."

The pages cannot simply be concatenated.  They share class names but not
rules -- 53 selectors mean different things on different pages, and only ONE
rule is common to all eleven -- so a naive merge silently restyles half the
document.  Each page's CSS is therefore scoped to its own panel id, which is
also why every panel keeps looking exactly as it does today.

Only @media appears among the at-rules, and no page has keyframes or
@font-face, so scoping is a selector rewrite and nothing more.

Run:  python scripts/research/s16s_make_master_page.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = os.path.join('docs', 'research')
OUT = os.path.join(SRC, 'S16S_pattern_master.html')

# (file, tab label, one-line summary), grouped by what the group is FOR
GROUPS = [
    ('複習', [
        ('S16S_day0831_review', '8/31 一日複習',
         '25 個 commit、兩支指標驗收、六條教訓。型態層的落地標準在那天被改寫'),
    ]),
    ('落地', [
        ('S16S_landing_map', '落地地圖',
         '72 種裡 28 種畫得到、0 種未審查。用「畫得到嗎」而不是「檢定過嗎」盤點'),
    ]),
    ('2x2 家族', [
        ('S16S_grid5_diagram', '五個新格子',
         'P08 P10 P11 P20 P22 -- 真實 K 棒案例，與擴散家族同一張格子表'),
    ]),
    ('七種接線', [
        ('S16S_seven_diagram', '七種規格對照圖',
         'P15 P26 P32 P56 P59 P65 P72 逐條規格標到圖上，Build 260890 已編碼'),
    ]),
    ('方向量測', [
        ('S16S_verdict_diagram', '破位方向量測',
         '2026-08-31：破位方向不含型態資訊。這是訊號層的輸入，不是型態層的成績單'),
    ]),
    ('現況', [
        ('S16S_pattern_layer_status', '型態層總覽',
         '72 種純圖形走到哪裡，哪些結案、哪些還沒碰'),
    ]),
    ('圖鑑', [
        ('S16S_pattern_atlas_full', '全圖鑑 143 種',
         'K 棒與圖形型態的完整清單，每種一句話'),
        ('S16S_kbar_atlas_33', 'K 棒圖鑑 33 種',
         '已編碼並檢定過的 33 種 K 棒型態'),
        ('S16S_kbar_patterns', 'K 棒規格',
         '33 種的逐條定義'),
    ]),
    ('擴散家族', [
        ('S16S_P29_diagram', 'P29 擴散三角',
         '高更高、低更低。整套方法論的原型'),
        ('S16S_P49_P50_diagram', 'P49 ／ P50',
         '同一個形狀，用形成前的走勢分頂與底'),
        ('S16S_P51_P54_diagram', 'P51-P54 擴散楔形',
         '四個變體共用一個框架；破位方向不含型態資訊'),
    ]),
    ('缺口與鑽石', [
        ('S16S_gap_group_diagram', '缺口組 P31 P62 P67',
         '5 分 K 不存在跳空 —— 一次關掉 26 個型態'),
        ('S16S_diamond_diagram', '鑽石 P30 P61',
         '完整鑽石八年只出現一次。編碼上圖，不再研究'),
    ]),
    ('最後兩組', [
        ('S16S_eleven_diagram', '十一種完整流程',
         '型態層最後一組。12 進 11 出，P39 化約成頭頭降原語'),
        ('S16S_census15_diagram', '母體普查',
         '型態層最後 15 種。13 個化約成既有原語，杯柄因為「有價位」留下'),
    ]),
    ('樞紐型', [
        ('S16S_groupA_diagram', 'A 組七型態',
         'P15 P16 P18 P21 P23 P57 P17。區間裝置、衰減律、三類條件'),
        ('S16S_pivot_scale', '樞紐尺度',
         '視窗 1 每 2.8 根就認一個樞紐 —— 那些「雙頂」跨度只有 3 根'),
    ]),
]

KPI = [('72', '種純圖形型態'), ('28', '種已落地'), ('15', '種等接線'),
       ('0', '種待審查')]

# What closing a pattern means, and the reason named for each of the 52.
# Willy asked, and the question was fair: the old tab label put a STATUS among
# four FAMILY names, which made 已結案 look like a verdict rather than a state.
CLOSED = [
    ('前提不成立', '缺口組 P31 P62 P67', '3',
     '5 分 K 不存在跳空。時段內缺口 1,923 個，<b>90.4% 剛好 1 點</b>，'
     '零個達到 10 點來回成本，五根內 100% 回補。'
     '<b>同時關掉圖鑑中因跳空排除的 23 個 K 棒型態</b>'),
    ('母體不足', '鑽石 P30 P61', '2',
     '完整鑽石需 10 個樞紐，八年<b>只出現 1 個</b>。'
     '依裁示 I1 <b>仍編碼上圖</b> —— 不再研究，但未來出現時看得到'),
    ('上層答案已覆蓋', '擴散家族 7 種', '7',
     '<b>破位方向 ＝ 起算位置 ＋ 低點方向延續，不含型態資訊</b>。'
     '這題答完之後，後續型態都不必再測「它往哪邊破」'),
    ('逐一裁示', '樞紐型 7 種', '7',
     '<b>3 個空方通過並編碼</b>（P18 P57 P17）；2 個無方向'
     '（P15 P16，峰谷形狀類，鏡像同樣通過）；'
     '2 個是多方（P23 P21），純空策略排除'),
    ('已檢定', 'K 棒型態 33 種', '33',
     '全部編碼、全部實測，<b>33 次檢定全負</b>（Bonferroni 門檻 3.17）'),
    ('化約為既有原語', '曲率四個 ＋ 趨勢八個', '12',
     '<b>用戶 2026-08-30 三點裁示，全部量過。</b>'
     '曲率標籤是<b>擲銅板</b>（17.4／28.2／54.4 對上兩個獨立銅板的 25／25／50）；'
     '趨勢型態只是<b>頭頭比較 × 底底比較</b>那個 2×2 的格子'
     '（P24 只是降降格的 19.0%）；<b>P60 逐字等於 P24</b>'),
    ('完整流程走完、待編碼', '最後一組十一種', '11',
     '2026-08-31 晚。<b>P33 P35 P37 P13 P14 P41 P42 P43 P45 P47 P48</b>。'
     '四個裝置把三個門檻換掉：<b>排名</b>（Crabel N=4/7）、'
     '<b>上影 &gt; 實體</b>、<b>差距 &lt; 影線</b>、<b>跑到分出勝負</b>'
     '（旗形因此沒有根數）。鏡像 0.78–1.02x，<b>沒有一個偏空</b>；'
     '三個過門檻但方向全反 —— 那是台指偏多漂移，'
     '<b>不能當成它們有效的證據</b>'),
    ('保留並編碼', 'P28 杯柄／P64 倒置杯柄／P55 駝峰', '3',
     '<b>杯柄的兩個緣是一個價位區間</b> —— 用戶指出的，'
     '也是型態層唯一交出「可交易價位」的東西。'
     '八年 7＋4 次，依裁示 A1 <b>編碼上圖</b>（Build 260880）。'
     'P55 帶進<b>斜率比較</b>這個新原語，628 個'),
    ('不在範疇', 'D 組 P07 P58 P69 P70 P71', '5',
     '<b>用戶裁示 2026-08-30：這並非圖形型態探討的範疇。</b>'
     '指標型態（P07）、趨勢線疊圖（P58 P71）、分析框架（P69 P70）'
     '都不是價格形狀本身。<b>這是唯一一列不是靠實測結案的</b> —— '
     'P69 化約後其實零參數、母體 4,564、跨尺度 74–78% 穩定，'
     '它出局純粹因為範疇，不是因為數字'),
]

FINDINGS = [
    ('★ 區間裝置',
     '兩點定義區間、第三點受測：<code>min(A,B) ≤ C ≤ max(A,B)</code>。'
     '容差 ＝ |A−B|，<b>由型態自身推導，不花參數</b>；順序因果正確；'
     '<b>免疫於衰減律</b>。P18 用它從 43 個樣本變成 6,352 個，倍率不變。'),
    ('★ 衰減律',
     '命中率 × 中位擺幅 ≈ 常數（八年間 608–850）。TXF1 的 tick 固定 1 點，'
     '中位擺幅從 9 點（2019）漲到 90 點（2026），'
     '<b>所以「完全相等」型態以 1／擺幅 衰減</b> —— 不是型態失效，是尺規沒跟著長。'),
    ('★ 三類條件',
     '<b>單調方向</b>（有資訊且有方向）／<b>峰谷形狀</b>（鏡像同樣通過 → 無方向）'
     '／<b>精確相等</b>（有資訊但鏡像必通過 → 無方向）。'
     '落在後兩類的型態<b>不必再測方向</b>。'),
    ('★ 尺度',
     '視窗 1 下 35.9% 的 K 棒都是樞紐，所以「雙頂」跨度中位只有 3 根 —— <b>那不是雙頂</b>。'
     '視窗 3 跨 30 根 ≈ 半個日盤才像型態。'
     '<b>視窗變粗 ≠ 換週期</b>：K 棒仍是 5 分 K，進出場停損全部不變。'),
    ('破位方向',
     '擴散家族證明：<b>破位方向 ＝ 起算位置 ＋ 低點方向延續，不含型態資訊</b>。'
     '所以後續型態都不必再測「它往哪邊破」，只要問形狀能不能零參數定死、母體夠不夠。'),
    ('對照組',
     'P17 的對照組做了三次才對 —— 前兩次分別給出 391x 與 80x，都是 artifact。'
     '兩個高點中位相隔 3 根，<b>它們價格接近是因為時間接近</b>。'
     '只有<b>區塊局部置換</b>（僅在鄰近 200 個框架內洗牌）站得住。'),
]


def scope_css(css, sel):
    """Confine a page's CSS to one panel, so eleven stylesheets coexist."""
    def one(s):
        s = s.strip()
        if not s:
            return s
        if s == '*':
            return '%s, %s *' % (sel, sel)
        if s in ('body', 'html', ':root'):
            return sel
        m = re.match(r'^:root(\[[^\]]+\])(.*)$', s)
        if m:
            return '%s %s%s' % (m.group(1), sel, m.group(2))
        m = re.match(r'^:root(:not\([^)]*\))(.*)$', s)
        if m:
            return ':root%s %s%s' % (m.group(1), sel, m.group(2))
        if s.startswith('body') or s.startswith('html'):
            return sel + s[4:]
        return '%s %s' % (sel, s)

    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            out.append(css[i:])
            break
        head = css[i:j]
        if '@media' in head or '@supports' in head:
            depth, k = 0, j
            while k < n:
                if css[k] == '{':
                    depth += 1
                elif css[k] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            out.append(head + '{' + scope_css(css[j + 1:k], sel) + '}')
            i = k + 1
            continue
        k = css.find('}', j)
        sels = ', '.join(one(x) for x in head.split(','))
        out.append(sels + '{' + css[j + 1:k] + '}')
        i = k + 1
    return ''.join(out)


def split_page(path):
    s = open(path, encoding='utf-8').read()
    css = re.findall(r'<style>(.*?)</style>', s, re.S)[0]
    body = s.split('</style>', 1)[1]
    return css, body


HEAD = '''<title>圖形型態研究全集</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=IBM+Plex+Mono:wght@400;600&amp;display=swap" rel="stylesheet">
<style>
:root{--mxbg:#fbfaf7;--mxsurf:#fff;--mxink:#1a1a17;--mxdim:#6a6a62;
 --mxline:#e0ddd4;--mxacc:#0f9d76;--mxrail:#f2efe8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --mxbg:#14140f;--mxsurf:#1c1c17;--mxink:#eceae2;--mxdim:#9a978c;
 --mxline:#33322a;--mxacc:#3fbf9a;--mxrail:#1f1f19}}
:root[data-theme="dark"]{--mxbg:#14140f;--mxsurf:#1c1c17;--mxink:#eceae2;
 --mxdim:#9a978c;--mxline:#33322a;--mxacc:#3fbf9a;--mxrail:#1f1f19}
:root[data-theme="light"]{--mxbg:#fbfaf7;--mxsurf:#fff;--mxink:#1a1a17;
 --mxdim:#6a6a62;--mxline:#e0ddd4;--mxacc:#0f9d76;--mxrail:#f2efe8}
body{margin:0;background:var(--mxbg);color:var(--mxink);
 font-family:"Noto Sans TC",system-ui,sans-serif;line-height:1.62}
.mxwrap{max-width:1180px;margin:0 auto;padding:0 20px 10px}
.mxhero{padding:56px 0 26px;border-bottom:2px solid var(--mxink)}
.mxeyebrow{font-family:"IBM Plex Mono",monospace;font-size:12px;
 letter-spacing:.18em;text-transform:uppercase;color:var(--mxacc);margin:0 0 12px}
.mxhero h1{font-family:"Noto Serif TC",serif;font-size:clamp(30px,4.6vw,50px);
 line-height:1.12;margin:0 0 14px;text-wrap:balance;letter-spacing:-.01em}
.mxhero p{margin:0;max-width:62ch;color:var(--mxdim);font-size:16px}
.mxkpi{display:flex;flex-wrap:wrap;gap:34px;margin:26px 0 0}
.mxkpi div{display:flex;flex-direction:column}
.mxkpi b{font-family:"IBM Plex Mono",monospace;font-size:29px;
 font-variant-numeric:tabular-nums;line-height:1;color:var(--mxacc)}
.mxkpi span{font-size:12px;color:var(--mxdim);margin-top:5px}
.mxfind{display:grid;gap:1px;background:var(--mxline);border:1px solid var(--mxline);
 grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin:30px 0 0}
.mxfind section{background:var(--mxsurf);padding:17px 19px}
.mxfind h3{margin:0 0 7px;font-size:14px;font-family:"Noto Serif TC",serif}
.mxfind p{margin:0;font-size:13.5px;color:var(--mxdim);line-height:1.65}
.mxfind b{color:var(--mxink)}
.mxfind code{font-family:"IBM Plex Mono",monospace;font-size:12.5px;
 background:var(--mxrail);padding:1px 5px;color:var(--mxink)}
.mxclosed{margin:34px 0 0;border:1px solid var(--mxline);
 background:var(--mxsurf);padding:22px 24px 24px}
.mxclosed h2{font-family:"Noto Serif TC",serif;font-size:20px;margin:0 0 10px}
.mxlede{margin:0 0 18px;font-size:14px;color:var(--mxdim);max-width:74ch;
 line-height:1.7}
.mxlede b{color:var(--mxink)}
.mxclosed table{width:100%;border-collapse:collapse;font-size:13.5px}
.mxclosed th{text-align:left;font-size:11px;letter-spacing:.1em;
 color:var(--mxdim);font-weight:500;border-bottom:1px solid var(--mxink);
 padding:0 12px 7px 0}
.mxclosed td{padding:11px 12px 11px 0;border-bottom:1px solid var(--mxline);
 vertical-align:top;color:var(--mxdim);line-height:1.65}
.mxclosed td b{color:var(--mxink)}
.mxwhy{color:var(--mxink);font-weight:600;white-space:nowrap}
.mxwhat{color:var(--mxink);white-space:nowrap}
.mxn{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;
 text-align:right;color:var(--mxacc);font-weight:600;padding-right:18px}
tr.mxsum td{border-bottom:none;color:var(--mxink);font-weight:600}
.mxnote{margin:16px 0 0;font-size:13px;color:var(--mxdim);line-height:1.7}
.mxnote b{color:var(--mxink)}
.mxnav{position:sticky;top:0;z-index:9;background:var(--mxbg);
 border-bottom:1px solid var(--mxline);margin:30px 0 0}
.mxnavin{max-width:1180px;margin:0 auto;padding:0 20px;display:flex;
 gap:26px;overflow-x:auto}
.mxgrp{padding:11px 0 10px;flex:0 0 auto}
.mxgrp>span{display:block;font-family:"IBM Plex Mono",monospace;font-size:10px;
 letter-spacing:.16em;color:var(--mxdim);margin:0 0 6px}
.mxgrp>div{display:flex;gap:6px}
.mxtab{font:inherit;font-size:13px;padding:5px 11px;cursor:pointer;
 background:transparent;color:var(--mxdim);border:1px solid transparent;
 white-space:nowrap;border-radius:2px}
.mxtab:hover{color:var(--mxink);background:var(--mxrail)}
.mxtab[aria-selected="true"]{background:var(--mxink);color:var(--mxbg);
 border-color:var(--mxink);font-weight:600}
.mxtab:focus-visible{outline:2px solid var(--mxacc);outline-offset:2px}
.mxcap{max-width:1180px;margin:0 auto;padding:22px 20px 0}
.mxcap p{margin:0;color:var(--mxdim);font-size:13.5px}
.mxcap b{color:var(--mxink)}
.mxcap code{font-family:"IBM Plex Mono",monospace;font-size:12px}
.mxpanel[hidden]{display:none}
.mxfoot{max-width:1180px;margin:0 auto;padding:34px 20px 60px;
 border-top:1px solid var(--mxline);color:var(--mxdim);font-size:12.5px}
.mxfoot code{font-family:"IBM Plex Mono",monospace}
@media (max-width:640px){.mxnavin{gap:16px}.mxkpi{gap:22px}}
</style>
'''

SCRIPT = '''<script>
(function(){
 var tabs=[].slice.call(document.querySelectorAll('.mxtab'));
 function fill(n){
  var host=document.getElementById('pg'+n),tpl=document.getElementById('tpl'+n);
  if(host&&tpl&&!host.firstChild){host.appendChild(tpl.content.cloneNode(true));}
 }
 function show(n){
  fill(n);
  tabs.forEach(function(t){
   var on=t.dataset.p===n;
   t.setAttribute('aria-selected',on?'true':'false');
   document.getElementById('pane'+t.dataset.p).hidden=!on;
  });
  try{localStorage.setItem('s16s_master_tab',n);}catch(e){}
 }
 tabs.forEach(function(t){
  t.addEventListener('click',function(){
   show(t.dataset.p);
   var nav=document.querySelector('.mxnav');
   window.scrollTo({top:nav.offsetTop-1});
  });
 });
 var saved=null;
 try{saved=localStorage.getItem('s16s_master_tab');}catch(e){}
 if(saved&&document.getElementById('pane'+saved))show(saved);
})();
</script>'''


def main():
    styles, panels, nav = [], [], []
    pid = 0
    for gname, items in GROUPS:
        btns = []
        for stem, label, note in items:
            pid += 1
            sel = '#pg%d' % pid
            css, body = split_page(os.path.join(SRC, stem + '.html'))
            styles.append('/* %s */\n%s' % (stem, scope_css(css, sel)))
            # The first panel is live so the page paints at once; the
            # rest sit in a <template>, which the browser parses but never
            # styles or lays out, and are cloned in on first click.
            cap = ('<div class="mxcap"><p><b>%s</b> — %s　'
                   '<code>docs/research/%s.html</code></p></div>'
                   % (label, note, stem))
            if pid == 1:
                inner = '<div id="pg%d">%s</div>' % (pid, body)
            else:
                inner = ('<div id="pg%d"></div>'
                         '<template id="tpl%d">%s</template>' % (pid, pid, body))
            panels.append('<div class="mxpanel" id="pane%d" role="tabpanel"%s>'
                          '%s%s</div>'
                          % (pid, '' if pid == 1 else ' hidden', cap, inner))
            btns.append('<button class="mxtab" role="tab" data-p="%d" '
                        'aria-selected="%s">%s</button>'
                        % (pid, 'true' if pid == 1 else 'false', label))
        nav.append('<div class="mxgrp"><span>%s</span>'
                   '<div role="tablist" aria-label="%s">%s</div></div>'
                   % (gname, gname, ''.join(btns)))

    kpi = ''.join('<div><b>%s</b><span>%s</span></div>' % k for k in KPI)
    closed = ''.join(
        '<tr><td class="mxwhy">%s</td><td class="mxwhat">%s</td>'
        '<td class="mxn">%s</td><td>%s</td></tr>' % c for c in CLOSED)
    find = ''.join('<section><h3>%s</h3><p>%s</p></section>' % f
                   for f in FINDINGS)

    html = (
        HEAD
        + ''.join('<style>%s</style>\n' % s for s in styles)
        + '<div class="mxwrap"><div class="mxhero">'
          '<p class="mxeyebrow">S16_S MACrossShort</p>'
          '<h1>圖形型態研究全集</h1>'
          '<p>十一份研究併成一份。每一頁維持原樣 —— 樣式各自限定在自己的面板裡，'
          '因為十一份頁面共用 class 名稱卻不共用規則，'
          '直接合併會把彼此改壞。</p>'
          '<div class="mxkpi">' + kpi + '</div></div>'
          '<div class="mxfind">' + find + '</div>'
          '<section class="mxclosed"><h2>「已結案」是什麼意思</h2>'
          '<p class="mxlede">結案 ＝ <b>這個型態不會再回頭研究，而且能指名理由</b>。'
          '它是<b>研究狀態</b>，不是<b>裁示結果</b> —— '
          'P18／P57／P17 也是已結案，但它們通過了對照組，而且已經進指標。'
          '反過來，未研究的 20 種不代表有希望，只代表還沒量。</p>'
          '<table><thead><tr><th>結案理由</th><th>對象</th><th>種</th>'
          '<th>依據</th></tr></thead><tbody>' + closed +
          '<tr class="mxsum"><td>合計</td><td></td><td class="mxn">72</td>'
          '<td>★ 全部走完流程</td></tr></tbody></table>'
          '<p class="mxnote">指標上畫的 <b>15 種</b>是 P29／P49／P50、'
          'P51-P54、P30／P61、P18／P57／P17、<b>P28／P64／P55</b> —— '
          '其中<b>只有 P18／P57／P17 是通過對照組的空方型態</b>，'
          '其餘是為了看得見而畫，不是訊號。</p></section></div>'
        + '<nav class="mxnav"><div class="mxnavin">' + ''.join(nav)
        + '</div></nav>'
        + ''.join(panels)
        + '<div class="mxfoot"><p>產生器 '
          '<code>scripts/research/s16s_make_master_page.py</code>　'
          '十一份來源頁面各自仍可單獨開啟，內容以來源為準。</p></div>'
        + SCRIPT)
    open(OUT, 'w', encoding='utf-8').write(html)
    print('wrote %s' % os.path.abspath(OUT))
    print('  %d 面板   %.0f KB' % (pid, len(html.encode('utf-8')) / 1024))


if __name__ == '__main__':
    main()
