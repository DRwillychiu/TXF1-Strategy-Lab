# S3 RapidPullbackShort v2.0 — Alpha Thesis (60M Regime Edition)

- **Date**: 2026-06-20
- **Author**: Strategy Lab (User Option B — preserve thesis, shorten regime time-frame)
- **Document type**: Alpha thesis（策略本體論述）
- **Version relationship**: v1.1 thesis 完整保留；僅 **regime time-frame** 從 Daily 縮短至 60M
- **Companion docs**:
  - v1.1 完整論述：[S3_RapidPullbackShort_strategy.md](S3_RapidPullbackShort_strategy.md) ★ thesis 細節仍以此為主
  - v1.1 設計規格：[S3_PullbackShort_design_spec_v2.md](S3_PullbackShort_design_spec_v2.md)
  - v2.0 程式碼：[S3_RapidPullbackShort_v2.pla](S3_RapidPullbackShort_v2.pla)
  - v2.0 參數範圍：[S3_v2_optimization_ranges.md](S3_v2_optimization_ranges.md)
  - v2.0 結構驗證：[scripts/verify_s3_v2.py](../../../scripts/verify_s3_v2.py)（94/94 PASS）
  - 策略 R&D SOP：[docs/STRATEGY_RD_SOP.md](../../../docs/STRATEGY_RD_SOP.md)
- **Constitution compliance**: Rule #11 / #12 / #13 — 全數 inherited from v1.1

---

## 1. Strategy Identity

| 欄位 | v1.1 | **v2.0** |
|------|------|----------|
| **Code name** | `S3_RapidPullbackShort` | `S3_RapidPullbackShort_v2` |
| **MC Load name** | `STRATEGY_GEN_RapidPullbackShort` | `STRATEGY_GEN_S3_RapidPullbackShort_v2` |
| **Label prefix** | `SE/SX_RPS_*` | `SE/SX_RPS_v2_*` |
| **One-line essence** | 強多頭過熱（Daily） + 5M 動能轉空 → 短線做空 | **強多頭過熱（60M）** + 5M 動能轉空 → 短線做空 |
| **Direction** | Short-only | Short-only |
| **Strategy class** | Counter-trend mean-reversion w/ momentum confirmation | **同 v1.1** |
| **Execution TF** | Data1=5M, Data2=60M (reserved), Data3=Daily | **Data1=5M, Data2=60M (active regime)** |
| **Holding horizon** | 30 min - 2 hr (120 min hard cap) | **30 min - 90 min (18 bar hard cap)** |
| **Position** | 1 口 | 1 口 |
| **Sessions** | 日盤 only (08:50-13:25) | **日盤 only (08:50-13:25)**（夜盤 v2.1 加入） |

**v2.0 本質定位**：v1.1 thesis 100% preserved。Daily regime gate 因觸發過稀（3.4/yr）導致全策略觸發 9/yr、PF 含滑價 -0.92。v2.0 將 regime time-frame 縮短至 60M（同一個 thesis、更短的觀察窗），預期觸發次數 25-50/yr，PF 含滑價 > 1.0。

---

## 2. Alpha Thesis — Why This Still Works on 60M

### 2.1 v1.1 thesis 完整保留

v1.1 §2 完整論述適用 v2.0：
- **獲利了結節奏**（profit-taking rhythm）
- **散戶 FOMO 高峰**（retail capitulation buying peak）
- **日內 momentum exhaustion**
- **學術支持**：filter-confirmed mean reversion >> pure contrarian

詳見 [v1.1 strategy.md §2](S3_RapidPullbackShort_strategy.md)。

### 2.2 為什麼 60M 不破壞 thesis

v1.1 用 Daily 是因為「過熱」這個概念**通常**用 daily-scale 框架（教科書 RSI > 70 = daily），但其實「過熱」是**一個價格距離與動能的相對概念**，可在任意時間框架下定義：

