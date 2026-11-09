import pandas as pd, numpy as np, pickle, sys
b=pd.read_pickle('b15.pkl'); D=pd.read_pickle('D2.pkl')
m=np.load('m1.npz'); MT,MO,MH,ML,MC=m['t'],m['o'],m['h'],m['l'],m['c']
# 15m ATRs (simple average true range, MC AvgTrueRange)
pc=b.Close.shift(1); tr=np.maximum(b.High,pc)-np.minimum(b.Low,pc); tr.iloc[0]=b.High.iloc[0]-b.Low.iloc[0]
b['atr35']=tr.rolling(35).mean(); b['atr280']=tr.rolling(280).mean()
# daily context
Dd=D[['O','H','L','C','R']].copy()
Dd['ma60']=Dd.C.rolling(60).mean()
Dd['r5']=Dd.H.rolling(5).max()-Dd.L.rolling(5).min()
days=list(Dd.index); H=Dd.H.values; L=Dd.L.values
box={}; inc=False; top=btm=np.nan
for i in range(4,len(days)):
    rh=H[i-4:i].max(); rl=L[i-4:i].min()
    if H[i]<=rh and L[i]>=rl and (H[i]-L[i])/(rh-rl)<=0.6: inc=True; top,btm=rh,rl
    if inc and (H[i]>top or L[i]<btm): inc=False
    box[days[i]]=(top,btm) if inc else None          # known after day i closes -> used on day i+1
ctx={}
for i in range(60,len(days)-1):
    d=days[i]; T=days[i+1]
    ctx[T]=dict(up=Dd.C.iloc[i]>Dd.ma60.iloc[i], box=box.get(d), pR=Dd.R.iloc[i], r5=Dd.r5.iloc[i])
# candidate signals (same for all methods): L5-like, uptrend, active box, half box >= 1.5 * 4.5*ATR35
bi=b.index.values.astype('datetime64[m]'); td=b.td.values
cl=b.Close.values; a35=b.atr35.values; a280=b.atr280.values
cand=[]
for i in range(300,len(b)-1):
    c=ctx.get(pd.Timestamp(td[i]))
    if not c or not c['up'] or c['box'] is None or td[i+1]!=td[i]: continue
    top,btm=c['box']; mid=(top+btm)/2; half=(top-btm)/2; buf=4.5*a35[i]
    if half < 1.5*buf: continue
    for leg,lvl in (('Bot',btm),('Mid',mid)):
        if cl[i]<lvl and cl[i]>lvl-buf:
            cand.append((i,leg,lvl,half,a35[i],a280[i],c['pR'],c['r5'])); break
print('candidate signals',len(cand))
C=pd.DataFrame(cand,columns=['i','leg','lvl','half','a35','a280','pR','r5'])
C['t']=bi[C.i]; C['td']=td[C.i]
pre=pd.to_datetime(C.td).dt.year<2026
s1=4.5*C.a35
def cal(x): return float(np.median((s1/ x)[pre]))
k_pct=float(np.median((s1/C.lvl)[pre]))
meth={'S1 ATR35x4.5':s1,
      'S2 S1 cap 1%':np.minimum(s1,0.01*C.lvl),
      'S3 fixed %(cal)':k_pct*C.lvl,
      'S3b fixed 1.0%':0.01*C.lvl,
      'S4 prevday(cal)':cal(C.pR)*C.pR,
      'S5 prev5day(cal)':cal(C.r5)*C.r5,
      'S6 ATR280(cal)':cal(C.a280)*C.a280}
meth['S7 S1 clip S6 .75-1.33']=np.clip(s1,0.75*meth['S6 ATR280(cal)'],1.333*meth['S6 ATR280(cal)'])
print('calibration: fixed %% = %.3f%%, prevday x%.3f, prev5day x%.3f, ATR280 x%.2f'%(k_pct*100,cal(C.pR),cal(C.r5),cal(C.a280)))
COST=10; HOR=465
MTi=MT.astype('int64'); BIi=bi.astype('int64')
CI=C.i.values; CT=BIi[CI]; CN=BIi[CI+1]; CL=C.lvl.values; CH=C.half.values; CLEG=C.leg.values; CTD=C.td.values
J0=np.searchsorted(MTi,CT,side='right'); J1=np.searchsorted(MTi,CN,side='right')
def run(dist):
    out=[]; busy=-1
    for k in range(len(C)):
        if CT[k]<busy: continue
        j0=J0[k]; j1=J1[k]; lvl=CL[k]
        hit=np.nonzero(MH[j0:j1]>=lvl)[0]
        if len(hit)==0: continue
        jf=j0+hit[0]; fill=max(lvl,MO[jf]); d=float(dist[k])
        stop=fill-d; tp=fill+0.7*CH[k]
        seg=slice(jf+1,min(jf+1+HOR,len(MT)))
        sh=np.nonzero(ML[seg]<=stop)[0]; th=np.nonzero(MH[seg]>=tp)[0]
        js=sh[0] if len(sh) else 10**9; jt=th[0] if len(th) else 10**9
        if js==10**9 and jt==10**9:
            je=seg.stop-1; px=MC[je]; typ='time'
        elif js<=jt:
            je=jf+1+js; px=min(stop,MO[je]); typ='stop'
        else:
            je=jf+1+jt; px=max(tp,MO[je]) if MO[je]>tp else tp; typ='tp'
        rec=dict(t=MT[jf],td=CTD[k],leg=CLEG[k],fill=fill,d=d,px=px,typ=typ,pts=px-fill-COST,exit_t=MT[je])
        if typ=='stop':
            w=slice(je+1,min(je+241,len(MT)))
            rec['recover']=bool((MH[w]>=fill).any()); rec['deeper']=float(px-ML[w].min()) if w.stop>w.start else 0.0
        out.append(rec); busy=MTi[je]
    return pd.DataFrame(out)
res={}
for name,dist in meth.items():
    res[name]=run(np.asarray(dist)); print(name,len(res[name]),flush=True)
pickle.dump((C,res),open('simres.pkl','wb'))
