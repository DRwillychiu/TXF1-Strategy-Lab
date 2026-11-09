import sys, datetime as dt
exec(open('l1_streak_test.py').read().split("grid=[")[0])
for nm,ov in [('現行',{}),('當日連虧3停到隔天',{'DN':3}),('當日連虧2停到隔天',{'DN':2}),('150點',{'SLMAX':150}),('150點+當日3',{'SLMAX':150,'DN':3}),('150點+暫停3/1',{'SLMAX':150,'PN':3,'PK':1}),('150點+暫停3/1+當日3',{'SLMAX':150,'PN':3,'PK':1,'DN':3})]:
    T=run(S0,ov)
    print(f"{nm:<20}", stats(T,S0,A(2026,9,25)), stats(T,A(2026,6,17),A(2026,9,25)), flush=True)
