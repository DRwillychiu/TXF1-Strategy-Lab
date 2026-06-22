# 策略優化進度追蹤表

> 最後更新：2026-06-22 (S2 KILLED / S3 RapidPullback 部署 live_sim / S3 VolSqueeze 啟動 / L1-L5 v2.6 含 ImmediateStop)
> 規則：每隻策略經過完整 4 Phase 優化流程後，依據「績效門檻」判定 Pass/Fail
>
> **NEW 2026-06-22**：本表與 [`docs/policies/OFFICIAL_ROADMAP.md`](../docs/policies/OFFICIAL_ROADMAP.md) 互補，依 Rule #14 嚴守原始 batch01-03 排程。

---

## 績效門檻（必須全部通過）

| 門檻項目 | 標準 | 說明 |
|---------|------|------|
| Walk-Forward Efficiency | ≥ 50% | OOS 獲利窗口佔比 |
| OOS Profit Factor | > 1.0 | 樣本外必須獲利 |
| Monte Carlo 95% MDD | < 帳戶 30% | 帳戶規模依策略而定（S1: 1,000,000 NTD） |
| 破產機率 | < 5% | Monte Carlo 50% DD |
| 參數高原寬度 | > 參數範圍 20% | 非尖峰 = 非過擬合 |
| 最低月交易次數 | ≥ 2 筆 | 統計可驗證 |
| 邏輯可解釋性 | 主觀判斷 | 不接受純 curve-fitting |

---

## 策略總覽表

| 批次 | 代號 | 策略名稱 | 方向 | 週期 | 基線淨利 | 基線PF | 基線MDD | 月均交易 | 優化狀態 | Phase | 判定 | 優先級 |
|------|------|---------|------|------|---------|--------|---------|---------|---------|-------|------|--------|
| B01 | S1 | NightMomentum | ★純做多 | 15M | +1,997,000 | 1.448 | -278,800 | ~12.4 | 🟢 **live_sim** | 4/4 | **MC12 部署，模擬中** | 🥇 高 |
| B01 | S2 | InsideBarBreak | ★雙向(MA) | 30M+D | +791,754 | 4.61 | -63,879 | 0.5 | ⛔ **KILLED 2026-06-22** | 2/4 | **alpha 已死，archive 歸檔** | — |
| B01 | **S3_L** | **VolSqueezeLong** | **★純多** | **60M** | -115,622 | 0.88 | -645,467 | 0.5 | 🔵 **CURRENT — W0 Pre-verify** | 0/4 | **2026-06-22 啟動 Sx_L/Sx_S 拆解** | 🥇 當前 |
| B01 | S3_S | VolSqueezeShort | ★純空 | 60M | — | — | — | — | ⏳ Queue（S3_L 後） | 0/4 | — | 🥈 next |
| B01 | S4_L | MACDDivergenceLong | ★純多逆勢 | 60M | +38,000 | — | 0 | 0.03 | ⏳ Queue | 0/4 | — | 🥉 後 |
| B01 | S4_S | MACDDivergenceShort | ★純空逆勢 | 60M | — | — | — | — | ⏳ Queue | 0/4 | — | 🥉 後 |
| B01 | S5_L | SettlementWeekLong | ★結算後多 | 日線 | — | — | — | — | ⏳ Queue | 0/4 | — | ⚠️ 高風險 |
| B01 | S5_S | SettlementWeekShort | ★結算前空 | 日線 | — | — | — | — | ⏳ Queue | 0/4 | — | ⚠️ 高風險 |
| B02 | S6 | FlashCrashMomentum | ★純空 | 5M | -1,674,550 | 0.73 | -2,211,835 | 2.5 | ⏳ Queue | 0/4 | 不拆（原已純空） | 🥈 中(需5M) |
| B02 | S7 | BullPullbackLong | ★純多 | 15M+D | 0 | — | 0 | — | ⏳ Queue | 0/4 | 不拆（原已純多） | 🥉 低(需15M) |
| B02 | S8 | BearBounceSell | ★純空 | 15M+D | 0 | — | 0 | — | ⏳ Queue | 0/4 | 不拆（原已純空） | 🥉 低(需15M) |
| B02 | S9_L | VolExplosionLong | ★純多 | 5M | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | ⚠️ 需5M |
| B02 | S9_S | VolExplosionShort | ★純空 | 5M | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | ⚠️ 需5M |
| B02 | S10_L | AdaptiveBreakoutLong | ★純多 | 30M | +5,533,942 | 1.66 | -943,544 | 4.0 | ⏳ Queue | 0/4 | 拆解 | 🥇 高 |
| B02 | S10_S | AdaptiveBreakoutShort | ★純空 | 30M | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | 🥇 高 |
| B03 | S11 | MiddayCompression | ★純多 | 45M | +639,782 | 2.28 | -195,541 | 0.4 | ⏳ Queue | 0/4 | 不拆（原已純多） | 🥈 中 |
| B03 | S12_L | WeekdayMomentumLong | ★純多 | 日線 | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | 🥉 低 |
| B03 | S12_S | WeekdayMomentumShort | ★純空 | 日線 | -115,128 | 0.90 | -381,827 | 1.1 | ⏳ Queue | 0/4 | 拆解（基線虧損） | 🥉 低 |
| B03 | S13 | VolCollapseShort | ★純空 | 30M | +65,070 | 1.58 | -86,798 | 0.1 | ⏳ Queue | 0/4 | 不拆（原已純空） | ⚠️ 低頻 |
| B03 | S14_L | TripleTFTrendLong | ★純多 | 15M | +2,457,619 | 1.86 | -820,336 | 1.2 | ⏳ Queue | 0/4 | 拆解 | 🥇 高 |
| B03 | S14_S | TripleTFTrendShort | ★純空 | 15M | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | 🥇 高 |
| B03 | S15_L | BBReversionLong | ★純多 | 60M | +934,134 | 9.03 | -67,642 | 0.2 | ⏳ Queue | 0/4 | 拆解 | ⚠️ PF異常 |
| B03 | S15_S | BBReversionShort | ★純空 | 60M | — | — | — | — | ⏳ Queue | 0/4 | 拆解 | ⚠️ PF異常 |

