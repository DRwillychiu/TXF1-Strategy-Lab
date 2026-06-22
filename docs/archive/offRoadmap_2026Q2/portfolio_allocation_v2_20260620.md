# Portfolio Allocation v2 — 6 策略凍結版

**生效日**：2026-06-20
**狀態**：**6 策略凍結（用戶 2026-06-20 決定）**
**整合依據**：[P0-1 Correlation](portfolio_correlation_matrix_20260620.md) + [P0-2 Walk-Forward](portfolio_walk_forward_20260620.md)
**未來焦點**：新策略開發（見 [strategy_development_roadmap_v1_20260620.md](strategy_development_roadmap_v1_20260620.md)）

---

## 一、用戶 2026-06-20 戰略決策

> 「L1-L5 以及 S1 的策略就完全不要做更動了。  
> 反而是要針對接下來的策略規劃以及開發作更深層的規畫以及研究。」

**含義**：
- 6 策略當前版本鎖定為 **production frozen**
- 不再個別優化（L4 v14.5 / S2 v0.6 等實驗已停止）
- 精力轉向**新策略 alpha 創新**
- 本文件作為 **freeze 配置基準**

---

## 二、最終配置（P0-1 + P0-2 整合）

### 配置表

| 策略 | 版本 | 配置 % | 1 口保證金 | 預期年化貢獻 | Verdict |
|------|------|--------|---------|------------|---------|
| **L1** TrendLong | V2.6 + Settlement + ImmediateStop | **29%** | 290K | +10-12% | ✅ ROBUST |
| **L2** TrendShort | 5.2 + Settlement + ImmediateStop | **22%** | 220K | +5-7% | ⚠️ WATCH |
| **L3** ConsolidationLong | v13.4 + Settlement + ImmediateStop | **10%** | 100K | +1-2% | ⚠️ WATCH（PSR 邊界）|
| **L4** ConsolidationShort | v14.4 + ImmediateStop | **3%** | 30K | +0.1% | ❌ OVERFIT_RISK |
| **L5** BreakoutLong | v19.8 + Settlement + ImmediateStop | **16%** | 160K | +5-7% | ✅ ROBUST |
| **S1** NightMomentum | v2.7 + Settlement + ImmediateStop | **20%** | 200K | +5-6% | ⚠️ WATCH |
| **總計** | — | **100%** | **1,000K** | **+26-35%** | — |

### 帳戶資金需求

| 帳戶規模 | 倉位實作 |
|---------|--------|
| **1,000,000 NTD（推薦）**| 每隻策略 1 口固定（保證金約 184K × 6 = 1.1M，須留 30% buffer）|
| 500,000 NTD | 只跑 L1 + L5 + S1（3 隻 robust + 1 hedge）|
| < 300,000 | 不建議實盤 |

### 為什麼是這個比例

#### L1 = 29%（最大持倉）
- **唯一全 robust 策略**（5/5 tests pass）
- 個別 Sharpe 最高
- L1↔S1 是**唯一三市況皆負相關的 hedge pair**
- Drop-one marginal Sharpe 最高（+0.140）
- → **書中第一柱**

#### L5 = 16%（次大）
- ROBUST verdict（1 caveat：2024-25 outsized）
- PF 2.02 / Sharpe 0.255
- 與 L1 月相關 +0.524（高，**避免疊加做多風險**）
- → 從 P0-1 推薦 15% 微升到 16%（P0-2 確認 robust）

#### S1 = 20%（不變）
- WATCH but 樣本 774 最充足
- 與 L1 結構性對沖（不可砍）
- 夜盤 alpha 不與其他重疊
- → **portfolio 的 backstop**

#### L2 = 22%（顯著加重）
- 從 15% 加到 22% = **第二大加重**
- Drop-one marginal Sharpe 第二高（+0.128）
- PF 2.88 最高（雖樣本 79 偏少）
- 唯一**真正能大賺的空策略**
- → essential

#### L3 = 10%（微減）
- PSR 0.884 < 0.95 邊界
- Bootstrap p5 < 0
- 保留理由：**最乾淨低相關 diversifier**（與 L1/L2/L4 月相關 < 0.06）
- → 從 12% 微減到 10%

#### L4 = 3%（最小）
- **OVERFIT_RISK verdict** 確認
- 沒有 2025-04-07（單筆 +287K）就是 5 年 -55K
- 保留 1 口最小倉位的理由：
  - portfolio 唯一「**黑天鵝下跌**」捕捉策略（2025-04 證明）
  - diagnostic continuity（資料持續累積）
  - 倉位小到不會傷整體
- → **不可加倉，不可砍光**

---

## 三、實盤部署 SOP

### MC12 多策略配置步驟

```
1. 確認 6 隻策略都載入最新 .pla 版本（list 見配置表）
2. 每隻策略獨立 chart，獨立 strategy properties
3. 統一設定:
   Initial Capital     : 1,000,000
   Slippage            : 1,000 NTD round-trip
   Commission          : 30 NTD / trade
   Position size       : 1 contract fixed
   Pyramiding          : false
4. 帳戶配置:
   實質保證金需求 = 6 × 184K = 1.1M
   建議帳戶餘額 ≥ 1.5M（留 30% buffer for MDD）
```

