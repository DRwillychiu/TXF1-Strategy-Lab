"""S3_S v1.1 baseline backtest analyzer - identify which trades caught real extreme events."""
import sys, io
from collections import defaultdict, Counter
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r'C:\Users\User\Downloads\TXF1  VolSqueezeShort 策略回測績效報告.xlsx'
wb = load_workbook(PATH, data_only=True)

# === Sheet 1: Performance summary ===
print('=' * 80)
print('PERFORMANCE SUMMARY')
print('=' * 80)
ws = wb['策略分析']
metrics = {}
for row in ws.iter_rows(min_row=1, max_row=100, values_only=True):
    if not row[0]: continue
    label = str(row[0]).strip()
    if label in ['淨利', '毛利', '毛損', '獲利因子', '調整獲利因子', '滑價支付',
                 '交易總次數', '%勝率', '%獲利交易', '%虧損交易',
                 '年度夏普比率', '索丁諾比率', '年報酬率',
                 '最大策略虧損', '最大策略虧損 (%)',
                 '最大連續獲利', '最大連續虧損',
                 '平均交易獲利', '最大單筆獲利', '最大單筆虧損']:
        metrics[label] = row[1]
        print(f'  {label:<20} {row[1]}')

# === Sheet 5: Settings ===
print()
print('=' * 80)
print('INPUTS USED')
print('=' * 80)
ws = wb['設定']
for row in ws.iter_rows(values_only=True):
    if row[0] and row[1] is not None:
        print(f'  {str(row[0]):<30} {row[1]}')

# === Sheet 2: Trade details ===
print()
print('=' * 80)
print('TRADE DETAILS EXTRACTION')
print('=' * 80)
ws = wb['交易明細']
trades = []
pending = None
for row in ws.iter_rows(min_row=4, values_only=True):
    if not row or not row[3]: continue
    sig = str(row[3]) if row[3] else None
    dt = row[4]
    tm = row[5] if len(row) > 5 else None
    px = row[6] if len(row) > 6 else None
    pnl = row[8] if len(row) > 8 else None
    if sig and 'SE_' in sig:
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        pnl_val = pnl if isinstance(pnl, (int, float)) else 0
        pending = {'entry_d': entry_d, 'entry_t': tm, 'entry_px': px,
                   'entry_sig': sig, 'pnl': pnl_val}
    elif sig and 'SX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append({**pending, 'exit_d': exit_d, 'exit_t': tm,
                       'exit_px': px, 'exit_sig': sig})
        pending = None
print(f'Total trades extracted: {len(trades)}')

# === Year distribution ===
print()
print('=' * 80)
print('YEAR DISTRIBUTION + REGIME CONTEXT')
print('=' * 80)
yr_stats = defaultdict(lambda: {'n': 0, 'pnl': 0, 'wins': 0, 'pf_n': 0, 'pf_d': 0})
for t in trades:
    y = t['entry_d'].year
    yr_stats[y]['n'] += 1
    yr_stats[y]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        yr_stats[y]['wins'] += 1
        yr_stats[y]['pf_n'] += t['pnl']
    else:
        yr_stats[y]['pf_d'] += abs(t['pnl'])

regime_notes = {
    2020: 'COVID crash Q1 + recovery',
    2021: 'Bull continuation, low vol',
    2022: 'Fed tightening cycle, Ukraine war Feb, full year bear',
    2023: 'AI bull start, mixed',
    2024: 'Bull continuation, Aug BoJ shock, Nov US election',
    2025: 'Strong bull',
    2026: 'Trump tariffs April, current ongoing',
}
print(f'{"Year":<6} {"N":>4} {"PnL":>12} {"WR":>6} {"PF":>6}  Regime')
print('-' * 100)
for y in sorted(yr_stats.keys()):
    s = yr_stats[y]
    wr = s['wins']/s['n']*100 if s['n'] else 0
    pf = s['pf_n']/s['pf_d'] if s['pf_d'] else 99
    print(f'{y:<6} {s["n"]:>4} {s["pnl"]:>+12,.0f} {wr:>5.1f}% {pf:>5.2f}  {regime_notes.get(y, "?")}')

# === Top 15 winners and losers ===
print()
print('=' * 80)
print('TOP 15 WINNERS (biggest profits)')
print('=' * 80)
print(f'{"Entry":<13} {"Exit":<13} {"PnL":>10} {"ExitSig":<22} {"Bars":>5}  {"Event?"}')
print('-' * 110)
known_events = {
    '2020-03': 'COVID crash',
    '2020-04': 'COVID continuation',
    '2022-02': 'Ukraine war begins',
    '2022-03': 'Russia invasion peak',
    '2022-05': 'Fed 50bp hike',
    '2022-06': 'Fed 75bp hike',
    '2022-09': 'Fed 75bp + recession fear',
    '2022-10': 'BoE crisis + UK gilt',
    '2024-08': 'BoJ Aug shock + carry unwind',
    '2024-11': 'US election uncertainty',
    '2024-12': 'Year-end Fed hawkish',
    '2025-04': 'Trump tariff anniversary',
    '2025-08': 'Mid-2025 vol spike',
    '2026-01': 'Year start',
    '2026-04': 'Trump Liberation Day tariffs',
}
def tag_event(d):
    key = f'{d.year}-{d.month:02d}'
    return known_events.get(key, '')

