# 策略部

> 負責：進出場邏輯、程式規範、開發排程、晉升流程｜主管確認後才送驗證部

## 重點（詳細見團隊文件）
- 參數一律 `inputs:` 宣告不寫死；變數 `v_` 前綴；Data2 用 `[1]` 已收盤索引；不用未來函數
- 進場 `buy/sell short next bar at X stop/limit`；出場 `sell/buy to cover next bar at X stop`
- 同根 K 棒不可先用 `marketposition` 再引用；用 `v_Prev_MP` 追前根部位，腳本最末行更新
- 每隻策略 < 150 行、進場條件 ≤ 5 個；策略名稱 `STRATEGY_GEN_` 前綴
- 回看長度 ≤ 99（MaxBarsBack 100）
- 開發排程照 `docs/policies/OFFICIAL_ROADMAP.md`：不發明新名稱、不跳號、不平行開發；雙向策略必拆 `Sx_L`／`Sx_S`，先 L 後 S
- 三層晉升：research →（WFE > 50%、MC 95% MDD < 30%、OOS PF > 1.0）→ live_simulation →（≥ 30 筆、PF ≥ 1.2、偏離 ≤ 30%）→ live
- 品質門檻：WFE > 50%、MC 95% MDD < 帳戶 30%、參數高原寬度 > 範圍 20%、OOS PF > 1.0、每月 ≥ 2 筆

## 參數優化流程（Phase 1–4）
1. 參數敏感度：合理範圍掃描，確認是「高原」不是「尖峰」
2. Walk-Forward：IS 滾動 2 年、OOS 6 個月、步長 6 個月；合格 OOS PF > 1.0 且淨利 > 0
3. Monte Carlo：打亂序列 10,000 次，算 95% MDD 與破產機率
4. 組合分析：相關性矩陣、等權 equity、Sharpe 最佳化

## 團隊（詳細內容在這裡）
| 團隊 | 文件 |
|---|---|
| 排程 | `docs/policies/OFFICIAL_ROADMAP.md` |
| L3 優化 | `docs/specs/spec_L3_R2.md` |
| L4 優化 | `docs/specs/spec_L4_R2.md`（待寫） |
| 實盤五支 | `strategies/live/`｜研究 `strategies/research/` |
| 晉升檢查 | `docs/policies/PROMOTE_CHECKLIST.md` |
| 目錄結構 | `docs/REPO_STRUCTURE.md` |
| 規範編號對照 | `docs/departments/RULES_INDEX.md` |
