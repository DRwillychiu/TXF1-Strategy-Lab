# HANDOFF — 2026-08-26 EOD

> 依 CLAUDE.md Rule #16 七區段。接手者先讀 §1 與 §5。
> **本文涵蓋 S16_S 圖形型態這條線。** 同日 L2/L4/L5 的工作由其他工作階段推送。

---

## 1. Status

**今天從「邏輯規劃」一路走到「MC12 指標可用」。**

| 里程 | 狀態 |
|---|---|
| 母體 172 → **202** | ✅ 時段邊界那條線套錯規則，移除後 +17.4% |
| P49 / P50 邏輯規劃 | ✅ 沿用 P29 七段，唯一新東西是 M7 |
| 裁示 12 / 13 | ✅ M7 用 12 根最小平方斜率；開口大小記成屬性 |
| `IND_S16S_P29.pla` | ✅ 偵測驗收 **202 / 202**，逐年相符 |
| K 棒換色顯示 | ✅ **已在 MC12 實機確認可用** |
| P49 / P50 顏色區分 | ✅ Build_ID 260830，黃=P49 / 白=P50 |
| **定義檢查表 skill** | ✅ `.claude/skills/pattern-definition-checklist/` |

**`.pla` 策略檔一行未動。P29 的報酬從未檢定。**

---

## 2. ★ 今天最重要的三件事

### 2.1 顯示的問題不是「畫得不夠」，是「找不到」

```
202 個型態 / 421,513 根 = 平均每 2,086 根一個 = 約 9.2 個交易日
全部型態合計只涵蓋 2,470 根 = 0.586%
```

兩條細線畫在 9 根 K 棒上，在顯示數百根的圖上等於不存在。
**解法是換 K 棒顏色**（`PlotPaintBar`），不是畫更多線。

### 2.2 ⚠️ 掛指標第一件事：座標範圍設「和商品一致」

不設的話，`PlotPaintBar` 的四個 plot 會被畫在自己的座標軸上並當成線圖，
**跨越 `NoPlot` 缺口互相連線** —— 在沒有型態的日子畫出橫跨整張圖的假線。

**和前一天把 `Plot1/Plot2` 改成 `TL_New` 的理由是同一個 MC12 行為：`Plot` 會跨缺口連線。**
**P49/P50 的指標一定會再踩一次。**

### 2.3 換色必須涵蓋「型態本體」，不是只有成立之後

Build_ID 260827 的缺陷：`v_State` 要到第六個樞紐**確認**才變 1。
2026-06-11 的型態本體是 01:20~02:05，260827 卻從 02:10 才上色 ——
**六個樞紐整段沒被標到**，正好漏掉要看的東西。

260828 起在成立那一根**回頭**把本體整段上色。涵蓋率 0.586% → **1.22%**。

---

## 3. Changed

| 檔案 | 內容 |
|---|---|
| `strategies/research/S16_MACrossShort/indicators/IND_S16S_P29.pla` | **Build_ID 260830**。PaintBar、回頭上色、P49/P50 分色、TL 診斷（預設關） |
| `.claude/skills/pattern-definition-checklist/SKILL.md` | **新增 — 16 條定義檢查表** |
| `docs/research/S16S_P29_display_design_20260826.md` | 新增 — 六個 MC12 顯示工具的設計 |
| `docs/research/S16S_pattern_workflow_review_20260826.md` | 新增 — 效率檢視 |
| `docs/research/S16S_P29_screenshot_windows_20260826.md` | 大改 — 驗收方式改成「捲動看顏色」 |
| `docs/research/S16S_ARTIFACTS.md` | 記入 P49/P50 網址 |
| `scripts/verify_pla_semantics.py` | 加入 `plotpaintbar` 內建 |

---

## 4. State

### 指標 inputs（Build_ID 260830）

```
Build_ID 260830   M7_Bars 12   Run_Bars 3
Line_Mode 1   Print_Events 1   Log_Lines 0   Show_State 0   Show_Pivots 0
Col_Upper red   Col_Lower cyan   Line_Width 3
Paint_Mode 1   Col_Active cyan   Col_Testing magenta
Col_Shape_Top yellow   Col_Shape_Bot white   Paint_MaxBack 60
```

| 顏色 | 意義 | 個數 |
|---|---|---|
| **黃** | P49 擴散頂本體（進入前上升） | 111 / 55% |
| **白** | P50 擴散底本體（進入前下降） | 91 / 45% |
| 青 | 存活期 | — |
| 洋紅 | 測試邊界中 | — |

