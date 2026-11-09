# Render L1-L5 original vs final comparison (comparison-table SKILL layout) -> widget HTML + markdown.
import json
D=json.load(open('/tmp/claude-0/l1_l5_compare.json')); PO=json.load(open('/tmp/claude-0/l1_l5_portfolio.json'))
M='−'; ACC=300000
def n0(v): return (M if v<0 else '')+f'{abs(round(v)):,}'
def f2(v): return (M if v<0 else '')+f'{abs(v):.2f}'
# metric spec: (label, getter, kind) kind: 'gain' higher better, 'loss' negative values smaller magnitude better,
# 'cnt_low' lower better, 'pt' percentage points higher better, 'acct' account % lower better, 'neutral'
def rows_for(o,f,odd,fdd):
    a,b=o['全期'],f['全期']
    return [
     ('淨利（全期）',a['net'],b['net'],'gain'),
     ('交易筆數（部位）',a['n'],b['n'],'neutral'),
     ('勝率',a['win'],b['win'],'pt'),
     ('獲利因子',a['pf'],b['pf'],'gainf'),
     ('平均每筆',a['avg'],b['avg'],'gain'),
     ('賺賠比',a['wl'],b['wl'],'gainf'),
     ('最大策略虧損（含持倉）',odd,fdd,'loss'),
     ('平倉 MDD',a['mdd'],b['mdd'],'loss'),
     ('平倉 MDD 佔帳戶',-a['mdd']/ACC*100,-b['mdd']/ACC*100,'acct'),
     ('最大連虧金額',a['streak'],b['streak'],'loss'),
     ('最大連續虧損次數',a['mcl'],b['mcl'],'cnt_low'),
     ('最大單筆虧損',a['maxloss'],b['maxloss'],'loss'),
     ('近兩年淨利（2024/10～）',o['近兩年']['net'],f['近兩年']['net'],'gain'),
     ('近兩年平倉 MDD',o['近兩年']['mdd'],f['近兩年']['mdd'],'loss'),
     ('2026 淨利',o['2026']['net'],f['2026']['net'],'gain'),
     ('樣本外淨利（6/17～9/24）',o['樣本外']['net'],f['樣本外']['net'],'gain'),
    ]
def fmt(v,kind):
    if v is None: return '—'
    if kind in ('gainf',): return f2(v)
    if kind=='pt': return f'{v:.1f}%'
    if kind=='acct': return f'{v:.1f}%'
    return n0(v)
def delta(o,f,kind):
    """returns (diff_text, pct_text, verdict) verdict: good/bad/same/na"""
    if o is None or f is None: return '—','—','na'
    if kind in ('pt','acct'):
        d=f-o; t=('+' if d>0 else (M if d<0 else '±'))+f'{abs(d):.1f} pt'
        good = d>0 if kind=='pt' else d<0
        return t,'—',('same' if abs(d)<0.05 else ('good' if good else 'bad'))
    d=f-o
    dt=('±0' if d==0 else (('+' if d>0 else M)+(f'{abs(d):.2f}' if kind=='gainf' else f'{abs(round(d)):,}')))
    if kind=='loss':
        if o==0: return dt,'—','na'
        p=(abs(f)-abs(o))/abs(o)*100
        return dt,('±0%' if abs(p)<0.05 else (('+' if p>0 else M)+f'{abs(p):.1f}%')),('same' if d==0 else ('good' if p<0 else 'bad'))
    if kind=='cnt_low':
        p=(f-o)/o*100 if o else 0
        return dt,('±0%' if d==0 else (('+' if p>0 else M)+f'{abs(p):.1f}%')),('same' if d==0 else ('good' if d<0 else 'bad'))
    if o==0: return dt,'原本 0 筆' if kind!='neutral' else '—',('good' if f>0 else 'same')
    if o<0 and f>0: return dt,'由負轉正','good'
    p=(f-o)/abs(o)*100
    v='same' if d==0 else (('good' if d>0 else 'bad') if kind!='neutral' else 'neutral')
    return dt,('±0%' if d==0 else (('+' if p>0 else M)+f'{abs(p):.1f}%')),v
