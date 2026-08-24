# -*- coding: utf-8 -*-
"""33 K-bar patterns -> one HTML reference sheet.

The candles are drawn from the UNIT TEST FIXTURES, so every drawing is a
shape the shipped .pla actually fires on -- not an illustration I invented.
"""
import io, os, sys
sys.path.insert(0, os.path.abspath('scripts/research'))
from s16s_kbar_unittest import FIX
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')

# code -> (chinese, english, occurrences, times seen on a real entry signal bar)
M = {
 1: ('空頭吞噬', 'Bearish Engulfing', 27249, 40),
 2: ('空頭孕線', 'Bearish Harami', 28880, 1),
 3: ('空頭十字孕線', 'Bearish Harami Cross', 6091, 0),
 4: ('鑷子頂', 'Tweezers Top', 15085, 6),
 5: ('高價配', 'Matching High', 1879, 0),
 6: ('三隻烏鴉', 'Three Black Crows', 567, 2),
 7: ('三內部下跌', 'Three Inside Down', 12469, 12),
 8: ('三外部下跌', 'Three Outside Down', 11334, 19),
 9: ('三胎鴉', 'Identical Three Crows', 1165, 5),
 10: ('大敵當前', 'Advance Block', 2100, 0),
 11: ('步步為營', 'Deliberation', 2991, 0),
 12: ('下降三法', 'Falling Three Methods', 5, 0),
 13: ('三線打擊（跌）', 'Bearish Three Line Strike', 177, 2),
 14: ('空頭 Hikkake', 'Bearish Hikkake', 6425, 4),
 15: ('下降之鷹', 'Descending Hawk', 3598, 0),
 16: ('多頭吞噬', 'Bullish Engulfing', 27760, 0),
 17: ('多頭孕線', 'Bullish Harami', 28018, 0),
 18: ('多頭十字孕線', 'Bullish Harami Cross', 5747, 0),
 19: ('鑷子底', 'Tweezers Bottom', 14275, 0),
 20: ('低價配', 'Matching Low', 1837, 0),
 21: ('三白兵', 'Three White Soldiers', 628, 0),
 22: ('三內部上漲', 'Three Inside Up', 12470, 0),
 23: ('三外部上漲', 'Three Outside Up', 12113, 0),
 24: ('南方三星', 'Three Stars in the South', 9, 0),
 25: ('獨特三河床', 'Unique Three River Bottom', 1, 0),
 26: ('上升三法', 'Rising Three Methods', 12, 0),
 27: ('梯底', 'Ladder Bottom', 11, 0),
 28: ('三線打擊（漲）', 'Bullish Three Line Strike', 189, 0),
 29: ('內含線', 'Inside Bar', 87942, 1),
 30: ('外包線', 'Outside Bar', 65039, 26),
 31: ('多頭 Hikkake', 'Bullish Hikkake', 4132, 0),
 32: ('家鴿', 'Homing Pigeon', 3509, 0),
 33: ('三明治', 'Stick Sandwich', 3341, 0),
}
BULL3 = set(range(21, 29)) | {31}
NEWC = {31, 32, 33}
TOTALBARS = 421513


def svg(bars):
    """bars: (O,H,L,C) oldest -> newest."""
    lo = min(b[2] for b in bars)
    hi = max(b[1] for b in bars)
    rng = max(hi - lo, 1e-9)
    n = len(bars)
    W, H, PAD = 30.0, 108.0, 9.0

    def y(v):
        return PAD + (hi - v) / rng * (H - 2 * PAD)

    out = []
    for i, (o, h, l, c) in enumerate(bars):
        x = i * W + W / 2.0
        cls = 'up' if c >= o else 'dn'
        bt, bb = y(max(o, c)), y(min(o, c))
        if bb - bt < 1.6:
            m = (bt + bb) / 2.0
            bt, bb = m - 0.8, m + 0.8
        out.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                   % (cls, x, y(h), x, y(l)))
        out.append('<rect class="bd %s" x="%.1f" y="%.1f" width="12" height="%.1f" rx="1"/>'
                   % (cls, x - 6, bt, bb - bt))
    return ('<svg viewBox="0 0 %.0f %.0f" preserveAspectRatio="xMidYMid meet" '
            'role="img" aria-label="%d bars">%s</svg>'
            % (n * W, H, n, ''.join(out)))


FX = dict((c, b) for c, _, b, _ in FIX)


def card(code):
    zh, en, occ, gate = M[code]
    bars = FX[code]
    t = []
    if code in NEWC:
        t.append('<span class="tag new">2026-08-24 新增</span>')
    if code in BULL3:
        t.append('<span class="tag exit">出場旗標</span>')
    if occ <= 20:
        t.append('<span class="tag rare">近乎不出現</span>')
    if gate > 0:
        t.append('<span class="tag gate">進場棒 %d 次</span>' % gate)
    return ('<figure class="c"><div class="chart">%s</div><figcaption>'
            '<div class="hd"><span class="no">%d</span><span class="zh">%s</span>'
            '<span class="bars">%d 根</span></div>'
            '<div class="en">%s</div>'
            '<div class="occ"><b>%s</b> 次 <span class="pc">%.2f%%</span></div>'
            '<div class="tags">%s</div></figcaption></figure>'
            % (svg(bars), code, zh, len(bars), en,
               format(occ, ','), 100.0 * occ / TOTALBARS, ''.join(t)))


