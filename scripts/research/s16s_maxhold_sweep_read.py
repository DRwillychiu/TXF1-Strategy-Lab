"""Read the MaxHold_Pct sweep and grade it against the pre-registration.

Pre-registration: docs/research/S16S_MaxHoldPct_sweep_preregistration_20260824.md
committed as 781ccc6 BEFORE this data existed.
"""
import sys
import collections
sys.path.insert(0, 'C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts')
import compare_mc12_reports as C

# (MaxHold_Pct, net, maxIntradayDD) transcribed from the MC12 optimisation report
ROWS = [
    (2.35, 2494400, -505600), (2.45, 2490400, -505600), (2.30, 2474800, -505600),
    (4.40, 2456000, -505600), (4.00, 2454400, -505600), (2.40, 2446400, -505600),
    (4.35, 2444800, -505600), (3.95, 2442000, -505600), (4.30, 2433600, -505600),
    (3.90, 2429200, -505600), (4.25, 2422800, -505600), (2.25, 2420000, -505600),
    (3.85, 2416400, -505600), (3.65, 2412400, -505600), (4.20, 2412000, -505600),
    (3.80, 2404000, -505600), (4.15, 2400800, -505600), (3.60, 2396400, -505600),
    (3.75, 2391200, -505600), (4.10, 2390000, -505600), (3.55, 2379600, -505600),
    (4.05, 2379200, -505600), (3.70, 2378400, -505600), (3.40, 2377600, -505600),
    (2.20, 2366400, -505600), (3.50, 2363600, -505600), (3.35, 2357200, -505600),
    (3.45, 2347600, -505600), (3.30, 2337600, -505600), (3.25, 2317600, -505600),
    (2.10, 2313600, -505600), (2.15, 2312000, -505600), (3.20, 2297200, -505600),
    (2.05, 2278400, -505600), (3.15, 2277600, -505600), (3.10, 2257600, -505600),
    (3.05, 2237200, -505600), (2.55, 2236000, -505600), (2.00, 2230800, -505600),
    (2.80, 2228400, -505600), (3.00, 2217200, -505600), (2.50, 2201200, -505600),
    (2.75, 2201200, -505600), (2.95, 2197600, -505600), (2.90, 2176800, -505600),
    (2.70, 2174800, -505600), (1.95, 2164000, -505600), (2.85, 2157600, -505600),
    (2.65, 2147600, -505600), (2.60, 2120400, -505600), (1.90, 2097600, -505600),
    (1.85, 2053200, -505600), (4.55, 2041200, -583200), (4.50, 2039200, -583200),
    (4.45, 2036800, -583200), (1.80, 2004400, -505600), (1.75, 1987200, -505600),
    (4.60, 1984000, -583200), (4.65, 1984000, -583200), (4.70, 1984000, -583200),
    (4.75, 1984000, -583200), (4.80, 1984000, -583200), (4.85, 1984000, -583200),
    (4.90, 1984000, -583200), (4.95, 1984000, -583200), (5.00, 1984000, -583200),
    (1.70, 1900800, -505600), (1.65, 1874000, -505600), (1.60, 1781600, -505600),
    (1.40, 1768000, -505600), (1.55, 1717200, -505600), (1.45, 1707600, -505600),
    (1.20, 1659200, -364800), (1.35, 1645600, -505600), (1.25, 1623200, -364800),
    (1.50, 1620800, -505600), (1.00, 1565200, -350000), (1.30, 1552000, -505600),
    (1.15, 1544400, -364800), (1.10, 1540800, -364800), (1.05, 1418000, -364800),
]
D = {r[0]: (r[1], r[2]) for r in ROWS}
CUR = 2.30
BASE = D[CUR][0]


def m(x):
    return format(int(round(x)), ',')


assert len(ROWS) == 81, len(ROWS)
print('=' * 78)
print('MaxHold_Pct SWEEP  --  81 cells, graded against pre-registration 781ccc6')
print('=' * 78)

# ---------- P1 ----------
print('\n[P1] MODEL VALIDATION  -- 27 predicted cells, 1.00 to 2.30')
print('-' * 78)
T = C.read_trades('C:/Users/User/Downloads/TXF1  S16_S_MACrossShort_v1.26.0 策略回測績效報告.xlsx')
LOT, SLIP = 400.0, 4000.0


def predict(p):
    tot = 0
    for t in T:
        tgt = t['p_in'] * p / 100 * LOT - SLIP
        tot += tgt if t['mfe'] >= tgt else t['pnl']
    return tot


errs = []
print('  %-6s %13s %13s %10s' % ('pct', 'predicted', 'actual', 'error'))
p = 1.00
while p <= 2.30001:
    pr, ac = predict(p), D[round(p, 2)][0]
    e = abs(pr - ac) / ac * 100
    errs.append(e)
    print('  %-6.2f %13s %13s %9.2f%%' % (p, m(pr), m(ac), e))
    p = round(p + 0.05, 2)
