"""S3_L DD Clustering 深 dive - 找出 max DD source: single event vs systemic."""
import sys, io
from collections import defaultdict
from statistics import mean, stdev
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r'C:\Users\User\Downloads\TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後3.xlsx'
wb = load_workbook(PATH, data_only=True)
ws = wb['交易明細']

# Extract trades with full detail
trades = []  # (entry_date, exit_date, exit_signal, pnl, entry_price, exit_price)
pending = None
for row in ws.iter_rows(min_row=4, values_only=True):
    sig = row[3] if len(row) > 3 else None
    dt = row[4] if len(row) > 4 else None
    px = row[6] if len(row) > 6 else None
    pnl = row[8] if len(row) > 8 else None
    if sig and isinstance(sig, str) and 'LE_' in sig:
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        pnl_val = pnl if isinstance(pnl, (int, float)) else 0
        pending = (entry_d, pnl_val, px)
    elif sig and isinstance(sig, str) and 'LX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append({
            'entry_d': pending[0], 'exit_d': exit_d, 'pnl': pending[1],
            'entry_px': pending[2], 'exit_px': px, 'exit_sig': sig
        })
        pending = None

# Sort by entry date
trades.sort(key=lambda t: t['entry_d'])

# Build daily equity curve (assign PnL to exit date)
daily_pnl = defaultdict(float)
for t in trades:
    daily_pnl[t['exit_d']] += t['pnl']

sorted_dates = sorted(daily_pnl.keys())
equity = []
cum = 0
peak = 0
peak_date = sorted_dates[0]
dd_series = []
for d in sorted_dates:
    cum += daily_pnl[d]
    if cum > peak:
        peak = cum
        peak_date = d
    dd = peak - cum
    equity.append({'date': d, 'cum': cum, 'peak': peak, 'peak_date': peak_date, 'dd': dd})

# Find Max DD
max_dd_row = max(equity, key=lambda r: r['dd'])
max_dd = max_dd_row['dd']
max_dd_date = max_dd_row['date']
max_dd_peak_date = max_dd_row['peak_date']
max_dd_peak = max_dd_row['peak']

# Find DD recovery date (when cum returns to peak)
recovery_date = None
for r in equity:
    if r['date'] > max_dd_date and r['cum'] >= max_dd_peak:
        recovery_date = r['date']
        break

print('=' * 80)
print('S3_L Max DD Source Analysis')
print('=' * 80)
print(f'Max DD: {max_dd:,.0f} NTD ({max_dd/1000000*100:.2f}% of initial 1M account)')
print(f'Peak date:     {max_dd_peak_date}  (equity peak = {max_dd_peak:,.0f})')
print(f'Trough date:   {max_dd_date}  (equity = {max_dd_row["cum"]:,.0f})')
print(f'Recovery date: {recovery_date}  ({(recovery_date - max_dd_date).days if recovery_date else "?"} days to recover)')
duration = (max_dd_date - max_dd_peak_date).days
print(f'DD Duration:   {duration} days (peak → trough)')
print()

# Find ALL trades that contributed to max DD (entry_d > peak_date AND exit_d <= max_dd_date)
dd_trades = [t for t in trades
             if t['exit_d'] > max_dd_peak_date and t['exit_d'] <= max_dd_date]
print(f'=== Trades contributing to Max DD ({len(dd_trades)} trades) ===')
print(f'{"Entry":<12} {"Exit":<12} {"ExitSig":<22} {"PnL":>10} {"Cum DD":>10}')
print('-' * 70)
running = 0
for t in dd_trades:
    running += t['pnl']
    print(f'{str(t["entry_d"]):<12} {str(t["exit_d"]):<12} {t["exit_sig"]:<22} {t["pnl"]:>+10,.0f} {running:>+10,.0f}')

