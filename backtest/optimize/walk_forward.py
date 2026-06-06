"""
Walk-Forward Optimization Framework for TXF1 Strategies.
Usage: python walk_forward.py --strategy NightMomentum
"""
import argparse
import pandas as pd
import numpy as np
import json
from itertools import product

MULTIPLIER = 200
SLIPPAGE = 1000

def load_data():
    df = pd.read_csv("backtest/twii_daily.csv", index_col=0, parse_dates=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def night_momentum_backtest(df, params):
    """Backtest NightMomentum with given params on given data slice."""
    lookback_pct = params.get('lookback_pct', 0.7)
    stop = params.get('stop', 60)
    target = params.get('target', 120)
    
    atr = df['High'] - df['Low']
    atr_ma = atr.rolling(14).mean()
    trades = []
    
    for i in range(20, len(df)-1):
        if atr.iloc[i] < atr_ma.iloc[i] * lookback_pct:
            prev_h, prev_l = df['High'].iloc[i], df['Low'].iloc[i]
            nxt = df.iloc[i+1]
            if nxt['High'] > prev_h + 10 and nxt['Close'] > prev_h:
                entry = prev_h + 10
                if nxt['Low'] <= entry - stop:
                    exit_p = entry - stop
                elif nxt['High'] >= entry + target:
                    exit_p = entry + target
                else:
                    exit_p = nxt['Close']
                pnl = (exit_p - entry) * MULTIPLIER - SLIPPAGE
                trades.append(pnl)
            elif nxt['Low'] < prev_l - 10 and nxt['Close'] < prev_l:
                entry = prev_l - 10
                if nxt['High'] >= entry + stop:
                    exit_p = entry + stop
                elif nxt['Low'] <= entry - target:
                    exit_p = entry - target
                else:
                    exit_p = nxt['Close']
                pnl = (entry - exit_p) * MULTIPLIER - SLIPPAGE
                trades.append(pnl)
    
    if not trades:
        return {'net_profit': 0, 'num_trades': 0, 'pf': 0, 'win_rate': 0}
    
    pnls = np.array(trades)
    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    
    return {
        'net_profit': float(pnls.sum()),
        'num_trades': len(pnls),
        'pf': float(wins.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() != 0 else 999,
        'win_rate': float(len(wins) / len(pnls) * 100),
        'mdd': float(np.maximum.accumulate(np.cumsum(pnls)) - np.cumsum(pnls)).max() if len(pnls) > 0 else 0
    }

STRATEGY_MAP = {
    'NightMomentum': {
        'func': night_momentum_backtest,
        'param_grid': {
            'lookback_pct': [0.5, 0.6, 0.7, 0.8, 0.9],
            'stop': [40, 50, 60, 70, 80, 100],
            'target': [80, 100, 120, 150, 180]
        }
    }
    # Add other strategies here
}

def walk_forward(df, strategy_name, is_months=24, oos_months=6, step_months=6):
    """Run Walk-Forward optimization."""
    config = STRATEGY_MAP[strategy_name]
    func = config['func']
    param_grid = config['param_grid']
    
    # Generate all param combinations
    keys = list(param_grid.keys())
    combos = [dict(zip(keys, v)) for v in product(*param_grid.values())]
    
    results = []
    start = df.index[0]
    end = df.index[-1]
    
    current = start
    window = 0
    
    while True:
        is_start = current
        is_end = is_start + pd.DateOffset(months=is_months)
        oos_start = is_end
        oos_end = oos_start + pd.DateOffset(months=oos_months)
        
        if oos_end > end:
            break
        
        is_data = df[(df.index >= is_start) & (df.index < is_end)]
        oos_data = df[(df.index >= oos_start) & (df.index < oos_end)]
        
        if len(is_data) < 100 or len(oos_data) < 20:
            current += pd.DateOffset(months=step_months)
            continue
        
        # Find best params on IS
        best_pf = -999
        best_params = None
        for combo in combos:
            r = func(is_data, combo)
            if r['num_trades'] >= 5 and r['pf'] > best_pf:
                best_pf = r['pf']
                best_params = combo
        
        if best_params is None:
            current += pd.DateOffset(months=step_months)
            continue
        
        # Test on OOS
        is_result = func(is_data, best_params)
        oos_result = func(oos_data, best_params)
        
        results.append({
            'window': window,
            'is_period': f"{is_start.strftime('%Y-%m')} ~ {is_end.strftime('%Y-%m')}",
            'oos_period': f"{oos_start.strftime('%Y-%m')} ~ {oos_end.strftime('%Y-%m')}",
            'best_params': best_params,
            'is_pf': is_result['pf'],
            'is_net': is_result['net_profit'],
            'is_trades': is_result['num_trades'],
            'oos_pf': oos_result['pf'],
            'oos_net': oos_result['net_profit'],
            'oos_trades': oos_result['num_trades'],
            'oos_win_rate': oos_result['win_rate'],
        })
        
        window += 1
        current += pd.DateOffset(months=step_months)
    
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--is-months', type=int, default=24)
    parser.add_argument('--oos-months', type=int, default=6)
    parser.add_argument('--step-months', type=int, default=6)
    args = parser.parse_args()
    
    if args.strategy not in STRATEGY_MAP:
        print(f"Available strategies: {list(STRATEGY_MAP.keys())}")
        return
    
    df = load_data()
    results = walk_forward(df, args.strategy, args.is_months, args.oos_months, args.step_months)
    
    print(f"\n{'='*80}")
    print(f"Walk-Forward Results: {args.strategy}")
    print(f"IS={args.is_months}m, OOS={args.oos_months}m, Step={args.step_months}m")
    print(f"{'='*80}")
    
    total_oos_profit = 0
    oos_positive = 0
    
    for r in results:
        status = "✓" if r['oos_pf'] > 1.0 else "✗"
        print(f"  Window {r['window']}: IS {r['is_period']} (PF={r['is_pf']:.2f}, ${r['is_net']:,.0f}) → OOS {r['oos_period']} (PF={r['oos_pf']:.2f}, ${r['oos_net']:,.0f}) {status}")
        print(f"    Best params: {r['best_params']}")
        total_oos_profit += r['oos_net']
        if r['oos_pf'] > 1.0:
            oos_positive += 1
    
    wfe = oos_positive / len(results) * 100 if results else 0
    print(f"\nWalk-Forward Efficiency: {wfe:.0f}% ({oos_positive}/{len(results)} windows profitable OOS)")
    print(f"Total OOS Net Profit: {total_oos_profit:,.0f} NTD")
    print(f"Verdict: {'PASS ✓' if wfe >= 50 else 'FAIL ✗'} (threshold: 50%)")
    
    with open(f"backtest/optimize/wf_results_{args.strategy}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

if __name__ == '__main__':
    main()
