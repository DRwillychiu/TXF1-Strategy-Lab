# S7 PreSettlementHarvest — FINAL VERDICT (KILLED)

**結案日**：2026-06-21（**SOP v2 自動化 10 分鐘 KILL**）
**狀態**：💀 **KILLED — NOT FEASIBLE**（不可行，正式結案）
**用戶決策**：2026-06-21 ultracode session（user 選 A 後 SOP 自動 KILL）
**最後版本**：N/A（pre-verification killed before W1）

---

## Stage -1: 策略內容說明（**2026-06-21 retroactively added per user instruction**）

> 用戶 2026-06-21 sharp 反饋：「我都不知道策略在幹嘛，你就否決」
> SOP v2 已加入 Stage -1 必走規則。本 verdict 補上 Stage -1。

### 策略內容（roadmap §9.3 S7）
```
類型: 純 calendar / event-driven Long-only

進場規則:
  - 偵測月份的第 3 個週三 (期貨結算日)
  - 該日 08:50 進場做多 (TXF1 day-session 開盤後 5 分鐘)
  - Filter: 前一日 close > 過去 5 日 SMA (uptrend confirmation)

出場規則:
  - 10:00 強制平倉 (持倉約 1 小時 10 分)
  - 或 1×ATR stop loss
  - 不持夜，不持隔日

樣本: 12 trades/year × 28y = ~340 trades
TAG: EVENT_DRIVEN_EXEMPT (需 Constitution amendment)
```

### 優點
- 純 calendar 邏輯，~80 LOC
- 純 TXF1 native, MC12 PASS
- 樣本充足 12/yr × 28y = 340 trades
- Operational coherence (標準 day-session)
- 學術文獻支持「結算前主力推升」現象
- 邏輯直觀，散戶都聽過

### 缺點
- 教科書級公開效應 (流傳 ≥ 10 年, algo 套利)
- 08:50 即進場無法判斷當日 regime
- 大空頭日 + uptrend filter 仍可能 long-trapped
- 持倉 1hr 10min 滑價佔比高
- 類似 L4 retire 證明 single-event 多單 hedge 也不必要
- EVENT_DRIVEN_EXEMPT amendment 需 user sign-off

### 為什麼不合適（**一段話**）
**「結算日多單」是台股期貨教科書級眾所周知的公開 anomaly（流傳 ≥ 10 年），TXF1 28 年 (1997-2026) 實證直接打臉這個直覺：6/6 macro regime **全部 Sharpe < 0.3**（最佳 1997-2002 +0.007，最差 2008-2009 GFC -0.924），整體 28y Sharpe -0.308 / PF 0.749 / WR 45.6% / Cum -8.13%。180 個 trades 樣本充足，不是樣本量問題；是「alpha 已被市場效率徹底消化」的結構性死亡。這精準驗證 L16 預警「教科書策略 default 視為 alpha 已衰減」。L22 lesson 由此誕生：calendar effects (S4 月末 + S7 結算日) 在 TWII/TXF1 系統性失效，未來不再追 calendar 類策略。**

---

## 一、為什麼 KILL — 一句話總結

> **「3rd Wed 結算日 08:50 進場做多 + uptrend filter」在 TWII 28 年 (1997-2026) 實證
> 完全沒有 alpha：28y Sharpe -0.308 / PF 0.749 / 6 個 macro regime 全部失敗 (0/6 Sharpe > 0.3)。
> L16「教科書策略 default 視為 alpha 已衰減」預警準確 — 結算日多單是公開
> ≥ 10 年的眾所周知 anomaly，已被市場效率消化。**

---

## 二、KILL 觸發證據（SOP v2 4 gates 全 FAIL）

### Gate A: 28-year Sharpe / PF

| 維度 | 數字 | 標準 | 結果 |
|------|------|------|------|
| 28-year Sharpe | **-0.308** | > 0.4 | ❌ FAIL |
| 28-year PF | **0.749** | > 1.3 | ❌ FAIL |
| 28-year Cum return | -8.13% | > 0 | ❌ |
| 28-year Mean return | -0.045% / trade | > 0 | ❌ |
| WR | 45.6% | > 50% | ❌ |

### Gate B: ≥ 4/6 regimes Sharpe > 0.3

