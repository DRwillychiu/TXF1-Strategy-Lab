#!/usr/bin/env python3
"""從規格資料產生統一的 HTML 參考文件。

markdown 是權威來源，HTML 是導覽層。兩者不一致時以 docs/specs/*.md 為準。
"""
from __future__ import annotations

import html
from pathlib import Path

OUT = Path("/mnt/user-data/outputs/txf1_L1-L5_reference.html")

C = {
    "ground": "#16202B", "panel": "#1D2A38", "panel2": "#223347", "rule": "#33475C",
    "ink": "#DCE6EE", "muted": "#8399AC",
    "live": "#6FD1B4", "back": "#8FA8D9", "hard": "#F0B45A", "warn": "#E8735E",
}

# ---------------------------------------------------------------- 五支資料
STRATS = [
    dict(
        key="L2", name="TrendShort", cn="趨勢空頭", order=1,
        d1="60M", d2=None, d3=None, iog="false（未宣告）", dirn="純空",
        types="Market · Stop", pos="單一", exitctl="ExitFired 短路",
        maxorders=1, status="已完成移植",
        uniq=["唯一單資料流", "週線在 60M 流內自行合成", "不需 quotes/align"],
        firsts=[],
        dkeys=[
            ("D-1", "引擎停損錨 Close，自訂停損錨 EntryPrice，不同棒計算", "中"),
            ("D-2", "追蹤停損會放鬆：比較 tsl_line 卻使用 active_tsl，差 ATR×1.1", "高"),
            ("D-3", "SL_Pct 未套用於追蹤路徑", "中"),
            ("D-4", "週線取 12:45 而非註解宣稱的 13:45", "中"),
            ("D-5", "優先級 4 遮蔽 5 與 6，自訂停損單不再掛出", "高"),
            ("D-6", "13:45 那根歸夜盤，出場延到 15:00 開盤", "中"),
            ("D-8", "標頭兩組績效矛盾 77/2.67M vs 78/2.88M", "高"),
        ],
        anchor="完整回測 77–78 筆。<b>自 2025-06-03 起停擺 443 天</b>，"
               "驗收標準是該期間必須零觸發。",
        flat=300,
    ),
    dict(
        key="L4", name="ConsolShort", cn="盤整空頭", order=2,
        d1="15M", d2="60M", d3="Daily", iog="false（明宣告）", dirn="純空",
        types="Market · Stop", pos="單一", exitctl="ExitFired 短路",
        maxorders=1, status="待移植",
        uniq=["誘多狀態機（High 碰箱頂即進入，六根衰減）",
              "SL_Pct 統一套用全部停損路徑",
              "凍結中間變數而非價位"],
        firsts=["多資料流對齊", "變數歷史 v_Stop_Level[1]"],
        dkeys=[
            ("D-1", "SetStopLoss 在盤整判斷內，SetStopContract 在頂層", "中"),
            ("D-2", "凍結 ATR 與箱頂等中間變數，與 L1/L2/L3 凍結價位不同", "中"),
            ("D-3", "BreakExit 只認向上突破", "低"),
            ("D-4", "v_Stop_Level 未列入空手重置清單", "低"),
            ("D-5", "兩組績效無法調和 877,200 vs 894,400，同為 79 筆", "高"),
        ],
        anchor="完整回測 <b>79 筆</b>。標頭明載「多頭市場零交易 = 正確行為」，"
               "v15/v16 研究線全部失敗。",
        flat=415,
    ),
    dict(
        key="L3", name="ConsolLong", cn="盤整多頭", order=3,
        d1="15M", d2="60M", d3="Daily", iog="false（未宣告）", dirn="純多",
        types="Market · Stop · <b>Limit</b>", pos="單一",
        exitctl="無 ExitFired，bracket 常態兩張",
        maxorders=4, status="待移植",
        uniq=["箱體收縮率 0.1（L4 是 0.7，差七倍）",
              "開盤封鎖擋的是「成交會落在禁區」的訊號",
              "報酬風險比閘門"],
        firsts=["Limit 單", "OCO 撤銷語意"],
        dkeys=[
            ("D-1", "SetStopContract 在盤整判斷內", "中"),
            ("D-2", "箱體失效後 TP 與 SL 兩張都不再掛出，只剩市價", "中"),
            ("D-3", "CL_Kill 在 else-if 鏈外，與 L1 的 J-3 同型", "中"),
            ("D-4", "v15.0 376 筆 vs v15.1 anchor 360 筆，卻宣稱零行為變更", "高"),
        ],
        anchor="v15.0 376 筆 / 2,446,000；v15.1 anchor 360 筆 / 1,389,600。"
               "<b>兩者矛盾，須先釐清測試條件。</b> "
               "re-entry 登記為區間 20 ≤ n ≤ 115。",
        flat=415,
    ),
    dict(
        key="L5", name="BreakoutLong", cn="盤整多頭突破", order=4,
        d1="15M", d2="<b>Daily</b>", d3="Weekly", iog="false（未宣告）", dirn="純多",
        types="Market · Stop · <b>Limit</b>", pos="<b>雙腿 + 40% 分批</b>",
        exitctl="無 ExitFired，每腿獨立",
        maxorders=8, status="待移植",
        uniq=["Data2 是日線，四日箱（L3/L4 是 60M）",
              "箱體失效用 High/Low（L3/L4 用 Close）",
              "28 處 from Entry 綁定，全案唯一",
              "SL_Pct 錨在 v_Box_Btm（其餘四支錨在 Close）",
              "週線濾網用 AND（L1 用 OR）"],
        firsts=["部分口數出場", "from Entry 腿綁定",
                "CurrentContracts / MaxContracts", "TickSize = MinMove/PriceScale",
                "引擎停損作為獨立出場類型"],
        dkeys=[
            ("D-1", "箱體失效用 High/Low，與 L3/L4 的 Close 不同", "中"),
            ("D-2", "SL_Pct 上限錨在 v_Box_Btm", "中"),
            ("D-3", "引擎停損可在無任何出場單的情況下平倉，171 筆中 1 筆", "高"),
            ("D-5", "v19.6 的績效基線，v19.7 之後未重測", "中"),
        ],
        anchor="v19.6 基線 162 筆 / 1,713,000 / PF 2.136。"
               "MC12 於 2026-08-26 執行為 <b>171 筆進場</b>。"
               "<b>v19.7 後未重測。</b>",
        flat=415,
    ),
    dict(
        key="L1", name="TrendLong", cn="趨勢多頭", order=5,
        d1="<b>45M</b>", d2="Daily", d3="Weekly", iog="<b>true</b>", dirn="純多",
        types="Market · Stop", pos="單一",
        exitctl="無 ExitFired",
        maxorders=3, status="待移植",
        uniq=["五支唯一 IOG = true",
              "IntraBarPersist 三個變數",
              "BarStatus(1)=2 守衛切分收盤與盤中",
              "Crosses Over（唯一使用穿越運算子）",
              "單一停損架構：三層取最高合成一個價位",
              "45M 網格，全案唯一",
              "週線濾網用 OR（L5 用 AND）"],
        firsts=["tick 級評估", "IntraBarPersist", "BarStatus 守衛"],
        dkeys=[
            ("D-1", "v_Prev_MP 在守衛外，IOG 下記錄 tick 而非 bar", "中"),
            ("D-2", "兩組 V2.7 績效 476 筆 vs 451 筆未調和", "高"),
            ("D-3", "J-3：Manual_Kill_Switch 在鏈外，一根最多三張市價單", "高"),
            ("D-4", "IOG 行為未在 MC 實測，且 MC 匯不出 tick 級狀態", "高"),
            ("D-6", "標籤路由用 0.001 浮點容差", "低"),
        ],
        anchor="V2.7 476 筆 / 3,018,400 與 451 筆 / 3,938K 兩組。"
               "V3.2 明載舊筆數「<b>NOT a valid baseline</b>」，"
               "須<b>兩次執行</b>重建 anchor。",
        flat=345,
    ),
]

