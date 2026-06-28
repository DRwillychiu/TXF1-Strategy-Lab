# S3_S VolSqueezeShort — Strategy Definition (v1.7.3-PROD)

**Promote 日**：2026-06-28
**版本**：v1.7.3-PROD（band-reject regime filter + Stage 1 GA best）
**狀態**：✅ PROMOTED to `live_simulation/`
**對應 .pla**：`strategies/live_simulation/S3_S_VolSqueezeShort.pla`
**R-6 配對**：S3_L VolSqueezeLong（long-side hedge pair）

---

## 一、策略本質（一句話 tagline）

> **「在對的 regime（強多 OR 任何空頭）中，吃 BBW squeeze 後剛出現的向下 expansion 起始段。」**

更白話：
> **「壓縮後第一刀下殺捕手，但只在強趨勢時出手。」**

---

## 二、用戶定義的 5 點本質（2026-06-28 對話確認）

### 1. 適合行情（3 種）
- **強勢多頭中的「驚嚇式回檔」**（cluster top 急殺）
- **快速崩跌的延續**（panic 後 follow-through）
- **順勢空方行情**（弱/強空頭中的延伸下殺）

### 2. 賺什麼錢
- 賺「**快速回檔的下殺錢**」
- 短時間、大震盪、單向下行
- 不貪長尾，鎖中短目標

### 3. 不做什麼盤
- **趨勢中性區段（Daily MA15/MA40 ratio 0.98-1.05）**
- 對應多數整理盤（不論震幅大小）
- Filter 判定依據是 **trend ratio**，不是震幅

### 4. 本質定調
- **MDD 低**（-23.1%）
- **WR 高**（80.6%）
- **PF 高**（gross 3.38 / adj 1.92）
- **精準出手打擊型**（4 trades/year, avg +30.7K）

### 5. 賺錢目標
| 維度 | 目標 | v1.7.3 實證 |
|------|------|------------|
| 頻率 | 3-5 trades/year | 4.1 trades/year ✅ |
| WR | > 75% | 80.6% ✅ |
| Avg trade | > +25K | +30.7K ✅ |
| Annual Net | +100K~+180K | +127K ✅ |
| PF gross | > 2.5 | 3.38 ✅ |
| Sortino | > 1.0 | 1.02 ✅ |
| MDD % | < -25% | -23.1% ✅ |

---

## 三、進場邏輯（8 個 gates 全 True → 次根市價放空）

1. 目前**空手**（MarketPosition = 0）
2. **BBW** 在過去 120 K 棒**最低 30% 百分位**（squeeze）
3. **收盤跌破 Bollinger 下軌**（向下爆發）
4. **非同日冷卻期**（前次平倉滿一日）
5. **非假日尾段**（63 筆登錄表，Time < 500）
6. **非結算日**（每月第 3 個週三 15-21 日）
7. **註冊有效期內**（Date ≤ 1270101）
8. **Regime 通過**：Daily MA15/MA40 ratio **> 1.05 或 < 0.98**（擋 0.98-1.05 中性區）

---

## 四、出場邏輯（6 層 priority 由高到低）

| Priority | 條件 | 動作 | Label |
|---|---|---|---|
| 1 | Manual Kill = True | 市價平倉 | SX_VS_Kill |
| 2 | 註冊期失效 | 市價平倉 | SX_VS_RegistryEnd |
| 3 | 假日尾段 + Time 415-455 | 市價平倉 | SX_VS_HolFlat |
| 4 | 結算日 + Time ≥ 1230 | 市價平倉 | SX_VS_Settlement |
| 5 | **TP**：到「進場價 − 3.5×ATR」 | Limit 鎖利 | SX_VS_TP |
| 6 | **Mid**：持倉≥2K 後收盤 > 中軌 | 市價認錯 | SX_VS_Mid |
| 7 | **TimeStop**：持倉 ≥ 35 K 棒 | 市價平倉 | SX_VS_TimeStop |
| 8a | **SP**（peak ≥ 1.5×ATR 後啟動）：止損動態移到「進場價 − peak × 70%」 | Stop 鎖 70% | SX_VS_SP |
| 8b | **SL**（SP 未啟動 fallback）：止損固定在「進場價 + 2.75×ATR」 | Stop 兜底 | SX_VS_SL |

