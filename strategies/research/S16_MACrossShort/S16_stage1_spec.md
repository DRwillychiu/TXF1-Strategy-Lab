# S16 MACrossShort — Stage-1 設計討論

**啟動日**：2026-06-28（待 S4_S 完成）
**前置**：用戶 2026-06-28 ruling 加入新策略（override Rule R-1）
**規範**：必須通過 W0 → W1 → W2 → W3 → W4 → W5 → W6 完整流程
**等候**：S4_S 完成後啟動（Rule R-3 不可平行開發）

---

## 一、用戶給的初始 spec

| 維度 | 規格 |
|------|------|
| **時框** | **15M**（固定，short-cycle）|
| **指標** | MA Fast + MA Slow（雙均線交叉）|
| **進場** | **死亡交叉**（Fast MA cross down Slow MA）|
| **出場** | **黃金交叉**（Fast MA cross up Slow MA）|
| **MA 參數** | **可優化**（W4 Phase 2 GA 決定）|
| **參數上限** | 必須**符合 15M 操作週期的時間限制**（避免長週期 MA 失去 short-cycle 意義）|

---

## 二、賺什麼錢

**賺「中短期動能下行趨勢」的順勢空頭錢**：
- 15M 時框觀察 Fast MA 跌破 Slow MA → 短期趨勢轉空
- 持倉直到 Fast MA 重新站回 Slow MA → 趨勢反轉認錯出場
- 純動能交叉策略，無預測，無逆勢

---

## 三、適合 vs 不適合行情

### ✅ 適合
- **下行趨勢延續**（持續性下殺）
- **空頭轉折確立段**（剛從多頭轉空）
- **大波段中的盤面整理後續跌**

### ❌ 不適合
- **強勢多頭**（whipsaw 嚴重，連續死叉假信號）
- **緊密盤整**（MA 反覆交叉、雙打耳光）
- **間歇性反彈**（cross 後立刻 cross back）

---

## 四、Stage-1 4 段討論（待 user 確認 + W0 後 lock）

### A. 內容（待優化 ranges 由 W4 決定）
- **主週期**：15M（user 鎖定）
- **建議 MA 範圍**（待 Phase 2 GA）：
  - Fast MA: 5 / 8 / 10 / 12 / 15
  - Slow MA: 20 / 25 / 30 / 40 / 50
  - 約束：Slow > Fast × 2，且 Slow ≤ 50（15M × 50 ≈ 12.5 小時 = 1.5 個交易日，仍 short-cycle）
- **進場**：
  - 死亡交叉觸發即 sell short next bar at market
  - 加合規 gates（settlement / holiday / kill / registry）
- **出場**：
  - 黃金交叉 → buy to cover next bar at market（主要出場）
  - **必要保護**：SL（避免一根反彈大棒打爆）
  - **時間止損**（避免持倉跨假日）
  - **無 TP**（讓 cross 自然出場 = 讓利潤奔跑直到趨勢反轉）

### B. 優點
- **規則極簡單**（單一指標雙條件），可解釋性最高
- 跟 S3_S（波動率突破）、L2（週線過濾 Donchian）、L4（盤整假突破）、S3（拉回狙擊）結構性**不同 alpha source**
- 15M 短週期 → trade 頻率較高（預期 30-80 筆/年），sample 充足
- 黃金交叉出場 = **內建讓利潤奔跑機制**，符合趨勢策略哲學

### C. 缺點
- **TXF1 2020-2026 主要為多頭** → 純 MA cross 短週期可能 whipsaw 嚴重
- 無趨勢過濾 → 在強多頭年（如 2024）可能連續死叉假信號
- 出場依賴 cross back → MA 反應慢，可能讓回 60%+ 浮盈

### D. 為什麼合適
- 補強做空 sleeve 厚度（用戶 2026-06-28 ruling 主旨）
- 補上 portfolio 中缺的「純動能下行 sleeve」（live + live_sim 4 隻空頭都有複雜 trigger）
- 15M 時框跟 L3/L5 部分 component 兼容
- 規則簡單 = live monitor 容易（人工判讀直覺）

---

## 五、W0 Alpha Pre-Verify Plan

| Gate | 標準 |
|------|------|
| Trigger 頻率 | ≥ 30 instances/year（15M 短週期應 trigger 頻繁）|
| 後續 N bar 方向 hit rate | ≥ 40%（保守低於 50% 因 MA cross 隨機性）|
| Risk-reward ratio | ≥ 1.0（cross-based exits，無強制 TP/SL ratio）|
| 跨年穩定 | 至少 40% 年份有正 PnL（多頭年預期虧損）|

### Python script TODO（待 S4_S 完成後）
1. Load TWII 15M data (2018-2026)
2. For each (Fast, Slow) combo ∈ {5,8,10,12,15} × {20,25,30,40,50}:
   - Detect death cross (Fast crosses below Slow)
   - Forward-test entry: short next bar
   - Detect golden cross (Fast crosses above Slow): cover
   - Compute metrics
3. Find best (Fast, Slow) by Net Profit + sample 健康度
4. Compute 4 gates on best combo

→ **FAIL（whipsaw 嚴重）→ KILL with FINAL_VERDICT.md**
→ **PASS → 進 W1 strategy.md + 4 段討論 lock**

---

## 六、預期挑戰（warning）

1. **Whipsaw 風險極高**：純 MA cross 在多頭 regime 多數情況下會 false signal
2. **可能需加 trend filter**（如 Daily MA filter, 跟 S3_S regime filter 類似），但這違反**用戶 "規則極簡單" 設計初衷**
3. **W4 WFA 可能 fail**（因 MA cross alpha 對參數敏感，sample drop）
4. **L24 風險**：若加 filter 救績效，會違反 lesson L24「regime sub-filter 削 alpha」

---

## 七、相關文件

- ROADMAP: `docs/policies/OFFICIAL_ROADMAP.md` Batch 04 S16
- Spec doc: 本檔
- Lessons reference: L24 (不可加 event/regime filter) + L25 candidate (regime filter on small sample kills)
- User ruling: 2026-06-28 chat