CAPS = [
    ("多資料流 of Data2/Data3", "L1 L3 L4 L5"),
    ("策略變數歷史 v_X[1]", "全部"),
    ("MarketPosition[1] 冷卻計數", "L4"),
    ("Limit 單", "L3 L5"),
    ("部分口數 N contracts", "L5"),
    ("from Entry 腿綁定", "L5"),
    ("CurrentContracts / MaxContracts", "L5"),
    ("TickSize = MinMove/PriceScale", "L5"),
    ("IOG tick 生命週期", "L1"),
    ("IntraBarPersist", "L1"),
    ("BarStatus(1)=2 守衛", "L1"),
    ("成交模型 fill", "全部"),
    ("Fill → 權益曲線", "全部"),
    ("換月 / 連續合約", "全部"),
]

SAME_DIFF = [
    ("箱體失效判定", "L3 L4 用 <code>Close of Data2</code>",
     "L5 用 <code>High/Low of Data2</code>", "L5 的箱體脆弱得多，影線碰到就終止"),
    ("SL_Pct 上限錨點", "L1–L4 錨在 <code>Close</code>",
     "L5 錨在 <code>v_Box_Btm</code>", "未見註解說明理由"),
    ("SetStopContract 位置", "L1 L4 L5 頂層無條件",
     "L2 在條件內、L3 在盤整判斷內", "L5 註解寫 must be outside conditional"),
    ("箱體收縮率", "L3 是 0.1（極窄）", "L4 是 0.7、L5 是 0.6", "同形狀，鬆緊差七倍"),
    ("週線濾網邏輯", "L1 用 <b>OR</b>", "L5 用 <b>AND</b>",
     "L1 註解：趨勢策略需在起點就進場，AND 會錯過早期多頭"),
    ("深夜封鎖區間", "L4 是 200–500", "L5 是 400–500",
     "L4 夜盤淨 −120,800、L5 淨 +87,800，方向相反"),
    ("凍結對象", "L1 L2 L3 凍結最終價位", "L4 L5 凍結中間變數",
     "當中間變數在持倉期間變動時兩者分岔"),
    ("Kill 開關位置", "L2 L4 L5 在 else-if 鏈上", "L1 L3 在鏈外獨立 if",
     "鏈外者一根可多發一張市價單"),
]

