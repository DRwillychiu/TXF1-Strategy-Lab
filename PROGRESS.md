# PROGRESS

> 規則：Phase ＝ 一次開發主題（討論定案後寫入 ＋ commit）；Task ＝ 完成主題的關鍵步驟。
> 每 Task：實作 ＋ 驗證通過（`verify.bat`）→ 打勾 → commit（`Task N.M：摘要`，勾選與程式同一 commit）。
> 【Tier 1】進出場邏輯、停損、風控規則、下單防呆、實盤部署：每 Task 暫停，等 Willy 審查才繼續；其他連續做到 Phase 結束。
> 只增不改：完成的 Phase 不回頭編輯；中止的 Phase 原地標註「中止，由 Phase N 取代」。
> 交接：接手者依序讀 本檔 → `CLAUDE.md` → 該 Phase 的 Spec；**第一個未勾選的 Task 就是下一步**。
> 期限：2026/10/1 上線；9/29 上線閘門——未通過驗證的項目不上線，改用前一版。

---

## Phase 1：實戰第一階段績效報告（V3）

> Spec：`docs/reports/2026Q3_live_phase1/`｜開卷：2026/09/17｜完成：2026/09/23

- [x] Task 1.1：v2.2 報告逐頁校正、口徑統一（帳戶口徑為主、MC 口徑為輔）
- [x] Task 1.2：改為主報告 9 頁 ＋ 附錄補充 41 頁（依老闆六問重排）
- [x] Task 1.3：主報告逐頁定案（五支都優化連續虧損、L4 增加交易機會、及格線＝12/31 帳上 > 30 萬、過了也要檢討）
- [x] Task 1.4：附錄補充全份一致性檢查（修正 4 處）

## Phase 2：驗證 SOP（V1）

> Spec：`docs/policies/VERIFICATION_SOP.md`｜開卷：2026/09/23

- [x] Task 2.1：G1 靜態檢查 `tools/verify_static.py`（實盤五支 5/5 PASS）
- [x] Task 2.2：G3 回測基準比對 `tools/verify_baseline.py` ＋ L1–L5 基準檔
- [x] Task 2.3：`verify.bat` ＋ SOP 文件
- [x] Task 2.4：G0 文件檢查 `tools/verify_docs.py`（CLAUDE.md 行數上限、必要段落、連結；PROGRESS Task 格式與編號）
- [ ] Task 2.5：`verify.bat` 掛進 `.githooks`（待 Willy 決定）
- [ ] Task 2.6：G2 單元測試（待 Python 規則層）

## Phase 3：R1 策略層損失規則（V1）【Tier 1】

> Spec：`docs/specs/spec_R1_loss_rules.md`｜開卷：2026/09/23

- [x] Task 3.1：五支注入規則模組（`strategies/research/R1_loss_rules/`），G1 5/5 PASS
- [x] Task 3.2：L3 停用線改為帳戶 10%（1,500 點），G1 PASS
- [ ] Task 3.3：L3：MC 規則關（G3 對上架版本，同時驗證實盤圖表設定）／規則開
- [ ] Task 3.4：L5：同上
- [ ] Task 3.5：L4：同上
- [ ] Task 3.6：L1：同上
- [ ] Task 3.7：L2：同上
- [ ] Task 3.8：Willy 核准新基準（`tools/make_baseline.py`）

## Phase 4：R2 帳戶層防呆與 TG 通知（V1）【Tier 1】

> Spec：待寫 `docs/specs/spec_R2_account_guard.md`｜開卷：2026/09/23

- [ ] Task 4.1：Spec 討論定案（部位對帳、出場口數上限、帳戶回撤 20% 通知、每日心跳）
- [ ] Task 4.2：MC 端寫出事件檔與狀態檔
- [ ] Task 4.3：Python 監看 ＋ TG（Token 與 Chat ID 由 Willy 自填本機設定，不進 git）
- [ ] Task 4.4：MC 模擬模式觸發測試（故意製造部位不一致）
- [ ] Task 4.5：凱基對帳單 6/17–9/10 與實戰工作表逐筆核對

## Phase 5：L3 優化——停損等比例 ＋ 盈虧比（V2）【Tier 1】

> Spec：`docs/specs/spec_L3_R2.md`｜開卷：2026/09/23

- [x] Task 5.1：深度歸因（停損被洗 81%、同時段進出虧、極端期不虧）
- [x] Task 5.2：設計定案（見 Spec §2）
- [x] Task 5.3：兩項待決結案：箱體記錄併入新版；箱體定義本次就改（邊界碰 2 次、排除單根影線）
- [ ] Task 5.4：L3 R2 程式（`.txt`）＋ G1：新停損、箱體品質開關（`Box_Touch_Min`／`Box_NoWick`）、箱體記錄
- [ ] Task 5.5：四組合隔離測試（基準／箱體品質／新停損／兩者）
- [ ] Task 5.6：MC 掃描 X（10%–50%）× 盈虧比（1.5／2.0／2.5），取高原
- [ ] Task 5.7：連虧門檻：2 筆（主）vs 依盈虧比（2020–2023 算、2024–2026 驗）
- [ ] Task 5.8：箱體四道檢查 ＋ 目標價盲點研究
- [ ] Task 5.9：驗收：帳戶回撤 ≤ 10%、淨利跌幅 ≤ 30%、G3、五件套

## Phase 6：L4 增加交易機會（V2）【Tier 1】

> Spec：待寫｜開卷：2026/09/23

- [ ] Task 6.1：設計討論（第一目標一年筆數 × 2，最終 ≥ 50 筆；可放寬日線多頭封鎖，搭配連虧 3 筆暫停）
- [ ] Task 6.2：程式（`.txt`）＋ G1
- [ ] Task 6.3：MC 測試與驗收

## Phase 7：非 WFA 五件套（V1）

> Spec：`docs/methodology/non_WFA_validation_SOP_20260630.md`｜開卷：2026/09/23

- [ ] Task 7.1：蒙地卡羅、Bootstrap（用套規則後的交易序列）
- [ ] Task 7.2：壓力測試、行情分段
- [ ] Task 7.3：參數穩健度（MC 最佳化器 ±20%）

## Phase 8：上線（V2）【Tier 1】

> 開卷：2026/09/23

- [ ] Task 8.1：9/28 全份 `verify.bat`、整理 commit
- [ ] Task 8.2：9/29 上線閘門逐項判定
- [ ] Task 8.3：9/29 夜盤空跑（通知、部位對帳）
- [ ] Task 8.4：10/1 上線
