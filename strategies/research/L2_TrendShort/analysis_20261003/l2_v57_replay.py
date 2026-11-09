# L2 v5.7 research replay = v5.6 (loss pause, caps) + BP bull-pullback path + stop-profit in % (SPPPCT). Generated from l2_replay_pause.py (10/3 ~14:35).
# Previous header: L2 v5.3 replay + loss pause (PN losses in a row -> skip next PK entry signals; counter resets after a pause). Generated from l2_replay.py.
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
LOOSE=[]   # (bar, Active_TSL - SL_Trig, Active_TSL - entry) when the trailing stop sits ABOVE the initial trigger
P0=dict(WK=13,C0F=0.45,SLR=1.1,ACC=0.5,NLN=15,MINB=3,TSLK=9,TSLM=1.0,TPN=30,TTPA=4.0,TTPR=1.5,SPP=250,SPR=55,SLP=1.25,
        WKIN=1,WKEX=1,SLMAX=0)
def run(OV=None, start=dt.datetime(2019,6,1), end=dt.datetime(2026,9,25), entry_fn=None, PN=0, PK=0, PB=0, PR=False,
        BEAR=1, BP=0, BPDD=3.0, BPLB=20, BPBODY=1.0, BPSL=1.5, BPCAP=450, BPTRK=1.0, BPT=40, BPK=1, BPLEGT=0, BPATR=0.0, SCOPE='bear', BPSLP=0.0, BPTRP=0.0, BPBODYP=0.0, SKIPN=0, SKIPK=1):
    # Willy 10/3 15:17: SKIPN losses in a row (bear path) -> skip the next SKIPK trades only. A skipped trade blocks its whole signal run
    # (the bear entry condition stays true for several bars; blocking one bar would only delay the entry by one bar).
    sk_left=0; sk_ep=False; sk_cl=0
    # Willy 10/3 14:43 (ATR lags in volatility spikes): BPSLP>0 stop = % of signal close (cap BPCAP); BPTRP>0 trail = lowest low x (1+%); BPBODYP>0 body gate in % of price instead of ATR
    # BP: bull-pullback short, only when weekly filter is OFF; exits = holiday/settlement flat, stop (1.5 ATR <= cap) trailed to lowest low + BPTRK*ATR, time BPT bars.
    # BPK entries per pullback leg (leg = BPLB-bar high at first BP entry; reset when High >= it, or after BPLEGT bars). SCOPE='bear': loss pause counts bear-path trades only.
    leg_hh=None; leg_n=0; leg_i=0
    # PR=True (v5.6 #26/#27 semantics): after PN losses pause; release when weekly filter is off, or (PB>0) after PB bars, whichever first
    # PK>0: skip PK signal EPISODES (rising edges); PK=-1: until weekly filter off; PB>0: pause PB bars after PN losses
    cl=0; skip=0; ntc=0; psig=False; pause_to=-1
    P=dict(P0); P.update(OV or {})
    trades=[]; pos=None; pend=None   # pend: ('entry',) or ('exit',label)
    stop_ord=None                     # (level,label) for next bar
    wk=[]; fok=False; c1prev=False
    fok_cnt=0; wdepth=0.0   # Willy 10/3 15:45: P['WCONF'] weekly updates in a row with FilterOK on; P['WDEPTH'] % weekly close below SMA13
    for i in range(40,n):
        e=BE[i]
        if e>=end: break
        if PR and skip<0 and (not fok or (PB>0 and i>pause_to)): skip=0
        if leg_hh is not None and (H[i]>=leg_hh or (BPLEGT and i-leg_i>=BPLEGT)): leg_hh=None; leg_n=0
        elif (not PR) and skip<0 and not fok: skip=0   # PK=-1: pause until the weekly bear filter switches off (regime reset)
        # ---------- intrabar: fills ----------
        if pend is not None:
            if pend[0]=='entry' and pos is None:
                pos=dict(ep=O[i],ei=i,et=e,dist=pend[1],locked=False,slt=0,armed=False,tsl=0,lc=0,spb=0,spp=0,act=0,src=0,esig=pend[2])
                stop_ord=None
            elif pend[0]=='exit' and pos is not None:
                trades.append((pos['et'],pos['ep'],e,O[i],pend[1],pos['esig'],pos.get('slt',0) or pos['ep']+pos['dist'])); pos=None; stop_ord=None
            pend=None
        if pos is not None:
            lv=[(pos['ep']+pos['dist'],'Stop Loss')] if (ENGINE_ALL or pos['ei']==i) else [(1e12,'none')]
            if stop_ord is not None and pos['ei']<i: lv.append(stop_ord)
            if pos['ei']<i and (P.get('HARD',0) or P.get('HARDP',0)):   # v5.6 #28 Night_Hard_Stop proxy: intrabar stop at entry + cap, every bar after entry
                cap=min([x for x in (P.get('HARD',0), pos['ep']*P.get('HARDP',0)/100) if x>0]); lv.append((pos['ep']+cap,'TS_HardSL'))
            lvl,lab=min(lv,key=lambda x:x[0])
            if pos['ei']<i and O[i]>=lvl: trades.append((pos['et'],pos['ep'],e,O[i],lab,pos['esig'],pos.get('slt',0) or pos['ep']+pos['dist'])); pos=None
            elif H[i]>=lvl: trades.append((pos['et'],pos['ep'],e,lvl,lab,pos['esig'],pos.get('slt',0) or pos['ep']+pos['dist'])); pos=None
        stop_ord=None
        # loss counter updated AFTER this bar's fills, BEFORE bar-close signals (MC: MarketPosition/PositionProfit at bar close)
        while ntc<len(trades):
            tr=trades[ntc]; ntc+=1
            if SCOPE=='bear' and tr[5]=='BP': continue   # BP trades do not feed the bear-path loss pause (counter var renamed nt->ntc 10/3: collided with TSL nt)
            if SKIPN:
                sk_cl=sk_cl+1 if (tr[1]-tr[3])*20-200<0 else 0
                if sk_cl>=SKIPN: sk_left=SKIPK; sk_cl=0
            cl=cl+1 if (tr[1]-tr[3])*20-200<0 else 0
            if PN and cl>=PN:
                cl=0
                if PR: skip=-1; pause_to=i+PB
                elif PB: pause_to=i+PB
                else: skip=PK
        # ---------- bar close ----------
        t=TM[i]; d=e.date()
        isday= 845<=t<=1245
        holblk = (t<=500 and d in HOL)
        settle = (e.weekday()==2 and 15<=e.day<=21)
        if TM[i-1]==1245 and BE[i-1].weekday()==4:
            wk.insert(0,C[i-1]); wk=wk[:P['WK']]
            fok = len(wk)>=P['WK'] and wk[0]<sum(wk)/P['WK']
            fok_cnt = fok_cnt+1 if fok else 0
            wdepth = (1-wk[0]/(sum(wk)/P['WK']))*100 if len(wk)>=P['WK'] else 0.0
        wsma = sum(wk)/len(wk) if len(wk)>=P['WK'] else None
        if e<start: c1prev=False; continue
        atr=ATR[i]; dcl=DCL[i]
        c0 = C[i] < dcl - atr*P['C0F']; ca=Z[i]<Z[i-1]; cb=Z[i]<E[i]
        mp=-1 if pos is not None else 0
        if mp==0:
            dist=abs((dcl+atr*P['SLR'])-C[i])
            if P['SLP']>0: dist=min(dist,C[i]*P['SLP']/100)
            if P['SLMAX']>0: dist=min(dist,P['SLMAX'])
            sig = BEAR and (fok or P['WKIN']==0) and c0 and ca and cb and fok_cnt>=P.get('WCONF',1) and wdepth>=P.get('WDEPTH',0.0)
            lab='TS_Entry'
            if not sig and entry_fn is not None:
                r=entry_fn(i,P,fok)
                if r: sig=True; lab=r
            edge = sig and not psig; psig = sig
            if BP and not sig and not fok and not holblk and not settle and ATR[i]/C[i]*100>=BPATR:
                hh=H[max(0,i-BPLB+1):i+1].max()
                body_ok = ((O[i]-C[i])/C[i]*100>=BPBODYP) if BPBODYP>0 else ((O[i]-C[i])>=BPBODY*ATR[i])
                if (1-C[i]/hh)*100>=BPDD and body_ok and not (BPK and leg_hh is not None and leg_n>=BPK):
                    if leg_hh is None: leg_hh=hh; leg_i=i
                    leg_n+=1; pend=('entry',min((C[i]*BPSLP/100) if BPSLP>0 else BPSL*ATR[i],BPCAP),'BP')
            if not sig: sk_ep=False
            if SKIPN and sig and not holblk and not settle and (sk_ep or sk_left>0):
                if not sk_ep: sk_left-=1; sk_ep=True
                sig=False   # skipped trade: no order for this whole signal run
            if sig and not holblk and not settle:
                if skip<0 or ((not PR) and i<=pause_to): pass
                elif skip>0:
                    if edge: skip-=1
                    if skip>0 or edge: pass
                    else: pend=('entry',dist,lab)
                else: pend=('entry',dist,lab)
            c1prev=False
            continue
        bse=i-pos['ei']
        if pos['esig']=='BP':
            pos['ll']=L[i] if bse==0 else min(pos['ll'],L[i])
            if bse==0: pos['bstop']=pos['ep']+pos['dist']
            pos['bstop']=min(pos['bstop'],(pos['ll']*(1+BPTRP/100)) if BPTRP>0 else (pos['ll']+BPTRK*ATR[i]))
            if holblk and t>=300: pend=('exit','TS_Holiday')
            elif settle and t>=1230: pend=('exit','TS_Settlement')
            elif bse>=BPT: pend=('exit','BP_Time')
            else: stop_ord=(pos['bstop'],'BP_Stop')
            c1prev=False
            continue
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
            if pos['tsl']<pos['slt'] and atsl>pos['slt']: LOOSE.append((e,round(atsl-pos['slt']),round(atsl-pos['ep'])))   # placed AFTER if/else (first try broke the pairing)
        else: act=pos['slt']; src=2
        pos['lc']=C[i] if bse==0 else min(pos['lc'],C[i])
        wave=pos['ep']-pos['lc']; ttp_fire = wave>=atr*P['TTPA'] and C[i]>pos['lc']*(1+P['TTPR']/100)
        spp_thr = P['SPP'] if not (P.get('SPPATR',0) or P.get('SPPPCT',0)) else (P['SPPATR']*atr if P.get('SPPATR',0) else pos['ep']*P['SPPPCT']/100)   # research: stop-profit activation in ATR or % of entry instead of fixed points
        if pos['ep']-C[i]>=spp_thr:
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
