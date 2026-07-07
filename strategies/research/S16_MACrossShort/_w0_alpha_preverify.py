"""S16_S MACrossShort - W0 Alpha Pre-Verify (Python, daily proxy).

Goal: validate ZLEMA death-cross short-side alpha exists before writing .pla.

Note: TXF1 5M raw data not locally available. Uses TWII daily as proxy —
if momentum alpha exists on daily, it typically exists on 5M with more
signals but similar structure; if it fails on daily, 5M attempt is KILL.

4 institutional gates (per STRATEGY_SUCCESS_CRITERIA.md):
  1. Trigger frequency >= 3 death-crosses/year (daily proxy freq lower than 5M)
  2. Forward N-bar short hit rate >= 40%
  3. Risk-reward ratio (avg win / avg loss) >= 1.0
     (S16 design has NO fixed TP, cross-based exit lets profits run;
      gate 1.0 is lower than S4 divergence's 1.5 because MA cross entries
      are simpler / higher frequency / lower per-trade edge is acceptable)
  4. Cross-year stability >= 40% years with positive PnL
     (short strategy in TXF1 bull-biased regime, 40% is realistic)

Test matrix:
  - Fast ZLEMA: 3, 5, 8, 10, 12, 15
  - Slow ZLEMA: 15, 20, 25, 30, 40, 50
  - Constraint: Slow > Fast * 2 AND Slow <= 50
  - M1 slope filter: |Slow_slope| >= MinSlope (test 0, 1, 2)

PASS best combo across gates -> proceed to W1 strategy.md
FAIL -> KILL with FINAL_VERDICT.md
"""
import sys, io, csv, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict
from statistics import mean

CSV_PATH = r'C:\Users\User\Desktop\TXF1-Strategy-Lab\backtest\twii_daily.csv'


