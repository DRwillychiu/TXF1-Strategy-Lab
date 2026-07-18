# 優化方向存活清單 + 資料抓取路線圖（2026-07-18）

- **來源鏈**：Deep Research（多頭格局真假突破，~25 源）→ 機構級再驗證（實戰 + 機構雙視角）→ 交叉 Portfolio DD Post-Mortem（`docs/research/portfolio_DD_postmortem_202607_L1-L5.md`）
- **性質**：研究路線圖 + 資料抓取方向。**非設計 spec**——第 2 優先項進 maintenance window 時，依 Rule 16 另開設計 spec。
- **統計**：原始 47 個優化方向 → 機構標準過堂後：**3 項風險側立即執行、6 項量測任務、9 項 maintenance window 候選、其餘 KILL/凍結**。
- **觸發背景**：2026/07 帳戶 -21.3% DD（越過 §4.2 的 20% 熔斷線）+ L4 上架至今零進場（多頭格局盤整空缺口）。

---

## 0. 兩條鐵律（本文件所有項目的前提）

### 鐵律 1：驗證時鐘規則
L1-L5 正在 6 個月實戰驗證期。**驗證期中改 .pla = 實驗中途換受測物，驗證作廢重來。** 唯一例外：風控強制介入（熔斷已觸發 = 義務）。live_simulation 四隻（S1/S3_L/S3_S/S16_S）同理：改一行 code = 30 筆模擬門檻重新計時。

分籃原則：
- **風險側**（不碰 .pla，或熔斷義務）→ 立即執行
- **Alpha 側**（改策略碼）→ maintenance window，帶全套 Rule 13/18 驗證

### 鐵律 2：機制先於統計（Economic Rationale First）
任何 filter 上線前，先在 TXF1 自己的數據上量測該機制是否存在。**不引用美股/FX 統計直接編碼。** 理由：本輪已抓到外部證據自相矛盾（見附錄 A 的 Bulkowski 矛盾記錄）；且 47 個方向的多重檢定下，以 p=0.05 計期望有 2-3 個純噪音改動 in-sample 看起來效果卓越。

---

## 1. 第 0 優先：風險側（立即執行，不碰任何 .pla）

| # | 項目 | 內容 | 依據 |
|---|---|---|---|
| 0-1 | **資金適足性正面決策** | 熔斷已觸發（-21.3% > 20%）：全策略降至最小口數是 `position_sizing_and_capacity.md` §4.2 的義務。300K 帳戶 vs 合併回測 MDD -375K（125%）的根本矛盾需裁決：縮策略數 / 增資 / 承認超額風險並書面接受 | DD post-mortem §3 §5 |
| 0-2 | **Portfolio 日/週虧損上限 + 恢復規則** | 機構零爭議標配（daily VaR limit / kill switch）。MC 單策略架構不支援 → 外部實作：最簡版 = 每日收盤人工檢查淨值，觸線降口數/停機；進階版 = Python 對帳監控。**必配 re-risking 規則**（例：帳戶回到 -10% 內恢復口數），否則單向永久縮水 | 機構標準 + 七月事故放大機制 |
| 0-3 | **L3 v14.1 回滾 v13.2B 決策** | 7/3-7/4 無 review 部署、7/7 首戰遇史上第 8 大跌點、主要出血源候選。回滾至已驗證版本屬風險側動作，不受驗證時鐘限制 | Handoff 20260717 Next #2 |

---

## 2. 第 1 優先：TXF1 自量測包（研究任務，不碰 .pla、不重置時鐘）

### 2.1 量測任務總表

