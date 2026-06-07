"""
Simplified backtester for 5 TXF1 strategies using daily TAIEX data.
Simulates core logic of each strategy on daily bars.
Contract multiplier: 200 NTD/pt, Slippage: 1000 NTD round-trip, 1 lot.
"""
import pandas as pd
import numpy as np
import json

MULTIPLIER = 200
SLIPPAGE = 1000  # round-trip per trade

df = pd.read_csv("/tmp/TXF1-Strategy-Lab/backtest/twii_daily.csv", index_col=0, parse_dates=True)
df.columns = [c.strip() for c in df.columns]

results = {}

def calc_metrics(trades, name, direction):
    """Calculate strategy metrics from trade list [(entry_price, exit_price, direction, entry_date, exit_date)]"""
    if not trades:
        return None
    
    pnls = []
    for t in trades:
        ep, xp, d, ed, xd = t
        raw_pnl = (xp - ep) * d * MULTIPLIER - SLIPPAGE
        pnls.append(raw_pnl)
    
    pnls = np.array(pnls)
    net_profit = pnls.sum()
    num_trades = len(pnls)
    winners = (pnls > 0).sum()
    losers = (pnls <= 0).sum()
    win_rate = winners / num_trades * 100 if num_trades > 0 else 0
    avg_win = pnls[pnls > 0].mean() if winners > 0 else 0
    avg_loss = abs(pnls[pnls <= 0].mean()) if losers > 0 else 1
    pf = (pnls[pnls > 0].sum() / abs(pnls[pnls <= 0].sum())) if losers > 0 and pnls[pnls <= 0].sum() != 0 else 999
    
    # Equity curve & MDD
    equity = np.cumsum(pnls)
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    mdd = dd.max()
    
    # CAGR (approximate from first to last trade date)
    if len(trades) >= 2:
        first_date = pd.Timestamp(trades[0][3])
        last_date = pd.Timestamp(trades[-1][4])
        years = (last_date - first_date).days / 365.25
        if years > 0 and net_profit > 0:
            # Simple: treat initial capital as 300000 NTD (≈1 lot margin)
            initial_capital = 300000
            cagr = ((initial_capital + net_profit) / initial_capital) ** (1/years) - 1
        else:
            cagr = 0
        ann_return = net_profit / years if years > 0 else 0
    else:
        years = 1
        cagr = 0
        ann_return = 0
    
    return {
        "策略名稱": name,
        "交易方向": direction,
        "總交易次數": num_trades,
        "勝率(%)": round(win_rate, 1),
        "Profit Factor": round(pf, 2),
        "淨利(NTD)": int(net_profit),
        "MDD(NTD)": int(mdd),
        "CAGR(%)": round(cagr * 100, 1),
        "年化報酬(NTD)": int(ann_return),
        "平均獲利(NTD)": int(avg_win),
        "平均虧損(NTD)": int(avg_loss),
        "盈虧比": round(avg_win / avg_loss, 2) if avg_loss > 0 else 999,
        "回測期間": f"{df.index[0].strftime('%Y/%m/%d')} ~ {df.index[-1].strftime('%Y/%m/%d')}",
        "交易年數": round(years, 1),
    }

# ============================================================
# Strategy 1: Night Momentum (simulated as Opening Range Breakout)
# Since we only have daily data, simulate as: if prev day range is narrow,
# next day breakout of prev high/low → trend follow
# Direction: BOTH (long + short)
# ============================================================
print("Running Strategy 1: NightMomentum (ORB proxy)...")
trades_s1 = []
atr14 = df['High'] - df['Low']
atr14_ma = atr14.rolling(14).mean()

for i in range(20, len(df)-1):
    # Narrow range day → next day breakout
    if atr14.iloc[i] < atr14_ma.iloc[i] * 0.7:
        prev_h = df['High'].iloc[i]
        prev_l = df['Low'].iloc[i]
        nxt = df.iloc[i+1]
        # Long breakout
        if nxt['High'] > prev_h + 10 and nxt['Close'] > prev_h:
            entry = prev_h + 10
            stop = entry - 60
            target = entry + 120
            exit_p = min(max(nxt['Low'], stop), min(nxt['High'], target))
            if nxt['Low'] <= stop:
                exit_p = stop
            elif nxt['High'] >= target:
                exit_p = target
            else:
                exit_p = nxt['Close']
            trades_s1.append((entry, exit_p, 1, df.index[i+1], df.index[i+1]))
        # Short breakout
        elif nxt['Low'] < prev_l - 10 and nxt['Close'] < prev_l:
            entry = prev_l - 10
            stop = entry + 60
            target = entry - 120
            if nxt['High'] >= stop:
                exit_p = stop
            elif nxt['Low'] <= target:
                exit_p = target
            else:
                exit_p = nxt['Close']
            trades_s1.append((entry, exit_p, -1, df.index[i+1], df.index[i+1]))