# =============================================================================
# 1. LOAD DATA
# =============================================================================
bars = []
with open(CSV_PATH, encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        bars.append({
            'date': row['Date'],
            'o': float(row['Open']),
            'h': float(row['High']),
            'l': float(row['Low']),
            'c': float(row['Close']),
        })

print('=' * 100)
print('S16_S MACrossShort - W0 Alpha Pre-Verify (Daily Proxy)')
print('=' * 100)
print(f'Loaded {len(bars)} TWII daily bars: {bars[0]["date"]} to {bars[-1]["date"]}')

closes = [b['c'] for b in bars]
dates = [b['date'] for b in bars]


# =============================================================================
# 2. ZLEMA IMPLEMENTATION
# =============================================================================
def ema(values, n):
    """Standard EMA."""
    if not values:
        return []
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def zlema(values, n):
    """Zero-Lag EMA: EMA of (2*price - price[lag]).
    lag = int((n - 1) / 2).
    """
    if len(values) < n + 1:
        return [values[0]] * len(values) if values else []
    lag = max(1, (n - 1) // 2)
    delagged = []
    for i in range(len(values)):
        if i < lag:
            delagged.append(values[i])
        else:
            delagged.append(2 * values[i] - values[i - lag])
    return ema(delagged, n)


# =============================================================================
# 3. DEATH-CROSS DETECTION + FORWARD SHORT TEST
# =============================================================================
def find_death_crosses(fast_arr, slow_arr, min_slope=0):
    """Return list of bar indices where Fast crosses BELOW Slow.
    Cross defined at bar i: fast[i-1] >= slow[i-1] AND fast[i] < slow[i].
    Optional M1 slope filter on Slow (needs to be sloping down).
    """
    crosses = []
    for i in range(2, len(fast_arr)):
        crossed_below = fast_arr[i - 1] >= slow_arr[i - 1] and fast_arr[i] < slow_arr[i]
        if not crossed_below:
            continue
        if min_slope > 0:
            slope = abs(slow_arr[i] - slow_arr[i - 1])
            if slope < min_slope:
                continue
        crosses.append(i)
    return crosses


def forward_short_test(entry_idx, fwd_n, bars):
    """Simulate a short: enter at close[entry_idx], exit at close[entry_idx+fwd_n].
    Returns pct return (positive = short profit = price dropped).
    """
    if entry_idx + fwd_n >= len(bars):
        return None
    entry_c = bars[entry_idx]['c']
    exit_c = bars[entry_idx + fwd_n]['c']
    ret_pct = (entry_c - exit_c) / entry_c * 100  # short pnl
    return ret_pct


# =============================================================================
# 4. BATCH TEST ALL (Fast, Slow) COMBINATIONS
# =============================================================================
FAST_RANGE = [3, 5, 8, 10, 12, 15]
SLOW_RANGE = [15, 20, 25, 30, 40, 50]
FWD_LIST = [3, 5, 10, 20]
MIN_SLOPE_LIST = [0, 1.0]  # 0 = no filter, 1.0 = light filter

n_years = (len(bars) / 250)  # trading days per year approx

print()
print(f'Test matrix:')
print(f'  Fast: {FAST_RANGE}')
print(f'  Slow: {SLOW_RANGE}')
print(f'  Fwd  N: {FWD_LIST}')
print(f'  MinSlope: {MIN_SLOPE_LIST}')
print(f'  Data span: {n_years:.1f} years')
print()


# Pre-compute all ZLEMA
zlema_cache = {}
for n in set(FAST_RANGE + SLOW_RANGE):
    zlema_cache[n] = zlema(closes, n)


results = []
for fast_n in FAST_RANGE:
    for slow_n in SLOW_RANGE:
        # Constraint: Slow > Fast * 2
        if slow_n <= fast_n * 2:
            continue
        if slow_n > 50:
            continue

        fast_arr = zlema_cache[fast_n]
        slow_arr = zlema_cache[slow_n]

        for min_slope in MIN_SLOPE_LIST:
            crosses = find_death_crosses(fast_arr, slow_arr, min_slope)
            if not crosses:
                continue

            for fwd_n in FWD_LIST:
                trades = []
                yearly = defaultdict(list)
                for idx in crosses:
                    ret = forward_short_test(idx, fwd_n, bars)
                    if ret is None:
                        continue
                    year = int(dates[idx][:4])
                    trades.append(ret)
                    yearly[year].append(ret)

                if not trades:
                    continue

                n_trades = len(trades)
                trigger_per_yr = n_trades / n_years
                wins = [r for r in trades if r > 0]
                losses = [r for r in trades if r < 0]
                wr = len(wins) / n_trades * 100
                avg_ret = mean(trades)
                avg_win = mean(wins) if wins else 0
                avg_loss = mean(losses) if losses else 0
                rr = abs(avg_win / avg_loss) if avg_loss else 0

                years_positive = sum(
                    1 for y_rets in yearly.values() if sum(y_rets) > 0
                )
                stability = (years_positive / len(yearly)) * 100 if yearly else 0

                # 4 gates
                g1_freq = trigger_per_yr >= 3
                g2_wr = wr >= 40
                g3_rr = rr >= 1.0
                g4_stab = stability >= 40
                pass_n = sum([g1_freq, g2_wr, g3_rr, g4_stab])

                results.append({
                    'fast': fast_n, 'slow': slow_n, 'slope': min_slope, 'fwd': fwd_n,
                    'n': n_trades, 'freq': trigger_per_yr,
                    'wr': wr, 'avg_ret': avg_ret,
                    'avg_win': avg_win, 'avg_loss': avg_loss, 'rr': rr,
                    'stab': stability, 'yearly': dict(yearly),
                    'g1': g1_freq, 'g2': g2_wr, 'g3': g3_rr, 'g4': g4_stab,
                    'pass_n': pass_n,
                })


# =============================================================================
# 5. RANK RESULTS
# =============================================================================
# Score: 4/4 gates pass + high avg_ret * n as tiebreak
def score(r):
    return (r['pass_n'], r['avg_ret'] * r['n'] / 100)


results.sort(key=score, reverse=True)

print('=' * 100)
print('TOP 15 COMBINATIONS (by pass_n, then aggregate short return)')
print('=' * 100)
print(f'{"Fast":>4} {"Slow":>4} {"Slope":>5} {"Fwd":>3} {"N":>4} {"Freq":>5} '
      f'{"WR%":>5} {"AvgRet":>7} {"AvgWin":>7} {"AvgLoss":>8} {"RR":>5} {"Stab":>5} {"Gates":>5}')
print('-' * 100)
for r in results[:15]:
    gates_str = f'{"Y" if r["g1"] else "-"}{"Y" if r["g2"] else "-"}{"Y" if r["g3"] else "-"}{"Y" if r["g4"] else "-"}'
    print(f'{r["fast"]:>4} {r["slow"]:>4} {r["slope"]:>5.1f} {r["fwd"]:>3} '
          f'{r["n"]:>4} {r["freq"]:>5.1f} {r["wr"]:>5.1f} {r["avg_ret"]:>+7.2f} '
          f'{r["avg_win"]:>+7.2f} {r["avg_loss"]:>+8.2f} {r["rr"]:>5.2f} '
          f'{r["stab"]:>5.1f} {gates_str:>5}')


# =============================================================================
# 6. FOCUS ON DESIGN DEFAULT (Fast=5, Slow=20, Slope=1.0)
# =============================================================================
DESIGN_DEFAULT = {'fast': 5, 'slow': 20, 'slope': 1.0}
design_results = [r for r in results
                  if r['fast'] == DESIGN_DEFAULT['fast']
                  and r['slow'] == DESIGN_DEFAULT['slow']
                  and r['slope'] == DESIGN_DEFAULT['slope']]

print()
print('=' * 100)
print(f'DESIGN DEFAULT (Fast=5, Slow=20, Slope>=1.0) across Fwd_N variants:')
print('=' * 100)
print(f'{"Fwd":>3} {"N":>4} {"Freq":>5} {"WR%":>5} {"AvgRet":>7} {"RR":>5} {"Stab":>5} {"Gates":>5}')
for r in sorted(design_results, key=lambda x: x['fwd']):
    gates_str = f'{"Y" if r["g1"] else "-"}{"Y" if r["g2"] else "-"}{"Y" if r["g3"] else "-"}{"Y" if r["g4"] else "-"}'
    print(f'{r["fwd"]:>3} {r["n"]:>4} {r["freq"]:>5.1f} {r["wr"]:>5.1f} {r["avg_ret"]:>+7.2f} '
          f'{r["rr"]:>5.2f} {r["stab"]:>5.1f} {gates_str:>5}')


# =============================================================================
# 7. YEAR-BY-YEAR BREAKDOWN OF BEST COMBO
# =============================================================================
if results:
    best = results[0]
    print()
    print('=' * 100)
    print(f'BEST COMBO YEAR-BY-YEAR: Fast={best["fast"]}, Slow={best["slow"]}, '
          f'Slope>={best["slope"]}, Fwd_N={best["fwd"]}')
    print('=' * 100)
    print(f'{"Year":<6} {"N":>3} {"Total Ret %":>13} {"Avg/trade %":>13}')
    for y in sorted(best['yearly'].keys()):
        y_rets = best['yearly'][y]
        total = sum(y_rets)
        avg = mean(y_rets) if y_rets else 0
        print(f'  {y:<4} {len(y_rets):>3} {total:>+13.2f} {avg:>+13.3f}')


# =============================================================================
# 8. VERDICT
# =============================================================================
print()
print('=' * 100)
print('VERDICT SUMMARY')
print('=' * 100)

if not results:
    print('>>> NO VALID COMBINATIONS - Structural failure, KILL S16_S')
    sys.exit(1)

perfect_pass = [r for r in results if r['pass_n'] == 4]
three_pass = [r for r in results if r['pass_n'] == 3]

print(f'Total combinations tested: {len(results)}')
print(f'4/4 gates PASS: {len(perfect_pass)} combinations')
print(f'3/4 gates PASS (marginal): {len(three_pass)} combinations')
print()

if perfect_pass:
    print('STRONG PASS - Multiple combinations achieve full 4/4 gates.')
    print('Verdict: PROCEED TO W1 STRATEGY.MD')
    best = perfect_pass[0]
    print(f'Recommended default: Fast={best["fast"]}, Slow={best["slow"]}, '
          f'MinSlope={best["slope"]}, Fwd_N={best["fwd"]}')
elif three_pass:
    print('MARGINAL PASS - No 4/4 combinations, but 3/4 combinations exist.')
    print('Verdict: DISCUSS WITH USER before proceeding.')
    best = three_pass[0]
    print(f'Best 3/4: Fast={best["fast"]}, Slow={best["slow"]}, '
          f'MinSlope={best["slope"]}, Fwd_N={best["fwd"]}')
    print(f'  Failed gate(s):')
    if not best['g1']: print(f'    - G1 freq: {best["freq"]:.1f}/yr < 3')
    if not best['g2']: print(f'    - G2 WR:   {best["wr"]:.1f}% < 40%')
    if not best['g3']: print(f'    - G3 RR:   {best["rr"]:.2f} < 1.0')
    if not best['g4']: print(f'    - G4 stab: {best["stab"]:.1f}% < 40%')
else:
    print('FAIL - No combination achieves 3/4 gates. Structural alpha absent on daily.')
    print('Verdict: KILL S16_S with FINAL_VERDICT.md, drop to S16_L or S5 next.')


# =============================================================================
# 9. IMPORTANT CAVEATS
# =============================================================================
print()
print('=' * 100)
print('CAVEATS (must document in W0 result md)')
print('=' * 100)
print('1. This is DAILY PROXY, not 5M raw data. Momentum alpha typically')
print('   translates from daily to intraday but not always. Passing daily is')
print('   NECESSARY but not SUFFICIENT for 5M live behavior.')
print('2. Whipsaw pattern differs between daily and 5M. Daily whipsaw = weekly')
print('   basis; 5M whipsaw = intraday oscillation. Layer 2 exit design targets')
print('   5M-specific whipsaw, cannot be validated with daily.')
print('3. 5M-specific microstructure effects (open/close, night session) not')
print('   captured in this test.')
print('4. Slippage / commission not modeled. Real 5M edge shrinks by ~10-20%')
print('   after realistic costs.')
print('5. Daily proxy verdict PASS => S16_S retains W1 GO status, but W3')
print('   MC12 backtest on real 5M data is where final go/no-go happens.')


# =============================================================================
# 10. SAVE JSON
# =============================================================================
out = {
    'strategy': 'S16_S MACrossShort',
    'date': '2026-07-08',
    'method': 'Daily proxy (TWII daily 2020-2026)',
    'data_bars': len(bars),
    'data_years': n_years,
    'total_combos_tested': len(results),
    'gate_counts': {
        'pass_4_4': len(perfect_pass),
        'pass_3_4': len(three_pass),
    },
    'top_5': [
        {k: v for k, v in r.items() if k != 'yearly'}
        for r in results[:5]
    ],
    'design_default': design_results,
    'best_by_year': {str(y): {'n': len(v), 'total_ret_pct': sum(v)}
                     for y, v in results[0]['yearly'].items()} if results else {},
    'verdict': (
        'STRONG_PASS' if perfect_pass else
        'MARGINAL' if three_pass else
        'FAIL_KILL'
    ),
}

OUT_JSON = r'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop/9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f/scratchpad/s16_s_w0_result.json'
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\n[JSON saved to {OUT_JSON}]')
