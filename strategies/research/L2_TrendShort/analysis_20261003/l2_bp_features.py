# Features of the trades the weekly filter blocks (A1 minus live), to design a bull-pullback path. Estimate.
import datetime as dt, numpy as np, collections
from l2_funnel import BE,O,H,L,C,ATR,FOK
from l2_replay import run,pnl
idx={e:i for i,e in enumerate(BE)}
# daily series
dk={}
for i,e in enumerate(BE):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    dk.setdefault(k,[i,i]); dk[k][1]=i
D=sorted(dk); DC=np.array([C[dk[k][1]] for k in D]); DH=np.array([H[dk[k][0]:dk[k][1]+1].max() for k in D])
def sma(x,k):
    out=np.full(len(x),np.nan); cs=np.cumsum(np.r_[0,x]); out[k-1:]=(cs[k:]-cs[:-k])/k; return out
M20=sma(DC,20); M60=sma(DC,60)
import bisect
def dprev(e):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    return bisect.bisect_left(D,k)-1
R=run(dict(WKIN=0),start=dt.datetime(2020,2,7))
rows=[]
for t in R:
    i=idx[t[0]]-1   # signal bar
    if FOK[i]: continue
    j=dprev(BE[i])
    hi10=max(DH[j-9:j+1].max(), H[dk[D[j+1]][0]:i+1].max() if j+1<len(D) else 0)
    f=dict(t=t[0],p=pnl(t),pts=t[1]-t[3],
           dd10=(1-C[i]/hi10)*100,                     # % below 10-day high (incl. today)
           d60=(DC[j]/M60[j]-1)*100, d20=(DC[j]/M20[j]-1)*100,
           bull=DC[j]>M60[j], rng=(H[i]-L[i])/ATR[i], body=(O[i]-C[i])/ATR[i],
           night=not (845<=BE[i].hour*100+BE[i].minute<=1345), atrp=ATR[i]/C[i]*100)
    rows.append(f)
print('blocked trades (FOK false at signal):',len(rows),'net',round(sum(r['p'] for r in rows)))
def split(name,cond):
    a=[r for r in rows if cond(r)]; b=[r for r in rows if not cond(r)]
    fmt=lambda X:(len(X),round(sum(r['p'] for r in X)),round(np.mean([r['p']>0 for r in X])*100) if X else 0)
    print(f'{name:28s} yes {fmt(a)} | no {fmt(b)}')
for th in (1,2,3,4,5): split(f'dd10 >= {th}%',lambda r,th=th:r['dd10']>=th)
split('bull (close>MA60)',lambda r:r['bull'])
for th in (0,2,4): split(f'd20 >= {th}%',lambda r,th=th:r['d20']>=th)
for th in (1.0,1.5,2.0): split(f'range >= {th} ATR',lambda r,th=th:r['rng']>=th)
for th in (0.5,1.0): split(f'body >= {th} ATR',lambda r,th=th:r['body']>=th)
split('night signal',lambda r:r['night'])
