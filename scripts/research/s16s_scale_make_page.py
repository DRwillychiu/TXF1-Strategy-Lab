# -*- coding: utf-8 -*-
"""樞紐尺度 -- the discussion Willy asked to finish before any coding.

His question: "圖形型態，本質其實可以是非常多根 K 棒組合而成。這件事情你有
意識到?"  His rulings that followed:

  X3   expose the pivot window as an input and look before committing
  and  "記得操作週期就是 5 分 K" -- a coarser window is NOT a coarser timeframe
  and  "絕對是要挑選空方的圖形型態，然後避免多方的圖形型態上進行操作"
  and  add the band device to the checklist

So this page carries three things: the scale problem, the distinction the
second ruling protects, and what the short-only ruling leaves standing.

Reuses _diagram.css.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_pivot_scale.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()
W, HH = 470.0, 210.0
PL_, PR, PT, PB = 30.0, 30.0, 24.0, 34.0


def mk(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return (lambda x: PL_ + (x - x0) * (W - PL_ - PR) / float(max(x1 - x0, 1e-9)),
            lambda y: HH - PB - (y - y0) * (HH - PT - PB) / float(max(y1 - y0, 1e-9)))


def scale_demo(bars, piv, title):
    """Same bars, pivots marked at one window; shows how many survive."""
    n = len(bars)
    X, Y = mk(list(range(n)), [b[1] for b in bars] + [b[2] for b in bars])
    bw = max((W - PL_ - PR) / float(n) * 0.6, 1.8)
    o = []
    for i, (op, hi, lo, cl) in enumerate(bars):
        c = 'up' if cl >= op else 'dn'
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (c, x, Y(hi), x, Y(lo)))
        t, b = Y(max(op, cl)), Y(min(op, cl))
        if b - t < 1.1:
            m = (t + b) / 2.0
            t, b = m - .55, m + .55
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (c, x - bw / 2, t, bw, b - t))
    for i, k in piv:
        v = bars[i][1] if k == 'H' else bars[i][2]
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="3.4"/>'
                 % ('ph' if k == 'H' else 'pl', X(i), Y(v)))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


SCALE = [(1, '151,147', 2.8, 2, 203, 12, '1,365', 3, 0, '現行'),
         (2, '88,079', 4.8, 4, 125, 19, '514', 6, 1, ''),
         (3, '61,617', 6.8, 5, 101, 30, '275', 8, 4, '★ MaxBarsBack 上限'),
         (5, '37,900', 11.1, 9, 69, 44, '94', 11, 39, '撞牆'),
         (8, '23,322', 18.1, 14, 41, 70, '35', 17, 93, '不可行')]

INV = [('P29 擴散', '0.16x', '0.18x', '0.20x'),
       ('鑽石', '0.80x', '0.78x', '0.81x'),
       ('沙漏（鏡像）', '0.80x', '0.79x', '0.77x'),
       ('頭肩 峰:谷', '0.958 : 1', '0.981 : 1', '0.944 : 1')]

BEAR = [('P18', '三重頂', '★ 通過', '10.19x', '6,352 個，八年無掛零', True),
        ('P17', '雙頂', '★ 通過', '6.75x', '1,365 個', True),
        ('P57', '測量移動（下）', '★ 通過', '2.33x', '255 個', True),
        ('P29', '擴散三角', '稀有', '0.16x', '逆結構，但破位方向 37:43 是銅板', False),
        ('P51', '上升擴散楔形', '屬性', '2.08x', '218／年，裁示 A1 當屬性', False),
        ('P15', '頭肩頂', '不含資訊', '0.958:1', '形狀對照與鏡像同值', False),
        ('P53', '右角擴散（上）', '近乎不存在', '—', '八年 7 個，四年掛零', False),
        ('P30', '鑽石頂', '已結案', '—', '完整版八年 0 個', False),
        ('P31', '島狀反轉', '已結案', '—', '跳空規則', False),
        ('P67', '缺口四分類', '已結案', '—', '跳空規則', False)]

BULL = 'P50 擴散底、P52 下降擴散楔形、P54 右角擴散（下）、P61 鑽石底、' \
       'P62 島狀底、P16 頭肩底、P23 三重底、P21 上升通道'


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    O = [float(r['open']) for r in rows]
    C = [float(r['close']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    # ONE day session, start to finish -- a demo that crossed the 13:45 close
    # would be misleading, since pivots may not span a session gap
    a = next(i for i in range(200000, N) if rows[i]['ymd'] == '20230705'
             and S[i] == 1 and int(rows[i]['hhmm']) < 1300)
    b = a
    while b + 1 < N and S[b + 1] > 1:
        b += 1
    b += 1
    bars = [(O[i], H[i], L[i], C[i]) for i in range(a, b)]
    demos = []
    for w in (1, 3):
        pv = []
        for i in range(a + w, b - w):
            if S[i] < w + 1 or any(S[t] == 1 for t in range(i - w + 1, i + w + 1)):
                continue
            if all(H[i] > H[i - k] and H[i] > H[i + k] for k in range(1, w + 1)):
                pv.append((i - a, 'H'))
            if all(L[i] < L[i - k] and L[i] < L[i + k] for k in range(1, w + 1)):
                pv.append((i - a, 'L'))
        demos.append((w, len(pv), scale_demo(bars, pv, '')))

    EXTRA = """
