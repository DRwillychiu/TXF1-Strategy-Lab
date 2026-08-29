# -*- coding: utf-8 -*-
"""Group A -- the seven pivot-based patterns -- picture first, discussion after.

Willy, 2026-08-28: produce the HTML for all of group A before the deep
discussion.  Checklist discipline 1 still applies, so everything was measured
first and this page reports it.

The methodological spine of this page is the CONTROL, which had to be rebuilt
three times before it could be believed:

  1  the whole-series shuffle gave P68 391x -- an artifact, because it pits a
     2019 high against a 2026 one and TWII ran 10,000 to 28,000
  2  the year-stratified shuffle gave 80x -- still an artifact, because
     January and December differ too
  3  the block-local shuffle, 200 neighbouring frames, is the one that holds

Reuses _diagram.css, shared with every other pattern page.
"""
import io, os, sys, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'docs', 'research',
                                    'S16S_groupA_diagram.html'))
CSS = open(os.path.join(HERE, '_diagram.css'), encoding='utf-8').read()

W, HH = 440.0, 230.0
PL, PR, PT, PB = 30.0, 30.0, 24.0, 34.0


def mk(xs, ys):
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx = (W - PL - PR) / float(max(x1 - x0, 1e-9))
    sy = (HH - PT - PB) / float(max(y1 - y0, 1e-9))
    return (lambda x: PL + (x - x0) * sx, lambda y: HH - PB - (y - y0) * sy)


def sch(seq, lines=()):
    """seq: [(kind, value)] alternating.  lines: [(i, j, cls)] pivot indices."""
    n = len(seq)
    xs = [6 + i * (88.0 / max(n - 1, 1)) for i in range(n)]
    ys = [v for _, v in seq]
    pts = ([(0, ys[0] + (6 if seq[0][0] == 'H' else -6))]
           + list(zip(xs, ys))
           + [(100, ys[-1] + (6 if seq[-1][0] == 'H' else -6))])
    X, Y = mk([p[0] for p in pts], [p[1] for p in pts] + [10, 96])
    o = []
    for i, j, cls in lines:
        o.append('<line class="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, X(xs[i]), Y(ys[i]), X(xs[j]), Y(ys[j])))
    o.append('<polyline class="px" points="%s"/>'
             % ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in pts))
    for i, (k, v) in enumerate(seq):
        c = 'ph' if k == 'H' else 'pl'
        o.append('<circle class="pv %s" cx="%.1f" cy="%.1f" r="4.2"/>' % (c, X(xs[i]), Y(v)))
    return '<svg viewBox="0 0 %.0f %.0f" role="img">%s</svg>' % (W, HH, ''.join(o))


SH = {
 'P15': ([('H', 62), ('L', 34), ('H', 88), ('L', 32), ('H', 60)],
         [(0, 4, 'tlu solid'), (1, 3, 'tld solid')]),
 'P16': ([('L', 40), ('H', 68), ('L', 14), ('H', 70), ('L', 42)],
         [(0, 4, 'tld solid'), (1, 3, 'tlu solid')]),
 'P18': ([('H', 80), ('L', 36), ('H', 80), ('L', 30), ('H', 80)],
         [(0, 4, 'tlu solid')]),
 'P23': ([('L', 24), ('H', 66), ('L', 24), ('H', 72), ('L', 24)],
         [(0, 4, 'tld solid')]),
 'P21': ([('H', 56), ('L', 26), ('H', 74), ('L', 44), ('H', 92), ('L', 62)],
         [(0, 4, 'tlu solid'), (1, 5, 'tld solid')]),
 'P57': ([('H', 92), ('L', 56), ('H', 74), ('L', 38), ('H', 56)],
         [(0, 1, 'tld solid'), (2, 3, 'tld solid')]),
 'P68': ([('H', 82), ('L', 30), ('H', 82)], [(0, 2, 'tlu solid')]),
}

