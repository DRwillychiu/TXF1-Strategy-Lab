# Lesson L24 — Risk Overlay 不可削 Alpha Source

**Codified**：2026-06-23
**起源**：S3_L VolSqueezeLong W5 institutional eval 過程
**用戶 ruling**：「波動率壓縮策略的本意，本身就會涉及到重要經濟數據公布所產生的波動行情。所以本質上，應該是要去享受波動才對。」
**Lessons 編號**：累計 **L1-L24**（L1-L23 詳見 `docs/archive/offRoadmap_2026Q2/`）

---

## 核心規範

**設計 risk control 時，絕不可削掉 alpha source。**

任何 strategy-level 修補若會切斷策略的 alpha 來源市場 → **拒絕**。
所有 macro / event tail risk → **portfolio-level 解決**（sizing / diversification）。

---

## Why（規範起源）

### 案例：S3_L VolSqueezeLong 2026-04-02 -124K 事件

| 事件 | 數據 |
|------|------|
| Entry | 2026-04-01 13:45 LE_VS_Entry @ 33,332 |
| Exit | 2026-04-02 10:45 LX_VS_SL @ 32,721 |
| Loss | -124,200 NTD (12.4% 帳戶) |
| Catalyst | 川普 Liberation Day Reciprocal Tariff（台北 4/2 早 4:00）|

### 我（Claude）的錯誤提議

看到 single trade tail -124K，建議「加 Pre-event Flat 模組」（FOMC / CPI / 關稅日 registry → 前一日全 flat）來防止類似事件。

### 用戶 push back（決定性論證）

> Vol Squeeze 策略的 alpha 本質：偵測 BBWidth 極度壓縮 → 等待突破 → 賺 vol expansion 利潤。  
> **Vol expansion 的 catalyst 就是這些 macro events**。  
> Filter 掉 events = self-defeat alpha = 把 alpha 跟風險一起切掉。

### 為什麼錯誤

| 維度 | Pre-event Flat | 真實本質 |
|------|---------------|--------|
| 我以為的本質 | Risk control | **削 alpha** |
| 過擬合風險 | 看起來 "forward policy" | **hindsight bias**（基於 single 事件後反推）|
| 對策略 | 防虧損 | **拒絕策略應賺的市場** |
| 對 alpha | 中性 | **直接切斷 alpha source** |

### 2026-04-02 真實本質（修正解讀）

不是 alpha 失敗，是 **方向不對稱**：
- Vol expansion event = 策略正確抓到訊號
- 方向向下 = Long-only 設計的固有 cost
- 真正 hedge 是 **R-6 對手策略**（S3_S VolSqueezeShort），不是 strategy-level filter

---

## How to Apply

### 設計 risk control 前的必問

> 「這個 control 會不會削我們策略的 alpha source？」

| 答案 | 動作 |
|------|------|
| ✅ 不會（純機械 / portfolio level） | 允許 |
| ⚠️ 可能會 | 重設計或拒絕 |
| ❌ 會 | **拒絕** |

### 區分判斷表

| 例子 | Alpha source? | Verdict |
|------|-------------|---------|
| Settlement_Flat（結算日 flat）| 結算 vol 不是 strategy alpha（是 idiosyncratic risk）| ✅ 允許 |
| Holiday_Tail（假日前 flat） | 假日 gap 不是 alpha source | ✅ 允許 |
| Manual_Kill_Switch | 不削 alpha（手動 emergency）| ✅ 允許 |
| Position Sizing 降低 | 純機械，不 predict 任何 event | ✅ 允許 |
| **FOMC event flat (vol breakout 策略)** | **FOMC 就是 vol expansion catalyst = alpha source** | ❌ **拒絕** |
| **CPI release flat (vol breakout 策略)** | **CPI 就是 vol expansion catalyst** | ❌ **拒絕** |
| **NFP day flat (momentum 策略)** | **NFP 是 momentum 觸發** | ❌ **拒絕** |
| 結算週 flat (mean reversion 策略) | 結算 vol 不是 mean reversion alpha source | ✅ 允許 |

### 如何替代 strategy-level filter

當看到 single bad trade event 想加 filter，先停下來，改用以下：

1. **Position Sizing 降低**（純機械，零過擬合）
2. **Portfolio allocation cap**（不動 strategy）
3. **R-6 配對開發**（用對手策略 hedge directional risk）
4. **Portfolio diversification**（多 sleeve 攤平）
5. **Accept tail as design cost**（明確 disclose）

---

## 案例對照

### ✅ 正確套用 L24 — S3_L promote 決策

S3_L 帶 single trade tail 12.4% account → 我們選擇：
- ✅ Portfolio 5% cap
- ✅ 啟動 S3_S 開發補完 R-6
- ✅ 不加 Pre-event Flat
- ✅ Accept directional cost as R-6 split design cost

結果：**S3_L promoted to live_simulation with intact alpha source**。

### ❌ 反例 — 假設場景

若當初我加 Pre-event Flat：
- 在 FOMC / CPI / 關稅日全 flat
- 看似 backtest DD 從 -124K 降到 -40K → 自以為更安全
- **實際上**：
  - 切掉 ~30-50% vol expansion events = alpha source 大砍
  - PF 從 2.55 可能跌到 1.3
  - OOS performance 不明（無法 forward verify）
  - **策略本質被破壞**

---

## 跟 L18 (Recent Bias) / L23 (Sign Flip) 區別

| Lesson | 規範 | 對 strategy 行動 |
|--------|------|---------------|
| L18 | Recent bias = real alpha 還是 lucky? | 多 sub-period check |
| L23 | Sub-period sign flip = 結構性 alpha 死亡 | AUTO-KILL |
| **L24** | **Risk overlay 削 alpha source = 違規** | **拒絕修補，用 portfolio 解** |

L18 / L23 是 **alpha 真實性檢測**；L24 是 **alpha 保護規範**。

---

## 連結

- **S3_L W5 eval**: [`strategies/research/S03_VolSqueezeLong/W5_10dim_evaluation.md`](../../strategies/research/S03_VolSqueezeLong/W5_10dim_evaluation.md)
- **S3_L deployment manifest**: [`strategies/live_simulation/S3_VolSqueezeLong_DEPLOYMENT.md`](../../strategies/live_simulation/S3_VolSqueezeLong_DEPLOYMENT.md)
- **S3_S README** (R-6 對手): [`strategies/research/S03_VolSqueezeShort/README.md`](../../strategies/research/S03_VolSqueezeShort/README.md)
- **OFFICIAL_ROADMAP** (R-6 規則): [`docs/policies/OFFICIAL_ROADMAP.md`](OFFICIAL_ROADMAP.md)