SEC = [
 ('空方結構 — 支持做空', '代碼 1-15',
  '進場時這 15 種是「順風」。但實測顯示'
  '它們<b>無法</b>改善進場：n=4,422 上 PF 0.52，'
  '對照斜率閘門的 1.89。', list(range(1, 16))),
 ('多方結構 — 否決做空', '代碼 16-28、31-33',
  '進場那根若帶這 16 種任一種，<b>一律不下單</b>'
  '（R1，常駐、無開關）。其中 3 根以上的 9 種'
  '另外舉旗給出場規則用。', list(range(16, 29)) + [31, 32, 33]),
 ('中性', '代碼 29-30',
  '只描述兩根 K 棒的包含關係，不帶方向，'
  '<b>不參與</b>任何進出場判斷。', [29, 30]),
]

CSS = """
:root{
  --ink:#191713;--ink2:#4d463c;--ink3:#7d7466;
  --bg:#f7f4ee;--card:#fffdf9;--line:#e2dacb;--line2:#efe8da;
  --up:#c02a2a;--dn:#1d7a52;
  --tnew:#8a6a1f;--texit:#1d5c8a;--trare:#8a4a2a;--tgate:#5a3a7a;
  --serif:'Noto Serif TC',Georgia,'Songti TC',serif;
  --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#f0ebe1;--ink2:#bdb4a4;--ink3:#8a8174;
  --bg:#14120f;--card:#1d1a16;--line:#332e26;--line2:#26221c;
  --up:#e8564e;--dn:#3fbb84;
  --tnew:#d6b055;--texit:#6fb2e0;--trare:#e08a5a;--tgate:#b28ad6;
}}
:root[data-theme="dark"]{
  --ink:#f0ebe1;--ink2:#bdb4a4;--ink3:#8a8174;
  --bg:#14120f;--card:#1d1a16;--line:#332e26;--line2:#26221c;
  --up:#e8564e;--dn:#3fbb84;
  --tnew:#d6b055;--texit:#6fb2e0;--trare:#e08a5a;--tgate:#b28ad6;
}
:root[data-theme="light"]{
  --ink:#191713;--ink2:#4d463c;--ink3:#7d7466;
  --bg:#f7f4ee;--card:#fffdf9;--line:#e2dacb;--line2:#efe8da;
  --up:#c02a2a;--dn:#1d7a52;
  --tnew:#8a6a1f;--texit:#1d5c8a;--trare:#8a4a2a;--tgate:#5a3a7a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:52px 22px 88px;
  display:flex;flex-direction:column;gap:48px}
header.top{display:flex;flex-direction:column;gap:12px}
h1{font-family:var(--serif);font-weight:700;font-size:clamp(27px,4.3vw,40px);
  margin:0;letter-spacing:-.01em;text-wrap:balance}
.lede{color:var(--ink2);max-width:64ch;margin:0;font-size:15px}
.lede b{color:var(--ink);font-weight:700}
.meta{font-family:var(--mono);font-size:11.5px;color:var(--ink3);
  letter-spacing:.03em;margin:0}
.legend{display:flex;flex-wrap:wrap;gap:9px 20px;padding:13px 17px;
  border:1px solid var(--line);border-radius:3px;background:var(--card);
  font-size:12.5px;color:var(--ink2)}
.legend b{color:var(--ink);font-weight:500}
.sw{display:inline-block;width:9px;height:14px;border-radius:1px;
  vertical-align:-2px;margin-right:5px}
section{display:flex;flex-direction:column;gap:13px}
.sh{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
  border-bottom:2px solid var(--ink);padding-bottom:7px}
.sh h2{font-family:var(--serif);font-size:20px;font-weight:700;margin:0}
.sub{font-family:var(--mono);font-size:11px;color:var(--ink3);letter-spacing:.04em}
.sd{margin:0;color:var(--ink2);font-size:13.5px;max-width:76ch}
.sd b{color:var(--ink);font-weight:700}
.grid{display:grid;gap:13px;grid-template-columns:repeat(auto-fill,minmax(194px,1fr))}
.c{margin:0;background:var(--card);border:1px solid var(--line);border-radius:3px;
  padding:12px;display:flex;flex-direction:column;gap:9px}
.chart{height:108px;display:flex;align-items:center;justify-content:center;
  border-bottom:1px solid var(--line2);padding-bottom:8px}
.chart svg{height:100%;max-width:100%}
.wk{stroke-width:1.4}.wk.up{stroke:var(--up)}.wk.dn{stroke:var(--dn)}
.bd.up{fill:var(--card);stroke:var(--up);stroke-width:1.4}
.bd.dn{fill:var(--dn);stroke:var(--dn);stroke-width:1.4}
figcaption{display:flex;flex-direction:column;gap:3px}
.hd{display:flex;align-items:baseline;gap:6px}
.no{font-family:var(--mono);font-size:11px;color:var(--bg);background:var(--ink3);
  border-radius:2px;padding:1px 5px;font-weight:500}
.zh{font-family:var(--serif);font-weight:700;font-size:14.5px}
.bars{margin-left:auto;font-family:var(--mono);font-size:10.5px;color:var(--ink3)}
.en{font-size:10.5px;color:var(--ink3);font-style:italic;line-height:1.35}
.occ{font-family:var(--mono);font-size:12px;color:var(--ink2);
  font-variant-numeric:tabular-nums}
.occ b{color:var(--ink);font-weight:500}
.pc{color:var(--ink3)}
.tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}
.tag{font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid;
  letter-spacing:.02em;white-space:nowrap}
.tag.new{color:var(--tnew);border-color:var(--tnew)}
.tag.exit{color:var(--texit);border-color:var(--texit)}
.tag.rare{color:var(--trare);border-color:var(--trare)}
.tag.gate{color:var(--tgate);border-color:var(--tgate)}
.foot{border-top:1px solid var(--line);padding-top:18px;color:var(--ink3);
  font-size:12.5px;display:flex;flex-direction:column;gap:9px;max-width:82ch}
.foot b{color:var(--ink2);font-weight:500}
code{font-family:var(--mono);font-size:.9em;color:var(--ink2)}
"""

