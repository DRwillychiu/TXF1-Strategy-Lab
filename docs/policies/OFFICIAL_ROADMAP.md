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

## 二、原始排程（拆解後，2026-06-22 用戶決策 Sx_L / Sx_S）

### 拆解規則

| 原始策略方向 | 拆解 | 命名 |
|-------------|------|------|
| 雙向（多+空） | 拆 2 隻 | `Sx_L`（純多）+ `Sx_S`（純空） |
| 純多 | 不拆 | `Sx`（保持原名） |
| 純空 | 不拆 | `Sx`（保持原名） |
| 結算/日曆雙向 | 拆 2 隻 | `Sx_L` + `Sx_S` |

**開發順序鐵則**：**一律 L 先、S 後**（TXF1 2020-2026 偏多 regime，Long 驗證較快）。

### Batch 01 — S2-S5（拆解後）
| # | 策略名稱 | 類別 | 主週期 | 方向 | 狀態 |
|---|---------|------|--------|------|------|
| ~~S2~~ | ~~InsideBarBreak~~ | B 價格結構 | 30M + 日線 | 雙向 | ⚰️ KILLED 2026-06-22 |
| S3_L | VolSqueezeLong | C 波動率 | 60M | 純多 | ✅ **PROMOTED to live_simulation/ (2026-06-23, W5 PASS)** |
| S3_S | VolSqueezeShort | C 波動率 | 60M + 1M | 純空 | ✅ **PROMOTED v1.9.6-OPT-PROD (2026-07-06, 7/7 PASS, 71T/+731K/PF1.749, 3% cap)** |
| ~~S4_L~~ | ~~MACDDivergenceLong~~ | ~~D 動量逆勢~~ | ~~60M~~ | ~~純多~~ | ⚰️ **KILLED 2026-07-07 (MACD 概念不適合作為獨立策略，僅保留作判斷指標)** |
| ~~S4_S~~ | ~~MACDDivergenceShort~~ | ~~D 動量逆勢~~ | ~~60M~~ | ~~純空~~ | ⚰️ **KILLED 2026-07-07 (同 S4_L，W0 3/4 MARGINAL RR 1.33<1.5)** |
| S5_L | SettlementWeekLong | E 統計 | 日線 | 結算後做多 | ⏳ Queue |
| S5_S | SettlementWeekShort | E 統計 | 日線 | 結算前做空 | ⏳ Queue |

### Batch 02 — S6-S10（拆解後）
| # | 策略名稱 | 主週期 | 方向 | 狀態 |
|---|---------|--------|------|------|
| S6 | FlashCrashMomentum | 5M | 純空（原已是） | ⏳ Queue |
| S7 | BullPullbackLong | 15M + 日線 | 純多（原已是） | ⏳ Queue |
| S8 | BearBounceSell | 15M + 日線 | 純空（原已是） | ⏳ Queue |
| S9_L | VolExplosionLong | 5M | 純多 | ⏳ Queue |
| S9_S | VolExplosionShort | 5M | 純空 | ⏳ Queue |
| S10_L | AdaptiveBreakoutLong | 30M | 純多 | ⏳ Queue |
| S10_S | AdaptiveBreakoutShort | 30M | 純空 | ⏳ Queue |

### Batch 03 — S11-S15（拆解後）
| # | 策略名稱 | 類別 | 主週期 | 方向 | 狀態 |
|---|---------|------|--------|------|------|
| S11 | MiddayCompression | A 時段型 | 45M | 純多（原已是） | ⏳ Queue |
| S12_L | WeekdayMomentumLong | E 統計型 | 日線 | 純多 | ⏳ Queue |
| S12_S | WeekdayMomentumShort | E 統計型 | 日線 | 純空 | ⏳ Queue |
| S13 | VolCollapseShort | C 波動率型 | 30M | 純空（原已是） | ⏳ Queue |
| S14_L | TripleTFTrendLong | F 多時間框架 | 15M | 純多 | ⏳ Queue |
| S14_S | TripleTFTrendShort | F 多時間框架 | 15M | 純空 | ⏳ Queue |
| S15_L | BBReversionLong | B 價格結構 | 60M | 純多 | ⏳ Queue |
| S15_S | BBReversionShort | B 價格結構 | 60M | 純空 | ⏳ Queue |

### Batch 04 — User-added MA Cross（2026-06-28 ruling, 2026-07-07 split L/S）
| # | 策略名稱 | 類別 | 主週期 | 方向 | 狀態 |
|---|---------|------|--------|------|------|
| **S16_S** | **MACrossShort** | **G 動量交叉** | **5M** | **純空** | ✅ **v1.4-BELATE 正式上架 2026-07-18（官方 718: 107T/+1,094,800/PF 1.91/MDD -18.3%；5件套通用4/5適性5/5；原WFE 77.4%作廢見WFA_AUDIT；參數凍結鐵則）** |
| **S16_L** | **MACrossLong** | **G 動量交叉** | **5M** | **純多** | 🟡 SUSPENDED（10M 實驗已完結：正面收案不部署，容量擴充模組封存）|
| **S17_S** | **SwingShort60M（暫名）** | **中速空方 swing** | **60M+日線** | **純空** | 🔵 **CURRENT — Stage-1 Topic 1 初步共識 B+C 雙層（日線 filter + 60M K棒觸發），Topics 2-6 待議** |

