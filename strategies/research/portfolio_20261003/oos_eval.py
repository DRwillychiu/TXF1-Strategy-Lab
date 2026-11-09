# OOS (上架後) window: entry 2026-06-17 .. report end 2026-09-24. Final = MC portfolio trades (L1 also single-chart G4);
# original live versions = single-chart reports used in docs/research/L1_L5_final_compare_20261003.md.
import sys, json, datetime as dt
sys.path.insert(0,'.'); sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from portfolio_eval import load_pf, positions, metrics, FULL
import stopstruct
A=dt.datetime; S,E=A(2026,6,17),A(2026,9,25); ACC=300000
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
ORIG={'L1':'/tmp/L1_P0.xlsx','L2':'/tmp/L2_540.xlsx','L3':'/mnt/user-data/uploads/TXF1__L3_consolidationlong_v15_2_策略回測績效報告_原始上架版本.xlsx',
      'L4':U+'e11a417c-TXF1__L4_ConsolidationShort_________.xlsx','L5':'/tmp/claude-0/l5/efe53f73.xlsx'}
T=load_pf(FULL)
G4=stopstruct.load('/tmp/L1_G4.xlsx')
for t in G4: t['s']='L1'
def win(TT): return [t for t in TT if S<=t['edt']<E]
fin={}; 
Pmc=positions(win(T)); Pfx=positions(win([t for t in T if t['s']!='L1']+G4))
fin['ALL_mc']=metrics(Pmc); fin['ALL_fix']=metrics(Pfx)
for k in ['L2','L3','L4','L5']: fin[k]=metrics([p for p in Pmc if p['s']==k])
fin['L1_pf']=metrics([p for p in Pmc if p['s']=='L1']); fin['L1']=metrics([p for p in Pfx if p['s']=='L1'])
org={}; allo=[]
for k,f in ORIG.items():
    R=stopstruct.load(f)
    for t in R: t['s']=k
    W=win(R); allo+=W; org[k]=metrics(positions(W))
org['ALL']=metrics(positions(allo))
late={k:[(str(t['edt']),t['pnl']/20) for t in win(T) if t['edt']>=A(2026,9,18) and t['s']==k] for k in ['L1','L2','L3','L4','L5']}
json.dump(dict(fin=fin,org=org,late=late),open('/tmp/claude-0/oos.json','w'),ensure_ascii=False,indent=1,default=str)
for k,v in fin.items(): print('FIN',k,v)
for k,v in org.items(): print('ORG',k,v)
print('entries 9/18-9/24:',late)
