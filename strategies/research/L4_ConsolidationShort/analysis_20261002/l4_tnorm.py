import sys, datetime as dt
sys.path.insert(0,'.')
from stopstruct import load, positions
NOW=44813  # 2026/08/20 L4 entry price = latest known index level in data
V=['R0']+[f'T{i}' for i in range(1,7)]
base=None
print('| 版本 | 現價換算淨利 | 現價MDD | %帳戶 | 現價連虧金額(次) | %帳戶 | 現價最大單筆 | 點/口 | %帳戶 |')
for n in V:
    P=sorted(positions(load(f'/tmp/L4{n}.xlsx')),key=lambda p:p['xdt'])
    eq=pk=mdd=s=c=0;k=cn=0;big=0
    for p in P:
        x=p['pnl']/p['epx']*NOW
        eq+=x;pk=max(pk,eq);mdd=min(mdd,eq-pk);big=min(big,x)
        if x<0:c+=x;cn+=1
        else:c=0;cn=0
        if c<s:s=c;k=cn
    print(f"| {n} | {eq:,.0f} | {-mdd:,.0f} | {-mdd/3000:.1f}% | {-s:,.0f}({k}) | {-s/3000:.1f}% | {-big:,.0f} | {-big/20:.0f} | {-big/3000:.2f}% |")