SHARED = [
    ("Holiday_Tail 63 筆陣列值", True, "五份逐筆相同"),
    ("結算日偵測", True, "DayOfWeek=3 and DayOfMonth in [15,21]"),
    ("Settlement_Flat_Time", True, "五支皆 1230"),
    ("Registry_Valid_Until", True, "五支皆 1270101"),
    ("註冊表過期 fail-safe", True, "邏輯一致"),
    ("Holiday_Flat_Time", False, "345 / 300 / 415 / 415 / 415，隨網格而異"),
    ("初始化守衛", False, "L1 用 Init_Done，其餘用 CurrentBar = 1"),
    ("假日偵測區塊", False, "L1 包在 BarStatus 內，其餘在頂層"),
    ("強制平倉區塊結構", False, "四種不同寫法"),
]

PKGS = [
    ("層 0 基礎設施", [
        ("contracts", "三顆插頭 + 十個 port", True),
        ("types", "bar · orders · mctime · stateful", True),
        ("instruments", "商品主檔 · TickSize · 回測資金", True),
        ("costs", "手續費 + 期交稅", True),
        ("metrics", "drawdown · portfolio_mdd", True),
        ("journal", "append-only 事件日誌", False),
        ("timing", "Clock + 三戳記", False),
        ("state", "持久化 + KillSwitch", False),
        ("lineage", "血緣雜湊", False),
        ("obs", "心跳 + 觸發次數監控", False),
    ]),
    ("共用支撐", [
        ("indicators", "ATR · SMA · EMA · ZLEMA · CrossesOver", True),
        ("tradecal", "假日 · 結算 · 過期", True),
        ("engine", "context · orders · position · protective · fill · accounting", False),
    ]),
    ("層 1 報價", [("quotes", "session · bars · align · continuous · history", False)]),
    ("層 2 策略", [("strategies", "base ✓ · l2 ✓ · l4 · l3 · l5 · l1", True)]),
    ("層 3 風險", [("risk", "limits · reconcile", False)]),
    ("層 5 通知下單", [("notify", "message · channels · dedupe · heartbeat", False),
                   ("broker", "券商 adapter", False)]),
    ("旁路", [("parity", "mc_report · replay · diff · golden", False)]),
    ("組裝根", [("runtime", "backtest.py · live.py", False)]),
]


