# -*- coding: utf-8 -*-
"""七種型態的規格對照圖 —— 每個條件標出對應圖上哪裡.

memory 規則 `feedback_pattern_logic_diagram`：
「每討論完一個型態的邏輯，必須畫圖標出規格各段對應圖上哪裡。」

★ 這支腳本用真正的述詞斷言示意圖的座標

示意圖的樞紐價格不是隨手畫的，是先寫下來、再餵進**與指標同一組述詞**
檢查它確實成立。座標若不滿足條件，腳本就掛掉，圖不可能跟規格說的不一致。
這是 2026-08-30 那條「產生結構的腳本必須檢查自己產生的結構」的延伸。

Run:  python scripts/research/s16s_seven_make_diagram.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.join('docs', 'research', 'S16S_seven_diagram.html')

# ---- 述詞，與 s16s_seven_scan.py / SECTION 6e 同一份 ----------------------
def dome(a, b, c, d, e):
    return a < b < c > d > e and (b - a) > (c - b) and (c - d) < (d - e)


def spike(a, b, c, d, e):
    return a < b < c > d > e and (b - a) < (c - b) and (c - d) > (d - e)


def inband(x, p, q):
    return min(p, q) <= x <= max(p, q)


# 每個型態：代號、名稱、樞紐價（依序，第一個的型別由 start 決定）、
#           bar 間距（只有 P65 用得到）、條件列、母體、檢查函式
def chk_P15(p, _):
    return p[0] < p[2] > p[4]


def chk_P26(p, _):
    return dome(p[0], p[2], p[4], p[6], p[8])


def chk_P32(p, _):
    return spike(p[0], p[2], p[4], p[6], p[8])


def chk_P56(p, _):
    return p[1] < p[0] and inband(p[2], p[1], p[0]) and p[3] < p[1]


def chk_P59(p, _):
    return (p[1] > p[3] < p[5] and (p[1] - p[3]) > (p[5] - p[3])
            and p[6] > p[0])


def chk_P65(p, g):
    ub, db = g[1] - g[0], g[2] - g[1]
    return p[1] > p[0] and p[2] < p[0] and db <= ub


def chk_P72(p, _):
    return p[2] > p[0] and p[1] < p[0]


PATS = [
    dict(code='P15', zh='頭肩頂', en='Head and Shoulders', n=5242, start='H',
         px=[60, 35, 85, 38, 62], gap=[0, 1, 2, 3, 4], chk=chk_P15,
         lead='五個交替樞紐，以樞紐高起頭。頭必須高過兩肩 —— 只有這一條。',
         conds=[('頭高過左肩', 'h0 &lt; h2', '第 1 與第 3 個高點'),
                ('頭高過右肩', 'h2 &gt; h4', '第 3 與第 5 個高點')],
         zero='<b>肩不要求對稱。</b>「兩肩要多接近」是容差，容差就是參數。'
              '頸線水平化同理。加上去的代價量在 <code>s16s_hs_scan.py</code>。',
         note='08-29 原裁示是不編碼（鏡像同樣通過、不含方向）。'
              '08-31 標準改為「有出現就畫」，本型態因此進來。'),
    dict(code='P26', zh='圓弧頂', en='Rounding Top', n=60, start='H',
         px=[40, 30, 62, 50, 72, 60, 55, 42, 25],
         gap=list(range(9)), chk=chk_P26,
         lead='九個交替樞紐，取其中五個高點。先升後降，而且'
              '<b>上行在減速、下行在加速</b>。',
         conds=[('先升後降', 'a &lt; b &lt; c &gt; d &gt; e', '五個高點的排列'),
                ('上行減速', '(b−a) &gt; (c−b)', '第二段漲幅小於第一段'),
                ('下行加速', '(c−d) &lt; (d−e)', '第二段跌幅大於第一段')],
         zero='三條全是<b>同尺度的比較</b>，沒有任何外來常數。'
              '「圓不圓」不靠曲率門檻，靠兩段漲幅／兩段跌幅誰大誰小。',
         note='08-30 量測：給定「先漲後跌」，圓弧 20.7%／尖頂 30.1%／混合 49.2%，'
              '接近兩個獨立銅板的 25/25/50 —— <b>這個標籤被量到沒有內容</b>。'
              '照 08-31 裁示仍然畫上去，讓你用眼睛檢查這個量測。'),
    dict(code='P32', zh='V 型反轉', en='V Reversal', n=97, start='H',
         px=[30, 25, 45, 38, 85, 55, 40, 32, 25],
         gap=list(range(9)), chk=chk_P32,
         lead='與 P26 <b>同一組九個樞紐</b>，只有加減速方向相反：'
              '<b>上行在加速、下行在減速</b> —— 一個尖頂。',
         conds=[('先升後降', 'a &lt; b &lt; c &gt; d &gt; e', '與 P26 完全相同'),
                ('上行加速', '(b−a) &lt; (c−b)', '第二段漲幅大於第一段'),
                ('下行減速', '(c−d) &gt; (d−e)', '第二段跌幅小於第一段')],
         zero='與 P26 互斥：兩者的第二、三條剛好相反，'
              '所以同一組樞紐不可能兩個都成立，指標裡用 else if 表達。',
         note='「把畫面縮小，任何東西都符合 V」——'
              '你 08-30 的這句話成立，量測見左。'),
    dict(code='P56', zh='死貓反彈', en='Dead-Cat Bounce', n=9134, start='H',
         px=[70, 35, 55, 20], gap=[0, 1, 2, 3], chk=chk_P56,
         lead='四個交替樞紐。跌下來、反彈、<b>反彈死在原本那段的區間裡</b>、'
              '然後創更低的低。',
         conds=[('先跌一段', 'l1 &lt; h0', '第一個低點低於第一個高點'),
                ('反彈死在區間內', 'min(l1,h0) ≤ h1 ≤ max(l1,h0)',
                 '第二個高點落在前兩點框出的帶子裡'),
                ('再創低', 'l2 &lt; l1', '第二個低點低於第一個低點')],
         zero='<b>區間裝置</b>（08-29 裁示）：兩點定區間、第三點受測，'
              '容差就是 |h0−l1|，由型態自己給。零參數、免疫於衰減律。',
         note='本組最頻繁的三個之一：8 年 9,134 個，每 46 根一個。'),
    dict(code='P59', zh='穿越型態', en='Descending Scallop', n=309, start='H',
         px=[55, 40, 50, 20, 45, 32, 70],
         gap=list(range(7)), chk=chk_P59,
         lead='七個交替樞紐，取其中三個低點與頭尾兩個高點 —— '
              '<b>一個走完的 J</b>：探底、回升、而且回升比下跌短。',
         conds=[('中間那個低是谷底', 'l1 &gt; l2 &lt; l3', '三個低點的排列'),
                ('回升短於下跌', '(l1−l2) &gt; (l3−l2)',
                 '從谷底回升的幅度小於跌進谷底的幅度'),
                ('尾高過頭高', 'h4 &gt; h0', '最後一個高點高於第一個')],
         zero='三條都是型態自身兩段長度的比較。'
              '「J 的弧度」沒有被量，因為量它就要參數。'),
    dict(code='P65', zh='塔形頂', en='Tower Top', n=8572, start='L',
         px=[35, 80, 25], gap=[0, 6, 10], chk=chk_P65,
         lead='三個交替樞紐，<b>以樞紐低起頭</b>。漲上去、全數吐回、'
              '而且<b>跌的根數不多於漲的根數</b>。',
         conds=[('先漲', 'h1 &gt; l0', '中間的高點高於起點的低點'),
                ('全數吐回', 'l1 &lt; l0', '收尾的低點低於起點的低點'),
                ('跌得不比漲慢', '跌的根數 ≤ 漲的根數',
                 '兩段的 K 棒根數相比，不是速度門檻')],
         zero='第三條用<b>根數比根數</b>，不是「幾根之內」那種門檻。'
              '普查時原本還有一條「跌幅至少等於漲幅」，'
              '實測發現它完全被第二條涵蓋，個數一根不變，已刪。'),
    dict(code='P72', zh='訂單塊', en='Order Block', n=18705, start='H',
         px=[55, 35, 75], gap=[0, 1, 2], chk=chk_P72,
         lead='三個交替樞紐。<b>更高的高點，而且中間那個低點沉在舊高之下</b> —— '
              '也就是那段吃掉舊高的推進，是從舊高底下發動的。',
         conds=[('中間的低沉在舊高之下', 'l1 &lt; h0',
                 '回檔跌破了第一個高點的價位'),
                ('新高過舊高', 'h1 &gt; h0', '第二個高點高於第一個')],
         zero='兩條都是價位大小比較。沒有「訂單塊要多大」「要停留幾根」'
              '這類外加條件 —— 那些都是參數。',
         note='本組最頻繁：8 年 18,705 個，每 23 根一個。'
              '條件只有兩條，寬鬆是必然的。'),
]

W, H = 660, 200
PAD_L, PAD_R, TOP, BOT = 46, 24, 26, 46


def svg(p):
    px, gap = p['px'], p['gap']
    n = len(px)
    span = float(gap[-1] - gap[0]) or 1.0
    xs = [PAD_L + (gap[i] - gap[0]) / span * (W - PAD_L - PAD_R)
          for i in range(n)]
    lo, hi = min(px), max(px)
    rng = float(hi - lo) or 1.0
    ys = [TOP + (hi - v) / rng * (H - TOP - BOT) for v in px]
    first_high = p['start'] == 'H'
    out = ['<svg viewBox="0 0 %d %d" role="img" aria-label="%s %s 規格對照圖">'
           % (W, H, p['code'], p['zh'])]
    pts = ' '.join('%.1f,%.1f' % (xs[i], ys[i]) for i in range(n))
    out.append('<polyline class="zz" points="%s"/>' % pts)
    hi_i = lo_i = 0
    for i in range(n):
        is_high = (i % 2 == 0) == first_high
        cls = 'ph' if is_high else 'pl'
        if is_high:
            hi_i += 1
            lbl = 'h%d' % (hi_i - 1)
        else:
            lo_i += 1
            lbl = 'l%d' % lo_i
        out.append('<circle class="%s" cx="%.1f" cy="%.1f" r="5"/>'
                   % (cls, xs[i], ys[i]))
        dy = -13 if is_high else 19
        out.append('<text class="pv" x="%.1f" y="%.1f">%s</text>'
                   % (xs[i], ys[i] + dy, lbl))
    out.append('<text class="ax" x="4" y="%d">高</text>' % (TOP + 4))
    out.append('<text class="ax" x="4" y="%d">低</text>' % (H - BOT))
    out.append('<text class="cap" x="%d" y="%d">%s 個樞紐，以樞紐%s起頭</text>'
               % (PAD_L, H - 14, n, '高' if first_high else '低'))
    out.append('</svg>')
    return '\n'.join(out)


def main():
    for p in PATS:
        assert p['chk'](p['px'], p['gap']), \
            '%s 的示意圖座標不滿足它自己的條件' % p['code']
        assert len(p['px']) == len(p['gap']), p['code']
    print('七張示意圖的座標全部通過各自的述詞')

    A = []
    w = A.append
    w('<title>七種型態規格對照圖</title>')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:'
      'wght@500;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;'
      'family=JetBrains+Mono:wght@500;600&amp;display=swap" rel="stylesheet">')
    w('''<style>
:root{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --ph:#c8302e;--pl:#17795e;--acc:#7a5cc4;
 --serif:'Noto Serif TC',Georgia,serif;
 --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
 --mono:'JetBrains Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --ph:#e8564e;--pl:#3ec08d;--acc:#a98ce8}}
:root[data-theme="dark"]{--ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --ph:#e8564e;--pl:#3ec08d;--acc:#a98ce8}
:root[data-theme="light"]{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --ph:#c8302e;--pl:#17795e;--acc:#7a5cc4}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 line-height:1.62}
.wrap{max-width:1120px;margin:0 auto;padding:44px 20px 84px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
h1{font-family:var(--serif);font-size:33px;font-weight:700;margin:0 0 12px;
 letter-spacing:-.01em}
.lede{font-size:16px;color:var(--ink2);max-width:64ch;margin:0 0 26px}
.pat{background:var(--card);border:1px solid var(--line);border-radius:11px;
 padding:24px 26px;margin:22px 0}
.hd{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
 border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:16px}
.hd code{font-family:var(--mono);font-size:15px;font-weight:600;
 color:var(--acc)}
.hd h2{font-family:var(--serif);font-size:22px;margin:0;font-weight:700}
.hd .en{font-size:12.5px;color:var(--ink3)}
.hd .n{margin-left:auto;font-family:var(--mono);font-size:13px;
 color:var(--ink2);font-variant-numeric:tabular-nums}
.body{display:grid;gap:24px;grid-template-columns:minmax(300px,1fr) minmax(280px,1fr)}
.fig{overflow-x:auto}
svg{display:block;max-width:100%;height:auto}
.zz{fill:none;stroke:var(--ink2);stroke-width:2;stroke-linejoin:round}
circle.ph{fill:var(--ph)}circle.pl{fill:var(--pl)}
text.pv{font:600 12px 'JetBrains Mono',monospace;fill:var(--ink);
 text-anchor:middle}
text.ax{font:500 11px 'Noto Sans TC',sans-serif;fill:var(--ink3)}
text.cap{font:500 12px 'Noto Sans TC',sans-serif;fill:var(--ink3)}
p{margin:0 0 12px;font-size:14.5px;color:var(--ink2)}
p.lead{color:var(--ink);font-size:15px}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0 14px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line2);
 vertical-align:top}
th{font-size:11.5px;letter-spacing:.06em;color:var(--ink3);font-weight:600;
 text-transform:uppercase;border-bottom:1px solid var(--line)}
td.f{font-family:var(--mono);font-size:12.5px;color:var(--ink);
 white-space:nowrap}
.zero{background:var(--bg);border-left:3px solid var(--acc);
 border-radius:0 7px 7px 0;padding:12px 15px;font-size:13.5px;
 color:var(--ink2);margin:0 0 12px}
.zero b{color:var(--ink)}
.nb{font-size:13px;color:var(--ink3);border-top:1px dashed var(--line);
 padding-top:11px;margin:0}
.nb b{color:var(--ink2)}
code{font-family:var(--mono);font-size:12.5px}
.note{background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--ink3);border-radius:10px;padding:18px 20px;
 margin:26px 0;font-size:14px;color:var(--ink2)}
.note b{color:var(--ink)}
.note h3{margin:0 0 8px;font-size:15px;color:var(--ink)}
</style>''')
    w('<div class="wrap">')
    w('<div class="eyebrow">S16_S · 2026-08-31 · Build 260890</div>')
    w('<h1>七種型態 —— 規格逐條對照圖</h1>')
    w('<p class="lede">這七種的邏輯先前已經審查過（08-29 樞紐型 A 組、'
      '08-30 母體普查），本頁把每一條規格標到圖上對應的位置，'
      '並記錄它為什麼是零參數。定義原樣取自已審查的來源，本頁沒有重寫任何一條。</p>')
    w('<div class="note"><h3>示意圖不是隨手畫的</h3>'
      '每張圖的樞紐價格都先寫下來，再餵進<b>與指標同一組述詞</b>檢查它確實成立。'
      '座標若不滿足條件，產生器就掛掉。'
      '所以圖上看到的排列，就是程式碼會判定成立的排列。</div>')

    for p in PATS:
        w('<div class="pat">')
        w('<div class="hd"><code>%s</code><h2>%s</h2>'
          '<span class="en">%s</span>'
          '<span class="n">八年 %s 個</span></div>'
          % (p['code'], p['zh'], p['en'], format(p['n'], ',')))
        w('<div class="body">')
        w('<div class="fig">%s</div>' % svg(p))
        w('<div>')
        w('<p class="lead">%s</p>' % p['lead'])
        w('<table><thead><tr><th>條件</th><th>式子</th><th>圖上哪裡</th></tr>'
          '</thead><tbody>')
        for nm, f, whr in p['conds']:
            w('<tr><td>%s</td><td class="f">%s</td><td>%s</td></tr>'
              % (nm, f, whr))
        w('</tbody></table>')
        w('<p class="zero"><b>零參數：</b>%s</p>' % p['zero'])
        if p.get('note'):
            w('<p class="nb"><b>註：</b>%s</p>' % p['note'])
        w('</div></div></div>')

    w('<div class="note"><h3>母體與繪圖量</h3>'
      '七種合計 <b>42,119</b> 個，加上原有的 3,602 個約 45,700 個型態。'
      '標籤與趨勢線都開的話約九萬個繪圖物件。'
      '<b>MC12 的上限我不知道，也不猜。</b>依 08-31 裁示七個全開，'
      '若跑不動，解法是限制繪製的回看根數，不是停止偵測一個真的發生過的形狀。<br><br>'
      '數字由 <code>scripts/research/s16s_seven_scan.py</code> 重放指標自己的'
      '十二槽鏈算出，不是沿用普查的滑動視窗 —— 那正是 08-30 整份普查要重算的原因。'
      '</div>')
    w('<div class="note"><h3>誠實聲明</h3>'
      '本頁的示意圖是<b>示意</b>，不是真實 K 棒案例。'
      '真實案例在各自的來源頁（08-29 樞紐型 A 組、08-30 母體普查）。'
      '母體數字可複現；指標 Build 260890 <b>尚未在 MC12 跑過</b>，'
      '本頁沒有宣稱它跑得出這些數字。本頁由 Claude 產出，未經第二方審查。</div>')
    w('</div>')
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(A))
    print('wrote %s' % OUT)


if __name__ == '__main__':
    main()
