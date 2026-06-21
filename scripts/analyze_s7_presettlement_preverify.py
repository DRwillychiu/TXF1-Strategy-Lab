"""
S7 PreSettlementHarvest — Pre-verification (apply STRATEGY_RD_SOP_v2 gates)

Strategy hypothesis (from roadmap §9.3):
  Entry: Long at 08:50 on 3rd Wed of month
         IF prior-day close > 5-day SMA (uptrend filter)
  Exit:  Force-flat at 10:00 OR 1×ATR stop
  Tagged with EVENT_DRIVEN_EXEMPT flag (needs Constitution amendment)

Pre-W0 Gate 1 (MC12 execution): ✓ PASS (pure TXF1 calendar, MC native)
Pre-W0 Gate 2 (Operational): ✓ PASS (Constitution amendment one-time)

W0 Alpha Pre-verification (4 gates):
  Gate A: 28-year validation (L14) — use TWII 1997-2026
  Gate B: ≥4/6 macro regimes Sharpe > 0.3
  Gate C: L18 recent-bias < 2.5×
  Gate D: Skipping (S7 is Long-only event, not signal-following)

Test method:
  - For each 3rd Wed in 1997-2026
  - If prior trading day's close > prior-5-day SMA (uptrend filter)
  - Simulate buying at OPEN of 3rd Wed
  - Exit at 10:00 (intra-day intraday return approximated by:
    first-1hr-of-day return ≈ (open + 0.25 * (high - low)) - open
    — limitation: TWII daily data has no intraday detail
    — proxy: use 'first half of day session' = (Close_open + 1/3 day range)

Simplification: Since we only have TWII daily data (not 5M intraday),
  approximate "08:50 to 10:00 return" using **opening 1hr drift**:
    open_to_first_hr ≈ open + 0.3 × (high - low) when day is up
                     ≈ open + 0.3 × (low - high) when day is down

  Better: use full day's open-to-close as upper bound estimate
  (real S7 would force-flat at 10:00, so actual return <= day return)

  We test BOTH:
    (a) Open-to-close (upper bound, overestimate)
    (b) Open-to-mid-day proxy (0.3 × day range)
"""
import csv
import io
import sys
from datetime import date, timedelta
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- Fetch TWII 1997-2026 ----------
print('Fetching ^TWII 1997-2026 via yfinance...')
import yfinance as yf
df = yf.download('^TWII', start='1997-01-01', end='2026-06-21',
                  progress=False, auto_adjust=False)
