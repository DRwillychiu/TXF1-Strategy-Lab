"""S3_S v1.2 FROZEN Cool=1 - 極端行情捕捉覆蓋率分析."""
import sys, io
from collections import defaultdict
from datetime import date, timedelta
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read v1.2 Cool=1 xlsx (re-uploaded as same filename)
PATH = r'C:\Users\User\Downloads\TXF1  VolSqueezeShort 策略回測績效報告_COOL1.xlsx'
wb = load_workbook(PATH, data_only=True)

ws = wb['策略分析']
metrics = {}
for row in ws.iter_rows(min_row=1, max_row=100, values_only=True):
    if not row[0]: continue
    label = str(row[0]).strip()
    if label in ['淨利','獲利因子','交易總次數','%勝率','年度夏普比率',
                 '最大策略虧損 (%)']:
        metrics[label] = row[1]
print('=== v1.2 FROZEN Cool=1 confirm ===')
for k, v in metrics.items():
    print(f'  {k}: {v}')

ws = wb['交易明細']
trades = []
pending = None
for row in ws.iter_rows(min_row=4, values_only=True):
    if not row or not row[3]: continue
    sig = str(row[3]) if row[3] else None
    dt = row[4]
    tm = row[5] if len(row) > 5 else None
    pnl = row[8] if len(row) > 8 else None
    if sig and 'SE_' in sig:
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        pnl_val = pnl if isinstance(pnl, (int, float)) else 0
        pending = {'entry_d': entry_d, 'entry_t': tm,
                   'pnl': pnl_val, 'entry_sig': sig}
    elif sig and 'SX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append({**pending, 'exit_d': exit_d, 'exit_t': tm, 'exit_sig': sig})
        pending = None

print(f'\nTotal trades: {len(trades)}')

# Build trade-by-date index
trade_dates = defaultdict(list)
for t in trades:
    trade_dates[t['entry_d']].append(t)

# Fetch TWII daily for "extreme down day" detection
print('Fetching TWII daily...')
import yfinance as yf
df = yf.download('^TWII', start='2020-01-01', end='2026-06-30',
                  progress=False, auto_adjust=False)
twii = []
for idx, row in df.iterrows():
    try:
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        twii.append((idx.date(), c))
    except: pass

# Daily returns
twii_ret = []
for i in range(1, len(twii)):
    d = twii[i][0]
    r = (twii[i][1] - twii[i-1][1]) / twii[i-1][1] * 100
    twii_ret.append((d, r, twii[i][1]))

# Find DOWN extreme days (return <= -2%)
down_extreme = [(d, r, p) for d, r, p in twii_ret if r <= -2.0]
print(f'\nDOWN extreme days (return <= -2pct): {len(down_extreme)}')

# Find DOWN smaller threshold (-1.5%) for comprehensive coverage
down_significant = [(d, r, p) for d, r, p in twii_ret if r <= -1.5]
print(f'Significant down days (return <= -1.5pct): {len(down_significant)}')

# Known macro events (manual catalog)
macro_events = [
    (date(2020, 1, 23), 'COVID 武漢封城首日'),
    (date(2020, 2, 27), 'COVID 全球擴散恐慌'),
    (date(2020, 3, 9),  'SPX 第一次熔斷'),
    (date(2020, 3, 12), 'SPX 第二次熔斷（最大跌）'),
    (date(2020, 3, 16), 'SPX 第三次熔斷'),
    (date(2020, 3, 18), 'SPX 第四次熔斷'),
    (date(2020, 4, 21), '油價負值'),
    (date(2020, 10, 28), '美選前不確定'),
    (date(2021, 1, 27), 'GameStop short squeeze'),
    (date(2021, 3, 5),  '美 bond yield surge'),
    (date(2021, 5, 12), '美通膨 + AI sell-off'),
    (date(2021, 9, 20), '恆大危機'),
    (date(2021, 12, 1), 'Omicron 變種出現'),
    (date(2022, 2, 24), '俄羅斯入侵烏克蘭'),
    (date(2022, 5, 5),  'Fed 50bp 升息'),
    (date(2022, 6, 13), 'CPI 8.6pct 史高'),
    (date(2022, 6, 16), 'Fed 75bp (1994 來最大)'),
    (date(2022, 7, 13), 'CPI 9.1pct (40 年高)'),
    (date(2022, 8, 26), 'Powell Jackson Hole hawkish'),
    (date(2022, 9, 13), 'CPI 比預期高'),
    (date(2022, 9, 21), 'Fed 75bp 第三次'),
    (date(2022, 9, 26), '英鎊崩'),
    (date(2022, 11, 3), 'Fed 75bp 第四次'),
    (date(2022, 12, 14), 'Fed hawkish dot plot'),
    (date(2023, 3, 10), 'SVB 銀行倒閉'),
    (date(2023, 3, 13), 'Credit Suisse 恐慌'),
    (date(2023, 5, 2),  'First Republic 倒閉'),
    (date(2023, 8, 2),  'Fitch 降評美國'),
    (date(2024, 4, 12), '中東 + 通膨擔憂'),
    (date(2024, 8, 2),  'BoJ 升息 carry unwind'),
    (date(2024, 8, 5),  '日股 -12.4pct 全球股災'),
    (date(2024, 9, 4),  'AI 股 sell-off'),
    (date(2024, 11, 1), '美選前不確定'),
    (date(2024, 11, 5), '美大選日'),
    (date(2024, 12, 18), 'Fed hawkish dot plot'),
    (date(2025, 1, 27), 'DeepSeek AI 股大跌'),
    (date(2025, 2, 3),  'Trump 加墨關稅'),
    (date(2025, 3, 4),  'Trump 中國關稅升級'),
    (date(2025, 4, 2),  'Trump Liberation Day'),
    (date(2025, 4, 7),  '關稅恐慌延續'),
    (date(2026, 4, 2),  'Trump 關稅再起'),
]

