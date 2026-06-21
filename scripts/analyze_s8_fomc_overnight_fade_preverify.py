"""
S8 FOMC_OvernightFade — Pre-verification (apply STRATEGY_RD_SOP_v2 gates)

Strategy hypothesis (from roadmap §9.3 #6):
  FOMC announcements cause large SPX overnight moves.
  TWII often over-reacts at open → fade the overnight move.

Spec idea:
  Entry: At TXF1 day-session open, if SPX overnight return > |THRESHOLD|
         enter TXF1 OPPOSITE direction (fade)
    - SPX up >|1.5%| → TXF1 short (fade overnight optimism)
    - SPX down >|1.5%| → TXF1 long (fade overnight panic)
  Exit: 1×ATR target / 1×ATR stop / force-flat 12:00

Proxy: We don't have exact FOMC dates 1997-2026. Use HIGH-VOLATILITY
  proxy: |SPX overnight return| > THRESHOLD captures FOMC days + other
  high-impact events (NFP, ECB, geopolitical). This is broader but
  directionally same alpha hypothesis.

Pre-W0 Gate 1 (MC12 execution): ✓ PASS (SPX via yfinance + CSV ASCII feed,
                                        already proven via S5 architecture)
Pre-W0 Gate 2 (Operational): ✓ PASS (same as S5)

W0 Alpha Pre-verification (4 gates):
  Gate A: 28-year Sharpe > 0.4 + PF > 1.3
  Gate B: ≥4/6 regimes Sharpe > 0.3
  Gate C: L18 recent-bias < 2.5x
  Gate D: Direction symmetry (L20) — check both long-side and short-side
"""
import csv
import io
import sys
from datetime import date, timedelta
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ---------- Fetch SPX + TWII ----------
print('Fetching ^GSPC + ^TWII 1997-2026...')
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

twii_df = yf.download('^TWII', start='1997-01-01', end='2026-06-21',
                       progress=False, auto_adjust=False)
twii_data = []
for idx, row in twii_df.iterrows():
    try:
        o = float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open'])
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        twii_data.append((idx.date(), o, c))
    except (ValueError, TypeError):
        continue
print(f'  SPX: {len(spx_data)} days, TWII: {len(twii_data)} days')

# ---------- SPX overnight return ----------
spx_dates_sorted = sorted(spx_data.keys())
spx_ret = {}
for i in range(1, len(spx_dates_sorted)):
    d = spx_dates_sorted[i]
    d_prev = spx_dates_sorted[i - 1]
    spx_ret[d] = (spx_data[d] - spx_data[d_prev]) / spx_data[d_prev]

def latest_spx_before(target_d):
    candidates = [d for d in spx_dates_sorted if d < target_d]
    return candidates[-1] if candidates else None

# ---------- Test multiple thresholds (fade direction) ----------
def run_fade_strategy(threshold_pct):
    """Returns list of (date, direction, fade_pnl, sig_ret)"""
    trades = []
    for d, o, c in twii_data:
        spx_signal_d = latest_spx_before(d)
        if spx_signal_d is None or spx_signal_d not in spx_ret:
            continue
        sig_ret = spx_ret[spx_signal_d]
        if abs(sig_ret) * 100 < threshold_pct:
            continue
        # FADE direction: opposite of SPX move
        # SPX up → short TXF1; SPX down → long TXF1
        twii_day_ret = (c - o) / o if o > 0 else 0
        fade_direction = 'short' if sig_ret > 0 else 'long'
        # If fade=short, profit when TWII goes down (negative day ret)
        # If fade=long, profit when TWII goes up (positive day ret)
        fade_pnl = -twii_day_ret if fade_direction == 'short' else twii_day_ret
        trades.append((d, fade_direction, fade_pnl, sig_ret))
    return trades

