import sys
sys.path.insert(0,'.')
from stopstruct import load, positions
P=sorted(positions(load('/mnt/user-data/uploads/TXF1__L4_ConsolidationShort_策略回測績效報告_上架版本.xlsx')),key=lambda p:p['edt'])
def stats(seq):
    eq=pk=mdd=st=cur=0
    for x in seq:
        eq+=x; pk=max(pk,eq); mdd=min(mdd,eq-pk)
        cur = cur+x if x<0 else 0; st=min(st,cur)
    return round(eq),round(mdd),round(st),len(seq)
base=[p['pnl'] for p in P]
print('上架版', stats(base))
def skipnext(n,k=1):
    out=[];c=0;skip=0
    for x in base:
        if skip>0: skip-=1; c=0; continue
        out.append(x)
        c = c+1 if x<0 else 0
        if c>=n: skip=k; c=0
    return out
def shadow(n):
    # after n consecutive real losses, stop trading; resume after the first virtual win
    out=[];c=0;off=False
    for x in base:
        if off:
            if x>0: off=False; c=0
            continue
        out.append(x); c=c+1 if x<0 else 0
        if c>=n: off=True
    return out
for n in (2,3,4):
    print(f'連虧{n}→跳過下一筆', stats(skipnext(n)))
for n in (2,3):
    print(f'連虧{n}→停到虛擬單賺錢', stats(shadow(n)))