# ---------------------------------------------------------------- SVG
def strat_svg(s: dict) -> str:
    """每支的資料流帶狀圖。"""
    streams = [x for x in (s["d1"], s["d2"], s["d3"]) if x]
    n = len(streams)
    H = 150 + n * 8
    hl = C["hard"]
    out = [f'<svg viewBox="0 0 900 {H}" xmlns="http://www.w3.org/2000/svg" role="img">']
    out.append(f'<rect width="900" height="{H}" fill="{C["ground"]}"/>')

    def box(x, y, w, h, title, sub, color=None, dash=False):
        st = color or C["rule"]
        d = ' stroke-dasharray="5 4"' if dash else ""
        r = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" '
             f'fill="{C["panel"]}" stroke="{st}" stroke-width="1.2"{d}/>']
        r.append(f'<text x="{x+w/2}" y="{y+20}" text-anchor="middle" '
                 f'font-size="12" font-weight="700" fill="{color or C["ink"]}">{title}</text>')
        for i, line in enumerate(sub):
            r.append(f'<text x="{x+w/2}" y="{y+37+i*15}" text-anchor="middle" '
                     f'font-size="10" fill="{C["muted"]}">{line}</text>')
        return "".join(r)

    def arrow(x1, y1, x2, y2, color=None):
        col = color or C["muted"]
        return (f'<path d="M{x1},{y1} L{x2-7},{y2}" stroke="{col}" stroke-width="1.4" '
                f'fill="none"/><path d="M{x2-7},{y2-4} L{x2},{y2} L{x2-7},{y2+4} Z" fill="{col}"/>')

    ymid = 30 + (n * 34) / 2

    # 插頭一
    out.append(box(10, 30, 108, n * 34 + 10, "插頭一", ["回測 1分K", "即時 tick"], C["live"]))
    # 層 1
    for i, st in enumerate(streams):
        lbl = st.replace("<b>", "").replace("</b>", "")
        col = hl if "<b>" in st else None
        out.append(box(140, 30 + i * 34, 108, 28, lbl,
                       [], col))
    out.append(f'<text x="194" y="{30+n*34+16}" text-anchor="middle" font-size="10" '
               f'fill="{C["muted"]}">層 1 quotes</text>')
    out.append(arrow(120, ymid, 138, ymid, C["live"]))

    # 支撐
    out.append(box(272, 30, 118, n * 34 + 10, "共用支撐",
                   ["indicators", "tradecal", "engine"], C["back"]))
    out.append(arrow(250, ymid, 270, ymid))

    # 層 2
    out.append(box(414, 30, 150, n * 34 + 10, f'{s["key"]} {s["cn"]}',
                   [s["dirn"], f'IOG {s["iog"].split("（")[0]}'], C["live"]))
    out.append(arrow(392, ymid, 412, ymid))

    # 層 3
    out.append(box(588, 30, 100, n * 34 + 10, "層 3 風險", ["決定口數"], C["live"]))
    out.append(arrow(566, ymid, 586, ymid, C["live"]))

    # 插頭二
    mo = s["maxorders"]
    col2 = C["warn"] if mo > 1 else C["live"]
    out.append(box(712, 30, 176, n * 34 + 10, "插頭二",
                   [s["types"].replace("<b>", "").replace("</b>", ""),
                    f"一根最多 {mo} 張"], col2))
    out.append(arrow(690, ymid, 710, ymid, C["live"]))

    y2 = 30 + n * 34 + 34
    out.append(f'<text x="10" y="{y2}" font-size="10.5" fill="{C["hard"]}">'
               f'獨有：{" · ".join(x for x in s["uniq"][:2])}</text>')
    if s["firsts"]:
        out.append(f'<text x="10" y="{y2+17}" font-size="10.5" fill="{C["warn"]}">'
                   f'首次需要：{" · ".join(s["firsts"])}</text>')
    out.append("</svg>")
    return "".join(out)


