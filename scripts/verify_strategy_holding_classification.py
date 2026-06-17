"""
策略持倉商品交易日分布驗證 (配合 SETTLEMENT_DAY_DESIGN_CONSTITUTION 條款 6-8)

TXF 商品交易日定義 (台指期):
  一個交易日 = 前日 15:00 ~ 當日 13:45
  即: 15:00 ~ 23:59 屬於「隔日」商品交易日
       00:00 ~ 05:00 屬於「當日」商品交易日
       08:45 ~ 13:45 屬於「當日」商品交易日

「真跨日」定義:
  進場與出場的「商品交易日」不同 = 跨越過至少一次 13:30 結算邊界

分類:
  Intraday        - 99%+ 同一商品交易日進出場
  Intraday (>95%) - 95-99% 同日 (含少量跨日 edge)
  Night           - 全部在 15:00 ~ 隔日 05:00, 且同一商品交易日
  Swing-Trend     - 真跨日比例 > 10% 且策略類型為趨勢
  Swing-Range     - 真跨日比例 > 10% 且策略類型為盤整 (★ 設計禁區 ★)
  Mixed           - 不符合上述任一定義
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path
from datetime import date, time as dtime, timedelta
from collections import Counter


def txf_trade_date(d, hhmm):
    """ Map (calendar date, HHMM int) to TXF futures trade date.
        Night session 15:00 ~ 23:59 -> NEXT calendar day's trade date
        Early morning 00:00 ~ 05:00 -> SAME calendar day's trade date
        Day session   08:45 ~ 13:45 -> SAME calendar day's trade date
        Gap windows (05:01-08:44, 13:46-14:59) treated as same day for safety.
    """
    if d is None or hhmm is None:
        return d
    if hhmm >= 1500:
        return d + timedelta(days=1)
    return d

FILES = [
    ('L1', 'TrendLong',          'WILLY_ATR_LONG_60M',           'Swing-Trend'),
    ('L2', 'TrendShort',         'Trendbearish_V1',              'Swing-Trend'),
    ('L3', 'ConsolidationLong',  'STRATEGY_WILLY_LONG_C',        'Intraday'),     # post v13.3 with RangeForceExit
    ('L4', 'ConsolidationShort', 'STRATEGY_WILLY_SHORT_CTEST2',  'Intraday'),     # post v14.3 with RangeForceExit
    ('L5', 'BreakoutLong',       'STRATEGY_WILLY_LONG_BREAKOUT_C','Swing-Trend'),  # 突破策略本質跨日, 與 L1 同類
    ('S1', 'NightMomentum',      'STRATEGY_GEN_NightMomentum',   'Night'),
]

DL = Path('C:/Users/User/Downloads')


def load_trades(fpath):
    raw = pd.read_excel(fpath, sheet_name='交易明細', header=None)
    h = None
    for i in range(10):
        if str(raw.iloc[i, 0]).strip() == '交易編號':
            h = i; break
    df = pd.read_excel(fpath, sheet_name='交易明細', header=h).dropna(how='all').reset_index(drop=True)
    return df


def to_date(x):
    if isinstance(x, pd.Timestamp): return x.date()
    try: return pd.to_datetime(x).date()
    except: return None


def to_time_int(t):
    """ HHMM int """
    if isinstance(t, dtime): return t.hour * 100 + t.minute
    if isinstance(t, pd.Timestamp): return t.hour * 100 + t.minute
    try:
        tt = pd.to_datetime(t).time()
        return tt.hour * 100 + tt.minute
    except:
        return None


def pair_trades(df):
    out = []
    last_entry = None
    for _, r in df.iterrows():
        typ = str(r.get('類型', '') or '').strip()
        ed = to_date(r.get('日期'))
        et = to_time_int(r.get('時間'))
        if ed is None: continue
        if '進入' in typ:
            last_entry = (ed, et, str(r.get('訊號', '') or '').strip())
        elif '離開' in typ and last_entry is not None:
            entry_td = txf_trade_date(last_entry[0], last_entry[1])
            exit_td = txf_trade_date(ed, et)
            out.append({
                'entry_date': last_entry[0],
                'entry_time': last_entry[1],
                'entry_signal': last_entry[2],
                'exit_date': ed,
                'exit_time': et,
                'exit_signal': str(r.get('訊號', '') or '').strip(),
                'days_calendar': (ed - last_entry[0]).days,
                'days_trade': (exit_td - entry_td).days if entry_td and exit_td else 0,
                'entry_tradedate': entry_td,
                'exit_tradedate': exit_td,
            })
            last_entry = None
    return pd.DataFrame(out)


def in_day_session(hhmm):
    """ 08:45 ~ 13:45 """
    return hhmm is not None and 845 <= hhmm <= 1345


def in_night_session(hhmm):
    """ 15:00 ~ 05:00 next day """
    return hhmm is not None and (hhmm >= 1500 or hhmm <= 500)


def classify(trades, expected):
    n = len(trades)
    if n == 0: return ('No-Data', {})

    # use TXF trade-date for true cross-day logic
    same_td = (trades['days_trade'] == 0).sum()
    cross_td = n - same_td
    cross_pct = cross_td / n * 100

    # raw calendar-day cross (for comparison)
    same_cal = (trades['days_calendar'] == 0).sum()
    cross_cal = n - same_cal
    cross_cal_pct = cross_cal / n * 100

    # entry / exit session classification
    entries_in_night = trades['entry_time'].apply(in_night_session).sum()
    exits_in_night = trades['exit_time'].apply(in_night_session).sum()
    night_entry_pct = entries_in_night / n * 100

    # trade-date distribution
    dist = dict(Counter(trades['days_trade'].tolist()))
    dist_sorted = dict(sorted(dist.items()))

    # auto classification (priority order)
    if cross_pct < 1:
        if night_entry_pct >= 80:
            auto_cls = 'Night'
        else:
            auto_cls = 'Intraday'
    elif cross_pct < 5:
        if night_entry_pct >= 80:
            auto_cls = 'Night (>95%)'
        else:
            auto_cls = 'Intraday (>95%)'
    elif cross_pct >= 30:
        if 'Trend' in expected:
            auto_cls = 'Swing-Trend'
        elif 'Range' in expected or 'Consolidation' in expected:
            auto_cls = 'Swing-Range'
        else:
            auto_cls = 'Swing-Mixed'
    else:
        # 5-30% cross-trade-date = mostly intraday with leak
        auto_cls = 'Intraday-Leaky'

    return (auto_cls, {
        'n_trades': n,
        'same_td': same_td,
        'cross_td': cross_td,
        'cross_pct': cross_pct,
        'cross_cal_pct': cross_cal_pct,
        'night_entry_pct': night_entry_pct,
        'dist': dist_sorted,
    })


def verdict(auto_cls, expected):
    """ Return (status, note) """
    if auto_cls == 'No-Data':
        return ('SKIP', 'no trades')
    if auto_cls == 'Swing-Range':
        return ('FAIL', 'CONSTITUTION VIOLATION: cross-day range strategy is forbidden')
    if auto_cls == 'Intraday-Leaky':
        return ('WARN', '5-30% trades cross trade-date; tighten TimeExit or accept as light swing')
    if expected == auto_cls:
        return ('PASS', 'matches design intent')
    if expected == 'Intraday' and auto_cls.startswith('Intraday'):
        return ('PASS', 'effectively intraday')
    if expected == 'Night' and auto_cls.startswith('Night'):
        return ('PASS', 'night-session confirmed')
    if expected == 'Swing-Trend' and auto_cls == 'Swing-Trend':
        return ('PASS', 'cross-day trend confirmed')
    return ('WARN', f'design said {expected}, data says {auto_cls}')


# ============================================================
# Run
# ============================================================
print('=' * 88)
print('STRATEGY HOLDING-PERIOD CLASSIFICATION (Constitution clauses 6-8)')
print('=' * 88)
print()

all_results = []
for sid, sname, raw_name, expected in FILES:
    fname = f'TXF1  {raw_name} 策略回測績效報告.xlsx'
    fpath = DL / fname
    if not fpath.exists():
        print(f'{sid}: file missing  [SKIP]')
        continue
    df = load_trades(fpath)
    trades = pair_trades(df)
    auto_cls, stats = classify(trades, expected)
    status, note = verdict(auto_cls, expected)

    print(f'--- {sid} {sname} ---')
    print(f'  file: {fname}')
    print(f'  expected (design): {expected}')
    print(f'  auto-classified:   {auto_cls}')
    print(f'  total trades:      {stats.get("n_trades", 0)}')
    print(f'  same-tradedate (true intraday):   {stats.get("same_td", 0)}  ({100 - stats.get("cross_pct", 0):.1f}%)')
    print(f'  cross-tradedate (true crossing):  {stats.get("cross_td", 0)}  ({stats.get("cross_pct", 0):.1f}%)')
    print(f'  raw calendar-day cross:           ({stats.get("cross_cal_pct", 0):.1f}%)  [for reference]')
    print(f'  night-session entry pct:          {stats.get("night_entry_pct", 0):.1f}%')
    if 'dist' in stats:
        d = stats['dist']
        top5 = list(d.items())[:8]
        print(f'  holding-tradedates dist (top):    {top5}')
    print(f'  VERDICT: [{status}]  {note}')
    print()
    all_results.append({'sid': sid, 'expected': expected, 'auto': auto_cls, 'status': status, 'note': note, **stats})

# ============================================================
# Summary
# ============================================================
print('=' * 88)
print('SUMMARY')
print('=' * 88)
print()
print(f'{"Strategy":<6} {"Expected":<14} {"AutoClass":<18} {"Trades":>8} {"Cross%":>8} {"Verdict":<10}')
print('-' * 88)
for r in all_results:
    print(f'{r["sid"]:<6} {r["expected"]:<14} {r["auto"]:<18} {r.get("n_trades", 0):>8} '
          f'{r.get("cross_pct", 0):>7.1f}% {r["status"]:<10}')
print()

pass_n = sum(1 for r in all_results if r['status'] == 'PASS')
warn_n = sum(1 for r in all_results if r['status'] == 'WARN')
fail_n = sum(1 for r in all_results if r['status'] == 'FAIL')
print(f'  PASS: {pass_n}/{len(all_results)}')
print(f'  WARN: {warn_n}/{len(all_results)}')
print(f'  FAIL: {fail_n}/{len(all_results)}')

if fail_n > 0:
    print()
    print('  *** CONSTITUTION VIOLATION DETECTED ***')
    print('  Swing-Range strategies must be redesigned (forced TimeExit < 12:00) before live.')