errs.sort()
med = errs[len(errs) // 2]
print('  ---')
print('  MEDIAN ABSOLUTE ERROR  %.2f%%   (kill threshold was 15%%, trust threshold 5%%)' % med)
print('  worst single cell      %.2f%%' % errs[-1])
over = [(k, v[0]) for k, v in D.items() if k < CUR and v[0] > BASE]
print('  cells below %.2f that beat the current %s : %s'
      % (CUR, m(BASE), over if over else 'NONE  -> monotonicity claim survives'))
print('  VERDICT: %s' % ('MODEL VALIDATED' if med < 5 and not over else 'MODEL FAILED'))

# ---------- P5 ----------
print('\n[P5] N-INFINITY  -- what the strategy is worth with NO percentage target')
print('-' * 78)
tops = sorted(k for k in D if k >= 4.60)
vals = set(D[k][0] for k in tops)
print('  cells 4.60..5.00 : %s  -> %s' % (sorted(vals), 'CONVERGED' if len(vals) == 1 else 'not converged'))
NINF = D[5.00][0]
print('  N-infinity        %13s' % m(NINF))
print('  current 2.30      %13s' % m(BASE))
print('  the target is worth %s  = +%.1f%%' % (m(BASE - NINF), 100.0 * (BASE - NINF) / NINF))
print('  -> M8_Form = 2 (percentage target) is decisively confirmed')

# ---------- P4 ----------
print('\n[P4] DRAWDOWN')
print('-' * 78)
dd = collections.defaultdict(list)
for k, (n, d) in D.items():
    dd[d].append(k)
for d in sorted(dd):
    ks = sorted(dd[d])
    print('  %10s  %2d cells   %.2f .. %.2f' % (m(d), len(ks), ks[0], ks[-1]))
print('  prediction was "MDD will not improve at higher targets" -> %s'
      % ('HELD (high cells are WORSE at -583,200)' if D[5.00][1] < D[CUR][1] else 'REFUTED'))
lowdd = [k for k, v in D.items() if v[1] > -400000]
print('  cells with BETTER MDD than current: %s' % sorted(lowdd))
best_low = max(lowdd, key=lambda k: D[k][0])
print('  best of them: %.2f  net %s (%s vs current)  MDD %s (%s)'
      % (best_low, m(D[best_low][0]), m(D[best_low][0] - BASE), m(D[best_low][1]),
         m(D[best_low][1] - D[CUR][1])))

# ---------- plateau ----------
print('\n[PLATEAU] contiguous bands within 5% of the global max')
print('-' * 78)
ks = sorted(D)
mx = max(v[0] for v in D.values())
thr = mx * 0.95
band = []
bands = []
for k in ks:
    if D[k][0] >= thr:
        band.append(k)
    else:
        if band:
            bands.append(band)
        band = []
if band:
    bands.append(band)
print('  global max %s at %.2f ; threshold %s' % (m(mx), max(D, key=lambda k: D[k][0]), m(thr)))
for b in sorted(bands, key=lambda b: -(b[-1] - b[0])):
    v = [D[k][0] for k in b]
    width = b[-1] - b[0]
    print('  %.2f .. %.2f  width %.2f (%2d cells)  min %s  mean %s  spread %.1f%%  centre %.2f'
          % (b[0], b[-1], width, len(b), m(min(v)), m(sum(v) / len(v)),
             100.0 * (max(v) - min(v)) / max(v), (b[0] + b[-1]) / 2))
print('  CLAUDE.md gate: plateau width > 20%% of swept range (4.00) = 0.80')
for b in bands:
    print('     %.2f..%.2f width %.2f -> %s' % (b[0], b[-1], b[-1] - b[0],
          'PASS' if b[-1] - b[0] > 0.80 else 'FAIL'))

# ---------- cliffs ----------
print('\n[CLIFFS] largest single-step drops')
print('-' * 78)
drops = []
for i in range(len(ks) - 1):
    a, b = ks[i], ks[i + 1]
    drops.append((D[b][0] - D[a][0], a, b))
drops.sort()
for d, a, b in drops[:6]:
    print('  %.2f -> %.2f   %12s   (%.1f%% of net)' % (a, b, m(d), 100.0 * abs(d) / D[a][0]))

# ---------- neighbourhood robustness ----------
print('\n[ROBUSTNESS] 5-cell window (+-0.10) around each candidate')
print('-' * 78)
print('  %-6s %13s %13s %13s' % ('pct', 'window min', 'window mean', 'net'))
for c in (2.25, 2.30, 2.35, 2.40, 2.45, 3.95, 4.00, 4.40):
    w = [D[round(c + o, 2)][0] for o in (-.10, -.05, 0, .05, .10) if round(c + o, 2) in D]
    print('  %-6.2f %13s %13s %13s%s' % (c, m(min(w)), m(sum(w) / len(w)), m(D[c][0]),
          '   <== current' if c == CUR else ''))