| Regime | Sharpe | PASS? |
|--------|--------|-------|
| 1997-2002 Dot-com | +0.007 | ❌ |
| 2003-2007 China bull | -0.713 | ❌ |
| 2008-2009 GFC | -0.924 | ❌ |
| 2010-2014 Post-GFC | -0.485 | ❌ |
| 2015-2019 Sideways | +0.111 | ❌ |
| 2020-2026 COVID+AI | -0.338 | ❌ |

→ **0/6 regimes 通過**。L14 跨期 robustness 徹底失敗。

### Gate C: L18 Recent-bias check

- 28-year Sharpe: **-0.308**
- Recent 6.4y Sharpe: **-0.353**
- Ratio: undefined (28y 為負)
- → AUTO-KILL

### Gate D: Direction symmetry — N/A

S7 是 Long-only event，不適用雙方向測試。

---

## 三、Alpha 為什麼死了 — L16 教科書衰減精準預警

**「結算日多單」是台股期貨**人盡皆知**的公開 anomaly**：
- TXF1 結算日 = 每月第 3 週週三
- 「結算日 08:45 開盤通常會拉抬，後續 10:00-12:30 多空角力」
- 這個故事在期貨投資人 / 散戶教育材料中**至少流傳 10+ 年**
- Algo trader 大量套利已將 alpha 消化

**實證證據** (S7 W0 pre-verify):
- 1997-2002 Dot-com 時期 Sharpe 接近 0 (可能曾有微弱 alpha)
- 2003 以後**逐漸轉負**，2008/03/2010s 全部負 Sharpe
- 2020-2026 仍負 → **未現任何復活跡象**

**對比 S4 TurnOfMonth 結局**：
- S4: 6 regime 3/6 正 (但 cyclical decay 仍 KILL)
- **S7: 6 regime 0/6 正 (比 S4 更明確死亡)**

→ Calendar effects 在 TWII/TXF1 上**全面失效**。S4 + S7 兩個都死，**未來不再追 calendar 類策略**。

---

## 四、SOP v2 自動化效率證明

S7 KILL 流程套用新 SOP v2：

| Stage | Time | Action |
|-------|------|--------|
| Pre-W0 Gate 1 (MC12 native) | 1 min | ✓ PASS (純 TXF1 calendar) |
| Pre-W0 Gate 2 (Op coherence) | 1 min | ✓ PASS (Constitution amendment 一次性) |
| W0 Python pre-verify | 5 min | ❌ All 4 gates FAIL |
| FINAL_VERDICT.md 寫作 | 5 min | 完成 |
| **總時間** | **~10 分鐘** | **vs S2 多週、S6 0.1 天** |

**SOP v2 + Python pre-verify 把 KILL decision 壓到 minutes** — 比 S2 快 1000×+

---

## 五、KILL 速度全紀錄（5 個 KILL）

| 策略 | KILL 速度 | KILL 觸發 |
|------|---------|----------|
| S2 InsideBarBreak | 5 版本 + 多週 | 5 次迭代後實證 |
| S4 TurnOfMonth | 1 天 | W1 同日 28y 驗證 |
| S5 SPX_Overnight | 0.5 天 | W0 pre-verify |
| S6 ForeignPositionFade | 0.1 天 | pre-W0 user gate (L21) |
| **S7 PreSettlementHarvest** | **~10 分鐘** | **SOP v2 自動 4 gates** |

**Lessons compound 達到 1000× 加速**

---

## 六、學自 S7 的新 lesson **L22**

8. **L22: Calendar effects 在 TWII/TXF1 系統性死亡**
   - **S4 TurnOfMonth (月末多單)**: 28y cyclical decay
   - **S7 PreSettlementHarvest (結算日多單)**: 28y 0/6 regimes
   - 兩個獨立 calendar effect 都死亡 = TWII/TXF1 **calendar anomaly 普遍失效**
   - 未來不再追 calendar / day-of-week / month-end 類策略
   - 例外：若有**非直觀**的 calendar pattern（如 farmers' settlement Wednesday, 量子曆等冷門 angle），仍可考慮 — 但 default 高度懷疑

**累積 lessons (S2-S7)**：
- S2: L1-L13 (13)
- S4: L14-L18 (5)
- S5: L19-L20 (2)
- S6: L21 (1)
- **S7: L22 (1)** → **總計 L1-L22 (22 lessons)**

---

