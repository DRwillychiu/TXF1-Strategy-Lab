"""Second decomposition layer for one S16_S MC12 report.

Layer 1 (s16s_report_decompose.py) answers "what is the shape".
This one answers the questions layer 1 raised:
  A. the survivor cohort -- what happens to a trade that outlives QuickStop
  B. would QuickStop have killed the fish
  C. when did the signal rate change, and does it track scale or volatility
  D. where is the drawdown right now
  E. the giveback pile -- 40 losers that were once in profit
  F. the re-entry leg
"""
import sys
import collections
sys.path.insert(0, 'scripts')
import compare_mc12_reports as C

p = sys.argv[1]
T = C.read_trades(p)
N = len(T)
net = sum(t['pnl'] for t in T)


def m(x):
    return format(int(round(x)), ',')


def q(v, f):
    if not v:
        return 0
    i = f * (len(v) - 1)
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def line():
    print('-' * 78)


QS = 'SX_MA_QuickStop_Time'
killed = [t for t in T if t['exit_sig'] == QS]
surv = [t for t in T if t['exit_sig'] != QS]

print('=' * 78)
print('S16_S LAYER 2')
print('=' * 78)

# ---------- A ----------
print('\n[A] THE 20-MINUTE AUDITION')
line()
kw = [t for t in killed if t['pnl'] > 0]
sw = [t for t in surv if t['pnl'] > 0]
print('  culled by QuickStop  n=%-4d WR %5.1f%%  net %13s  med %10s'
      % (len(killed), 100.0 * len(kw) / len(killed), m(sum(t['pnl'] for t in killed)),
         m(q(sorted(t['pnl'] for t in killed), .5))))
print('  survived QuickStop   n=%-4d WR %5.1f%%  net %13s  med %10s'
      % (len(surv), 100.0 * len(sw) / len(surv), m(sum(t['pnl'] for t in surv)),
         m(q(sorted(t['pnl'] for t in surv), .5))))
print('  survival rate %.1f%%   ->   a trade that lives past QuickStop wins %.0f%% of the time'
      % (100.0 * len(surv) / N, 100.0 * len(sw) / len(surv)))
sl = [t for t in surv if t['pnl'] <= 0]
print('  the %d survivors that still lost:' % len(sl))
for t in sorted(sl, key=lambda t: t['pnl']):
    print('      %s  %-22s %10s' % (t['t_in'], t['exit_sig'], m(t['pnl'])))
print('  survivor WR by year:')
g = collections.defaultdict(list)
for t in surv:
    g[t['t_in'].year].append(t)
for y in sorted(g):
    v = g[y]
    w = [x for x in v if x['pnl'] > 0]
    print('      %d  n=%-3d WR %5.0f%%  net %12s' % (y, len(v), 100.0*len(w)/len(v), m(sum(x['pnl'] for x in v))))

# ---------- B ----------
print('\n[B] WOULD A TIGHTER / LOOSER QUICKSTOP HAVE TOUCHED THE FISH')
line()
S = sorted(T, key=lambda t: -t['pnl'])
fish = S[:7]
print('  QS_MaxLoss_Pct = 0.7%% of entry price, 2 lots, 200 NTD/pt')
print('  %-20s %8s %11s %11s %11s' % ('fish entry', 'entry', 'QS money', 'its MAE', 'headroom'))
for t in fish:
    thr = t['p_in'] * 0.007 * 200 * 2
    mae = abs(t['mae'])
    print('  %-20s %8.0f %11s %11s %11s%s'
          % (str(t['t_in'])[:16], t['p_in'], m(thr), m(mae), m(thr - mae),
             '   <== WOULD HAVE BEEN AT RISK' if mae >= thr else ''))
allw = [t for t in T if t['pnl'] > 0]
risky = [t for t in allw if abs(t['mae']) >= t['p_in'] * 0.007 * 200 * 2]
print('  ---')
print('  winners whose MAE already exceeded the QS loss threshold: %d of %d  (net %s)'
      % (len(risky), len(allw), m(sum(t['pnl'] for t in risky))))
print('  (they survived only because the excursion came AFTER bar 4)')
for t in sorted(risky, key=lambda t: -t['pnl'])[:8]:
    print('      %s  MAE %9s  thr %9s  pnl %10s'
          % (str(t['t_in'])[:16], m(abs(t['mae'])), m(t['p_in']*0.007*200*2), m(t['pnl'])))

