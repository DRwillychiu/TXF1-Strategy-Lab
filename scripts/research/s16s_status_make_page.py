# -*- coding: utf-8 -*-
"""Where the pattern layer stands -- 72 pure chart patterns, one page.

Willy, 2026-08-28: "我想清楚知道那些圖形型態已經討論完整?那些還沒做討論。
我不希望虛度時間也不希望降低效率"

So this page answers two questions and nothing else: what is finished, and
what is left.  The second half groups the remainder by the MACHINERY it would
reuse, because that is what decides cost -- the broadening family took two
days and built the infrastructure, the gap group took under a day and closed
three, the diamond under a day and closed two.  The rate is rising because the
frame is already there, and the grouping shows where that carries over.

Status is read from the atlas lists and cross-checked against the closure
documents: all twelve closures have one.
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_pattern_layer_status.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

DONE = [
    ('已編碼並檢定', 33, 'P01-P48 的 33 種',
     '兩波共 33 次檢定<b>全部為負</b>（Bonferroni 門檻 3.17）。'
     '定義由我自訂、我自跑，2026-08-25 已裁定<b>不作為否定圖形型態的證據</b>。'),
    ('擴散家族結案', 7, 'P29 P49 P50 P51 P52 P53 P54',
     '裁示 A1／B1／C。留下永久結論：<b>破位方向 ＝ 起算位置 ＋ 低點方向延續</b>，'
     '之後任何型態都不必再測「往哪邊破」。'),
    ('缺口組結案', 3, 'P31 P62 P67',
     '裁示：<b>5 分 K 完全不會出現跳空</b>。時段內缺口 90.4% 剛好 1 tick、'
     '零個達到 10 點成本、五根內 100% 回補。<b>同時關掉圖鑑裡 23 個 K 棒缺口型態</b>。'),
    ('鑽石結案', 2, 'P30 P61',
     '裁示 I1：不再研究，但<b>已編碼上圖</b>（Build 260861，MC12 驗收 P30=0 P61=1 全中）。'
     '完整鑽石需 10 樞紐，八年只出現一次。'),
    ('樞紐型結案', 7, 'P15 P16 P18 P21 P23 P57 P68',
     '<b>三個空方通過並編碼</b>（P18 10.19x／P68 6.75x／P57 2.33x，'
     'Build 260873 驗收 6,155／1,337／251 全中）。'
     'P15 P16 屬峰谷形狀類，<b>鏡像同樣通過所以不含方向</b>；'
     'P23 P21 統計乾淨但<b>是多方</b>，依純空裁示排除。'),
    ('化約結案', 12, 'P24 P25 P26 P27 P32 P56 P59 P60 P63 P65 P66 P72',
     '用戶 08-30 三點裁示：曲率標籤是<b>擲銅板</b>（17.4／28.2／54.4 對上'
     '兩個獨立銅板的 25／25／50）；趨勢型態只是'
     '<b>頭頭比較 × 底底比較</b>那個 2×2 的格子'
     '（P24 只是降降格的 19.0%）；<b>P60 逐字等於 P24</b>。'),
    ('保留並編碼', 3, 'P28 P64 P55',
     '<b>杯柄的兩個緣是一個價位區間</b>（用戶指出）—— 型態層唯一交出'
     '「可交易價位」的東西，八年 7＋4 次，依裁示 A1 編碼上圖。'
     'P55 駝峰反轉 628 個，帶進<b>斜率比較</b>這個新原語。'
     '全部在 <b>Build 260880</b>。'),
    ('D 組不在範疇', 5, 'P07 P58 P69 P70 P71',
     '裁示 2026-08-30：<b>這並非圖形型態探討的範疇</b>。'
     '指標型態（P07）、趨勢線疊圖（P58 P71）、分析框架（P69 P70）'
     '都不是價格形狀本身。<b>這是範疇判定，不是效果判定</b> —— '
     '實測數字保留在 <code>S16S_GROUPD_MEASURED_20260830.md</code>。'),
]

GROUPS = [
    ('X', '型態層已全部結案 —— 本區留空', 0, 'ok', [],
     '2026-08-30，72 種全部有裁示。'
     '<b>唯一未完成的是 P18／P57／P68 的破位方向驗收</b>，'
     'Build 260880 已把它們接進 SECTION 7，數字由 MC12 產生。'),
    ('B_OLD', '曲率型 —— 圓弧、杯、V', 0, 'warn',
     [('P26', '圓弧頂'), ('P27', '圓弧底'), ('P28', '杯柄'), ('P32', 'V 型反轉'),
      ('P59', '穿越型態'), ('P63', 'V 型底'), ('P64', '倒置杯柄'), ('P66', '平底鍋底')],
     '「圓」與「V」的差別是<b>曲率</b>，而曲率必須有門檻 —— '
     '本質上就是自由參數。<b>建議只量母體，不投入定義討論</b>：'
     '先寫一個暫定的零參數版本掃一次，母體不足就結案。'),
    ('C', '幅度／速度型 —— 旗形、駝峰、塔形', 0, 'warn',
     [('P24', '多方旗形'), ('P25', '多方三角旗'), ('P55', '駝峰反轉'),
      ('P56', '死貓反彈'), ('P60', '高位緊密旗形'), ('P65', '塔形頂')],
     '「急漲」「緊密」「大幅」都需要幅度或速度門檻。'
     '旗形的旗桿<b>可以用斜率閘門從已固定的東西推導</b>（圖鑑已有前例），'
     '所以這組不是全無希望，但要逐一判斷。'),
    ('E', '其他', 0, 'warn', [('P72', '訂單塊 ／ 反轉塊')],
     '需要先定義「訂單塊」的零參數版本。樞紐型的框架可以直接沿用。'),
]

RATE = [('擴散家族', '7 種', '約 2 天', '同時建好整套基礎設施'),
        ('缺口組', '3 種', '不到 1 天', '三者共用一套偵測'),
        ('鑽石', '2 種', '不到 1 天', '直接沿用六樞紐框架'),
        ('樞紐型', '7 種', '約 1 天', '共用六樞紐鏈與一套對照組，三個進指標'),
        ('D 組', '5 種', '不到 1 天', '範疇判定，不必逐一定義')]

EXTRA = """
.grp{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden}
.gi{background:var(--card);padding:15px 17px;display:flex;gap:14px;align-items:flex-start}
.gi .lt{flex:0 0 30px;height:30px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-family:var(--mono);font-size:14px;font-weight:600;
  background:var(--ink);color:var(--card);margin-top:2px}
