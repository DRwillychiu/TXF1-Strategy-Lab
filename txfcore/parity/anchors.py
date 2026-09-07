"""MC12 對帳基準 —— 來自 repo 內的 anchor result 文件，非 .pla 標頭轉述。

**2026-09-07 發現**：我先前一直說「標頭的兩組數字互相矛盾、來源 Excel 不在 repo」，
但從未去找 repo 裡有沒有別的紀錄。實際上 `docs/research/` 下有一批
**帶日期、被 git 追蹤的 anchor result 文件**，記錄了逐格比對的結果。

那才是可信的基準。標頭是事前登記或事後轉述，會漂移；
anchor 文件是某一次具體執行的產物，且註明了匯出時間。

## 我先前搞錯的兩件事

**一、L4 的 79 是 `CS_Entry` 的數量，不是總筆數。**
真正的 anchor 是 **82**（79 CS_Entry + 3 CS_ReEntry）。
我拿 79 當總數比，於是「多 4 筆」——實際只多 1 筆。

**二、L2 的進場拆分是 57 / 20，不是標頭的 55 / 22。**
標頭那組是事前登記，實測推翻了它（`L2_v5.4_label_anchor_result_20260825.md` §1）。

## ★ 回測視窗是第一級參數，而且每支不同

2026-09-07 實測 L3：同一份程式碼、同一份資料，

```
2019-12-16 ~ 2026-07-25   399 筆   vs MC 376   +23  (+6.1%)
2020-05-12 ~ 2026-07-25   379 筆   vs MC 376   +3   (+0.8%)
```

**視窗移動就從 +23 變成 +3。** L3 的標頭明載
「Backtest: 2020/05/12 - 2026/07/04」，而我先前對三支都用 2019-12-16
（那是 L1 的基準起點）。

> **視窗的影響比我追了一整天的成交假設、對齊規則、換月假象加起來都大。**

## 資料區間的影響

MC 報告有匯出日期，我的資料截止 2026-09-05。**匯出日之後的交易是我多的。**

2026-09-07 實測：L2 與 L4 在匯出日之後皆為 0 筆，**這次不受影響**。
但 L3 / L5 / L1 移植時必須重查——`check_window_effect()` 就是做這件事的。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Anchor:
    """一次具體的 MC12 執行結果。"""

    strategy: str
    version: str
    source_doc: str
    export_date: int          # MC 報告匯出日，民國年 YYYMMDD
    total_trades: int
    net_profit: float
    profit_factor: float
    # 回測視窗。**每支不同，且影響極大** —— L3 實測 +23 vs +3 筆的差別
    backtest_start: int = 0
    backtest_end: int = 0     # 0 = 用 export_date
    win_rate: float | None = None
    max_drawdown: float | None = None
    entry_labels: dict[str, int] = field(default_factory=dict)
    exit_labels: dict[str, int] = field(default_factory=dict)
    notes: str = ""


# ---------------------------------------------------------------------------
# L2 v5.4 —— docs/research/L2_v5.4_label_anchor_result_20260825.md
#
# 該文件的最強證據：24 個彙總指標 24/24 相同，逐筆 8 欄位中 7 欄零差異，
# 只有 entry_sig 變（77 筆中 20 筆）。**純標籤改動，行為零變化。**
# ---------------------------------------------------------------------------
L2_V54 = Anchor(
    strategy="L2_TrendShort", version="v5.4",
    source_doc="docs/research/L2_v5.4_label_anchor_result_20260825.md",
    export_date=1260825,
    total_trades=77,
    net_profit=2_670_000,
    profit_factor=2.7456,
    win_rate=41.6,
    max_drawdown=-484_400,
    backtest_start=1191216,   # 未載明，沿用 L1 的基準起點
    entry_labels={"TS_Entry": 57, "TS_ReEntry": 20},
    notes=(
        "re-entry 20 筆 / 勝率 45.0% / 淨額 +225,200 / 佔淨利 8.4%。"
        "定義是「訊號那根的 Close <= 前筆成交價」——**下單當下可判定**。"
        "離線用成交價比較的版本在 PowerLanguage 裡不可實作。"
    ),
)

# ---------------------------------------------------------------------------
# L4 v14.7 —— docs/research/L4_v14.7_anchor_result_20260826.md
#
# 3,735 列零差異，全部 4 處差異 = 3 筆改標 + 1 個策略名稱。
# **總筆數 82，其中 CS_Entry 79 + CS_ReEntry 3。**
# ---------------------------------------------------------------------------
L4_V147 = Anchor(
    strategy="L4_ConsolShort", version="v14.7",
    source_doc="docs/research/L4_v14.7_anchor_result_20260826.md",
    export_date=1260826,
    total_trades=82,
    net_profit=800_000,
    profit_factor=1.4150,
    win_rate=42.6829,
    max_drawdown=-789_200,
    backtest_start=1191216,   # 未載明
    entry_labels={"CS_Entry": 79, "CS_ReEntry": 3},
    exit_labels={"CS_SL": 38, "CS_BreakExit": 30, "CS_TimeExit": 14},
    notes=(
        "re-entry 3 筆 / 勝率 66.7% / 淨額 +15,600 / 佔淨利 1.9%。"
        "**L4 的二次進場是雜訊，不是優化標的。**"
        "定義是「同箱型第 2 次以上」——結構定義，不是時間間隔定義。"
    ),
)

# ---------------------------------------------------------------------------
# L4 v18.0 —— docs/research/L4_v18.0_reentry_zero_fire_20260824.md
#
# **G-3 事故的第一手紀錄。** ReEntry_On = 1 但 CS_ReEntry 零觸發。
# 這份 anchor 的資料區間與 v14.7 不同（79 vs 82 筆、877,200 vs 800,000）。
# ---------------------------------------------------------------------------
L4_V180 = Anchor(
    strategy="L4_ConsolShort", version="v18.0",
    source_doc="docs/research/L4_v18.0_reentry_zero_fire_20260824.md",
    export_date=1260824,
    total_trades=79,
    net_profit=877_200,
    profit_factor=1.4902,
    win_rate=41.77,
    max_drawdown=-789_200,
    entry_labels={"CS_Entry": 79, "CS_ReEntry": 0},
    notes=(
        "**零觸發。** 根因：DISARM 條件 `Close of Data2 > v_ReEntry_BoxTop` "
        "被停損本身蘊含——停損永遠在箱頂上方 2 個 ATR，"
        "被停損帶走就代表價格必然穿過箱頂。**旗標在設立的同一根被清掉。**"
        "與 L1 那個「突破帶是觸發器不是結構」是同一族陷阱的鏡像版。"
        "資料區間與 v14.7 不同，兩者的筆數與淨利不可直接比較。"
    ),
)

# ---------------------------------------------------------------------------
# L3 v15.0 —— 標頭的 PERFORMANCE 區塊（MC9 2026/07/25，含 OB945）
#
# **視窗明載於 v14.1 的標頭**：Backtest 2020/05/12 - 2026/07/04。
# 用這個視窗，我的移植是 379 筆 vs 376，差 +3（+0.8%）——三支裡最接近。
#
# 注意 v15.1 的 CHANGELOG 另給一組 anchor：360 筆 / 1,389,600。
# **同一份檔案內部矛盾**，兩組相差 16 筆、超過 100 萬。
# ---------------------------------------------------------------------------
L3_V150 = Anchor(
    strategy="L3_ConsolLong", version="v15.0",
    source_doc="strategies/research/L3_ConsolidationLong/L3_v15.0/ 標頭 PERFORMANCE",
    export_date=1260725,
    backtest_start=1200512,   # v14.1 標頭明載
    backtest_end=1260725,
    total_trades=376,
    net_profit=2_446_000,
    profit_factor=1.255,
    win_rate=46.3,
    max_drawdown=-810_800,
    notes=(
        "v15.1 的 CHANGELOG 另給 360 筆 / 1,389,600，與本組矛盾。"
        "re-entry **無法事前登記精確值**（「同一 episode」需要 K 棒資料），"
        "登記為區間 20 <= CL_ReEntry <= 115。**超過 115 代表 episode 閘門沒作用。**"
    ),
)

# ---------------------------------------------------------------------------
# L5 v19.6 —— 標頭 PERFORMANCE BASELINE
# 標頭自註「to be re-verified after v19.7 MC9 deployment with fresh Excel」。
# MC12 於 2026-08-26 的執行為 171 筆進場（見 v19.9-R1 的 SEC-3b 註解）。
# ---------------------------------------------------------------------------
L5_V196 = Anchor(
    strategy="L5_BreakoutLong", version="v19.6",
    source_doc="strategies/research/L5_BreakoutLong/L5_v19.9_R1/ 標頭 BASELINE",
    export_date=1260826,
    backtest_start=1210828,   # 4.8 年往回推，標頭只寫「約 4.8 年」
    backtest_end=1260616,
    total_trades=162,
    net_profit=1_713_000,
    profit_factor=2.136,
    win_rate=52.47,
    max_drawdown=-193_200,
    notes=(
        "**標頭自註待重測**（v19.7 之後未更新）。回測期間「約 4.8 年」，起訖未載明。"
        "2026-09-07 實測：4.8 年窗口 + NIGHT_FIRST 日線定義 → **筆數逐位命中 162**。"
        "但 PF 1.302 vs 2.136——同筆數同勝率下獲利能力只有一半，"
        "**46% 的出場是 31 根的時間停損，那些是被砍斷的贏家**。"
    ),
)

# ---------------------------------------------------------------------------
# L1 V2.7 —— 標頭 PERFORMANCE（Excel 2026/07/02，SP 500，期初 100 萬）
#
# **V3.2 明載這組不是有效基準**：
#   「Trade counts in the older documents were taken on an earlier bar set
#    and are NOT a valid baseline. TWO runs are required.」
# 另有一組 451 筆 / 3,938K，兩組矛盾。
#
# **而且我的移植是收盤評估，不是 IOG 逐 tick**（見 l1_trendlong 模組說明）。
# ---------------------------------------------------------------------------
L1_V27 = Anchor(
    strategy="L1_TrendLong", version="V2.7",
    source_doc="strategies/research/L1_TrendLong/L1_v3.2/ 標頭 PERFORMANCE",
    export_date=1260702,
    backtest_start=1191216,   # 標頭明載
    backtest_end=1260702,
    total_trades=476,
    net_profit=3_018_400,
    profit_factor=1.496,
    win_rate=31.3,
    max_drawdown=-547_800,
    notes=(
        "**V3.2 明載此組不是有效基準，需要兩次執行重建。**"
        "另一組 451 筆 / 3,938K。"
        "本移植為收盤評估，P7 只看得到收盤峰值 -> TL_SP 觸發次數是下限。"
    ),
)

ANCHORS: dict[str, Anchor] = {
    "L1": L1_V27,
    "L2": L2_V54,
    "L3": L3_V150,
    "L4": L4_V147,
    "L5": L5_V196,
    "L4_v18": L4_V180,
}


def window(trades, anchor: Anchor):
    """套用 anchor 的回測視窗。

    **每支的視窗不同，而且影響極大。** L3 實測：視窗從 2019-12-16
    改成 2020-05-12（標頭明載），筆數差距從 +23 掉到 +3。
    """
    lo = anchor.backtest_start or 0
    hi = anchor.backtest_end or anchor.export_date
    return [t for t in trades if lo <= t.entry_date <= hi]


def check_window_effect(trades, anchor: Anchor) -> list:
    """回傳在 MC 報告匯出日**之後**才進場的交易。

    我的資料截止日晚於 MC 報告，那段期間的交易是我多的、與移植正確性無關。
    移植每一支新策略時都必須先跑這個檢查。
    """
    return [t for t in trades if t.entry_date > anchor.export_date]


def label_distance(mine: dict[str, int], theirs: dict[str, int]) -> int:
    """標籤向量的 L1 距離。0 = 完全吻合。"""
    keys = set(mine) | set(theirs)
    return sum(abs(mine.get(k, 0) - theirs.get(k, 0)) for k in keys)
