"""S3_S Regime deep dive: which market conditions win/lose + entry/exit optimization."""
import sys, io
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Use Phase 2 GA best xlsx (172 trades = v1.6, but result equivalent to v1.2)
PATH = r'C:\Users\User\Downloads\TXF1  VolSqueezeShort 策略回測績效報告.xlsx'
wb = load_workbook(PATH, data_only=True)
ws = wb['交易明細']
trades = []
pending = None
for row in ws.iter_rows(min_row=4, values_only=True):
    if not row or not row[3]: continue
    sig = str(row[3]) if row[3] else None
    dt = row[4]
    tm = row[5] if len(row) > 5 else None
    pnl = row[8] if len(row) > 8 else None
    px = row[6] if len(row) > 6 else None
    if sig and 'SE_' in sig:
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        pnl_val = pnl if isinstance(pnl, (int, float)) else 0
        pending = {'entry_d': entry_d, 'entry_t': tm, 'entry_px': px,
                   'pnl': pnl_val, 'entry_sig': sig}
    elif sig and 'SX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append({**pending, 'exit_d': exit_d, 'exit_t': tm,
                       'exit_px': px, 'exit_sig': sig})
        pending = None
print(f'Trades: {len(trades)}')

# Fetch TWII
import yfinance as yf
df = yf.download('^TWII', start='2019-09-01', end='2026-06-30',
                  progress=False, auto_adjust=False)
twii = []
for idx, r in df.iterrows():
    try:
        c = float(r['Close'].iloc[0] if hasattr(r['Close'], 'iloc') else r['Close'])
        h = float(r['High'].iloc[0] if hasattr(r['High'], 'iloc') else r['High'])
        l = float(r['Low'].iloc[0] if hasattr(r['Low'], 'iloc') else r['Low'])
        twii.append({'date': idx.date(), 'close': c, 'high': h, 'low': l})
    except: pass

# MA50 / MA200 + daily return
for i in range(len(twii)):
    twii[i]['ma50'] = mean([twii[j]['close'] for j in range(max(0, i-49), i+1)])
    twii[i]['ma200'] = mean([twii[j]['close'] for j in range(max(0, i-199), i+1)])
    twii[i]['ret'] = ((twii[i]['close'] - twii[i-1]['close']) / twii[i-1]['close'] * 100) if i > 0 else 0
twii_dict = {t['date']: t for t in twii}

# Regime classification (MA-based + vol overlay)
def classify_regime(t):
    if t is None or t['ma200'] == 0:
        return 'preheat'
    ratio = t['ma50'] / t['ma200']
    if ratio > 1.05: return 'strong_bull'
    if ratio > 1.02: return 'bull'
    if ratio < 0.95: return 'strong_bear'
    if ratio < 0.98: return 'bear'
    return 'range'

# Tag each trade
for t in trades:
    twii_d = twii_dict.get(t['entry_d'])
    if twii_d is None:
        for off in range(1, 5):
            twii_d = twii_dict.get(t['entry_d'] - timedelta(days=off))
            if twii_d: break
    t['regime'] = classify_regime(twii_d)
    t['twii_ret'] = twii_d['ret'] if twii_d else 0
    # vol spike: |return| > 1.5%
    t['vol_spike'] = abs(t['twii_ret']) > 1.5
    t['big_down'] = t['twii_ret'] < -1.5
    t['big_up'] = t['twii_ret'] > 1.5

# ===== Q1+Q2+Q3: Regime breakdown =====
print()
print('='*90)
print('REGIME ANALYSIS (entry_date 對應 TWII regime)')
print('='*90)
print(f'{"Regime":<14} {"N":>4} {"WR":>5} {"PnL":>13} {"avg":>10} {"PF":>6}  notes')
print('-' * 90)
regime_stats = defaultdict(lambda: {'n':0, 'pnl':0, 'wins':0, 'pf_n':0, 'pf_d':0})
for t in trades:
    s = regime_stats[t['regime']]
    s['n'] += 1
    s['pnl'] += t['pnl']
    if t['pnl'] > 0:
        s['wins'] += 1
        s['pf_n'] += t['pnl']
    else:
        s['pf_d'] += abs(t['pnl'])
notes = {
    'strong_bull': '極強多頭 (MA50/200 > 1.05)',
    'bull': '多頭 (1.02-1.05)',
    'range': '震盪 (0.98-1.02)',
    'bear': '空頭 (0.95-0.98)',
    'strong_bear': '極強空頭 (< 0.95)',
    'preheat': '數據暖機'
}
for reg in ['strong_bull', 'bull', 'range', 'bear', 'strong_bear', 'preheat']:
    s = regime_stats[reg]
    if s['n'] == 0: continue
    wr = s['wins']/s['n']*100 if s['n'] else 0
    pf = s['pf_n']/s['pf_d'] if s['pf_d'] > 0 else 99
    avg = s['pnl']/s['n']
    print(f'  {reg:<12} {s["n"]:>4} {wr:>4.0f}% {s["pnl"]:>+13,.0f} {avg:>+10,.0f} {pf:>5.2f}  {notes.get(reg, "")}')

