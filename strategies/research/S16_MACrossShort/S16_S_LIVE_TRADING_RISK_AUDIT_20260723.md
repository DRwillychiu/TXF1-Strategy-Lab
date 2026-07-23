# S16_S MACrossShort — Live Trading Risk Audit (Pre-Seal)

**Date**: 2026-07-23
**Version audited**: v1.4-BELATE (frozen production)
**Purpose**: Adversarial forward-looking analysis — what could go wrong in live trading?
**Methodology**: Line-by-line code inspection + scenario simulation + cross-reference with L1-L5 known issues

---

## P1 CRITICAL — Time Bombs (Will Break Strategy Without Intervention)

### C1. Holiday Registry Expiration — Silent Death on 2027-01-01

**Code**: Section 3, line 352
```
if Date > Registry_Valid_Until then
    v_Registry_Expired = True;
```

**Problem**: `Registry_Valid_Until = 1270101` (EL date for 2027-01-01). Once the first trading day after 2027-01-01 arrives, `v_Registry_Expired = True` permanently. This causes:
- All entries blocked (entry gate checks `v_Registry_Expired = False`)
- All existing positions force-exited (P0 `SX_MA_Registry`)
- `v_Holiday_Block` also forced True (line 365-366)
- **Strategy goes 100% dead with ZERO user notification**

**Impact**: If the user doesn't refresh the registry before 2026-12-31 night session, S16_S silently stops trading. Given ~17 trades/year, a 2-month gap could cost ~3 missed trades in Bear/Volatile regime.

**Timeline**: ~5 months from now (2026-12 deadline noted in DEPLOYMENT.md)

**Solution**:
1. **Short-term**: Calendar reminder in Dec 2026 to update Holiday_Tail[64+] with 2027-2028 TAIFEX holidays
2. **Long-term**: Build a shared `HolidayFlat_v4` registry function across all strategies, updated once per year in a single file. Requires MC12 function/include mechanism.
3. **Monitoring**: Add to weekly LOOP check — if Date > `Registry_Valid_Until - 900000` (roughly 90 calendar days), flag WARNING in email alert

### C2. Holiday Array Only Covers 2019-2027 — Future Holidays Uncovered

**Code**: Section 3, lines 314-348 (Holiday_Tail[1..63])

**Problem**: The array is hardcoded with 63 holidays from 2019-2027. After updating Registry_Valid_Until, the array itself must also be extended with new holiday dates. Missing a holiday means:
- Strategy trades into a pre-holiday night session when it should block
- Position held across holiday closure → gap risk on re-open

**Interdependency**: This is coupled with C1 — both must be updated together. But they're in DIFFERENT parts of the code (array init in Section 3, expiry date in Group H inputs), making a partial update (fixing one but forgetting the other) likely.

**Solution**: When updating, use a checklist:
- [ ] Add new holiday dates to Holiday_Tail array
- [ ] Update array size declaration if > 80 entries
- [ ] Update Registry_Valid_Until to new cutoff
- [ ] Run `scripts/verify_settlement_flat.py` to confirm holiday coverage
- [ ] Commit + push + rebuild in MC12
- **This breaks parameter freeze** — clock resets to 0 trades

---

## P2 HIGH — Will Affect Real P&L

### H1. MC12 Restart Mid-Position — State Variable Loss

**Scenario**: MC12 crashes or PC restarts while S16_S has an open short position.

**Code affected**: All variables declared in Section 2 reset to initial values on strategy restart. MC12 replays historical bars to reconstruct state, but this depends on:
1. Data having sufficient history (MaxBarsBack >= 200)
2. Replay triggering the EXACT same entry
3. No data corrections between live feed and historical data

**Failure mode**: If the replay doesn't reproduce the entry (due to data adjustment, missing bar, or different rounding), MC12 reports MarketPosition = 0 while the BROKER still has an open position. The strategy then:
- Sets v_SL_Locked = False (no frozen SL)
- May generate a NEW entry signal (double position at broker)
- SetStopLoss (P7) recalculates with wrong parameters

**Real-world probability**: LOW for live_simulation (MC12 paper-trading). MEDIUM for future live (MC9 has broker connection issues documented in L1-L5 experience).

