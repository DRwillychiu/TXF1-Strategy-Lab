# 檔案路徑與儲存方式

> 這份文件說明本次產出的每一個檔案該放在 `TXF1-Strategy-Lab` 的哪裡、為什麼。
> **每次我產出檔案都會附這份對照。**

---

## 一、放置規則（三條，之後一律照這個走）

**規則 1　`txfcore/` 與 `scripts/` 嚴格分開**

`scripts/` 現有 40 幾支拋棄式研究腳本加一堆 `_temp_*.pkl`。
`txfcore/` 是要被信任的長期資產，必須有測試、有型別、有版本。
**兩者永不互相 import。**

**規則 2　規格文件放 `docs/specs/`，不放 `docs/research/`**

`docs/research/` 是一次性的研究紀錄。
`docs/specs/` 是**寫程式時要看的東西**，跟著程式碼一起維護、一起被 diff。

**規則 3　`.pla` 的 inputs 變成 config，不寫死在程式碼裡**

容差門檻、模式開關、SL_Pct 這些值必須放 git 追蹤的獨立檔案，
修改需獨立 commit 附理由（規劃書層 4 的防篡改要求）。

---

## 二、本次產出的完整對照表

從壓縮檔解開後，直接把 `txfcore/`、`tests/`、`docs/` 三個目錄合併進 repo 根目錄即可。

**分層的權威定義在 `txfcore/LAYERS.md`，依賴規則由 `tests/test_layer_boundaries.py` 機械檢查。**

```
TXF1-Strategy-Lab/
│
├── txfcore/                          ★ 新增。長期資產，與 scripts/ 嚴格分開
│   ├── LAYERS.md                     ✓ 分層與依賴規則（權威定義）
│   │
│   │  ── 層 0 基礎設施（不在流上，全層依賴；不得依賴任何其他套件）──
│   ├── types/        ✓ mctime.py bar.py orders.py
│   ├── costs/        ✓ fees.py
│   ├── metrics/      ✓ drawdown.py
│   ├── journal/      ○ 事件日誌（append-only，重放的唯一輸入）
│   ├── timing/       ○ event/receipt/decision 三戳記 + 時鐘插頭
│   ├── state/        ○ 持久化與崩潰復原 + killswitch
│   ├── lineage/      ○ 血緣雜湊 code+config+data+calendar
│   ├── obs/          ○ 結構化日誌 + 心跳 + 觸發次數監控
│   │
│   │  ── 共用支撐層（.pla 裡不存在，五支共用；被層 2 呼叫）──
│   ├── indicators/   ✓ core.py
│   ├── tradecal/     ✓ registry.py gates.py
│   ├── engine/       ○ fill_mc12 orders position protective context
│   │
│   │  ── 層 1 到層 5（資料流）──
│   ├── quotes/       ○ 1分K→各週期聚合、時段與網格、對齊
│   ├── strategies/   ✓ base.py l2_trendshort.py
│   ├── risk/         ○ 停機開關、部位上限、券商部位對帳迴路
│   ├── backtest/     ○ 換三顆插頭的驅動器
│   ├── parity/       ○ mc_report replay diff + 黃金測試集
│   ├── notify/       ○ message channels dedupe heartbeat
│   └── broker/       ○ 券商介面（終點已定為自動下單，此層必要）
│
├── tests/
│   ├── test_txfcore.py               ✓ 33 個功能測試
│   └── test_layer_boundaries.py      ✓ 33 個依賴檢查
│
└── docs/
    └── specs/                        ★ 新增目錄
        ├── L2_TrendShort_spec.md
        ├── L1-L5_cross_comparison.md
        └── PLACEMENT.md              本檔

✓ 有內容    ○ 目錄已建但為空
完成度 6/18 套件
```

**空目錄是刻意保留的。** 它讓「還沒做」在檔案樹上看得見，而不是靠人記得；
`test_every_declared_package_exists` 會確保 LAYERS.md 宣告的套件都存在。

---

## 二之二、依賴規則

```
層 0                       不得依賴任何其他 txfcore 套件
共用支撐  indicators tradecal engine    可依賴 層 0
層 1      quotes                        可依賴 層 0
層 2      strategies                    可依賴 層 0 + 支撐   ← 不得碰 quotes/notify/broker
層 3      risk                          可依賴 層 0 + 支撐   ← 不得碰 quotes/notify/broker
層 4      backtest parity               可依賴 層 0 1 2 3 + 支撐
層 5      notify broker                 可依賴 層 0
```