| ID | 量測 | 裁決對象 | 建議決策門檻（可調） |
|---|---|---|---|
| M-a | 突破 bar 的 session-relative volume vs 交易結果 | C2 成交量確認 filter（方向未定：高量好或壞） | 高量組 vs 低量組失敗率差 ≥ 15pp 且每組樣本 ≥ 20 → filter 進設計；否則 KILL |
| M-b | Spring Trap poke 深度 vs CS_BreakExit 歸因 | C4 BEM 延伸上限（L4 最佳 alpha 候選） | CS_BreakExit 28 筆的 poke 深度中位數 > 獲利組 1.5 倍 → BEM cap 進設計；反向則 KILL |
| M-c | 箱體期間 up/down volume ratio vs 結果 | C3 Wyckoff distribution 簡化代理 | ratio<1（distribution 指紋）組勝率差 ≥ 15pp → 進設計 |
| M-d | 日線 ADX(14) 分佈 + 各 ADX 區間的假突破失敗率 | C1 ADX 第三狀態 filter（橫跨 L3/L4/L5） | ADX<20 組 Spring Trap 勝率 ≥ 55% 且樣本 ≥ 20 → 進設計 |
| M-e | L1 連虧 k 筆後下一筆訊號期望值 | C6 連虧冷卻（預期大概率否決） | 連虧後下一筆期望值 ≥ 全體平均 → cooldown KILL；顯著更差才續議 |
| M-f | Range_Shrink 0.7 vs 0.5 箱體品質差異 | L4 箱體門檻收緊 | 0.5 檢出箱體的後續交易品質顯著優於 0.7 增量部分 → 進設計；注意樣本死亡螺旋 |

### 2.2 資料抓取需求（給 MC 匯出）

| 資料 | 欄位 | 區間 | 餵給 |
|---|---|---|---|
| **TXF1 15M K 線** | Date / Time / Open / High / Low / Close / **Volume** | 2020/01 ~ 今 | M-a, M-b, M-f |
| **TXF1 60M K 線** | 同上 | 2020/01 ~ 今 | M-b, M-c, M-f（箱體重建：Lookback 15 / Shrink 0.7 邏輯復刻） |
| **TXF1 日線 K 線** | 同上（Volume 可選） | 2019/01 ~ 今（ADX 需暖機） | M-d |
| L4 交易明細 | 已有：`TXF1 STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告_14.4.xlsx`（81-84 筆） | — | M-a, M-b, M-c, M-d |
| L1 交易明細 | 已有：`TXF1 WILLY_ATR_LONG_60M 策略回測績效報告.xlsx`（450 筆） | — | M-e |

**Volume 處理鐵則（適用 M-a / M-c 全部 volume 量測）：**
1. **Session-relative 基準**：日盤（08:45-13:45）與夜盤（15:00-05:00）量能差一個數量級，任何「vs N 期均量」必須用同時段 slot 基準（過去 20 日同一 15M slot 的均量），嚴禁跨時段直接比較。
2. **換月週處理**：結算週 volume 向次月轉移，量測時標記結算週樣本另行分組或剔除。
3. 60M 箱體重建必須依 MC 的 session-aligned bar 切法（60M bar 對齊時段開盤），Python 聚合時需比對 MC 圖表確認一致。

### 2.3 量測方法摘要

- **M-a**：每筆 L4 交易回推其 Spring Trap 突破 bar（`High > Box_Top` 那根 15M）→ 計算 session-relative volume ratio → 按出場標籤分組（獲利 / CS_SL / CS_BreakExit）比較分佈。
- **M-b**：每筆交易計算 poke 深度 `(max(High) - Box_Top) / ATR`（trap zone 期間）→ CS_BreakExit 組 vs 其他組的深度分佈。**若 CS_BreakExit 集中於深 poke，BEM cap 一石二鳥（同時解 -545K 問題）。**
- **M-c**：箱體形成期間（60M）up-bar volume 總和 / down-bar volume 總和 → ratio < 1 = distribution 指紋 → 分組勝率。
- **M-d**：日線 ADX(14) 全期分佈（各區間天數占比）→ 84 筆按進場日 ADX 分組勝率。重點驗證「日線多頭 + ADX<20 = 多頭中的盤整」這個第三狀態的存在性與可交易性。
- **M-e**：L1 450 筆依序掃描，統計連虧 k = 3/5/8/10 之後那一筆的平均損益 vs 全體平均。
- **M-f**：60M 數據上復刻箱體偵測，比較 Shrink 0.7 與 0.5 的檢出箱體集合差異與後續價格行為。

