# Portfolio Allocation v3 — 7 策略配置（L4 退役 + S3 上線）

**生效日**：2026-06-20
**狀態**：**v3 FINAL — L4 退役、S3 RapidPullbackShort 接手 3% 槽位**
**前一版本**：[portfolio_allocation_v2_20260620.md](portfolio_allocation_v2_20260620.md)（6 策略凍結版）
**整合依據**：v2 基準 + [L4_retirement_report_20260620.md](L4_retirement_report_20260620.md) + 2026-06-20 S3 設計決策 D1-D8

---

## 一、版本差異摘要（v2 → v3）

### 1.1 配置變更總覽

| 策略 | v2 配置 % | v3 配置 % | Delta | 變更原因 |
|------|-----------|-----------|-------|---------|
| L1 TrendLong | 29% | **29%** | 0 | 凍結，無變更 |
| L2 TrendShort | 22% | **22%** | 0 | 凍結，無變更 |
| L3 ConsolidationLong | 10% | **10%** | 0 | 凍結，無變更 |
| **L4 ConsolidationShort** | **3%** | **0%** | **−3** | **★ 退役（D6 決策）** |
| L5 BreakoutLong | 16% | **16%** | 0 | 凍結，無變更 |
| S1 NightMomentum | 20% | **20%** | 0 | 凍結，無變更 |
| **S3 RapidPullbackShort** | — | **3%** | **+3** | **★ 新增（接手 L4 槽位）** |
| **總計** | **100%** | **100%** | 0 | — |

### 1.2 v2 → v3 三大改變

1. **L4 退役**：3% → 0%，程式碼保留但實盤配置歸零
2. **S3 新增**：0 → 3%，作為「牛市拉回對沖」填補 v2 識別的 Gap 1
3. **策略數量**：6 → 7（live 5 + live_simulation 2）

### 1.3 不變項

- L1/L2/L3/L5/S1 維持 **production frozen** 狀態
- 整體 100% 配置不變
- 推薦帳戶資金需求不變（~1.5M）
- Settlement_Flat + ImmediateStop 共通模組強制要求不變

---

## 二、D6 決策：L4 退役

### 2.1 決策內容

| 項目 | 內容 |
|---|---|
| 決策時點 | 2026-06-20（S3 設計討論中明確指示） |
| 決策內容 | L4 ConsolidationShort 從實盤配置中退役（3% → 0%） |
| 授權方式 | User explicit override |
| 覆蓋指令 | 推翻 2026-06-19「L4 保留 3% 小倉作為黑天鵝捕手」之承諾 |
| 取代策略 | S3 RapidPullbackShort 接收原本配給 L4 的 3% 額度 |
| 程式碼處置 | `strategies/live/L4_ConsolidationShort.pla` **保留**（隨時可重啟），但 MC12 上 disabled |
| 完整論證 | 詳見 [L4_retirement_report_20260620.md](L4_retirement_report_20260620.md) |

### 2.2 為何 L4 必須退役（引用 L4_retirement_report）

L4 在 P0-2 Walk-Forward 與 Bootstrap 階段已暴露 5 大結構性問題：

| # | 指標 | L4 實測 | 門檻 | 結果 |
|---|------|--------|------|------|
| 1 | Walk-Forward 穩定性 | 4/5 FAIL | ≥ 3/5 PASS | ✗ |
| 2 | Bootstrap Robustness | 76.5% | ≥ 95% | ✗ |
| 3 | 排除 2025 後 5 年 NET | −55K | > 0 | ✗ |
| 4 | Yearly Instability Score | 3.24 | ≤ 1.0 | ✗ |
| 5 | Probabilistic Sharpe Ratio | 0.884 | ≥ 0.95 | ✗ |
| 6 | Gini Concentration | 0.619 | ≤ 0.4 | ✗（lottery dependency） |

**核心病根**：L4 賺錢機制是 **black-swan capture**（2025-04-07 暴跌單筆 +286.6K 佔全年 97%），扣除該筆後 5 年淨利為 **−55K**。樣本量不足以做統計顯著的期望值估計，PSR 0.884 < 0.95 明確告知不應以此設定資金配置。

### 2.3 為何 S3 比 L4 更值得這 3% 槽位

| 比較維度 | L4（black-swan 捕手） | S3（牛市拉回對沖） |
|---------|--------------------|------------------|
| 觸發頻率 | 5 年 1-2 次符合規模 | 預估 25-40 trades/year |
| 統計顯著性 | PSR 0.884 < 0.95 | 待 P3 驗證（目標 ≥ 0.95） |
| 預期年度貢獻 | ~30-60K，95% CI 跨越 0 | ~80-130K（基於 ATR-based exit） |
| Hedge 功能 | 黑天鵝下跌 | 牛市中段拉回（v2 Gap 1） |
| Portfolio 互補性 | 與既有 6 隻完全不相關（極低觸發） | 填補多頭年 pullback 對沖缺口 |