### 已在 MC12 確認的驗收視窗

| 日期 | 應看到 |
|---|---|
| **2026-08-11 21:15 ~ 23:00** | 兩個型態疊在一起，本體 21:15~22:00 與 21:20~22:10 |
| **2026-07-28 20:15 ~ 21:25** | 單一型態，本體 20:15~20:50 |

滑鼠停在色塊上，`Plot1~Plot4` 應等於該根的 High/Low/Open/Close。

---

## 5. Next

**用戶裁定順序：C → A。C 已完成。**

| 順位 | 動作 | 狀態 |
|---|---|---|
| **0** | **驗收 Build_ID 260830 的 P49/P50 分色** | ⏳ **明天第一件事** |
| **1** | **A：P49/P50 指標** | ⏳ **開工前先照新檢查表跑 16 條，裁示點一次列給用戶** |
| 2 | P51-P54 擴散家族四變體 | ⏳ |
| 3 | P29-W2 粗尺度變體（89 個，74 個窗 1 看不到） | ⏳ |
| 4 | 共用資料層 `s16s_pivots.json` / `s16s_patterns.json` | ⏳ |
| 5 | 夜盤超額 2.3 倍的解釋 | ⏳ |

### 5.1 開 A 之前必做

**照 `pattern-definition-checklist` 跑 16 條**，把待裁示點**一次**列給用戶
（紀律 2：批次問，不要一次一題）。
P49/P50 沿用 P29 全部七段，唯一新東西是 M7，預期只有少數幾條需要裁示。

### 5.2 仍掛著的舊 BLOCKER

| # | 內容 |
|---|---|
| B-1 | L1 回測不可重現（同碼同參數 500 / 501 筆） |
| **B-2** | **四支 live 策略全部過不了 Rule #13 MDD，L3 的 95% MDD 達帳戶 106.3%** |

### 5.3 其他掛著的裁示

- **P47 號角頂**要不要立為「掛牌觀察」（n=259，t=2.09，7/8 年方向一致，
  但 33 檢定的 family-wise p=0.673）

---

## 6. Files

| 路徑 | 說明 |
|---|---|
| `.claude/skills/pattern-definition-checklist/SKILL.md` | **開 A 之前先讀這份** |
| `.claude/skills/pattern-logic-summary/SKILL.md` | 五段總整理格式 |
| `docs/research/S16S_P29_CLOSED_20260825.md` | P29 封閉規格 |
| `docs/research/S16S_P49_P50_SUMMARY_20260826.md` | P49/P50 五段總整理 |
| `docs/research/S16S_P29_screenshot_windows_20260826.md` | **驗收清單，含座標設定** |
| `docs/research/S16S_pattern_workflow_review_20260826.md` | 效率檢視 |
| P29 示意圖 | https://claude.ai/code/artifact/79ff51ff-ec21-4a24-9bc1-be99c4215c25 |
| P49/P50 示意圖 | https://claude.ai/code/artifact/30ee09ef-fae0-4742-9323-12c7a3cb7e67 |
| 型態全圖鑑 | https://claude.ai/code/artifact/22fa588b-51f5-43ce-8e11-bc301d4c35ef |

---

## 7. Git

- 分支 `main`，工作區乾淨，與 `origin/main` 同步
- **策略 `.pla` 未動**；指標 `Build_ID = 260830`
- 換機器開工前必做：`git config core.hooksPath .githooks`
- `s16s_5min.csv` 32 MB **不進 git**，換機器需由 1 分 K 母檔重建
  （`Desktop\Multichart_9\報價\TXF1 1 分鐘.txt`，MD5 `db35ecb739346b73fc2a1ccae5013582`）

---

## 8. 誠實聲明

1. **Build_ID 260830 的 P49/P50 分色，MC12 尚未跑過。** 260829 的換色已實機確認。
2. **P29 / P49 / P50 的報酬從未檢定**，也不該在用戶同意前檢定。
3. 今天我在「四條淺藍線」上**錯了兩次**：先怪 Monitor 指標、再叫用戶移除指標，
   **兩次都是推測不是檢查**。把問題推到終點的是加了診斷輸出那一版。
4. 效率檢視的效益是**預估**，尚未驗證。P51 做完才知道檢查表有沒有用。
5. 本文由 Claude 產出，**未經第二方審查**。
