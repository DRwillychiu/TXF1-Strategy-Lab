# S16_S MACrossShort — Strategy Definition (W1)

**啟動日**：2026-06-28（用戶 override Rule R-1 加入 roadmap）
**版本**：v0.1-DRAFT（W1 spec，待 W2 .pla 實作）
**狀態**：🔵 CURRENT — W0 STRONG PASS (2026-07-08)，進 W2 code
**類別**：G 類動量交叉（純空）
**時框**：Data1 = 5M（訊號 + 執行）
**指標**：ZLEMA（Zero Lag EMA）
**Alpha 來源**：動能異常（Momentum Anomaly，學術支撐 Jegadeesh & Titman 1993）
**R-6 配對**：S16_L MACrossLong（W2 未開始，S16_S 完成後）

---

## 一、策略本質（一句話 tagline）

> **「用零延遲雙均線抓 5 分鐘級別短期動能轉空的起始點，讓利潤在趨勢中奔跑。」**

更白話：
> **「短期動能剛翻空就跟進，趨勢延續就抱、翻轉就撤，洗盤就快速止損。」**

---

## 二、用戶定義的 5 點本質（2026-07-07 / 07-08 對話確認）

### 1. 適合行情（3 種）
- **短期急速下殺開端**（動能突然翻空的爆點）
- **中短期趨勢延續下行**（下跌動能未耗盡）
- **波段中間的整理後續跌**（Fast MA 反彈遇 Slow MA 壓回再下）

### 2. 賺什麼錢
- 賺「**中短期動能下行趨勢**」的順勢空頭錢
- 5M 級別短週期，一趟持倉 30-60 分鐘為主（M8 上限 4 小時）
- 不預測、不逆勢，讓利潤在 Golden Cross 前自然奔跑

### 3. 不做什麼盤
- **絕對不做多**（Rule R-6 純空 sleeve）
- **不加 Regime Filter**（用戶 2026-07-08 ruling A：不因多頭年迴避，接受 whipsaw，靠 exit 端控管）
- **不設固定 TP**（feedback_trend_let_profits_run，讓 Golden Cross 自然出場）

### 4. 本質定調
- **每筆虧損嚴格可控**（M5 Quick Stop 上限 15 pts = 3,000 NTD）
- **多層出場防護**（P0 合規 → P1 Quick → P2 Rule#17 多層 → P3 BE Trail → P4 Golden Cross → P5 Time → P6 SL）
- **規則透明** — 3 秒能對老闆解釋（僅 5 個 entry gate）
- **短線爆點捕手 + 嚴格控管虧損型**

### 5. 賺錢目標

| 維度 | 目標（中性情境）| W0 daily proxy 實測（Fast=12/Slow=30/Fwd=3）|
|------|--------------|------------------------------------------|
| 頻率 | 50-80 trades/year | 11.6/年（daily 較稀）|
| WR | 30-45% | **45.8%** ✅ |
| Avg trade | +0.5 ~ +1.5 pts | +0.07% per trade |
| PF | 1.0-1.5 | **1.29 RR** ✅ |
| Annual Net | +30K~+80K | 待 W3 MC12 5M 驗證 |
| MDD | < -20% | 待 W3-W5 驗證 |
| Sharpe | > 0.4 | 待 W3-W5 驗證 |
| Stability | ≥ 40% 年份正 | **57.1%** ✅ |

---

## 三、核心設計哲學

> **「進場簡單，出場嚴格控管」**
> **「進場門戶大開，出場刀鋒銳利」**
> **「Whipsaw 可接受 — 只要每筆虧損嚴格控管」**

### 為何選 ZLEMA？

一般 EMA(20) 在 5M K 上延遲 **47 分鐘**（9.5 K × 5 min）才反應趨勢轉折，對短線策略 **致命**。ZLEMA（Zero Lag EMA）用價格預補償公式 `deLagged = 2*Price - Price[lag]`，將延遲壓到 **≈ 0-10 分鐘**。

**代價**：ZLEMA 跟得更緊 → 更容易被雜訊觸發 → whipsaw 更頻繁 → 靠 Layer 2 exit 端嚴格控管。

### 動能異常（Momentum Anomaly）— alpha 學術根基

- Jegadeesh & Titman (1993)：3-12 個月動能在股票上顯著
- Moskowitz, Ooi, Pedersen (2012)：時間序列動能在 58 個期貨市場上顯著
- Asness, Moskowitz, Pedersen (2013)：動能在全球股/債/匯/商品都存在

