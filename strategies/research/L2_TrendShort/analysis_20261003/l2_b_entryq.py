# Plan B MDD topic (Willy 10/3 15:45): entry quality in late-bear chop and false filter episodes.
# Base B = SP_Pct 0.75, Pause_Mode 1, Bear_Pause_N 3, Skip_K 1 (anchor: MC 85/85). Candidates: (1) filter confirmed N weekly updates, (2) weekly close >= D% below SMA13. Replay estimate.
import datetime as dt
import l2_v57_research as X, l2_v57_replay as V
from l2_skip_next import nm
def run(**ov):
    o=dict(SPPPCT=0.75); o.update(ov); return X.run(OV=o,PN=0,PR=False,SKIPN=3,SKIPK=1)
def line(name,T):
    s=[X.st(T,a,b) for _,a,b in X.W]
    print(f"{name:24s} | n {s[0]['n']} net {s[0]['net']} (MC≈{s[0]['net']*20:,}) 全期 MDD {s[0]['mdd']} stk {s[0]['stk']}({s[0]['sn']}) | 20-22 {s[1]['mdd']} | 22-24 {s[2]['mdd']} | 近兩年 net {s[3]['net']} MDD {s[3]['mdd']} stk {s[3]['stk']} | 現價換算 {-nm(T,*X.W[0][1:])/3000:.1f}%")
    return s
if __name__=='__main__':
    b=run(); assert len(b)==85, len(b)
    line('B base',b)
    print('-- candidate 1: filter on for N weekly updates in a row')
    for w in (2,3): line(f'confirm {w} weeks',run(WCONF=w))
    print('-- candidate 2: weekly close at least D% below SMA13')
    for d in (0.5,1.0,1.5,2.0,2.5,3.0,4.0): line(f'depth >= {d}%',run(WDEPTH=d))
