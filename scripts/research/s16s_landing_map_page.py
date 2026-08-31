# -*- coding: utf-8 -*-
"""型態層落地地圖 —— 72 種圖形型態，照「畫得到嗎」而不是「檢定過嗎」分類.

Willy 2026-08-31 的界定：

  「今天型態出現了，接下來才是進入規劃訊號以及策略層面的事情。
    因此應該是全部圖形討論清楚以及邏輯化後，並優化成指標，
    然後就能夠完整先在圖表上確認所有的圖形型態。
    這樣才是針對圖形型態的規畫之型態層的落地。」

所以型態層的驗收標準是**畫得到**，不是**檢定過**。
dn/up 那個量測屬於訊號層規劃時的輸入，不是型態層的成績單。

2026-08-31 收盤：28 種已畫且驗收、4 種已編碼待驗收。從 21% 到 44%。

資料源：
  scripts/research/s16s_make_full_atlas.py   72 種的代號／中文名／英文名
  docs/research/S16S_chart_pattern_catalogue_20260824.md   第一波 17
  docs/research/S16S_chart_pattern_wave2_20260824.md       第二波 16
  docs/research/S16S_pattern_layer_inventory.md            08-28~30 的裁示

Run:  python scripts/research/s16s_landing_map_page.py
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ATLAS = os.path.join('scripts', 'research', 's16s_make_full_atlas.py')
OUT = os.path.join('docs', 'research', 'S16S_landing_map.html')

# 五個桶，互斥且窮盡 72 種。分類軸是「畫得到嗎」，不是「檢定過嗎」。
#
# 2026-08-31 兩條裁示改了這張表：
#   ① 「兩個都畫」 —— 化約掉的型態，底層骨架與 named pattern 都上圖。
#      化約成立不代表畫不出來；把 named pattern 疊在骨架上當子標籤，
#      沒有東西被藏起來，而且用戶在真實 K 棒上看那個標籤，
#      本身就是在檢查「曲率是擲銅板」那個量測。
#   ② 「只需要避開多方型態，但不需要繪製」 —— 18 種多方移出待辦。
#
# 而「已檢定未畫」那 24 種必須跟其餘分開，因為它們是 2026-08-25 被退回的那批：
# 定義是 Claude 自行發明、自行檢定、事後回報的，從未逐一審查。
# 定義存在不等於邏輯討論過。它們要走完整流程，不是轉譯工作。
# 2026-08-31 收盤。三個狀態要分開，因為「寫進程式碼」不等於「MC12 驗收過」——
# 今天有兩次數字對不上都是把前者當成後者。
DRAWN = ('P29 P49 P50 P51 P52 P53 P54 P30 P61 P18 P57 P68 P28 P64 P55 '
         'P15 P26 P32 P56 P59 P65 P72 '          # IND_S16S_P29，260894 驗收
         'P01 P02 P03 P04 P05 P06').split()      # IND_S16S_CONV6，260901 驗收
# 已編碼、尚未 MC12 驗收（Build 260910 的 3x3 格新分支）
PENDING = 'P08 P10 P11 P22'.split()
# 邏輯從未審查（2026-08-25 退回的那批裡還沒處理的）
UNREVIEWED = ('P13 P14 P17 P33 P35 P37 P39 P41 P42 P43 P45 P47 P48').split()
# 多方，2026-08-31 裁示不繪製；P20 另有理由（見下）
BULLISH = ('P09 P12 P16 P19 P21 P23 P24 P25 P27 P34 P36 P38 P40 P44 P46 '
           'P60 P63 P66 P20').split()
# 結構性排除
EXCLUDED = 'P31 P62 P67 P07 P58 P69 P70 P71'.split()

BUCKETS = [
    ('done', '已畫在圖上，且 MC12 驗收過', DRAWN,
     '<b>IND_S16S_P29</b> Build 260894 的 22 種（價格圖，標籤／趨勢線／本體上色），'
     '其中 P28 P50 P52 P54 P61 五個多方依 08-31 裁示只計數不繪製。<br>'
     '<b>IND_S16S_CONV6</b> Build 260901 的 6 種（副圖六列色帶，'
     'MC12 實測 135777/89163/12730/1784/57140/63021 全中）。',
     '無。價格圖標籤依「需要幾個樞紐」分七條固定車道，'
     '最擁擠的 300 根視窗 58 個、中位 26 個；'
     '收斂六種在副圖，每個標記只有一根 K 棒寬。'),
    ('ready', '已編碼，尚未 MC12 驗收', PENDING,
     'Build 260910 把 3x3 格補滿：P11 上升楔形 1,919、P10 對稱三角 463、'
     'P08 下降三角 2,065、P22 箱型 3,063。'
     '同一版把 P53／P54 的「平」從<b>完全相等</b>改成<b>收斂</b>'
     '（散布 &lt; 對邊移動距離）—— 完全相等是全檔唯一尺度相依的測試，'
     '八年只有 7 個和 8 個且 2026 掛零。全等的那些保留成子標籤。',
     '<b>跑 MC12 驗收</b>。三道護欄必須不動'
     '（P29 202／P51 1670／P52 1716），全等子集必須仍是 7 與 8。'),
    ('todo', '邏輯從未審查', UNREVIEWED,
     '2026-08-24 兩波檢定裡的空方與中性型態。'
     '<b>那批定義是 Claude 自行發明、自行檢定、事後才回報的</b>，'
     '2026-08-25 已因違反標準流程被退回，33 個定義從未逐一審查。'
     'Python 裡有程式碼，不等於邏輯討論過。',
     '走完整流程：<b>討論 → 逐一邏輯規劃 → 對照圖 → .md → HTML → 才程式碼化</b>。'
     '每一個都要先確認零參數、確認定義是你認可的，才輪到接線。'),
    ('out', '不繪製 —— 多方裁示，或多餘', BULLISH,
     '「我認為只需要避開多方型態，但不需要繪製。」十八種多方依此排除。<br>'
     '<b>P20 下降通道另有理由</b>：降降格 3,101 個 ＝ P52 1,716（已畫）'
     '＋ P12 下降楔形 1,299（多方，不畫）＋ 86 個平手。'
     'P20 只會把已經在圖上的重貼一次，<b>填不到任何洞</b>。',
     '不做。'),
    ('out', '結構性排除', EXCLUDED,
     '缺口組 P31／P62／P67：5 分 K 上不存在跳空，時段內缺口 1,923 個、'
     '90.4% 剛好 1 點。D 組 P07／P58／P69／P70／P71：'
     '「因為這並非圖形型態探討的範疇」，範疇判定位階在實測之上。',
     '沒有東西可畫，或不在範疇。這不是待辦。'),
]

def names():
    src = io.open(ATLAS, encoding='utf-8').read()
    out = {}
    for c, zh, en in re.findall(r"\('(P\d\d)',\s*'([^']*)',\s*'([^']*)'", src):
        out.setdefault(c, (zh, en))
    return out


def main():
    nm = names()
    seen, dup = set(), []
    for _, _, codes, _, _ in BUCKETS:
        for c in codes:
            if c in seen:
                dup.append(c)
            seen.add(c)
    # 產生結構的腳本必須檢查自己產生的結構（2026-08-30 的教訓）
    assert not dup, '代號重複分類: %s' % dup
    assert len(seen) == 72, '分類到 %d 種，母體應為 72' % len(seen)
    missing = sorted(set(nm) - seen)
    assert not missing, '未分類: %s' % missing
    for c in sorted(seen):
        assert c in nm, '%s 在桶裡但圖鑑沒有它' % c

    n_done, n_ready = len(DRAWN), len(PENDING)
    n_todo, n_out = len(UNREVIEWED), len(BULLISH) + len(EXCLUDED)
    assert n_done + n_ready + n_todo + n_out == 72

    P = []
    w = P.append
    w('<title>型態層落地地圖</title>')
    w('<link rel="preconnect" href="https://fonts.googleapis.com">')
    w('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
      '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500;600'
      '&amp;display=swap" rel="stylesheet">')
    w('''<style>
:root{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --done:#17795e;--ready:#b8860b;--todo:#c8302e;--out:#7c8595;
 --serif:'Noto Serif TC',Georgia,'Songti TC',serif;
 --sans:'Noto Sans TC',-apple-system,'Microsoft JhengHei',sans-serif;
 --mono:'JetBrains Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
 --ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --done:#3ec08d;--ready:#e0b64a;--todo:#e8564e;--out:#79828f}}
:root[data-theme="dark"]{--ink:#eef1f6;--ink2:#a8b2c1;--ink3:#79828f;
 --bg:#0e1116;--card:#171b22;--line:#262c36;--line2:#1e232b;
 --done:#3ec08d;--ready:#e0b64a;--todo:#e8564e;--out:#79828f}
:root[data-theme="light"]{--ink:#14171c;--ink2:#4a525e;--ink3:#7c8595;
 --bg:#f5f6f8;--card:#ffffff;--line:#dfe3ea;--line2:#eef1f5;
 --done:#17795e;--ready:#b8860b;--todo:#c8302e;--out:#7c8595}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
 line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:44px 20px 84px}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
h1{font-family:var(--serif);font-size:34px;font-weight:700;margin:0 0 12px;
 letter-spacing:-.01em;text-wrap:balance}
.lede{font-size:16px;color:var(--ink2);max-width:64ch;margin:0 0 30px}
.quote{font-family:var(--serif);font-size:17px;color:var(--ink);
 border-left:3px solid var(--ink3);padding:2px 0 2px 16px;margin:0 0 30px;
 max-width:64ch}
.quote span{display:block;font-family:var(--sans);font-size:13px;
 color:var(--ink3);margin-top:8px}
.kpi{display:flex;flex-wrap:wrap;gap:34px;margin:0 0 8px;
 padding:22px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.kpi div{display:flex;flex-direction:column}
.kpi b{font-family:var(--mono);font-size:30px;line-height:1;font-weight:600;
 font-variant-numeric:tabular-nums}
.kpi span{font-size:12px;color:var(--ink3);margin-top:6px}
.kpi .d b{color:var(--done)}.kpi .r b{color:var(--ready)}
.kpi .t b{color:var(--todo)}.kpi .o b{color:var(--out)}
.bar{display:flex;height:12px;border-radius:6px;overflow:hidden;margin:26px 0 6px;
 background:var(--line2)}
.bar i{display:block}
.barlbl{display:flex;justify-content:space-between;font-size:12px;
 color:var(--ink3);font-family:var(--mono);margin-bottom:34px}
h2{font-family:var(--serif);font-size:21px;font-weight:700;margin:38px 0 6px;
 padding-top:22px;border-top:1px solid var(--line)}
.tag{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;
 letter-spacing:.08em;padding:2px 8px;border-radius:4px;margin-left:10px;
 vertical-align:3px;color:#fff}
.tag.done{background:var(--done)}.tag.todo{background:var(--todo)}
.tag.ready{background:var(--ready)}.tag.out{background:var(--out)}
p{margin:0 0 12px;max-width:66ch;font-size:14.5px;color:var(--ink2)}
p.work{color:var(--ink);border-left:3px solid var(--line);padding-left:14px}
p.work b{font-weight:700}
.chips{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
 border-radius:7px;overflow:hidden;margin:16px 0 4px;
 grid-template-columns:repeat(auto-fill,minmax(232px,1fr))}
.chip{background:var(--card);padding:9px 13px;display:flex;gap:10px;
 align-items:baseline}
.chip code{font-family:var(--mono);font-size:12px;font-weight:600;color:var(--ink3);
 flex:none}
.chip .zh{font-size:13.5px;color:var(--ink)}
.chip .en{font-size:11px;color:var(--ink3);margin-left:auto;text-align:right;
 max-width:46%;line-height:1.35}
.note{background:var(--card);border:1px solid var(--line);
 border-left:3px solid var(--ink3);border-radius:9px;padding:18px 20px;
 margin:26px 0;font-size:14px;color:var(--ink2)}
.note b{color:var(--ink)}
.note h3{margin:0 0 8px;font-size:15px;color:var(--ink)}
</style>''')

    w('<div class="wrap">')
    w('<div class="eyebrow">S16_S · 2026-08-31 · 型態層</div>')
    w('<h1>落地地圖 —— 72 種，畫得到的有幾種</h1>')
    w('<p class="lede">這張表用的標準是<b>畫得到嗎</b>，不是<b>檢定過嗎</b>。'
      '兩者不同，而且用錯標準會把還沒做完的事情算成做完了。</p>')
    w('<div class="quote">今天型態出現了，接下來才是進入規劃訊號以及策略層面的事情。'
      '因此應該是全部圖形討論清楚以及邏輯化後，並優化成指標，'
      '然後就能夠完整先在圖表上確認所有的圖形型態。'
      '這樣才是針對圖形型態的規畫之型態層的落地。'
      '<span>Willy，2026-08-31</span></div>')

    w('<div class="kpi">')
    w('<div class="d"><b>%d</b><span>已畫且驗收</span></div>' % n_done)
    w('<div class="r"><b>%d</b><span>已編碼待驗收</span></div>' % n_ready)
    w('<div class="t"><b>%d</b><span>邏輯從未審查</span></div>' % n_todo)
    w('<div class="o"><b>%d</b><span>不繪製</span></div>' % n_out)
    w('<div><b>72</b><span>純圖形型態母體</span></div>')
    w('</div>')

    w('<div class="bar">'
      '<i style="width:%.2f%%;background:var(--done)"></i>'
      '<i style="width:%.2f%%;background:var(--ready)"></i>'
      '<i style="width:%.2f%%;background:var(--todo)"></i>'
      '<i style="width:%.2f%%;background:var(--out)"></i></div>'
      % (100.0 * n_done / 72, 100.0 * n_ready / 72,
         100.0 * n_todo / 72, 100.0 * n_out / 72))
    w('<div class="barlbl"><span>已落地 %d</span><span>待驗收 %d</span>'
      '<span>要走完整流程 %d</span><span>不繪製 %d</span></div>'
      % (n_done, n_ready, n_todo, n_out))

    w('<div class="note"><h3>2026-08-31 的兩條裁示</h3>'
      '<b>①「兩個都畫」</b> —— 化約掉的型態，底層骨架與 named pattern 都上圖，'
      'named pattern 疊成子標籤。化約成立不代表畫不出來，'
      '而且在真實 K 棒上看「圓弧頂」這個標籤，本身就是在檢查'
      '「曲率是擲銅板」那個量測。<br><br>'
      '<b>②「只需要避開多方型態，但不需要繪製」</b> —— 18 種多方移出待辦。<br><br>'
      '<b>尚未裁示：</b>已畫在圖上的 15 種裡有 5 個是多方 —— '
      'P50 擴散底、P52 下降擴散楔形、P54 右角擴散（下）、P28 杯柄、P61 鑽石底。'
      '前三個是 08-28「有出現就畫上去」裁示的直接產物，'
      '且 P50 是 P29 的 M7 拆分、拆不開；後兩個是裁示 A1／I1 要求編碼上圖的。'
      '<b>要不要拿掉，等你裁示，我不替你推翻你自己三天前的裁示。</b></div>')
    w('<div class="note"><h3>那個 dn／up 的量測放在哪裡</h3>'
      '2026-08-31 量到 P18 破位往下 50.43%、P57 54.12%、P68 53.59%，'
      '都過不了本專案對 33 次檢定用的 2.96 門檻。'
      '<b>那是訊號層規劃時的輸入，不是型態層的成績單。</b>'
      '型態層的工作是把形狀講清楚、邏輯化、畫上圖；'
      '形狀能不能預測方向，是下一層才問的問題。'
      '先前把它當成型態層的判決，是把下一階段的問題提前套在這一階段上。</div>')

    for kind, title, codes, why, work in BUCKETS:
        w('<h2>%s<span class="tag %s">%d 種</span></h2>' % (title, kind, len(codes)))
        w('<p>%s</p>' % why)
        w('<p class="work"><b>要做什麼：</b>%s</p>' % work)
        w('<div class="chips">')
        for c in codes:
            zh, en = nm[c]
            w('<div class="chip"><code>%s</code><span class="zh">%s</span>'
              '<span class="en">%s</span></div>' % (c, zh, en))
        w('</div>')

    w('<div class="note"><h3>誠實聲明</h3>'
      '六個桶互斥且窮盡 72 種，由本腳本斷言檢查（重複、遺漏、代號存在性）。'
      '「已檢定未畫」的 33 種<b>定義存在於 Python，從未接進 MC12</b> —— '
      '2026-08-24 的檢定跑的是 Python。本頁不宣稱它們在 PowerLanguage 裡'
      '一定寫得出來，那要逐一評估。本頁由 Claude 產出，未經第二方審查。</div>')
    w('</div>')

    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(P))
    print('wrote %s' % OUT)
    print('  已落地 %d / 等接線 %d / 走完整流程 %d / 不繪製 %d   合計 %d'
          % (n_done, n_ready, n_todo, n_out, n_done + n_ready + n_todo + n_out))


if __name__ == '__main__':
    main()