---

## 3. 第 2 優先：Maintenance Window 候選（動 .pla，需 Rule 16 spec + Rule 13/18 全套驗證）

**啟動條件**：對應量測通過門檻 + 維護窗口開啟（驗證期滿或正式暫停驗證）。

| # | 策略 | 項目 | 前置量測 | 備註 |
|---|---|---|---|---|
| 2-1 | L4 | ADX 第三狀態疊加 Kill Switch（`ADX<20 且日線多頭` 開放 Spring Trap） | M-d | **重定位：不是取代 MA 交叉（日線 ADX lag 同量級，速度優勢是誤傳），是疊加 no-trend 第三狀態**。直接回應「多頭格局盤整空缺口」 |
| 2-2 | L4 | BEM 延伸上限（poke > Box_Top + N×ATR 不進場） | M-b | 純價格邏輯、零 volume 地雷；可能同時是 CS_BreakExit -545K 的解藥 |
| 2-3 | L4 | BOF 第三條件（失敗 bar Close < 突破 bar Low） | M-b 附帶 | A/B 測試項：結構確認 vs 進場延遲 1+ bar 的 edge 損耗 |
| 2-4 | L4 | 突破 bar volume 確認 | M-a | 方向由量測決定（外部證據自相矛盾，不預設高量好/壞） |
| 2-5 | L4 | 箱體 up/down volume ratio 進場確認 | M-c | Wyckoff distribution 簡化代理 |
| 2-6 | L3 | 日線 OR 濾網收緊（OR→AND 或加 ADX 門檻） | M-d + regime-split 回測 | **機構警告：recency bias**——必附 2020-2024 各年 PF 變化，不能只看七月 |
| 2-7 | L3 | 交易冷卻間隔 | 無 | 盤整策略無右尾依賴，跳訊號傷害小，機構可接受 |
| 2-8 | L5 | 持續 N bars 站上箱頂確認 + 跌勢 regime gate | M-d + regime-split | L5 最便宜的假突破防護；進場延遲 vs 假訊號減少 A/B |
| 2-9 | L2 | v6 redesign scoping（ADX+DMI regime 引擎） | 無（獨立工程） | **定性為 redesign 非優化**：換 regime 引擎 = 換策略身分。致命驗證困境：樣本期內只有 2022 一個熊市（n=1 regime），機構標準需跨市場代理數據驗證 |
| 2-10 | Portfolio | 濾網不對稱修正 + regime 煞車 spec | M-d | 多方 OR（寬鬆）vs 空方嚴格慢速 → 跌勢初段淨偏多的結構債；依 Rule 16 開 spec |

---

## 4. KILL / 凍結清單（防止未來重提）

| 項目 | 判定 | 理由 |
|---|---|---|
| live_simulation 四隻（S1/S3_L/S3_S/S16_S）所有優化 | ❄️ 凍結 | 改 code = 30 筆模擬門檻重計時。S3_S 另有 v1.9.6 audit 15 findings 未結案，先結案 |
| L2 空頭行情加碼 | ❌ KILL | 違反固定 1 口紀律；資金適足性未解前不可能談加碼 |
| L5 偏好低量突破 | ❌ KILL | Bulkowski pattern-specific 數據（rectangle 向上突破 = 高量較好）與 generic 悖論相反，而 L5 正是 rectangle-up case；extraction 內部亦矛盾。等 M-a 自量測 |
| L1 ADX>50 過熱警告 | ❌ KILL | ADX>50 天數極稀少，樣本不足以驗證 |
| L1 連虧冷卻 | 🔬 待 M-e（預期否決） | 趨勢策略右尾依賴：大贏緊跟連虧串；與 Portfolio cap（0-2）功能重複；機構 CTA 極少在策略層跳訊號 |
| VPIN / order flow / volume profile 類 | ❌ KILL | 需 tick 級數據基礎設施，MC12 15M 架構無法計算 |
| 機構流動性陷阱防護（L5） | ❌ 轉化 | 概念正確但無 order flow 數據 → 已轉化為 2-8 持續確認 |

