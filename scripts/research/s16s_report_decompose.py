"""Decompose one MC12 report of S16_S. Distribution first, totals last.

Deliberately does NOT rank anything by trade count -- see the memory rule
feedback_no_trade_count_optimization. Cross-period consistency is the
primary criterion, and every year is shown with its own best trade removed
so a single fish cannot carry a year.
"""
import sys
import collections
sys.path.insert(0, 'scripts')
import compare_mc12_reports as C

p = sys.argv[1]
T = C.read_trades(p)
N = len(T)
net = sum(t['pnl'] for t in T)
W = [t for t in T if t['pnl'] > 0]
L = [t for t in T if t['pnl'] <= 0]
gp = sum(t['pnl'] for t in W)
gl = sum(t['pnl'] for t in L)


def m(x):
    return format(int(round(x)), ',')


def q(v, f):
    i = f * (len(v) - 1)
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def line():
    print('-' * 78)


print('=' * 78)
print('S16_S DECOMPOSITION   %s' % p.split('/')[-1])
print('=' * 78)
print('window  %s  ..  %s   (last CLOSED exit)' % (T[0]['t_in'], T[-1]['t_out']))
print('trades %d   net %s   PF %.4f   WR %.2f%%'
      % (N, m(net), gp / -gl, 100.0 * len(W) / N))

# ---------- 1 ----------
print('\n[1] CONCENTRATION  -- how few trades carry the result')
line()
S = sorted(T, key=lambda t: -t['pnl'])
for k in (1, 3, 5, 7, 10, 20):
    top = sum(t['pnl'] for t in S[:k])
    print('  top %-3d winners  %12s   %6.1f%% of net   %5.1f%% of trades'
          % (k, m(top), 100.0 * top / net, 100.0 * k / N))
print('  ---')
for k in (1, 3, 5, 10):
    bot = sum(t['pnl'] for t in S[-k:])
    print('  worst %-3d losers %12s   %6.1f%% of net' % (k, m(bot), 100.0 * bot / net))
print('  ---')
print('  ALL %d trades outside the top 7 : %s'
      % (N - 7, m(sum(t['pnl'] for t in S[7:]))))

# ---------- 2 ----------
print('\n[2] P&L DISTRIBUTION')
line()
allp = sorted(t['pnl'] for t in T)
print('  min %s   P05 %s   P25 %s   MED %s   P75 %s   P95 %s   max %s'
      % tuple(m(q(allp, f)) for f in (0, .05, .25, .5, .75, .95, 1)))
wp = sorted(t['pnl'] for t in W)
lp = sorted(t['pnl'] for t in L)
mw = sum(wp) / len(wp)
ml = sum(lp) / len(lp)
print('  winners n=%-4d med %10s  mean %10s  max %s' % (len(W), m(q(wp, .5)), m(mw), m(wp[-1])))
print('  losers  n=%-4d med %10s  mean %10s  min %s' % (len(L), m(q(lp, .5)), m(ml), m(lp[0])))
print('  payoff ratio (mean win / mean loss) = %.2f' % abs(mw / ml))
print('  breakeven WR needed at this payoff  = %.1f%%   actual %.1f%%'
      % (100.0 / (1 + abs(mw / ml)), 100.0 * len(W) / N))

# ---------- 3 ----------
print('\n[3] BY EXIT LABEL')
line()
g = collections.defaultdict(list)
for t in T:
    g[t['exit_sig']].append(t)
print('  %-26s %4s %6s %13s %11s %11s' % ('label', 'n', 'WR%', 'net', 'med', 'worst'))
for k in sorted(g, key=lambda k: -sum(x['pnl'] for x in g[k])):
    v = g[k]
    w = [x for x in v if x['pnl'] > 0]
    pn = sorted(x['pnl'] for x in v)
    print('  %-26s %4d %5.0f%% %13s %11s %11s'
          % (k, len(v), 100.0 * len(w) / len(v), m(sum(pn)), m(q(pn, .5)), m(pn[0])))

# ---------- 4 ----------
print('\n[4] BY ENTRY SOURCE')
line()
g = collections.defaultdict(list)
for t in T:
    g[t['entry_sig']].append(t)
for k in sorted(g, key=lambda k: -sum(x['pnl'] for x in g[k])):
    v = g[k]
    w = [x for x in v if x['pnl'] > 0]
    print('  %-26s %4d  WR %4.0f%%  net %13s'
          % (k, len(v), 100.0 * len(w) / len(v), m(sum(x['pnl'] for x in v))))

# ---------- 5 ----------
print('\n[5] BY YEAR  -- cross-period consistency is the primary criterion')
line()
g = collections.defaultdict(list)
for t in T:
    g[t['t_in'].year].append(t)
