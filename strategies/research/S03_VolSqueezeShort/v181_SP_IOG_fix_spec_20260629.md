# S3_S v1.8.1 EXPERIMENTAL — Bug 2 SP IOG Fix

**日期**：2026-06-29
**基於**：v1.8.0 GA Round 1 best (PF gross 4.13 / PF adj 2.24 歷史新高，但 SP maxL -132K)
**修正目標**：消除 SP IOG 副作用，恢復 v1.7.3 SP 機制 (-5K maxL)
**狀態**：🟡 EXPERIMENTAL，待 backtest 驗證

---

## 一、Headline

| Bug 2 修正 | v1.8.0-GA | **v1.8.1 預估** |
|-----------|-----------|--------------|
| SP maxL | -132,200 🚨 | **-5~-10K** ✅ |
| Net Profit | +846K | **+970K ~ +1,050K** ⭐ |
| 2024 BoJ trade | -132K (Bug 2 受傷) | **+78K**（同 v1.7.3） |
| 1M_Exit 機制 | 2 trades ✅ | 2 trades ✅ (保留) |
| 6/8 case 救援 | -10 點 ✅ | -10 點 ✅ (保留) |

---

## 二、Root Cause: SP IOG 副作用

### v1.7.3 (IOG=false) SP 行為
```
60M K 收盤 → 計算 SP_Floor_Price → set stop order
next 60M K 開盤 fill at SP_Floor_Price (或 gap 後 worst, 但受 floor 約束)
SP maxL = -5K (正常 30% 回吐範圍內)
```

### v1.8.0 (IOG=true) SP 副作用
```
每根 1M K 形成 → re-evaluate SP_Floor_Price → re-set stop order
1M K 內價格瞬間反彈越過 floor → fill at intrabar worst tick
SP maxL = -132K (穿透 floor 的 ~25x 距離)
```

### 受影響 case
- 2024-08-05 BoJ 那筆 SP -132K = 此 bug 受害
- 多筆 SP 平均 maxL 偏大也是此原因

---

## 三、Fix Design: BarStatus(1) = 2 Gate

### 邏輯
```pla
{ 所有 alpha exits 只在 60M K 收盤後 fire }
{ BarStatus(1) = 2 表示 Data1 (60M) 已是收盤狀態 }

if ExitFired = 0 and BarStatus(1) = 2 then begin
    {
      S-1 TP (limit)
      S-2 Mid (market)
      S-3 TimeStop (market)
      S-4a SP (stop) ← critical fix
      S-4b SL (stop) ← critical fix
    }
end;

{ 1M_Exit (S-0) 保持無 gate，IOG=true 即時反應 capitulation }
```

### 為什麼這 fix 對
1. **完全模擬 v1.7.3 IOG=false 行為**（已驗證 SP -5K OK）
2. **1M_Exit 不受影響**（保留 6/8 救援能力）
3. **P0 安全層不受影響**（Kill/Registry/Holiday/Settlement 仍可隨時 fire）
4. **改動極小**（1 行 BarStatus gate）

### 修改範圍
| Section | 修改 |
|---------|------|
| Section 9 Frozen SL + SetStopLoss | **不動** |
| Section 10 Entry | **不動**（v1.8.0 已加 gate）|
| Section 11 P0 safety | **不動**（必須隨時 fire）|
| Section 11 S-0 1M_Exit | **不動**（保留 IOG=true 救援能力）|
| **Section 11 S-1 ~ S-4** | **✅ 加 BarStatus(1)=2 gate** |
| Section 12-13 | **不動** |

---

## 四、v1.8.1 完整 inputs（**v1.8.0 GA-best 鎖定**）

### 從 GA Round 1 best 直接套用

| Input | v1.8.0 default | **v1.8.1 (GA best)** |
|-------|---------------|--------------------|
| ML_ActivationPct | 40 | **30** |
| ML_ScoreTrigger | 65 | **30** ⭐ |
| ML_MinCategories | 3 | 3 |
| ML_VolSpikeMult | 2.5 | **1.5** ⭐ |
| ML_VolAvgLen | 20 | **15** |
| ML_SpeedBars | 5 | 5 |
| ML_SpeedThreshPts | 80 | **30** ⭐ |
| ML_ATR_Short_Len | 5 | **3** |
| ML_ATR_Long_Len | 60 | **90** |
| ML_ATR_Ratio | 2.0 | **2.5** |

### 其他 22 個 inputs 鎖 v1.7.3-FINAL（不變）
- BBLen=45, BBStd=2, BWLookback=120, BWPctile=25
- ATR_Len=14, StopATRMult=2.75, TargetATRMult=3.5
- MaxBars=35, MidExit=True, MidExit_MinBars=2
- SP_Trigger=1.5, SP_Retain=70, Cooldown=1
- Use_Regime=True, FastMA=15, SlowMA=40, BlockRange=True, BlockWeakBull=True
- Holiday=415, Registry=1270101, Manual_Kill=False, Settlement=1230

