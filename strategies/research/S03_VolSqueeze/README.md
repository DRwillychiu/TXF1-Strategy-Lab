# S3 VolSqueeze — Bollinger BandWidth Squeeze Breakout (原始排程)

**啟動日**：2026-06-22
**狀態**：📋 **W0 Pre-verify 階段**（pre-code）
**Roadmap 依據**：[../archive/README.md](../archive/README.md) batch01_S2-S5 — S3 = VolSqueeze
**原始概念檔**：[../archive/batch01_S2-S5/S3_VolSqueeze.pla](../archive/batch01_S2-S5/S3_VolSqueeze.pla)
**原始說明**：[../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md §策略3](../archive/batch01_S2-S5/TXF1_Strategies_Batch01.md)

---

## 一、策略一句話

**Bollinger BandWidth 降至歷史 20 百分位 → 波動率壓縮即將爆發 → 突破上/下軌進場順勢**

= C 類波動率型策略
= 賺壓縮 → 擴張的方向性突破

---

## 二、為什麼是 S3（roadmap 依據）

原始 batch01 排程：S2 InsideBarBreak / **S3 VolSqueeze** / S4 MACDDivergence / S5 SettlementWeek

之前桌機端誤將 "S3 RapidPullbackShort" 當作 S3，已歸檔至：
- 生產 .pla → `strategies/live_simulation/S3_RapidPullbackShort.pla`
- 設計歷史 → [../archive/S03_RapidPullbackShort_archived_20260622/](../archive/S03_RapidPullbackShort_archived_20260622/)

---

## 三、原始規格快照（從 archive/batch01）

| 項目 | 內容 |
|------|------|
| 類別 | C 類（波動率型） |
| 方向 | ★ 雙向（多 + 空） |
| 主週期 | 60 分鐘 |
| 進場（多） | BBW ≤ 過去 120 期的 20 百分位 + 收盤 > BB 上軌 |
| 進場（空） | 同 BBW 條件 + 收盤 < BB 下軌 |
| 出場 SL | ATR(14) × 1.5 |
| 出場 TP | ATR(14) × 3.0 |
| 中軌出場 | 進場後 ≥3 根 K + 收盤回穿 MA |
| 時間出場 | 持倉 > 40 根 K |
| 預期頻率 | 每月 4-8 筆 |

---

## 四、原始日線代理回測結果（不可信，需 60M 重測）

| 指標 | 值 |
|------|-----|
| 交易數 | 33 |
| 勝率 | 36.4% |
| **PF** | **0.88** ❌ |
| 淨利 | -115,622 NTD |
| MDD | -645,467 NTD |

註：原始評語「日線回測虧損。此策略設計在 60M 週期運行，日線上 BB 收縮訊號特性不同。務必在 MC12 用 60M 數據重新回測。」

---

## 五、現行規範差距（必須補完，不可缺）

| # | 規範 | 原始 .pla 狀態 |
|---|------|---------------|
| #11 | Settlement_Flat 7 元素 | ❌ 需補 |
| #12 | P3b SetStopLoss | ❌ 需補 |
| HolidayFlat_v3 | 假日前平倉 + Registry | ❌ 需補 |
| IOG=false 宣告 | ❌ 需補 |
| Manual_Kill_Switch | ❌ 需補 |
| Registry_Valid_Until | ❌ 需補 |
| MC Time 24hr 閉區間 | ❌ 需補 |
| Label 命名 (LE_VS_/SE_VS_) | ✅ 已合規 |

→ 原始 73 行 .pla 將升級到約 600-700 行（對齊 L1-L5 層級）。

---

## 六、開發路線（嚴格遵守）

### Phase W0：Alpha Pre-verify（**現在**）
- 寫 `scripts/analyze_s3_volsqueeze_preverify.py`
- 用 TXF1 60M 真實資料驗證：
  - BBW < 20 百分位的發生頻率（是否有足夠樣本）
  - Squeeze 後突破上/下軌的 N bar 內 ATR×3 命中率
  - vs ATR×1.5 反向命中率
- **若 alpha 不存在 → 立即 KILL（不寫 .pla）**

### Phase W1：策略文件
- `S3_VolSqueeze_strategy.md`（機構級規格）
- `S3_VolSqueeze_annotated.md`（中文逐段註解）

### Phase W2：.pla 實作
- `S3_VolSqueeze.pla`（補完 7 個規範缺口）
- `scripts/verify_s3_volsqueeze.py`

### Phase W3：MC12 baseline backtest
- 60M TXF1 2020-2026
- 對齊 inputs 預設值
- 純 design_spec 中位值，不開 GA

### Phase W4：Walk-Forward
- IS 2020-2024 / OOS 2025-2026
- WFE > 50%

### Phase W5：10 維度評估 + 晉升 live_simulation

---

## 七、開發紀律（從 S3 RapidPullbackShort 學到的教訓）

```
S3 VolSqueeze 開發必須遵守：
1. ✅ 先 W0 alpha pre-verify，後寫 .pla（不再設計超前實證）
2. ✅ 任何 filter 必須做重疊度 + 通過率雙重檢查
3. ✅ Time 條件必須閉區間（MC Time 24hr 規則）
4. ✅ 從一開始決定雙向 vs 單向（原始為雙向）
5. ✅ SL/TP 倍率必從 MFE 統計推導
6. ✅ 同日多進場必有 cooldown
7. ✅ 與 Buy and Hold 對比作為現實檢驗
8. ✅ MC 真實回測前不可宣稱 alpha 真實
9. ✅ 不可發明新策略名稱／不可偏離 archive/ 原始排程
10. ✅ S3 完成後立即進 S4 MACDDivergence（原始排程下一個）
```

---

## 八、下一步

等用戶決定要走哪條 alpha pre-verify 路徑（W0 開始）。
