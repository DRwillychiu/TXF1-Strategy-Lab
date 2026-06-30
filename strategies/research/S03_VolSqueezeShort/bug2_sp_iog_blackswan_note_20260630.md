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

## 2. User Ruling: BoJ 2024-08-05 Trade is Unrealistic in Live Trading

### Reasoning (user 2026-06-30)

1. **Liquidity constraint**: TAIEX limit-down day = no counterparty for new short entries. Order book would be empty or queue would be too deep for retail-sized orders to fill.

2. **No pre-market order system**: S3_S does not have pre-market (before 08:45) order placement logic. The strategy evaluates signals during market hours only.

3. **Manual override available**: In live trading, the user can manually close positions during extreme events, providing a human safety layer that backtests cannot model.

4. **Backtest artifact**: MC12 assumes infinite liquidity and instant fills. A new short entry during limit-down is a backtest-only scenario that would not occur in production.

### Conclusion

The SP -132K loss attributed to Bug 2 is tied to a trade that **would not have been entered in live trading**. Therefore:

- Bug 2 observed impact is **overstated** by backtest assumptions
- The actual live-trading impact of Bug 2 is **significantly lower** than -132K
- Bug 2 remains a theoretical risk for future events but is **not blocking** v1.8.x development

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
