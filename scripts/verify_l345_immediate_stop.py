"""Verify L3/L4/L5 P3b Immediate Stop Guard implementation.

Checks per strategy:
  1. Version includes ImmediateStop
  2. Changelog has P3b entry
  3. SetStopLoss call with correct formula (box-based)
  4. Correct MP guard direction (Long: MP<=0, Short: MP>=0)
  5. SetStopLoss placed before entry order
  6. BigPointValue used
  7. Existing v_SL_Locked freeze still intact
  8. Settlement_Flat still intact
  9. Exactly 1 SetStopLoss call (outside comments)
"""
import re, sys, io
from strategy_discovery import resolve
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def strip_comments(s):
    out = []; depth = 0
    for c in s:
        if c == '{': depth += 1; continue
        if c == '}':
            if depth > 0: depth -= 1
            continue
        if depth == 0: out.append(c)
    return ''.join(out)

results = []
def chk(name, ok, detail=''):
    print(f'  [{"OK  " if ok else "FAIL"}] {name}{": " + detail if detail else ""}')
    results.append(ok)

strategies = [
    {
        'name': 'L3 ConsolidationLong',
        'file': resolve('L3_ConsolidationLong'),
        'version_pat': r'ImmediateStop',
        'changelog_pat': r'v13\.4\+.*P3b\s+Immediate\s+Stop',
        'ssl_pat': r'SetStopLoss\s*\(\s*AbsValue\s*\(\s*Close\s*-\s*\(\s*v_Box_Btm\s*-\s*v_ATR_Buffer\s*\)\s*\)\s*\*\s*BigPointValue\s*\)',
        'mp_guard_pat': r'if\s+MarketPosition\s*<=\s*0\s+then\s*\n\s*SetStopLoss',
        'entry_label': 'CL_Entry_Bot',
        'settlement_label': 'CL_Settlement',
        'direction': 'Long',
    },
    {
        'name': 'L4 ConsolidationShort',
        'file': resolve('L4_ConsolidationShort'),
        'version_pat': r'ImmediateStop',
        'changelog_pat': r'v14\.4\+.*P3b\s+Immediate\s+Stop',
        'ssl_pat': r'SetStopLoss\s*\(\s*AbsValue\s*\(\s*\(\s*v_Box_Top\s*\+\s*v_Current_ATR\s*\*\s*ATR_Stop_Mult\s*\)\s*-\s*Close\s*\)\s*\*\s*BigPointValue\s*\)',
        'mp_guard_pat': r'if\s+MarketPosition\s*>=\s*0\s+then\s*\n\s*SetStopLoss',
        'entry_label': 'CS_Entry',
        'settlement_label': 'CS_Settlement',
        'direction': 'Short',
    },
    {
        'name': 'L5 BreakoutLong',
        'file': resolve('L5_BreakoutLong'),
        'version_pat': r'ImmediateStop',
        'changelog_pat': r'v19\.8\+.*P3b\s+Immediate\s+Stop',
        'ssl_pat': r'SetStopLoss\s*\(\s*AbsValue\s*\(\s*Close\s*-\s*\(\s*v_Box_Btm\s*-\s*v_ATR_Buffer\s*\)\s*\)\s*\*\s*BigPointValue\s*\)',
        'mp_guard_pat': r'if\s+MarketPosition\s*<=\s*0\s+then\s*\n\s*SetStopLoss',
        'entry_label': 'BL_Entry_Bot',
        'settlement_label': 'BL_Settlement',
        'direction': 'Long',
    },
]

for s in strategies:
    with open(s['file'], 'r', encoding='utf-8') as f:
        raw = f.read()
    clean = strip_comments(raw)
    lines = raw.split('\n')

    print(f'=== {s["name"]} P3b Verification ({s["file"]}) ===')
    print(f'    Lines: {len(lines)}')

    # 1. Version
    chk(f'{s["name"]}: Version includes ImmediateStop',
        bool(re.search(s['version_pat'], raw)), '')

    # 2. Changelog
    chk(f'{s["name"]}: Changelog has P3b entry',
        bool(re.search(s['changelog_pat'], raw)), '')

    # 3. SetStopLoss formula
    ssl_match = re.search(s['ssl_pat'], clean, re.DOTALL)
    chk(f'{s["name"]}: SetStopLoss formula correct',
        bool(ssl_match),
        'box-based formula')

    # 4. MP guard
    mp_match = re.search(s['mp_guard_pat'], raw, re.IGNORECASE)
    chk(f'{s["name"]}: MP guard correct ({s["direction"]})',
        bool(mp_match),
        f'{"MP<=0" if s["direction"]=="Long" else "MP>=0"}')

    # 5. Placement before entry
    ssl_line = None
    entry_line = None
    for i, line in enumerate(lines):
        if 'SetStopLoss' in line and ('AbsValue' in line or 'BigPointValue' in line) and ssl_line is None:
            ssl_line = i
        if s['entry_label'] in line and entry_line is None:
            entry_line = i
    chk(f'{s["name"]}: SetStopLoss before entry',
        ssl_line is not None and entry_line is not None and ssl_line < entry_line,
        f'SSL@{ssl_line+1 if ssl_line else "?"}, entry@{entry_line+1 if entry_line else "?"}')

    # 6. BigPointValue
    chk(f'{s["name"]}: BigPointValue used',
        'BigPointValue' in clean, '')

    # 7. v_SL_Locked still intact
    chk(f'{s["name"]}: v_SL_Locked still present',
        'v_SL_Locked' in clean, '')

    # 8. Settlement_Flat
    chk(f'{s["name"]}: Settlement label present',
        bool(re.search(s['settlement_label'], raw)), '')

    # 9. Exactly 1 SetStopLoss call
    ssl_count = len(re.findall(r'SetStopLoss\s*\(', clean))
    chk(f'{s["name"]}: Exactly 1 SetStopLoss (outside comments)',
        ssl_count == 1,
        f'found {ssl_count}')

    print()

# Summary
passed = sum(results)
total = len(results)
print(f'=== TOTAL: {passed}/{total} {"ALL PASS" if passed == total else "FAILURES DETECTED"} ===')
sys.exit(0 if passed == total else 1)