COL={'good':'g','bad':'b','same':'s','na':'s','neutral':'n'}


html=[]; md=[]
for r in D:
    o,f=r['o'],r['f']; R=rows_for(o,f,o['dd_intraday'],f['dd_intraday'])
    note=f"（兩版共同期間 {r['start']} 起）" if r['start'] else ''
    html.append(f'<tr class="h"><td colspan="5"><b>{r["name"]}</b><span>　{r["orig"]} → {r["final"]}　｜　{r["status"]}{note}</span></td></tr>')
    md.append(f"\n### {r['name']}：{r['orig']} → {r['final']}（{r['status']}）{note}\n\n| 指標 | 原始 | 定案 | 變化 | 變化% |\n|---|---|---|---|---|")
    for i,(lab,a,b,k) in enumerate(R):
        dt,pt,v=delta(a,b,k); z=' class="z"' if i%2 else ''
        html.append(f'<tr{z}><td>{lab}</td><td>{fmt(a,k)}</td><td>{fmt(b,k)}</td><td class="{COL[v]}">{dt}</td><td class="{COL[v]}">{pt}</td></tr>')
        md.append(f'| {lab} | {fmt(a,k)} | {fmt(b,k)} | {dt} | {pt} |')
# portfolio
po,pf=PO['o'],PO['f']
P=[('淨利（2020 起）',po['全期']['net'],pf['全期']['net'],'gain'),('交易筆數（部位）',po['全期']['n'],pf['全期']['n'],'neutral'),
   ('平倉 MDD',po['全期']['mdd'],pf['全期']['mdd'],'loss'),('平倉 MDD 佔帳戶',-po['全期']['mdd']/ACC*100,-pf['全期']['mdd']/ACC*100,'acct'),
   ('最大連虧金額',po['全期']['streak'],pf['全期']['streak'],'loss'),('最大連續虧損次數',po['全期']['mcl'],pf['全期']['mcl'],'cnt_low'),
   ('近兩年淨利',po['近兩年']['net'],pf['近兩年']['net'],'gain'),('近兩年平倉 MDD',po['近兩年']['mdd'],pf['近兩年']['mdd'],'loss'),
   ('2026 淨利',po['2026']['net'],pf['2026']['net'],'gain'),('樣本外淨利',po['樣本外']['net'],pf['樣本外']['net'],'gain'),('樣本外平倉 MDD',po['樣本外']['mdd'],pf['樣本外']['mdd'],'loss')]
ph=[]; md.append('\n### 五支合計（同一個 30 萬帳戶同時跑；2020/1/1 起進場；以出場時間累計）\n\n| 指標 | 原始五支 | 定案五支 | 變化 | 變化% |\n|---|---|---|---|---|')
for i,(lab,a,b,k) in enumerate(P):
    dt,pt,v=delta(a,b,k); z=' class="k"' if lab=='平倉 MDD' else (' class="z"' if i%2 else '')
    ph.append(f'<tr{z}><td>{lab}</td><td>{fmt(a,k)}</td><td>{fmt(b,k)}</td><td class="{COL[v]}">{dt}</td><td class="{COL[v]}">{pt}</td></tr>')
    md.append(f'| {lab} | {fmt(a,k)} | {fmt(b,k)} | {dt} | {pt} |')
open('/tmp/claude-0/cmp_rows.html','w').write('\n'.join(html)); open('/tmp/claude-0/cmp_port.html','w').write('\n'.join(ph))
open('/tmp/claude-0/cmp.md','w').write('\n'.join(md))
# headline numbers
st=[(r['name'][:2],round((abs(r['f']['全期']['streak'])-abs(r['o']['全期']['streak']))/abs(r['o']['全期']['streak'])*100,1)) for r in D]
print(st)
print('port mdd %',round((abs(pf['全期']['mdd'])-abs(po['全期']['mdd']))/abs(po['全期']['mdd'])*100,1),'net %',round((pf['全期']['net']-po['全期']['net'])/po['全期']['net']*100,1))
