"""[DEPRECATED] Re-run Monte Carlo with v1.0 Walk-Forward optimized parameters.
⚠️ 此腳本為 v1.0 固定點數日線代理版本，已被 MC12 15M v2.1 ATR 版本取代。
正式 Phase 3 結果見 optimization/logs/B01_S1_NightMomentum.md
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s1_optimize import load_data, backtest_s1, calc_metrics, INITIAL_CAPITAL
import numpy as np

df = load_data()
trades = backtest_s1(df, lookback=6, entry_offset=6, stop_pts=80, target_pts=160,
                     trail_activate=50, trail_offset=30)
m = calc_metrics(trades)
print(f"WF-optimized params: lookback=6, offset=6, stop=80, target=160")
print(f"Trades={m['num_trades']}  Net={m['net_profit']:,}  PF={m['pf']}  Win={m['win_rate']}%  MDD={m['mdd']:,}")

pnls = np.array([t[0] for t in trades])
rng = np.random.default_rng(42)
mdds = np.zeros(10000)
ruin_count = 0
for i in range(10000):
    shuffled = rng.permutation(pnls)
    eq = np.cumsum(shuffled)
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq).max()
    mdds[i] = dd
    if dd >= INITIAL_CAPITAL * 0.5:
        ruin_count += 1

threshold = INITIAL_CAPITAL * 0.30
p95 = np.percentile(mdds, 95)
print(f"\nMonte Carlo (WF-optimized, 10k iterations):")
print(f"  Mean MDD:   {mdds.mean():>10,.0f}")
print(f"  Median MDD: {np.median(mdds):>10,.0f}")
print(f"  95th MDD:   {p95:>10,.0f}  vs threshold {threshold:,.0f}")
print(f"  99th MDD:   {np.percentile(mdds, 99):>10,.0f}")
print(f"  Ruin prob:  {ruin_count/10000*100:.2f}%")
status = "PASS" if p95 < threshold else "FAIL"
print(f"\n  Phase 3 (WF-optimized): {status}")
