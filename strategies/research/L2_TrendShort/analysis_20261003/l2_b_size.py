# Plan B MDD topic, step 2 (both entry-delay candidates failed): (a) half size after N losses in a row until a win; (b) SL_ATR_Ratio sweep. Base B. Replay estimate.
import datetime as dt
import l2_v57_research as X, l2_v57_replay as V
from l2_b_entryq import run
NOW=48091
W=X.W
def sized(T,N):
    out=[]; cl=0
    for t in sorted(T,key=lambda t:t[2]):
        lots=1 if (N and cl>=N) else 2
        p=V.pnl(t)*lots/2; out.append((t[0],t[2],p,t[1]))
        if p<0: cl+=1
        else: cl=0
    return out
def st(S,a,b,norm=False):
    S=[x for x in S if a<=x[0]<b]; eq=pk=m=0; c=s=0; cn=sn=0
    for x in S:
        v=x[2]/x[3]*NOW if norm else x[2]; eq+=v; pk=max(pk,eq); m=min(m,eq-pk)
        if v<0: c+=v; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return round(eq),round(m),round(s),sn
def line(name,S):
    f=st(S,*W[0][1:]); r=st(S,*W[3][1:]); w2=st(S,*W[2][1:]); n=st(S,*W[0][1:],norm=True)
    print(f'{name:30s} | 全期 net {f[0]} MDD {f[1]} stk {f[2]}({f[3]}) | 22-24 MDD {w2[1]} | 近兩年 net {r[0]} MDD {r[1]} stk {r[2]} | 現價換算 {-n[1]/3000:.1f}%')
if __name__=='__main__':
    B=run()
    for N in (0,1,2,3): line(f'B, 1 lot after {N} losses' if N else 'B base (2 lots)',sized(B,N))
    print('-- SL_ATR_Ratio (initial stop = DC_Lower + ratio x ATR), B base')
    for r in (0.8,0.9,1.0,1.1,1.25,1.4): line(f'SL_ATR_Ratio {r}',sized(run(SLR=r),0))
