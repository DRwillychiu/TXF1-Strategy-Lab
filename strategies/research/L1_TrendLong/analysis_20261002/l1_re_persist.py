import sys, datetime as dt
exec(open('l1_streak_test.py').read().split("grid=[")[0])
for nm,ov in [('150點',{'SLMAX':150}),('150點＋二次進場整根有效',{'SLMAX':150,'RE_PERSIST':1}),('現行＋二次進場整根有效',{'RE_PERSIST':1})]:
    T=run(S0,ov); re=[t for t in T if t[0]>=S0 and t[4]]
    print(f"{nm:<22}", stats(T,S0,A(2026,9,25)), stats(T,A(2026,6,17),A(2026,9,25)), '二次進場',len(re),round(sum((t[3]-t[2]-SLIP)*20 for t in re)), flush=True)
