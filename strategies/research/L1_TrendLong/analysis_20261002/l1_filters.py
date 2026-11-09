# Estimate (trade filtering, not MC): candidate entry filters / streak rules on L1_0 trades. micro.
import sys, pickle, bisect, datetime as dt, numpy as np, collections
sys.path.insert(0,'.')
exec(open('l1_attr.py').read().split("R=rows('/tmp/L1_0.xlsx')")[0])
R=rows('/tmp/L1_0.xlsx')
S='/tmp/claude-0/-home-claude/80321d76-5295-5bee-b187-42c9b8d27a01/scratchpad/'
tdates,daily=pickle.load(open(S+'daily_1500.pkl','rb'))
DC=np.array([daily[d][3] for d in tdates]); DH=np.array([daily[d][1] for d in tdates]); DL=np.array([daily[d][2] for d in tdates])
ma=lambda x,n: np.convolve(x,np.ones(n)/n,'full')[:len(x)]
d20=ma(DC,20); d60=ma(DC,60)
wk=collections.OrderedDict()
for i,d in enumerate(tdates): wk[d.isocalendar()[:2]]=i
wkeys=list(wk); wclose=np.array([DC[wk[k]] for k in wkeys]); w20=ma(wclose,20); w60=ma(wclose,60)
def di(t):
    d=t.date() if t.hour*100+t.minute<1500 else t.date()+dt.timedelta(days=1)
    return bisect.bisect_left(tdates,d)-1
def feat(t):
    j=di(t); k=wkeys.index(tdates[j].isocalendar()[:2]); kp=k-1
    return dict(d_c=DC[j],d20=d20[j],d60=d60[j],wc=wclose[kp],w20=w20[kp],w60=w60[kp],rng=(DH[j]-DL[j])/DC[j]*100)
for r in R: r['f']=feat(r['edt'])
def stats(Q):
    Q=sorted(Q,key=lambda r:r['xdt']); e,m,_,s,n,_=curve(Q); return len(Q),round(e),round(m),round(s),n
base=stats(R); print('base',base)
F={
 'W2 週收>週MA20且>週MA60':lambda f:f['wc']>f['w20'] and f['wc']>f['w60'],
 'W3 週MA20>週MA60':lambda f:f['w20']>f['w60'],
 'D1 日收>日MA20':lambda f:f['d_c']>f['d20'],
 'D2 日收>日MA60':lambda f:f['d_c']>f['d60'],
 'D3 日MA20>日MA60':lambda f:f['d20']>f['d60'],
 'V 前日振幅<2.5%':lambda f:f['rng']<2.5,
}
top20=set(id(r) for r in sorted(R,key=lambda r:-r['m'])[:20])
for k,fn in F.items():
    keep=[r for r in R if fn(r['f'])]; cut=[r for r in R if not fn(r['f'])]
    st=stats(keep); print(f"{k}: keep {st} | cut {len(cut)} trades net {round(sum(r['m'] for r in cut))} | top20 cut {sum(id(r) in top20 for r in cut)}")
# streak pause: after N losses in a row, skip next K trades (virtual losses keep counting)
for N in (3,4,5):
    for K in (1,2):
        keep=[];c=0;skip=0
        for r in R:
            if skip>0: skip-=1; c = c+1 if r['m']<0 else 0; continue
            keep.append(r); c = c+1 if r['m']<0 else 0
            if c>=N: skip=K; c=0
        st=stats(keep); print(f'pause N{N} K{K}',st,'top20 cut',sum(1 for r in R if id(r) in top20 and r not in keep))
print('--- real-only pause (count real losses only; after N, skip next K signals; counter restarts)')
def pause(RR,N,K):
    keep=[];c=0;skip=0
    for r in RR:
        if skip>0: skip-=1; continue
        keep.append(r); c = c+1 if r['m']<0 else 0
        if c>=N: skip=K; c=0
    return keep
for N in (3,4,5):
    for K in (1,2,3):
        kp=pause(R,N,K); print(f'N{N} K{K}',stats(kp),'top20 cut',sum(1 for r in R if id(r) in top20 and r not in kp))
d3=[r for r in R if F['D3 日MA20>日MA60'](r['f'])]
print('D3',stats(d3))
for N,K in ((3,1),(4,1),(4,2),(5,2)):
    kp=pause(d3,N,K); print(f'D3+N{N}K{K}',stats(kp),'top20 cut',sum(1 for r in R if id(r) in top20 and r not in kp))
w3d3=[r for r in R if F['D3 日MA20>日MA60'](r['f']) and F['W3 週MA20>週MA60'](r['f'])]; print('D3+W3',stats(w3d3))
lv=[r for r in R if A(2026,7,25)<=r['edt']<A(2026,9,11)]; print('backtest 7/25-9/10',len(lv),round(sum(r['m'] for r in lv)))
lv=[r for r in R if A(2026,6,17)<=r['edt']<A(2026,7,25)]; print('backtest 6/17-7/24',len(lv),round(sum(r['m'] for r in lv)))
