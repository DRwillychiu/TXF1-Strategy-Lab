# Crash-path parameter optimisation on v5.9 (plan B base), replay (anchor: v5.9 Crash_On 1 = MC 96/96 entries, net 0.25%).
# Rule (Willy 10/3 15:54): recent-2y closed MDD not worse than plan B (-6,365 replay / -6,380 MC). Reported: recent net, full MDD/streak, crash n, crash ex-2026, crash minus top.
import datetime as dt, itertools, json
from multiprocessing import Pool
import l2_v57_research as X, l2_v57_replay as V
def run(**kw): return X.run(OV=dict(SPPPCT=0.75),PN=0,PR=False,SKIPN=3,SKIPK=1,BP=1,BPSLP=1.0,**kw)
def ev(p):
    g,dd,lb,bd,tr=p
    T=run(BPATR=g,BPDD=dd,BPLB=lb,BPBODY=bd,BPTRK=tr); s=[X.st(T,a,b) for _,a,b in X.W]
    cr=[V.pnl(t) for t in T if t[5]=='BP']; ex26=sum(V.pnl(t) for t in T if t[5]=='BP' and t[0].year!=2026)
    new=[V.pnl(t) for t in T if t[0]>=dt.datetime(2025,6,4)]
    return dict(p=p,n=s[0]['n'],net=s[0]['net'],fmdd=s[0]['mdd'],fstk=s[0]['stk'],rnet=s[3]['net'],rmdd=s[3]['mdd'],rstk=s[3]['stk'],
                crn=len(cr),crnet=round(sum(cr)),ex26=round(ex26),mtop=round(sum(cr)-max(cr)) if cr else 0,newn=len(new),newnet=round(sum(new)))
if __name__=='__main__':
    grid=list(itertools.product((0.5,0.55,0.6,0.65,0.7),(2.5,3.0,3.5,4.0),(15,20,25,30),(0.8,1.0,1.2),(0.75,1.0,1.25)))
    with Pool(2) as pool: res=pool.map(ev,grid,chunksize=8)
    json.dump(res,open('/tmp/claude-0/l2_crash_grid.json','w'))
    print('combos',len(res))
