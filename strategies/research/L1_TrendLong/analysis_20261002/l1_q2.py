import sys
exec(open('l1_filters.py').read().split("print('--- real-only")[0].replace("print(","(lambda *a,**k:None)("))
import statistics as st
# Q1: size of losses inside MDD window and max streak
a,b=A(2025,2,19),A(2025,8,20)
W=[r for r in R if a<r['xdt']<=b]; Ls=[r['m'] for r in W if r['m']<0]
print('MDD window',len(W),'losers',len(Ls),'median loss',round(st.median(Ls)),'max loss',round(min(Ls)),'pts/lot median',round(-st.median(Ls)/20))
S=[r for r in R if A(2025,10,30)<=r['edt']<=A(2025,11,26)]
for r in S: print('  streak',r['edt'].strftime('%m/%d %H:%M'),r['xsig'],round(r['m']),round(r['hrs'],1),'h')
allL=[r['m'] for r in R if r['m']<0]; print('all losers median',round(st.median(allL)),'p90',round(sorted(allL)[int(len(allL)*0.1)]))
# D3 effect on MDD window and streak
d3=lambda r: F['D3 日MA20>日MA60'](r['f'])
cutW=[r for r in W if not d3(r)]; print('D3 cuts in MDD window',len(cutW),round(sum(r['m'] for r in cutW)),'of',len(W))
cutS=[r for r in S if not d3(r)]; print('D3 cuts in streak',len(cutS))
cut=[r for r in R if not d3(r)]; print('D3 cut trades',len(cut),'<4h',sum(r['hrs']<4 for r in cut),'winrate',round(sum(r['m']>0 for r in cut)/len(cut)*100),'net',round(sum(r['m'] for r in cut)))
# N5K2 trigger count and skipped trades
keep=[];c=0;skip=0;trig=0;sk=[]
for r in R:
    if skip>0: skip-=1; sk.append(r); continue
    keep.append(r); c=c+1 if r['m']<0 else 0
    if c>=5: skip=2; c=0; trig+=1
print('N5K2 triggers',trig,'skipped',len(sk),'skipped net',round(sum(r['m'] for r in sk)),'skipped winners',sum(r['m']>0 for r in sk),'biggest skipped',round(max(r['m'] for r in sk)))
by=collections.Counter(r['xdt'].year for r in sk); print('skipped by year',dict(sorted(by.items())))
for nm,a2,b2 in (('2026',A(2026,1,1),A(2026,9,25)),('OOS',A(2026,6,17),A(2026,9,25))):
    Q=[r for r in R if a2<=r['edt']<b2]; k=[r for r in Q if d3(r)]
    print(nm,'base',stats(Q),'D3',stats(k))
