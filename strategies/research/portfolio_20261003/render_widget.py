import json
E=json.load(open('/tmp/claude-0/pf_eval2.json')); W=json.load(open('/tmp/claude-0/pf_windows.json'))
mc,fx=E['mc'],E['fix']
M=lambda v:'—' if v is None else ('−' if v<0 else '')+f"{abs(round(v)):,}"
P=lambda v:'—' if v is None else ('−' if v<0 else '')+f"{abs(v):.1f}%"
ACC=300000
def row(cells,cls=''):
    return '<tr'+(f' class="{cls}"' if cls else '')+'>'+''.join(f'<td>{c}</td>' for c in cells)+'</tr>'
def table(head,rows,widths=None):
    cg=''.join(f'<col style="width:{w}">' for w in widths) if widths else ''
    return '<div class="tw"><table><colgroup>'+cg+'</colgroup><tr>'+''.join(f'<th>{h}</th>' for h in head)+'</tr>'+''.join(rows)+'</table></div>'
ddi={'ALL':-56000,'L1':-62540,'L1s':-40140,'L2':-31500,'L3':-31560,'L4':-19540,'L5':-51900}
first={'ALL':'2018/04/20','L1':'2019/12/16','L1s':'2019/12/16','L2':'2018/04/20','L3':'2018/05/17','L4':'2018/07/07','L5':'2019/12/20'}
cols=[('ALL',mc['full']['ALL']),('FIX',fx['full']['ALL']),('L1',mc['full']['L1']),('L1s',fx['full']['L1']),('L2',mc['full']['L2']),('L3',mc['full']['L3']),('L4',mc['full']['L4']),('L5',mc['full']['L5'])]
H=['指標','組合 MC','組合 L1換單圖（估）','L1 組合內','L1 單圖','L2','L3','L4','L5']
def r(lbl,f): return row([lbl]+[f(k,v) for k,v in cols])
R=[r('首筆交易',lambda k,v:first.get(k,'2018/04/20')),
   r('淨利',lambda k,v:M(v['net'])),
   r('淨利 / 30 萬',lambda k,v:P(100*v['net']/ACC)),
   r('部位數',lambda k,v:f"{v['n']:,}"),
   r('勝率',lambda k,v:f"{v['win']}%"),
   r('獲利因子',lambda k,v:f"{v['pf']:.2f}"),
   r('最大策略虧損（含持倉）',lambda k,v:'—' if k=='FIX' else M(ddi[k])),
   r('　佔 30 萬',lambda k,v:'—' if k=='FIX' else P(100*ddi[k]/ACC)),
   r('平倉 MDD',lambda k,v:M(v['mdd'])),
   r('　佔 30 萬',lambda k,v:P(v['mdd_pct'])),
   r('　期間',lambda k,v:f"{v['dd_from'][2:].replace('-','/')}→{v['dd_to'][2:].replace('-','/')}"),
   r('最大連虧金額',lambda k,v:M(v['streak'])),
   r('最大連虧次數',lambda k,v:str(v['mcl'])),
   r('最大單筆虧損',lambda k,v:M(v['worst']))]
mcy={2026:320330,2025:224150,2024:64010,2023:22530,2022:6320,2021:6320,2020:57340,2019:4460,2018:-9630}
Y=[]
for y in range(2018,2027):
    a=mc['year'][str(y)]['ALL']; b=fx['year'][str(y)]['ALL']
    Y.append(row([str(y)+('（至 9/24）' if y==2026 else ''),M(mcy[y]),P(100*mcy[y]/ACC),f"{a['pf']:.2f}",str(a['n']),f"{a['win']}%",M(a['mdd']),M(a['streak']),str(a['mcl']),M(b['net']),M(b['mdd'])],'neg' if mcy[y]<0 else ''))
S=[]
for y in range(2018,2027):
    v=mc['year'][str(y)]; f=fx['year'][str(y)]
    S.append(row([str(y)]+[M(v[k]['net']) if v[k] else '—' for k in ['L1']]+[M(f['L1']['net']) if f['L1'] else '—']+[M(v[k]['net']) if v[k] else '—' for k in ['L2','L3','L4','L5']]))
WR=[]
for w in W:
    p=w['per']
    WR.append(row([w['win'],w['start'][2:].replace('-','/')+'→'+w['end'][2:].replace('-','/'),M(w['net']),f"{w['pf']:.2f}".replace('-','−'),str(w['rows']),M(w['dd']),M(w['cdd']),p['L1']['first'][2:].replace('-','/') if p['L1']['first']!='n/a' else '未交易',p['L5']['first'][2:].replace('-','/') if p['L5']['first']!='n/a' else '未交易']))
