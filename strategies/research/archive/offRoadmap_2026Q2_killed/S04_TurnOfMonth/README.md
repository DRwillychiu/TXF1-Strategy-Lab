# S4 TurnOfMonth_Long — Calendar Effect Positional Long

> ⚠️ **2026-06-21 STATUS UPDATE**：本策略已於 W1 完成當日 **KILLED**。
> 詳見：[S4_FINAL_VERDICT.md](S4_FINAL_VERDICT.md)
>
> KILL 理由（一句話）：28-year robustness test 顯示 alpha cyclical decay，
> 6 個 macro regime 中只有 3 個有正 Sharpe，2010-2018 連續 8 年負 Sharpe，
> 28-year overall Sharpe 0.33 / Max DD -32% 超過機構警戒。
> 我之前的 6.4-year Sharpe 0.87 是 over-optimistic recent-bias snapshot。

---

**建立日**：2026-06-21
**結案日**：2026-06-21（同日 KILL，W2 .pla 未寫）
**狀態**：💀 **KILLED — NOT FEASIBLE**
**最終版本**：v0.2 (TXF1-empirics-corrected，已棄用)
**KILL 速度**：1 天（vs S2 5 版本多週）→ S2 lessons 發揮作用

---

## 一、策略一句話

**每個月底前 4 個交易日進場做多，月初 3 個交易日後出場 — 純 calendar 效應，無動量無 regime。**

= Turn-of-Month Effect
= Calendar Anomaly Strategy
= Positional Long (5-7 day hold)

---

## 二、Portfolio 角色（**為什麼必須做**）

### 7-策略 portfolio 缺口分析

```
現有 6 策略類型分布：
─────────────────────────────────────────────────────
趨勢 (L1/L2/L5)    動量 (S1, S3 v2.0.4)    區間 (L3, L4)
   ❌ 缺：純 calendar / event-driven 無動量依賴
                            ↓
                        S4 補在這
```

### Sharpe-additive 核心理由

| 維度 | S4 預期 | 與其他策略 |
|------|---------|-----------|
| 相關性 ρ | **≈ 0** | 與 L1-L5 + S1 + S3 全部不相關 |
| Sharpe 貢獻 | **HIGH** | 純 diversifier，提升整體 risk-adj return |
| 複雜度 | **LOW** | 純 calendar 邏輯 ~150 LOC |
| 樣本 | 12/年 × 6.5 年 = **78 trades** | 邊際但可用 |

**核心 alpha**：月末資金結算 / 401k 流入 / window dressing → 短期 buy pressure（國際學術文獻支持，最早 Ariel 1987）

---

## 三、12 月 Roadmap 中的位置

```
Q1 2026 (now)         #1 S3 PullbackShort       ✅ v2.0.4 LOCKED (LIVE_SIM)
                      #2 S4 TurnOfMonth_Long    ← 現在啟動

Q2 2026               #3 S5 SPX_Overnight_DayOpen
                      #4 S6 ForeignPositionFade

Q3 2026               #5 S7 PreSettlementHarvest
                      #6 S8 FOMC_OvernightFade

Q4 2026               #7 S9 (TBD per portfolio gap analysis)
```

**S4 = Q1 第 2 個 quick win**，跟 S3 平行進行。

---

## 四、檔案結構

```
S04_TurnOfMonth/
├── README.md                       ← 本檔（入口）
├── S4_TurnOfMonth_strategy.md      ← W1 deliverable：alpha thesis（建立中）
└── (未來會加)
    ├── S4_TurnOfMonth_annotated.md       ← W2: 中文逐段註解
    ├── S4_TurnOfMonth.pla                ← W2: MC12 程式碼 (~150 LOC)
    ├── S4_known_issues.md                ← issue tracker
    ├── verify_s4_turnofmonth.py          ← W3 (~40 checks)
    └── backtests/                         ← MC 回測 xlsx
```

---

## 五、開發路線（7 週 W1-W7）

依 [roadmap](../../../docs/strategy_development_roadmap_v1_20260620.md)：

| Week | Deliverable | 狀態 |
|------|-------------|------|
| **W1** | Scaffold 資料夾 + 寫 `S4_TurnOfMonth_strategy.md` | 🔄 **進行中**（今天）|
| **W2** | 寫 `.pla` (~150 LOC, calendar-only logic) | ⏳ |
| **W3** | 寫 `verify_s4_turnofmonth.py` + 6 年回測 → ~70 trades | ⏳ |
| **W4** | Phase 1 sensitivity sweep（T-3/T-4/T-5 + T+2/T+3/T+4）| ⏳ |
| **W5** | Phase 2 Walk-Forward（樣本邊際，文件化 sample-gate 放寬）| ⏳ |
| **W6** | Phase 3 Monte Carlo + 10-dim institutional eval | ⏳ |
| **W7** | 通過則 promote 到 `live_simulation/` | ⏳ |

---

## 六、核心 Trading Spec（W1 摘要）

### 進場
```
Trigger:  T-4 (月底前第 4 個交易日)
Time:     當日 day-session close (13:25 - 13:45 之間)
Direction: Long
Method:   "buy next bar at Market" 在 T-4 close
```

### 出場
```
Primary:  T+3 (月初第 3 個交易日) day-session close
Backup:   -2 ATR trailing stop（從 entry 算）
Override: Settlement Wed 在持倉中 → defer entry to next month
          （Rule #11 Settlement_Flat 強制）
```

