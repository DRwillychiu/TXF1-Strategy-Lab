"""Deep comparison of L5 v19.8 variants A-F.

Reads 6 Excel reports from user Downloads, normalizes metrics,
compares SP module effectiveness across variants, and identifies
which variant (if any) wins under the v19.8 acceptance criteria.
"""
import pandas as pd, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict

DL = r'C:\Users\User\Downloads'
files = {
    'A': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告.xlsx',
    'B': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告_B Aggressive.xlsx',
    'C': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告_C Mid.xlsx',
    'D': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告_D Conservative.xlsx',
    'E': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告_E LessRetain.xlsx',
    'F': 'TXF1  STRATEGY_WILLY_LONG_BREAKOUT_C 策略回測績效報告_F L1-Like.xlsx',
}

results = {}
for vname, fn in files.items():
    p = os.path.join(DL, fn)
    sdf = pd.read_excel(p, sheet_name='策略分析', header=None)
    net = pf = mdd = wr = None
    for i in range(len(sdf)):
        row = [str(x) for x in sdf.iloc[i].tolist() if str(x) != 'nan']
        if not row: continue
        if row[0] == '淨利': net = int(float(row[1]))
        elif row[0] == '獲利因子': pf = float(row[1])
        elif row[0] == '最大策略虧損': mdd = int(float(row[1]))
        elif row[0] == '%勝率': wr = float(row[1])

    df = pd.read_excel(p, sheet_name='交易明細', header=2)
    entries = df[df['類型'].astype(str).str.contains('進入', na=False)].copy()
    exits = df[df['類型'].astype(str).str.contains('離開', na=False)].copy()
    trades = []
    for i in range(len(entries)):
        e = entries.iloc[i]
        eord = int(e['委託單編號'])
        x_match = exits[exits['委託單編號'] == eord + 1]
        if len(x_match) == 0: continue
        x = x_match.iloc[0]
        trades.append({
            'i':i+1, 'date':str(e['日期'])[:10], 'time':str(e['時間'])[:5],
            'entry_label':e['訊號'], 'exit_label':x['訊號'],
            'pnl':float(e['獲利(¤)']) if pd.notna(e['獲利(¤)']) else 0,
            'mfe':float(e['最大可能獲利(¤)']) if pd.notna(e['最大可能獲利(¤)']) else 0,
            'price':float(e['價格']),
        })
    results[vname] = {'n':len(trades), 'net':net, 'pf':pf, 'mdd':mdd,
                     'wr':wr, 'trades':trades}

# Master comparison
print('=' * 100)
print('L5 v19.8 SIX-VARIANT MASTER COMPARISON')
print('=' * 100)
A_net = results['A']['net']
A_mdd = results['A']['mdd']
print(f'{"Var":<3} {"N":>4} {"Net":>11} {"d vs A":>10} {"d%":>7} '
      f'{"PF":>6} {"MDD":>11} {"MDDd":>9} {"WR%":>6}')
for v in 'ABCDEF':
    r = results[v]
    delta = r['net'] - A_net
    dpct = (r['net']/A_net - 1) * 100 if A_net else 0
    mdd_delta = r['mdd'] - A_mdd
    print(f'{v:<3} {r["n"]:>4} {r["net"]:>+11,} {delta:>+10,} {dpct:>+6.1f}% '
          f'{r["pf"]:>6.2f} {r["mdd"]:>+11,} {mdd_delta:>+9,} {r["wr"]:>5.1f}%')

# BL_SP fires analysis
print()
print('=' * 100)
print('BL_SP MECHANISM: fires count, WR, total PnL per variant')
print('=' * 100)
for v in 'ABCDEF':
    trades = results[v]['trades']
    labels = defaultdict(lambda: {'n':0, 'pnl':0, 'wins':0, 'mfe':0})
    for t in trades:
        s = labels[t['exit_label']]
        s['n'] += 1; s['pnl'] += t['pnl']; s['mfe'] += t['mfe']
        if t['pnl']>0: s['wins'] += 1
    sp_total = sum(s['n'] for k,s in labels.items() if 'BL_SP' in k)
    sp_pnl = sum(s['pnl'] for k,s in labels.items() if 'BL_SP' in k)
    sp_wins = sum(s['wins'] for k,s in labels.items() if 'BL_SP' in k)
    sp_wr = sp_wins/sp_total*100 if sp_total else 0
    print(f'\nVariant {v}:')
    if sp_total:
        print(f'  BL_SP TOTAL: {sp_total} fires, WR={sp_wr:.1f}%, '
              f'total {sp_pnl:+,.0f}')
        for lbl in sorted(labels.keys()):
            if 'BL_SP' in lbl:
                s = labels[lbl]
                wr = s['wins']/s['n']*100
                print(f'    {lbl}: {s["n"]} fires, WR={wr:.0f}%, '
                      f'total {s["pnl"]:+,.0f}, avg {s["pnl"]/s["n"]:+,.0f}')
    else:
        print(f'  No BL_SP fires (SP off or threshold never reached)')

