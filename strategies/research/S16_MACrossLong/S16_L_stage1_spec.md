# S16_L MACrossLong — Stage -1 Strategy Discussion

**啟動日**：2026-07-10
**前置**：S16_S v1.0-PROD PROMOTED (2026-07-10)
**Roadmap 依據**：OFFICIAL_ROADMAP.md Batch 04 (R-6 拆分 Long 對照)
**規範**：必須通過 W0 → W1 → W2 → W3 → W4 → W5 → W6 完整流程
**設計原則**：**大方向鏡像 S16_S，但 Long-specific 邏輯調整 + 借鑑 S16_S 3 天開發教訓**

---

## 一、內容（策略一句話）

**在台指期 5 分鐘 K 線上，用 ZLEMA 雙均線黃金交叉搭配陡峭上升斜率過濾器抓極短動能爆發向上，2 小時內走完就退場，不適合的行情小虧不做。**

= G 類動量交叉（純多，鏡像 S16_S 空頭版）
= 「進場精挑細選，出場迅速果斷」的 Sniper 多頭

---

## 二、優點（**why alpha 應該存在**）

| # | 理由 |
|---|------|
| 1 | **TXF1 長期偏多 regime** → 順勢策略天然有利（vs S16_S 逆勢）|
| 2 | **補完 R-6 pair**：S16_S 已 promote，S16_L 完成後形成完整 hedge pair |
| 3 | **portfolio 補位**：與 S3_L (BB compression) 不同 trigger（動能 vs 波動率壓縮）|
| 4 | **5M sniper 時框**：portfolio 中只有 S16 系列是 5M 級別 |
| 5 | **S16_S 教訓可直接借鑑**：Layer 2 8 層 chain 完整 reusable，開發成本低 |
| 6 | **與 L1/L3/L5 多頭策略互補**（15-60M vs 5M 時框）|

---

## 三、缺點 / 風險

| # | 風險 | 嚴重度 |
|---|------|--------|
| 1 | **TXF1 崩盤快、rally 慢**：向上動能爆發次數可能少於向下 | 🔴 高 |
| 2 | **Bull regime whipsaw**：假突破後死叉 | 🔴 高 |
| 3 | **與 L1/L5 多頭 crossover 較高**：可能高 correlation | 🟡 中 |
| 4 | **Sharpe 通常不如 short 在 crash**（單筆 win 較小）| 🟡 中 |
| 5 | **熊市 whipsaw 保險成本**（鏡像 S16_S 的 Bull 保險成本）| 🟠 高 |
| 6 | **Long 策略在急殺中 gap 風險**（vs Short 在急漲的 gap）| 🟡 中 |

---

## 四、為什麼合適（roadmap + portfolio 角度）

| # | 理由 |
|---|------|
| 1 | **Rule R-6 純多拆分**：S16_S 完成必接 S16_L（**Roadmap 鐵則**）|
| 2 | **Portfolio identity 補位**：portfolio 缺「5M 短期動能純多 sleeve」 |
| 3 | **開發成本極低**：Layer 1/2/3 直接鏡像 S16_S，只改邏輯方向 |
| 4 | **Alpha 假設具體**：TXF1 動能異常 in both directions（已被 S16_S 部分驗證 short side）|
| 5 | **測試相關性**：S16_L + S16_S 相關性應該接近 0（一個做多、一個做空）|

---

## 五、與 S16_S 的核心差異對照表

| 面向 | S16_S (Short) | **S16_L (Long)** |
|------|-------------|--------------|
| 進場觸發 | Death Cross (Fast 跌破 Slow) | **Golden Cross** (Fast 突破 Slow) |
| MinSlope 定義 | `Fast[i-1] - Fast[i] > 28` (下跌) | **`Fast[i] - Fast[i-1] > 28`** (上升) |
| 部位方向 | sell short | **buy** |
| 出場 P4 | Golden Cross (死叉出場) | **Death Cross** (黃金反轉) |
| Rule #12 SetStopLoss | MP >= 0 | **MP <= 0** |
| SL 方向 | Entry + ATR*Mult | **Entry - ATR*Mult** |
| Loss 計算 | Close - Entry | **Entry - Close** |
| Profit 計算 | Entry - Close | **Close - Entry** |
| Regime 主場 | Bear + Volatile | **Bull + Volatile 起漲期** |
| 保險成本 | Bull whipsaw | **Bear 急殺** |

---

## 六、從 S16_S 3 天開發學到的**必須避免陷阱**

### 🚨 教訓 1 — 不要走 v0.4/v0.6 走過的彎路

| 陷阱 | S16_S 走過 | S16_L 直接跳過 |
|------|--------|------------|
| Slow 太遠（例 90） | v0.4 Slow=90 走偏 | ✋ **強制 Slow ≤ 50-70** |
| ATR 混淆方向與波動 | v0.6 走偏 | ✋ **絕不用 ATR 作 slope filter** |
| MinSlope 用比值 | 討論過拒絕 | ✋ **純點數** |

