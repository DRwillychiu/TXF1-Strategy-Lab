"""
L3 v14 Pre-Verify: Full-Range Consolidation Strategy Alpha Test

PURPOSE: Before redesigning L3 from half-box to full-range architecture,
         verify the alpha hypothesis on 28-year TWII daily data.

HYPOTHESIS: "Buy at support zone of detected consolidation box, target
            the FULL range (resistance/box top), with small-box filter"
            produces better risk-adjusted returns than the current half-box.

3 VARIANTS COMPARED:
  A (Current L3):  Mid-line entry → half-box target (box top for mid leg)
  B (Full-range):  Support zone entry → box top target
  C (Filtered):    Same as B, but skip boxes < Min_Box_ATR_Ratio × ATR

W0 GATES (SOP v2):
  Gate A: 28-year Sharpe, PF
  Gate B: ≥4/6 macro regimes Sharpe > 0.3
  Gate C: Recent-bias ratio < 2.5×

Box detection adapted from L3's 60M algorithm to daily bars:
  - Lookback: parameterized (default 20 days)
  - Shrink: today's range / reference range ≤ threshold
  - Inside: High ≤ Ref_High AND Low ≥ Ref_Low
"""
import io
import sys
from datetime import date
from collections import defaultdict
from statistics import mean, stdev

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# 1. FETCH DATA
# ============================================================
print('='*80)
print('L3 v14 Pre-Verify: Full-Range Consolidation Alpha')
print('='*80)
print()
print('Fetching ^TWII 1997-2026 via yfinance...')
import yfinance as yf
df = yf.download('^TWII', start='1997-01-01', end='2026-07-03',
                 progress=False, auto_adjust=False)
