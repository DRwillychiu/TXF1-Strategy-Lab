# Composite: MC portfolio trades for L2-L5 + L1 single-chart (IOG on) G4 trades, closed-trade basis (estimate).
import sys, json, datetime as dt
sys.path.insert(0,'.'); sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from portfolio_eval import load_pf, positions, metrics, FULL
import stopstruct
T=load_pf(FULL)
G4=stopstruct.load('/tmp/L1_G4.xlsx')
for t in G4: t['s']='L1'
T2=[t for t in T if t['s']!='L1']+G4
out={}
for tag,TT in (('mc',T),('fix',T2)):
    P=positions(TT); o={'full':{},'year':{}}
    for k in ['ALL','L1','L2','L3','L4','L5']:
        Q=P if k=='ALL' else [p for p in P if p['s']==k]; o['full'][k]=metrics(Q)
    for y in range(2018,2027):
        o['year'][y]={k:(metrics([p for p in P if p['xdt'].year==y and (k=='ALL' or p['s']==k)]) or None) if [p for p in P if p['xdt'].year==y and (k=='ALL' or p['s']==k)] else None for k in ['ALL','L1','L2','L3','L4','L5']}
    out[tag]=o
json.dump(out,open('/tmp/claude-0/pf_eval2.json','w'),ensure_ascii=False,indent=1,default=str)
for tag in out:
    print(tag,'ALL',out[tag]['full']['ALL']); print(tag,'L1',out[tag]['full']['L1'])
    for y,v in out[tag]['year'].items(): a=v['ALL']; print('  ',y,a['net'],a['n'],a['win'],a['pf'],a['mdd'],a['streak'],a['mcl'],a['worst'])
