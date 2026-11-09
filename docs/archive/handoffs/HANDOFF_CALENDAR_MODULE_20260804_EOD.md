# HANDOFF — 行事曆模組化 Step 1 + 全庫邏輯歸納（2026-08-04 EOD）

> 依 CLAUDE.md Rule #16 七區段格式。接手者請先讀 §1 與 §7 的「開工前必做」。

---

## 1. Status

**本 session 完成**：全庫策略條件邏輯歸納（交付）、3 項合規缺口修補（交付，待物理驗證）、
2 支強制驗證腳本重建 + pre-commit hook（交付，已實跑）、行事曆模組化 SOP 第 1 步（交付）。

**當前卡點**：模組化 #1/#2 有 **3 個前置阻擋點**，全部不是單靠 Claude 能完成的（見 §5）。

**最急件**：**S3_L 的假日強制平倉是死碼**，而該策略無每日強平兜底 → 現況可抱部位穿越連假。
詳見 §4 J-2。

**未經物理驗證**：本 session 所有 `.pla` 改動**都沒有經過 MC12 編譯**。依鐵律 4 需執行
編譯 + runtime + log 三層驗證後才能視為完成。

---

## 2. Changed（本 session 的 7 個 commit，均已推雲端）

| commit | 內容 | 風險等級 |
|---|---|---|
| `5172b82` | 全庫策略條件邏輯歸納文件（九層出場矩陣） | 文件 |
| `3fd98f2` | **S3_L + S3_S 補 Rule #12 三件套** | **高：改變引擎停損寬度** |
| `22cbb72` | L4 修 Rule #15 非 ASCII（`:507`/`:622` 的 `×`） | 低：僅註解 |
| `7d2d3ee` | 重建 `verify_pla_ascii.py` / `verify_settlement_flat.py` + 新增 `strategy_discovery.py` | 中：驗證機制 |
| `c31cc52` | 新增 `.githooks/pre-commit` 強制執行 Rule #11/#15 | 中：影響每次 commit |
| `3a94836` | `.gitattributes` 鎖 `.githooks/**` 為 LF | 低 |
| `a57a73e` | 行事曆模組化 SOP 第 1 步（規則手冊 / 差異清單 / 平台研究） | 文件 |

**另有兩個 commit 來自另一台機器**（本 session 期間並行推入）：
`f90265f` A2 結構型移動停利實驗設計、`0556cca` **S16_S v1.13.0 A2 模組實作**（1069 行，預設 OFF）。

---

## 3. State（現況與已驗證事實）

### 3.1 驗證機制（已實跑，非推測）

```
verify_pla_ascii.py --strict        48/48 PASS   COVERAGE 48/48 OK   EXIT=0
verify_settlement_flat.py --strict  70/70 元素   10/10 策略          EXIT=0
```

新的 `v1.13.0` 已被自動納入掃描（48 檔，原為 47）——這證明 auto-discovery 有效，
不會像舊版那樣因新增檔案／搬動資料夾而靜默漏掉。

### 3.2 Rule #12 三件套現況

| 策略 | 狀態 |
|---|---|
| L1-L5、S1、S16_S、S3_RPS | 3/3（S3_RPS 的 `SL_Pct=0` 未啟用） |
| **S3_L、S3_S** | **本 session 由 1/3 補為 3/3**，`SL_Pct` 預設 **0（停用）** |
| S16_S v1.12.0 / v1.13.0 | 3/3 |

### 3.3 本 session 發現但**尚未修**的問題

| # | 問題 | 位置 |
|---|---|---|
| P1 | **S3_L 假日平倉永不觸發**：60M 夜盤網格為整點，窗口 `[0415,0455]` 內無收盤點 | `S3_VolSqueezeLong.pla:120,481-484` |
| P2 | S3_L 無每日強平兜底（TimeStop = 70×60M ≈ 5 個交易日）→ P1 的後果被放大 | 同上 |
| P3 | L1/L3 的 Kill 在 else-if 鏈外且排最後，違反憲法條款 3 | `L1:646`、`L3:458` |
| P4 | S1/S3_L/S3_S 進場 gate 缺 `Manual_Kill_Switch = False`（S3_RPS 檔內列為已知 bug CB-1 並已修，S16_S 亦已修） | 三支的進場區塊 |
| P5 | 憲法自相矛盾：條款 1 元素 5 參考實作用無上界 `Time >=`，同文件 checklist 第 234 行卻要求閉區間 → 10 支照抄，10 處未配對 | `SETTLEMENT_DAY_DESIGN_CONSTITUTION.md:75` vs `:234` |
| P6 | S3_S 的 Layer 2 SP：主路徑被 TP 堵死（`SP_Trigger_ATRMult=2.0` == `TargetATRMult=2`），次路徑（ATR 收縮）仍開 | `S3_S:972-974, 1027` |