---

## 五、Regime 5 區判定（filter 判斷依據）

| Zone | Ratio 範圍 | 屬性 | 進場？| PF 證據 |
|------|-----------|------|------|--------|
| Strong Bull | > 1.05 | 強多頭 | ✅ 進（突發回檔）| 4.49 |
| Weak Bull | 1.02 - 1.05 | 弱多頭 | ❌ **擋** | 1.61 marginal |
| Range | 0.98 - 1.02 | 整理盤 | ❌ **擋** | 0.73 (虧) |
| Weak Bear | 0.95 - 0.98 | 弱空頭 | ✅ 進（順勢）| 11.00 ⭐ |
| Strong Bear | < 0.95 | 強空頭 | ✅ 進（延續）| ~99 (1 trade) |

---

## 六、Portfolio sleeve 角色

### 不適合 S3_S 的 regime 由其他 sleeves cover

| Regime | S3_S | Portfolio cover |
|--------|------|---------------|
| Range (0.98-1.02) | ❌ 擋 | L3 ConsolidationLong（range mean revert） + S3_L Long Squeeze |
| Weak Bull (1.02-1.05) | ❌ 擋 | L1 TrendLong + S1 NightMomentum（multi-day long trend）|
| Strong Bull (>1.05) | ✅ 進 | L1 TrendLong 同 active（long 主力）|
| Weak Bear (0.95-0.98) | ✅ 進 | （L4 已退役，S3_S 獨擔）|
| Strong Bear (<0.95) | ✅ 進 | portfolio 整體 reduce exposure |

### Portfolio context 邏輯
- **S3_S = R-6 short hedge sleeve**（配 S3_L long）
- **不需 all-weather**，是 **regime-selective hedge**
- Range/Weak Bull 中 S3_S 休息，其他 sleeves 收割
- Strong Bull/Bear 中 S3_S 出手，S3_L 等其他 cover 反向

---

## 七、Final 定案參數（鎖定）

```pla
{ Bollinger Bands - v1.2 baseline (鎖定) }
BBLen                = 45
BBStd                = 2.0
BWLookback           = 120
BWPctile             = 30

{ ATR / Stop / Target - v1.2 baseline (鎖定) }
ATR_Len              = 14
StopATRMult          = 2.75
TargetATRMult        = 3.5

{ Exit timing - v1.2 baseline (鎖定) }
MaxBars              = 35
UseMidExit           = True
MidExit_MinBars      = 2

{ Layer 2 Trailing SP - v1.1 (鎖定) }
SP_Trigger_ATRMult   = 1.5
SP_Retain_Pct        = 70

{ Cooldown - v1.2 baseline (鎖定) }
Cooldown_Days        = 1

{ Regime Filter - v1.7.3-PROD Stage 1 GA best }
Use_Regime_Filter    = True
Regime_FastMA        = 15      *** GA best (v1.7.1 R1 was 20) ***
Regime_SlowMA        = 80      *** GA best (v1.7.1 R1 was 50) ***
Regime_BlockRange    = True    *** v1.7.3 NEW (band-reject 0.98-1.02) ***
Regime_BlockWeakBull = True    *** band-reject 1.02-1.05 ***

{ Compliance 模組 (鎖定) }
Holiday_Flat_Time    = 415
Registry_Valid_Until = 1270101
Manual_Kill_Switch   = False
Settlement_Flat_Time = 1230
```

---

## 八、驗證歷史（institutional accountability trail）

### v1.7.1 Round 1（baseline 候選）— 2026-06-27 評估
- Stage-2 8/8 gates PASS（Sharpe 0.55, MDD -19.4%, PF adj 1.42）
- W4 WFA 8/9 PASS（Median WFE +103.7%）
- W5 10-dim 9/10 PASS（Range FAIL）
- 樣本 140 / 8 年

### v1.7.3 band-reject（採用）— 2026-06-28 評估
- Stage 1 GA 60 組合 → best FastMA=15/SlowMA=80/BWPctile=30
- W4 WFA 2/9 isolated FAIL（但 portfolio sleeve context **不適用 single-strategy WFA standard**）
- 樣本 31 / 8 年（**by design 精選**，4 trades/year）
- 用戶 ruling 2026-06-28：「WFA 標準無法作為判斷依據，因為這份策略本身就是單一策略沒有任何 cover，可是在實戰上架策略來說，我卻有其他策略能夠 cover。再來交易次數極低是非常正確的事情，因為這支策略本身就是做該做的行情。」

