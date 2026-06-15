# strategies/research/ — 研究中策略（每週 5 組新批次）

> 用戶規範（2026-06-13）：每週新增 5 組研究策略，按 **ISO 週號** 分資料夾。

---

## 📅 時間軸資料夾結構（生效中）

```
strategies/research/
├── README.md                  ← 本檔案（研究工作流總覽）
│
├── 2026-W24/                  ← 當前週（6/8-6/14，本週）
│   └── README.md              ← 本週批次摘要（待填入 5 組策略）
│
├── 2026-W25/                  ← 下週（6/15-6/21）
│   └── ...
│
├── 2026-W26/ ...              ← 之後每週累積
│
└── archive/                   ← 週批次系統前的歷史檔
    ├── README.md
    ├── batch01_S2-S5/         ← 第一批（含原 S1，已升級至 live_simulation）
    ├── batch02_S6-S10/        ← 第二批（指數位階論系列，2026-06-07）
    ├── batch03_S11-S15/       ← 第三批（多策略類型，2026-06-07）
    └── _batch_summaries/      ← 各批次跨策略摘要
```

---

## 🗓 週號對照表（2026 H2）

| ISO 週號 | 日期區間（週一-週日）| 用途 |
|----------|---------------------|------|
| 2026-W24 | 6/8 - 6/14 | 本週（S16-S20）|
| 2026-W25 | 6/15 - 6/21 | 下週（S21-S25）|
| 2026-W26 | 6/22 - 6/28 | (S26-S30) |
| 2026-W27 | 6/29 - 7/5 | (S31-S35) |
| 2026-W28 | 7/6 - 7/12 | (S36-S40) |
| 2026-W29 | 7/13 - 7/19 | (S41-S45) |
| 2026-W30 | 7/20 - 7/26 | (S46-S50) |
| 2026-W31 | 7/27 - 8/2 | (S51-S55) |
| ... | ... | ... |

**ISO 週號計算規則**：週一為週的第一天；包含當年第一個週四的週為 W1。

**Linux 取得本週**：`date +%G-W%V`（macOS：`date +%Y-W%V`）

---

## 📂 單週資料夾標準結構

```
2026-W25/
├── README.md                       ← 本週 5 組策略狀態摘要
├── S21_StrategyName/
│   ├── S21_StrategyName.pla        ← PowerLanguage 程式碼（必須）
│   ├── S21_StrategyName_strategy.md ← 策略邏輯說明（必須）
│   ├── S21_StrategyName_annotated.md ← 中文逐行註解（必須）
│   ├── STRATEGY_GEN_Name.txt       ← 同 .pla 內容，方便 MC12 匯入
│   └── results.json                ← P1-P3 回測結果（測完才有）
├── S22_StrategyName/  ...
├── S23_StrategyName/  ...
├── S24_StrategyName/  ...
└── S25_StrategyName/  ...
```

---

## ✅ 每週新增 5 組策略 — 操作步驟

### Step 1: 開新週資料夾
```bash
mkdir strategies/research/2026-Www         # 替換 ww 為當前 ISO 週號
mkdir strategies/research/2026-Www/Sxx_Name
```

### Step 2: 必備 3 份文件
每個 `Sxx_Name/` 內須有：
1. **`Sxx_Name.pla`** — PowerLanguage 程式碼
2. **`Sxx_Name_strategy.md`** — 策略邏輯說明（白話）
3. **`Sxx_Name_annotated.md`** — 中文逐行註解（教學用）

### Step 3: 遵守 CLAUDE.md 程式碼規範
- 所有參數 `inputs:` 宣告
- 變數 `v_` 前綴
- 進場：`buy/sell short next bar at X stop/limit`
- 出場：`sell/buy to cover next bar at X stop`
- 名稱前綴 `STRATEGY_GEN_`
- 進場條件 ≤ 5 個
- **每隻策略 < 150 行**
- 用 `v_Prev_MP` 追蹤前根部位
- Data2 用 `[1]` 已收盤索引（不可前瞻）

### Step 4: P1-P3 三階段驗證
```bash
# P1 參數敏感度（3D 表面圖、確認高原而非尖峰）
python backtest/optimize/param_sensitivity.py --strategy Sxx_Name

# P2 Walk-Forward（IS 24m / OOS 6m / 9 窗口）
python backtest/optimize/walk_forward.py --strategy Sxx_Name

# P3 Monte Carlo（10,000 次序列打亂，95% MDD）
python backtest/optimize/monte_carlo.py --strategy Sxx_Name
```

### Step 5: 寫週批次 README
在 `2026-Www/README.md` 列出 5 組策略：
- 名稱、類別、方向、週期
- P1-P3 通過/不通過狀態
- 是否準備升級至 live_simulation/

### Step 6: 通過 P1-P3 後升級
```bash
git mv strategies/research/2026-Www/Sxx_Name strategies/live_simulation/Sxx_Name
```

---

## 🎯 品質門檻（CLAUDE.md 標準）

| 指標 | 門檻 |
|------|------|
| Walk-Forward Efficiency | > 50% |
| Monte Carlo 95% MDD | < 帳戶 30% |
| 參數高原寬度 | > 參數範圍 20% |
| OOS Profit Factor | > 1.0 |
| 每月最少交易筆數 | ≥ 2 |

---

## 🔢 策略編號規範（避免衝突）

| 區段 | 用途 | 已使用 |
|------|------|--------|
| L1-L9 | 實盤上架策略 | L1-L5（live/）|
| S1-S15 | 歷史研究策略（pre-weekly 系統）| 全部（S1→live_simulation, S2-S15→archive）|
| **S16 起** | **新週批次研究策略** | 待 W24 使用 |

**規則**：新策略一律 S16 開始連續編號，不再回收已用編號。

---

## 📚 跨週主題索引（更新中）

各週批次以「主題」分類較易追蹤，例如：
- 2026-W24: TBD（待第一週實際選題）
- 2026-W25: TBD
- ...

歷史主題（archive 內）：
- batch01: 基礎時段/突破/動能（S2-S5）
- batch02: 指數位階論系列（6/5 崩跌缺口，S6-S10）
- batch03: 多策略類型擴展（時段/動能/波動率/多時框/反轉，S11-S15）

---

## 🚀 三層晉升路徑

```
research/2026-Www/Sxx_Name/   ──[P1-P3 PASS]──►   live_simulation/Sxx_Name/
                                                     │
                                                     └─[模擬 ≥30 筆 + PF≥1.2]──►  live/Lxx_Name/
```

---

## 📋 參考

- [CLAUDE.md](../../CLAUDE.md) — 專案總覽 + 程式碼規範
- [strategies/live/README.md](../live/README.md) — 實盤上架清單
- [strategies/live_simulation/README.md](../live_simulation/README.md) — 模擬中清單
- [archive/README.md](archive/README.md) — 歷史批次說明
