"""
S9 NightFadeShort — Pre-verification (apply STRATEGY_RD_SOP_v2 gates)

Strategy hypothesis (roadmap §9.4 S9):
  Mirror of S1 NightMomentum, but SHORT direction.
  Night ORB (15:00-16:30 range): if price closes below ORB low after
  US-weak overnight, short on next bar with ATR stop and 05:00 force-flat.
  Goal: anti-correlation hedge to S1 (Long night).

LIMITATION: yfinance has no TXF1 night session intraday data.
  Use PROXY:
    1. SPX overnight return < -X% (US weak)
    2. + TWII day open < TWII prior day's close (TWII opens weak in line with SPX)
    3. Simulate short at open, exit at day close (= proxy for night break-down + ATR stop)

This proxy is DIRECTIONAL but not exact. If proxy shows clear positive Sharpe,
S9 might work in real night session. If proxy negative, S9 directionally
unlikely to work.

Pre-W0 Gate 1 (MC12 execution): ✓ PASS (TXF1 night native + SPX via existing CSV)
Pre-W0 Gate 2 (Operational): ✓ PASS (mirrors S1 architecture)

W0 Alpha Pre-verification: 4 gates
"""
import io
import sys
from datetime import date
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

# SPX overnight return
spx_dates = sorted(spx_data.keys())
spx_ret = {}
for i in range(1, len(spx_dates)):
    spx_ret[spx_dates[i]] = (spx_data[spx_dates[i]] - spx_data[spx_dates[i - 1]]) / spx_data[spx_dates[i - 1]]

def latest_spx_before(target_d):
    for d in reversed(spx_dates):
        if d < target_d:
            return d
    return None

# TWII prior close lookup
twii_by_date = {row[0]: row for row in twii_data}
twii_dates_sorted = [row[0] for row in twii_data]

def prior_twii_close(target_d):
    for d in reversed(twii_dates_sorted):
        if d < target_d:
            return twii_by_date[d][2]  # close
    return None

# ---------- Simulate S9 proxy ----------
# Entry: SPX overnight < -X% AND TWII open < prior close (weak open)
# Direction: Short (mirror of S1 Long-on-strength)
# PnL: short proxy = -(day return) = -(close - open)/open

