#!/usr/bin/env python3
"""Semantic gate for L3 v19.3 (Day_Pat_On). Three independent pieces:
  ENGINE : a small model of how MC fills the real orders (buy stop, CL_SL stop, CL_TP limit, market,
           entry-bar engine stop with the no-magnifier O-H-L-C / O-L-H-C path).
  PORT   : a statement-by-statement port of the v19.3 PowerLanguage logic that was added
           (session trading-day counter, pattern scoring, virtual trade A1/A2, entry gate, virtual exits).
  SPEC   : Willy's words, written at trade-list level only (no code reused):
           today = TAIFEX trading day from the official calendar; score today's closed trades;
           two same results in a row -> the next trade (the one that would have been taken) is not taken;
           the skipped trade does not count; the pause expires when the trading day changes.
Checks on thousands of random markets on the real 2019-2026 TAIFEX calendar:
  T1 identity  : switches off  -> same trades as the engine without any v19.3 code
  T2 twin      : Virt_Test_On  -> real trades unchanged AND each virtual twin enters/exits on the real bars
  T3 semantics : Day_Pat_On, Mode 1 -> trades == SPEC(baseline trades)
  T4 mode 2    : no real entry while a virtual trade is open inside its own trading day"""
import random, datetime as D, json, sys
CLOSED = {D.date.fromisoformat(r['date']) for r in json.load(open('/home/claude/repo/data/taifex_market_closures.json'))['closed_weekdays']}
def biz(d): return d.weekday() < 5 and d not in CLOSED

def timeline(start, ndays, rnd):
    """15M bar close stamps. Night session of business day T runs from the previous business day P 15:15
    to P+1 05:00 (session_fact); day session T 09:00-13:45. Random extra: a day with no night session."""
    days = []; d = start
    while len(days) < ndays:
        if biz(d): days.append(d)
        d += D.timedelta(days=1)
    bars = []
    for i, T in enumerate(days[1:], 1):
        P = days[i - 1]
        if rnd.random() > 0.03:  # 3% of days: night session missing (typhoon style)
            t = D.datetime.combine(P, D.time(15, 15))
            while t <= D.datetime.combine(P + D.timedelta(days=1), D.time(5, 0)):
                bars.append(t); t += D.timedelta(minutes=15)
        t = D.datetime.combine(T, D.time(9, 0))
        while t <= D.datetime.combine(T, D.time(13, 45)):
            bars.append(t); t += D.timedelta(minutes=15)
    return bars

def market(bars, rnd):
    px = 20000.0; out = []
    for t in bars:
        o = px + rnd.gauss(0, 8); h = o + abs(rnd.gauss(0, 25)); l = o - abs(rnd.gauss(0, 25)); c = rnd.uniform(l, h); px = c
        act = rnd.random() > 0.08
        out.append(dict(t=t, O=round(o), H=round(h), L=round(l), C=round(c), active=act,
                        sig=act and rnd.random() < 0.35, X=round(c + rnd.uniform(-15, 15)), d=round(rnd.uniform(15, 60)),
                        slo=round(rnd.uniform(15, 60)), tpo=round(rnd.uniform(15, 90)), safety=rnd.random() < 0.01))
    return out

def same_bar_stop(b, X, esl):   # engine stop on the entry bar, MC no-magnifier path
    if b['O'] >= X: return b['L'] <= esl
    if (b['H'] - b['O']) <= (b['O'] - b['L']): return b['L'] <= esl
    return b['C'] <= esl

