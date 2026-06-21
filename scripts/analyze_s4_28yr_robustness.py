"""
S4 TurnOfMonth — 28-year robustness test (1997-2026)

User challenge (2026-06-21): "Could this be curve-fit to backtest period?"

Test: Run best config (T-1 enter, 4-day hold) on 1997-2026 TWII (~28 years).
  - Does alpha persist across decades?
  - 6 distinct macro regimes covered:
      1997-2002: Dot-com bubble + crash
      2003-2007: China-led bull market
      2008-2009: Global Financial Crisis
      2010-2014: Post-GFC recovery + Eurozone crisis
      2015-2019: Sideways + trade-war
      2020-2026: COVID + AI boom (the original backtest period)

If alpha persists in pre-2020 regimes → robust
If alpha only exists in 2020-2026 → curve-fit warning
"""
import csv
import io
import sys
from datetime import date
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- Fetch 1997-2019 + load 2020-2026 ----------
print('Fetching 1997-2019 TWII via yfinance...')
import yfinance as yf
df_old = yf.download('^TWII', start='1997-01-01', end='2020-01-01',
                     progress=False, auto_adjust=False)
old_data = []
for idx, row in df_old.iterrows():
    try:
        close = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        old_data.append((idx.date(), close))
    except (ValueError, TypeError):
        continue
print(f'  Fetched {len(old_data)} rows from 1997-2019')

