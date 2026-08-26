# -*- coding: utf-8 -*-
"""P49 / P50 diagram -- same visual language as the P29 page, real bars.

The two shapes are identical. Everything that separates them sits in the hour
BEFORE the pattern starts, so the page has to show that hour, not just the
megaphone. Both charts are real TXF1 5-minute bars, not sketches.

Input : s16s_p49_example.json  (written by the selector; real OHLC)
Output: docs/research/S16S_P49_P50_diagram.html
"""
import io, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 's16s_p49_example.json')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_P49_P50_diagram.html'))

W, HH = 1040, 400
PAD_L, PAD_R, PAD_T, PAD_B = 58, 150, 30, 46
LB = 12

CSS = """
:root{
  --ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
  --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
  --up:#c8302e;--dn:#17795e;
  --ph:#0f9d76;--pl:#d97528;--m7:#b8860b;--map:#7a5cc4;--midc:#8a93a3;
  --zone:rgba(184,134,11,.085);
  --serif:'Noto Serif TC',Georgia,'Songti TC',serif;
  --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
  --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
  --up:#e8564e;--dn:#3ec08d;
  --ph:#3ecfa0;--pl:#f0a04b;--m7:#e8b93c;--map:#a98ce8;--midc:#79828f;
  --zone:rgba(232,185,60,.11);
}}
:root[data-theme="dark"]{
  --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
  --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
  --up:#e8564e;--dn:#3ec08d;
  --ph:#3ecfa0;--pl:#f0a04b;--m7:#e8b93c;--map:#a98ce8;--midc:#79828f;
  --zone:rgba(232,185,60,.11);
}
:root[data-theme="light"]{
  --ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
  --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
  --up:#c8302e;--dn:#17795e;
  --ph:#0f9d76;--pl:#d97528;--m7:#b8860b;--map:#7a5cc4;--midc:#8a93a3;
  --zone:rgba(184,134,11,.085);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:44px 20px 84px;
  display:flex;flex-direction:column;gap:34px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.12em;color:var(--ink3)}
h1{font-family:var(--serif);font-weight:700;margin:0;
  font-size:clamp(26px,4vw,38px);letter-spacing:-.01em}
h2{font-family:var(--serif);font-weight:700;margin:0 0 14px;font-size:21px}
h3{font-weight:600;margin:0 0 6px;font-size:15px}
.lead{color:var(--ink2);font-size:16px;margin:6px 0 0;max-width:74ch}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:24px 26px}
.chartbox{overflow-x:auto}
svg{display:block;max-width:100%;height:auto}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line2);padding:8px 10px;text-align:left}
th{color:var(--ink3);font-weight:600;font-size:12px;letter-spacing:.04em}
td.n,th.n{text-align:right;font-family:var(--mono);
  font-variant-numeric:tabular-nums}
code{font-family:var(--mono);font-size:13px;background:var(--line2);
  padding:1px 5px;border-radius:4px}
pre{font-family:var(--mono);font-size:13px;background:var(--line2);
  padding:14px 16px;border-radius:8px;overflow-x:auto;margin:0}
.note{color:var(--ink2);font-size:14px;margin:10px 0 0}
.tag{display:inline-block;font-family:var(--mono);font-size:11px;
  padding:2px 8px;border-radius:999px;border:1px solid var(--line);
  color:var(--ink2);margin-right:6px}
.ok{color:var(--dn);font-weight:600}
.warn{color:var(--up);font-weight:600}
.k{stroke-width:1.1}
.kb{stroke-width:5.2}
.up{stroke:var(--up)}
.dn{stroke:var(--dn)}
.tl{stroke:var(--ph);stroke-width:1.3;stroke-dasharray:6 4;fill:none}
.pvH{fill:var(--ph)}
.pvL{fill:var(--pl)}
.pvr{fill:none;stroke:var(--card);stroke-width:2}
.ax{stroke:var(--line);stroke-width:1}
.gl{stroke:var(--line2);stroke-width:1}
.lbl{font-family:var(--mono);font-size:11px;fill:var(--ink3)}
.lblb{font-family:var(--sans);font-size:13px;fill:var(--ink);font-weight:600}
.lbl2{font-family:var(--sans);font-size:12px;fill:var(--ink2)}
.zone{fill:var(--zone);stroke:var(--m7);stroke-width:.8;stroke-dasharray:5 4}
.m7{stroke:var(--m7);stroke-width:2.4;fill:none}
.ah{fill:var(--m7)}
"""

