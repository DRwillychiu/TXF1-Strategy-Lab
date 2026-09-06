# Handoff: L1 停損戰役 2026-07-22 收工 → 明日繼續

**Date**: 2026-07-22 深夜收工
**Session**: Desktop 主 session (停損機制深度研究 → V2.9/V2.9.1 落地)
**Repo**: `C:/Users/User/Desktop/TXF1-Strategy-Lab/` (main @ `d03c025`, 已全數 push)

---

## 1. Status

L1 停損機制戰役**研究+修復閉環, 只剩用戶 MC9 部署動作**。V2.9 (P3b 取腿修復 + SetStopContract) 與 V2.9.1 (標籤 taxonomy) 雙雙通過 MC12 gate, 部署許可成立。7 條死路被數據封死, 7 月 MDD 真兇 (C-up 脈絡) 已診斷未治療。

## 2. Changed (今晚全部 commit)

| Commit | 內容 |
|---|---|
| `103ab50` | V2.9: P3b MaxList→MinList + SetStopContract + 驗證器修正 (V-4 反轉/V-4b/V-13 新增/V-6 錨點修復) + 4 研究文件 + skill 第7步/附錄C |
| `9ed21a2` | V2.9 MC12 gate PASS (65 diffs 逐筆解釋, net -36 pts, MDD 不變) |
| `c78eba9` | V2.9.1: 標籤損益側互斥 (TL_TSL/TL_SP_Gap 新增) |
| `38ac1f9` | Buffer 掃描 + 窄域 Reclaim 雙測試否決 (L35/L36) |
| `5ab63f3` | L37 (引擎函數隱藏預設語義) 入 bug ledger |
| `aa76310` | spec §5b V2.9.1 re-gate 檢查清單 |
| `d03c025` | V2.9.1 re-gate PASS (462/462 一致, 35 筆 TL_TP→TL_TSL, 0 違規) |

## 3. State (關鍵事實)

- **L1_TrendLong.pla = V2.9.1**, 靜態驗證 19/19 + ASCII 28/28, MC12 雙 gate PASS, **尚未部署 MC9**
- 用戶配置: 200 萬 / 2 口大台 (SetStopContract 使 2 口停損距離正確)
- 今日停損規格: 緊腿 266 pts / 舊 P3b 鬆腿 736 pts (修復消除 2.77x 進場棒暴露)
- Closed MDD 2,038 pts = 2026/07/03-16 五連停損, V2.9.x 對此不變 (病因在脈絡非停損)
- 已封死的路 (勿重開): 停損收緊 34 變體 / 固定點數 cap / 固定 % 0.4-1.0% / daily loss cap (V2.8) / P3b buffer / 窄域 reclaim / 廣義再進場 (Plan C)
- 教訓 L25-L37 已入文件; skill adversarial-engineering-sop 升級 (第 7 步 Before/After/Expected + 附錄 C 八陷阱)
- 標籤裁示已入記憶 (feedback_mc_entry_exit_labels): 損益側互斥, 適用所有策略

## 4. Decisions (用戶裁示記錄)

- 停損手術不收案宣告 → 對抗式審查 → V2.9 提案 (1.2% clip) 被自己的審查殺死 → 真正的修復是 P3b 取腿
- Buffer/Reclaim 兩測試: 數據否決, 用戶未再堅持
- 標籤: 停損類只能虧損、停利另立標籤 (已實作+入記憶)
- 合約口數議題 (40.8% vs 20% 預算) 擱置中, 數學在桌上

## 5. Next (明日)

1. **用戶動作**: MC9 編譯 V2.9.1 → 等空手 → 部署 → 前 3 筆核對 (停損距離 ≈ 緊腿非一半; 標籤按新表)
2. **主線研究**: 方案 2 = C-up 脈絡封鎖 (距 20 日高 3-8% + 日 MA20 上升 → 封鎖) 參數敏感度網格
   - 資料就緒: `TXF1 1 分鐘.txt` (MC9_20260108/報價/, 2019/01-2026/07/22) + 45M 合成快取在 scratchpad (需重建可跑 build_45m_bars.py 邏輯)
   - 紅旗: #431 (+3,342) 的 MA20 斜率 -0.12% 距邊界一髮 — 網格必須證明高原非尖峰
   - 依據: `L1_stop_forensics_20260722.md` §A 脈絡地圖
3. **排隊**: 方案 3 SP giveback 55→35 MC12 A/B (B7 紅旗: 86.6% 效益集中 2026); B-swing N=3 MC12 終審 (可選)
4. **更遠**: L2-L5 同等深度檢查 / L2 濾網鎖死 / L5 trail 死亡

## 6. Files (今晚產出)

- `strategies/live/L1_TrendLong.pla` (V2.9.1)
- `scripts/verify_l1_immediate_stop.py` (19 檢查)
- `docs/research/L1_stop_mechanism_deep_research_20260722.md`
- `docs/research/L1_stop_replay_bench_bug_ledger_20260722.md` (B1-B7 + L37)
- `docs/research/L1_stop_forensics_20260722.md` (F1-F3 + 脈絡地圖 ← 方案 2 的起點)
- `docs/research/L1_v2.9_p3b_fix_spec_20260722.md` (含雙 gate PASS 記錄)
- `docs/research/L1_buffer_reclaim_tests_20260722.md` (L35/L36)
- `.claude/skills/adversarial-engineering-sop/SKILL.md` (第 7 步 + 附錄 C)

## 7. Git

main @ `d03c025`, working tree clean, local = origin。全部已 push 至 github.com/DRwillychiu/TXF1-Strategy-Lab。