results['S1'] = calc_metrics(trades_s1, "STRATEGY_GEN_NightMomentum", "[DEPRECATED v1.0] ★純做多(v2.1) — 見 S1_NightMomentum.pla")

# ============================================================
# Strategy 2: Inside Bar Breakout
# Direction: BOTH (long with MA up, short with MA down)
# ============================================================
print("Running Strategy 2: InsideBarBreak...")
trades_s2 = []
ma20 = df['Close'].rolling(20).mean()

for i in range(22, len(df)-3):
    # Inside bar: today's H < yesterday's H AND today's L > yesterday's L
    mother_h = df['High'].iloc[i-1]
    mother_l = df['Low'].iloc[i-1]
    inside_h = df['High'].iloc[i]
    inside_l = df['Low'].iloc[i]
    
    if inside_h < mother_h and inside_l > mother_l:
        mother_range = mother_h - mother_l
        if mother_range < 50 or mother_range > 400:
            continue
        stop_dist = max(mother_range * 0.5, 40)
        target_dist = mother_range * 1.5
        
        # Next day breakout
        nxt = df.iloc[i+1]
        # Long (MA up)
        if df['Close'].iloc[i] > ma20.iloc[i] and nxt['Close'] > inside_h + 5:
            entry = inside_h + 5
            sl = entry - stop_dist
            tp = entry + target_dist
            # Hold up to 3 days
            exit_p = nxt['Close']
            exit_date = df.index[i+1]
            for j in range(1, 4):
                if i+1+j >= len(df):
                    break
                bar = df.iloc[i+1+j]
                if bar['Low'] <= sl:
                    exit_p = sl; exit_date = df.index[i+1+j]; break
                if bar['High'] >= tp:
                    exit_p = tp; exit_date = df.index[i+1+j]; break
                exit_p = bar['Close']
                exit_date = df.index[i+1+j]
            trades_s2.append((entry, exit_p, 1, df.index[i+1], exit_date))
        
        # Short (MA down)
        elif df['Close'].iloc[i] < ma20.iloc[i] and nxt['Close'] < inside_l - 5:
            entry = inside_l - 5
            sl = entry + stop_dist
            tp = entry - target_dist
            exit_p = nxt['Close']
            exit_date = df.index[i+1]
            for j in range(1, 4):
                if i+1+j >= len(df):
                    break
                bar = df.iloc[i+1+j]
                if bar['High'] >= sl:
                    exit_p = sl; exit_date = df.index[i+1+j]; break
                if bar['Low'] <= tp:
                    exit_p = tp; exit_date = df.index[i+1+j]; break
                exit_p = bar['Close']
                exit_date = df.index[i+1+j]
            trades_s2.append((entry, exit_p, -1, df.index[i+1], exit_date))

results['S2'] = calc_metrics(trades_s2, "STRATEGY_GEN_InsideBarBreak", "★雙向（做多+做空，MA方向過濾）")

# ============================================================
# Strategy 3: Volatility Squeeze
# Direction: BOTH
# ============================================================
print("Running Strategy 3: VolSqueeze...")
trades_s3 = []
bb_len = 20
bb_std = 2.0
ma_bb = df['Close'].rolling(bb_len).mean()
std_bb = df['Close'].rolling(bb_len).std()
upper = ma_bb + bb_std * std_bb
lower = ma_bb - bb_std * std_bb
bandwidth = ((upper - lower) / ma_bb * 100)
bw_pctile = bandwidth.rolling(120).rank(pct=True) * 100

atr_s3 = (df['High'] - df['Low']).rolling(14).mean()

