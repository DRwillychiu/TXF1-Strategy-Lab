# scripts/ — 驗證與分析工具

> 對應 live + live_simulation 策略的自動化驗證與分析腳本。
> 所有腳本必須 Windows + Python 3.10+ 可執行，繁中輸出用 utf-8。

---

## 一、Master 跨策略驗證

| 腳本 | 用途 |
|------|------|
| [`verify_all_live.py`](verify_all_live.py) | L1-L5 跨策略 110 項合規檢查（Settlement / SetStopLoss / Holiday / Registry / Kill） |

---

## 二、P3b Immediate Stop Guard 驗證（Rule #12）

| 腳本 | 對應策略 | 檢查數 |
|------|---------|--------|
| [`verify_l1_immediate_stop.py`](verify_l1_immediate_stop.py) | L1 TrendLong | 17 |
| [`verify_l2_immediate_stop.py`](verify_l2_immediate_stop.py) | L2 TrendShort | 15 |
| [`verify_l345_immediate_stop.py`](verify_l345_immediate_stop.py) | L3 + L4 + L5（合併） | 27 |
| [`verify_s1_immediate_stop.py`](verify_s1_immediate_stop.py) | S1 NightMomentum | 15 |

---

## 三、Settlement 模組驗證（Rule #11）

| 腳本 | 用途 |
|------|------|
| [`verify_settlement_flat.py`](verify_settlement_flat.py) | 6 隻策略 Settlement_Flat 7 元素合規 |
| [`verify_settlement_detection_proof.py`](verify_settlement_detection_proof.py) | 結算日偵測邏輯數學證明 |
| [`verify_strategy_holding_classification.py`](verify_strategy_holding_classification.py) | 策略持倉分類 × Settlement 角色矩陣 |

---

## 四、策略專屬深度驗證

| 腳本 | 對應策略 | 用途 |
|------|---------|------|
| [`verify_l4_v142.py`](verify_l4_v142.py) | L4 v14.2 | 67 項 A-G 七變體驗證 |
| [`verify_range_force_exit.py`](verify_range_force_exit.py) | L3 / L4 | RangeForceExit 部署驗證 |
| [`verify_s1_v22.py`](verify_s1_v22.py) | S1 v2.2 | 26 項基礎驗證 |
| [`verify_s1_v23.py`](verify_s1_v23.py) | S1 v2.3 | 日盤平倉重設計驗證 |
| [`verify_s1_v24.py`](verify_s1_v24.py) | S1 v2.4 | 隔夜 gap 機制驗證 |
| [`verify_s1_v25.py`](verify_s1_v25.py) | S1 v2.5 | Trail 機制驗證 |
| [`verify_s1_v26.py`](verify_s1_v26.py) | S1 v2.6 | 趨勢 filter 驗證 |

---

## 五、A/B 分析與回測解析

| 腳本 | 用途 |
|------|------|
| [`analyze_l5_v198_variants.py`](analyze_l5_v198_variants.py) | L5 v19.8 A/B 六變體實證分析 |
| [`analyze_settlement_backtest.py`](analyze_settlement_backtest.py) | 6 隻策略結算回測深度分析 |

---

## 六、執行範例

```bash
# 跑 master 驗證
python scripts/verify_all_live.py

# 跑 L1 P3b 驗證
python scripts/verify_l1_immediate_stop.py

# 跑結算偵測數學證明
python scripts/verify_settlement_detection_proof.py
```

所有腳本在策略 .pla 變更後**必須**重跑確認 PASS。

---

## 七、新增腳本紀律

1. 檔名格式：`verify_<scope>_<topic>.py` / `analyze_<scope>_<topic>.py`
2. 必須輸出 PASS/FAIL 計數
3. 失敗 → `sys.exit(1)` 讓 CI 能捕捉
4. UTF-8 輸出（Windows: `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`）
5. 引用 .pla 路徑用相對路徑（從 repo root）
6. 在本 README 加索引

---

## 八、已歸檔（不在此清單）

以下腳本因策略已 KILL 或歸檔，已移至對應策略的 archive 資料夾：
- `verify_s2_v06.py` → `strategies/research/archive/S02_InsideBarBreak_killed_20260622/_analyze_scripts/`
- `verify_s3_pullbackshort.py`、`verify_s3_v2.py`、`eval_s3_v204_institutional.py` → `strategies/research/archive/S03_RapidPullbackShort_archived_20260622/_analyze_scripts/`
- `analyze_s4-s9_*.py` → `strategies/research/archive/offRoadmap_2026Q2_killed/_analyze_scripts/`
- `analyze_l4_v145_ab.py` → `docs/archive/offRoadmap_2026Q2/`
- `_compute_yearly_metrics.py`、`_extract_portfolio_pnl.py` → `docs/archive/offRoadmap_2026Q2/`
