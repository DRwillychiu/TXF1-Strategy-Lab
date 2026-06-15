"""S1 v2.4 verification — revert to v2.1 ExitTime behavior + keep Holiday safety."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('strategies/live_simulation/S1_NightMomentum.pla', 'r', encoding='utf-8') as f:
    s = f.read()

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

clean = strip_comments(s)
checks = []
def chk(name, ok, detail=''):
    print(f'  [{"OK  " if ok else "FAIL"}] {name}: {detail}')
    checks.append(ok)

print('=' * 65)
print('S1 v2.4 — REVERT TO v2.1 ExitTime + KEEP Holiday Safety')
print('=' * 65)

# Version
chk('Version v2.4 in header', 'v2.4' in s, '')

# v2.1 ORIGINAL ExitTime RESTORED
m = re.search(r'ExitTime\s*\(\s*(\d+)\s*\)', clean)
chk('ExitTime = 500 (v2.1 original)',
    m and m.group(1) == '500',
    f'got {m.group(1) if m else "none"}')

# v2.3 inputs REMOVED
for name in ['EntryEnd_Time', 'DailyFlat_Time', 'NightCloseBar_Time']:
    chk(f'v2.3 input {name} REMOVED',
        not re.search(rf'\b{name}\s*\(\s*\d+\s*\)', clean), '')

# v2.3 label REMOVED
chk('v2.3 label LX_NM_DailyFlat REMOVED',
    'LX_NM_DailyFlat' not in clean, '')
chk('v2.3 label LX_NM_DaySession_EMERGENCY REMOVED',
    'LX_NM_DaySession_EMERGENCY' not in clean, '')

# v2.1 ORIGINAL label RESTORED
chk('v2.1 label LX_NM_Time RESTORED', 'LX_NM_Time' in s, '')

# Holiday Safety KEPT (kept from v2.2/v2.3)
for name, default in [('Holiday_Flat_Time', '415'),
                      ('Registry_Valid_Until', '1270101')]:
    m = re.search(rf'{name}\s*\(\s*(\d+)\s*\)', clean)
    chk(f'Holiday Safety input {name} = {default}',
        m and m.group(1) == default, '')

m = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', clean)
chk('Holiday Safety Manual_Kill_Switch = false',
    m and m.group(1).lower() == 'false', '')

# Holiday labels still present
for lbl in ['LX_NM_Kill', 'LX_NM_RegistryEnd', 'LX_NM_Holiday']:
    chk(f'Holiday label {lbl} present', lbl in s, '')

# v2.1 entry condition restored
chk('Entry condition uses Time < ExitTime (v2.1 original)',
    'Time < ExitTime' in clean, '')

# v2.1 night session definition restored
chk('v_IsNightSession uses ExitTime (v2.1 original)',
    bool(re.search(
        r'v_IsNightSession\s*=\s*\(Time\s*>=\s*NightOpen\)\s*or\s*\(Time\s*<\s*ExitTime\)',
        clean)), '')

# Entry gate has v_Holiday_Block (kept from v2.2/v2.3)
m = re.search(
    r'if v_RangeReady and v_IsNightSession and Time < ExitTime and\s*'
    r'v_VolPass and v_Holiday_Block = false then begin', clean)
chk('Entry gate has v_Holiday_Block = false',
    bool(m), 'safety preserved')

# Time-based exit fires at Time >= ExitTime
chk('LX_NM_Time exit condition: Time >= ExitTime and Time < NightOpen',
    bool(re.search(
        r'if Time >= ExitTime and Time < NightOpen then begin',
        clean)), '')

# Holiday registry preserved (63 entries)
entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)
chk('63 Holiday registry entries preserved',
    len(entries) == 63, f'got {len(entries)}')

# Existing labels preserved
for lbl in ['LE_NM_Long', 'LX_NM_SL', 'LX_NM_TP', 'LX_NM_Trail']:
    chk(f'Preserved label {lbl}', lbl in s, '')

# Syntax sanity
b = len(re.findall(r'\bbegin\b', clean, re.IGNORECASE))
e = len(re.findall(r'\bend\b', clean, re.IGNORECASE))
chk(f'begin/end balance ({b}/{e})', b == e, '')

last_char = s.rstrip()[-1]
chk('File ends cleanly', last_char in ';}', '')

print()
passed = sum(1 for c in checks if c)
print(f'PASSED: {passed}/{len(checks)} ({100*passed/len(checks):.0f}%)')
if passed == len(checks):
    print('S1 v2.4 ready - matches v2.1 ExitTime + Holiday safety preserved')
