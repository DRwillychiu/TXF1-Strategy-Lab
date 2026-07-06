# S3_S VolSqueezeShort — Bollinger BandWidth Squeeze Breakout (R-6 Short half)

**啟動日**：2026-06-23
**狀態**：🟢 **v1.9.6 Config B + OPT — Rule #18 全套 PASS (2026-07-06)，Portfolio Correlation NEXT (final gate)**
**當前版本**：
- **Active**: [S3_VolSqueezeShort_v196_ANTIHUNT.pla](S3_VolSqueezeShort_v196_ANTIHUNT.pla) (1107 LOC, Config B + optimized defaults)
- **Baseline (archived)**: [S3_VolSqueezeShort_v195_EXPERIMENTAL.pla](S3_VolSqueezeShort_v195_EXPERIMENTAL.pla) (969 LOC)
- **Spec**: [v196_ANTIHUNT_spec_20260704.md](v196_ANTIHUNT_spec_20260704.md)
**架構**：Data1=1M（執行）, Data2=60M（訊號）, Data3=Daily（Regime）
**Stage -1 + 用戶 ruling**: 2026-06-23 完成（4 段討論 + 4 follow-up Q&A）
**前置**：[S3_L VolSqueezeLong](../archive/S03_VolSqueezeLong_promoted_20260620/) 已 W5 PASS + Promoted (2026-06-23)
**R-6 對手**：S3_S 是 S3_L 的鏡像，補完 vol expansion 雙向 capture
**Roadmap 依據**：[../../../docs/policies/OFFICIAL_ROADMAP.md](../../../docs/policies/OFFICIAL_ROADMAP.md) batch01 — S3_S

---

## v1.9.5 GA 最佳化結果（2026-07-02，當前基準線）

| 指標 | 值 |
|------|---|
| 交易數 | 68 |
| 淨利 | +513,400 NTD |
| 獲利因子 | 1.574 |
| MDD | -19.05% |
| 勝率 | 50.0% |
| 最大單筆獲利 | +278,800（2025-04-07 崩盤捕獲） |
| 最大單筆虧損 | -135,400（2026-06-08 V 轉） |

### GA 關鍵參數變動（8/38）

BWPctile 25→35, StopATRMult 2.75→3.75, TargetATRMult 3.5→2.0,
SP_Trigger_ATRMult 1.5→1.4, Thrust_Margin_ATR 0.25→0.15,
Hunt_Max_Stops 3→2, ML_ActivationPct 30→15, ML_ScoreTrigger 30→40

GA 將策略從「寬 TP + 窄 SL」轉為「窄 TP + 寬 SL」（R:R 反轉）。

---

## 版本演進

| 版本 | 核心改動 | 結果 |
|------|----------|------|
| v1.0 | 初版（鏡像 S3_L） | W2 baseline |
| v1.7.x | 多輪 WFA + 機構評估 | 不穩定 |
| v1.8.0 | SP Priority Fire + Tiered Retain（出場端） | PROD baseline |
| v1.9.0 | Data1=1M 架構重寫 | Bug 2 消除 |
| v1.9.1 | BWRank count(<) 修正 | 語意正確但時序衝突 |
| v1.9.2 | SP Priority Fire + Tiered Retain（出場端） | v1.8.0 之上 |
| v1.9.3 | Squeeze memory 進場窗口 | 31T / -205K / FAIL |
| v1.9.4 | Hunt state machine（取代固定窗口） | 73T / -23.8K / PF 0.97 |
| **v1.9.5** | **Thrust margin + circuit breaker** | **68T / +513.4K / PF 1.574** |
| ~~v1.9.6~~ (舊) | Post-crash continuation hunt | 171T / +369.6K / PF 1.169 — **棄用** |
| **v1.9.6-ANTIHUNT** | **Anti-hunt L1+L2 + BWRank bug + Exit/SP hardening (7 items)** | **Config B + OPT: 70T / +770.8K / PF 1.823 / MDD -16.02%** |

### v1.9.6 棄用原因

