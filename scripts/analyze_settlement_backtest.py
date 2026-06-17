"""
Settlement_Flat 部署後真實回測深度分析

讀 6 隻策略的 MC 回測 xlsx, parse 交易明細, 分析:
  1. 結算日當天的進場數 (應為 0, 因 Entry gate 阻擋)
  2. *_Settlement 標籤的出場次數與 P&L 分布
  3. 結算日 12:30 後 vs 12:30 前的活動對比
  4. Settlement_Flat 模組對整體 PF / 淨利 / MDD 的影響
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path
from datetime import date, time
from collections import defaultdict

FILES = [
    ('L1', 'TrendLong',          'WILLY_ATR_LONG_60M'),
    ('L2', 'TrendShort',         'Trendbearish_V1'),
    ('L3', 'ConsolidationLong',  'STRATEGY_WILLY_LONG_C'),
    ('L4', 'ConsolidationShort', 'STRATEGY_WILLY_SHORT_CTEST2'),
    ('L5', 'BreakoutLong',       'STRATEGY_WILLY_LONG_BREAKOUT_C'),
    ('S1', 'NightMomentum',      'STRATEGY_GEN_NightMomentum'),
]

DL = Path('C:/Users/User/Downloads')


def is_settlement_day(d):
    """3rd Wed of month, per Settlement_Flat detection."""
    if not isinstance(d, (pd.Timestamp, date)):
        return False
    return d.weekday() == 2 and 15 <= d.day <= 21


def load_trades(fpath):
    """MC report format: row 1 = column header, data starts row 2."""
    raw = pd.read_excel(fpath, sheet_name='交易明細', header=None)
    header_row_idx = None
    for i in range(min(10, len(raw))):
        if str(raw.iloc[i, 0]).strip() == '交易編號':
            header_row_idx = i
            break
    if header_row_idx is None:
        raise RuntimeError(f'cannot find header in {fpath.name}')
    df = pd.read_excel(fpath, sheet_name='交易明細', header=header_row_idx)
    df = df.dropna(how='all').reset_index(drop=True)
    return df


def parse_trades(df):
    """Pair entry+exit into trade records. Each trade = 2 consecutive rows.
       entry row has 交易編號, exit row has NaN 交易編號."""
    trades = []
    entry = None
    for _, r in df.iterrows():
        type_str = str(r.get('類型', '') or '').strip()
        date_v = r.get('日期')
        time_v = r.get('時間')
        signal = str(r.get('訊號', '') or '').strip()
        price = r.get('價格')
        pnl = r.get('獲利(¤)')

        if pd.isna(date_v):
            continue

        # convert date
        if isinstance(date_v, pd.Timestamp):
            d = date_v.date()
        else:
            d = pd.to_datetime(date_v).date()

        # convert time
        t = None
        if isinstance(time_v, time):
            t = time_v
        elif isinstance(time_v, pd.Timestamp):
            t = time_v.time()
        elif isinstance(time_v, str):
            try:
                t = pd.to_datetime(time_v).time()
            except Exception:
                pass

        rec = {
            'type': type_str,
            'date': d,
            'time': t,
            'signal': signal,
            'price': price,
            'pnl': pnl,
        }

        if '進入' in type_str or 'Entry' in type_str:
            entry = rec
        elif ('離開' in type_str or 'Exit' in type_str) and entry is not None:
            trades.append({
                'entry_date': entry['date'],
                'entry_time': entry['time'],
                'entry_signal': entry['signal'],
                'entry_price': entry['price'],
                'exit_date': rec['date'],
                'exit_time': rec['time'],
                'exit_signal': rec['signal'],
                'exit_price': rec['price'],
                'pnl': entry['pnl'],
                'side': 'Long' if 'Long' in entry['type'] else 'Short',
            })
            entry = None
    return pd.DataFrame(trades)


def analyze(sid, sname, raw_name):
    fname = f'TXF1  {raw_name} 策略回測績效報告.xlsx'
    fpath = DL / fname
    if not fpath.exists():
        return None

    df = load_trades(fpath)
    trades = parse_trades(df)
    if trades.empty:
        return None

    # Date range
    date_min = trades['entry_date'].min()
    date_max = trades['exit_date'].max()
    n_trades = len(trades)

    # Settlement-day classification
    trades['exit_on_settlement_day'] = trades['exit_date'].apply(is_settlement_day)
    trades['entry_on_settlement_day'] = trades['entry_date'].apply(is_settlement_day)
    trades['settlement_exit'] = trades['exit_signal'].str.contains('Settlement', na=False)

    # Counts
    n_settlement_exits = trades['settlement_exit'].sum()
    n_exits_on_sday = trades['exit_on_settlement_day'].sum()
    n_entries_on_sday = trades['entry_on_settlement_day'].sum()

    # P&L breakdown
    total_pnl = trades['pnl'].sum()
    settlement_trades = trades[trades['settlement_exit']]
    settlement_pnl = settlement_trades['pnl'].sum()
    settlement_wins = (settlement_trades['pnl'] > 0).sum()
    settlement_losses = (settlement_trades['pnl'] < 0).sum()
    settlement_avg = settlement_trades['pnl'].mean() if len(settlement_trades) > 0 else 0

    # Exit time of settlement trades (should be >= 12:30)
    sday_exit_times = settlement_trades['exit_time'].apply(
        lambda t: t.hour * 100 + t.minute if t else None
    ).dropna()

    # Entries on settlement day - should be ALL before today (08:45) since gate blocks
    sday_entries = trades[trades['entry_on_settlement_day']]
    sday_entry_times = sday_entries['entry_time'].apply(
        lambda t: t.hour * 100 + t.minute if t else None
    ).dropna()

    # Overall stats
    wins = (trades['pnl'] > 0).sum()
    losses = (trades['pnl'] < 0).sum()
    wr = wins / n_trades * 100 if n_trades else 0
    gross_profit = trades[trades['pnl'] > 0]['pnl'].sum()
    gross_loss = -trades[trades['pnl'] < 0]['pnl'].sum()
    pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

    # PnL if settlement exits were REMOVED (hypothetical: position held to next exit)
    # Approximation: settlement pnl shows the captured value; we just isolate it
    pnl_without_settlement = total_pnl - settlement_pnl
    pct_pnl_from_settlement = (settlement_pnl / total_pnl * 100) if total_pnl else 0

    return {
        'sid': sid,
        'sname': sname,
        'file': fname,
        'date_min': date_min,
        'date_max': date_max,
        'n_trades': n_trades,
        'total_pnl': total_pnl,
        'wr': wr,
        'pf': pf,
        'n_settlement_exits': n_settlement_exits,
        'n_exits_on_sday': n_exits_on_sday,
        'n_entries_on_sday': n_entries_on_sday,
        'settlement_pnl': settlement_pnl,
        'settlement_wins': settlement_wins,
        'settlement_losses': settlement_losses,
        'settlement_avg': settlement_avg,
        'sday_exit_times': sorted(sday_exit_times.tolist()) if len(sday_exit_times) else [],
        'sday_entry_times': sorted(sday_entry_times.tolist()) if len(sday_entry_times) else [],
        'pnl_without_settlement': pnl_without_settlement,
        'pct_pnl_from_settlement': pct_pnl_from_settlement,
        'settlement_trades_detail': settlement_trades[['entry_date','entry_time','entry_price','exit_date','exit_time','exit_price','exit_signal','pnl','side']].copy(),
    }


# ============================================================
# Run analysis
# ============================================================
print("=" * 90)
print("SETTLEMENT_FLAT 部署後真實回測深度分析")
print("=" * 90)
print()

results = []
for sid, sname, raw_name in FILES:
    print(f"--- {sid} {sname} ---")
    res = analyze(sid, sname, raw_name)
    if res is None:
        print("  no data")
        continue
    results.append(res)
    print(f"  回測區間: {res['date_min']} ~ {res['date_max']}")
    print(f"  總交易筆數: {res['n_trades']}")
    print(f"  總淨利: {res['total_pnl']:,.0f}  WR: {res['wr']:.1f}%  PF: {res['pf']:.2f}")
    print(f"  *_Settlement 出場筆數: {res['n_settlement_exits']}")
    print(f"  結算日進場筆數: {res['n_entries_on_sday']}")
    print(f"  結算日出場筆數: {res['n_exits_on_sday']}")
    print(f"  Settlement P&L: {res['settlement_pnl']:,.0f}  (佔總 P&L {res['pct_pnl_from_settlement']:.1f}%)")
    print(f"  Settlement 勝/敗: {res['settlement_wins']}/{res['settlement_losses']}  平均: {res['settlement_avg']:,.0f}")
    if res['sday_exit_times']:
        unique_times = sorted(set(res['sday_exit_times']))
        print(f"  結算日出場時段(unique): {unique_times[:10]}")
    if res['sday_entry_times']:
        unique = sorted(set(res['sday_entry_times']))
        print(f"  結算日進場時段(unique): {unique[:10]}")
    print()

# ============================================================
# Cross-strategy summary
# ============================================================
print("=" * 90)
print("六隻策略結算日效果對照")
print("=" * 90)
print()
print(f"{'策略':<5} {'總筆數':>8} {'總淨利':>14} {'結算出場':>10} {'結算P&L':>14} {'佔比':>8} {'結算進場':>10}")
print("-" * 90)
for r in results:
    print(f"{r['sid']:<5} {r['n_trades']:>8} {r['total_pnl']:>14,.0f} {r['n_settlement_exits']:>10} "
          f"{r['settlement_pnl']:>14,.0f} {r['pct_pnl_from_settlement']:>7.1f}% {r['n_entries_on_sday']:>10}")
print()

# ============================================================
# Settlement-day entry gate audit
# ============================================================
print("=" * 90)
print("【關鍵稽核】結算日 Entry Gate 效果驗證")
print("=" * 90)
print()
print("若 Entry gate 正確運作, 結算日進場應為 0 (或全部 < 08:45 夜盤已建倉)")
print()
for r in results:
    if r['n_entries_on_sday'] > 0:
        times = r['sday_entry_times']
        late_entries = [t for t in times if t and t >= 845]  # 08:45+
        early_entries = [t for t in times if t and t < 845]  # before 08:45 (night)
        status = "OK" if not late_entries else "FAIL"
        print(f"  {r['sid']}: 結算日進場 {r['n_entries_on_sday']} 筆 "
              f"(夜盤<08:45: {len(early_entries)}, 日盤≥08:45: {len(late_entries)}) [{status}]")
        if late_entries:
            print(f"      日盤違規時段: {late_entries[:5]}")
    else:
        print(f"  {r['sid']}: 結算日 0 進場 [OK]")
print()

# ============================================================
# Settlement exit time distribution (should be >= 12:30)
# ============================================================
print("=" * 90)
print("【關鍵稽核】Settlement 出場時段分布 (應全部 >= 12:30)")
print("=" * 90)
print()
for r in results:
    if r['n_settlement_exits'] == 0:
        print(f"  {r['sid']}: 0 Settlement 出場 (此策略可能無跨日持倉/已透過原邏輯出場)")
        continue
    times = r['sday_exit_times']
    early = [t for t in times if t and t < 1230]
    on_time = [t for t in times if t and 1230 <= t < 1330]
    late = [t for t in times if t and t >= 1330]
    print(f"  {r['sid']}: Settlement 出場 {len(times)} 筆")
    print(f"      <12:30: {len(early)}  | 12:30~13:30: {len(on_time)}  | >=13:30: {len(late)}")
    if early:
        print(f"      早於 12:30 異常時段: {early[:5]}")
print()

# ============================================================
# Per-strategy Settlement trade detail (first 5 each)
# ============================================================
print("=" * 90)
print("各策略 Settlement 出場交易明細 (前 5 筆)")
print("=" * 90)
for r in results:
    if r['n_settlement_exits'] == 0:
        continue
    print(f"\n--- {r['sid']} {r['sname']} ---")
    detail = r['settlement_trades_detail'].head(5)
    for _, row in detail.iterrows():
        print(f"  Entry: {row['entry_date']} {row['entry_time']} @{row['entry_price']:.0f} "
              f"→ Exit: {row['exit_date']} {row['exit_time']} @{row['exit_price']:.0f} "
              f"[{row['exit_signal']}] P&L: {row['pnl']:,.0f}")
