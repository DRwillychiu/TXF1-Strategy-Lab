# 結算日策略設計憲法（Settlement-Day Design Constitution）

> **位階**：本文件為 TXF1-Strategy-Lab 所有上架／模擬／研究策略的**強制設計準則**。
> 任何新策略、任何版本升級、任何 input 調整，**必須先檢視是否違反本憲法**。
> 違反條款 = 不可上架。

**生效日**：2026-06-17（第一次月結算日當天定憲）
**最後更新**：2026-06-17（v1.2 條款 7/8 撤回，條款 1-6 保留）
**當前版本**：v1.2
**涵蓋商品**：TXF1（台指期近月連續）

---

## 第一章：為什麼結算日是「先天危險日」

### 1.1 市場結構性危險

台指期月結算（TAIFEX TXF）的本質：
- **時間**：每月第三個星期三，**13:30** 強制現金結算
- **機制**：所有未平倉部位以結算價現金交割，**不可拒絕、不可延後、不可協商**
- **價格**：結算價 = 13:25~13:30 共 5 分鐘的成交均價
- **影響**：當月合約於 13:30 後失效，下月合約從次日開始為主力

### 1.2 歷史行情特徵（為何結算日不可當「正常交易日」）

| 特徵 | 描述 | 對策略的破壞性 |
|------|------|--------------|
| **結算前波動放大** | 12:00 ~ 13:30 大戶結算前部位調整 | 趨勢策略 / 突破策略誤觸大量假信號 |
| **結算價操縱風險** | 13:25~13:30 拉抬／砍壓影響結算價 | 此區間進場 = 賭結算價方向 |
| **TXF1 連續合約跳價** | 13:30 後 data feed 切換到下月，價格 gap | 跨日持倉 = 跟換月合約混淆，圖表分析失真 |
| **流動性不均** | 結算日早盤大、午盤被結算壓單吸收 | 12:30 後出場 slippage 可能放大 |
| **隔日重新定價** | 06 合約結算 vs 07 合約開盤可能有結算貼水 | 跨結算持倉 = 隱性 gap risk |

### 1.3 為什麼「跨結算持倉」是策略設計的禁忌

**理由 1（資金管理）**：當月部位被強制現金交割，明日新單必須在新合約上重建。如果策略沒有處理這個切換，**MC12 上的策略狀態與實際 broker 持倉脫鉤**，導致風控失靈。

**理由 2（價格連續性）**：MC12 的 TXF1 是「近月連續」，結算後自動接續到下月合約。**圖表上看起來連續的 K 棒，實際合約已經變了**，所有歷史 SL / Trail / SP 的 ATR 計算基準也跟著變，策略邏輯出現潛在錯誤。

**理由 3（結算前 1 小時的行情噪訊）**：
- 12:30 ~ 13:30 = 結算前 1 小時 = 大戶平倉／操作結算價的高度操縱區
- 此區間進場 = **拿你的本金賭大戶結算行為**，不是賭你的策略 alpha

**理由 4（trade-off 已驗證）**：
- 「結算日強制平倉」損失 = 該日 12:30 之後的趨勢延續機會
- 「結算日不平倉」風險 = 結算價操縱 / 隔日合約跳價 / 結算前噪訊
- 歷史經驗：**後者 > 前者**

---

## 第二章：強制設計規範

### 條款 1：所有策略必須內建 Settlement_Flat 模組

每隻 .pla 檔必須具備以下 7 個元素，缺一不可上架：