**Solution**:
1. After any MC restart, manually verify MarketPosition matches broker
2. Keep MC12 data aligned — never manually edit historical bars
3. If mismatch detected: manually close the orphaned position at broker, then restart MC clean
4. Consider adding a `Print` debug line at entry/exit that logs to TradeManager log for audit trail

### H2. MinSlope=28 Absolute Points vs Index Level Drift

**Code**: Section 9, line 468
```
v_Slope > MinSlope
```

**Problem**: MinSlope = 28 is in pure points, not percentage or ATR-normalized.
- At TXF1 = 20,000 (2020): 28 pts = 0.14% per 5M bar
- At TXF1 = 45,000 (2026): 28 pts = 0.062% per 5M bar
- At TXF1 = 70,000 (hypothetical 2030): 28 pts = 0.040% per 5M bar

As the index rises, the SAME absolute slope becomes relatively easier to achieve. This means:
- **Signal frequency gradually increases** over time
- More marginal (lower-quality) death crosses pass the filter
- Backtest WR of 22.6% may degrade as more noise signals slip through

**Evidence**: This was partially acknowledged in v0.6-REJECTED header — ATR-based adaptive slope was tested and failed. The absolute-points approach was a deliberate choice because ATR measures volatility (both directions), not directional slope.

**Trigger**: Monitor when TXF1 reaches ~55,000 (already flagged in DEPLOYMENT.md as re-evaluation point).

**Solution**:
1. **Current**: No action needed — 28 pts at 45,000 is still conservative (0.062%)
2. **At 55K+**: Re-evaluate MinSlope threshold. Consider scaling: `MinSlope_Scaled = 28 * (Index / 45000)` = 34 at 55K
3. **Red line**: If monthly trade count > 15 (DEPLOYMENT review trigger), investigate whether index level drift is the cause
4. **This re-evaluation breaks parameter freeze** — treat as red-line-triggered exception

### H3. Lunch Break (13:45-15:00) Gap Exposure

**Scenario**: Position enters during day session (08:45-13:45), held through 13:45 close, exposed to 75-minute gap until 15:00 re-open.

**Code gap**: TailFlat (P0.5) protects the overnight break (04:40-08:45), but there is NO equivalent for the lunch break.

**Exit mechanisms during 13:45-15:00 break**:
- P1-P5: Cannot fire (no bars generated) ❌
- P6 Frozen SL stop order: Unclear if MC processes stop orders during session break ⚠️
- P7 SetStopLoss: Engine-level, SHOULD be active ✅ (but depends on MC implementation)

**Real-world impact analysis**:
- S16_S holds for max 24 bars = 2 hours
- Entry at 11:40 → TimeStop at 13:40 (last day session bar) ✅ Exits before break
- Entry at 11:45 → 23 bars by 13:40, TimeStop at 15:00 (first night bar) → **held through break**
- Entry at 12:00-13:35 → position spans the break

**Mitigating factors**:
- Most S16_S entries occur during high-activity periods (market open, night session)
- Death cross + MinSlope>28 is most common during bear/volatile sessions, less common in quiet midday
- SetStopLoss (P7) provides engine-level guard
- The 13:45-15:00 gap is typically small (75 min, Taiwan market hours overlap)

**Probability**: LOW but non-zero. Over 17 trades/year, perhaps 1-2 trades/year might enter between 11:45-13:35.

**Solution**:
1. **Monitor**: Check trade log for entries after 11:30 — if persistent, consider adding a day-session LastEntry guard
2. **If upgrading**: Add `Time <= 1335 or Time > 500` guard to entry conditions (blocks entries that would span lunch break). This would lose ~1-2 trades over 7 years but eliminates gap risk.
3. **This breaks parameter freeze** — treat as compliance enhancement if ever implemented

### H4. SetStopLoss Pre-Load vs P6 Frozen SL — ATR Timing Mismatch

**Code**: Section 6-7
```
// Section 6 (every bar):
v_ATR      = AvgTrueRange( ATR_Len );
v_StopDist = v_ATR * StopATRMult;      // uses CURRENT bar ATR

// Section 7 (on entry):
v_Frozen_ATR     = v_ATR;              // freezes ENTRY bar ATR
v_Frozen_SL_Dist = v_Frozen_ATR * StopATRMult;

// Section 7 (SetStopLoss pre-load when MP=0):
if MarketPosition >= 0 then
    SetStopLoss( v_StopDist * BigPointValue );  // uses SIGNAL bar ATR
```

