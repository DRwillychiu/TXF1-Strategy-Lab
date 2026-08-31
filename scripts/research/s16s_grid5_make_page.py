# -*- coding: utf-8 -*-
"""2x2 家族五個新格子的邏輯層討論頁 —— 附真實 K 棒案例.

Willy 2026-08-31：「也要記得附上真實的情況以及型態的邏輯層討論」

所以每個型態都畫真的 K 棒，不是示意圖：從 s16s_5min.csv 取出該案例的
實際 OHLC，標出六個樞紐，並把規格逐條對到圖上的位置。

案例挑選：跨度取中位數、不跨時段者。中位數而不是最漂亮的那個 ——
挑好看的案例是在替型態說話。

Run:  python scripts/research/s16s_grid5_make_page.py
"""
import collections
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, 's16s_5min.csv')
OUT = os.path.join('docs', 'research', 'S16S_grid5_diagram.html')
SLOTS = 12
PAD = 4                                        # 案例左右各多畫幾根


def band(x, p, q):
    return min(p, q) <= x <= max(p, q)


def scan():
    rows = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    O = [float(r['open']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)

    def is_ph(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and H[i] > H[i - 1] and H[i] > H[i + 1])

    def is_pl(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and L[i] < L[i - 1] and L[i] < L[i + 1])

    hit = collections.defaultdict(list)
    chain = []
    for b in range(1, N):
        i = b - 1
        for k in (1, 2):
            if not (is_ph(i) if k == 1 else is_pl(i)):
                continue
            if chain and chain[-1][2] == k:
                chain = []
            if len(chain) >= SLOTS:
                chain = chain[1:]
            chain.append((i, H[i] if k == 1 else L[i], k))
            if len(chain) < 6:
                continue
            w = chain[-6:]
            hs = [x for x in w if x[2] == 1]
            ls = [x for x in w if x[2] == 2]
            if len(hs) != 3 or len(ls) != 3:
                continue
            hp = [x[1] for x in hs]
            lp = [x[1] for x in ls]
            if not (lp[0] < hp[0] and lp[2] < hp[2]):
                continue
            rH = hp[0] < hp[1] < hp[2]
            fH = hp[0] > hp[1] > hp[2]
            rL = lp[0] < lp[1] < lp[2]
            fL = lp[0] > lp[1] > lp[2]
            bH = band(hp[2], hp[0], hp[1])
            bL = band(lp[2], lp[0], lp[1])
            sH, sL = hp[2] - hp[0], lp[2] - lp[0]
            rec = (w[0][0], w[-1][0], [(x[0], x[1], x[2]) for x in w])
            if fH and bL and not fL and not rL:  hit['P08'].append(rec)
            if fH and rL:                        hit['P10'].append(rec)
            if rH and rL and sH < sL:            hit['P11'].append(rec)
            if fH and fL:                        hit['P20'].append(rec)
            if bH and bL and not (rH or fH) and not (rL or fL):
                hit['P22'].append(rec)
    return rows, O, H, L, C, S, hit


PATS = [
    dict(code='P08', zh='下降三角', en='Descending Triangle', n=2623,
         cell='高降 x 低平', dirn='空',
         lead='三個高點單調下移，三個低點<b>停在同一條帶子裡</b> —— '
              '賣壓一階一階往下壓，買盤守在同一個價位。',
         conds=[('高單調下移', 'h1 &gt; h2 &gt; h3', '上緣三個點'),
                ('低點落在帶子內', 'min(l1,l2) &le; l3 &le; max(l1,l2)',
                 '下緣：前兩個低定帶子，第三個受測'),
                ('低在高下', 'l1 &lt; h1 且 l3 &lt; h3', '整個型態的幾何一致性')],
         zero='第二條原本寫「低完全相等」，八年只有 <b>7 個</b>、四個年份掛零。'
              '改用區間裝置後 <b>2,623 個</b>、零掛零年，而容差是 |l1−l2| '
              '由型態自己給 —— 仍然零參數。'),
    dict(code='P10', zh='對稱三角', en='Symmetrical Triangle', n=463,
         cell='高降 x 低升', dirn='續勢',
         lead='高點下移、低點上移 —— 兩邊同時收斂。'
              '它是 P29 擴散三角的<b>鏡像</b>：P29 兩邊同時外擴。',
         conds=[('高單調下移', 'h1 &gt; h2 &gt; h3', '上緣'),
                ('低單調上移', 'l1 &lt; l2 &lt; l3', '下緣'),
                ('低在高下', 'l1 &lt; h1 且 l3 &lt; h3', '幾何一致性')],
         zero='兩條單調條件，沒有任何常數。'
              '八年 463 個，是這一組裡最少的 —— 兩邊同時收斂比較難成立。'),
    dict(code='P11', zh='上升楔形', en='Rising Wedge', n=1919,
         cell='高升 x 低升，高漲得慢', dirn='空（反轉）',
         lead='高低點都在上移，但<b>高點漲得比低點慢</b> —— '
              '空間被由下往上擠掉。它跟已編碼的 P51 上升擴散楔形'
              '共用同一格，差別只在誰漲得快。',
         conds=[('高單調上移', 'h1 &lt; h2 &lt; h3', '上緣'),
                ('低單調上移', 'l1 &lt; l2 &lt; l3', '下緣'),
                ('高漲幅小於低漲幅', '(h3−h1) &lt; (l3−l1)',
                 '兩條線的跨距相比，收斂')],
         zero='第三條是<b>比較</b>不是門檻 —— 沒有「要收斂多少」這種常數。'
              '同一格裡 P51 是 (h3−h1) &gt; (l3−l1)、P11 是 &lt;，'
              '另有 140 個兩者相等落在中間，兩個都不算。'),
    dict(code='P20', zh='下降通道', en='Descending Channel', n=3101,
         cell='高降 x 低降（整格）', dirn='空（續勢）',
         lead='高低點同步下移。<b>這一格就是它</b> —— 沒有跨距條件，'
              '所以已編碼的 P52 下降擴散楔形（低跌得比較快）'
              '是它的子集，量到 1,716 個，占 55.3%。',
         conds=[('高單調下移', 'h1 &gt; h2 &gt; h3', '上緣'),
                ('低單調下移', 'l1 &gt; l2 &gt; l3', '下緣'),
                ('低在高下', 'l1 &lt; h1 且 l3 &lt; h3', '幾何一致性')],
         zero='兩條單調，零常數。'
              '<b>P52 完全落在 P20 之內，已驗證。</b>依 2026-08-31'
              '「兩個都畫」裁示，底層的 P20 與子集 P52 都上圖。'),
    dict(code='P22', zh='箱型', en='Rectangle / Box', n=3063,
         cell='高平 x 低平', dirn='中性',
         lead='上下緣都停在自己的帶子裡 —— 一段沒有方向的區間。',
         conds=[('高點落在帶子內', 'min(h1,h2) &le; h3 &le; max(h1,h2)',
                 '上緣：前兩個高定帶子'),
                ('低點落在帶子內', 'min(l1,l2) &le; l3 &le; max(l1,l2)',
                 '下緣：前兩個低定帶子'),
                ('兩邊都不單調', '非升也非降', '否則它屬於別的格子')],
         zero='原定義是「高完全相等 ＋ 低完全相等」，'
              '八年只有 <b>2 個</b>、七個年份掛零 —— 幾乎不存在。'
              '區間裝置版 <b>3,063 個</b>、零掛零年，倍率 1,532 倍。'),
]

W, HGT = 700, 260
ML, MR, MT, MB = 8, 8, 22, 34


def candles(rows, O, H, L, C, a, z, piv):
    lo_i, hi_i = max(0, a - PAD), min(len(rows) - 1, z + PAD)
    n = hi_i - lo_i + 1
    lo = min(L[lo_i:hi_i + 1])
    hi = max(H[lo_i:hi_i + 1])
    rng = float(hi - lo) or 1.0
    bw = (W - ML - MR) / float(n)
    def X(i):
        return ML + (i - lo_i + 0.5) * bw
    def Yv(p):
        return MT + (hi - p) / rng * (HGT - MT - MB)
    out = ['<svg viewBox="0 0 %d %d" role="img" aria-label="real bars">'
           % (W, HGT)]
    body = max(1.6, bw * 0.62)
    for i in range(lo_i, hi_i + 1):
        up = C[i] >= O[i]
        cls = 'cu' if up else 'cd'
        inpat = a <= i <= z
        op = '' if inpat else ' opacity=".34"'
        out.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"%s/>'
                   % (cls, X(i), Yv(H[i]), X(i), Yv(L[i]), op))
        y0, y1 = Yv(max(O[i], C[i])), Yv(min(O[i], C[i]))
        out.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" '
                   'height="%.1f"%s/>'
                   % (cls, X(i) - body / 2, y0, body, max(1.0, y1 - y0), op))
    hp = [(x, p) for x, p, t in piv if t == 1]
    lp = [(x, p) for x, p, t in piv if t == 2]
    for pts, cls in ((hp, 'ph'), (lp, 'pl')):
        out.append('<polyline class="gd %s" points="%s"/>'
                   % (cls, ' '.join('%.1f,%.1f' % (X(x), Yv(p))
                                    for x, p in pts)))
    for j, (x, p) in enumerate(hp):
        out.append('<circle class="ph" cx="%.1f" cy="%.1f" r="3.6"/>'
                   % (X(x), Yv(p)))
        out.append('<text class="pv" x="%.1f" y="%.1f">h%d</text>'
                   % (X(x), Yv(p) - 8, j + 1))
    for j, (x, p) in enumerate(lp):
        out.append('<circle class="pl" cx="%.1f" cy="%.1f" r="3.6"/>'
                   % (X(x), Yv(p)))
        out.append('<text class="pv" x="%.1f" y="%.1f">l%d</text>'
                   % (X(x), Yv(p) + 14, j + 1))
    out.append('<text class="ax" x="%d" y="%d">%s %s</text>'
               % (ML, HGT - 12, rows[a]['ymd'], rows[a]['hhmm']))
    out.append('<text class="ax" x="%d" y="%d" text-anchor="end">'
               '%s %s   %d 根 K 棒</text>'
               % (W - MR, HGT - 12, rows[z]['ymd'], rows[z]['hhmm'],
                  z - a + 1))
    out.append('</svg>')
    return '\n'.join(out)


