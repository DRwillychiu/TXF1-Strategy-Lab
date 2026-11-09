# Handoff 2026-07-17 — L1-L5 組合 DD 危機審計完成（Laptop → Desktop）

## 1. Status

- **事件**：帳戶 300K → 236K（-64K，-21.3%），2026/07 上旬。
- 三路 subagent 全檔審計**完成**（L1+L2 / L3+L4 / 組合層文件 + TWSE 官方行情）。
- 完整報告：`docs/research/portfolio_DD_postmortem_202607_L1-L5.md`（commit `37bae8a`，已推 GitHub）。
- 本 session **未修改任何策略程式碼**——純診斷。
- **帳戶 DD 已越過 §4.2 的 20% 熔斷線；30% 全面停機線 = 帳戶 210K，距現值 -26K。**

## 2. Changed

- 新增 `docs/research/portfolio_DD_postmortem_202607_L1-L5.md`
- 新增本 handoff
- 無 .pla 改動

## 3. State（三層診斷結論）

1. **資金適足性（根因）**：allocation v2/v3 明載 <300K 不建議實盤；L1-L5 合併回測 MDD -375K = 帳戶 125%；任一單策略 MDD 都超過整個帳戶。
2. **結構性多空不對稱**：多方濾網全是 OR（L1 週線 OR、L3 日線 OR）→ 跌勢初段全開；空方濾網嚴格慢速（L2 13週SMA 2026 全年 0 筆、L4 MA20>MA60 禁空殘留）→ 全關。七月 = L1/L3/L5 反覆送停損 + L2/L4 零對沖。
3. **流程違規**：L3 v14.1 於 7/3-7/4 部署、無 review、7/7 即遇 -1,077 點（史上第 8 大）。

## 4. Decisions

- 診斷純文件化，不趁 DD 情緒急改程式碼（Rule 16 流程優先）。
- 濾網不對稱 + 無組合級日/週虧損上限 = 結構債，列維護窗口走設計 spec。

## 5. Next（桌機端執行順序）

1. **[熔斷執行]** 依 `position_sizing_and_capacity.md:208-213`：全策略降至最小口數；帳戶跌至 210K = 無條件全面停機。
2. **[高優先]** L3 v14.1 停用或回滾 v13.2B（無 review 首戰 + 主要出血源候選）。
3. **[歸因]** MC9 匯出 7/1-7/11 平倉明細：核對 L1 TL_SL 筆數、L3 出場標籤（CL_SL vs CL_BreakExit）、L2/L4 是否零進場、L5 兩筆實際損益。
4. **[確認]** 實盤合約類型與口數（微台×2？小台×2？）——微台×2 則 -64K = 縮放回測 MDD 的 1.7 倍（異常）；小台×2 則在回測範圍內但曝險 62% 帳戶（自殺級）。
5. **[確認]** MC9 實際運行版本 = repo HEAD？（L1 V2.7 / L2 V5.2 均有「空手部署」條款，未驗證是否生效）。
6. **[結構債 backlog]** 濾網不對稱修正 + 組合級虧損上限 + regime 煞車，依 Rule 16 開設計 spec。

## 6. Files

- `docs/research/portfolio_DD_postmortem_202607_L1-L5.md` — 完整診斷（15 findings 級，含 TWSE 行情表 + 未驗證清單）
- `docs/methodology/position_sizing_and_capacity.md:208-213` — 熔斷規則出處
- `docs/archive/offRoadmap_2026Q2/portfolio_allocation_v2/v3` — 資金檔位表
- `backtest/results/portfolio/portfolio_pnl_6sleeves_2019-2026.json` — 合併 MDD 計算來源
- 各 `strategies/live/*_BOSS_VIEW.md` — 單策略 MDD

## 7. Git

- 起點：`83388be`（S16_S handoff 2026-07-16）
- 本次：`37bae8a`（post-mortem）+ 本 handoff commit
- 未追蹤殘留：各 `.bak_*`（刻意不入庫）
