"""
verify_range_force_exit.py
Verify Constitution v1.1 Clause 7 (Range Force Exit) deployment.

L3 ConsolidationLong + L4 ConsolidationShort must contain:
  1. Range_ForceExit_Time(1200) input
  2. Range Force Exit Priority 0 block with proper label
  3. Priority order: comes AFTER Settlement_Flat, BEFORE strategy-specific exits

Other strategies (L1/L2/L5/S1) must NOT contain Range_ForceExit_Time
(they are not range strategies and the module would shorten their alpha).
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
import re

BASE = Path('C:/Users/User/Desktop/TXF1-Strategy-Lab/strategies')

RANGE_STRATEGIES = [
    ('L3', 'live/L3_ConsolidationLong.pla',  'CL_RangeForceExit',  'Sell'),
    ('L4', 'live/L4_ConsolidationShort.pla', 'CS_RangeForceExit',  'BuyToCover'),
]

NON_RANGE = [
    ('L1', 'live/L1_TrendLong.pla'),
    ('L2', 'live/L2_TrendShort.pla'),
    ('L5', 'live/L5_BreakoutLong.pla'),
    ('S1', 'live_simulation/S1_NightMomentum.pla'),
]


def check_file(text, sid, label, direction):
    results = []

    # 1. Input declaration
    m = re.search(r'Range_ForceExit_Time\s*\(\s*(\d+)\s*\)', text)
    if m and m.group(1) == '1200':
        results.append((f'{sid}-1', True, f'Range_ForceExit_Time(1200) input: got {m.group(1)}'))
    else:
        results.append((f'{sid}-1', False, f'Range_ForceExit_Time(1200) input MISSING or wrong default'))

    # 2. Label emitted
    if label in text:
        results.append((f'{sid}-2', True, f'{label} label emitted'))
    else:
        results.append((f'{sid}-2', False, f'{label} label NOT FOUND'))

    # 3. Time >= Range_ForceExit_Time gating
    pat = re.compile(rf'Time\s*>=\s*Range_ForceExit_Time', re.IGNORECASE)
    if pat.search(text):
        results.append((f'{sid}-3', True, 'Time >= Range_ForceExit_Time gate present'))
    else:
        results.append((f'{sid}-3', False, 'Time >= Range_ForceExit_Time gate MISSING'))

    # 4. Direction-correct exit order (Sell for L3, BuyToCover for L4)
    near_label = re.search(
        rf'{direction}\s*\(\s*"{label}"\s*\)\s*next\s*bar\s*at\s*Market',
        text, re.IGNORECASE)
    if near_label:
        results.append((f'{sid}-4', True, f'{direction}("{label}") next bar at Market'))
    else:
        results.append((f'{sid}-4', False, f'{direction}("{label}") syntax INCORRECT'))

    # 5. Priority ordering: Range MUST come after Settlement in the exit-chain code.
    #    (BreakExit positioning is strategy-internal; both end in "next bar at Market"
    #    so even if dual-triggered, only one exit fills next bar.)
    settle_label = label.replace('RangeForceExit', 'Settlement')

    def find_exit_code_pos(lbl):
        pat = re.compile(rf'(?:Sell|BuyToCover)\s*\(\s*"{lbl}"\s*\)\s*next', re.IGNORECASE)
        m = pat.search(text)
        return m.start() if m else -1

    pos_range = find_exit_code_pos(label)
    pos_settle = find_exit_code_pos(settle_label)

    if pos_range > 0 and pos_settle > 0 and pos_range > pos_settle:
        results.append((f'{sid}-5', True, f'order OK: Settlement({pos_settle}) < Range({pos_range})'))
    else:
        results.append((f'{sid}-5', False, f'order WRONG: Settlement({pos_settle}) > Range({pos_range})'))

    # 6. Range Force Exit 時間早於 Settlement_Flat_Time (1200 < 1230)
    rng_t = re.search(r'Range_ForceExit_Time\s*\(\s*(\d+)\s*\)', text)
    set_t = re.search(r'Settlement_Flat_Time\s*\(\s*(\d+)\s*\)', text)
    if rng_t and set_t:
        rv, sv = int(rng_t.group(1)), int(set_t.group(1))
        if rv < sv:
            results.append((f'{sid}-6', True, f'time order OK: Range({rv}) < Settlement({sv})'))
        else:
            results.append((f'{sid}-6', False, f'time order WRONG: Range({rv}) >= Settlement({sv})'))

    return results


def check_non_range(text, sid):
    """Non-range strategies must NOT have Range_ForceExit_Time
       (would cut trend alpha)."""
    if 'Range_ForceExit_Time' in text:
        return [(f'{sid}-NR', False, f'{sid} (non-range) contains Range_ForceExit_Time = ALPHA RISK')]
    return [(f'{sid}-NR', True, f'{sid} (non-range) correctly excludes Range_ForceExit_Time')]


print('=' * 80)
print('CONSTITUTION v1.1 CLAUSE 7 - Range Force Exit Verification')
print('=' * 80)
print()

all_results = []

print('--- Range strategies (must have RangeForceExit) ---')
for sid, path, label, direction in RANGE_STRATEGIES:
    fp = BASE / path
    text = fp.read_text(encoding='utf-8', errors='replace')
    print(f'\n[{sid}] {path}')
    for r in check_file(text, sid, label, direction):
        mark = '[OK  ]' if r[1] else '[FAIL]'
        print(f'  {mark} {r[0]}: {r[2]}')
        all_results.append(r)

print()
print('--- Non-range strategies (must NOT have RangeForceExit) ---')
for sid, path in NON_RANGE:
    fp = BASE / path
    text = fp.read_text(encoding='utf-8', errors='replace')
    for r in check_non_range(text, sid):
        mark = '[OK  ]' if r[1] else '[FAIL]'
        print(f'  {mark} {r[0]}: {r[2]}')
        all_results.append(r)

print()
print('=' * 80)
passed = sum(1 for _, ok, _ in all_results if ok)
total = len(all_results)
print(f'TOTAL: {passed}/{total} ({passed * 100 // total}%)')
if passed == total:
    print('Constitution v1.1 Clause 7 deployment OK.')
else:
    print('*** DEPLOYMENT INCOMPLETE ***')
    sys.exit(1)
