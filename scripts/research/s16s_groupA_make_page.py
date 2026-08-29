# -*- coding: utf-8 -*-
"""Group A -- the seven pivot-based patterns, one card each.

Willy, 2026-08-28: "把個別的 7 種型態完整列出來邏輯說明以及定義，因為我認為
你沒有像前面擴散型態的討論模式討論清楚。"

He is right.  The broadening family got, per pattern, a labelled schematic with
PH1/PH2/PH3, the exact inequality, the population, the year-by-year split and a
free-parameter audit.  My first version of this page gave a one-line
description each and jumped to the statistics.  Rebuilt to the same depth.

Four corrections stand behind the numbers, and the page says so rather than
presenting the final figures as if they had arrived first:

  control v1   whole-series shuffle      P68 391x   artifact
  control v2   year-stratified           P68  80x   artifact
  control v3   block-local, 200 frames   P68 6.8x   holds
  definition   P18 written as an arithmetic progression, not a triple top --
               0.92x became 87.93x once corrected

Reuses _diagram.css, shared with every other pattern page.
"""
import io, os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_groupA_diagram.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

W, HH = 460.0, 240.0
PL_, PR, PT, PB = 32.0, 32.0, 30.0, 40.0
YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']


def mk(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (W - PL_ - PR) / float(max(x1 - x0, 1e-9))
    sy = (HH - PT - PB) / float(max(y1 - y0, 1e-9))
    return (lambda x: PL_ + (x - x0) * sx, lambda y: HH - PB - (y - y0) * sy)


def sch(seq, lines=()):
    """seq: [(kind, value)] alternating, labelled PH1.. / PL1.. in order."""
    n = len(seq)
    xs = [7 + i * (86.0 / max(n - 1, 1)) for i in range(n)]
    ys = [v for _, v in seq]
    pts = ([(0, ys[0] + (7 if seq[0][0] == 'H' else -7))]
           + list(zip(xs, ys))
           + [(100, ys[-1] + (7 if seq[-1][0] == 'H' else -7))])
    X, Y = mk([p[0] for p in pts], [p[1] for p in pts] + [6, 100])
    o, nh, nl = [], 0, 0
    for i, j, cls in lines:
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(xs[i]), Y(ys[i]), X(xs[j]), Y(ys[j])))
    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts))
    for i, (k, v) in enumerate(seq):
        if k == 'H':
            nh += 1
            lab, c = 'PH%d' % nh, 'ph'
        else:
            nl += 1
            lab, c = 'PL%d' % nl, 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.4"/>' % (c, X(xs[i]), Y(v)))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s</text>'
                 % (c, X(xs[i]), Y(v) + (-11 if c == 'ph' else 18), lab))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


EX = json.load(open(os.path.join(HERE, 's16s_groupA_example.json'), encoding='utf-8'))


def real(d):
    """One real instance: candles, with the pattern's own pivots ringed."""
    bars, pv = d['bars'], d['piv']
    n = len(bars)
    X, Y = mk(list(range(n)), [b['h'] for b in bars] + [b['l'] for b in bars])
    bw = max((W - PL_ - PR) / float(n) * 0.56, 2.2)
    o = []
    idx = [p[0] for p in pv]
    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
             % (X(min(idx)) - bw, PT - 6, X(max(idx)) - X(min(idx)) + 2 * bw,
                HH - PT - PB + 14))
    for i, b in enumerate(bars):
        c = 'up' if b['c'] >= b['o'] else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (c, x, Y(b['h']), x, Y(b['l'])))
        t, bt = Y(max(b['o'], b['c'])), Y(min(b['o'], b['c']))
        if bt - t < 1.2:
            m = (t + bt) / 2.0
            t, bt = m - .6, m + .6
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (c, x - bw / 2, t, bw, bt - t))
    for i, k in pv:
        v = bars[i]['h'] if k == 'H' else bars[i]['l']
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="3.8"/>'
                 % ('ph' if k == 'H' else 'pl', X(i), Y(v)))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


