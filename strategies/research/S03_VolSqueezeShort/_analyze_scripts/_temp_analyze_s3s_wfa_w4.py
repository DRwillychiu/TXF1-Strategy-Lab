"""S3_S W4 WFA — 9 windows IS/OOS comprehensive analysis."""
import sys, io, os
from openpyxl import load_workbook
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = r'C:\Users\User\Downloads'
prefix = 'TXF1  VolSqueezeShort 策略回測績效報告'

def extract(path):
    if not os.path.exists(path):
        return None
    wb = load_workbook(path, data_only=True)
    out = {}
    ws = wb['策略分析']
    for row in ws.iter_rows(min_row=1, max_row=100, values_only=True):
        if not row[0]: continue
        label = str(row[0]).strip()
        m = {'淨利':'net','獲利因子':'pf','調整獲利因子':'adj_pf','滑價支付':'slip',
             '交易總次數':'n','%勝率':'wr','年度夏普比率':'sharpe',
             '索丁諾比率':'sortino','最大策略虧損':'mdd_abs','最大策略虧損 (%)':'mdd_pct',
             '年報酬率':'ann_ret','毛利':'gross_profit','毛損':'gross_loss'}
        if label in m:
            out[m[label]] = row[1]
    # Dates from 設定
    ws = wb['設定']
    for row in ws.iter_rows(values_only=True):
        if row[0] == '開始日期':
            out['start'] = row[1].date() if hasattr(row[1], 'date') else row[1]
        elif row[0] == '結束日期':
            out['end'] = row[1].date() if hasattr(row[1], 'date') else row[1]
    return out

results = []
for w in range(1, 10):
    is_path = f'{BASE}\\{prefix}_ISW{w}.xlsx'
    oos_path = f'{BASE}\\{prefix}_OOSW{w}.xlsx'
    is_d = extract(is_path)
    oos_d = extract(oos_path)
    results.append({'w': w, 'is': is_d, 'oos': oos_d})

# Full table
print('='*120)
print(f'{"W":<3} {"IS Period":<24} {"IS N":>5} {"IS PF":>6} {"IS Sh":>6} {"IS Net":>10} {"IS MDD%":>8}  '
      f'{"OOS Period":<24} {"OOS N":>5} {"OOS PF":>6} {"OOS Sh":>6} {"OOS Net":>10} {"OOS MDD%":>9} {"WFE":>7}')
print('='*120)

def fmt_date(d):
    if d is None: return '?'
    return str(d)[:10]

wfe_list = []
oos_pf_list = []
oos_sharpe_list = []
oos_net_list = []
oos_mdd_list = []
gate_passes = []

for r in results:
    is_d, oos_d = r['is'], r['oos']
    if not is_d or not oos_d:
        print(f'W{r["w"]:<2} MISSING FILE')
        continue
    is_period = f'{fmt_date(is_d.get("start"))}~{fmt_date(is_d.get("end"))[5:]}'
    oos_period = f'{fmt_date(oos_d.get("start"))}~{fmt_date(oos_d.get("end"))[5:]}'

    is_pf = is_d.get('pf', 0) or 0
    oos_pf = oos_d.get('pf', 0) or 0
    is_sh = is_d.get('sharpe', 0) or 0
    oos_sh = oos_d.get('sharpe', 0) or 0
    is_n = is_d.get('n', 0) or 0
    oos_n = oos_d.get('n', 0) or 0
    is_net = is_d.get('net', 0) or 0
    oos_net = oos_d.get('net', 0) or 0
    is_mdd = is_d.get('mdd_pct', 0) or 0
    oos_mdd = oos_d.get('mdd_pct', 0) or 0

    wfe = (oos_pf / is_pf * 100) if is_pf > 0 else 0
    wfe_list.append(wfe)
    oos_pf_list.append(oos_pf if isinstance(oos_pf, (int, float)) else 0)
    oos_sharpe_list.append(oos_sh if isinstance(oos_sh, (int, float)) else 0)
    oos_net_list.append(oos_net if isinstance(oos_net, (int, float)) else 0)
    oos_mdd_list.append(oos_mdd if isinstance(oos_mdd, (int, float)) else 0)

    g1 = wfe > 50
    g2 = isinstance(oos_pf, (int, float)) and oos_pf > 1.0
    g3 = isinstance(oos_sh, (int, float)) and oos_sh > 0
    all_pass = g1 and g2 and g3
    gate_passes.append(all_pass)

    print(f'W{r["w"]:<2} {is_period:<24} {is_n:>5} {is_pf:>6.2f} {is_sh:>6.2f} {is_net:>+10,.0f} {is_mdd:>7.1f}%  '
          f'{oos_period:<24} {oos_n:>5} {oos_pf:>6.2f} {oos_sh:>6.2f} {oos_net:>+10,.0f} {oos_mdd:>8.1f}% {wfe:>6.1f}%')

