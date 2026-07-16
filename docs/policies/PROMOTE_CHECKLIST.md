# PROMOTE CHECKLIST — research → live_simulation 強制檢查

**建立日期**: 2026-07-16
**觸發事件**: S16_S v1.0-PROD 帶著 W2 draft placeholder `v_Holiday_Block = False` 通過 PROMOTE，違反 Rule #11 直到 6 天後 audit 才發現
**規範層級**: 補足 CLAUDE.md Rule #11/#12/#13/#17 的驗證盲區
**適用範圍**: 所有 research → live_simulation 的 PROMOTE 動作
**違反本 checklist = 違反用戶 2026-07-16 明確指示（不再有犯錯空間）**

---

## 一、事件背景（Root Cause）

### S16_S v1.0-PROD Holiday_Block Placeholder Audit Gap

**時間軸**:
- 2026-07-08: W2 draft 寫成，Section 3 註明 `For W2 draft: hardcode Registry expiry only.`
- 2026-07-10: v1.0-PROD 通過 W4 WFA + W5 5-piece → PROMOTE
- 2026-07-16: 例行 self-audit 才發現 `v_Holiday_Block = False;` 一直 hardcoded

**為什麼發生**:
1. W2 comment 明說「placeholder」但 W3/W4/W5 review 皆未 flag
2. `verify_pla_ascii.py` 只檢 ASCII 合規，不檢 placeholder pattern
3. Rule #13 10 維度評估未含「hardcoded gate default」項目
4. PROMOTE SOP 只要求「Rule #11 Settlement_Flat 模組存在」，未要求「模組實際有效」

**傷害**（未實際發生但存在潛在風險）:
- 假日期間策略可能誤進場 / 誤持倉
- 若跨假 gap 產生 20K+ 損失，會直接歸因於「策略設計失敗」而非「合規 gap」

---

## 二、PROMOTE 前 6 項強制檢查

### Check 1 — Placeholder Scan（HIGHEST）
```bash
# 掃 hardcoded gate/flag = False/True 是否為 placeholder
grep -n "v_Holiday_Block\s*=\s*\(False\|True\);" strategies/<PATH>.pla
grep -n "v_Settlement_Day\s*=\s*\(False\|True\);" strategies/<PATH>.pla
grep -n "v_Registry_Expired\s*=\s*\(False\|True\);" strategies/<PATH>.pla
grep -n "v_.*_Block\s*=\s*False;" strategies/<PATH>.pla
grep -n "placeholder\|TODO\|FIXME\|W2 draft\|W3 draft" strategies/<PATH>.pla
```
**Pass 標準**: 上述查詢**不得**返回無條件賦值行（i.e. `v_X = False;` 且下方無 loop 覆寫）；亦不得含 placeholder/TODO/FIXME/Wx draft 字串
**Fail 處置**: 立即 patch 或 downgrade 回 research

### Check 2 — Rule #11 Settlement_Flat 7 元素齊全
```bash
# Registry array + init + detection + entry gate + exit gate
python scripts/verify_settlement_flat.py --strategy <NAME>
```
**Pass 標準**: 7/7 元素齊全
**Fail 處置**: 拒絕 PROMOTE

### Check 3 — Rule #12 SetStopLoss Guard
```bash
python scripts/verify_l1_immediate_stop.py --strategy <NAME>  # or similar
```
**Pass 標準**: SetStopLoss 存在 + Guard 條件正確（Long: MP<=0, Short: MP>=0）
**Fail 處置**: 拒絕 PROMOTE

### Check 4 — Rule #15 ASCII 100%
```bash
python scripts/verify_pla_ascii.py --strict
```
**Pass 標準**: 27/27 PASS
**Fail 處置**: 拒絕 PROMOTE

### Check 5 — Rule #13 10 維度 + Rule #18 5 件套
- 10 維度：Sharpe/Sortino/Calmar、VaR/CVaR、跨策略相關性<0.7、DD clustering、樣本>=100、WFE>50%、三市況 PF>1.0、成本、operational、regulatory
- 5 件套：Monte Carlo / Bootstrap / Stress / Regime / Robustness (>=4/5 pass)
**Pass 標準**: 詳見 [institutional_risk_framework](institutional_risk_framework_20260619.md) 與 [non_WFA_validation_SOP](../methodology/non_WFA_validation_SOP_20260630.md)

### Check 6 — Sniper 特殊條件（適用低頻策略 <20 trades/yr）
若為 Sniper 型策略（低勝率 + 高賺賠比 + 低頻），額外檢：
- Ruin probability < 1%
- Kelly criterion 落在 5-20%
- Expected value/trade > 0
- Bear PF > 1.5 (Sniper 主場)

---

## 三、Master PROMOTE Verification Script

**建議未來擴充**：`scripts/verify_promote_readiness.py <STRATEGY_NAME>`

單一入口，一次跑完 Check 1-6，返回 GO/NO-GO + 詳細 log。

---

## 四、S16_S v1.0-PROD 事件教訓（Codified）

| Lesson | 內容 |
|--------|-----|
| L-P1 | W2 draft 內的 comment `placeholder` / `TODO` 必須在 PROMOTE 前 grep 掃過 |
| L-P2 | Rule #11 存在 !== Rule #11 有效。程式碼含 array 宣告不代表 registry 有值 |
| L-P3 | ASCII verification 不足以做 promotion gate，需擴充語意 lint |
| L-P4 | 每個 hardcoded `v_X = False;` 都應該有 justification comment（如「short strategy, MP=1 impossible」）|
| L-P5 | PROMOTE 是「合規契約」，不只是「績效通過」— 兩者缺一不可 |

---

## 五、Enforcement

- 本 checklist 為 CLAUDE.md Rule #11/#12/#13/#15/#17/#18 的**執行層**
- 未通過 Check 1-4 任一項 = **拒絕 PROMOTE**
- 若 PROMOTE 後才發現 gap（如本次 S16_S 事件），必須：
  1. 立即 patch，版本號 +.1 (v1.0-PROD → v1.0.1)
  2. 更新 DEPLOYMENT.md 記錄事件
  3. 更新本 checklist（新增 lesson）
  4. Commit + push（Git 完整同步）

---

## 六、與其他規範文件的關係

| 文件 | 角色 |
|------|-----|
| CLAUDE.md | 18 條強制規範（設計層）|
| OFFICIAL_ROADMAP | 策略排程（Rule #14）|
| institutional_risk_framework | Rule #13 10 維度 |
| non_WFA_validation_SOP | Rule #18 5 件套 |
| **本文件（PROMOTE_CHECKLIST）** | **PROMOTE 動作的執行層 6 項檢查** |

---

**End of PROMOTE_CHECKLIST v1.0 — 2026-07-16**
