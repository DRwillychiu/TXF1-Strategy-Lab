# S3_S v1.7.4 EXPERIMENTAL — Hard SL Cap Spec

**日期**：2026-06-28
**狀態**：🟡 EXPERIMENTAL — research/ 中，**不動 live_simulation v1.7.3-FINAL**
**驅動哲學**（user 2026-06-28 ruling）：
> 「賺該賺的行情，不該賺的行情就不做。然後做到小虧損，小獲利以及大獲利。控制賠就是最好的策略規劃。」

---

## 一、Headline 一句話

**v1.7.4 = v1.7.3-FINAL + 單筆 SL 強制上限 100 點（-20K NTD = -2% 帳戶）**

---

## 二、Why（核心 design rationale）

### v1.7.3-FINAL 實證問題

| 類別 | avg/筆 | 帳戶占比 | 符合 "小虧" 哲學？|
|------|-------|---------|------------------|
| SL | **-106K** | **-10.6%** | ❌ 太大 |
| SP | +29K | +2.9% | ✅ 小獲利 |
| TP | +144K | +14.4% | ✅ 大獲利 |

→ 2/3 哲學達成，**SL 端是 systemic flaw**

### Root cause（從 6/9 chart case）
- 進場時 Frozen ATR 193 點（vol expansion）
- 2.75 × 193 = **530 點 SL**
- 一根 60M K 內反彈 530 點 = 1.0% 漲幅（盤中常見）
- 結果：單筆吃滿 -10.6% 帳戶

---

## 三、What（具體改動，1 input + 1 行）

### 改動 1：新增 input

```pla
SL_Hard_Cap_Pts ( 100 ),   { v1.7.4: max SL distance pts; 100 pts = -20K NTD = -2pct account on 1M }
```

### 改動 2：Section 9 Frozen SL 計算用 MinList cap

```pla
{ v1.7.3 (原): }
v_Frozen_SL_Dist = v_Frozen_ATR * StopATRMult;

{ v1.7.4 (新): }
v_Frozen_SL_Dist = MinList( v_Frozen_ATR * StopATRMult, SL_Hard_Cap_Pts );
```

### 改動範圍：**僅 2 行**（Section 1 inputs + Section 9 frozen SL 計算）
- 其他 22 個 input 完全不變
- 其他 12 個 section 完全不變
- 出場 8 layer priority chain 完全不變
- SP/TP/Mid/TimeStop 機制完全不變

---

## 四、Effect（vol 分區效果）

| Vol 環境 | 60M ATR | 原 SL (2.75 ATR) | v1.7.4 SL | Cap 是否生效 |
|---------|--------|----------------|-----------|------------|
| 平時 | ~60 點 | 165 點 | 100 點 | ✅ 生效（限制 -65 點）|
| 中等 vol | ~80 點 | 220 點 | 100 點 | ✅ 生效（限制 -120 點）|
| Vol expansion | ~120 點 | 330 點 | 100 點 | ✅ 生效（限制 -230 點）|
| **6/9 case** | **~193 點** | **530 點** | **100 點** | ✅ **限制 -430 點 = +86K NTD** |
| 極端 vol | ~250 點 | 690 點 | 100 點 | ✅ 限制 -590 點 |

→ **Hard cap 永遠生效**（除非 ATR 極低 < 37 點，理論上 < 1% TXF1 60M）

---

## 五、Expected Impact（基於 v1.7.3 數據預估）

### 樂觀情境（hard cap 完美救 SL 不傷 SP/TP）

| 指標 | v1.7.3-FINAL | v1.7.4 預估 | 變化 |
|------|--------------|------------|------|
| SL trades | 3 / -319K (avg -106K) | **3 / -60K (avg -20K)** | 救 **+259K** |
| TP trades | 5 / +721K | 5 / +721K（不變）| = |
| SP trades | 21 / +612K | 21 / +612K（不變）| = |
| Mid trades | 0 | 0 | = |
| **Net Profit** | +1,013,600 | **+1,272,600** | **+25.6%** |
| **PF gross** | 3.95 | **~5.5+** | +39% |
| **PF adj** | 2.17 | **~3.0+** | +38% |
| **MDD %** | -22.1% | **~-12%** | **改善 10pp** |
| **WR** | 82.8% | 82.8% | = |
| **Avg trade** | +34,952 | **+43,883** | +26% |

### 中性情境（hard cap 救 SL 但部分 SL trades 翻成更多 SL）

| 指標 | 預估 |
|------|------|
| SL trades | 5-8 / -100~150K（每筆 ~-20K，但筆數增）|
| Net | ~+1,100K (+8%) |
| MDD | ~-15% (-7pp) |
| PF | ~4.5 |

### 悲觀情境（hard cap 截斷正常波動 trades）

| 指標 | 預估 |
|------|------|
| SL trades 大增 | 8-12 筆 |
| 部分 SP/TP 被誤截為 SL | -50~100K 損失 |
| Net | ~+900K (-11%) |
| 但 MDD 仍改善 -15% 級 |

→ **無論哪個情境，MDD 必改善**（哲學最重要的「控制賠」達成）

---

