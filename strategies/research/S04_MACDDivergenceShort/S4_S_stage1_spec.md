# S4_S MACDDivergenceShort — Stage-1 設計討論

**啟動日**：2026-06-28
**前置**：用戶 2026-06-28 ruling 跳過 S4_L，先做 S4_S
**對應 archive**：`strategies/research/archive/batch01_S2-S5/S4_MACDDivergence.pla` + `TXF1_Strategies_Batch01.md` 策略 4
**規範**：必須通過 W0 → W1 → W2 → W3 → W4 → W5 → W6 完整流程

---

## 一、原始 archive 設計（R-6 拆解前的 S4 雙向）

| 維度 | spec |
|------|------|
| 類別 | D 類（動量型逆勢）|
| 方向 | ★ 雙向（底背離做多 + 頂背離做空）|
| 主週期 | 60M |
| 確認週期 | 無 |
| 預期頻率 | 3-7 筆/月 |
| 賺什麼 | 趨勢動能衰竭的反轉 — 價格創新高/低但 MACD 柱狀體未跟隨 = 動能枯竭 → 反轉 |

### Archive 日線代理結果（樣本不足）
- N = 2 trades only / WR 100% / Net +38K / **無統計意義**
- 需 MC12 60M 重新驗證

---

## 二、R-6 拆解後（S4_S 純空角度）

### 賺什麼錢（短側）
**賺「強多頭末端動能衰竭」的反轉空頭錢**：
- 價格創新高（高點突破）
- 但 MACD 柱狀體**未同步創新高**（頂背離）
- 通常加 RSI 極值（>= 70）確認過熱
- 趨勢動能枯竭 → 預期反轉下跌

### 適合行情
1. 強勢多頭末端（趨勢將盡）
2. RSI 極值（過熱區）
3. MACD 柱狀體高位回落

### 不適合行情
- 趨勢中段（背離可能持續多次失敗）
- 盤整盤（無趨勢動能可衰竭）
- 強空頭中（無頂背離可抓）

---

## 三、Stage-1 4 段討論（待 user 確認）

### A. 內容（建議）
- **主週期**：60M（沿用 archive）
- **指標**：MACD(12,26,9) + RSI(14)
- **進場觸發**：
  - 價格新高（過去 N 根 K 棒最高）
  - MACD histogram 未同步新高（頂背離）
  - RSI ≥ 70 過熱確認
- **出場**：
  - TP at ATR × N（待 W0 後決定）
  - SL at ATR × N（待 W0 後決定）
  - Time stop

### B. 優點
- 逆勢 alpha source 跟其他 portfolio sleeves 結構性不同（L1/L5 趨勢、L4 假突破、S3_S 波動率突破）
- 高 WR potential（頂背離成立後反轉機率高）
- 60M 時框跟 S3_S 一致（chart setup 簡單）

### C. 缺點
- 逆勢策略 inherent risk: 趨勢延伸時連續 SL
- 背離判定 subjective（多個 lookback 方式）
- 頻率低（3-7 筆/月 = 50-100 筆/年），sample 需 6+ 年才足
- 原始 archive 只 2 筆，**alpha 真實存在性未驗證**

### D. 為什麼合適
- 補強做空 sleeve 厚度（用戶 2026-06-28 ruling 主旨）
- D 類動量逆勢，跟現有 4 隻做空（趨勢/盤整/波動率/反趨勢拉回）互補
- 跟 L1/L5 強勢多頭結構性對沖（多頭末端 = L1 SP 啟動時，S4_S 進場）

---

## 四、W0 Alpha Pre-Verify Plan（next step）

| Gate | 標準 |
|------|------|
| Trigger 頻率 | ≥ 5 instances/year（避 sample 不足）|
| 後續 N bar 方向 hit rate | ≥ 40% |
| Risk-reward ratio | ≥ 1.5 |
| 跨年穩定 | 至少 50% 年份有正 PnL |

### Python script TODO
1. Load TWII 60M data (2018-2026)
2. Compute MACD(12,26,9) histogram + RSI(14)
3. Detect 頂背離: price new high (lookback 20) AND MACD histogram 未新高 AND RSI>=70
4. Forward-test entry: shorts N bars later
5. Compute 4 gates

→ **FAIL → KILL with FINAL_VERDICT.md（不寫 .pla）**
→ **PASS → 進 W1 strategy.md + 4 段討論 lock**

---

## 五、相關文件

- Archive: `strategies/research/archive/batch01_S2-S5/TXF1_Strategies_Batch01.md` 策略 4
- Archive .pla: `strategies/research/archive/batch01_S2-S5/S4_MACDDivergence.pla`
- ROADMAP: `docs/policies/OFFICIAL_ROADMAP.md` Batch 01 S4_S
- Spec doc: 本檔
- Lessons reference: `docs/policies/STRATEGY_RD_SOP_v2.md` W0 gates
