import sys, datetime as dt
exec(open('l1_streak_test.py').read().split("grid=[")[0])
grid=[('base',{}),('上限120點',{'SLMAX':120}),('上限150點',{'SLMAX':150}),('上限180點',{'SLMAX':180}),('上限210點',{'SLMAX':210}),
('150點+暫停3/1',{'SLMAX':150,'PN':3,'PK':1}),('180點+暫停3/1',{'SLMAX':180,'PN':3,'PK':1}),('150點+閘門+3/1',{'SLMAX':150,'DT':1,'PN':3,'PK':1})]
for nm,ov in grid:
    T=run(S0,ov)
    print(f"{nm:<14}", stats(T,S0,A(2026,9,25)), stats(T,A(2026,6,17),A(2026,9,25)), flush=True)
