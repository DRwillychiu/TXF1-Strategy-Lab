"""
S5 SPX_Overnight_DayOpen — Pre-verification (apply L14-L18 from S4 KILL)

Hypothesis: TWII day-session price reacts in-line with SPX overnight move.
If SPX overnight return > |0.7%|, enter TXF1 day-session in same direction.

Pre-verification before W1 spec (S4 lessons applied):
  L14: 28-year validation (1997-2026)
  L15: Cross-period must extend outside backtest window (we have 28y)
  L16: Cross-asset (NOT textbook calendar) — lower decay risk
  L17: Read literature carefully — SPX-TWII overnight spillover well documented
  L18: Recent-bias check — recent/long Sharpe ratio < 2.5x

Mechanism: TWII opens at 09:00 TW = 21:00 NY previous day (US still open),
  so TWII open price reflects ~5h of US trading. SPX overnight (yesterday
  close → today open NY) is mostly absorbed. So we use SPX prev-day close →
  today close as "overnight return" relative to TWII open.

Test: For each TWII day, simulate entering at open IF SPX yesterday's
  full-day return (close[d-1] → close[d-2]) exceeds threshold.
"""
import csv
import io
import sys
from datetime import date, timedelta
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- Fetch SPX + TWII ----------
print('Fetching ^GSPC + ^TWII 1997-2026 via yfinance...')
import yfinance as yf

spx_df = yf.download('^GSPC', start='1997-01-01', end='2026-06-21',
                      progress=False, auto_adjust=False)
spx_data = {}
for idx, row in spx_df.iterrows():
    try:
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        spx_data[idx.date()] = c
    except (ValueError, TypeError):
        continue
print(f'  SPX: {len(spx_data)} days, {min(spx_data)} → {max(spx_data)}')

twii_df = yf.download('^TWII', start='1997-01-01', end='2026-06-21',
                       progress=False, auto_adjust=False)
