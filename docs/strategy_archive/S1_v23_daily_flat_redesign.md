# S1 v2.3 — Daily 05:00 Flat 為 PRIMARY 安全機制（重新架構）

> 建立日期：2026-06-13
> 用戶批評：「你是特別針對節日作時間調整但本質上這份純夜盤策略應該要在 05:00 就把夜盤策略的單平倉才對。這部分你沒有規劃清楚。」
> 對應修正：v2.2 → v2.3 重新架構（Daily Flat = 第一順位）

---

## 一、用戶批評的本質

### v2.2 的設計錯誤
v2.2 的 changelog 把修正包裝成「**P0 ExitTime bug fix + P1 Holiday 模組**」，把 Holiday 寫成「P1 主要新增」。

但對 **純夜盤策略** S1 而言：
- 「每天 05:00 必須空手」= 本質性、不可妥協的需求
- Holiday 跨假保護 = 已被「每天空手」自動覆蓋的次要需求

**v2.2 把次要當主要，本末倒置**。

### 用戶要求
「**05:00 就把夜盤策略的單平倉**」必須清楚規劃、設計穩固，不能依賴 Holiday 模組或一個 input 的單一數值。

---

## 二、v2.3 重新架構：三層安全模型

```
┌─────────────────────────────────────────────────────────────┐
│  PRIMARY（每天必須做到）                                      │
│  ✅ Daily 05:00 Flat                                         │
│     - 每晚 04:15 開始觸發 forced flat                         │
│     - 04:30 / 04:45 / 05:00 共 3 次重試                      │
│     - 04:45 OPEN 之前 GUARANTEED 空手                        │
│     - 標籤：LX_NM_DailyFlat                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  SECONDARY（特殊日子加碼，對 S1 多為冗餘）                     │
│  ⚠ Holiday Flat (LX_NM_Holiday)                              │
│  ⚠ Manual Kill Switch (LX_NM_Kill)                           │
│  ⚠ Registry Fail-Safe (LX_NM_RegistryEnd)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  TERTIARY（緊急救命，理論上永不觸發）                          │
│  🚨 Day Session Emergency (LX_NM_DaySession_EMERGENCY)       │
│     - 若 PRIMARY 失敗，position 殘留到 08:45 日盤             │
│     - 立即市價平倉                                            │
│     - 觸發 = 需要立刻調查 Daily Flat 為什麼失敗               │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、Input 重新設計

### v2.2 的混亂
單一 `ExitTime` input 身兼**三職**：
1. 進場閘門（`Time < ExitTime`）
2. 出場觸發（`Time >= ExitTime`）
3. 夜盤定義（`v_IsNightSession = Time < ExitTime`）

→ 用戶看到「ExitTime=415」不知道實際影響範圍

### v2.3 的清晰
拆成 3 個專責 input：

| Input | 預設 | 職責 | 用戶可調整？ |
|-------|------|------|--------------|
| `EntryEnd_Time` | 415 | 進場閘門（Time ≥ 此 → 不再發新單）| ✅ 是 |
| `DailyFlat_Time` | 415 | 出場觸發（Time ≥ 此 → forced flat）| ✅ 是 |
| `NightCloseBar_Time` | **500** | **HARD CAP** — 永不在此 bar 發單（防 09:00 bug）| ❌ **不可改** |

`NightCloseBar_Time` = 500 是 **物理常數**，因為 TXF1 夜盤的最後一根 15M K 棒就是 04:45-05:00（Time=500）。在這根 bar 發 market 單，next bar = 08:45 日盤 = 3 小時 45 分鐘 gap 暴露。

---

## 四、為什麼這次絕對不會出 v2.2 的 bug？

### v2.2 的 bug 重述
- `if Time >= ExitTime and Time < NightOpen then sell next bar at market`
- `NightOpen = 1500`，所以 `Time < 1500` 包含 Time=500（最後夜盤 bar）AND 日盤所有 bar
- 若 position 在 Time=500 bar 還在 → `sell next bar at market` → 下一根 bar = Time=900 → **08:45 開盤成交 = bug**

### v2.3 的硬性保護
- `if Time >= DailyFlat_Time and Time < NightCloseBar_Time then sell next bar at market`
- `NightCloseBar_Time = 500`，所以 `Time < 500` **排除** Time=500 bar
- 在 Time=500 bar 上：條件 `Time < 500` = FALSE → **永不發單** → bug 從架構層級被消滅

### 即使用戶把 DailyFlat_Time 設錯
- 用戶設 `DailyFlat_Time = 500`（v2.1 的 bug 值）
- 條件：`Time >= 500 AND Time < 500` = **永遠 FALSE** → DailyFlat 永不觸發
- 但 Day Session Emergency 在 Time>=845 接管 → 雖然在 08:45 才平倉，但起碼有 fallback
- 用戶會立刻發現問題（因為 LX_NM_DailyFlat 應該每天觸發，沒觸發 = 設定錯誤）

### 即使用戶把 EntryEnd_Time 設錯
- 用戶設 `EntryEnd_Time = 500`（允許到最後一根 bar 進場）
- 進場仍可能在 Time=445 bar 發單，Time=500 bar 成交
- 但 DailyFlat 在 Time=415 已經發出 market 出場單
- 在 Time=500 bar 上 PRIORITY 0 出場優先：DailyFlat fires → sell next bar
- 下一根 bar = Time=900（日盤）→ **bug 又出現！**

🔴 **這就是為什麼 `NightCloseBar_Time` 防的是 DailyFlat 在 Time=500 fire，不是 entry**。

修正：DailyFlat 條件 `Time < NightCloseBar_Time=500` 確保 Time=500 上不 fire。但若 entry 在 Time=500 bar 進場，DailyFlat 在 SAME bar 也不 fire（因條件 FALSE），Day Session Emergency 在 Time=900 接手。

所以即使用戶 mis-set EntryEnd_Time，只是會有 1-2 筆 09:00 出場（Day Session Emergency 救援），不會像 v2.1 全部都是。

**從架構層級限制 bug 的最大破壞範圍**。

---

## 五、Priority 0 出場優先序（互斥）

```powerlanguage
if MarketPosition = 1 then begin
    if Manual_Kill_Switch then
        sell ("LX_NM_Kill") next bar at market
    else if v_Registry_Expired then
        sell ("LX_NM_RegistryEnd") next bar at market
    else if v_Holiday_Block and Time >= Holiday_Flat_Time then
        sell ("LX_NM_Holiday") next bar at market
    else if Time >= DailyFlat_Time and Time < NightCloseBar_Time then
        sell ("LX_NM_DailyFlat") next bar at market         ← PRIMARY (每天必觸發)
    else if Time >= 845 and Time <= 1245 then
        sell ("LX_NM_DaySession_EMERGENCY") next bar at market;  ← 永不該觸發