**S16_S = 動能效應機械化 5M 版本**。Fast ZLEMA < Slow ZLEMA = 短期動能 < 中期 = 空頭方向確認。

---

## 四、進場規格（Layer 1，5 個 gate）

```pla
Entry Signal:
  ZLEMA_Fast(8) crosses BELOW ZLEMA_Slow(25) at Data1 (5M) close
  AND AbsValue(ZLEMA_Slow - ZLEMA_Slow[1]) > MinSlope(1.0)   // M1 斜率過濾
  AND v_Settlement_Day     = False                            // Rule #11
  AND v_Holiday_Block      = False                            // Rule #11
  AND v_Registry_Expired   = False                            // Rule #11
  AND Manual_Kill_Switch   = False                            // Rule #11 P0

Order:
  sell short next bar at market
```

### Layer 1 機制決策（2026-07-07 lock）

| 機制 | 決策 | 理由 |
|------|------|------|
| M1 Slope confirmation | ✅ KEEP | 過濾盤整噪音 |
| M2 N-bar delay | ❌ DROP | 5M 承擔不起延遲 |
| M3 ATR threshold | ❌ DROP from entry | ATR 屬出場範疇 |
| M4 Volume confirmation | ❌ DROP | 會擋夜盤 |

**設計哲學**：進場門戶大開，不加多餘 filter。

---

## 五、出場規格（Layer 2，8 層 priority chain）

```
P0: Kill / Registry / Holiday / Settlement    (Rule #11/#12 硬性合規)
P1: M5 Quick Stop                              (短線洗盤第一刀)
P2: M6 Rule #17 多層 1M 監控                   (極端行情商辦大樓)
P3: M7 Breakeven Trailing                      (進 profit 後保護)
P4: Golden Cross                               (主要出場)
P5: M8 Time Stop                               (最大持倉 4 小時)
P6: ATR-based Frozen SL                        (最後防線)
P7: SetStopLoss engine guard                   (Rule #12 backup)

NO TP - trend running per feedback_trend_let_profits_run
```

### 4 個核心 Layer 2 機制摘要

| 機制 | 觸發 | 目的 |
|------|------|------|
| **M5 Quick Stop** | 6 K 沒賺錢 OR loss > 15 pts | 立即認錯，防洗盤累損 |
| **M6 Rule #17 多層** | 積分 ≥ 65% + 跨類別 ≥ 3 | 極端反轉提早撤退（借用 S3_S）|
| **M7 Breakeven Trail** | Profit ≥ 1.0 / 1.5 ATR | 保護已賺獲利不倒退 |
| **M8 Time Stop** | Bars ≥ 48 (4 小時) | 動能耗盡或跨風險時段 |

**完整 Layer 2 code 骨架** 詳見 [`S16_S_entry_exit_spec_20260708.md`](S16_S_entry_exit_spec_20260708.md)

---

## 六、Regime Filter 決策 — 2026-07-08 LOCK 選項 A

**不加 Regime Filter**。

### 5 個支撐理由
1. **Lesson L24 精神** — 不為救 alpha 疊 sub-filter
2. **哲學一致性** — 進場門戶大開，filter 屬進場端加碼
3. **可解釋性最大化** — 3 秒可解釋 vs 加 filter 需 2 分鐘
4. **Layer 2 已足夠** — M5+M6+M7 提供 4 層 whipsaw 防護
5. **信任 exit rigor** — 用戶明確 ruling「洗盤只做嚴格控管虧損」

### 接受的 trade-off
- ⚠️ 多頭年（如 2024）預期較多 whipsaw
- ✅ 每筆虧損可預期（≤ 15 pts by M5）、可控管
- 上線後**紅燈監控指標**：
  - 連 3 個月 PF < 0.8 → review
  - 累計 MDD > 25% → 立即檢討
  - 多頭年單月 whipsaw > 20 次 → 考慮重評選項 B

---

## 七、W0 Alpha Pre-Verify 證據（2026-07-08）

**方法**：TWII daily proxy 2020-2026（1558 bars, 6.2 年）
**Verdict**：🎯 **STRONG PASS — 40/216 combos 4/4 gates PASS**

### Best combo (Fast=12, Slow=30, Fwd_N=3)