# For each event, check if trade exists in [event-1, event+2] window
def find_trade_near(target_d, window_before=1, window_after=3):
    found = []
    for offset in range(-window_before, window_after+1):
        d = target_d + timedelta(days=offset)
        if d in trade_dates:
            for t in trade_dates[d]:
                found.append((offset, t))
    return found

print()
print('=' * 100)
print('PART 1: KNOWN MACRO EVENTS COVERAGE')
print('=' * 100)
hit_events = []
miss_events = []
for ed, name in macro_events:
    found = find_trade_near(ed)
    if found:
        total_pnl = sum(t['pnl'] for _, t in found)
        wins = sum(1 for _, t in found if t['pnl'] > 0)
        hit_events.append((ed, name, found, total_pnl, wins))
    else:
        miss_events.append((ed, name))

print(f'\n[CAUGHT] {len(hit_events)} events with trades nearby:')
print(f'{"Date":<12} {"N":>3} {"PnL":>10} {"WR":>5}  Event')
print('-' * 100)
for ed, name, found, total, wins in hit_events:
    wr = wins/len(found)*100 if found else 0
    print(f'{str(ed):<12} {len(found):>3} {total:>+10,.0f} {wr:>4.0f}%  {name}')

print()
print(f'[MISSED] {len(miss_events)} events with NO trades nearby:')
print(f'{"Date":<12}  Event')
print('-' * 100)
for ed, name in miss_events:
    # Check TWII return that day
    twii_r = next((r for d, r, _ in twii_ret if d == ed), None)
    r_str = f'(TWII {twii_r:+.2f}%)' if twii_r else ''
    print(f'{str(ed):<12}  {name}  {r_str}')

# PART 2: All TWII down extreme days (-2% threshold)
print()
print('=' * 100)
print(f'PART 2: ALL TWII DOWN EXTREME DAYS (return <= -2pct, {len(down_extreme)} total)')
print('=' * 100)
caught_2pct = []
missed_2pct = []
for ed, r, p in down_extreme:
    found = find_trade_near(ed)
    if found:
        caught_2pct.append((ed, r, p, found))
    else:
        missed_2pct.append((ed, r, p))

print(f'\n[CAUGHT] {len(caught_2pct)}/{len(down_extreme)} = {len(caught_2pct)/len(down_extreme)*100:.1f}% catch rate')

# Sort missed by severity (most negative first)
missed_2pct.sort(key=lambda x: x[1])
print(f'\n[MISSED] {len(missed_2pct)} extreme down days NOT caught (sorted by severity):')
print(f'{"Date":<12} {"TWII %":>8}  Index')
print('-' * 60)
for ed, r, p in missed_2pct[:30]:  # top 30 worst missed
    print(f'{str(ed):<12} {r:>+8.2f}%  {p:>8,.0f}')

# PART 3: Big losses analysis
print()
print('=' * 100)
print('PART 3: BIGGEST LOSERS - did they catch valid events or noise?')
print('=' * 100)
print(f'{"Date":<12} {"PnL":>10} {"ExitSig":<22}  Same day TWII return')
print('-' * 80)
worst = sorted(trades, key=lambda t: t['pnl'])[:15]
for t in worst:
    twii_r = next((r for d, r, _ in twii_ret if d == t['entry_d']), None)
    r_str = f'TWII {twii_r:+.2f}%' if twii_r else 'TWII data missing'
    judgement = ''
    if twii_r is not None:
        if twii_r > 0.5:
            judgement = '<- entry on UP day (false squeeze signal)'
        elif twii_r > -0.5:
            judgement = '<- entry on FLAT day (noise)'
        else:
            judgement = '<- entry on DOWN day (real signal but failed)'
    print(f'{str(t["entry_d"]):<12} {t["pnl"]:>+10,.0f} {t["exit_sig"]:<22}  {r_str}  {judgement}')
