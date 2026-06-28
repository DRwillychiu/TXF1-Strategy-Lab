# BOSS_VIEW Template — 老闆快速 View 標準格式

**用途**：每隻 promoted 到 live_simulation 或 live 的策略**強制**要有一份此格式的 BOSS_VIEW.md

**檔名規則**：`<策略名>_BOSS_VIEW.md`（與 strategy.md / DEPLOYMENT.md 同層）

**目標**：3 分鐘讓非技術老闆 / 主管 / 投委會理解策略本質、績效、風險

---

## 📋 必填 7 區段（按順序）

### 1️⃣ 標頭資訊（1 行）
版本 ｜ 回測期間 ｜ 狀態

### 2️⃣ 績效重點（**表格**）
必含 metrics（粗體 = 必出）：
- **淨利** (NTD 總獲利)
- **年化報酬 %**
- **獲利因子 gross**
- **獲利因子 adj（含滑價）**
- **勝率 %**
- **Sharpe 年化**
- **Sortino**
- **最大回撤 %**
- **總交易筆數 / 期間**
- **平均每筆獲利 NTD**
- 最大單筆 SL（avg or max）

### 3️⃣ 賺什麼錢（**1 段 + 3-5 個具體類型**）
- 一句話描述「賺什麼」（如「賺快速回檔的下殺錢」）
- 列點 3-5 個典型賺錢情境（含實例 ideal）
- 標示「不貪 X」principle（如「不貪長尾」）

### 4️⃣ 適合行情（**3 點列**）+ 不做行情（**1-2 點**）
- ✅ 適合：列 2-4 個 regime
- ❌ 不做：明確列哪些 regime / 為何擋
- 強調「portfolio 中由其他 sleeve cover」

### 5️⃣ 進場規則（**4 個重點**，不超過 5 點）
- 每點 1 句話，**白話**
- 結尾「→ 全部成立才動作」

### 6️⃣ 出場規則（**4 個情境表格**）
| 情境 | 動作 |
- 高紀律化、無情緒
- 列 TP / 移動鎖利 / SL / 時間止損 等
- 含合規緊急層

### 7️⃣ 風控配置（**列點**）
- 口數（1 contract / 加碼？）
- Portfolio cap %
- R-6 配對（若有）
- Kill triggers（自動停用條件）

---

## 🎯 結尾必有 2 區塊

### 一句話 pitch（**> 寫成 quote**）
> 「<策略本質一句話>」
> + 1-2 句補充

### 老闆決策摘要（**Q&A 表格**）
| 問題 | 答 |
|------|---|
| 這策略幹什麼？ | <1 句> |
| 多久進一次？ | <頻率> |
| 每筆賺多少？ | <NTD avg> |
| 最大會虧多少？ | <kill trigger + 史上 MDD> |
| 跟其他策略衝突？ | <portfolio 角色> |
| 為什麼上架？ | <KEY metrics + 期間> |
| 風險？ | <2-3 個 honest caveat> |

---

## ⚠️ 寫作規範

1. **長度** ≤ 1 頁（A4，~600-800 字）
2. **無 jargon**：不寫 BBW / ATR / WFA / Sharpe（如必須提及，加 1 句白話解釋）
3. **數字必填**：每個指標必有實際數據（不可寫 "TBD" 或 "TBC"）
4. **誠實 caveats**：風險區段必須寫真實限制（4 trades/year 心理壓力、alpha gap 等）
5. **白話 + 表格**：避免長段落，最多 3 段，其餘用表格
6. **ASCII 中文混排 OK**（這是給人看的 doc，不是 .pla）

---

## 📝 寫作 checklist（送 review 前自檢）

- [ ] 績效表格 11 個 metrics 全填
- [ ] 賺什麼錢一段含具體實例
- [ ] 適合 / 不適合各 2-4 點 regime 列點
- [ ] 進場 4 點全白話（無 jargon）
- [ ] 出場表格含 TP / SP / SL / 合規 4 層以上
- [ ] 風控含 portfolio cap % + kill triggers
- [ ] 一句話 pitch < 30 字
- [ ] 老闆 Q&A 含 7 個 questions
- [ ] 文件 < 1 頁
- [ ] 連結 strategy.md + DEPLOYMENT.md 詳細文件

---

## 🔗 引用 examples

- 範本：`strategies/live_simulation/S3_S_VolSqueezeShort_BOSS_VIEW.md`
- 未來：S4_L / S5_L / ... 每隻 promote 後**強制**寫此格式

---

## 📅 規範生效

| 日期 | 修訂 |
|------|------|
| 2026-06-28 | 初版（從 S3_S BOSS_VIEW 抽出標準）|

**強制範圍**：所有 `strategies/live_simulation/` 與 `strategies/live/` 內策略
