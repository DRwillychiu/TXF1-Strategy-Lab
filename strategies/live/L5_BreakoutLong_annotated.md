# L5 盤整多頭突破 — STRATEGY_WILLY_LONG_BREAKOUT_C

> 腳本名稱：_Live_Adaptive_Farmer_v19_8_BreakoutLong
> MC 載入名稱：STRATEGY_WILLY_LONG_BREAKOUT_C
> 版本：**v19.9 + Cooldown-D + HolidayFlat_v3 + FrozenSL + ImmediateStop**
> 平台：MultiCharts 9.0 PowerLanguage x64
> 狀態：**READY**（v19.9 GA 驗證完成，ATR_Stop_Mult 高原確認，待部署）
> 口數：**1 口**（100 萬本金）

---

## v19.9 變更（2026-06-25）

### 1. 1 口簡化：移除 dead code

在 1 口操作下，以下機制永遠不觸發，全部移除：

| 移除項目 | 原因 |
|---------|------|
| ScaleOut_Percent 輸入 + v_ScaleOut_Size | Round(1 × 0.4) = 0，無法分批 |
| TP 出場（BL_TP_Bot/Mid）| 需要 ScaleOut_Size > 0 |
| SP 模組（SP_Trigger_Pts/SP_Retain_Pct + 全部 SP 變數）| v19.8 A/B 全 FAIL，永久關閉 |
| Fallback 區塊（BL_HoldSP/BL_HoldBE）| 需要 CurrentContracts < MaxContracts，1 口不可能 |

**10 個出場標籤移除**（BL_TP/SP/TrailSP/HoldSP/HoldBE × Bot/Mid），**16 個保留**。

完整移除程式碼歸檔：[L5_v199_1contract_removed_code.md](../../docs/strategy_archive/L5_v199_1contract_removed_code.md)

日後擴展至多口數時（建議 5 口以上），按歸檔文件中的 Restoration guide 恢復。

### 2. Cooldown-D：同箱封鎖 + 新箱冷卻

**問題**：182 筆交易中 56% 為同價位 cluster churn。27 個虧損 cluster、73 筆、-719,400 NTD（佔毛損 38%）。最嚴重案例：T58-T63 在 @20249 連續 6 次進場，5 次虧損。

**根因**：SL 出場後 Box 沒變，進場條件立刻重新成立，策略盲目重新進場。

**解決方案（Plan D）**：

| 規則 | 觸發條件 | 動作 |
|------|---------|------|
| 同箱封鎖 | `v_Box_Top = v_LastExit_BoxTop` | **永久禁止**進場，直到新箱形成 |
| 新箱冷卻 | 不同 Box 但 `BarNumber - v_LastExit_BarNum < Cooldown_Bars` | 等待 N 根 bar |

新增輸入：`Cooldown_Bars(3)` — GA 範圍 1-10，step 1

新增變數：
- `v_Cooldown_OK` — 每根 bar 計算，決定是否允許進場
- `v_LastExit_BarNum` — 上次出場的 BarNumber
- `v_LastExit_BoxTop` — 上次出場的 Box_Top（從 v_Entry_BoxTop 繼承）
- `v_Entry_BoxTop` — 進場時鎖定的 Box_Top

### 3. 出場架構簡化

v19.9 在 1 口下只有兩條出場路徑：

```
進場 → 盤整中 → Stage 1（SL 或 TimeExit）
進場 → 突破盤整 → Stage 2（Trail 4 階動態追蹤 + BE 底線）
```

出場優先序：
```
Priority 0: Kill > Registry > Holiday > Settlement
Stage 1:    SL（Frozen ATR）> TimeExit
Stage 2:    Trail（4 階動態）> BE（進場價）
```

---

## v19.8 SP A/B 實證摘要（歷史，程式碼已移除）

裁定：**全 5 變體 FAIL**，SP 程式碼在 v19.9 完全移除。
- L5 淨利 88% 集中在 Top-10 大贏家，SP 截斷大尾巴 = 自殺
- 完整實證：[L5_v198_variant_results.md](../../docs/strategy_archive/L5_v198_variant_results.md)

---

## v19.7 三大修正（2026-06-13）

