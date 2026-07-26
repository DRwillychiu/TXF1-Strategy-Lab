# S1 NightMomentum — 老闆快速 View

**版本** v2.6 + Entry Trend Filter + ImmediateStop + HolidayFlat_v3 ｜ **回測** 2020 ~ 2026（6.5 年）｜ **狀態** ✅ live_simulation

---

## 📊 績效重點

| 指標 | 數值 |
|------|-----|
| **淨利** | **+1,720,600 NTD** (v2.4 baseline) |
| **v2.6 預期** | ~+2,000K ~ +2,200K |
| **獲利因子** | 1.42 (v2.4) |
| **最大回撤** | -270K |
| **交易筆數** | **783 筆 / 6.5 年** ≈ 120 筆/年（高頻夜盤）|

---

## 💰 賺什麼錢

**賺「夜盤突破 + 隔日跳空向上 gap」錢** — 夜盤多頭結構成立做多，跨夜捕捉隔日開盤 gap up。
v2.3 揭露：純夜盤淨利僅 +402K，**隔日 gap 貢獻 +1,318K（+12.6 點/筆系統性正向 gap）**。

---

## ✅ 適合行情

1. **夜盤多頭結構成立的日子**
2. **隔日開盤跳空向上**
3. v2.6 Trend Filter 加強 entry quality

## ❌ 不適合行情

- **弱勢盤**（夜盤無結構力道）
- **假日多日跨度 gap**（不確定性高，強制提早平倉）

---

## 🎯 進場規則

1. **時段** Time < 05:00（純夜盤）
2. **夜盤突破**：Night Session close > highest 最近 N 根
3. **非假日尾段**（63 筆登錄表）
4. **非結算日**
5. **v2.6 Trend Filter gate**（0=off / 1=Vol ratio / 2=Vol+Daily MA / 3=All）

---

## 🚪 出場規則

| 優先級 | 情境 | 動作 |
|------|------|-----|
| P0 | Kill / Holiday / Settlement | 強制 |
| 1 | **09:00 Time exit**（gap 捕捉）| 鎖隔日跳空 |
| 2 | **SL** (Entry - 2.75 × ATR) | 初始保護 |
| 3 | **TP** (Entry + 2.0 × ATR) | 目標 |
| - | v2.5 Trail | ❌ 已放棄（證實對短週期 momentum 無效）|

---

## 🛡 風控

- 單口 ｜ 夜盤型 sleeve（與其他日盤策略時段分工）
- v2.6 改走 entry 端 Trend Filter，不再碰 mid-position 保護
- **教訓 L20**：v2.5 Trail B -385K 災難證實「entry quality > mid-position protection」

---

## 🎯 一句話 pitch

> **「夜盤突破 + 隔日 gap up 捕手 — 6.5 年 +172 萬，靠 +12.6 點/筆系統性 gap alpha。」**

---

## 📋 老闆決策摘要

| 問題 | 答 |
|------|-----|
| 這策略幹什麼？| 抓夜盤突破 + 跨夜 gap up |
| 多久進一次？| ~120 筆/年（高頻）|
| 每筆賺多少？| 平均 +2.2K（含 gap 補貼）|
| 最大會虧多少？| MDD -270K |
| 跟其他策略衝突？| 純夜盤，與所有日盤策略時段分工 |
| 為什麼上架？| 6.5 年實證 +172 萬，夜盤 alpha 獨有 |
| 風險？| 假日 gap 不可預測 / Trail 試錯歷史 / 預期 portfolio 10-15% cap |

---

**詳細**：見 `S1_NightMomentum_annotated.md`