⚠️ **S16 是用戶 2026-06-28 explicit override Rule R-1 加入**。2026-07-07 用戶決策拆分為 S16_S + S16_L，**先 S 後 L**（override 先 L 後 S 鐵則，理由：補強做空 sleeve 為原始動機）。
規格（2026-07-07 更新）：5M 時框（原 15M）、True Zero-Lag EMA（ZLEMA）、死亡交叉進場（S16_S）/ 黃金交叉進場（S16_L）、搭配極端行情多層停損 SOP（Rule #17）。
Whipsaw 防護設計哲學：進場門寬開，出場刀鋒利。進場僅保留 M1 Slow ZLEMA 斜率 ≠ 0（輕量 gate），損害控制集中在出場端。
合規仍需走 W0-W6 完整流程 + 7 個強制模組（Settlement / SetStopLoss / Holiday / Kill / Registry / IOG=false / ASCII）。

### 總計（2026-07-07 update）

- **原始排程**：13 隻策略（部分雙向）→ 拆解 21 個開發單位（不含 KILL 的 S2）
- **KILLED**：S4_L + S4_S = -2
- **+ Batch 04 user-added**：S16_S + S16_L = +2
- **= 21 個存活開發單位**（含已完成 S3_L、S3_S）

### 完整開發順序（2026-06-28 user ruling override）

```
2026-07-07 起更新順序:
  [已完成] S3_L → S3_S
  [KILLED] S4_S, S4_L (MACD 概念 KILL, 2026-07-07)
  [進行中] S16 → S5_L → S5_S → ...

完整順序 (扣除 KILL):
  S3_L → S3_S → S16_S → S16_L → S5_L → S5_S → S6 → S7 → S8
    → S9_L → S9_S → S10_L → S10_S → S11 → S12_L → S12_S → S13
    → S14_L → S14_S → S15_L → S15_S
```

### 用戶 2026-06-28 ruling audit trail

| 條目 | 說明 |
|------|------|
| 衝突 Rule | R-1（不發明）/ R-2（不跳號）/ Rule #14（嚴格排程）|
| Override 理由 | 做空 sleeve 4 隻 vs 多頭 5 隻偏弱，先補完做空再回排程 |
| 緩解措施 | S16 寫入 ROADMAP 合法化 + 走完 W0-W6 + 全合規模組 |
| 風險 | off-roadmap 過往集體 KILL (S5-S9)，需嚴守 W0 pre-verify gates |
| 順序 | S4_S 先（跳過 S4_L），完成後 S16，再回 S4_L |

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
不平行開發。S3_L 沒結束（晉升 OR KILL）不能碰 S3_S。S3_S 沒結束不能碰 S4_L。

### 規則 R-6：雙向策略必拆解為 Sx_L / Sx_S（2026-06-22 用戶決策）
- 原始排程屬於雙向（多+空）的策略，**必須**拆解為純多 (`Sx_L`) 與純空 (`Sx_S`) 兩隻獨立策略
- 開發順序：**先 L 後 S**（不可顛倒）
- 每隻獨立走完 W0-W6，獨立 FINAL_VERDICT.md
- 已預先拆解列表見上方第二節 21 個單位

---

## 五、當前進度

| 階段 | 狀態 |
|------|------|
| **S3_L VolSqueezeLong** | 🔵 **W0 Pre-verify 啟動中** |
| S3_S VolSqueezeShort | ⏳ Queue (S3_L 結束後) |
| S4_L MACDDivergenceLong | ⏳ Queue |
| S4_S MACDDivergenceShort | ⏳ Queue |
| S5_L SettlementWeekLong | ⏳ Queue |
| S5_S SettlementWeekShort | ⏳ Queue |
| S6, S7, S8 (純向，不拆) | ⏳ Queue |
| S9_L, S9_S | ⏳ Queue |
| S10_L, S10_S | ⏳ Queue |
| S11 (純多，不拆) | ⏳ Queue |
| S12_L, S12_S | ⏳ Queue |
| S13 (純空，不拆) | ⏳ Queue |
| S14_L, S14_S | ⏳ Queue |
| S15_L, S15_S | ⏳ Queue |

**剩餘開發單位**：21 隻（含當前 S3_L）

---

## 六、決策紀錄