---

## 附錄 A：外部證據來源 + 品質警告

### A.1 Bulkowski 矛盾記錄（本輪最重要的方法論教訓）

| 來源 | 主張 | 方向 |
|---|---|---|
| thepatternsite.com/volbkout.html | 高量突破成功 65% vs 低量 39% | **高量好** |
| thepatternsite.com/VolumeStudy.html | 高於均量突破失敗率 2x（up 14% vs 5%；down 28% vs 11%）；throwback 率 3x（57% vs 18%） | **高量壞** |

兩篇量測定義不同（成功率門檻 vs 失敗率 vs throwback），但方向性衝突足以否決直接引用。**Deep research 的對抗驗證階段因中斷未執行，此矛盾由人工複查抓出。** 同時三重 domain transfer 失效：美股個股 ≠ 指數期貨、日線波段 ≠ 15M/60M intraday、10% 週級門檻 ≠ 期貨點數級。→ 一切以 M-a 自量測為準。

對 L4 的正確映射：throwback 統計（高量突破後 57% 回測）只保證價格回到箱頂附近（= Spring Trap 進場前提），**不保證跌穿箱體（= L4 獲利需求）**——中間缺的環節是 distribution vs re-accumulation（M-c 的驗證對象）。

### A.2 保留引用的核心來源

| 主題 | 來源 | 等級 |
|---|---|---|
| Regime 依賴的失敗率基線（多頭中向下突破失敗率 26%→49%） | Bulkowski FailureRates.html（13,932 patterns, 1991-2008） | Primary |
| 機構流動性捕獲機制（假突破 = 獵停損） | SSRN 6592020 (Costa, 3,800+ breakouts)；SSRN 5962358 (Mittal & Choudhary, 15,000+ breakouts, volume-at-price) | Working paper |
| BOF 三條件確認 + BEM 延伸度量 | "BOF - Breakout Failure in Financial Markets" (Academia.edu, VRZ framework) | 實務型論文（非期刊） |
| BOF 趨勢過濾警告：「上升趨勢只做多方 BOF；反趨勢 BOF 是最低勝率配置」 | 同上 | 同上 |
| Wyckoff distribution vs re-accumulation 信號 | StockCharts Wyckoff Tutorial；Wyckoff Analytics Official；Villahermosa | 教科書級 |
| Wyckoff 四相量化映射（variance × trend） | arXiv 1812.02527 | Peer-review 前印本 |
| ADX regime 分層（<20 盤整 / 25-40 趨勢） | 多個實務源（fxnx、pyquantlab 等） | Blog 級（「降停損 30-40%」數字不可引用） |
| 順序化突破驗證（direction→resistance→authenticity，70% 準確率） | FinLLM-B, arXiv 2402.07536（S&P 500 futures footprint） | Primary |

### A.3 關聯文件

- `docs/research/portfolio_DD_postmortem_202607_L1-L5.md` — DD 危機診斷（本文件的風險側依據）
- `docs/handoffs/handoff_20260717_portfolio_DD_audit.md` — 桌機端執行順序
- `docs/methodology/position_sizing_and_capacity.md` §4.2 — 熔斷規則
- `strategies/live/L4_ConsolidationShort.pla` — Spring Trap 現行實作（v14.4 + P3b）
- `docs/methodology/non_WFA_validation_SOP_20260630.md` — Rule 18 五件套（所有第 2 優先項的驗證關卡）
- `docs/institutional_risk_framework_20260619.md` — Rule 13 十維度

---

## 執行順序總結

```
[現在]   0-1 資金決策 → 0-2 Portfolio cap → 0-3 L3 回滾決策
[本週]   MC 匯出 15M/60M/日線 三份 K 線資料（§2.2 規格）
[量測]   M-a ~ M-f 六項量測 → 每項對照決策門檻 → 產出裁決
[窗口]   通過門檻的項目 → Rule 16 spec → Rule 13/18 驗證 → 部署
[永不]   KILL 清單不重提；live_simulation 凍結至期滿
```