C=[['','L1','L2','L3','L4','L5'],['L1','1','0.02','0.04','0.01','0.20'],['L2','','1','0.01','<b>0.37</b>','0.08'],['L3','','','1','−0.02','0.06'],['L4','','','','1','0.06'],['L5','','','','','1']]
html=f'''<h2 class="sr-only">L1 到 L5 定案版組合績效：MC 組合報表 2018/4 至 2026/9，最大策略虧損 −56,000（帳戶 18.7%），平倉 MDD −40,640。</h2>
<style>.tw{{overflow-x:auto;margin:0 0 1.25rem}}table{{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums;table-layout:fixed}}th{{text-align:right;font-weight:500;padding:6px 6px;border-bottom:1px solid var(--border-strong);color:var(--text-secondary)}}td{{text-align:right;padding:5px 6px;border-bottom:0.5px solid var(--border)}}th:first-child,td:first-child{{text-align:left}}tr:nth-child(even) td{{background:var(--surface-1)}}tr.neg td{{color:var(--text-danger)}}.cap{{font-size:13px;color:var(--text-secondary);margin:1.25rem 0 .4rem}}.k{{font-size:12px;letter-spacing:.1em;color:var(--text-secondary)}}</style>
<div style="background:var(--surface-1);border-radius:12px;padding:1.25rem 1.5rem;margin:0 0 1rem">
<div style="font-size:13px;color:var(--text-secondary)">L1–L5 定案版組合｜MC 組合報表 2018/4/20–2026/9/24｜微台 2 口（MC ÷ 20），帳戶 30 萬</div>
<div style="font-size:26px;font-weight:500;margin:6px 0">8.4 年淨賺 695,830，最大回落 −56,000（帳戶 18.7%）</div>
<div style="font-size:14px;line-height:1.65;color:var(--text-secondary)">最大回落與平倉 MDD 都發生在 2026 年 7 月。L2、L3、L4 與單圖逐筆相同；L1 在組合報表裡跑出來和單圖不同，上線看單圖。</div></div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:0 0 1.25rem">
<div style="border:0.5px solid var(--border);border-radius:12px;padding:1rem 1.25rem"><div class="k">與單圖逐筆相同</div><div style="font-size:34px;font-weight:500">4<span style="font-size:18px;color:var(--text-secondary)"> / 5</span></div><div style="font-size:13px;line-height:1.9;color:var(--text-secondary)">L2 v5.11：96／96（2020/1/31 起）<br>L3 v18.4：469／469<br>L4 v14.10：135／135（2020/2/21 起）<br>L5 v19.20：＝桌機 v19.18，多 10 筆（2026 年損失記憶未擋，符合 1261005）</div></div>
<div style="border:2px solid var(--border-accent);border-radius:12px;padding:1rem 1.25rem"><div class="k">不同</div><div style="font-size:34px;font-weight:500">L1<span style="font-size:18px;color:var(--text-secondary)"> 283 / 461</span></div><div style="font-size:13px;line-height:1.9;color:var(--text-secondary)">組合內出場晚一根 45 分 K（結算 12:30→13:15、假日 03:45→04:30）<br>行為像 IOG 關（原因未確認）<br>淨利 198,580 vs 單圖 231,720<br>最大策略虧損 −62,540 vs 單圖 −40,140</div></div></div>
<div class="cap">完整指標（全期）</div>
{table(H,R,['19%']+['10.1%']*8)}
<div class="cap">逐年（全期一次回測，依年度切）｜淨利、佔帳戶取 MC 年度分析；其餘依出場日計算</div>
{table(['年度','淨利','佔 30 萬','PF','部位','勝率','平倉 MDD','連虧金額','連虧次數','L1換單圖 淨利（估）','L1換單圖 MDD（估）'],Y,['13%','9%','8%','6%','6%','7%','9%','9%','7%','13%','13%'])}
<div class="cap">各策略逐年淨利（依出場日）</div>
{table(['年度','L1 組合內','L1 單圖','L2','L3','L4','L5'],S)}
<div class="cap">8 份分段報表（原樣）｜L1、L5 要約 2 年暖機，分段裡幾乎沒交易，不能當年度績效</div>
{table(['檔案','交易期間','淨利','PF','列數','最大回落','平倉回落','L1 首筆','L5 首筆'],WR,['10%','17%','10%','7%','7%','11%','11%','13%','14%'])}
<div class="cap">日權益相關係數（MC）｜最高 L2–L4 0.37（兩支空單）</div>
{table(C[0],[row(c) for c in C[1:]])}
<div style="background:var(--surface-1);border-radius:12px;padding:1rem 1.25rem;font-size:13px;line-height:1.8">
一、更正：10/3 17:08 比對表估算組合平倉 MDD −34,210（11.4%）。MC 組合實測 −40,640（13.5%），最大策略虧損 −56,000（18.7%）。主因 L5 跑全預設（1261005）路徑與桌機資料。<br>
二、月度：102 個月中 34 個月虧損，最長連 5 個月；最差 2026/9 −18,340，最佳 2026/4 ＋119,660。<br>
三、組合最大回落 −56,000 只有五支各自最大回落合計（−197,040）的 28%。</div>'''
open('/tmp/claude-0/pf_widget.html','w').write(html); print(len(html))