# Top 10 winner retention
print()
print('=' * 100)
print('TOP-10 WINNER RETENTION (vs Variant A baseline)')
print('=' * 100)
A_top10 = sorted(results['A']['trades'], key=lambda t: -t['pnl'])[:10]
A_top10_pnl = sum(t['pnl'] for t in A_top10)

for v in 'ABCDEF':
    trades = results[v]['trades']
    retained = 0
    retained_pnl = 0
    for at in A_top10:
        for vt in trades:
            if vt['date']==at['date'] and vt['time']==at['time']:
                if vt['pnl'] > 0:
                    retained += 1
                    retained_pnl += vt['pnl']
                break
    ret_pct = retained/10*100
    pnl_ret_pct = retained_pnl/A_top10_pnl*100 if A_top10_pnl else 0
    print(f'  Variant {v}: top-10 winners {retained}/10 ({ret_pct:.0f}%), '
          f'PnL retention {pnl_ret_pct:.0f}% ({retained_pnl:+,.0f} vs A {A_top10_pnl:+,.0f})')

# A's top 10 detailed
print()
print('=' * 100)
print("A's Top-10 trades: did variants kill any?")
print('=' * 100)
print(f'{"#":<3} {"Date":<11} {"Time":<6} {"A PnL":>9} ', end='')
for v in 'BCDEF':
    print(f'{v+" PnL":>9} ', end='')
print()
for idx, at in enumerate(A_top10, 1):
    print(f'{idx:<3} {at["date"]} {at["time"]:<6} {at["pnl"]:>+9,.0f} ', end='')
    for v in 'BCDEF':
        vt = None
        for t in results[v]['trades']:
            if t['date']==at['date'] and t['time']==at['time']:
                vt = t; break
        if vt:
            print(f'{vt["pnl"]:>+9,.0f} ', end='')
        else:
            print(f'{"(rm)":>9} ', end='')
    print()

# SP efficiency: rescue or kill?
print()
print('=' * 100)
print('SP EFFICIENCY ANALYSIS (per SP fire, compared to what happened in A)')
print('=' * 100)
for v in 'BCDEF':
    trades = results[v]['trades']
    sp_trades = [t for t in trades if 'BL_SP' in t['exit_label']]
    if not sp_trades:
        continue
    rescued = killed = same = 0
    total_diff = 0
    rescue_examples = []
    kill_examples = []
    for st in sp_trades:
        a_match = None
        for at in results['A']['trades']:
            if at['date']==st['date'] and at['time']==st['time']:
                a_match = at; break
        if a_match:
            diff = st['pnl'] - a_match['pnl']
            total_diff += diff
            if st['pnl'] > 0 and a_match['pnl'] <= 0:
                rescued += 1
                rescue_examples.append((st, a_match, diff))
            elif st['pnl'] < a_match['pnl'] and a_match['pnl'] > 0:
                killed += 1
                kill_examples.append((st, a_match, diff))
            else:
                same += 1
    print(f'\nVariant {v}: {len(sp_trades)} BL_SP fires')
    print(f'  Rescued (A was loser): {rescued}')
    print(f'  Killed (A was bigger winner): {killed}')
    print(f'  Same/marginal: {same}')
    print(f'  Net PnL impact (SP - A): {total_diff:+,.0f}')

# Top 3 kills (worst impact)
    if kill_examples:
        kill_examples.sort(key=lambda x: x[2])
        print(f'  Top kills (SP took less than A):')
        for st, at, d in kill_examples[:3]:
            print(f'    {st["date"]} {st["time"]}: SP {st["pnl"]:+,.0f} '
                  f'vs A {at["pnl"]:+,.0f} = {d:+,.0f}')