for i in range(130, len(df)-5):
    if pd.isna(bw_pctile.iloc[i]):
        continue
    if bw_pctile.iloc[i] <= 20:  # Squeeze
        if df['Close'].iloc[i] > upper.iloc[i]:  # Break upper
            entry = df['Close'].iloc[i]
            sl = entry - atr_s3.iloc[i] * 1.5
            tp = entry + atr_s3.iloc[i] * 3.0
            exit_p = entry
            exit_date = df.index[i]
            for j in range(1, 6):
                if i+j >= len(df): break
                bar = df.iloc[i+j]
                if bar['Low'] <= sl:
                    exit_p = sl; exit_date = df.index[i+j]; break
                if bar['High'] >= tp:
                    exit_p = tp; exit_date = df.index[i+j]; break
                if bar['Close'] < ma_bb.iloc[i+j] and j >= 2:
                    exit_p = bar['Close']; exit_date = df.index[i+j]; break
                exit_p = bar['Close']; exit_date = df.index[i+j]
            trades_s3.append((entry, exit_p, 1, df.index[i], exit_date))
        
        elif df['Close'].iloc[i] < lower.iloc[i]:  # Break lower
            entry = df['Close'].iloc[i]
            sl = entry + atr_s3.iloc[i] * 1.5
            tp = entry - atr_s3.iloc[i] * 3.0
            exit_p = entry
            exit_date = df.index[i]
            for j in range(1, 6):
                if i+j >= len(df): break
                bar = df.iloc[i+j]
                if bar['High'] >= sl:
                    exit_p = sl; exit_date = df.index[i+j]; break
                if bar['Low'] <= tp:
                    exit_p = tp; exit_date = df.index[i+j]; break
                if bar['Close'] > ma_bb.iloc[i+j] and j >= 2:
                    exit_p = bar['Close']; exit_date = df.index[i+j]; break
                exit_p = bar['Close']; exit_date = df.index[i+j]
            trades_s3.append((entry, exit_p, -1, df.index[i], exit_date))

results['S3'] = calc_metrics(trades_s3, "STRATEGY_GEN_VolSqueeze", "★雙向（做多+做空）")

# ============================================================
# Strategy 4: MACD Divergence Reversal
# Direction: BOTH (counter-trend)
# ============================================================
print("Running Strategy 4: MACDDivergence...")
trades_s4 = []
ema12 = df['Close'].ewm(span=12).mean()
ema26 = df['Close'].ewm(span=26).mean()
macd = ema12 - ema26
signal = macd.ewm(span=9).mean()
hist = macd - signal

# RSI
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))

for i in range(60, len(df)-5):
    # Bullish divergence: price new low but hist higher low
    price_new_low = df['Low'].iloc[i] == df['Low'].iloc[i-50:i+1].min()
    hist_curr_low = hist.iloc[i-10:i+1].min()
    hist_prev_low = hist.iloc[i-40:i-10].min()
    
    if price_new_low and hist_curr_low > hist_prev_low and hist.iloc[i] > 0 and hist.iloc[i-1] <= 0 and rsi.iloc[i] < 35:
        entry = df['Close'].iloc[i]
        sl = df['Low'].iloc[i-10:i+1].min() - 15
        tp = entry + 100
        exit_p = entry; exit_date = df.index[i]
        for j in range(1, 6):
            if i+j >= len(df): break
            bar = df.iloc[i+j]
            if bar['Low'] <= sl:
                exit_p = sl; exit_date = df.index[i+j]; break
            if bar['High'] >= tp:
                exit_p = tp; exit_date = df.index[i+j]; break
            exit_p = bar['Close']; exit_date = df.index[i+j]
        trades_s4.append((entry, exit_p, 1, df.index[i], exit_date))
    
    # Bearish divergence
    price_new_high = df['High'].iloc[i] == df['High'].iloc[i-50:i+1].max()
    hist_curr_high = hist.iloc[i-10:i+1].max()
    hist_prev_high = hist.iloc[i-40:i-10].max()
    
    if price_new_high and hist_curr_high < hist_prev_high and hist.iloc[i] < 0 and hist.iloc[i-1] >= 0 and rsi.iloc[i] > 65:
        entry = df['Close'].iloc[i]
        sl = df['High'].iloc[i-10:i+1].max() + 15
        tp = entry - 100
        exit_p = entry; exit_date = df.index[i]
        for j in range(1, 6):
            if i+j >= len(df): break
            bar = df.iloc[i+j]
            if bar['High'] >= sl:
                exit_p = sl; exit_date = df.index[i+j]; break
            if bar['Low'] <= tp:
                exit_p = tp; exit_date = df.index[i+j]; break
            exit_p = bar['Close']; exit_date = df.index[i+j]
        trades_s4.append((entry, exit_p, -1, df.index[i], exit_date))