**結論**：S3 機會成本 +50K~+70K/year 且變異數更低。

---

## 三、更新版 7-策略配置表

### 3.1 完整配置（v3 FINAL）

| 策略 | 版本 | 配置 % | 1 口保證金 | 預期年化貢獻 | Verdict | Layer |
|------|------|-------|-----------|------------|---------|-------|
| **L1** TrendLong | V2.6 + Settlement + ImmediateStop | **29%** | 290K | +10-12% | ✅ ROBUST | live |
| **L2** TrendShort | 5.2 + Settlement + ImmediateStop | **22%** | 220K | +5-7% | ⚠️ WATCH | live |
| **L3** ConsolidationLong | v13.4 + Settlement + ImmediateStop | **10%** | 100K | +1-2% | ⚠️ WATCH（PSR 邊界） | live |
| ~~**L4** ConsolidationShort~~ | ~~v14.4 + ImmediateStop~~ | ~~3%~~ → **0%** | — | — | ❌ RETIRED | live（disabled） |
| **L5** BreakoutLong | v19.8 + Settlement + ImmediateStop | **16%** | 160K | +5-7% | ✅ ROBUST | live |
| **S1** NightMomentum | v2.7 + Settlement + ImmediateStop | **20%** | 200K | +5-6% | ⚠️ WATCH | live_simulation |
| **S3** RapidPullbackShort | v1.0（設計中） | **3%** | 30K | +1-2%（estimate） | 🆕 DESIGN | research → live_simulation |
| **總計** | — | **100%** | **~970K** | **+27-36%** | — | — |

### 3.2 角色說明

| 策略 | Portfolio 角色 |
|------|-------------|
| L1 | Portfolio 第一柱、唯一三市況皆與 S1 負相關之 hedge pair |
| L2 | 真正能大賺的空策略、PF 2.88 最高 |
| L3 | 最乾淨低相關 diversifier（與 L1/L2 月相關 < 0.06） |
| L5 | 次大 robust、突破型多單 |
| S1 | Portfolio backstop、夜盤 alpha 不與其他重疊 |
| **S3** | **★ 牛市中段拉回對沖（v2 Gap 1 解法）、日內短倉、ATR-based exit** |

### 3.3 各策略 % 不變項說明（為何 L1/L2/L3/L5/S1 不調整）

- v2 的 6 隻凍結策略仍處於 production frozen 狀態
- L4 退役釋出的 3% 槽位**僅**轉至 S3，不重新分配至其他策略
- 此設計保留 v2 P0-1/P0-2 整合結果的完整性，避免一次變更過多

---

## 四、為何 S3 接手 L4 的 3%（資料驅動論證）

### 4.1 Portfolio Gap 識別（來自 v2 第六節）

v2 凍結時明確識別：
> Gap 1：Short-the-Rip（多頭中段拉回對沖）— 用戶 2026-06-20 親自發現，現有 6 策略無一覆蓋。

S3 RapidPullbackShort 即為此 gap 的對應解法。

### 4.2 觸發頻率對比

| 事件類型 | 5 年發生次數 | 年均頻率 | Portfolio 涵蓋 |
|---------|------------|---------|--------------|
| Black-swan 暴跌（L4 目標） | 1-2 次 | 0.2-0.4 / year | L4（即將退役） |
| 牛市中段拉回（S3 目標） | 125-200 次 | 25-40 / year | **無** → S3 補完 |

S3 觸發頻率為 L4 的 **62-200 倍**，提供顯著更穩健的統計樣本基礎。

### 4.3 S3 設計重點（D1-D8 摘要）

| 決策 | 內容 |
|------|------|
| D1 Regime Gate | MODERATE — A AND (B OR C)。A: Daily MA20>MA60；B: Daily RSI(14)>70 sustained 2 bars；C: Daily 距 MA20 > +3%。預期 WATCH ~5 days/month |
| D2 Momentum Trigger | BALANCED 4-AND（3 連黑、Close<EMA5 且 EMA5 下傾、ATR(5)>ATR(20)×1.3、距高點 0.5%~1.5%）。Volume 條件 dropped（S2 lesson） |
| D3 Exit Tier | TP 0.7%、SL ATR(14)×4 (~0.58%)、Time 120 min 硬上限。R:R 1.21，目標 WR 52-58% |
| D4 TP 結構備援 | 5M EMA20 touch（whichever fires first） |
| D5 Entry Window | 08:45 - 12:30（wider） |
| D6 L4 處置 | RETIRE（3% → 0%），S3 接手 |
| D7 Volume 預驗證 | 5-line MC ShowMe study 先做（程序性，非 blocking） |
| D8 HighConviction Modifier | dist > +5% 僅 logging（v1.0），v1.1 才掃參數 |

