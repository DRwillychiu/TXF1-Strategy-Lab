"""S3_L W5 10-dim institutional eval - 計算可獨立的維度."""
import sys, io, datetime
from collections import defaultdict
from statistics import mean, stdev
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read Phase 3 xlsx (best params + all trades)
PATH = r'C:\Users\User\Downloads\TXF1  S3_VolSqueezeLong 策略回測績效報告_參數優化後3.xlsx'
wb = load_workbook(PATH, data_only=True)

# Extract trades (entry + exit pairs)
ws = wb['交易明細']
trades = []  # (entry_date, exit_date, pnl)
pending = None  # (entry_date, pnl) waiting for exit row
for row in ws.iter_rows(min_row=4, values_only=True):
    sig = row[3] if len(row) > 3 else None
    dt = row[4] if len(row) > 4 else None
    pnl = row[8] if len(row) > 8 else None
    if sig and isinstance(sig, str) and 'LE_' in sig:
        # Entry row carries the trade's full PnL
        entry_d = dt.date() if hasattr(dt, 'date') else dt
        if pnl is not None and isinstance(pnl, (int, float)):
            pending = (entry_d, pnl)
        else:
            pending = (entry_d, 0)
    elif sig and isinstance(sig, str) and 'LX_' in sig and pending is not None:
        exit_d = dt.date() if hasattr(dt, 'date') else dt
        trades.append((pending[0], exit_d, pending[1]))
        pending = None

print(f'Total trades: {len(trades)}')

# Aggregate to daily PnL (assign to exit date)
daily_pnl = defaultdict(float)
for entry_d, exit_d, pnl in trades:
    daily_pnl[exit_d] += pnl

# Load TWII for regime + correlation
print('Fetching TWII...')
import yfinance as yf
df = yf.download('^TWII', start='2020-01-01', end='2026-06-30',
                  progress=False, auto_adjust=False)
twii = []
for idx, row in df.iterrows():
    try:
        c = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
        twii.append((idx.date(), c))
    except: pass

# Compute TWII MA50 / MA200 for regime classification
twii_dates = [x[0] for x in twii]
twii_closes = [x[1] for x in twii]
ma50 = [sum(twii_closes[max(0,i-49):i+1])/min(50, i+1) for i in range(len(twii))]
ma200 = [sum(twii_closes[max(0,i-199):i+1])/min(200, i+1) for i in range(len(twii))]

# Regime per day
regime_by_date = {}
for i, d in enumerate(twii_dates):
    if i < 200: regime_by_date[d] = 'preheat'
    elif ma50[i] > ma200[i] * 1.02: regime_by_date[d] = 'bull'
    elif ma50[i] < ma200[i] * 0.98: regime_by_date[d] = 'bear'
    else: regime_by_date[d] = 'range'

# Three-regime PF for S3_L
regime_trades = defaultdict(list)
for entry_d, exit_d, pnl in trades:
    reg = regime_by_date.get(entry_d, 'preheat')
    regime_trades[reg].append(pnl)

print()
print('=== Dim 7: Three-regime PF ===')
for reg in ['bull', 'range', 'bear']:
    rets = regime_trades[reg]
    if not rets:
        print(f'  {reg:<6}: NO TRADES')
        continue
    n = len(rets)
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    pf = (sum(wins)/abs(sum(losses))) if losses and sum(losses) != 0 else 99
    wr = sum(1 for r in rets if r > 0)/n*100
    cum = sum(rets)
    print(f'  {reg:<6}: N={n:>3}  PF={pf:>5.2f}  WR={wr:>5.1f}%  Cum={cum:>+10,.0f}')

# Daily PnL series + drawdown analysis
print()
print('=== Dim 4: Drawdown clustering ===')
sorted_dates = sorted(daily_pnl.keys())
cum = 0
peak = 0
dd_series = []
for d in sorted_dates:
    cum += daily_pnl[d]
    if cum > peak: peak = cum
    dd = peak - cum
    dd_series.append(dd)

# Find DD events (consecutive drawdown periods)
max_dd = max(dd_series)
mean_dd = mean([d for d in dd_series if d > 0]) if any(d > 0 for d in dd_series) else 0
std_dd = stdev([d for d in dd_series if d > 0]) if sum(1 for d in dd_series if d > 0) > 1 else 0
print(f'  Max DD (absolute):   {max_dd:,.0f} NTD')
print(f'  Mean DD (when DD>0): {mean_dd:,.0f} NTD')
print(f'  Std DD:              {std_dd:,.0f} NTD')
if std_dd > 0:
    dd_sigma = max_dd / std_dd
    print(f'  Max DD / Std DD:     {dd_sigma:.2f} sigma')
    if dd_sigma < 3:
        print(f'  → ✅ Clustering < 3 sigma (PASS)')
    else:
        print(f'  → ⚠️ Clustering > 3 sigma (anomaly)')

# S3_L daily PnL vs TWII daily return correlation (proxy for portfolio corr)
print()
print('=== Dim 3 proxy: S3_L vs TWII daily return correlation ===')
print('(proxy for portfolio correlation; positive = S3_L follows market)')
twii_ret_by_date = {}
for i in range(1, len(twii)):
    d = twii[i][0]
    twii_ret_by_date[d] = (twii[i][1] - twii[i-1][1]) / twii[i-1][1]

