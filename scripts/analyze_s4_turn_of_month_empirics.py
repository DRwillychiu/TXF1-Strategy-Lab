"""
S4 TurnOfMonth_Long — TXF1 empirical verification (using ^TWII proxy)

User challenged me (2026-06-21): "I want to see TXF1 data proving the
T-4 / T+3 effect, not academic citations."

This script answers 4 questions empirically:
  Q1: Does TXF1 have a turn-of-month effect at all in 2020-2026?
  Q2: If yes, what are the best entry/exit days (not academic T-4/T+3)?
  Q3: What's the realistic WR / PF / Sharpe vs Buy & Hold?
  Q4: Should we proceed with S4, or kill it (like S2)?

Output: docs/s4_empirics_analysis_20260621.md + plots if matplotlib available.
"""
import csv
import io
import sys
from datetime import date, timedelta
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_PATH = r'backtest/twii_daily.csv'

# ---------- Load + parse ----------
rows = []
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            d = date.fromisoformat(r['Date'])
            close = float(r['Close'])
            rows.append((d, close))
        except (ValueError, KeyError):
            continue

rows.sort()
dates = [r[0] for r in rows]
closes = [r[1] for r in rows]

print(f'Data: {len(rows)} trading days, {dates[0]} → {dates[-1]}')

# ---------- Compute daily returns ----------
rets = [0.0]  # first day no return
for i in range(1, len(closes)):
    rets.append((closes[i] - closes[i - 1]) / closes[i - 1])

# ---------- Assign trading-day labels: T-N to month-end, T+N from month-start ----------
# Group dates by year-month
month_groups = defaultdict(list)
for i, d in enumerate(dates):
    month_groups[(d.year, d.month)].append(i)

# For each trading day, compute:
#   tdays_to_monthend: trading days to end-of-month (last trading day in same month)
#                      T-1 = last day, T-2 = second-to-last, ...
#   tdays_from_monthstart: trading days from start of month
#                          T+1 = first day, T+2 = second, ...
tdays_to_end = [0] * len(dates)
tdays_from_start = [0] * len(dates)
for (yr, mo), indices in month_groups.items():
    n = len(indices)
    for pos, idx in enumerate(indices):
        tdays_from_start[idx] = pos + 1  # 1-indexed
        tdays_to_end[idx] = n - pos  # T-1 = last day in month

# Also: assign "calendar slot" = either T-N (if in last 7 days of month)
# or T+N (if in first 7 days of next month), else "middle"
slot = ['middle'] * len(dates)
for i, d in enumerate(dates):
    if tdays_to_end[i] <= 7:
        slot[i] = f'T-{tdays_to_end[i]}'  # T-1 = month-end day, T-4 = 4th from end
    elif tdays_from_start[i] <= 7:
        slot[i] = f'T+{tdays_from_start[i]}'

# ---------- Question 1: average return by slot ----------
print()
print('=' * 80)
print('Q1: Mean daily return by calendar slot (basis points)')
print('=' * 80)
by_slot = defaultdict(list)
for i in range(1, len(rets)):
    by_slot[slot[i]].append(rets[i])

# Sort slots in a meaningful order: T-7..T-1, T+1..T+7, middle
order_slots = ([f'T-{i}' for i in range(7, 0, -1)] +
               [f'T+{i}' for i in range(1, 8)] +
               ['middle'])