### ✅ 教訓 2 — 直接沿用 S16_S 已驗證的架構

- Layer 2 8 層 priority chain（**完整鏡像**，只改方向）
- Layer 3 Option A（**不加 Regime Filter**）
- Layer 1 M2/M3/M4 DROP（5M 時框承擔不起延遲）
- Sniper-adapted 5 件套標準（**確認可用**）

### 🎯 教訓 3 — Rule 命名 & 檔案結構

- 用 `SE_MA_` / `SX_MA_` 前綴？ → **改用 `LE_MA_` / `LX_MA_`**（Long entry/exit convention）
- 資料夾 `S16_MACrossLong/`（已建）
- Signal Name: `STRATEGY_GEN_S16_L_MACrossLong`

---

## 七、預期挑戰（W0 前必知）

1. **Alpha 可能不對稱**：TXF1 momentum burst 向上可能比向下少（crash 快、rally 緩）
2. **可能與 L1/L3/L5 高相關**：需要 Portfolio Correlation 驗證
3. **Whipsaw 可能更嚴重**：多頭中的短暫死叉極多
4. **W0 daily proxy 可能表現不如 S16_S**（S16_S W0: 40/216 combos 4/4 PASS）
5. **v0.5 config 直接鏡像**可能不 optimal（Long 動能特性不同）

---

## 八、初步 W2 参數估計（Stage -1 hint，實際等 W4 GA）

**若鏡像 S16_S v1.0-PROD**：

| Input | 鏡像 v0.5 值 | Long 版本可能調整 |
|-------|-----------|---------------|
| ZLEMA_Fast | 25 | 可能相同或更小（Long 需要更敏感）|
| ZLEMA_Slow | 70 | 可能相同 |
| MinSlope | 28 pts (上升) | **可能較小**（Long 動能 typically 較小）|
| QuickStop_MaxLoss_Pts | 60 | 相同 |
| MaxHoldingBars | 24 (2hr) | 可能較大（rally 較慢）|
| StopATRMult | 4.0 | 相同 |

**注意**：v0.5 sniper config 是 for TXF1 空頭 momentum burst，Long 版本**必須重新 GA optimize**（不能直接鏡像）。

---

## 九、開發 Roadmap（沿用 S16_S 前例）

### Stage -1（**本文，等用戶確認**）
- 寫 4 段策略討論 → 等 GO/NO-GO

### W0 Alpha Pre-Verify（下一步）
- Python daily proxy on TWII
- **注意**：改抓「Golden Cross + 上升 slope」
- 判準：4 gates（trigger freq / Forward hit rate / RR / stability）
- **若 W0 FAIL** → KILL S16_L with FINAL_VERDICT.md

### W1-W6（依 S16_S 前例）
- W1: strategy.md（機構級 14 章）
- W2: .pla（鏡像 S16_S code 結構，改方向）
- W3: MC12 baseline backtest
- W4: GA optimization + WFA
- W5: Sniper-adapted 5-piece validation
- W6: Promote 決策

---

## 十、Alpha Hypothesis（W0 前明確化）

**假設**：TXF1 5M 級別上，Golden Cross + MinSlope > X pts 上升動能 = 可信賴的 momentum burst 起漲信號

**測試方法**：
- TWII daily proxy 尋找 Golden Cross 後 N 個交易日的向上 momentum
- 判定：avg return / hit rate / cross-year stability

**Alpha 存在證據**：
- Momentum anomaly 學術根基普世（Jegadeesh & Titman 1993 對 long side 有效）
- CTA 業界 long trend-following 廣泛使用
- S3_L VolSqueezeLong 已驗證台指多頭波動率壓縮 alpha 存在
- **S16_S 已證明短側動能有效** → **對稱情況下長側也應存在**

---

## 十一、等用戶 ruling

### 3 個關鍵決策點

**A**：**照鏡像 S16_S 大方向 + 借鑑教訓直接進 W0**（**推薦**）
**B**：**先修改設計方向**（例如加 trend filter？改時框？）
**C**：**討論 4 段內容有需要調整**

**若選 A**：Auto mode 進 W0 Python script → daily proxy 驗證 alpha
**若選 B/C**：先深化討論

---

## 十二、Rule #16 五支柱 checklist

- Rules：Rule #14 R-6 拆分（S16 Batch 04 已寫入）
- Context：本文 + S16_S 完整開發歷程可 reference
- Verification：等 W0 Python + W2 ASCII verify + W3 MC12 backtest
- Memory：對齊 `reference_strategy_rd_sop` (SOP v2)
- Format：Stage -1 spec md（本檔）+ 未來 W0-W6 documents

---

**End of Stage -1 Spec — 2026-07-10 Desktop**

**Ready for user GO/NO-GO decision.** 🎯
