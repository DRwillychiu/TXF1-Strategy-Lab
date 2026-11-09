# v5.6 batch expected values: #26 Bear_Pause_N x #27 Bear_Pause_Bars (0 = until weekly filter off; >0 = filter off or N bars, whichever first). Replay estimate.
import datetime as dt, l2_replay_pause as R
from l2_v56_expect import st, W
A=R.run(start=dt.datetime(2020,1,1),PN=3,PK=-1); B=R.run(start=dt.datetime(2020,1,1),PN=3,PR=True)
assert [t[0] for t in A]==[t[0] for t in B], 'PR mode with PB=0 must equal regime pause'
print('check OK: PR mode Bars=0 == regime pause')
for pn in (0,1,2,3,4,5):
    for pb in (0,200,400,800):
        if pn==0 and pb: continue
        T=R.run(start=dt.datetime(2020,1,1),PN=pn,PR=True,PB=pb)
        s=[st(T,a,b) for _,a,b in W]
        print(f"N {pn} Bars {pb:3d} | 全期 n {s[0][0]} net {s[0][1]} MDD {s[0][2]} stk {s[0][3]}({s[0][4]}) | "+" | ".join(f"MDD {x[2]} stk {x[3]}({x[4]}) net {x[1]}" for x in s[1:]))