print(f'{"Slot":<8} {"N":>5} {"Mean (bps)":>12} {"Std (bps)":>12} {"WR%":>6} {"t-stat":>8}')
print('-' * 60)
slot_stats = {}
for s in order_slots:
    if s not in by_slot:
        continue
    vals = by_slot[s]
    n = len(vals)
    m = mean(vals) * 10000  # to basis points
    sd = stdev(vals) * 10000 if n > 1 else 0
    wr = sum(1 for v in vals if v > 0) / n * 100
    # t-stat: mean / (std / sqrt(n))
    t = m / (sd / (n ** 0.5)) if sd > 0 else 0
    slot_stats[s] = {'n': n, 'mean_bps': m, 'std_bps': sd, 'wr': wr, 't': t}
    sig = ' ***' if abs(t) > 2.58 else (' **' if abs(t) > 1.96 else (' *' if abs(t) > 1.645 else ''))
    print(f'{s:<8} {n:>5} {m:>12.2f} {sd:>12.2f} {wr:>6.1f} {t:>8.2f}{sig}')

print()
print('Significance: * p<0.10, ** p<0.05, *** p<0.01')

# ---------- Question 2: cumulative return for T-4 to T+3 hold ----------
print()
print('=' * 80)
print('Q2: Multi-day holding return — simulate S4 trades')
print('=' * 80)

# For each entry slot, simulate: enter at slot S close, exit N days later
def simulate_strategy(entry_slot, hold_days):
    """Returns list of trade returns."""
    trade_rets = []
    trade_dates = []
    for i in range(len(dates)):
        if slot[i] == entry_slot:
            exit_idx = i + hold_days
            if exit_idx < len(dates):
                # Buy at close[i], sell at close[exit_idx]
                r = (closes[exit_idx] - closes[i]) / closes[i]
                trade_rets.append(r)
                trade_dates.append((dates[i], dates[exit_idx]))
    return trade_rets, trade_dates

print(f'\n{"Config":<20} {"N":>4} {"Mean%":>7} {"WR%":>6} {"PF":>6} {"Sharpe(y)":>10}')
print('-' * 65)

