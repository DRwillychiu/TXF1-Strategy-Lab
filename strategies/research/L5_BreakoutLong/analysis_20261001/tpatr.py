exec(open('l5/pullback.py').read().split("IS=[p for p in P if p['edt']<LIVE]")[0])
print('MFE in ATR units (high-based) by year: share reaching 1.5 / 2 / 3 / 4.7 ATR')
for y in range(2022,2027):
    X=[p for p in P if p['edt'].year==y]; r=[p['mfep']/p['atr'] for p in X]
    print(y,len(X),' '.join('%.1f:%2.0f%%'%(k,100*sum(v>=k for v in r)/len(r)) for k in (1.5,2,3,4.7)))
S=[p for p in P if p['edt'].year==2026 and p['xs'][-1].startswith('BL_SP1')]
print('2026 SP1 exits: MFE/ATR median %.2f, share >=2 ATR %d/%d'%(st.median(p['mfep']/p['atr'] for p in S),sum(p['mfep']/p['atr']>=2 for p in S),len(S)))
def tpk(p,k):
    L=legs[(p['edt'],p['epx'])]; e=p['epx']; a=p['atr']; lvl=e+k*a
    tend=max(tm(x['xdt']) for x in L); tp=[x for x in L if x['xsig'].startswith('BL_TP')]
    tlim=tm(tp[0]['xdt']) if tp else tend
    j0=np.searchsorted(MT,tm(p['edt']),side='right'); j1=np.searchsorted(MT,tlim,side='left')
    idx=np.nonzero(MH[j0:j1]>=lvl)[0]
    if len(idx)==0: return p['pnl']
    th=MT[j0+idx[0]]
    # was the original position already partly/fully closed before th? (only if a non-TP leg exited earlier)
    if any(tm(x['xdt'])<=th for x in L): return p['pnl']
    tp_leg=(k*a-COST)*10
    runner=[x for x in L if not x['xsig'].startswith('BL_TP')]
    if tp:   # original had TP leg (1 lot) + runner leg (1 lot): runner unchanged, but floored at BE
        rx=runner[0]; r_px=max(rx['xpx'],e)
        return tp_leg+(r_px-e-COST)*10
    # original single exit for 2 lots: runner gets that exit price floored at BE
    x=L[-1]; r_px=max(x['xpx'],e)
    return tp_leg+(r_px-e-COST)*10
IS=[p for p in P if p['edt']<LIVE]; OOS=[p for p in P if p['edt']>=LIVE]
def line(lab,f):
    a=[f(p) for p in IS]; c=[f(p) for p in OOS]
    x=stats(a,IS); y=stats(c,OOS)
    print('%-28s| IS %7d %7d %7d payoff %.2f win %3.0f%% | OOS %7d %7d %7d payoff %.2f win %3.0f%%'%(lab,*x,*y))
line('v19.15',lambda p:p['pnl'])
for k in [1.5,2.0,2.5,3.0,3.5]:
    line('first TP 1 lot at %.1f ATR'%k,lambda p,k=k:tpk(p,k))