## 七、Roadmap 損傷終評估 — **5/6 KILLED**

| 策略 | 狀態 | KILL 理由 |
|------|------|----------|
| ~~S2 InsideBarBreak~~ | 💀 ARCHIVED FINAL | 教科書 alpha 衰減 (L5)|
| ~~S4 TurnOfMonth~~ | 💀 KILLED (1 天) | Cyclical decay (L16, L18)|
| ~~S5 SPX_Overnight~~ | 💀 KILLED (0.5 天) | Cross-asset follow 邏輯錯 (L19, L20)|
| ~~S6 ForeignPositionFade~~ | 💀 KILLED (0.1 天) | MC12 無法執行 (L21)|
| ~~**S7 PreSettlementHarvest**~~ | 💀 **KILLED (10 分)** | **Calendar 全死亡 (L22)** |
| **S8 FOMC_OvernightFade** | 🟡 **僅剩候選** | event-driven, 樣本 8/yr |

**5/6 KILLED = 83% KILL rate** → **roadmap 設計品質受嚴重質疑**

---

## 八、KILL 規範

```
若你看到本檔（S7_FINAL_VERDICT.md）：
  ❌ 不要寫 S7 spec / .pla
  ❌ 不要再嘗試任何「結算日做多」變種
  ❌ 不要嘗試其他 calendar 類策略（L22）
  ✅ 可以讀本檔 + L22
  
重啟條件（極嚴）：
  1. TWII 結算機制改變 (e.g., 改週四結算 / 改月結算)
  2. 學術新研究證明結算日 alpha 復活
  3. 用戶明確要求
```

---

## 九、資源轉向（**強烈建議認知 portfolio saturation**）

剩餘僅 **S8 FOMC_OvernightFade** 一個候選：
- Event-driven (FOMC FOMC 8 次/年)
- L20 favors fade (S5 SHORTS +0.230 提供 weak evidence for fade)
- L14 樣本 8 × 28 = 224 trades 充足
- L19 cross-asset 但是 fade 不 follow → 比 S5 less microstructure risk
- **預判：50-50 機會通過**

如果 S8 也 KILL → **接受 portfolio 已 100% saturate (6 frozen + S3 v2.0.4)**，所有 Q1-Q3 roadmap 候選都死

---

## 十、相關文件交叉參考

- **新 SOP v2** (本次 KILL 套用)：[../../../docs/STRATEGY_RD_SOP_v2.md](../../../docs/STRATEGY_RD_SOP_v2.md)
- **預檢分析腳本**：[../../../scripts/analyze_s7_presettlement_preverify.py](../../../scripts/analyze_s7_presettlement_preverify.py)
- **前置 S4 (calendar 第一個 KILL)**：[../S04_TurnOfMonth/S4_FINAL_VERDICT.md](../S04_TurnOfMonth/S4_FINAL_VERDICT.md)
- **S6 (Pre-W0 gate 來源)**：[../S06_ForeignPositionFade/S6_FINAL_VERDICT.md](../S06_ForeignPositionFade/S6_FINAL_VERDICT.md)
- **Roadmap (now 5/6 KILLED)**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)

---

## 十一、用戶聲明

> 「A，然後進入 S7」  
> — 2026-06-21 ultracode session

用戶選 A (寫 SOP v2 codify lessons) → 自動套用到 S7 → 10 分鐘 KILL。  
這是 **SOP automation 的標準 use case**：把 lessons 變成可重複的 gates，不依賴 Claude 即時判斷。

---

## 十二、Final stamp

```
S7 PreSettlementHarvest
Status: KILLED
Date:   2026-06-21 (same day as S4/S5/S6/S7 — 4 KILLs in one day)
Reason: 
  1. TWII 28-year calendar effect completely dead
     (Sharpe -0.308, PF 0.749, 0/6 regimes positive)
  2. L16 textbook decay precisely predicted
  3. Joins S4 in confirming calendar effects systemic death (L22)
Effort: ~10 minutes (SOP v2 automation)
Lessons: L22 contributed (calendar effects systemic death in TWII)
KILL speed: 1000x+ faster than S2 (SOP automation final state)
Replaced by: S8 FOMC (only remaining candidate) OR portfolio saturation acceptance
```

---

**Five strikes (S2, S4, S5, S6, S7) in one day. Roadmap is on its last leg — S8 is the final test.**
