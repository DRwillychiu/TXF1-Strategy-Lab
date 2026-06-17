# S2 InsideBarBreak v0.2 — 中文逐段註解

**MC Load Name**：`STRATEGY_GEN_InsideBarBreak`
**版本**：v0.2（Phase 1 模組化升級完成，2026-06-17）
**檔案**：[`S2_InsideBarBreak.pla`](S2_InsideBarBreak.pla)
**前身**：[`archive/batch01_S2-S5/S2_InsideBarBreak.pla`](../archive/batch01_S2-S5/S2_InsideBarBreak.pla)

---

## 一、策略本質

### 1.1 賺什麼錢

日線層級的「**內包母子線突破**」(Inside Bar Break) 賺**方向選擇後的爆發行情**。

```
母棒 (Mother Bar) ：較大範圍的日 K 棒
  ┌────────┐
  │        │  ← Mother High
  │   ┌─┐  │
  │   │ │  │  ← Inside Bar（完全被母棒包覆）
  │   └─┘  │
  │        │  ← Mother Low
  └────────┘
```

行情走勢通常會在內包形成「**波動率壓縮**」，之後爆出方向 → 我們等突破發生再進場跟隨。

### 1.2 進場邏輯

| 條件 | 內容 |
|------|------|
| 樣態識別 | Data2(Daily)[1] H < Data2[2] H **且** Data2[1] L > Data2[2] L |
| 母棒過濾 | `MinMotherRange ≤ MotherRange ≤ MaxMotherRange`（避免過小/過大）|
| 趨勢過濾 | Daily MA(20) 上 → **只做多**；下 → **只做空** |
| 觸發 | Close > MotherBar 高 + `BreakOffset`（多）或 Close < MotherBar 低 - `BreakOffset`（空）|
| 進場 | next bar at Market |

### 1.3 出場邏輯

| 出場類型 | 觸發條件 | 標籤 |
|---------|---------|------|
| 停損 | EntryPrice ∓ MotherRange × StopPct% （最少 `MinStopPts`）| `*X_IB_SL` |
| 停利 | EntryPrice ± MotherRange × TargetMult | `*X_IB_TP` |
| 時間停損 | 持倉 ≥ `MaxBarsHeld(30)` 根 30M K | `*X_IB_Time` |

---

## 二、Phase 1 防護模組（憲法 v1.2 強制）

### 2.1 Settlement_Flat 模組

```powerlanguage
{ 偵測 - 每根 K 棒執行 }
v_Settlement_Day = (DayOfWeek(Date) = 3) and
                   (DayOfMonth(Date) >= 15) and
                   (DayOfMonth(Date) <= 21);

{ Entry gate - 結算日當天 0 進場 }
if v_IsInsideBar and ... and (v_Settlement_Day = false) then ...

{ Priority 0 出場 - 12:30 強制平倉 }
else if v_Settlement_Day and Time >= Settlement_Flat_Time then
    sell ("LX_IB_Settlement") next bar at Market;
```

**為什麼 S2 必須有**：MaxBarsHeld=30 個 30M K = **15 小時持倉** → 跨日是設計本意 → 必然會撞結算日。

### 2.2 HolidayFlat_v3 模組

63 筆 TAIFEX 假日登錄表（與 L1-L5 共用）；夜盤 04:15 前強制平倉避免假日跨假持倉。

### 2.3 Manual_Kill_Switch + Registry_Valid_Until

颱風臨時休市等黑天鵝事件的人工開關 + 登錄表過期兜底。

---

## 三、Priority 0 出場優先序

```
LONG 側：                       SHORT 側：
  P0-1 Manual_Kill_Switch    →    P0-1 Manual_Kill_Switch
  P0-2 v_Registry_Expired    →    P0-2 v_Registry_Expired
  P0-3 v_Holiday_Block       →    P0-3 v_Holiday_Block
  P0-4 v_Settlement_Day      →    P0-4 v_Settlement_Day
  P0-5 SL / TP / Time        →    P0-5 SL / TP / Time
```

雙向策略每側獨立的 Priority 0 鏈，標籤 LX_IB_ / SX_IB_ 嚴格區分。

---

## 四、標籤完整清單

