#!/usr/bin/env python3
r"""產出回測模組九層討論文件。

```powershell
python tools\modules9.py
```

**這不是規格書，是討論用的現況圖。**
每一層標明：已定案 / 討論中 / 未討論。
未回答的問題**永遠不自動關閉**。
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

C = dict(bg="#16202B", pn="#1D2A38", p2="#223347", ru="#33475C", ink="#DCE6EE",
         mu="#8399AC", up="#6FD1B4", dn="#E8735E", hd="#F0B45A", bk="#8FA8D9")

DONE, TALKING, TODO = "已定案", "討論中", "未討論"


@dataclass(frozen=True)
class Layer:
    id: str
    name: str
    what: str
    items: tuple          # (項目, 狀態, 說明)
    questions: tuple = ()  # 該層待答的問題


LAYERS = (
    Layer("M1", "部位與帳務",
          "部位 → 權益曲線 → 成本 → 保證金。**所有上層都建在它上面**",
          (("PositionBook", DONE, "多腿部位、加權均價、CurrentContracts / MaxContracts"),
           ("Ledger 權益曲線", DONE, "Fill → 逐日損益 → 權益。已實現部分"),
           ("成本模型", DONE, "手續費依商品 + 期交稅依契約金額，分開算"),
           ("未平倉市值 mark-to-market", TODO,
            "**不做，部位開著時的浮虧看不見，MaxDrawdownGuard 在回測裡永遠不觸發**"),
           ("保證金資料", DONE,
            "txfcore/instruments/margin.py。**回測用當前值，不做歷史查表**")),
          ("每支 6 萬本金，微台 2 口的原始保證金佔多少？超過一半就要優先做",
           "未平倉市值要用哪一根 K 棒的收盤價？Data1 還是 1 分 K？",
           "逐日結算的切點已用 trading_day()，未平倉要不要也用同一個切點")),

    Layer("M2", "交易統計",
          "MC12 績效報告的全部欄位。**對帳的基礎，缺一欄就是缺一塊**",
          (("筆數 · 勝率 · PF · 平均盈虧", DONE, "report.py 已有"),
           ("出場標籤歸因", DONE, "每條路徑的筆數 / 勝率 / 淨額"),
           ("連續盈虧 · 持倉根數", TODO, "MC12 有，我沒有"),
           ("多空拆分 Total/Long/Short", TODO,
            "**實戰多空 56:3，回測的方向性從未被檢視**"),
           ("Periodical Returns 年/月", TODO, "MC12 有，我沒有"),
           ("MAE / MFE", TODO,
            "**唯一能回答「停損設得對不對」的東西**"),
           ("Account Size Required", TODO, "= 期初 + MDD 金額")),
          ("MC12 的 22 個欄位，哪些是你真的要看的？",
           "平手（損益恰為 0）算贏、算輸、還是單獨一類？MC 算在虧損側",
           "MAE / MFE 用點數還是金額？點數才能與停損設定直接比較")),

    Layer("M3", "風險度量",
          "回撤族。**定義已與你完整討論並定案，不重開**",
          (("每日動態回撤", DONE,
            "drawdown(t) = (M(t) − V(t)) / M(t)，M 為滾動峰值"),
           ("MDD", DONE, "每日動態回撤曲線中的最高點"),
           ("MDD 金額", DONE, "峰值到谷底的絕對金額"),
           ("水下比例 · 最長回撤", DONE, "已在 drawdown.py"),
           ("組合 MDD", DONE,
            "**逐日損益相加成一條曲線，再做一次 MDD。不可將各支 MDD 相加**"),
           ("含未平倉的逐 K 棒 MDD", TODO,
            "依賴 M1 的 mark-to-market。**部位被砍之前承受的風險是真實的**"),
           ("CDaR · Ulcer · CVaR", TODO, "**未討論，2026-09-08 已刪除**")),
          ("固定口數下，MDD 百分比是期初資金的函數。要不要一律同時印金額？",
           "單支 MDD 的分母：6 萬（該支）還是 18/12 萬（該帳戶）還是 30 萬（總）？",
           "含未平倉的 MDD 要不要做？它是保護器能否在回測中運作的前提")),

    Layer("M4", "風險調整報酬",
          "Sharpe · Sortino · Calmar · Omega",
          (("全部", TODO, "**未討論，2026-09-08 已刪除**"),),
          ("**固定口數下這些指標的意義要重新想**——Sharpe 假設可依權益調整部位，我們不能",
           "無風險利率設多少？年化週期用幾天？序列用逐日還是逐筆？",
           "這些指標你實際上會用來做什麼決策？不會用就不做")),

    Layer("M5", "歸因",
          "誰賺誰賠 · 什麼時候賺 · 什麼市況賺",
          (("出場標籤歸因", DONE, "report.py 已有"),
           ("各支貢獻度", TODO, "需要先定案帳戶結構"),
           ("時間切片 年/月/時段", TODO, ""),
           ("市場狀態拆分", TODO,
            "**L2 停擺 443 天、L4「多頭零交易 = 正確行為」——只有它分得出設計與故障**")),
          ("市場狀態怎麼定義？日線 MA60 之上/下/橫盤？定義必須事前登記",
           "各支貢獻度用組合曲線算還是各自曲線相加？")),

    Layer("M6", "組合",
          "★ **雙帳戶**。2026-09-08 才得知，先前全部按單帳戶做，已刪除",
          (("帳戶結構", TALKING,
            "帳戶 A（多）L1·L3·L5 = 18 萬 · 最大 6 口　"
            "帳戶 B（空）L2·L4 = 12 萬 · 最大 4 口"),
           ("每支本金", DONE, "6 萬名目分攤，總 30 萬。多 20 萬 / 空 10 萬"),
           ("保證金資料資產", DONE,
            "6 則公告 · 鏈結零斷裂 · 比例恆為 20:5:1 · 超範圍拒絕"),
           ("組合權益曲線", TODO, "兩條還是三條？"),
           ("相關性矩陣", TODO, ""),
           ("邊際風險貢獻", TODO, ""),
           ("總曝險 / 淨曝險", TODO, "函數有，沒有呼叫者"),
           ("保證金檢查", TALKING,
            "**裁決：回測不檢查，M6 組合監控才檢查**。"
            "當前值下 A 帳戶滿倉 105%、B 帳戶 140%"),
           ("ProtectionStack 保護器", TODO,
            "**四個保護器寫好了，沒有任何東西呼叫它們**")),
          ("★ 「組合 MDD」在雙帳戶下指什麼？兩個各算 / 相加成一條 / 兩者都算",
           "★ 每支 6 萬的分母怎麼用？單支 6 萬、帳戶 18/12 萬、總體 30 萬",
           "兩個帳戶之間有沒有互相影響？例如一邊爆倉要不要停另一邊",
           "MaxDrawdownGuard 的門檻幾 %？觸發後停進場還是全平？",
           "實戰 76 天的 MDD 是 31.53%——門檻設 25% 會在中途停掉整個組合")),

    Layer("M7", "穩健性",
          "Walk-Forward · Monte Carlo · 參數敏感度 · PBO",
          (("全部", TODO,
            "**明確排最後。成交模型還是樂觀假設時做，是在最佳化一個假的東西**"),),
          ("樣本內外已定案為 06/17 為界。Walk-Forward 要用滾動窗口還是固定？",
           "Monte Carlo 重排交易順序，還是 bootstrap 抽樣？",
           "**這一層要不要做？它不影響上線，只影響對策略的信心**")),

    Layer("M8", "執行品質",
          "滑價 · 延遲 · 成交率。**回測與實戰的橋樑**",
          (("成交模型", TALKING,
            "現在是 fill_mc12：觸價即成交、零滑價。**四個開關已可切換**"),
           ("真實滑價", TODO,
            "**CLAUDE.md 的 1,000 NTD/邊/口 是設定值不是量測值**"),
           ("延遲分布", TODO, "MeasuredLatency 型別已有，**樣本數 0**"),
           ("成交率 / 拒單率", TODO, "需要券商回報")),
          ("★ 實戰紀錄能不能給我？滑價可以從訊號價 vs 成交價量出來",
           "實戰紀錄的三個已知缺陷要先修：分批未合併 30.5%、日期倒置一筆、MDD 分母",
           "延遲要從 MC12 現在的實盤下單錄，還是等 Python 上線再錄？")),

    Layer("M9", "報告",
          "前面全部的呈現",
          (("逐筆 CSV", DONE, "欄位對齊 MC12 交易明細"),
           ("彙總 CSV", DONE, ""),
           ("HTML 報告", TALKING, "report.py 有基礎版"),
           ("血緣戳記印在報告上", TODO, "算得出來，**沒印**"),
           ("MC12 對帳報告", TODO, ""),
           ("實戰對帳報告", TODO, "★ **你的真實目標**")),
          ("報告要給誰看？自己看 / 交出去 / 兩者格式不同",
           "血緣戳記要不要印？印了就不可能拿兩份不同程式碼跑的報告互比")),
)

OPEN_DECISIONS = (
    ("Q1", "「組合 MDD」在雙帳戶下指什麼", "未回答"),
    ("Q2", "每支 6 萬的 MDD 分母怎麼用", "未回答"),
    ("Q3", "保證金要不要進回測", "**已回答**：回測不檢查，M6 才檢查"),
    ("Q4", "回測商品：三種等比例都跑", "**已回答**（小台需修正為 30 萬/支）"),
    ("Q5", "M2 的 22 個欄位哪些真的要", "未回答"),
    ("D1", "多策略怎麼驅動：1 分 K 統一 vs 各支獨立", "未回答"),
    ("D2", "風險層何時介入：每根 K 棒 vs 每張單", "未回答"),
    ("D3", "組合權益何時算：事後 vs 即時", "未回答"),
    ("D5", "成交模型何時換成真實的", "未回答"),
)

# **從 capital.py 讀，不寫死**——否則這張表會與程式碼岔開。
from txfcore.instruments.capital import allocation as _alloc
SCALING = tuple(
    (f"{n} {c}", a.point_value, int(a.per_strategy_nominal), int(a.total), "✓ 單一來源")
    for c, n in (("TMF", "微台"), ("MXF", "小台"), ("TXF", "大台"))
    for a in [_alloc(c)]
)


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "reports")
    out.mkdir(exist_ok=True)
    badge = {DONE: ("ok", "✓"), TALKING: ("pt", "◐"), TODO: ("no", "✗")}
    H = [f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>回測模組九層　討論用</title><style>
body{{margin:0;background:{C['bg']};color:{C['ink']};
font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
font-size:15px;line-height:1.75}}
.w{{max-width:980px;margin:0 auto;padding:36px 18px 90px}}
h1{{font-size:28px;font-weight:600;margin:0 0 4px}}
.sub{{color:{C['mu']};font-size:13.5px;margin:0 0 26px}}
h2{{font-size:20px;margin:44px 0 4px;padding-bottom:9px;
border-bottom:1px solid {C['ru']}}}
h2 .id{{font-family:ui-monospace,monospace;color:{C['hd']};margin-right:12px}}
h2 .w{{font-size:13px;color:{C['mu']};font-weight:400;display:block;margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid {C['ru']};
vertical-align:top}}
th{{color:{C['mu']};font-size:12.5px;background:{C['p2']}}}
td.s{{width:74px;white-space:nowrap;font-size:12.5px}}
td.n{{width:210px}}
.ok{{color:{C['up']}}}.pt{{color:{C['hd']}}}.no{{color:{C['dn']}}}
.q{{border-left:3px solid {C['bk']};background:rgba(143,168,217,.07);
padding:9px 14px;margin:10px 0;font-size:13.5px}}
.q b{{color:{C['bk']}}}.q ul{{margin:4px 0 0;padding-left:1.2em}}
.q li{{margin-bottom:3px}}
.warn{{border-left:3px solid {C['dn']};background:rgba(232,115,94,.07);
padding:10px 14px;margin:12px 0;font-size:13.5px}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:.9em;color:{C['hd']}}}
nav{{display:flex;flex-wrap:wrap;gap:0 18px;padding:11px 0;
border-top:1px solid {C['ru']};border-bottom:1px solid {C['ru']};
margin:0 0 32px;font-size:13px}}
nav a{{color:{C['mu']};text-decoration:none}}nav a:hover{{color:{C['up']}}}
footer{{border-top:1px solid {C['ru']};margin-top:46px;padding-top:16px;
color:{C['mu']};font-size:12.5px}}
</style></head><body><div class="w">
<h1>回測模組　九層</h1>
<p class="sub"><b>這不是規格書，是討論用的現況圖。</b>
每一層標明已定案 / 討論中 / 未討論。<b>未回答的問題永遠不自動關閉。</b></p>
<nav>""" + "".join(f'<a href="#{l.id}">{l.id} {l.name}</a>' for l in LAYERS)
         + '<a href="#open">待決清單</a><a href="#cap">資金配置</a></nav>']

    # 資金配置
    H.append('<h2 id="cap"><span class="id">前提</span>資金配置'
             '<span class="w">2026-09-08 定案：總本金 30 萬，'
             '每支 6 萬，兩個帳戶</span></h2>')
    H.append('<table><thead><tr><th>商品</th><th>點值</th><th>2 口/點</th>'
             '<th>每支本金</th><th>可承受點數</th><th>總本金</th><th>檢查</th>'
             "</tr></thead><tbody>")
    for n, pv, cap, tot, chk in SCALING:
        cls = "ok" if chk.startswith("✓") else "no"
        H.append(f'<tr><td>{n}</td><td>{pv}</td><td>{pv*2}</td>'
                 f'<td>{cap:,}</td><td>{cap//(pv*2):,}</td><td>{tot:,}</td>'
                 f'<td class="{cls}">{chk}</td></tr>')
    H.append("</tbody></table>")
    H.append('<div class="warn"><b>2026-09-08 已定案。</b>'
             '點值比 <code>10 : 50 : 200 = 1 : 5 : 20</code>，'
             '資金按同比例，三者的可承受點數都是 3,000。'
             '小台代號為 <code>MTX</code>（非 MXF）。'
             '詳見 <code>docs/specs/CAPITAL_AND_MARGIN.md</code>。</div>')
    H.append('<table><thead><tr><th>帳戶</th><th>策略</th><th>本金（微台）</th>'
             '<th>最大口數</th></tr></thead><tbody>'
             '<tr><td>A　多單</td><td>L1 · L3 · L5</td><td>200,000</td>'
             '<td>6 口</td></tr>'
             '<tr><td>B　空單</td><td>L2 · L4</td><td>100,000</td>'
             '<td>4 口</td></tr>'
             '<tr><td><b>合計</b></td><td>5 支</td><td><b>300,000</b></td>'
             '<td>10 口（實務上最多 6 口）</td></tr></tbody></table>')

    for l in LAYERS:
        H.append(f'<h2 id="{l.id}"><span class="id">{l.id}</span>{l.name}'
                 f'<span class="w">{l.what}</span></h2>')
        H.append('<table><thead><tr><th class="n">項目</th><th class="s">狀態</th>'
                 "<th>說明</th></tr></thead><tbody>")
        for name, st, note in l.items:
            cls, mk = badge[st]
            H.append(f'<tr><td class="n">{name}</td>'
                     f'<td class="s {cls}">{mk} {st}</td><td>{note}</td></tr>')
        H.append("</tbody></table>")
        if l.questions:
            H.append('<div class="q"><b>待討論</b><ul>'
                     + "".join(f"<li>{q}</li>" for q in l.questions)
                     + "</ul></div>")

    H.append('<h2 id="open"><span class="id">★</span>待決清單'
             '<span class="w">未回答的問題永遠不自動關閉</span></h2>')
    H.append('<table><thead><tr><th>編號</th><th>問題</th><th>狀態</th>'
             "</tr></thead><tbody>")
    for i, q, s in OPEN_DECISIONS:
        cls = "ok" if "已回答" in s else "no"
        H.append(f'<tr><td><code>{i}</code></td><td>{q}</td>'
                 f'<td class="{cls}">{s}</td></tr>')
    H.append("</tbody></table>")

    H.append(f"""<footer>
<p>指令　<code>python tools\\modules9.py</code></p>
<p>MDD 的定義已於先前完整討論並定案，實作在
<code>txfcore/metrics/drawdown.py</code>。<b>2026-09-08 已刪除所有未經討論的
回撤族模組</b>（CDaR · Ulcer · CVaR · 組合模型），因為它們的帳戶結構前提是錯的。</p>
</footer></div></body></html>""")
    p = out / "modules9.html"
    p.write_text("".join(H), encoding="utf-8")
    print(f"已寫出 {p.resolve()}　{p.stat().st_size:,} bytes")
    d = sum(1 for l in LAYERS for _, s, _ in l.items if s == DONE)
    t = sum(len(l.items) for l in LAYERS)
    q = sum(len(l.questions) for l in LAYERS)
    print(f"項目 {d}/{t} 已定案　·　待討論問題 {q + len(OPEN_DECISIONS)} 個")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
