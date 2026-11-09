# L2 bull-pullback (BP) path feasibility on 60M bars (1-minute built). Estimate, NOT MC.
# Entry: weekly bear filter OFF (bull regime) + L2 trigger (C0 & ZLEMA down & ZLEMA<EMA20) + drop from 60-bar high >= DD%.
# Exit: intrabar stop at entry+min(SLK*ATR, 450); chandelier lowest low + TRK*ATR (updated at bar close, intrabar stop);
#       time stop after TMAX bars (market next open). Costs 10 pts round trip/lot, 2 lots, micro x20.
import datetime as dt, numpy as np, itertools, sys
from l2_funnel import BE,O,H,L,C,ATR,FOK,C0,CA,CB
n=len(C); TM=np.array([e.hour*100+e.minute for e in BE])
HH60=np.full(n,np.nan)
for i in range(60,n): HH60[i]=H[i-59:i+1].max()
def run(DD=2.0,SLK=1.5,TRK=1.5,TMAX=40,CAP=450,start=dt.datetime(2023,1,1),end=dt.datetime(2026,9,25),trig='L2'):
    tr=[]; pos=None; pend=False
    for i in range(61,n):
        e=BE[i]
        if e<start: continue
        if e>=end: break
        if pend and pos is None:
            ep=O[i]; dist=min(SLK*ATR[i-1],CAP); pos=dict(ep=ep,ei=i,stop=ep+dist,ll=L[i]); pend=False
            # entry bar intrabar stop
            if H[i]>=pos['stop']: tr.append((BE[pos['ei']],ep,e,pos['stop'],'SL')); pos=None; continue
        elif pos is not None:
            if pos.get('mkt'):
                tr.append((BE[pos['ei']],pos['ep'],e,O[i],pos['mkt'])); pos=None
            else:
                lv=pos['stop']
                if O[i]>=lv: tr.append((BE[pos['ei']],pos['ep'],e,O[i],'SLg')); pos=None
                elif H[i]>=lv: tr.append((BE[pos['ei']],pos['ep'],e,lv,'SL')); pos=None
        # bar close
        if pos is not None:
            pos['ll']=min(pos['ll'],L[i])
            pos['stop']=min(pos['stop'],pos['ll']+TRK*ATR[i])
            if i-pos['ei']>=TMAX: pos['mkt']='TIME'
            continue
        t=TM[i]; d=e.date()
        if (e.weekday()==2 and 15<=e.day<=21): continue
        sig = (not FOK[i]) and C0[i] and CA[i] and CB[i] and (1-C[i]/HH60[i])*100>=DD
        if sig: pend=True
    return tr
def pnl(t): return (t[1]-t[3]-10)*20
def stats(tr,a,b):
    T=[t for t in tr if a<=t[0]<b]; T.sort(key=lambda t:t[2]); eq=pk=m=0; s=c=0; mc=cn=0
    for t in T:
        x=pnl(t); eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        s=min(s,c); mc=max(mc,cn)
    W=[pnl(t) for t in T if pnl(t)>0]; Lo=[pnl(t) for t in T if pnl(t)<=0]
    return dict(n=len(T),net=round(eq),mdd=round(m),streak=round(s),mcl=mc,win=round(len(W)/max(1,len(T))*100),pf=round(sum(W)/abs(sum(Lo)),2) if Lo else 9.9,maxloss=round(min([pnl(t) for t in T],default=0)))
if __name__=='__main__':
    R2=(dt.datetime(2024,10,1),dt.datetime(2026,9,25)); IS=(dt.datetime(2023,1,1),dt.datetime(2024,10,1))
    res=[]
    for DD,SLK,TRK,TMAX in itertools.product((0,1.5,2.5,3.5),(1.0,1.5,2.0),(1.0,1.5,2.0,3.0),(20,40,80)):
        tr=run(DD,SLK,TRK,TMAX)
        a=stats(tr,*R2); b=stats(tr,*IS)
        res.append(((DD,SLK,TRK,TMAX),a,b))
    res.sort(key=lambda x:-x[1]['net'])
    for k,a,b in res[:25]: print(k,'R2y',a,'| 2023-24/9',b)
    import pickle; pickle.dump(res,open('/tmp/claude-0/l2_bp_grid.pkl','wb'))
