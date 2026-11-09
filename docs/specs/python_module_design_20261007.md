# Python 模組化設計（草案，2026-10-07，待 Willy 修正）

> 依據：Willy 10/7 18:46「完整拆解策略成各個項目的模組才是 py 化的優化；不同停損模組裡的函式未來也會被抓取使用；資料處理與模組化是首選」。
> 事實說明：repo 現有的分層規劃（`docs/specs/L1-L5_layer_plan.md`，9 月）把每支策略放在一個檔案（層 2 `strategies/lx_*.py`），沒有寫到停損、進場等策略內模組。這一份是補上那一層。

## 一、原則

- 策略檔只負責「組裝」：讀設定、把共用模組串起來、決定順序。規則本身都在模組裡。
- 每個模組是獨立函式，不依賴特定策略，輸入輸出寫清楚，可以單獨被其他策略或新專案抓去用。
- 參數不寫在程式裡：每個策略版本一份設定檔，讀取時自動比對 .pla 預設值，不一致就紅燈。
- 帳密、API 位址、TG token 放 `.env`（不進 git，只提交 `.env.example`）。
- MC 相容的引擎行為（今天校正的 7 項）集中成一個「MC 相容設定檔」，不再散落在呼叫端。
- 重構的護欄：L2 96／96、L4 135／135 這兩份考題，重構前後必須都通過。

## 二、目錄（新增與調整）

```
txfcore/
  data/                         ← 資料處理（首選，先做）
    sources/mc_minutes.py         讀 MC 匯出 1 分 K（＋資料版本檢查）
    sources/recorder.py           錄製系統（之後；6 商品、近遠月）
    bars.py                       15／45／60 分 K
    daily.py                      日 K（MC 收盤日歸屬）、週 K
    align.py                      Data2／Data3 對齊（讀已收完的那一根）
    rollover.py                   換月（期交所規則＋下單大師雙重確認，之後）
  calendar/                     ← 現在的 tradecal 搬過來
    holidays.py  settlement.py  registry.py
  modules/                      ← 策略內共用模組（本次重點）
    gates/      進場閘門
      calendar_gate.py            假日尾盤、登錄表到期、結算日（靜態／資料兩種）
      session_block.py            時段封鎖（L4 02:00–04:59、L5 等）
      kill.py                     Kill 開關（擋進場＋平倉）
      cooldown.py                 出場後冷卻 N 根
      trend_filter.py             週線均線濾網（L2）、日線趨勢封鎖（L3/L4）、週線濾網（L1）
      loss_streak.py              連虧暫停／跳過下一段／損失記憶（L1、L2、L4、L5）
    signals/    進場訊號
      box.py                      箱體偵測（L3、L4、L5）
      breakdown.py                跌破通道＋ZLEMA（L2 空頭）
      crash.py                    暴跌腿（L2）
      spring.py                   誘多後跌回（L4）
      breakout.py                 均線＋ATR 突破（L1）、箱頂突破（L5）
      reentry.py                  二次進場（L1、S16）
    stops/      停損
      engine_stop.py              SetStopLoss 距離（含 % 與點數上限）、是否只在進場根
      initial_stop.py             凍結初始停損（最緊的一條）
      caps.py                     % 上限、點數上限
      trailing.py                 最低收盤＋ATR、最低低點＋ATR 棘輪、MA 移動停利
      hard_stop.py                硬停損（進場價＋N 點，每根都掛）
    exits/      出場
      forced.py                   Kill／登錄表／假日／結算 的優先序 0
      profit_protect.py           峰值回吐保護（門檻 % 或點數、保留比例）
      take_profit.py              結構停利、回抽停利、TP1 分批
      time_exit.py                時間出場
      structure_exit.py           週線出場、箱體失效出場
    chain.py                    出場鏈（ExitFired 短路、鏈外單）
  strategies/
    l2_trendshort_v5_11.py        只剩組裝（約 100 行）
    l4_consolshort_v14_10.py
    ...
  profiles/mc_compat.py         MC 相容設定：tick 進位、引擎停損只活進場根、同根停損、
                                限價不計滑價、成本口徑、日 K 歸屬、靜態結算日
config/
  strategies/L2_v5.11.toml  L4_v14.10.toml ...
.env.example                    下單大師 API、TG、錄製系統路徑（實盤層用）
```

## 三、L2、L4 現有程式對應到模組

| 現在在策略檔裡的規則 | 搬到 |
|---|---|
| 假日尾盤表、登錄表、靜態結算日（L2 自帶一份假日表 ← 重複） | `gates/calendar_gate.py`（唯一一份） |
| 週線 13 週均線濾網（L2） | `gates/trend_filter.py` |
| 日線 MA20／MA60 封鎖＋F6（L4） | `gates/trend_filter.py` |
| 方案 B 連虧跳過（L2）、R1 連虧跳過（L4） | `gates/loss_streak.py` |
| 冷卻 8 根（L4） | `gates/cooldown.py` |
| 深夜封鎖（L4） | `gates/session_block.py` |
| 空頭訊號、暴跌腿（L2） | `signals/breakdown.py`、`signals/crash.py` |
| 60 分箱體、誘多區（L4） | `signals/box.py`、`signals/spring.py` |
| 引擎停損距離（L2、L4） | `stops/engine_stop.py` |
| 凍結初始停損、% 與 450 上限 | `stops/initial_stop.py`、`stops/caps.py` |
| 追蹤停損（L2 最低收盤＋ATR、L4 最低低點＋ATR 棘輪） | `stops/trailing.py` |
| 硬停損（L2） | `stops/hard_stop.py` |
| 優先序 0、峰值回吐、結構／回抽停利、TP1、時間出場、週線出場、箱體失效 | `exits/*` |

## 四、驗收（每一步都要過）

1. 先做 `data/`、`calendar/`、`profiles/mc_compat.py` → L2 96／96、L4 135／135 仍通過
2. 抽 `gates/` → 同上
3. 抽 `stops/`、`exits/` → 同上
4. 抽 `signals/` → 同上；L2、L4 策略檔只剩組裝
5. 設定檔取代程式內參數 → 參數考題改讀設定檔，仍通過
6. 每個模組有自己的單元測試（輸入→輸出），不靠整支回測
7. 之後 L3、L5、L1 直接用模組組裝，缺的模組才新增

## 五、待 Willy 修正

1. 模組切法（上面二）是否符合你其他專案的拆法？有沒有要加、要併的？
2. 設定檔格式：TOML（建議，可寫註解）或 YAML、JSON
3. `.env` 內容：下單大師 API、TG、錄製系統路徑，還有其他嗎？
