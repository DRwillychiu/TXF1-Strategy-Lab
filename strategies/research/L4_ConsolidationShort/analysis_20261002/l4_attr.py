import sys, datetime as dt, collections, statistics as stt, pickle, numpy as np, bisect
sys.path.insert(0,'.')
from stopstruct import load, positions
F='/mnt/user-data/uploads/TXF1__L4_ConsolidationShort_策略回測績效報告_上架版本.xlsx'
tr=load(F); P=sorted(positions(tr),key=lambda p:p['edt'])
for p in P:
    p['pts']=p['pnl']/20; p['mfe_pts']=p['mfe']/20; p['mae_pts']=p['mae']/20
    p['h']=(p['xdt']-p['edt']).total_seconds()/3600
    x=p['xs'][-1]
    p['cat']=('SL_虧' if p['pnl']<0 else 'SL_賺(移動停利)') if x in ('CS_SL','Stop Loss') else (x.replace('CS_','')+('_賺' if p['pnl']>0 else '_虧'))
    hm=p['edt'].hour*100+p['edt'].minute
    p['sess']='日盤' if 845<=hm<=1345 else '夜盤'
tot=sum(p['pnl'] for p in P)
print('總筆數',len(P),'淨利',round(tot))
print('== 出場分類')
g=collections.defaultdict(list)
for p in P: g[p['cat']].append(p)
for k,v in sorted(g.items(),key=lambda kv:sum(p['pnl'] for p in kv[1])):
    print(f"  {k}: {len(v)} 筆 {round(sum(p['pnl'] for p in v))} 平均 {round(stt.mean(p['pnl'] for p in v))} 持有中位 {stt.median(p['h'] for p in v):.1f}h")
L=[p for p in P if p['pnl']<0]; W=[p for p in P if p['pnl']>0]
print('== 虧損結構：',len(L),'筆',round(sum(p['pnl'] for p in L)),'平均',round(stt.mean(p['pnl'] for p in L)),'| 獲利',len(W),'筆',round(sum(p['pnl'] for p in W)),'平均',round(stt.mean(p['pnl'] for p in W)))
print('  虧損點數/口 中位',round(stt.median(-p['pts'] for p in L)),'最大',round(max(-p['pts'] for p in L)))
# SL_Pct cap hits: loss pts approx 1.5% of entry
cap=[p for p in L if -p['pts']>=0.0145*p['epx']]
print('  碰到 1.5% 上限的虧損',len(cap),round(sum(p['pnl'] for p in cap)))
print('== 先賺後賠（虧損單的最大浮盈）')
for th in (50,100,200):
    q=[p for p in L if p['mfe_pts']>=th]; print(f'  浮盈曾 >= {th} 點/口: {len(q)}/{len(L)} 筆 合計 {round(sum(p["pnl"] for p in q))}')
q=[p for p in L if p['mfe_pts']>=0.5*(-p['pts'])]; print('  浮盈曾 >= 最後虧損的一半:',len(q),round(sum(p['pnl'] for p in q)))
print('  獲利單 MFE 中位',round(stt.median(p['mfe_pts'] for p in W)),'實拿中位',round(stt.median(p['pts'] for p in W)),'→ 回吐比例中位',f"{stt.median(1-p['pts']/p['mfe_pts'] for p in W if p['mfe_pts']>0):.0%}")
print('== 快速虧損（持有 < 4 小時）')
q=[p for p in L if p['h']<4]; print(f'  {len(q)}/{len(L)} 筆 {round(sum(p["pnl"] for p in q))}')
print('== 日盤／夜盤進場')
for s in ('日盤','夜盤'):
    q=[p for p in P if p['sess']==s]; print(f'  {s}: {len(q)} 筆 淨利 {round(sum(p["pnl"] for p in q))} 勝率 {sum(p["pnl"]>0 for p in q)/len(q):.0%}')
print('== 前 10 大獲利單')
top=sorted(P,key=lambda p:-p['pnl'])[:10]
print('  合計',round(sum(p['pnl'] for p in top)),f'占淨利 {sum(p["pnl"] for p in top)/tot:.0%}', [ (p['edt'].strftime('%Y-%m-%d'),round(p['pnl']),p['cat']) for p in top])
print('== 逐年')
y=collections.defaultdict(list)
for p in P: y[p['xdt'].year].append(p)
for k in sorted(y): print(f'  {k}: {len(y[k])} 筆 {round(sum(p["pnl"] for p in y[k]))} 勝率 {sum(p["pnl"]>0 for p in y[k])/len(y[k]):.0%}')
print('== 前一筆虧損後 24 小時內再進場')
re=[P[i] for i in range(1,len(P)) if P[i-1]['pnl']<0 and (P[i]['edt']-P[i-1]['xdt']).total_seconds()<=86400]
print(f'  {len(re)} 筆 {round(sum(p["pnl"] for p in re))} 勝率 {sum(p["pnl"]>0 for p in re)/max(1,len(re)):.0%}')
print('== 最大連虧 2024/9/6～2025/4/1')
for p in P:
    if dt.datetime(2024,9,1)<=p['edt']<=dt.datetime(2025,4,2):
        print(f"  {p['edt']:%Y-%m-%d %H:%M} {p['sess']} 進 {p['epx']} 出 {p['xdt']:%m-%d %H:%M} {p['xs'][-1]} {round(p['pnl'])} 浮盈 {round(p['mfe_pts'])} 點 持有 {p['h']:.1f}h")