### 監控指標（每週）

| 指標 | 警示閾值 | 行動 |
|------|--------|------|
| 整體 MDD% | > 帳戶 20% | 暫停所有策略 review |
| 單一策略 MDD% | > 該策略歷史 MDD × 1.5 | 該策略暫停 |
| 連續虧損週 | > 3 週 | review portfolio regime |
| L4 月虧 | > 50K | L4 暫停 |

### 季度 review checklist

```
[ ] 跑 verify_all_live.py (110/110 PASS)
[ ] 跑 verify_settlement_flat.py (42/42 PASS)
[ ] 跑 verify_strategy_holding_classification.py
[ ] 比對 actual vs backtest 偏離度（per CLAUDE.md gate ≤ 30%）
[ ] 檢查 holiday_tail registry 是否需更新（Q4 each year）
[ ] 檢查 Registry_Valid_Until 是否超過半年
```

---

## 四、Frozen 狀態的含義（明確規範）

### 不可做的事 ❌

1. **不可修改任何 .pla 程式碼**（L1-L5 + S1）
2. **不可改變 input 預設值**
3. **不可加新 filter / 新 input switch**
4. **不可試圖優化現有策略 alpha**

### 可以做的事 ✅

1. **每季更新 Holiday_Tail 登錄表**（exception，只更新 TAIFEX 假日資料）
2. **更新 Registry_Valid_Until 延展**（每年 Q4）
3. **可加新策略到 portfolio**（不污染現有 6 隻）
4. **可微調 portfolio 配置 %**（基於季度績效）

### 何時可以解凍

當且僅當以下任一條件滿足：
- ❶ 連續 6 個月某策略偏離度 > 50%（明確失效）
- ❷ 機構級新發現顛覆現有設計（如新監管 / 新市場結構）
- ❸ 用戶明確主動要求

---

## 五、配置 vs 昨日 preliminary 對比

| 策略 | 昨日 preliminary | P0-1 推薦 | **P0-2 final** | 變化 |
|------|---------------|----------|--------------|------|
| L1 | 25% | 28% | **29%** | ↑4 |
| L2 | 15% | 22% | **22%** | ↑7 |
| L3 | 10% | 12% | **10%** | 0 |
| L4 | 10% | 3% | **3%** | ↓7 |
| L5 | 20% | 15% | **16%** | ↓4 |
| S1 | 20% | 20% | **20%** | 0 |

### 主要變化解讀

1. **L1 + L2 合計 +11%**（從 40% → 51%）
   - 兩個 essential 策略加重
   - L1 是 portfolio 第一柱
   - L2 是真正能大賺的空策略

2. **L4 -7%**（從 10% → 3%）
   - OVERFIT_RISK 確認
   - 不刪除是因為 2025-04 證明的黑天鵝捕捉
   - 倉位小到不會傷整體

3. **L5 -4%**（從 20% → 16%）
   - 與 L1 月相關 +0.524（避免疊加多單風險）
   - 仍是 ROBUST，只是減少 redundancy

---

## 六、Portfolio 缺口（**未來新策略的對象**）

雖然 6 策略凍結，但 P0-1 + P0-2 + 用戶洞察明確識別了 **portfolio gap**：

### Gap 1：**Short-the-Rip（多頭中段拉回對沖）**

- 用戶 2026-06-20 親自發現
- 現有 6 策略無一覆蓋
- 預估 portfolio impact：補完 portfolio 在多頭年的 pullback 對沖

### Gap 2-N：**待 strategy_development_roadmap_v1 確認**

深度研究 Workflow（task `wljrmnf9q`）跑完後會列出 top 7 候選策略。

---

## 七、Allocation v2 立刻可做的事

### 你立刻可做（30 分鐘）

```
1. MC12 各策略 strategy properties → 倉位設定 1 contract
2. 帳戶餘額確認 ≥ 1.5M
3. 確認所有 6 隻 .pla 是最新版本（見配置表）
4. 開始實盤
```

### 我這邊在做的（並行）

- Workflow `wljrmnf9q` 跑深度新策略研究
- 完成後給 12 月 roadmap

---

## 八、相關文件

- [P0-1 Correlation Matrix](portfolio_correlation_matrix_20260620.md)
- [P0-2 Walk-Forward](portfolio_walk_forward_20260620.md)
- [Portfolio Institutional Audit](portfolio_institutional_audit_20260619.md)
- [Settlement_Flat Constitution v1.2](SETTLEMENT_DAY_DESIGN_CONSTITUTION.md)
- [L4 Portfolio Role](L4_portfolio_role_20260618.md)
- [Strategy Development Roadmap v1](strategy_development_roadmap_v1_20260620.md)（待生成）
- [CLAUDE.md](../CLAUDE.md) 規則 #11/#12/#13

---

## 九、版本

| 版本 | 日期 | 變更 |
|------|------|------|
| **v2 (本檔)** | **2026-06-20** | **6 策略凍結 + P0-1/2 整合 final allocation** |
| v1 (preliminary) | 2026-06-19 | 機構審視初稿 |

---

**用戶 2026-06-20 戰略指示已執行：6 策略凍結 + 焦點轉向新策略創新。**
