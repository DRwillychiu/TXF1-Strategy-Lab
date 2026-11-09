# Plan B full report (Bear_Pause_N 3, Skip_K 1) vs A (v5.7 SP 0.75) vs v5.3: windows, years, MDD location. MC/20 = micro.
import sys, datetime as dt, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
import l2_v56_mc_eval as E, l2_v57_research as X
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
B=load(U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx')
A=load(U+'8f5e7c50-TXF1__L2_TrendShort_v5.7__________SL_0.75.xlsx'); O=load('/tmp/L2_540.xlsx')
print('MC summary B:',E.mc(U+'b78ca0d8-TXF1__L2_TrendShort_v5.8__________Bear_Pause_N__3_Skip_K__1.xlsx'))
R=X.run(OV=dict(SPPPCT=0.75),PN=0,PR=False,SKIPN=3,SKIPK=1)
print('replay vs MC entry times equal:',[t[0] for t in R]==[r['edt'] for r in B],len(R),len(B))
W=E.W+[('2025/1-2026/9',dt.datetime(2025,1,1),dt.datetime(2026,9,25))]
for nm,T in (('v5.3',O),('A v5.7',A),('B v5.8',B)):
    print('==',nm)
    for wn,a,b in W:
        s=E.st(T,a,b); print(f'   {wn:14s} n {s["n"]:3d} net {s["net"]:7d} MDD {s["mdd"]:7d} streak {s["stk"]}({s["sn"]}) maxLosers {s["mcl"]}')
def yr(T):
    y=collections.defaultdict(lambda:[0,0.0,0.0])
    for r in T:
        k=r['edt'].year; y[k][0]+=1; y[k][1]+=r['pnl']/20; y[k][2]+=min(0,r['pnl']/20)
    return {k:(v[0],round(v[1]),round(v[2])) for k,v in sorted(y.items())}
for nm,T in (('v5.3',O),('A',A),('B',B)): print(nm,'by year (n, net, sum of losses):',yr(T))
# MDD episode for B
S=sorted(B,key=lambda r:r['xdt']); eq=pk=0; pkt=None; w=(0,None,None)
for r in S:
    eq+=r['pnl']/20
    if eq>=pk: pk=eq; pkt=r['xdt']
    elif eq-pk<w[0]: w=(eq-pk,pkt,r['xdt'])
print('B MDD',round(w[0]),'from',w[1],'to',w[2])
print('  trades:',[(f"{r['edt']:%Y/%m/%d}",round(r['pnl']/20),r['xsig']) for r in S if w[1]<r['xdt']<=w[2]])
print('2025 trades A:',[(f"{r['edt']:%m/%d}",round(r['pnl']/20)) for r in A if r['edt'].year==2025])
print('2025 trades B:',[(f"{r['edt']:%m/%d}",round(r['pnl']/20)) for r in B if r['edt'].year==2025])
print('last trade B',B[-1]['edt'],'| exits B',dict(collections.Counter(r['xsig'] for r in B)))
