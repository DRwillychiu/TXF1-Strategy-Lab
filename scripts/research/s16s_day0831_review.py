# -*- coding: utf-8 -*-
"""2026-08-31 一日複習頁.

Willy 2026-09-01：「完整幫我針對昨日進度用 HTML 複習」

那天做了 25 個 commit（筆電 19 ＋ 桌機 6），型態層從 21% 推到 39%，
並且改寫了「型態層算不算落地」的定義本身。

本頁的數字全部取自當天的 MC12 輸出與已 commit 的量測腳本，
不是重新推導的。錯誤那一段照實列，因為那天有六次是我自己犯的。

Run:  python scripts/research/s16s_day0831_review.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.join('docs', 'research', 'S16S_day0831_review.html')

# 進度條：72 種的四個狀態
STATE = [('已畫且 MC12 驗收', 28, 'done'),
         ('已編碼／已定義，待接線或驗收', 15, 'ready'),
         ('邏輯從未審查', 0, 'todo'),
         ('依裁示不繪製', 29, 'out')]

TIMELINE = [
    dict(t='早上', h='型態層判決 —— 然後這個框架被推翻',
         k='frame',
         b='Build 260881 驗收十一個量全中，P18／P57／P17 的破位方向量出來是擲銅板'
           '（P18 50.43%，z=+0.56）。我把它稱為「型態層的判決」並宣告正面產出是空的。'
           '<br><br><b>用戶當天中午的界定推翻了這個框架：</b>'
           '「今天型態出現了，接下來才是進入規劃訊號以及策略層面的事情……'
           '就能夠完整先在圖表上確認所有的圖形型態，這樣才是型態層的落地。」'
           '<br><br>驗收標準是<b>畫得到</b>，不是<b>檢定過</b>。'
           '把訊號層的考題提前套在型態層，讓一個只完成 21% 的階段看起來像結束了。'),
    dict(t='上午', h='鑽石翻轉 —— 護欄抓到一個真的索引 bug',
         k='fix',
         b='<code>DIA TALLY</code> 印 P30=1 P61=0，參考值是 0／1。'
           '鑽石用 M7 在<b>第一個樞紐</b>分頂底，但程式讀 <code>v_DM7a[0]</code> 寫死 0；'
           '杯柄的編碼把鏈從 10 槽加寬到 12 槽，視窗起點 <code>v_d0</code> 變成 2，'
           '所以它讀的是鑽石開始<b>前兩個</b>的樞紐。'
           '<br><br>8/30 的 handoff 預言過這個失敗模式並把 DIA 放進驗收表。'),
    dict(t='中午', h='七種接線 —— 標籤車道',
         k='ship',
         b='P15 頭肩頂／P26 圓弧頂／P32 V 型反轉／P56 死貓反彈／P59 穿越型態／'
           'P65 塔形頂／P72 訂單塊，定義原樣取自已審查來源。'
           '<br><br>37,228 個型態、300 根視窗中位 26 個標籤。'
           '每個型態一條固定車道、依「需要幾個樞紐」由大到小排，標籤成列不亂疊。'
           '<br><br><b>MC12 全中</b>：5216 / 60 / 97 / 9133 / 307 / 3977 / 18433。'),
    dict(t='下午', h='收斂六種 —— 副圖色帶',
         k='ship',
         b='P01 NR4 一個人就佔 <b>32.21% 的 K 棒</b>，六個聯集 148,748 個、'
           '每 2.8 根一次、300 根視窗 104 個標記。'
           '<br><br>那個密度下<b>文字是錯的原語</b> —— 標籤寬十個字元，'
           '碰撞發生在寬度不是高度，車道救不了。改成新指標 '
           '<code>IND_S16S_CONV6</code>：副圖六列，每個標記只有一根 K 棒寬。'
           '<br><br><b>MC12 全中</b>：135777 / 89163 / 12730 / 1784 / 57140 / 63021。'),
    dict(t='傍晚', h='多方移除 —— 但是擋繪圖，不是擋偵測',
         k='ship',
         b='P28 杯柄／P50 擴散底／P52 下降擴散楔形／P54 右角擴散／P61 鑽石底。'
           '<br><br>四個有 <code>Enable_</code> 可以直接關，但關掉會連<b>偵測與計數</b>'
           '一起關掉，已驗證的 202／112／90、DIA 0／1、75／88／39 全部會消失。'
           '<b>普查要完整，被過濾的是顯示。</b>'
           '<br><br>順帶查過 SECTION 8a 的本體上色是另一條路徑，也一起擋掉 —— 不是假設，是查過。'),
    dict(t='晚上', h='3x3 格補滿 —— 而「平」不再是「跟 tick 相等」',
         k='ship',
         b='五個新格子填進同一張表：P11 上升楔形 1,919、P10 對稱三角 463、'
           'P08 下降三角 2,065、P22 箱型 3,063。'
           '<b>P20 下降通道刻意不加</b> —— 降降格 3,101 ＝ P52 1,716（已畫）'
           '＋ P12 下降楔形 1,299（多方，不畫）＋ 86 平手，它填不到任何洞。'),
    dict(t='深夜（桌機）', h='P17／P68 代號錯置，以及最後十一種',
         k='fix',
         b='桌機驗收 260911 零回歸，並抓到一個<b>代號錯置</b>：'
           '指標裡標成 P68 的判定式是「兩個完全等高的樞紐高」，'
           '<b>那是 P17 雙頂的定義</b>；P68 是「雙頂四變體」（依頂尖或圓細分），'
           '至今未編碼也不該編碼。<b>判定式與所有計數都對，只有代號錯。</b>'
           'Build 260912 已正名。'
           '<br><br>同時把最後十二種走完流程（P39 化約掉），'
           '「邏輯從未審查」<b>歸零</b>。'),
]

LESSONS = [
    ('MC12 的數字只在「重新匯入 ＋ 完整重算」之後才算數',
     '同碼、同 421,455 根、同樞紐數：手改 input 跑出 P52 <b>1716</b>，'
     '重新匯入跑出 <b>1715</b>（＝參考值）。計數器在第 672-687 行、'
     '第一個開關閘門在 758 行 —— <b>設定結構上碰不到計數路徑</b>。'
     'MC12 未完整重算是假設，未證實；規矩可以直接用。'
     '<br><b>代價：為了差 1 追了三輪。</b>'),
    ('母體不只由述詞定義，也由「誰先被問」定義',
     'SECTION 6e 用短路，每次推入只有一個型態成立。產生參考值的腳本讓七個'
     '各自獨立命中，於是 <b>P65 被算成 8,572 而 MC12 印 3,977 —— 差 54%</b>。'
     '加了 break 之後清單順序就是語意，第一次修完順序還是錯的。'),
    ('<code>bars=</code> 從來不是「圖表長度」',
     '我把「P29 報 421,455」講成「MC12 少載 58 根」，'
     '<b>寫進檔頭、判決文件、落地地圖，還拿它解釋 P52 的 1715</b>。'
     'CONV6 在同一張圖報 421,507 ＝ 421,513 − 6，而 6 正是它自己最深的引用 '
     '<code>High[6]</code>。圖表是完整的，58 是 P29 的暖身期。'
     '<br><b>把程式碼的性質說成資料的性質 —— 跟當天早上鑽石那個 bug 同一種錯，'
     '八小時後又犯。</b>'),
    ('三支驗證器一起放行了一份編譯不過的檔案',
     '260890 的 20 個純量被加進 <code>arrays:</code> 區，'
     'MC12 逐行回報 <code>Bracket [ expected</code>。'
     'ASCII 73/73、scope 26/26、semantics FAIL 0 —— <b>全過，而它編不過</b>。'
     '已加 DECLSEC 規則，帶負向對照。'),
    ('不要用審美蓋掉規格',
     '260850 把 P51／P52 預設關掉，理由是「會把 P29 埋掉」。那是審美判斷，'
     '而 <code>Enable_Pxx = 0</code> 不只是不畫 —— 它閘住 <code>v_Ok</code>，'
     '型態<b>完全不被登記</b>。「我不想看」變成了「它沒有被量」。'),
    ('新計數不入 scope 清單 ＝ 把檢查關掉',
     '當天發生兩次（260890 的七個、260910 的八個）。'
     '那支檢查是為 260871 的「每根跑兩次」而寫的，'
     '新計數不納入等於對它們關閉。清單現在 34 個。'),
]


def main():
    A = []
    w = A.append
    w('<title>2026-08-31 一日複習</title>')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:'
      'wght@500;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;'
      'family=JetBrains+Mono:wght@500;600&amp;display=swap" rel="stylesheet">')
    w('''<style>
:root{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --done:#17795e;--ready:#b8860b;--todo:#c8302e;--out:#7c8595;--acc:#7a5cc4;
 --serif:'Noto Serif TC',Georgia,serif;
 --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
 --mono:'JetBrains Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --done:#3ec08d;--ready:#e0b64a;--todo:#e8564e;--out:#79828f;--acc:#a98ce8}}
:root[data-theme="dark"]{--ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --done:#3ec08d;--ready:#e0b64a;--todo:#e8564e;--out:#79828f;--acc:#a98ce8}
:root[data-theme="light"]{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --done:#17795e;--ready:#b8860b;--todo:#c8302e;--out:#7c8595;--acc:#7a5cc4}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 line-height:1.62}
.wrap{max-width:1120px;margin:0 auto;padding:44px 20px 84px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
h1{font-family:var(--serif);font-size:34px;font-weight:700;margin:0 0 12px;
 letter-spacing:-.01em;text-wrap:balance}
.lede{font-size:16px;color:var(--ink2);max-width:64ch;margin:0 0 30px}
.kpi{display:flex;flex-wrap:wrap;gap:34px;padding:22px 0;margin:0 0 8px;
 border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.kpi div{display:flex;flex-direction:column}
.kpi b{font-family:var(--mono);font-size:30px;line-height:1;font-weight:600;
 font-variant-numeric:tabular-nums}
.kpi span{font-size:12px;color:var(--ink3);margin-top:6px}
.bar{display:flex;height:12px;border-radius:6px;overflow:hidden;margin:26px 0 6px;
 background:var(--line2)}
.bar i{display:block}
.barlbl{display:flex;justify-content:space-between;font-size:12px;
 color:var(--ink3);font-family:var(--mono);margin-bottom:36px}
h2{font-family:var(--serif);font-size:22px;font-weight:700;margin:42px 0 16px;
 padding-top:24px;border-top:1px solid var(--line)}
.tl{display:flex;flex-direction:column;gap:1px;background:var(--line);
 border:1px solid var(--line);border-radius:10px;overflow:hidden}
.ev{background:var(--card);padding:20px 22px;display:grid;gap:4px 18px;
 grid-template-columns:82px 1fr}
.ev .t{font-family:var(--mono);font-size:12px;color:var(--ink3);padding-top:3px}
.ev h3{margin:0;font-size:16px;font-weight:700;grid-column:2}
.ev p{margin:6px 0 0;grid-column:2;font-size:14px;color:var(--ink2)}
.ev.frame{border-left:3px solid var(--acc)}
.ev.fix{border-left:3px solid var(--todo)}
.ev.ship{border-left:3px solid var(--done)}
.ls{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 border-radius:10px;overflow:hidden}
.li{background:var(--card);padding:18px 22px}
.li h4{margin:0 0 6px;font-size:15px;font-weight:700;display:flex;gap:11px;
 align-items:baseline}
.li h4 em{font-style:normal;font-family:var(--mono);font-size:12px;
 color:var(--todo);flex:none}
.li p{margin:0;font-size:14px;color:var(--ink2)}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:8px 0 18px;
 font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line2)}
th{font-size:11.5px;letter-spacing:.06em;color:var(--ink3);font-weight:600;
 text-transform:uppercase;border-bottom:1px solid var(--line)}
td.n{text-align:right;font-family:var(--mono)}
.ok{color:var(--done);font-weight:700}
code{font-family:var(--mono);font-size:12.5px}
p{margin:0 0 12px;font-size:14.5px;color:var(--ink2);max-width:66ch}
.note{background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--ink3);border-radius:10px;padding:18px 20px;
 margin:24px 0;font-size:14px;color:var(--ink2)}
.note b{color:var(--ink)}.note h3{margin:0 0 8px;font-size:15px;color:var(--ink)}
</style>''')
    w('<div class="wrap">')
    w('<div class="eyebrow">S16_S · 2026-08-31 · 一日複習</div>')
    w('<h1>把型態畫上圖的那一天</h1>')
    w('<p class="lede">25 個 commit（筆電 19 ＋ 桌機 6）。型態層從 21% 推到 39%，'
      '兩支指標各自通過 MC12 驗收，'
      '而最重要的一件事是<b>「型態層算不算落地」的定義被改寫了</b>。</p>')

    tot = sum(n for _, n, _ in STATE)
    w('<div class="kpi">')
    for lab, n, k in STATE:
        w('<div><b style="color:var(--%s)">%d</b><span>%s</span></div>'
          % (k, n, lab))
    w('<div><b>%d</b><span>純圖形型態母體</span></div>' % tot)
    w('</div>')
    w('<div class="bar">' + ''.join(
        '<i style="width:%.2f%%;background:var(--%s)"></i>' % (100.0 * n / tot, k)
        for _, n, k in STATE if n) + '</div>')
    w('<div class="barlbl"><span>8/31 早上 15 種</span>'
      '<span>8/31 收盤 28 種畫得到、0 種未審查</span></div>')

    w('<h2>那一天發生的事</h2>')
    w('<div class="tl">')
    for e in TIMELINE:
        w('<div class="ev %s"><div class="t">%s</div><h3>%s</h3><p>%s</p></div>'
          % (e['k'], e['t'], e['h'], e['b']))
    w('</div>')

    w('<h2>兩支指標的驗收</h2>')
    w('<table><thead><tr><th>指標</th><th>Build</th><th>驗收內容</th>'
      '<th class="n">結果</th></tr></thead><tbody>')
    for a, b, c in (
        ('IND_S16S_P29', '260881',
         '十一個量：bars／樞紐／formations 202／P49 112／P50 90／逐年／'
         '五變體／P52 逐年／break 75-88-39／overflow 0'),
        ('IND_S16S_P29', '260893', 'SEVEN TALLY 七種 ＋ 兩道護欄未動'),
        ('IND_S16S_CONV6', '260901', 'CONV6 TALLY 六種 ＋ bars'),
        ('IND_S16S_P29', '260911', '桌機：與 8/30 同圖六項護欄逐字相同，零回歸'),
    ):
        w('<tr><td><code>%s</code></td><td class="n">%s</td><td>%s</td>'
          '<td class="n ok">全中</td></tr>' % (a, b, c))
    w('</tbody></table>')

    w('<h2>量出來的一件事：「完全相等」正在被算術消滅</h2>')
    w('<table><thead><tr><th>年</th><th class="n">中位單根區間</th>'
      '<th class="n">四個「完全相等」型態合計命中</th></tr></thead><tbody>')
    for y, r, n in (('2019', 4, 9), ('2020', 8, 2), ('2021', 10, 1),
                    ('2022', 12, 4), ('2023', 8, 5), ('2024', 16, 2),
                    ('2025', 17, 1), ('2026', 49, 0)):
        w('<tr><td>%s</td><td class="n">%d 點</td><td class="n">%d</td></tr>'
          % (y, r, n))
    w('</tbody></table>')
    w('<p>tick 固定 1 點，擺幅從 4 點漲到 49 點。三個獨立的擺盪低點要落在同一個'
      '整數價位，機率隨擺幅反比衰減 —— <b>2026 年至今四個全部掛零</b>。'
      '不是市場變了，是分母變大了。</p>')
    w('<p>用戶的裁示：<b>「就算市場震幅變大，型態相同的就是直接抓出來」</b>。'
      '審計後發現全檔只有「價格全等」這一個測試是尺度相依的 —— '
      '其餘全是價格對價格、根數對根數，本來就尺度不變。'
      '改成<b>收斂</b>（這一邊的散布 &lt; 另一邊的移動距離），'
      '全等的那些保留成子標籤，桌機驗證 <b>P53 7 ／ P54 8 完全相同</b> —— '
      '舊集合原封不動被包在新定義裡。</p>')

    w('<h2>那天犯的錯</h2>')
    w('<p>六條，其中三條是同一類：把程式碼的性質說成資料的性質。'
      '列在這裡因為它們比成果更耐用。</p>')
    w('<div class="ls">')
    for i, (h, b) in enumerate(LESSONS, 1):
        w('<div class="li"><h4><em>%d</em>%s</h4><p>%s</p></div>' % (i, h, b))
    w('</div>')

    w('<div class="note"><h3>還有一個是隔天才發現的</h3>'
      '指標裡標成 <code>P68</code> 的判定式是「兩個完全等高的樞紐高」，'
      '<b>那是 P17 雙頂的定義</b>。P68 其實是「雙頂四變體」，'
      '依頂尖或圓細分，需要曲率門檻所以不編碼。'
      '<br><br><b>判定式與所有計數都是對的，錯的只有代號</b> —— '
      '但代號在這個專案裡是主鍵，落地地圖曾經把 P68 算成「已畫」、'
      'P17 算成「未審查」，兩個都反了。Build 260912 已正名。</div>')

    w('<div class="note"><h3>誠實聲明</h3>'
      '本頁所有 MC12 數字都是當天用戶貼出的實際輸出；'
      '母體數字來自已 commit 的量測腳本，可複現。'
      '進度條的 28／15／0／29 取自 <code>s16s_landing_map_page.py</code> 當前狀態。'
      '<b>Build 260912 尚未在這台機器驗收</b>，桌機的零回歸是在桌機的 409,546 根圖上。'
      '本頁由 Claude 產出，未經第二方審查。</div>')
    w('</div>')
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(A))
    print('wrote %s' % OUT)
    print('  狀態合計 %d（應為 72）' % tot)
    assert tot == 72, '狀態合計不是 72'


if __name__ == '__main__':
    main()