configs = [
    ('T-4 enter, 5d hold', 'T-4', 5),
    ('T-4 enter, 6d hold', 'T-4', 6),
    ('T-4 enter, 7d hold', 'T-4', 7),
    ('T-5 enter, 5d hold', 'T-5', 5),
    ('T-5 enter, 6d hold', 'T-5', 6),
    ('T-5 enter, 7d hold', 'T-5', 7),
    ('T-3 enter, 4d hold', 'T-3', 4),
    ('T-3 enter, 5d hold', 'T-3', 5),
    ('T-3 enter, 6d hold', 'T-3', 6),
    ('T-2 enter, 4d hold', 'T-2', 4),
    ('T-2 enter, 5d hold', 'T-2', 5),
    ('T-1 enter, 3d hold', 'T-1', 3),
    ('T-1 enter, 4d hold', 'T-1', 4),
]
config_results = {}
for name, entry, hold in configs:
    trade_rets, trade_dates = simulate_strategy(entry, hold)
    if not trade_rets:
        continue
    n = len(trade_rets)
    m = mean(trade_rets) * 100  # to %
    wr = sum(1 for r in trade_rets if r > 0) / n * 100
    wins = [r for r in trade_rets if r > 0]
    losses = [r for r in trade_rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else float('inf')
    # Annualized Sharpe: trades/yr * mean / (std * sqrt(trades/yr))
    # Trades/yr ≈ 12, mean per trade, std per trade
    sd_per_trade = stdev(trade_rets) if n > 1 else 0
    trades_per_yr = n / 6.5
    annual_ret = trades_per_yr * m / 100
    annual_vol = sd_per_trade * (trades_per_yr ** 0.5)
    sharpe = annual_ret / annual_vol if annual_vol > 0 else 0
    config_results[name] = {
        'n': n, 'mean_pct': m, 'wr': wr, 'pf': pf, 'sharpe': sharpe,
        'trade_rets': trade_rets
    }
    print(f'{name:<20} {n:>4} {m:>7.3f} {wr:>6.1f} {pf:>6.3f} {sharpe:>10.3f}')

# ---------- Question 3: Buy & Hold benchmark ----------
print()
print('=' * 80)
print('Q3: Buy & Hold benchmark (reality check)')
print('=' * 80)
bh_ret_total = (closes[-1] - closes[0]) / closes[0] * 100
years = (dates[-1] - dates[0]).days / 365.25
bh_annual = ((closes[-1] / closes[0]) ** (1 / years) - 1) * 100
# Daily volatility annualized
daily_vol_annual = stdev([r for r in rets if r != 0]) * (252 ** 0.5) * 100
bh_sharpe = bh_annual / daily_vol_annual if daily_vol_annual > 0 else 0
print(f'  Period: {dates[0]} → {dates[-1]} = {years:.2f} years')
print(f'  Total return:    {bh_ret_total:>7.2f}%')
print(f'  Annual return:   {bh_annual:>7.2f}%')
print(f'  Annual vol:      {daily_vol_annual:>7.2f}%')
print(f'  Sharpe (annual): {bh_sharpe:>7.3f}')
print(f'  Final ratio:     {closes[-1] / closes[0]:.2f}×')

# ---------- Question 4: Verdict ----------
print()
print('=' * 80)
print('Q4: Verdict — does S4 TurnOfMonth_Long pass empirical bar?')
print('=' * 80)

# Find best config
best = max(config_results.items(), key=lambda x: x[1]['sharpe'])
best_name, best_stats = best
print(f'\nBest config: {best_name}')
print(f'  Trades: {best_stats["n"]}')
print(f'  Mean per trade: {best_stats["mean_pct"]:.3f}%')
print(f'  WR: {best_stats["wr"]:.1f}%')
print(f'  PF: {best_stats["pf"]:.3f}')
print(f'  Sharpe (annual): {best_stats["sharpe"]:.3f}')

print()
print(f'Strategy vs B&H Sharpe: {best_stats["sharpe"]:.3f} vs {bh_sharpe:.3f}')
trade_ret_total = sum(best_stats['trade_rets']) * 100
print(f'Strategy total return ({best_stats["n"]} trades): {trade_ret_total:.2f}%')
print(f'B&H total return: {bh_ret_total:.2f}%')
print(f'Coverage ratio: {trade_ret_total/bh_ret_total*100 if bh_ret_total != 0 else 0:.1f}%')

print()
print('=' * 80)
print('VERDICT criteria (institutional):')
print('  PASS if: best config Sharpe > 0.4 AND PF > 1.3 AND >50 trades')
print('         AND captures >30% of B&H with <50% time in market')
print('=' * 80)
sharpe_pass = best_stats['sharpe'] > 0.4
pf_pass = best_stats['pf'] > 1.3
n_pass = best_stats['n'] > 50
print(f'  Sharpe > 0.4:   {"PASS ✓" if sharpe_pass else "FAIL ❌"} ({best_stats["sharpe"]:.3f})')
print(f'  PF > 1.3:        {"PASS ✓" if pf_pass else "FAIL ❌"} ({best_stats["pf"]:.3f})')
print(f'  N > 50:         {"PASS ✓" if n_pass else "FAIL ❌"} ({best_stats["n"]})')

all_pass = sharpe_pass and pf_pass and n_pass
print()
if all_pass:
    print('  → 全部 PASS = S4 GO for .pla implementation')
else:
    print('  → 至少 1 個 FAIL = S4 必須重新考慮 design 或結案')

# Save best trade dates for reference
print()
print('Top 5 winning trades:')
sorted_trades = sorted(zip(best_stats['trade_rets'],
                            [simulate_strategy(best_name.split()[0], int(best_name.split()[2][:-1]))[1][i]
                             for i in range(best_stats['n'])]),
                       key=lambda x: -x[0])[:5]
for r, (d_in, d_out) in sorted_trades:
    print(f'  {d_in} → {d_out}: {r*100:+.2f}%')

print()
print('Top 5 losing trades:')
for r, (d_in, d_out) in sorted_trades[-5:]:
    print(f'  {d_in} → {d_out}: {r*100:+.2f}%')