def simulate(spx_weak_threshold_pct):
    """Returns list of (date, short_pnl, sig_ret, twii_open_to_close)"""
    trades = []
    for d, o, c in twii_data:
        spx_signal_d = latest_spx_before(d)
        if spx_signal_d is None or spx_signal_d not in spx_ret:
            continue
        sig_ret = spx_ret[spx_signal_d]
        # US weak filter
        if sig_ret * 100 > -spx_weak_threshold_pct:
            continue
        # TWII open weak (< prior close)
        prior_c = prior_twii_close(d)
        if prior_c is None or o >= prior_c:
            continue
        # Simulate short
        twii_day_ret = (c - o) / o if o > 0 else 0
        short_pnl = -twii_day_ret  # short profits when day goes down
        trades.append((d, short_pnl, sig_ret, twii_day_ret))
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
print('Q1: SPX weak threshold sensitivity (short direction proxy)')
print('=' * 80)
print(f'{"SPX<":>6} {"N":>5} {"tpy":>5} {"Mean%":>7} {"WR%":>5} {"PF":>6} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 70)
best_thr = None
best_sharpe = -99
for thr in [0.3, 0.5, 0.7, 1.0, 1.3, 1.5, 2.0]:
    trades = simulate(thr)
    rets = [t[1] for t in trades]
    s = stats(rets, 28.4)
    if s is None:
        print(f'{-thr:>5.1f}% NO TRADES')
        continue
    print(f'{-thr:>5.1f}% {s["n"]:>5} {s["tpy"]:>5.1f} {s["mean_pct"]:>7.3f} {s["wr"]:>5.1f} {s["pf"]:>6.3f} {s["cum"]:>+7.2f}% {s["sharpe"]:>7.3f}')
    if s['sharpe'] > best_sharpe:
        best_sharpe = s['sharpe']
        best_thr = thr

print(f'\nBest SPX-weak threshold: {-best_thr:.1f}% (Sharpe {best_sharpe:.3f})')

# ---------- Use best threshold for SOP v2 4 gates ----------
best_trades = simulate(best_thr)

# ---------- Q2: 6 regime split ----------
print()
print('=' * 80)
print(f'Q2: 6 macro regimes (Gate B) — threshold SPX < {-best_thr:.1f}%')
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
    sub_rets = [t[1] for t in best_trades if d_start <= t[0] <= d_end]
    if not sub_rets:
        continue
    yrs = (d_end - d_start).days / 365.25
    sd = stats(sub_rets, yrs)
    regime_results.append((name, sd['n'], sd['mean_pct'], sd['wr'], sd['pf'], sd['sharpe']))
    print(f'{name:<30} {sd["n"]:>4} {sd["mean_pct"]:>7.3f} {sd["wr"]:>5.1f} {sd["pf"]:>5.2f} {sd["sharpe"]:>7.3f}')

# ---------- Q3: Recent-bias check (L18 + L23 sign flip) ----------
print()
print('=' * 80)
print('Q3: Recent-bias + sign-flip check (Gate C: L18 + L23)')
print('=' * 80)
all_rets = [t[1] for t in best_trades]
recent_rets = [t[1] for t in best_trades if t[0] >= date(2020, 1, 1)]
s_all = stats(all_rets, 28.4)
s_recent = stats(recent_rets, 6.4)
print(f'  28-year Sharpe: {s_all["sharpe"]:.3f}')
print(f'  Recent 6.4y Sharpe: {s_recent["sharpe"] if s_recent else "N/A"}')

c_pass = False
if s_recent and s_all['sharpe'] > 0 and s_recent['sharpe'] > 0:
    ratio = s_recent['sharpe'] / s_all['sharpe']
    print(f'  Ratio recent/long: {ratio:.2f}x')
    if ratio < 0:
        print('  ❌ L23 SIGN FLIP AUTO-KILL')
    elif ratio > 2.5:
        print('  ❌ L18 AUTO-KILL: ratio > 2.5x')
    else:
        c_pass = True
        print('  ✅ L18 + L23 PASS')
elif s_all['sharpe'] > 0 and s_recent and s_recent['sharpe'] < 0:
    print(f'  ❌ L23 SIGN FLIP AUTO-KILL: 28y +{s_all["sharpe"]:.3f} → recent {s_recent["sharpe"]:.3f}')
elif s_all['sharpe'] < 0:
    print('  ❌ 28y Sharpe negative → AUTO-KILL')

# ---------- Q4: Correlation with S1 (Gate D extension) ----------
print()
print('=' * 80)
print('Q4: S9 anti-correlation with S1 NightMomentum (roadmap target <0.6)')
print('=' * 80)
print('  NOTE: Cannot compute exactly without S1 actual trade dates from MC12.')
print('  Proxy: S9 fires on US-weak days (SPX < -X%)')
print('         S1 fires on US-strong/normal days (no down filter)')
print('  → By construction, S9 and S1 should fire on different days.')
print('  → Anti-correlation likely PASS by design, but verify in real MC12 test.')

# ---------- VERDICT ----------
print()
print('=' * 80)
print('SOP v2 VERDICT')
print('=' * 80)
gate_a_sharpe = s_all['sharpe'] > 0.4
gate_a_pf = s_all['pf'] > 1.3
regime_pass = sum(1 for _, _, _, _, _, sh in regime_results if sh > 0.3)
gate_b = regime_pass >= 4
gate_c = c_pass

print(f'  Gate A 28y Sharpe > 0.4:        {"PASS" if gate_a_sharpe else "FAIL"}  ({s_all["sharpe"]:.3f})')
print(f'  Gate A 28y PF > 1.3:            {"PASS" if gate_a_pf else "FAIL"}  ({s_all["pf"]:.3f})')
print(f'  Gate B ≥4/6 regimes Sharpe>0.3: {"PASS" if gate_b else "FAIL"}  ({regime_pass}/6)')
print(f'  Gate C L18+L23 robust ratio:    {"PASS" if gate_c else "FAIL"}')
print(f'  Gate D anti-corr w/ S1:         (deferred to MC12 actual)')
print()
all_pass = gate_a_sharpe and gate_a_pf and gate_b and gate_c
if all_pass:
    print('  ✅ ALL APPLICABLE GATES PASS → GO for W1 spec')
    print('  (Gate D anti-correlation to verify in actual MC12 backtest)')
else:
    print('  ❌ GATE(S) FAIL → KILL S9 → write S9_FINAL_VERDICT.md')
