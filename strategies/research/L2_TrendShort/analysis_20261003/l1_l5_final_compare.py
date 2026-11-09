# L1-L5 original (live before Q4) vs finalized version: one uniform metric set from MC full reports (Willy 10/3 17:02).
# Units: micro NTD 2 lots = MC amount / 20; account 300,000. Positions merged (partial exits -> one position) for counts,
# win rate, PF, streaks, single loss and closed MDD. 最大策略虧損 (intraday, incl. open P&L) = MC summary / 20.
import sys, json, datetime as dt, openpyxl
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
from stopstruct import load, positions
A=dt.datetime; ACC=300_000
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
PAIRS=[
 ('L1 趨勢多','V3.2（實盤）','V3.7（定案）','/tmp/L1_P0.xlsx','/tmp/L1_G4.xlsx',None,'10/5 上架（定案 10/3 11:53）'),
 ('L2 趨勢空','v5.3（實盤）','v5.9＋Crash_On 1（候選）','/tmp/L2_540.xlsx',U+'e235d8fe-TXF1__L2_TrendShort_v5.9__________Crash_On__1.xlsx',None,'候選：五件套 4/5 通過，第 5 件待跑'),
 ('L3 盤整多','v15.0（原上架）','v18.2（定案）','/mnt/user-data/uploads/TXF1__L3_consolidationlong_v15_2_策略回測績效報告_原始上架版本.xlsx',U+'abf84359-TXF1__L3_ConsolidationLong_v18_2_________.xlsx',A(2019,12,19),'已上線（9/30 15:00 起）'),
 ('L4 盤整空','v14.6（實盤）','v14.8 T8（定案）',U+'e11a417c-TXF1__L4_ConsolidationShort_________.xlsx',U+'a4de76d4-TXF1__L4_ConsolidationShort_v14.8_________.xlsx',None,'10/5 上架'),
 ('L5 突破多','v19.9（實盤）','v19.18（定案）','/tmp/claude-0/l5/efe53f73.xlsx','/tmp/claude-0/l5/53d2884b.xlsx',None,'10/5 上架'),
]
K=['淨利','最大策略虧損','交易總次數']
def mc(f):
    wb=openpyxl.load_workbook(f,read_only=True); m={}
    for row in wb['策略分析'].iter_rows(values_only=True):
        r=[c for c in row if c is not None]
        if len(r)>=2 and isinstance(r[0],str) and r[0].strip() in K and r[0].strip() not in m: m[r[0].strip()]=r[1]
    return m
def curve(P):
    P=sorted(P,key=lambda p:p['xdt']); eq=pk=mdd=0; c=s=0; cn=sn=mcl=0
    for p in P:
        x=p['pnl']; eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        if x<0: c+=x; cn+=1
        else: c=0; cn=0
        if c<s: s=c; sn=cn
        mcl=max(mcl,cn)
    return dict(net=round(eq),mdd=round(mdd),streak=round(s),sn=sn,mcl=mcl)
def stats(P):
    W=[p['pnl'] for p in P if p['pnl']>0]; L=[p['pnl'] for p in P if p['pnl']<=0]
    gp,gl=sum(W),sum(L); c=curve(P)
    return dict(n=len(P),win=round(len(W)/max(1,len(P))*100,1),pf=gp/abs(gl) if gl else None,
                avg=round((gp+gl)/max(1,len(P))),wl=(gp/max(1,len(W)))/abs(gl/max(1,len(L))) if L and W else None,
                maxloss=round(min([p['pnl'] for p in P],default=0)),**c)
WIN={'全期':(A(2017,1,1),A(2026,9,26)),'近兩年':(A(2024,10,1),A(2026,9,26)),'2026':(A(2026,1,1),A(2026,9,26)),'樣本外':(A(2026,6,17),A(2026,9,26))}
out=[]
for name,o,f,fo,ff,start,status in PAIRS:
    row=dict(name=name,orig=o,final=f,status=status,start=str(start.date()) if start else None)
    for tag,fp in (('o',fo),('f',ff)):
        P=positions(load(fp)); m=mc(fp)
        if start: P=[p for p in P if p['edt']>=start]
        row[tag]={wn:stats([p for p in P if a<=p['edt']<b]) for wn,(a,b) in WIN.items()}
        row[tag]['mc']={k:v for k,v in m.items()}; row[tag]['dd_intraday']=round(m['最大策略虧損']/20)
        row[tag]['first']=str(min(p['edt'] for p in P).date()); row[tag]['last']=str(max(p['xdt'] for p in P).date())
    out.append(row)
    print(name,{t:(row[t]['全期']['n'],row[t]['全期']['net'],row[t]['全期']['mdd'],row[t]['dd_intraday'],row[t]['全期']['streak'],row[t]['全期']['sn'],row[t]['近兩年']['net'],row[t]['近兩年']['mdd'],row[t]['first'],row[t]['mc'].get('交易總次數')) for t in 'of'})
json.dump(out,open('/tmp/claude-0/l1_l5_compare.json','w'),ensure_ascii=False,default=str,indent=1)

# Portfolio (5 strategies combined, entries from 2020/1/1), closed-trade equity by exit time.
def port(tag):
    P=[]
    for name,o,f,fo,ff,start,status in PAIRS:
        X=positions(load(fo if tag=='o' else ff)); P+=[p for p in X if p['edt']>=A(2020,1,1)]
    return {wn:stats([p for p in P if a<=p['edt']<b]) for wn,(a,b) in WIN.items()}
PO={'o':port('o'),'f':port('f')}
for t in 'of': print('portfolio',t,{w:(v['n'],v['net'],v['mdd'],v['streak'],v['mcl']) for w,v in PO[t].items()})
json.dump(PO,open('/tmp/claude-0/l1_l5_portfolio.json','w'),ensure_ascii=False,default=str,indent=1)