**關鍵約束**：所有數值門檻必須是 PowerLanguage `inputs:`，**不可寫死**，留給後續 MC12 optimization sweep。

### 4.4 S3 必須達成的 quality gates（晉升 live_simulation 條件）

- WFE > 50%
- Monte Carlo 95% MDD < 帳戶 30%
- OOS PF > 1.0
- 樣本 ≥ 100 trades
- 通過 CLAUDE.md 規則 #11/#12/#13（Settlement_Flat + P3b SetStopLoss + 10 維評估）

未達標前 S3 維持 `research/` 層，3% 配額**暫時不啟用**（保留現金 buffer，不重分配給其他策略）。

---

## 五、帳戶資金需求（與 v2 一致）

### 5.1 推薦資金門檻

| 帳戶規模 | 倉位實作 |
|---------|--------|
| **1,500,000 NTD（推薦）** | 全部 7 隻策略可同時上線（S3 上線後）、含 30% MDD buffer |
| 1,000,000 NTD | 跑 L1+L2+L3+L5+S1（5 隻）；S3 待 P3 通過後再上 |
| 500,000 NTD | 只跑 L1 + L5 + S1（3 隻 robust + 1 hedge） |
| < 300,000 | 不建議實盤 |

### 5.2 v2 → v3 資金需求差異

- v2：6 × 184K ≈ 1.1M 保證金
- v3：6 × 184K（L1/L2/L3/L5/S1 + S3）≈ 1.1M（L4 退役釋出 30K，S3 新增 30K，淨變化 0）
- 推薦帳戶仍為 **1.5M**（含 30% buffer）

---

## 六、MC12 部署 SOP（v3 變更）

### 6.1 從 v2 切到 v3 的最小變更步驟

```
1. MC12 開啟 L4_ConsolidationShort 圖表
   → 右鍵 strategy → properties → 暫停 strategy（Auto Trading: OFF）
   → 不刪除圖表、不卸載 .pla（程式碼保留以利重啟）
   → 圖表標題加註 "[RETIRED 2026-06-20]"

2. S3 設計完成 + P3 通過後（預估數週內）：
   → 新增獨立 chart 載入 STRATEGY_GEN_RapidPullbackShort
   → strategy properties:
       Initial Capital     : 1,000,000
       Slippage            : 1,000 NTD round-trip
       Commission          : 30 NTD / trade
       Position size       : 1 contract fixed
       Pyramiding          : false
   → 初期 MC12 模擬帳戶執行（live_simulation 層），不上 MC9 實盤

3. 其餘 5 隻策略（L1/L2/L3/L5/S1）完全不動
```

### 6.2 多策略統一設定（不變）

```
Initial Capital     : 1,000,000
Slippage            : 1,000 NTD round-trip
Commission          : 30 NTD / trade
Position size       : 1 contract fixed
Pyramiding          : false
帳戶餘額            : ≥ 1.5M（留 30% buffer for MDD）
```

### 6.3 監控指標（每週 — 加入 S3 行）

| 指標 | 警示閾值 | 行動 |
|------|--------|------|
| 整體 MDD% | > 帳戶 20% | 暫停所有策略 review |
| 單一策略 MDD% | > 該策略歷史 MDD × 1.5 | 該策略暫停 |
| 連續虧損週 | > 3 週 | review portfolio regime |
| S3 月觸發次數 | < 1 或 > 8 | review regime gate 是否失效 |
| S3 偏離度 | > 30% | 立即暫停、回 research |
| ~~L4 月虧~~ | ~~> 50K~~ | ~~已退役、N/A~~ |

---

## 七、季度 review checklist（更新為 7 策略含 S3）

```
[ ] 跑 verify_all_live.py（L1-L5 共 110 項）
[ ] 跑 verify_settlement_flat.py（含 S3 共 49 項，原 42 項 + 7 項 S3）
[ ] 跑 verify_strategy_holding_classification.py
[ ] 跑 verify_s1_v22.py（S1 模擬層）
[ ] 跑 verify_s3_v10.py（待 S3 設計完成後建立）
[ ] 比對 actual vs backtest 偏離度（per CLAUDE.md gate ≤ 30%）
[ ] 檢查 holiday_tail registry 是否需更新（Q4 each year）
[ ] 檢查 Registry_Valid_Until 是否超過半年
[ ] 確認 L4 圖表仍標註 [RETIRED 2026-06-20]，未被誤開啟
[ ] S3 季度績效檢視：若 trade count < 60/year 或 PSR 連 2 季 < 0.95 → 重新評估
```

---

## 八、Frozen 狀態的含義（v3 更新）

### 8.1 Production Frozen 範圍（不變）

