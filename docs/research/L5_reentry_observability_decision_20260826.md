---
建立日期: 2026-08-26
主題: L5 二次進場可讀性 — 為什麼不貼標籤，改印 log
狀態: 程式碼已寫、已推雲端；MC12 物理驗證未做
前置: docs/research/L2L5_reentry_label_decision_20260825.md
---

# L5 二次進場可讀性 — 決策紀錄

## 1. 一句話

L2/L3/L4 貼標籤，**L5 不貼**。L5 的 28 張出場單全部綁在進場名稱上，
改進場標籤會讓那些出場單失效、部位失去停損。改為在進場時印一行 log。

## 2. 阻擋點（實測，非推論）

```
from Entry 綁定數
  L5   28   (BL_Entry_Bot 14 + BL_Entry_Mid 14)
  L3    0
  L2    0
  L4    0
```

L5 不追蹤哪條腿開著。它無條件同時發出兩條腿的出場單，靠 `from Entry`
讓 MC 路由，不相干的自動作廢。這是 L5 獨有的結構。

`L3/L2/L4 = 0` 是這條決策成立的關鍵：它們的標籤化是純字串替換，
所以 L5 的例外**有明確技術邊界**，不是隨意的不一致。

## 3. 三個方案的實際成本

| | B 標進場 | C 標出場 | **F 印 log（採用）** |
|---|---|---|---|
| 動到下單語句 | 28 | 28 | **0** |
| 新增標籤 | 2 | 22 | **0** |
| 新增可執行行數 | ~100 | ~100 | **13** |
| 涵蓋引擎 `Stop Loss` | 是 | **否** | **是** |
| 最壞失效後果 | **部位裸奔** | 標籤標錯 | 少一行 log |
| 退化錨點 | 需回測驗證 | 需回測驗證 | **數學恆等** |
| 報表內直接可讀 | 是 | 是 | 否，需 join |

**「C 比較簡單」是被推翻的假設。** 全庫零先例用變數當下單標籤，
`iff()` 寫法不成立，C 必須逐張寫 if/else，語句數與 B 相同。

## 4. F 關掉的盲點

L5 的 `SL_Pct = 1.0`（不是 0）。引擎層 `SetStopLoss` 可以在**沒有任何
`Sell()` 語句觸發**的情況下平倉，報表顯示為 `Stop Loss`，2020-2026 回測
中發生 1 次（178 筆中）。

**任何掛在出場端的標籤都標不到這條路徑。** log 標得到。

## 5. F 的代價（誠實列出）

1. **報表打不開就看不見。** 要用 Date+Time join，多一個步驟。
2. **分批出場重複計數。** 6 次分批在報表上是兩筆獨立交易，共用同一個
   時間戳，會繼承同一個旗標 → 二次進場「交易數」比「事件數」多 6。
   join 腳本會發警告。（此問題 B、C 同樣有，非 F 獨有。）
3. **`Print` 拖慢最佳化。** 已加 `Debug_Entry_Log` input，跑 sweep 前設 False。

## 6. 改了什麼

檔案：`strategies/research/L5_BreakoutLong/L5_v199_R1/L5_BreakoutLong_v199_R1.pla`
（live 一個位元組沒動）

```
input   Debug_Entry_Log(true)
vars    v_Prev_MP, v_Episode_ID, v_Episode_Entries
[SEC-1c] 箱型 episode 上升緣計數器
[SEC-3b] 每次成交印一行:
         L5_ENTRY,Date,Time,EntryPrice,EpisodeID,EntryNo,BoxTop,BoxBtm
         EntryNo = 1 首次進場 / >= 2 二次進場
[SEC-6]  v_Prev_MP = MarketPosition（腳本最末行）
```

**順帶修掉一個既有違規**：L5 原本完全沒有 `v_Prev_MP`，
違反 CLAUDE.md PowerLanguage 規範第 8 條。

### 為什麼定義用「箱型內第幾次進場」而不是「幾天內」

08-25 量到的 L5 二次進場（31 次、+381,600）用的是「≤3 天」時間代理。
時間代理不可程式化為穩定條件。改用**結構定義**：同一個
`v_is_in_consolidation` 區段內的第 N 次進場。

理由來自 L3 研究：L4 v18 的解除條件是價格式的、被自己的停損蘊含，
結果**觸發零次**。結構定義沒有這個失效模式。

**後果**：v199 印出的二次進場次數**不會等於 31**。兩者定義不同，
不可互相驗證。31 是舊定義下的舊數字。

## 7. 已驗證 / 未驗證

已驗證（有輸出可指）：
- 剝除註解後的 diff：21 處，唯二刪除是分號改逗號。
  **沒有任何 Buy / Sell / from Entry / SetStopLoss 行出現在 diff 裡**
- begin/end 36 → 38，配對
- `verify_pla_ascii.py --strict` 71/71 PASS，涵蓋 71/71
- `verify_settlement_flat.py --strict` 10/10 合規，70/70 元素
- `scripts/research/join_l5_entry_log.py` 的報表解析器對真實報表
  178/178 通過四項；合成 log 端對端 178/178 join、0 未匹配

未驗證（不可宣稱）：
- **v199 沒有在 MC12 編譯過，沒有跑過**
- 二次進場次數、損益、佔比——**一個數字都還沒有**
- `v_is_in_consolidation[1]` 在 MC12 的實際行為（L3 v15.1 有先例但未親驗）

## 8. 下一步

1. MC12 載入 v199（訊號名 `STRATEGY_L5_V199_R1_RESEARCH`，**不可用 live 名稱**）
2. 錨點：淨利 / 筆數 / MDD / 每筆進出場時間價格，須與 live 完全相同
3. 輸出視窗內容存成 .txt，連同 Trades List .xlsx 餵給 join 腳本
4. L4 標籤化（`from Entry` = 0，照 L2/L3 方式做）
