# S3_S VolSqueezeShort — Bollinger BandWidth Squeeze Breakout (R-6 Short half)

**啟動日**：2026-06-23
**狀態**：📋 **Stage -1 策略討論階段**（pre-W0）
**前置**：[S3_L VolSqueezeLong](../S03_VolSqueezeLong/) 已 W5 PASS + Promoted (2026-06-23)
**R-6 對手**：S3_S 是 S3_L 的鏡像，補完 vol expansion 雙向 capture
**Roadmap 依據**：[../../../docs/policies/OFFICIAL_ROADMAP.md](../../../docs/policies/OFFICIAL_ROADMAP.md) batch01 — S3_S
**原始概念檔**：[../archive/batch01_S2-S5/S3_VolSqueeze.pla](../archive/batch01_S2-S5/S3_VolSqueeze.pla) (原雙向 spec 的 short 部分)
**原始說明**：[../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md §策略3](../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md)

---

## 🎯 Stage -1 — 用戶必讀策略討論（按 SOP v2 Enforcement）

### 1. 內容（策略一句話）

**Bollinger BandWidth 降至 30 百分位 → 波動率極度壓縮 → 收盤跌破下軌 → 做空，賺 vol expansion 向下方向的趨勢利潤。**

= C 類波動率型策略（鏡像 S3_L）
= 賺壓縮 → 擴張的方向性突破（向下版）

### 2. 優點（為什麼這 alpha 應該存在）

| # | 理由 |
|---|------|
| 1 | **直接 hedge S3_L 的 directional cost** — S3_L 在 2024 Q3-Q4 與 2026-04-02 虧錢的環境，S3_S 應該賺 |
| 2 | **Vol expansion 不對稱**：bad news 比 good news 更快、更暴力（panic > FOMO）→ short side breakout 動能通常 > long side |
| 3 | **Vol squeeze 物理本質中性**：壓縮後爆發方向 50/50（短期），純做多吃半邊太可惜 |
| 4 | **TXF1 重大 macro shock 多向下**：FOMC 緊縮 / 央行干預 / 川普關稅 / 地緣戰爭 / 美股 limit down → 全是 down catalyst |
| 5 | **Portfolio Sharpe > 單 sleeve Sharpe**：S3_L + S3_S 組合即使 S3_S 單獨 Sharpe < 1，hedge value 仍可推升 portfolio metric |
| 6 | **Lesson L24 直接動機**：用 R-6 配對做 directional hedge，不用 strategy-level filter 削 alpha |

### 3. 缺點 / 風險

| # | 風險 | 嚴重度 |
|---|------|--------|
| 1 | **TXF1 長期偏多 regime** → short bias 結構不利 | 🔴 高 |
| 2 | **Dead cat bounce**：短暫破下軌後反彈會打停損 | 🔴 高 |
| 3 | **Bear regime 樣本少**（2020-2026 只 2022 全年 + 2024 H2 短暫）→ 樣本不足 | 🟡 中 |
| 4 | **Squeeze 後若向上爆發** → S3_S 直接 SL | 🟡 中 |
| 5 | **Short 滑價通常 > Long**（夜盤跳空向上 vs 向下 asymmetry）| 🟡 中 |
| 6 | **單獨 Sharpe 可能 < 0.5**（fail 機構 gate）→ 必須靠 portfolio 配對 justify | 🟡 中 |
| 7 | **可能 S3_S 跟 S3_L 高 correlation**（共用 squeeze trigger）→ hedge 效果有限 | 🟢 低（待驗證）|

### 4. 為什麼合適（portfolio + roadmap 角度）

| # | 理由 |
|---|------|
| 1 | **OFFICIAL_ROADMAP R-6 鐵則**：S3_L 完成必拆 S3_S（用戶 2026-06-22 ruling）|
| 2 | **S3_L promote 條件**：5% portfolio cap + 等 S3_S 配對 = S3_S 不開發則 S3_L 永遠帶 directional cost |
| 3 | **Lesson L24 應用**：directional hedge 必用 R-6 配對，不用 strategy-level event filter |
| 4 | **既有 portfolio short sleeves 不足**：L2 (trend short) / L4 (range short) / S3_RPS (pullback short)，缺 vol expansion short → S3_S 填補空缺 |
| 5 | **R-6 鏡像對稱**：S3_L .pla 已 validate full institutional flow，S3_S 結構 90% reuse → 開發成本低 |
| 6 | **Verify hypothesis**：archive 原始 S3 是雙向 spec，long 側已證有 alpha (PF 2.55)；short 側值得驗證 |

