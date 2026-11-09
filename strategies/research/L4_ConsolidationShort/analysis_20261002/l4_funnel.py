# L4 v14.6 signal funnel replica (estimate, not MC): how many trap-short signals per year,
# and how many survive each filter; Macro_Mode 0/1/2/3 comparison.
import datetime as dt, numpy as np, pickle, bisect, collections
F='/mnt/user-data/uploads/TXF1_1_分鐘_1.txt'
bars={}
with open(F) as fh:
    next(fh)
    for line in fh:
        p=line.split(',')
        if len(p)<6: continue
        y,m,d=map(int,p[0].split('/')); hh=int(p[1][0:2]); mm=int(p[1][3:5])
        t=dt.datetime(y,m,d,hh,mm)
        if t.year<2019: continue
        o,h,l,c=float(p[2]),float(p[3]),float(p[4]),float(p[5])
        q=(mm+14)//15*15; e=t.replace(minute=0)+dt.timedelta(minutes=q)
        b=bars.get(e)
        if b is None: bars[e]=[o,h,l,c]
        else:
            if h>b[1]: b[1]=h
            if l<b[2]: b[2]=l
            b[3]=c
ks=sorted(k for k in bars if (900<=k.hour*100+k.minute<=1345) or (k.hour*100+k.minute>=1515) or (k.hour*100+k.minute<=500))
V=np.array([bars[k] for k in ks]); O,H,L,C=V.T
n=len(ks)
pc=np.r_[C[0],C[:-1]]; tr=np.maximum(H,pc)-np.minimum(L,pc)
atr60=np.convolve(tr,np.ones(60)/60,'full')[:n]
def sess(t):
    hm=t.hour*100+t.minute
    return ('D',t.date()) if 900<=hm<=1345 else ('N',t.date() if hm>=1515 else t.date()-dt.timedelta(days=1))
sid=[sess(t) for t in ks]
ends=[];i=0
while i<n:
    j=i
    while j<n and sid[j]==sid[i]: j+=1
    for s in range(i,j,4): ends.append(min(s+4,j)-1)
    i=j
Hb=[];Lb=[];Cb=[];prev=0
for e in ends: Hb.append(H[prev:e+1].max()); Lb.append(L[prev:e+1].min()); Cb.append(C[e]); prev=e+1
Hb,Lb,Cb=map(np.array,(Hb,Lb,Cb)); ma48=np.convolve(Cb,np.ones(48)/48,'full')[:len(Cb)]
tdates,daily=pickle.load(open('/tmp/claude-0/-home-claude/80321d76-5295-5bee-b187-42c9b8d27a01/scratchpad/daily_1500.pkl','rb'))
DC=np.array([daily[d][3] for d in tdates]); m20=np.convolve(DC,np.ones(20)/20,'full')[:len(DC)]; m60=np.convolve(DC,np.ones(60)/60,'full')[:len(DC)]
def daily_idx(t):
    d=t.date() if t.hour*100+t.minute<1500 else t.date()+dt.timedelta(days=1)
    return bisect.bisect_left(tdates,d)-1
def condAB(j):
    A=DC[j]>m60[j] and m60[j]>=m60[j-1]; B=m20[j]>m60[j]; return A,B
# state per 15m bar
cons=False; top=btm=0; k=0; trend=1
trap=False; tc=0
cnt=collections.defaultdict(lambda: collections.Counter())
blockdays=collections.defaultdict(lambda: collections.Counter())
for i in range(n):
    while k<len(ends) and ends[k]<i:
        k+=1
    if k<len(ends) and ends[k]==i:
        if k>=15:
            rh=Hb[k-15:k].max(); rl=Lb[k-15:k].min(); rr=rh-rl; cr=Hb[k]-Lb[k]
            if Hb[k]<=rh and Lb[k]>=rl and rr>0 and cr/rr<=0.7: cons=True; top,btm=rh,rl
        if cons and (Cb[k]>top or Cb[k]<btm): cons=False
        trend=-1 if (k>=47 and Cb[k]<ma48[k]) else 1
    t=ks[i]; y=t.year
    j=daily_idx(t)
    if j<60: continue
    A,B=condAB(j)
    if not (cons and top>btm): trap=False; continue
    if H[i]>top: trap=True; tc=0
    if trap:
        tc+=1
        if tc>6: trap=False
    hm=t.hour*100+t.minute
    night_block= 200<=hm<=459
    if trap and C[i]<top-0.4*atr60[i] and not night_block:
        cnt[y]['陷阱訊號']+=1
        if trend==-1:
            cnt[y]['＋60分趨勢向下']+=1
            if not (A or B): cnt[y]['M0 上架版']+=1
            if not (A and B): cnt[y]['M1 A且B才擋']+=1
            if not A: cnt[y]['M2 只擋A']+=1
            cnt[y]['M3 不擋']+=1
        trap=False
# daily block share
for jj in range(61,len(tdates)):
    A,B=condAB(jj); y=tdates[jj].year
    blockdays[y]['天數']+=1; blockdays[y]['A或B(擋)']+= (A or B); blockdays[y]['A且B']+=(A and B); blockdays[y]['A']+=A
cols=['陷阱訊號','＋60分趨勢向下','M0 上架版','M1 A且B才擋','M2 只擋A','M3 不擋']
print('年 | '+' | '.join(cols))
for y in sorted(cnt): print(y,'|',' | '.join(str(cnt[y][c]) for c in cols))
tot={c:sum(cnt[y][c] for y in cnt) for c in cols}; print('合計',tot)
print('日線封鎖天數比例（上架版 A或B）：',{y:f"{blockdays[y]['A或B(擋)']/blockdays[y]['天數']:.0%}" for y in sorted(blockdays) if y>=2019})