def stats(rets, years):
    if not rets:
        return None
    n = len(rets)
    m = mean(rets) * 100
    wr = sum(1 for r in rets if r > 0) / n * 100
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 99
    cum = sum(rets) * 100
    sd = stdev(rets) if n > 1 else 0
    tpy = n / years
    sharpe = (tpy * m / 100) / (sd * (tpy ** 0.5)) if sd > 0 else 0
    return {'n': n, 'mean_pct': m, 'wr': wr, 'pf': pf, 'cum': cum, 'sharpe': sharpe, 'tpy': tpy}

# ---------- Q1: Threshold sensitivity ----------
print()
print('=' * 80)
print('Q1: Threshold sensitivity (fade direction)')
print('=' * 80)
print(f'{"Threshold":>9} {"N":>5} {"tpy":>5} {"Mean%":>7} {"WR%":>5} {"PF":>6} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 70)
best_thr = None
best_sharpe = -99
for thr in [0.7, 1.0, 1.3, 1.5, 2.0, 2.5, 3.0]:
    trades = run_fade_strategy(thr)
    rets = [t[2] for t in trades]
    s = stats(rets, 28.4)
    if s is None:
        continue
    print(f'{thr:>8.1f}% {s["n"]:>5} {s["tpy"]:>5.1f} {s["mean_pct"]:>7.3f} {s["wr"]:>5.1f} {s["pf"]:>6.3f} {s["cum"]:>+7.2f}% {s["sharpe"]:>7.3f}')
    if s['sharpe'] > best_sharpe:
        best_sharpe = s['sharpe']
        best_thr = thr

print(f'\nBest threshold: {best_thr}% (Sharpe {best_sharpe:.3f})')

# ---------- Use best threshold for deeper analysis ----------
best_trades = run_fade_strategy(best_thr)
print(f'\nUsing best threshold {best_thr}% for SOP v2 4 gates analysis:')

# ---------- Q2: Direction symmetry (L20 Gate D) ----------
print()
print('=' * 80)
print(f'Q2: Direction symmetry (Gate D, L20) — threshold |{best_thr}%|')
print('=' * 80)
longs = [t[2] for t in best_trades if t[1] == 'long']
shorts = [t[2] for t in best_trades if t[1] == 'short']
print(f'  Fade-long  (SPX down → TWII long):  N={len(longs)}')
print(f'  Fade-short (SPX up → TWII short):   N={len(shorts)}')

s_long = stats(longs, 28.4)
s_short = stats(shorts, 28.4)
s_all = stats([t[2] for t in best_trades], 28.4)
for label, sd in [('LONGS (fade panic)', s_long), ('SHORTS (fade FOMO)', s_short), ('ALL', s_all)]:
    if sd:
        print(f'  {label:<22} Mean%={sd["mean_pct"]:>7.3f} WR%={sd["wr"]:>5.1f} PF={sd["pf"]:.3f} Sharpe={sd["sharpe"]:.3f}')

if s_long and s_short:
    asymmetry = abs(s_long['sharpe'] - s_short['sharpe'])
    print(f'\n  Direction asymmetry (|long_sharpe - short_sharpe|): {asymmetry:.3f}')
    if s_long['sharpe'] > 0.3 and s_short['sharpe'] > 0.3:
        print('  ✅ Gate D PASS: both directions > 0.3')
    elif s_long['sharpe'] > 0.3 or s_short['sharpe'] > 0.3:
        print('  ⚠️ Gate D PARTIAL: only one direction works → asymmetric')
    else:
        print('  ❌ Gate D FAIL: both directions weak')

# ---------- Q3: 6 macro regime split (Gate B) ----------
print()
print('=' * 80)
print('Q3: 6 macro regimes (Gate B: L14 ≥4/6 Sharpe > 0.3)')
print('=' * 80)
regimes = [
    ('1997-2002 Dot-com', date(1997, 1, 1), date(2002, 12, 31)),
    ('2003-2007 China bull', date(2003, 1, 1), date(2007, 12, 31)),
    ('2008-2009 GFC', date(2008, 1, 1), date(2009, 12, 31)),
    ('2010-2014 Post-GFC', date(2010, 1, 1), date(2014, 12, 31)),
    ('2015-2019 Sideways', date(2015, 1, 1), date(2019, 12, 31)),
    ('2020-2026 COVID+AI', date(2020, 1, 1), date(2026, 12, 31)),
]
print(f'{"Regime":<30} {"N":>4} {"Mean%":>7} {"WR%":>5} {"PF":>5} {"Sharpe":>7}')
print('-' * 70)
regime_results = []
for name, d_start, d_end in regimes:
    sub_rets = [t[2] for t in best_trades if d_start <= t[0] <= d_end]
    if not sub_rets:
        continue
    yrs = (d_end - d_start).days / 365.25
    sd = stats(sub_rets, yrs)
    regime_results.append((name, sd['n'], sd['mean_pct'], sd['wr'], sd['pf'], sd['sharpe']))
    print(f'{name:<30} {sd["n"]:>4} {sd["mean_pct"]:>7.3f} {sd["wr"]:>5.1f} {sd["pf"]:>5.2f} {sd["sharpe"]:>7.3f}')

# ---------- Q4: L18 recent-bias check (Gate C) ----------
print()
print('=' * 80)
print('Q4: Recent-bias check (Gate C: L18 mandatory)')
print('=' * 80)
recent_rets = [t[2] for t in best_trades if t[0] >= date(2020, 1, 1)]
s_recent = stats(recent_rets, 6.4)
print(f'  28-year Sharpe: {s_all["sharpe"]:.3f}')
print(f'  Recent 6.4y Sharpe: {s_recent["sharpe"] if s_recent else "N/A"}')
if s_all['sharpe'] > 0 and s_recent:
    ratio = s_recent['sharpe'] / s_all['sharpe']
    print(f'  Ratio recent/long: {ratio:.2f}x')
    if ratio > 2.5:
        print('  ❌ L18 AUTO-KILL: ratio > 2.5x')
    elif 0.4 <= ratio <= 2.5:
        print('  ✅ L18 PASS')
    else:
        print('  ⚠️ L18 WARNING')
else:
    print('  ❌ 28y Sharpe negative or recent N/A → AUTO-KILL')

# ---------- VERDICT ----------
print()
print('=' * 80)
print('SOP v2 VERDICT — 4 gates')
print('=' * 80)
gate_a_sharpe = s_all['sharpe'] > 0.4
gate_a_pf = s_all['pf'] > 1.3
regime_pass = sum(1 for _, _, _, _, _, sh in regime_results if sh > 0.3)
gate_b = regime_pass >= 4
gate_c_ratio = (s_all['sharpe'] > 0 and s_recent
                 and 0.4 <= s_recent['sharpe'] / s_all['sharpe'] <= 2.5)
gate_d = (s_long and s_short
           and s_long['sharpe'] > 0.3 and s_short['sharpe'] > 0.3)

print(f'  Gate A 28y Sharpe > 0.4:        {"PASS" if gate_a_sharpe else "FAIL"}  ({s_all["sharpe"]:.3f})')
print(f'  Gate A 28y PF > 1.3:            {"PASS" if gate_a_pf else "FAIL"}  ({s_all["pf"]:.3f})')
print(f'  Gate B ≥4/6 regimes Sharpe>0.3: {"PASS" if gate_b else "FAIL"}  ({regime_pass}/6)')
print(f'  Gate C L18 ratio in [0.4, 2.5]: {"PASS" if gate_c_ratio else "FAIL"}')
print(f'  Gate D both directions > 0.3:   {"PASS" if gate_d else "FAIL"}')
print()
all_pass = gate_a_sharpe and gate_a_pf and gate_b and gate_c_ratio and gate_d
if all_pass:
    print('  ✅ ALL 5 GATES PASS → GO for W1 spec')
else:
    failed = []
    if not gate_a_sharpe: failed.append('A-Sharpe')
    if not gate_a_pf: failed.append('A-PF')
    if not gate_b: failed.append(f'B-regime({regime_pass}/6)')
    if not gate_c_ratio: failed.append('C-L18')
    if not gate_d: failed.append('D-direction')
    print(f'  ❌ GATE(S) FAIL ({", ".join(failed)}) → KILL S8')
