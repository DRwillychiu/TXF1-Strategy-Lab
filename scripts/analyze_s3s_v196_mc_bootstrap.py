"""
S3_S v1.9.6-ANTIHUNT Config B + OPT — MC + Bootstrap Non-WFA Validation
Date: 2026-07-06
Baseline: v1.9.5 (68T / +513.4K / PF 1.574 / MDD -19.05% / MC95 -30.64% FAIL boundary)
Expected: v1.9.6 Config B + OPT (70T / +770.8K / PF 1.823 / MDD -16.02%)
Gates:
    - MC 95% MDD < 30% (v1.9.5 boundary FAIL)
    - Bootstrap P(Net>0) > 60% (v1.9.5 89.3% PASS)
    - Bootstrap P(PF>1) > 60% (v1.9.5 89.3% PASS)
    - Trade Concentration HHI < 0.25
    - Remove Top 3 still profitable
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
from openpyxl import load_workbook
from collections import defaultdict

PATH = r'C:/Users/User/Downloads/TXF1  VolSqueezeShort_v196_ANTIHUNT 策略回測績效報告OPT.xlsx'
ACCOUNT = 1_000_000
N_MC = 10_000
N_BOOT = 10_000
SEED = 20260706

np.random.seed(SEED)

# =============================================================================
# 1. Load xlsx
# =============================================================================
wb = load_workbook(PATH, data_only=True)


def num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.replace(',', '').strip())
        except Exception:
            return 0.0
    return 0.0


# ---- Strategy analysis metrics ----
lm = {
    '淨利': 'net', '獲利因子': 'pf', '調整獲利因子': 'apf',
    '交易總次數': 'n', '%勝率': 'wr', '年度夏普比率': 'sharpe',
    '索丁諾比率': 'sortino', '最大策略虧損 (%)': 'mddp',
    '最大策略虧損': 'mdd', '平均交易淨利': 'avg',
    '最大獲利交易': 'maxW_t', '最大虧損交易': 'maxL_t',
    '獲利交易總次數': 'winN', '虧損交易總次數': 'lossN',
    '平均獲利交易': 'avgW', '平均虧損交易': 'avgL',
    '復原因子': 'recovery',
}
metrics = {}
for r in wb['策略分析'].iter_rows(min_row=1, max_row=200, values_only=True):
    if not r[0]:
        continue
    label = str(r[0]).strip()
    if label in lm:
        metrics[lm[label]] = num(r[1])

# ---- Inputs verification ----
inputs = {}
for r in wb['設定'].iter_rows(values_only=True):
    if r[0] and r[1] is not None:
        inputs[str(r[0]).strip()] = r[1]

# ---- Parse trades ----
ws = wb['交易明細']
trades = []
current = None
for r in ws.iter_rows(min_row=4, values_only=True):
    if not r or not r[3]:
        continue
    sig = str(r[3])
    date_v = r[4]
    time_v = r[5]
    pnl_v = r[8]
    max_favor = r[12] if len(r) > 12 else None
    max_adverse = r[14] if len(r) > 14 else None

    if 'SE_' in sig:
        d = date_v.date() if hasattr(date_v, 'date') else date_v
        t = time_v if hasattr(time_v, 'hour') else None
        pnl = pnl_v if isinstance(pnl_v, (int, float)) else 0
        current = {
            'ed': d, 'et': t,
            'pnl': pnl,
            'max_favor': max_favor if isinstance(max_favor, (int, float)) else 0,
            'max_adverse': max_adverse if isinstance(max_adverse, (int, float)) else 0,
        }
    elif 'SX_' in sig and current is not None:
        trades.append({**current, 'sig': sig})
        current = None

pnl_arr = np.array([t['pnl'] for t in trades])
n_trades = len(trades)

print('=' * 100)
print('S3_S v1.9.6-ANTIHUNT Config B + OPT — MC + Bootstrap Analysis')
print('=' * 100)
print()
print('[Baseline Metrics from xlsx]')
print(f'  Net Profit:      {metrics.get("net", 0):+13,.0f}')
print(f'  PF:              {metrics.get("pf", 0):8.3f}')
print(f'  PF adj:          {metrics.get("apf", 0):8.3f}')
print(f'  Sharpe:          {metrics.get("sharpe", 0):+8.3f}')
print(f'  MDD %:           {metrics.get("mddp", 0):+8.2f}')
print(f'  MDD $:           {metrics.get("mdd", 0):+13,.0f}')
print(f'  Trades (xlsx):   {int(metrics.get("n", 0)):8d}')
print(f'  Trades parsed:   {n_trades:8d}')
print(f'  WR %:            {metrics.get("wr", 0):8.2f} ({int(metrics.get("winN", 0))}W/{int(metrics.get("lossN", 0))}L)')
print(f'  Avg trade:       {metrics.get("avg", 0):+13,.2f}')
print(f'  Max Win:         {metrics.get("maxW_t", 0):+13,.0f}')
print(f'  Max Loss:        {metrics.get("maxL_t", 0):+13,.0f}')

# =============================================================================
# 2. Verify key inputs (Config B + OPT)
# =============================================================================
print()
print('[Config B + OPT Verification]')
verify_list = {
    'BWPctile': 40, 'StopATRMult': 3.25, 'SP_Trigger_ATRMult': 2.0,
    'Hunt_Max_Stops': 4, 'ML_ScoreTrigger': 35,
    'BWRank_EqualGuard_On': True, 'NightSL_Widen_On': False,
    'ConfirmSL_On': False, 'SP_Night_VolConfirm_On': False,
    'MidExit_ConfirmBars': 1, 'MidExit_PeakMinATR': 0, 'SP_Peak_Min_Pts': 0,
}
verify_ok = True
for k, v in verify_list.items():
    val = inputs.get(k, 'N/A')
    matches = str(val).lower() == str(v).lower()
    marker = 'OK  ' if matches else 'MISMATCH'
    if not matches:
        verify_ok = False
    print(f'  [{marker}] {k:<26} expected={v}   actual={val}')
print(f'  Config B + OPT alignment: {"PASS" if verify_ok else "FAIL"}')


# =============================================================================
# 3. Monte Carlo Simulation (10,000 shuffles)
# =============================================================================
def mdd_of_equity(equity):
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    return dd.max()


print()
print('=' * 100)
print(f'[1] MONTE CARLO SIMULATION ({N_MC:,} shuffles)')
print('=' * 100)

mc_mdd_pcts = []
mc_bankrupt = 0
for _ in range(N_MC):
    perm = np.random.permutation(pnl_arr)
    equity = ACCOUNT + np.cumsum(perm)
    dd = mdd_of_equity(equity)
    peak = np.maximum.accumulate(equity).max()
    mdd_pct = dd / peak * 100 if peak > 0 else 0
    mc_mdd_pcts.append(mdd_pct)
    if equity.min() < ACCOUNT * 0.5:
        mc_bankrupt += 1

mc_mdd_pcts = np.array(mc_mdd_pcts)
pcts = [1, 5, 10, 25, 50, 75, 95]
print('MDD Distribution (percentile of worst DD %):')
for p in pcts:
    print(f'  {p:3d}% percentile: -{np.percentile(mc_mdd_pcts, 100-p):6.2f}%')
mc_95 = np.percentile(mc_mdd_pcts, 95)
bankrupt_rate = mc_bankrupt / N_MC * 100

print()
print(f'MC 95% MDD:            -{mc_95:.2f}%')
print(f'MC 99% MDD (worst):    -{np.percentile(mc_mdd_pcts, 99):.2f}%')
print(f'Bankruptcy rate:        {bankrupt_rate:.3f}%  ({mc_bankrupt}/{N_MC})')

gate_mc_95 = 'PASS' if mc_95 < 30.0 else 'FAIL'
print(f'>>> Gate MC 95% MDD < 30%:  {gate_mc_95}')

# =============================================================================
# 4. Bootstrap Resampling (10,000 samples with replacement)
# =============================================================================
print()
print('=' * 100)
print(f'[2] BOOTSTRAP RESAMPLING ({N_BOOT:,} samples)')
print('=' * 100)

boot_net, boot_pf, boot_mdd_pct = [], [], []
for _ in range(N_BOOT):
    sample = np.random.choice(pnl_arr, size=n_trades, replace=True)
    net = sample.sum()
    wins = sample[sample > 0].sum()
    losses = -sample[sample < 0].sum()
    pf = wins / losses if losses > 0 else (99.0 if wins > 0 else 1.0)
    equity = ACCOUNT + np.cumsum(sample)
    peak = np.maximum.accumulate(equity).max()
    mdd = mdd_of_equity(equity)
    mdd_pct = mdd / peak * 100 if peak > 0 else 0
    boot_net.append(net)
    boot_pf.append(pf)
    boot_mdd_pct.append(mdd_pct)

boot_net = np.array(boot_net)
boot_pf = np.array(boot_pf)
boot_mdd_pct = np.array(boot_mdd_pct)

p_net_pos = (boot_net > 0).mean() * 100
p_pf_gt1 = (boot_pf > 1).mean() * 100

print('Confidence intervals:')
print(f'  Net Profit    2.5% = {np.percentile(boot_net, 2.5):+13,.0f}  '
      f'50% = {np.percentile(boot_net, 50):+13,.0f}  '
      f'97.5% = {np.percentile(boot_net, 97.5):+13,.0f}')
print(f'  PF            2.5% = {np.percentile(boot_pf, 2.5):8.3f}       '
      f'50% = {np.percentile(boot_pf, 50):8.3f}       '
      f'97.5% = {np.percentile(boot_pf, 97.5):8.3f}')
print(f'  MDD %         2.5% = -{np.percentile(boot_mdd_pct, 2.5):6.2f}%       '
      f'50% = -{np.percentile(boot_mdd_pct, 50):6.2f}%       '
      f'97.5% = -{np.percentile(boot_mdd_pct, 97.5):6.2f}%')
print()
print(f'P(Net > 0)  =  {p_net_pos:5.1f}%')
print(f'P(PF > 1.0) =  {p_pf_gt1:5.1f}%')
gate_p_net = 'PASS' if p_net_pos > 60 else 'FAIL'
gate_p_pf = 'PASS' if p_pf_gt1 > 60 else 'FAIL'
print(f'>>> Gate P(Net > 0)  > 60%:  {gate_p_net}')
print(f'>>> Gate P(PF > 1.0) > 60%:  {gate_p_pf}')

# =============================================================================
# 5. Trade Concentration Analysis
# =============================================================================
print()
print('=' * 100)
print('[3] TRADE CONCENTRATION ANALYSIS')
print('=' * 100)

trades_sorted = sorted(trades, key=lambda t: -t['pnl'])
top5_win = trades_sorted[:5]
top5_loss = sorted(trades, key=lambda t: t['pnl'])[:5]

net_total = pnl_arr.sum()

print()
print('Top 5 Wins:')
for i, t in enumerate(top5_win, 1):
    pct = t['pnl'] / net_total * 100 if net_total > 0 else 0
    print(f'  #{i} {t["ed"]} {str(t["et"])[:8]:<8} {t["sig"]:<24} {t["pnl"]:+11,.0f}  ({pct:5.1f}% Net)')

print()
print('Top 5 Losses:')
for i, t in enumerate(top5_loss, 1):
    pct = t['pnl'] / net_total * 100 if net_total > 0 else 0
    print(f'  #{i} {t["ed"]} {str(t["et"])[:8]:<8} {t["sig"]:<24} {t["pnl"]:+11,.0f}  ({pct:5.1f}% Net)')

print()
print('Removal Sensitivity:')
for n in [1, 2, 3, 5]:
    filtered = pnl_arr.copy()
    top_pnls = np.array([t['pnl'] for t in trades_sorted[:n]])
    for tp in top_pnls:
        idx = np.where(filtered == tp)[0]
        if len(idx) > 0:
            filtered = np.delete(filtered, idx[0])
    new_net = filtered.sum()
    wins = filtered[filtered > 0].sum()
    losses = -filtered[filtered < 0].sum()
    new_pf = wins / losses if losses > 0 else 99
    verdict = 'still profitable' if new_net > 0 else 'TURNS NEGATIVE'
    print(f'  Remove top {n}: Net = {new_net:+13,.0f}   PF = {new_pf:5.3f}   [{verdict}]')

# Herfindahl Index (over winning trades)
wins_only = pnl_arr[pnl_arr > 0]
total_wins = wins_only.sum()
if total_wins > 0:
    shares = wins_only / total_wins
    hhi = (shares ** 2).sum()
else:
    hhi = 0
print()
print(f'Herfindahl Index (winning trades): {hhi:.4f}')
gate_hhi = 'PASS' if hhi < 0.25 else 'FAIL'
print(f'>>> Gate HHI < 0.25:  {gate_hhi}  (< 0.10 = diversified, < 0.25 = concentrated OK)')

# Remove top 3 still profitable
top3_pnl = sum(t['pnl'] for t in trades_sorted[:3])
remove_top3_net = net_total - top3_pnl
gate_top3 = 'PASS' if remove_top3_net > 0 else 'FAIL'
print(f'>>> Gate Remove Top 3 still profitable:  {gate_top3}  (Net after = {remove_top3_net:+,.0f})')

# =============================================================================
# 6. Exit Signal Breakdown
# =============================================================================
print()
print('=' * 100)
print('[4] EXIT SIGNAL BREAKDOWN')
print('=' * 100)
es = defaultdict(lambda: {'n': 0, 'pnl': 0, 'wins': 0, 'maxL': 0, 'maxW': 0})
for t in trades:
    s = es[t['sig']]
    s['n'] += 1
    s['pnl'] += t['pnl']
    if t['pnl'] > 0:
        s['wins'] += 1
    if t['pnl'] < s['maxL']:
        s['maxL'] = t['pnl']
    if t['pnl'] > s['maxW']:
        s['maxW'] = t['pnl']

print(f'{"Signal":<24} {"N":>3} {"Total":>13} {"WR%":>5} {"Avg":>11} {"MaxLoss":>11} {"MaxWin":>11}')
print('-' * 100)
for sig in sorted(es.keys(), key=lambda x: -es[x]['pnl']):
    s = es[sig]
    wr = s['wins'] / s['n'] * 100 if s['n'] else 0
    avg = s['pnl'] / s['n'] if s['n'] else 0
    print(f'  {sig:<22} {s["n"]:>3} {s["pnl"]:>+13,.0f} {wr:>4.0f}% {avg:>+11,.0f} {s["maxL"]:>+11,.0f} {s["maxW"]:>+11,.0f}')

# =============================================================================
# 7. Yearly + Regime Analysis
# =============================================================================
print()
print('=' * 100)
print('[5] YEARLY BREAKDOWN')
print('=' * 100)
yr = defaultdict(lambda: {'n': 0, 'pnl': 0, 'wins': 0})
for t in trades:
    y = t['ed'].year if t['ed'] else 0
    yr[y]['n'] += 1
    yr[y]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        yr[y]['wins'] += 1
print(f'{"Year":<6} {"N":>3} {"Wins":>5} {"WR%":>5} {"Net":>13} {"Avg":>11}')
for y in sorted(yr.keys()):
    d = yr[y]
    wr = d['wins'] / d['n'] * 100 if d['n'] else 0
    avg = d['pnl'] / d['n'] if d['n'] else 0
    print(f'  {y:<4} {d["n"]:>3} {d["wins"]:>5} {wr:>4.0f}% {d["pnl"]:>+13,.0f} {avg:>+11,.0f}')

# =============================================================================
# 8. Monthly P&L
# =============================================================================
print()
print('=' * 100)
print('[6] MONTHLY P&L (Active months)')
print('=' * 100)
mo = defaultdict(lambda: {'n': 0, 'pnl': 0, 'wins': 0})
for t in trades:
    key = f'{t["ed"].year}-{t["ed"].month:02d}'
    mo[key]['n'] += 1
    mo[key]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        mo[key]['wins'] += 1

active = len(mo)
positive_mo = sum(1 for d in mo.values() if d['pnl'] > 0)
negative_mo = active - positive_mo

print(f'Active months: {active}')
print(f'Positive months: {positive_mo} ({positive_mo/active*100:.1f}%)')
print(f'Negative months: {negative_mo} ({negative_mo/active*100:.1f}%)')
print()
top3 = sorted(mo.items(), key=lambda x: -x[1]['pnl'])[:3]
bot3 = sorted(mo.items(), key=lambda x: x[1]['pnl'])[:3]
print('Top 3 months:')
for k, d in top3:
    print(f'  {k}: {d["pnl"]:+13,.0f}   ({d["n"]}T, {d["wins"]}W)')
print('Bottom 3 months:')
for k, d in bot3:
    print(f'  {k}: {d["pnl"]:+13,.0f}   ({d["n"]}T, {d["wins"]}W)')

# =============================================================================
# 9. Summary Verdict
# =============================================================================
print()
print('=' * 100)
print('SUMMARY VERDICT — Rule #18 5-Piece Non-WFA Validation')
print('=' * 100)
gates = [
    ('MC 95% MDD < 30% (account)', f'{mc_95:.2f}%', 30.0, gate_mc_95),
    ('Bootstrap P(Net > 0) > 60%', f'{p_net_pos:.1f}%', 60.0, gate_p_net),
    ('Bootstrap P(PF > 1.0) > 60%', f'{p_pf_gt1:.1f}%', 60.0, gate_p_pf),
    ('Trade Concentration HHI < 0.25', f'{hhi:.4f}', 0.25, gate_hhi),
    ('Remove Top 3 still profitable', f'{remove_top3_net:+,.0f}', 0, gate_top3),
]
pass_n = sum(1 for g in gates if g[3] == 'PASS')
for name, val, tgt, ok in gates:
    print(f'  [{ok}]  {name:<40}  value = {val}')
print()
print(f'>>> TOTAL: {pass_n}/{len(gates)} gates PASS')
print()

if pass_n >= 4:
    print('  >>> STRONG PASS candidate for Stress Testing next.')
elif pass_n >= 3:
    print('  >>> MARGINAL — investigate failing gate before promote.')
else:
    print('  >>> INSUFFICIENT — needs refine before promote.')

# =============================================================================
# 10. Save summary JSON
# =============================================================================
out = {
    'version': 'v1.9.6-ANTIHUNT Config B + OPT',
    'date': '2026-07-06',
    'baseline': {
        'trades': n_trades,
        'net': metrics.get('net', 0),
        'pf': metrics.get('pf', 0),
        'mdd_pct': metrics.get('mddp', 0),
        'mdd': metrics.get('mdd', 0),
        'wr': metrics.get('wr', 0),
        'sharpe': metrics.get('sharpe', 0),
    },
    'mc': {
        'n_shuffles': N_MC,
        'mdd_95pct': float(mc_95),
        'mdd_99pct': float(np.percentile(mc_mdd_pcts, 99)),
        'bankrupt_rate_pct': bankrupt_rate,
        'gate_pass': gate_mc_95 == 'PASS',
    },
    'bootstrap': {
        'n_samples': N_BOOT,
        'p_net_pos_pct': float(p_net_pos),
        'p_pf_gt1_pct': float(p_pf_gt1),
        'net_ci': [float(np.percentile(boot_net, 2.5)), float(np.percentile(boot_net, 50)), float(np.percentile(boot_net, 97.5))],
        'pf_ci': [float(np.percentile(boot_pf, 2.5)), float(np.percentile(boot_pf, 50)), float(np.percentile(boot_pf, 97.5))],
        'mdd_ci': [float(np.percentile(boot_mdd_pct, 2.5)), float(np.percentile(boot_mdd_pct, 50)), float(np.percentile(boot_mdd_pct, 97.5))],
    },
    'concentration': {
        'hhi_winners': float(hhi),
        'remove_top3_net': float(remove_top3_net),
        'top3_share_pct': float(top3_pnl / net_total * 100) if net_total > 0 else 0,
    },
    'gates': {
        'mc_95_mdd': gate_mc_95,
        'boot_p_net': gate_p_net,
        'boot_p_pf': gate_p_pf,
        'hhi': gate_hhi,
        'remove_top3': gate_top3,
        'pass_n': pass_n,
        'total': len(gates),
    },
    'inputs_verified': verify_ok,
}
OUT_JSON = r'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop/9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f/scratchpad/mc_bootstrap_v196_opt_result.json'
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\n[Result JSON saved to {OUT_JSON}]')
