"""S3_S v1.2 FROZEN Cool=1 - extreme event coverage WITH exit details per event."""
import sys, io
from collections import defaultdict
from datetime import date, timedelta
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r'C:\Users\User\Downloads\TXF1  VolSqueezeShort 策略回測績效報告_COOL1.xlsx'
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
    if sig and 'SE_' in sig:
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        pnl_val = pnl if isinstance(pnl, (int, float)) else 0
        pending = {'entry_d': entry_d, 'entry_t': tm,
                   'pnl': pnl_val, 'entry_sig': sig}
    elif sig and 'SX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append({**pending, 'exit_d': exit_d, 'exit_t': tm, 'exit_sig': sig})
        pending = None
trade_dates = defaultdict(list)
for t in trades:
    trade_dates[t['entry_d']].append(t)

macro_events = [
    (date(2020, 1, 23), 'COVID 武漢封城首日'),
    (date(2020, 2, 27), 'COVID 全球擴散恐慌'),
    (date(2020, 3, 9),  'SPX 第一次熔斷'),
    (date(2020, 3, 12), 'SPX 第二次熔斷 (最大跌)'),
    (date(2020, 3, 16), 'SPX 第三次熔斷'),
    (date(2020, 3, 18), 'SPX 第四次熔斷'),
    (date(2020, 4, 21), '油價負值'),
    (date(2020, 10, 28),'美選前不確定'),
    (date(2021, 1, 27), 'GameStop short squeeze'),
    (date(2021, 3, 5),  '美 bond yield surge'),
    (date(2021, 5, 12), '美通膨 + AI sell-off'),
    (date(2021, 9, 20), '恆大危機'),
    (date(2021, 12, 1), 'Omicron 變種'),
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
    (date(2022, 12, 14),'Fed hawkish dot plot'),
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
    (date(2024, 12, 18),'Fed hawkish dot plot'),
    (date(2025, 1, 27), 'DeepSeek AI 股大跌'),
    (date(2025, 2, 3),  'Trump 加墨關稅'),
    (date(2025, 3, 4),  'Trump 中國關稅升級'),
    (date(2025, 4, 2),  'Trump Liberation Day'),
    (date(2025, 4, 7),  '關稅恐慌延續'),
    (date(2026, 4, 2),  'Trump 關稅再起'),
]

def find_near(target, before=1, after=3):
    found = []
    for off in range(-before, after+1):
        d = target + timedelta(days=off)
        if d in trade_dates:
            for t in trade_dates[d]:
                found.append((off, t))
    return found

# Per-event exit detail
print('Date         Event                              Entry->Exit              Off  PnL         Sig')
print('-' * 120)
for ed, name in macro_events:
    fnd = find_near(ed)
    if not fnd:
        print(f'{ed} {name:<35} [NO TRADE NEAR]')
        continue
    for off, t in fnd:
        line = f'{ed} {name[:33]:<35} {t["entry_d"]}->{t["exit_d"]}  D{off:+d} {t["pnl"]:>+10,.0f}  {t["exit_sig"]}'
        print(line)

# Aggregate exit signal stats for caught events
print()
print('=' * 80)
print('EXIT SIGNAL BREAKDOWN ACROSS ALL CAUGHT MACRO EVENTS')
print('=' * 80)
exit_stats = defaultdict(lambda: {'n':0, 'pnl':0, 'wins':0})
for ed, name in macro_events:
    fnd = find_near(ed)
    for off, t in fnd:
        s = exit_stats[t['exit_sig']]
        s['n'] += 1
        s['pnl'] += t['pnl']
        if t['pnl'] > 0: s['wins'] += 1
print(f'{"Exit Signal":<22} {"N":>4} {"Total PnL":>12} {"WR":>6}  Meaning')
print('-' * 100)
for sig in sorted(exit_stats.keys()):
    s = exit_stats[sig]
    wr = s['wins']/s['n']*100 if s['n'] else 0
    meaning = {
        'SX_VS_TP': 'Layer 4 - 達 ATR x 3.5 停利 (理想出場)',
        'SX_VS_SP': 'Layer 2 - 移動停損鎖利 (峰值 70%)',
        'SX_VS_SL': 'Layer 1 - ATR x 2.75 停損 (進場錯)',
        'SX_VS_Mid': 'Layer 3 - 中軌出場 (論點失效)',
        'SX_VS_TimeStop': 'Layer 5 - 持倉超 35 K (拖太久)',
        'SX_VS_Settlement': 'Layer 0 - 結算日強平',
        'SX_VS_HolFlat': 'Layer 0 - 假日鐵律強平',
        'SX_VS_Kill': 'Layer 0 - 手動緊急停用',
    }.get(sig, '?')
    print(f'  {sig:<20} {s["n"]:>4} {s["pnl"]:>+12,.0f} {wr:>5.0f}%  {meaning}')
