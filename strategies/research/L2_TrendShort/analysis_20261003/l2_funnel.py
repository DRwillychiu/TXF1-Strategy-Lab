# L2 v5.3 entry funnel replica on 60M bars built from 1-minute data (estimate, not MC).
# Entry = FilterOK (last Friday-12:45 close < 13-week SMA of those closes) and C0 (Close < Lowest(Low[1],30) - 0.45*ATR21)
#         and C_A (ZLEMA falling) and C_B (ZLEMA < EMA20). ZLEMA = XAverage(2C - C[9], 20).
import datetime as dt, collections, numpy as np, sys, pickle, os
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
F='/mnt/user-data/uploads/TXF1_1_分鐘_2.txt'
CACHE='/tmp/claude-0/l2_60m.pkl'
def bar_end(t):
    hm=t.hour*100+t.minute
    if 846<=hm<=1345:
        b=t.replace(hour=8,minute=45); k=(int((t-b).total_seconds()//60)-1)//60; return min(b+dt.timedelta(minutes=60*(k+1)), t.replace(hour=13,minute=45))
    if hm>=1501: b=t.replace(hour=15,minute=0)
    elif hm<=500: b=(t-dt.timedelta(days=1)).replace(hour=15,minute=0)
    else: return None
    k=(int((t-b).total_seconds()//60)-1)//60; return min(b+dt.timedelta(minutes=60*(k+1)), (b+dt.timedelta(days=1)).replace(hour=5,minute=0))
if os.path.exists(CACHE): BE,O,H,L,C=pickle.load(open(CACHE,'rb'))
else:
    bars=collections.OrderedDict()
    with open(F) as fh:
        next(fh)
        for line in fh:
            p=line.split(','); y,m,d=map(int,p[0].split('/'))
            t=dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5])); e=bar_end(t)
            if e is None: continue
            o,h,l,c=float(p[2]),float(p[3]),float(p[4]),float(p[5])
            b=bars.get(e)
            if b is None: bars[e]=[o,h,l,c]
            else: b[1]=max(b[1],h); b[2]=min(b[2],l); b[3]=c
    BE=list(bars); O=np.array([bars[e][0] for e in BE]); H=np.array([bars[e][1] for e in BE]); L=np.array([bars[e][2] for e in BE]); C=np.array([bars[e][3] for e in BE])
    os.makedirs(os.path.dirname(CACHE),exist_ok=True); pickle.dump((BE,O,H,L,C),open(CACHE,'wb'))
n=len(C)
pc=np.r_[C[0],C[:-1]]; TR=np.maximum(H,pc)-np.minimum(L,pc)
def sma(x,k):
    out=np.full(len(x),np.nan); cs=np.cumsum(np.r_[0,x]); out[k-1:]=(cs[k:]-cs[:-k])/k; return out
def xavg(x,k):
    a=2/(k+1); out=np.empty(len(x)); out[0]=x[0]
    for i in range(1,len(x)): out[i]=out[i-1]+a*(x[i]-out[i-1])
    return out
ATR=sma(TR,21)
DCL=np.full(n,np.nan)
for i in range(31,n): DCL[i]=L[i-30:i].min()
comp=np.r_[C[:9],2*C[9:]-C[:-9]]; Z=xavg(comp,20); E=xavg(C,20)
C0=C<DCL-0.45*ATR; CA=np.r_[False,Z[1:]<Z[:-1]]; CB=Z<E
# weekly filter state
FOK=np.zeros(n,bool); wk=[]; state=False
for i in range(1,n):
    if BE[i-1].hour==12 and BE[i-1].minute==45 and BE[i-1].weekday()==4:
        wk.insert(0,C[i-1]); wk=wk[:13]
        state = len(wk)>=13 and wk[0] < sum(wk)/13
    FOK[i]=state
WKSMA=None
SIG=FOK&C0&CA&CB
if __name__=='__main__':
    sys.path.insert(0,'.')
    from stopstruct import load
    T=load('/mnt/user-data/uploads/TXF1__L2_TrendShort_策略回測績效報告_上架策略版本.xlsx')
    idx={e:i for i,e in enumerate(BE)}
    hit=0; miss=[]
    for r in T:
        i=idx.get(r['edt'])
        if i is None: miss.append((r['edt'],'nobar')); continue
        if SIG[i-1] or (r['esig'].endswith('ReEntry')): hit+=1
        else: miss.append((r['edt'],r['esig'],FOK[i-1],C0[i-1],CA[i-1],CB[i-1]))
    print('validation: MC entries',len(T),'signal at prior bar',hit); print(' misses',miss[:8])
    s=[i for i in range(n) if SIG[i] and BE[i]>=dt.datetime(2020,2,1)]
    print('replica signal bars 2020-2026/9:',len(s))
    for a,b,nm in ((dt.datetime(2020,2,1),dt.datetime(2025,6,3),'2020/2-2025/6/2'),(dt.datetime(2025,6,4),dt.datetime(2026,9,25),'2025/6/4-2026/9/24')):
        m=[i for i in range(n) if a<=BE[i]<b]; N=len(m)
        f=lambda X: sum(X[i] for i in m)
        print(f'{nm}: bars {N} | FilterOK {f(FOK)} ({f(FOK)/N*100:.1f}%) | C0 {f(C0)} | C0&CA&CB {sum(C0[i] and CA[i] and CB[i] for i in m)} | FOK&C0 {sum(FOK[i] and C0[i] for i in m)} | ALL {f(SIG)}')
