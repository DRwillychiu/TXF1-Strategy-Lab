# Willy 10/3 15:04: optimise for the post-2026 high-level, high-volatility market, not only history.
# Q1 world without classic bears / Q2 a bear that hits every L2 weakness. Replay on v5.6 base (anchor MC 40/40); estimates.
import datetime as dt, collections, numpy as np
import l2_v57_replay as V, l2_v57_research as X
NOW=48091
def run(**kw): return X.run(**kw)
def yr(T):
    y=collections.defaultdict(lambda:[0,0.0])
    for t in T: y[t[0].year][0]+=1; y[t[0].year][1]+=V.pnl(t)
    return {k:(v[0],round(v[1])) for k,v in sorted(y.items())}
# ---- Q2a: pause that ends after N bars vs only at regime end: does L2 get the main leg back?
print('== Q2a pause release: main legs restored?')
for pb in (0,200,400,800):
    T=run(PB=pb); s=X.st(T,*X.W[0][1:])
    legs={k:[f"{t[0]:%m/%d}:{round(V.pnl(t))}" for t in T if a<=t[0]<b] for k,(a,b) in {'2020/2-4 COVID':(dt.datetime(2020,2,1),dt.datetime(2020,5,1)),'2022/4-6':(dt.datetime(2022,4,1),dt.datetime(2022,7,1))}.items()}
    print(f' #27 {pb:3d}: n {s["n"]} net {s["net"]} MDD {s["mdd"]} stk {s["stk"]}({s["sn"]}) | COVID {legs["2020/2-4 COVID"]} | 2022/4-6 {legs["2022/4-6"]}')
# ---- Q2b: the same bears replayed at today's index (48,091): fixed 450 cap vs volatility stop with 1 lot
def norm_series(T,lots_fn):
    out=[]
    for t in T:
        pts=(t[1]-t[3])/t[1]*NOW; d=(t[6]-t[1])/t[1]*NOW if t[6] else 0; lots=lots_fn(d)
        out.append((t[0],t[2],lots*(pts-10)*10,d,lots))
    return out
def stats(S,a,b):
    S=sorted([x for x in S if a<=x[0]<b],key=lambda x:x[1]); eq=pk=m=0; c=s=0; cn=sn=0
    for x in S:
        eq+=x[2]; pk=max(pk,eq); m=min(m,eq-pk)
        if x[2]<0: c+=x[2]; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return round(eq),round(m),round(s),sn,round(min([x[2] for x in S],default=0))
print('== Q2b bear path replayed at 48,091 (P&L scaled to today, micro 2 lots base)')
A=run(OV=dict(SLMAX=0,HARD=0,SLP=0.94))                 # today: the 450 cap (=0.94%) binds, 2 lots always
B=run(OV=dict(SLMAX=0,HARD=0,SLP=1.25))                 # design stop 1.25% (=601 pts today), size down to 1 lot when > 450
SA=norm_series(A,lambda d:2); SB=norm_series(B,lambda d:2 if d<=450 else 1)
print('  B: share of trades sized to 1 lot',round(np.mean([x[4]==1 for x in SB])*100),'% | planned stop pts today median',round(float(np.median([x[3] for x in SB]))))
for nm,S in (('A cap 450, 2 lots',SA),('B 1.25% stop, 1 lot if >450',SB)):
    f=stats(S,*X.W[0][1:]); r=stats(S,*X.W[3][1:])
    print(f'  {nm:28s} 全期 net {f[0]} MDD {f[1]} ({-f[1]/3000:.1f}%) stk {f[2]}({f[3]}) worst {f[4]} | 近兩年 net {r[0]} MDD {r[1]} stk {r[2]}')
# ---- Q1: what L2 earned in 2024-2026 (secular bull with violent crashes) and which episodes
print('== Q1 v5.6 by year:',yr(run()))
T=run(); print('  2024-2025 trades:',[(f"{t[0]:%Y/%m/%d}",round(V.pnl(t))) for t in T if t[0].year>=2024])
