"""S4_S MACDDivergenceShort — W0 Alpha Pre-Verify (Python, daily proxy).

Goal: validate bearish divergence alpha exists before writing .pla.

4 institutional gates (per STRATEGY_SUCCESS_CRITERIA.md):
  1. Trigger frequency >= 5 instances/year (avoid sample shortage)
  2. Forward N-bar short hit rate >= 40%
  3. Risk-reward ratio (avg win / avg loss) >= 1.5
  4. Cross-year stability >= 50% years positive PnL

Methodology:
  - TWII daily 2020-2026 (proxy for 60M behavior - daily 越易發現 divergence)
  - MACD(12, 26, 9) + RSI(14)
  - Bearish divergence detection:
      * Price new high vs prior swing high (lookback 20 bars)
      * MACD histogram NOT new high (lower)
      * RSI >= 70 (overheated confirm)
  - Forward N bars short test (N = 5, 10, 20)

PASS -> proceed to W1 strategy.md
FAIL -> KILL with FINAL_VERDICT.md
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict
from statistics import mean

CSV_PATH = r'C:\Users\User\Desktop\TXF1-Strategy-Lab\backtest\twii_daily.csv'

# === LOAD DATA ===
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
print(f'Loaded {len(bars)} TWII daily bars: {bars[0]["date"]} ~ {bars[-1]["date"]}')

# === COMPUTE MACD(12,26,9) ===
def ema(values, n):
    out = []
    if not values: return out
    k = 2 / (n + 1)
    cur = values[0]
    out.append(cur)
    for v in values[1:]:
        cur = v * k + cur * (1 - k)
        out.append(cur)
    return out

closes = [b['c'] for b in bars]
ema12 = ema(closes, 12)
ema26 = ema(closes, 26)
macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
signal = ema(macd_line, 9)
histogram = [macd_line[i] - signal[i] for i in range(len(closes))]

# === COMPUTE RSI(14) ===
def rsi(values, n=14):
    out = [50.0] * len(values)
    if len(values) < n + 1: return out
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains[:n]) / n
    avg_l = sum(losses[:n]) / n
    for i in range(n, len(values)):
        if i > n:
            avg_g = (avg_g * (n-1) + gains[i-1]) / n
            avg_l = (avg_l * (n-1) + losses[i-1]) / n
        rs = avg_g / avg_l if avg_l > 0 else 999
        out[i] = 100 - (100 / (1 + rs))
    return out

rsi14 = rsi(closes, 14)

# === BEARISH DIVERGENCE DETECTION ===
# Bearish divergence: price new high but MACD histogram lower than prior peak + RSI overheated
LOOKBACK = 20
RSI_THRESHOLD = 70

def find_swing_high(bars, hist, end_idx, lookback):
    """Find most recent prior price swing high + its histogram value, within [end_idx-lookback*2, end_idx-lookback]."""
    best_idx = -1
    best_high = -1
    start = max(0, end_idx - lookback * 2)
    stop = end_idx - lookback
    for i in range(start, stop):
        # local high: higher than 5 bars before and after
        if i < 5 or i >= len(bars) - 5: continue
        h = bars[i]['h']
        is_local_high = all(bars[i]['h'] >= bars[i+k]['h'] for k in range(-5, 6) if k != 0 and 0 <= i+k < len(bars))
        if is_local_high and h > best_high:
            best_high = h
            best_idx = i
    return best_idx

divergence_signals = []
for i in range(50, len(bars)):
    cur_high = bars[i]['h']
    cur_hist = histogram[i]
    cur_rsi = rsi14[i]
    # is current bar a recent high?
    if i < 5: continue
    if not all(bars[i]['h'] >= bars[i-k]['h'] for k in range(1, 6)): continue
    if cur_rsi < RSI_THRESHOLD: continue

    # find prior swing high
    prior_idx = find_swing_high(bars, histogram, i, LOOKBACK)
    if prior_idx < 0: continue
    prior_high = bars[prior_idx]['h']
    prior_hist = histogram[prior_idx]

    # bearish divergence condition
    if cur_high > prior_high and cur_hist < prior_hist:
        divergence_signals.append({
            'idx': i,
            'date': bars[i]['date'],
            'entry_price': bars[i]['c'],
            'prior_idx': prior_idx,
            'cur_hist': cur_hist,
            'prior_hist': prior_hist,
            'rsi': cur_rsi,
        })

print(f'\nDetected {len(divergence_signals)} bearish divergence signals')

# === FORWARD TEST (short next bar, exit after N bars) ===
results_by_N = {}
for FWD_N in [5, 10, 20]:
    trades = []
    for sig in divergence_signals:
        i = sig['idx']
        if i + FWD_N >= len(bars): continue
        entry = bars[i+1]['o'] if i+1 < len(bars) else bars[i]['c']
        exit_p = bars[i+FWD_N]['c']
        ret_pct = (entry - exit_p) / entry * 100  # short return
        trades.append({**sig, 'fwd_n': FWD_N, 'entry': entry, 'exit_p': exit_p, 'ret_pct': ret_pct})
    results_by_N[FWD_N] = trades

# === COMPUTE 4 GATES ===
print('\n' + '='*80)
print('S4_S Bearish Divergence Forward Test Results')
print('='*80)
print(f'{"Fwd N":<7} {"Trades":<8} {"WR%":<7} {"Avg Ret%":<10} {"Avg Win%":<10} {"Avg Loss%":<10} {"RR":<6}')
print('-'*80)
for FWD_N, trades in results_by_N.items():
    if not trades:
        print(f'{FWD_N:<7} no trades')
        continue
    wins = [t['ret_pct'] for t in trades if t['ret_pct'] > 0]
    losses = [t['ret_pct'] for t in trades if t['ret_pct'] <= 0]
    wr = len(wins) / len(trades) * 100
    avg_ret = mean([t['ret_pct'] for t in trades])
    avg_w = mean(wins) if wins else 0
    avg_l = mean(losses) if losses else 0
    rr = abs(avg_w / avg_l) if avg_l != 0 else 99
    print(f'{FWD_N:<7} {len(trades):<8} {wr:<7.1f} {avg_ret:<+10.2f} {avg_w:<+10.2f} {avg_l:<+10.2f} {rr:<6.2f}')

# === Pick FWD_N = 10 as default (mid-term) ===
DEFAULT_N = 10
trades_default = results_by_N[DEFAULT_N]
if not trades_default:
    print('\nNO TRADES - CANNOT EVALUATE')
    sys.exit(2)

print(f'\n=== 4 GATES CHECK (FWD_N={DEFAULT_N}) ===')

# Gate 1: Frequency >= 5/year
years_span = 6.4  # 2020-2026
freq_per_year = len(divergence_signals) / years_span
gate1 = freq_per_year >= 5
print(f'  G1 Frequency:    {freq_per_year:.1f} signals/yr  (gate >=5/yr)  [{"PASS" if gate1 else "FAIL"}]')

# Gate 2: Hit rate >= 40%
hit_rate = sum(1 for t in trades_default if t['ret_pct'] > 0) / len(trades_default) * 100
gate2 = hit_rate >= 40
print(f'  G2 Hit Rate:     {hit_rate:.1f}%  (gate >=40%)  [{"PASS" if gate2 else "FAIL"}]')

# Gate 3: RR >= 1.5
wins = [t['ret_pct'] for t in trades_default if t['ret_pct'] > 0]
losses = [t['ret_pct'] for t in trades_default if t['ret_pct'] <= 0]
avg_w = mean(wins) if wins else 0
avg_l = mean(losses) if losses else 0
rr = abs(avg_w / avg_l) if avg_l != 0 else 99
gate3 = rr >= 1.5
print(f'  G3 RR ratio:     {rr:.2f}  (gate >=1.5)  [{"PASS" if gate3 else "FAIL"}]')

# Gate 4: Cross-year stability
yr_pnl = defaultdict(float)
yr_count = defaultdict(int)
for t in trades_default:
    y = int(t['date'][:4])
    yr_pnl[y] += t['ret_pct']
    yr_count[y] += 1
positive_years = sum(1 for y, pnl in yr_pnl.items() if pnl > 0)
total_years = len(yr_pnl)
gate4 = (positive_years / total_years) >= 0.5 if total_years > 0 else False
print(f'  G4 Cross-year:   {positive_years}/{total_years} years positive ({positive_years/total_years*100:.0f}%)  (gate >=50%)  [{"PASS" if gate4 else "FAIL"}]')

print('\nYear-by-Year (FWD_N={}):'.format(DEFAULT_N))
for y in sorted(yr_pnl.keys()):
    print(f'  {y}  N={yr_count[y]:>3}  Total Ret={yr_pnl[y]:+7.2f}%  Avg={yr_pnl[y]/yr_count[y]:+5.2f}%')

# === OVERALL VERDICT ===
gates_passed = sum([gate1, gate2, gate3, gate4])
print(f'\n=== OVERALL: {gates_passed}/4 gates pass ===')
if gates_passed == 4:
    print('VERDICT: PASS - proceed to W1 strategy.md (Stage-1 4-段討論 lock)')
    sys.exit(0)
elif gates_passed >= 3:
    print('VERDICT: MARGINAL - 3/4 pass, user decision required')
    sys.exit(1)
else:
    print('VERDICT: FAIL - KILL with FINAL_VERDICT.md (skip .pla, 節省 5-7 days)')
    sys.exit(1)
