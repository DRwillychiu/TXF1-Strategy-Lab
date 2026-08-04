# HANDOFF — S16_S v1.13.0 A2 採用 + 全庫合規修補（2026-08-04 EOD）

> 依 CLAUDE.md Rule #16 七區段。本 session 專做 S16_S 單一策略（用戶 2026-08-04 指示：
> 此對話框只做單一策略開發與優化）。

---

## 1. Status

**S16_S v1.13.0 A2 結構型移動停利已採用並收案。**

```
129T / Net 2,646,400 / PF 1.7954 / MDD -561,200 / Max Single Win 602,800
Struct_On=True / Lookback=20 / Buffer_Pts=20 / UseClose=True / Trigger_Pct=1.20
Trail_On=True / 1.20 / 80      <- 保留但實測觸發 0 次
BE_On=True / 0.80 / 10
```

另完成兩項全庫合規修補（開工時同步雲端後發現，非本 session 原訂範圍）。

**未經 MC12 編譯**：本 session 所有 `.pla` 改動皆未編譯，僅靜態檢查 + pre-commit hook。

---

## 2. Changed（本 session 4 個 commit，均已推雲端）

| commit | 內容 | 風險 |
|---|---|---|
| `6d6fb70` | **S3_L 假日平倉死碼修復** 415 -> 300 + 全庫網格對齊稽核 | 中：分支由死碼變活碼 |
| `86d88ea` | **Manual_Kill_Switch 補進場 gate**（S1 / S3_L / S3_S） | 零：預設 False = no-op |
| `2c368c4` | **v1.13.0 A2 採用** Struct_On True / 20 / 20 | 中：改變出場行為 |
| — | 另有 `16b89e0` `b57865a` 來自另一台機器（TAIFEX 假日核對、憲法 v1.3），已併入 |

---

## 3. State

### 3.1 A2 三階段實證（全部 MC12 實跑）

| 設定 | Net | PF | 勝 | Max Win | MDD |
|---|---|---|---|---|---|
| BE only | 2,488,000 | 1.7478 | 33 | 602,800 | -461,200 |
| Trail 1.20/80 | 2,556,800 | 1.7685 | 35 | 602,800 | -461,200 |
| **Struct 20/20** | **2,646,400** | **1.7954** | 35 | 602,800 | -461,200 |
| 兩腿併存 | 2,646,400（與 Struct 單獨**位元相同**） | 1.7954 | 35 | 602,800 | -461,200 |

**A2 取代而非補強 Trail**：兩者修的是**完全相同的 2 筆**，A2 榨出 2.3 倍
（+158,400 vs +68,800）。Struct 開啟後 `SX_MA_Trail` 觸發 0 次。
Trail 仍保留 —— 程式碼取三腿鎖利最大值，留著永不更差。

### 3.2 退化錨點（掃描前置，皆通過）

| 錨點 | 設定 | 結果 |
|---|---|---|
| A | `Struct_On=False` + `Trigger_Pct=99` | 129 筆全欄位位元相同 |
| B | `Struct_On=True` + `Buffer_Pts=2000` | 129 筆全欄位位元相同 |

錨點 B **實際武裝 24/129 筆**，證明 `Highest(Close, v_Struct_Window)` 在執行期被呼叫。

> 錨點 A 實際跑 `Struct_On=False`，`Trigger_Pct=99` 讀不到，退化成基準重跑。
> **未補跑**：B 嚴格涵蓋（同一次跑完 24 筆武裝 + 105 筆未武裝）。

### 3.3 掃描（80 格）的兩個結構性發現

**Buffer 對淨利完美線性**：每 +5 點固定 -4,000。
反推 `4,000 / (5 × 200 × 2) = 2 筆` —— A2 全樣本只對 2 筆生效。

**Lookback >= 25 是假參數**：`MinList(Lookback, BarsSince+1)` 且 `MaxHoldingBars=24`
→ 25/30/35/40 全部 clamp 成同值，掃描結果完全相同。

> 這推翻設計意圖：A2 的效益不來自「追蹤滾動結構」，而來自「以進場後最高點為參考」。
> 真正的滾動行為（Lookback < 15）反而更差。

### 3.4 全庫合規現況