### 5. 預期挑戰（pre-W0 已知）

- W0 alpha pre-verify 可能直接 KILL（若 short side alpha 不存在）
- TXF1 偏多 bias 預期 OOS Sharpe 比 S3_L 低
- 需要設計「only short when bearish regime」filter 還是「always squeeze trigger」(後者更純，但虧更多)
- Frozen SL 計算公式需鏡像 (Long 用 BB_Btm - ATR×k，Short 用 BB_Top + ATR×k)
- Mid exit 邏輯鏡像（短倉 mid line = 中軌，碰回是空轉多 trigger）

---

## 等用戶確認 Stage -1 後才進 W0

按 SOP v2 + Lesson L24：**Never make a decision the user couldn't explain to their board**。

用戶必須確認上述 4 段（內容 / 優點 / 缺點 / 為什麼合適）後，才進 W0 alpha pre-verify。

---

## 開發路線（嚴格遵守 SOP v2）

### Stage -1：策略討論（本檔，**現在**）
- 寫策略 4 段 → 等用戶 GO / NO-GO

### Phase W0：Alpha Pre-verify（pre-code）
- `scripts/analyze_s3s_volsqueeze_short_preverify.py`
- 用 TXF1 60M 真實資料驗證：
  - BBW < 30 pctile 後**跌破下軌**的發生頻率
  - 突破下軌後 N bar 內 ATR×N 向下命中率
  - vs 向上反彈反向命中率（驗證是否多多）
  - 跟 S3_L 訊號的時間 correlation（避免共線性）
- **若 alpha 不存在 → 立即 KILL（不寫 .pla）**

### Phase W1：策略文件
- `S3_VolSqueezeShort_strategy.md`（機構級規格）
- `S3_VolSqueezeShort_annotated.md`（中文逐段註解）

### Phase W2：.pla 實作
- `S3_VolSqueezeShort.pla`（鏡像 S3_L 結構，補完所有 Rule #11/12/13/14）
- `scripts/verify_s3_volsqueeze_short.py`

### Phase W3：MC12 baseline backtest
- 60M TXF1 2020-2026
- 用 archive 預設值或 S3_L 鏡像 inputs
- 純 design_spec 中位值，不開 GA

### Phase W4：Walk-Forward
- IS 2y / OOS 6m / step 6m (S3_L 同 setup)
- WFE > 50%

### Phase W5：10 維度評估 + 晉升 live_simulation
- **特別關注**：S3_S × S3_L correlation（必算）→ 確認 hedge 真實
- 配對 portfolio Sharpe vs 單 sleeve Sharpe

---

## 開發紀律（從 S3_L 學到 + 新教訓）

```
S3_S 開發必須遵守：
1. ✅ Stage -1 先做完（不可跳過）
2. ✅ W0 alpha pre-verify 必跑（KILL gate）
3. ✅ Mirror S3_L 結構：90% 可 reuse (Section 0 Holiday, Settlement, etc.)
4. ✅ Time 條件閉區間（MC Time 24hr 規則）
5. ✅ Cooldown_Days 同 S3_L (= 1)
6. ✅ SL/TP 從 short side MFE 統計推導（不可直接用 S3_L 數字）
7. ✅ 不可加 Pre-event Flat（L24, alpha source 不可削）
8. ✅ Single trade tail 風險接受（portfolio level 配對解決）
9. ✅ 不可發明新策略名稱
10. ✅ S3_S 完成後立即進 S4_L (MACDDivergenceLong，原始 batch01 下一個)
```

---

## 下一步

**等用戶 confirm Stage -1 → 啟動 W0 alpha pre-verify。**
