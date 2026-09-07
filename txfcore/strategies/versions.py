"""移植版本對照表 —— 裁決 2026-09-06。

**全部只移植 research 版。**

五支的 research 版正好都是 live 版加一層可觀測性，且全部宣稱
「zero behaviour change」。所以：

    移植對象   research vN+1
    對帳目標   live vN 的 MC 報告
    宣稱       「行為等同」列為**待驗證**，不是前提

> 這正好是對帳能回答的問題。對得上 → 宣稱變成證據；
> 對不上 → 那是真正有價值的發現，而且會一次驗證五支。

**為什麼不直接移植 live 版：**

  1. research 版的 re-entry 標籤讓對帳看得見更多
     L2 的 55 + 22 = 77 拆分，只有 v5.4 印得出來
  2. L5 的 Print 日誌是唯一能標到引擎停損的東西
     標頭實測 171 筆中 1 筆由 SetStopLoss 直接平倉，無任何 Sell 語句
  3. 「行為等同」是可驗證的宣稱，不該當成必須先相信的前提
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VersionPair:
    key: str
    live_version: str
    live_sha256: str
    research_version: str
    delta: str          # research 相對 live 多了什麼
    dead_code: str      # 移植時會連帶帶到的關閉模組


PORTING_TARGETS: tuple[VersionPair, ...] = (
    VersionPair(
        "L1", "V3.1 (V3.0 base + SL_Pct percentage cap)",
        "1873911C75A02288F2DEF0B0F963BFD50018E7F2F3949BCD6CE2453FB4E17AAB",
        "v3.2",
        "re-entry 模組（ReEntry_On = 0，完全惰性）+ v_Prev_MP",
        "ReEntry_On = 0 整條腿",
    ),
    VersionPair(
        "L2", "5.3 + SetStopContract + SL_Pct (v5.2 base)",
        "CDCF0F80CFFC024C9ED8BD49C91BA3AD82F982D4869994D73EE840B4534BF0E3",
        "v5.4",
        "re-entry LABEL only（TS_Entry / TS_ReEntry 拆分）",
        "無",
    ),
    VersionPair(
        "L3", "v15.0 (v14.1 base + SetStopContract + SL_Pct 0.55% + Opening Block + Min R:R)",
        "F09BB0150F697396BE0554A1619C3A85B4D127E3D7CAA0398DE235D80B876A55",
        "v15.1",
        "re-entry LABEL only（episode 定義，非 L2 的價格定義）",
        "BE 層（BE_Trigger_Pts = 0）",
    ),
    VersionPair(
        "L4", "v14.6 + SetStopContract + SL_Pct (PRODUCTION; v14.5 fully removed)",
        "69D1C1E77CB6DEBB4D9DF0FD84BE52182ADD6B83D4CC70FCFC517BAC4922FA30",
        "v14.7",
        "re-entry LABEL only（純結構，不看價格也不看盈虧）",
        "BE 層 + SP 層（兩者皆 0）",
    ),
    VersionPair(
        "L5", "v19.9 + SetStopContract + SL_Pct + HolidayFlat_v3 + FrozenSL + ImmediateStop",
        "64AF5D2A25BD3CF1695BE55B386B53042C441A51E36B68FD40D8E740D8F69E67",
        "v19.9-R1",
        "Print 日誌 + v_Prev_MP + episode 計數器。**不發任何單**",
        "SP 模組（SP_Trigger_Pts = 0，標註 PERMANENT）",
    ),
)

BY_KEY = {v.key: v for v in PORTING_TARGETS}

# 移植順序，依實測複雜度（見 docs/specs/L1-L5_cross_comparison.md）
PORTING_ORDER: tuple[str, ...] = ("L2", "L4", "L3", "L5", "L1")

# 不採用的 research 分支。標頭明載已關閉或失敗。
REJECTED_BRANCHES: dict[str, str] = {
    "L4_v15.0": "FAILED, research line CLOSED 2026-07-26",
    "L4_v15.1": "FAILED, research line CLOSED 2026-07-26",
    "L4_v16.0": "FAILED, research line CLOSED 2026-07-26",
    "L4_v17.0": "非 production 版本",
    "L4_v18.0": "二次進場零觸發事故（G-3 的原型）。DIAG 版可供研究，不移植",
    "L1_v3.0": "v3.1 的前代",
    "L3_v14.1": "v15.0 的前代",
    "L5_v19.8": "v19.9 的前代",
}

# 死碼處置：mc12 模式不移植路徑，但保留 input 欄位。
# 開關為 0 時路徑本來就不執行，對帳結果完全相同；保留欄位讓 v2 日後能接。
#
# **但這些 A/B 全部失敗過**：
#   L1 Plan C   拖累 −920K，69 筆 re-entry 淨負
#   L3 BE +50   100 筆 CL_BE 全 0% 勝率
#   L4 BE +60   淨 −345K，砍掉前十大贏家中的 4 筆
#   L4 SP +80   CS_SL 從 +1,019K 掉到 +619K
#   L5 SP B–F   三筆超級贏家被砍到 +7K–38K
# v2 若要重試，第一件事是讀完這些 postmortem。
DEAD_CODE_POLICY = "mc12 不移植路徑，保留 input 欄位供 v2 使用"
