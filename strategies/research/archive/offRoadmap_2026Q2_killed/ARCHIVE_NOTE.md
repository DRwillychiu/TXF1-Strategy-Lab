# ARCHIVED — Off-roadmap Strategies (2026-06-20 ~ 06-21 桌機端偏離排程產物)

**歸檔日期**：2026-06-22
**歸檔原因**：以下策略 **不在原始 [archive/README.md](../README.md) batch01-03 排程中**，是桌機端 2026-06-20/21 ultracode session 自行衍生的設計，全部已 KILLED。

---

## Off-roadmap 策略清單（vs 原始排程對照）

| 偏離排程的策略 | 原始排程應該是 |
|---------------|---------------|
| S04 TurnOfMonth | S4 MACDDivergence |
| S05 SPX_Overnight | S5 SettlementWeek |
| S06 ForeignPositionFade | S6 FlashCrashMomentum |
| S07 PreSettlementHarvest | S7 BullPullbackLong |
| S08 FOMC_OvernightFade | S8 BearBounceSell |
| S09 NightFadeShort | S9 VolExplosion |

---

## 為什麼這些策略全部 KILLED

每隻都有自己的 `S<N>_FINAL_VERDICT.md`，但**根本問題是**：
1. 沒有對齊原始 archive/README.md 排程
2. 用 28-year empirical pre-verify 套用到本來就**沒被排程驗證過的新想法**
3. 100% kill rate (7/7) **不是 SOP 嚴格的證明**，是「自行發明 candidates 卻不符實證」的結果

---

## 為什麼 portfolio_saturation_acceptance 是錯的

桌機端 2026-06-21 宣告「Portfolio 已 7-sleeve saturated」並把這 7 隻 KILL 當作 saturation 證據。
**這個宣告基於錯誤的 candidate 集合**——真正的 S4 MACDDivergence、S5 SettlementWeek、S6-S9（原始 batch02）等都還沒被驗證過。

正確的排程應該是：
- 完成 S3 VolSqueeze
- 完成 S4 MACDDivergence
- 完成 S5 SettlementWeek
- 完成 S6 FlashCrashMomentum, S7 BullPullbackLong, S8 BearBounceSell, S9 VolExplosion, S10 AdaptiveBreakout
- 完成 S11-S15

---

## 是否要重新嘗試原始 S4-S9?

✅ **是的**。S3 VolSqueeze 完成後，按原始排程繼續 S4 MACDDivergence。
不接受發明新策略名稱、不接受偏離原始排程。

---

## 23 個 lessons（L1-L23）的處理

這些 lessons 雖然來自 off-roadmap 工作，但部分仍有參考價值。
若未來原始 S4-S9 開發遇到類似問題，可參考各策略的 `S<N>_FINAL_VERDICT.md`。

---

## 檔案內容

```
S04_TurnOfMonth/           — TurnOfMonth strategy KILLED 2026-06-21
S05_SPX_Overnight/         — SPX overnight follow KILLED 2026-06-21
S06_ForeignPositionFade/   — Foreign position fade KILLED 2026-06-21
S07_PreSettlementHarvest/  — Pre-settlement harvest KILLED 2026-06-21
S08_FOMC_OvernightFade/    — FOMC overnight fade KILLED 2026-06-21
S09_NightFadeShort/        — Night fade short KILLED 2026-06-21
_analyze_scripts/          — 8 個 analyze_s4-s9 pre-verify scripts (用於 KILL 決策)
```
