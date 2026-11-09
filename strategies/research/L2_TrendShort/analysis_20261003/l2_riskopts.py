# Bear-path-only risk options on the validated v5.3 replay (78/78 vs MC): loss pause, persistent engine stop (~Guard_Persist), 450 cap. Estimate.
import datetime as dt
import l2_replay_pause as R
W=[('2020/10-22/9',dt.datetime(2020,10,1),dt.datetime(2022,10,1)),('2022/10-24/9',dt.datetime(2022,10,1),dt.datetime(2024,10,1)),('recent 2y',dt.datetime(2024,10,1),dt.datetime(2026,9,25)),('2020/1-26/9',dt.datetime(2020,1,1),dt.datetime(2026,9,25))]
def st(T,a,b):
    T=[t for t in T if a<=t[0]<b]; eq=pk=m=0; c=s=0; cn=sn=0
    for t in T:
        x=R.pnl(t); eq+=x; pk=max(pk,eq); m=min(m,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
    return f"n {len(T)} net {round(eq)} MDD {round(m)} stk {round(s)}({sn})"
def show(name,T): print(f"{name:26s} | "+" | ".join(st(T,a,b) for _,a,b in W))
base=R.run(start=dt.datetime(2020,1,1))
assert len(base)==78 and abs(sum(R.pnl(t) for t in base)-144120)<1000, (len(base),sum(R.pnl(t) for t in base))   # replay 144,406 vs MC 144,120 (0.2%)
show('v5.3 replay (MC 78 / 144,120)',base)
show('SL_Max 450',R.run(OV=dict(SLMAX=450),start=dt.datetime(2020,1,1)))
for pn,pk in ((2,1),(3,1),(3,2),(4,1)):
    show(f'{pn} losses -> skip {pk} episodes',R.run(start=dt.datetime(2020,1,1),PN=pn,PK=pk))
for pn,pb in ((3,100),(3,200),(3,400),(4,200),(4,400)):
    show(f'{pn} losses -> pause {pb} bars',R.run(start=dt.datetime(2020,1,1),PN=pn,PB=pb))
R.ENGINE_ALL=True
show('engine stop every bar',R.run(start=dt.datetime(2020,1,1)))
show('engine all + pause 3/1',R.run(start=dt.datetime(2020,1,1),PN=3,PK=1))
# 450 pts at index 48,091 = 0.94% -> replay history with the equivalent percentage cap (proxy for the cap binding at today's price)
R.ENGINE_ALL=False
for slp in (1.25,1.0,0.94,0.75,0.5):
    show(f'SL_Pct {slp} (450pt@48k=0.94)',R.run(OV=dict(SLP=slp),start=dt.datetime(2020,1,1)))
# pause until the weekly filter switches off (regime reset), after N losses in a row
for pn in (2,3,4,5):
    show(f'{pn} losses -> pause to regime end',R.run(start=dt.datetime(2020,1,1),PN=pn,PK=-1))
