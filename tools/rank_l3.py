#!/usr/bin/env python3
"""L3 final ranking. Rule B locked by Willy 2026-09-28 20:38, BEFORE any C2 report was seen.
Gate unchanged (9/27 19:24): pre-live max streak AND top-3 both smaller than live, at least one by more than
one band (45,065); pre-live net drop <= 15%; out-of-sample max streak smaller than live by more than one band.
Ranking among gate passers (rule B):
  1. out of sample first: challenger wins if OOS max streak AND OOS net are both better, at least one by more
     than one band (45,065 MC = 2,253 micro); the current best stays if the reverse holds;
  2. otherwise (tie / mixed) -> rule E on pre-live (streaks first, net only when streaks tie).
usage: python rank_l3.py name=report.xlsx [name=report.xlsx ...]"""
import sys, pickle
sys.path.insert(0, '/home/claude/l3r')
from regime import load_mc
from score_group import metrics, e_compare, LO, LIVE, HI, BAND
def mets(path):
    tr = load_mc(path)
    return metrics([t for t in tr if LO <= t['dt'] < LIVE]), metrics([t for t in tr if LIVE <= t['dt'] < HI])
def gate(pre, oos, c):
    dm, dt = pre['max_streak'] - c['pre']['max_streak'], pre['top3'] - c['pre']['top3']
    g12 = dm > 0 and dt > 0 and (dm > BAND or dt > BAND); g3 = pre['net'] >= 0.85 * c['pre']['net']
    g4 = oos['max_streak'] - c['oos']['max_streak'] > BAND
    why = [] if g12 else ['streaks not both smaller (one by > band)']
    if not g3: why.append(f"net {pre['net'] / c['pre']['net'] * 100 - 100:+.1f}% beyond -15%")
    if g12 and g3 and not g4: why.append('out-of-sample max streak not better by > band')
    return g12 and g3 and g4, why
def b_compare(a, b):
    """a = challenger (pre, oos), b = current best (pre, oos)"""
    ds, dn = a[1]['max_streak'] - b[1]['max_streak'], a[1]['net'] - b[1]['net']
    txt = f"OOS micro: max streak {ds / 20:+,.0f}, net {dn / 20:+,.0f} (band 2,253)"
    if ds > 0 and dn > 0 and (ds > BAND or dn > BAND): return True, 'CHALLENGER wins on out of sample; ' + txt
    if ds < 0 and dn < 0 and (-ds > BAND or -dn > BAND): return False, 'CURRENT BEST stays on out of sample; ' + txt
    e = e_compare(a[0], b[0])
    return e.startswith('CHALLENGER'), f'out of sample tie/mixed ({txt}) -> rule E: {e}'
if __name__ == '__main__':
    c = pickle.load(open('/tmp/control_g1.pkl', 'rb'))
    best = None
    for arg in sys.argv[1:]:
        name, path = arg.split('=', 1); pre, oos = mets(path); ok, why = gate(pre, oos, c)
        print(f"{name:10s} gate {'PASS' if ok else 'FAIL: ' + '; '.join(why)} | pre net {pre['net']:,.0f} maxstk {pre['max_streak']:,.0f} top3 {pre['top3']:,.0f} MDD {pre['mdd']:,.0f} | OOS micro net {oos['net'] / 20:,.0f} maxstk {oos['max_streak'] / 20:,.0f}")
        if not ok: continue
        if best is None: best = (name, pre, oos); print(f"   -> first gate passer, becomes current best"); continue
        win, txt = b_compare((pre, oos), (best[1], best[2]))
        print(f"   vs current best {best[0]}: {txt}")
        if win: best = (name, pre, oos)
    print('CURRENT BEST (rule B):', best[0] if best else 'none -> live version stays')
