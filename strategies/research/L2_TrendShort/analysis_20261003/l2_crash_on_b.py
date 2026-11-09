# Topic 2 (Willy 10/3 15:54): crash path above the weekly MA, on plan B base; acceptance = recent-2y L2 MDD not worse than B.
# Base B = SP_Pct 0.75, Pause_Mode 1, Bear_Pause_N 3, Skip_K 1 (MC 85/85). Crash stop in % (Crash_SL_Pct), trail ATR, gate ATR%. Replay estimate.
import datetime as dt
import l2_v57_research as X, l2_v57_replay as V
from l2_skip_next import nm
def run(**kw):
    return X.run(OV=dict(SPPPCT=0.75),PN=0,PR=False,SKIPN=3,SKIPK=1,**kw)
def line(name,T):
    s=[X.st(T,a,b) for _,a,b in X.W]; cr=[t for t in T if t[5]=='BP']; x=[V.pnl(t) for t in cr]
    new=[t for t in T if t[0]>=dt.datetime(2025,6,4)]
    print(f"{name:30s} | n {s[0]['n']} net {s[0]['net']} MC≈{s[0]['net']*20:,} 全期 MDD {s[0]['mdd']} stk {s[0]['stk']}({s[0]['sn']}) | 近兩年 net {s[3]['net']} MDD {s[3]['mdd']} stk {s[3]['stk']} | 暴跌路徑 n {len(cr)} net {round(sum(x))} | 2025/6/4 後 {len(new)} 筆 {round(sum(V.pnl(t) for t in new))} | 現價換算 {-nm(T,*X.W[0][1:])/3000:.1f}%")
    return s
if __name__=='__main__':
    line('B (no crash path)',run())
    for g in (0.55,0.6,0.65):
        for lt in (0,200):
            line(f'crash ATR%>={g} legT {lt}',run(BP=1,BPATR=g,BPSLP=1.0,BPLEGT=lt))