def stack_svg() -> str:
    """執行層能力疊加圖。"""
    rows = [
        ("L2", "Market · Stop · ExitFired 單張", "最小集合", C["live"]),
        ("L4", "＋ 多資料流對齊 · 變數歷史 [1]", "", C["live"]),
        ("L3", "＋ Limit 單 · OCO 撤銷", "首次多張並存", C["hard"]),
        ("L5", "＋ 多腿 · 分批 · from Entry · TickSize", "完整 OMS", C["hard"]),
        ("L1", "＋ tick 生命週期 · IntraBarPersist · BarStatus", "最難", C["warn"]),
    ]
    H = 40 + len(rows) * 46
    o = [f'<svg viewBox="0 0 880 {H}" xmlns="http://www.w3.org/2000/svg" role="img">',
         f'<rect width="880" height="{H}" fill="{C["ground"]}"/>']
    for i, (k, txt, note, col) in enumerate(rows):
        y = 20 + i * 46
        w = 240 + i * 150
        o.append(f'<rect x="60" y="{y}" width="{w}" height="34" rx="4" '
                 f'fill="{C["panel"]}" stroke="{col}" stroke-width="1.2"/>')
        o.append(f'<text x="24" y="{y+22}" font-size="15" font-weight="700" fill="{col}">{k}</text>')
        o.append(f'<text x="74" y="{y+22}" font-size="11.5" fill="{C["ink"]}">{txt}</text>')
        if note:
            o.append(f'<text x="{70+w}" y="{y+22}" font-size="10.5" fill="{col}">{note}</text>')
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- HTML
def esc(x: str) -> str:
    return x


