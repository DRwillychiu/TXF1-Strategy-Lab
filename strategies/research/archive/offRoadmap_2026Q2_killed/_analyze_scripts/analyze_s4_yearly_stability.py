"""
S4 TurnOfMonth_Long — Yearly Stability + Sub-Period Analysis

Follow-up to analyze_s4_turn_of_month_empirics.py per user choice C (2026-06-21):
"Don't proceed to .pla until you prove cross-year stability — Top 5 winning
trades all in 2024-11+ is a S3 v1.1-style red flag."

Tests:
  Q5: Year-by-year P&L breakdown for best config
  Q6: 2020-2024 (early) vs 2024-11→2026-06 (late) sub-period split
  Q7: Would early-period alone pass institutional bar?
"""
import csv
import io
import sys
from datetime import date
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_PATH = r'backtest/twii_daily.csv'

# ---------- Load ----------
rows = []
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        try:
            rows.append((date.fromisoformat(r['Date']), float(r['Close'])))
        except (ValueError, KeyError):
            continue
rows.sort()
dates = [x[0] for x in rows]
closes = [x[1] for x in rows]

# ---------- Slot labels ----------
month_groups = defaultdict(list)
for i, d in enumerate(dates):
    month_groups[(d.year, d.month)].append(i)
tdays_to_end = [0] * len(dates)
tdays_from_start = [0] * len(dates)
for (yr, mo), idx_list in month_groups.items():
    n = len(idx_list)
    for pos, idx in enumerate(idx_list):
        tdays_from_start[idx] = pos + 1
        tdays_to_end[idx] = n - pos
slot = ['middle'] * len(dates)
for i in range(len(dates)):
    if tdays_to_end[i] <= 7:
        slot[i] = f'T-{tdays_to_end[i]}'
    elif tdays_from_start[i] <= 7:
        slot[i] = f'T+{tdays_from_start[i]}'

# ---------- Simulate best config: T-1 enter, 4d hold ----------
def simulate(entry_slot, hold_days):
    out = []
    for i in range(len(dates)):
        if slot[i] == entry_slot:
            j = i + hold_days
            if j < len(dates):
                r = (closes[j] - closes[i]) / closes[i]
                out.append((r, dates[i], dates[j]))
    return out

best_trades = simulate('T-1', 4)
print(f'Best config: T-1 enter, 4d hold — N={len(best_trades)} trades')
print()

# ---------- Q5: Yearly breakdown ----------
print('=' * 80)
print('Q5: YEARLY BREAKDOWN (best config trade by trade by year)')
print('=' * 80)
yearly = defaultdict(list)
for r, d_in, d_out in best_trades:
    yearly[d_in.year].append(r)

