# L3-style 60M box: long (L3) vs mirrored short (L4 idea). Rough estimate, NOT MC.
import pickle, numpy as np, datetime as dt, bisect, collections
S='/tmp/claude-0/-home-claude/80321d76-5295-5bee-b187-42c9b8d27a01/scratchpad/'
ks,vals=pickle.load(open(S+'l5/bars15.pkl','rb'))
v=np.array(vals); O,H,L,C=v[:,0],v[:,1],v[:,2],v[:,3]
pc=np.r_[C[0],C[:-1]]; tr=np.maximum(H,pc)-np.minimum(L,pc)
atr9=np.convolve(tr,np.ones(9)/9,'full')[:len(tr)]
tdates,daily=pickle.load(open(S+'daily_1500.pkl','rb'))
def prevrng(t):
    d=t.date() if t.hour*100+t.minute<1500 else t.date()+dt.timedelta(days=1)
    i=bisect.bisect_left(tdates,d)-1
    D=tdates[i]; h,l,c=daily[D][1],daily[D][2],daily[D][3]; return (h-l)/c*100
def sess(t):
    hm=t.hour*100+t.minute
    return ('D',t.date()) if 900<=hm<=1345 else ('N',t.date() if hm>=1515 else t.date()-dt.timedelta(days=1))
sid=[sess(t) for t in ks]
# 60M bars: index of last 15m bar of each 60M bar
ends=[];i=0;n=len(ks)
while i<n:
    j=i
    while j<n and sid[j]==sid[i]: j+=1
    for s in range(i,j,4): ends.append(min(s+4,j)-1)
    i=j
eH=[H[ends[0]:ends[0]+1].max()]
B=[]
prev=0
for e in ends:
    s=prev; B.append((e,H[s:e+1].max(),L[s:e+1].min(),C[e])); prev=e+1
# box state per 15m bar (updated at 60M bar close)
N=16; SHR=0.1
state=np.zeros(n,dtype=bool); top=np.zeros(n); btm=np.zeros(n)
cons=False; tp=bt=0; bi=0
Hb=np.array([b[1] for b in B]); Lb=np.array([b[2] for b in B]); Cb=np.array([b[3] for b in B]); Eb=[b[0] for b in B]
k=0
for i in range(n):
    while k<len(B) and Eb[k]==i:
        if k>=N:
            rh=Hb[k-N:k].max(); rl=Lb[k-N:k].min(); rr=rh-rl; cr=Hb[k]-Lb[k]
            if Hb[k]<=rh and Lb[k]>=rl and rr>0 and cr/rr<=SHR: cons=True; tp,bt=rh,rl
        if cons and (Cb[k]>tp or Cb[k]<bt): cons=False
        k+=1
    state[i]=cons; top[i]=tp; btm[i]=bt
def run(side, night_only, start=dt.datetime(2021,9,16)):
    trades=[]; pos=None
    for i in range(1,n-1):
        t=ks[i]
        if pos:
            e,st,tg,d0=pos
            # exit checks on bar i (orders from previous bar)
            if side==1:
                if L[i]<=st: trades.append((d0,st-e-10)); pos=None
                elif H[i]>=tg: trades.append((d0,tg-e-10)); pos=None
            else:
                if H[i]>=st: trades.append((d0,e-st-10)); pos=None
                elif L[i]<=tg: trades.append((d0,e-tg-10)); pos=None
            if pos and not state[i]:
                x=O[i+1]; trades.append((d0,(x-e)*side-10)); pos=None
            continue
        if t<start or not state[i]: continue
        tp,bt=top[i],btm[i]; rng=tp-bt
        if rng<8.5*atr9[i]: continue
        hm=ks[i+1].hour*100+ks[i+1].minute
        if night_only and 900<=hm<=1345: continue
        if hm==500 or (900<=hm<945): continue
        sd=max(C[i]*prevrng(t)*0.30/100,60); sd=min(sd,C[i]*0.007)
        if side==1:
            if not (C[i]<bt+rng*0.5 and C[i]>bt-sd): continue
            if H[i+1]>=bt:
                e=max(O[i+1],bt); pos=(e,e-sd,e+(tp-e)*0.9,ks[i+1])
        else:
            if not (C[i]>tp-rng*0.5 and C[i]<tp+sd): continue
            if L[i+1]<=tp:
                e=min(O[i+1],tp); pos=(e,e+sd,e-(e-bt)*0.9,ks[i+1])
    return trades
def rep(lab,tr):
    if not tr: print(lab,'0 筆'); return
    p=np.array([x[1] for x in tr]); yrs=collections.defaultdict(float)
    for d,x in tr: yrs[d.year]+=x
    eq=np.cumsum(p); mdd=(eq-np.maximum.accumulate(eq)).min()
    print(f"{lab}: {len(p)} 筆（{len(p)/5:.0f}/年） 勝率 {np.mean(p>0):.0%} 平均 {p.mean():+.0f} 點 合計 {p.sum():+.0f} 點 MDD {mdd:.0f} 點 | 逐年 {{{', '.join(f'{k}:{v:+.0f}' for k,v in sorted(yrs.items()))}}}")
rep('L3 型做多（只做夜盤）',run(1,True))
rep('L3 型做多（全時段）',run(1,False))
rep('鏡像做空（只做夜盤）',run(-1,True))
rep('鏡像做空（全時段）',run(-1,False))
