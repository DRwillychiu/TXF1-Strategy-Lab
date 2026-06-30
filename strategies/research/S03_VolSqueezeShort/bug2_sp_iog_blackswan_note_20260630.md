# Bug 2 SP IOG Black Swan Note — Practical Assessment

**Date**: 2026-06-30
**Author**: User ruling + Claude analysis
**Status**: DOCUMENTED — Bug 2 downgraded to non-blocking for v1.8.x development

---

## 1. Bug 2 Summary

**What**: IOG=true causes SP (Stop Profit) stop orders to fire at intrabar worst tick instead of next 60M close.

**Observed impact**: v1.8.0-GA SP maxL = -132,200 NTD (vs v1.7.3 SP maxL = -5,000 NTD)

**Affected case**: 2024-08-05 BoJ rate shock reversal (single occurrence in 6-year backtest)

---

## 2. Trade Detail Verification (MC12 Trade List)

### Actual trade (from MC12 backtest):
- **Entry**: 2024/8/5 16:00 (night session, SE_VS_En) @ 19,374
- **Exit**: 2024/8/6 02:00 (night session, SX_VS_SP) @ 20,080
- **Loss**: 706 pts x 200 = -141,200 NTD (+ slippage = -143,200)
- **Session**: Night session (15:00-05:00), NOT day session limit-down

### Key finding
The entry was during the **night session** (16:00), 1 hour after night session open.
This is AFTER the day session limit-down ended. Night session has active liquidity.
**This trade IS plausible in live trading** — unlike a day-session limit-down entry.

### User assessment (2026-06-30)
1. Night session entry at 16:00 is technically executable (liquidity exists)
2. However, user has **manual override** capability — in extreme BoJ-level events, user can manually close positions
3. Bug 2 SP fill at worst intrabar tick remains a real risk for overnight positions during violent reversals
4. The risk is bounded: night session has liquidity for exits, just with potentially worse fill prices

### Conclusion
- Bug 2 is a **real but low-frequency risk** (1 event in 6 years)
- Primary defense (1M_Exit market order) is unaffected
- Non-blocking for v1.8.x development; still requires awareness before live deployment
- User manual override provides additional safety layer in production

---

## 3. When to Revisit Bug 2

Bug 2 should be revisited if ANY of these conditions apply:

| Condition | Trigger |
|-----------|---------|
| Pre-market order system added | Strategy can place orders before 08:45 open |
| Overnight position held into limit event | Entry was before the extreme day, position carries overnight |
| v1.8.x promoted to live (real money) | Before real capital deployment, SP mechanism must be verified |
| New extreme event observed in live_simulation | MC12 simulation shows SP fill anomaly in real-time |

---

## 4. Exit Liquidity Verification

Historical evidence from v1.7.3 (45 trades across 28 macro events):

| Exit type | Trades | All filled? | Note |
|-----------|--------|-------------|------|
| SP (stop profit) | 30 | Yes | Including extreme reversal days |
| TP (take profit) | 5 | Yes | COVID, BoJ, Trump 4-7 |
| SL (stop loss) | 8 | Yes | Reversal catches |
| Mid exit | 2 | Yes | Thesis invalidation |

**No evidence of exit failure due to liquidity** in any historical extreme event.

TAIEX futures reversal days typically have HIGH liquidity (panic buying + short covering = deep order book).

---

## 5. Bug 2 Risk Classification Update

| Attribute | Previous (2026-06-29) | Updated (2026-06-30) |
|-----------|----------------------|---------------------|
| Severity | Critical | **Important (downgraded)** |
| Urgency | Important | **Low (non-blocking)** |
| Blocking WFA? | No | **No** |
| Blocking v1.8.x dev? | No | **No** |
| Blocking promote to live? | Yes | **Yes (unchanged)** |
| Observed frequency | 1 in 6 years | **1 in 6 years (likely unrealistic)** |

---

## 6. Affected Exit Mechanisms Recap

| Mechanism | Order type | Bug 2 affected? | v1.8.x status |
|-----------|-----------|-----------------|---------------|
| **1M_Exit** (active defense) | **Market order** | **No** | Working (2 triggers, 6/8 saved) |
| SP (profit protection) | Stop order | **Yes** | Bug 2 root cause |
| SL / SetStopLoss | Stop / engine | Partial | Secondary risk |
| TP (take profit) | Limit order | No | Unaffected |
| Mid / TimeStop | Market order | No | Unaffected |

**Key**: The primary active defense (1M_Exit) uses market orders and is **completely unaffected** by Bug 2. Bug 2 only affects the passive stop-order layers (SP/SL), which are backup mechanisms.

---

## 7. Related Files

- `v180_GA_R1_result_20260629.md` — v1.8.0-GA backtest with Bug 2 SP evidence
- `v181_BarStatusFix_FAILED_20260629.md` — Failed Bug 2 fix attempt
- `v181_GA_FAILED_architecture_verdict_20260629.md` — Architecture limitation confirmed
- `extreme_event_coverage_20260624.md` — 45-trade exit analysis (v1.7.3)
- `docs/handoffs/handoff_20260629_evening_bug2_unsolved_revisit_tomorrow.md` — Previous session handoff
