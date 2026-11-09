# BP trigger variants (estimate). Same exits as l2_bp_sim (SLK*ATR capped 450, chandelier TRK*ATR, time TMAX).
import datetime as dt, numpy as np, itertools, bisect
from l2_funnel import BE,O,H,L,C,ATR,FOK,C0,CA,CB
from l2_bp_sim import stats, pnl
n=len(C); TM=np.array([e.hour*100+e.minute for e in BE])
dk={}
for i,e in enumerate(BE):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    dk.setdefault(k,[i,i]); dk[k][1]=i
D=sorted(dk); DC=np.array([C[dk[k][1]] for k in D])
def sma(x,k):
    out=np.full(len(x),np.nan); cs=np.cumsum(np.r_[0,x]); out[k-1:]=(cs[k:]-cs[:-k])/k; return out
M20=sma(DC,20); M60=sma(DC,60)
dprev=np.zeros(n,int)
for i,e in enumerate(BE):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    dprev[i]=bisect.bisect_left(D,k)-1
HH=lambda i,k: H[max(0,i-k+1):i+1].max()
LLc=lambda i,k: C[i-k:i].min()
def sim(sigf,SLK=1.5,TRK=1.0,TMAX=40,CAP=450,start=dt.datetime(2023,1,1),end=dt.datetime(2026,9,25)):
    tr=[]; pos=None; pend=False
    for i in range(70,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP); pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i]); pend=False
            if H[i]>=pos['stop']: tr.append((BE[i],ep,e,pos['stop'],'SL')); pos=None; continue
        elif pos is not None:
            if pos.get('mkt'): tr.append((BE[pos['ei']],pos['ep'],e,O[i],pos['mkt'])); pos=None
            else:
                lv=pos['stop']
                if O[i]>=lv: tr.append((BE[pos['ei']],pos['ep'],e,O[i],'SLg')); pos=None
                elif H[i]>=lv: tr.append((BE[pos['ei']],pos['ep'],e,lv,'SL')); pos=None
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i]); pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        if e.weekday()==2 and 15<=e.day<=21: continue
        if sigf(i): pend=True
    return tr
j=lambda i: dprev[i]
SIG={
 'L2trig+DD2.5':      lambda i: (not FOK[i]) and C0[i] and CA[i] and CB[i] and (1-C[i]/HH(i,60))*100>=2.5,
 'bull60up+L2trig+DD2.5': lambda i: M60[j(i)]>M60[j(i)-5] and C0[i] and CA[i] and CB[i] and (1-C[i]/HH(i,60))*100>=2.5,
 'speed3%/20b+newlow':lambda i: (not FOK[i]) and (1-C[i]/HH(i,20))*100>=3 and C[i]<LLc(i,10),
 'speed3%+body1ATR':  lambda i: (not FOK[i]) and (1-C[i]/HH(i,20))*100>=3 and (O[i]-C[i])>=ATR[i],
 'speed4%/40b+newlow':lambda i: (not FOK[i]) and (1-C[i]/HH(i,40))*100>=4 and C[i]<LLc(i,10),
 'belowM20d+L2trig':  lambda i: (not FOK[i]) and DC[j(i)]<M20[j(i)] and M60[j(i)]>M60[j(i)-5] and C0[i] and CA[i] and CB[i],
}
R2=(dt.datetime(2024,10,1),dt.datetime(2026,9,25)); IS=(dt.datetime(2023,1,1),dt.datetime(2024,10,1))
if __name__=='__main__':
    for name,f in SIG.items():
        for SLK,TRK in ((1.0,1.0),(1.5,1.0),(1.5,1.5),(2.0,1.5)):
            tr=sim(f,SLK,TRK)
            a=stats(tr,*R2); b=stats(tr,*IS)
            print(f'{name:22s} SLK {SLK} TRK {TRK} | R2y n {a["n"]} net {a["net"]} MDD {a["mdd"]} streak {a["streak"]} pf {a["pf"]} | 23-24/9 n {b["n"]} net {b["net"]} MDD {b["mdd"]} pf {b["pf"]}')