| Gate | 標準 | 實際 | 結果 |
|------|------|------|------|
| G1 Trigger 頻率 | ≥ 3/年 | 11.6/年 | ✅ |
| G2 Forward hit rate | ≥ 40% | 45.8% | ✅ |
| G3 Risk-reward ratio | ≥ 1.0 | 1.29 | ✅ |
| G4 Cross-year stability | ≥ 40% | 57.1% | ✅ |

### 5M 對應推算
Daily best (12/30) → 5M 對應 **Fast=8, Slow=25**（已寫入 spec 為 default）

### 年度分解（Best 12/30 daily proxy）
| Year | N | Total Ret % | 評估 |
|-----:|---:|-----------:|------|
| 2020 | 12 | -3.55% | ❌ COVID 復甦強牛 |
| 2021 | 11 | +1.58% | 🟡 略正 |
| 2022 | 11 | +0.49% | 🟡 熊年勉強持平 |
| 2023 | 11 | -4.01% | ❌ 復甦牛 |
| 2024 | 11 | **+13.20%** | 🏆 意外最好 |
| 2025 | 13 | -8.34% | ❌ AI 主升段 |
| 2026 | 3 | +5.89% | ✅ 上半年 |

**4/7 年正報酬** → stability 57.1% ≥ 40% gate。

### Caveats（W3 必復驗）
- Daily proxy 是**必要非充分**條件
- Whipsaw pattern 不同（daily 週級別 vs 5M intraday）
- 5M microstructure（夜盤/開盤/結算日）daily 未 model
- 滑價未 model，edge 會縮 10-20%
- **W3 MC12 backtest 真實 5M 資料 = 最終驗證**

詳見 [`W0_alpha_preverify_result_20260708.md`](W0_alpha_preverify_result_20260708.md)

---

## 八、完整參數清單（W2 .pla 直接對照）

### Group A — Entry (ZLEMA)
| Input | Default | Range | 說明 |
|-------|---------|-------|------|
| ZLEMA_Fast | **8** | 3-15 | 5M 對應 daily 12 |
| ZLEMA_Slow | **25** | 15-50 | 5M 對應 daily 30 |
| MinSlope | 1.0 | 0.5-2.0 | Slow ZLEMA 斜率過濾 |

### Group B — M5 Quick Stop
| Input | Default | Range |
|-------|---------|-------|
| QuickStop_On | True | T/F |
| QuickStop_MaxBars | 6 | 3-10 |
| QuickStop_MaxLoss_Pts | 15 | 10-25 |

### Group C — M6 Rule #17 Multi-Layer
| Input | Default | Range |
|-------|---------|-------|
| ML_On | True | T/F |
| ML_ActivationPct | 20 | 10-25 |
| ML_ScoreTrigger | 65 | 50-70 |
| ML_MinCategories | 3 | 2-4 |

### Group D — M7 Breakeven Trail
| Input | Default | Range |
|-------|---------|-------|
| BE_On | True | T/F |
| BE_Trigger_ATR | 1.0 | 0.5-2.0 |
| BE_Buffer_Pts | 5 | 0-15 |
| BE_Tier2_ATR | 1.5 | 1.5-2.5 |
| BE_Tier2_Buffer_Pts | 10 | 5-20 |

### Group E — M8 Time Stop
| Input | Default | Range |
|-------|---------|-------|
| M8_On | True | T/F |
| MaxHoldingBars | 48 | 24-96 |

### Group F — ATR SL (Frozen)
| Input | Default | Range |
|-------|---------|-------|
| ATR_Len | 14 | 10-20 |
| StopATRMult | 2.0 | 1.5-3.0 |

### Group H — Rule #11 合規
| Input | Default |
|-------|---------|
| Holiday_Flat_Time | 415 |
| Registry_Valid_Until | 1280101 |
| Manual_Kill_Switch | False |
| Settlement_Flat_Time | 1230 |

---

## 九、標籤規範（Rule #14/16）

### Prefix
- **SE_MA_** = Short Entry (MA cross)
- **SX_MA_** = Short Exit (MA cross)

