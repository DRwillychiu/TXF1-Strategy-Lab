# Claude Code 策略深度優化工作流程

## 前置準備

### Step 1: Clone Repo
```bash
git clone https://github.com/DRwillychiu/TXF1-Strategy-Lab.git
cd TXF1-Strategy-Lab
```

### Step 2: 安裝依賴
```bash
pip install yfinance pandas numpy matplotlib seaborn
```

### Step 3: 更新市場資料
```bash
python backtest/fetch_data.py
```

---

## 優化流程（每隻策略 4 Phase）

### 開始優化一隻策略時，告訴 Claude Code：

```
我要優化策略 S1 NightMomentum。
請依序執行 Phase 1 → 2 → 3 → 4，每個 Phase 完成後：
1. 更新 optimization/logs/B01_S1_NightMomentum.md 的對應區塊
2. 更新 optimization/TRACKER.md 的對應欄位
3. 如果某個 Phase FAIL，停下來告訴我失敗原因和建議修復方向
4. commit 每個 Phase 的結果
```

### Phase 1 指令範例：
```
對 S1 NightMomentum 執行參數敏感度分析：
- LookbackBars: 2 到 10，步長 1
- StopLossPts: 30 到 120，步長 10
- EntryOffset: 0 到 25，步長 5

對每個參數掃描 PF 和淨利，繪製圖表。
判斷是否有高原（高原寬度 > 範圍 20%）。
結果寫入 optimization/logs/B01_S1_NightMomentum.md Phase 1 區塊。
```

### Phase 2 指令範例：
```
對 S1 NightMomentum 執行 Walk-Forward 優化：
- IS: 24 個月, OOS: 6 個月, 步長: 6 個月
- 在 IS 中用 Phase 1 確認的參數範圍做網格搜索
- 用最佳 IS 參數在 OOS 上測試
- 計算 WFE

python backtest/optimize/walk_forward.py --strategy NightMomentum

結果寫入 optimization/logs/B01_S1_NightMomentum.md Phase 2 區塊。
WFE < 50% → FAIL，停下來討論。
```

### Phase 3 指令範例：
```
對 S1 NightMomentum 執行 Monte Carlo 壓力測試：
- 用 Walk-Forward 最終確認的參數跑完整回測
- 取得所有交易 PnL 序列
- 執行 10,000 次隨機重排
- 計算 95% MDD 和破產機率

結果寫入 optimization/logs/B01_S1_NightMomentum.md Phase 3 區塊。
95% MDD > 90,000 或破產率 > 5% → FAIL。
```

### Phase 4 指令範例：
```
將所有已 PASS 策略做組合分析：
- 計算策略間 daily return 相關性矩陣
- 模擬等權配置的組合 equity curve
- 計算組合 Sharpe, MDD, PF
- 測試加入新策略是否改善組合

結果寫入各策略 Phase 4 區塊 + TRACKER.md。
```

---

## 策略判定後的處理

### PASS 策略
1. 確認最終參數
2. 更新 PowerLanguage 程式碼中的 inputs 預設值
3. 匯出 `.pla` 格式供 MC12 匯入（手動）
4. 標記 TRACKER.md 為 🟢
5. Git commit + push

### FAIL 策略
1. 記錄失敗原因到 optimization/logs/
2. 記錄到 TRACKER.md「FAIL 策略墓地」
3. 評估是否值得修復
4. 如果值得 → 建立修復分支，記錄修復嘗試
5. 如果不值得 → 歸檔，等下一批新策略

### 提早完成
- 更新 TRACKER.md 狀態
- 可以提前開始下一批策略的 Phase 1
- 或對已 PASS 策略做進階優化（加入新濾網、調整時段等）

### 來不及完成
- 更新 TRACKER.md 標記 ⏸️ 暫停，附上目前進度
- 記錄已完成的 Phase 結果
- 下次繼續時從暫停處恢復

---

## Git Commit 規範

```
feat: B01-S1 Phase1 complete - param sensitivity analysis
feat: B01-S1 Phase2 complete - WFE=67% PASS
feat: B01-S1 Phase3 complete - MC 95% MDD=52K PASS
feat: B01-S1 Phase4 complete - correlation 0.12 with TL
feat: B01-S1 FINAL PASS - all 4 phases cleared
fix: B01-S3 Phase2 FAIL - WFE=33%, moving to graveyard
```

---

## 進階優化（PASS 後可選）

### 5a. 時段過濾
測試只在特定時段交易是否改善績效（日盤 vs 夜盤 vs 特定小時）

### 5b. 波動率體制過濾
用 VIX 或 ATR 百分位區分高/低波動環境，分別測試策略表現

### 5c. 動態部位大小
Kelly Criterion 或 Fixed Fractional 替代固定 1 口

### 5d. 多策略輪動
根據近 N 期表現動態開關策略