### 3.4 文件已知過時處

`docs/research/strategy_logic_inventory_20260804.md` 記載 S16_S research head 為 **v1.12.0**，
實際已推進到 **v1.13.0**（`0556cca`）。該文件的 rev.2 區段記錄了本 session 的修補，
但**未反映另一台機器的 A2 工作**。

---

## 4. Decisions

### 4.1 已定案

| # | 決策 | 理由摘要 |
|---|---|---|
| **D-1** | 行事曆模組採**產生期共用**（Python 產生器 + 驗證器斷言），**否決執行期共用**（PowerLanguage User Function） | Function 方案改完必須每台機器 Recompile All，否則已掛圖策略靜默使用舊表——與 2026-07-26 事故同型。產生期共用讓每支策略執行期仍持有副本，單點失效移到驗證器看得到的地方 |
| **D-2** | Settlement 維持動態偵測，**不併入**假日資料表 | `settlement_flat_module_20260617.md` §九 已評估並否決靜態表；兩種架構是刻意設計 |
| D-3 | `S3_L`/`S3_S` 的 `SL_Pct` 預設 **0** | Rule #12 要求預設值由 MC sweep 決定，sweep 未跑，不得憑空填數字 |
| D-4 | 驗證腳本的 structural failure **無條件 exit 1**（不需 `--strict`） | 守門員看不到自己該看的範圍時，絕不允許回報成功 |

### 4.2 待使用者裁決（**這是回家後第一件要決定的事**）

| # | 事項 | 選項 | 建議 |
|---|---|---|---|
| **J-2** | S3_L `Holiday_Flat_Time` 415（死碼） | (a) 改 **300**（60M 網格留一次重試：03:00 觸發→04:00 成交；未成交 04:00 再發→05:00）(b) 改 400（僅一次機會）(c) 記錄為已知限制 | **(a)** |
| J-1 | 憲法 P5 矛盾 | (a) 10 支 Settlement 分支全補 `Time <=` 上界 + 修憲法參考實作 (b) checklist 加註 Settlement 分支豁免 | 傾向 **(b)**：`v_Settlement_Day` 是純日期守衛，補上界反而多一個出錯點 |
| J-3 | L1/L3 Kill 移回鏈首 | (a) 修正 (b) 書面豁免 | (a)，但 L1 是實盤，需排期 |
| J-4 | S1/S3_L/S3_S 補進場 Kill gate | (a) 補 (b) 維持 | (a) |
| J-5 | 結算日純日曆推算無假日修正 | 憲法 6.1 已指定「手動加入 HolidayFlat 表」為對策 | 維持，但確認一次 |

---

## 5. Next（依賴圖與建議順序）

### 5.1 三個前置阻擋點（全部需要人／外部資源）

```
A. 憲法 P5 矛盾裁決        <- 需使用者裁決        阻擋 #1 模組化
B. 63 筆日期 vs 期交所 PDF  <- 需 TAIFEX PDF       阻擋 #2 模組化
C. S3_L 60M 夜盤實際收盤時戳 <- 需 MC12 實機一眼    阻擋 J-2 修復
```

**B 特別重要**：兩個 agent 獨立確認 63 筆日期在 10 支之間**完全相同**（md5 一致），
但那只證明「10 份副本一致」，**沒有證明「這 63 筆是對的」**。L1/L2 保留的 9 個 `*`
標記明白寫著那幾筆未經 PDF 驗證。**把未驗證的表模組化，只會讓同一個錯誤更有效率地散佈。**

### 5.2 建議推進順序

1. **裁決 J-2 並修 S3_L**（最急，唯一有實質風險曝露的項目）
2. 裁決 J-1（阻擋 #1）
3. 取得期交所 PDF 核對 63 筆（阻擋 #2）
4. 進 SOP 第 2 步：壓力測試規則（雙重翻譯 ×2 + 試跑 2-3 個代表性檔案）
5. J-3 / J-4 可與上述平行

### 5.3 需要 MC12 物理驗證的清單（累積）

