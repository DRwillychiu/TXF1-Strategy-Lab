import pandas as pd, numpy as np
b=pd.read_pickle('b15.pkl')
g=b.groupby('td')
D=pd.DataFrame({'O':g['Open'].first(),'H':g['High'].max(),'L':g['Low'].min(),'C':g['Close'].last(),'n':g.size()})
dd=b[b.sess=='D'].groupby('td'); D['dO']=dd['Open'].first(); D['dC']=dd['Close'].last(); D['dH']=dd['High'].max(); D['dL']=dd['Low'].min()
D=D[D.n>=20]   # drop partial days
D['R']=D.H-D.L
D['A20']=D.R.shift(1).rolling(20).mean()
D['Rrel']=D.R/D.A20
D['net']=(D.C-D.O).abs(); D['netR']=D.net/D.R
D['dnet']=(D.dC-D.dO).abs()
# zigzag legs within the trading day on 15m closes/high/low, threshold = 0.5*A20
legs={}
for day,x in b.groupby('td'):
    if day not in D.index or np.isnan(D.at[day,'A20']): continue
    th=0.5*D.at[day,'A20']; hi=x.High.values; lo=x.Low.values
    n=0; dirn=0; ext_hi=hi[0]; ext_lo=lo[0]
    for h,l in zip(hi,lo):
        if dirn>=0:
            if h>ext_hi: ext_hi=h
            if ext_hi-l>=th: n+=1; dirn=-1; ext_lo=l
        if dirn<0:
            if l<ext_lo: ext_lo=l
            if h-ext_lo>=th: n+=1; dirn=1; ext_hi=h
    legs[day]=n
D['legs']=pd.Series(legs)
# false breakouts vs prior day and vs 4-day box
D['pH']=D.H.shift(1); D['pL']=D.L.shift(1)
D['bH']=D.H.shift(1).rolling(4).max(); D['bL']=D.L.shift(1).rolling(4).min()
e=0.1*D.A20
D['fbo1']=(D.H>D.pH+e)&(D.C<D.pH); D['fbd1']=(D.L<D.pL-e)&(D.C>D.pL)
D['fbo4']=(D.H>D.bH+e)&(D.C<D.bH); D['fbd4']=(D.L<D.bL-e)&(D.C>D.bL)
D['both4']=D.fbo4&D.fbd4
D['whip']=(D.Rrel>=1.3)&(D.netR<=0.25)&(D.legs>=3)
D['big']=D.Rrel>=1.5; D['small']=D.Rrel<=0.6
D['atrpct']=D.A20/D.C.shift(1)*100
D.to_pickle('D.pkl')
D=D.dropna(subset=['A20'])
def maxrun(s):
    m=c=0
    for v in s: c=c+1 if v else 0; m=max(m,c)
    return m
rows=[]
for y,x in D.groupby(D.index.year):
    rows.append(dict(year=y,days=len(x),avgR_pct=round((x.R/x.C).mean()*100,2),
      big=x.big.sum(),small=x.small.sum(),big_run=maxrun(x.big),small_run=maxrun(x.small),
      whip=x.whip.sum(),legs3=(x.legs>=3).sum(),fbo4=x.fbo4.sum(),fbd4=x.fbd4.sum(),both4=x.both4.sum(),
      fbo_run=maxrun(x.fbo1),fbd_run=maxrun(x.fbd1),fbo1=x.fbo1.sum(),fbd1=x.fbd1.sum()))
T=pd.DataFrame(rows).set_index('year'); print(T.to_string())
# per-63-day windows: distribution of counts (what a 3-month window can contain)
print('\nrolling 63 trading days (≈10/5-1/5): median / 90th pct / max over 2019-2026')
for c in ['big','small','whip','legs3','fbo4','fbd4','fbo1','fbd1']:
    r=D[c].astype(int).rolling(63).sum().dropna()
    print(c, int(r.median()), int(r.quantile(.9)), int(r.max()), '| last 63d (to 9/24):', int(D[c].astype(int).iloc[-63:].sum()))
print('\nbig->small->big within 3 days count per year:')
s=D.big.values; m=D.small.values; idx=D.index
alt=[idx[i] for i in range(2,len(s)) if s[i-2] and m[i-1] and s[i]]
print(pd.Series([d.year for d in alt]).value_counts().sort_index().to_dict())
