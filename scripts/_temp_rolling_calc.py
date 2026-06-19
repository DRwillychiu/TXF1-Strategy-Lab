"""Compute rolling-window PF and Sharpe statistics per strategy."""
import json
import math
import pickle
from datetime import datetime, timedelta


def daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def profit_factor(pnls):
    gains = sum(p for p in pnls if p > 0)
    losses = -sum(p for p in pnls if p < 0)
    if losses == 0:
        return float('inf') if gains > 0 else float('nan')
    return gains / losses


def annualized_sharpe(daily_pnls):
    # Use trade-day-only series (non-zero PnL days) for Sharpe with sqrt(252) annualization
    arr = [p for p in daily_pnls if p != 0]
    if len(arr) < 2:
        return float('nan')
    m = sum(arr) / len(arr)
    var = sum((x - m) ** 2 for x in arr) / (len(arr) - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return float('nan')
    return (m / sd) * math.sqrt(252)


def safe_std(values):
    vals = [v for v in values if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))]
    if len(vals) < 2:
        return float('nan')
    m = sum(vals) / len(vals)
    var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
    return math.sqrt(var)


def safe_mean(values):
    vals = [v for v in values if v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))]
    if not vals:
        return float('nan')
    return sum(vals) / len(vals)


def main():
    data = json.load(open('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json'))
    results = {}

    for strat, pnl_dict in data.items():
        items = sorted([(datetime.strptime(k, '%Y-%m-%d').date(), float(v)) for k, v in pnl_dict.items()])
        first_date = items[0][0]
        last_date = items[-1][0]
        pnl_map = {d: p for d, p in items}

        full_dates = list(daterange(first_date, last_date))
        full_pnls = [pnl_map.get(d, 0.0) for d in full_dates]
        total_days = len(full_dates)

        rolling = {}
        for window in [180, 360, 720]:
            if total_days < window:
                rolling[window] = {
                    'pfs': [], 'sharpes': [], 'dates': [],
                    'pf_mean': float('nan'), 'pf_std': float('nan'),
                    'sharpe_mean': float('nan'), 'sharpe_std': float('nan'),
                    'fail_rate_pct': float('nan'),
                    'min_pf': float('nan'), 'max_pf': float('nan'),
                    'min_sharpe': float('nan'), 'max_sharpe': float('nan'),
                    'n_windows': 0,
                }
                continue

            pfs, sharpes, dates_end = [], [], []
            for end_i in range(window - 1, total_days):
                start_i = end_i - window + 1
                wp = full_pnls[start_i:end_i + 1]
                pfs.append(profit_factor(wp))
                sharpes.append(annualized_sharpe(wp))
                dates_end.append(full_dates[end_i])

            fail_count = sum(1 for p in pfs if (not math.isnan(p)) and p < 1.0)
            fail_rate = 100.0 * fail_count / len(pfs)

            rolling[window] = {
                'pfs': pfs,
                'sharpes': sharpes,
                'dates': dates_end,
                'pf_mean': safe_mean(pfs),
                'pf_std': safe_std(pfs),
                'sharpe_mean': safe_mean(sharpes),
                'sharpe_std': safe_std(sharpes),
                'fail_rate_pct': fail_rate,
                'min_pf': min(pfs),
                'max_pf': max(pfs),
                'min_sharpe': min(sharpes),
                'max_sharpe': max(sharpes),
                'n_windows': len(pfs),
            }

        pf360_mean = rolling[360]['pf_mean']
        pf360_std = rolling[360]['pf_std']
        sh360_mean = rolling[360]['sharpe_mean']
        sh360_std = rolling[360]['sharpe_std']

        pf_instab = float('nan')
        if not math.isnan(pf360_mean) and not math.isnan(pf360_std) and pf360_mean != 0:
            pf_instab = pf360_std / pf360_mean

        sh_instab = float('nan')
        if not math.isnan(sh360_mean) and not math.isnan(sh360_std) and sh360_mean != 0:
            sh_instab = sh360_std / abs(sh360_mean)

        any_720_fail = False
        worst_720_pf = float('nan')
        worst_720_date = None
        if rolling[720]['pfs']:
            worst_720_pf = min(rolling[720]['pfs'])
            idx = rolling[720]['pfs'].index(worst_720_pf)
            worst_720_date = rolling[720]['dates'][idx]
            any_720_fail = worst_720_pf < 1.0

        flags = []
        fr = rolling[360]['fail_rate_pct']
        if not math.isnan(fr) and fr > 30:
            flags.append('failure_rate_high')
        if not math.isnan(pf_instab) and pf_instab > 0.5:
            flags.append('pf_instability_high')
        if any_720_fail:
            flags.append('720d_pf_below_1')

        if not flags:
            verdict = 'STABLE'
        elif '720d_pf_below_1' in flags or len(flags) >= 2:
            verdict = 'UNSTABLE'
        else:
            verdict = 'WATCH'

        results[strat] = {
            'first_date': first_date.isoformat(),
            'last_date': last_date.isoformat(),
            'n_trade_days': len(items),
            'total_calendar_days': total_days,
            'rolling': rolling,
            'pf_instability': pf_instab,
            'sharpe_instability': sh_instab,
            'any_720_fail': any_720_fail,
            'worst_720_pf': worst_720_pf,
            'worst_720_date': worst_720_date.isoformat() if worst_720_date else None,
            'flags': flags,
            'verdict': verdict,
        }

    with open('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_rolling_cache.pkl', 'wb') as f:
        pickle.dump(results, f)

    print('Strategies:', list(results.keys()))
    for s, r in results.items():
        print()
        print('---', s, '(', r['verdict'], ')', '---')
        print('  trade_days', r['n_trade_days'], 'cal_days', r['total_calendar_days'])
        for w in [180, 360, 720]:
            rw = r['rolling'][w]
            if rw['n_windows'] == 0:
                print('  win', w, ': insufficient data')
                continue
            print('  win', w, 'n=', rw['n_windows'],
                  'PFmean=', round(rw['pf_mean'], 3),
                  'PFstd=', round(rw['pf_std'], 3),
                  'PFmin=', round(rw['min_pf'], 3),
                  'PFmax=', round(rw['max_pf'], 3),
                  'fail%=', round(rw['fail_rate_pct'], 1),
                  'Shmean=', round(rw['sharpe_mean'], 3),
                  'Shstd=', round(rw['sharpe_std'], 3))
        print('  PF instability=', round(r['pf_instability'], 3) if not math.isnan(r['pf_instability']) else 'nan')
        print('  Sh instability=', round(r['sharpe_instability'], 3) if not math.isnan(r['sharpe_instability']) else 'nan')
        print('  any_720_fail=', r['any_720_fail'], 'worst720pf=', round(r['worst_720_pf'], 3) if not math.isnan(r['worst_720_pf']) else 'nan', 'date=', r['worst_720_date'])
        print('  flags=', r['flags'])


if __name__ == '__main__':
    main()
