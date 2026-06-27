"""WFA Loop Runner — production-grade WFA analyzer for any strategy.

Usage:
    python scripts/wfa_loop_runner.py --strategy S3_S --xlsx-dir "C:/Users/User/Downloads"
    python scripts/wfa_loop_runner.py --strategy S4_L --windows 9

Exit codes:
    0 = WFA PASS (>=5/9 + median WFE>50% + total OOS>0)
    1 = WFA FAIL
    2 = data missing / setup error

Output:
    - Console summary table
    - JSON to scripts/results/wfa_<strategy>_<timestamp>.json
    - Per-window IS/OOS metrics
    - Pass/fail verdict per institutional gates
"""
import argparse, json, os, sys, io, glob
from collections import defaultdict
from datetime import datetime
from statistics import mean, median, stdev
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_metrics(path):
    """Extract perf metrics from MC12 xlsx 策略分析 sheet."""
    if not os.path.exists(path):
        return None
    wb = load_workbook(path, data_only=True)
    out = {}
    label_map = {
        '淨利': 'net', '毛利': 'gross_profit', '毛損': 'gross_loss',
        '獲利因子': 'pf', '調整獲利因子': 'adj_pf', '滑價支付': 'slippage',
        '交易總次數': 'n', '%勝率': 'wr', '年度夏普比率': 'sharpe',
        '索丁諾比率': 'sortino', '最大策略虧損': 'mdd_abs',
        '最大策略虧損 (%)': 'mdd_pct', '年報酬率': 'ann_ret',
    }
    ws = wb['策略分析']
    for row in ws.iter_rows(min_row=1, max_row=100, values_only=True):
        if not row[0]: continue
        label = str(row[0]).strip()
        if label in label_map:
            out[label_map[label]] = row[1]
    # Dates from 設定
    if '設定' in wb.sheetnames:
        ws = wb['設定']
        for row in ws.iter_rows(values_only=True):
            if row[0] == '開始日期':
                out['start'] = row[1].date() if hasattr(row[1], 'date') else row[1]
            elif row[0] == '結束日期':
                out['end'] = row[1].date() if hasattr(row[1], 'date') else row[1]
    return out


def gate_check(is_d, oos_d, gate_wfe=50, gate_oos_pf=1.0):
    """Per-window 3 gates check. Returns (pass, dict of gate results)."""
    is_pf = (is_d.get('pf') or 0) if is_d else 0
    oos_pf = (oos_d.get('pf') or 0) if oos_d else 0
    oos_sh = (oos_d.get('sharpe') or 0) if oos_d else 0
    wfe = (oos_pf / is_pf * 100) if is_pf > 0 else 0
    g1 = wfe > gate_wfe
    g2 = isinstance(oos_pf, (int, float)) and oos_pf > gate_oos_pf
    g3 = isinstance(oos_sh, (int, float)) and oos_sh > 0
    return (g1 and g2 and g3), {'wfe': wfe, 'oos_pf': oos_pf, 'oos_sh': oos_sh,
                                 'g1_wfe': g1, 'g2_pf': g2, 'g3_sh': g3}