# cid, 名稱, 英文, 方向, 樞紐序列, 示意圖資料, 連線, 定義行, 母體, 年均, 跨度,
# 逐年, 檢定(觀測,期望,倍率,p,通過), 判定
PAT = [
 ('P15', '頭肩頂', 'Head and Shoulders', '空', 'H L H L H',
  [('H', 60), ('L', 32), ('H', 88), ('L', 30), ('H', 58)],
  [(0, 4, 'tlu solid'), (1, 3, 'tld solid')],
  ['PH2 &gt; PH1', 'PH2 &gt; PH3', 'PL1、PL2 <b>不設條件</b>'],
  '5,239', '685.7', 9, [353, 576, 647, 774, 573, 770, 858, 688],
  None,
  '<b>不含資訊。</b>同一批框架裡「中間最高」5,239 個、'
  '「中間最低」5,466 個 —— <b>0.958 : 1</b>，兩者理論占比相同。'
  '零參數收緊（PH3 &lt; PH1，反彈一次比一次弱）在對照組是 47.3% 對 44.9%，'
  '<b>只把母體砍一半，沒選出東西</b>。嚴格版（雙肩相等＋頸線水平）'
  '八年 14 個且 2024-2026 全掛零。'),

 ('P16', '頭肩底', 'Inverse Head and Shoulders', '多', 'L H L H L',
  [('L', 40), ('H', 68), ('L', 12), ('H', 70), ('L', 42)],
  [(0, 4, 'tld solid'), (1, 3, 'tlu solid')],
  ['PL2 &lt; PL1', 'PL2 &lt; PL3', 'PH1、PH2 <b>不設條件</b>'],
  '5,288', '692.1', 9, [318, 592, 655, 763, 622, 806, 884, 648],
  None,
  '<b>它不是 P15 的虛無對照</b> —— 兩者是頂／底這一對，'
  '等同 P49／P50 的關係，<b>一樣多是預期，不是證據</b>。'
  '正確的對照是同一批框架內的形狀鏡像，見 P15。'),

 ('P18', '三重頂', 'Triple Top', '空', 'H L H L H',
  [('H', 82), ('L', 34), ('H', 82), ('L', 28), ('H', 82)],
  [(0, 4, 'tlu solid')],
  ['<b>PH1、PH2 定義區間</b>　[min(PH1,PH2), max(PH1,PH2)]',
   'min(PH1,PH2) &lt;= <b>PH3</b> &lt;= max(PH1,PH2)', 'PL1、PL2 不設條件'],
  '6,352', '831.4', 8, [502, 748, 792, 971, 726, 889, 976, 748],
  ('6,352', '623.2', '10.19x', '0.0005', True),
  '<b>★ 用戶 2026-08-28 裁示：不必完全相等，PH1／PH2 先定義區間，再看 PH3。</b>'
  '容差 ＝ |PH1 − PH2|，<b>從型態自己推導，零參數</b>，而且因果順序正確 —— '
  '前兩峰形成壓力區，第三峰去測試它，無前瞻。'
  '<br><b>完全相等版</b>：43 個、10.20x、<b>2026 掛零</b>。'
  '<b>區間版</b>：6,352 個、10.19x、<b>八年無掛零</b>。'
  '<b>效果一樣強、樣本多 148 倍、且不衰減</b> —— 因為區間寬度會隨擺幅一起長大。'
  '區間寬度中位 10 點，50.6% 在 10 點以內。'),

 ('P23', '三重底', 'Triple Bottom', '多', 'L H L H L',
  [('L', 22), ('H', 68), ('L', 22), ('H', 74), ('L', 22)],
  [(0, 4, 'tld solid')],
  ['<b>PL1、PL2 定義區間</b>', 'min(PL1,PL2) &lt;= <b>PL3</b> &lt;= max(PL1,PL2)',
   'PH1、PH2 不設條件'],
  '6,551', '857.5', 7, [501, 764, 810, 965, 805, 936, 1022, 748],
  ('6,551', '676.1', '9.69x', '0.0005', True),
  '同一裝置的鏡像，同樣通過（9.69x）、同樣無掛零。'
  '<b>鏡像也通過代表沒有方向性</b> —— 測到的是價位被重訪，不是頂或底。'),

 ('P21', '上升通道', 'Ascending Channel', '多', '6 個交替樞紐（H 起或 L 起皆可）',
  [('H', 54), ('L', 22), ('H', 72), ('L', 40), ('H', 90), ('L', 58)],
  [(0, 4, 'tlu solid'), (1, 5, 'tld solid')],
  ['PH1 &lt; PH2 &lt; PH3', 'PL1 &lt; PL2 &lt; PL3',
   'PL1 &lt; PH1 且 PL3 &lt; PH3　（低在高下）',
   '通道寬度 w = PH − PL，取三對',
   '<b>w1、w2 定義區間</b>，min(w1,w2) &lt;= <b>w3</b> &lt;= max(w1,w2)　'
   '<b>相似平行</b>'],
  '1,276', '167.0', 12, [87, 153, 140, 168, 143, 204, 210, 171],
  ('1,276', '728.0', '1.75x', '0.0005', True),
  '<b>★ 用戶裁示：「完全平行」應改為「相似平行」。</b>'
  '用同一個區間裝置 —— 通道寬度 w1、w2 定區間，w3 落在其中。'
  '<br><b>但這個是取捨，不像 P18 是純賺</b>：'
  '完全平行版 140 個、<b>2.82x</b>；區間版 1,276 個、<b>1.75x</b>，'
  '而且吃掉母集的 <b>34.2%</b>（每 2.5 個交易日一個）。'
  '<b>樣本多 9 倍，效果弱掉四成。</b>'
  '下降通道對照 1.80x <b>也通過</b>，同樣沒有方向性。'),

 ('P57', '測量移動（下）', 'Measured Move Down', '空', 'H L H L H',
  [('H', 92), ('L', 54), ('H', 72), ('L', 34), ('H', 52)],
  [(0, 1, 'tld solid'), (2, 3, 'tld solid')],
  ['PH2 &lt; PH1', 'PL2 &lt; PL1',
   '(PH1 − PL1) = (PH2 − PL2)　<b>兩段跌幅完全相等</b>'],
  '255', '33.4', 8, [33, 29, 38, 37, 40, 36, 29, 13],
  ('255', '109.6', '2.33x', '0.0005', True),
  '<b>★ 通過。</b>兩段跌幅精確相等 255 次，期望 109.6。'
  '上升版對照 2.17x <b>也通過</b>。'
  '2026 掉到 13，<b>與其他精確相等類一樣在衰減</b>。'),

 ('P68', '雙頂', 'Double Top', '空', 'H L H',
  [('H', 84), ('L', 26), ('H', 84)], [(0, 2, 'tlu solid')],
  ['PH1 = PH2　<b>完全相等</b>', 'PL1 不設條件'],
  '1,365', '178.7', 3, [278, 229, 158, 192, 182, 140, 144, 42],
  ('1,365', '202.1', '6.75x', '0.0005', True),
  '<b>★ 通過。</b>雙底對照 6.41x <b>也通過</b>。'
  '四變體（Adam &amp; Adam / Adam &amp; Eve …）靠「尖 vs 圓」區分 —— '
  '<b>曲率門檻，本質是自由參數，未編碼</b>。'
  '逐年 278 → 42，衰減最明顯。'),
]