## 六、Caveats（誠實警告，不可掩飾）

### Caveat 1: 可能截斷 60M K 內回轉的 trades
- 譬如進場後虧 -120 點，本來 60M K 收盤前可能 recover
- Hard cap 100 點直接出 → 變成實虧
- **但這正是「控制賠」的設計代價**

### Caveat 2: Vol expansion 進場可能變難
- ATR 100+ 點時，cap 100 點 = SL 距離小於 1 ATR
- noise 就觸 SL
- 可能 SL trades 從 3 增至 5-8 筆（但每筆都小虧）

### Caveat 3: 改變策略本質
- 從 "Vol-adaptive SL" → "Fixed-risk SL"
- 對 vol 突發異常的容忍度下降
- 但 **這是好事**（你要的 "控制賠"）

### Caveat 4: 真實 live 滑價
- Hard cap 100 點 SL 觸發, 滑價 5-10 點 = -105~110 點實際
- 計入後仍 ~-22K (-2.2% 帳戶) = 還在「小虧」範圍

### Caveat 5: 動 .pla 規範代價
- v1.7.4 是 EXPERIMENTAL，**不動 live_simulation v1.7.3-FINAL**
- 必須走完 W3 backtest + W4 WFA + W5 10-dim 才能 promote
- 預估時間 5-7 days

---

## 七、Backtest Verification Plan（W3 / W4）

### Step 1: W3 Full-period backtest（4 組對照）

| 組別 | SL_Hard_Cap_Pts | 預期效果 |
|------|---------------|---------|
| **Baseline** | 9999 (effectively 無 cap) = v1.7.3 | 對照組 |
| **A** | **100** (推薦初值) | 主測試 |
| B | 80 | 更激進 |
| C | 150 | 更保守 |

跑 2020-2026 full period，比較 4 組：
- Net / PF / Sharpe / MDD / WR
- SL trades count + avg
- TP/SP trades 是否被誤截

### Step 2: 若 A 組數據強 → W4 WFA 9 windows
- 套同 v1.7.3 的 9 windows 時間表
- 比較 vs v1.7.3 WFA 結果 (2/9)
- 改善 ≥ 4/9 才考慮 promote

### Step 3: 若 W4 PASS → W5 10-dim eval → promote v1.7.4

### Step 4: 若 W3 顯示 hard cap 害事 → archive v1.7.4 EXPERIMENTAL，維持 v1.7.3

---

## 八、MC12 Backtest SOP

### Chart Setup
- Data1 = TXF1 60M（不變）
- Data2 = TXF1 Daily（不變，regime filter 需要）
- Initial Capital = 1,000,000 NTD
- Slippage = 1,000 NTD round-trip
- Trade Size = 1 contract
- IntrabarOrderGeneration = false（不變）
- 策略運算最大使用 K 棒數量 = 1000

### 4 組 Inputs 配置（其他 22 個 input 全鎖 v1.7.3 best）

| Input | Baseline | A | B | C |
|-------|----------|---|---|---|
| SL_Hard_Cap_Pts | **9999** | **100** | **80** | **150** |
| 其他 22 個 | 同 v1.7.3 | 同 v1.7.3 | 同 v1.7.3 | 同 v1.7.3 |

### 輸出
- 4 個 xlsx：
  - `TXF1  VolSqueezeShort_v17 v174_Baseline.xlsx`
  - `TXF1  VolSqueezeShort_v17 v174_A_cap100.xlsx`
  - `TXF1  VolSqueezeShort_v17 v174_B_cap80.xlsx`
  - `TXF1  VolSqueezeShort_v17 v174_C_cap150.xlsx`

→ 跑完傳 4 個 xlsx，我做完整對比 + W4 WFA 決策

---

## 九、Lesson L26 Candidate（無論 v1.7.4 結果如何）

```
Lesson L26: 「Hard SL Cap 是 short 策略 systemic risk control 必要設計」

Why:
  - 短策略遇 capitulation 反彈時 SL 設計上就是 worst case
  - ATR-based SL 在 vol expansion 進場時自動變大
  - 純 ATR 機制無法防止單筆 -10%+ 帳戶虧損
  - 違反 institutional 「單筆 risk 1-2%」標準

How to apply:
  - 所有 short 策略 SL 加 hard cap input
  - 預設值 ~ 100 點（-2% 帳戶）
  - W3 backtest 驗證不害真實 alpha
  - 若 hard cap 過嚴 (cap < 1 ATR) → 適度放寬到 1.2 ATR 級

System-wide rollout (after S3_S v1.7.4 verify):
  - L2 TrendShort: check SL distance distribution
  - L4 ConsolidationShort: check
  - S3 RapidPullbackShort: check
  - Apply hard cap to all 4 short sleeves
```

---

## 十、相關文件

- `S3_VolSqueezeShort_v174_EXPERIMENTAL.pla` (本檔對應 .pla)
- `S3_S_VolSqueezeShort.pla` (live_simulation v1.7.3-FINAL，**不動**)
- `S3_S_VolSqueezeShort_strategy.md` (v1.7.3 strategy doc)
- 用戶 2026-06-28 對話 ruling