```powerlanguage
{ 元素 1: inputs 段 }
Settlement_Flat_Time(1230),    { 12:30 trigger before 13:30 monthly settlement }

{ 元素 2: variables 段 }
v_Settlement_Day(false),

{ 元素 3: 偵測邏輯（必須在 entry/exit 邏輯之前執行）}
v_Settlement_Day = (DayOfWeek(Date) = 3) and
                   (DayOfMonth(Date) >= 15) and
                   (DayOfMonth(Date) <= 21);

{ 元素 4: Entry gate（進場條件必含此句）}
... and (v_Settlement_Day = false) then begin
    Buy/SellShort ("*_Entry") next bar at Market;
end;

{ 元素 5: Priority 0 出場（互斥優先序的第 4 位）}
else if v_Settlement_Day and Time >= Settlement_Flat_Time then begin
    Sell/BuyToCover ("*_Settlement") next bar at Market;
end;

{ 元素 6: Settlement 出場標籤前綴必須符合策略 prefix 規範 }
{ L1=TL_, L2=TS_, L3=CL_, L4=CS_, L5=BL_, S1=NM_ }

{ 元素 7: 驗證腳本 scripts/verify_settlement_flat.py 必須通過 }
```

### 條款 2：Settlement_Flat_Time 預設不可修改

- **預設值**：1230（12:30）
- **可調整範圍**：1200 ~ 1300（用戶自選但不建議）
- **絕對禁止**：> 1315（13:15 後無法保證 13:30 前歸零）
- **絕對禁止**：< 1130（11:30 前過於保守，犧牲日盤獲利機會）

### 條款 3：Priority 0 出場鏈順序固定

```
P0-1  Manual_Kill_Switch       (緊急停市)
P0-2  v_Registry_Expired       (假日登錄表過期)
P0-3  v_Holiday_Block          (假日 04:15)
P0-4  v_Settlement_Day + 12:30 (月結算 12:30)   ★ Settlement
P0-5  原策略邏輯               (SP / Trail / Daily Exit)
```

**順序不可更動**：Kill > Registry > Holiday > Settlement > 原邏輯。
任何違反順序的策略 = 不可上架。

### 條款 4：Scale-out 策略的 Settlement 必須成對

L5 / 未來任何 scale-out 策略：每口 Entry 標籤對應一個 `*_Settlement_<口別>` 標籤。

```powerlanguage
{ L5 範例 }
end else if v_Settlement_Day and Time >= Settlement_Flat_Time then begin
    Sell ("BL_Settlement_Bot") from Entry ("BL_Entry_Bot") next bar at Market;
    Sell ("BL_Settlement_Mid") from Entry ("BL_Entry_Mid") next bar at Market;
end;
```

### 條款 5：禁止「結算日 Roll-Over 模式」進入 live

理由：跨 chart 信號同步複雜度高，違反「先求穩定再求最佳」原則。
若未來要做，必須先在 research/ 跑滿 6 個月模擬 + 通過 P1-P3 才可晉升 live_simulation。

### 條款 6：策略分類三選一（用回測數據確認，非設計意圖）

**先前共識「日內 vs 跨日」二分法被 2026-06-17 實證推翻**。
真實分類維度不是「會否跨日」，而是「**會否撐到結算日 12:30**」。

| 類別 | 定義 | Settlement_Flat 角色 | 上架許可 |
|------|------|---------------------|---------|
| **A. Swing-Trend** | 趨勢類 + 任一筆撐到結算 12:30 | **核心鎖利機制** | ✅ |
| **B. Intraday / Night** | 任何 Alpha 類型 + 0 筆撐到結算 | **無感兜底保險** | ✅ |
| **C. Swing-Range** | 盤整類 + 任一筆撐到結算 12:30 | **災難級兜底**（在反轉前砍倉）| ❌ **設計禁區** |

**分類強制用回測數據**：
- 看 *_Settlement 標籤出場是否出現
- 若有任一筆觸發 → 該策略撐到結算
- 若無 → 該策略不撐結算

**禁止用「設計意圖」分類**。代碼可能有 bug、input 可能被改、Trail 可能未觸發 → 設計意圖 ≠ 實際行為。

### 條款 7：⚠️ 已撤回（2026-06-17）— 盤整類策略強制 TimeExit

**原條款**：盤整類策略必須在 12:00 強制平倉。