def run(B, day_pat=False, mode=1, twin=False, v193=True, mut=None):
    MP = 0; EP = 0; trades = []; cur = None; pend = None; ex = None; locked = False; FSL = FTP = 0
    TT = 0; NP = 0
    # port state
    TD = 0; P_Day = 0; R1 = R2 = 0; LastTT = 0; LastNP = 0; Skip = False; PrevT = 0; PrevD = None
    V_On = False; V_Pend = None; V_EP = 0; V_PSL = V_PTP = 0; V_PMkt = False; V_Locked = False; V_FSL = V_FTP = 0
    vlog = []; blocked_entries = []
    for k, b in enumerate(B):
        # ---------- ENGINE: orders sent at k-1 close are worked during bar k ----------
        if MP == 1 and ex is not None:
            xp = None
            if ex['mkt']: xp = b['O']
            else:
                sl_hit = ex['sl'] and b['L'] <= ex['sl']; tp_hit = ex['tp'] and b['H'] >= ex['tp']
                if sl_hit and tp_hit:
                    sl_first = (b['H'] - b['O']) > (b['O'] - b['L'])   # O-L-H-C: low first
                    xp = min(b['O'], ex['sl']) if sl_first else max(b['O'], ex['tp'])
                elif sl_hit: xp = min(b['O'], ex['sl'])
                elif tp_hit: xp = max(b['O'], ex['tp'])
            if xp is not None:
                MP = 0; pnl = (xp - EP) * 400 - 2000; TT += 1; NP += pnl
                cur['xt'] = b['t']; cur['pnl'] = pnl; trades.append(cur); cur = None
        ex = None
        if MP == 0 and pend is not None and b['H'] >= pend['X']:
            MP = 1; EP = max(b['O'], pend['X']); locked = False; cur = dict(dt=b['t'])
            esl = EP - pend['d']
            if same_bar_stop(b, pend['X'], esl):
                MP = 0; xp = min(b['O'], esl) if b['O'] >= pend['X'] else esl
                pnl = (xp - EP) * 400 - 2000; TT += 1; NP += pnl; cur['xt'] = b['t']; cur['pnl'] = pnl; trades.append(cur); cur = None
        pend = None
        # ---------- PORT of v19.3 (bar close) ----------
        T = b['t'].hour * 100 + b['t'].minute; Dt = b['t'].date()
        if v193:
            if mut == 'M2_weekend_day':
                j = b['t'].date() + (D.timedelta(days=1) if T >= 1500 else D.timedelta(0))
                j += D.timedelta(days={5: 2, 6: 1}.get(j.weekday(), 0)); TD = j.toordinal()
            elif k > 0:
                if T >= 1500:
                    if PrevT < 1500 or Dt != PrevD: TD += 1
                elif T > 500:
                    if PrevT > 500 and PrevT < 1500 and Dt != PrevD: TD += 1
            PrevT = T; PrevD = Dt
            LastBar = 1345 <= T < 1500 and mut != 'M4_no_lastbar'
            if TD != P_Day:
                P_Day = TD; R1 = R2 = 0; Skip = False
                if mode == 2 and not twin and V_On: V_On = False; vlog.append(('OUT', b['t'], 6))
            if TT > LastTT:
                R1 = R2; R2 = 1 if NP - LastNP > 0 else -1
                if day_pat and R1 != 0 and R1 == R2: Skip = True
                LastNP = NP; LastTT = TT
            if V_On:
                code = 0
                if V_PMkt: code = 1
                elif V_PSL > 0 and b['L'] <= V_PSL: code = 3
                elif V_PTP > 0 and b['H'] >= V_PTP: code = 4
                if code:
                    V_On = False; vlog.append(('OUT', b['t'], code))
                    if mut == 'M3_count_virtual':
                        vx = b['O'] if code == 1 else (V_PSL if code == 3 else V_PTP)
                        R1 = R2; R2 = 1 if (vx - V_EP) * 400 - 2000 > 0 else -1
                        if day_pat and R1 != 0 and R1 == R2: Skip = True
            if V_Pend is not None:
                if b['H'] >= V_Pend['X'] and mut == 'M1_v192_one_bar':
                    Skip = False
                elif b['H'] >= V_Pend['X']:
                    V_On = True; V_EP = max(b['O'], V_Pend['X']); V_Locked = False
                    if not twin: Skip = False
                    if mut == 'M5_restart_after_pause': R1 = R2 = 0
                    vlog.append(('IN', b['t'], 0))
                    if same_bar_stop(b, V_Pend['X'], V_EP - V_Pend['d']): V_On = False; vlog.append(('OUT', b['t'], 5))
                V_Pend = None
            V_PSL = V_PTP = 0; V_PMkt = False
            if (not day_pat) or twin: Skip = False
        # entry block
        if b['active'] and b['sig'] and MP == 0 and ((not V_On) or twin or not v193 or (v193 and mode == 2 and LastBar and mut != 'M6_v193_no_1345')):
            if v193 and Skip and not LastBar:
                V_Pend = dict(X=b['X'], d=b['d'])
            else:
                if v193 and twin: V_Pend = dict(X=b['X'], d=b['d'])
                pend = dict(X=b['X'], d=b['d'])
        elif b['active'] and b['sig'] and MP == 0 and V_On:
            blocked_entries.append((b['t'], P_Day))
        # exit block
        if b['active']:
            if MP == 1:
                if not locked: FSL = EP - b['slo']; FTP = EP + b['tpo']; locked = True
                ex = dict(mkt=False, sl=FSL, tp=FTP)
            if v193 and V_On:
                if not V_Locked: V_FSL = V_EP - b['slo']; V_FTP = V_EP + b['tpo']; V_Locked = True
                V_PTP = V_FTP; V_PSL = V_FSL
        else:
            if MP == 1: ex = dict(mkt=True, sl=0, tp=0)
            if v193 and V_On: V_PMkt = True
        if b['safety']:
            if MP == 1: ex = dict(mkt=True, sl=0, tp=0)
            if v193 and V_On: V_PMkt = True
    return trades, vlog, blocked_entries

