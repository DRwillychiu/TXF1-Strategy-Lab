"""
S9 NightFadeShort + Regime Filters — Could a regime filter save S9?

User question 2026-06-21:
  "S9 若加上適合操作盤勢的條件，仍然還是會造成不必要的損失？"

Test 4 regime filter variants on top of base S9 logic:
  F1: TWII MA50 < MA200 (TWII downtrend, "適合做空" regime)
  F2: SPX MA50 < MA200 (US downtrend)
  F3: VIX > 20 proxy (high volatility) — use TWII rolling std
  F4: F1 AND F2 combined (both markets downtrend)

For each variant, check if 1997-2009 (the bad period) can be salvaged.
"""
import io, sys
from datetime import date
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('Fetching SPX + TWII...')
import yfinance as yf
spx_df = yf.download('^GSPC', start='1997-01-01', end='2026-06-21',
                      progress=False, auto_adjust=False)
twii_df = yf.download('^TWII', start='1997-01-01', end='2026-06-21',
                       progress=False, auto_adjust=False)

# Build sorted lists with all needed fields
spx_list = []
for idx, row in spx_df.iterrows():
    try:
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        spx_list.append((idx.date(), c))
    except (ValueError, TypeError):
        continue
spx_list.sort()

twii_list = []
for idx, row in twii_df.iterrows():
    try:
        o = float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open'])
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        twii_list.append((idx.date(), o, c))
    except (ValueError, TypeError):
        continue
twii_list.sort()

# Pre-compute MAs (200-day, 50-day) for SPX and TWII
def compute_ma(price_list, window):
    """Returns dict: date -> MA value (or None if insufficient history)"""
    result = {}
    closes = [p[-1] for p in price_list]  # last element is close
    for i, p in enumerate(price_list):
        if i < window - 1:
            result[p[0]] = None
        else:
            result[p[0]] = sum(closes[i - window + 1:i + 1]) / window
    return result

spx_ma200 = compute_ma(spx_list, 200)
spx_ma50 = compute_ma(spx_list, 50)
twii_ma200 = compute_ma(twii_list, 200)
twii_ma50 = compute_ma(twii_list, 50)

# Rolling 20-day std for TWII (VIX proxy)
def compute_rolling_std(price_list, window):
    result = {}
    closes = [p[-1] for p in price_list]
    rets = [0.0]
    for i in range(1, len(closes)):
        rets.append((closes[i] - closes[i - 1]) / closes[i - 1])
    for i, p in enumerate(price_list):
        if i < window - 1:
            result[p[0]] = None
        else:
            window_rets = rets[i - window + 1:i + 1]
            m = sum(window_rets) / len(window_rets)
            var = sum((r - m) ** 2 for r in window_rets) / len(window_rets)
            result[p[0]] = (var ** 0.5) * (252 ** 0.5)  # annualized
    return result

twii_vol = compute_rolling_std(twii_list, 20)

# SPX dates + returns
spx_data = {d: c for d, c in spx_list}
spx_dates_sorted = [p[0] for p in spx_list]
spx_ret = {}
for i in range(1, len(spx_dates_sorted)):
    d = spx_dates_sorted[i]
    d_prev = spx_dates_sorted[i - 1]
    spx_ret[d] = (spx_data[d] - spx_data[d_prev]) / spx_data[d_prev]

def latest_spx_before(target_d):
    for d in reversed(spx_dates_sorted):
        if d < target_d:
            return d
    return None

twii_by_date = {p[0]: p for p in twii_list}
twii_dates_sorted = [p[0] for p in twii_list]
def prior_twii_close(target_d):
    for d in reversed(twii_dates_sorted):
        if d < target_d:
            return twii_by_date[d][2]
    return None

# ---------- Simulate S9 base + filter ----------
def simulate(spx_weak_thr, filter_name):
    """Returns list of (date, short_pnl)"""
    trades = []
    for d, o, c in twii_list:
        spx_signal_d = latest_spx_before(d)
        if spx_signal_d is None or spx_signal_d not in spx_ret:
            continue
        sig_ret = spx_ret[spx_signal_d]
        if sig_ret * 100 > -spx_weak_thr:
            continue
        prior_c = prior_twii_close(d)
        if prior_c is None or o >= prior_c:
            continue
        # Apply regime filter
        if filter_name == 'NONE':
            pass
        elif filter_name == 'F1_TWII_DOWN':
            if (twii_ma50.get(d) is None or twii_ma200.get(d) is None or
                    twii_ma50[d] >= twii_ma200[d]):
                continue
        elif filter_name == 'F2_SPX_DOWN':
            spx_d = latest_spx_before(d)
            if (spx_ma50.get(spx_d) is None or spx_ma200.get(spx_d) is None or
                    spx_ma50[spx_d] >= spx_ma200[spx_d]):
                continue
        elif filter_name == 'F3_HIGH_VOL':
            if twii_vol.get(d) is None or twii_vol[d] < 0.25:  # 25% annualized
                continue
        elif filter_name == 'F4_BOTH_DOWN':
            if (twii_ma50.get(d) is None or twii_ma200.get(d) is None or
                    twii_ma50[d] >= twii_ma200[d]):
                continue
            spx_d = latest_spx_before(d)
            if (spx_ma50.get(spx_d) is None or spx_ma200.get(spx_d) is None or
                    spx_ma50[spx_d] >= spx_ma200[spx_d]):
                continue
        twii_day_ret = (c - o) / o if o > 0 else 0
        short_pnl = -twii_day_ret
        trades.append((d, short_pnl))
    return trades