.two{display:grid;gap:13px;grid-template-columns:repeat(auto-fit,minmax(360px,1fr))}
.qf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:12px 14px;display:flex;flex-direction:column;gap:7px}
.qf svg{width:100%;height:auto;display:block}
.qh{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.qh b{font-family:var(--serif);font-size:15px}
.qr{font-family:var(--mono);font-size:11.5px;color:var(--ink3);
  font-variant-numeric:tabular-nums;border-top:1px solid var(--line2);padding-top:7px}
.qr b{color:var(--ink)}
.z{color:var(--brk);font-weight:600}
.g{color:var(--ph);font-weight:600}
.big{border-left:3px solid var(--ph);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:5px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:16.5px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
.big.warnv{border-left-color:var(--brk)}
tr.hit td{background:rgba(15,157,118,.09)}
tr.hit td:first-child{color:var(--ph);font-weight:600}
"""

    dm = ''.join(
        '<figure class="qf"><div class="qh"><b>視窗 %d</b>'
        '<span style="font-family:var(--mono);font-size:11px;color:var(--ink3)">'
        '%s</span></div>%s'
        '<div class="qr">這 60 根裡找到 <b>%d</b> 個樞紐</div></figure>'
        % (w, '現行' if w == 1 else '★ MaxBarsBack 允許的上限', svg, n)
        for w, n, svg in demos)

    sc = ''.join(
        '<tr%s><td>%d</td><td>%s</td><td>%.1f</td><td>%d</td><td>%d</td>'
        '<td>%d</td><td>%s</td><td class="%s">%d</td><td class="%s">%d%%</td>'
        '<td>%s</td></tr>'
        % (' class="hit"' if w == 3 else '', w, pv, per, gap, p29, sp,
           dt, 'z' if dts <= 3 else '', dts, 'z' if ov > 5 else '', ov, note)
        for w, pv, per, gap, p29, sp, dt, dts, ov, note in SCALE)

    inv = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % r
                  for r in INV)

    bear = ''.join(
        '<tr%s><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td>'
        '<td style="text-align:left">%s</td></tr>'
        % (' class="hit"' if ok else '', c, n, 'g' if ok else '', v, r, e)
        for c, n, v, r, e, ok in BEAR)

    HEAD = ('<title>樞紐尺度</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
            '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
            '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

    TOP = ('<div class="wrap"><header class="top">'
           '<div class="eyebrow">S16_S 型態層 · 樞紐尺度 · 2026-08-28</div>'
           '<h1>樞紐尺度</h1>'
           '<p class="sub">用戶提問：<b>「圖形型態本質其實可以是非常多根 K 棒組合而成，'
           '這件事情你有意識到?」</b>　'
           '意識到一部分，而且沒意識到它推翻了整個框架的尺度假設。'
           '討論已完成，<b>Build 260870 四項裁示全部落地</b>（見第六節）。</p>'
           '<div class="kpi">'
           '<span><b>35.9%</b>的 K 棒是樞紐</span>'
           '<span><b>3 根</b>「雙頂」的跨度中位</span>'
           '<span><b>視窗 3</b>MaxBarsBack 允許的上限</span>'
           '<span><b>260870</b>已編碼</span>'
           '</div></header>')

    P1 = ('<section class="panel"><div class="ph2"><h2>一、問題</h2>'
          '<span class="tag">同樣 60 根日盤 K 棒，兩種視窗</span></div>'
          '<div class="two">' + dm + '</div>'
          '<p class="warn"><b>視窗 1 每 2.8 根就認一個樞紐，35.9% 的 K 棒都是樞紐。</b>'
          '所以「雙頂」的跨度中位只有 <b>3 根</b> —— '
          '一根高、中間一根、再一根高。<b>那不是雙頂。</b>'
          '這與島狀底那個「兩根 K 棒高低完全相同」是同一類錯誤：'
          '<b>標籤承諾了一個資料裡沒有的結構</b>。</p></section>')

    P2 = ('<section class="panel"><div class="ph2"><h2>二、粗一點會怎樣</h2>'
          '<span class="tag">紅色 ＝ 超出 MaxBarsBack 100</span></div>'
          '<table><thead><tr><th>視窗</th><th>樞紐總數</th><th>每N根</th>'
          '<th>中位間隔</th><th>P29 母體</th><th>P29 跨度</th>'
          '<th>雙頂母體</th><th>雙頂跨度</th><th>形成+有效期&gt;99</th>'
          '<th></th></tr></thead><tbody>' + sc + '</tbody></table>'
          '<p class="cap">日盤 08:45-13:45 ＝ 60 根 5 分 K。'
          '<b>視窗 3 的 P29 跨 30 根 ≈ 半個日盤</b>，才開始像圖形型態。'
          '視窗 5 以上，39% 與 93% 的型態會超出 MaxBarsBack 100 —— '
          '「形成 + 有效期」是跨度的兩倍再加確認延遲。</p></section>')

    P3 = ('<section class="panel"><div class="ph2">'
          '<h2>三、★ 但結論不隨尺度改變</h2>'
          '<span class="tag">這決定了要不要重做</span></div>'
          '<table><thead><tr><th>判定</th><th>視窗 1</th><th>視窗 2</th>'
          '<th>視窗 3</th></tr></thead><tbody>' + inv + '</tbody></table>'
          '<div class="big"><p>三個判定在三種尺度下一致。</p>'
          '<small>P29 一直是強烈壓抑（0.16 ~ 0.20x）、'
          '鑽石一直與鏡像相同（0.80 對 0.80、0.81 對 0.77）、'
          '頭肩一直在 0.94 ~ 0.98 的平手。<br>'
          '<b>所以至今的分析不必重做</b>，變的只有母體數字與跨度。'
          '問題比看起來窄很多 —— 不是「分析錯了」，'
          '而是「<b>偵測器該不該跑粗一點，讓圖上畫的東西名副其實</b>」。</small></div>'
          '</section>')

    P4 = ('<section class="panel"><div class="ph2">'
          '<h2>四、★ 視窗變粗 ≠ 換週期</h2>'
          '<span class="tag">用戶 2026-08-28 特別叮嚀</span></div>'
          '<table><thead><tr><th></th><th style="text-align:left">改視窗（本頁在談的）</th>'
          '<th style="text-align:left">換週期（<b>不是</b>本頁在談的）</th></tr></thead>'
          '<tbody>'
          '<tr><td>K 棒</td><td style="text-align:left">'
          '仍是 <b>5 分 K</b></td><td style="text-align:left">變成 15 分 K</td></tr>'
          '<tr><td>OHLC</td><td style="text-align:left">不變</td>'
          '<td style="text-align:left">全部重算</td></tr>'
          '<tr><td>進場／出場</td><td style="text-align:left">'
          '仍在 <b>5 分 K</b> 上</td><td style="text-align:left">變成 15 分 K 上</td></tr>'
          '<tr><td>停損距離</td><td style="text-align:left">不變</td>'
          '<td style="text-align:left">跟著 K 棒放大</td></tr>'
          '<tr><td>改了什麼</td><td style="text-align:left">'
          '<b>只改「哪一根算樞紐」</b>：'
          '視窗 3 ＝ 高點要高過左右各 3 根</td>'
          '<td style="text-align:left">整個交易基準</td></tr>'
          '</tbody></table>'
          '<p class="warn"><b>操作週期永遠是 5 分 K。</b>'
          '視窗只是樞紐的認定門檻，跟 S16_S 的進出場、停損、'
          '結算日平倉全部無關。</p></section>')

    P5 = ('<section class="panel"><div class="ph2">'
          '<h2>五、★ 純空策略下還剩什麼</h2>'
          '<span class="tag">用戶裁示：挑空方、避開多方</span></div>'
          '<table><thead><tr><th>代號</th><th>名稱</th><th>判定</th><th>倍率</th>'
          '<th style="text-align:left">依據</th></tr></thead>'
          '<tbody>' + bear + '</tbody></table>'
          '<p class="cap"><b>多方型態（依裁示不作為進場依據）</b>：' + BULL + '</p>'
          '<div class="big"><p>已研究 19 個型態，'
          '<b>空方且通過嚴格對照的只有三個</b>：'
          'P18 三重頂、P17 雙頂、P57 測量移動（下）。</p>'
          '<small>三個的<b>鏡像也全部通過</b>，'
          '所以它們證實的是「價位與幅度會被精確重訪」，<b>不是方向性</b>。'
          '要當空方素材，方向必須另外來 —— 例如 S16_S 本身的 ZLEMA 死亡交叉。<br><br>'
          'P21 上升通道統計上是本組最乾淨的之一，'
          '但它是<b>多方型態，依裁示不列入</b>。</small></div></section>')

    P6 = ('<section class="panel"><div class="ph2">'
          '<h2>六、已編碼　Build 260870</h2>'
          '<span class="tag">2026-08-28　四項裁示全部落地</span></div>'
          '<table><thead><tr><th>裁示</th><th style="text-align:left">內容</th>'
          '<th style="text-align:left">實作</th></tr></thead><tbody>'
          '<tr><td>X3</td><td style="text-align:left">樞紐視窗做成 input</td>'
          '<td style="text-align:left"><code>Pivot_Window ( 1 )</code>　'
          '<b>w=1 與舊碼逐字等價</b>，模擬確認 P29 仍為 203</td></tr>'
          '<tr><td>—</td><td style="text-align:left">操作週期是 5 分 K</td>'
          '<td style="text-align:left">寫進 input 檔頭註解，見第四節</td></tr>'
          '<tr><td>—</td><td style="text-align:left">只挑空方</td>'
          '<td style="text-align:left"><b>P18／P17／P57</b> 三個進指標，'
          'P21 上升通道因是多方而排除</td></tr>'
          '<tr><td>17/18</td><td style="text-align:left">區間裝置與尺度</td>'
          '<td style="text-align:left">檢查表 15 條 → <b>18 條</b></td></tr>'
          '</tbody></table>'
          '<p class="cap"><b>三個型態不新增任何鏈</b> —— 既有六樞紐鏈已經握著最後六個'
          '交替樞紐，P17 讀最後 3 個、P18／P57 讀最後 5 個。'
          '鏈本身保證交替，所以只需檢查第一個的型別。'
          '鑽石的十樞紐鏈也<b>一行沒動</b>。</p>'
          '<p class="warn"><b>三個型態不塗 K 棒，只下標籤。</b>'
          'PowerLanguage 十六色已用掉十四個，剩下的 Black 與 DarkGray '
          '在黑底上看不見；而 P18 每年 831 個，塗色會把 P29 家族整個埋掉。'
          '標籤與計數器才是它們的價值。</p>'
          '<p class="cap" style="margin-top:2px"><b>MC12 驗收（Pivot_Window = 1）</b></p>'
          '<table><thead><tr><th>輸出</th><th style="text-align:left">應讀到</th>'
          '</tr></thead><tbody>'
          '<tr><td>REV TALLY</td><td style="text-align:left">'
          '<code>P18= 6352　P57= 255　P17= 1365</code></td></tr>'
          '<tr><td>PIVOT</td><td style="text-align:left">'
          '<code>window= 1　pivot_high= 75127　pivot_low= 76020</code>'
          '（依圖表載入根數而定）</td></tr>'
          '<tr><td>P29 TALLY</td><td style="text-align:left">不變</td></tr>'
          '<tr><td>DIA TALLY</td><td style="text-align:left">不變</td></tr>'
          '</tbody></table>'
          '<p class="warn"><b>離線驗證</b>：ASCII 73/73（第一版有六行中文註解，'
          '被 Rule #15 擋下）、語意 <b>0 FAIL 0 WARN 18 PASS</b>、'
          'begin/end 120/120、'
          '<b>整條鏈移植回 Python 逐根模擬，6,352 / 255 / 1,365 / 203 全中</b>。'
          '時段閘門的兩種寫法在 w=1/2/3/5 下產生完全相同的樞紐集合。'
          '<br>驗的是演算法，<b>不是 PowerLanguage 語法</b> —— 語法要在 MC12 上跑才算數。</p>'
          '</section>')

    FOOT = ('<footer class="foot">'
            '量測 <code>scripts/research/s16s_pivot_scale.py</code>　·　'
            '本頁 <code>s16s_scale_make_page.py</code>　·　'
            '樣式共用 <code>_diagram.css</code>。<b>本頁無損益欄。</b>'
            '</footer></div>')

    open(OUT, 'w', encoding='utf-8').write(
        HEAD + TOP + P1 + P2 + P3 + P4 + P5 + P6 + FOOT)
    print('wrote %s' % OUT)
    print('  示範區間 %s %s ~ %s，%d 根' % (rows[a]['ymd'], rows[a]['hhmm'],
                                     rows[b - 1]['hhmm'], b - a))
    for w, n, _ in demos:
        print('    視窗 %d -> %d 個樞紐' % (w, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
