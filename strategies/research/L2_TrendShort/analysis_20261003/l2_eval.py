import datetime as dt, collections
from l2_replay import run, pnl
NOW=48091; ACC=300000
def stats(R, s=dt.datetime(2020,2,7), e=dt.datetime(2026,9,25)):
    R=[t for t in R if s<=t[0]<e]; R.sort(key=lambda t:t[2])
    eq=pk=mdd=0; st=c=0; n=cn=0; neq=npk=nmdd=0; nst=nc=0
    for t in R:
        x=pnl(t); eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        y=x/t[1]*NOW; neq+=y; npk=max(npk,neq); nmdd=min(nmdd,neq-npk)
        if x<0: c+=x; cn+=1; nc+=y
        else: c=0; cn=0; nc=0
        if c<st: st=c; n=cn
        if nc<nst: nst=nc
    W=[pnl(t) for t in R if pnl(t)>0]; maxl=min([pnl(t) for t in R],default=0)
    maxpts=max([t[3]-t[1] for t in R],default=0)
    return dict(n=len(R),net=round(eq),mdd=round(mdd),streak=round(st),sn=n,win=round(len(W)/max(1,len(R))*100),maxloss=round(maxl),maxpts=round(maxpts),
                nmdd=round(-nmdd/ACC*100,1),nstreak=round(-nst/ACC*100,1))
def yearly(R):
    y=collections.defaultdict(lambda:[0,0.0])
    for t in R: y[t[2].year][0]+=1; y[t[2].year][1]+=pnl(t)
    return {k:(v[0],round(v[1])) for k,v in sorted(y.items())}
if __name__=='__main__':
    S=dt.datetime(2020,2,7); OOS=dt.datetime(2025,6,4)
    for nm,ov in (('live',{}),('A1 noWkIn',dict(WKIN=0)),('A2 noWkIn noWkEx',dict(WKIN=0,WKEX=0))):
        R=run(ov,start=S)
        print(nm,'FULL',stats(R)); print('   2025/6/4+',stats(R,OOS)); print('   yearly',yearly(R))