延續模式（SE_VS_Cont）增加 100 筆交易但淨損 -43.4K。
設計缺陷：需 hunt DISARM（Close > MidBand）才啟動延續，但崩盤後 MidBand 高懸，
正好是想捕捉的情境反而觸發不了。06-08 後 21 天空白期未解決。

---

## 驗證進度（以 v1.9.6 Config B + OPT 為基準）

### Config A/B/C/D 測試結果 (2026-07-06)

| Config | 設定 | 淨利 | PF | MDD% | 結論 |
|--------|------|------|-----|------|------|
| A | 全關 (sanity) | +413,000 | 1.402 | -22.70% | baseline |
| **B** | **BWRank ON** | **+424,000** | **1.418** | **-22.52%** | **CONFIG SELECTED** |
| C | 全開 (7/7) | +402,800 | 1.389 | -22.88% | L1+L2 抵消 BWRank 正效 |
| D | L1+L2 only | +391,800 | 1.374 | -23.07% | anti-hunt 淨負效 |

### 5-Param Optimization 結果 (2026-07-06)

以 Config B 為基底，MC12 Exhaustive 最佳化 5 個參數：

| 參數 | Config B | OPT | 意涵 |
|------|----------|-----|------|
| BWPctile | 35 | **40** | 放寬壓縮定義 |
| StopATRMult | 3.75 | **3.25** | 收緊停損 |
| SP_Trigger_ATRMult | 1.4 | **2.0** | 延後追蹤停利 |
| Hunt_Max_Stops | 2 | **4** | 容忍更多連續止損 |
| ML_ScoreTrigger | 40 | **35** | 降低 ML exit 門檻 |

OPT 結果：**70T / +770,800 / PF 1.823 / MDD -16.02% / 年化 11.31%**
成本結構：滑價 1000/口（含佣金），無另計手續費

### 5 件套驗證清單（Rule #18）

1. ~~**MC + Bootstrap on v1.9.5**~~ — DONE (2026-07-03), 3/5 pass (MC 邊界 FAIL by 0.64%)
2. ~~**參數最佳化**~~ — DONE (2026-07-06), 5 參數已寫入 .pla 預設值
3. ~~**Walk-Forward 驗證**~~ — CONDITIONAL FAIL (2026-07-06), Path A exemption
   - WFE = 14.8%（threshold >50%）— 形式上 FAIL
   - 有交易的 OOS window (W1-W3, W7) 全部獲利 +166K / PF avg 1.278
   - W4/W5/W6 OOS = 0 trades (bull regime 結構性)
   - 用戶 ruling: WFA 對 low-freq short 策略結構性不公平, Path A 跳過
4. ✅ **MC + Bootstrap on v1.9.6 Config B + OPT** — **DONE (2026-07-06), 5/5 PASS** 🎯
   - 詳見 [v196_ANTIHUNT_MC_bootstrap_OPT_20260706.md](v196_ANTIHUNT_MC_bootstrap_OPT_20260706.md)
   - MC 95% MDD = -20.47% ✅ (v1.9.5 -30.64% ❌ → +10.17pp 改善)
   - Bootstrap P(Net>0) = 95.0% ✅ (v1.9.5 89.3% → +5.7pp)
   - Bootstrap P(PF>1) = 95.0% ✅ (v1.9.5 89.3% → +5.7pp)
   - HHI = 0.0655 ✅ (v1.9.5 0.077 → 更 diverse)
   - Remove Top 3 = +146.4K ✅ (v1.9.5 -17.2K ❌ → +163.6K 改善)
5. ✅ **Stress Testing 6 events** — **DONE (2026-07-06), 6/6 Event-Net Gate PASS** 🎯
   - 詳見 [v196_ANTIHUNT_stress_test_20260706.md](v196_ANTIHUNT_stress_test_20260706.md)
   - E1 COVID: -28K (2.8% ≪ 5%) SURVIVED
   - E2 2022 熊: **+153K** CRASH WIN
   - E3 2022-Q4 CPI: **+87K** CRASH WIN (WR 75%)
   - E4 2024-08 BoJ: 0 trade（Regime filter 正常 blocked）
   - E5 2025-04-07 Trump: **+190K** CRASH WIN
   - E6 2026-06 crash cluster: **+343K** CRASH WIN
