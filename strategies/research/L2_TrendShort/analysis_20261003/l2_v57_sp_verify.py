# Topic 1 close-out: MC v5.7 #29 0.75 full report vs replay and vs v5.6 #26 2 report (MC/20 = micro).
import sys, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
import l2_v56_mc_eval as E, l2_v57_research as X
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
A=load(U+'6788b1da-TXF1__L2_TrendShort_v5.6__________26_2.xlsx'); B=load(U+'8f5e7c50-TXF1__L2_TrendShort_v5.7__________SL_0.75.xlsx')
print('MC summary 0.75:',{k:v for k,v in E.mc(U+'8f5e7c50-TXF1__L2_TrendShort_v5.7__________SL_0.75.xlsx').items()})
for nm,T in (('v5.6',A),('v5.7 SP0.75',B)):
    for wn,a,b in E.W:
        s=E.st(T,a,b); print(f'  {nm:12s} {wn:13s} n {s["n"]} net {s["net"]} MDD {s["mdd"]} streak {s["stk"]}({s["sn"]}) maxLosers {s["mcl"]}')
    print('  exits',dict(collections.Counter(r['xsig'] for r in T)))
R=X.run(OV=dict(SPPPCT=0.75))
print('replay vs MC entry times equal:',[t[0] for t in R]==[r['edt'] for r in B], len(R), len(B))
ea=set(r['edt'] for r in A); eb=set(r['edt'] for r in B)
print('only v5.6:',len(ea-eb),'only v5.7:',len(eb-ea),'common:',len(ea&eb))
ma={r['edt']:r for r in A}; ch=[(r['edt'],ma[r['edt']]['xsig'],r['xsig'],round(ma[r['edt']]['pnl']/20),round(r['pnl']/20)) for r in B if r['edt'] in ma and (ma[r['edt']]['xsig']!=r['xsig'] or ma[r['edt']]['pnl']!=r['pnl'])]
print('common trades with different exit:',len(ch)); [print('   ',x) for x in ch]
NOW=48091
def norm(T):
    U_=[dict(r) for r in T]
    for r in U_: r['pnl']=r['pnl']/r['epx']*NOW
    return U_
for nm,T in (('v5.6',A),('v5.7',B)):
    s=E.st(norm(T),*E.W[0][1:]); print(f'  normalized@48,091 {nm}: MDD {s["mdd"]} ({-s["mdd"]/3000:.1f}%) streak {s["stk"]}')