| TF | 過熱定義 | 觸發頻率 |
|----|---------|---------|
| Daily | 收盤距 MA20 > +3% AND RSI(14)>70 sustained 2 days | **3.4 events/yr**（過稀） |
| **60M** | **60M 收盤距 MA20 > +1.5% AND RSI(14)>65 sustained 2 hours** | **30-60 events/yr 預估** |
| 15M | 15M 距 MA20 > +0.8% AND RSI > 60 | 過於敏感（每日多次） |

60M 是「過熱」這個概念在 intraday context 仍可被穩定識別的時間框架。15M 以下噪音太多，Daily 以上樣本太少。

**關鍵**：v2.0 仍保留 **「Tier 1 filter, Tier 2 trigger」** 兩層 gate 架構。60M 過熱定義 = Tier 1（背景條件，非進場訊號）；5M 4-AND momentum = Tier 2（進場訊號）。架構與 v1.1 同形。

### 2.3 為什麼不直接 redesign

「Path C 強勢日內反轉」與「Path D 波動率爆發捕捉」(v2.0 LOCKED draft) 已驗證 Daily-level alpha 為負（Path C 強勢日隔日 mean drop 0.53% vs mean rise 0.95%，drop > rise 僅 42%）。詳見對話歷史 `_temp_sc6_path_c_frequency.py` 輸出。

「強勢日易反轉」在 TXF1 並非穩定 alpha；強勢日傾向**動能延續**。原 S3 thesis（過熱多頭中的回檔做空）才是 TXF1 的真實 edge — 但需要「過熱」這個 filter 將「強勢但仍在延續」與「強勢且即將回檔」區隔開來。

v1.1 用 Daily 過熱定義對了 thesis 但用錯了 cadence，導致 backtests 因樣本量不足無法生效。v2.0 修正 cadence。

---

## 3. v2.0 Design — Diffs from v1.1

### 3.1 Tier 1 Regime Gate（v2.0 主要變動）

| 維度 | v1.1 Daily (Data3) | **v2.0 60M (Data2)** |
|------|---------------------|----------------------|
| 結構 | A AND (B OR C) | **A AND (B OR C)**（不變） |
| A: trend | Daily MA20 > MA60 | **60M MA20 > MA60**（20hr 趨勢 > 60hr 趨勢） |
| B: RSI threshold | Daily RSI(14) > 70 sustained 2 days | **60M RSI(14) > 65 sustained 2 hours**（門檻鬆綁，cadence 縮短）|
| C: dist MA20 | Daily 距 MA20 > +3% | **60M 距 MA20 > +1.5%**（60M 距離自然較小）|
| RSI snapshot | Daily new-bar 邊界 shift | **Hour new-bar 邊界 shift** |
| 觸發頻率 (預估) | ~3.4/yr | **30-60/yr** |

**RSI snapshot 細節**：v1.1 用 Daily-bar 邊界 shift 解決「5M 級別 RSI[hidx] 不是 Daily offset」的 stale 問題。v2.0 採同一機制但 cadence 改為 hour-boundary：`Hour(Time) <> v_LastSeenHour` 觸發 shift。同樣原理、更快 cadence、不需要 Data3。

### 3.2 Tier 2 Momentum Trigger（**保留 v1.1**）

5M 4-AND 條件 (M1-M4) 完全 unchanged：

| Condition | Default | 是否變動 |
|-----------|---------|----------|
| M1: Consec_Red_Bars | 3 | 不變 |
| M2: Close < EMA5 AND EMA falling | EMA_Fast_Len=5 | 不變 |
| M3: ATR(5) > ATR(20) × 1.3 | ATR_Spike_Mult=1.3 | 不變 |
| M4: 距 intraday high 在 [0.3%, 1.5%] | **Pullback_Min_Pct: 0.5 → 0.3** | 鬆綁 |