META = [
 ('P15', '頭肩頂', 'Head and Shoulders', '空', '5,239', '685.7',
  '頭高過兩肩。<b>肩不設對稱要求</b>（要求就得有容差＝參數）。'),
 ('P16', '頭肩底', 'Inverse H&amp;S', '多', '5,288', '692.1',
  '鏡像。<b>它不是 P15 的虛無對照</b> —— 兩者是頂／底這一對，等同 P49／P50。'),
 ('P18', '三重頂', 'Triple Top', '空', '43', '5.6',
  '三個高點<b>完全相等</b>。逐年 12→8→5→6→6→5→1→0，<b>持續衰減</b>。'),
 ('P23', '三重底', 'Triple Bottom', '多', '33', '4.3', '鏡像，同樣衰減。'),
 ('P21', '上升通道', 'Ascending Channel', '多', '140', '18.3',
  '高遞增 ＋ 低遞增 ＋ <b>兩條線完全平行</b>（升幅相等）。逐年無掛零。'),
 ('P57', '測量移動（下）', 'Measured Move Down', '空', '255', '33.4',
  '兩段跌幅<b>完全相等</b>，中間一段反彈。'),
 ('P68', '雙頂', 'Double Top', '空', '1,365', '178.7',
  '兩個高點<b>完全相等</b>。四變體（Adam／Eve）靠尖 vs 圓區分 —— '
  '曲率門檻，本質是參數，<b>未編碼</b>。'),
]

CTRL = [
 ('1', '整條序列打散', 'P68 = 391x',
  '拿 2019 的高點跟 2026 的比。台指從萬點漲到兩萬八，'
  '<b>精確相等在打散後幾乎不可能</b>，期望值假到 3.5。'),
 ('2', '同年內打散', 'P68 = 80x',
  '一月比十二月，年內波動幾千點。<b>仍然是假的</b>。'),
 ('3', '鄰近 200 個框架內打散', 'P68 = 6.78x',
  '保留局部價格水準與波動度，<b>只破壞配對</b>。'
  '兩個高點中位相隔 3 根 K 棒 —— 它們價格接近是因為時間接近，'
  '任何打破這個鄰近性的對照都會製造出巨大的倍率。<b>這一版才站得住。</b>'),
]

RES = [('P18 三重頂', '21,927', '419', 455.2, 0.92, '0.963', False),
       ('P23 三重底', '22,254', '392', 416.9, 0.94, '0.893', False),
       ('P68 雙頂', '40,439', '1,365', 201.3, 6.78, '0.0005', True),
       ('　雙底（鏡像）', '40,925', '1,300', 202.4, 6.42, '0.0005', True),
       ('P57 測量移動下', '6,399', '255', 109.6, 2.33, '0.0005', True),
       ('　測量移動上（鏡像）', '7,028', '276', 127.3, 2.17, '0.0005', True),
       ('P21 上升通道', '3,729', '140', 49.6, 2.82, '0.0005', True),
       ('　下降通道（鏡像）', '3,106', '86', 36.7, 2.34, '0.0005', True)]

SHAPE = [('P15 頭肩頂 vs 谷（形狀鏡像）', '5,239 : 5,466', '0.958 : 1', False),
         ('鑽石 vs 沙漏（08-28 已測）', '1,467 : 1,581', '0.80x : 0.80x', False),
         ('P29 擴散 vs 獨立期望', '203 : 1,247', '0.16x', True),
         ('P51 vs 獨立期望', '3,729 : 1,791', '2.08x', True)]