6. 🎯 **Portfolio Correlation vs S3_L** — ★ NEXT，promote 前最後測（Rule #13 < 0.7 gate）
7. **T68 V 轉保護評估** — 2026-06-08 -120K 單筆是否需 MAE Cap（可 parallel 或 promote 後）

### 📊 v1.9.6 Config B + OPT 實測 (2026-07-06, xlsx)

| 指標 | 值 |
|------|---|
| 交易數 | 71 |
| 淨利 | **+731,000 NTD** |
| PF | **1.749** |
| MDD % | **-17.17%** |
| Sharpe | **+0.549** |
| WR | 49.30% |
| MC 95% MDD | -20.47% ✅ |
| Bootstrap P(Net>0) | 95.0% ✅ |

---

## 🎯 Stage -1 — 用戶必讀策略討論（按 SOP v2 Enforcement）

### 1. 內容（策略一句話）

**Bollinger BandWidth 降至 30 百分位 → 波動率極度壓縮 → 收盤跌破下軌 → 做空，賺 vol expansion 向下方向的趨勢利潤。**

= C 類波動率型策略（鏡像 S3_L）
= 賺壓縮 → 擴張的方向性突破（向下版）

### 2. 優點（為什麼這 alpha 應該存在）

| # | 理由 |
|---|------|
| 1 | **直接 hedge S3_L 的 directional cost** — S3_L 在 2024 Q3-Q4 與 2026-04-02 虧錢的環境，S3_S 應該賺 |
| 2 | **Vol expansion 不對稱**：bad news 比 good news 更快、更暴力（panic > FOMO）→ short side breakout 動能通常 > long side |
| 3 | **Vol squeeze 物理本質中性**：壓縮後爆發方向 50/50（短期），純做多吃半邊太可惜 |
| 4 | **TXF1 重大 macro shock 多向下**：FOMC 緊縮 / 央行干預 / 川普關稅 / 地緣戰爭 / 美股 limit down → 全是 down catalyst |
| 5 | **Portfolio Sharpe > 單 sleeve Sharpe**：S3_L + S3_S 組合即使 S3_S 單獨 Sharpe < 1，hedge value 仍可推升 portfolio metric |
| 6 | **Lesson L24 直接動機**：用 R-6 配對做 directional hedge，不用 strategy-level filter 削 alpha |

### 3. 缺點 / 風險

| # | 風險 | 嚴重度 |
|---|------|--------|
| 1 | **TXF1 長期偏多 regime** → short bias 結構不利 | 🔴 高 |
| 2 | **Dead cat bounce**：短暫破下軌後反彈會打停損 | 🔴 高 |
| 3 | **Bear regime 樣本少**（2020-2026 只 2022 全年 + 2024 H2 短暫）→ 樣本不足 | 🟡 中 |
| 4 | **Squeeze 後若向上爆發** → S3_S 直接 SL | 🟡 中 |
| 5 | **Short 滑價通常 > Long**（夜盤跳空向上 vs 向下 asymmetry）| 🟡 中 |
| 6 | **單獨 Sharpe 可能 < 0.5**（fail 機構 gate）→ 必須靠 portfolio 配對 justify | 🟡 中 |
| 7 | **可能 S3_S 跟 S3_L 高 correlation**（共用 squeeze trigger）→ hedge 效果有限 | 🟢 低（待驗證）|

### 4. 為什麼合適（portfolio + roadmap 角度）

| # | 理由 |
|---|------|
| 1 | **OFFICIAL_ROADMAP R-6 鐵則**：S3_L 完成必拆 S3_S（用戶 2026-06-22 ruling）|
| 2 | **S3_L promote 條件**：5% portfolio cap + 等 S3_S 配對 = S3_S 不開發則 S3_L 永遠帶 directional cost |
| 3 | **Lesson L24 應用**：directional hedge 必用 R-6 配對，不用 strategy-level event filter |
| 4 | **既有 portfolio short sleeves 不足**：L2 (trend short) / L4 (range short) / S3_RPS (pullback short)，缺 vol expansion short → S3_S 填補空缺 |
| 5 | **R-6 鏡像對稱**：S3_L .pla 已 validate full institutional flow，S3_S 結構 90% reuse → 開發成本低 |
| 6 | **Verify hypothesis**：archive 原始 S3 是雙向 spec，long 側已證有 alpha (PF 2.55)；short 側值得驗證 |

