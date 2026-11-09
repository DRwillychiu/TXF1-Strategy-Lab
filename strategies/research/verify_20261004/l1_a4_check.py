# A4: L1 V3.8 single-chart alias report vs V3.7 G4 (trade by trade) + G2 settings.
import sys, re, openpyxl, collections
sys.path.insert(0,'/home/claude/repo/strategies/research/L1_TrendLong/analysis_20261002')
import stopstruct
F=sys.argv[1]
wb=openpyxl.load_workbook(F,read_only=True,data_only=True)
print('sheets',wb.sheetnames)
S={}
for r in wb['策略分析'].iter_rows(values_only=True):
    r=[x for x in r if x is not None]
    if len(r)>=2 and isinstance(r[0],str) and r[0] in ('淨利','最大策略虧損','最大平倉交易虧損','最大策略虧損日期'): S[r[0]]=r[1]
for r in wb['交易分析'].iter_rows(values_only=True):
    r=[x for x in r if x is not None]
    if len(r)>=2 and r[0]=='交易總次數': S['交易總次數']=r[1]
print('summary',S)
st=[[x for x in r if x is not None] for r in wb['設定'].iter_rows(values_only=True)]
st=[r for r in st if r]
gen={r[0]:r[1] for r in st if len(r)>=2 and r[0] in ('商品名稱','原始資本','佣金','回測基本假設','滑價','壓縮','細部資料','開始日期','結束日期','回測模式')}
print('settings',gen)
# G2 inputs
src=open('/home/claude/repo/strategies/research/L1_TrendLong/L1_v3.8/L1_TrendLong_v3.8.pla').read()
c=re.sub(r'\{[^}]*\}','',src); body=re.search(r'(?is)\binputs\s*:(.*?);',c).group(1)
d=dict(re.findall(r'([A-Za-z_]\w*)\s*\(\s*([^)]*?)\s*\)',body))
rep={r[0]:r[1] for r in st if len(r)==2 and r[0] in d}
norm=lambda v:(lambda s:{'true':1.0,'false':0.0}.get(s,float(s) if s.replace('.','',1).lstrip('-').isdigit() else s))(str(v).strip().lower())
print('G2 inputs pla',len(d),'report',len(rep),'diff',[(k,d[k],rep.get(k)) for k in d if norm(d[k])!=norm(rep.get(k))])
A=stopstruct.load(F); G=stopstruct.load('/tmp/L1_G4.xlsx')
print('first trade',A[0]['edt'],A[0]['epx'],A[0]['xsig'],A[0]['xdt'],A[0]['xpx'],A[0]['pnl'])
end=max(t['xdt'] for t in G)
Aw=[t for t in A if t['xdt']<=end]
ka=[(t['edt'],t['epx'],t['xdt'],t['xpx'],t['xsig'],t['pnl']) for t in Aw]; kg=[(t['edt'],t['epx'],t['xdt'],t['xpx'],t['xsig'],t['pnl']) for t in G]
same=len(set(ka)&set(kg)); print('A4 rows',len(A),'within G4 end',len(Aw),'G4',len(G),'same',same,'netA_window',sum(t['pnl'] for t in Aw),'netG',sum(t['pnl'] for t in G))
diff=sorted(set(ka)^set(kg))[:6]; print('first diffs',diff)
print('after G4 end',[(str(t['edt']),t['xsig'],t['pnl']) for t in A if t['xdt']>end])
