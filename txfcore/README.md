# TXF1 Python 專案（txfcore）

把 MultiCharts 上架策略轉成 Python。Q4 只做訊號平行比對、不下單；最快 2027/1 接下單大師 API。

## 一、怎麼跑

```
pip install -r requirements.txt          # 只需要 pytest（Python 3.11 以上）
run_tests.bat                            # 單元測試，約 2 秒
```

逐筆考題（Python 對 MC 報表逐筆相同，約 70 秒）：

```
set TXF1_MIN_DATA=D:\資料\TXF1_1_分鐘.txt      # MC 匯出 1 分 K，必須是 9/24 那份
python -m pytest -q tests\test_port_l2_v5_11.py tests\test_port_l4_v14_10.py
```

- 結算日曆綁 9/24 資料檔的雜湊（開頭 `4642037171d1`），換資料要重新反推，程式會擋
- 秘密（下單大師 API、TG）放 `.env`，範本是 `.env.example`；`.env` 不進 git

## 二、資料夾

| 位置 | 內容 |
|---|---|
| `txfcore/strategies/` | 策略**組裝檔**：只把模組接起來，不寫規則 |
| `txfcore/modules/` | 共用規則：`gates`（行事曆、Kill、時段、冷卻、趨勢過濾、連虧跳過）、`signals`（進場訊號）、`stops`（停損）、`exits`（出場） |
| `config/strategies/*.toml` | 參數；載入時自動與 `.pla` 預設值比對，不一致就報錯 |
| `txfcore/profiles/mc_compat.py` | 對 MC 用的 7 項成交設定（見第四節） |
| `txfcore/engine/`、`runtime/` | 回測引擎：成交、部位、單策略與多策略執行 |
| `txfcore/quotes/`、`tradecal/` | K 棒組成、日 K、交易日曆、結算日 |
| `txfcore/indicators/`、`metrics/` | 指標、績效 |
| `txfcore/contracts/` | 對外插頭（報價、下單、通知）；`broker`、`notify` 待接 |
| `tests/` | 單元測試、分層邊界、逐筆考題；`fixtures/` 是 MC 報表（唯讀） |
| `tools/` | 營運與研究工具（`report.py`、`signals.py` 已改用上架版） |
| `strategies/research/` | 五支上架 `.pla`（參數比對的來源） |

分層規則見 `txfcore/LAYERS.md`，由 `tests/test_layer_boundaries.py` 自動擋。

## 三、進度

| 策略 | 上架版 | Python | 對 MC |
|---|---|---|---|
| L2 TrendShort | v5.11 | `l2_trendshort_v5_11.py` | 96／96 逐筆相同 |
| L4 ConsolShort | v14.10 | `l4_consolshort_v14_10.py` | 135／135 逐筆相同 |
| L3 ConsolLong | v18.4 | 舊版移植（`l3_consollong.py`） | 待移植上架版 |
| L5 BreakoutLong | v19.20 | 舊版移植（`l5_breakoutlong.py`） | 待移植上架版 |
| L1 TrendLong | V3.2 | 舊版移植（`l1_trendlong.py`） | 待 Willy 定基準 |

`l2_trendshort.py`（v5.4）、`l4_consolshort.py`（v14.7）是舊版，研究工具還在用，之後退場。

## 四、對 MC 的 7 項成交設定（`mc_compat.py`）

1. 停損、限價進位到整點（買進停損往上、賣出停損往下）
2. 引擎停損只在進場那根有效
3. 進場那根可以被引擎停損出場
4. 滑價每口每邊 1,000 元，限價單不計；手續費 0
5. 日 K 按收盤日歸屬（前一晚夜盤＋當天日盤）
6. 結算日用 .pla 的靜態規則（第三個週三）；實盤改用資料推得的結算日
7. 同一根 K 棒可以先 TP1 限價、再停損

以上是**回測對 MC**用。實盤執行層（停損碰價就送、進場收盤就送）尚未實作。

## 五、新增一支策略的步驟

1. `config/strategies/<名稱>.toml`：`pla`、`mc_load_name`、`[params]`（與 .pla 一字不差）
2. 缺的規則先寫進 `txfcore/modules/`，附單元測試（`tests/test_modules.py`）
3. `txfcore/strategies/<名稱>.py` 只做組裝
4. `tests/test_port_<名稱>.py`：MC 報表放 `tests/fixtures/`，逐筆比對
5. 規則手冊：`docs/research/py_modularize_rules.md`（R1–R13）