# Single event vs cluster classification
losses = [t for t in dd_trades if t['pnl'] < 0]
wins = [t for t in dd_trades if t['pnl'] > 0]
total_loss = sum(t['pnl'] for t in losses)
total_win = sum(t['pnl'] for t in wins)
max_single_loss = min((t['pnl'] for t in losses), default=0)
max_single_loss_pct = abs(max_single_loss) / max_dd * 100 if max_dd > 0 else 0

print()
print('=== DD Composition ===')
print(f'  Losing trades:       {len(losses)}  total = {total_loss:+,.0f}')
print(f'  Winning trades:      {len(wins)}  total = {total_win:+,.0f}')
print(f'  Worst single loss:   {max_single_loss:+,.0f}')
print(f'  Worst loss / Max DD: {max_single_loss_pct:.1f}%')
print()

# Verdict
print('=== Verdict ===')
if max_single_loss_pct >= 80:
    print(f'  → ⚠️ SINGLE EVENT: {max_single_loss_pct:.0f}% of max DD from 1 trade')
    print(f'    Acceptable if explainable (e.g. SL widen on extreme bar)')
elif max_single_loss_pct >= 50:
    print(f'  → 🟡 DOMINANT EVENT: 1 trade = {max_single_loss_pct:.0f}% of max DD')
    print(f'    Mostly single event with secondary contributors')
elif len(losses) >= 5 and len(losses) >= len(dd_trades) * 0.6:
    print(f'  → ❌ SYSTEMIC CLUSTER: {len(losses)} losing trades in DD period')
    print(f'    Strategy systematically failed during this regime')
else:
    print(f'  → 🟢 MIXED: not dominant single event, not full cluster')
    print(f'    Normal drawdown distribution')

# Regime context (which year/period the DD happened in)
print()
print('=== Temporal context ===')
print(f'  DD peak year: {max_dd_peak_date.year}-{max_dd_peak_date.month:02d}')
print(f'  DD trough year: {max_dd_date.year}-{max_dd_date.month:02d}')

# Top 5 worst single trades overall (compare to max DD source)
print()
print('=== Top 5 worst single trades overall ===')
worst5 = sorted(trades, key=lambda t: t['pnl'])[:5]
for t in worst5:
    in_dd = '* in max-DD' if (t['exit_d'] > max_dd_peak_date and t['exit_d'] <= max_dd_date) else ''
    print(f'  {t["entry_d"]} → {t["exit_d"]}  {t["exit_sig"]:<22} {t["pnl"]:+10,.0f}  {in_dd}')

# All historical DD events > 50K (count clusters)
print()
print('=== All major DD events (DD > 50K NTD) ===')
in_dd = False
dd_start = None
dd_max = 0
events = []
for r in equity:
    if r['dd'] > 0 and not in_dd:
        in_dd = True
        dd_start = r['date']
        dd_max = r['dd']
        dd_trough = r['date']
    elif in_dd:
        if r['dd'] > dd_max:
            dd_max = r['dd']
            dd_trough = r['date']
        if r['dd'] == 0:
            if dd_max >= 50000:
                events.append((dd_start, dd_trough, r['date'], dd_max))
            in_dd = False
if in_dd and dd_max >= 50000:
    events.append((dd_start, dd_trough, sorted_dates[-1], dd_max))

print(f'  Total DD events > 50K NTD: {len(events)}')
print(f'  {"Peak->Start":<13} {"Trough":<12} {"Recovery":<12} {"Max DD":>10}')
for s, t, r, dd in events:
    marker = ' ← MAX' if dd == max_dd else ''
    print(f'  {str(s):<13} {str(t):<12} {str(r):<12} {dd:>10,.0f}{marker}')

# Distribution
dds = [e[3] for e in events]
if dds:
    print()
    print(f'  Mean DD event: {mean(dds):,.0f}')
    if len(dds) > 1:
        print(f'  Std DD event:  {stdev(dds):,.0f}')
        print(f'  Max DD / Mean: {max(dds)/mean(dds):.2f}x')
        print(f'  Max DD / 2nd:  {max(dds)/sorted(dds)[-2]:.2f}x')
