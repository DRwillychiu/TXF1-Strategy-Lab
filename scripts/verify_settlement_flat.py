"""Verify Settlement_Flat module deployed to L1-L5 + S1.

Detection rule: 3rd Wed of month = DayOfWeek(Date)=3 AND DayOfMonth in [15,21].
Each strategy should have:
  1. Settlement_Flat_Time(1230) input
  2. v_Settlement_Day variable
  3. Detection logic
  4. Entry block (v_Settlement_Day = false in entry condition)
  5. Priority 0 exit (with strategy-specific label)
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILES = {
    'L1': ('strategies/live/L1_TrendLong.pla', 'TL_Settlement'),
    'L2': ('strategies/live/L2_TrendShort.pla', 'TS_Settlement'),
    'L3': ('strategies/live/L3_ConsolidationLong.pla', 'CL_Settlement'),
    'L4': ('strategies/live/L4_ConsolidationShort.pla', 'CS_Settlement'),
    'L5': ('strategies/live/L5_BreakoutLong.pla', 'BL_Settlement'),
    'S1': ('strategies/live_simulation/S1_NightMomentum.pla', 'LX_NM_Settlement'),
}

def strip_comments(s):
    out = []; depth = 0
    for c in s:
        if c == '{':
            depth += 1; continue
        if c == '}':
            if depth > 0: depth -= 1
            continue
        if depth == 0: out.append(c)
    return ''.join(out)

results = []
def chk(name, ok, detail=''):
    print(f'  [{"OK  " if ok else "FAIL"}] {name}: {detail}')
    results.append(ok)

for k, (path, expected_label) in FILES.items():
    print()
    print(f'=== {k} ({path}) ===')
    with open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    clean = strip_comments(s)

    # 1. Settlement_Flat_Time input
    m = re.search(r'Settlement_Flat_Time\s*\(\s*(\d+)\s*\)', clean)
    chk(f'{k}-1: Settlement_Flat_Time(1230) input',
        m and m.group(1) == '1230',
        f'got {m.group(1) if m else "missing"}')

    # 2. v_Settlement_Day variable
    chk(f'{k}-2: v_Settlement_Day variable declared',
        bool(re.search(r'\bv_Settlement_Day\s*\(', clean, re.IGNORECASE)), '')

    # 3. Detection logic
    has_detection = bool(re.search(
        r'v_Settlement_Day\s*=\s*\(\s*DayOfWeek\s*\(\s*Date\s*\)\s*=\s*3\s*\)',
        clean, re.IGNORECASE))
    chk(f'{k}-3: DayOfWeek(Date)=3 detection logic',
        has_detection, '')

    # 4. DayOfMonth bounds
    has_bounds = bool(re.search(
        r'DayOfMonth\s*\(\s*Date\s*\)\s*>=\s*15\s*\)?\s+and\s*\(?\s*DayOfMonth\s*\(\s*Date\s*\)\s*<=\s*21',
        clean, re.IGNORECASE))
    chk(f'{k}-4: DayOfMonth in [15,21] bounds',
        has_bounds, '')

    # 5. Strategy-specific Settlement label exists in code
    chk(f'{k}-5: {expected_label} label emitted',
        expected_label in s, '')
    # Also accept _Bot/_Mid variants (L5)
    if expected_label not in s:
        # Try _Bot variant for L5
        if expected_label + '_Bot' in s:
            print(f'      ({expected_label}_Bot/_Mid variant accepted for L5)')

    # 6. Entry block via v_Settlement_Day = false OR v_Settlement_Day then v_Allow_Entry=false (L5 pattern)
    has_entry_block = (
        bool(re.search(r'v_Settlement_Day\s*=\s*false', clean, re.IGNORECASE)) or
        bool(re.search(r'if\s+v_Settlement_Day\s+then\s*\n?\s*v_Allow_Entry\s*=\s*false',
                       clean, re.IGNORECASE))
    )
    chk(f'{k}-6: Entry block via v_Settlement_Day',
        has_entry_block, '')

    # 7. Time >= Settlement_Flat_Time gate in exit
    has_time_gate = bool(re.search(
        r'Time\s*>=\s*Settlement_Flat_Time', clean, re.IGNORECASE))
    chk(f'{k}-7: Exit gated by Time >= Settlement_Flat_Time',
        has_time_gate, '')

print()
print('=' * 60)
passed = sum(1 for r in results if r)
total = len(results)
print(f'TOTAL: {passed}/{total} ({100*passed/total:.0f}%)')
if passed == total:
    print('Settlement_Flat module deployed to all 6 strategies (L1-L5 + S1)')
else:
    print(f'{total - passed} checks failed - review above')