### 狀態圖例
- 🔴 未開始
- 🟡 進行中（標註 Phase 1-4）
- 🟢 完成 — PASS
- ⛔ 完成 — FAIL（附失敗原因）
- ⏸️ 暫停（附原因）

### 優先級建議
**Batch01:**
1. **S1 NightMomentum** → 基線最佳（PF 2.58, 淨利 +194 萬），月交易 3.6 筆，最值得優化
2. **S2 InsideBarBreak** → PF 4.61 極高但交易太少（月均 0.5），需在 30M 上確認頻率
3. **S3 VolSqueeze** → 日線虧損，需 60M 重測。如 60M 仍虧 → 直接 FAIL
4. **S4 MACDDivergence** → 日線僅 2 筆，需 60M 驗證。逆勢策略風險高
5. **S5 SettlementWeek** → 日線虧損且 PF 0.60，高機率 FAIL

**Batch02（指數位階論）:**
6. **S10 AdaptiveBreakout** 🥇 → 日線即強（PF 1.66, +553 萬），位階自適應停損創新，最先優化
7. **S6 FlashCrashMomentum** 🥈 → 閃崩捕捉核心，日線虧損但 5M 預期有效
8. **S7 BullPullbackLong** 🥉 → 多頭回檔抄底，需 15M 驗證，可能需放寬門檻
9. **S8 BearBounceSell** 🥉 → S7 鏡像，需 15M 驗證
10. **S9 VolExplosion** ⚠️ → 波動率爆發概念好，ATRRatio 門檻可能過嚴

---

## 各 Phase 細項檢核表

### Phase 1: 參數敏感度分析
| 策略 | 參數1 | 範圍 | 高原? | 參數2 | 範圍 | 高原? | 參數3 | 範圍 | 高原? | P1 結論 |
|------|-------|------|-------|-------|------|-------|-------|------|-------|---------|
| S1 | LookbackBars | 2-10 | ✅ 44.4% | StopLossPts | 30-120 | ✅ 50.0% | EntryOffset | 0-24 | ✅ 69.2% | ✅ PASS |
| S2 | BreakOffset | 0-15 | — | StopPct | 30-70 | — | TargetMult | 1.0-2.5 | — | — |
| S3 | BWPctile | 10-30 | — | StopATRMult | 1.0-2.5 | — | BBLen | 15-30 | — | — |
| S4 | RSIOversold | 25-45 | — | TargetPts | 60-150 | — | PriceLookback | 30-80 | — | — |
| S5 | DaysBefore | 1-3 | — | HoldDays | 2-5 | — | StopPts | 60-150 | — | — |
| S6 | AccelBars | 3-10 | — | AccelThresh | 2.0-5.0 | — | VolSpikeRatio | 1.5-3.0 | — | — |
| S7 | RSIOversold | 10-25 | — | ConsecDownBars | 2-5 | — | DevATRMult | 1.5-3.5 | — | — |
| S8 | RSIOverbought | 75-90 | — | ConsecUpBars | 2-5 | — | DevATRMult | 1.5-3.5 | — | — |
| S9 | ATRRatio | 1.5-3.5 | — | MomBars | 2-5 | — | StopATRMult | 1.0-2.5 | — | — |
| S10 | BreakoutBars | 10-40 | — | StopATRMult | 1.0-3.0 | — | StopPctCap | 0.008-0.025 | — | — |