# ---------- C ----------
print('\n[C] SIGNAL RATE OVER TIME  -- 2023 traded 4 times, 2026 traded 53')
line()
g = collections.defaultdict(list)
for t in T:
    g[(t['t_in'].year, (t['t_in'].month - 1) // 3 + 1)].append(t)
print('  %-10s %4s %10s %12s   %s' % ('quarter', 'n', 'avg entry', 'net', 'bar'))
for k in sorted(g):
    v = g[k]
    avg = sum(x['p_in'] for x in v) / len(v)
    nt = sum(x['pnl'] for x in v)
    print('  %d-Q%d      %4d %10.0f %12s   %s'
          % (k[0], k[1], len(v), avg, m(nt), '#' * min(len(v), 40)))
print('  ---')
print('  Rule #13 floor is 2 trades per month = 6 per quarter.')
bad = [k for k in sorted(g) if len(g[k]) < 6]
print('  quarters BELOW the floor: %d of %d  ->  %s'
      % (len(bad), len(g), ', '.join('%dQ%d(%d)' % (k[0], k[1], len(g[k])) for k in bad)))

# ---------- D ----------
print('\n[D] WHERE IS THE DRAWDOWN RIGHT NOW')
line()
eq = 0
peak = 0
peak_at = None
mdd = 0
mdd_at = None
mdd_peak_at = None
for t in T:
    eq += t['pnl']
    if eq > peak:
        peak, peak_at = eq, t['t_out']
    if eq - peak < mdd:
        mdd, mdd_at, mdd_peak_at = eq - peak, t['t_out'], peak_at
print('  final closed equity      %13s' % m(eq))
print('  highest closed equity    %13s   at %s' % (m(peak), peak_at))
print('  max closed-trade DD      %13s   peak %s -> trough %s' % (m(mdd), mdd_peak_at, mdd_at))
print('  current DD from peak     %13s' % m(eq - peak))
if abs(eq - peak) > 0 and abs((eq - peak) - mdd) < 1:
    print('  ** THE STRATEGY IS SITTING AT ITS ALL-TIME MAXIMUM DRAWDOWN RIGHT NOW **')
run = []
c = 0
for t in T:
    if t['pnl'] <= 0:
        c += 1
    else:
        run.append(c)
        c = 0
run.append(c)
print('  longest losing streak    %d trades' % max(run))
seq = []
c = 0
for t in T:
    if t['pnl'] <= 0:
        c += 1
        if c == max(run):
            seq = [t['t_in']]
    else:
        c = 0
print('  ends near                %s' % (seq[0] if seq else 'n/a'))

# ---------- E ----------
print('\n[E] THE GIVEBACK PILE')
line()
L = [t for t in T if t['pnl'] <= 0]
for thr in (10000, 20000, 40000, 80000):
    gb = [t for t in L if abs(t['mfe']) > thr]
    print('  losers once up more than %7s : %3d   net %12s   their peak sum %12s'
          % (m(thr), len(gb), m(sum(t['pnl'] for t in gb)), m(sum(abs(t['mfe']) for t in gb))))
print('  ---  BE_Trigger_Pct = 0.7%% of entry; BE fired only 5 times all history')
gb = sorted([t for t in L if abs(t['mfe']) > 20000], key=lambda t: -abs(t['mfe']))
print('  worst 8 givebacks:')
for t in gb[:8]:
    thr = t['p_in'] * 0.007 * 200 * 2
    print('      %s  MFE %9s (BE thr %8s)  ended %10s   %s'
          % (str(t['t_in'])[:16], m(abs(t['mfe'])), m(thr), m(t['pnl']), t['exit_sig']))

# ---------- F ----------
print('\n[F] THE RE-ENTRY LEG')
line()
re = [t for t in T if t['entry_sig'] == 'SE_MA_ReEntry']
mn = [t for t in T if t['entry_sig'] != 'SE_MA_ReEntry']


def stat(lbl, v):
    if not v:
        return
    w = [x for x in v if x['pnl'] > 0]
    pn = sorted(x['pnl'] for x in v)
    print('  %-12s n=%-4d WR %5.1f%%  net %12s  med %10s  mean %10s'
          % (lbl, len(v), 100.0*len(w)/len(v), m(sum(pn)), m(q(pn, .5)), m(sum(pn)/len(pn))))


stat('re-entry', re)
stat('main', mn)
for t in re:
    print('      %s -> %s  %-22s %10s' % (t['t_in'], str(t['t_out'])[:16], t['exit_sig'], m(t['pnl'])))
