import pandas as pd, numpy as np, pickle
C,res=pickle.load(open('simres.pkl','rb')); D=pd.read_pickle('D2.pkl')
def eqstats(x):
    v=x.pts.values*20; eq=np.cumsum(v); pk=np.maximum.accumulate(np.maximum(eq,0)); mdd=(eq-pk).min() if len(v) else 0
    run=worst=0
    for a in v:
        run=run+a if a<0 else 0; worst=min(worst,run)
    return v.sum(),mdd,worst
rows=[]
for name,r in res.items():
    r=r.copy(); r['y']=pd.to_datetime(r.td).dt.year
    st=r[r.typ=='stop']; base_med=(st[st.y<2026].pts*20).median()
    for per,x in (('19-25',r[r.y<2026]),('2026',r[r.y==2026])):
        s=x[x.typ=='stop']; net,mdd,streak=eqstats(x)
        wash=s[s.recover & (s.deeper<=0.25*s.d)]
        rows.append(dict(method=name,per=per,n=len(x),win=round((x.pts>0).mean()*100),net=round(net),mdd=round(mdd),streak=round(streak),
            stops=len(s),avg_stop=round((s.pts*20).mean()) if len(s) else 0,worst=round((s.pts*20).min()) if len(s) else 0,
            big_loss=int(((s.pts*20)<3*base_med).sum()),wash=len(wash),wash_amt=round((wash.pts*20).sum())))
T=pd.DataFrame(rows)
pd.set_option('display.width',250)
for per in ('19-25','2026'):
    print('=== ',per); print(T[T.per==per].drop(columns='per').to_string(index=False))
# stop-outs by day regime (all years), for S1 vs S2 vs S7
print('\nstop-outs by entry-day regime (all years): count / avg loss / wash count')
for name in ['S1 ATR35x4.5','S2 S1 cap 1%','S3b fixed 1.0%','S7 S1 clip S6 .75-1.33']:
    r=res[name]; s=r[r.typ=='stop'].copy(); s=s.join(D[['whipA','big','small','fbo1','fbd1']],on='td')
    out=[]
    for c in ['whipA','big','small','fbd1']:
        z=s[s[c]==True]; out.append('%s %d/%d/%d'%(c,len(z),(z.pts*20).mean() if len(z) else 0,(z.recover&(z.deeper<=0.25*z.d)).sum()))
    print(name,'|',' ; '.join(out))
T.to_csv('stop_methods.csv',index=False)
