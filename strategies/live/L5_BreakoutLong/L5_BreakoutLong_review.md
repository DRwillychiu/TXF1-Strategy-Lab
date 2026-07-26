# L5 BreakoutLong — v19.7 結構性審查（2026-06-13）

> 目的：將 L5 升級到與 L1/L2/L3/L4 同等的安全層級（假日鐵律、凍結停損、移除 dead code）
> 範圍：純結構性修正，不動 God Mode 核心引擎（Scale-Out / MFE 三階追蹤 / BL_BE）
> 實證：舊版 BREAKOUT AND Excel（152 筆 / 5 口）作為診斷基礎；v19.7 部署後需 1 口新 Excel 驗證

---

## 一、發現 — 三個結構性問題

### 問題 1：DayOfWeek = 7 dead code（3 處）

**現況**（v19.6）：
```powerlanguage
{ Line 103 }  if DayOfWeek(Date) = 7 then v_Allow_Entry = false;
{ Line 106 }  if DayOfWeek(Date) = 6 and Time >= 1330 then v_Allow_Entry = false;
{ Line 109 }  if DayOfWeek(Date) = 7 and Time >= 400 then begin
{ Line 110 }      if MarketPosition = 1 then begin
{ Line 111 }          Sell ("BL_SatClose_Bot") ... Market;
{ Line 112 }          Sell ("BL_SatClose_Mid") ... Market;
{ Line 113-114 }  end; end;
```

**根因**：PowerLanguage / MultiCharts 的 `DayOfWeek` 返回 **0-6**（Sun=0, Mon=1, ..., Sat=6）。
**DayOfWeek = 7 永遠 false**，3 處引用全部 dead code。

**作者原意推測**：可能誤以為 PL 用 1-7 索引（Sun=1, Sat=7），所以：
- Line 103：原意「週日不交易」→ 永不觸發（無傷，週日本來就沒 bar）
- Line 106：用 DOW=6 是正確的（Saturday），這條工作
- Line 109-114：原意「週六早上 04:00 後強制平倉」→ **dead，從未觸發**

**舊版 Excel 實證**（4.8 年 / 152 筆）：
- BL_SatClose_Bot 觸發筆數：**0**
- BL_SatClose_Mid 觸發筆數：**0**
- 確認 dead code

**v19.7 處置**：移除 line 103 和 line 109-114（連同 BL_SatClose 標籤）。保留 line 106（DOW=6 Saturday block 是對的）。

---

### 問題 2：缺乏假日鐵律保護

**現況**：L5 v19.6 是 5 隻上架策略中 **唯一沒有 HolidayFlat 模組** 的。

| 策略 | 假日模組 |
|------|---------|
| L1 | ✅ HolidayFlat_v3 |
| L2 | ✅ HolidayFlat_v3 |
| L3 | ✅ HolidayFlat_v3 |
| L4 | ✅ HolidayFlat_v3 |
| **L5** | ❌ **無** |

**風險**：跨假持倉會在重新開盤時受跳空衝擊。

**舊版 Excel 實證**：4.8 年 152 筆 **0 筆跨假持倉**——歷史運氣好（L5 持倉時間中位 ~7.5h，較少跨日）。

**v19.7 處置**：套用與 L1-L4 同一份模組（byte-identical）：
- Holiday_Tail[80] 63 筆 TAIFEX 登錄表
- Holiday_Flat_Time(415) — 15M 格線 04:15 強制歸零
- Registry_Valid_Until(1270101) fail-safe
- Manual_Kill_Switch(false) 緊急開關
- 新標籤：BL_Holiday_Bot/Mid、BL_RegistryEnd_Bot/Mid、BL_Kill_Bot/Mid

**6/18 端午是首次實戰測試**。

---

### 問題 3：初始停損 ATR 漂移

**現況**（v19.6）：
```powerlanguage
v_ATR_Buffer = v_Current_ATR * ATR_Stop_Mult;
... 
Sell ("BL_SL_Bot") ... at (v_Box_Btm - v_ATR_Buffer) Stop;
```

`v_Current_ATR = AvgTrueRange(35)` 每根 15M K 棒重算。
**同 L1 V2.5 之前、L4 v14.0 的同一個 bug**：reload 策略停損價會變、ATR 擴張時停損漂移。

**v19.7 處置**：加入 Freeze_SL_On(true) 切換：
```powerlanguage
if Freeze_SL_On and v_SL_Locked = false then begin
    v_Frozen_ATR        = v_Current_ATR;
    v_Frozen_ATR_Buffer = v_Frozen_ATR * ATR_Stop_Mult;
    v_SL_Locked         = true;
end;
{ initial stop uses v_Frozen_ATR_Buffer instead of v_ATR_Buffer }
```

追蹤層仍用 v_Current_ATR（設計意圖：追蹤跟隨當下波動）。

---

## 二、本輪刻意不動的部分

### 不動 BL_BE 機制（待下一輪 A/B）

L5 v19.6 已有 BL_BE_Bot/Mid 機制：
- Scale-Out 後 60% 剩餘倉位
- Trail 未啟動或 trail 算出的停損 < 進場價 → 改用 BE（進場價）保護

這是 **內建設計**，從未做 A/B 對照。

**L4 v14.2 A/B 經驗**：BE 在多階段獲利策略會截斷大尾巴，淨損 -345K。

