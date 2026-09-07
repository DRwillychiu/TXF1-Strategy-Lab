# 移植基準版本

> **釘死日期 2026-09-06。**
> 雜湊變了 → 該支的對帳作廢重跑。這是防「L3 基準線自己從 360 變 361」的唯一機制。

## live（MC9 實盤，對帳目標）

| 策略 | 版本 | SHA-256 |
|---|---|---|
| L1_TrendLong | **V3.1**（V3.0 base + SL_Pct percentage cap） | `1873911C75A02288F2DEF0B0F963BFD50018E7F2F3949BCD6CE2453FB4E17AAB` |
| **L2_TrendShort** | **5.3 + SetStopContract + SL_Pct（v5.2 base）** | `CDCF0F80CFFC024C9ED8BD49C91BA3AD82F982D4869994D73EE840B4534BF0E3` |
| L3_ConsolidationLong | **v15.0**（v14.1 base + SetStopContract + SL_Pct 0.55% + Opening Block + Min R:R） | `F09BB0150F697396BE0554A1619C3A85B4D127E3D7CAA0398DE235D80B876A55` |
| L4_ConsolidationShort | **v14.6** + SetStopContract + SL_Pct（PRODUCTION；v14.5 A/B 失敗後完全移除） | `69D1C1E77CB6DEBB4D9DF0FD84BE52182ADD6B83D4CC70FCFC517BAC4922FA30` |
| L5_BreakoutLong | **v19.9** + SetStopContract + SL_Pct + HolidayFlat_v3 + FrozenSL + ImmediateStop | `64AF5D2A25BD3CF1695BE55B386B53042C441A51E36B68FD40D8E740D8F69E67` |

## research（移植對象）

| 策略 | 版本 | 與 live 的關係 |
|---|---|---|
| L1 | v3.2 | v3.1 base + re-entry 模組（`ReEntry_On = 0`，完全惰性） |
| **L2** | **v5.4** | **v5.3 base + re-entry LABEL only。標頭：「untouched to the character」** |
| L3 | v15.1 | v15.0 base + re-entry LABEL only |
| L4 | v14.7 | v14.6 base + re-entry LABEL only |
| L5 | v19.9-R1 | v19.9 + Print 日誌，不發任何單 |

## ★ 乾淨的 1:1 對應

```
live          research      差異
L1  v3.1  →   v3.2          re-entry 模組（ReEntry_On = 0，惰性）+ v_Prev_MP
L2  v5.3  →   v5.4          re-entry LABEL only
L3  v15.0 →   v15.1         re-entry LABEL only（episode 定義）
L4  v14.6 →   v14.7         re-entry LABEL only（純結構）
L5  v19.9 →   v19.9-R1      Print 日誌，不發任何單
```

**五支的 research 版正好都是 live 版加一層可觀測性，且全部宣稱 zero behaviour change。**

> 同一套對帳程序會**一次驗證五次**這個宣稱。

## 裁決：全部只移植 research 版，對帳目標是 live 版

**live L2 = v5.3，research L2 = v5.4。** 兩者的關係已由 v5.4 標頭宣告：

> The four entry conditions, the Rule #11 gates, the order type and the timing
> are **untouched to the character**. Only the string differs, so the anchor
> **must reproduce every metric exactly**.

所以：

- **移植 v5.4**（邏輯完整、標籤齊全）
- **對帳基準是 live v5.3 的 MC 報告**
- **「zero behaviour change」列為待驗證，不是前提**

> 這正好是對帳能回答的問題。對得上 → 宣稱變成證據；對不上 → 那是真正有價值的發現。

## 關於「research 版績效更好」

**邏輯完整性成立，績效改善沒有證據。** 五支的 A/B 紀錄：

| 策略 | 優化嘗試 | 結果 |
|---|---|---|
| L1 | Plan C：被動出場後 re-entry | **拖累 −920K**，69 筆 re-entry 淨負 |
| L4 | v15 / v15.1 / v16 研究線 | **全部失敗**，2026-07-26 關閉 |
| L4 | BE +60 | 淨 −345K，砍掉前十大贏家中的 4 筆 |
| L4 | SP +80/50% | CS_SP 100% 勝率，但 CS_SL 從 +1,019K 掉到 +619K |
| L5 | SP 五個變體 B–F | 全部失敗，三筆超級贏家被砍到 +7K–38K |
| L3 | BE +50 | 100 筆 CL_BE 全 0% 勝率 |

**四支的 re-entry 是標籤不是新行為。** L2 標頭明說「has always re-entered」，
只是以前在報告裡分不出來。

> `v2` 模式的第一件事應該是讀完這些 postmortem，
> 而不是重試已經被 A/B 否決過的方向。

## 不採用的 research 分支

| 分支 | 理由 |
|---|---|
| L4 v15.0 / v15.1 / v16.0 | **FAILED**，research line CLOSED 2026-07-26 |
| L4 v17.0 | 非 production 版本 |
| L4 v18.0 | **二次進場零觸發事故**（G-3 的原型）。DIAG 版可供研究，不移植 |
| L1 v3.0 · L3 v14.1 · L5 v19.8 | 各自的前代 |

記錄「不採用的」與「採用的」同等重要——否則六個月後會有人重試一次。

## 死碼處置

移植 research 版會連帶帶到這些關閉中的模組：

| 策略 | 死碼 | 開關 |
|---|---|---|
| L1 | re-entry 模組 | `ReEntry_On = 0` |
| L3 | BE 層 | `BE_Trigger_Pts = 0` |
| L4 | BE + SP 兩層 | 兩者皆 `0` |
| L5 | SP 模組 | `SP_Trigger_Pts = 0`（標註 PERMANENT） |

**政策：`mc12` 不移植路徑，但保留 input 欄位。**
開關為 0 時路徑本來就不執行，對帳結果完全相同；保留欄位讓 `v2` 日後能接。

## 待補

- [ ] 五支的 MC 報告重跑並存檔（帶時間戳 + SHA-256）
- [ ] L1 的 v3.2 anchor 需要**兩次執行**（標頭明載舊筆數 NOT a valid baseline）

---

> 本表已編碼為 `txfcore/strategies/versions.py`，由測試機器檢查。
> 文件與程式碼不一致時，以程式碼為準——文件會漂移，測試不會。