**撤回原因**：
1. 2026-06-17 在 L3 v13.3 / L4 v14.3 嘗試實作
2. 初版條件 `Time >= 1200` 在 MC PowerLanguage 24-hour 制下，
   夜盤 15:00-23:59 全部為 true → 持倉到夜盤開盤就被誤平倉
3. Hotfix v13.3.1 / v14.3.1 加入 `Time <= 1330` 上界
4. 用戶實測 L4 績效仍轉負 → **概念本身對既有盤整策略破壞性過大**
5. 完全回滾為 L3 v13.4 / L4 v14.4（保留 Settlement_Flat，移除 RangeForceExit）

**目前狀態**：暫不強制執行此條款。
**保留條款**：條款 1-6 仍有效。
**未來研究方向**（暫不上架）：
- 「結算日當天 + 盤整策略 = 12:00 提前」（限定條件，不影響一般日）
- 「持倉 > N 個商品交易日後 + 盤整策略 = 強制平倉」（基於持倉天數）
- 重新評估「跨日盤整 = 災難」這個論點是否在 L3/L4 實證上成立

詳見：[`docs/range_force_exit_rollback_20260617.md`](range_force_exit_rollback_20260617.md)

### 條款 8：⚠️ 同樣存在時段陷阱風險 — Trail / BE 的「跨日防線」

**原條款**：含 Trail / BE 的策略必須在 13:30 強制出場。

**重新檢視**：
與條款 7 同樣的 MC `Time` 24-hour 制陷阱 — `Time >= 1330` 在夜盤 15:00-23:59 都為 true。

**若未來實作此條款必須**：
1. 用閉區間 `Time >= 1330 AND Time <= 1345`（日盤收盤前 15 分鐘）
2. 或加日盤判定 `Time >= 1330 AND Time <= 1345 AND DayOfWeek(Date) in [1,2,3,4,5]`
3. 加 verify 腳本檢查「任何時段條件必須閉區間」

**目前狀態**：暫不強制執行此條款。實際上 L1 / L5 雖含 Trail / SP / BE，但歷史回測未出現「Trail 未觸發跨日 + Settlement_Flat 鎖利」的衝突。

### 補充規則 4：手動 Roll Over 後必須在 MC 同步 Force Flat

實戰場景：用戶在 broker 端手動把舊月份合約 Roll 到新月份合約。
**MC 不知道這個動作**，策略狀態仍顯示「持有舊合約」。

**強制流程**：
1. broker 手動 Roll 完成
2. **立刻**到 MC 對應策略上執行「Force Flat」（強制歸零策略內部部位）
3. 策略 reset 後，下一根 K 棒會根據新月份合約重新評估進場

未執行此流程 → Settlement_Flat 12:30 會發送平倉指令到 broker，但 broker 無對應部位 → 策略狀態錯亂。

### 補充規則 5：每次 input 調整後必須重跑分類驗證

實戰風險：今天 L5 在 Q1（Intraday/Night），但若改 TimeExit 從 13:30 改 14:00，
就可能漂移到 Q2 或 Q4。

**強制**：每次 input 修改後執行：
```bash
python scripts/verify_strategy_holding_classification.py
```
確認所有策略仍在 Q1/Q2/Q3 三象限內，無一漂移到 Q4。

---

## 第三章：12:30 為什麼是最佳觸發時點

| 候選時間 | 距結算 | 重試窗 | 缺點 | 評分 |
|---------|-------|-------|------|------|
| 11:30 | 120 分鐘 | 充裕 | 犧牲早盤趨勢機會過多 | ❌ |
| **12:30** ✓ | **60 分鐘** | **充裕（3 根 15-min K）** | **平衡點** | **✓ 採用** |
| 13:00 | 30 分鐘 | 緊（2 根）| 流動性快速衰減 | △ |
| 13:15 | 15 分鐘 | 極緊（1 根）| 無重試機會 | ❌ |
| 13:25 | 5 分鐘 | 無 | 結算前操縱區，slippage 不可控 | ❌❌ |

