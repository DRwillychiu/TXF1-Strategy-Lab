import sys, pickle, bisect, statistics as stt, numpy as np
sys.path.insert(0,'.')
from stopstruct import load, positions
tdates,daily=pickle.load(open('/tmp/claude-0/-home-claude/80321d76-5295-5bee-b187-42c9b8d27a01/scratchpad/daily_1500.pkl','rb'))
C=np.array([daily[d][3] for d in tdates]); H=np.array([daily[d][1] for d in tdates]); L=np.array([daily[d][2] for d in tdates])
P=positions(load('/mnt/user-data/uploads/TXF1__L4_ConsolidationShort_策略回測績效報告_上架版本.xlsx'))
rows=[]
for p in P:
    i=bisect.bisect_left(tdates,p['edt'].date())-1   # last completed daily bar before entry day
    if i<60: continue
    r20=(p['epx']/C[i-20]-1)*100
    ma60=C[i-59:i+1].mean(); d60=(p['epx']/ma60-1)*100
    hi60=H[i-59:i+1].max(); lo60=L[i-59:i+1].min(); pos60=(p['epx']-lo60)/(hi60-lo60)
    x=p['xs'][-1]; cat='BreakExit虧' if ('BreakExit' in x and p['pnl']<0) else ('移動停利賺' if x=='CS_SL' and p['pnl']>0 else ('停損虧' if p['pnl']<0 else '其他賺'))
    rows.append((cat,r20,d60,pos60,p['pnl']))
for cat in ('移動停利賺','其他賺','BreakExit虧','停損虧'):
    q=[r for r in rows if r[0]==cat]
    print(f"{cat}: {len(q)} 筆 | 進場前20日報酬 中位 {stt.median(r[1] for r in q):+.1f}% | 距60日均線 中位 {stt.median(r[2] for r in q):+.1f}% | 60日區間位置 中位 {stt.median(r[3] for r in q):.2f}")
for lab,cond in (('距60日均線 > 0（價格在均線上）',lambda r:r[2]>0),('距60日均線 <= 0',lambda r:r[2]<=0),('60日區間位置 >= 0.5',lambda r:r[3]>=0.5),('60日區間位置 < 0.5',lambda r:r[3]<0.5)):
    q=[r for r in rows if cond(r)]
    print(f"{lab}: {len(q)} 筆 淨利 {round(sum(r[4] for r in q))} 勝率 {sum(r[4]>0 for r in q)/len(q):.0%}")