| 日期 | 決策 | 理由 |
|------|------|------|
| 2026-06-22 | 鎖定原始 batch01-03 排程 | 桌機端偏離排程造成 100% kill rate 假象，必須回正 |
| 2026-06-22 | S3 RapidPullbackShort 視為「歪打正著」生產品保留 live_simulation | 已部署成功，不重做，但編號歸還 VolSqueeze |
| 2026-06-22 | S2 InsideBarBreak KILL 永久成立 | alpha 已死，無需重做 |
| 2026-06-22 | **Sx_L / Sx_S 拆解規則生效**（R-6） | 用戶偏好純多 / 純空分開規劃，避免互相干擾統計 |
| 2026-06-22 | **開發順序鐵則：先 L 後 S** | TXF1 2020-2026 偏多 regime，Long 驗證較快 |
| 2026-06-22 | S3 改為 **S3_L VolSqueezeLong**，短邊由 S3_S 接續 | 對應 Sx_L / Sx_S 新規則 |
| 2026-06-28 | S16 MACrossShort 加入排程（override R-1） | 補強做空 sleeve 厚度，先完成 S4_S+S16 再回 S4_L |
| 2026-07-06 | S3_S v1.9.6-OPT PROMOTED to live_simulation | 7/7 quantitative PASS, 71T/+731K/PF1.749, 3% cap |
| 2026-07-07 | **S4_L + S4_S MACDDivergence 雙殺 KILL** | MACD 概念不適合獨立策略（W0 RR 1.33 MARGINAL），保留作指標用途 |
| 2026-07-07 | S16 時框 15M→5M + MA 類型改為 ZLEMA | 用戶決策：更低操作週期 + True Zero-Lag EMA 減少滯後 |
| 2026-07-07 | S16 排序提前為 S3_S 之後直接開發 | S4 KILL 後 S16 成為 CURRENT |
| 2026-07-07 | **S16 拆分為 S16_S + S16_L，先 S 後 L** | 用戶決策：策略可同時做多做空，S16_S 先行（原始動機為補強空頭 sleeve） |
| 2026-07-07 | S16 Whipsaw Layer 1 設計完成 | 進場門寬開出場刀鋒利；M1 斜率保留（寬鬆）、M2 延遲棄用、M3 ATR 歸出場端、M4 量確認棄用 |
| 2026-07-08 | S16_S Layer 2 出場端 4 機制設計完成 | M5 Quick Stop / M6 Rule #17 多層 1M / M7 Breakeven Trail / M8 Time Stop 全鎖定 |
| 2026-07-08 | S16_S Layer 3 Regime Filter LOCK = 選項 A（純規則簡單，不加 filter） | Lesson L24 精神 + 哲學一致性 + 信任 Layer 2 exit rigor |
| 2026-07-08 | **S16_S W0 Alpha Pre-Verify STRONG PASS** | Daily proxy 40/216 combos 4/4 gates PASS, best Fast=12/Slow=30/RR=1.29/WR=45.8%，進 W1 strategy.md |
| 2026-07-09 | S16_S W2/W3/W4 GA+W5 5-piece Sniper 8/8 PASS | v0.5-FINAL LOCK Config F25/S70/Slope28 pure points, 106T/+1.03M/PF1.885 |
| 2026-07-10 | S16_S W6 v0.6-ADAPTIVE 拒絕 (ATR 用錯方向), revert v0.5 | ATR is volatility range (both dir), not directional slope; user insight confirmed |
| 2026-07-10 | S16_S W4 WFA STRONG PASS | WFE 77.4% (gate>50%), 9 windows / 416 OOS trades / +1.74M / 7-9 PASS |
| 2026-07-10 | **S16_S v1.0-PROD PROMOTED to live_simulation** | 3% cap, Bull whipsaw insurance cost disclosed, sniper hedge role |
| 2026-07-16~18 | S16_S 三日大修：Holiday 合規 → 彩券單移除 → 時間護欄 v1.3 → BE 延後 v1.4 → 官方 718 baseline 正式上架 | Rule #19 誕生、原 WFA 77.4% 作廢（窗口污染）、乾淨 WFA 轉化為參數凍結鐵則（固定勝滾動 +100 萬）、5 件套通用 4/5 適性 5/5 |
| 2026-07-18 | S16_S_10M 時框實驗完結：正面收案不部署 | robustness 達成（獨立 PF 1.61）+ 5M 粒度優勢全維度實證；corr 0.89 排除第二 sleeve；封存為容量擴充模組 |
| 2026-07-18 | **S17_S SwingShort60M 用戶 override 立案（Option A ruling）** | 理由：7 月 DD post-mortem 文件化「中速空方」結構洞（L2 13週SMA 2026 全年 0 筆 + L4 禁空殘留 + S16_S 只抓暴力段/2022 慢熊僅 3 筆）；saturation acceptance 例外依據 = 修組合已知洞非開新 alpha；60M+ 間距符合機構週期階梯法則；Stage-1 討論先行（S16_L 教訓：不跳步）|
| 2026-07-20 | S17_S Stage-1 Topic 1 初步共識 | B+C 雙層架構（C=日線環境filter + B=60M K棒反彈失敗觸發）；排除 A（ZLEMA 同家族 corr 風險）；量暫緩至 Phase 2；5 隱性風險識別（缺口/假日衝突/V轉/趨勢結束/期貨量品質）；K棒型態適用性原則：週期越長越適合 |
