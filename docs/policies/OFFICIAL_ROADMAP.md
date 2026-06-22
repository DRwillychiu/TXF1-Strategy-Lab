# OFFICIAL ROADMAP — 原始策略開發排程（強制鎖定）

**建立日**：2026-06-22
**狀態**：🔒 **LOCKED — 不可偏離，不可發明新策略名稱**
**起源依據**：[strategies/research/archive/README.md](../strategies/research/archive/README.md) batch01-03

---

## 一、為什麼鎖定排程

### 歷史教訓（2026-06-19 ~ 06-21）

桌機端 ultracode session 偏離原始 archive 排程，自行發明：
- S3 RapidPullbackShort（取代原本 VolSqueeze）→ 已部署 live_simulation，但編號錯亂
- S4 TurnOfMonth（取代原本 MACDDivergence）→ KILLED
- S5 SPX_Overnight（取代原本 SettlementWeek）→ KILLED
- S6 ForeignPositionFade（取代原本 FlashCrashMomentum）→ KILLED
- S7 PreSettlementHarvest（取代原本 BullPullbackLong）→ KILLED
- S8 FOMC_OvernightFade（取代原本 BearBounceSell）→ KILLED
- S9 NightFadeShort（取代原本 VolExplosion）→ KILLED

**100% kill rate + 編號錯亂**，且宣告 "portfolio saturated" — 但其實**原始排程一個都沒做**。

→ **用戶 2026-06-22 明確要求按排程走**：「我需要的是按照排程走」「能夠確保你會完整地進入 S4 的開發，而不是突然加入你所自己思考的東西」。

---

## 二、原始排程（不可變更）

### Batch 01 — S2-S5（已遷移）
| # | 策略名稱 | 類別 | 主週期 | 方向 | 狀態 |
|---|---------|------|--------|------|------|
| S2 | InsideBarBreak | B 價格結構 | 30M + 日線 | 雙向 | ⚰️ KILLED in research (alpha 已死) |
| **S3** | **VolSqueeze** | **C 波動率** | **60M** | **雙向** | 🔵 **CURRENT — 開發中** |
| S4 | MACDDivergence | D 動量逆勢 | 60M | 雙向 | ⏳ NEXT after S3 |
| S5 | SettlementWeek | E 統計 | 日線 | 結算前空/後多 | ⏳ Queue |

### Batch 02 — S6-S10（指數位階論系列，2026-06-07）
| # | 策略名稱 | 動機 | 狀態 |
|---|---------|------|------|
| S6 | FlashCrashMomentum | 閃崩動量做空 | ⏳ Queue |
| S7 | BullPullbackLong | 多頭回檔抄底 | ⏳ Queue |
| S8 | BearBounceSell | 空頭反彈放空 | ⏳ Queue |
| S9 | VolExplosion | 波動爆發 | ⏳ Queue |
| S10 | AdaptiveBreakout | 自適應突破 | ⏳ Queue |

### Batch 03 — S11-S15（2026-06-07，多策略類型擴展）
| # | 策略名稱 | 類別 | 主週期 | 方向 | 狀態 |
|---|---------|------|--------|------|------|
| S11 | MiddayCompression | A 時段型 | 45M | 多 | ⏳ Queue |
| S12 | WeekdayMomentum | E 統計型 | 日線 | 雙向 | ⏳ Queue |
| S13 | VolCollapseShort | C 波動率型 | 30M | 空 | ⏳ Queue |
| S14 | TripleTFTrend | F 多時間框架 | 15M | 雙向 | ⏳ Queue |
| S15 | BBReversion | B 價格結構 | 60M | 雙向 | ⏳ Queue |

---

## 三、進場 / 結束 SOP

### 進場 SOP（每隻策略）

每隻策略**必須**走完完整週期：

1. **W0 Alpha Pre-verify** — 用 TXF1 真實資料 Python 驗證 alpha 是否存在
2. **W1 策略文件** — strategy.md + annotated.md
3. **W2 .pla 實作** — 包含 7 個規範（Rule #11 Settlement_Flat、Rule #12 SetStopLoss、HolidayFlat_v3、IOG=false、Manual_Kill_Switch、Registry_Valid_Until、MC Time 24hr 閉區間）
4. **W3 MC12 baseline backtest**
5. **W4 Walk-Forward 優化**
6. **W5 10 維度評估**（Rule #13）
7. **W6 晉升 live_simulation** OR **KILL with FINAL_VERDICT.md**

### 結束 SOP（進入下一隻）

S3 結束（無論晉升或 KILL）後：
1. ✅ 完整 commit + push S3 最終狀態
2. ✅ 寫 `S3_FINAL_VERDICT.md`（KILL）或 `S3_promotion_report.md`（晉升）
3. ✅ **立即開始 S4 MACDDivergence** — 不發明、不偏離
4. ✅ S4 重複 W0-W6 流程

---

## 四、強制執行規則

### 規則 R-1：不發明策略名稱
任何 `S<N>_<NewName>` 必須來自上方 batch01-03 表格。不允許自行衍生（如 RapidPullbackShort、TurnOfMonth、SPX_Overnight 等）。

### 規則 R-2：不跳號
S3 完成 → S4 MACDDivergence。S4 完成 → S5 SettlementWeek。依此類推。
不允許跳過 S5 直接去做 S11，除非用戶**明確同意**並在本文件**新增決策紀錄**。

### 規則 R-3：策略內容必須對齊 archive 原始說明
- 主週期 / 類別 / 方向 / 進場邏輯 / 出場邏輯 → 必須對齊 `archive/batch01_S2-S5/TXF1_Strategies_Batch01.md`（或 batch02 / batch03 對應文件）
- 可以**升級對齊規範體系**（補 Settlement / SetStopLoss / Holiday）
- 不可**根本改變策略本質**（如把 60M 改成 5M、把雙向改成單向，除非有 KILL 後重新設計的明確理由）

### 規則 R-4：每隻策略必有 W0 Pre-verify
- 用 Python 真實資料驗證 alpha 是否存在
- W0 fail → 立即 KILL，寫 FINAL_VERDICT.md
- W0 pass → 才寫 .pla
- 此規則防止 S3 RapidPullbackShort 失敗模式（設計超前實證）

### 規則 R-5：完成一隻才進下一隻
不平行開發。S3 沒結束（晉升 OR KILL）不能碰 S4。

---

## 五、當前進度

| 階段 | 狀態 |
|------|------|
| S3 VolSqueeze | 📋 W0 Pre-verify 待開始 |
| S4 MACDDivergence | ⏳ Queue（S3 結束後） |
| S5 SettlementWeek | ⏳ Queue |
| S6-S10 | ⏳ Queue |
| S11-S15 | ⏳ Queue |

---

## 六、決策紀錄

| 日期 | 決策 | 理由 |
|------|------|------|
| 2026-06-22 | 鎖定原始 batch01-03 排程 | 桌機端偏離排程造成 100% kill rate 假象，必須回正 |
| 2026-06-22 | S3 RapidPullbackShort 視為「歪打正著」生產品保留 live_simulation | 已部署成功，不重做，但編號歸還 VolSqueeze |
| 2026-06-22 | S2 InsideBarBreak KILL 永久成立 | alpha 已死，無需重做 |