print(f'{"Year":<6} {"N":>4} {"Mean%":>8} {"Median%":>9} {"WR%":>6} {"PF":>7} {"Cum%":>9}  Trades distribution')
print('-' * 90)
for yr in sorted(yearly.keys()):
    vals = yearly[yr]
    n = len(vals)
    m = mean(vals) * 100
    sv = sorted(vals)
    med = sv[n // 2] * 100 if n > 0 else 0
    wr = sum(1 for v in vals if v > 0) / n * 100
    wins = [v for v in vals if v > 0]
    losses = [v for v in vals if v <= 0]
    pf_val = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99.0
    cum = sum(vals) * 100
    # Mini visualization
    viz = ''.join('+' if v > 0 else '-' for v in vals)
    print(f'{yr:<6} {n:>4} {m:>8.3f} {med:>9.3f} {wr:>6.1f} {pf_val:>7.2f} {cum:>+8.2f}%  {viz}')

# ---------- Q6: Sub-period split ----------
print()
print('=' * 80)
print('Q6: SUB-PERIOD SPLIT — pre-Nov-2024 vs post')
print('=' * 80)

split_d = date(2024, 11, 1)
early = [(r, d_in) for r, d_in, _ in best_trades if d_in < split_d]
late = [(r, d_in) for r, d_in, _ in best_trades if d_in >= split_d]

def summarize(name, samples):
    if not samples:
        print(f'  {name}: NO TRADES')
        return None
    rets = [r for r, _ in samples]
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99.0
    sd = stdev(rets) if n > 1 else 0
    cum = sum(rets) * 100
    dmin = min(d for _, d in samples)
    dmax = max(d for _, d in samples)
    yrs = (dmax - dmin).days / 365.25 + 0.01
    tpy = n / yrs
    annual = tpy * m / 100
    avol = sd * (tpy ** 0.5)
    sharpe = annual / avol if avol > 0 else 0
    print(f'  {name}')
    print(f'    Period   : {dmin} → {dmax} ({yrs:.2f} yrs, {tpy:.1f} trades/yr)')
    print(f'    N        : {n}')
    print(f'    Mean%    : {m:>7.3f}   WR%: {wr:>5.1f}   PF: {pf:.3f}')
    print(f'    Cum%     : {cum:>+7.2f}%  Sharpe(y): {sharpe:.3f}')
    return {'n': n, 'sharpe': sharpe, 'pf': pf, 'cum': cum, 'm': m, 'wr': wr}

print()
s_early = summarize('EARLY (2020-01 → 2024-10) — NORMAL regime', early)
print()
s_late = summarize('LATE  (2024-11 → 2026-06) — RECENT BULL', late)

print()
if s_early and s_late:
    if s_early['sharpe'] > 0:
        ratio = s_late['sharpe'] / s_early['sharpe']
    else:
        ratio = float('inf')
    print(f'  Sharpe ratio (late/early): {ratio:.2f}x')
    if ratio > 3:
        print('  🔴 SEVERE REGIME OVER-FIT: late-period Sharpe >3x early')
    elif ratio > 2:
        print('  🟠 REGIME CONCENTRATION: late-period Sharpe >2x early')
    elif s_early['sharpe'] > 0.4:
        print('  ✅ ALPHA PERSISTS: early-period Sharpe > 0.4')
    else:
        print('  ⚠️ MARGINAL EARLY ALPHA: investigate further')

# ---------- Q7: Institutional bar on early-period alone ----------
print()
print('=' * 80)
print('Q7: WOULD EARLY-PERIOD ALONE (2020-2024) PASS INSTITUTIONAL BAR?')
print('=' * 80)
if s_early:
    print(f'  Sharpe > 0.4:  {"PASS" if s_early["sharpe"] > 0.4 else "FAIL"}  ({s_early["sharpe"]:.3f})')
    print(f'  PF > 1.3:       {"PASS" if s_early["pf"] > 1.3 else "FAIL"}  ({s_early["pf"]:.3f})')
    print(f'  N > 50:        {"PASS" if s_early["n"] > 50 else "FAIL"}  ({s_early["n"]})')
    print(f'  WR > 55%:      {"PASS" if s_early["wr"] > 55 else "FAIL"}  ({s_early["wr"]:.1f}%)')
    all_pass = (s_early['sharpe'] > 0.4 and s_early['pf'] > 1.3
                and s_early['n'] > 50 and s_early['wr'] > 55)
    print()
    if all_pass:
        print('  → REAL ALPHA across regimes → GO for S4')
    else:
        print('  → S4 alpha is regime-dependent → HIGH OVER-FIT RISK')
        print('     Decision: kill S4 OR redesign with regime filter')

# ---------- Q8: Equity curve year-end snapshot ----------
print()
print('=' * 80)
print('Q8: EQUITY CURVE — when did the money actually come?')
print('=' * 80)
cum_pct = 0.0
year_end_cum = {}
for r, d_in, d_out in best_trades:
    cum_pct += r * 100
    year_end_cum[d_in.year] = cum_pct

print(f'  {"Year":<6} {"Cum return (compounded)":<30}')
print('  ' + '-' * 40)
prev_cum = 0
for yr in sorted(year_end_cum.keys()):
    cum = year_end_cum[yr]
    incr = cum - prev_cum
    bar = '█' * max(1, int(abs(incr)))
    sign = '+' if incr >= 0 else '-'
    print(f'  {yr:<6} {cum:>+7.2f}%   ({sign}{abs(incr):.2f}%)  {bar}')
    prev_cum = cum

# ---------- Q9: Win-loss asymmetry by period ----------
print()
print('=' * 80)
print('Q9: WIN-LOSS ASYMMETRY by sub-period')
print('=' * 80)
def asym(samples, label):
    if not samples:
        return
    rets = [r for r, _ in samples]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    avg_win = mean(wins) * 100 if wins else 0
    avg_loss = mean(losses) * 100 if losses else 0
    max_win = max(wins) * 100 if wins else 0
    max_loss = min(losses) * 100 if losses else 0
    print(f'  {label}')
    print(f'    Avg win:  {avg_win:>+6.3f}%   Max win:  {max_win:>+6.2f}%')
    print(f'    Avg loss: {avg_loss:>+6.3f}%   Max loss: {max_loss:>+6.2f}%')
    print(f'    Asymmetry (avg_win / |avg_loss|): {avg_win / abs(avg_loss) if avg_loss < 0 else "N/A"}')

asym(early, 'Early (2020-2024)')
print()
asym(late, 'Late (2024-11+)')

print()
print('=' * 80)
print('FINAL VERDICT (User Q4 follow-up)')
print('=' * 80)
if s_early and s_late:
    if s_early['sharpe'] > 0.4 and s_early['pf'] > 1.3:
        print('  ✅ S4 alpha is real across regimes → GO')
    elif s_late['sharpe'] > 0.4 and s_early['sharpe'] < 0.3:
        print('  ❌ S4 alpha is regime-dependent (2024-2026 only) → KILL or REDESIGN')
    else:
        print('  ⚠️ S4 alpha is marginal → user decision required')