def spec(base, B):
    """Willy's rule applied to the baseline trade list. prev[t] = bar before t (the bar that sent the order)."""
    idx = {b['t']: i for i, b in enumerate(B)}
    def tdcal(x):
        d = x.date(); hm = x.hour * 100 + x.minute
        if hm >= 1500: d += D.timedelta(days=1)
        elif hm > 500: return d
        while not biz(d): d += D.timedelta(days=1)
        return d
    cur = None; r1 = r2 = 0; flag = None; kept = []; skipped = []
    for t in base:
        pb = B[idx[t['dt']] - 1]['t']
        if flag is not None and flag != tdcal(pb): flag = None
        last = 1345 <= pb.hour * 100 + pb.minute < 1500
        if flag is not None and not last: skipped.append(t); flag = None; continue
        kept.append(t); d = tdcal(t['xt'])
        if d != cur: cur = d; r1 = r2 = 0
        r1 = r2; r2 = 1 if t['pnl'] > 0 else -1
        if r1 != 0 and r1 == r2: flag = d
    return kept, skipped

def tdcal(x):
    d = x.date(); hm = x.hour * 100 + x.minute
    if hm >= 1500: d += D.timedelta(days=1)
    elif hm > 500: return d
    while not biz(d): d += D.timedelta(days=1)
    return d

def spec_engine(B, mode):
    """Second, independent SPEC: the skipped trade is really held by the engine as a PHANTOM position
    (same fills, same exits, result not counted, not scored). Mode 2: the phantom is dropped when the
    trading day changes (next 15:00 open); an order sent on the 13:45 bar may fill at/after 15:00.
    Uses the official calendar for 'today'; shares no code with the v19.3 port."""
    MP = 0; EP = 0; cur = None; pend = None; ex = None; locked = False; FSL = FTP = 0
    counted = []; flag = None; tday = None; r1 = r2 = 0
    for k, b in enumerate(B):
        if mode == 2 and MP == 1 and cur['ph'] and tdcal(b['t']) != cur['td']:
            MP = 0; cur = None; ex = None                       # released at the new trading day
        closed = None
        if MP == 1 and ex is not None:
            xp = None
            if ex['mkt']: xp = b['O']
            else:
                sl_hit = ex['sl'] and b['L'] <= ex['sl']; tp_hit = ex['tp'] and b['H'] >= ex['tp']
                if sl_hit and tp_hit:
                    xp = min(b['O'], ex['sl']) if (b['H'] - b['O']) > (b['O'] - b['L']) else max(b['O'], ex['tp'])
                elif sl_hit: xp = min(b['O'], ex['sl'])
                elif tp_hit: xp = max(b['O'], ex['tp'])
            if xp is not None:
                MP = 0; cur['xt'] = b['t']; cur['pnl'] = (xp - EP) * 400 - 2000; closed = cur; cur = None
        ex = None
        if MP == 0 and pend is not None and b['H'] >= pend['X']:
            MP = 1; EP = max(b['O'], pend['X']); locked = False; cur = dict(dt=b['t'], ph=pend['ph'], td=tdcal(b['t']))
            if pend['ph']: flag = None                           # the pause is used by this trade
            esl = EP - pend['d']
            if same_bar_stop(b, pend['X'], esl):
                xp = min(b['O'], esl) if b['O'] >= pend['X'] else esl
                MP = 0; cur['xt'] = b['t']; cur['pnl'] = (xp - EP) * 400 - 2000; closed = cur; cur = None
        pend = None
        today = tdcal(b['t']); last = b['t'].hour * 100 + b['t'].minute == 1345
        if today != tday: tday = today; r1 = r2 = 0; flag = None
        if closed is not None and not closed['ph']:
            counted.append(closed); r1 = r2; r2 = 1 if closed['pnl'] > 0 else -1
            if r1 != 0 and r1 == r2: flag = today
        held_ph = MP == 1 and cur['ph']
        if b['active'] and b['sig'] and (MP == 0 or (mode == 2 and last and held_ph)):
            pend = dict(X=b['X'], d=b['d'], ph=(flag is not None and not last and MP == 0))
        if MP == 1:
            if b['active']:
                if not locked: FSL = EP - b['slo']; FTP = EP + b['tpo']; locked = True
                ex = dict(mkt=False, sl=FSL, tp=FTP)
            else: ex = dict(mkt=True, sl=0, tp=0)
            if b['safety']: ex = dict(mkt=True, sl=0, tp=0)
    return counted

