# TXF1-Strategy-Lab — 總管

台指期貨（TXF1）量化策略庫。策略以 MultiCharts PowerLanguage 撰寫，Python 做驗證與分析。
**本檔是總管：只放重點與入口。細節找部門，部門再找團隊。**

## 文件三層

```
CLAUDE.md（總管：重點＋入口）
   └─ docs/departments/DEPT_*.md（部門：重點＋團隊清單）
        └─ docs/specs、policies、methodology、registers、reports（團隊：完整細節）
```

## 我的部門

| 部門 | 負責 | 入口 | Tier 1 |
|---|---|---|---|
| 策略部 | 進出場、程式規範、開發排程、晉升 | `docs/departments/DEPT_STRATEGY.md` | ✅ |
| 風控部 | 停損、連虧與上限、結算平倉、下單防呆 | `docs/departments/DEPT_RISK.md` | ✅ |
| 驗證部 | G0–G5 關卡、基準檔、放行與退回 | `docs/departments/DEPT_VERIFY.md` | ✅（基準更新） |
| 資料部 | 回測與實戰資料來源、格式、口徑換算 | `docs/departments/DEPT_DATA.md` | — |
| 營運部 | 上線部署、圖表設定、監看通知、事故處理 | `docs/departments/DEPT_OPS.md` | ✅ |
| 文件部 | 規範、進度、溝通、登記簿 | `docs/departments/DEPT_DOCS.md` | — |
| 報告部 | 對外報告與講稿 | `docs/departments/DEPT_REPORT.md` | — |

- 規範編號 Rule #1–#19 的現址見 `docs/departments/RULES_INDEX.md`（編號永久保留）
- **Tier 1 ＝ 出錯直接賠錢**：每完成一個 Task 就停下，等 Willy 審查才繼續；其他部門連續做到 Phase 結束

## 技術規格

| 項目 | 值 |
|---|---|
| 商品 | TXF1；大台 1 點 200 元、微台 1 點 10 元 |
| 實盤 | 微台 2 口，期初 30 萬（帳戶口徑分母） |
| 回測 | 大台 2 口、滑價每口每邊 1,000 元（＝5 點）、參數固定、2020/01 起 |
| 平台 | MultiCharts 9（實盤）／12（研究）；MaxBarsBack 100 → 回看 ≤ 99 |
| 時段 | 日盤 08:45–13:45／夜盤 15:00–05:00 |
| 期限 | 2026/10/1 上線；9/29 上線閘門 |

## 驗證關卡（詳見 `docs/departments/DEPT_VERIFY.md`）

| 關卡 | 檢查 | 何時 |
|---|---|---|
| G0 文件 | 本檔行數／段落／連結、PROGRESS 格式 | 每 Task |
| G1 靜態 | .pla 規範（ASCII、結算平倉、停損三件套、進場需空手、回看長度） | 每 Task |
| G2 單元 | 規則層純函式（待建） | 每 Task |
| G3 基準 | 設定與逐筆交易 vs 核准基準 | Phase 結束 |
| G4 券商 | 下單與部位對帳（待建） | 上線前 |
| G5 設定 | 圖表 Data1/2/3、時段 | 回測前 |

## 兩套流程

**每個 Task**
```
團隊做 Task → verify.bat（G0＋G1，約 0.2 秒）
   紅燈 → 退回團隊：問題＋三個解法 → 修 → 重驗
   綠燈 → 主管確認 → PROGRESS.md 打勾 → `push.bat "Task N.M：摘要"` → 回報 Willy
            Tier 1：回報後暫停，等審查
```

**每個 Phase 結束**
```
最後一個 Task 打勾 → verify.bat 報告.xlsx tools\baselines\Lx.json（G0＋G1＋G3）
   策略類另加非 WFA 五件套（≥ 4/5）
   全綠 → Phase 收尾 commit → 回報 Willy → 開下一個 Phase
   任一紅燈 → 不得收尾、不得上線
```

## 規矩

- `PROGRESS.md` 是進度唯一來源：**第一個未勾選的 Task ＝ 下一步**；只增不改
- Spec 沒寫的設計決策不要自行發明；矛盾或缺漏 → 標註、停下來問
- 討論階段不附程式碼；交付一律 `.txt`，repo 存 `.pla`
- 基準檔只能由 Willy 核准的版本產生，更新單獨 commit（Tier 1）
- 本檔上限 300 行，滿了依 `docs/policies/DOC_MAINTENANCE.md` 備份切割