| 項目 | 狀態 |
|---|---|
| Rule #11 Settlement_Flat | 70/70 元素、10/10 策略 |
| Rule #15 ASCII | 48/48 |
| 假日窗口 vs K 棒網格 | 10/10 對齊（S3_L 本 session 修復） |
| Manual_Kill_Switch 進場 gate | **5/10**（live_sim 全補齊，**實盤 L1-L5 仍缺**） |

---

## 4. Decisions

| # | 決策 | 依據 |
|---|---|---|
| **D-1** | **A2 採用，Struct_On=True / 20 / 20** | 8/9 驗收通過，2 筆改變皆改善零筆劣化 |
| **D-2** | **第 9 項驗收字面未過仍採用** | 用戶 2026-08-04 裁決，見下 |
| D-3 | Lookback 選 20 | 達最高分的最小值；25+ 被 clamp 等價，是假選項 |
| D-4 | Buffer 選 20 而非最高分的 0 | Buffer 0 把停損壓在近期高點上必被掃損；**操作判斷非最佳化結果** |
| D-5 | Trail 保留不關 | 取三腿最大值，零成本保險 |
| D-6 | S3_L `Holiday_Flat_Time` 415 -> 300 | 依 L2（同 60M）既有先例，非推算 |
| D-7 | 實盤 L1-L5 的 Kill gate 不由 Claude 逕改 | 真實資金，需 MC9 重編譯 + 掛圖 |

### D-2 詳述：第 9 項未過的處置

年度分布 `2024 +55,200 (34.8%) / 2026 +103,200 (65.2%)`，門檻 50%。

**用戶裁決原文**：
> 「採用！因為很簡單，現階段的斜率所導致的績效集中，而且未來的指數價位肯定不會
> 再回去過去 20000-30000 點的價位。」

拆解：
- **(a)** n=2 時該標準無法通過 —— 任何兩筆分布至少 50/50，無法區分「機制集中」與「樣本太小」
- **(b)** 集中度根因是 **MinSlope 固定 28 點**：指數 8,700 時 = 0.32%（極嚴）、
  46,000 時 = 0.061%（極鬆，寬 5.2 倍）→ **交易母體本身偏向近年**，非 A2 缺陷。
  且前瞻上指數不回 20,000-30,000，未來母體近似 2026。

**強制條款：MinSlope 百分比化後，交易母體改變，第 9 項必須原樣重驗。**

---

## 5. Next

### 5.1 S16_S 本身（依序）

| 順位 | 項目 | 需要 |
|---|---|---|
| **1** | **P2：`Struct_UseClose = False` 對照** | 1 次回測。A2 唯一還沒驗的參數，夜盤長上影是已知風險 |
| 2 | **MinSlope 百分比化** | 錨定 `28/40634 = 0.0689%`；完成後重驗第 9 項 |
| 3 | 進場端濾網研究 | 見 5.2 |
| 4 | ML Monitor 去留 | 129 筆觸發 0 次，移除可省 10 input + 17 變數 |
| 5 | PROMOTE_CHECKLIST（Rule #19）+ Non-WFA 5 件套（Rule #18） | promote 前必跑 |

### 5.2 本 session 已完成分析、尚未實作的兩個議題

**議題一：MinSlope 改用快線/慢線比值**

用戶提案的「Fast / Slow 比值」**數學上退化**：死叉的定義就是 Fast 穿越 Slow，
交叉當根比值恆 ~= 1.000，無法區分任何交易。

有效替代（完整比較表見對話記錄）：

| 形式 | 公式 | 評估 |
|---|---|---|
| 現行 | `Fast[1]-Fast` | 絕對點數，不隨指數縮放 |
| **斜率百分比** | `(Fast[1]-Fast)/Close×100` | **首選**，直接解決縮放，錨定 0.0689% |
| 斜率比值 | `(Fast[1]-Fast)/(Slow[1]-Slow)` | 新穎，但慢線斜率 ~= 0 時爆炸 |
| ATR 標準化 | `(Fast[1]-Fast)/ATR` | **v0.6 已試並失敗**，ATR 測波動不測方向 |

> ⚠️ v1.9.0 曾試百分比制並被否決，理由記為「高指數更嚴/低指數更鬆」。
> 但現在的分析顯示**「高指數更嚴」正是需要的修正**。同一事實兩種解讀，
> 當時判為缺陷、現在判為修正。**需用戶裁決是否翻案。**

