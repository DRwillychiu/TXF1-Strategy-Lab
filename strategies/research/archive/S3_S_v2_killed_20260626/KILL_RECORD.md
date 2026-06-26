# S3_S v2.0 KILL Record (2026-06-26)

**Verdict**: KILL — v2.0 "ride-to-end" thesis proven unprofitable.
**Production version**: v1.2 FROZEN (unchanged)

---

## v2.0 Design (what was tested)

Thesis shift from v1.2 "fast in-out" to "ride to end + K-pattern reversal exit":

| Change | v1.2 | v2.0 | Rationale |
|--------|------|------|-----------|
| TargetATRMult | 3.5 | **10** | TP far, let trail drive exit |
| SP_Retain_Pct | 70 | **67** | 33% giveback (owner ruling) |
| K-pattern Reversal | (none) | **NEW** | Hammer/bullish body exit when armed |

---

## v1.2 vs v2.0 Backtest Comparison

| Metric | v1.2 (Cool=1) | v2.0 | Change |
|--------|:----------:|:----:|:------:|
| Trades | 185 | 191 | +6 |
| Net | **+552,200** | **-506,800** | **-1,059,000** |
| PF | 1.18 | 0.864 | **<1 = losing** |
| Win Rate | ~59% | 58.6% | ~same |
| MDD | -52% | ~-66% | worse |

### Exit Signal Comparison

| Exit | v1.2 | v2.0 | Delta |
|------|------|------|-------|
| TP (3.5 ATR) | 21 / +1,479,400 | (removed) | — |
| Reversal | (none) | 24 / +1,111,600 | **-368K vs TP** |
| SP (trail) | 112 / +1,979,800 | 105 / +1,895,000 | -85K |
| SL | 43 / -2,495,800 | 47 / -2,799,200 | **-303K worse** |
| Mid | 7 / -380,400 | 12 / -636,800 | **-256K worse** |

### Per-Year

| Year | v2.0 Net | Trades | Note |
|------|----------|--------|------|
| 2020 | +156,400 | 27 | OK |
| 2021 | -271,200 | 38 | Loss |
| 2022 | +225,000 | 38 | OK |
| 2023 | -18,800 | 18 | Flat |
| 2024 | +354,200 | 30 | OK (BoJ event) |
| 2025 | **-597,000** | 32 | Disaster (bull market) |
| 2026 | **-355,400** | 8 | Disaster |

---

## Three Root Causes of Failure

### 1. TP too far (10 ATR) — trades that SHOULD have profited now lose

V1.2's TP at 3.5 ATR catches the panic drop and locks in profit.
V2.0's TP at 10 ATR almost never triggers. Trades that would have
hit 3.5 ATR TP now continue running, bounce back, and exit via
Mid (loss) or SP (less profit).

Evidence: v1.2 TP 21 trades +1,479K vs v2.0 Reversal 24 trades
+1,112K. Reversal captures 3 more trades but -368K less total.

### 2. Mid exit becomes a disaster (12 trades, -636K, 0% WR)

With TP at 10 ATR, the Mid exit (close above Bollinger midline)
becomes the "I gave up" exit. All 12 Mid exits are losses — the
trade ran in the right direction, bounced back through midline,
and exited at a loss. V1.2 had only 7 Mid exits (-380K).

### 3. SL losses INCREASE, not decrease (47 trades, -2,799K)

V2.0 has 4 MORE SL trades than v1.2 and -303K more total SL loss.
82% of SL losers had positive MFE (avg +8,430) — they went the
right way first, then reversed and hit SL. The "ride to end"
framework does nothing to reduce these.

---

## Fundamental Lesson

**Vol squeeze short profits come from FAST, SHORT panic drops.**

The v1.2 "fast in-out" thesis is correct:
- Short panic = V-bottom, profit window is narrow
- TP 3.5 ATR catches the drop and locks in before the bounce
- Riding to the end means the bounce eats the profit

This mirrors the L3 Cooldown-D lesson (2026-06-25): optimization
frameworks must match the strategy's profit mechanism. "Ride to
end" works for L5 breakout (long trends), not for S3_S (fast panics).

---

## Files

- `S3_VolSqueezeShort_v2.pla` — archived here (719 lines)
- Production: `strategies/research/S03_VolSqueezeShort/S3_VolSqueezeShort.pla` (v1.2 FROZEN)
