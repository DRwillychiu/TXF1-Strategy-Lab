import sys, datetime as dt
exec(open('l1_streak_test.py').read().split("grid=[")[0])
grid=[('現行 0.5%',{}),('0.35%',{'SLP':0.35}),('0.30%',{'SLP':0.30}),('0.25%（≈150點@60,000）',{'SLP':0.25}),('0.20%（≈150點@75,000）',{'SLP':0.20}),('150點',{'SLMAX':150})]
for nm,ov in grid:
    T=run(S0,ov)
    st=stats(T,S0,A(2026,9,25)); lv=stats(T,A(2026,6,17),A(2026,9,25))
    w=sum((t[3]-t[2]-SLIP)>0 for t in T if t[0]>=S0)/max(1,st[0])*100
    print(f"{nm:<22}", st, f"win {w:.0f}%", lv, flush=True)
