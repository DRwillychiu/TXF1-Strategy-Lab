# -*- coding: utf-8 -*-
"""The gap group -- P31 / P62 / P67 -- picture first, discussion after.

Willy's standing rule since 2026-08-27: the HTML comes before the deep
discussion, because judging a shape from prose does not work.

Checklist discipline 1 still applies, so the measurement ran first and this
page reports it.  The finding is largely negative and the page says so plainly
rather than dressing three dead patterns up as candidates.

Reuses _diagram.css, shared with the P29 and P51-P54 pages.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_gap_group_diagram.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

W, HH = 480.0, 260.0
PL, PR, PT, PB = 34.0, 34.0, 26.0, 40.0


def mk(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (W - PL - PR) / float(max(x1 - x0, 1e-9))
    sy = (HH - PT - PB) / float(max(y1 - y0, 1e-9))
    return (lambda x: PL + (x - x0) * sx, lambda y: HH - PB - (y - y0) * sy)


def candles(bars, marks=(), band=None):
    """bars: list of (o,h,l,c).  marks: {index: css class}.  band: (lo,hi)."""
    n = len(bars)
    X, Y = mk(list(range(n)), [b[1] for b in bars] + [b[2] for b in bars])
    bw = max((W - PL - PR) / float(n) * 0.55, 2.4)
    o = []
    if band:
        o.append('<rect class="zone" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (PL - 6, Y(band[1]), W - PL - PR + 12, max(Y(band[0]) - Y(band[1]), 2)))
    for i, (op, hi, lo, cl) in enumerate(bars):
        c = marks.get(i) or ('up' if cl >= op else 'dn')
        x = X(i)
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (c, x, Y(hi), x, Y(lo)))
        t, b = Y(max(op, cl)), Y(min(op, cl))
        if b - t < 1.4:
            m = (t + b) / 2.0
            t, b = m - .7, m + .7
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (c, x - bw / 2, t, bw, b - t))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


# ---- schematics: the shapes as the textbooks draw them ---------------------
ISL_TOP = [(10, 12, 9, 11), (11, 13, 10, 12), (12, 14, 11, 13),
           (18, 21, 17, 20), (20, 22, 18, 19), (19, 21, 17, 18),
           (12, 14, 11, 12), (11, 13, 10, 11), (10, 12, 9, 10)]
ISL_BOT = [(20, 22, 19, 21), (19, 21, 18, 20), (18, 20, 17, 19),
           (11, 13, 9, 10), (10, 12, 8, 11), (11, 13, 9, 12),
           (18, 20, 17, 19), (19, 21, 18, 20), (20, 22, 19, 21)]
GAP4 = [(10, 11, 9, 10), (10, 11, 9, 10), (10, 11, 9, 10),
        (14, 16, 13, 15), (16, 18, 15, 17), (18, 20, 17, 19),
        (22, 24, 21, 23), (23, 25, 20, 21), (21, 23, 19, 20)]

MARK_TOP = {3: 'brkbar', 4: 'brkbar', 5: 'brkbar'}
MARK_BOT = {3: 'brkbar', 4: 'brkbar', 5: 'brkbar'}
MARK_G4 = {3: 'brkbar', 6: 'brkbar'}


def real_case(a, b, kind):
    rows = real_case.rows
    H, L = real_case.H, real_case.L
    lo = max(a - 4, 0)
    hi = min(b + 4, len(rows) - 1)
    bars = [(float(rows[i]['open']), float(rows[i]['high']),
             float(rows[i]['low']), float(rows[i]['close'])) for i in range(lo, hi + 1)]
    marks = {i - lo: 'brkbar' for i in range(a, b)}
    gin = (L[a] - H[a - 1]) if kind == 'top' else (L[a - 1] - H[a])
    gout = (L[b - 1] - H[b]) if kind == 'top' else (L[b] - H[b - 1])
    body = max(H[u] for u in range(a, b)) - min(L[u] for u in range(a, b))
    return (candles(bars, marks), rows[a]['ymd'], rows[a]['hhmm'], rows[b]['hhmm'],
            b - a, gin, gout, body)


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 's16s_5min.csv'), encoding='utf-8')))
    real_case.rows = rows
    real_case.H = [float(r['high']) for r in rows]
    real_case.L = [float(r['low']) for r in rows]
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    N = len(rows)
    up = {t for t in range(1, N) if S[t] >= 2 and L[t] > H[t - 1]}
    dn = {t for t in range(1, N) if S[t] >= 2 and H[t] < L[t - 1]}

    def islands(entry, ex, top):
        out = []
        for a in sorted(entry):
            for b in range(a + 1, min(a + 60, N)):
                if b in ex:
                    body = range(a, b)
                    ok = (min(L[u] for u in body) > max(H[a - 1], H[b])) if top \
                        else (max(H[u] for u in body) < min(L[a - 1], L[b]))
                    if ok:
                        out.append((a, b))
                    break
                if S[b] == 1:
                    break
        return out

    tops, bots = islands(up, dn, True), islands(dn, up, False)
    tops.sort(key=lambda x: x[1] - x[0])
    bots.sort(key=lambda x: x[1] - x[0])
    rc_top = real_case(*tops[len(tops) // 2], kind='top')
    rc_bot = real_case(*bots[len(bots) // 2], kind='bot')

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
.wk.brkbar{stroke:var(--map)}
.bd.brkbar{fill:var(--map);stroke:var(--map)}
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

    SCH = [
        ('P31', '島狀反轉（頂）', 'Island Reversal', ISL_TOP, MARK_TOP,
         '向上跳空進場，孤立交易數根，再向下跳空離開。'
         '島身與兩側完全不重疊 —— 這是它與一般反轉的差別。'),
        ('P62', '島狀底', 'Island Bottom', ISL_BOT, MARK_BOT,
         '同一件事的鏡像：向下跳空進、向上跳空出。多方結構，'
         '但依 P54 的教訓，它<b>失敗</b>時是空方素材。'),
        ('P67', '缺口四分類', 'Breakaway / Runaway / Exhaustion / Common', GAP4, MARK_G4,
         '傳統上依「多快被回補」與「在趨勢的哪個階段」分成四類。'
         '<b>兩者都是門檻。</b>'),
    ]
    sc = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<span class="en">%s</span></div>%s<div class="qd">%s</div></figure>'
        % (cid, zh, en, candles(bars, marks), desc)
        for cid, zh, en, bars, marks, desc in SCH)

    rc = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<span class="en">%s %s ~ %s</span></div>%s'
        '<div class="qr">島身 <b>%d</b> 根　進場跳空 <b class="bad">%.0f</b> 點　'
        '離場跳空 <b>%.0f</b> 點　島身高度 <b class="bad">%.0f</b> 點</div></figure>'
        % (cid, zh, r[1], r[2], r[3], r[0], r[4], r[5], r[6], r[7])
        for cid, zh, r in (('P31', '島狀反轉（頂）', rc_top), ('P62', '島狀底', rc_bot)))

    SIZE = [(1, 1739, 90.4), (2, 118, 6.1), (3, 28, 1.5), (4, 20, 1.0),
            (5, 8, 0.4), (6, 5, 0.3), (7, 3, 0.2), (8, 1, 0.1), (9, 1, 0.1)]
    sz = ''.join('<tr><td>%d 點</td><td>%s</td><td>%.1f%%</td><td>%s</td></tr>'
                 % (p, format(n, ','), q, '低於成本' if p < 10 else '')
                 for p, n, q in SIZE)

    POP = [('時段內（可能是型態）', 1923, 1058, 865, '1', '9', True),
           ('時段首根（結構性）', 1852, 1062, 790, '16', '1,676', False)]
    pop = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td%s>%s</td><td>%s</td></tr>'
        % (nm, format(t, ','), format(u, ','), format(d, ','),
           ' class="z"' if bad else '', md, mx)
        for nm, t, u, d, md, mx, bad in POP)

    YRS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
    ISL = [('僅時段內（嚴格）', [14, 5, 3, 1, 0, 3, 2, 2], 30, 3.9, 1),
           ('允許時段邊界', [21, 9, 5, 3, 6, 6, 7, 6], 63, 8.2, 0)]
    isl = ''.join(
        '<tr><td>%s</td>%s<td><b>%d</b></td><td>%.1f</td><td%s>%d</td></tr>'
        % (nm, ''.join('<td%s>%d</td>' % (' class="z"' if v == 0 else '', v) for v in ys),
           tot, avg, ' class="z"' if z else '', z)
        for nm, ys, tot, avg, z in ISL)

    FILL = [(5, 1923, 100.0), (10, 1923, 100.0), (20, 1923, 100.0),
            (50, 1923, 100.0), (100, 1923, 100.0), (500, 1923, 100.0)]
    fill = ''.join('<tr><td>%d 根</td><td>%s</td><td class="z">%.1f%%</td></tr>'
                   % (w, format(n, ','), q) for w, n, q in FILL)

    HEAD = ('<title>缺口型態組 P31 P62 P67</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
            '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
            '&amp;display=swap" rel="stylesheet">\n<style>' + CSS + EXTRA + '</style>\n')

    TOP = ('<div class="wrap"><header class="top">'
           '<div class="eyebrow">S16_S 圖形型態 · 缺口組 · 2026-08-28</div>'
           '<h1>缺口型態組 P31 · P62 · P67</h1>'
           '<p class="sub">型態層剩餘 32 種的<b>第一順位</b>。三個型態共用同一套缺口偵測，'
           '所以第二、三個的邊際成本接近零 —— 這是把它們排在最前面的理由。'
           '所有數字量自 421,513 根 5 分 K，<b>無任何損益欄</b>。</p>'
           '<div class="kpi">'
           '<span><b>1,923</b>時段內缺口</span>'
           '<span><b>90.4%</b>剛好 1 個 tick</span>'
           '<span><b>0</b>達到 10 點來回成本</span>'
           '<span><b>30</b>島狀型態（八年）</span>'
           '</div>'
           '<p class="warn">⚠️ <b>本頁的發現是負面的，而且很硬。</b>'
           '依你 2026-08-27 的規矩，先出圖再深度討論 —— '
           '但量測已經先跑（檢查表紀律 1），結論寫在第三節。</p>'
           '</header>')

    P1 = ('<section class="panel"><div class="ph2"><h2>一、三個型態的形狀</h2>'
          '<span class="tag">紫色＝型態本體</span></div>'
          '<div class="quad">' + sc + '</div></section>')

    P2 = ('<section class="panel"><div class="ph2"><h2>二、真實案例</h2>'
          '<span class="tag">從 421,513 根裡由程式選出，取島長中位數</span></div>'
          '<div class="quad">' + rc + '</div>'
          '<p class="warn"><b>真實案例看起來和上面的示意圖完全不像 —— '
          '那個落差就是本頁的發現。</b>取中位數樣本後：島狀頂的島身是 <b>1 根</b>，'
          '進場跳空 <b>1 點</b>（一個 tick）；島狀底的島身是 <b>2 根</b>，'
          '進出各跳空 <b>1 點</b>，而且那兩根的高低完全相同 —— '
          '<b>島身高度 0 點</b>。那不是型態，是三個 tick 的雜訊。</p>'
          '<p class="cap">選取依據<b>只有形狀</b>（取島長中位數），'
          '無損益欄、不依報酬排序 —— 與 P29、P51-P54 同一條規矩。'
          '若改挑最大的那個，圖會好看很多，但那會是八年裡最極端的一個 —— '
          'P51 的示意圖已經犯過這個錯，已改正。</p></section>')

    P3 = ('<section class="panel"><div class="ph2">'
          '<h2>三、★ 缺口在 TXF1 5 分 K 上不存在</h2>'
          '<span class="tag">這節決定三個型態的命運</span></div>'
          '<table><thead><tr><th>缺口種類</th><th>個數</th><th>向上</th><th>向下</th>'
          '<th>中位（點）</th><th>最大</th></tr></thead>'
          '<tbody>' + pop + '</tbody></table>'
          '<p class="cap">時段首根的缺口是<b>結構性</b>的 —— 日盤 08:45-13:45、'
          '夜盤 15:00-05:00，每個時段開盤都隔著 75 分鐘或 3 小時 45 分。'
          '每天 0.82 個，那是隔夜跳空，不是圖形型態的缺口。</p>'
          '<table><thead><tr><th>時段內缺口大小</th><th>個數</th><th>占比</th>'
          '<th></th></tr></thead><tbody>' + sz + '</tbody></table>'
          '<div class="big"><p>1,923 個時段內缺口裡，1,739 個剛好是 <b>1 點</b>，'
          '也就是一個 tick。<b>沒有任何一個達到 10 點的來回成本。</b></p>'
          '<small>TXF1 的最小跳動是 1 點，5 分 K 又夠密。'
          '所謂「時段內缺口」其實是<b>某一跳沒有成交</b>的流動性破洞，不是價格結構。'
          '最大的一個是 9 點，仍然低於滑價來回 10 點（CLAUDE.md 成本規格）。</small></div>'
          '<table><thead><tr><th>回補視窗</th><th>已回補</th><th>比率</th>'
          '</tr></thead><tbody>' + fill + '</tbody></table>'
          '<p class="warn"><b>P67 的四分類沒有東西可以分。</b>'
          'Common / Breakaway / Runaway / Exhaustion 的差別在「多快被回補」與'
          '「在趨勢的哪個階段」—— 但這裡<b>五根之內 100% 全部回補</b>。'
          '一個五根內就補掉的缺口不是突破缺口。'
          '而且那兩個判準本身都是門檻，會是本專案第一個掃出來的自由參數。</p>'
          '</section>')

    P4 = ('<section class="panel"><div class="ph2"><h2>四、島狀型態的母體</h2>'
          '<span class="tag">紅色 0 ＝ 整年掛零</span></div>'
          '<table><thead><tr><th>定義</th>'
          + ''.join('<th>%s</th>' % y for y in YRS) +
          '<th>合計</th><th>年均</th><th>掛零年</th></tr></thead>'
          '<tbody>' + isl + '</tbody></table>'
          '<p class="cap">對照：<b>P29 八年 202-203 個、年均 26.6、沒有掛零</b>；'
          '而 P53／P54 八年 15 個、各四年掛零，已依裁示 B1 標記「近乎不出現」結案。'
          '嚴格版的島狀是 30 個、一年掛零 —— <b>與 P53／P54 同一級距</b>。</p>'
          '<p class="warn">兩個版本都<b>嚴重前傾 2019</b>：嚴格版 14/30（47%），'
          '寬鬆版 21/63（33%）。時段內缺口的「每萬根」在 2019 是 80.4，'
          '其餘年份 24-53 —— <b>2019 的缺口多是流動性造成的，不是型態變多。</b>'
          '一個母體有一半來自八年裡的第一年，跨期驗證做不了。</p>'
          '</section>')

    P5 = ('<section class="panel"><div class="ph2">'
          '<h2>五、待裁示</h2><span class="tag">批次問，不一次一題</span></div>'
          '<div class="rule">'
          '<div class="ro"><span class="tag rec">G1　建議</span><p>'
          '<b>P67 缺口四分類 —— 直接結案，不投入研究。</b>'
          '時段內缺口 90.4% 是一個 tick、五根內 100% 回補、零個達到來回成本；'
          '時段首根缺口是結構性的每日事件。<b>四分類沒有可分的對象。</b></p></div>'
          '</div>'
          '<div class="rule">'
          '<div class="ro"><span class="tag">H1</span><p>'
          '<b>島狀採嚴格定義（僅時段內缺口）</b> —— 八年 30 個、2023 掛零、'
          '47% 集中在 2019。<b>與 P53／P54 同級</b>，'
          '建議同樣標記「近乎不出現」並結案。</p></div>'
          '<div class="ro"><span class="tag rec">H2　建議</span><p>'
          '<b>島狀採寬鬆定義（允許時段邊界當缺口）</b> —— 八年 63 個、年均 8.2、'
          '<b>沒有掛零年</b>。仍然稀有但可做跨期驗證。'
          '代價：「島」的意思變成「某個時段整段脫離鄰居」，'
          '<b>語意上更接近時段跳空而非圖形型態</b>，這點必須誠實承認。</p></div>'
          '<div class="ro"><span class="tag">H3</span><p>'
          '<b>兩個都不做，整組結案</b> —— 承認缺口型態在 TXF1 5 分 K 上不成立，'
          '把三個一起關掉，直接進第 2 順位（P30 鑽石頂／P61 鑽石底）。</p></div>'
          '</div>'
          '<p class="warn"><b>還有一題從 8/27 掛到現在沒回：</b>'
          'D 組 4 種（P07 布林擠壓／P69 艾略特／P70 費波那契／P71 江恩）要不要直接結案？'
          '砍掉的話剩餘從 32 降為 28。</p>'
          '</section>')

    FOOT = ('<footer class="foot">'
            '共用資料層 <code>scripts/research/s16s_gaps.py</code> → '
            '<code>s16s_gaps.json</code>（檢查表 G 段要求：一次算完，其餘腳本只讀）　·　'
            '本頁 <code>s16s_gap_make_diagram.py</code>　·　'
            '樣式與 P29／P51-P54 共用 <code>_diagram.css</code>。'
            '<b>全部無損益欄。</b></footer></div>')

    open(OUT, 'w', encoding='utf-8').write(
        HEAD + TOP + P1 + P2 + P3 + P4 + P5 + FOOT)
    print('wrote %s' % OUT)
    print('  島狀頂 %d 個，島狀底 %d 個' % (len(tops), len(bots)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
