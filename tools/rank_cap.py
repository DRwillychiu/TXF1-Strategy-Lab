#!/usr/bin/env python3
"""A-test (v18 + stop cap) judge. Rule locked by Willy 2026-09-28 22:25, BEFORE any cap report was seen:
current best = v18.1 defaults (== v18.0 trade by trade from 2019-01-10);
1. guard: pre-live net of the challenger >= 85% of v18's pre-live net (drop <= 15%);
2. rule B: out of sample first (max streak AND net both better, one by > band 45,065 MC = 2,253 micro),
   reverse -> v18 stays; tie / mixed -> rule E on pre-live (streaks first, net when streaks tie).
usage: python rank_cap.py name=report.xlsx [...]"""
import sys
sys.path.insert(0, '/home/claude/l3r')
from rank_l3 import mets, b_compare
sys.path.insert(0, '/mnt/user-data/outputs')
from verify_settings import report_settings, pla_inputs, norm
BASE = '/tmp/vw/L3_v181.xlsx'
CODE = '/home/claude/l3r/v181.txt'
RUNKEYS = ('開始日期', '結束日期', '原始資本', '滑價', '佣金', '壓縮')
def valid(name, path):
    """added 2026-09-29 10:55: a report counts only if SL_Pct is the ONLY input changed vs v18.1 defaults
    and period / capital / slippage / commission / bars equal the v18.1 base report."""
    defaults = pla_inputs(open(CODE).read()); _, params, run = report_settings(path); _, _, run0 = report_settings(BASE)
    if '策略參數' in params:
        vals = [x.strip() for x in str(params['策略參數']).strip('()').split(',')]
        if len(vals) != len(defaults): print(f'[BAD] {name}: positional inputs {len(vals)} != code {len(defaults)}'); return False
        params = dict(zip(defaults.keys(), vals))
    missing = [k for k in defaults if k not in params] + [f'extra:{k}' for k in params if k not in defaults]
    changed = {k: norm(v) for k, v in params.items() if k in defaults and norm(v) != norm(defaults[k])}
    bad_run = [(k, str(run.get(k)), str(run0.get(k))) for k in RUNKEYS if str(run.get(k)) != str(run0.get(k))]
    # 2026-09-29 14:40 clarification (after the cap reports arrived; does not touch any metric): a LATER end date is
    # accepted only when the report has no trade entered or exited after the base end, so the compared window is identical.
    if bad_run and [k for k, _, _ in bad_run] == ['結束日期'] and run.get('結束日期') > run0.get('結束日期'):
        from lf import load2
        late = [t for t in load2(path) if t['dt'] > run0['結束日期'] or t['xt'] > run0['結束日期']]
        print(f"[info] {name}: end {run.get('結束日期')} vs base {run0.get('結束日期')}; trades after base end: {len(late)}")
        if not late: bad_run = []
    ok = not missing and sorted(changed) == sorted(ALLOW) and not bad_run
    print(f"[{'OK ' if ok else 'BAD'}] {name}: inputs changed {changed or 'none'}; missing {missing or 'none'}; run diffs {bad_run or 'none'}")
    return ok
ALLOW = ['SL_Pct']
if __name__ == '__main__':
    # 2026-09-29 16:20: optional --base= --code= --allow=A,B so the same locked rule (net guard + rule B -> E)
    # can judge the Loser_Flat test: base = v18.2 report, code = v18.3, allowed change = Loser_Flat_On
    args = []
    for a in sys.argv[1:]:
        if a.startswith('--base='): BASE = a[7:]
        elif a.startswith('--code='): CODE = a[7:]
        elif a.startswith('--allow='): ALLOW = a[8:].split(',')
        else: args.append(a)
    sys.argv = [sys.argv[0]] + args
    bp, bo = mets(BASE); best = ('base', bp, bo)
    print(f"v18 (current best) pre net {bp['net']:,.0f} maxstk {bp['max_streak']:,.0f} top3 {bp['top3']:,.0f} MDD {bp['mdd']:,.0f} | OOS micro net {bo['net']/20:,.0f} maxstk {bo['max_streak']/20:,.0f}")
    for arg in sys.argv[1:]:
        name, path = arg.split('=', 1)
        if not valid(name, path): print(f'{name}: INVALID RUN, not judged'); continue
        pre, oos = mets(path)
        g = pre['net'] >= 0.85 * bp['net']
        print(f"{name:8s} pre net {pre['net']:,.0f} ({(pre['net']/bp['net']-1)*100:+.1f}% vs v18) maxstk {pre['max_streak']:,.0f} top3 {pre['top3']:,.0f} MDD {pre['mdd']:,.0f} | OOS micro net {oos['net']/20:,.0f} maxstk {oos['max_streak']/20:,.0f} | net guard {'PASS' if g else 'FAIL'}")
        if not g: continue
        win, txt = b_compare((pre, oos), (best[1], best[2])); print(f"   vs current best {best[0]}: {txt}")
        if win: best = (name, pre, oos)
    print('RESULT (A-test rule):', best[0])