### 12:30 的具體機制

```
12:30 (Time=1230) → 條件成立，next bar at Market 發單
12:45 → 第 1 次成交機會（多數情況此處完成）
13:00 → 第 2 次重試（若 12:45 未成交）
13:15 → 第 3 次重試（最後機會）
13:30 → 結算 = 必為 0 部位 ✓
```

3 次重試 + 60 分鐘 buffer = 即使極端流動性危機也保證歸零。

---

## 第四章：新策略 onboarding 強制 checklist

**任何新策略進入 research/ 階段必須回答**：

- [ ] 是否內建 Settlement_Flat 模組（7 元素）？
- [ ] 是否通過 `scripts/verify_settlement_flat.py`？
- [ ] **是否通過 `scripts/verify_strategy_holding_classification.py`？**
- [ ] **三象限分類落位（A/B/C）= ？必須非 C**
- [ ] ~~若 Alpha 為 mean reversion：是否含 Time >= 1200 強制出場？~~ （條款 7 暫撤回）
- [ ] ~~若含 Trail/BE：是否含 Time >= 1330 強制出場？~~ （條款 8 暫撤回）
- [ ] 任何 `Time >=` 條件是否同時有 `Time <=` 閉區間？（防夜盤誤觸）
- [ ] 結算日當天的回測表現是否單獨計算？
- [ ] 結算日績效是否被排除在主績效指標外？

**任何 research → live_simulation 晉升必須回答**：

- [ ] Settlement_Flat 模組是否經過實盤模擬至少 1 次結算日測試？
- [ ] Settlement 出場標籤是否與其他出場明顯區隔？
- [ ] 對策略 PF / MDD 的衝擊是否 < 5%？
- [ ] **回測中 *_Settlement 觸發次數記錄存檔（決定 A 或 B 類別）？**

**任何 live_simulation → live 晉升必須回答**：

- [ ] 是否已在 MC9 / MC12 上完成「完全移除 → 重載 .pla」流程？
- [ ] 是否有完整文件記錄 Settlement_Flat 的部署日與測試結果？
- [ ] **是否已記錄手動 Roll Over 後 MC Force Flat 的標準流程？**

**任何 input 調整後必做**：

- [ ] 重跑 `verify_strategy_holding_classification.py`
- [ ] 確認分類仍在 A / B 象限（無漂移到 C 禁區）

---

## 第五章：結算日歷史與未來完整列表（2020-2030）

### 已驗證 132/132 個結算日（100% 精準）
驗證腳本：[`scripts/verify_settlement_detection_proof.py`](../scripts/verify_settlement_detection_proof.py)

### 近期重點結算日（用於上架後追蹤）

| 結算日 | 星期 | DoM | 備註 |
|--------|------|-----|------|
| 2025-12-17 | Wed | 17 | 模組設計前 |
| 2026-01-21 | Wed | 21 | 模組設計前 |
| 2026-02-18 | Wed | 18 | 模組設計前 |
| 2026-03-18 | Wed | 18 | 模組設計前 |
| 2026-04-15 | Wed | 15 | 模組設計前 |
| 2026-05-20 | Wed | 20 | 模組設計前 |
| **2026-06-17** | **Wed** | **17** | **★ Settlement_Flat 部署當天** |
| 2026-07-15 | Wed | 15 | 第 1 次實戰結算測試 |
| 2026-08-19 | Wed | 19 | 第 2 次 |
| 2026-09-16 | Wed | 16 | 第 3 次 |
| 2026-10-21 | Wed | 21 | 第 4 次 |
| 2026-11-18 | Wed | 18 | 第 5 次 |
| 2026-12-16 | Wed | 16 | 第 6 次 |

---

## 第六章：殘餘風險與後續工作