**為什麼 M4 鬆綁**：v1.1 0.5% 下限對應 Daily-scale 進場時機（一天可能只有少數機會）；v2.0 60M scale 下，0.3% 起步更符合 intraday 即時觸發。

### 3.3 Exit Tier（v2.0 整體收緊 + v2.1 加 trailing layer）

| 出場 | v1.1 | **v2.0** | **v2.1** | 理由 |
|------|------|----------|----------|------|
| TP_Pct | 0.7% | **0.6%** | 0.6% | 90 min hold cap 內 0.7% 較難達成 |
| SL_ATR_Mult (Engine + initial Frozen SL) | × 4 (~0.58%) | **× 3 (~0.44%)** | × 3（**不變**，初始 max-loss cap）| Engine SL 不 trail，用戶 mandate |
| Max_Bars_TimeStop | 24 bar (120 min) | **18 bar (90 min)** | 18 bar | 縮短「猶豫部位」拖延時間 |
| EMA20 backup TP | 有 | 有（同 v1.1 fix #1）| 有 | TP_EMA20_MinBars=3 guard 保留 |
| Frozen SL backup S-3 | 固定 | 固定（同 v1.1 fix #10）| **可被 trail 縮緊** ⭐ | v2.1 透過 v_SL_Level update |
| **Trailing SL (Section 5c)** | — | — | **NEW** ⭐ | 浮盈 ≥ 0.5% 後啟動，每根 K trail 至 MIN(SL, Close + ATR×2) |
| Same-day cooldown | 有 | 有 | 有 | 不變 |

**R:R 計算**：v1.1 0.7/0.58 = 1.21 → v2.0 0.6/0.44 = 1.36（略提升）→ v2.1 動態 R:R（trailing 鎖盈後，effective SL 距離縮小，R:R 視 trail trigger 後距離而定）

### 3.3.1 v2.1 ATR Trailing 詳解

**目的**：解決 v2.0.1 baseline backtest 揭示的「賺後回吐 → 倒虧 / SL 出場」風險。

**機制**：
- 浮盈 = `(EntryPrice - Close) / EntryPrice × 100`（short 變體）
- 啟動：浮盈 ≥ `TrailingActivate_Pct` (default 0.5%)
- Trail：每根 5M K 把 `v_SL_Level` 縮緊到 `MIN(current_SL, Close + ATR(14) × TrailingATR_Mult)`
- **單向**：只縮緊不放鬆（即使 Close 反彈，v_SL_Level 不會回頭擴大）
- **Engine SL 不動**：Section 5b 的 SetStopLoss 仍是 entry-bar ATR × 3 = max loss cap
- **Trailing 透過 Section 7 S-3 BuyToCover at Stop** 執行

**實例（entry @ 17,500，ATR=20pt，Trail=0.5%, Mult=2）**：

| 時點 | Close | 浮盈% | 動作 | v_SL_Level |
|------|-------|------|------|-----------|
| Entry | 17,500 | 0% | initial Frozen lock | 17,560 (entry + 3×20) |
| K+2 | 17,410 | 0.51% ★ | **觸發 trail**：Cand = 17,454 | **17,454** |
| K+3 | 17,400 | 0.57% | trail 縮緊 | **17,444** |
| K+4 | 17,420（反彈）| 0.46% | Cand 17,464 > current → **不放鬆** | **17,444** |
| K+6 | 17,448（觸停）| — | **觸停 → 出場 @ 17,444** | exit lock 56pt 獲利 |

### 3.4 Entry Window（v2.0 拓寬）

| Input | v1.1 | **v2.0** |
|-------|------|----------|
| Entry_Open_Time | 850 (08:50) | 850 |
| Entry_Cutoff_Time | **1230** | **1325** |
| Daily_Flat_Time | 1325 | 1325 |

**為什麼拓寬**：v1.1 1230 cutoff 是基於 D5 「wider」決策；v2.0 更積極使用 13:25 之前所有 5M bar。13:25-13:25 之間有 5 個 5M bar 仍可進場（直到 force flat 觸發前）。