twii = []
for idx, row in df.iterrows():
    try:
        o = float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open'])
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        h = float(row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High'])
        l = float(row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low'])
        twii.append((idx.date(), o, h, l, c))
    except (ValueError, TypeError):
        continue
print(f'  Loaded {len(twii)} trading days, {twii[0][0]} → {twii[-1][0]}')

# ---------- Find 3rd Wed of each month ----------
def is_3rd_wednesday(d):
    """3rd Wed = first Wed + 14 days"""
    if d.weekday() != 2:  # Wed = 2
        return False
    # Find first Wed of this month
    first = date(d.year, d.month, 1)
    days_to_wed = (2 - first.weekday()) % 7
    first_wed = first + timedelta(days=days_to_wed)
    third_wed = first_wed + timedelta(days=14)
    return d == third_wed

# Build index for fast lookup
twii_by_date = {row[0]: row for row in twii}
twii_dates_sorted = [row[0] for row in twii]

# ---------- Simulate S7 ----------
# For each TWII trading day that IS a 3rd Wed:
#   1. Find prior trading day (and prior-5 close for SMA filter)
#   2. Apply uptrend filter: prior close > prior-5-day SMA?
#   3. If pass: simulate Long entry at OPEN, exit at "10:00" (proxy)
#   4. Record trade PnL
trades_full_day = []  # open-to-close return
trades_first_hr_proxy = []  # open + 0.3 × day range

for i, (d, o, h, l, c) in enumerate(twii):
    if not is_3rd_wednesday(d):
        continue
    # Need prior 5 trading days' closes for SMA
    if i < 5:
        continue
    prior_closes = [twii[i - k][4] for k in range(1, 6)]  # 5 prior closes
    prior_5_sma = sum(prior_closes) / 5
    prior_close = prior_closes[0]
    # Uptrend filter
    if prior_close <= prior_5_sma:
        continue
    # Simulate trades
    # (a) Open-to-close
    if o > 0:
        ret_full = (c - o) / o
        trades_full_day.append((d, ret_full))
    # (b) First-hour proxy: assume we capture 30% of day's range in direction of day
    if o > 0:
        if c > o:
            # day was up — first hour proxy: open + 0.3 × (high - low)
            mid_estimate = o + 0.3 * (h - l)
        else:
            mid_estimate = o - 0.3 * (h - l)
        ret_proxy = (mid_estimate - o) / o
        # But we exit at 10:00 even if day continues — cap upside, allow loss
        # Conservative: take min of full_day and proxy if same sign
        if c > o:
            ret_first_hr = min(ret_full, ret_proxy) if ret_full > 0 else ret_proxy
        else:
            ret_first_hr = max(ret_full, ret_proxy) if ret_full < 0 else ret_proxy
        trades_first_hr_proxy.append((d, ret_first_hr))

print(f'\n3rd Wed entries passing uptrend filter: {len(trades_full_day)}')
print(f'Frequency: {len(trades_full_day) / 28.4:.1f} per year (expected ~12)')

# ---------- Stats helper ----------
def summarize(label, samples, years):
    if not samples:
        print(f'  {label}: no trades')
        return None
    rets = [r for _, r in samples]
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    tpy = n / years
    annual = tpy * m / 100
    avol = sd * (tpy ** 0.5)
    sharpe = annual / avol if avol > 0 else 0
    print(f'  {label}')
    print(f'    N={n}  Mean%={m:.3f}  WR%={wr:.1f}  PF={pf:.3f}  Cum%={cum:+.2f}%  Sharpe(y)={sharpe:.3f}')
    return {'n': n, 'mean_pct': m, 'wr': wr, 'pf': pf, 'cum': cum, 'sharpe': sharpe}

# ---------- Q1: Overall + comparison full-day vs first-hr proxy ----------
print()
print('=' * 80)
print('Q1: Overall stats (Full-day return vs First-hr proxy)')
print('=' * 80)
s_full = summarize('Full day open→close (upper bound, overestimate)', trades_full_day, 28.4)
print()
s_proxy = summarize('First-hr proxy (0.3 × day range capped)', trades_first_hr_proxy, 28.4)

# ---------- Q2: 6 macro regime split (Gate B) ----------
print()
print('=' * 80)
print('Q2: 6 macro regimes (Gate B: L14 ≥4/6 Sharpe > 0.3)')
print('=' * 80)
regimes = [
    ('1997-2002 Dot-com', date(1997, 1, 1), date(2002, 12, 31)),
    ('2003-2007 China bull', date(2003, 1, 1), date(2007, 12, 31)),
    ('2008-2009 GFC', date(2008, 1, 1), date(2009, 12, 31)),
    ('2010-2014 Post-GFC', date(2010, 1, 1), date(2014, 12, 31)),
    ('2015-2019 Sideways', date(2015, 1, 1), date(2019, 12, 31)),
    ('2020-2026 COVID+AI', date(2020, 1, 1), date(2026, 12, 31)),
]
print('\nUsing First-hr proxy (more realistic):')
print(f'{"Regime":<30} {"N":>3} {"Mean%":>7} {"WR%":>5} {"PF":>5} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 75)
regime_results = []
for name, d_start, d_end in regimes:
    sub = [(d, r) for d, r in trades_first_hr_proxy if d_start <= d <= d_end]
    if not sub:
        continue
    rets = [r for _, r in sub]
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    yrs = (d_end - d_start).days / 365.25
    tpy = n / yrs
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    regime_results.append((name, n, m, wr, pf, cum, sharpe))
    print(f'{name:<30} {n:>3} {m:>7.3f} {wr:>5.1f} {pf:>5.2f} {cum:>+7.2f}% {sharpe:>7.3f}')

# ---------- Q3: Recent-bias check (Gate C: L18) ----------
print()
print('=' * 80)
print('Q3: Recent-bias check (Gate C: L18 mandatory)')
print('=' * 80)
all_rets = [r for _, r in trades_first_hr_proxy]
recent_rets = [r for d, r in trades_first_hr_proxy if d >= date(2020, 1, 1)]

def quick_sharpe(rets, yrs):
    n = len(rets)
    if n == 0:
        return None
    m = mean(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    tpy = n / yrs
    return (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0

s_all = quick_sharpe(all_rets, 28.4)
s_recent = quick_sharpe(recent_rets, 6.4)
print(f'  28-year Sharpe: {s_all:.3f}')
print(f'  Recent 6.4y Sharpe: {s_recent:.3f}')
if s_all > 0:
    ratio = s_recent / s_all
    print(f'  Ratio recent/long: {ratio:.2f}x')
    if ratio > 2.5:
        print(f'  ❌ L18 AUTO-KILL: ratio > 2.5x')
    elif 0.5 < ratio < 2.5:
        print(f'  ✅ L18 PASS')
    else:
        print(f'  ⚠️ L18 WARNING')
else:
    print(f'  ❌ 28y Sharpe negative → ratio undefined, AUTO-KILL')

# ---------- VERDICT ----------
print()
print('=' * 80)
print('VERDICT — apply SOP v2 4 gates')
print('=' * 80)

if s_proxy is None or s_all is None:
    print('Insufficient data')
    sys.exit(1)

regime_pass = sum(1 for _, _, _, _, _, _, sh in regime_results if sh > 0.3)

print(f'  Gate A 28y Sharpe > 0.4:        {"PASS" if s_proxy["sharpe"] > 0.4 else "FAIL"}  ({s_proxy["sharpe"]:.3f})')
print(f'  Gate A 28y PF > 1.3:            {"PASS" if s_proxy["pf"] > 1.3 else "FAIL"}  ({s_proxy["pf"]:.3f})')
ratio_str = f'{s_recent / s_all:.2f}x' if s_all > 0 else 'undefined (neg)'
ratio_pass = (s_all > 0 and 0.4 <= s_recent / s_all <= 2.5)
print(f'  Gate C L18 ratio < 2.5x:        {"PASS" if ratio_pass else "FAIL"}  ({ratio_str})')
print(f'  Gate B ≥4/6 regimes Sharpe>0.3: {"PASS" if regime_pass >= 4 else "FAIL"}  ({regime_pass}/6)')
print()
all_pass = (s_proxy['sharpe'] > 0.4 and s_proxy['pf'] > 1.3
            and ratio_pass and regime_pass >= 4)
if all_pass:
    print('  ✅ ALL 4 GATES PASS → GO for W1 spec')
else:
    print('  ❌ GATE(S) FAIL → KILL S7 → write S7_FINAL_VERDICT.md')

# Additional context: 78 expected trades (12/yr × 6.5y) vs actual
expected_trades = 12 * 28.4
print()
print(f'  Sample sufficiency: actual {len(trades_first_hr_proxy)} vs expected {expected_trades:.0f} over 28y')
if len(trades_first_hr_proxy) < 50:
    print(f'  ⚠️ Sample < 50 — statistical significance weak')
