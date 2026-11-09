# L2 TrendShort v5.3 replay on 60M bars built from 1-minute data (IOG off, bar-close logic). Estimate, NOT MC.
# Fills: market orders at next bar open; stop orders (day SL / TSL / SP) and the engine SetStopLoss intrabar:
# lowest triggered buy-stop level wins (fill at open if gapped through). Costs: 1,000 NTD per side per lot, 2 lots.
import datetime as dt, numpy as np
from l2_funnel import BE,O,H,L,C,ATR,DCL,Z,E,C0 as C0A,CA as CAA,CB as CBA
n=len(C)
HOL={dt.date(2000+int(str(x)[1:3]),int(str(x)[3:5]),int(str(x)[5:7])) for x in
 [1190913,1191010,1200101,1200121,1200228,1200402,1200501,1200625,1201001,1201009,1210101,1210206,1210227,1210402,1210612,1210918,
  1211009,1211231,1220127,1220226,1220402,1220430,1220603,1220909,1221008,1221231,1230118,1230225,1230401,1230429,1230622,1230929,
  1231007,1231230,1240206,1240228,1240404,1240501,1240608,1240917,1241010,1250101,1250123,1250228,1250403,1250501,1250530,1250927,
  1251004,1251010,1251024,1251225,1260101,1260212,1260227,1260403,1260501,1260619,1260925,1261009,1261024,1261225,1270101]}
TM=np.array([e.hour*100+e.minute for e in BE])
def lowest(x,k,i):  # Lowest(x[1],k) at bar i
    return x[i-k:i].min()
def highest(x,k,i): return x[i-k:i].max()
ENGINE_ALL=False
P0=dict(WK=13,C0F=0.45,SLR=1.1,ACC=0.5,NLN=15,MINB=3,TSLK=9,TSLM=1.0,TPN=30,TTPA=4.0,TTPR=1.5,SPP=250,SPR=55,SLP=1.25,
        WKIN=1,WKEX=1,SLMAX=0)
def run(OV=None, start=dt.datetime(2019,6,1), end=dt.datetime(2026,9,25), entry_fn=None):
    P=dict(P0); P.update(OV or {})
    trades=[]; pos=None; pend=None   # pend: ('entry',) or ('exit',label)
    stop_ord=None                     # (level,label) for next bar
    wk=[]; fok=False; c1prev=False
    for i in range(40,n):
        e=BE[i]
        if e>=end: break
        # ---------- intrabar: fills ----------
        if pend is not None:
            if pend[0]=='entry' and pos is None:
                pos=dict(ep=O[i],ei=i,et=e,dist=pend[1],locked=False,slt=0,armed=False,tsl=0,lc=0,spb=0,spp=0,act=0,src=0,esig=pend[2])
                stop_ord=None
            elif pend[0]=='exit' and pos is not None:
                trades.append((pos['et'],pos['ep'],e,O[i],pend[1],pos['esig'])); pos=None; stop_ord=None
            pend=None
        if pos is not None:
            lv=[(pos['ep']+pos['dist'],'Stop Loss')] if (ENGINE_ALL or pos['ei']==i) else [(1e12,'none')]
            if stop_ord is not None and pos['ei']<i: lv.append(stop_ord)
            lvl,lab=min(lv,key=lambda x:x[0])
            if pos['ei']<i and O[i]>=lvl: trades.append((pos['et'],pos['ep'],e,O[i],lab,pos['esig'])); pos=None
            elif H[i]>=lvl: trades.append((pos['et'],pos['ep'],e,lvl,lab,pos['esig'])); pos=None
        stop_ord=None
        # ---------- bar close ----------
        t=TM[i]; d=e.date()
        isday= 845<=t<=1245
        holblk = (t<=500 and d in HOL)
        settle = (e.weekday()==2 and 15<=e.day<=21)
        if TM[i-1]==1245 and BE[i-1].weekday()==4:
            wk.insert(0,C[i-1]); wk=wk[:P['WK']]
            fok = len(wk)>=P['WK'] and wk[0]<sum(wk)/P['WK']
        wsma = sum(wk)/len(wk) if len(wk)>=P['WK'] else None
        if e<start: c1prev=False; continue
        atr=ATR[i]; dcl=DCL[i]
        c0 = C[i] < dcl - atr*P['C0F']; ca=Z[i]<Z[i-1]; cb=Z[i]<E[i]
        mp=-1 if pos is not None else 0
        if mp==0:
            dist=abs((dcl+atr*P['SLR'])-C[i])
            if P['SLP']>0: dist=min(dist,C[i]*P['SLP']/100)
            if P['SLMAX']>0: dist=min(dist,P['SLMAX'])
            sig = (fok or P['WKIN']==0) and c0 and ca and cb
            lab='TS_Entry'
            if not sig and entry_fn is not None:
                r=entry_fn(i,P,fok)
                if r: sig=True; lab=r
            if sig and not holblk and not settle:
                pend=('entry',dist,lab)
            c1prev=False
            continue
        bse=i-pos['ei']
        if bse==0 and not pos['locked']:
            slt=dcl+atr*P['SLR']
            if P['SLP']>0: slt=min(slt,pos['ep']*(1+P['SLP']/100))
            if P['SLMAX']>0: slt=min(slt,pos['ep']+P['SLMAX'])
            pos['slt']=slt; pos['locked']=True
        accel=(O[i]-C[i])>atr*P['ACC'] and C[i]<O[i]
        nlow=C[i]<lowest(C,P['NLN'],i)
        c1=accel and nlow
        if (not pos['armed']) and c1 and c1prev and bse>=P['MINB']: pos['armed']=True
        c1prev=c1
        if pos['armed']:
            nt=lowest(C,P['TSLK'],i)+atr*P['TSLM']
            pos['tsl']=nt if pos['tsl']==0 else min(pos['tsl'],nt)
            atsl=pos['tsl']+atr*P['SLR']
            if pos['tsl']<pos['slt']: act=atsl; src=1
            else: act=pos['slt']; src=2
        else: act=pos['slt']; src=2
        pos['lc']=C[i] if bse==0 else min(pos['lc'],C[i])
        wave=pos['ep']-pos['lc']; ttp_fire = wave>=atr*P['TTPA'] and C[i]>pos['lc']*(1+P['TTPR']/100)
        if pos['ep']-C[i]>=P['SPP']:
            pos['spb']=max(pos['spb'],pos['ep']-C[i]); pos['spp']=pos['ep']-pos['spb']*(1-P['SPR']/100)
        # exits (priority chain)
        if holblk and t>=300: pend=('exit','TS_Holiday')
        elif settle and t>=1230: pend=('exit','TS_Settlement')
        elif P['WKEX'] and e.weekday()==4 and t==1245 and wsma is not None and C[i]>wsma: pend=('exit','TS_WeeklyExit')
        elif C[i]>highest(C,P['TPN'],i): pend=('exit','TS_StructureTP')
        elif ttp_fire: pend=('exit','TS_TTP')
        elif pos['spp']>0: stop_ord=(pos['spp'],'TS_StopProfit')
        elif isday and act>0: stop_ord=(act,'TS_TSL_D' if src==1 else 'TS_InitSL_D')
        elif (not isday) and act>0 and C[i]>act: pend=('exit','TS_TSL_N' if src==1 else 'TS_InitSL_N')
    return trades
def pnl(tr): return (tr[1]-tr[3])*20-200     # micro, 2 lots, costs incl.