| # | 項目 | 為何需要 |
|---|---|---|
| V1 | S3_L / S3_S 改動後編譯 + runtime + log | 鐵律 4，本 session 只做到靜態檢查 |
| V2 | S3_S 重跑回測 + 7/7 gates | `SetStopContract` 使引擎停損寬度回到設計值，2026-07-06 PROMOTE 的驗證是舊行為下取得的 |
| V3 | S3_L / S3_S 的 `SL_Pct` MC sweep 0.00-5.00 step 0.25 | 現為 0＝停用，Rule #12 要求由 sweep 決定預設 |
| V4 | S3_S SP 死碼三假設 H-A / H-B / H-C | 見 inventory 文件 8a-U1 補述 |
| V5 | S3_L 60M 夜盤 K 棒的實際 `Time` 值 | 前置阻擋點 C |
| V6 | `v_Settlement_Day` 在夜盤是否為 true | 抽模組前第一順位 |
| V7 | L4 重新編譯（本 session 改過註解） | 註解改動不影響邏輯，但需重載 |

---

## 6. Files

### 6.1 本 session 新增

| 路徑 | 說明 |
|---|---|
| `docs/research/strategy_logic_inventory_20260804.md` | **全庫條件邏輯歸納**（九層矩陣 / 停損詳表 / 停利詳表 / 合規矩陣 / 13 個模組化候選） |
| `docs/research/calendar_module_rules_20260804.md` | **規則手冊**（架構決策 D-1/D-2、鐵則 R-1~R-10、依賴圖、陷阱清單） |
| `docs/research/calendar_module_diff_checklist_20260804.md` | 差異清單 921 行，10 支逐檔 |
| `docs/research/powerlanguage_shared_module_feasibility_20260804.md` | 平台可行性（本機 MC 9.0.11581 官方文件實證） |
| `scripts/strategy_discovery.py` | 策略發現的單一事實來源 |
| `.githooks/pre-commit` | Rule #11/#15 強制執行 |
| `.gitattributes` | 鎖 `.githooks/**` 為 LF |

### 6.2 本 session 修改

- `strategies/live_simulation/S3_VolSqueezeLong/S3_VolSqueezeLong.pla`（Rule #12）
- `strategies/live_simulation/S3_S_VolSqueezeShort/S3_S_VolSqueezeShort.pla`（Rule #12）
- `strategies/live/L4_ConsolidationShort/L4_ConsolidationShort.pla`（ASCII，僅註解）
- `scripts/verify_pla_ascii.py`、`scripts/verify_settlement_flat.py`（重建）

備份：同目錄 `.bak_20260804`（本機，未進版控）

---

## 7. Git

### 7.1 開工前必做（**換機器必看**）

```bash
git config core.hooksPath .githooks
```

**沒設這行，pre-commit hook 不會執行。** hook 本身在版控裡（`.githooks/pre-commit`），
但啟用設定是 per-machine 的。`.gitattributes` 已鎖 LF，避免 checkout 後 shebang 變成
`#!/bin/sh\r` 而靜默失效。

驗證 hook 有效：

```bash
sh .githooks/pre-commit
```

應輸出 `ALL CHECKS PASSED -- commit allowed.` 且 exit 0。

### 7.2 同步狀態

- 分支：`main`（repo 只有這一個分支，無 tag）
- 本 session 結束時：`main...origin/main` = **0 ahead / 0 behind**
- 雲端 commit 總數：455（session 開始時 445，其中 7 個來自本 session、3 個來自另一台機器）

### 7.3 未追蹤項目（刻意保留，非遺漏）

- 各目錄的 `.bak_*` 備份（鐵律 3 產物，本機恢復用；跨機恢復靠 git 歷史）
- `strategies/research/L1_v3.1/`（僅含 `.bak_20260724` 與一個 log，非原始碼；
  真正的 v31 原始碼在 `strategies/research/L1_TrendLong/L1_v3.1/`，已在版控內）

---

## 8. 誠實聲明

- 本 session 所有 `.pla` 改動**未經 MC12 編譯**，僅做靜態檢查。
- 行事曆模組化的所有結論來自 `.pla` 靜態閱讀，**無回測、無 runtime log**。
- 63 筆假日日期**尚未與期交所 PDF 核對**。
- S3_L 死碼判定依賴「夜盤 15:00 起算、session-aligned」推算模型；校準點是 L1 的
  03:45 精準落在 45M 網格上（`entry_exit_sop.md` §三之一 明文佐證），但夜盤實際
  對齊方式**未經 MC12 實機確認**。
- 本文件由 Claude 產出，**未經第二方審查**（inventory 文件有走 fresh-context 驗收，本文件沒有）。