**Problem**: When the entry signal fires on bar N (MP=0), SetStopLoss uses bar N's ATR. The entry fills at bar N+1 open. The Frozen SL is set at bar N+1 close (when MC evaluates and finds MP=-1 for the first time). The frozen SL uses bar N+1's ATR.

If ATR changes between bar N and bar N+1, SetStopLoss distance != Frozen SL distance.

**Practical severity**: ATR(14) on 5M bars changes slowly between adjacent bars. The difference is typically < 2-3 points. In S16_S's design where trades last ~2 hours, this initial 1-bar mismatch is negligible.

**Exception**: In flash-crash scenarios (exactly when S16_S enters), ATR can spike 30-50% in 1 bar. The SetStopLoss (bar N ATR) would be NARROWER than the Frozen SL (bar N+1 ATR), potentially triggering an early stop before the Frozen SL takes over.

**Solution**:
1. **Current**: Accept as design trade-off. SetStopLoss is a backup guard (P7), not the primary stop mechanism.
2. **Monitoring**: If SX_MA_SL fires and the frozen SL distance was wider, investigate whether SetStopLoss pre-empted the intended stop level.
3. **Root fix**: After parameter freeze expires, move SetStopLoss to the first MP=-1 bar using v_Frozen_SL_Dist instead of v_StopDist. Requires careful Rule #12 compliance review.

---

## P3 MEDIUM — Edge Cases and Design Tensions

### M1. BE Trailing Uses Live ATR vs Frozen ATR

**Code**: Section 10, P3, lines 602-606
```
if v_Profit >= BE_Tier2_ATR * v_ATR then begin
    v_BE_Tier2_Active = True;
```

**Observation**: `v_ATR` is the CURRENT bar's ATR, not `v_Frozen_ATR` (entry-bar ATR). This means:
- **If vol drops after entry**: v_ATR decreases → BE threshold decreases → BE activates earlier → may lock in profits too early
- **If vol increases after entry**: v_ATR increases → BE threshold increases → BE less likely to activate → lets position run longer

**Design tension**: The v1.4-BELATE change specifically raised BE triggers to avoid strangling winners. Using live ATR introduces a second lever that could undermine this if vol drops significantly during the 2-hour hold.

**Real-world severity**: LOW-MEDIUM. S16_S enters during high-vol moments (MinSlope>28 = strong downward momentum). Vol typically stays elevated during the 2-hour hold. The scenario of entering on a spike then vol collapsing is uncommon for death-cross entries.

**Quantification**: With Frozen ATR ~50 (typical), BE_Trigger_ATR=2.5 → threshold = 125 pts. If live ATR drops to 40 during the trade → threshold = 100 pts. 25-point difference on a 45,000 index. Marginal.

### M2. ZLEMA_Slow=70 Narrow Peak Sensitivity

**Evidence**: v0.5 GA header: "ZLEMA_Slow 70: narrow peak (S80=-33.5%)"

**Problem**: If the optimal Slow parameter shifts (due to market microstructure evolution — algo trading prevalence, tick size changes, session hour changes), performance degrades rapidly. S80 (Slow=80) is -33.5% worse than S70.

**Current mitigation**: Parameter freeze prevents chasing. The strategy accepts its parameter set and tolerates degradation within red-line bounds.

**Long-term risk**: Over 3-5 years, market structure changes could shift the optimal from 70 to 60 or 80, which would significantly impact performance without triggering any red line quickly.

**Solution**: Semi-annual backtest comparison (already in DEPLOYMENT.md review cycle). If recent-2-year PF drops below 1.2 while full-period PF is still good, suspect parameter drift.

### M3. Settlement Day Formula — TAIFEX Rule Change Risk

**Code**: Section 3, line 369-371
```
v_Settlement_Day = ( DayOfWeek(Date) = 3 ) and
                   ( DayOfMonth(Date) >= 15 ) and
                   ( DayOfMonth(Date) <= 21 );
```