def key(tr): return [(t['dt'], t['xt'], t['pnl']) for t in tr]

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    fails = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0, 'T5': 0, 'T6': 0}; nsk = ntr = ncross = 0; first = {}
    for seed in range(N):
        rnd = random.Random(seed)
        start = D.date(2019, 1, 2) + D.timedelta(days=rnd.randrange(0, 2700))
        B = market(timeline(start, 60, rnd), rnd)
        base, _, _ = run(B, v193=False)
        off, _, _ = run(B)
        if key(off) != key(base): fails['T1'] += 1; first.setdefault('T1', seed)
        tw, vlog, _ = run(B, twin=True)
        ins = [x[1] for x in vlog if x[0] == 'IN']; outs = [x[1] for x in vlog if x[0] == 'OUT']
        if len(ins) == len(outs) + 1: ins = ins[:-1]   # a position still open when the data ends is not a trade
        if key(tw) != key(base) or ins != [t['dt'] for t in base] or outs != [t['xt'] for t in base]:
            fails['T2'] += 1; first.setdefault('T2', seed)
        p1, _, _ = run(B, day_pat=True, mode=1)
        kept, sk = spec(base, B); nsk += len(sk); ntr += len(base)
        ncross += sum(1 for t in sk if t['xt'].date() != t['dt'].date())
        if key(p1) != key(kept): fails['T3'] += 1; first.setdefault('T3', seed)
        if key(p1) != key(spec_engine(B, 1)): fails['T5'] += 1; first.setdefault('T5', seed)
        p2, vl2, blk = run(B, day_pat=True, mode=2)
        if key(p2) != key(spec_engine(B, 2)): fails['T6'] += 1; first.setdefault('T6', seed)
        # T4: inside the trading day of a virtual trade no real entry may fill before its OUT
        ok = True; open_v = None
        for ev in vl2:
            if ev[0] == 'IN': open_v = ev[1]
            else:
                if open_v:
                    for t in p2:
                        if open_v < t['dt'] < ev[1] and ev[2] != 6: ok = False
                open_v = None
        if not ok: fails['T4'] += 1; first.setdefault('T4', seed)
    print(f'markets {N} | baseline trades {ntr} | skips predicted by SPEC {nsk} (crossing a day {ncross})')
    for k, v in fails.items(): print(f'  {k}: {"PASS" if v == 0 else f"FAIL in {v} markets (first seed {first[k]})"}')

def mutation_check(N=150):
    """A gate that cannot fail proves nothing: each known wrong reading must make T3 fail."""
    for m in ('M1_v192_one_bar', 'M2_weekend_day', 'M3_count_virtual', 'M4_no_lastbar', 'M5_restart_after_pause'):
        bad = 0
        for seed in range(N):
            rnd = random.Random(seed); start = D.date(2019, 1, 2) + D.timedelta(days=rnd.randrange(0, 2700))
            B = market(timeline(start, 60, rnd), rnd); base, _, _ = run(B, v193=False)
            kept, _ = spec(base, B); p1, _, _ = run(B, day_pat=True, mode=1, mut=m)
            bad += key(p1) != key(kept)
        print(f'  mutation {m:24s}: T3 caught it in {bad}/{N} markets -> {"GATE WORKS" if bad else "GATE BLIND"}')

def mutation_check_mode2(N=150):
    for m, mode in (('M6_v193_no_1345', 2), ('M7_mode1_as_mode2', 1), ('M1_v192_one_bar', 2)):
        bad = 0
        for seed in range(N):
            rnd = random.Random(seed); start = D.date(2019, 1, 2) + D.timedelta(days=rnd.randrange(0, 2700))
            B = market(timeline(start, 60, rnd), rnd)
            p, _, _ = run(B, day_pat=True, mode=mode, mut=m if m != 'M7_mode1_as_mode2' else None)
            bad += key(p) != key(spec_engine(B, 2))
        print(f'  mutation {m:24s}: T6 caught it in {bad}/{N} markets -> {"GATE WORKS" if bad else "GATE BLIND"}')