print('  %-6s %4s %6s %13s %13s %13s' % ('year', 'n', 'WR%', 'net', 'best', 'worst'))
for y in sorted(g):
    v = g[y]
    w = [x for x in v if x['pnl'] > 0]
    pn = sorted(x['pnl'] for x in v)
    print('  %-6d %4d %5.0f%% %13s %13s %13s'
          % (y, len(v), 100.0 * len(w) / len(v), m(sum(pn)), m(pn[-1]), m(pn[0])))

# ---------- 6 ----------
print('\n[6] EACH YEAR MINUS ITS OWN BEST TRADE  (symmetric extreme handling)')
line()
tot = 0
for y in sorted(g):
    v = sorted(g[y], key=lambda t: -t['pnl'])
    cut = sum(t['pnl'] for t in v[1:])
    tot += cut
    print('  %-6d  full %13s   minus best %13s   %s'
          % (y, m(sum(t['pnl'] for t in v)), m(cut),
             'positive' if cut > 0 else '** NEGATIVE **'))
print('  ALL YEARS, each minus its own best : %s' % m(tot))

# ---------- 7 ----------
print('\n[7] BY SESSION  (entry time)')
line()


def sess(t):
    hm = t['t_in'].hour * 100 + t['t_in'].minute
    return 'DAY 0845-1345' if 845 <= hm <= 1345 else 'NIGHT 1500-0500'


g = collections.defaultdict(list)
for t in T:
    g[sess(t)].append(t)
for k in sorted(g):
    v = g[k]
    w = [x for x in v if x['pnl'] > 0]
    pn = sorted(x['pnl'] for x in v)
    print('  %-18s %4d  WR %4.0f%%  net %13s  med %10s  best %12s'
          % (k, len(v), 100.0 * len(w) / len(v), m(sum(pn)), m(q(pn, .5)), m(pn[-1])))

# ---------- 8 ----------
print('\n[8] EQUITY PATH  (closed-trade, chronological)')
line()
eq = 0
peak = 0
mdd = 0
mdd_at = None
for t in T:
    eq += t['pnl']
    if eq > peak:
        peak = eq
    if eq - peak < mdd:
        mdd, mdd_at = eq - peak, t['t_out']
print('  closed-trade MDD %s   at %s' % (m(mdd), mdd_at))
yr = collections.OrderedDict()
run = 0
for t in T:
    run += t['pnl']
    yr[t['t_out'].year] = run
print('  running equity at each year end:')
for y, v in yr.items():
    print('     %d  %13s' % (y, m(v)))

# ---------- 9 ----------
print('\n[9] HOLDING TIME vs OUTCOME')
line()
for lbl, S2 in (('winners', W), ('losers', L)):
    h = sorted((t['t_out'] - t['t_in']).total_seconds() / 60.0 for t in S2)
    print('  %-8s n=%-4d  med %6.0f min   P75 %6.0f   P95 %7.0f   max %7.0f'
          % (lbl, len(S2), q(h, .5), q(h, .75), q(h, .95), h[-1]))

# ---------- 10 ----------
print('\n[10] MAE / MFE')
line()
for lbl, S2 in (('winners', W), ('losers', L)):
    mae = sorted(abs(t['mae']) for t in S2)
    mfe = sorted(abs(t['mfe']) for t in S2)
    print('  %-8s MAE med %9s P95 %10s max %10s | MFE med %9s P95 %10s max %10s'
          % (lbl, m(q(mae, .5)), m(q(mae, .95)), m(mae[-1]),
             m(q(mfe, .5)), m(q(mfe, .95)), m(mfe[-1])))
gb = [t for t in L if abs(t['mfe']) > 20000]
print('  losers that were up more than 20,000 at some point: %d  (net %s)'
      % (len(gb), m(sum(t['pnl'] for t in gb))))

# ---------- 11 ----------
print('\n[11] THE TAIL, AND THE LAST TRADE')
line()
for t in S[:7]:
    print('  +  %s -> %s  %-24s %12s' % (t['t_in'], t['t_out'], t['exit_sig'], m(t['pnl'])))
print('  ---')
for t in S[-5:]:
    print('  -  %s -> %s  %-24s %12s' % (t['t_in'], t['t_out'], t['exit_sig'], m(t['pnl'])))
print('  ---')
t = T[-1]
print('  LAST TRADE IN THE BACKTEST:')
print('     %s @%.0f -> %s @%.0f  %s  %s'
      % (t['t_in'], t['p_in'], t['t_out'], t['p_out'], t['exit_sig'], m(t['pnl'])))