def stats(trades, years):
    if not trades:
        return None
    rets = [t[1] for t in trades]
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

# ---------- Compare 5 variants ----------
print()
print('=' * 90)
print('Compare base S9 vs 4 regime-filtered variants (SPX < -0.5% trigger)')
print('=' * 90)
print(f'{"Variant":<22} {"N":>5} {"tpy":>5} {"Mean%":>7} {"WR%":>5} {"PF":>6} {"Cum%":>8} {"Sharpe":>7}')
print('-' * 90)
variants = [
    ('NONE (base S9)', 'NONE'),
    ('F1 TWII downtrend', 'F1_TWII_DOWN'),
    ('F2 SPX downtrend', 'F2_SPX_DOWN'),
    ('F3 High vol (>25%)', 'F3_HIGH_VOL'),
    ('F4 Both down (TWII+SPX)', 'F4_BOTH_DOWN'),
]
results = {}
for label, fname in variants:
    trades = simulate(0.5, fname)  # use SPX < -0.5%
    s = stats(trades, 28.4)
    if s:
        print(f'{label:<22} {s["n"]:>5} {s["tpy"]:>5.1f} {s["mean_pct"]:>7.3f} {s["wr"]:>5.1f} {s["pf"]:>6.3f} {s["cum"]:>+7.2f}% {s["sharpe"]:>7.3f}')
        results[label] = (trades, s)

# ---------- For best filtered variant, check 6 regime + recent bias ----------
best_label = max(results.keys(), key=lambda k: results[k][1]['sharpe'])
print(f'\nBest variant: {best_label}')
best_trades, best_stats = results[best_label]

print()
print('=' * 80)
print(f'6 regime breakdown ({best_label})')
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
print('-' * 75)
regime_pass = 0
for name, d_start, d_end in regimes:
    sub = [t for t in best_trades if d_start <= t[0] <= d_end]
    if not sub:
        print(f'{name:<30} (no trades)')
        continue
    yrs = (d_end - d_start).days / 365.25
    s = stats(sub, yrs)
    flag = '✓' if s['sharpe'] > 0.3 else '❌'
    if s['sharpe'] > 0.3:
        regime_pass += 1
    print(f'{name:<30} {s["n"]:>4} {s["mean_pct"]:>7.3f} {s["wr"]:>5.1f} {s["pf"]:>5.2f} {s["sharpe"]:>7.3f}  {flag}')

# ---------- Recent bias ----------
print()
print('=' * 80)
print('Recent bias check (Gate C: L18)')
print('=' * 80)
s_all = stats(best_trades, 28.4)
recent_trades = [t for t in best_trades if t[0] >= date(2020, 1, 1)]
s_recent = stats(recent_trades, 6.4)
print(f'  28y Sharpe: {s_all["sharpe"]:.3f}')
if s_recent:
    print(f'  Recent 6.4y Sharpe: {s_recent["sharpe"]:.3f}')
    if s_all["sharpe"] > 0 and s_recent["sharpe"] > 0:
        ratio = s_recent["sharpe"] / s_all["sharpe"]
        print(f'  Ratio: {ratio:.2f}x')

# ---------- VERDICT: did filter save S9? ----------
print()
print('=' * 80)
print('VERDICT — Did regime filter save S9?')
print('=' * 80)
base_sharpe = results['NONE (base S9)'][1]['sharpe']
base_pf = results['NONE (base S9)'][1]['pf']
best_sharpe = best_stats['sharpe']
best_pf = best_stats['pf']
print(f'  Base S9     Sharpe: {base_sharpe:.3f}  PF: {base_pf:.3f}')
print(f'  Best filter Sharpe: {best_sharpe:.3f}  PF: {best_pf:.3f}')
print(f'  Sharpe improvement: {best_sharpe - base_sharpe:+.3f}')
print(f'  PF improvement:     {best_pf - base_pf:+.3f}')
print()
print(f'  SOP v2 Gates on best filtered variant:')
print(f'    Gate A 28y Sharpe > 0.4:  {"PASS" if best_sharpe > 0.4 else "FAIL"} ({best_sharpe:.3f})')
print(f'    Gate A 28y PF > 1.3:      {"PASS" if best_pf > 1.3 else "FAIL"} ({best_pf:.3f})')
print(f'    Gate B ≥4/6 regimes >0.3: {"PASS" if regime_pass >= 4 else "FAIL"} ({regime_pass}/6)')
print()
if best_sharpe > 0.4 and best_pf > 1.3 and regime_pass >= 4:
    print('  → ✅ Filter DID save S9 → could reconsider')
else:
    print('  → ❌ Filter did NOT save S9 → KILL decision stands')
    print('     Reason: alpha is fundamentally not robust, no filter can fix that.')

# ---------- Caveat: over-fit warning ----------
print()
print('⚠️ OVERFIT WARNING:')
print('  Testing multiple filters and picking the best = classic data mining.')
print('  Even if a filter "saves" S9 in this 28y backtest, it may fail OOS.')
print('  Truly robust filter would need its own pre-verification on different data.')
