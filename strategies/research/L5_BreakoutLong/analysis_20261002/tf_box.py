import pickle, numpy as np, datetime as dt
ks,vals=pickle.load(open('bars15.pkl','rb'))
v=np.array(vals); hi,lo,cl=v[:,1],v[:,2],v[:,3]
pc=np.r_[cl[0],cl[:-1]]; tr=np.maximum(hi,pc)-np.minimum(lo,pc)
atr=np.convolve(tr,np.ones(35)/35,'full')[:len(tr)]
start=dt.datetime(2021,9,16)
def sess_id(t):
    hm=t.hour*100+t.minute
    if 900<=hm<=1345: return ('D',t.date())
    d=t.date() if hm>=1515 else t.date()-dt.timedelta(days=1)
    return ('N',d)
sid=[sess_id(t) for t in ks]
def agg(k):
    out=[];i=0;n=len(ks)
    while i<n:
        j=i; 
        while j<n and sid[j]==sid[i]: j+=1
        for s in range(i,j,k):
            e=min(s+k,j)
            out.append((ks[e-1],hi[s:e].max(),lo[s:e].min(),e-1))
        i=j
    return out
def boxes(bars,N,shrink=0.6):
    H=np.array([b[1] for b in bars]);L=np.array([b[2] for b in bars])
    forms=[]
    for k in range(N,len(bars)):
        if bars[k][0]<start: continue
        rh=H[k-N:k].max(); rl=L[k-N:k].min(); rr=rh-rl; cr=H[k]-L[k]
        if H[k]<=rh and L[k]>=rl and rr>0 and cr/rr<=shrink:
            a=atr[bars[k][3]]; forms.append((rr, rr/a))
    return forms
yrs=(dt.datetime(2026,9,24)-start).days/365.25
print('週期 | N | 涵蓋時間 | 成箱次數/年 | 箱寬中位(點) | 箱寬/ATR15 中位 | 過門檻(箱寬≥13.5ATR)')
for name,k,Ns in (('30M',2,(4,8)),('60M',4,(4,16)),('120M',8,(4,8))):
    bars=agg(k)
    for N in Ns:
        f=boxes(bars,N)
        w=np.array([x[0] for x in f]); r=np.array([x[1] for x in f])
        print(f'{name} | {N} | {N*k*15/60:.0f} 小時 | {len(f)/yrs:.0f} | {np.median(w):.0f} | {np.median(r):.1f} | {np.mean(r>=13.5):.0%}')
V=pickle.load(open('daily_variants.pkl','rb')); b=V['cal']
H=np.array([x[1] for x in b]);L=np.array([x[2] for x in b])
import bisect
f=[]
for k in range(4,len(b)):
    if b[k][0]<start: continue
    rh=H[k-4:k].max(); rl=L[k-4:k].min(); rr=rh-rl; cr=H[k]-L[k]
    if H[k]<=rh and L[k]>=rl and rr>0 and cr/rr<=0.6:
        i=bisect.bisect_right(ks,b[k][0])-1; f.append((rr,rr/atr[i]))
w=np.array([x[0] for x in f]); r=np.array([x[1] for x in f])
print(f'日K(桌機) | 4 | 約3-4天 | {len(f)/yrs:.0f} | {np.median(w):.0f} | {np.median(r):.1f} | {np.mean(r>=13.5):.0%}')
