import pickle,datetime,collections
import pandas as pd, numpy as np
exec(open('l5/stopstruct.py').read())
b=pd.read_pickle('full/b15.pkl'); ks=b.index; O,H,L,C=b.Open.values,b.High.values,b.Low.values,b.Close.values
P=sorted(pickle.load(open('l5/P1915.pkl','rb')),key=lambda p:p['edt'])
tr=[t for t in load('l5/v1915_def.xlsx') if t['edt']>=LO]
tpt={(t['edt'],t['epx']):t['xdt'] for t in tr if t['xsig'].startswith('BL_TP')}
def capped(p,cap_pts):
    """pnl if the stop were at most cap_pts below entry (tighter-only), path on 15m bars"""
    if cap_pts>=p['stopd']: return p['pnl']
    lvl=p['epx']-cap_pts; i=ks.searchsorted(p['edt']); j=ks.searchsorted(p['xdt']); tpx=tpt.get((p['edt'],p['epx']))
    for k in range(i+1,min(j,len(ks)-1)+1):
        if tpx and ks[k]>=tpx: break
        if L[k]<=lvl: return (min(O[k],lvl)-p['epx'])*20
    return p['pnl']
def fri(p):
    e=p['edt']; return (e.weekday()==4 and e.hour*100+e.minute>1500) or e.weekday()==5
def run(seq,mode=None,budget=None,thr=6000,alpha=1.0,weekend=False):
    eq=pk=mdd=run_=worst=0; Lref=None; rec_target=None; out=0; maxloss=0
    for p in seq:
        if weekend and fri(p): out+=1; continue
        planned=p['stopd']*20
        v=p['pnl']
        lim=None
        if budget: lim=budget
        if Lref is not None: lim=min(lim,alpha*Lref) if lim else alpha*Lref
        if lim is not None and planned>lim:
            if mode=='gate': out+=1; continue
            if mode=='cap': v=capped(p,lim/20)
        eq+=v; pk=max(pk,eq); mdd=min(mdd,eq-pk); run_=run_+v if v<0 else 0; worst=min(worst,run_); maxloss=min(maxloss,v)
        if mode in('gate','cap') and thr is not None:
            if v<=-thr and (Lref is None or -v>Lref or True): Lref=-v if Lref is None else min(Lref,-v) if False else -v; rec_target=eq+(-v)
            elif Lref is not None and eq>=rec_target: Lref=None
    return eq,mdd,worst,maxloss,out
IS=[p for p in P if p['edt']<LIVE]; OOS=[p for p in P if p['edt']>=LIVE]
def line(lab,**kw):
    a=run(IS,**kw); c=run(OOS,**kw)
    print('%-44s| IS %7d %7d %7d max1 %7d out %2d | OOS %7d %7d %7d max1 %7d out %2d'%(lab,*a,*c))
line('v19.15')
print('--- hard cap per trade (account %, tighter stop)')
for pct in [1,2,3]:
    B=3000*pct
    a=[capped(p,B/20) if p['stopd']*20>B else p['pnl'] for p in IS]; c=[capped(p,B/20) if p['stopd']*20>B else p['pnl'] for p in OOS]
    for p,v in zip(IS+OOS,a+c): p['hc']=v
    def st(X):
        eq=pk=mdd=r=w=0;m1=0
        for p in sorted(X,key=lambda p:p['xdt']):
            v=p['hc'];eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk);r=r+v if v<0 else 0;w=min(w,r);m1=min(m1,v)
        return eq,mdd,w,m1
    k26=sum(1 for p in P if p['edt'].year==2026 and p['pnl']>0 and p['hc']<0)
    print('cap %d%% (%d pts)  IS %s  OOS %s  | 2026 winners turned to losses: %d'%(pct,B/20,st(IS),st(OOS),k26))
print('--- planned-loss gate (skip if 4.5xATR stop x2 lots > budget)')
for pct in [2,3]:
    line('gate %d%% (%d)'%(pct,3000*pct),mode='gate',budget=3000*pct,thr=None)
print('--- loss memory: after a loss >= thr, next entries need planned loss <= alpha x that loss, until equity recovers it')
for mode in ['gate','cap']:
  for thr in [6000,9000]:
    for alpha in [0.5,0.75,1.0]:
        line('%s thr %d alpha %.2f'%(mode,thr,alpha),mode=mode,thr=thr,alpha=alpha)
line('loss memory gate 6000 a0.75 + Fri-night',mode='gate',thr=6000,alpha=0.75,weekend=True)
line('loss memory cap 6000 a0.75 + Fri-night',mode='cap',thr=6000,alpha=0.75,weekend=True)
print('--- 2026 stop-loss trades: stop % of price')
for p in P:
    if p['stop'] and p['edt'].year==2026: print(str(p['edt'])[:16],p['esig'],int(p['pnl']),'stop %.0f pts = %.2f%% of price = %.1f%% of 30萬'%(p['stopd'],p['stopd']/p['epx']*100,-p['pnl']/3000))
print('--- combos')
line('LM gate thr9000 a0.5 + Fri-night',mode='gate',thr=9000,alpha=0.5,weekend=True)
x=[p for p in P if p['pnl']<=-12000]; print('losses <= -12000:',[(str(p['edt'])[:16],p['esig'],p['pnl'],p['stop'],p['xs']) for p in x])
# stress replay 7/8-9/11 twice, and with 4.78% gap
W=[p for p in P if datetime.datetime(2026,7,8)<=p['edt']<=datetime.datetime(2026,9,12)]
gap=dict(W[-1]); gap['pnl']=-45900.0
for lab,seq in [('重演兩次',W+W),('重演兩次+4.78%跳空',W[:-1]+[gap]+W[:-1]+[gap])]:
    for name,kw in [('無',{}),('LM 9000/0.5',dict(mode='gate',thr=9000,alpha=0.5)),('LM+W',dict(mode='gate',thr=9000,alpha=0.5,weekend=True))]:
        r=run(seq,**kw); print('%-18s %-12s net %7d MDD %7d streak %7d max1 %7d out %d'%(lab,name,*r))
