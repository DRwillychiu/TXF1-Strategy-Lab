# Willy 10/3 15:17: SP_Pct 0.75 adopted; bear loss pause = skip only the NEXT trade. Base = v5.6 caps + SP 0.75. Replay estimate.
import datetime as dt
import l2_v57_research as X, l2_v57_replay as V
NOW=48091
def nm(T,a,b):
    T=sorted([t for t in T if a<=t[0]<b],key=lambda t:t[2]); eq=pk=m=0
    for t in T: x=V.pnl(t)/t[1]*NOW; eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
    return round(m)
def go(nm_,**kw):
    T=X.run(OV=dict(SPPPCT=0.75),**kw); s=[X.st(T,a,b) for _,a,b in X.W]
    print(f"{nm_:34s} | 全期 n {s[0]['n']} net {s[0]['net']} MDD {s[0]['mdd']} stk {s[0]['stk']}({s[0]['sn']}) | 20-22 {s[1]['mdd']}/{s[1]['stk']} | 22-24 {s[2]['mdd']}/{s[2]['stk']} | 2y net {s[3]['net']} {s[3]['mdd']}/{s[3]['stk']} | 現價換算 {nm(T,*X.W[0][1:])} ({-nm(T,*X.W[0][1:])/3000:.1f}%)")
    return T
if __name__=='__main__':
    go('no pause',PN=0,PR=False)
    go('v5.6 pause: 2 losses -> regime end',PN=2,PR=True)
    for n,k in ((1,1),(2,1),(3,1),(2,2),(3,2),(2,3)):
        go(f'skip next {k} trade(s) after {n} losses',PN=0,PR=False,SKIPN=n,SKIPK=k)