def main():
    p = argparse.ArgumentParser(description='WFA Loop Runner')
    p.add_argument('--strategy', required=True, help='Strategy name (e.g. S3_S / S4_L)')
    p.add_argument('--xlsx-dir', default=r'C:\Users\User\Downloads',
                   help='Folder containing IS/OOS xlsx files')
    p.add_argument('--prefix', default='TXF1  VolSqueezeShort 策略回測績效報告',
                   help='xlsx filename prefix (before _ISWn / _OOSWn)')
    p.add_argument('--windows', type=int, default=9, help='# of WFA windows (default 9)')
    p.add_argument('--gate-min-pass', type=int, default=5, help='Min windows pass (default 5)')
    p.add_argument('--gate-median-wfe', type=float, default=50, help='Min median WFE % (default 50)')
    p.add_argument('--json-out', default=None, help='Output JSON path (default auto)')
    args = p.parse_args()

    results = []
    missing = []
    for w in range(1, args.windows + 1):
        is_path = os.path.join(args.xlsx_dir, f'{args.prefix}_ISW{w}.xlsx')
        oos_path = os.path.join(args.xlsx_dir, f'{args.prefix}_OOSW{w}.xlsx')
        is_d = extract_metrics(is_path)
        oos_d = extract_metrics(oos_path)
        if is_d is None: missing.append(is_path)
        if oos_d is None: missing.append(oos_path)
        passed, gates = gate_check(is_d, oos_d)
        results.append({'window': w, 'is': is_d, 'oos': oos_d,
                       'passed': passed, 'gates': gates})

    if missing:
        print(f'[ERROR] Missing {len(missing)} files:', file=sys.stderr)
        for m in missing[:5]:
            print(f'  {m}', file=sys.stderr)
        sys.exit(2)

    # Stats
    wfe_list = [r['gates']['wfe'] for r in results]
    oos_pf_list = [r['gates']['oos_pf'] for r in results]
    oos_sh_list = [r['gates']['oos_sh'] for r in results]
    oos_net_list = [(r['oos'].get('net') or 0) for r in results]
    n_pass = sum(1 for r in results if r['passed'])
    median_wfe = median(wfe_list)
    mean_wfe = mean(wfe_list)
    mean_oos_pf = mean(oos_pf_list)
    total_oos_net = sum(oos_net_list)

    # Console summary
    print('=' * 80)
    print(f'WFA Loop Runner — {args.strategy}')
    print(f'Windows: {args.windows} | Gate: >= {args.gate_min_pass}/{args.windows} pass')
    print('=' * 80)
    print(f'{"W":<3} {"IS PF":>6} {"OOS PF":>7} {"WFE":>7} {"OOS Sh":>7} {"OOS Net":>11} Status')
    print('-' * 80)
    for r in results:
        is_pf = (r['is'].get('pf') or 0)
        oos_pf = r['gates']['oos_pf']
        wfe = r['gates']['wfe']
        oos_sh = r['gates']['oos_sh']
        oos_net = r['oos'].get('net') or 0
        fail_codes = ''
        if not r['gates']['g1_wfe']: fail_codes += 'W'
        if not r['gates']['g2_pf']: fail_codes += 'P'
        if not r['gates']['g3_sh']: fail_codes += 'S'
        status = 'PASS' if r['passed'] else f'FAIL ({fail_codes})'
        print(f'W{r["window"]:<2} {is_pf:>6.2f} {oos_pf:>7.2f} {wfe:>+6.1f}% '
              f'{oos_sh:>+7.2f} {oos_net:>+11,.0f}  {status}')

    print()
    print('=' * 80)
    print('VERDICT vs Institutional Gates')
    print('=' * 80)
    pass_5 = n_pass >= args.gate_min_pass
    pass_wfe = median_wfe > args.gate_median_wfe
    pass_oos_pf = mean_oos_pf > 1.0
    pass_oos_net = total_oos_net > 0
    overall_pass = pass_5 and pass_wfe and pass_oos_pf and pass_oos_net

    print(f'  Windows pass >= {args.gate_min_pass}/{args.windows}:  {n_pass}/{args.windows}  {"PASS" if pass_5 else "FAIL"}')
    print(f'  Median WFE > {args.gate_median_wfe}%:        {median_wfe:+.1f}%  {"PASS" if pass_wfe else "FAIL"}')
    print(f'  Mean OOS PF > 1.0:           {mean_oos_pf:+.2f}  {"PASS" if pass_oos_pf else "FAIL"}')
    print(f'  Total OOS Net > 0:           {total_oos_net:+,.0f}  {"PASS" if pass_oos_net else "FAIL"}')
    print()
    print(f'  OVERALL:  {"PASS - promote-eligible" if overall_pass else "FAIL - KILL or iterate"}')

    # JSON output
    out = {
        'strategy': args.strategy, 'timestamp': datetime.now().isoformat(timespec='seconds'),
        'windows': args.windows, 'gates_min_pass': args.gate_min_pass,
        'summary': {
            'windows_passed': n_pass, 'median_wfe': median_wfe, 'mean_wfe': mean_wfe,
            'mean_oos_pf': mean_oos_pf, 'total_oos_net': total_oos_net,
            'overall_pass': overall_pass,
        },
        'per_window': [{
            'w': r['window'],
            'is_pf': r['is'].get('pf'), 'oos_pf': r['gates']['oos_pf'],
            'wfe': r['gates']['wfe'], 'oos_sh': r['gates']['oos_sh'],
            'oos_net': r['oos'].get('net'), 'passed': r['passed'],
        } for r in results]
    }
    out_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = args.json_out or os.path.join(out_dir, f'wfa_{args.strategy}_{ts}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, default=str, indent=2, ensure_ascii=False)
    print(f'\nJSON saved: {out_path}')

    sys.exit(0 if overall_pass else 1)


if __name__ == '__main__':
    main()