twii_data = []
for idx, row in twii_df.iterrows():
    try:
        o = float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open'])
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        h = float(row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High'])
        l = float(row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low'])
        twii_data.append((idx.date(), o, h, l, c))
    except (ValueError, TypeError):
        continue
print(f'  TWII: {len(twii_data)} days, {twii_data[0][0]} → {twii_data[-1][0]}')

# ---------- Compute SPX prev-day return (using close-to-close) ----------
spx_dates_sorted = sorted(spx_data.keys())
spx_ret = {}  # date d → (close[d] - close[d-1]) / close[d-1]
for i in range(1, len(spx_dates_sorted)):
    d = spx_dates_sorted[i]
    d_prev = spx_dates_sorted[i - 1]
    spx_ret[d] = (spx_data[d] - spx_data[d_prev]) / spx_data[d_prev]

# ---------- Lookup: for each TWII day, find SPX prev-trading-day return ----------
def latest_spx_before(target_d):
    """Get most recent SPX close date strictly before target_d."""
    candidates = [d for d in spx_dates_sorted if d < target_d]
    if not candidates:
        return None
    return candidates[-1]

# Build trade list
THRESHOLD_PCT = 0.7  # |SPX overnight return| > 0.7%

trades = []  # (twii_date, direction, twii_open_to_close_ret, spx_signal_ret)
for d, o, h, l, c in twii_data:
    spx_signal_d = latest_spx_before(d)
    if spx_signal_d is None or spx_signal_d not in spx_ret:
        continue
    sig_ret = spx_ret[spx_signal_d]
    if abs(sig_ret) * 100 < THRESHOLD_PCT:
        continue
    # TWII day return: open to close
    twii_day_ret = (c - o) / o if o > 0 else 0
    # Direction: long if SPX up, short if SPX down
    direction = 'long' if sig_ret > 0 else 'short'
    # Trade pnl: if long, day return positive = win; if short, day return negative = win
    trade_pnl = twii_day_ret if direction == 'long' else -twii_day_ret
    trades.append((d, direction, trade_pnl, sig_ret, twii_day_ret))

print(f'\nWith |SPX overnight| > {THRESHOLD_PCT}%: {len(trades)} trade days '
      f'({len(trades) / 28.4:.1f}/year)')

# ---------- Q1: Direction breakdown + WR/PF ----------
print()
print('=' * 80)
print('Q1: Direction breakdown + overall stats')
print('=' * 80)
longs = [(d, p, s, t) for d, dr, p, s, t in trades if dr == 'long']
shorts = [(d, p, s, t) for d, dr, p, s, t in trades if dr == 'short']
print(f'  Long signals (SPX up >{THRESHOLD_PCT}%): {len(longs)}')
print(f'  Short signals (SPX down >{THRESHOLD_PCT}%): {len(shorts)}')

for label, samples in [('LONGS', longs), ('SHORTS', shorts), ('ALL', [(d, p, s, t) for d, _, p, s, t in trades])]:
    rets = [p for _, p, _, _ in samples]
    if not rets:
        continue
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    yrs = 28.4
    tpy = n / yrs
    annual = tpy * m / 100
    avol = sd * (tpy ** 0.5)
    sharpe = annual / avol if avol > 0 else 0
    print(f'  {label:<8} N={n:<4} Mean%={m:>7.3f} WR%={wr:>5.1f} PF={pf:.3f} Cum%={cum:>+7.2f}% Sharpe={sharpe:.3f}')

# ---------- Q2: 6 regime split (apply L14) ----------
print()
print('=' * 80)
print('Q2: 6 macro regimes (apply S4 lesson L14)')
print('=' * 80)
regimes = [
    ('1997-2002 Dot-com', date(1997, 1, 1), date(2002, 12, 31)),
    ('2003-2007 China bull', date(2003, 1, 1), date(2007, 12, 31)),
    ('2008-2009 GFC', date(2008, 1, 1), date(2009, 12, 31)),
    ('2010-2014 Post-GFC', date(2010, 1, 1), date(2014, 12, 31)),
    ('2015-2019 Sideways', date(2015, 1, 1), date(2019, 12, 31)),
    ('2020-2026 COVID+AI', date(2020, 1, 1), date(2026, 12, 31)),
]
print(f'{"Regime":<30} {"N":>4} {"Mean%":>7} {"WR%":>5} {"PF":>5} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 80)
regime_results = []
for name, d_start, d_end in regimes:
    sub = [(d, dr, p, s, t) for d, dr, p, s, t in trades if d_start <= d <= d_end]
    if not sub:
        continue
    rets = [p for _, _, p, _, _ in sub]
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    yrs = (d_end - d_start).days / 365.25
    tpy = n / yrs
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    regime_results.append((name, n, m, wr, pf, cum, sharpe))
    print(f'{name:<30} {n:>4} {m:>7.3f} {wr:>5.1f} {pf:>5.2f} {cum:>+7.2f}% {sharpe:>7.3f}')

# ---------- Q3: Recent-bias check (L18 mandatory gate) ----------
print()
print('=' * 80)
print('Q3: Recent-bias check (L18 mandatory)')
print('=' * 80)

all_rets = [p for _, _, p, _, _ in trades]
recent_rets = [p for d, _, p, _, _ in trades if d >= date(2020, 1, 1)]

def quick_stats(rets, yrs):
    n = len(rets)
    if n == 0:
        return None
    m = mean(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    tpy = n / yrs
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    return sharpe

s_all = quick_stats(all_rets, 28.4)
s_recent = quick_stats(recent_rets, 6.4)
print(f'  28-year Sharpe: {s_all:.3f}')
print(f'  Recent 6.4y Sharpe: {s_recent:.3f}')
ratio = s_recent / s_all if s_all > 0 else float('inf')
print(f'  Ratio recent/long: {ratio:.2f}x')
if ratio > 2.5:
    print(f'  ❌ L18 AUTO-KILL: ratio > 2.5x indicates over-fit to recent regime')
elif ratio > 1.5:
    print(f'  ⚠️ L18 WARNING: ratio > 1.5x, possible recent bias')
elif 0.5 < ratio < 1.5:
    print(f'  ✅ L18 PASS: ratio within 0.5-1.5x = robust across periods')
else:
    print(f'  ⚠️ L18 WARNING: ratio < 0.5x, alpha may be decaying')

# ---------- Q4: Threshold sensitivity ----------
print()
print('=' * 80)
print('Q4: Threshold sensitivity — what is optimal |SPX| filter?')
print('=' * 80)
print(f'{"Threshold":>10} {"N":>4} {"trades/yr":>10} {"WR%":>5} {"PF":>5} {"Sharpe":>7} {"Cum%":>8}')
print('-' * 60)
for thr in [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]:
    sub_trades = []
    for d, o, h, l, c in twii_data:
        spx_signal_d = latest_spx_before(d)
        if spx_signal_d is None or spx_signal_d not in spx_ret:
            continue
        sig_ret = spx_ret[spx_signal_d]
        if abs(sig_ret) * 100 < thr:
            continue
        twii_day_ret = (c - o) / o if o > 0 else 0
        direction = 'long' if sig_ret > 0 else 'short'
        trade_pnl = twii_day_ret if direction == 'long' else -twii_day_ret
        sub_trades.append(trade_pnl)
    n = len(sub_trades)
    if n == 0:
        continue
    m = mean(sub_trades) * 100
    wr = sum(1 for r in sub_trades if r > 0) / n * 100
    wins = [r for r in sub_trades if r > 0]
    losses = [r for r in sub_trades if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(sub_trades) * 100
    sd = stdev(sub_trades) if n > 1 else 0
    tpy = n / 28.4
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    print(f'{thr:>8.1f}% {n:>4} {tpy:>10.1f} {wr:>5.1f} {pf:>5.2f} {sharpe:>7.3f} {cum:>+7.2f}%')

# ---------- VERDICT ----------
print()
print('=' * 80)
print('PRE-VERIFICATION VERDICT (apply L14-L18 institutional gates)')
print('=' * 80)
all_n = len(all_rets)
all_wr = sum(1 for r in all_rets if r > 0) / all_n * 100 if all_n > 0 else 0
all_pf_wins = [r for r in all_rets if r > 0]
all_pf_losses = [r for r in all_rets if r <= 0]
all_pf = (sum(all_pf_wins) / abs(sum(all_pf_losses))) if all_pf_losses and sum(all_pf_losses) != 0 else 99

regime_pass = sum(1 for _, _, _, _, _, _, sh in regime_results if sh > 0.3)
print(f'  28-year Sharpe > 0.4:     {"PASS" if s_all > 0.4 else "FAIL"}  ({s_all:.3f})')
print(f'  28-year PF > 1.3:         {"PASS" if all_pf > 1.3 else "FAIL"}  ({all_pf:.3f})')
print(f'  L18 recent-bias < 2.5x:   {"PASS" if ratio < 2.5 else "FAIL"}  ({ratio:.2f}x)')
print(f'  ≥4/6 regimes Sharpe>0.3:  {"PASS" if regime_pass >= 4 else "FAIL"}  ({regime_pass}/6)')
print()
all_pass = s_all > 0.4 and all_pf > 1.3 and ratio < 2.5 and regime_pass >= 4
if all_pass:
    print('  ✅ ALL GATES PASS → GO for W1 spec')
else:
    print('  ❌ GATE(S) FAIL → KILL or REDESIGN before W1')
