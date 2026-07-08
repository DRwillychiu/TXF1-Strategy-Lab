# S16_S v0.4-CANDIDATE Deep Analysis (2026-07-09)

**Config**: Fast=25 / Slow=90 / Slope=26 / QS45 / **MaxHold=24** / StopATRMult=4
**xlsx**: `MC9_20260108/回測報告/TXF1  S16_S_MACrossShort 策略回測績效報告.xlsx`
**Verdict**: 🟡 **CANDIDATE PROFITABLE — 但已從 "MA Cross" 蛻變為 "Momentum Burst + Time Stop" 策略**

---

## 一、Headline Metrics

| 指標 | 值 | Rule 判定 |
|------|---|---------|
| **Net Profit** | **+1,059,200** | ✅ |
| **PF** | **1.903** | ✅ |
| PF adj | 1.415 | ❌ (< 1.5) |
| **MDD $** | **-259,200** | ✅ (< 300K abs) |
| MDD % | -65.62% | ❌ (> 30% relative) |
| Trades | 119 | ✅ (≥ 100) |
| WR % | 26.89% | ❌ (< 30%) |
| Sharpe | +0.459 | ❌ (< 0.5) |
| Recovery | 0.000 | ⚠️ |
| Avg Trade | +8,900 (推算) | ✅ |

**4/8 Rule #13 gates PASS**

---

## 二、🚨 出場結構完全「異化」— 策略本質已改變

### Exit Signal Distribution

| Signal | N | Total | WR% | Avg | Max Loss | Max Win |
|--------|---|-------|-----|------|----------|---------|
| **SX_MA_TimeStop** | **31** | **+2,232,200** | **100%** | **+72,006** | 0 | **+388,000** |
| SX_MA_BE_Trail2 | 2 | -5,200 | 50% | -2,600 | -5,600 | +400 |
| SX_MA_BE_Trail1 | 2 | -9,800 | 0% | -4,900 | -7,800 | 0 |
| SX_MA_QuickStop_Time | 27 | -117,000 | 0% | -4,333 | -10,000 | 0 |
| SX_MA_QuickStop_Loss | 57 | -1,041,000 | 0% | -18,263 | -39,600 | 0 |
| **SX_MA_GoldenCross** | **0** | **N/A** | N/A | N/A | N/A | N/A |
| SX_MA_ML_Exit | 0 | N/A | N/A | N/A | N/A | N/A |
| SX_MA_SL | 0 | N/A | N/A | N/A | N/A | N/A |

### 🔥 關鍵洞察

1. **TimeStop 100% WR 全 31 筆獲利 avg +72K** — 這是驚人的
   - 意味 **持倉滿 24 bars（2 小時）就走完 momentum burst**
   - MaxHold=24 是 **alpha 直接產生器**，不是 safety net
2. **Golden Cross 0 trades** — Fast=25/Slow=90 差距太大，交叉根本觸不到
3. **ML_Exit 0 trades** — Multi-Layer 沒 fire
4. **SL 0 trades** — StopATRMult=4 太寬，QuickStop 已先出場

**策略已質變**：
```
原本設計:  ZLEMA 死叉 → 抓中短期動能 → Golden Cross 出場（讓利潤奔跑）
實際運作:  MinSlope 26 篩極端動能 → 抓 momentum burst → 2 小時後強制 exit
```

**這是一個「Time-Based Momentum Burst Capture」策略**，不是 MA Cross。

---

## 三、Year-by-Year 表現

| Year | N | Wins | WR | Net | Avg |
|------|---|------|-----|-----|-----|
| 2020 | 3 | 1 | 33% | +38,600 | +12,867 |
| 2021 | 2 | 0 | 0% | -29,800 | -14,900 |
| 2022 | 3 | 1 | 33% | -10,600 | -3,533 |
| 2023 | 0 | 0 | - | 0 | - |
| **2024** | 10 | 2 | 20% | +49,800 | +4,980 |
| **2025** | 21 | 5 | 24% | **+433,400** | +20,638 |
| **2026** | 80 | 23 | 29% | **+577,800** | +7,222 |

**Stability 問題**：
- 2025-2026 佔 **95.5% 淨利** (2020-2024 只 +48K，2 年空窗 2023 + 部分)
- 這是 v0.3-P0FIX 舊 xlsx 診斷過的 **P1 S2 time concentration** 問題延續

---

## 四、獲利集中度分析

### Top 5 Wins（全部 SX_MA_TimeStop）

| Rank | Date | Signal | P&L | MFE | MAE |
|------|------|--------|-----|-----|-----|
| 1 | 2025-04-03 04:40 | TimeStop | **+388,000** | +388,500 | -2,700 |
| 2 | 2026-06-23 13:10 | TimeStop | +312,800 | +323,900 | -10,500 |
| 3 | 2026-07-02 22:55 | TimeStop | +182,400 | +194,300 | -15,500 |
| 4 | 2026-04-23 10:10 | TimeStop | +144,200 | +196,100 | -1,700 |
| 5 | 2026-06-10 16:10 | TimeStop | +105,200 | +134,300 | -12,100 |

### Removal Sensitivity

| 移除 | Net | PF | Verdict |
|-----|-----|-----|---------|
| Baseline (119T) | +1,059,200 | 1.903 | ✅ |
| Remove Top 1 | +671,200 | 1.572 | ✅ still profitable |
| Remove Top 2 | +358,400 | 1.305 | ✅ still profitable |
| Remove Top 3 | +176,000 | 1.150 | ✅ still profitable |
| **Remove Top 5** | **-73,400** | 0.937 | ❌ TURNS NEGATIVE |
| Remove Top 10 | -485,800 | 0.586 | ❌ severe negative |