**最重要的一條**：`strategies/` 與 `risk/` 不得 import `quotes/` `notify/` `broker/`。
鐵則是「回測與即時跑同一份策略碼」；策略層若能直接抓報價或直接下單，
那份程式碼就綁死在某一端，換插頭就不再是換插頭。

---

## 三、已存在檔案的處置

| 檔案 | 動作 | 理由 |
|---|---|---|
| `CLAUDE.md` | **需修正** | 規格與 README.md 矛盾：口數 2 vs 1、滑價單邊 1000 vs round-trip 1000 |
| `README.md` | **需修正** | 同上。且實盤跑的是微台，兩份文件都寫大台 |
| `backtest/run_backtest.py` | 不動 | 已標 DEPRECATED，留作歷史紀錄 |
| `scripts/taifex_calendar.py` | **暫不搬** | 等 `txfcore/tradecal/` 的註冊表通過驗證後再搬，避免同時有兩份真相 |
| `scripts/compare_mc12_reports.py` | 暫不搬 | 等層 4 對帳層動工 |

**`CLAUDE.md` 與 `README.md` 的矛盾必須先解，因為「回測期初資金」這一題有三個候選值**
（200 萬 / 未列 / 30 萬），而選哪個會直接改變 MDD 的百分比。

---

## 四、`.gitignore` 需要追加

自動下單意味著 repo 裡會出現券商相關的東西。

```gitignore
# MC12 匯出的原始 K 棒（1 分 K 檔案很大，可重新匯出）
data/mc_export/

# 實盤紀錄與對帳報告（含帳務資訊）
data/live_records/
data/parity_reports/

# 券商連線設定與憑證 —— 任何情況都不得進 git，即使是私有 repo
config/broker_*.yaml
config/*_credentials.*
*.pfx
*.p12
.env.broker
```

---

## 五、建議現在建立的兩個檔案（我還沒產出，需要你的資料）

**`docs/specs/strategy_baseline.md`** —— 釘死今天的版本

```markdown
| 策略 | 檔名 | 版本 | SHA-256 | 釘死日期 |
|---|---|---|---|---|
| L1 | ... .pla | V3.2 | ⬜ | 2026-09-06 |
| L2 | ... .pla | v5.4 | ⬜ | 2026-09-06 |
| L3 | ... .pla | v15.1 | ⬜ | 2026-09-06 |
| L4 | ... .pla | v14.7 | ⬜ | 2026-09-06 |
| L5 | ... .pla | v19.9-R1 | ⬜ | 2026-09-06 |
```

雜湊變了 → 該支的對帳作廢重跑。這是防 L3 基準線事故的唯一機制。

**`config/tolerances.yaml`** —— 對帳容差，事前登記

```yaml
# 修改本檔需獨立 commit 並附理由。
# diff 工具會在報告開頭印出本次使用的門檻與其 commit。
L2_TrendShort:
  decision:           # 決策對帳：時間 / 方向 / 單型 / 口數
    max_diff_trades: 0
  fill:               # 成交對帳：容許差異但須歸因到成交假設
    max_price_diff_pts: null   # 待定
  performance:        # 績效對帳：不設標準（MC 不是判官）
    enabled: false
```

---

## 六、執行方式

```bash
cd TXF1-Strategy-Lab
python -m pytest tests/ -q          # 33 passed
```

`txfcore` 目前無外部相依，只用標準函式庫。測試需要 `pytest`。

---

## 七、下次產出的路徑（先講好）

| 產出 | 路徑 |
|---|---|
| L4 規格表 | `docs/specs/L4_ConsolShort_spec.md` |
| L4 移植 | `txfcore/strategies/l4_consolshort.py` |
| 1 分 K 聚合器 | `txfcore/quotes/bars.py` |
| 時段與網格 | `txfcore/quotes/session.py` |
| MC12 成交模型 | `txfcore/engine/fill_mc12.py` |
| 回測驅動器 | `txfcore/backtest/runner.py` |
| 對帳工具 | `txfcore/parity/diff.py` |
| 黃金測試集 | `tests/golden/` |