bars = []
for idx, row in df.iterrows():
    try:
        o = float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open'])
        h = float(row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High'])
        l = float(row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low'])
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        if o > 0 and h > 0 and l > 0 and c > 0:
            bars.append({'date': idx.date(), 'o': o, 'h': h, 'l': l, 'c': c})
    except (ValueError, TypeError):
        continue
print(f'  Loaded {len(bars)} trading days, {bars[0]["date"]} → {bars[-1]["date"]}')
years_total = (bars[-1]['date'] - bars[0]['date']).days / 365.25
print(f'  Span: {years_total:.1f} years')

# ============================================================
# 2. COMPUTE ATR (20-day True Range average)
# ============================================================
for i in range(len(bars)):
    if i == 0:
        bars[i]['tr'] = bars[i]['h'] - bars[i]['l']
    else:
        prev_c = bars[i-1]['c']
        bars[i]['tr'] = max(bars[i]['h'] - bars[i]['l'],
                           abs(bars[i]['h'] - prev_c),
                           abs(bars[i]['l'] - prev_c))

ATR_LEN = 20
for i in range(len(bars)):
    if i < ATR_LEN:
        bars[i]['atr'] = bars[i]['tr']
    else:
        bars[i]['atr'] = sum(b['tr'] for b in bars[i-ATR_LEN+1:i+1]) / ATR_LEN

# ============================================================
# 3. BOX DETECTION (L3 algorithm adapted to daily)
# ============================================================
LOOKBACK = 20
SHRINK_RATE = 0.15

for i in range(len(bars)):
    bars[i]['in_box'] = False
    bars[i]['box_top'] = 0
    bars[i]['box_btm'] = 0
    bars[i]['box_mid'] = 0
    bars[i]['box_range'] = 0
    bars[i]['box_range_atr'] = 0

    if i < LOOKBACK + 1:
        continue

    ref_high = max(b['h'] for b in bars[i-LOOKBACK:i])
    ref_low  = min(b['l'] for b in bars[i-LOOKBACK:i])
    ref_range = ref_high - ref_low
    curr_range = bars[i]['h'] - bars[i]['l']

    if ref_range <= 0:
        continue

    if (bars[i]['h'] <= ref_high and
        bars[i]['l'] >= ref_low and
        curr_range / ref_range <= SHRINK_RATE):

        bars[i]['in_box'] = True
        bars[i]['box_top'] = ref_high
        bars[i]['box_btm'] = ref_low
        bars[i]['box_mid'] = (ref_high + ref_low) / 2
        bars[i]['box_range'] = ref_range
        bars[i]['box_range_atr'] = ref_range / bars[i]['atr'] if bars[i]['atr'] > 0 else 0

box_days = sum(1 for b in bars if b['in_box'])
print(f'  Consolidation days detected: {box_days} / {len(bars)} ({box_days/len(bars)*100:.1f}%)')

# ============================================================
# 4. SIMULATE TRADES
# ============================================================
SLIPPAGE_PCT = 0.0005  # 0.05% round-trip slippage proxy
MIN_BOX_ATR_RATIO = 5.0  # Variant C: skip boxes < 5× ATR (daily boxes are large)

def simulate_variant(bars, variant_name, entry_zone_pct=0.30, target_mode='full',
                     min_box_atr=0.0, max_hold_days=20):
    """
    Simulate consolidation trades on daily TWII data.

    entry_zone_pct: entry when close is in bottom X% of box
    target_mode: 'half' (mid-line) or 'full' (box top)
    min_box_atr: minimum box_range/ATR to take trade (0=no filter)
    max_hold_days: force exit after N days
    """
    trades = []
    i = 0
    while i < len(bars) - 1:
        b = bars[i]

        if not b['in_box']:
            i += 1
            continue

        # Box size filter
        if min_box_atr > 0 and b['box_range_atr'] < min_box_atr:
            i += 1
            continue

        box_top = b['box_top']
        box_btm = b['box_btm']
        box_mid = b['box_mid']
        box_range = b['box_range']
        atr = b['atr']

        # Entry zone check
        entry_threshold = box_btm + box_range * entry_zone_pct
        if b['c'] > entry_threshold:
            i += 1
            continue

        # Entry next day at open
        entry_idx = i + 1
        if entry_idx >= len(bars):
            break
        entry_price = bars[entry_idx]['o']

        # Stop and target
        stop_price = box_btm - atr * 0.5
        if target_mode == 'half':
            target_price = box_mid
        elif target_mode == 'full':
            target_price = box_top
        else:
            target_price = box_top

        # Simulate bar-by-bar
        exit_price = None
        exit_type = None
        exit_date = None
        hold_days = 0

        for j in range(entry_idx + 1, min(entry_idx + max_hold_days + 1, len(bars))):
            bar = bars[j]
            hold_days += 1

            # Check stop (low touches stop)
            if bar['l'] <= stop_price:
                exit_price = stop_price
                exit_type = 'SL'
                exit_date = bar['date']
                break

            # Check target (high touches target)
            if bar['h'] >= target_price:
                exit_price = target_price
                exit_type = 'TP'
                exit_date = bar['date']
                break

            # Check box break (close outside box)
            if bar['c'] > box_top or bar['c'] < box_btm:
                exit_price = bar['c']
                exit_type = 'BoxBreak'
                exit_date = bar['date']
                break

        # Force exit at max hold
        if exit_price is None:
            last_j = min(entry_idx + max_hold_days, len(bars) - 1)
            exit_price = bars[last_j]['c']
            exit_type = 'TimeOut'
            exit_date = bars[last_j]['date']

        # PnL (points, with slippage)
        pnl_pts = exit_price - entry_price
        pnl_pct = pnl_pts / entry_price - SLIPPAGE_PCT

        trades.append({
            'entry_date': bars[entry_idx]['date'],
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pts': pnl_pts,
            'pnl_pct': pnl_pct,
            'exit_type': exit_type,
            'hold_days': hold_days,
            'box_range': box_range,
            'box_range_atr': b['box_range_atr'],
        })

        # Skip to exit day + 1
        exit_bar_idx = next((k for k in range(entry_idx, len(bars))
                           if bars[k]['date'] >= exit_date), entry_idx + hold_days)
        i = exit_bar_idx + 1
        continue

        i += 1

    return trades

# Run 3 variants
print()
print('Running simulations...')
trades_A = simulate_variant(bars, 'A_HalfBox',
                            entry_zone_pct=0.50, target_mode='half',
                            min_box_atr=0.0)
trades_B = simulate_variant(bars, 'B_FullRange',
                            entry_zone_pct=0.30, target_mode='full',
                            min_box_atr=0.0)
trades_C = simulate_variant(bars, 'C_Filtered',
                            entry_zone_pct=0.30, target_mode='full',
                            min_box_atr=MIN_BOX_ATR_RATIO)

print(f'  Variant A (Half-box):    {len(trades_A)} trades')
print(f'  Variant B (Full-range):  {len(trades_B)} trades')
print(f'  Variant C (Filtered):    {len(trades_C)} trades')

# ============================================================
# 5. STATS ENGINE
# ============================================================
def compute_stats(trades, label, total_years):
    if not trades:
        print(f'\n  {label}: NO TRADES')
        return None

    pnls = [t['pnl_pct'] for t in trades]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    wr = len(wins) / n * 100
    avg_win = mean(wins) * 100 if wins else 0
    avg_loss = mean(losses) * 100 if losses else 0
    reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 99
    pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 99
    cum_pct = sum(pnls) * 100
    m = mean(pnls)
    sd = stdev(pnls) if n > 1 else 0
    tpy = n / total_years
    annual_ret = tpy * m
    annual_vol = sd * (tpy ** 0.5)
    sharpe = annual_ret / annual_vol if annual_vol > 0 else 0

    # Exit type breakdown
    exit_counts = defaultdict(int)
    exit_pnl = defaultdict(float)
    for t in trades:
        exit_counts[t['exit_type']] += 1
        exit_pnl[t['exit_type']] += t['pnl_pct']

    # Box size stats
    box_sizes = [t['box_range_atr'] for t in trades]

    print(f'\n  {label}')
    print(f'    Trades: {n}  ({tpy:.1f}/yr)')
    print(f'    WR: {wr:.1f}%  AvgWin: {avg_win:+.3f}%  AvgLoss: {avg_loss:+.3f}%  Reward: {reward_ratio:.2f}x')
    print(f'    PF: {pf:.3f}  Cum: {cum_pct:+.2f}%  Sharpe(ann): {sharpe:.3f}')
    print(f'    Box size (ATR): min={min(box_sizes):.1f}  med={sorted(box_sizes)[len(box_sizes)//2]:.1f}  max={max(box_sizes):.1f}')
    print(f'    Exits: ', end='')
    for etype in ['TP', 'SL', 'BoxBreak', 'TimeOut']:
        if exit_counts[etype] > 0:
            pct = exit_counts[etype] / n * 100
            avg_e = exit_pnl[etype] / exit_counts[etype] * 100
            print(f'{etype}={exit_counts[etype]}({pct:.0f}%,{avg_e:+.2f}%) ', end='')
    print()

    return {
        'n': n, 'wr': wr, 'pf': pf, 'reward': reward_ratio,
        'cum_pct': cum_pct, 'sharpe': sharpe, 'tpy': tpy,
        'avg_win': avg_win, 'avg_loss': avg_loss,
        'trades': trades
    }

# ============================================================
# 6. OVERALL RESULTS
# ============================================================
print()
print('='*80)
print('OVERALL RESULTS')
print('='*80)

stats_A = compute_stats(trades_A, 'A: Current Half-Box (mid entry → mid target)', years_total)
stats_B = compute_stats(trades_B, 'B: Full-Range (support zone → box top)', years_total)
stats_C = compute_stats(trades_C, f'C: Filtered Full-Range (min box ≥ {MIN_BOX_ATR_RATIO}×ATR)', years_total)

# ============================================================
# 7. COMPARISON TABLE
# ============================================================
print()
print('='*80)
print('HEAD-TO-HEAD COMPARISON')
print('='*80)
print(f'{"Metric":<20} {"A:HalfBox":>12} {"B:FullRange":>12} {"C:Filtered":>12}  {"B vs A":>10} {"C vs A":>10}')
print('-'*80)

for metric, key in [
    ('Trades', 'n'),
    ('WR %', 'wr'),
    ('PF', 'pf'),
    ('Reward Ratio', 'reward'),
    ('Cum Return %', 'cum_pct'),
    ('Sharpe (ann)', 'sharpe'),
    ('Avg Win %', 'avg_win'),
    ('Avg Loss %', 'avg_loss'),
]:
    a_val = stats_A[key] if stats_A else 0
    b_val = stats_B[key] if stats_B else 0
    c_val = stats_C[key] if stats_C else 0
    b_diff = b_val - a_val
    c_diff = c_val - a_val
    print(f'{metric:<20} {a_val:>12.3f} {b_val:>12.3f} {c_val:>12.3f}  {b_diff:>+10.3f} {c_diff:>+10.3f}')

# ============================================================
# 8. W0 GATE ANALYSIS (on best variant)
# ============================================================
print()
print('='*80)
print('W0 GATES (SOP v2) — applied to each variant')
print('='*80)

REGIMES = [
    ('1997-2002 Dot-com',    date(1997, 1, 1), date(2002, 12, 31)),
    ('2003-2007 China bull',  date(2003, 1, 1), date(2007, 12, 31)),
    ('2008-2009 GFC',        date(2008, 1, 1), date(2009, 12, 31)),
    ('2010-2014 Post-GFC',   date(2010, 1, 1), date(2014, 12, 31)),
    ('2015-2019 Sideways',   date(2015, 1, 1), date(2019, 12, 31)),
    ('2020-2026 COVID+AI',   date(2020, 1, 1), date(2026, 12, 31)),
]

def run_w0_gates(trades, label, stats):
    if not trades or not stats:
        print(f'\n  {label}: SKIP (no trades)')
        return

    print(f'\n--- {label} ---')

    # Gate A: 28-year robustness
    ga_sharpe = stats['sharpe'] > 0.4
    ga_pf = stats['pf'] > 1.3
    print(f'  Gate A  28y Sharpe > 0.4:  {"PASS" if ga_sharpe else "FAIL"}  ({stats["sharpe"]:.3f})')
    print(f'  Gate A  28y PF > 1.3:      {"PASS" if ga_pf else "FAIL"}  ({stats["pf"]:.3f})')

    # Gate B: regime analysis
    print(f'\n  Gate B  Regime Sharpe (≥4/6 > 0.3):')
    print(f'  {"Regime":<25} {"N":>4} {"WR%":>6} {"PF":>6} {"Cum%":>8} {"Sharpe":>8}')
    print(f'  {"-"*60}')
    regime_pass = 0
    for rname, d_start, d_end in REGIMES:
        rt = [t for t in trades if d_start <= t['entry_date'] <= d_end]
        if not rt:
            print(f'  {rname:<25}    -      -      -        -        -')
            continue
        rpnls = [t['pnl_pct'] for t in rt]
        rn = len(rpnls)
        rwr = sum(1 for p in rpnls if p > 0) / rn * 100
        rwins = [p for p in rpnls if p > 0]
        rlosses = [p for p in rpnls if p <= 0]
        rpf = sum(rwins) / abs(sum(rlosses)) if rlosses and sum(rlosses) != 0 else 99
        rcum = sum(rpnls) * 100
        rsd = stdev(rpnls) if rn > 1 else 0
        ryrs = (d_end - d_start).days / 365.25
        rtpy = rn / ryrs
        rsharpe = (rtpy * mean(rpnls)) / (rsd * (rtpy**0.5)) if rsd > 0 and rtpy > 0 else 0
        flag = '  ✓' if rsharpe > 0.3 else '  ✗'
        if rsharpe > 0.3:
            regime_pass += 1
        print(f'  {rname:<25} {rn:>4} {rwr:>6.1f} {rpf:>6.2f} {rcum:>+7.1f}% {rsharpe:>8.3f}{flag}')
    gb = regime_pass >= 4
    print(f'  Result: {regime_pass}/6 pass → {"PASS" if gb else "FAIL"}')

    # Gate C: recent-bias
    all_pnls = [t['pnl_pct'] for t in trades]
    recent_pnls = [t['pnl_pct'] for t in trades if t['entry_date'] >= date(2020, 1, 1)]
    recent_yrs = 6.5

    def qsharpe(pnls, yrs):
        if not pnls: return 0
        n = len(pnls)
        m = mean(pnls)
        sd_ = stdev(pnls) if n > 1 else 0
        tpy_ = n / yrs
        return (tpy_ * m) / (sd_ * (tpy_**0.5)) if sd_ > 0 else 0

    s28 = qsharpe(all_pnls, years_total)
    s_recent = qsharpe(recent_pnls, recent_yrs)
    if s28 > 0:
        ratio = s_recent / s28
        gc = 0.4 <= ratio <= 2.5
    else:
        ratio = float('inf')
        gc = False
    print(f'\n  Gate C  Recent-bias (L18):')
    print(f'    28y Sharpe: {s28:.3f}  Recent {recent_yrs}y: {s_recent:.3f}  Ratio: {ratio:.2f}x → {"PASS" if gc else "FAIL"}')

    # Verdict
    all_pass = ga_sharpe and ga_pf and gb and gc
    print(f'\n  VERDICT: {"✅ ALL GATES PASS" if all_pass else "❌ GATE(S) FAIL"}')
    return all_pass

result_A = run_w0_gates(trades_A, 'A: Half-Box', stats_A)
result_B = run_w0_gates(trades_B, 'B: Full-Range', stats_B)
result_C = run_w0_gates(trades_C, 'C: Filtered', stats_C)

# ============================================================
# 9. BOX SIZE ANALYSIS
# ============================================================
print()
print('='*80)
print('BOX SIZE DISTRIBUTION (Variant B — all trades)')
print('='*80)
if trades_B:
    box_sizes_b = sorted([t['box_range_atr'] for t in trades_B])
    # Quintile analysis
    quintiles = [0, 20, 40, 60, 80, 100]
    print(f'  {"Quintile":<15} {"Box/ATR":>8} {"N":>5} {"WR%":>6} {"PF":>6} {"AvgPnl%":>8}')
    print(f'  {"-"*50}')
    for q in range(len(quintiles)-1):
        lo_pct = quintiles[q]
        hi_pct = quintiles[q+1]
        lo_idx = int(len(box_sizes_b) * lo_pct / 100)
        hi_idx = int(len(box_sizes_b) * hi_pct / 100)
        if lo_idx >= len(box_sizes_b):
            continue
        lo_val = box_sizes_b[lo_idx]
        hi_val = box_sizes_b[min(hi_idx, len(box_sizes_b)-1)]
        qt = [t for t in trades_B if lo_val <= t['box_range_atr'] <= hi_val]
        if not qt:
            continue
        qpnls = [t['pnl_pct'] for t in qt]
        qn = len(qpnls)
        qwr = sum(1 for p in qpnls if p > 0) / qn * 100
        qwins = [p for p in qpnls if p > 0]
        qlosses = [p for p in qpnls if p <= 0]
        qpf = sum(qwins) / abs(sum(qlosses)) if qlosses and sum(qlosses) != 0 else 99
        qavg = mean(qpnls) * 100
        print(f'  Q{q+1} ({lo_pct}-{hi_pct}%)    {lo_val:>4.1f}-{hi_val:<4.1f} {qn:>5} {qwr:>6.1f} {qpf:>6.2f} {qavg:>+7.3f}%')

# ============================================================
# 10. YEARLY BREAKDOWN (best variant)
# ============================================================
print()
print('='*80)
print('YEARLY PnL — All 3 Variants')
print('='*80)

def yearly_pnl(trades):
    by_year = defaultdict(list)
    for t in trades:
        by_year[t['entry_date'].year].append(t['pnl_pct'])
    return by_year

ya = yearly_pnl(trades_A)
yb = yearly_pnl(trades_B)
yc = yearly_pnl(trades_C)
all_years = sorted(set(list(ya.keys()) + list(yb.keys()) + list(yc.keys())))

print(f'  {"Year":<6} {"A:N":>4} {"A:Cum%":>8} {"B:N":>4} {"B:Cum%":>8} {"C:N":>4} {"C:Cum%":>8}')
print(f'  {"-"*50}')
for yr in all_years:
    an = len(ya.get(yr, []))
    ac = sum(ya.get(yr, [])) * 100
    bn = len(yb.get(yr, []))
    bc = sum(yb.get(yr, [])) * 100
    cn = len(yc.get(yr, []))
    cc = sum(yc.get(yr, [])) * 100
    print(f'  {yr:<6} {an:>4} {ac:>+7.2f}% {bn:>4} {bc:>+7.2f}% {cn:>4} {cc:>+7.2f}%')

# ============================================================
# 11. FINAL RECOMMENDATION
# ============================================================
print()
print('='*80)
print('FINAL RECOMMENDATION')
print('='*80)

variants = [
    ('A: Half-Box (current)', stats_A, result_A),
    ('B: Full-Range', stats_B, result_B),
    ('C: Filtered Full-Range', stats_C, result_C),
]

best = None
best_sharpe = -99
for name, st, gates in variants:
    if st is None:
        continue
    print(f'  {name:<30} Sharpe={st["sharpe"]:.3f}  PF={st["pf"]:.3f}  Reward={st["reward"]:.2f}x  Gates={"PASS" if gates else "FAIL"}')
    if st['sharpe'] > best_sharpe and gates:
        best = name
        best_sharpe = st['sharpe']

print()
if best:
    print(f'  → BEST: {best} (Sharpe {best_sharpe:.3f})')
    print(f'  → Proceed to V14 implementation')
else:
    print(f'  → No variant passes all W0 gates')
    print(f'  → Review parameters or reconsider redesign')