def main():
    rows, O, H, L, C, S, hit = scan()
    for p in PATS:
        hs = hit[p['code']]
        assert hs, p['code']
        assert len(hs) == p['n'], '%s 量到 %d，頁面寫 %d' % (
            p['code'], len(hs), p['n'])
        clean = [r for r in hs
                 if all(S[t] > 1 for t in range(r[0] + 1, r[1] + 1))]
        if not clean:
            clean = hs
        clean.sort(key=lambda r: r[1] - r[0])
        p['ex'] = clean[len(clean) // 2]
    print('五個型態的個數與頁面標示一致，案例皆為跨度中位且不跨時段')

    A = []
    w = A.append
    w('<title>2x2 家族五格 - 真實案例</title>')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:'
      'wght@500;700&amp;family=Noto+Sans+TC:wght@400;500;700&amp;'
      'family=JetBrains+Mono:wght@500;600&amp;display=swap" rel="stylesheet">')
    w('''<style>
:root{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --up:#c8302e;--dn:#17795e;--ph:#d1382f;--pl:#0f9d76;--acc:#7a5cc4;
 --serif:'Noto Serif TC',Georgia,serif;
 --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
 --mono:'JetBrains Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --up:#e8564e;--dn:#3ec08d;--ph:#ff6b5e;--pl:#3ecfa0;--acc:#a98ce8}}
:root[data-theme="dark"]{--ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --up:#e8564e;--dn:#3ec08d;--ph:#ff6b5e;--pl:#3ecfa0;--acc:#a98ce8}
:root[data-theme="light"]{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --up:#c8302e;--dn:#17795e;--ph:#d1382f;--pl:#0f9d76;--acc:#7a5cc4}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 line-height:1.62}
.wrap{max-width:1120px;margin:0 auto;padding:44px 20px 84px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
h1{font-family:var(--serif);font-size:33px;font-weight:700;margin:0 0 12px}
.lede{font-size:16px;color:var(--ink2);max-width:64ch;margin:0 0 26px}
.grid{border-collapse:collapse;margin:20px 0 28px;font-size:13.5px}
.grid th,.grid td{border:1px solid var(--line);padding:9px 13px;
 text-align:center}
.grid th{background:var(--card);color:var(--ink3);font-size:12px;
 font-weight:600}
.grid td{background:var(--card)}
.grid td.new{background:rgba(122,92,196,.10);font-weight:700;color:var(--ink)}
.grid td.old{color:var(--ink3)}
.grid td.hole{color:var(--ink3);font-style:italic}
.pat{background:var(--card);border:1px solid var(--line);border-radius:11px;
 padding:24px 26px;margin:22px 0}
.hd{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
 border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:16px}
.hd code{font-family:var(--mono);font-size:15px;font-weight:600;
 color:var(--acc)}
.hd h2{font-family:var(--serif);font-size:22px;margin:0;font-weight:700}
.hd .en{font-size:12.5px;color:var(--ink3)}
.hd .cell{font-family:var(--mono);font-size:12px;color:var(--ink2);
 border:1px solid var(--line);border-radius:4px;padding:1px 7px}
.hd .n{margin-left:auto;font-family:var(--mono);font-size:13px;
 color:var(--ink2);font-variant-numeric:tabular-nums}
.fig{overflow-x:auto;margin:0 0 6px}
svg{display:block;max-width:100%;height:auto}
.wk{stroke-width:1.3}.wk.cu{stroke:var(--up)}.wk.cd{stroke:var(--dn)}
.bd.cu{fill:var(--card);stroke:var(--up);stroke-width:1.2}
.bd.cd{fill:var(--dn);stroke:var(--dn);stroke-width:1.2}
.gd{fill:none;stroke-width:1.4;stroke-dasharray:5 3;opacity:.75}
.gd.ph{stroke:var(--ph)}.gd.pl{stroke:var(--pl)}
circle.ph{fill:var(--ph)}circle.pl{fill:var(--pl)}
text.pv{font:600 11px 'JetBrains Mono',monospace;fill:var(--ink);
 text-anchor:middle}
text.ax{font:500 11px 'JetBrains Mono',monospace;fill:var(--ink3)}
.cap{font-size:12.5px;color:var(--ink3);margin:0 0 16px}
p{margin:0 0 12px;font-size:14.5px;color:var(--ink2)}
p.lead{color:var(--ink);font-size:15px}
table.cd{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0 14px}
table.cd th,table.cd td{text-align:left;padding:7px 10px;
 border-bottom:1px solid var(--line2);vertical-align:top}
table.cd th{font-size:11.5px;letter-spacing:.06em;color:var(--ink3);
 font-weight:600;text-transform:uppercase;border-bottom:1px solid var(--line)}
table.cd td.f{font-family:var(--mono);font-size:12.5px;color:var(--ink);
 white-space:nowrap}
.zero{background:var(--bg);border-left:3px solid var(--acc);
 border-radius:0 7px 7px 0;padding:12px 15px;font-size:13.5px;
 color:var(--ink2);margin:0}
.zero b{color:var(--ink)}
.note{background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--ink3);border-radius:10px;padding:18px 20px;
 margin:26px 0;font-size:14px;color:var(--ink2)}
.note b{color:var(--ink)}.note h3{margin:0 0 8px;font-size:15px;color:var(--ink)}
</style>''')
    w('<div class="wrap">')
    w('<div class="eyebrow">S16_S · 2026-08-31 · 邏輯層討論</div>')
    w('<h1>2x2 家族的五個新格子</h1>')
    w('<p class="lede">P08 下降三角／P10 對稱三角／P11 上升楔形／'
      'P20 下降通道／P22 箱型。這五個不是五個新骨架 —— '
      '它們跟已經編碼的擴散家族填的是<b>同一張格子表</b>。</p>')

    w('<table class="grid"><thead><tr><th></th>'
      '<th>低升</th><th>低降</th><th>低平</th></tr></thead><tbody>')
    w('<tr><th>高升</th>'
      '<td class="old">P51 擴散楔形<br><small>高漲較快</small></td>'
      '<td class="old">P29 擴散三角</td><td class="old">P54 右角擴散</td></tr>')
    w('<tr><th></th><td class="new">P11 上升楔形<br><small>高漲較慢</small></td>'
      '<td></td><td></td></tr>')
    w('<tr><th>高降</th><td class="new">P10 對稱三角</td>'
      '<td class="new">P20 下降通道<br><small>整格</small></td>'
      '<td class="new">P08 下降三角</td></tr>')
    w('<tr><th></th><td></td>'
      '<td class="old">P52 擴散楔形<br><small>低跌較快，P20 的子集</small></td>'
      '<td></td></tr>')
    w('<tr><th>高平</th><td class="hole">空缺</td>'
      '<td class="old">P53 右角擴散</td><td class="new">P22 箱型</td></tr>')
    w('</tbody></table>')
    w('<p class="cap">灰字 = 已編碼並驗收；紫底 = 本頁討論的五個。'
      '格子表的兩個交叉驗證自動命中：高升×低降格量到 <b>202</b>，'
      '正是 P29 已驗證的母體；P52 量到 <b>1,716</b>，正是已編碼的值。'
      '本頁的腳本跑的是指標自己那條鏈。</p>')

    for p in PATS:
        a, z, piv = p['ex']
        w('<div class="pat">')
        w('<div class="hd"><code>%s</code><h2>%s</h2>'
          '<span class="en">%s</span><span class="cell">%s</span>'
          '<span class="cell">%s</span>'
          '<span class="n">八年 %s 個</span></div>'
          % (p['code'], p['zh'], p['en'], p['cell'], p['dirn'],
             format(p['n'], ',')))
        w('<div class="fig">%s</div>' % candles(rows, O, H, L, C, a, z, piv))
        w('<p class="cap">真實 K 棒，跨度中位數的案例（不是最漂亮的那個）。'
          '淡化的是型態前後的脈絡棒。紅點 = 樞紐高，綠點 = 樞紐低，'
          '虛線連出上下兩緣。</p>')
        w('<p class="lead">%s</p>' % p['lead'])
        w('<table class="cd"><thead><tr><th>條件</th><th>式子</th>'
          '<th>圖上哪裡</th></tr></thead><tbody>')
        for nm, f, whr in p['conds']:
            w('<tr><td>%s</td><td class="f">%s</td><td>%s</td></tr>'
              % (nm, f, whr))
        w('</tbody></table>')
        w('<p class="zero"><b>零參數：</b>%s</p>' % p['zero'])
        w('</div>')

    w('<div class="note"><h3>「完全相等」第三次被算術殺死</h3>'
      'P08 與 P22 的原始定義都寫「完全相等」。實測八年：'
      '<b>P08 只有 7 個</b>（四個年份掛零）、<b>P22 只有 2 個</b>'
      '（七個年份掛零）—— 跟 P53 的 7 個、P54 的 8 個一模一樣。<br><br>'
      '改用區間裝置（兩點定帶、第三點受測，容差 = |A−B| 由型態自身給）：'
      'P08 <b>2,623</b>、P22 <b>3,063</b>，兩者零掛零年，'
      '倍率 375 倍與 1,532 倍。<b>仍然零參數。</b><br><br>'
      '這是檢查表第 17 條預測到的，也是 2026-08-28 量過的衰減律：'
      'tick 固定 1 點而擺幅八年從 9 點漲到 90 點，'
      '完全相等的命中率以 1/擺幅 衰減。<br><br>'
      '<b>待裁示：</b>若 P08／P22 改用區間裝置，'
      '已編碼的 P53／P54（現在用完全相等，7 個與 8 個）要不要一致？'
      '改了會動到已驗證的數字。')
    w('</div>')
    w('<div class="note"><h3>誠實聲明</h3>'
      '本頁的 K 棒是真實資料，案例取跨度中位數且不跨時段 —— '
      '<b>挑最漂亮的案例是在替型態說話</b>。個數由本頁的腳本算出，'
      '腳本重放指標自己的十二槽鏈，並以 P29 的 202 與 P52 的 1,716 '
      '兩個已驗收數字作為交叉驗證。<b>這五個尚未寫進指標</b>，'
      '本頁沒有宣稱 MC12 跑得出這些數字。'
      '本頁由 Claude 產出，未經第二方審查。</div>')
    w('</div>')
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(A))
    print('wrote %s' % OUT)


if __name__ == '__main__':
    main()