DEFS = ('<defs><marker id="am" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto">'
        '<path d="M0,1 L9,5 L0,9" class="ah"/></marker></defs>')


def chart(ex, title, sub, verdict):
    bars = ex['bars']
    meta = ex['meta']
    n = len(bars)
    lo = min(b['l'] for b in bars)
    hi = max(b['h'] for b in bars)
    pad = (hi - lo) * .10
    lo -= pad
    hi += pad

    def X(k):
        return PAD_L + (W - PAD_L - PAD_R) * (k + .5) / float(n)

    def Y(p):
        return PAD_T + (HH - PAD_T - PAD_B) * (hi - p) / float(hi - lo)

    bw = max(2.4, (W - PAD_L - PAD_R) / float(n) * .56)
    o = [DEFS]

    # price grid
    step = 10 ** len(str(int((hi - lo) / 5))) if hi - lo > 50 else 10
    step = max(step, 5)
    g = int(lo / step) * step
    while g < hi:
        if g > lo:
            o.append('<line class="gl" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (PAD_L, Y(g), W - PAD_R, Y(g)))
            o.append('<text class="lbl" x="%.1f" y="%.1f" text-anchor="end">%d</text>'
                     % (PAD_L - 8, Y(g) + 4, g))
        g += step

    # the 12-bar prior window
    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>'
             % (X(0) - bw, PAD_T, X(LB) - X(0) + bw, HH - PAD_T - PAD_B))
    o.append('<text class="lbl" x="%.1f" y="%.1f">12 根回看窗 = 1 小時</text>'
             % (X(0) - bw + 6, PAD_T + 16))

    # M7 arrow across the window
    o.append('<line class="m7" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
             'marker-end="url(#am)"/>'
             % (X(0), Y(bars[0]['c']), X(LB) - 4, Y(bars[LB]['c'])))

    # the two diverging trendlines through the outer pivots
    idx = {b['i']: k for k, b in enumerate(bars)}
    hs, ls = meta['hs'], meta['ls']
    o.append('<line class="tl" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (X(idx[hs[0]]), Y(bars[idx[hs[0]]]['h']),
                X(idx[hs[2]]), Y(bars[idx[hs[2]]]['h'])))
    o.append('<line class="tl" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (X(idx[ls[0]]), Y(bars[idx[ls[0]]]['l']),
                X(idx[ls[2]]), Y(bars[idx[ls[2]]]['l'])))

    # candles
    for k, b in enumerate(bars):
        cls = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(k)
        o.append('<line class="k %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, x, Y(b['h']), x, Y(b['l'])))
        o.append('<line class="kb %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke-linecap="butt"/>'
                 % (cls, x, Y(max(b['o'], b['c'])), x, Y(min(b['o'], b['c']))))

    # pivots
    for j, i in enumerate(hs):
        k = idx[i]
        o.append('<circle class="pvr" cx="%.1f" cy="%.1f" r="5.6"/>' % (X(k), Y(bars[k]['h'])))
        o.append('<circle class="pvH" cx="%.1f" cy="%.1f" r="4.2"/>' % (X(k), Y(bars[k]['h'])))
        o.append('<text class="lbl" x="%.1f" y="%.1f" text-anchor="middle">PH%d</text>'
                 % (X(k), Y(bars[k]['h']) - 12, 3 - j))
    for j, i in enumerate(ls):
        k = idx[i]
        o.append('<circle class="pvr" cx="%.1f" cy="%.1f" r="5.6"/>' % (X(k), Y(bars[k]['l'])))
        o.append('<circle class="pvL" cx="%.1f" cy="%.1f" r="4.2"/>' % (X(k), Y(bars[k]['l'])))
        o.append('<text class="lbl" x="%.1f" y="%.1f" text-anchor="middle">PL%d</text>'
                 % (X(k), Y(bars[k]['l']) + 20, 3 - j))

    # right-hand caption
    rx = W - PAD_R + 14
    o.append('<text class="lblb" x="%.1f" y="%.1f">%s</text>' % (rx, PAD_T + 34, title))
    for j, line in enumerate(sub):
        o.append('<text class="lbl2" x="%.1f" y="%.1f">%s</text>'
                 % (rx, PAD_T + 56 + j * 19, line))
    o.append('<text class="lblb" x="%.1f" y="%.1f">%s</text>'
             % (rx, PAD_T + 62 + len(sub) * 19, verdict))

    # time axis
    o.append('<line class="ax" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
             % (PAD_L, HH - PAD_B, W - PAD_R, HH - PAD_B))
    for k in sorted({0, LB, idx[max(meta['hs'][2], meta['ls'][2])], n - 1}):
        o.append('<text class="lbl" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                 % (X(k), HH - PAD_B + 20, bars[k]['t'][9:]))
    o.append('<text class="lbl" x="%.1f" y="%.1f">%s</text>'
             % (PAD_L, HH - 8, bars[0]['t'][:4] + '-' + bars[0]['t'][4:6] + '-' + bars[0]['t'][6:8]))

    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" role="img">'
            '<title>%s</title>%s</svg>' % (W, HH, W, HH, title, ''.join(o)))


def main():
    ex = json.load(io.open(SRC, encoding='utf-8'))
    p49, p50 = ex['P49'], ex['P50']

    d49 = p49['bars'][LB]['c'] - p49['bars'][0]['c']
    d50 = p50['bars'][LB]['c'] - p50['bars'][0]['c']

    c49 = chart(p49, 'P49 擴散頂',
                ['喇叭形之前的一小時', '收盤 %.0f → %.0f' % (p49['bars'][0]['c'], p49['bars'][LB]['c']),
                 '%+.0f 點，往上' % d49, '',
                 '母體 112 個 · 55.4%', '年均 14.0 · 夜盤 96',
                 '', '案例 2026-07-02 夜盤',
                 'S1 穩健度 %d/6' % p49['meta']['s1']],
                '→ 前段上漲 = 擴散頂')
    c50 = chart(p50, 'P50 擴散底',
                ['喇叭形之前的一小時', '收盤 %.0f → %.0f' % (p50['bars'][0]['c'], p50['bars'][LB]['c']),
                 '%+.0f 點，往下' % d50, '',
                 '母體 90 個 · 44.6%', '年均 11.2 · 夜盤 77',
                 '', '案例 2021-10-01 日盤',
                 'S1 穩健度 %d/6' % p50['meta']['s1']],
                '→ 前段下跌 = 擴散底')

    html = """<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>P49 / P50 規格示意圖</title><style>%s</style>
<div class="wrap">

<div class="top">
  <div class="eyebrow">S16_S · 圖形型態 · 逐一邏輯規劃</div>
  <h1>P49 擴散頂 ／ P50 擴散底</h1>
  <p class="lead">兩個型態的喇叭形<b>一模一樣</b>。六個樞紐的條件、趨勢線、突破確認、有效期
  全部繼承 P29，一行都不改。唯一的差別在型態出現<b>之前那一小時</b>——價格是漲是跌。
  下面兩張都是真實的 TXF1 5 分 K，不是示意草圖。</p>
</div>

<div class="card">
  <h2>一、真實案例 — P49 擴散頂</h2>
  <div class="chartbox">%s</div>
  <p class="note">橘色框是回看窗，橘色箭頭是 M7。綠點為樞紐高（PH3→PH1 一路墊高），
  橘點為樞紐低（PL3→PL1 一路下移），兩條虛線往外張開。
  <b>回看窗那一小時漲了 %+.0f 點，所以是頂不是底。</b></p>
</div>

<div class="card">
  <h2>二、真實案例 — P50 擴散底</h2>
  <div class="chartbox">%s</div>
  <p class="note">同樣六個樞紐、同樣兩條張開的線。<b>差別只有回看窗那一小時跌了 %.0f 點。</b>
  注意這個例子的開口只有 %.0f 點，而 P49 那個是 %.0f 點——
  <b>定義不含尺度門檻，兩者被當成同一件事</b>（裁示 1：樞紐不加 ATR 門檻的直接後果）。</p>
</div>

<div class="card">
  <h2>三、M7 判別器 — 唯一的新東西</h2>
  <pre>M7 = 第一個樞紐往前 12 根（1 小時）的走勢

      往上  →  P49 擴散頂（空）
      往下  →  P50 擴散底（多）</pre>
  <div class="grid2" style="margin-top:16px">
    <div>
      <h3>裁示 12：採用最小平方斜率</h3>
      <table>
        <tr><th>量法</th><th class="n">P49</th><th class="n">P50</th><th class="n">持平</th></tr>
        <tr><td>端點差</td><td class="n">105</td><td class="n">93</td><td class="n warn">4</td></tr>
        <tr><td><b>12 根最小平方斜率</b></td><td class="n"><b>112</b></td>
            <td class="n"><b>90</b></td><td class="n ok">0</td></tr>
      </table>
      <p class="note">兩法方向一致 <b>89.6%%</b>，差的 21 個全部落在絕對值最小的一群。</p>
    </div>
    <div>
      <h3>為什麼是 12 根</h3>
      <p class="note">用戶裁示：以一小時為前置觀察區間。<b>它是常數不是掃描結果</b>，
      與 <code>Tail_DayNoEntry_From = 1335</code> 同類（交易理由，非最佳化）。
      <b>必須釘死，永不進最佳化掃描。</b></p>
      <p class="note">巧合值得記一筆：P29 自己的跨度中位數是 <b>12 根</b>，
      前段窗與型態本身等長。</p>
    </div>
  </div>
</div>

<div class="card">
  <h2>四、裁示 12 的依據 — 穩定性，不是論述</h2>
  <p class="note">M7 是分類器。同一個型態因為窗口挪一根就換邊，代表它分不乾淨。
  下表每格是 202 個型態中方向翻轉的個數。</p>
  <table>
    <tr><th>擾動</th><th class="n">端點差</th><th class="n">最小平方斜率</th><th class="n">差異</th></tr>
    <tr><td>窗長 12 → 10</td><td class="n">31</td><td class="n">22</td><td class="n ok">−9</td></tr>
    <tr><td>窗長 12 → 11</td><td class="n">20</td><td class="n">9</td><td class="n ok">−11</td></tr>
    <tr><td>窗長 12 → 13</td><td class="n">17</td><td class="n">8</td><td class="n ok">−9</td></tr>
    <tr><td>窗長 12 → 14</td><td class="n">26</td><td class="n">18</td><td class="n ok">−8</td></tr>
    <tr><td><b>窗長小計</b></td><td class="n"><b>11.6%%</b></td>
        <td class="n"><b>7.1%%</b></td><td class="n ok"><b>−39%%</b></td></tr>
    <tr><td>起點 −1 根</td><td class="n">19</td><td class="n">13</td><td class="n ok">−6</td></tr>
    <tr><td>起點 +1 根</td><td class="n">22</td><td class="n">13</td><td class="n ok">−9</td></tr>
    <tr><td><b>起點小計</b></td><td class="n"><b>10.1%%</b></td>
        <td class="n"><b>6.4%%</b></td><td class="n ok"><b>−37%%</b></td></tr>
    <tr><td><b>恰為 0 的型態數</b></td><td class="n warn"><b>4</b></td>
        <td class="n ok"><b>0</b></td><td class="n">−4</td></tr>
    <tr><td>最小非零值</td><td class="n">1.0000 點</td>
        <td class="n">0.0055 點／根</td><td class="n">解析度高 182 倍</td></tr>
  </table>
  <p class="note"><b>三個決定性理由。</b>
  一、「起點挪一根」在實作上真的會發生——樞紐在第 <code>i</code> 根成立、<code>i+1</code> 才確認，
  端點差在這個擾動下翻掉 10.1%%。
  二、端點差有 4 個恰為 0，需要一條沒有推導支撐的平手規則；斜率 0 個平手。
  三、解析度差 182 倍。
  <span class="warn">更正：先前推薦斜率的理由是「用滿 12 根比較抗雜訊」，那是論述不是證據。上表才是。</span></p>
</div>

<div class="card">
  <h2>五、三個檢查 — 都過了</h2>
  <table>
    <tr><th>檢查</th><th>結果</th><th>判讀</th></tr>
    <tr><td>被「排列」污染？</td><td class="n">57.7%% vs 53.1%%，差 4.6pp</td>
        <td><span class="ok">過</span> 雜訊本身 14.4pp，遠大於它</td></tr>
    <tr><td>與 M2 重複？</td><td class="n">同號 55.4%%</td>
        <td><span class="ok">過</span> 獨立為 50%%，兩者量不同東西</td></tr>
    <tr><td>分派自帶偏差？</td><td class="n">55.4%% vs 隨機 52.5%%</td>
        <td><span class="ok">過</span> 落在隨機範圍 47.0–61.4%% 內</td></tr>
  </table>
  <p class="note">第三個最重要：<b>P29 出現前的走勢，和隨機挑一個時點沒有分別。</b>
  代表 M7 是乾淨的分類器——它把母體切開，但沒有偷偷塞進方向偏誤。
  對照組是昨天被推翻的 §3 三向細分，那個的排列差距是 18.9–32pp。</p>
</div>

<div class="card">
  <h2>六、母體 — 2026-08-26 重掃</h2>
  <div class="grid2">
    <div>
      <h3>跨時段裁示讓母體 +17.4%%</h3>
      <table>
        <tr><th>版本</th><th class="n">個數</th></tr>
        <tr><td>只准同時段（舊）</td><td class="n">172</td></tr>
        <tr><td><b>允許跨時段（現行）</b></td><td class="n"><b>202</b></td></tr>
      </table>
      <p class="note">舊碼把 K 棒結構的「同時段」限制誤套到圖形型態上。
      多出的 30 個<b>全部只跨 1 個邊界</b>，起始集中在 <code>04</code>（20 個）、
      <code>03</code>、<code>12</code>、<code>13</code>——正是時段末端。
      起始小時涵蓋 <b>17 → 19</b> 個。</p>
    </div>
    <div>
      <h3>開口大小 — 62 倍差距</h3>
      <table>
        <tr><th></th><th class="n">最小</th><th class="n">中位</th><th class="n">最大</th></tr>
        <tr><td>點數</td><td class="n">9</td><td class="n">60</td><td class="n">559</td></tr>
        <tr><td>佔價</td><td class="n">0.048%%</td><td class="n">0.302%%</td><td class="n">3.127%%</td></tr>
      </table>
      <p class="note">37.1%% 的開口不到 50 點。<b>定義不含尺度門檻</b>，
      9 點與 559 點被當成同一件事——這是裁示 1（樞紐不加 ATR 門檻）的後果，不是缺陷。</p>
      <p class="note"><b>裁示 13：記成屬性，不設門檻</b>（與 S1 同一套哲學）。
      <code>v_P29_Open</code> 與 <code>v_P29_OpenPct</code>，自由參數 0。
      任何門檻現在都只能從這 202 個裡挑，那就是對結果變數選擇。</p>
    </div>
  </div>
</div>

<div class="card">
  <h2>七、繼承自 P29 的七段 — 一行都不改</h2>
  <table>
    <tr><th>段</th><th>內容</th><th>P49／P50</th></tr>
    <tr><td>§1 樞紐</td><td>純分形，i-1/i/i+1 同時段</td><td class="ok">相同</td></tr>
    <tr><td>§2 成立</td><td>對稱 3+3 ＋ 交替 ＋ 低點在高點下方</td><td class="ok">相同</td></tr>
    <tr><td>§3 方向</td><td>M2 通道漂移 ＋ 排列六格</td><td class="ok">相同</td></tr>
    <tr><td>§4 地圖</td><td>事前價位地圖</td><td class="ok">相同</td></tr>
    <tr><td>§5 突破</td><td>E1 外推 ＋ 收盤單根</td><td class="ok">相同</td></tr>
    <tr><td>§6 有效期</td><td>＝ 形成所花的根數</td><td class="ok">相同</td></tr>
    <tr><td>§7 S1</td><td>0-6 穩健度分數，不設門檻</td><td class="ok">相同</td></tr>
    <tr><td><b>M7</b></td><td><b>前 12 根走勢</b></td><td class="warn">新增</td></tr>
  </table>
  <p class="note"><span class="tag">自由參數</span>P29 七段合計 0，M7 帶入一個釘死的常數 12。
  <b>M7 專供 P49／P50，不可用於 §3</b>——用了就與 P49／P50 重複計數。</p>
</div>

<div class="card">
  <h2>八、生命週期 — 型態是狀態，不是訊號</h2>
  <p class="note">2026-08-26 裁示 20：底層只維護狀態，永不下單。中層進場與上層二次進場
  都是<b>讀者</b>。假突破與假跌破都回到有效，型態不因發出訊號而消耗。</p>
  <pre>有效  --收盤突破上緣或跌破下緣-->  測試中
測試中  --下一個樞紐時已回到型態內-->  有效        假突破 25 ／ 假跌破 11
測試中  --下一個樞紐時仍在型態外-->    失效
有效  --存活根數 > 形成根數-->        失效</pre>
  <div class="grid2" style="margin-top:16px">
    <div>
      <h3>結局分布（n = 202）</h3>
      <table>
        <tr><th>結局</th><th class="n">個數</th><th class="n">佔比</th></tr>
        <tr><td><b>有效期屆滿</b></td><td class="n"><b>138</b></td><td class="n"><b>68.3%%</b></td></tr>
        <tr><td>價格破壞（三根紅K）</td><td class="n">21</td><td class="n">10.4%%</td></tr>
        <tr><td>真跌破（三根黑K）</td><td class="n">16</td><td class="n">7.9%%</td></tr>
        <tr><td>真跌破（樞紐確認）</td><td class="n">15</td><td class="n">7.4%%</td></tr>
        <tr><td>真突破（樞紐確認）</td><td class="n">12</td><td class="n">5.9%%</td></tr>
      </table>
      <p class="note">型態存活中位 <b>10 根</b>。空方訊號 <b>47 次</b>，
      其中三黑 16 ／ 待樞紐確認 31（裁示 19 的兩級強度）。</p>
    </div>
    <div>
      <h3>裁示 18：長實體條件被實測否決</h3>
      <table>
        <tr><th>版本</th><th class="n">向上突破符合</th><th class="n">向下跌破符合</th></tr>
        <tr><td><b>純紅黑（採用）</b></td><td class="n"><b>45.5%%</b></td><td class="n"><b>40.0%%</b></td></tr>
        <tr><td>加 Body >= 50%% 區間</td><td class="n warn">4.5%%</td><td class="n warn">5.0%%</td></tr>
      </table>
      <p class="note">加上長實體條件，44 個向上突破裡只有 <b>2 個</b>會走這條路
      —— <span class="warn">那條規則等於不存在</span>。</p>
      <p class="note"><b>「價格破壞」也被重新定義。</b>舊版是「收盤越過最高樞紐」，
      但擴散的定義就是高點不斷創高，那條規則把「正在擴散」判成「被破壞」，
      且會讓假突破存活路徑變成 <b>0 次的死碼</b>。改成「三根同向」之後，
      觸發率從 41.6%% 降到 10.4%%，假突破路徑活了過來。</p>
    </div>
  </div>
</div>

<div class="card">
  <h2>九、指標已寫好</h2>
  <pre>strategies/research/S16_MACrossShort/indicators/IND_S16S_P29.pla   420 行</pre>
  <table>
    <tr><th>檢查</th><th>結果</th></tr>
    <tr><td>Rule #15 ASCII</td><td class="ok">73 / 73 PASS</td></tr>
    <tr><td>語意驗證</td><td class="ok">FAIL 0 ／ WARN 0 ／ PASS 18</td></tr>
    <tr><td>前瞻索引 [0]</td><td class="ok">無</td></tr>
    <tr><td>下單語句</td><td class="ok">0 筆（裁示 20：型態層不下單）</td></tr>
    <tr><td>MC12 編譯</td><td class="warn">尚未執行</td></tr>
    <tr><td>逐筆對照 Python 202 筆</td><td class="warn">尚未執行</td></tr>
  </table>
  <p class="note">指標把樞紐價格、棒號與 M7 <b>鎖存進陣列</b>，型態判定是純算術，
  完全不回看 —— MaxBarsBack 只需覆蓋 M7 的 13 根收盤。
  <code>Print</code> 每個事件一行，供 diff 對照。</p>
  <p class="note">過程中修好驗證器四個盲點：陣列下標被誤判為前瞻索引、
  陣列元素指派不算寫入、<code>Plot3-9</code> 與 <code>NoPlot</code> 不在內建表、
  策略專屬規範（Rule #11／#12／IOG／<code>v_Prev_MP</code>）被套到指標上。
  <b>修完後既有策略仍是 FAIL 0 ／ WARN 0 ／ PASS 23，無回歸。</b></p>
</div>

<div class="card">
  <h2>十、還沒做的事</h2>
  <table>
    <tr><th>項目</th><th>狀態</th></tr>
    <tr><td>M7 量法（裁示 12）</td><td class="ok">已定：12 根最小平方斜率</td></tr>
    <tr><td>開口大小（裁示 13）</td><td class="ok">已定：記成屬性，不設門檻</td></tr>
    <tr><td>S1 雙尺度在 202 母體上重跑</td><td class="warn">舊數字跑在 172 上，尚未重測</td></tr>
    <tr><td>指標 IND_S16S_P29.pla</td><td class="ok">已寫，驗證全過</td></tr>
    <tr><td>MC12 編譯 ＋ 逐筆對照 202 筆</td><td class="warn">尚未執行</td></tr>
    <tr><td>寫進 .pla</td><td class="warn">一行都沒寫</td></tr>
    <tr><td>報酬檢定</td><td class="warn">從未進行，且不應在用戶同意前進行</td></tr>
    <tr><td>P51–P54（§2 要重寫）</td><td class="warn">未規劃</td></tr>
    <tr><td>P29-W2 粗尺度變體</td><td class="warn">未規劃</td></tr>
  </table>
</div>

<div class="card">
  <div class="eyebrow">資料來源</div>
  <p class="note">TXF1 1 分鐘.txt（106,676,935 bytes，md5 db35ecb7…）→ 5 分 K <b>421,513 根</b>，
  2019-01-02 08:50 ~ 2026-08-22 05:00。日盤 110,867 ／ 夜盤 310,646 ／ 不屬任一時段 0。
  逐年 2019:54,858 到 2026:34,921，涵蓋 21 個小時。
  普查腳本無損益欄。本頁由 <code>s16s_p49_make_diagram.py</code> 產生。</p>
</div>

</div>""" % (CSS, c49, d49, c50, abs(d50),
             p50['bars'][-1]['h'] - p50['bars'][-1]['l'],
             max(b['h'] for b in p49['bars']) - min(b['l'] for b in p49['bars']))

    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
    print('wrote %s  %d KB' % (OUT, len(html.encode('utf-8')) // 1024))


if __name__ == '__main__':
    main()
