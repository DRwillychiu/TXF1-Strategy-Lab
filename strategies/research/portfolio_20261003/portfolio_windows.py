# The 8 two-year MC portfolio files (Willy 10/3 19:52): summary + first trade per strategy (warm-up check).
import openpyxl, json, datetime as dt
U='/root/.claude/uploads/80321d76-5295-5bee-b187-42c9b8d27a01/'
F=[('2018-2019','cd74504b'),('2019-2020','6a3039ea'),('2020-2021','a2e3a362'),('2021-2022','b048002f'),('2022-2023','efe197dd'),('2023-2024','fa00cd6c'),('2024-2025','56cbd389'),('2025-2026','1fcb784a')]
MAP=['L1','L2','L5','L3','L4']   # 商品概要 order: 45m, 60m, 15m(L5), 15m(L3), 15m(L4)
import glob
out=[]
for lab,p in F:
    f=glob.glob(U+p+'*')[0]; wb=openpyxl.load_workbook(f,read_only=True,data_only=True)
    kv=lambda sh:{r[0].strip():r[1] for r in ([x for x in rr if x is not None] for rr in wb[sh].iter_rows(values_only=True)) if len(r)>=2 and isinstance(r[0],str)}
    s,t,st=kv('策略分析'),kv('交易分析'),kv('設定')
    pc=[[x for x in r] for r in list(wb['商品概要'].iter_rows(values_only=True))[2:]]
    pc=[[x for x in r if x is not None] for r in pc]; pc=[r for r in pc if r and str(r[0]).startswith('TXF1')]
    per={MAP[i]:dict(first=str(r[1])[:10],net=(r[3]/20 if isinstance(r[3],(int,float)) else None),n=r[4]) for i,r in enumerate(pc)}
    out.append(dict(win=lab,start=str(st['開始日期'])[:10],end=str(st['結束日期'])[:10],net=s['淨利']/20,pf=round(s['獲利因子'],2),rows=t['交易總次數'],
                    winp=round(t['勝率'],1),dd=s['投組最大可能虧損']/20,cdd=s['投組最大平倉交易虧損']/20,per=per))
json.dump(out,open('/tmp/claude-0/pf_windows.json','w'),ensure_ascii=False,indent=1)
for o in out: print(o['win'],o['start'],o['end'],o['net'],o['pf'],o['rows'],o['winp'],o['dd'],o['cdd'],{k:(v['first'],v['n']) for k,v in o['per'].items()})
