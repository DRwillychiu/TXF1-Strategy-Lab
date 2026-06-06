"""
Monte Carlo simulation for TXF1 strategies.
Shuffles trade sequence N times to estimate MDD distribution.
Usage: python monte_carlo.py --strategy NightMomentum --iterations 10000
"""
import argparse
import numpy as np
import json

def run_monte_carlo(trade_pnls, iterations=10000, initial_capital=300000):
    """Shuffle trade sequence and compute MDD distribution."""
    pnls = np.array(trade_pnls)
    n = len(pnls)
    
    mdds = []
    final_equities = []
    ruin_count = 0
    ruin_threshold = initial_capital * 0.5  # 50% drawdown = ruin
    
    for _ in range(iterations):
        shuffled = np.random.permutation(pnls)
        equity = np.cumsum(shuffled)
        peak = np.maximum.accumulate(equity)
        dd = peak - equity
        max_dd = dd.max()
        mdds.append(max_dd)
        final_equities.append(equity[-1])
        if max_dd >= ruin_threshold:
            ruin_count += 1
    
    mdds = np.array(mdds)
    final_equities = np.array(final_equities)
    
    return {
        'iterations': iterations,
        'num_trades': n,
        'original_net_profit': float(pnls.sum()),
        'mdd_mean': float(mdds.mean()),
        'mdd_median': float(np.median(mdds)),
        'mdd_95pct': float(np.percentile(mdds, 95)),
        'mdd_99pct': float(np.percentile(mdds, 99)),
        'ruin_probability': float(ruin_count / iterations * 100),
        'final_equity_5pct': float(np.percentile(final_equities, 5)),
        'final_equity_median': float(np.median(final_equities)),
        'final_equity_95pct': float(np.percentile(final_equities, 95)),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-file', required=True, help='Path to backtest results JSON')
    parser.add_argument('--iterations', type=int, default=10000)
    args = parser.parse_args()
    
    # Load trade PnLs from results
    with open(args.results_file) as f:
        data = json.load(f)
    
    # Expect data to have a 'trade_pnls' key (list of individual trade PnLs)
    if 'trade_pnls' not in data:
        print("ERROR: results file must contain 'trade_pnls' array")
        return
    
    results = run_monte_carlo(data['trade_pnls'], args.iterations)
    
    print(f"\nMonte Carlo Simulation ({results['iterations']:,} iterations)")
    print(f"{'='*50}")
    print(f"Trades: {results['num_trades']}")
    print(f"Original Net Profit: {results['original_net_profit']:,.0f} NTD")
    print(f"")
    print(f"MDD Distribution:")
    print(f"  Mean:   {results['mdd_mean']:>10,.0f} NTD")
    print(f"  Median: {results['mdd_median']:>10,.0f} NTD")
    print(f"  95%:    {results['mdd_95pct']:>10,.0f} NTD")
    print(f"  99%:    {results['mdd_99pct']:>10,.0f} NTD")
    print(f"")
    print(f"Ruin Probability (50% DD): {results['ruin_probability']:.2f}%")
    print(f"Final Equity (5%-median-95%): {results['final_equity_5pct']:,.0f} / {results['final_equity_median']:,.0f} / {results['final_equity_95pct']:,.0f}")

if __name__ == '__main__':
    main()