results['S4'] = calc_metrics(trades_s4, "STRATEGY_GEN_MACDDivergence", "★雙向（做多+做空，逆勢反轉）")

# ============================================================
# Strategy 5: Settlement Week Effect
# Direction: Short before settlement, Long after
# ============================================================
print("Running Strategy 5: SettlementWeek...")
trades_s5 = []

for i in range(5, len(df)-5):
    dt = df.index[i]
    dom = dt.day
    dow = dt.dayofweek  # 0=Mon, 2=Wed
    month = dt.month
    
    # Third Wednesday: DOM 15-21 and Wednesday
    is_settle = (dow == 2) and (dom >= 15) and (dom <= 21)
    
    # 2 days before settlement = Monday of settlement week
    is_pre_settle = (dow == 0) and (dom >= 13) and (dom <= 19)
    
    # 1 day after settlement = Thursday after 3rd Wed
    is_post_settle = (dow == 3) and (dom >= 16) and (dom <= 22)
    
    # Short before settlement (Monday, bearish candle filter)
    if is_pre_settle and df['Close'].iloc[i] < df['Open'].iloc[i]:
        entry = df['Close'].iloc[i]
        sl = entry + 80
        tp = entry - 100
        exit_p = entry; exit_date = df.index[i]
        for j in range(1, 4):
            if i+j >= len(df): break
            bar = df.iloc[i+j]
            if bar['High'] >= sl:
                exit_p = sl; exit_date = df.index[i+j]; break
            if bar['Low'] <= tp:
                exit_p = tp; exit_date = df.index[i+j]; break
            exit_p = bar['Close']; exit_date = df.index[i+j]
        trades_s5.append((entry, exit_p, -1, df.index[i], exit_date))
    
    # Long after settlement (Thursday, above 5MA filter)
    ma5 = df['Close'].iloc[max(0,i-4):i+1].mean()
    if is_post_settle and df['Close'].iloc[i] > ma5:
        entry = df['Close'].iloc[i]
        sl = entry - 80
        tp = entry + 100
        exit_p = entry; exit_date = df.index[i]
        for j in range(1, 4):
            if i+j >= len(df): break
            bar = df.iloc[i+j]
            if bar['Low'] <= sl:
                exit_p = sl; exit_date = df.index[i+j]; break
            if bar['High'] >= tp:
                exit_p = tp; exit_date = df.index[i+j]; break
            exit_p = bar['Close']; exit_date = df.index[i+j]
        trades_s5.append((entry, exit_p, 1, df.index[i], exit_date))

results['S5'] = calc_metrics(trades_s5, "STRATEGY_GEN_SettlementWeek", "★結算前做空 / 結算後做多")

# Print results
print("\n" + "="*80)
print("TXF1 策略模擬回測結果摘要")
print("="*80)
print(f"{'':>3} | {'策略':^30} | {'方向':^20} | {'交易數':>5} | {'勝率%':>6} | {'PF':>6} | {'淨利':>10} | {'MDD':>10} | {'CAGR%':>6} | {'年化報酬':>10} | {'盈虧比':>5}")
print("-"*140)
for k in ['S1','S2','S3','S4','S5']:
    r = results[k]
    if r:
        print(f" {k} | {r['策略名稱']:^30} | {r['交易方向']:^20} | {r['總交易次數']:>5} | {r['勝率(%)']:>5.1f}% | {r['Profit Factor']:>5.2f} | {r['淨利(NTD)']:>9,} | {r['MDD(NTD)']:>9,} | {r['CAGR(%)']:>5.1f}% | {r['年化報酬(NTD)']:>9,} | {r['盈虧比']:>5.2f}")

# Save JSON
with open("/tmp/TXF1-Strategy-Lab/backtest/results_batch01.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print("\nResults saved to results_batch01.json")