CTRL = [
 ('1', '整條序列打散', 'P68 = 391x',
  '拿 2019 的高點跟 2026 的比。台指從萬點漲到四萬多，'
  '<b>打散後精確相等幾乎不可能</b>，期望值假到 3.5。'),
 ('2', '同年內打散', 'P68 = 80x',
  '一月比十二月，年內也差幾千點。<b>仍然是假的</b>。'),
 ('3', '鄰近 200 個框架內打散', 'P68 = 6.75x',
  '保留局部價格水準與波動度，<b>只破壞配對</b>。'
  '雙頂的兩個高點中位相隔 3 根 K 棒 —— <b>它們價格接近是因為時間接近</b>，'
  '任何打破鄰近性的對照都會製造巨大倍率。<b>這一版才站得住。</b>'),
 ('4', '★ 而定義本身也錯過一次', 'P18：0.92x → 87.93x',
  '我把三重頂寫成 <code>PH1−PH2 = PH2−PH3</code> —— 那是<b>等差數列</b>，'
  '80/75/70 也算，<b>不是三重頂</b>，並據此回報「與隨機無異」。'
  '改成三高全等後 <b>43 個 vs 期望 0.49，87.93x，通過</b>。'
  '<b>是用戶問「為什麼三重頂不可以」才把它揪出來的。</b>'),
]

DECAY = [('2019', '3,376', 278, 82.35, 9, 741), ('2020', '4,899', 229, 46.74, 17, 795),
         ('2021', '5,194', 158, 30.42, 20, 608), ('2022', '5,801', 192, 33.10, 24, 794),
         ('2023', '4,745', 182, 38.36, 17, 652), ('2024', '5,793', 140, 24.17, 32, 773),
         ('2025', '6,183', 144, 23.29, 32, 745), ('2026', '4,448', 42, 9.44, 90, 850)]

SCALE = [(1, '2.8', 12, 3, '0%', '現行'),
         (2, '4.8', 19, 6, '1%', ''),
         (3, '6.8', 30, 8, '4%', 'MaxBarsBack 上限'),
         (5, '11.1', 44, 11, '39%', '撞牆'),
         (8, '18.1', 70, 17, '93%', '不可行')]

INV = [('P29 擴散', '0.16x', '0.18x', '0.20x'),
       ('鑽石', '0.80x', '0.78x', '0.81x'),
       ('沙漏（鏡像）', '0.80x', '0.79x', '0.77x'),
       ('頭肩 峰:谷', '0.958 : 1', '0.981 : 1', '0.944 : 1')]

CODED = {'P18', 'P57', 'P68'}

CLS = [('單調方向', 'P29 0.16x　收斂 0.22x　P51 2.08x　P52 2.12x',
        '與高低點同向共動 10.3 : 1 的結構互動', '含資訊 <b>且有方向性</b>', True),
       ('峰谷形狀', '頭肩 0.958:1　鑽石 0.80x 對沙漏 0.80x',
        '完全不碰那個結構', '<b>不含資訊</b>', False),
       ('精確相等', 'P18 87.9x　P68 6.75x　P21 2.82x　P57 2.33x',
        '價位與幅度會被精確重訪', '含資訊，<b>但鏡像同樣通過，無方向性</b>', None)]


