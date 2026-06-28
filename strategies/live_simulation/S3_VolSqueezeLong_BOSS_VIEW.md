# S3_L VolSqueezeLong — 老闆快速 View

**版本** v1.1（Phase 3 best params locked）｜ **回測** 2020-01 ~ 2026-06（6.4 年）｜ **狀態** ✅ live_simulation（5% portfolio cap）

---

## 📊 績效重點

| 指標 | 數值 |
|------|-----|
| **淨利** | **+2,654,000 NTD** |
| **獲利因子 (gross)** | **2.55** |
| **獲利因子 (含滑價)** | **2.00** ⭐ |
| **Sharpe (年化)** | **1.02** ⭐ |
| **Sortino** | 0.84 |
| **勝率** | 53.0% |
| **最大回撤 (equity)** | -13.1%（vs initial -23.7%）|
| **交易筆數** | **134 筆 / 6.4 年** ≈ 21 筆/年 |
| **vs Buy&Hold** | 1.07x overtake ⭐ |

---

## 💰 賺什麼錢

**賺「波動率壓縮後向上爆發」的長期波段錢** — Bollinger BandWidth 壓縮到 20 百分位（vol cycle 底部），收盤突破上軌做多，吃完整 vol expansion 向上段。
**TargetATR 8.0 遠 TP** = 抓大波段而非短打。

---

## ✅ 適合行情

1. **多頭強勢日**（PF 3.28）
2. **vol expansion 向上 event**（FOMC / CPI / Trump 推文）
3. **趨勢年延伸**

## ❌ 不適合行情

- **區間盤**（PF 0.46，N=11 邊際）
- **vol 向下 expansion**（Long-only 方向成本）
- **空頭盤**

---

## 🎯 進場規則

1. **BBW 百分位 ≤ 20%**（壓縮條件）
2. **收盤突破 Bollinger 上軌**（向上爆發）
3. **非結算日 + 非假日尾段**
4. **冷卻期 1 天 + 同日最多 1 筆**

---

## 🚪 出場規則

| 優先級 | 情境 | 動作 |
|------|------|-----|
| P0 | Kill / Registry / Holiday / Settlement | 強制 |
| 1 | **TP**（Entry + 8.0 × ATR）| 遠目標 |
| 2 | **MidExit**（Entry + 3.0 × ATR, 3 根後）| 37% 出場 |
| 3 | **SL**（Entry - 2.75 × ATR Frozen）| 兜底 |
| 4 | **TimeStop**（70 根 60M ≈ 4.3 小時）| 時間 |

---

## 🛡 風控

- **Portfolio cap：≤ 5%**（隔離單 sleeve tail risk）
- **配對 S3_S** 形成 R-6 hedge pair（已上線 2026-06-28）
- **L24 鎖**：不可加 event filter、不改方向、不縮 TargetATR

---

## 🎯 一句話 pitch

> **「波動率壓縮後向上爆發長尾捕手 — 6.4 年 +265 萬、PF 2.55、Sharpe 1.02、Beat B&H 1.07x。」**

---

## 📋 老闆決策摘要

| 問題 | 答 |
|------|-----|
| 這策略幹什麼？| 抓波動率壓縮後向上爆發的長尾 |
| 多久進一次？| ~21 筆/年（中低頻）|
| 每筆賺多少？| 平均 +19.8K |
| 最大會虧多少？| MDD -23.7% / 單筆 tail -124K（Trump 2026-04-02 gap）|
| 跟其他策略衝突？| 配對 S3_S 形成 R-6 hedge 完整 directional pair |
| 為什麼上架？| Sharpe 1.02、PF 2.00（含滑價）、Beat B&H、機構級合格 |
| 風險？| 區間盤 PF 0.46 / 2024 Q3-Q4 DD cluster -174K / 單筆 tail -12.4% 帳戶 |

---

**詳細**：見 `S3_VolSqueezeLong_annotated.md` + `S3_VolSqueezeLong_DEPLOYMENT.md`