### 進場標籤
| 標籤 | 動作 | 觸發 |
|------|------|------|
| `LE_IB_Entry` | buy | Inside Bar + MA up + 突破上沿 |
| `SE_IB_Entry` | sell short | Inside Bar + MA down + 跌破下沿 |

### Long 出場標籤
| 標籤 | 觸發 |
|------|------|
| `LX_IB_Kill` | Manual_Kill_Switch=true |
| `LX_IB_RegistryEnd` | Date > Registry_Valid_Until |
| `LX_IB_HolFlat` | 假日前夕 04:15 |
| `LX_IB_Settlement` | 結算日 12:30 |
| `LX_IB_SL` | EntryPrice - v_StopDist |
| `LX_IB_TP` | EntryPrice + v_TargetDist |
| `LX_IB_Time` | 持倉 ≥ MaxBarsHeld |

### Short 出場標籤
鏡像對應的 `SX_IB_*` 共 7 個。

**總計：2 個進場 + 14 個出場 = 16 個標籤**，全部符合 LE_/SE_/LX_/SX_ 規範。

---

## 五、Inputs 完整清單

| Input | 預設 | 用途 |
|-------|------|------|
| BreakOffset | 5 | 突破閥值 |
| StopPct | 50 | 停損 = MotherRange × 50% |
| TargetMult | 1.5 | 停利 = MotherRange × 1.5 |
| MinMotherRange | 50 | 母棒下界 |
| MaxMotherRange | 400 | 母棒上界 |
| MALen | 20 | 日線 MA 過濾 |
| MaxBarsHeld | 30 | 持倉上限（30 × 30M = 15h）|
| MinStopPts | 40 | 停損最少點數 |
| Holiday_Flat_Time | 415 | 04:15 假日平倉 |
| Registry_Valid_Until | 1270101 | 登錄表有效到 2027/01/01 |
| Manual_Kill_Switch | false | 緊急停市開關 |
| Settlement_Flat_Time | 1230 | 12:30 結算平倉 |

**共 12 個 input**，全部具備 production 預設值。

---

## 六、未來 Phase 路線

### Phase 1 ✅（本檔完成 2026-06-17）
- [x] 從 archive 拉出
- [x] 加入 Settlement_Flat 模組
- [x] 加入 HolidayFlat_v3 模組
- [x] 加入 Manual_Kill_Switch + Registry
- [x] 統一標籤前綴
- [x] 寫 annotated 文件

### Phase 2 ⏳（待 MC 真實回測）
- [ ] 在 MC12 30M chart 載入新版 S2 .pla
- [ ] 跑 2020/01/01 ~ 2026/06/17 完整回測
- [ ] 確認 MC 30M 真實績效（與 Python 日線代理對比）
- [ ] 跑 `verify_strategy_holding_classification.py` 確認分類為 Swing-Trend

### Phase 3 ⏳（P1-P3 標準驗證）
- [ ] Walk-Forward Analysis WFE > 50%
- [ ] Monte Carlo 95% MDD < 帳戶 30%
- [ ] OOS PF > 1.0
- [ ] 至少 60 筆樣本（避免統計噪訊）

### Phase 4 ⏳（晉升 live_simulation）
- [ ] 滿足晉升條件
- [ ] 移到 `strategies/live_simulation/S2_InsideBarBreak.pla`
- [ ] 註冊到 `verify_settlement_flat.py` 與其他 master verify

---

## 七、風險警告

1. **歷史回測樣本僅 34 筆**：統計信心不足，需要 MC 重跑驗證
2. **PF 4.61 過高**：可能是過擬合或樣本偏差，應對 OOS 表現持懷疑
3. **雙向策略**：Long 和 Short alpha 可能不對稱，可能需要拆兩隻單向版本
4. **日線級訊號 + 30M 進場**：跨週期協調需要 MC 真實回測驗證

---

## 八、相關文件

- [策略總則](../README.md)
- [憲法 v1.2](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [策略分類決策矩陣](../../../docs/strategy_classification_decision_matrix.svg)
- [原 archive 版本（v0.1 對照）](../archive/batch01_S2-S5/S2_InsideBarBreak.pla)
- [batch01 績效總覽](../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md)
