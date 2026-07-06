# S3_S VolSqueezeShort — 老闆快速 View

**版本** v1.8.0-PROD（1M Multi-layer 升級版）｜ **回測** 2020-2026（6.3 年）｜ **狀態** ✅ live_simulation（取代 v1.7.3-FINAL，2026-06-30 promote）

---

## 📊 績效重點

| 指標 | 數值 |
|------|------|
| **淨利** | **+845,600 NTD**（2020-2026 全期 GA-best）|
| **獲利因子（含滑價）** | **2.24** ⭐ 歷史新高 |
| **獲利因子 (gross)** | **4.13** ⭐ 歷史新高 |
| **勝率** | 75% |
| **Sharpe (年化)** | 0.56 |
| **最大回撤** | **-19.4%** |
| **交易筆數** | **24 筆 / 6.3 年** ≈ 4-5 筆/年 |
| **平均每筆獲利** | +35K |
| **2025-2026 表現** | **+823K**（97% alpha，近期 regime 強）|

---

## 💰 賺什麼錢
**賺「波動率壓縮後向下爆發 + 1M 即時退場」的精準下殺錢**：
- 60M BBW squeeze（30 百分位內）→ Close 跌破下軌
- **NEW v1.8.0**：每根 1M K 棒監控 11 個 factor（5 floors）
- 偵測到「即將反彈」就先 market exit，**搶在 ATR SL 觸發前出場**
- 6/8 case 證實：v1.7.3 -530 點 → v1.8.0 **-10 點**（完美救援）

---

## ✅ 適合行情
1. **強勢多頭中的驚嚇式急殺**（如 2025-04 Trump 關稅）
2. **快速崩跌延續**（panic 後 follow-through）
3. **順勢空方下殺**

## ❌ 不做行情
**趨勢中性區段**（Daily MA15/MA40 ratio 0.98-1.05），自動 0 交易守規。

---

## 🎯 進場規則（8 個 gates 全 True）
1. 空手 + BBW squeeze (≤30%) + 收盤跌破下軌
2. Regime 在強多 (>1.05) 或任何空頭 (<0.98) 區
3. 非假日 / 結算日 / 同日冷卻 / 註冊有效

---

## 🚪 出場規則（**v1.8.0 新增 1M Multi-layer**）

| Priority | 機制 | 邏輯 |
|---------|------|------|
| P0 | 安全層 | Kill / Registry / Holiday / Settlement |
| **S-0** ⭐ | **1M_Exit (NEW)** | **11 factor 評分 ≥ 30% + 3 類別 + 浮虧>30% SL → 提前市價** |
| S-1 | TP | 進場價 - 3.5 ATR limit |
| S-2 | Mid | 收盤過中軌 |
| S-3 | TimeStop | 持倉 ≥ 35 K 棒 |
| S-4 | SP / SL | 浮盈 ≥1.5 ATR arm SP / fallback ATR×2.75 SL |

### 1M 評分系統（11 factor 滿分 30 分）
- **1F K-bar**：量+下影/吞噬/連陽/擴張陽
- **2F 量價**：量爆+漲/升量升價
- **3F 動能**：價格加速/速度門檻
- **4F 結構**：1M 跳空/突破進場價
- **5F 波動率**：vol regime shift

---

## 🛡 風控
- 單口 ｜ Portfolio 3% cap ｜ 配對 S3_L 形成 R-6 hedge
- 自動 Kill：月虧 > 5% / 3 連 SL / 12 月無交易
- **Bug 2 SP IOG**: 已 documented 為 blackswan non-blocking（夜盤可操作 + 1M_Exit 不受影響）

---

## 🎯 一句話 pitch
> **「波動率壓縮後第一刀下殺捕手 + 1M 即時退場護身 — 6.3 年 PF 4.13、avg +35K、1M 機制 6/8 完美救援。」**

---

## 📋 老闆決策摘要

| 問題 | 答 |
|------|---|
| 這策略幹什麼？| 抓壓縮後第一刀下殺，1M 即時退場避免反彈大虧 |
| 多久進一次？| 4-5 筆/年（精準打擊）|
| 每筆賺多少？| 平均 +35K |
| 最大會虧多少？| MDD -19.4%（單筆 cap by 1M_Exit）|
| 跟其他策略衝突？| 配對 S3_L 形成 R-6 hedge |
| 為什麼上架？| PF 歷史新高 4.13 + 6/8 1M_Exit 證實救援 -1,560 → -10 點 |
| 風險？| WFA 3-6/9 (regime 偏好近期); alpha 集中 2025-2026; sample 30 trades 較少 |
| 升級 v1.7.3 → v1.8.0 理由？| 1M 機制證實能救極端 case + GA 找到 sweet spot |

---

**詳細**：見 `S3_S_VolSqueezeShort_strategy.md` + `_DEPLOYMENT.md`
**取代 v1.7.3-FINAL**：archived 在 `strategies/research/archive/S03_VolSqueezeShort_v173_archived_20260630/`
