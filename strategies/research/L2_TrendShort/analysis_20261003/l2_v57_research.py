# L2 v5.7 research (Willy 10/3 14:28): v5.6 base + stop-profit in % + BP bull-pullback path. Replay (anchors: v5.6 = MC 40/40; BP-only = l2_bp_endcheck 27/27). Estimate.
import sys, datetime as dt, collections
import l2_v57_replay as V
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
S0=dt.datetime(2020,1,1)
W=[('全期',dt.datetime(2020,1,1),dt.datetime(2026,9,25)),('20/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('22/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('近兩年',dt.datetime(2024,10,1),dt.datetime(2026,9,25))]
L1=load('/tmp/L1_G4.xlsx')
for r in L1: r['m']=r['pnl']/20
def st(T,a,b):
    T=[t for t in T if a<=t[0]<b]; eq=pk=m=0; c=s=0; cn=sn=0
    for t in sorted(T,key=lambda t:t[2]):
        x=V.pnl(t); eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return dict(n=len(T),net=round(eq),mdd=round(m),stk=round(s),sn=sn)
def port(T,a,b):
    ev=[(r['xdt'],r['m']) for r in L1 if a<=r['edt']<b]+[(t[2],V.pnl(t)) for t in T if a<=t[0]<b]
    ev.sort(key=lambda x:x[0]); eq=pk=m=0
    for _,x in ev: eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
    return round(m)
def run(**kw):
    base=dict(OV=dict(SLMAX=450,HARD=450),start=S0,PN=2,PR=True); ov=kw.pop('OV',{}); base['OV'].update(ov); base.update(kw)
    return V.run(**base)
def report(name,T):
    s=[st(T,a,b) for _,a,b in W]; bp=[t for t in T if t[5]=='BP']
    bpx=[V.pnl(t) for t in bp]; ex26=sum(V.pnl(t) for t in bp if t[0].year!=2026); top=max(bpx) if bpx else 0
    maxpts=max([t[3]-t[1] for t in T]+[0])
    print(f"{name:34s} 全期 n {s[0]['n']} net {s[0]['net']} MDD {s[0]['mdd']} stk {s[0]['stk']}({s[0]['sn']}) | 近兩年 n {s[3]['n']} net {s[3]['net']} MDD {s[3]['mdd']} stk {s[3]['stk']}({s[3]['sn']}) | 20-22 MDD {s[1]['mdd']} | 22-24 MDD {s[2]['mdd']} | BP n {len(bp)} net {round(sum(bpx))} ex26 {round(ex26)} -top {round(sum(bpx)-top)} | maxloss {round(maxpts)}pts | port MDD 2y {port(T,*W[3][1:])} 20/10+ {port(T,dt.datetime(2020,10,1),W[0][2])}")
    return s
if __name__=='__main__':
    report('v5.6 base',run())
    print('-- stop-profit activation in % of entry (bear path)')
    for p in (1.0,1.2,1.5,1.8,2.0): report(f'SP {p}%',run(OV=dict(SPPPCT=p)))
    print('-- BP path on v5.6 (K=1 per leg)')
    for atr in (0,0.5,0.55,0.6,0.7):
        for lt in (0,200):
            report(f'BP ATR%>={atr} legT {lt}',run(BP=1,BPATR=atr,BPLEGT=lt))
    print('-- pause scope: BP losses also counted (SCOPE=all)')
    report('BP ATR%>=0 SCOPE all',run(BP=1,SCOPE='all')); report('BP ATR%>=0.55 SCOPE all',run(BP=1,BPATR=0.55,SCOPE='all'))