def build() -> str:
    p = []
    a = p.append

    a(f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TXF1 L1-L5 分層參考</title><style>
:root{{--g:{C['ground']};--pn:{C['panel']};--p2:{C['panel2']};--ru:{C['rule']};
--ink:{C['ink']};--mu:{C['muted']};--lv:{C['live']};--bk:{C['back']};--hd:{C['hard']};--wn:{C['warn']};
--sans:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
--mono:"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--g);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.75}}
.wrap{{max-width:1000px;margin:0 auto;padding:48px 22px 96px}}
.meta{{font-family:var(--mono);font-size:12px;color:var(--mu);letter-spacing:.05em;margin:0 0 14px}}
h1{{font-size:clamp(26px,4.2vw,40px);line-height:1.24;font-weight:600;margin:0 0 10px}}
.stamp{{font-family:var(--mono);font-size:11.5px;color:var(--mu);margin:0 0 34px}}
nav{{display:flex;flex-wrap:wrap;gap:0 20px;padding:13px 0;border-top:1px solid var(--ru);
border-bottom:1px solid var(--ru);margin:0 0 48px;font-size:13px}}
nav a{{color:var(--mu);text-decoration:none;border-bottom:1px solid transparent;padding-bottom:2px}}
nav a:hover{{color:var(--lv);border-bottom-color:var(--lv)}}
section{{margin:0 0 74px;scroll-margin-top:16px}}
h2{{font-size:22px;font-weight:600;margin:0 0 6px;padding-bottom:11px;border-bottom:1px solid var(--ru)}}
h2 .n{{font-family:var(--mono);font-size:13px;color:var(--mu);margin-right:13px;font-weight:400}}
h3{{font-size:17px;font-weight:600;margin:36px 0 10px}}
h3 .k{{font-family:var(--mono);color:var(--hd);margin-right:10px}}
.lede{{color:var(--mu);font-size:14.5px;margin:12px 0 24px;max-width:46em}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:0 0 10px}}
th,td{{text-align:left;padding:9px 11px;border-bottom:1px solid var(--ru);vertical-align:top}}
th{{color:var(--mu);font-size:12.5px;font-weight:600;background:var(--p2)}}
td.m{{font-family:var(--mono);font-size:12.5px;white-space:nowrap}}
code{{font-family:var(--mono);font-size:.9em;color:var(--hd)}}
.ok{{color:var(--lv)}} .no{{color:var(--wn)}} .pt{{color:var(--hd)}}
svg{{display:block;width:100%;height:auto;margin:6px 0 4px}}
.scroll{{overflow-x:auto}} .scroll svg{{min-width:820px}}
.card{{border:1px solid var(--ru);background:var(--pn);padding:0;margin:0 0 26px}}
.card-hd{{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px;padding:15px 20px;
background:var(--p2);border-bottom:1px solid var(--ru)}}
.card-hd .k{{font-family:var(--mono);font-size:19px;font-weight:700;color:var(--lv)}}
.card-hd .nm{{font-size:16px;font-weight:600}}
.card-hd .or{{margin-left:auto;font-family:var(--mono);font-size:11.5px;color:var(--mu)}}
.card-bd{{padding:16px 20px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px 26px;margin:0 0 18px}}
.grid h4{{font-size:11.5px;color:var(--mu);font-weight:600;margin:0 0 7px;
padding-bottom:5px;border-bottom:1px solid var(--ru)}}
.grid ul{{margin:0;padding-left:1.15em}} .grid li{{font-size:13px;line-height:1.6;margin-bottom:4px}}
.d li{{color:var(--mu)}} .d b{{color:var(--ink)}}
.sev{{font-family:var(--mono);font-size:10.5px;padding:1px 6px;border-radius:2px;margin-left:6px}}
.sev.h{{color:var(--wn);border:1px solid var(--wn)}}
.sev.m{{color:var(--hd);border:1px solid var(--hd)}}
.sev.l{{color:var(--mu);border:1px solid var(--ru)}}
.note{{border-left:3px solid var(--hd);background:rgba(240,180,90,.06);padding:11px 15px;
font-size:13.5px;line-height:1.62;margin:0 0 16px}}
.note.w{{border-left-color:var(--wn);background:rgba(232,115,94,.06)}}
.note.b{{border-left-color:var(--bk);background:rgba(143,168,217,.06)}}
.box{{border:1px solid var(--hd);padding:20px 24px;background:rgba(240,180,90,.05);margin:26px 0 0}}
.box p{{margin:0;font-size:16px;line-height:1.68;font-weight:500}}
.box p+p{{margin-top:10px;font-size:13.5px;font-weight:400;color:var(--mu)}}
.box.w{{border-color:var(--wn);background:rgba(232,115,94,.06)}}
footer{{border-top:1px solid var(--ru);padding-top:20px;color:var(--mu);font-size:13px}}
footer p{{margin:0 0 7px;max-width:46em}}
@media(max-width:640px){{.wrap{{padding:30px 14px 56px}}table{{font-size:12.5px}}th,td{{padding:7px 6px}}}}
</style></head><body><div class="wrap">""")

    a('<p class="meta">TXF1 · L1–L5 · PowerLanguage → Python</p>')
    a("<h1>分層參考</h1>")
    a('<p class="stamp">2026-09-06　·　五支原始碼反推　·　'
      '權威來源為 <code>docs/specs/*.md</code>，本檔為導覽層</p>')

    a('<nav>'
      '<a href="#quick">速查</a>'
      '<a href="#stack">能力疊加</a>'
      '<a href="#pkg">系統分層</a>'
      '<a href="#each">各支分層</a>'
      '<a href="#same">看似相同</a>'
      '<a href="#shared">共用範圍</a>'
      '<a href="#caps">能力矩陣</a>'
      '<a href="#block">擋路項</a>'
      '</nav>')

    # ---- 速查
    a('<section id="quick"><h2><span class="n">一</span>五支速查</h2>')
    a('<p class="lede">按移植順序排列。順序依實測複雜度，不是猜測——'
      '執行層的能力必須按這個順序疊加。</p>')
    a('<div class="scroll"><table><thead><tr>'
      '<th>順位</th><th>策略</th><th>Data1 / 2 / 3</th><th>IOG</th>'
      '<th>單型</th><th>部位</th><th>出場控制</th><th>最多單數</th><th>狀態</th>'
      "</tr></thead><tbody>")
    for s in sorted(STRATS, key=lambda x: x["order"]):
        ds = " / ".join(x for x in (s["d1"], s["d2"] or "—", s["d3"] or "—"))
        st = f'<span class="ok">{s["status"]}</span>' if "完成" in s["status"] else s["status"]
        a(f'<tr><td class="m">{s["order"]}</td>'
          f'<td class="m"><b>{s["key"]}</b> {s["cn"]}</td>'
          f'<td class="m">{ds}</td><td class="m">{s["iog"]}</td>'
          f'<td class="m">{s["types"]}</td><td>{s["pos"]}</td>'
          f'<td>{s["exitctl"]}</td>'
          f'<td class="m">{"<b class=no>" + str(s["maxorders"]) + "</b>" if s["maxorders"]>1 else s["maxorders"]}</td>'
          f"<td>{st}</td></tr>")
    a("</tbody></table></div>")
    a('<div class="note b"><b>Holiday_Flat_Time 不共用</b>：'
      "L1=345 · L2=300 · L3/L4/L5=415。跟著各自的 K 棒網格走，是 config 不是常數。</div>")
    a("</section>")

    # ---- 疊加
    a('<section id="stack"><h2><span class="n">二</span>執行層能力疊加</h2>')
    a('<p class="lede">每一支只新增它自己需要的能力。L2 通過時執行層只需最小集合，'
      "到 L5 才需要多腿部位，到 L1 才需要 tick 生命週期。</p>")
    a(f'<div class="scroll">{stack_svg()}</div>')
    a('<div class="note"><code>engine/context.py</code> 的資料模型仍須從第一天就以 '
      "tick 為原生、bar close 為特例。否則做到 L1 要回頭重構，前四支已通過的對帳全部重跑。</div>")
    a("</section>")

    # ---- 系統分層
    a('<section id="pkg"><h2><span class="n">三</span>系統分層</h2>')
    a('<p class="lede">20 套件。ports-and-adapters：層 0 定義介面，各層提供實作。'
      "三顆插頭就是三個 Protocol，鐵則因此不是紀律而是型別。</p>")
    a('<div class="scroll"><table><thead><tr><th style="width:16%">層</th>'
      '<th style="width:15%">套件</th><th>內容</th><th style="width:70px">狀態</th>'
      "</tr></thead><tbody>")
    for layer, items in PKGS:
        for i, (pkg, desc, done) in enumerate(items):
            lc = layer if i == 0 else ""
            mark = '<span class="ok">✓</span>' if done else '<span class="pt">○</span>'
            a(f'<tr><td>{lc}</td><td class="m">{pkg}</td><td>{desc}</td>'
              f"<td>{mark}</td></tr>")
    a("</tbody></table></div>")
    a('<div class="note"><b>兩條禁令由 CI 機械檢查</b>（<code>tests/test_layer_boundaries.py</code>，39 項）：'
      "<br>一、<code>strategies/</code> 與 <code>risk/</code> 不得 import "
      "<code>quotes/</code> <code>notify/</code> <code>broker/</code>。"
      "<br>二、層 0 不得依賴其他套件。</div>")
    a("</section>")

    # ---- 各支
    a('<section id="each"><h2><span class="n">四</span>各支分層</h2>')
    a('<p class="lede">每支一張資料流帶狀圖，加獨有特徵與已知落差。'
      "完整規格見 <code>docs/specs/Lx_layers.md</code> 與 "
      "<code>docs/specs/Lx_&lt;Name&gt;_spec.md</code>。</p>")
    for s in sorted(STRATS, key=lambda x: x["order"]):
        a('<div class="card">')
        a(f'<div class="card-hd"><span class="k">{s["key"]}</span>'
          f'<span class="nm">{s["name"]} · {s["cn"]}</span>'
          f'<span class="or">移植順位 {s["order"]}　·　'
          f'Holiday_Flat_Time {s["flat"]}</span></div>')
        a('<div class="card-bd">')
        a(f'<div class="scroll">{strat_svg(s)}</div>')
        a('<div class="grid">')
        a("<div><h4>獨有特徵</h4><ul>")
        for u in s["uniq"]:
            a(f"<li>{u}</li>")
        a("</ul></div>")
        if s["firsts"]:
            a("<div><h4>首次需要的能力</h4><ul>")
            for f in s["firsts"]:
                a(f'<li class="pt">{f}</li>')
            a("</ul></div>")
        a("</div>")
        a('<div class="grid"><div style="grid-column:1/-1"><h4>已知落差</h4><ul class="d">')
        for code, txt, sev in s["dkeys"]:
            cls = {"高": "h", "中": "m", "低": "l"}[sev]
            a(f'<li><b>{code}</b> {txt}<span class="sev {cls}">{sev}</span></li>')
        a("</ul></div></div>")
        a(f'<div class="note">對帳基準：{s["anchor"]}</div>')
        a("</div></div>")
    a("</section>")

    # ---- 看似相同
    a('<section id="same"><h2><span class="n">五</span>看似相同其實不同</h2>')
    a('<p class="lede">程式碼形狀幾乎一致、語意不同。這是移植最容易踩的一類，'
      "因為照抄看起來是對的。</p>")
    a('<div class="scroll"><table><thead><tr><th style="width:16%">項目</th>'
      "<th>一邊</th><th>另一邊</th><th>後果</th></tr></thead><tbody>")
    for item, a1, a2, why in SAME_DIFF:
        a(f"<tr><td><b>{item}</b></td><td>{a1}</td><td>{a2}</td>"
          f'<td class="m" style="white-space:normal">{why}</td></tr>')
    a("</tbody></table></div></section>")

    # ---- 共用範圍
    a('<section id="shared"><h2><span class="n">六</span>共用範圍</h2>')
    a('<p class="lede">原規劃假設假日偵測 / 結算偵測 / 強制平倉為五支共用。'
      "逐份比對後：<b>共用的是資料與偵測，不共用的是時間常數與執行結構。</b></p>")
    a('<table><thead><tr><th style="width:30%">元件</th><th style="width:80px">共用</th>'
      "<th>說明</th></tr></thead><tbody>")
    for name, yes, note in SHARED:
        m = '<span class="ok">✓</span>' if yes else '<span class="no">✗</span>'
        a(f"<tr><td>{name}</td><td>{m}</td><td>{note}</td></tr>")
    a("</tbody></table>")
    a('<div class="note w">若照原規劃把整個區塊抽成共用模組，'
      "<b>會改變其中至少三支的行為</b>。<br>"
      "<code>tradecal/</code> 可抽出：註冊表、假日偵測、結算偵測、過期判定。<br>"
      "不可抽出：<code>Holiday_Flat_Time</code>、強制平倉的下單區塊。</div>")
    a("</section>")

    # ---- 能力矩陣
    a('<section id="caps"><h2><span class="n">七</span>能力矩陣</h2>')
    a('<p class="lede">全部由五份原始碼實際用到的東西反推，不是設計偏好。</p>')
    a('<table><thead><tr><th style="width:44%">能力</th><th>誰需要</th></tr></thead><tbody>')
    for cap, who in CAPS:
        a(f"<tr><td>{cap}</td><td class=\"m\">{who}</td></tr>")
    a("</tbody></table></section>")

    # ---- 擋路
    a('<section id="block"><h2><span class="n">八</span>擋路項</h2>')
    a('<div class="box w"><p>五支的績效基準全部不可信。</p>'
      "<p>五支都必須重跑 MC 報告並存檔（帶時間戳 + SHA-256）才能對帳。"
      "這是唯一同時卡住五支的東西。</p></div>")
    a('<table style="margin-top:22px"><thead><tr><th style="width:80px">策略</th>'
      "<th>問題</th></tr></thead><tbody>")
    for s in sorted(STRATS, key=lambda x: x["order"]):
        bad = [d for d in s["dkeys"] if d[2] == "高" and
               any(k in d[1] for k in ("績效", "筆", "anchor", "基線"))]
        txt = bad[0][1] if bad else "—"
        a(f'<tr><td class="m"><b>{s["key"]}</b></td><td>{txt}</td></tr>')
    a("</tbody></table>")

    a('<h3>待決三題</h3><table><thead><tr><th style="width:44px">#</th><th>問題</th>'
      "<th>影響</th></tr></thead><tbody>"
      '<tr><td class="m">1</td><td>小台回測資金 500,000 是按點值比例推的，非裁決值</td>'
      "<td>MDD 百分比基準</td></tr>"
      '<tr><td class="m">2</td><td>L5 兩腿同時成交時 <code>MaxContracts</code> 如何決定</td>'
      "<td>層 3 的 sizing 邏輯</td></tr>"
      '<tr><td class="m">3</td><td>五支的死碼（L1 re-entry · L3 BE · L4 BE/SP · L5 SP）是否移植</td>'
      "<td>工作量</td></tr>"
      "</tbody></table>")

    a('<h3>下一步</h3>'
      '<div class="note">階段 A 需要 <b>MC12 匯出的 1 分 K 前 10 行</b>，'
      "用來確認欄位格式與時間戳語意（開盤標記或收盤標記——弄錯就是整體偏移一分鐘且不報錯）。</div>")
    a("</section>")

    a("<footer>"
      "<p>本檔由 <code>docs/specs/*.md</code> 產生，是導覽層。"
      "兩者不一致時以 markdown 為準。</p>"
      "<p>所有內容由五份 PowerLanguage 原始碼反推。"
      "承諾與斷言的驗證為靜態閱讀，未在 MC 上實測；"
      "L1 的 IOG 行為無法用歷史驗證，須改採平行前向驗證。</p>"
      "<p>五支的績效數字全部引用自各自標頭，且各自都有內部矛盾或未重測。"
      "對帳前必須重跑並存檔。</p>"
      "</footer></div></body></html>")
    return "".join(p)


OUT.write_text(build(), encoding="utf-8")
print(f"written {OUT}  {OUT.stat().st_size:,} bytes")