### 為什麼選 v1.7.3 而非 v1.7.1

| 維度 | v1.7.1 R1 | **v1.7.3** | 用戶選 v1.7.3 理由 |
|------|----------|-----------|------------------|
| Net | +1.245M | +953K | -23% acceptable |
| Avg trade | +8.9K | **+30.7K** | **+245% precision 提升** |
| WR | 65% | **80.6%** | 高勝率支撐心理紀律 |
| Sortino | 0.46 | **1.02** | downside asymmetric 強 |
| PF gross | 1.82 | **3.38** | 高效鎖利 |
| Range trades | 65 (-259K loss) | **0 (excluded)** | 完全避免劣質 zone |
| 哲學一致性 | 全天候 | **精準打擊** | **符合用戶設計初心** |

---

## 九、Live caveats（必讀）

### Caveat 1: 4 trades/year 心理壓力極端
- 平均 3 個月才一筆
- 長等待期可能打破紀律（手癢加倉、提前出場）
- **Mitigation**：set up 月度提醒「沒進場 = 正確守則 」，不可手動干預策略

### Caveat 2: 2024 Tier S 大魚被擋走的事實
- 2024-08 BoJ +316K → v1.7.3 沒抓
- 2024-09 AI sell-off +104K → v1.7.3 沒抓
- 兩個 events 都在 weak_bull / weak_bear 邊界
- **接受 trade-off**：用「精選 + portfolio cover」彌補

### Caveat 3: L24 風險未完全消除
- BlockRange 是 hard-coded zone reject
- 未來 TWII 進入長期 range 可能 filter 失效
- **Monitor**：若 12 個月內 0 trades = manual review 必要

### Caveat 4: 統計顯著性弱
- 31 trades / 8 yr 樣本對 statistical inference 偏弱
- **Mitigation**：live_simulation 前 6 個月 paper trade，累積 ≥ 5 trades 後再考慮 live

---

## 十、Kill triggers（live 期間自動停用條件）

任一觸發即停用 + 寫 incident report：

1. **Monthly DD > 5% of account**（單月虧 > 5%）
2. **3 consecutive SL > -100K each within 30 days**（3 連 SL）
3. **12 個月內 0 trades**（filter dead → 需 review）
4. **Cluster losses > 3σ outside historical DD**（黑天鵝 outlier）

---

## 十一、Portfolio allocation

- **Portfolio cap**: **3% 帳戶**（vs S3_L 5% squeeze sleeve）
- **與 S3_L 合計**：squeeze sleeve = **8% portfolio**
- **每月 review**：若 actual exposure > target +1pp → manual rebalance

---

## 十二、相關文件

- `S3_S_VolSqueezeShort.pla` — production .pla v1.7.3-PROD
- `S3_S_VolSqueezeShort_DEPLOYMENT.md` — deployment caveat + kill triggers
- `../research/S03_VolSqueezeShort/v17_round1_evaluation_20260627.md` — v1.7.1 R1 完整評估
- `../research/S03_VolSqueezeShort/v17_round1_w4_wfa_20260627.md` — v1.7.1 R1 W4 WFA（8/9 PASS）
- `../research/S03_VolSqueezeShort/v17_round1_w5_institutional_20260627.md` — v1.7.1 R1 W5 10-dim
- `../research/S03_VolSqueezeShort/v173_w4_wfa_FAIL_verdict_20260628.md` — v1.7.3 isolated WFA verdict
- `docs/policies/STRATEGY_SUCCESS_CRITERIA.md` — institutional gates spec
- `docs/policies/lesson_L24_risk_overlay_alpha_preservation.md` — L24 lesson
- `docs/policies/OFFICIAL_ROADMAP.md` — S3_S 標 PROMOTED

---

## 十三、修訂歷史

| 日期 | 修訂 |
|------|------|
| 2026-06-28 | v1.7.3-PROD 鎖定 + promote to live_simulation |
| 2026-06-27 | v1.7.1 Round 1 評估完成（baseline 候選）|
| 2026-06-23 | v1.0 initial release（R-6 short mirror）|