### 6.1 已識別但未處理的風險

| 風險 | 機率 | 處理 |
|------|------|------|
| 農曆假日（春節、端午、中秋）撞第三個週三 | < 0.5% / 年 | TAIFEX 會延後結算，需手動加入 HolidayFlat 登錄表 |
| 颱風臨時休市撞結算日 | < 0.1% | Manual_Kill_Switch 兜底 |
| MC12 input 持久化覆蓋預設值 | 中 | 規範要求「完全移除→重載」流程 |
| 用戶手動 Roll-Over 與策略部位脫鉤 | 中 | 規範要求 Roll 後手動 Force Flat 策略 |

### 6.2 開放研究題目（暫不上架）

1. **Settlement_Roll Mode**：12:30 平 06 後立刻在 07 合約建倉，需跨 chart 信號
2. **Settlement-day-specific alpha**：能否在結算日早盤捕捉特定 pattern（如結算多空對決）
3. **跨結算趨勢延續成本**：歷史回測比較「有/無 Settlement_Flat」對 L1 / L2 長期 PF 差距

---

## 第七章：條款修正流程

**任何條款修改必須**：
1. 在 GitHub 開 issue 說明動機
2. 提出實證資料佐證（歷史回測 / 結算日案例）
3. 經至少 3 個月實盤觀察期
4. 通過 verify_settlement_flat.py 與 verify_all_live.py 全項
5. 修改後須 commit 並更新本文件「最後更新」日期

**未經上述流程的修改 = 自動失效**。

---

## 附錄：相關文件交叉引用

### 設計文件
- [`docs/settlement_flat_module_20260617.md`](settlement_flat_module_20260617.md) — 模組詳細設計與五方案比較
- [`docs/settlement_flat_flow_diagram.svg`](settlement_flat_flow_diagram.svg) — 結算日完整決策流程圖
- [`docs/strategy_classification_decision_matrix.svg`](strategy_classification_decision_matrix.svg) — 策略分類×Settlement 角色決策矩陣 ★

### 實證報告
- [`docs/settlement_flat_backtest_validation_20260617.md`](settlement_flat_backtest_validation_20260617.md) — 6 隻策略真實回測深度驗證（L1 67.3% PnL 來自 Settlement）

### 驗證腳本
- [`scripts/verify_settlement_flat.py`](../scripts/verify_settlement_flat.py) — 42 項自動驗證（部署完整性）
- [`scripts/verify_settlement_detection_proof.py`](../scripts/verify_settlement_detection_proof.py) — 數學證明 + 132/132 月實測
- [`scripts/verify_strategy_holding_classification.py`](../scripts/verify_strategy_holding_classification.py) — ★ 三象限分類強制驗證
- [`scripts/analyze_settlement_backtest.py`](../scripts/analyze_settlement_backtest.py) — Settlement 出場績效分析
- [`scripts/verify_all_live.py`](../scripts/verify_all_live.py) — 110 項上架策略 master 驗證

### 專案總則
- [`CLAUDE.md`](../CLAUDE.md) — 含 PowerLanguage 規範第 11 條

---

## 修訂歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0 | 2026-06-17 | 初版生效（條款 1-5 + 章節 1-7）|
| 1.1 | 2026-06-17 | 新增條款 6-8 + 補充規則 4-5（基於 L3/L4/L5 跨日 33-47% 實證發現）|
| **1.2** | **2026-06-17** | **條款 7/8 撤回 — RangeForceExit 實作失敗（夜盤誤觸 + L4 績效轉負），保留條款 1-6 與補充規則 4-5。詳見 [rollback report](range_force_exit_rollback_20260617.md)** |

---

**本憲法 v1.2 生效於 2026-06-17。任何在此之後開發的策略，若無 Settlement_Flat 模組（條款 1-5）、未通過三象限分類驗證（條款 6），將不被視為合格上架候選。條款 7/8 暫撤回待重新設計。**
