import sys, datetime as dt, collections
exec(open('l1_streak_test.py').read().split("grid=[")[0])
B=run(S0,{}); X=run(S0,{'SLMAX':150})
pn=lambda t:(t[3]-t[2]-SLIP)*20
bm={t[0]:t for t in B}; xm={t[0]:t for t in X}
both=[k for k in xm if k in bm]
kill=[k for k in both if pn(xm[k])<0 and pn(bm[k])>0]           # 150 stopped, base would have won
save=[k for k in both if pn(xm[k])<0 and pn(bm[k])<pn(xm[k])-500]  # both lose, 150 lost less
same=[k for k in both if abs(pn(xm[k])-pn(bm[k]))<=500]
only_x=[k for k in xm if k not in bm]; only_b=[k for k in bm if k not in xm]
print('matched',len(both),'same',len(same))
print('洗掉（150 停損、原版會賺）',len(kill),'原版合計',round(sum(pn(bm[k]) for k in kill)),'150版合計',round(sum(pn(xm[k]) for k in kill)))
for k in kill: print('   ',k.strftime('%Y/%m/%d %H:%M'),xm[k][2],'150:',round(pn(xm[k])),'原版:',round(pn(bm[k])),bm[k][5])
print('少虧（兩版都虧，150 少虧）',len(save),'省下',round(sum(pn(xm[k])-pn(bm[k]) for k in save)))
print('150 版多出來的交易',len(only_x),'合計',round(sum(pn(xm[k]) for k in only_x)),'其中二次進場',sum(xm[k][4] for k in only_x),round(sum(pn(xm[k]) for k in only_x if xm[k][4])))
print('原版有、150 版沒有的交易',len(only_b),'合計',round(sum(pn(bm[k]) for k in only_b)))
print('total diff',round(sum(pn(t) for t in X if t[0]>=S0)-sum(pn(t) for t in B if t[0]>=S0)))
# stop-outs by entry hour (150 version, losers)
h=collections.Counter(); hs=collections.defaultdict(float)
for t in X:
    if t[0]<S0: continue
    hh=t[0].hour; k='日盤開盤 08:45-09:30' if (hh==8 or (hh==9 and t[0].minute<=30)) else ('日盤' if 9<=hh<14 else ('夜盤開盤 15:00-15:45' if hh==15 else '夜盤'))
    h[k,pn(t)>0]+=1; hs[k]+=pn(t)
print({k:(h[k,True],h[k,False],round(hs[k])) for k in ('日盤開盤 08:45-09:30','日盤','夜盤開盤 15:00-15:45','夜盤')})
