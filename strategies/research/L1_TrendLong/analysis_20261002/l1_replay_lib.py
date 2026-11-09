# L1 V3.2 (live inputs) replay on 1-minute data (Willy 23:47 file TXF1_1_分鐘_2.txt). Estimate, NOT MC.
# Synthetic ticks per minute: O, then L,H (if C>=O) or H,L (if C<O), then C.  mode='worst' -> always L before H.
import datetime as dt, sys, collections, numpy as np
F='/mnt/user-data/uploads/TXF1_1_分鐘_2.txt'
START=dt.datetime(2023,1,2)
MODE=sys.argv[1] if len(sys.argv)>1 else 'std'
P0=dict(L60=61,EM=2.0,SLM=1.5,DCM=0.5,SLP=0.5,L20=55,TO=50,SPP=200,SPR=55,ATRL=20,WF=20,WS=60,RE_ON=1,RE_RATIO=0.2)
mins=[]
with open(F) as fh:
    next(fh)
    for line in fh:
        p=line.split(',')
        y,m,d=map(int,p[0].split('/'))
        t=dt.datetime(y,m,d,int(p[1][:2]),int(p[1][3:5]))
        if t<START: continue
        mins.append((t,float(p[2]),float(p[3]),float(p[4]),float(p[5])))
def bar_end(t):
    hm=t.hour*100+t.minute
    if 846<=hm<=1345:
        base=t.replace(hour=8,minute=45); k=(int((t-base).total_seconds()//60)-1)//45
        e=base+dt.timedelta(minutes=45*(k+1)); cap=t.replace(hour=13,minute=45); return min(e,cap)
    if hm>=1501:
        base=t.replace(hour=15,minute=0)
    elif hm<=500:
        base=(t-dt.timedelta(days=1)).replace(hour=15,minute=0)
    else: return None
    k=(int((t-base).total_seconds()//60)-1)//45
    e=base+dt.timedelta(minutes=45*(k+1)); cap=(base+dt.timedelta(days=1)).replace(hour=5,minute=0); return min(e,cap)
bars=collections.OrderedDict()
for m in mins:
    e=bar_end(m[0])
    if e is None: continue
    bars.setdefault(e,[]).append(m)
BE=list(bars)
O=np.array([bars[e][0][1] for e in BE]); H=np.array([max(x[2] for x in bars[e]) for e in BE]); L=np.array([min(x[3] for x in bars[e]) for e in BE]); C=np.array([bars[e][-1][4] for e in BE])
def sma(x,n): 
    out=np.full(len(x),np.nan); cs=np.cumsum(np.r_[0,x])
    out[n-1:]=(cs[n:]-cs[:-n])/n; return out
pc=np.r_[C[0],C[:-1]]; TR=np.maximum(H,pc)-np.minimum(L,pc)
maBase=sma(C,P0['L60']); maTrail=sma(C,P0['L20']); ATR=sma(TR,P0['ATRL'])
# daily (desktop composition: key = date if hm<=1345 else date+1)
dd=collections.OrderedDict()
for m in mins:
    t=m[0]; hm=t.hour*100+t.minute
    if not (846<=hm<=1345 or hm>=1501 or hm<=500): continue
    k=t.date() if hm<=1345 else t.date()+dt.timedelta(days=1)
    b=dd.get(k)
    if b is None: dd[k]=[m[1],m[2],m[3],m[4]]
    else: b[1]=max(b[1],m[2]); b[2]=min(b[2],m[3]); b[3]=m[4]
DK=list(dd); DH=np.array([dd[k][1] for k in DK]); DL=np.array([dd[k][2] for k in DK]); DC=np.array([dd[k][3] for k in DK])
dpc=np.r_[DC[0],DC[:-1]]; DTR=np.maximum(DH,dpc)-np.minimum(DL,dpc); DATR=sma(DTR,P0['ATRL']); DM20=sma(DC,20); DM60=sma(DC,60)
import bisect
def dtrend_prev(e, slope=0):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    i=bisect.bisect_left(DK,k)
    ok=DM20[i-1]>DM60[i-1]
    if slope>0 and DM60[i-1]>DM60[i-1-slope]: ok=True   # v3.5 #31: MA slow rising vs N days ago
    return ok
def daily_atr_prev(e):  # [1] of Data2 = previous completed daily bar relative to current daily bar
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    i=bisect.bisect_left(DK,k)   # index of current daily bar (in progress)
    return DATR[i-1] if i-1>=0 else np.nan
wk=collections.OrderedDict()
for i,k in enumerate(DK): wk[k.isocalendar()[:2]]=i
WK=list(wk); WC=np.array([DC[wk[k]] for k in WK]); W20=sma(WC,P0['WF']); W60=sma(WC,P0['WS'])
def weekly_ok(e):
    k=e.date() if e.hour*100+e.minute<=1345 else e.date()+dt.timedelta(days=1)
    wkey=k.isocalendar()[:2]; j=WK.index(wkey)
    # current week in progress: use latest close (bar close price) vs MAs of completed weeks incl. current? use completed weeks MAs and current price
    c=C[BE.index(e)] if False else None
    return j
HOL={dt.date(2026,1,1),dt.date(2026,2,12),dt.date(2026,2,27),dt.date(2026,4,3),dt.date(2026,5,1),dt.date(2026,6,19),dt.date(2026,9,25),dt.date(2025,1,1),dt.date(2025,1,23),dt.date(2025,2,28)}
def settle(d): return d.weekday()==2 and 15<=d.day<=21
SLIP=10 # points per lot round trip (MC 1000/contract/side on TXF = 5 pts/side)
P=dict(P0)
def run(SIM_START, OV):
    global P
    P=dict(P0); P.update(OV)
    trades=[]; pos=None; pend=None; prevMP=0
    armed=False; reP=0; frozGap=0; frozSLorig=0; lastEntry=0
    lossrun=0; skipleft=0; ntr=0; daykey=None; daylr=0; dayblk=False
    eng_D=0
    idx_of={e:i for i,e in enumerate(BE)}
    sim_start=SIM_START
    for i,e in enumerate(BE):
        if e<sim_start: continue
        ms=bars[e]
        ticks=[]
        for (t,o,h,l,c) in ms:
            if MODE=='worst' or c>=o: seq=[o,l,h,c]
            else: seq=[o,h,l,c]
            ticks+= [(t,x) for x in seq]
        hm=e.hour*100+e.minute
        tdate=e.date()
        hol_tail=(tdate in HOL and hm<=500)
        mtrail_prev=maTrail[i-1]
        for j,(t,px) in enumerate(ticks):
            # 1) pending entry from previous bar close (only first tick)
            if pos is None and pend and (j==0 or (pend[0]=='stop' and P.get('RE_PERSIST',0))):
                typ,lvl,isre,D0=pend
                fill=None
                if typ=='mkt': fill=px
                elif px>=lvl: fill=px if j==0 else max(px,lvl) if False else lvl if px>=lvl and j>0 else px
                if fill is not None:
                    pos=dict(entry=fill,et=t,eb=e,isre=isre,locked=False,froz=0,peak=0,spf=0,trail=0,eng=fill-D0,final=None,gapx=False)
                if fill is not None or not (pend[0]=='stop' and P.get('RE_PERSIST',0)): pend=None
                if pos is not None: 
                    pos['final']=max(pos['eng'],0); continue
            if pos is not None:
                # pending gap market exit
                if pos.get('gapx') and j==0:
                    trades.append((pos['et'],t,pos['entry'],px,pos['isre'],'GAP')); pos=None; continue
                # pending force exit
                if pos.get('fx') and j>0 or (pos.get('fx') and j==0):
                    trades.append((pos['et'],t,pos['entry'],px,pos['isre'],pos['fx'])); pos=None; continue
                # stop check vs orders from previous tick (final and engine stop)
                stopl=max(pos['final'] if pos['final'] else 0, pos['eng'])
                if px<=stopl:
                    prev=ticks[j-1][1] if j>0 else None
                    fillp = stopl if (prev is not None and prev>stopl and j%4!=0) else px
                    tag='SP' if (pos['spf']>0 and abs(stopl-pos['spf'])<1e-9) else ('ENG/SL' if stopl in (pos['eng'],pos['froz']) else 'TRAIL')
                    trades.append((pos['et'],t,pos['entry'],fillp,pos['isre'],tag)); pos=None; continue
                # update SP / trail / final on this tick
                if px-pos['entry']>=P['SPP']:
                    pos['peak']=max(pos['peak'],px-pos['entry']); pos['spf']=pos['entry']+pos['peak']*(1-P['SPR']/100)
                pos['trail']=max(pos['trail'], mtrail_prev-P['TO'])
                pos['final']=max(pos['trail'],pos['froz'],pos['spf'])
                # force exits (settlement / holiday) evaluated each tick
                if settle(tdate) and hm>=1230: pos['fx']='SETTLE'
                if hol_tail and hm>=345: pos['fx']='HOL'
        # ---- bar close (BarStatus=2) ----
        dk=e.date()+dt.timedelta(days=1 if e.hour*100+e.minute>=1500 else 0)
        if dk!=daykey: daykey=dk; daylr=0; dayblk=False
        while ntr<len(trades):
            x=(trades[ntr][3]-trades[ntr][2]-SLIP)
            daylr = daylr+1 if x<0 else 0
            if P.get('DN',0)>0 and daylr>=P['DN']: dayblk=True
            lossrun = lossrun+1 if x<0 else 0
            if P.get('PN',0)>0 and lossrun>=P['PN']: skipleft=P.get('PK',1); lossrun=0
            ntr+=1
        MP=1 if pos else 0
        if pos is not None:
            if not pos['locked']:
                ep=pos['entry']
                legs=max(ep-ATR[i]*P['SLM'], ep-daily_atr_prev(e)*P['DCM'], ep-ep*P['SLP']/100, ep-P.get('SLMAX',10**9))
                if pos['isre'] and frozSLorig>0: pos['froz']=max(frozSLorig,legs)
                else:
                    pos['froz']=legs; frozSLorig=legs; frozGap=ep-maBase[i]
                pos['locked']=True; lastEntry=ep
                pos['final']=max(pos['trail'],pos['froz'],pos['spf'])
            lastEntry=pos['entry']
            # trail uses this bar's maTrail from now on
            pos['trail']=max(pos['trail'], maTrail[i]-P['TO']); pos['final']=max(pos['trail'],pos['froz'],pos['spf'])
            if C[i]<pos['final']: pos['gapx']=True
        # weekly filter: completed weeks MA, current price vs MA (approx)
        k=e.date() if hm<=1345 else e.date()+dt.timedelta(days=1)
        wj=WK.index(k.isocalendar()[:2]); wf=(C[i]>W20[wj-1]) or (C[i]>W60[wj-1])
        trendr=(C[i]-maBase[i])/frozGap if frozGap>0 else 0
        if prevMP==1 and MP==0 and frozGap>0: armed=True; reP=lastEntry
        if armed and (trendr<=0 or not wf): armed=False; reP=0
        brk=C[i]>maBase[i]+ATR[i]*P['EM'] and C[i-1]<=maBase[i-1]+ATR[i-1]*P['EM']
        if brk: armed=False; reP=0
        blocked=hol_tail or settle(tdate)
        dtok=((not P.get('DT',0)) or dtrend_prev(e,P.get('DSL',0))) and not dayblk
        D0=min(ATR[i]*P['SLM'], daily_atr_prev(e)*P['DCM'], C[i]*P['SLP']/100, P.get('SLMAX',10**9))
        if MP==0 and brk and wf and dtok and not blocked:
            if skipleft>0: skipleft-=1
            else: pend=('mkt',0,False,D0)
        elif MP==0 and P['RE_ON'] and armed and C[i]<=reP and trendr>=P['RE_RATIO'] and wf and dtok and not blocked:
            if skipleft>0: skipleft-=1; armed=False; reP=0
            else: pend=('stop',reP,True,D0)
        prevMP=MP

    return trades
