# S16_S Re-Entry Research — v1.6 → v1.6.2 (2026-07-28)

## Summary

v1.5 baseline 基礎上嘗試新增「二次進場」機制，歷經三個迭代版本：

| Version | Change | Re-Entry Trades | Re-Entry PnL | Total Net | PF | MDD |
|---------|--------|-----------------|-------------|-----------|-----|-----|
| v1.5 | baseline (no re-entry) | 0 | — | +1,963,600 | 1.746 | -456,000 (-18.6%) |
| v1.6 | +re-entry mechanism | 142 | -866,000 | +1,097,600 | 1.173 | -641,000 (-22.7%) |
| v1.6.1 | +slope gate (MinSlope) | 39 | +44,400 | +2,008,000 | 1.495 | -778,000 (-24.5%) |
| v1.6.2 | +close gate (Close>=Price) | 10 | +234,400 | +2,198,000 | 1.711 | -542,400 (-22.2%) |

v1.6.2 為目前最佳版本：淨利最高、PF 接近 baseline、MDD 可控。

---

## Re-Entry Mechanism (v1.6.2)

### 邏輯

1. 每次出場後自動記錄原始進場價，啟動二次進場旗標 (v_ReEntry_Armed)
2. 死亡交叉結構持續成立（ZLEMA Fast < Slow）時，以 stop 掛單等待
3. **斜率門檻 (v1.6.1)**：v_Slope > MinSlope — ZLEMA 快線下降速度須超過 28 點/bar
4. **方向性門檻 (v1.6.2)**：Close >= v_ReEntry_Price — stop 掛單只在收盤價仍於進場水位上方時掛出，確保下一根 bar 必須「由上往下跌到」才成交
5. 出現黃金交叉（結構消失）或新死亡交叉時，自動取消旗標

### 程式碼位置

- Variables: Section 2 (line ~347-350)
- State management: Section 5.5 (line ~470-485)
- EntryPrice capture: Section 7 (line ~501-502)
- Order placement: Section 9 (line ~580-591)
- Prev_MP tracking: Section 11 (line ~771)

---

## v1.6.2 Performance Detail

### Core Metrics

| Metric | v1.5 baseline | v1.6.2 | Delta |
|--------|--------------|--------|-------|
| Net profit | +1,963,600 | +2,198,000 | +234,400 (+11.9%) |
| Profit factor | 1.746 | 1.711 | -0.035 |
| Max drawdown | -456,000 (-18.6%) | -542,400 (-22.2%) | -86,400 worse |
| Win rate | 25.4% | 25.0% | -0.4pp |
| Total trades | 114 | 124 | +10 |
| Avg trade PnL | +17,225 | +17,726 | +501 |
| Net/MDD ratio | 4.31x | 4.05x | -0.26x |

### Re-Entry 10 Trades

| # | Date | Entry | PnL | Exit Signal |
|---|------|-------|-----|-------------|
| 1 | 2026-03-10 | 32,970 | -50,800 | QS_Loss |
| 2 | 2026-03-11 | 33,104 | -35,600 | QS_Loss |
| 3 | 2026-05-06 | 41,211 | -44,400 | QS_Loss |
| 4 | 2026-06-09 | 44,298 | **+565,600** | TimeStop |
| 5 | 2026-06-10 | 43,880 | -42,400 | QS_Loss |
| 6 | 2026-06-12 | 43,451 | -152,000 | SL (engine) |
| 7 | 2026-07-08 | 45,488 | -13,200 | QS_Time |
| 8 | 2026-07-17 | 44,181 | -78,000 | QS_Loss |
| 9 | 2026-07-17 | 44,181 | **+128,000** | GoldenCross |
| 10 | 2026-07-23 | 44,889 | -42,800 | QS_Loss |

- Total: +234,400 | Win 2 (+693,600) | Loss 8 (-459,200)
- WR: 20% | Avg: +23,440/trade
- Arm source: 100% QS_Loss (Close gate 自動過濾掉 QS_Time/TimeStop/TailFlat)
- Ordinal: #1 re-entry 9 trades (+106,400), #2 re-entry 1 trade (+128,000)