### Phase 2: Walk-Forward 優化
| 策略 | IS 月數 | OOS 月數 | 窗口數 | WFE% | OOS PF | OOS 淨利 | P2 結論 |
|------|---------|---------|--------|------|--------|---------|---------|
| S1 | 24 | 6 | 9 | **62.5% (5/8)** | 累計PF>1 | **+1,939,500** | ✅ PASS (v2.1 VolFilter) |
| S2 | 24 | 6 | — | — | — | — | — |
| S3 | 24 | 6 | — | — | — | — | — |
| S4 | 24 | 6 | — | — | — | — | — |
| S5 | 24 | 6 | — | — | — | — | — |
| S6 | 12 | 3 | — | — | — | — | — |
| S7 | 24 | 6 | — | — | — | — | — |
| S8 | 24 | 6 | — | — | — | — | — |
| S9 | 12 | 3 | — | — | — | — | — |
| S10 | 24 | 6 | — | — | — | — | — |

### Phase 3: Monte Carlo 壓力測試
| 策略 | 迭代數 | MDD Mean | MDD 95% | MDD 99% | 破產率 | P3 結論 |
|------|--------|---------|---------|---------|--------|---------|
| S1 | 10,000 | -186,707 | -276,440 (55.3%) | -336,883 | 8.76%@500k / 0.01%@1M | ❌@500k / ✅@1M |
| S2 | 10,000 | — | — | — | — | — |
| S3 | 10,000 | — | — | — | — | — |
| S4 | 10,000 | — | — | — | — | — |
| S5 | 10,000 | — | — | — | — | — |
| S6 | 10,000 | — | — | — | — | — |
| S7 | 10,000 | — | — | — | — | — |
| S8 | 10,000 | — | — | — | — | — |
| S9 | 10,000 | — | — | — | — | — |
| S10 | 10,000 | — | — | — | — | — |

### Phase 4: 策略組合分析
| 組合 | 策略成員 | 組合 PF | 組合 MDD | Sharpe | 相關性 | P4 結論 |
|------|---------|--------|---------|--------|--------|---------|
| — | — | — | — | — | — | — |

---

## 判定結果彙總

| 策略 | P1 參數 | P2 WF | P3 MC | P4 組合 | 最終 | 判定日期 | 備註 |
|------|--------|-------|-------|--------|------|---------|------|
| S1 NightMomentum | ✅ | ✅ v2.1 PASS | ❌@500k/✅@1M | — | 🟢 **PASS@1M 上架實測** | 2026-06-07 | 最低帳戶1M, 95%MDD=27.2% |
| S2 InsideBarBreak | — | — | — | — | — | — | 頻率預警 |
| S3 VolSqueeze | — | — | — | — | — | — | 日線虧損 |
| S4 MACDDivergence | — | — | — | — | — | — | 樣本不足 |
| S5 SettlementWeek | — | — | — | — | — | — | 高風險 |
| S6 FlashCrashMomentum | — | — | — | — | — | — | 需5M數據 |
| S7 BullPullbackLong | — | — | — | — | — | — | 需15M數據 |
| S8 BearBounceSell | — | — | — | — | — | — | 需15M數據 |
| S9 VolExplosion | — | — | — | — | — | — | 需5M數據 |
| S10 AdaptiveBreakout | — | — | — | — | — | — | 日線PF=1.66✅ |

---

## FAIL 策略墓地