**L5 是否有同樣問題？需要 A/B 驗證**。但本輪 scope 是「結構性安全」，不動核心引擎。

**列為下一輪研究**：L5 v19.8 候選 — `BE_Enable(true/false)` 切換 + A/B。

### 不做夜盤封鎖（L5 與 L4 特性不同）

| 策略 | 02-04 進場 PnL | 處置 |
|------|----------------|------|
| L4 | -120,800（9 筆 / 3 贏 6 輸 / 0 BR）| **封鎖** |
| L5（舊 Excel）| **+87,800**（12 筆 / 7 贏 5 輸）| **不封鎖** |

L5 夜盤實際賺錢，封鎖會傷害績效。

### 不動 Scale-Out / Trail 倍數

God Mode 引擎核心參數（ScaleOut_Percent / Trail_Start_Mult / MFE_ATR_Tier_1-3）保留 v19.6 原值。

---

## 三、v19.7 完整變更摘要

| 變更 | 類型 | 影響 |
|------|------|------|
| 移除 line 103 (DOW=7 entry block) | Dead code 清除 | 無功能變化（從未觸發）|
| 移除 line 109-114 (BL_SatClose) | Dead code 清除 | 無功能變化（從未觸發）|
| 加入 Holiday_Tail[80] + 63 筆登錄表 | 新增結構 | 前瞻保護假日（歷史 0 違規）|
| 加入 Holiday_Flat_Time(415) | 新增 input | 04:15 強制歸零 |
| 加入 Registry_Valid_Until(1270101) | 新增 input | fail-safe 2027/1/1 |
| 加入 Manual_Kill_Switch(false) | 新增 input | 緊急停市 |
| 加入 Freeze_SL_On(true) | 新增 input | 修復 ATR 漂移 bug |
| 加入 v_Frozen_ATR / v_Frozen_ATR_Buffer | 新增變數 | 凍結停損計算 |
| 加入 v_Holiday_Block / v_Registry_Expired / Registry_Warn_ID / hidx | 新增變數 | 假日狀態追蹤 |
| 加入 v_SL_Locked | 新增變數 | 凍結觸發旗標 |
| 加入 6 個 Priority 0 出場標籤 | 新增 sell orders | BL_Holiday / BL_RegistryEnd / BL_Kill（各 _Bot/_Mid）|
| 修改初始 SL 計算（Freeze 時用 Frozen ATR）| 行為變化 | reload 不變、ATR 擴張不漂移 |

---

## 四、預期影響評估

### 預期會改變

- 初始 SL fill 分布（因 ATR 凍結讓停損價在進場後固定）
- 4.8 年無跨假持倉 → Holiday 模組不影響歷史
- 整體淨利、PF、MDD 可能微幅變動（ATR 凍結效應）

### 預期不會改變

- 進場筆數（除非有交易曾經剛好在尾段日窗口進場，舊版 0 筆已驗證）
- BL_BE / BL_Trail / BL_TP / BL_TimeExit / BL_BreakExit 行為
- Scale-Out 機制

### 接受條件（v19.7 部署後）

- ✅ 淨利偏差 ±5% 內（凍結 SL 是優化非劣化）
- ✅ MDD 不惡化超過 10%
- ✅ 0 BL_Holiday / BL_RegistryEnd / BL_Kill 觸發（符合歷史 0 違規）
- ✅ 0 BL_SatClose 觸發（標籤已不存在）
- ✅ Top-10 贏家保留 ≥ 90%（純結構修正不應砍大贏家）

---

## 五、MC9 部署步驟

1. **空手狀態確認** L5 無倉位
2. 載入 `_Live_Adaptive_Farmer_v19_7_BreakoutLong`
3. Inputs 預設值（生產）：
   - `Freeze_SL_On = true`
   - `Holiday_Flat_Time = 415`
   - `Registry_Valid_Until = 1270101`
   - `Manual_Kill_Switch = false`
4. 跑完整回測（與 v19.6 基準對比）
5. Export Excel → 提供作 v19.7 acceptance 驗證

---

## 六、下一輪 v19.8 候選議題

| 議題 | 必要性 | 工作量 |
|------|--------|--------|
| BL_BE A/B 測試（與 L4 同框架）| 中（可能截斷大贏家）| 半天 + MC9 |
| L5 MFE 分析（驗證多階段獲利模式）| 中 | 半天 |
| ScaleOut_Percent 敏感度（40% 是否最佳）| 低 | 半天 |
| 5 口 vs 1 口資金曲線（舊 Excel 是 5 口）| 中（口數策略）| 1 天 |

---

## 七、與其他策略的對齊

| 安全模組 | L1 | L2 | L3 | L4 | L5 v19.6 | **L5 v19.7** |
|----------|----|----|----|----|----------|---------------|
| HolidayFlat_v3 (63 筆) | ✅ | ✅ | ✅ | ✅ | ❌ | **✅** |
| FrozenSL | ✅ | ✅ | ✅ | ✅ | ❌ | **✅** |
| Manual_Kill_Switch | ✅ | ✅ | ✅ | ✅ | ❌ | **✅** |
| Registry_Valid_Until fail-safe | ✅ | ✅ | ✅ | ✅ | ❌ | **✅** |

**L5 v19.7 把 L5 從「上架但安全 gap」升級到「與 L1-L4 同等防護」。**
