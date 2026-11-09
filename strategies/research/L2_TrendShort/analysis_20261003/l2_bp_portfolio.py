# Portfolio end-state check (closed-trade, micro = MC/20; BP = replay estimate):
# L1 V3.7 (MC L1_G4) + L2 v5.3 bear path (MC L2_540) + BP K=1 ; overlap of BP with L4 T8 (MC L4T8, short) and L1.
import sys, datetime as dt
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load
from l2_bp_endcheck import sim, BE
def ld(f): 
    T=load(f)
    for r in T: r['m']=r['pnl']/20
    return T
L1=ld('/tmp/L1_G4.xlsx'); L2=ld('/tmp/L2_540.xlsx'); L4=ld('/tmp/L4T8.xlsx')
BP=[dict(edt=BE[t['ei']-1],xdt=BE[t['xi']],m=t['pnl']) for t in sim(K=1)]
def eqm(ev):
    ev=sorted(ev,key=lambda x:x[0]); eq=pk=m=0; s=c=0
    for _,x in ev:
        eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
    return round(eq),round(m)
def ev(T,a,b): return [(r['xdt'],r['m']) for r in T if a<=r['edt']<b]
for nm,a,b in (('recent 2y',dt.datetime(2024,10,1),dt.datetime(2026,9,25)),('2020/10-26/9',dt.datetime(2020,10,1),dt.datetime(2026,9,25))):
    print(nm,'| L1',eqm(ev(L1,a,b)),'| L1+L2v5.3',eqm(ev(L1,a,b)+ev(L2,a,b)),'| L1+L2v5.3+BP',eqm(ev(L1,a,b)+ev(L2,a,b)+ev(BP,a,b)))
def ov(T,t0,t1): return [r for r in T if r['edt']<t1 and r['xdt']>t0]
print('BP K1 trades overlapping L4 T8 shorts (full):',sum(1 for t in BP if ov(L4,t['edt'],t['xdt'])),'of',len(BP),
      '| overlapping L1:',sum(1 for t in BP if ov(L1,t['edt'],t['xdt'])))
for t in BP:
    o=ov(L4,t['edt'],t['xdt'])
    if o: print('  BP',t['edt'],round(t['m']),'| L4',[(str(r['edt']),round(r['m'])) for r in o])

# L2 standalone: bear path (MC v5.3) + BP (replay) -> does BP worsen L2's own MDD / streak?
import numpy as np, l2_bp_endcheck as E
def mdd_streak(T):
    T=sorted(T,key=lambda r:r['xdt']); eq=pk=m=0; c=s=0; cn=sn=0
    for r in T:
        eq+=r['m']; pk=max(pk,eq); m=min(m,eq-pk)
        if r['m']<0: c+=r['m']; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return round(eq),round(m),round(s),sn
F0=E.FOK.copy(); atrp=E.ATR/E.C*100
for v in (0,0.55):
    E.FOK=np.array(F0)|(atrp<v)
    BPv=[dict(edt=BE[t['ei']-1],xdt=BE[t['xi']],m=t['pnl']) for t in sim(K=1)]
    for nm,a,b in (('2020/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('2022/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('recent 2y',dt.datetime(2024,10,1),dt.datetime(2026,9,25)),('2020/1-26/9',dt.datetime(2020,1,1),dt.datetime(2026,9,25))):
        w=lambda T:[r for r in T if a<=r['edt']<b]
        print(f'ATR%>={v} {nm:13s} | L2 v5.3 (net,MDD,streak,n)',mdd_streak(w(L2)),'| v5.3+BP',mdd_streak(w(L2)+w(BPv)))
E.FOK=F0
