# -*- coding: utf-8 -*-
"""P30 diamond top / P61 diamond bottom -- picture first, discussion after.

Second of the remaining chart patterns, and it costs almost nothing: a diamond
is a broadening followed by a converging triangle, which on the six-pivot
frame P29 already built is a change of edge condition and nothing else.

    P29      highs monotone RISING     lows monotone FALLING
    diamond  highs PEAK in the middle  lows TROUGH in the middle

"Widest in the middle" needs no separate condition -- H2 > H1 with L2 < L1
gives H2-L2 > H1-L1, and the same on the right.  Zero free parameters.

The mirror is measured alongside as the null control, and it is what decides
the pattern.

Reuses _diagram.css, shared with the P29, P51-P54 and gap pages.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_diamond_diagram.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

W, HH = 480.0, 260.0
PL, PR, PT, PB = 34.0, 34.0, 26.0, 40.0


def mk(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (W - PL - PR) / float(max(x1 - x0, 1e-9))
    sy = (HH - PT - PB) / float(max(y1 - y0, 1e-9))
    return (lambda x: PL + (x - x0) * sx, lambda y: HH - PB - (y - y0) * sy)


def schematic(hi, lo):
    """Six alternating pivots; hi/lo are the three highs and three lows."""
    xh, xl = [14, 44, 74], [28, 58, 88]
    pts, pv = [], []
    for j in range(3):
        pts.append((xh[j], hi[j]))
        pv.append(('PH%d' % (j + 1), xh[j], hi[j], 'ph'))
        pts.append((xl[j], lo[j]))
        pv.append(('PL%d' % (j + 1), xl[j], lo[j], 'pl'))
    pts = [(4, (hi[0] + lo[0]) / 2)] + pts + [(96, (hi[2] + lo[2]) / 2)]
    X, Y = mk([p[0] for p in pts], [p[1] for p in pts] + [30, 110])
    o = []
    for a, b, cls in ((0, 1, 'tlu solid'), (1, 2, 'tlu solid')):
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(xh[a]), Y(hi[a]), X(xh[b]), Y(hi[b])))
    for a, b, cls in ((0, 1, 'tld solid'), (1, 2, 'tld solid')):
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(xl[a]), Y(lo[a]), X(xl[b]), Y(lo[b])))
    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts))
    for k, x, y, cls in pv:
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.4"/>' % (cls, X(x), Y(y)))
        o.append('<text class="pvl %s" x="%.1f" y="%.1f">%s</text>'
                 % (cls, X(x), Y(y) + (-11 if cls == 'ph' else 18), k))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


def real(bars, piv):
    n = len(bars)
    X, Y = mk(list(range(n)), [b[1] for b in bars] + [b[2] for b in bars])
    bw = max((W - PL - PR) / float(n) * 0.56, 2.2)
    o = []
    hs = [i for i, k in piv if k == 'H']
    ls = [i for i, k in piv if k == 'L']
    idx = [i for i, _ in piv]
    o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
             % (X(min(idx)) - bw, PT - 4, X(max(idx)) - X(min(idx)) + 2 * bw,
                HH - PT - PB + 10))
    for a, b in ((0, 1), (1, 2)):
        o.append('<line class="tlu solid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (X(hs[a]), Y(bars[hs[a]][1]), X(hs[b]), Y(bars[hs[b]][1])))
        o.append('<line class="tld solid" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (X(ls[a]), Y(bars[ls[a]][2]), X(ls[b]), Y(bars[ls[b]][2])))
    for i, (op, hi, lo, cl) in enumerate(bars):
        c = 'up' if cl >= op else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (c, x, Y(hi), x, Y(lo)))
        t, b = Y(max(op, cl)), Y(min(op, cl))
        if b - t < 1.2:
            m = (t + b) / 2.0
            t, b = m - .6, m + .6
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (c, x - bw / 2, t, bw, b - t))
    for i, k in piv:
        v = bars[i][1] if k == 'H' else bars[i][2]
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="3.6"/>'
                 % ('ph' if k == 'H' else 'pl', X(i), Y(v)))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


WT = [6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6]


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    O = [float(r['open']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    PH = [i for i in range(1, N - 1)
          if S[i] >= 2 and S[i + 1] >= 3 and H[i] > H[i - 1] and H[i] > H[i + 1]]
    PLo = [i for i in range(1, N - 1)
           if S[i] >= 2 and S[i + 1] >= 3 and L[i] < L[i - 1] and L[i] < L[i + 1]]
    piv = sorted([(i, 'H') for i in PH] + [(i, 'L') for i in PLo])
    fr = []
    for k in range(len(piv) - 5):
        w = piv[k:k + 6]
        if any(w[j][1] == w[j + 1][1] for j in range(5)):
            continue
        hs = [x[0] for x in w if x[1] == 'H']
        ls = [x[0] for x in w if x[1] == 'L']
        if not (L[ls[0]] < H[hs[0]] and L[ls[2]] < H[hs[2]]):
            continue
        fr.append((hs, ls, [x[0] for x in w], w))

    def m7(i):
        return 0.0 if i < 12 else sum(WT[k] * C[i - k] for k in range(13)) / 182.0

    dia = [f for f in fr
           if H[f[0][0]] < H[f[0][1]] > H[f[0][2]] and L[f[1][0]] > L[f[1][1]] < L[f[1][2]]]
    tops = [f for f in dia if m7(f[2][0]) > 0]
    bots = [f for f in dia if m7(f[2][0]) <= 0]

    def pick(g):
        cand = []
        for f in g:
            sp = f[2][-1] - f[2][0]
            if 8 <= sp <= 26 and min(f[2][j + 1] - f[2][j] for j in range(5)) >= 1:
                amp = max(H[i] for i in f[0]) - min(L[i] for i in f[1])
                cand.append((amp, f))
        cand.sort(key=lambda t: t[0])
        amp, f = cand[len(cand) // 2]
        lo = max(f[2][0] - 4, 0)
        hi = min(f[2][-1] + 5, N - 1)
        bars = [(O[i], H[i], L[i], C[i]) for i in range(lo, hi + 1)]
        pv = [(i - lo, k) for i, k in f[3]]
        return (real(bars, pv), rows[f[2][0]]['ymd'], rows[f[2][0]]['hhmm'],
                rows[f[2][-1]]['hhmm'], f[2][-1] - f[2][0], amp)

    rt, rb = pick(tops), pick(bots)

    EXTRA = """