**Problem**: Hardcoded assumption that TXF1 settlement is always the 3rd Wednesday of the month. If TAIFEX changes this rule (e.g., to 3rd Friday like CME, or to a fixed date), the formula silently becomes wrong.

**Historical precedent**: TAIFEX has used 3rd Wednesday since inception. Rule changes are rare but not impossible (2017 night session extension, 2020 hours change during COVID).

**Solution**: Part of annual review. If TAIFEX announces settlement rule change, update ALL strategies (L1-L5, S1, S3, S16_S) simultaneously.

### M4. Data Quality Impact on ZLEMA Cross Detection

**Scenario**: A missing 5M bar or a bad tick (extreme outlier price) in the data feed.

**Impact on ZLEMA**:
- Missing bar: ZLEMA doesn't update for that period → the "crossing" might fire one bar late or early
- Bad tick (e.g., 44,000 → 99,999 → 44,100): ZLEMA spikes, potentially creating a false death cross with extreme slope

**ZLEMA smoothing**: ZLEMA(25) has a smoothing factor alpha = 2/26 = 0.077. A single bad tick contributes 7.7% to the ZLEMA value. For a 55,000-point spike: ZLEMA impact = ~4,200 points. This would create a massive false slope, triggering entry on noise.

**Mitigating factors**:
- MC12 data feed filters (exchange-level price limits)
- TXF1 has 10% daily price limit
- In simulation, data is from MC export (already filtered)
- In live trading, broker feed may have its own bad-tick filters

**Solution**: No code-level fix during parameter freeze. When going to live, consider adding a "sanity check" like `v_Slope < MaxSlope` (e.g., < 500) to reject impossibly large slopes that indicate bad data.

---

## P4 LOW — Dead Code, Efficiency, Maintenance

### L1. v_ML_Loss — Declared Never Used

**Code**: Section 2, line 270
```
v_ML_Loss               ( 0     ),
```

**Impact**: Zero runtime impact. Variable is allocated but never assigned or read. Wastes negligible memory.

**Risk**: Future maintainer might think it's used somewhere and be confused.

**Solution**: Remove after parameter freeze expires (next code change window).

### L2. v_Prev_MP — Set But Never Read in Conditions

**Code**: Section 11, line 655
```
v_Prev_MP = MarketPosition;
```

**Impact**: v_Prev_MP is updated every bar per Rule #8 convention, but S16_S never reads it. With IOG=False, MarketPosition is always reliable at bar close, so v_Prev_MP isn't needed.

**Risk**: If someone enables IOG=True (locked to False in code, but if the lock is bypassed), MarketPosition becomes unreliable, and v_Prev_MP would be needed but isn't wired into the logic.

