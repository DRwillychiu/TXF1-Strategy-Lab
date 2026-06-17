# 結算日策略設計憲法（Settlement-Day Design Constitution）

> **位階**：本文件為 TXF1-Strategy-Lab 所有上架／模擬／研究策略的**強制設計準則**。
> 任何新策略、任何版本升級、任何 input 調整，**必須先檢視是否違反本憲法**。
> 違反條款 = 不可上架。

**生效日**：2026-06-17（第一次月結算日當天定憲）
**最後更新**：2026-06-17
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
- [ ] 結算日當天的回測表現是否單獨計算？
- [ ] 結算日績效是否被排除在主績效指標外？

**任何 research → live_simulation 晉升必須回答**：

- [ ] Settlement_Flat 模組是否經過實盤模擬至少 1 次結算日測試？
- [ ] Settlement 出場標籤是否與其他出場明顯區隔？
- [ ] 對策略 PF / MDD 的衝擊是否 < 5%？

**任何 live_simulation → live 晉升必須回答**：

- [ ] 是否已在 MC9 / MC12 上完成「完全移除 → 重載 .pla」流程？
- [ ] 是否有完整文件記錄 Settlement_Flat 的部署日與測試結果？

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

- [`docs/settlement_flat_module_20260617.md`](settlement_flat_module_20260617.md) — 模組詳細設計與五方案比較
- [`docs/settlement_flat_flow_diagram.svg`](settlement_flat_flow_diagram.svg) — 完整決策流程圖
- [`scripts/verify_settlement_flat.py`](../scripts/verify_settlement_flat.py) — 42 項自動驗證
- [`scripts/verify_settlement_detection_proof.py`](../scripts/verify_settlement_detection_proof.py) — 數學證明 + 132/132 月實測
- [`scripts/verify_all_live.py`](../scripts/verify_all_live.py) — 110 項上架策略 master 驗證
- [`CLAUDE.md`](../CLAUDE.md) — 專案總則

---

**本憲法生效於 2026-06-17。任何在此之後開發的策略，若無 Settlement_Flat 模組或違反任一條款，將不被視為合格上架候選。**