### 持倉
```
Min: 5 trading days (含 T-4 to T+1)
Max: 7 trading days (T-4 to T+3)
跨假日 / 結算日邏輯沿用 portfolio 共用 Holiday_Tail + Settlement
```

### 預期表現（pre-backtest）
```
Trades/年:   ~12 (每月 1 次)
WR:          ~58-65% (calendar effect 學術 estimate)
PF:          1.3-1.7 (含滑價)
Sharpe (年化): 0.6-1.0
Max DD:      < 8% of account
持倉週期:    5-7 trading days
跨年穩定性:  high (calendar 不受 regime 影響)
```

---

## 七、設計討論啟動點（**等用戶 review 後進 W2 寫 .pla**）

### 需要用戶決策的 5 個關鍵點

1. **進場時機**：T-4 close vs T-3 close vs T-5 close？
   - 學術建議 T-4，但 TXF1 可能不同
   - **建議**：W1 先用 T-4 做 baseline，W4 sensitivity sweep
   
2. **出場時機**：T+3 close vs T+2 close vs T+4 close？
   - 同上，T+3 為 baseline
   
3. **Settlement Wed 衝突處理**：
   - T-4 to T+3 約 5-7 個交易日
   - 必然會撞到當月 Settlement Wed（第 3 週 Wed）
   - **選項 A**：當 T-4 撞 Settlement → 跳過本月（最安全）
   - **選項 B**：當 T-4 撞 Settlement → 改用 T-3 entry
   - **選項 C**：強制 12:30 平倉跨 Settlement → 持倉時間縮短
   - **建議**：Option A（保守，符合 Rule #11 精神）

4. **倉位管理**：固定 1 口 vs 動態 sizing？
   - **建議**：1 口固定（跟 portfolio 其他策略一致）

5. **是否加 trend filter**：純 calendar vs 加 Daily MA200 trend filter？
   - **純 calendar**：alpha 來源純粹但可能空頭年虧損
   - **加 MA200 filter**：只在 Daily Close > MA200 時 enable
   - **建議**：純 calendar v1.0 baseline，加 trend filter 留 v1.1 sweep

---

## 八、Mandatory Compliance（Rule #11/#12/#13）

| Rule | 要求 | S4 計畫 |
|------|------|---------|
| **#11 Settlement_Flat** | 7 元素 + Priority 0 順序 | ✓ 沿用 L1-L5 模板 |
| **#12 P3b SetStopLoss** | 單一 call + MP <= 0 guard | ✓ -2 ATR stop 對應 |
| **#13 10-dim 評估** | live_sim 前必過 | W6 跑完整 10-dim |

---

## 九、跟 S2 的關係

S2 InsideBarBreak 已於 2026-06-21 **ARCHIVED FINAL**（alpha 死亡確認）。S4 是接續資源轉入的策略。

**S4 借鑑 S2 的 13 個教訓**：
- 教訓 #4「突破類 → Long-only」→ S4 本來就 Long-only ✓
- 教訓 #5「教科書 alpha 衰減」→ TurnOfMonth 是經典效應，**S4 必須驗證在 TXF1 上是否仍存在**（learn from S2 mistake）
- 教訓 #11「Buy & Hold 是現實檢驗」→ S4 必須對比 B&H
- 教訓 #13「Filter 重疊度檢查」→ S4 inputs 少，redundancy 風險低

---

## 十、相關文件

- **完整 12 月 roadmap**：[../../../docs/strategy_development_roadmap_v1_20260620.md](../../../docs/strategy_development_roadmap_v1_20260620.md)
- **Portfolio v3 (S3 加入後)**：[../../../docs/portfolio_allocation_v3_20260620.md](../../../docs/portfolio_allocation_v3_20260620.md)
- **機構級風險框架 (Rule #13)**：[../../../docs/institutional_risk_framework_20260619.md](../../../docs/institutional_risk_framework_20260619.md)
- **Settlement Constitution**：[../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md](../../../docs/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- **S2 結案（前置策略）**：[../S02_InsideBarBreak/S2_FINAL_VERDICT.md](../S02_InsideBarBreak/S2_FINAL_VERDICT.md)
- **S3 v2.0.4 LOCKED（並行 Q1 策略）**：[../S03_PullbackShort/](../S03_PullbackShort/)

---

## 十一、學習自 S3 v1.1 → v2.0 慘案的開發紀律（**S4 必守**）

1. ✅ **先深度討論，後寫 .pla**（不再設計超前實證）
2. ✅ **alpha thesis 先驗證**（W1 完成 strategy.md 才能 W2 寫 code）
3. ✅ **MC12 載入前跑完整 PL function existence check**（避免 LastBarOnChart_Ex 慘案）
4. ✅ **GA 設定族群 50 / 世代 30** 不是族群 256 / 世代 1
5. ✅ **任何 filter 必須做重疊度 + 通過率雙重檢查**
6. ✅ **Time 條件必須閉區間**（cross-day pitfall）
7. ✅ **TP 倍率必從 MFE 統計推導**
8. ✅ **MC 真實回測前不可宣稱 alpha 真實**

---

**現在進入 W1**：用戶 review 本 README + 確認 5 個 design decision → 我寫完整 `S4_TurnOfMonth_strategy.md` → W2 寫 .pla。