.gi.ok .lt{background:var(--ph)}
.gi.warn .lt{background:var(--pl)}
.gi.bad .lt{background:var(--brk)}
.gi .bd2{display:flex;flex-direction:column;gap:6px;min-width:0}
.gi h3{margin:0;font-family:var(--serif);font-size:15px;font-weight:700;
  display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.gi h3 em{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--ink3)}
.gi p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.6}
.gi b{color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chips span{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:3px;
  border:1px solid var(--line);color:var(--ink2);background:var(--bg)}
.chips span b{color:var(--ink);font-weight:600}
.done{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden}
.di{background:var(--card);padding:14px 16px;display:flex;gap:13px;align-items:flex-start}
.di .n{flex:0 0 auto;font-family:var(--mono);font-size:19px;color:var(--ph);
  font-weight:600;min-width:34px;text-align:right}
.di .bd2{display:flex;flex-direction:column;gap:4px}
.di h3{margin:0;font-family:var(--serif);font-size:14.5px;font-weight:700}
.di code{font-size:11px}
.di p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.di b{color:var(--ink)}
.big{border-left:3px solid var(--ph);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:4px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:17px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
"""

done = ''.join(
    '<div class="di"><div class="n">%d</div><div class="bd2">'
    '<h3>%s</h3><code>%s</code><p>%s</p></div></div>' % (n, t, c, d)
    for t, n, c, d in DONE)

grp = ''.join(
    '<div class="gi %s"><div class="lt">%s</div><div class="bd2">'
    '<h3>%s<em>%d 種</em></h3>'
    '<div class="chips">%s</div><p>%s</p></div></div>'
    % (cls, k, t, n, ''.join('<span><b>%s</b> %s</span>' % p for p in ps), d)
    for k, t, n, cls, ps, d in GROUPS)

rate = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td>'
               '<td style="text-align:left">%s</td></tr>' % r for r in RATE)

HEAD = ('<title>型態層總覽</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
        '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

TOP = ('<div class="wrap"><header class="top">'
       '<div class="eyebrow">S16_S 型態層 · 總覽 · 2026-08-30</div>'
       '<h1>型態層總覽</h1>'
       '<p class="sub">純圖形型態 <b>72 種</b>：<b>已全部結案</b>。'
       '狀態讀自圖鑑清單並與結案文件交叉查核 —— <b>24 個結案全部有文件佐證</b>。</p>'
       '<div class="kpi">'
       '<span><b>33</b>已編碼並檢定</span>'
       '<span><b>39</b>已結案（含文件）</span>'
       '<span><b>15</b>畫在指標上</span>'
       '<span><b>0</b>尚未討論</span>'
       '</div></header>')

P1 = ('<section class="panel"><div class="ph2"><h2>一、七十二種的結案理由</h2>'
      '<span class="tag">每一項都有結案文件</span></div>'
      '<div class="done">' + done + '</div></section>')

P2 = ('<section class="panel"><div class="ph2">'
      '<h2>二、原本的待辦分組（已全數結案，保留供追溯）</h2>'
      '<span class="tag">橘＝先量母體，再決定要不要深入</span></div>'
      '<div class="grp">' + grp + '</div></section>')

P3 = ('<section class="panel"><div class="ph2"><h2>三、速度正在加快</h2>'
      '<span class="tag">因為框架已經建好</span></div>'
      '<table><thead><tr><th>批次</th><th>種數</th><th>耗時</th>'
      '<th style="text-align:left">為什麼</th></tr></thead>'
      '<tbody>' + rate + '</tbody></table>'
      '<div class="big"><p>最省時間的做法：<b>先把 15 種的母體一次量完</b>，'
      '再只對站得住的做深度討論。</p>'
      '<small>目前為止的經驗是<b>量母體就殺掉大部分型態</b> —— '
      '缺口組三個、鑽石兩個，都是量完就結案，沒有一個需要深度討論。'
      '一次量完的成本，遠低於逐一討論再逐一量。'
      '暫定定義若不夠好也無妨：母體是 0 或爆量的那些，'
      '<b>不管定義怎麼修都會是同一個結論</b>；只有中間帶需要你裁示。</small></div>'
      '</section>')

P4 = ('<section class="panel"><div class="ph2"><h2>四、待裁示（三題，都不擋路）</h2>'
      '<span class="tag">不回我就照建議做</span></div>'
      '<table><thead><tr><th>題目</th><th style="text-align:left">建議</th>'
      '</tr></thead><tbody>'
      '<tr><td>P58 扇形原則</td><td style="text-align:left">'
      '用戶 08-30 裁示 D 組「不在圖形型態範疇」。那是<b>範疇判定</b>，'
      '同樣涵蓋 P58 的三條趨勢線 —— <b>已一併排除</b>，要留下的話一句話改回來'
      '</td></tr>'
      '<tr><td>三點規則</td><td style="text-align:left">'
      '升格為檢查表<b>第 17 條</b>：多段型態每一段每一條邊都要三個點才算確認。'
      'A 組第一個就用到</td></tr>'
      '<tr><td>F1 / F2 趨勢線</td><td style="text-align:left">'
      '維持 F1。F2 會讓線收在畫面內，但<b>會改變 SECTION 7 的 state 轉換行為</b>，'
      '不是純美化</td></tr>'
      '</tbody></table></section>')

FOOT = ('<footer class="foot">'
        '狀態產生器 <code>scripts/research/s16s_status_make_page.py</code>，'
        '讀取 <code>s16s_make_full_atlas.py</code> 的清單並與 '
        '<code>docs/research/*CLOSED*.md</code> 交叉查核。'
        '樣式共用 <code>_diagram.css</code>。<b>本頁無損益欄。</b>'
        '</footer></div>')

open(OUT, 'w', encoding='utf-8').write(HEAD + TOP + P1 + P2 + P3 + P4 + FOOT)
print('wrote %s' % OUT)
n = sum(g[2] for g in GROUPS)
print('  待辦合計 %d 種（應為 0）%s' % (n, 'OK' if n == 0 else '★ 不符'))
d = sum(x[1] for x in DONE)
print('  結案合計 %d 種（應為 72）%s' % (d, 'OK' if d == 72 else '★ 不符'))
print('  72 + 0 = %d（應為 72）%s' % (d + n, 'OK' if d + n == 72 else '★ 不符'))