def main():
    EXTRA = """
.quad{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.qf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:12px 13px;display:flex;flex-direction:column;gap:6px}
.qf svg{width:100%;height:auto;display:block}
.qh{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.qh b{font-family:var(--serif);font-size:14px}
.qh .cid{font-family:var(--mono);font-size:10.5px;color:var(--bg);
  background:var(--ink3);border-radius:2px;padding:1px 5px}
.qh .en{font-size:10px;color:var(--ink3);font-style:italic}
.qr{font-family:var(--mono);font-size:11px;color:var(--ink3);
  font-variant-numeric:tabular-nums;border-top:1px solid var(--line2);padding-top:6px}
.qr b{color:var(--ink)}
.pat{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:6px;overflow:hidden}
.pc{background:var(--card);padding:16px 18px;display:grid;gap:14px;
  grid-template-columns:minmax(300px,1fr) minmax(300px,1.15fr);align-items:start}
.pc svg{width:100%;height:auto;display:block}
.pc .rt{display:flex;flex-direction:column;gap:9px;min-width:0}
.ph3{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin:0}
.ph3 .cid{font-family:var(--mono);font-size:11.5px;color:var(--bg);
  background:var(--ink3);border-radius:2px;padding:1px 6px}
.ph3 b{font-family:var(--serif);font-size:16px}
.ph3 .en{font-size:10.5px;color:var(--ink3);font-style:italic}
.tg{font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid;white-space:nowrap}
.tg.b{color:var(--dn);border-color:var(--dn)}
.tg.u{color:var(--up);border-color:var(--up)}
.def{background:var(--bg);border:1px solid var(--line2);border-radius:4px;
  padding:9px 12px;font-family:var(--mono);font-size:12px;color:var(--ink2);
  display:flex;flex-direction:column;gap:3px}
.def .hd{font-family:var(--sans);font-size:10.5px;color:var(--ink3);
  letter-spacing:.06em;margin-bottom:2px}
.def b{color:var(--ink)}
.nums{display:flex;flex-wrap:wrap;gap:6px}
.nums span{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:3px;
  border:1px solid var(--line);color:var(--ink3);font-variant-numeric:tabular-nums}
.nums span b{color:var(--ink)}
.yr{font-family:var(--mono);font-size:11px;color:var(--ink3);
  font-variant-numeric:tabular-nums}
.yr b{color:var(--ink)}
.yr .z0{color:var(--brk);font-weight:600}
.vd{font-size:12.5px;color:var(--ink2);line-height:1.6}
.vd b{color:var(--ink)}
.steps{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden}
.st{background:var(--card);padding:13px 15px;display:flex;gap:12px;align-items:flex-start}
.st .n{flex:0 0 26px;height:26px;border-radius:50%;background:var(--brk);color:var(--bg);
  font-family:var(--mono);font-size:12px;font-weight:600;display:flex;
  align-items:center;justify-content:center;margin-top:1px}
.st.ok .n{background:var(--ph)}
.st .bd2{display:flex;flex-direction:column;gap:3px}
.st h3{margin:0;font-family:var(--serif);font-size:14px;font-weight:700;
  display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.st h3 em{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--brk)}
.st.ok h3 em{color:var(--ph)}
.st p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.st b{color:var(--ink)}
.z{color:var(--brk);font-weight:600}
.g{color:var(--ph);font-weight:600}
.tg.cd{color:var(--ph);border-color:var(--ph);font-weight:600}
tr.hit td{background:rgba(15,157,118,.09)}
tr.hit td:first-child{color:var(--ph);font-weight:600}
.big{border-left:3px solid var(--ph);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:5px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:16.5px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
@media(max-width:760px){.pc{grid-template-columns:1fr}}
"""

    cards = []
    for (cid, zh, en, d, seqtxt, seq, lines, defs, n, yr, sp, ys, tst, verdict) in PAT:
        yrtxt = '　'.join(
            '%s <span class="%s">%d</span>' % (y[2:], 'z0' if v == 0 else '', v)
            for y, v in zip(YRS, ys))
        t = ('<span>檢定 <b>%s</b> vs 期望 <b>%s</b></span>'
             '<span>倍率 <b>%s</b></span><span>p <b>%s</b></span>'
             % (tst[0], tst[1], tst[2], tst[3])) if tst else \
            '<span>形狀對照 <b>0.958 : 1</b></span>'
        cards.append(
            '<div class="pc"><div>%s</div><div class="rt">'
            '<h3 class="ph3"><span class="cid">%s</span><b>%s</b>'
            '<i class="tg %s">%s</i><span class="en">%s</span>%s</h3>'
            '<div class="def"><span class="hd">樞紐序列　%s</span>%s'
            '<span class="hd" style="margin-top:5px">自由參數　<b>0</b></span></div>'
            '<div class="nums"><span>母體 <b>%s</b></span>'
            '<span>年均 <b>%s</b></span><span>跨度中位 <b>%d</b> 根</span>%s</div>'
            '<div class="yr">逐年　%s</div>'
            '<div class="vd">%s</div></div></div>'
            % (sch(seq, lines), cid, zh, 'b' if d == '空' else 'u', d, en,
               ('<i class="tg cd">已編碼 260871</i>' if cid in CODED else ''),
               seqtxt, ''.join('<span>%s</span>' % x for x in defs),
               n, yr, sp, t, yrtxt, verdict))

    steps = ''.join(
        '<div class="st%s"><div class="n">%s</div><div class="bd2">'
        '<h3>%s<em>%s</em></h3><p>%s</p></div></div>'
        % (' ok' if k == '3' else '', k, t, r, dd) for k, t, r, dd in CTRL)

    decay = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%d</td><td>%.2f</td>'
        '<td class="z">%d</td><td class="g">%d</td></tr>' % r for r in DECAY)

    cls = ''.join(
        '<tr><td>%s</td><td>%s</td><td style="text-align:left">%s</td>'
        '<td style="text-align:left" class="%s">%s</td></tr>'
        % (a, b, c, 'g' if ok else ('z' if ok is False else ''), v)
        for a, b, c, v, ok in CLS)

    HEAD = ('<title>樞紐型 A 組七型態</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
            '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
            '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

    TOP = ('<div class="wrap"><header class="top">'
           '<div class="eyebrow">S16_S 圖形型態 · 樞紐型 A 組 · 2026-08-28</div>'
           '<h1>樞紐型 A 組　七個型態</h1>'
           '<p class="sub">型態層剩餘 27 種裡<b>最便宜的一組</b> —— '
           '樞紐鏈、交替、滑動取窗、M7 拆分全部已寫好，只換形狀條件。'
           '每個型態一張卡：<b>精確定義、樞紐序列、母體、逐年、檢定、判定</b>。'
           '所有數字量自 421,513 根 5 分 K，<b>無任何損益欄</b>。</p>'
           '<div class="kpi">'
           '<span><b>7</b>型態</span>'
           '<span><b>5</b>通過嚴格對照</span>'
           '<span><b>3</b>已編碼（空方）</span>'
           '<span><b>4</b>次更正才站得住</span>'
           '</div>'
           '<p class="warn"><b>這不是回測。</b>全部是計數與排列檢定，'
           '<b>沒有測任何報酬</b>。「通過」＝ 該形狀出現得比隨機多，'
           '<b>不等於可以交易</b> —— 五個通過的型態，鏡像全部同樣通過。</p>'
           '</header>')

    P1 = ('<section class="panel"><div class="ph2"><h2>一、七個型態，逐一定義</h2>'
          '<span class="tag">綠點＝樞紐高 PH　橘點＝樞紐低 PL　紅色 0 ＝ 該年掛零</span>'
          '</div><div class="pat">' + ''.join(cards) + '</div>'
          '<p class="cap">樞紐定義全組共用：純分形視窗 1，'
          '<code>H[i] &gt; H[i-1] and H[i] &gt; H[i+1]</code>，<b>i+1 才確認</b>（無前瞻），'
          '<b>不可跨時段</b>。取窗為時間序上任何 N 個連續交替樞紐，滑動測試，'
          '<b>不錨定單側</b>。<b>七個型態合計自由參數 0 個。</b></p></section>')

    rc = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<span class="en">%s %s ~ %s</span></div>%s'
        '<div class="qr">跨度 <b>%d</b> 根　振幅 <b>%.0f</b> 點　'
        '候選 <b>%s</b> 個中取中位振幅</div></figure>'
        % (cid, zh, EX[cid]['d0'], EX[cid]['t0'], EX[cid]['t1'], real(EX[cid]),
           EX[cid]['span'], EX[cid]['amp'], format(EX[cid]['n'], ','))
        for cid, zh in (('P15', '頭肩頂'), ('P16', '頭肩底'), ('P18', '三重頂'),
                        ('P23', '三重底'), ('P21', '上升通道'),
                        ('P57', '測量移動（下）'), ('P68', '雙頂')))

    PR_ = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
           '<span class="tag">紫框＝型態本體　綠點＝樞紐高　橘點＝樞紐低</span></div>'
           '<div class="quad">' + rc + '</div>'
           '<p class="warn">選取依據<b>只有形狀</b>（跨度在可讀範圍、樞紐不擠在一起、'
           '<b>振幅取中位數</b>），無損益欄、不依報酬排序。'
           '取最大振幅會讓圖好看很多，但那是八年裡最極端的一個 —— '
           'P51 的示意圖犯過這個錯，已改正。</p>'
           '<p class="cap">P18／P23 用的是<b>區間版</b>定義（裁示後），'
           '所以三個高（低）點<b>不必完全相等</b>，只要第三個落在前兩個構成的區間內。'
           'P21 同理，比的是三個通道寬度。</p></section>')

    P2 = ('<section class="panel"><div class="ph2">'
          '<h2>三、★ 這些數字修正了四次</h2>'
          '<span class="tag">前三次的倍率都是假的，第四次是定義寫錯</span></div>'
          '<div class="steps">' + steps + '</div>'
          '<p class="warn"><b>這一節比任何一個型態的結論都重要。</b>'
          '停在第一版會回報「雙頂比隨機高 391 倍」；'
          '停在定義寫錯那版會回報「三重頂與隨機無異」。'
          '<b>兩個都會是錯的，而且方向相反。</b></p></section>')

    P3 = ('<section class="panel"><div class="ph2">'
          '<h2>四、★ 三重頂為什麼不能用 —— 不是檢定，是算術</h2>'
          '<span class="tag">衰減定律</span></div>'
          '<p class="cap">P18 逐年 <b>12 → 8 → 5 → 6 → 6 → 5 → 1 → 0</b>，'
          '看起來像現象在消失。<b>不是。</b>'
          'TXF1 的 tick 固定 1 點，而雙頂框架的中位擺幅從 2019 的 9 點漲到 2026 的 90 點。'
          '一段擺幅跨 S 個 tick，兩段落在同一個整數的機率就是約 1/S。</p>'
          '<table><thead><tr><th>年</th><th>框架數</th><th>雙頂數</th>'
          '<th>命中率‰</th><th>中位擺幅</th><th>命中率 × 擺幅</th></tr></thead>'
          '<tbody>' + decay + '</tbody></table>'
          '<div class="big"><p>命中率八年掉了九倍，'
          '<b>但命中率 × 擺幅幾乎不動（608 ~ 850，平均 745）</b>。</p>'
          '<small>市場行為沒有改變，<b>算術上的機會變少了</b>。'
          '三重頂需要三次精確命中，衰減更快，2026 已經是 0；'
          '而且指數繼續漲、擺幅繼續變大，<b>它只會繼續衰減</b>。<br><br>'
          '反證：<b>不需要「相等」的單調類完全沒有這個問題</b> —— '
          'P29 逐年 9 15 18 31 24 31 42 33，<b>是上升的</b>。</small></div>'
          '</section>')

    P4 = ('<section class="panel"><div class="ph2"><h2>五、三類條件</h2>'
          '<span class="tag">我早先那版只分兩類，漏了第三類</span></div>'
          '<table><thead><tr><th>條件類型</th><th>證據</th>'
          '<th style="text-align:left">為什麼</th>'
          '<th style="text-align:left">判定</th></tr></thead>'
          '<tbody>' + cls + '</tbody></table>'
          '<p class="cap">這張表也預測 B 組（曲率型 8 種）：'
          '圓弧、杯、V 全部屬於<b>峰谷形狀</b>類，'
          '依此規則應該全部不含資訊。<b>錯了就是規則錯了。</b></p></section>')

    PB = ('<section class="panel"><div class="ph2">'
          '<h2>六、★ 區間裝置 —— 用戶 2026-08-28 裁示留下的通則</h2>'
          '<span class="tag">會用在之後每一個「相等」型態</span></div>'
          '<p class="cap">「完全相等」在 5 分 K 上會被算術殺死（第三節）。'
          '用戶給的替代不是加容差，而是<b>讓型態自己定義容差</b>：</p>'
          '<div class="big"><p>兩個點定義區間，第三個點落在其中。</p>'
          '<small>容差 ＝ 前兩點的差距，<b>從型態自身推導，不是外來常數</b> —— '
          '本專案第三種殺旋鈕的辦法。而且<b>因果順序正確</b>：'
          '前兩點先形成，第三點才去測試，沒有前瞻。<br><br>'
          '關鍵性質：<b>區間寬度會隨市場擺幅一起長大</b>，'
          '所以它免疫於第三節那條衰減定律。'
          'P18 從 43 個變 6,352 個、從 2026 掛零變八年無掛零，'
          '<b>而倍率完全沒變（10.20x → 10.19x）</b>。</small></div>'
          '<p class="warn"><b>但它不是萬靈丹。</b>'
          'P18 是純賺（效果不變、樣本多 148 倍）；'
          'P21 是取捨（樣本多 9 倍，效果 2.82x → 1.75x，且吃掉母集 34.2%）。'
          '差別在於：P18 比較的是<b>同一種量</b>（三個高點），'
          'P21 比較的是<b>衍生量</b>（通道寬度），衍生量本來就比較容易落在區間內。'
          '<b>之後套用這個裝置時要逐案量，不能假設它一定划算。</b></p>'
          '</section>')

    scale = "".join(
        '<tr%s><td>%d</td><td>%s</td><td>%d</td><td class="%s">%d</td>'
        '<td class="%s">%s</td><td>%s</td></tr>'
        % (' class="hit"' if w == 3 else '', w, per, sp,
           'z' if dt <= 3 else '', dt,
           'z' if ov not in ('0%', '1%', '4%') else '', ov, note)
        for w, per, sp, dt, ov, note in SCALE)

    inv = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % r
                  for r in INV)

    PS = ('<section class="panel"><div class="ph2">'
          '<h2>七、★ 樞紐尺度</h2>'
          '<span class="tag">用戶提問：型態本質是很多根 K 棒組合而成</span></div>'
          '<p class="warn"><b>視窗 1 每 2.8 根就認一個樞紐，35.9% 的 K 棒都是樞紐。</b>'
          '所以本頁的「雙頂」跨度中位只有 <b>3 根</b> —— '
          '一根高、中間一根、再一根高。<b>那不是雙頂。</b></p>'
          '<table><thead><tr><th>視窗</th><th>每 N 根一個</th><th>P29 跨度</th>'
          '<th>雙頂跨度</th><th>形成+有效期&gt;99</th><th></th></tr></thead>'
          '<tbody>' + scale + '</tbody></table>'
          '<p class="cap">日盤 ＝ 60 根。<b>視窗 3 的 P29 跨 30 根 ≈ 半個日盤</b>，'
          '才開始像圖形型態；視窗 5 以上有 39%／93% 的型態超出 MaxBarsBack 100。</p>'
          '<table><thead><tr><th>判定</th><th>視窗 1</th><th>視窗 2</th>'
          '<th>視窗 3</th></tr></thead><tbody>' + inv + '</tbody></table>'
          '<div class="big"><p>三個判定在三種尺度下一致 —— '
          '<b>本頁的結論不必因為改視窗而重做</b>，變的只有母體數字與跨度。</p>'
          '<small><b>★ 視窗變粗 ≠ 換週期。</b>'
          '視窗 3 的意思是「高點要高過左右各 3 根」，'
          '<b>K 棒仍是 5 分 K，進場、出場、停損全部仍在 5 分 K 上</b>。'
          '與改用 15 分 K 是完全不同的兩件事 —— 後者會連 OHLC、進場價、'
          '停損距離全部改掉。</small></div></section>')

    PC2 = ('<section class="panel"><div class="ph2">'
           '<h2>八、已編碼　Build 260871</h2>'
           '<span class="tag">只有空方三個進指標</span></div>'
           '<table><thead><tr><th>項目</th><th style="text-align:left">內容</th>'
           '</tr></thead><tbody>'
           '<tr class="hit"><td>P18 三重頂</td><td style="text-align:left">'
           '讀鏈上<b>最後 5 個</b>樞紐，區間裝置。參考 <b>6,352</b></td></tr>'
           '<tr class="hit"><td>P68 雙頂</td><td style="text-align:left">'
           '讀鏈上<b>最後 3 個</b>樞紐。參考 <b>1,365</b></td></tr>'
           '<tr class="hit"><td>P57 測量移動（下）</td><td style="text-align:left">'
           '讀鏈上<b>最後 5 個</b>樞紐（條件只用前 4 個）。參考 <b>255</b></td></tr>'
           '<tr><td>Pivot_Window</td><td style="text-align:left">'
           '新 input，預設 1。<b>w=1 與舊碼逐字等價</b>，'
           '模擬確認 P29 仍為 203</td></tr>'
           '<tr><td>P15／P16／P23／P21</td><td style="text-align:left">'
           '<b>未編碼</b> —— P15／P16 不含資訊；'
           'P23／P21 是<b>多方型態</b>，依裁示排除</td></tr>'
           '</tbody></table>'
           '<p class="cap"><b>不新增任何鏈。</b>既有六樞紐鏈已握著最後六個交替樞紐，'
           '鏈本身保證交替，所以只需檢查第一個的型別。'
           '鑽石的十樞紐鏈<b>一行沒動</b>。</p>'
           '<p class="warn"><b>三個型態不塗 K 棒，只下標籤。</b>'
           'PowerLanguage 十六色已用掉十四個，剩下的在黑底看不見；'
           '而 P18 每年 831 個，塗色會把 P29 家族整個埋掉。'
           '</p>'
           '<div class="big"><p><b>★ 260870 是錯的，260871 才是修正版。</b>'
           '用戶實跑 260870，得到 <b>P18 16,565 ／ P57 743 ／ P68 3,946</b>，'
           '是參考值的 2.6～2.9 倍 —— 而他的圖表<b>少了 11,909 根 K 棒</b>，'
           '數字只可能偏低，不可能偏高。</p>'
           '<p>倍率就是答案：<b>每 2.8 根 K 棒出現一個樞紐</b>。'
           '判定區塊寫在推入迴圈的<b>外面</b>，變成<b>每根 K 棒</b>跑一次而不是'
           '<b>每次推入樞紐</b>跑一次；兩次推入之間鏈完全沒變，'
           '同一個型態就被反覆計到下一個樞紐進來為止。'
           '把測試移到迴圈外重跑模擬得 <b>17,049 ／ 756 ／ 4,017</b>，'
           '與實測差的正是那 11,909 根。</p>'
           '<p class="warn" style="margin:10px 0 0"><b>驗證方式本身也錯了。</b>'
           '我把演算法移植回 Python，跑出 6,352 / 255 / 1,365，數字全中 —— '
           '但<b>移植版把判定放在迴圈裡，.pla 放在迴圈外</b>。'
           '模擬驗的是<b>邏輯</b>，從來沒驗過<b>放置位置</b>；'
           '照著意圖寫出來的模擬，本來就看不見「程式碼跟意圖不一致」。'
           '鑽石報 1 是<b>碰巧</b>（那個組態只活了一根 K 棒），不是因為它是對的。</p>'
           '<p style="margin:10px 0 0">補上 <code>scripts/verify_pla_scope.py</code>：'
           '直接數 begin／end 找出推入迴圈的行號範圍，'
           '再檢查 16 個計數器各自落在哪一層 —— '
           '<b>型態計數必須在迴圈內</b>（型態是樞紐鏈的性質，樞紐一進來就定案；'
           '且外包線一根會推入<b>兩次</b>，高點與低點都要判，'
           '所以「這根有沒有樞紐」的旗標並不等價），'
           '<b>破位與到期必須在迴圈外</b>（那是價格對已成形型態的性質，逐根判定）。'
           '拿 260870 當負向對照跑，<b>5 個 FAIL 全數抓出</b>。</p></div>'
           '<p class="cap"><b>驗收</b>：'
           '<code>REV TALLY  P18= 6352  P57= 255  P68= 1365</code>'
           '（Pivot_Window = 1、完整資料）。'
           '你的圖表少 11,909 根，預期會略低於此；'
           '<b>P29 的 75／85／39／0 與鑽石的 0／1 必須維持不變</b>。</p>'
           '</section>')

    P5 = ('<section class="panel"><div class="ph2">'
          '<h2>九、裁示與待決</h2><span class="tag">2026-08-28</span></div>'
          '<div class="steps">'
          '<div class="st ok"><div class="n">OK</div><div class="bd2">'
          '<h3>已裁示<em>P15/P16 完整　P18/P23 改區間　P21 改相似平行　'
          'P57/P68 通過</em></h3>'
          '<p>本頁七張卡的定義<b>已全部依裁示更新</b>。'
          'P18 從 43 個變 6,352 個且倍率不變；P21 從 140 個變 1,276 個但倍率'
          '從 2.82x 掉到 1.75x。以下是裁示後<b>仍未決</b>的部分。</p></div></div>'
          '<div class="st"><div class="n">K</div><div class="bd2">'
          '<h3>P15／P16 的肩要不要也用區間裝置<em>建議：不要</em></h3>'
          '<p>裝置需要<b>三個同類點</b>：兩個定區間、一個受測。'
          '頭肩只有<b>兩個肩</b>，沒有第三點可測，<b>套不上去</b>。'
          '維持「肩不設條件」，接受形狀對照 0.958:1 不含資訊的結論。</p></div></div>'
          '<div class="st"><div class="n">L</div><div class="bd2">'
          '<h3>五個通過的型態怎麼用<em>要你決定</em></h3>'
          '<p>P18／P23／P21／P57／P68 全部通過，'
          '<b>但每一個的鏡像也通過，所以沒有方向性</b>。'
          '<b>L1</b> 比照裁示 A1 全部當屬性（不是濾網）／'
          '<b>L2</b> 只編碼上圖如鑽石／<b>L3</b> 選擇性保留。'
          '密度參考：P18 831／年、P23 858／年、P21 167／年、'
          'P57 33／年、P68 179／年。</p></div></div>'
          '<div class="st"><div class="n">M</div><div class="bd2">'
          '<h3>「價位重訪」要不要獨立立項<em>新問題</em></h3>'
          '<p>區間裝置測到的 1.75x ~ 10.19x 是本專案目前<b>最強的統計效果</b>，'
          '但它是<b>價位行為</b>、不是型態 —— 三個高點落在同一個區間，'
          '就是支撐壓力。若要用，應以「<b>價位重訪</b>」立項，'
          '不要掛在圖形型態底下。</p></div></div>'
          '<div class="st"><div class="n">N</div><div class="bd2">'
          '<h3>區間裝置要不要升格為檢查表第 17 條<em>建議：要</em></h3>'
          '<p>「兩點定區間、第三點受測」是<b>零參數、因果正確、免疫於衰減</b>的'
          '通用替代方案，B 組與 C 組還會遇到很多「相等」型態。'
          '但必須附上警告：<b>逐案量，不能假設一定划算</b> —— '
          'P18 是純賺，P21 是取捨。</p></div></div>'
          '</div></section>')

    FOOT = ('<footer class="foot">'
            '掃描 <code>scripts/research/s16s_groupA_scan.py</code>、'
            '<code>s16s_hs_scan.py</code>、<code>s16s_equality_decay.py</code>　·　'
            '本頁 <code>s16s_groupA_make_page.py</code>　·　'
            '樣式共用 <code>_diagram.css</code>。<b>全部無損益欄。</b>'
            '</footer></div>')

    open(OUT, 'w', encoding='utf-8').write(
        HEAD + TOP + P1 + PR_ + P2 + P3 + P4 + PB + PS + PC2 + P5 + FOOT)
    print('wrote %s' % OUT)
    print('  型態卡 %d 張' % len(PAT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