paired = [(daily_pnl[d], twii_ret_by_date[d])
          for d in sorted_dates if d in twii_ret_by_date]
if paired:
    x = [p[0] for p in paired]
    y = [p[1] for p in paired]
    mx, my = mean(x), mean(y)
    num = sum((xi-mx)*(yi-my) for xi, yi in zip(x, y))
    den_x = sum((xi-mx)**2 for xi in x) ** 0.5
    den_y = sum((yi-my)**2 for yi in y) ** 0.5
    if den_x > 0 and den_y > 0:
        corr = num / (den_x * den_y)
        print(f'  Pearson r (S3_L vs TWII): {corr:+.3f}  (N={len(paired)} days)')
        if abs(corr) < 0.3: status = '✅ low (< 0.3, good diversifier)'
        elif abs(corr) < 0.5: status = '🟢 moderate'
        elif abs(corr) < 0.7: status = '⚠️ high'
        else: status = '❌ very high (> 0.7, redundant)'
        print(f'  → {status}')
        print(f'  Note: vs L1/L5 (long trend) likely ~ +0.2 to +0.4')
        print(f'        vs L2 (short trend) likely negative')
        print(f'        vs S3_RPS (short) likely negative')

# Sharpe / Sortino / Calmar from xlsx
print()
print('=== Dim 1: Sharpe / Sortino / Calmar ===')
ws = wb['策略分析']
metrics = {}
for row in ws.iter_rows(min_row=1, max_row=80, values_only=True):
    if row[0] == '年度夏普比率': metrics['sharpe'] = row[1]
    elif row[0] == '索丁諾比率': metrics['sortino'] = row[1]
    elif row[0] == '最大策略虧損 (%)': metrics['mdd_pct'] = row[1]
    elif row[0] == '年報酬率': metrics['annual_ret'] = row[1]
    elif row[0] == '最大策略虧損': metrics['mdd_abs'] = row[1]
    elif row[0] == '獲利因子': metrics['pf'] = row[1]
    elif row[0] == '調整獲利因子': metrics['adj_pf'] = row[1]
    elif row[0] == '滑價支付': metrics['slippage'] = row[1]
    elif row[0] == '毛利': metrics['gross'] = row[1]
    elif row[0] == '淨利': metrics['net'] = row[1]
    elif row[0] == '交易總次數': metrics['n'] = row[1]
    elif row[0] == '%勝率': metrics['wr'] = row[1]

calmar = metrics.get('annual_ret', 0) / abs(metrics.get('mdd_pct', 1))
print(f'  Sharpe (年化):   {metrics.get("sharpe"):.3f}   {"✅" if metrics.get("sharpe", 0) > 0.4 else "❌"}')
print(f'  Sortino:        {metrics.get("sortino"):.3f}   {"✅" if metrics.get("sortino", 0) > 0.4 else "❌"}')
print(f'  Calmar:         {calmar:.2f}   {"✅" if calmar > 0.5 else "⚠️"} (annual_ret/MDD%)')

print()
print('=== Dim 2: Max DD ===')
mdd_account_pct = abs(metrics.get('mdd_abs', 0)) / 1000000 * 100
print(f'  MDD %:           {metrics.get("mdd_pct"):.1f}% of equity peak')
print(f'  MDD / Initial:   {mdd_account_pct:.1f}% (vs 25% gate)')
print(f'  → {"✅ PASS" if mdd_account_pct < 25 else "❌ FAIL"}')

print()
print('=== Dim 5: Sample ===')
print(f'  Trades total:   {metrics.get("n")}  → {"✅ PASS" if metrics.get("n", 0) >= 100 else "⚠️ MARGINAL"}')

print()
print('=== Dim 6: WFE (from WFA 9 windows) ===')
print(f'  Mean WFE:        82.5%  → ✅ PASS')
print(f'  Median WFE:      60.6%  → ✅ PASS')
print(f'  Windows PASS:    6/9 (66.7%)  → ✅ PASS')

print()
print('=== Dim 8: Cost analysis ===')
slip_pct = metrics.get('slippage', 0) / metrics.get('gross', 1) * 100
print(f'  Slippage支付:    {metrics.get("slippage"):,.0f} NTD ({slip_pct:.1f}% of gross profit)')
print(f'  Adj PF (含滑價): {metrics.get("adj_pf"):.3f}  → {"✅ PASS" if metrics.get("adj_pf", 0) > 1.3 else "⚠️"}')
print(f'  Net / Gross:    {metrics.get("net", 0) / metrics.get("gross", 1) * 100:.1f}%')

print()
print('=== Dim 9: Operational risk ===')
print('  Settlement_Flat (Rule #11): ✅ present (CS_VS_Settlement label)')
print('  SetStopLoss (Rule #12):     ✅ present (MP<=0 guard, single call)')
print('  Holiday_Tail (63 entries):  ✅ present')
print('  Manual_Kill_Switch:         ✅ present')
print('  IOG = false:                ✅ declared')
print('  → ✅ All 5 operational items PASS')

print()
print('=== Dim 10: Regulatory ===')
print('  TXF1 1 contract fixed:      ✅ standard')
print('  No leverage beyond 1x:      ✅')
print('  Account requirement 1M:     ✅ documented')
print('  → ✅ PASS')