.quad{display:grid;gap:13px;grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.qf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:13px 14px;display:flex;flex-direction:column;gap:7px}
.qf svg{width:100%;height:auto;display:block}
.qh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.qh b{font-family:var(--serif);font-size:15px}
.qh .cid{font-family:var(--mono);font-size:11px;color:var(--bg);background:var(--ink3);
  border-radius:2px;padding:1px 5px}
.qh .en{font-size:10.5px;color:var(--ink3);font-style:italic}
.qd{font-size:12.5px;color:var(--ink2);line-height:1.5}
.qr{font-family:var(--mono);font-size:11.5px;color:var(--ink3);
  font-variant-numeric:tabular-nums;border-top:1px solid var(--line2);padding-top:7px}
.qr b{color:var(--ink)}
.bad{color:var(--brk);font-weight:600}
.z{color:var(--brk);font-weight:600}
.rule{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden;margin-top:4px}
.ro{background:var(--card);padding:13px 15px;display:flex;gap:12px;align-items:flex-start}
.ro .tag{flex:0 0 auto;font-family:var(--mono);font-size:11px;padding:2px 7px;
  border-radius:3px;border:1px solid var(--ink3);color:var(--ink3)}
.ro .tag.rec{border-color:var(--ph);color:var(--ph);font-weight:600}
.ro p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.6}
.ro b{color:var(--ink)}
.big{border-left:3px solid var(--brk);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:6px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:17px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
"""

    SCH = [('P30/P61', '鑽石', 'Diamond', [70, 100, 74], [46, 16, 42],
            '高點<b>中間最高</b>、低點<b>中間最低</b> —— 先擴散後收斂，'
            '中間最寬。「最寬」不需另設條件，由兩側的峰谷關係自動保證。'),
           ('對照', '沙漏（鏡像）', 'Hourglass', [100, 70, 96], [16, 46, 20],
            '把峰谷對調：中間<b>最窄</b>。'
            '這是虛無對照 —— 若鑽石只是機率的產物，兩者會一樣常見。')]
    sc = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<span class="en">%s</span></div>%s<div class="qd">%s</div></figure>'
        % (cid, zh, en, schematic(hi, lo), d) for cid, zh, en, hi, lo, d in SCH)

    rc = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<span class="en">%s %s ~ %s</span></div>%s'
        '<div class="qr">跨度 <b>%d</b> 根　振幅 <b>%.0f</b> 點　'
        '<span style="color:var(--ink3)">取中位振幅樣本</span></div></figure>'
        % (cid, zh, r[1], r[2], r[3], r[0], r[4], r[5])
        for cid, zh, r in (('P30', '鑽石頂', rt), ('P61', '鑽石底', rb)))

    LAYERS = [
        ('1 樞紐偵測', '找出所有轉折',
         '純分形視窗 1：<code>H[i] &gt; H[i-1] and H[i] &gt; H[i+1]</code>，'
         '<b>i+1 才確認</b>（無前瞻）。<b>不可跨時段</b> —— 分形是相鄰依賴。'),
        ('2 交替', '樞紐必須高低相間',
         'HLHLHL… 或 LHLHLH…。出現連續同型別就<b>重置整條鏈</b>。'),
        ('3 取窗', '哪幾個樞紐算一組',
         '時間序上<b>任何 N 個連續交替樞紐</b>，逐一滑動測試。'
         '<b>不錨定單側</b> —— P29 舊版錨定樞紐高，漏掉 91 個以樞紐低收尾者。'),
        ('4 形狀測試', '這組合不合格',
         '對窗內的高點序列與低點序列做不等式判斷。<b>本節以下全部是這一層的事。</b>'),
    ]
    lay = ''.join('<tr><td>%s</td><td>%s</td><td style="text-align:left">%s</td></tr>' % r
                  for r in LAYERS)

    CMP = [('6 樞紐（3 高 3 低）', '2 點', '32,094', '1,467', '1,581', '0', False),
           ('10 樞紐（5 高 5 低）', '3 點', '9,592', '1', '2', '7', True)]
    cmp_ = ''.join(
        '<tr><td>%s</td><td%s>%s</td><td>%s</td><td%s>%s</td><td>%s</td><td%s>%s</td></tr>'
        % (a, ' class="z"' if hl else '', b, c, ' class="z"' if hl else '', d, e,
           ' class="z"' if hl else '', f)
        for a, b, c, d, e, f, hl in CMP)

    EXP = [('高峰 × 低谷', 'P30 / P61 鑽石', 1467, 1834.2, 0.80, True),
           ('高谷 × 低峰', '沙漏（鏡像對照）', 1581, 1987.1, 0.80, True),
           ('高增 × 低減', 'P29 擴散', 203, 1247.4, 0.16, False),
           ('高減 × 低增', '收斂（對照）', 462, 2105.7, 0.22, False)]
    exp = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%.1f</td><td%s>%.2fx</td></tr>'
        % (a, b, format(o, ','), e, ' class="z"' if hl else '', r)
        for a, b, o, e, r, hl in EXP)

    YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
    YR = [('鑽石', [66, 160, 159, 227, 162, 232, 238, 223], 1467, 192.0),
          ('沙漏（對照）', [65, 147, 186, 233, 174, 258, 269, 249], 1581, 206.9),
          ('P29 擴散', [9, 15, 18, 31, 24, 31, 42, 33], 203, 26.6)]
    yr = ''.join('<tr><td>%s</td>%s<td><b>%s</b></td><td>%.1f</td></tr>'
                 % (nm, ''.join('<td>%d</td>' % v for v in ys), format(t, ','), a)
                 for nm, ys, t, a in YR)

    HEAD = ('<title>鑽石型態 P30 P61</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
            '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
            '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

    TOP = ('<div class="wrap"><header class="top">'
           '<div class="eyebrow">S16_S 圖形型態 · 鑽石 · 2026-08-28</div>'
           '<h1>鑽石型態 P30 · P61</h1>'
           '<p class="sub">缺口組結案後的下一順位。鑽石＝<b>先擴散後收斂</b>，'
           '在六樞紐框架上只是<b>換一個邊的條件</b>，'
           '32,094 個框架與 M7 前段趨勢拆分全部沿用擴散家族 —— '
           '<b>零新參數、零重算</b>。所有數字量自 421,513 根 5 分 K，<b>無損益欄</b>。</p>'
           '<div class="kpi">'
           '<span><b>1,467</b>鑽石（八年）</span>'
           '<span><b>1,581</b>沙漏鏡像對照</span>'
           '<span><b>1</b>完整鑽石（10 樞紐，八年）</span>'
           '<span><b>0.80x</b>6 樞紐版與鏡像同倍率</span>'
           '</div>'
           '<p class="warn">⚠️ <b>虛無對照給了否定的答案，第三節是關鍵。</b>'
           '依 2026-08-27 規矩，先出圖再深度討論；量測已先跑（檢查表紀律 1）。</p>'
           '</header>')

    P0 = ('<section class="panel"><div class="ph2">'
          '<h2>一、高低點是怎麼抓的</h2>'
          '<span class="tag">四層，每層都要分清楚</span></div>'
          '<table><thead><tr><th>層</th><th>做什麼</th>'
          '<th style="text-align:left">規則</th></tr></thead>'
          '<tbody>' + lay + '</tbody></table>'
          '<p class="warn"><b>關鍵在第 3 層：沒有「挑最顯著的高低點」這種步驟。</b>'
          '每一個連續交替樞紐窗都被測，所以<b>同一段行情可能同時屬於多個型態</b>，'
          '一個「鑽石」也可能只是更大結構的碎片。'
          '四層合計<b>自由參數 0 個</b>。</p></section>')

    PC = ('<section class="panel"><div class="ph2">'
          '<h2>三、★ 什麼叫「完整」的鑽石</h2>'
          '<span class="tag">這一節推翻了本頁的第一版</span></div>'
          '<p class="cap">上面那個 6 樞紐版本，擴散半段只用到 H1、H2 與 L1、L2 —— '
          '<b>每條邊只有兩個點</b>。而 P29 當初立規矩時寫的正好相反：</p>'
          '<div class="big" style="border-left-color:var(--ph)">'
          '<p>三個點，因為<b>兩點決定一條線，但三點才確認方向持續</b>。</p>'
          '<small>照這個標準，完整的鑽石是：擴散半段 '
          '<code>H1 &lt; H2 &lt; H3</code> 且 <code>L1 &gt; L2 &gt; L3</code>，'
          '收斂半段 <code>H3 &gt; H4 &gt; H5</code> 且 <code>L3 &lt; L4 &lt; L5</code>，'
          '共用中間的頂點 —— <b>5 高 + 5 低 = 10 個交替樞紐</b>。</small></div>'
          '<table><thead><tr><th>定義</th><th>每條邊點數</th><th>框架母體</th>'
          '<th>鑽石</th><th>鏡像沙漏</th><th>掛零年</th></tr></thead>'
          '<tbody>' + cmp_ + '</tbody></table>'
          '<div class="big"><p>常見的那版<b>不是確認過的鑽石</b>（每條邊只有兩點）；'
          '確認過的那版<b>八年出現一次</b>。</p>'
          '<small>兩個答案指向同一個結論，而且比虛無對照更直接：'
          '1,467 個是「形狀還沒被確認」的數量，1 個是「形狀被確認」的數量。'
          '中間沒有可用的地帶。</small></div></section>')

    P1 = ('<section class="panel"><div class="ph2"><h2>二、形狀與它的鏡像</h2>'
          '<span class="tag">綠點＝樞紐高　橘點＝樞紐低</span></div>'
          '<div class="quad">' + sc + '</div>'
          '<p class="cap">P30 與 P61 的差別<b>只有前段趨勢</b>（M7 &gt; 0 為頂），'
          '完全沿用 P49／P50 的裁示 12 —— 這是<b>分割</b>，不是額外條件。'
          'P30 鑽石頂 <b>774</b> 個，P61 鑽石底 <b>693</b> 個。</p></section>')

    P2 = ('<section class="panel"><div class="ph2"><h2>四、真實案例（6 樞紐版）</h2>'
          '<span class="tag">取中位振幅，非最大 —— P51 犯過那個錯</span></div>'
          '<div class="quad">' + rc + '</div>'
          '<p class="cap">選取依據<b>只有形狀</b>（跨度、樞紐不擠在一起、振幅取中位數），'
          '無損益欄、不依報酬排序。</p></section>')

    P3 = ('<section class="panel"><div class="ph2">'
          '<h2>五、虛無對照：「中間最寬」不含資訊</h2>'
          '<span class="tag">這節決定鑽石的命運</span></div>'
          '<table><thead><tr><th>組合</th><th></th><th>觀測</th>'
          '<th>獨立期望</th><th>倍率</th></tr></thead><tbody>' + exp + '</tbody></table>'
          '<div class="big"><p>鑽石 <b>0.80x</b>，它的鏡像沙漏也是 <b>0.80x</b> —— '
          '兩者<b>完全相同</b>。</p>'
          '<small>那個輕微的壓抑來自「兩側都非單調」這個<b>共同結構</b>，'
          '而「中間最寬」與「中間最窄」的區別<b>貢獻為零</b>。'
          '對照 P29 的 0.16x：它只有隨機的六分之一，'
          '<b>逆著資料結構</b>，那才是一個形狀值得被當成約束的理由。</small></div>'
          '<p class="cap">補充：高點三元組的四種形狀分布相當平均'
          '（谷 7,937／降 7,839／峰 7,706／升 6,667），'
          '低點亦然（升 8,621／峰 8,035／谷 7,639／降 6,005）。'
          '<b>峰與谷本來就各占約四分之一</b>，兩者相乘就是鑽石的期望值。</p>'
          '</section>')

    P4 = ('<section class="panel"><div class="ph2"><h2>六、母體與逐年（6 樞紐版）</h2>'
          '<span class="tag">沒有掛零年，但密度是 P29 的 7 倍</span></div>'
          '<table><thead><tr><th>型態</th>'
          + ''.join('<th>%s</th>' % y for y in YRS) +
          '<th>合計</th><th>年均</th></tr></thead><tbody>' + yr + '</tbody></table>'
          '<p class="cap">鑽石年均 <b>192</b>，每 <b>287</b> 根出現一次 —— '
          '約每 1.3 個交易日一個。<b>與 P51／P52（218／225）同一密度級距</b>，'
          '而那兩個已依裁示 A1 定為「屬性，不是濾網」。</p>'
          '<p class="warn">三者的 2019 都偏低（鑽石 66 vs 後續 160-238；'
          'P29 9 vs 後續 15-42）。台指從 2019 的萬點附近漲到 2026 的兩萬八，'
          '<b>價格水準上升使高低點更少相等</b>，嚴格不等式因此更容易成立。'
          '這是<b>價格水準效應，不是型態變多</b>，做跨期比較時必須記得。</p>'
          '</section>')

    P5 = ('<section class="panel"><div class="ph2">'
          '<h2>七、待裁示</h2><span class="tag">批次問</span></div>'
          '<div class="rule">'
          '<div class="ro"><span class="tag rec">I1　建議</span><p>'
          '<b>P30／P61 結案，不投入後續研究。</b>'
          '兩條獨立證據指向同一個結論：<b>(1)</b> 照本專案自己的三點規矩，'
          '完整鑽石<b>八年只出現一次</b>、七年掛零；'
          '<b>(2)</b> 放寬成兩點的版本雖有 1,467 個，'
          '但與鏡像沙漏的獨立性倍率完全相同（皆 0.80x），'
          '<b>「中間最寬」本身不含資訊</b>。</p></div>'
          '<div class="ro"><span class="tag">I2</span><p>'
          '<b>比照裁示 A1，當屬性保留</b> —— 與 P51／P52 同密度級距，'
          '當「中間最寬的擺盪結構」狀態標籤用。'
          '代價：<b>A1 當時沒有鏡像對照</b>，這次有，而且說了沒有資訊。</p></div>'
          '<div class="ro"><span class="tag">I3</span><p>'
          '<b>加條件收緊</b>（例如要求中間寬度是兩端的某個倍數）—— '
          '能壓低數量，但<b>倍數是自由參數</b>，會是本專案第一個掃出來的門檻。</p></div>'
          '</div>'
          '<p class="warn"><b>從 8/27 掛到現在還沒回的一題：</b>'
          'D 組 4 種（P07 布林擠壓／P69 艾略特／P70 費波那契／P71 江恩）'
          '要不要直接結案？砍掉的話剩餘從 29 降為 25。</p>'
          '</section>')

    FOOT = ('<footer class="foot">'
            '本頁 <code>scripts/research/s16s_diamond_make_diagram.py</code>　·　'
            '框架與 M7 沿用擴散家族，<b>母體只算過一次</b>（檢查表判準 2）　·　'
            '樣式共用 <code>_diagram.css</code>。<b>全部無損益欄。</b>'
            '</footer></div>')

    open(OUT, 'w', encoding='utf-8').write(
        HEAD + TOP + P0 + P1 + PC + P2 + P3 + P4 + P5 + FOOT)
    print('wrote %s' % OUT)
    print('  鑽石 %d（頂 %d / 底 %d）' % (len(dia), len(tops), len(bots)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
