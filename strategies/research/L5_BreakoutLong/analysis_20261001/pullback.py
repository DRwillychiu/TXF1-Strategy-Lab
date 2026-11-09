import pickle,collections,statistics as st
import numpy as np, pandas as pd
exec(open('l5/stopstruct.py').read())
m=np.load('full/m1.npz'); MT=m['t'].astype('int64'); MO,MH,ML,MC=m['o'],m['h'],m['l'],m['c']
b=pd.read_pickle('full/b15.pkl'); BT=b.index.values.astype('datetime64[m]').astype('int64'); BC=b.Close.values
P=sorted(pickle.load(open('l5/P1915.pkl','rb')),key=lambda p:p['edt'])
legs=collections.defaultdict(list)
for t in load('l5/v1915_def.xlsx'):
    if t['edt']>=LO: legs[(t['edt'],t['epx'])].append(t)
def tm(dt): return np.datetime64(dt,'m').astype('int64')
COST=10
def sim(p,mode,T,X):
    """mode 'atr': arm when high-peak >= T*ATR, exit when low <= peak - X*ATR (1-min, intrabar peak)
       mode 'sp' : SP floor on 15m-close peak: arm when close-peak >= T pts, floor = entry + peak*(1-X/100)"""
    L=legs[(p['edt'],p['epx'])]; e=p['epx']; a=p['atr']
    t0=tm(p['edt']); tend=max(tm(x['xdt']) for x in L)
    tp=[x for x in L if x['xsig'].startswith('BL_TP')]; ttp=tm(tp[0]['xdt']) if tp else None
    j0=np.searchsorted(MT,t0,side='right'); j1=np.searchsorted(MT,tend,side='left')   # minutes strictly after entry bar end, before final exit minute
    if j1<=j0: return p['pnl']
    hit=None
    if mode=='atr':
        h=MH[j0:j1]; l=ML[j0:j1]; pk=np.maximum.accumulate(h)
        armed=(pk-e)>=T*a; lvl=pk-X*a
        cond=armed & (l<=lvl)
        # use previous-minute peak to avoid same-minute high/low ordering
        pk_prev=np.concatenate([[e],pk[:-1]]); armed_prev=(pk_prev-e)>=T*a; cond=armed_prev & (l<=pk_prev-X*a)
        idx=np.nonzero(cond)[0]
        if len(idx): k=idx[0]; hit=(MT[j0+k],min(MO[j0+k],pk_prev[k]-X*a))
    else:
        bi0=np.searchsorted(BT,t0,side='right'); bi1=np.searchsorted(BT,tend,side='left')
        peak=0.0
        for bi in range(bi0,bi1):
            peak=max(peak,BC[bi]-e)
            if peak>=T:
                fl=e+peak*(1-X/100)
                s=np.searchsorted(MT,BT[bi],side='right'); s1=np.searchsorted(MT,BT[bi+1],side='right') if bi+1<len(BT) else len(MT)
                s1=min(s1,j1)
                if s>=s1: continue
                idx=np.nonzero(ML[s:s1]<=fl)[0]
                if len(idx): k=s+idx[0]; hit=(MT[k],min(MO[k],fl)); break
    if hit is None: return p['pnl']
    th,px=hit
    if ttp is not None and ttp<=th:      # TP leg already done -> only runner(s) affected
        out=0.0
        for x in L:
            if x['xsig'].startswith('BL_TP') or tm(x['xdt'])<=th: out+=x['pnl']/20
            else: out+=(px-e-COST)*10*x['qty']
        return max(out,p['pnl']) if False else out
    if th>=tend: return p['pnl']
    return (px-e-COST)*20
def stats(vals,ps):
    eq=pk=mdd=r=w=0;m1=0
    for v,p in sorted(zip(vals,ps),key=lambda z:z[1]['xdt']):
        eq+=v;pk=max(pk,eq);mdd=min(mdd,eq-pk);r=r+v if v<0 else 0;w=min(w,r);m1=min(m1,v)
    W=[v for v in vals if v>0]; Lo=[v for v in vals if v<=0]
    return eq,mdd,w,(st.mean(W)/-st.mean(Lo) if Lo and W else 0),100*len(W)/len(vals)
IS=[p for p in P if p['edt']<LIVE]; OOS=[p for p in P if p['edt']>=LIVE]
def line(lab,f):
    a=[f(p) for p in IS]; c=[f(p) for p in OOS]
    x=stats(a,IS); y=stats(c,OOS)
    print('%-30s| IS %7d %7d %7d payoff %.2f win %3.0f%% | OOS %7d %7d %7d payoff %.2f win %3.0f%%'%(lab,*x,*y))
line('v19.15 (SP 100/90)',lambda p:p['pnl'])
print('-- SP floor, keep more of the peak (existing params #22/#23)')
for T in [100,150,200]:
    for R in [50,60,70,80]:
        line('SP trig %d retain %d'%(T,R),lambda p,T=T,R=R:sim(p,'sp',T,R))
print('-- pullback from peak in ATR (new rule, on top of SP 100/90)')
for T in [1.0,1.5,2.0]:
    for X in [1.0,1.5,2.0,2.5]:
        line('arm %.1f ATR, pullback %.1f ATR'%(T,X),lambda p,T=T,X=X:sim(p,'atr',T,X))