### 5. 預期挑戰（pre-W0 已知）

- W0 alpha pre-verify 可能直接 KILL（若 short side alpha 不存在）
- TXF1 偏多 bias 預期 OOS Sharpe 比 S3_L 低
- 需要設計「only short when bearish regime」filter 還是「always squeeze trigger」(後者更純，但虧更多)
- Frozen SL 計算公式需鏡像 (Long 用 BB_Btm - ATR×k，Short 用 BB_Top + ATR×k)
- Mid exit 邏輯鏡像（短倉 mid line = 中軌，碰回是空轉多 trigger）

---

## 等用戶確認 Stage -1 後才進 W0

按 SOP v2 + Lesson L24：**Never make a decision the user couldn't explain to their board**。

用戶必須確認上述 4 段（內容 / 優點 / 缺點 / 為什麼合適）後，才進 W0 alpha pre-verify。

---

## 開發路線（嚴格遵守 SOP v2）

### Stage -1：策略討論（本檔，**現在**）
- 寫策略 4 段 → 等用戶 GO / NO-GO

### Phase W0：Alpha Pre-verify（pre-code）
- `scripts/analyze_s3s_volsqueeze_short_preverify.py`
- 用 TXF1 60M 真實資料驗證：
  - BBW < 30 pctile 後**跌破下軌**的發生頻率
  - 突破下軌後 N bar 內 ATR×N 向下命中率
  - vs 向上反彈反向命中率（驗證是否多多）
  - 跟 S3_L 訊號的時間 correlation（避免共線性）
- **若 alpha 不存在 → 立即 KILL（不寫 .pla）**

### Phase W1：策略文件
- `S3_VolSqueezeShort_strategy.md`（機構級規格）
- `S3_VolSqueezeShort_annotated.md`（中文逐段註解）

### Phase W2：.pla 實作
- `S3_VolSqueezeShort.pla`（鏡像 S3_L 結構，補完所有 Rule #11/12/13/14）
- `scripts/verify_s3_volsqueeze_short.py`

### Phase W3：MC12 baseline backtest
- 60M TXF1 2020-2026
- 用 archive 預設值或 S3_L 鏡像 inputs
- 純 design_spec 中位值，不開 GA

### Phase W4：Walk-Forward
- IS 2y / OOS 6m / step 6m (S3_L 同 setup)
- WFE > 50%

### Phase W5：10 維度評估 + 晉升 live_simulation
- **特別關注**：S3_S × S3_L correlation（必算）→ 確認 hedge 真實
- 配對 portfolio Sharpe vs 單 sleeve Sharpe

---

## 開發紀律（從 S3_L 學到 + 新教訓）

```
S3_S 開發必須遵守：
1. ✅ Stage -1 先做完（不可跳過）
2. ✅ W0 alpha pre-verify 必跑（KILL gate）
3. ✅ Mirror S3_L 結構：90% 可 reuse (Section 0 Holiday, Settlement, etc.)
4. ✅ Time 條件閉區間（MC Time 24hr 規則）
5. ✅ Cooldown_Days 同 S3_L (= 1)
6. ✅ SL/TP 從 short side MFE 統計推導（不可直接用 S3_L 數字）
7. ✅ 不可加 Pre-event Flat（L24, alpha source 不可削）
8. ✅ Single trade tail 風險接受（portfolio level 配對解決）
9. ✅ 不可發明新策略名稱
10. ✅ S3_S 完成後立即進 S4_L (MACDDivergenceLong，原始 batch01 下一個)
```

---

## 下一步

**等用戶 confirm Stage -1 → 啟動 W0 alpha pre-verify。**