# Load 2020-2026 from CSV
new_data = []
with open('backtest/twii_daily.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        try:
            new_data.append((date.fromisoformat(r['Date']), float(r['Close'])))
        except (ValueError, KeyError):
            continue
print(f'  Loaded {len(new_data)} rows from CSV 2020-2026')

# Merge + sort + dedup
all_data = sorted(set(old_data + new_data))
dates = [x[0] for x in all_data]
closes = [x[1] for x in all_data]
print(f'  TOTAL: {len(all_data)} trading days, {dates[0]} → {dates[-1]}')
print(f'  Years: {(dates[-1] - dates[0]).days / 365.25:.2f}')

# ---------- Compute slots ----------
month_groups = defaultdict(list)
for i, d in enumerate(dates):
    month_groups[(d.year, d.month)].append(i)
tdays_to_end = [0] * len(dates)
for indices in month_groups.values():
    n = len(indices)
    for pos, idx in enumerate(indices):
        tdays_to_end[idx] = n - pos
slot = ['middle'] * len(dates)
for i in range(len(dates)):
    if tdays_to_end[i] <= 7:
        slot[i] = f'T-{tdays_to_end[i]}'

# ---------- Simulate best config ----------
def simulate(entry_slot, hold_days):
    out = []
    for i in range(len(dates)):
        if slot[i] == entry_slot:
            j = i + hold_days
            if j < len(dates):
                r = (closes[j] - closes[i]) / closes[i]
                out.append((r, dates[i]))
    return out

trades = simulate('T-1', 4)
print(f'\nBest config T-1/4d hold: {len(trades)} trades over 28.4 years')

# ---------- Q1: 6 distinct regimes ----------
print()
print('=' * 80)
print('Q1: 6 macro regimes — does alpha persist?')
print('=' * 80)
regimes = [
    ('1997-2002 Dot-com bubble + crash', date(1997, 7, 1), date(2002, 12, 31)),
    ('2003-2007 China bull market',       date(2003, 1, 1), date(2007, 12, 31)),
    ('2008-2009 GFC',                     date(2008, 1, 1), date(2009, 12, 31)),
    ('2010-2014 Post-GFC + Euro crisis',  date(2010, 1, 1), date(2014, 12, 31)),
    ('2015-2019 Sideways + trade war',    date(2015, 1, 1), date(2019, 12, 31)),
    ('2020-2026 COVID + AI boom',         date(2020, 1, 1), date(2026, 12, 31)),
]

print(f'{"Regime":<40} {"N":>4} {"Mean%":>7} {"WR%":>6} {"PF":>6} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 90)
regime_stats = []
for name, d_start, d_end in regimes:
    sub = [(r, d) for r, d in trades if d_start <= d <= d_end]
    if not sub:
        print(f'{name:<40} (no trades)')
        continue
    rets = [r for r, _ in sub]
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    yrs = (sub[-1][1] - sub[0][1]).days / 365.25 + 0.01
    tpy = n / yrs
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    regime_stats.append((name, n, m, wr, pf, cum, sharpe))
    print(f'{name:<40} {n:>4} {m:>7.3f} {wr:>6.1f} {pf:>6.2f} {cum:>+7.2f}% {sharpe:>7.3f}')

# ---------- Q2: Rolling 4-year window Sharpe ----------
print()
print('=' * 80)
print('Q2: Rolling 4-year window stability — Sharpe per window')
print('=' * 80)
print(f'{"Window":<22} {"N":>4} {"Cum%":>8} {"PF":>6} {"Sharpe":>7}')
print('-' * 50)
for start_y in range(1998, 2024):
    end_y = start_y + 4
    sub = [(r, d) for r, d in trades if date(start_y, 1, 1) <= d <= date(end_y, 12, 31)]
    if len(sub) < 20:
        continue
    rets = [r for r, _ in sub]
    n = len(rets)
    cum = sum(rets) * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    sd = stdev(rets) if n > 1 else 0
    sharpe = (n / 4 * (mean(rets))) / (sd * ((n/4) ** 0.5)) if sd > 0 else 0
    flag = '✓' if sharpe > 0.4 else ('⚠️' if sharpe > 0 else '❌')
    print(f'{start_y}-{end_y:<5}        {n:>4} {cum:>+7.2f}% {pf:>6.2f} {sharpe:>7.3f}  {flag}')

# ---------- Q3: Overall 28-year vs 2020-2026 ----------
print()
print('=' * 80)
print('Q3: 28-year overall vs 2020-2026 only')
print('=' * 80)
all_rets = [r for r, _ in trades]
recent_rets = [r for r, d in trades if d >= date(2020, 1, 1)]

def summary(label, rets, yrs):
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    tpy = n / yrs
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    print(f'  {label}')
    print(f'    N={n} ({yrs:.1f}y, {tpy:.1f}/yr)')
    print(f'    Mean%={m:.3f} WR%={wr:.1f} PF={pf:.3f}')
    print(f'    Cum%={cum:+.2f}% Sharpe(y)={sharpe:.3f}')
    return sharpe

s_all = summary('28-year (1997-2026)', all_rets, 28.4)
print()
s_recent = summary('Recent only (2020-2026)', recent_rets, 6.4)

print()
ratio = s_recent / s_all if s_all > 0 else float('inf')
print(f'  Sharpe ratio recent/long-term: {ratio:.2f}x')
if abs(ratio - 1.0) < 0.3:
    print('  ✅ Recent Sharpe ≈ long-term → NOT curve-fit')
elif ratio > 1.5:
    print('  ⚠️ Recent Sharpe significantly > long-term → possibly recent-bias')
elif ratio < 0.5:
    print('  ⚠️ Recent Sharpe significantly < long-term → alpha may be decaying')

# ---------- Q4: Best vs worst 4-year window ----------
print()
print('=' * 80)
print('Q4: 28-year MAX drawdown of strategy')
print('=' * 80)
cum = 0
peak = 0
mdd = 0
mdd_start, mdd_end = None, None
trough_d = None
for r, d in trades:
    cum += r * 100
    if cum > peak:
        peak = cum
    dd = peak - cum
    if dd > mdd:
        mdd = dd
        mdd_end = d
print(f'  Total 28-year cum return: {cum:.2f}%')
print(f'  Max drawdown: -{mdd:.2f}%')
print(f'  MDD trough: {mdd_end}')

# ---------- VERDICT ----------
print()
print('=' * 80)
print('VERDICT — is S4 alpha real across 28 years?')
print('=' * 80)
sharpe_pass_count = sum(1 for _, _, _, _, _, _, sh in regime_stats if sh > 0.3)
pf_pass_count = sum(1 for _, _, _, _, pf, _, _ in regime_stats if pf > 1.2)
print(f'  Regimes with Sharpe > 0.3: {sharpe_pass_count}/{len(regime_stats)}')
print(f'  Regimes with PF > 1.2:     {pf_pass_count}/{len(regime_stats)}')

if sharpe_pass_count >= 5 and pf_pass_count >= 5:
    print('  → ✅ STRONG ROBUST: alpha exists across 5+ of 6 regimes')
elif sharpe_pass_count >= 4 and pf_pass_count >= 4:
    print('  → 🟢 ROBUST: alpha exists across 4+ regimes')
elif sharpe_pass_count >= 3:
    print('  → ⚠️ MIXED: alpha works in some regimes, not others')
else:
    print('  → ❌ CURVE-FIT WARNING: alpha mostly absent before 2020')
