"""
[DEPRECATED] S1 NightMomentum — v1.0 日線代理優化 pipeline.
⚠️ 此腳本為 v1.0 固定點數版本的日線代理回測，已被 MC12 15M v2.1 ATR 版本取代。
正式版策略參數與程式碼見：
  - strategies/batch01/S1_NightMomentum.pla (v2.1 GA optimized)
  - optimization/logs/B01_S1_NightMomentum.md (完整優化紀錄)

Phase 1: Parameter sensitivity (plateau detection)
Phase 2: Walk-Forward optimization
Phase 3: Monte Carlo stress test
All on daily TAIEX proxy (^TWII) — 僅供參考，非正式驗證。
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import product

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "twii_daily.csv")

MULTIPLIER = 200
SLIPPAGE = 1000
INITIAL_CAPITAL = 300_000


def load_data():
    df = pd.read_csv(CSV_PATH, index_col=0, parse_dates=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def backtest_s1(df, lookback=4, entry_offset=10, min_range=30, max_range=200,
                stop_pts=60, target_pts=120, trail_activate=50, trail_offset=30):
    """Return list of (pnl, entry_date, exit_date, direction)."""
    atr14 = df['High'] - df['Low']
    atr14_ma = atr14.rolling(14).mean()
    trades = []

    for i in range(max(20, lookback + 14), len(df) - 1):
        range_width = atr14.iloc[i]
        avg_range = atr14_ma.iloc[i]
        if pd.isna(avg_range):
            continue

        narrow = range_width < avg_range * (0.5 + 0.05 * lookback)
        if not narrow:
            continue

        rng = df['High'].iloc[i] - df['Low'].iloc[i]
        if rng < min_range or rng > max_range:
            continue

        prev_h = df['High'].iloc[i]
        prev_l = df['Low'].iloc[i]
        nxt = df.iloc[i + 1]

        # Long breakout
        if nxt['High'] > prev_h + entry_offset and nxt['Close'] > prev_h:
            entry = prev_h + entry_offset
            sl = entry - stop_pts
            tp = entry + target_pts
            if nxt['Low'] <= sl:
                exit_p = sl
            elif nxt['High'] >= tp:
                exit_p = tp
            else:
                exit_p = nxt['Close']
                if trail_activate > 0 and (exit_p - entry) >= trail_activate:
                    trail_stop = entry + trail_activate - trail_offset
                    exit_p = max(exit_p, trail_stop)
            raw_pnl = (exit_p - entry) * MULTIPLIER - SLIPPAGE
            trades.append((raw_pnl, df.index[i + 1], df.index[i + 1], 1))

        # Short breakout
        elif nxt['Low'] < prev_l - entry_offset and nxt['Close'] < prev_l:
            entry = prev_l - entry_offset
            sl = entry + stop_pts
            tp = entry - target_pts
            if nxt['High'] >= sl:
                exit_p = sl
            elif nxt['Low'] <= tp:
                exit_p = tp
            else:
                exit_p = nxt['Close']
                if trail_activate > 0 and (entry - exit_p) >= trail_activate:
                    trail_stop = entry - trail_activate + trail_offset
                    exit_p = min(exit_p, trail_stop)
            raw_pnl = (entry - exit_p) * MULTIPLIER - SLIPPAGE
            trades.append((raw_pnl, df.index[i + 1], df.index[i + 1], -1))

    return trades


def calc_metrics(trades):
    if not trades:
        return {"net_profit": 0, "num_trades": 0, "win_rate": 0, "pf": 0,
                "mdd": 0, "avg_win": 0, "avg_loss": 0, "sharpe": 0, "cagr": 0}
    pnls = np.array([t[0] for t in trades])
    net = pnls.sum()
    n = len(pnls)
    w = (pnls > 0).sum()
    l = (pnls <= 0).sum()
    win_rate = w / n * 100 if n else 0
    gross_win = pnls[pnls > 0].sum() if w else 0
    gross_loss = abs(pnls[pnls <= 0].sum()) if l else 1
    pf = gross_win / gross_loss if gross_loss > 0 else 999
    avg_win = pnls[pnls > 0].mean() if w else 0
    avg_loss = abs(pnls[pnls <= 0].mean()) if l else 0

    eq = np.cumsum(pnls)
    peak = np.maximum.accumulate(eq)
    mdd = (peak - eq).max()

    if n >= 2:
        d0 = pd.Timestamp(trades[0][1])
        d1 = pd.Timestamp(trades[-1][2])
        yrs = max((d1 - d0).days / 365.25, 0.5)
        ann_ret = net / yrs
        std_annual = pnls.std() * np.sqrt(n / yrs) if yrs > 0 else 0
        sharpe = ann_ret / std_annual if std_annual > 0 else 0
        if net > 0:
            cagr = ((INITIAL_CAPITAL + net) / INITIAL_CAPITAL) ** (1 / yrs) - 1
        else:
            cagr = 0
    else:
        sharpe, cagr = 0, 0

    return {"net_profit": int(net), "num_trades": n, "win_rate": round(win_rate, 1),
            "pf": round(pf, 2), "mdd": int(mdd), "avg_win": int(avg_win),
            "avg_loss": int(avg_loss), "sharpe": round(sharpe, 2), "cagr": round(cagr * 100, 1)}


# ── Phase 1: Parameter Sensitivity ──────────────────────────────
def phase1_sensitivity(df):
    print("=" * 70)
    print("Phase 1: Parameter Sensitivity Analysis — S1 NightMomentum")
    print("=" * 70)

    params = {
        "LookbackBars":  {"range": range(2, 11),      "default": {"lookback": None}},
        "EntryOffset":   {"range": range(0, 26, 2),    "default": {"entry_offset": None}},
        "StopLossPts":   {"range": range(30, 121, 10), "default": {"stop_pts": None}},
        "TakeProfitPts": {"range": range(60, 201, 10), "default": {"target_pts": None}},
        "TrailActivate": {"range": range(0, 101, 10),  "default": {"trail_activate": None}},
    }

    param_map = {
        "LookbackBars": "lookback",
        "EntryOffset": "entry_offset",
        "StopLossPts": "stop_pts",
        "TakeProfitPts": "target_pts",
        "TrailActivate": "trail_activate",
    }

    defaults = dict(lookback=4, entry_offset=10, stop_pts=60, target_pts=120,
                    trail_activate=50, trail_offset=30, min_range=30, max_range=200)

    results_all = {}
    plateau_results = {}

    for pname, cfg in params.items():
        key = param_map[pname]
        print(f"\n--- Scanning {pname} ({cfg['range'].start}..{cfg['range'].stop - cfg['range'].step}) ---")
        scan = []
        for val in cfg["range"]:
            kw = dict(defaults)
            kw[key] = val
            trades = backtest_s1(df, **kw)
            m = calc_metrics(trades)
            m["param_value"] = val
            scan.append(m)
            print(f"  {pname}={val:>4}  |  Net={m['net_profit']:>10,}  PF={m['pf']:>5.2f}  "
                  f"Win={m['win_rate']:>5.1f}%  Trades={m['num_trades']:>4}  MDD={m['mdd']:>8,}")
        results_all[pname] = scan

        # Plateau detection
        profits = [s["net_profit"] for s in scan]
        if max(profits) <= 0:
            plateau_results[pname] = {"width_pct": 0, "plateau": False, "best": 0, "note": "all negative"}
            continue
        best = max(profits)
        threshold = best * 0.7
        in_plateau = sum(1 for p in profits if p >= threshold)
        width_pct = round(in_plateau / len(profits) * 100, 1)
        plateau_results[pname] = {
            "width_pct": width_pct,
            "plateau": width_pct >= 20,
            "best": best,
            "best_value": scan[profits.index(best)]["param_value"],
        }
        print(f"  → Plateau width: {width_pct}% ({'✅ PASS' if width_pct >= 20 else '❌ FAIL'}) "
              f" Best={best:,} at {pname}={scan[profits.index(best)]['param_value']}")

    # 2D heatmap: StopLossPts × TakeProfitPts
    print("\n--- 2D Heatmap: StopLossPts × TakeProfitPts ---")
    stop_range = list(range(30, 121, 10))
    target_range = list(range(60, 201, 10))
    heatmap = np.zeros((len(stop_range), len(target_range)))
    for si, sv in enumerate(stop_range):
        for ti, tv in enumerate(target_range):
            kw = dict(defaults)
            kw["stop_pts"] = sv
            kw["target_pts"] = tv
            trades = backtest_s1(df, **kw)
            m = calc_metrics(trades)
            heatmap[si, ti] = m["net_profit"]

    out_dir = os.path.join(BASE_DIR, "results", "s1_optimization")
    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(heatmap, aspect='auto', origin='lower',
                   extent=[target_range[0], target_range[-1], stop_range[0], stop_range[-1]])
    ax.set_xlabel("TakeProfitPts")
    ax.set_ylabel("StopLossPts")
    ax.set_title("S1 NightMomentum — Net Profit Heatmap (Stop × Target)")
    plt.colorbar(im, label="Net Profit (NTD)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "phase1_heatmap_stop_target.png"), dpi=150)
    plt.close()
    print(f"  Heatmap saved → {out_dir}/phase1_heatmap_stop_target.png")

    # Individual param charts
    for pname, scan in results_all.items():
        vals = [s["param_value"] for s in scan]
        profits = [s["net_profit"] for s in scan]
        pfs = [s["pf"] for s in scan]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        ax1.bar(vals, profits, color=["#2196F3" if p > 0 else "#f44336" for p in profits])
        ax1.set_xlabel(pname)
        ax1.set_ylabel("Net Profit (NTD)")
        ax1.set_title(f"{pname} — Net Profit")
        ax1.axhline(0, color='black', linewidth=0.5)
        ax2.plot(vals, pfs, 'o-', color="#4CAF50")
        ax2.set_xlabel(pname)
        ax2.set_ylabel("Profit Factor")
        ax2.set_title(f"{pname} — Profit Factor")
        ax2.axhline(1.0, color='red', linewidth=0.5, linestyle='--')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, f"phase1_{pname}.png"), dpi=150)
        plt.close()

    # Summary
    print("\n" + "=" * 70)
    print("Phase 1 Summary")
    print("=" * 70)
    all_pass = True
    for pname, pr in plateau_results.items():
        status = "✅ PASS" if pr["plateau"] else "❌ FAIL"
        print(f"  {pname:>16}: width={pr['width_pct']:>5.1f}%  {status}")
        if not pr["plateau"]:
            all_pass = False
    print(f"\n  Phase 1 overall: {'✅ ALL PASS' if all_pass else '⚠️ SOME FAIL — review needed'}")

    return results_all, plateau_results


# ── Phase 2: Walk-Forward Optimization ──────────────────────────
def phase2_walkforward(df):
    print("\n" + "=" * 70)
    print("Phase 2: Walk-Forward Optimization — S1 NightMomentum")
    print("=" * 70)

    is_months = 24
    oos_months = 6
    step_months = 6

    param_grid = {
        "lookback": [3, 4, 5, 6],
        "entry_offset": [6, 8, 10, 12, 14],
        "stop_pts": [40, 50, 60, 70, 80],
        "target_pts": [80, 100, 120, 140, 160],
    }
    fixed = dict(trail_activate=50, trail_offset=30, min_range=30, max_range=200)

    start = df.index[0]
    end = df.index[-1]
    total_months = (end.year - start.year) * 12 + (end.month - start.month)

    windows = []
    offset = 0
    while True:
        is_start = start + pd.DateOffset(months=offset)
        is_end = is_start + pd.DateOffset(months=is_months)
        oos_start = is_end
        oos_end = oos_start + pd.DateOffset(months=oos_months)
        if oos_end > end:
            break
        windows.append((is_start, is_end, oos_start, oos_end))
        offset += step_months

    print(f"  Total windows: {len(windows)}")
    print(f"  IS={is_months}m, OOS={oos_months}m, Step={step_months}m")

    wf_results = []
    for wi, (is_s, is_e, oos_s, oos_e) in enumerate(windows):
        df_is = df[(df.index >= is_s) & (df.index < is_e)]
        df_oos = df[(df.index >= oos_s) & (df.index < oos_e)]

        print(f"\n  Window {wi+1}: IS={is_s.strftime('%Y-%m')}~{is_e.strftime('%Y-%m')}  "
              f"OOS={oos_s.strftime('%Y-%m')}~{oos_e.strftime('%Y-%m')}")

        # Grid search on IS
        best_is_profit = -999999
        best_params = None
        keys = list(param_grid.keys())
        combos = list(product(*param_grid.values()))

        for combo in combos:
            kw = dict(fixed)
            for k, v in zip(keys, combo):
                kw[k] = v
            trades = backtest_s1(df_is, **kw)
            m = calc_metrics(trades)
            if m["net_profit"] > best_is_profit and m["num_trades"] >= 5:
                best_is_profit = m["net_profit"]
                best_params = dict(zip(keys, combo))

        if best_params is None:
            print(f"    ⚠️ No valid IS params found (all combos < 5 trades)")
            wf_results.append({"window": wi + 1, "oos_profit": 0, "oos_pf": 0,
                               "is_profit": 0, "best_params": None})
            continue

        # Run best params on OOS
        kw_oos = dict(fixed)
        kw_oos.update(best_params)
        trades_is = backtest_s1(df_is, **kw_oos)
        trades_oos = backtest_s1(df_oos, **kw_oos)
        m_is = calc_metrics(trades_is)
        m_oos = calc_metrics(trades_oos)

        print(f"    Best IS params: {best_params}")
        print(f"    IS:  Net={m_is['net_profit']:>10,}  PF={m_is['pf']:>5.2f}  Trades={m_is['num_trades']}")
        print(f"    OOS: Net={m_oos['net_profit']:>10,}  PF={m_oos['pf']:>5.2f}  Trades={m_oos['num_trades']}")

        wf_results.append({
            "window": wi + 1,
            "is_period": f"{is_s.strftime('%Y-%m')}~{is_e.strftime('%Y-%m')}",
            "oos_period": f"{oos_s.strftime('%Y-%m')}~{oos_e.strftime('%Y-%m')}",
            "best_params": best_params,
            "is_profit": m_is["net_profit"],
            "is_pf": m_is["pf"],
            "is_trades": m_is["num_trades"],
            "oos_profit": m_oos["net_profit"],
            "oos_pf": m_oos["pf"],
            "oos_trades": m_oos["num_trades"],
        })

    # WFE calculation
    oos_positive = sum(1 for r in wf_results if r["oos_profit"] > 0)
    wfe = round(oos_positive / len(wf_results) * 100, 1) if wf_results else 0
    avg_oos_pf = np.mean([r.get("oos_pf", 0) for r in wf_results if r.get("oos_pf", 0) > 0]) if oos_positive else 0

    print(f"\n  Walk-Forward Efficiency: {wfe}% ({'✅ PASS' if wfe >= 50 else '❌ FAIL'})")
    print(f"  Avg OOS Profit Factor: {avg_oos_pf:.2f} ({'✅ PASS' if avg_oos_pf > 1.0 else '❌ FAIL'})")

    # Chart: OOS equity
    oos_profits = [r["oos_profit"] for r in wf_results]
    oos_cum = np.cumsum(oos_profits)
    out_dir = os.path.join(BASE_DIR, "results", "s1_optimization")
    os.makedirs(out_dir, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.bar(range(1, len(oos_profits) + 1), oos_profits,
            color=["#2196F3" if p > 0 else "#f44336" for p in oos_profits])
    ax1.set_xlabel("Window #")
    ax1.set_ylabel("OOS Net Profit (NTD)")
    ax1.set_title(f"S1 Walk-Forward OOS Profit per Window (WFE={wfe}%)")
    ax1.axhline(0, color='black', linewidth=0.5)

    ax2.plot(range(1, len(oos_cum) + 1), oos_cum, 'o-', color="#4CAF50")
    ax2.set_xlabel("Window #")
    ax2.set_ylabel("Cumulative OOS Profit (NTD)")
    ax2.set_title("Cumulative OOS Equity")
    ax2.axhline(0, color='red', linewidth=0.5, linestyle='--')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "phase2_walkforward.png"), dpi=150)
    plt.close()

    return {"wfe": wfe, "avg_oos_pf": round(avg_oos_pf, 2), "windows": wf_results}


# ── Phase 3: Monte Carlo Stress Test ────────────────────────────
def phase3_montecarlo(df, iterations=10000):
    print("\n" + "=" * 70)
    print(f"Phase 3: Monte Carlo Stress Test — S1 NightMomentum ({iterations:,} iterations)")
    print("=" * 70)

    trades = backtest_s1(df)
    if not trades:
        print("  No trades to simulate!")
        return None
    pnls = np.array([t[0] for t in trades])
    n = len(pnls)
    print(f"  Original trades: {n}")
    print(f"  Original net profit: {pnls.sum():,.0f} NTD")

    mdds = np.zeros(iterations)
    final_eq = np.zeros(iterations)
    ruin_count = 0
    ruin_threshold = INITIAL_CAPITAL * 0.5

    rng = np.random.default_rng(42)
    for i in range(iterations):
        shuffled = rng.permutation(pnls)
        eq = np.cumsum(shuffled)
        peak = np.maximum.accumulate(eq)
        dd = peak - eq
        mdds[i] = dd.max()
        final_eq[i] = eq[-1]
        if dd.max() >= ruin_threshold:
            ruin_count += 1

    mdd_mean = mdds.mean()
    mdd_median = np.median(mdds)
    mdd_95 = np.percentile(mdds, 95)
    mdd_99 = np.percentile(mdds, 99)
    ruin_pct = ruin_count / iterations * 100

    mdd_threshold = INITIAL_CAPITAL * 0.30  # 90,000 NTD

    print(f"\n  MDD Distribution:")
    print(f"    Mean:   {mdd_mean:>10,.0f} NTD")
    print(f"    Median: {mdd_median:>10,.0f} NTD")
    print(f"    95th:   {mdd_95:>10,.0f} NTD  ({'✅ PASS' if mdd_95 < mdd_threshold else '❌ FAIL'} vs {mdd_threshold:,.0f})")
    print(f"    99th:   {mdd_99:>10,.0f} NTD")
    print(f"  Ruin probability (50% DD): {ruin_pct:.2f}%  ({'✅ PASS' if ruin_pct < 5 else '❌ FAIL'})")

    out_dir = os.path.join(BASE_DIR, "results", "s1_optimization")
    os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].hist(mdds, bins=80, color="#2196F3", alpha=0.7, edgecolor="white")
    axes[0].axvline(mdd_95, color='red', linestyle='--', label=f'95th: {mdd_95:,.0f}')
    axes[0].axvline(mdd_99, color='darkred', linestyle='--', label=f'99th: {mdd_99:,.0f}')
    axes[0].axvline(mdd_threshold, color='green', linestyle='-', linewidth=2, label=f'Threshold: {mdd_threshold:,.0f}')
    axes[0].set_xlabel("Max Drawdown (NTD)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Monte Carlo MDD Distribution")
    axes[0].legend(fontsize=8)

    axes[1].hist(final_eq, bins=80, color="#4CAF50", alpha=0.7, edgecolor="white")
    axes[1].axvline(0, color='red', linestyle='--')
    axes[1].set_xlabel("Final Equity (NTD)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Monte Carlo Final Equity Distribution")

    sample_idx = rng.choice(iterations, size=min(200, iterations), replace=False)
    for idx in sample_idx:
        shuffled = rng.permutation(pnls)
        eq = np.cumsum(shuffled)
        axes[2].plot(eq, alpha=0.05, color="#2196F3")
    orig_eq = np.cumsum(pnls)
    axes[2].plot(orig_eq, color='red', linewidth=2, label='Original')
    axes[2].set_xlabel("Trade #")
    axes[2].set_ylabel("Equity (NTD)")
    axes[2].set_title("Monte Carlo Equity Curves (200 samples)")
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "phase3_montecarlo.png"), dpi=150)
    plt.close()

    return {
        "iterations": iterations,
        "original_trades": n,
        "original_net": int(pnls.sum()),
        "mdd_mean": int(mdd_mean),
        "mdd_median": int(mdd_median),
        "mdd_95": int(mdd_95),
        "mdd_99": int(mdd_99),
        "ruin_pct": round(ruin_pct, 2),
        "mdd_threshold": int(mdd_threshold),
        "mdd_95_pass": mdd_95 < mdd_threshold,
        "ruin_pass": ruin_pct < 5,
    }


# ── Main ────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_data()
    print(f"Data loaded: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')} ({len(df)} bars)\n")

    p1_results, p1_plateau = phase1_sensitivity(df)
    p2_results = phase2_walkforward(df)
    p3_results = phase3_montecarlo(df, iterations=10000)

    # Save all results
    out_dir = os.path.join(BASE_DIR, "results", "s1_optimization")
    os.makedirs(out_dir, exist_ok=True)

    summary = {
        "strategy": "S1_NightMomentum",
        "data_range": f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
        "phase1_plateau": {k: {kk: vv for kk, vv in v.items()} for k, v in p1_plateau.items()},
        "phase2_walkforward": p2_results,
        "phase3_montecarlo": p3_results,
    }

    with open(os.path.join(out_dir, "s1_optimization_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    print("\n" + "=" * 70)
    print("FINAL SUMMARY — S1 NightMomentum Optimization")
    print("=" * 70)

    p1_pass = all(v["plateau"] for v in p1_plateau.values())
    p2_pass = p2_results["wfe"] >= 50 and p2_results["avg_oos_pf"] > 1.0
    p3_pass = p3_results["mdd_95_pass"] and p3_results["ruin_pass"] if p3_results else False

    print(f"  Phase 1 (Param Sensitivity):  {'✅ PASS' if p1_pass else '❌ FAIL'}")
    for k, v in p1_plateau.items():
        print(f"    {k:>16}: plateau width {v['width_pct']}%")
    print(f"  Phase 2 (Walk-Forward):       {'✅ PASS' if p2_pass else '❌ FAIL'}")
    print(f"    WFE = {p2_results['wfe']}%, Avg OOS PF = {p2_results['avg_oos_pf']}")
    if p3_results:
        print(f"  Phase 3 (Monte Carlo):        {'✅ PASS' if p3_pass else '❌ FAIL'}")
        print(f"    95% MDD = {p3_results['mdd_95']:,} NTD (threshold {p3_results['mdd_threshold']:,})")
        print(f"    Ruin prob = {p3_results['ruin_pct']}%")

    overall = "✅ PASS" if (p1_pass and p2_pass and p3_pass) else "❌ FAIL"
    print(f"\n  OVERALL: {overall}")
    print(f"\n  Results saved to: {out_dir}/")