---

## 五、MC12 Backtest SOP

### Chart Setup
- 載入 `S3_VolSqueezeShort_v181_EXPERIMENTAL.pla`
- Data1 = TXF1 60M
- Data2 = TXF1 Daily
- **Data3 = TXF1 1M**（必要，1M_Exit 邏輯依賴）
- **IntrabarOrderGeneration = TRUE**（**仍然 true**，因 1M_Exit 需要即時）
- 策略運算最大使用 K 棒數量 = 1000
- Initial Capital = 1,000,000 NTD
- Slippage = 1,000 NTD round-trip
- Trade Size = 1 contract
- 回測期間 2020-03 ~ 2026-06

### Optimize 設定
- **不勾任何 Optimize**（全 inputs 已是 GA best 鎖定）
- 直接 Run backtest

### 預估時間
- 單一 backtest ~5-15 分鐘（含 1M Data3 + IOG=true 慢一點）

### 輸出
- 1 個 xlsx：`TXF1  VolSqueezeShort_v181_EXPERIMENTAL 策略回測績效報告.xlsx`

---

## 六、Expected Result（**樂觀預估**）

### 5-way 對比（含 v1.8.1）

| 指標 | v1.7.3 | v1.7.4 | v180-orig | v180-GA | **v1.8.1 預估** |
|------|--------|--------|-----------|---------|---------------|
| Net | +1,013K | +792K | +502K | +846K | **+970K ~ +1,050K** |
| PF gross | 3.95 | 2.81 | 1.87 | **4.13** | **4.13 ~ 4.5** |
| PF adj | 2.17 | 1.72 | -0.99 | 2.24 | **~2.6** |
| Sharpe | **0.69** | 0.64 | 0.40 | 0.56 | **~0.75** |
| Sortino | **1.08** | 1.18 | 0.27 | 0.47 | **~1.10** |
| MDD % | -22.1% | -19.2% | -19.9% | -19.4% | **~-15%** ⭐ |
| WR % | **82.8%** | 55.9% | 78.3% | 75.0% | **~80%** |
| **SP maxL** | -5K | -4.8K | -132K | -132K | **~-5K** ⭐⭐ |
| 1M_Exit | n/a | n/a | 0 | 2 | **2 (保留)** |

→ **預估 v1.8.1 全 dimension 接近或超越 v1.7.3-FINAL**

---

## 七、Verify Pass Criteria

| Gate | 標準 | 通過則 |
|------|------|--------|
| SP maxL | > -15K | ✅ Bug 2 fix 成功 |
| Net Profit | > +900K | ✅ 接近 v1.7.3 水準 |
| PF gross | > 3.95 | ✅ 超越 v1.7.3 |
| 1M_Exit trigger | ≥ 2 | ✅ 救援能力保留 |
| 6/8 case loss | < -20 點 | ✅ 1M_Exit 仍有效 |

→ **全 5 gate pass = 進 W4 WFA 9 windows**

→ W4 WFA pass ≥ 5/9 = **promote v1.8.1 取代 v1.7.3-FINAL**

---

## 八、Honest Caveats

### Caveat 1: 預估基於樂觀情境
- SP maxL 從 -132K → -5K 是 best case
- 實際 backtest 可能仍有殘留 IOG 副作用
- 需數據驗證

### Caveat 2: 1M_Exit 在 IOG=true 仍有 fill 風險
- 2 個 1M_Exit trades (-10 點 each) 是 best case
- 真實 live 可能 fill 在 worse 價（已知 IOG 限制）

### Caveat 3: 6/8 gap case 仍是 market structure 風險
- 1M_Exit 在開盤瞬間能否 fire 取決 1M K 形成速度
- 若 60M K 開盤直接 gap → 1M_Exit 也可能 dead

### Caveat 4: W4 WFA 仍待驗證
- backtest pass 不等於 OOS pass
- 必須 9 windows 9 個獨立期間驗證

---

## 九、相關文件

- `S3_VolSqueezeShort_v181_EXPERIMENTAL.pla` (本檔對應 .pla)
- `v180_GA_R1_result_20260629.md` (GA Round 1 結果)
- `v174_v180_desktop_threeway_analysis_20260629.md` (3-way 對比)
- `S3_VolSqueezeShort_v180_EXPERIMENTAL.pla` (v1.8.0 baseline)

---

## 十、Status

- v1.7.3-FINAL: ✅ production (live_simulation, 未動)
- v1.8.0-GA: 🟡 archived (Bug 2 受害, GA 證明 architecture)
- **v1.8.1: 🟢 EXPERIMENTAL, awaiting backtest verify**
- v1.7.4 cap 100: ARCHIVED (gap failure)
- v1.7.5 conditional: SUPERSEDED