# Summary
print()
print('='*80)
print('SUMMARY STATISTICS')
print('='*80)
from statistics import mean, median, stdev
n_total = len([r for r in results if r['is'] and r['oos']])
n_pass = sum(gate_passes)
print(f'Windows analyzed:        {n_total}')
print(f'Windows passing 3 gates: {n_pass}/{n_total} = {n_pass/n_total*100:.1f}%')
print(f'  (Gates: WFE>50% AND OOS PF>1.0 AND OOS Sharpe>0)')
print()
print(f'WFE Stats:')
print(f'  Mean WFE:    {mean(wfe_list):>+6.1f}%')
print(f'  Median WFE:  {median(wfe_list):>+6.1f}%')
if len(wfe_list) > 1: print(f'  Std WFE:     {stdev(wfe_list):>6.1f}%')
print()
print(f'OOS Stats:')
print(f'  Mean OOS PF:     {mean(oos_pf_list):>+5.2f}')
print(f'  Median OOS PF:   {median(oos_pf_list):>+5.2f}')
print(f'  Mean OOS Sharpe: {mean(oos_sharpe_list):>+5.2f}')
print(f'  Total OOS Net:   {sum(oos_net_list):>+,.0f}')
print(f'  Mean OOS MDD:    {mean(oos_mdd_list):>+5.1f}%')
oos_pf_pos = sum(1 for p in oos_pf_list if p > 1.0)
oos_sh_pos = sum(1 for s in oos_sharpe_list if s > 0)
oos_net_pos = sum(1 for n in oos_net_list if n > 0)
print(f'  OOS PF > 1.0:    {oos_pf_pos}/{n_total} ({oos_pf_pos/n_total*100:.0f}%)')
print(f'  OOS Sharpe > 0:  {oos_sh_pos}/{n_total} ({oos_sh_pos/n_total*100:.0f}%)')
print(f'  OOS Net > 0:     {oos_net_pos}/{n_total} ({oos_net_pos/n_total*100:.0f}%)')

# Per-window verdict
print()
print('='*80)
print('PER-WINDOW VERDICT')
print('='*80)
print(f'{"W":<3} {"IS PF":>6} {"OOS PF":>7} {"WFE":>7} {"OOS Sh":>7} {"OOS Net":>11} Status')
print('-' * 80)
for i, r in enumerate(results):
    is_d, oos_d = r['is'], r['oos']
    if not is_d or not oos_d: continue
    is_pf = is_d.get('pf', 0) or 0
    oos_pf = oos_d.get('pf', 0) or 0
    oos_sh = oos_d.get('sharpe', 0) or 0
    oos_net = oos_d.get('net', 0) or 0
    wfe = (oos_pf / is_pf * 100) if is_pf > 0 else 0
    g1 = wfe > 50
    g2 = isinstance(oos_pf, (int, float)) and oos_pf > 1.0
    g3 = isinstance(oos_sh, (int, float)) and oos_sh > 0
    fail = ''
    if not g1: fail += 'W'
    if not g2: fail += 'P'
    if not g3: fail += 'S'
    status = '✅ PASS' if g1 and g2 and g3 else f'❌ FAIL ({fail})'
    print(f'W{r["w"]:<2} {is_pf:>6.2f} {oos_pf:>7.2f} {wfe:>+6.1f}% {oos_sh:>+7.2f} {oos_net:>+11,.0f}  {status}')

# Final verdict
print()
print('='*80)
print('VERDICT vs Institutional Standards')
print('='*80)
print(f'  >= 5/9 windows pass 3 gates:  {n_pass}/9  {"PASS" if n_pass >= 5 else "FAIL"}')
print(f'  Mean WFE > 50%:                {mean(wfe_list):+.1f}%  {"PASS" if mean(wfe_list) > 50 else "FAIL"}')
print(f'  Median WFE > 50%:              {median(wfe_list):+.1f}%  {"PASS" if median(wfe_list) > 50 else "FAIL"}')
print(f'  Mean OOS PF > 1.0:             {mean(oos_pf_list):+.2f}  {"PASS" if mean(oos_pf_list) > 1.0 else "FAIL"}')
print(f'  Total OOS Net > 0:             {sum(oos_net_list):+,.0f}  {"PASS" if sum(oos_net_list) > 0 else "FAIL"}')

# vs v1.5
print()
print('='*80)
print('vs v1.5 (which FAILED)')
print('='*80)
print(f'  v1.5 (10-param GA): 2/9 pass, median WFE -38%, total OOS -762K')
print(f'  v1.6 (4-param GA):  {n_pass}/9 pass, median WFE {median(wfe_list):+.1f}%, total OOS {sum(oos_net_list):+,.0f}')