winners = sorted(trades, key=lambda t: -t['pnl'])[:15]
for t in winners:
    days = (t['exit_d'] - t['entry_d']).days
    print(f'{str(t["entry_d"]):<13} {str(t["exit_d"]):<13} {t["pnl"]:>+10,.0f} '
          f'{t["exit_sig"]:<22} {days:>5}  {tag_event(t["entry_d"])}')

print()
print('=' * 80)
print('TOP 15 LOSERS (biggest losses)')
print('=' * 80)
print(f'{"Entry":<13} {"Exit":<13} {"PnL":>10} {"ExitSig":<22} {"Bars":>5}  {"Event?"}')
print('-' * 110)
losers = sorted(trades, key=lambda t: t['pnl'])[:15]
for t in losers:
    days = (t['exit_d'] - t['entry_d']).days
    print(f'{str(t["entry_d"]):<13} {str(t["exit_d"]):<13} {t["pnl"]:>+10,.0f} '
          f'{t["exit_sig"]:<22} {days:>5}  {tag_event(t["entry_d"])}')

# === Exit signal distribution ===
print()
print('=' * 80)
print('EXIT SIGNAL DISTRIBUTION (5-layer exit verify)')
print('=' * 80)
sig_stats = defaultdict(lambda: {'n': 0, 'pnl': 0, 'wins': 0})
for t in trades:
    s = sig_stats[t['exit_sig']]
    s['n'] += 1
    s['pnl'] += t['pnl']
    if t['pnl'] > 0: s['wins'] += 1
print(f'{"ExitSig":<22} {"N":>4} {"PnL":>12} {"WR":>6} {"Avg":>10}')
print('-' * 65)
for sig in sorted(sig_stats.keys()):
    s = sig_stats[sig]
    wr = s['wins']/s['n']*100 if s['n'] else 0
    avg = s['pnl']/s['n']
    print(f'{sig:<22} {s["n"]:>4} {s["pnl"]:>+12,.0f} {wr:>5.1f}% {avg:>+10,.0f}')

# === Key extreme events check ===
print()
print('=' * 80)
print('KEY EXTREME EVENT COVERAGE CHECK')
print('=' * 80)
extreme_periods = [
    ('2020-03-01', '2020-04-30', 'COVID crash + recovery'),
    ('2022-01-15', '2022-03-31', 'Ukraine war + Fed pivot'),
    ('2022-04-01', '2022-10-31', 'Fed tightening 2022 H2'),
    ('2024-08-01', '2024-08-15', 'BoJ Aug shock'),
    ('2024-11-01', '2024-11-30', 'US election'),
    ('2025-04-01', '2025-04-15', 'Trump tariff early 2025'),
    ('2026-04-01', '2026-04-10', 'Trump Liberation Day tariffs'),
]
from datetime import date
def parse_d(s):
    parts = s.split('-')
    return date(int(parts[0]), int(parts[1]), int(parts[2]))

for start_s, end_s, label in extreme_periods:
    start = parse_d(start_s)
    end = parse_d(end_s)
    period_trades = [t for t in trades if start <= t['entry_d'] <= end]
    pnl = sum(t['pnl'] for t in period_trades)
    wins = sum(1 for t in period_trades if t['pnl'] > 0)
    print(f'\n  {label} ({start_s} ~ {end_s}):')
    print(f'    Trades: {len(period_trades)}, PnL: {pnl:+,.0f}, Wins: {wins}/{len(period_trades)}')
    if period_trades:
        for t in period_trades[:5]:
            print(f'      {t["entry_d"]} -> {t["exit_d"]}  {t["pnl"]:>+10,.0f}  {t["exit_sig"]}')
        if len(period_trades) > 5:
            print(f'      ... +{len(period_trades)-5} more')
    else:
        print(f'    !! NO TRADES - event missed')

# === Monthly density (find clusters) ===
print()
print('=' * 80)
print('MONTHLY TRADE DENSITY (top 12 busiest months)')
print('=' * 80)
mo_stats = defaultdict(lambda: {'n': 0, 'pnl': 0})
for t in trades:
    k = f'{t["entry_d"].year}-{t["entry_d"].month:02d}'
    mo_stats[k]['n'] += 1
    mo_stats[k]['pnl'] += t['pnl']
top_busy = sorted(mo_stats.items(), key=lambda x: -x[1]['n'])[:12]
print(f'{"Month":<10} {"N":>4} {"PnL":>12}  Event?')
print('-' * 65)
for k, s in top_busy:
    print(f'{k:<10} {s["n"]:>4} {s["pnl"]:>+12,.0f}  {known_events.get(k, "")}')