### 完整 signal 名稱
| Signal | 用途 |
|--------|------|
| SE_MA_DeathCross | 進場 |
| SX_MA_GoldenCross | 主要出場（P4）|
| SX_MA_QuickStop_Time | M5 時間止損 |
| SX_MA_QuickStop_Loss | M5 損失止損 |
| SX_MA_ML_Exit | M6 Multi-Layer 出場 |
| SX_MA_BE_Trail1 | M7 breakeven tier 1 |
| SX_MA_BE_Trail2 | M7 breakeven tier 2 |
| SX_MA_TimeStop | M8 最大持倉 |
| SX_MA_SL | Frozen SL |
| SX_MA_Kill | Manual kill |
| SX_MA_Registry | Registry 過期 |
| SX_MA_Holiday | 假日平倉 |
| SX_MA_Settlement | 結算日平倉 |

---

## 十、Portfolio 定位

### 與現有 sleeve 對比

| 策略 | 時框 | Trigger | 出場 | Alpha |
|------|------|---------|------|-------|
| L2 TrendShort | Daily | Donchian | ATR trail | 中長線趨勢 |
| L4 ConsolidationShort | 60M | Range 假破 | ATR stop | 盤整突破 |
| S3 RapidPullbackShort | 60M | 拉回狙擊 | Reversal | 反彈失敗 |
| S3_S VolSqueezeShort | 60M | BB 壓縮突破 | TP/SP/1M | 波動率爆發 |
| **S16_S MACrossShort** | **5M** | **ZLEMA 死叉** | **黃金交叉** | **中短期動能** ⭐ **portfolio 唯一** |

### 預期 correlation
- vs S3_S：**低**（不同 trigger + 不同時框 + 不同 alpha 來源）
- vs L2/L4/S3：**低**（週期 + 邏輯完全不同）
- **Portfolio 增值角色**：純動能 alpha 補位

### 建議部署 cap
- **初始 3%**（新策略保守）
- 模擬 30 筆 + PF ≥ 1.2 後可考慮升 5%

---

## 十一、Rule #14 合規 checklist

- ✅ Rule R-1 順序（依 explicit override 加入 S16_S）
- ✅ Rule R-6 純空拆分（S16_L 待 S16_S 完成後）
- ✅ 未發明策略名稱（S16 已寫入 OFFICIAL_ROADMAP）
- ✅ 未跳號（S4_L+S4_S 已 KILL）
- ✅ 未平行開發（S16_L 排隊）
- ✅ 每隻 W0 alpha pre-verify 已跑（STRONG PASS）

## 十二、Rule #16 五支柱 checklist

- **Rules**：對齊 #11/#12/#13/#14/#15/#17/#18
- **Context**：spec + MA_deep_research + W0 result 三份文件完整
- **Verification**：W0 40/216 4/4 gates PASS；W2 ASCII 待驗；W3 MC12 待跑
- **Memory**：對齊 `feedback_trend_let_profits_run` / `feedback_holiday_flatten_rule` / `feedback_mc_time_24hr_pitfall` / `feedback_mc_entry_exit_labels`
- **Format**：strategy.md（本檔）+ spec + W0 result + 未來 annotated.md

---

## 十三、下一步 Roadmap

1. ✅ Stage -1 策略討論
2. ✅ Layer 1 進場設計 lock（2026-07-07）
3. ✅ Layer 2 出場設計 lock（2026-07-08）
4. ✅ Layer 3 Regime Filter 用戶 ruling 選項 A（2026-07-08）
5. ✅ W0 Alpha Pre-Verify STRONG PASS（2026-07-08）
6. ✅ **W1 策略正式文件（本檔）**
7. ⏳ **W2 .pla 實作**（含 P0-P7 完整出場鏈 + ASCII verify）
8. ⏳ W3 MC12 baseline backtest（真實 5M 資料）
9. ⏳ W4 GA Phase 2 optimization
10. ⏳ W5 Rule #18 Non-WFA 5 件套（MC + Bootstrap + Stress + Sensitivity）
11. ⏳ W6 Promote 決策（→ live_simulation OR KILL）

---

## 十四、Files

- Strategy definition: `S16_S_strategy.md`（本檔）
- Entry+Exit spec: `S16_S_entry_exit_spec_20260708.md`
- W0 result: `W0_alpha_preverify_result_20260708.md`
- W0 script: `_w0_alpha_preverify.py`
- MA deep research: `MA_deep_research_20260707.md`
- Handoffs: `HANDOFF_20260706_desktop_to_laptop.md`, `HANDOFF_20260707_laptop_to_desktop.md`

---

**End of Strategy Definition — 2026-07-08 Desktop**
