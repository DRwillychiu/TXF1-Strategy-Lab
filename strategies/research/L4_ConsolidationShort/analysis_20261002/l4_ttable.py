import sys, json, datetime as dt, collections
sys.path.insert(0,'.')
from stopstruct import load, positions
A=dt.datetime
mc=json.load(open('/tmp/l4t_mc.json')); R=json.load(open('/tmp/l4t.json'))
V=['R0']+[f'T{i}' for i in range(1,7)]
ACC=300000
def f(x): return f"{x:,.0f}"
def pct(a,b): return (a-b)/abs(b)*100 if b else float('nan')
# calc extras
X={}
for n in V:
    P=sorted(positions(load(f'/tmp/L4{n}.xlsx')),key=lambda p:p['xdt'])
    eq=pk=0;pkd=P[0]['xdt'];uw=0;uws=None
    for p in P:
        eq+=p['pnl']
        if eq>=pk:
            if uws: uw=max(uw,(p['xdt']-uws).days)
            pk=eq;pkd=p['xdt'];uws=None
        elif uws is None: uws=pkd
    if uws: uw=max(uw,(A(2026,9,24)-uws).days)
    cr=sum(p['pnl'] for p in P if A(2025,4,7)<=p['xdt']<A(2025,4,9))
    X[n]=dict(uw=uw,crash=cr,ex=sum(p['pnl'] for p in P)-cr,y2024=sum(v for k,v in R[n]['yr'].items() if 2021<=int(k)<=2024))
rows=[ # name, getter, kind  (kind: 'gain' higher better, 'loss' magnitude lower better, 'cnt+' more better, 'cnt-' fewer better, 'r' ratio higher better)
 ('淨利',lambda n:mc[n]['淨利']/20,'gain'),
 ('最大策略虧損(盤中DD)',lambda n:-mc[n]['最大策略虧損']/20,'loss'),
 ('最大平倉交易虧損(平倉MDD)',lambda n:-mc[n]['最大平倉交易虧損']/20,'loss'),
 ('最大連續虧損金額',lambda n:-mc[n]['最大連續虧損金額']/20,'loss'),
 ('最大連續虧損次數(MC筆)',lambda n:mc[n]['最大連續虧損交易次數'],'cnt-'),
 ('最大單筆虧損',lambda n:-mc[n]['最大的交易虧損']/20,'loss'),
 ('毛利',lambda n:mc[n]['毛利']/20,'gain'),
 ('毛損',lambda n:-mc[n]['毛損']/20,'loss'),
 ('獲利因子',lambda n:mc[n]['獲利因子'],'r'),
 ('MC交易筆數',lambda n:mc[n]['交易總次數'],'cnt+'),
 ('MC勝率%',lambda n:mc[n]['%勝率'],'r'),
 ('滑價支付',lambda n:mc[n]['滑價支付']/20,'loss'),
 ('部位數(計算)',lambda n:R[n]['full']['n'],'cnt+'),
 ('部位連虧金額(計算)',lambda n:-R[n]['full']['stk'],'loss'),
 ('部位連虧次數(計算)',lambda n:R[n]['full']['stkn'],'cnt-'),
 ('部位勝率%(計算)',lambda n:R[n]['full']['win']*100,'r'),
 ('部位賺賠比(計算)',lambda n:R[n]['full']['pay'],'r'),
 ('最長水下天數(計算)',lambda n:X[n]['uw'],'cnt-'),
 ('2025/4/7-8 貢獻',lambda n:X[n]['crash'],'gain'),
 ('扣除4/7-8後淨利',lambda n:X[n]['ex'],'gain'),
 ('2021-2024 合計',lambda n:X[n]['y2024'],'gain'),
]
def fmt(v,k):
    return f"{v:.2f}" if k=='r' and v<10 else (f"{v:.1f}" if k=='r' else f(v))
def mark(d,k):
    if abs(d)<1e-9: return '＝'
    good = d>0 if k in('gain','cnt+','r') else d<0
    return '✅' if good else '❌'
out=[]
out.append('| 指標（微台元；損失以正數呈現＝越小越好） | '+' | '.join(V)+' |'); out.append('|'+'---|'*(len(V)+1))
for nm,g,k in rows: out.append(f'| {nm} | '+' | '.join(fmt(g(n),k) for n in V)+' |')
out.append('\nΔ金額 vs R0')
out.append('| 指標 | '+' | '.join(V[1:])+' |'); out.append('|'+'---|'*len(V))
for nm,g,k in rows:
    b=g('R0'); out.append(f'| {nm} | '+' | '.join(('+' if g(n)-b>0 else '')+fmt(g(n)-b,k)+mark(g(n)-b,k) for n in V[1:])+' |')
out.append('\nΔ% vs R0')
out.append('| 指標 | '+' | '.join(V[1:])+' |'); out.append('|'+'---|'*len(V))
for nm,g,k in rows:
    b=g('R0'); out.append(f'| {nm} | '+' | '.join(f"{pct(g(n),b):+.1f}%{mark(g(n)-b,k)}" if b else 'n/a' for n in V[1:])+' |')
out.append('\n佔帳戶 30萬 %')
out.append('| 指標 | '+' | '.join(V)+' |'); out.append('|'+'---|'*(len(V)+1))
for nm,g,k in rows[:6]:
    if k=='cnt-': continue
    out.append(f'| {nm} | '+' | '.join(f"{g(n)/ACC*100:.2f}%" for n in V)+' |')
out.append('\nBE 開關對照（BE on − BE off）')
out.append('| 指標 | T2−T1 | % | T4−T3 | % | T6−T5 | % |'); out.append('|---|---|---|---|---|---|---|')
for nm,g,k in rows[:12]:
    cells=[]
    for a,b in (('T2','T1'),('T4','T3'),('T6','T5')):
        d=g(a)-g(b); cells+= [('+' if d>0 else '')+fmt(d,k)+mark(d,k), f"{pct(g(a),g(b)):+.1f}%" if g(b) else 'n/a']
    out.append(f'| {nm} | '+' | '.join(cells)+' |')
out.append('\n樣本內 2021/9/16–2026/6/16 ／ 樣本外 2026/6/17–9/17（部位計算）')
out.append('| 版本 | IS部位 | IS淨利 | ΔIS淨利 | IS MDD | ΔIS MDD% | IS連虧(次) | OOS部位 | OOS淨利 | ΔOOS |'); out.append('|'+'---|'*10)
for n in V:
    I=R[n]['IS'];O=R[n]['OOS'];bI=R['R0']['IS'];bO=R['R0']['OOS']
    out.append(f"| {n} | {I['n']} | {f(I['net'])} | {pct(I['net'],bI['net']):+.1f}% | {f(-I['mdd'])} | {pct(-I['mdd'],-bI['mdd']):+.1f}% | {f(-I['stk'])}({I['stkn']}) | {O['n']} | {f(O['net'])} | {('+' if O['net']-bO['net']>0 else '')+f(O['net']-bO['net'])} |")
out.append('\n年度淨利（部位計算，依出場年）')
ys=sorted({int(y) for n in V for y in R[n]['yr']})
out.append('| 年 | '+' | '.join(V)+' |'); out.append('|'+'---|'*(len(V)+1))
for y in ys: out.append(f'| {y} | '+' | '.join(f(R[n]['yr'].get(str(y),0)) for n in V)+' |')
open('/tmp/l4t_tables.md','w').write('\n'.join(out)); print('\n'.join(out))
