# S16 MACrossShort — HANDOFF Laptop 2026-07-07 → Desktop

---

## 一、今日進度（2026-07-07 筆電端）

### 1. S4 MACD KILL (done, committed + pushed)
- S4_L + S4_S both KILLED
- Reason: MACD not suitable as standalone strategy, keep as indicator only
- Roadmap updated, commit `75110e6`

### 2. MA Deep Research (done, committed this session)
- `MA_deep_research_20260707.md` created (179 lines)
- Covers: MA mathematical essence, 4 observation layers, market usage panorama, momentum anomaly edge, ZLEMA analysis, 7 unresolved problems

### 3. S16 Split L/S (NEW decision)
- S16 split into **S16_S** (MACrossShort, CURRENT) and **S16_L** (MACrossLong, Queue)
- **S16_S first** (override L-first rule, original intent = short sleeve reinforcement)
- Roadmap updated with split + new decision records

### 4. Whipsaw Protection Layer 1 Design (DONE)
- Full 3-layer whipsaw framework discussed (10 mechanisms)
- **Layer 1 (Entry Gate) decisions finalized:**

| Mechanism | Decision | Reason |
|-----------|----------|--------|
| M1 Slope confirmation | **KEEP (loose threshold)** | Slow ZLEMA slope != 0 filters flat market noise |
| M2 N-bar delay | **DROP** | 5M timeframe cannot afford 10-15 min entry delay; exit-side handles false crosses |
| M3 ATR threshold | **DROP from entry** | ATR belongs in exit logic; keep entry pure |
| M4 Volume confirmation | **DROP** | Blocks night session signals; poor discriminator in day session |

- **Design philosophy**: Gate wide open at entry, knife sharp at exit. Whipsaw is accepted as long as each loss is strictly controlled.

### 5. Layer 2 + Layer 3 (NOT DONE)
- Layer 2 (Exit-side damage control): M5 quick stop, M6 Rule #17 multilayer, M7 breakeven trail, M8 time stop — **pending deep discussion**
- Layer 3 (Regime filter): M9 Daily MA, M10 volatility filter — **pending, L24 tension unresolved**

---

## 二、User Key Decisions (verbatim)

1. "這個策略的規劃我希望呈現的結果是能夠抓到短線上的獲利，因此如果遇到洗盤的部分，只要做到嚴格控管虧損即可"
2. "我會把這份策略區分成L以及S的策略，然後現階段會先執行S的策略為主規劃"
3. "今天操作週期為5分線以內了，就是為了立即抓到直接下跌或者直接上漲的起始點，因此不應該使用延遲K棒確認"
4. "M1通過後再去觀察1根的延遲再來判斷" (conditional 1-bar, not mandatory)
5. "ATR拿來做為出場判斷可以，但進場判斷盡可能純粹就好"

---

## 三、Desktop Next Actions

1. **Layer 2 deep design** — M5 quick stop + M6 Rule #17 multilayer are the core (user emphasized exit rigor)
2. **Layer 3 decision** — Regime filter yes/no, pending W0 data
3. **Update S16_stage1_spec.md** — Incorporate all new decisions (5M, ZLEMA, L/S split, Layer 1 design)
4. **W0 Python script** — ZLEMA 5M crossover on TXF1 data, compare conservative vs aggressive route
5. **Commit MA_deep_research** — Already committed this session

---

## 四、S16_S Entry Logic Summary (as of 2026-07-07)

```
Entry Signal (S16_S MACrossShort):
  ZLEMA_Fast crosses BELOW ZLEMA_Slow at Data1 (5M) close
  AND AbsValue(ZLEMA_Slow - ZLEMA_Slow[1]) > MinSlope  // M1: market is moving
  AND v_Settlement_Day = False
  AND v_Holiday_Block = False
  AND v_Registry_Expired = False
  AND Manual_Kill_Switch = False
Order:
  sell short next bar at market

Exit Priority (Layer 2 pending detailed design):
  P0: Kill / Registry / Holiday / Settlement (Rule #11/#12)
  P1: M5 Quick stop (N bars no profit or loss > X pts)
  P2: M6 Rule #17 multilayer 1M monitor (5-layer scoring)
  P3: Golden Cross -> buy to cover at market
  P4: M7 Breakeven trailing (after X*ATR profit)
  P5: M8 Time stop (max holding period)
  P6: ATR-based SL (last resort)
  P7: SetStopLoss engine guard (Rule #12 backup)

NO TP - trend running per feedback_trend_let_profits_run
```

---

## 五、Key Files

| File | Status |
|------|--------|
| `docs/policies/OFFICIAL_ROADMAP.md` | Updated (S16 L/S split + decision records) |
| `strategies/research/S16_MACrossShort/MA_deep_research_20260707.md` | NEW (committed) |
| `strategies/research/S16_MACrossShort/HANDOFF_20260707_laptop_to_desktop.md` | NEW (this file) |
| `strategies/research/S16_MACrossShort/HANDOFF_20260706_desktop_to_laptop.md` | Prior handoff |
| `strategies/research/S16_MACrossShort/S16_stage1_spec.md` | STALE (needs update with new decisions) |

---

## 六、Git Status

Local = Remote 100% synced after this commit.
Repo: https://github.com/DRwillychiu/TXF1-Strategy-Lab.git

---

**Handoff Complete — 2026-07-07 Laptop**
**Desktop continue with Layer 2 exit-side deep design**