# ===== Vol spike days =====
print()
print('='*90)
print('VOL SPIKE ANALYSIS (entry_day TWII |return| > 1.5%)')
print('='*90)
spike_down = [t for t in trades if t['big_down']]
spike_up = [t for t in trades if t['big_up']]
normal = [t for t in trades if not t['vol_spike']]
def stat(label, lst):
    if not lst:
        print(f'  {label:<20} N=0')
        return
    wins = sum(1 for t in lst if t['pnl'] > 0)
    p_sum = sum(t['pnl'] for t in lst)
    pf_n = sum(t['pnl'] for t in lst if t['pnl'] > 0)
    pf_d = sum(abs(t['pnl']) for t in lst if t['pnl'] <= 0)
    pf = pf_n/pf_d if pf_d > 0 else 99
    print(f'  {label:<20} N={len(lst):>3}  WR {wins/len(lst)*100:>4.0f}%  PnL {p_sum:>+11,.0f}  '
          f'avg {p_sum/len(lst):>+9,.0f}  PF {pf:>5.2f}')
stat('Big DOWN day (-1.5%)', spike_down)
stat('Big UP day (+1.5%)', spike_up)
stat('Normal day', normal)

# ===== Q3: 多空細分 — TWII 5-day trend prior to entry =====
print()
print('='*90)
print('PRE-ENTRY TREND (TWII 過去 5 trading days 走勢)')
print('='*90)
for t in trades:
    twii_d = twii_dict.get(t['entry_d'])
    if twii_d is None: t['trend5'] = 'unknown'; continue
    # Find index
    idx = next((i for i, x in enumerate(twii) if x['date'] == twii_d['date']), -1)
    if idx < 5: t['trend5'] = 'unknown'; continue
    ret5 = (twii[idx]['close'] - twii[idx-5]['close']) / twii[idx-5]['close'] * 100
    if ret5 < -3: t['trend5'] = 'falling_hard'
    elif ret5 < -1: t['trend5'] = 'falling'
    elif ret5 < 1: t['trend5'] = 'flat'
    elif ret5 < 3: t['trend5'] = 'rising'
    else: t['trend5'] = 'rising_hard'
trend_stats = defaultdict(lambda: {'n':0, 'pnl':0, 'wins':0})
for t in trades:
    s = trend_stats[t['trend5']]
    s['n'] += 1
    s['pnl'] += t['pnl']
    if t['pnl'] > 0: s['wins'] += 1
print(f'{"5-day Trend":<16} {"N":>4} {"WR":>5} {"PnL":>13} {"avg":>10}')
for trend in ['falling_hard', 'falling', 'flat', 'rising', 'rising_hard', 'unknown']:
    s = trend_stats[trend]
    if s['n'] == 0: continue
    wr = s['wins']/s['n']*100 if s['n'] else 0
    print(f'  {trend:<14} {s["n"]:>4} {wr:>4.0f}% {s["pnl"]:>+13,.0f} {s["pnl"]/s["n"]:>+10,.0f}')

# ===== Q4: Exit signal × regime cross-table =====
print()
print('='*90)
print('EXIT SIGNAL x REGIME CROSS-TABLE')
print('='*90)
cross = defaultdict(lambda: defaultdict(lambda: {'n':0, 'pnl':0}))
for t in trades:
    cross[t['regime']][t['exit_sig']]['n'] += 1
    cross[t['regime']][t['exit_sig']]['pnl'] += t['pnl']

exit_sigs = ['SX_VS_TP', 'SX_VS_SP', 'SX_VS_SL', 'SX_VS_Mid', 'SX_VS_TimeStop', 'SX_VS_Settlement']
regimes = ['strong_bull', 'bull', 'range', 'bear', 'strong_bear']
print(f'{"Exit":<22}  ' + '  '.join(f'{r:<12}' for r in regimes))
for sig in exit_sigs:
    line = f'  {sig:<20}'
    for reg in regimes:
        s = cross[reg].get(sig, {'n':0, 'pnl':0})
        if s['n'] == 0:
            line += f'  {"-":<12}'
        else:
            line += f'  {s["n"]:>2}/{s["pnl"]:>+8,.0f}'
    print(line)

# ===== Entry trigger analysis: BWPctile distribution at entry =====
print()
print('='*90)
print('SUMMARY VERDICTS')
print('='*90)
total_pnl = sum(t['pnl'] for t in trades)
print(f'Total trades: {len(trades)}')
print(f'Total Net:    {total_pnl:+,.0f}')
print()
print(f'>>> WORST regime: ', end='')
worst = min(regime_stats.items(), key=lambda x: x[1]['pnl'] if x[1]['n']>0 else 999)
print(f'{worst[0]} (N={worst[1]["n"]}, PnL {worst[1]["pnl"]:+,.0f}, avg {worst[1]["pnl"]/worst[1]["n"]:+,.0f})')

print(f'>>> BEST regime:  ', end='')
best = max(regime_stats.items(), key=lambda x: x[1]['pnl'] if x[1]['n']>0 else -999)
print(f'{best[0]} (N={best[1]["n"]}, PnL {best[1]["pnl"]:+,.0f}, avg {best[1]["pnl"]/best[1]["n"]:+,.0f})')

print(f'>>> Big DOWN day Net: {sum(t["pnl"] for t in spike_down):+,.0f} ({len(spike_down)} trades)')
print(f'>>> Big UP day Net:   {sum(t["pnl"] for t in spike_up):+,.0f} ({len(spike_up)} trades)')
print(f'>>> Normal day Net:   {sum(t["pnl"] for t in normal):+,.0f} ({len(normal)} trades)')

print(f'>>> Falling-hard 5d trend: ', end='')
s = trend_stats['falling_hard']
if s['n']: print(f'PnL {s["pnl"]:+,.0f} ({s["n"]} trades, WR {s["wins"]/s["n"]*100:.0f}%)')
print(f'>>> Rising-hard 5d trend:  ', end='')
s = trend_stats['rising_hard']
if s['n']: print(f'PnL {s["pnl"]:+,.0f} ({s["n"]} trades, WR {s["wins"]/s["n"]*100:.0f}%)')