L1 / L2 / L3 / L5 / S1 **仍處於 production frozen 狀態**：
1. 不可修改任何 .pla 程式碼
2. 不可改變 input 預設值
3. 不可加新 filter / 新 input switch
4. 不可試圖優化現有策略 alpha

### 8.2 L4 狀態（新）

- L4 處於 **RETIRED but PRESERVED** 狀態
- 程式碼留存（隨時可重啟）
- 實盤配置歸零
- 解凍/重啟條件：用戶明確主動要求

### 8.3 S3 狀態（新）

- S3 處於 **DESIGN PHASE**（research/ 層）
- **不**屬於 frozen 範圍（仍在開發中）
- 設計階段可自由迭代（D1-D8 之內）
- 所有數值門檻必須以 `inputs:` 宣告（待 MC12 optimization sweep）
- 通過 P3 + 10 維評估後晉升 live_simulation；通過模擬實證後晉升 live

### 8.4 何時可全面解凍（不變）

當且僅當以下任一條件滿足：
- ❶ 連續 6 個月某策略偏離度 > 50%（明確失效）
- ❷ 機構級新發現顛覆現有設計（如新監管 / 新市場結構）
- ❸ 用戶明確主動要求

---

## 九、相關文件（cross-references）

### 9.1 上游決策依據

- [portfolio_allocation_v2_20260620.md](portfolio_allocation_v2_20260620.md) — v2 凍結基準
- [L4_retirement_report_20260620.md](L4_retirement_report_20260620.md) — L4 退役完整論證
- [portfolio_correlation_matrix_20260620.md](portfolio_correlation_matrix_20260620.md) — P0-1 相關性分析
- [portfolio_walk_forward_20260620.md](portfolio_walk_forward_20260620.md) — P0-2 Walk-Forward 結果
- [portfolio_institutional_audit_20260619.md](portfolio_institutional_audit_20260619.md) — 機構審視

### 9.2 S3 設計相關（待生成）

- `docs/S3_RapidPullbackShort_design_spec_20260620.md` — S3 設計規格書（pending）
- `strategies/research/S03_RapidPullbackShort/STRATEGY_GEN_RapidPullbackShort.pla` — S3 PowerLanguage 程式碼（pending）
- `scripts/verify_s3_v10.py` — S3 驗證腳本（pending）

### 9.3 強制規範文件

- [SETTLEMENT_DAY_DESIGN_CONSTITUTION.md](SETTLEMENT_DAY_DESIGN_CONSTITUTION.md) — CLAUDE.md 規則 #11
- [P3b_immediate_stop_guard_design_20260618.md](P3b_immediate_stop_guard_design_20260618.md) — CLAUDE.md 規則 #12
- [institutional_risk_framework_20260619.md](institutional_risk_framework_20260619.md) — CLAUDE.md 規則 #13
- [strategy_development_roadmap_v1_20260620.md](strategy_development_roadmap_v1_20260620.md) — 新策略開發路線圖
- [CLAUDE.md](../CLAUDE.md) — 專案規範總則

### 9.4 L4 歷史相關文件（封存供參）

- [L4_portfolio_role_20260618.md](L4_portfolio_role_20260618.md) — L4 原本「不歸零」承諾來源
- [L4_v14.4_deep_analysis_20260618.md](L4_v14.4_deep_analysis_20260618.md) — L4 結構性問題深度分析
- [L4_v14.5_design_spec_20260618.md](L4_v14.5_design_spec_20260618.md) — L4 v14.5 設計規格（已凍結）
- [L4_v14.5_ab_results_20260618.md](L4_v14.5_ab_results_20260618.md) — L4 v14.5 A/B 結果

---

## 十、版本歷史

| 版本 | 日期 | 變更 | 狀態 |
|------|------|------|------|
| **v3 (本檔)** | **2026-06-20** | **L4 退役（3%→0%）+ S3 RapidPullbackShort 接手（+3%）** | **FINAL** |
| v2 | 2026-06-20 | 6 策略凍結 + P0-1/2 整合 final allocation | superseded by v3 |
| v1 (preliminary) | 2026-06-19 | 機構審視初稿 | superseded by v2 |

---

## 十一、用戶授權聲明

> **2026-06-20 用戶決策（D6）**：
> 「L4 RETIRE（3% → 0%），S3 接手該槽位。理由：S3 填補牛市拉回對沖缺口的頻率，遠高於 L4 捕捉黑天鵝事件的頻率。L4 已 4/5 stability tests fail，繼續保留小倉的論述不再成立。」
>
> 此決策**明確覆蓋** 2026-06-19 於 v2 + L4_portfolio_role 中提出的「L4 不歸零」承諾。

---

**Allocation v3 生效：L4 退役、S3 接手、其餘 5 隻 frozen 不變。**
**下一步：S3 設計規格書（D1-D8 落地為 .pla）+ verify_s3_v10.py + 10 維評估。**