HEAD = ('<title>S16_S K 棒型態圖鑑</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500'
        '&amp;display=swap" rel="stylesheet">\n<style>%s</style>\n' % CSS)

TOP = ('<header class="top">'
       '<p class="meta">S16_S_MACrossShort v1.26.0 &nbsp;·&nbsp; Build_ID 260826'
       ' &nbsp;·&nbsp; 2026-08-24</p>'
       '<h1>33 種 K 棒型態圖鑑</h1>'
       '<p class="lede">每一張 K 線圖都直接取自'
       '單元測試的 fixture，也就是'
       '<b>實際會讓程式碼觸發的那個形狀</b>'
       '，不是另外畫的示意圖。'
       '出現次數量自 421,513 根 5 分 K'
       '（2019-01-02 ~ 2026-08-22）。'
       '所有判定式<b>零自由參數</b>，'
       '33/33 通過單元測試，'
       '並在一跳擾動下 33/33 失效。</p>'
       '<div class="legend">'
       '<span><span class="sw" style="background:var(--card);border:1.4px solid var(--up)">'
       '</span><b>陽線</b> 收 ≥ 開</span>'
       '<span><span class="sw" style="background:var(--dn)"></span>'
       '<b>陰線</b> 收 &lt; 開</span>'
       '<span><span class="tag exit">出場旗標</span> '
       '<code>v_KB_Bull3</code>，3 根以上多頭結構</span>'
       '<span><span class="tag gate">進場棒</span> '
       '實際進場訊號棒上出現過</span>'
       '<span><span class="tag rare">近乎不出現</span> '
       '全歷史 ≤ 20 次</span>'
       '</div></header>')

FOOT = ('<footer class="foot">'
        '<p><b>為什麼有些型態次數是個位數。</b>'
        '下降三法 5 次、獨特三河床 1 次、'
        '梯底 11 次、上升三法 12 次、南方三星 9 次'
        ' —— 這些是 5 根／3 根的嚴格型態，'
        '在 5 分 K 上本來就極罕見。'
        '它們留在集合裡是為了母體完整，'
        '不是因為有用。</p>'
        '<p><b>為什麼多方 16 種的「進場棒」'
        '全部是 0。</b>那正是 R1 的作用：'
        '進場那根帶多頭結構就不下單。'
        '反過來說，斜率閘門要求該根跌 0.25%，'
        '本來就逼出大黑棒，'
        '多頭型態幾乎不可能同時成立。</p>'
        '<p><b>出場旗標讀的是旗標，不是代碼範圍。</b>'
        '型態辨識是 first-match 串接，'
        '三內部上漲的定義本身包含一個多頭孕線，'
        '會被排在前面的它蓋掉。'
        '若用代碼範圍判斷，上升三法與多頭三線打擊'
        '<b>永遠讀不到</b>。</p>'
        '<p style="color:var(--ink3);font-size:11.5px;padding-top:3px">'
        '資料管線 <code>scripts/research/s16s_bars5.py</code> · '
        '單元測試 <code>scripts/research/s16s_kbar_unittest.py</code> · '
        '普查 <code>scripts/research/s16s_pattern_census.py</code> · '
        '盤點 <code>docs/research/S16S_bullish_catalogue_20260824.md</code></p>'
        '</footer>')

body = []
for title, sub, desc, codes in SEC:
    body.append('<section><header class="sh"><h2>%s</h2><span class="sub">%s</span></header>'
                '<p class="sd">%s</p><div class="grid">%s</div></section>'
                % (title, sub, desc, ''.join(card(c) for c in codes)))

HTML = HEAD + '<div class="wrap">' + TOP + ''.join(body) + FOOT + '</div>'
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 's16s_kbar_atlas.html')
open(out, 'w', encoding='utf-8').write(HTML)
print('wrote %s   %d KB   %d cards' % (out, len(HTML) // 1024, len(M)))