# Top 3 rescues
    if rescue_examples:
        rescue_examples.sort(key=lambda x: -x[2])
        print(f'  Top rescues (SP saved a loss):')
        for st, at, d in rescue_examples[:3]:
            print(f'    {st["date"]} {st["time"]}: SP {st["pnl"]:+,.0f} '
                  f'vs A {at["pnl"]:+,.0f} = +{d:,.0f}')

# Annual
print()
print('=' * 100)
print('ANNUAL P&L per variant')
print('=' * 100)
years = sorted({t['date'][:4] for v in results for t in results[v]['trades']})
print(f'{"Year":<6} ' + ' '.join(f'{v:>12}' for v in 'ABCDEF'))
for yr in years:
    row = [yr]
    for v in 'ABCDEF':
        s = sum(t['pnl'] for t in results[v]['trades']
                if t['date'].startswith(yr))
        row.append(f'{s:>+12,}')
    print(f'{row[0]:<6} ' + ' '.join(row[1:]))

# ACCEPTANCE CHECK
print()
print('=' * 100)
print('ACCEPTANCE CRITERIA CHECK (per v19.8 design)')
print('=' * 100)
print('PASS = net>A AND SP_WR>=50 AND Top10_retention>=80 AND MDD not worse by >10')
print('FAIL = SP_WR<30 (L3/L4 trap) OR Top10<70 OR net<A')
print()
for v in 'ABCDEF':
    r = results[v]
    trades = r['trades']
    labels = defaultdict(lambda: {'n':0, 'wins':0})
    for t in trades:
        labels[t['exit_label']]['n'] += 1
        if t['pnl']>0: labels[t['exit_label']]['wins'] += 1
    sp_total = sum(s['n'] for k,s in labels.items() if 'BL_SP' in k)
    sp_wins = sum(s['wins'] for k,s in labels.items() if 'BL_SP' in k)
    sp_wr = sp_wins/sp_total*100 if sp_total else 0

    A_top10 = sorted(results['A']['trades'], key=lambda t: -t['pnl'])[:10]
    A_top10_pnl = sum(t['pnl'] for t in A_top10)
    retained_pnl = 0
    for at in A_top10:
        for vt in trades:
            if vt['date']==at['date'] and vt['time']==at['time']:
                if vt['pnl']>0:
                    retained_pnl += vt['pnl']
                break
    ret_pct = retained_pnl/A_top10_pnl*100 if A_top10_pnl else 0

    net_vs_a = r['net'] >= A_net
    sp_ok = sp_total == 0 or sp_wr >= 50
    sp_trap = sp_total > 0 and sp_wr < 30
    top10_ok = ret_pct >= 80
    top10_fail = ret_pct < 70
    mdd_ok = r['mdd'] >= A_mdd * 1.1  # MDD is negative; not worse by 10pct

    verdict = 'BASELINE' if v == 'A' else (
        'PASS' if (net_vs_a and sp_ok and top10_ok and mdd_ok) else
        ('FAIL-TRAP' if sp_trap else
         'FAIL-TOP10' if top10_fail else
         'FAIL-NET' if not net_vs_a else
         'FAIL-MDD' if not mdd_ok else
         'FAIL-OTHER'))
    sign = '+' if r["net"]>=A_net else '-'
    print(f'  {v}: net={r["net"]:+,} (vs A {A_net:+,}={sign}), '
          f'SP={sp_total} WR={sp_wr:.0f}%, Top10={ret_pct:.0f}%, '
          f'MDD={r["mdd"]:+,} -> {verdict}')

print()
print('=' * 100)
print('Detailed exit label distribution per variant (top 5 by PnL)')
print('=' * 100)
for v in 'ABCDEF':
    trades = results[v]['trades']
    labels = defaultdict(lambda: {'n':0, 'pnl':0, 'wins':0})
    for t in trades:
        s = labels[t['exit_label']]
        s['n'] += 1; s['pnl'] += t['pnl']
        if t['pnl']>0: s['wins'] += 1
    print(f'\nVariant {v}:')
    for lbl in sorted(labels.keys(), key=lambda k: -labels[k]['pnl'])[:6]:
        s = labels[lbl]
        wr = s['wins']/s['n']*100
        print(f'  {lbl:<22} {s["n"]:>3} ({wr:>5.1f}%) {s["pnl"]:>+11,.0f} '
              f'avg {s["pnl"]/s["n"]:>+8,.0f}')