| 修正 | v19.6 狀況 | v19.7 改善 |
|------|-----------|-----------|
| **DayOfWeek=7 Dead Code** | 3 處引用 DOW=7，PowerLanguage Sat=6 → 永不成立 | 全移除 |
| **無假日鐵律** | 跨假持倉無保護 | HolidayFlat_v3：63 筆 TAIFEX 登錄表 + 04:15 強制歸零 |
| **初始停損漂移** | v_ATR_Buffer 每根重算 | Freeze_SL_On：進場根鎖 ATR |

---

## 策略概述

- **類別**：盤整突破型
- **方向**：★純做多
- **週期**：Data1 = 15M / Data2 = 日線 / Data3 = 週線（三時間框架）
- **核心邏輯**：日線偵測盤整箱體（波動收縮） → 多頭環境確認 → 15M 突破箱體底部/中線進場做多 → MFE 三階追蹤停損
- **市場曝險**：僅 4.19%（大部分時間等待盤整形態出現）

---

## MC9 回測績效（v19.9 validated 2026/06/25）

| 指標 | v19.8 基準（無冷卻） | **v19.9 驗證版** |
|------|:-------------------:|:----------------:|
| 初始資金 | 1,000,000 NTD | 1,000,000 NTD |
| 滑價 | 1,000 NTD/口 RT | 1,000 NTD/口 RT |
| 總交易次數 | 182 | **93** |
| 勝率 | 44.5% | **60.2%** |
| Profit Factor | 1.553 | **2.680** |
| 淨利 | +1,049,200 NTD | **+1,361,400 NTD** |
| 毛利 | ~2,946,200 NTD | +2,171,600 NTD |
| 毛損 | ~-1,897,000 NTD | -810,200 NTD |
| MDD | -336,200 (-22.1%) | **-201,600 (-20.2%)** |
| SL 出場 | 84 | **20** |
| Trail 出場 | 18 | **9** |
| TimeExit 出場 | 76 | **61** |
| Cluster（虧損） | 27 個 / 73 筆 / -719,400 | **0 個 / 0 筆 / +0** |
| Top-10 集中度 | — | 92.6% |

### 交易分析

| 指標 | 數值 |
|------|------|
| 平均獲利交易 | +38,778 NTD |
| 平均虧損交易 | -21,897 NTD |
| 盈虧比 | 1.771 |
| 最大單筆獲利 | +340,800 NTD（2026/04/07） |
| 最大單筆虧損 | -104,600 NTD |

### GA 驗證紀錄（2026-06-25）

GA 多參數優化選出 ATR_Stop_Mult = 2.5（Net +772,600, PF 1.706）。
ATR_Stop_Mult 敏感度掃描推翻此結論：

| ATR_Stop_Mult | 淨利 | PF | MDD | 判定 |
|:---:|---:|:---:|---:|:---:|
| 4.5 | +1,361,400 | 2.680 | -201,600 | **峰值** |
| 3.5 | +1,304,400 | 2.616 | -201,600 | 高原 |
| 5.0 | +1,295,000 | 2.485 | -209,400 | 高原 |
| 4.0 | +1,212,200 | 2.440 | -201,600 | 高原 |
| 3.0 | +1,086,600 | 2.175 | -201,600 | 邊緣 |
| 2.5 | +772,600 | 1.706 | -217,600 | 斷崖 |

結論：**3.5-5.5 為高原（PF 2.4-2.7），ATR_Stop_Mult 維持 4.5**。
GA 改的 Trail 參數保留（Trail_Start_Mult=1, Trail_Mult_0=3.5 等），
僅 ATR_Stop_Mult 回復原值。

---

## 進場邏輯

### 第一層：日線盤整偵測（Commander）
```
① 當日高低點在前 4 日的高低區間內（High ≤ Ref_High, Low ≥ Ref_Low）
② 當日波幅 ≤ 前 4 日區間的 60%（Range_Shrink_Rate = 0.6）
→ 盤整箱體成立，記錄 Box_Top 和 Box_Btm
③ 若價格突破箱體 → 盤整失效，退出
```

### 第二層：方向過濾
```
① 日線趨勢：Close > MA60 → 偏多（v_Trend_Dir = 1）
② 週線過濾：Close > 20MA AND Close > 60MA（AND 邏輯，比 L1 更嚴格）
③ 風報比：Expected_Reward / Expected_Risk ≥ 1.1
```

### 第三層：進場執行（15M）
```
兩個進場區域：
• BL_Entry_Bot：價格跌到箱底附近 → 反彈回箱底時 Stop 單做多
• BL_Entry_Mid：價格跌到中線附近 → 反彈回中線時 Stop 單做多
前搶 5 tick，Target 設在中線/箱頂
```