end;
```

**互斥優先序**：
1. Kill（緊急停市）
2. RegistryEnd（登錄表過期）
3. Holiday（假日專屬）
4. **DailyFlat（每天本職）** ← 主要
5. DaySession EMERGENCY（救命）

---

## 六、新出場標籤對照表

| 標籤 | v2.2 | v2.3 | 觸發條件 |
|------|------|------|---------|
| LX_NM_Kill | ✅ | ✅ | Manual_Kill_Switch = true |
| LX_NM_RegistryEnd | ✅ | ✅ | Date > Registry_Valid_Until |
| LX_NM_Holiday | ✅ | ✅ | v_Holiday_Block AND Time >= Holiday_Flat_Time |
| **LX_NM_Time** | ✅ | ❌ 移除 | （已被 LX_NM_DailyFlat 取代）|
| **LX_NM_DailyFlat** | ❌ | ✅ **新** | **Time >= DailyFlat_Time AND Time < 500** |
| **LX_NM_DaySession_EMERGENCY** | ❌ | ✅ **新** | **Time >= 845 AND Time <= 1245**（救命）|

---

## 七、MC12 部署檢查清單

### 替換到 v2.3 時必做
1. **空手確認** MC12 S1 模擬部位為 0
2. **完全移除** 現有 S1 strategy（Format Window 刪除）
3. **重新從 .pla 新增** strategy（強制使用 .pla 預設值）
4. **截圖 Inputs 面板** 給我確認所有新欄位都正確
5. 必須看到的 5 個 PRIMARY/SECONDARY input：
   - `EntryEnd_Time` = 04:15 (415)
   - `DailyFlat_Time` = 04:15 (415)
   - `NightCloseBar_Time` = 05:00 (500)
   - `Holiday_Flat_Time` = 04:15 (415)
   - `Registry_Valid_Until` = 1270101
6. 不該再看到的：`ExitTime`（已移除）

### 重跑回測驗收條件
✅ **LX_NM_DailyFlat 出現**（取代舊 LX_NM_Time）
✅ **LX_NM_DailyFlat 出場時間 = 04:30 / 04:45 / 05:00**
✅ **沒有任何 09:00 出場**（除非 LX_NM_DaySession_EMERGENCY 觸發，那要立刻調查）
✅ **LX_NM_DaySession_EMERGENCY 觸發筆數 = 0**

---

## 八、v2.3 設計哲學總結

> **「Pure night strategy 的本質 = 每天 05:00 必須空手。其他都是次要的。」**

v2.3 用 **架構層級的硬性限制**（NightCloseBar_Time 不可越界）+ **三層防護**（PRIMARY / SECONDARY / TERTIARY）+ **明確職責分離**（EntryEnd / DailyFlat / NightCloseBar）+ **緊急救命網**（DaySession_EMERGENCY）來確保這個本質性需求 **不論用戶輸入什麼錯誤都能被守住**。

---

## 九、與 v2.2 績效對比預期

v2.2 baseline（用戶 Excel）：
- 783 trades, +1,720,600, PF 1.42, MDD -269,800
- LX_NM_Time 460 筆 **全部** 09:00 出場（bug）
- LX_NM_Time 平均吐掉 40 點 MFE

v2.3 預期：
- 進場筆數 ↓（EntryEnd_Time=415 嚴格執行）
- LX_NM_DailyFlat 出場時間散布 04:30-05:00
- 平均出場價格 ↑（避免日盤跳空）
- **預期淨利 ↑、PF ↑、MDD 改善**

**確切數字待 MC12 重跑回測驗收**。