**Solution**: Keep as-is during parameter freeze (it follows Rule #8 and costs nothing). If IOG is ever changed, wire v_Prev_MP into entry/exit conditions.

### L3. RSI Computed Twice

**Code**:
- Section 8, line 456: `v_ML_RSI = RSI( Close, 14 );`
- Section 10, P2, line 569: `v_ML_RSI_Prior = Lowest( RSI( Close, 14 ), 5 );`

**Problem**: `RSI(Close, 14)` in line 569 is a separate RSI call from v_ML_RSI. MC12 likely optimizes this internally (caches the indicator), but it's wasteful and confusing.

**Impact**: Minor CPU overhead. More importantly, if someone changes the RSI period in one place but not the other, they'd diverge silently.

**Solution**: Replace line 569 with `v_ML_RSI_Prior = Lowest( v_ML_RSI, 5 );` after parameter freeze expires.

### L4. Holiday Loop Iterates to 80 (Only 63 Entries)

**Code**: Section 3, line 358
```
for hidx = 1 to 80 begin
```

**Impact**: 17 extra comparisons per bar where Time <= 500. Holiday_Tail[64..80] = 0, and Date is never 0, so no false match.

**Runtime cost**: ~0.0001ms per bar. Completely negligible.

**Solution**: Change `80` to `63` (or the actual count) when updating the registry.

### L5. IND_S16_S_Monitor Parameter Sync Risk

**Problem**: The indicator has its own ZLEMA parameters (ZLEMA_Fast_Len=25, ZLEMA_Slow_Len=70, MinSlope_Threshold=28). If someone changes the strategy parameters (after parameter freeze), they might forget to update the indicator.

**Impact**: Indicator shows different signals than the strategy, causing confusion during diagnosis.

**Solution**: Document the dependency. When parameter freeze ends and any parameter changes, update both files in the same commit.

---

## Consolidated Resolution Matrix

| ID | Severity | Category | Fix Window | Breaks Freeze? |
|----|----------|----------|------------|----------------|
| C1 | CRITICAL | Registry expiry | **2026-12** | YES |
| C2 | CRITICAL | Holiday array | **2026-12** (bundled with C1) | YES |
| H1 | HIGH | MC restart | N/A (operational SOP) | No |
| H2 | HIGH | Index drift | **TXF1 > 55K** or monthly >15 trades | YES |
| H3 | HIGH | Lunch break gap | Next code window (optional) | YES |
| H4 | HIGH | ATR timing | Next code window (optional) | YES |
| M1 | MEDIUM | BE ATR source | Accept (design trade-off) | - |
| M2 | MEDIUM | Slow=70 peak | Semi-annual review | - |
| M3 | MEDIUM | Settlement rule | If TAIFEX changes | YES |
| M4 | MEDIUM | Data quality | Next code window (optional) | YES |
| L1 | LOW | Dead var | Next code window | YES |
| L2 | LOW | Dead var | Keep as-is (Rule #8) | No |
| L3 | LOW | Double RSI | Next code window | YES |
| L4 | LOW | Loop bounds | Bundle with C1/C2 | YES |
| L5 | LOW | Indicator sync | Documentation | No |

---

## Mandatory Action Timeline

```
NOW         → No code changes (parameter freeze active)
2026-Q3/Q4  → Monitor red lines per DEPLOYMENT.md
2026-12     → ★ C1+C2: Refresh holiday registry + expiry date
              (This resets 30-trade clock — coordinate with upgrade window)
2027-H1     → After 30 trades reached: bundle L1/L3/L4 cleanup
When 55K+   → H2: Re-evaluate MinSlope absolute threshold
Red line    → H3/H4/M4: Consider structural improvements
```

---

## Emergency Playbook (If Problem Occurs in Live)

### Scenario A: Strategy stops trading (no entries for >30 days in volatile market)
1. Check `v_Registry_Expired` — is Date past Registry_Valid_Until?
2. Check `v_Holiday_Block` — is the holiday registry blocking normal days?
3. Check `Manual_Kill_Switch` — is it accidentally set to True?
4. Check ZLEMA state via IND_S16_S_Monitor — are death crosses occurring but being blocked?
5. If registry expired: EMERGENCY patch holiday data + bump version

### Scenario B: MC12 restarts during open position
1. Immediately check broker position status
2. Compare MarketPosition in MC12 vs broker
3. If mismatch: manually close broker position, restart MC12 clean
4. Log the incident for later analysis

### Scenario C: Unexpected high-frequency entries (>15/month)
1. Check current TXF1 index level — has it risen significantly?
2. Run IND_S16_S_Monitor to inspect slope values — are marginal slopes (28-35) increasing?
3. If index-level drift confirmed: trigger red-line review per DEPLOYMENT.md

### Scenario D: Unexpectedly large single-trade loss (>1.5x historical max)
1. Check if SetStopLoss fired vs P6 Frozen SL — was there a timing mismatch (H4)?
2. Check if position was held through 13:45-15:00 gap (H3)
3. Check for data anomalies (bad tick, missing bars) (M4)
4. Review trade against IND_S16_S_Monitor for signal diagnosis

---

## Conclusion

S16_S v1.4-BELATE is structurally sound for its intended role as a 5M momentum-burst sniper. The two CRITICAL items (C1/C2 registry expiry) are **time-bounded and scheduled** — they require action by 2026-12 but are not bugs per se. The HIGH items are real-world edge cases that are mitigated by existing safety layers (SetStopLoss engine guard, TimeStop, QuickStop).

**Verdict**: Safe to seal. No immediate code changes needed. The C1/C2 calendar deadline and the DEPLOYMENT.md monitoring framework together provide adequate coverage for the identified risks.

**Next**: Seal S16_S, proceed to S17_S SwingShort60M development.
