# L1 daily-gate variants (Willy 10/3 01:16: 2026 trends start before the daily MA20>MA60 forms).
# Estimate only: removes V3.2 (L1_0) trades whose entry is blocked; ignores path effects (re-entry chains).
import sys, datetime as dt, collections, bisect, numpy as np
sys.path.insert(0,'.')
from stopstruct import load
F='/mnt/user-data/uploads/TXF1_1_分鐘_2.txt'
dd=collections.OrderedDict()
with open(F) as fh:
    next(fh)
    for line in fh:
        p=line.split(',')
        y,m,d=map(int,p[0].split('/')); hh=int(p[1][:2]); mi=int(p[1][3:5]); hm=hh*100+mi
        if not (846<=hm<=1345 or hm>=1501 or hm<=500): continue
        day=dt.date(y,m,d)
        k=day if hm<=1345 else day+dt.timedelta(days=1)
        o,h,l,c=float(p[2]),float(p[3]),float(p[4]),float(p[5])
        b=dd.get(k)
        if b is None: dd[k]=[o,h,l,c]
        else: b[1]=max(b[1],h); b[2]=min(b[2],l); b[3]=c
DK=list(dd); DC=np.array([dd[k][3] for k in DK])
def sma(x,n):
    out=np.full(len(x),np.nan); cs=np.cumsum(np.r_[0,x]); out[n-1:]=(cs[n:]-cs[:-n])/n; return out
MA={n:sma(DC,n) for n in (5,10,20,30,40,60)}
def prev_idx(t):
    k=t.date() if t.hour*100+t.minute<=1345 else t.date()+dt.timedelta(days=1)
    return bisect.bisect_left(DK,k)-1
def gate(name,i):
    c=DC[i]; m=lambda n:MA[n][i]
    if name=='none': return True
    if '|' in name: return any(gate(x,i) for x in name.split('|'))
    if name.startswith('X'):  # X_f_s : MA f > MA s
        f,s=map(int,name[1:].split('_')); return m(f)>m(s)
    if name.startswith('D'):  # D<pct> : close above MA60*(1-pct/100)
        return c>m(60)*(1-float(name[1:])/100)
    if name.startswith('U'):  # U<k> : MA60 rising over k days
        k=int(name[1:]); return MA[60][i]>MA[60][i-k]
    if name=='C>60': return c>m(60)
    if name=='C>20': return c>m(20)
    if name=='X20_60|C>20': return m(20)>m(60) or c>m(20)
    if name=='X20_60|C>60': return m(20)>m(60) or c>m(60)
    raise ValueError(name)
B=sorted(load('/tmp/L1_0.xlsx'),key=lambda r:r['edt'])
for r in B: r['m']=r['pnl']/20; r['i']=prev_idx(r['edt'])
M4=load('/tmp/L1_M4b.xlsx'); m4keys={(r['edt'],r['epx']) for r in M4}
def stats(T):
    T=sorted(T,key=lambda r:r['xdt']); eq=pk=mdd=s=c=0; n=cn=0; w=None; pkd=None
    for r in T:
        eq+=r['m']
        if eq>=pk: pk=eq; pkd=r['xdt']
        elif eq-pk<mdd: mdd=eq-pk; w=(pkd.date() if pkd else None, r['xdt'].date())
        if r['m']<0: c+=r['m']; cn+=1
        else: c=0; cn=0
        if c<s: s=c; n=cn
    return round(eq),round(mdd),w,round(s),n
def ydd(T,y):
    eq=pk=mdd=0
    for r in sorted([r for r in T if r['xdt'].year==y],key=lambda r:r['xdt']):
        eq+=r['m']; pk=max(pk,eq); mdd=min(mdd,eq-pk)
    return round(mdd)
# validation: predicted blocked (X20_60) vs actual missing in M4b
pred={(r['edt'],r['epx']) for r in B if not gate('X20_60',r['i'])}
act={(r['edt'],r['epx']) for r in B if (r['edt'],r['epx']) not in m4keys}
print('validate X20_60: predicted',len(pred),'actual missing in M4b',len(act),'overlap',len(pred&act))
V=['none','X20_60','X20_40','C>60','X20_60|C>20','X20_60|C>60','D3','D5','D8','U5','U10','X20_60|U5','X20_60|D5','X20_60|D3']
KEY=[(dt.datetime(2026,7,31,2,15),'7/31'),(dt.datetime(2026,8,26,11,0),'8/26'),(dt.datetime(2026,8,12,11,45),'8/12')]
print('variant | n net MDD(window) streak | 2025yrMDD 2023yrMDD | OOS net/MDD | 7/31 8/26 8/12 allowed')
for v in V:
    T=[r for r in B if gate(v,r['i'])]
    e,mdd,w,s,n=stats(T)
    O=[r for r in T if r['edt']>=dt.datetime(2026,6,17)]; eo,mo,_,_,_=stats(O)
    al=[('Y' if any(abs((r['edt']-k).total_seconds())<60 for r in T) else 'n') for k,_ in KEY]
    print(f'{v:12s} | {len(T)} {e} {mdd} {w} {s}({n}) | {ydd(T,2025)} {ydd(T,2023)} | {eo}/{mo} | {" ".join(al)}')