**設計思路：在盤整箱體的底部和中線「接球」做多，賺的是盤整突破後的多頭延續。**

---

## 出場邏輯（v19.9 簡化版）

### Stage 1：盤整中（SL + TimeExit）
| 機制 | 條件 |
|------|------|
| 初始停損 | Box_Btm/Mid - Frozen_ATR × 4.5（Stop） |
| 時間停損 | 持倉 ≥ 30 根 K 棒 → 市價出場 |

### Stage 2：突破盤整（4 階動態追蹤）
```
啟動：盤整箱體被打破（日線突破 Box_Top 或 Box_Btm）
追蹤停損倍數隨 MFE 距離動態調整：

MFE 距離          追蹤倍數    含義
< ATR × 2.5      3.5 ATR    寬鬆，讓利潤成長
≥ ATR × 2.5      2.0 ATR    收緊
≥ ATR × 6.0      2.0 ATR    維持
≥ ATR × 11.0     1.0 ATR    收緊，鎖住大部分利潤

追蹤停損 = 最高點 - ATR × 動態倍數
若追蹤停損 < 進場價 → 改用打平停損（BE）
```

### Cooldown-D（進場冷卻）
```
同箱封鎖：上次出場的 Box 仍在 → 禁止進場（硬規則）
新箱冷卻：新 Box 但距上次出場 < Cooldown_Bars 根 → 等待
```

---

## 參數一覽

| 參數 | 值 | 模組 | 說明 |
|------|-----|------|------|
| Lookback_Bars | 4 | Commander | 盤整參考期（日線） |
| Range_Shrink_Rate | 0.6 | Commander | 波幅收縮門檻（60%） |
| Daily_MA_Len | 60 | Commander | 日線趨勢 MA |
| Min_RR_Bull | 1.1 | 過濾 | 最低風報比 |
| ATR_Length | 35 | 共用 | ATR 計算長度 |
| ATR_Stop_Mult | 4.5 | 停損 | 初始停損 ATR 倍數 |
| FrontRun_Ticks | 5 | 進場 | 前搶 tick 數 |
| Time_Stop_Bars | 30 | 停損 | 時間停損 K 棒數 |
| Trail_Start_Mult | 1 | MFE | 追蹤啟動 ATR 倍數 |
| MFE_ATR_Tier_1 | 2.5 | MFE | 第一階收緊門檻 |
| MFE_ATR_Tier_2 | 6.0 | MFE | 第二階收緊門檻 |
| MFE_ATR_Tier_3 | 11 | MFE | 第三階收緊門檻 |
| Trail_Mult_0 | 3.5 | MFE | Tier 0 追蹤寬度（MFE < Tier_1） |
| Trail_Mult_1 | 2.0 | MFE | Tier 1 追蹤寬度 |
| Trail_Mult_2 | 2 | MFE | Tier 2 追蹤寬度 |
| Trail_Mult_3 | 1 | MFE | Tier 3 追蹤寬度 |
| Weekly_MA_Fast | 20 | 週線 | 週線快速 MA |
| Weekly_MA_Slow | 60 | 週線 | 週線慢速 MA |
| Cooldown_Bars | 3 | 冷卻 | 新箱冷卻等待 bar 數（GA 1-10） |

---

## MC 設定

| 項目 | 設定 |
|------|------|
| Data1 | TXF1 15 分鐘 |
| Data2 | TXF1 日線 |
| Data3 | TXF1 週線 |
| 初始資金 | 1,000,000 NTD |
| 滑價 | 1,000 NTD/口 |
| 手續費 | 0 |

---

## 策略特色

1. **盤整箱體偵測**：日線自動辨識波動收縮（≤ 60%），不依賴主觀判斷
2. **雙進場區域**：底部和中線兩個接球點，提高進場機會
3. **MFE 4 階追蹤（God Mode）**：隨利潤增長自動收緊停損，從 3.5 ATR 收到 1.0 ATR
4. **Cooldown-D 冷卻機制**：同箱永久封鎖 + 新箱時間冷卻，杜絕 cluster churn
5. **AND 週線過濾**：比 L1 的 OR 過濾更嚴格，確保多頭環境確立才進場
6. **時間過濾**：凌晨 4-5 點和週六不進場
7. **Frozen SL**：進場根鎖定 ATR，停損不漂移