def main():
    EXTRA = """
.quad{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.qf{margin:0;background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:12px 13px;display:flex;flex-direction:column;gap:6px}
.qf svg{width:100%;height:auto;display:block}
.qh{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.qh b{font-family:var(--serif);font-size:14.5px}
.qh .cid{font-family:var(--mono);font-size:11px;color:var(--bg);background:var(--ink3);
  border-radius:2px;padding:1px 5px}
.qh .en{font-size:10px;color:var(--ink3);font-style:italic}
.qd{font-size:12px;color:var(--ink2);line-height:1.5}
.qr{font-family:var(--mono);font-size:11px;color:var(--ink3);
  font-variant-numeric:tabular-nums;border-top:1px solid var(--line2);padding-top:6px}
.qr b{color:var(--ink)}
.tg{font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid;white-space:nowrap}
.tg.b{color:var(--dn);border-color:var(--dn)}
.tg.u{color:var(--up);border-color:var(--up)}
.z{color:var(--brk);font-weight:600}
.g{color:var(--ph);font-weight:600}
.steps{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
  border-radius:5px;overflow:hidden}
.st{background:var(--card);padding:13px 15px;display:flex;gap:12px;align-items:flex-start}
.st .n{flex:0 0 26px;height:26px;border-radius:50%;background:var(--ink3);color:var(--bg);
  font-family:var(--mono);font-size:12px;font-weight:600;display:flex;
  align-items:center;justify-content:center;margin-top:1px}
.st.ok .n{background:var(--ph)}
.st .bd2{display:flex;flex-direction:column;gap:3px}
.st h3{margin:0;font-family:var(--serif);font-size:14px;font-weight:700;
  display:flex;gap:10px;align-items:baseline}
.st h3 em{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--brk)}
.st.ok h3 em{color:var(--ph)}
.st p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.st b{color:var(--ink)}
.big{border-left:3px solid var(--ph);background:var(--card);padding:16px 20px;
  border-radius:0 5px 5px 0;margin:5px 0 2px}
.big p{margin:0;font-family:var(--serif);font-size:16.5px;line-height:1.6;color:var(--ink)}
.big small{display:block;margin-top:9px;font-family:var(--sans);font-size:12px;
  color:var(--ink3);line-height:1.6}
"""
    cards = ''.join(
        '<figure class="qf"><div class="qh"><b class="cid">%s</b><b>%s</b>'
        '<i class="tg %s">%s</i><span class="en">%s</span></div>%s'
        '<div class="qd">%s</div>'
        '<div class="qr"><b>%s</b> 個　年均 <b>%s</b></div></figure>'
        % (cid, zh, 'b' if d == '空' else 'u', d, en, sch(*SH[cid]), desc, n, yr)
        for cid, zh, en, d, n, yr, desc in META)

    steps = ''.join(
        '<div class="st%s"><div class="n">%s</div><div class="bd2">'
        '<h3>%s<em>%s</em></h3><p>%s</p></div></div>'
        % (' ok' if k == '3' else '', k, t, r, d) for k, t, r, d in CTRL)

    res = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%.1f</td>'
        '<td class="%s">%.2fx</td><td>%s</td><td class="%s">%s</td></tr>'
        % (nm, n, o, e, 'g' if ok else 'z', r, p, 'g' if ok else 'z',
           '★ 通過' if ok else '與隨機無異')
        for nm, n, o, e, r, p, ok in RES)

    shape = ''.join(
        '<tr><td>%s</td><td>%s</td><td class="%s">%s</td><td>%s</td></tr>'
        % (a, b, 'g' if ok else 'z', c, '含資訊' if ok else '不含資訊')
        for a, b, c, ok in SHAPE)

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
           '樞紐鏈、交替、滑動取窗、M7 拆分全部已經寫好，只換形狀條件。'
           '所有數字量自 421,513 根 5 分 K，<b>無任何損益欄</b>。</p>'
           '<div class="kpi">'
           '<span><b>7</b>型態</span>'
           '<span><b>3</b>通過嚴格對照</span>'
           '<span><b>3</b>次才修對對照</span>'
           '<span><b>0</b>具方向性</span>'
           '</div>'
           '<p class="warn">⚠️ <b>依 2026-08-27 規矩，先出圖再深度討論。</b>'
           '量測已先跑（檢查表紀律 1）。第三節是本頁的方法核心 —— '
           '<b>對照修了三次才站得住</b>。</p></header>')

    P1 = ('<section class="panel"><div class="ph2"><h2>一、七個型態的形狀</h2>'
          '<span class="tag">綠點＝樞紐高　橘點＝樞紐低</span></div>'
          '<div class="quad">' + cards + '</div></section>')

    P2 = ('<section class="panel"><div class="ph2">'
          '<h2>二、★ 對照修了三次</h2>'
          '<span class="tag">前兩次的數字都是假的</span></div>'
          '<div class="steps">' + steps + '</div>'
          '<p class="warn"><b>這一節比任何一個型態的結論都重要。</b>'
          '如果我在第一版就停手，會回報「雙頂 391 倍於隨機」—— '
          '一個看起來石破天驚、實際上完全是對照造成的數字。'
          '<b>每一次修正都讓倍率降低，而最嚴格的那版才是可以拿去用的。</b></p>'
          '</section>')

    P3 = ('<section class="panel"><div class="ph2">'
          '<h2>三、檢定結果（鄰近 200 框架打散，2,000 次）</h2>'
          '<span class="tag">Bonferroni 門檻 0.001</span></div>'
          '<table><thead><tr><th>型態</th><th>母體</th><th>觀測</th>'
          '<th>打散期望</th><th>倍率</th><th>p</th><th>判定</th></tr></thead>'
          '<tbody>' + res + '</tbody></table>'
          '<div class="big"><p>三個通過 —— <b>但每一個的鏡像也同樣通過</b>。</p>'
          '<small>雙頂 6.78x／雙底 6.42x，上升通道 2.82x／下降通道 2.34x，'
          '測量移動下 2.33x／上 2.17x。'
          '所以測到的是<b>「價位與幅度會被重訪」這個市場性質</b> —— '
          '支撐壓力的老現象 —— <b>而不是型態的方向性</b>。'
          '三重頂與三重底 0.92x／0.94x，連這個性質都沒有。</small></div>'
          '</section>')

    P4 = ('<section class="panel"><div class="ph2">'
          '<h2>四、修正後的規則</h2>'
          '<span class="tag">我 08-28 早先那版只對了一半</span></div>'
          '<table><thead><tr><th>對照</th><th>觀測 : 對照</th><th>倍率</th>'
          '<th>判定</th></tr></thead><tbody>' + shape + '</tbody></table>'
          '<p class="cap">我早先的規則是「<b>單調條件含資訊，峰谷條件不含</b>」。'
          '峰谷那半仍然成立（頭肩 0.958:1、鑽石 0.80x 對 0.80x），'
          '但<b>它漏掉了第三類</b>。</p>'
          '<div class="big"><p>三類，不是兩類：</p>'
          '<small><b>單調方向條件</b> —— 與高低點同向共動 10.3:1 的結構互動，'
          '含資訊且<b>有方向性</b>（P29 0.16x／P51 2.08x）。<br>'
          '<b>峰谷形狀條件</b> —— 完全不碰那個結構，<b>不含資訊</b>。<br>'
          '<b>精確相等條件</b> —— 含資訊（2.3x ~ 6.8x），'
          '但那是價位／幅度被重訪的性質，<b>鏡像同樣通過，沒有方向性</b>。</small></div>'
          '</section>')

    P5 = ('<section class="panel"><div class="ph2">'
          '<h2>五、待裁示</h2><span class="tag">批次問</span></div>'
          '<div class="steps">'
          '<div class="st"><div class="n">K</div><div class="bd2">'
          '<h3>P15／P16／P18／P23 結案<em>建議</em></h3>'
          '<p>頭肩 0.958:1 不含資訊，收緊（右肩&lt;左肩）在對照組也是同樣比例；'
          '三重頂 0.92x 連重訪性質都沒有，且逐年 12→0 衰減。</p></div></div>'
          '<div class="st"><div class="n">L</div><div class="bd2">'
          '<h3>P68／P57／P21 怎麼處理<em>要你決定</em></h3>'
          '<p>三個都通過嚴格對照，但都<b>沒有方向性</b>。'
          '選項：<b>L1</b> 比照裁示 A1 當屬性（不是濾網）／'
          '<b>L2</b> 只編碼上圖如鑽石／<b>L3</b> 一併結案。</p></div></div>'
          '<div class="st"><div class="n">M</div><div class="bd2">'
          '<h3>「重訪性質」要不要獨立立項<em>新問題</em></h3>'
          '<p>2.3x ~ 6.8x 是這個專案目前<b>最強的統計效果</b>，'
          '但它不是型態、是價位行為。若要用，應以「<b>價位重訪</b>」立項，'
          '不要掛在圖形型態底下。</p></div></div>'
          '</div></section>')

    FOOT = ('<footer class="foot">'
            '掃描 <code>scripts/research/s16s_groupA_scan.py</code>、'
            '<code>s16s_hs_scan.py</code>　·　'
            '本頁 <code>s16s_groupA_make_page.py</code>　·　'
            '樣式共用 <code>_diagram.css</code>。<b>全部無損益欄。</b>'
            '</footer></div>')

    open(OUT, 'w', encoding='utf-8').write(
        HEAD + TOP + P1 + P2 + P3 + P4 + P5 + FOOT)
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
