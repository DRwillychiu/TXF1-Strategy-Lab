"""
Parameter sensitivity analysis - scan one param at a time.
Usage: python param_sensitivity.py --strategy NightMomentum --param stop --range 30,120 --step 10
"""
import argparse
import pandas as pd
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', required=True)
    parser.add_argument('--param', required=True, help='Parameter name to scan')
    parser.add_argument('--range', required=True, help='min,max')
    parser.add_argument('--step', type=int, default=10)
    args = parser.parse_args()
    
    lo, hi = map(int, args.range.split(','))
    values = list(range(lo, hi+1, args.step))
    
    print(f"Parameter Sensitivity: {args.strategy}.{args.param}")
    print(f"Range: {lo} to {hi}, step {args.step}")
    print(f"{'Value':>8} | {'Net Profit':>12} | {'PF':>6} | {'Win%':>6} | {'Trades':>6} | {'MDD':>10}")
    print("-" * 60)
    
    # Placeholder - actual implementation imports strategy backtest function
    for v in values:
        print(f"{v:>8} | {'(run backtest)':>12} | {'':>6} | {'':>6} | {'':>6} | {'':>10}")
    
    print("\nTIP: Look for a 'plateau' - a wide range where performance is stable.")
    print("If performance peaks at one narrow value, it's likely overfit.")

if __name__ == '__main__':
    main()
