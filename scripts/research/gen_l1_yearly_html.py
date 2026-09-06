# -*- coding: utf-8 -*-
import json, os

BASE = r"C:\Users\WILLYC~1\AppData\Local\Temp\claude\C--Users-WILLY-CHIU\6339f9da-faaf-4075-a0cc-8cc8752b5e23\scratchpad"
d = json.load(open(os.path.join(BASE, "l1_report.json"), encoding="utf-8"))
Y = d["years"]

def f(n):
    return "{:,}".format(int(round(n)))

def sgn(n):
    return ("+" if n > 0 else "") + f(n)

# ---- bar chart geometry ----
W, H = 880, 300
PL, PR, PT, PB = 78, 20, 30, 46
iw, ih = W - PL - PR, H - PT - PB
vals = [y["net"] for y in Y]
lo, hi = min(0, min(vals)), max(0, max(vals))
span = (hi - lo) or 1

def yy(v):
    return PT + ih - (v - lo) / span * ih

zero = yy(0)
n = len(Y)
slot = iw / n
bw = min(58, slot * 0.56)

parts = []
for k in range(5):
    gv = lo + span * k / 4
    gy = yy(gv)
    parts.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (PL, gy, W - PR, gy))
    parts.append('<text class="axis" x="%d" y="%.1f" text-anchor="end">%s</text>' % (PL - 10, gy + 4, f(gv)))