### 3.5 Sessions 處理（v2.0 仍為 day-only）

v2.0 LOCKED draft 原規劃加夜盤（15:00-04:30）。User Option B 暫不啟用夜盤，理由：
1. v1.1 thesis 在夜盤量小的環境下「過熱」定義不一定適用
2. 60M regime gate 在夜盤仍持續計算（連續滾動），但進場僅日盤
3. 夜盤是 enhancement 不是 redesign 必須，delay 至 v2.1
4. 一次只動一個維度（time frame），便於回測時歸因

### 3.6 結構保留清單（100% identical to v1.1）

- Holiday tail registry (63 entries, byte-identical 與 L1-L5/S1/v1.1)
- Settlement_Flat module (Rule #11 七元素)
- P3b SetStopLoss engine guard (Rule #12 單一 call)
- Frozen SL backup (Section 5a + S-3 BuyToCover at Stop)
- Day-session-only intraday high tracker (v1.1 BUG FIX #4 preserved)
- TP fill-bar trap guards (v1.1 BUG FIX #1 三層 guards)
- Daily flat Time<=1340 上限 (v1.1 BUG FIX #3)
- Holiday flat Time<=455 上限 (v1.1 BUG FIX #2)
- Cooldown reset gated by day-session open (v1.1 BUG FIX #8)
- 所有 closed-interval Time safety audits

---

## 4. Expected Performance

### 4.1 v1.1 baseline vs v2.0 target

| 指標 | v1.1 實測 | v2.0 target |
|------|-----------|-------------|
| Trades/yr | **9** ❌ | **25-50** ✅ |
| WR | 53.85% | 48-55% |
| PF gross | 1.37 | 1.25-1.45 |
| **PF net (含滑價 1k NTD/trade)** | **-0.92** ❌ | **> 1.0** ✅ |
| Sharpe (年化) | 0.21 | 0.4-0.7 |
| Max DD | 19.5% | < 15% |
| 2026 H1 集中度 | **54%** ❌ | **< 35%** ✅ |

### 4.2 失敗條件（v2.0 NO-GO）

任一達成 → 不可上 live_simulation：
- PF net (含滑價) < 1.0
- Sharpe < 0.3
- 樣本集中度 (任一年) > 50%
- Walk-Forward Efficiency < 50%
- 任一 regime PF < 1.0（bull/bear/range）

若 v2.0 fail，後續路徑：
1. **v2.1**：加夜盤（樣本擴大）
2. **v2.2**：thesis pivot（可能改為 gap-fade / S1 鏡像策略）
3. **S3 retire**：slot 還給新策略

---

## 5. Portfolio Role & Risk

### 5.1 Portfolio fit

v2.0 角色不變於 v1.1：**反趨勢空頭組件**，填補 L1-L5+S1 大多為趨勢/動能 long 的 portfolio gap。

預期相關性（vs frozen 6）：
- L1/L5 (long trend): **negative**（反向）
- L4 (bear bounce sell, 已 retire): N/A
- S1 (night long momentum): **near-zero**（日盤 vs 夜盤）
- Portfolio Sharpe 預估 lift：1.329 → ~1.40（若 v2.0 PF net ~1.15 且樣本 30+/yr）

### 5.2 Risk surface

| 風險 | v1.1 | v2.0 緩解 |
|------|------|----------|
| Regime over-fit (2026 H1) | 嚴重 (54%) | 60M cadence 樣本擴大 → 預期均勻分布 |
| 滑價吃掉 edge | 嚴重 (-0.92) | 樣本擴大 + R:R 略升 (1.36) |
| 夜盤 thin liquidity | N/A | v2.0 仍 day-only，無此風險 |
| 多 strategy cohort 同時 short | 低 | S3 唯一日盤 short，無 cohort risk |

---

## 6. Implementation Quality Gates (must pass before MC GA)

| Gate | 標準 | 狀態 |
|------|------|------|
| P0-1 verify_s3_v2.py | 100% PASS | ✅ 94/94 |
| P0-2 Settlement_Flat 七元素 | 全植入 .pla | ✅ verify S7-4 |
| P0-3 SetStopLoss 單一 call | 1 個 call, guarded MP>=0 | ✅ verify S5-3/S5-4 |
| P0-4 10-dim eval baseline | 跑過 default params | ⏳ MC12 待跑 |
| P0-5 TXF1 5M data loaded | 2020-01-01 ~ 今 | ⏳ 用戶 MC 確認 |
| P0-6 TXF1 60M data loaded | 同期 | ⏳ 用戶 MC 確認 |
| P0-7 Auto-Trading OFF | 避免最佳化觸發實單 | ⏳ 用戶 MC 確認 |
| P0-8 v1.1 baseline result | 已記錄對照 | ✅ (-0.92 已 documented) |

---

## 7. Optimization Roadmap

依 [S3_v2_optimization_ranges.md](S3_v2_optimization_ranges.md)：
1. Stage 1: 4 HIGH-sens params × 5 levels = 625 combos (~30 min)
2. Stage 2: best ±1 step + 2 extra params = 729 combos
3. Walk-Forward: IS 2020-2022 / OOS 2023-2026-06
4. Compare to v1.1: PF net > 0 (v1.1 was -0.92)
5. 10 維度 institutional eval（CLAUDE.md Rule #13）

---

## 8. Decision Log

| 日期 | 決策 | 來源 |
|------|------|------|
| 2026-06-20 | **v2.1 ATR Trailing SL**: 解決 Q5「賺後回吐 / 倒虧 / SL 出場」結構問題。Section 5c 新增 trailing layer：浮盈 ≥ TrailingActivate_Pct (default 0.5%) 啟動，每根 K 把 v_SL_Level 縮緊至 `MIN(current, Close + ATR × TrailingATR_Mult)`。SHORT 變體（MIN，非 long 的 MAX）。Engine SetStopLoss (Section 5b) **不 trail**，維持 initial entry-bar ATR×3 作 max-loss cap（用戶 mandate）。新 inputs：`TrailingActivate_Pct=0.5` / `TrailingATR_Mult=2.0`。Dec: 覆蓋 v2.0.1 → v2.1（同檔），夜盤延後到 v2.2。 | 本 session（用戶 Q5 之後 mandate） |
| 2026-06-20 | **v2.0.1 MC12 patch**: Section 4 boundary detection `Hour(Time) <> v_LastSeenHour` (assumed 60M align hour, FALSE for TXF1 session-aligned 60M) → `(Date of Data2, Time of Data2)` tuple. Snap0 reads `( RSI(...) of Data2 )[1]` (just-closed, not partial). Section 2 60M MA: `Average(...)[1] of Data2` → `( Average(...) of Data2 )[1]` (explicit parens). | 本 session（用戶 audit） |
| 2026-06-20 | User selects Option B: preserve thesis, shorten regime TF Daily → 60M | 本 session |
| 2026-06-20 | User rejects: v2.0 雙路徑 (Path C+D) draft (Path C alpha 驗為負) | 本 session |
| 2026-06-20 | User defers: 夜盤至 v2.1 | 本 session（隱含於 Option B） |
| 2026-06-20 | User mandates: 不再 alpha workflow verify，直接 implement → MC backtest 驗 | 本 session |
| 2026-06-19 | v1.1 deployed (commit fe882a3), 16 bugs patched | 前 session |
| 2026-06-20 | v1.0 → v1.1 release (Settlement_Flat, SetStopLoss, frozen SL added) | 前 session |
| 2026-06-20 | v1.0 design accepted (D1-D8 8 decisions) | 前 session |

---

**Status**: **v2.0 implementation complete**. Awaiting MC12 GA + 10-dim eval to determine GO/NO-GO for live_simulation promotion.