| 批次 | 策略 | 失敗 Phase | 失敗原因 | 可能修復方向 | 值得重試? | 修復優先級 |
|------|------|-----------|---------|-------------|----------|-----------|
| B01 | S2 InsideBarBreak | Phase 2（樣本不足 + alpha 衰退） | 6.5 年僅 34 筆，v0.3→v0.6 多版迭代仍無法解決 Inside Bar 出現頻率過低；MC12 真實回測 PF < 1.0 | 放寬 Inside Bar 定義（如 Near-Inside Bar）→ 但會增加 false trigger | ❌ 不值得 | — |

---

## 進度時間軸

| 日期 | 操作 | 策略 | 說明 |
|------|------|------|------|
| 2026-06-07 | 建立系統 | ALL | Batch01 生成 + 日線代理回測 + 追蹤系統初始化 |
| 2026-06-07 | 基線分析 | ALL | 填入回測數據，設定優先級：S1 > S2 > S3/S4 > S5 |
| 2026-06-07 | P1~P3 | S1 | 完成三階段優化。P1全過、P2 WFE=87.5%、P3 MDD超標@300k |
| 2026-06-07 | 建立系統 | B02 ALL | Batch02 生成：指數位階論主題 5 策略（S6-S10） |
| 2026-06-07 | 代理回測 | S6-S10 | S10 日線PF=1.66強，S6虧損需5M，S7/S8/S9需分鐘數據 |
| 2026-06-07 | MC12 | S1 | MC12 15M 回測方向分析：空單 PF=0.93 淨利-618,600，移除空單改純做多 |
| 2026-06-07 | 重構 | S1 | v2.0: 全面移除固定點數，改 ATR 波動率自適應進出場（適應各指數位階）|
| 2026-06-07 | MC12 | S1 | v2.0 MC12 GA回測：淨利+1,597,400(PF=1.292), MDD-318,000(-29.6%), 大幅優於v1.0 |
| 2026-06-07 | 修正 | S1 | 日線代理WFA降級為「僅供參考」,WFA必須用MC12 15M執行 |
| 2026-06-07 | 修正 | S1 | git程式碼從v1.0同步至v2.0 ATR(.pla+STRATEGY_GEN) |
| 2026-06-07 | P2完成 | S1 | MC12 15M WFA 8窗口結果歸檔：WFE=50%(名義)/33.3%(有效), 判定不通過 |
| 2026-06-07 | 重構 | S1 | v2.1: 加入波動率擴張過濾器(VolSlowLen+VolRatioMin), 待MC12 GA+WFA重跑 |
| 2026-06-07 | P2完成 | S1 | v2.1 MC12 15M WFA: WFE=62.5%(5/8) ✅ PASS, OOS累計+1,939,500 |
| 2026-06-07 | P3完成 | S1 | Monte Carlo 10k次: 95%MDD~270k, FAIL@500k(55.3%), PASS@1M(27.2%) |
| 2026-06-07 | 🟢部署 | S1 | P1~P3檢驗完成, GA最佳參數寫入.pla, 全檔校正, **核准上架實測@1M** |
| 2026-06-13 | 升級 | S1 | v2.4-v2.6 經過多版優化（日盤平倉 / 隔夜 gap / 趨勢 filter） |
| 2026-06-13 | L1-L5 入庫 | L1-L5 | 5 隻既有 MC9 上架策略全部建立 .pla + annotated |
| 2026-06-18 | 升級 | L1-L5+S1 | 加入 P3b SetStopLoss（Rule #12），6 隻全部對齊 |
| 2026-06-17 | 升級 | L1-L5+S1 | 加入 Settlement_Flat（Rule #11），6 隻全部對齊 |
| 2026-06-17 | rollback | L3+L4 | RangeForceExit 部署 → 回滾（夜盤誤觸） |
| 2026-06-15~21 | off-roadmap | S4-S9 | 桌機端發明 6 隻偏離排程策略，全部 KILLED（已歸檔） |
| 2026-06-20 | 部署 | S3 RapidPullbackShort | v2.0.4 部署 live_simulation（off-roadmap 但保留） |
| 2026-06-22 | KILLED | S2 InsideBarBreak | alpha 已死，archive 歸檔 |
| 2026-06-22 | 🔵啟動 | S3 VolSqueeze | **回歸原始 batch01 排程，W0 Pre-verify 待開始** |
| 2026-06-22 | 拆解規則生效 | S3-S15 雙向策略 | **Rule R-6：Sx_L / Sx_S 命名，先 L 後 S。Queue 從 13 隻擴為 21 隻** |
| 2026-06-22 | 改名 | S3 → **S3_L VolSqueezeLong** | 純多單，短邊由 S3_S 接續 |