---

## Open Issues (Pending Discussion)

### Issue 1: Statistical Fragility (CRITICAL)

**現象**：10 筆 re-entry 中，trade #4 (+565,600) 佔總獲利 81.5%。

| Scenario | Net PnL |
|----------|---------|
| All 10 trades | +234,400 |
| Remove #1 winner | -331,200 |
| Remove top 2 winners | -459,200 |

Re-entry 本質為**低勝率高賠率結構**（WR 20%，贏的時候贏很大）。正期望值依賴極端值而非穩定產出。

**潛在方案**：
- (A) live_sim 前進測試至少 6 個月，驗證損益分布穩定性
- (B) 加入 MaxReEntryPerCycle = 1，每週期最多一次 re-entry
- (C) 維持現狀，接受低勝率高賠率特性

### Issue 2: Sample Concentration (CRITICAL)

**現象**：全部 10 筆 re-entry 集中在 2026 年（5 個月內），2020-2025 零筆。

**疑慮**：
- 可能只在 2026 年高波動 regime 有效
- TXF1 指數從 ~9,000 (2020) 漲至 ~45,000 (2026)，波動點數放大導致 QS_Loss 更頻繁
- 未來指數回落或波動收斂時可能失效

**潛在方案**：
- (A) 設定最少樣本數門檻（例如 20 筆以上才允許上實單）
- (B) 先以 live_sim 觀察模式運行
- (C) 若 QS_Loss 門檻改為 ATR-based（非固定點數），可能改善跨 regime 適用性（但影響主策略）

### Issue 3: Order-Fill Condition Gap (MEDIUM)

**現象**：Section 9 條件在 Bar N 檢查，stop 單在 Bar N+1 成交。兩根 bar 之間條件可能改變。

**最壞場景**：Bar N 斜率 OK + 結構 OK → 掛 stop。Bar N+1 急速 V 反轉 → stop 成交但 ZLEMA 已 golden cross → re-entry 一進場就觸發出場。

**緩解因素**：v_Slope > 28 意味 ZLEMA 快線每 bar 跌 28+ 點，一根 bar 內從快速下跌反轉到 golden cross 極罕見。

**潛在方案**：
- (A) 為 re-entry 設定獨立且更高的斜率門檻（MinSlope_ReEntry = 40+）
- (B) 接受此為 PL 固有限制

### Issue 4: Engine SL Impact on Re-Entry (MEDIUM)

**現象**：trade #6 被引擎停損打出 -152,000（10 筆中最大單筆虧損）。

**根因**：re-entry 進場後 Section 7 建立 frozen SL 基於當時 ATR。QS_Loss 出場代表市場剛經歷波動放大 → ATR 偏高 → SL 距離偏寬 → 虧損金額更大。

**潛在方案**：
- (A) 為 re-entry 設定獨立的 SL_Pct_ReEntry（例如 0.7% vs 主進場 1.0%）
- (B) 限制 re-entry 的 v_Guard_Distance 上限

### Issue 5: No Explicit Time Decay (LOW)

**現象**：v_ReEntry_Armed 從出場後持續到 golden cross / new death cross 才 reset。

**緩解因素**：Close gate 提供隱性時效 — 價格遠離 v_ReEntry_Price 時自然不掛單。但如果價格在 100+ bars 後反彈回原始進場價，仍會觸發掛單。

**潛在方案**：
- (A) 加入 v_ReEntry_ExitBar 記錄出場 bar，條件加入 CurrentBar - v_ReEntry_ExitBar <= MaxReEntryWindow
- (B) Close gate 已大幅緩解，可暫不處理

---

## Bug Review Summary

v1.6.2 程式碼邏輯**零 BUG**。所有場景追蹤（正常流程、Close gate 攔截、death cross 衝突、連續 re-entry、引擎停損、零價格防護、死鎖檢查）均通過驗證。

五個 open issues 均為設計層面的風險控制問題，非程式缺陷。

---

## Decision Pending

v1.6.2 是否上線（live_sim 或 production），以及是否進一步疊加 Issue 1-5 的方案，待與用戶討論後決定。