parts.append('<line class="zero" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (PL, zero, W - PR, zero))
for i, y in enumerate(Y):
    cx = PL + slot * (i + 0.5)
    v = y["net"]
    top = yy(max(v, 0))
    bot = yy(min(v, 0))
    h = max(abs(bot - top), 2)
    cls = "pos" if v >= 0 else "neg"
    aria = "%d 年 淨利 %s，%d 筆，勝率 %.1f%%" % (y["year"], sgn(v), y["n"], y["wr"])
    parts.append('<g class="bg %s" tabindex="0" role="img" aria-label="%s">' % (cls, aria))
    parts.append('<rect class="hit" x="%.1f" y="%d" width="%.1f" height="%d"/>' % (cx - slot / 2, PT, slot, ih))
    parts.append('<rect class="bar" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4"/>' % (cx - bw / 2, top, bw, h))
    ly = top - 9 if v >= 0 else top + h + 16
    parts.append('<text class="val" x="%.1f" y="%.1f" text-anchor="middle">%s</text>' % (cx, ly, sgn(v)))
    parts.append('<text class="axis" x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (cx, H - PB + 24, y["year"]))
    parts.append('<title>%d　淨利 %s　%d 筆　勝率 %.1f%%　PF %.2f</title>' % (y["year"], sgn(v), y["n"], y["wr"], y["pf"]))
    parts.append("</g>")
BAR = "\n".join(parts)

# ---- cumulative line ----
H2 = 250
PT2, PB2 = 26, 46
ih2 = H2 - PT2 - PB2
cvals = [y["cum"] for y in Y]
clo, chi = min(0, min(cvals)), max(cvals)
cspan = (chi - clo) or 1

def cy(v):
    return PT2 + ih2 - (v - clo) / cspan * ih2

pts = [(PL + slot * (i + 0.5), cy(y["cum"])) for i, y in enumerate(Y)]
lp = []
for k in range(5):
    gv = clo + cspan * k / 4
    gy = cy(gv)
    lp.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (PL, gy, W - PR, gy))
    lp.append('<text class="axis" x="%d" y="%.1f" text-anchor="end">%s</text>' % (PL - 10, gy + 4, f(gv)))
dpath = " ".join(("M" if i == 0 else "L") + "%.1f,%.1f" % (x, yv) for i, (x, yv) in enumerate(pts))
lp.append('<path class="cumline" d="%s"/>' % dpath)
for (x, yv), yr in zip(pts, Y):
    lp.append('<g class="cg" tabindex="0" role="img" aria-label="%d 年底累計 %s">' % (yr["year"], sgn(yr["cum"])))
    lp.append('<circle class="ring" cx="%.1f" cy="%.1f" r="6"/>' % (x, yv))
    lp.append('<circle class="dot" cx="%.1f" cy="%.1f" r="4"/>' % (x, yv))
    lp.append('<text class="axis" x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (x, H2 - PB2 + 24, yr["year"]))
    lp.append("<title>%d 年底累計 %s</title>" % (yr["year"], sgn(yr["cum"])))
    lp.append("</g>")
lp.append('<text class="val" x="%.1f" y="%.1f" text-anchor="end">%s</text>' % (pts[-1][0], pts[-1][1] - 13, sgn(Y[-1]["cum"])))
LINE = "\n".join(lp)

TRS = "\n".join(
    '<tr><td class="y">%d</td><td>%d</td><td class="num %s">%s</td><td class="num">%s</td>'
    '<td class="num">%.1f%%</td><td class="num">%.2f</td><td class="num">%s</td>'
    '<td class="num">-%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
    % (y["year"], y["n"], "p" if y["net"] >= 0 else "n", sgn(y["net"]), sgn(y["cum"]),
       y["wr"], y["pf"], f(y["gp"]), f(y["gl"]), f(y["mx"]), f(y["mn"]))
    for y in Y)

LABS = "\n".join(
    '<tr><td><code>%s</code></td><td>%d</td><td class="num">%.1f%%</td>'
    '<td class="num %s">%s</td><td class="num">%.1f%%</td></tr>'
    % (x["k"], x["n"], x["n"] / d["n"] * 100, "p" if x["net"] >= 0 else "n", sgn(x["net"]), x["wr"])
    for x in d["labels"])

CSS = """
*{box-sizing:border-box}
.rt{--s1:#fcfcfb;--s2:#f4f3f0;--tp:#0b0b0b;--ts:#52514e;--tm:#84837c;--bd:#e2e1dc;
--pos:#2a78d6;--neg:#e34948;--grid:#e8e7e2;--zero:#b9b8b1;
font-family:"Segoe UI","Noto Sans TC","PingFang TC",system-ui,sans-serif;
background:var(--s1);color:var(--tp);padding:28px 22px;max-width:960px;margin:0 auto;line-height:1.6}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) .rt{
--s1:#1a1a19;--s2:#232322;--tp:#fff;--ts:#c3c2b7;--tm:#8d8c84;--bd:#33332f;
--pos:#3987e5;--neg:#e66767;--grid:#2b2b28;--zero:#4a4a45}}
:root[data-theme="dark"] .rt{--s1:#1a1a19;--s2:#232322;--tp:#fff;--ts:#c3c2b7;--tm:#8d8c84;
--bd:#33332f;--pos:#3987e5;--neg:#e66767;--grid:#2b2b28;--zero:#4a4a45}
h1{font-size:1.5rem;margin:0 0 3px}
h2{font-size:1.05rem;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--bd)}
.sub{color:var(--ts);font-size:.85rem;margin:0 0 20px}
.heroes{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin:18px 0 6px}
.hero{background:var(--s2);border:1px solid var(--bd);border-radius:10px;padding:13px 15px}
.hero .k{font-size:.73rem;color:var(--tm);letter-spacing:.04em}
.hero .v{font-size:1.4rem;font-weight:650;margin-top:3px;font-variant-numeric:tabular-nums}
.wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
svg{display:block;min-width:880px}
.grid{stroke:var(--grid);stroke-width:1}
.zero{stroke:var(--zero);stroke-width:1.5}
.axis{fill:var(--tm);font-size:11px;font-variant-numeric:tabular-nums}
.val{fill:var(--ts);font-size:11.5px;font-weight:600;font-variant-numeric:tabular-nums}
.hit{fill:transparent}
.bg.pos .bar{fill:var(--pos)}
.bg.neg .bar{fill:var(--neg)}
.bg:hover .bar{opacity:.72}
.bg:focus{outline:none}
.bg:focus .bar{stroke:var(--tp);stroke-width:2}
.cumline{fill:none;stroke:var(--pos);stroke-width:2;stroke-linejoin:round}
.dot{fill:var(--pos)}
.ring{fill:var(--s1)}
table{width:100%;border-collapse:collapse;font-size:.85rem;font-variant-numeric:tabular-nums}
th,td{padding:7px 9px;border-bottom:1px solid var(--bd);text-align:left}
th{font-size:.73rem;color:var(--tm);font-weight:600;letter-spacing:.03em;white-space:nowrap}
td.num{text-align:right}
td.y{font-weight:650}
td.p{color:var(--pos)}
td.n{color:var(--neg)}
tbody tr:hover{background:var(--s2)}
code{background:var(--s2);padding:1px 5px;border-radius:4px;font-size:.86em}
.note{background:var(--s2);border:1px solid var(--bd);border-left:3px solid var(--neg);
border-radius:8px;padding:13px 16px;margin:15px 0;font-size:.86rem;color:var(--ts)}
.note b{color:var(--tp)}
.legend{display:flex;gap:16px;font-size:.79rem;color:var(--ts);margin:6px 0 2px}
.sw{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
ul{margin:8px 0;padding-left:20px}
li{margin:5px 0;font-size:.86rem;color:var(--ts)}
"""

HTML = """<title>L1 逐年績效</title>
<style>%s</style>
<div class="rt">
<h1>L1_TrendLong 逐年績效</h1>
<p class="sub">回測區間 %s ~ %s　·　固定 2 口　·　原始資本 2,000,000 NTD　·　來源 <code>TXF1 L1_TrendLong 策略回測績效報告.xls</code>（2026-07-27 匯出）</p>

<div class="heroes">
<div class="hero"><div class="k">淨利</div><div class="v">%s</div></div>
<div class="hero"><div class="k">交易筆數</div><div class="v">%d</div></div>
<div class="hero"><div class="k">勝率</div><div class="v">%.2f%%</div></div>
<div class="hero"><div class="k">獲利因子</div><div class="v">%.4f</div></div>
<div class="hero"><div class="k">最大策略虧損</div><div class="v">%s</div></div>
</div>

<h2>逐年淨利</h2>
<div class="legend"><span><span class="sw" style="background:var(--pos)"></span>獲利年</span><span><span class="sw" style="background:var(--neg)"></span>虧損年</span></div>
<div class="wrap"><svg viewBox="0 0 %d %d" width="100%%" height="%d" role="group" aria-label="逐年淨利長條圖">%s</svg></div>

<h2>累計淨利</h2>
<div class="wrap"><svg viewBox="0 0 %d %d" width="100%%" height="%d" role="group" aria-label="累計淨利折線圖">%s</svg></div>

<h2>逐年明細</h2>
<div class="wrap"><table>
<thead><tr><th>年度</th><th>筆數</th><th style="text-align:right">淨利</th><th style="text-align:right">累計</th><th style="text-align:right">勝率</th><th style="text-align:right">PF</th><th style="text-align:right">毛利</th><th style="text-align:right">毛損</th><th style="text-align:right">最大單筆賺</th><th style="text-align:right">最大單筆賠</th></tr></thead>
<tbody>%s</tbody></table></div>

<h2>出場標籤分布</h2>
<div class="wrap"><table>
<thead><tr><th>標籤</th><th>筆數</th><th style="text-align:right">佔比</th><th style="text-align:right">合計損益</th><th style="text-align:right">勝率</th></tr></thead>
<tbody>%s</tbody></table></div>

<h2>二次進場優化對照（v32）</h2>
<div class="note"><b>此節數字為使用者提供的 MC12 畫面轉錄，非本工具解析。</b>對應的明細匯出檔不在本機，因此無法做逐年拆解。</div>
<div class="wrap"><table>
<thead><tr><th>指標</th><th style="text-align:right">優化前</th><th style="text-align:right">優化後</th><th style="text-align:right">變化</th></tr></thead>
<tbody>
<tr><td>淨利</td><td class="num">5,133,200</td><td class="num">5,483,600</td><td class="num p">+350,400</td></tr>
<tr><td>獲利因子</td><td class="num">1.4529</td><td class="num">1.4863</td><td class="num p">+2.30%%</td></tr>
<tr><td>年度夏普</td><td class="num">0.9632</td><td class="num">1.0070</td><td class="num p">+4.55%%</td></tr>
<tr><td>最大策略虧損</td><td class="num">-892,000</td><td class="num">-892,000</td><td class="num">0</td></tr>
<tr><td><b>交易總次數</b></td><td class="num">498</td><td class="num">500</td><td class="num p"><b>+2</b></td></tr>
<tr><td>滑價支付</td><td class="num">1,992,000</td><td class="num">2,000,000</td><td class="num">+8,000</td></tr>
</tbody></table></div>
<div class="note">
<b>整個 +350,400 來自恰好 2 筆交易。</b>滑價欄自證：+8,000 = 2 筆 × 2 口 × 2 邊 × 1,000 NTD。平均每筆新交易 +175,200。
風險面全數未動（MDD、最大平倉虧損、帳戶所需金額、最長持平期間皆 ±0），代表這 2 筆沒有碰到回檔路徑。
但 <b>+6.83%% 建立在 2 筆之上，統計上未確立</b> —— 這與 S16_S A2 是相同形狀（該案「效益僅來自 2 筆、+158,400、配對檢定 1.36 sigma、未達 2 sigma」）。
年度夏普「突破 1.0」同樣由這 2 筆推動，門檻跨越不具獨立意義。
</div>

<h2>資料出處與保留事項</h2>
<ul>
<li><b>細部資料（Bar Magnifier）已停用</b> —— 成交價為 bar 層級推定，非 1 分鐘真實路徑。這正落在專案 SOP 附錄 C「幻想成交」陷阱的射程內。</li>
<li>本機另有一份 <code>L1_TrendLong_v3.1 ... 0.5.xls</code>，為 <b>1 口 / 原始資本 1M</b>，與專案標準（2 口 / 2M）不符，<b>未採用</b>。兩份策略參數完全相同，淨利差異主因為口數。</li>
<li>最大策略虧損 %s 由逐筆權益曲線重算，與報表摘要頁的欄位定義可能不同。</li>
<li>本頁所有數字來自單一次回測，<b>未經 Walk-Forward、Monte Carlo 或 Rule #18 五件套驗證</b>。</li>
<li>既有研究記載 L1 前 10 大贏家佔淨利 104.4%%，逐年數字須配合集中度一併解讀。</li>
</ul>
</div>""" % (CSS, d["period"][0], d["period"][1], sgn(d["total"]), d["n"], d["wr"], d["pf"], f(d["mdd"]),
             W, H, H, BAR, W, H2, H2, LINE, TRS, LABS, f(d["mdd"]))

out = os.path.join(BASE, "L1_yearly_performance.html")
open(out, "w", encoding="utf-8").write(HTML)
print("  generated: %s  (%d bytes)" % (out, len(HTML.encode("utf-8"))))