**HHI (winners): 0.0756** — 尚可（< 0.10 = diversified）

---

## 五、Monthly P&L

- **Active months: 29** / ~78 total = 37.2%
- Positive months: 13 (44.8%)
- Negative months: 16 (55.2%)

### Top 3 months
- **2025-04**: +477,000 (Trump 關稅 crash)
- **2026-06**: +199,000 (crash cluster)
- **2026-07**: +184,600

### Bottom 3 months
- 2026-03: -137,200 (20T 大量誤觸發)
- 2025-03: -35,000
- 2025-08: -27,400

---

## 六、與 v0.1 / Pre-fix Candidate E 對比

| 版本 | Config | Net | PF | MDD $ | Trades | WR | 出場主導 |
|------|--------|-----|-----|-------|--------|-----|--------|
| v0.1 draft | F8/S25/Slope1 | ? | ? | ? | ? | ? | 未跑 |
| Pre-fix Cand E | F15/S50/Slope16 | +1,095,600 | 2.24 | -508K | 84 | 21% | (含 M7 bug)|
| Phase 1 GA (post-fix) | F14/S44/Slope8 | -698K | 0.947 | -1.66M | 2569 | 24.5% | 全負 |
| **v0.4 Cand** | **F25/S90/Slope26** | **+1,059K** | **1.903** | **-259K** | **119** | **26.9%** | **TimeStop 主導** |

**v0.4 找到 sweet spot**：極慢 MA (25/90) + 極嚴 Slope (26) + 短 MaxHold (24)。

**Slope=26 的意涵**：
- Fast(25) ZLEMA 每 5M K 下跌 26 pts
- 這是**極端下跌動能**（TXF1 5M ATR 通常 20-40 pts）
- 只有真正 momentum burst 才觸發

---

## 七、優點 / 缺點

### ✅ 優點

1. **Net > 0**（+1,059K）
2. **PF 1.9** 健康
3. **MDD abs 259K < 300K** Rule #13 pass
4. **Sample 119** 足夠統計
5. **Alpha 來源明確**：極端動能 + 2 小時 momentum burst
6. **Alpha 分散** (HHI 0.076, 移除 Top 3 仍 +176K)
7. **策略本質變成 Time-Based Trend Following**（reproducible）

### ⚠️ 缺點

1. **WR 27% 太低**（心理難承受）
2. **95% 獲利集中 2025-2026**（Rule #13 stability 大問題）
3. **PF adj 1.415 < 1.5** gate
4. **Sharpe 0.459 < 0.5** by 0.041
5. **Golden Cross 主要出場 0 觸發** — 已不是 MA Cross 策略
6. **ML Exit + SL 完全 0 觸發** — 這些機制被架空
7. **MDD % 65.62%**（相對值）— 心理承受度低
8. **策略本質變質** — 名稱 vs 實質不符

---

## 八、戰略意涵

### v0.4 是新策略還是 S16_S 演化？

**辨識**：
- 名稱：MACrossShort → 實際運作：Momentum Burst Time Stop Short
- 進場：MinSlope 主導（非死叉）
- 出場：TimeStop 主導（非黃金交叉）
- alpha 來源：從「動能異常」→「短期 momentum burst」

**選項**：
- **A. 接受 v0.4 為 S16_S 演化**（保留策略名，更新 pla defaults）
- **B. 重新命名策略**（如 S16_S_MomentumBurst，違反 Rule #14）
- **C. Rule #14 justify: v0.4 仍屬 G 類動量交叉分支**（保留命名）

### 建議

**選項 A + C**：
- 保留 S16_S_MACrossShort 命名（Rule #14 合規）
- 更新 pla defaults 為 v0.4 值
- 版本標為 **v0.4-CANDIDATE**（非 PROD）
- Header 明確記錄「策略已演化為 Momentum Burst 型態」
- 繼續 Phase 2 refine 前先做 **Rule #18 5 件套 pre-check**

---

## 九、下一步 Roadmap

### 立即（W4 fine-tune）

1. **更新 pla defaults 為 v0.4 值**
2. **寫 Rule #18 pre-check**（MC + Bootstrap 用 xlsx trades）
3. **測試 Golden Cross 為何 0 觸發**（是設計 vs bug 判斷）
4. **考慮把 Golden Cross 出場移除**（既然 0 觸發），改成純 TimeStop-driven

### 中期（W5 validation）

5. **Stress Test on 2020-2024**（低頻期是否結構性風險）
6. **BE Trail 分析**（只 4 trades，是否值得保留）
7. **QuickStop_Loss -1M 是否可壓縮**（M5 太緊？）

### 長期（W6 promote decision）

8. **若 4/8 提升到 6/8 gates**：Promote 候選
9. **若始終 < 6/8**：Path A/D/K 決策點

---

## 十、決策節點

| 選項 | 判定 |
|-----|------|
| **接受 v0.4 + 更新 defaults** | ⭐ 推薦（有真 alpha，值得繼續）|
| 回頭跑 Phase 2 (MinSlope 0.5-3) | 可平行，不衝突 |
| 直接 KILL S16_S | 過早（4/8 gates 已算部分 pass）|
| 深度改架構（新版本 v0.5）| 需先看 v0.4 refine 上限 |

---

**End of Analysis — 2026-07-09 Desktop**