**議題二：K 棒型態 / 價格行為濾網**

篩選原則：現行進場已有「死叉 + 快線陡跌」，**任何同樣衡量「價格快速下跌」的型態都是冗餘**
（memory `feedback_filter_redundancy_check`）。價值在**正交資訊**。

建議優先序（完整候選表見對話記錄，涵蓋 A 結構型 / B K 棒型態 / C 價格行為 / D 量價 / E 位置情境）：

| 順位 | 候選 | 正交性 |
|---|---|---|
| 1 | **A1 頭頭低**（swing high 遞減） | 高 —— 多根結構 vs 單根斜率 |
| 2 | **C1 收盤位置 + C2 無下影線** | 高 —— 賣壓是否延續到收盤 |
| 3 | **E3 時段** | 最高 —— 純外生，先做 88 筆 QuickStop 的時段歸因 |
| 4 | B4 長上影 / B5 內包破低 | 高但筆數少 |
| 5 | D1 量價 | 最高但需先解夜盤量能標準化（ML 的量能條件 129 筆觸發 0 次） |

最大目標：**88 筆 QuickStop 以 0 勝虧掉 3,089,600**，這是進場品質問題。

### 5.3 全庫層級待裁決（非 S16_S）

| # | 事項 | 建議 |
|---|---|---|
| J-A | **實盤 L1-L5 補 Manual_Kill_Switch 進場 gate** | 修。邏輯零風險（預設 False = no-op），但需排 MC9 重編譯 + 掛圖 |
| J-B | S3_L 回測重跑 | 假日分支由死碼變活碼，若樣本內有假日持倉結果會變 |
| J-C | 驗證腳本補第 8 / 9 項 | 現行 7 項對本 session 兩個缺陷**全部亮綠燈** |

---

## 6. Files

### 新增
| 路徑 | 說明 |
|---|---|
| `docs/research/holiday_window_grid_alignment_audit_20260804.md` | 假日窗口 vs K 棒網格全庫稽核 + Kill switch 附帶發現 |
| 本檔 | 今日彙整 |

### 修改
| 路徑 | 改動 |
|---|---|
| `strategies/research/S16_MACrossShort/S16_S_MACrossShort_v1.13.0.pla` | Struct_On False -> True，標頭補 RESULT 區塊與限制 |
| `docs/research/S16S_A2_structure_trail_experiment_20260804.md` | 追加執行結果與裁定（7 節） |
| `strategies/live_simulation/S3_VolSqueezeLong/S3_VolSqueezeLong.pla` | Holiday_Flat_Time 415->300；補 Kill gate |
| `strategies/live_simulation/S3_S_VolSqueezeShort/S3_S_VolSqueezeShort.pla` | 補 Kill gate |
| `strategies/live_simulation/S1_NightMomentum/S1_NightMomentum.pla` | 補 Kill gate |

---

## 7. Git

### 開工前必做（換機器必看）
```bash
git config core.hooksPath .githooks
```
本機已設定並實測通過。

### 同步狀態
- 分支 `main`，本 session 結束時 **0 ahead / 0 behind**，working tree clean
- 最新 commit `2c368c4`

### 驗證
```
pre-commit hook: ASCII 48/48 PASS | Settlement_Flat 70/70 元素 10/10 策略 | EXIT=0
```

---

## 8. 誠實聲明

- **A2 效益僅來自 2 筆交易**，+158,400，配對檢定 **1.36 sigma**，未達 2 sigma。統計上未確立。
- `Struct_Buffer_Pts` 的**保護價值從未被測到** —— 只有 2 筆觸發，掃描只量到成本。
- `Struct_UseClose=False` **從未掃描**。
- 本 session 所有 `.pla` 改動**未經 MC12 編譯**。
- S3_L 假日修正**未重跑回測**。
- 有效樣本約 7 個月：2026 年 1-7 月佔 76% 筆數、92.4% 淨利。
- **不得宣稱「最佳停利機制」或「已收案」** —— 僅能宣稱在 MinSlope=28 固定點數、
  樣本集中於 2026 年的條件下優於基準。
