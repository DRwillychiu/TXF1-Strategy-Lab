"""S1 v2.3 verification — Daily Flat as PRIMARY safety."""
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

print('=' * 60)
print('S1 v2.3 PRIMARY SAFETY ARCHITECTURE CHECK')
print('=' * 60)

# Version
chk('v2.3 in header', 'v2.3' in s, '')

# Old ExitTime input REMOVED
chk('Old ExitTime input REMOVED',
    not re.search(r'\bExitTime\s*\(\s*\d+\s*\)', clean),
    'should not exist')

# New PRIMARY inputs
for name, default in [('EntryEnd_Time', '415'),
                      ('DailyFlat_Time', '415'),
                      ('NightCloseBar_Time', '500')]:
    m = re.search(rf'{name}\s*\(\s*(\d+)\s*\)', clean)
    chk(f'PRIMARY input {name} = {default}',
        m and m.group(1) == default,
        f'got {m.group(1) if m else "none"}')

# SECONDARY inputs (preserved from v2.2)
for name, default in [('Holiday_Flat_Time', '415'),
                      ('Registry_Valid_Until', '1270101')]:
    m = re.search(rf'{name}\s*\(\s*(\d+)\s*\)', clean)
    chk(f'SECONDARY input {name} = {default}',
        m and m.group(1) == default, '')

# Manual_Kill_Switch default false
m = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', clean)
chk('SECONDARY input Manual_Kill_Switch = false',
    m and m.group(1).lower() == 'false', '')

# OLD LX_NM_Time label REMOVED, replaced by LX_NM_DailyFlat
chk('Old LX_NM_Time label REMOVED',
    'LX_NM_Time' not in clean,
    'must not be in code')
chk('New LX_NM_DailyFlat label EMITTED',
    'LX_NM_DailyFlat' in clean, '')

# NEW Day Session Emergency safety net
chk('NEW LX_NM_DaySession_EMERGENCY safety net',
    'LX_NM_DaySession_EMERGENCY' in clean, '')

# Daily flat condition uses NightCloseBar_Time as hard cap
chk('DailyFlat fires only Time < NightCloseBar_Time',
    bool(re.search(
        r'Time\s*>=\s*DailyFlat_Time\s+and\s+Time\s*<\s*NightCloseBar_Time',
        clean)), 'prevents 09:00 bug')

# Entry condition uses EntryEnd_Time (not ExitTime)
chk('Entry condition uses Time < EntryEnd_Time',
    'Time < EntryEnd_Time' in clean,
    'no longer uses old ExitTime')

# v_IsNightSession uses NightCloseBar_Time
chk('v_IsNightSession uses NightCloseBar_Time',
    bool(re.search(
        r'v_IsNightSession\s*=\s*\(Time\s*>=\s*NightOpen\)\s*or\s*\(Time\s*<\s*NightCloseBar_Time\)',
        clean)), '')

# Mutually exclusive priority chain (if/else if)
chk('PRIORITY chain has 5 mutually-exclusive branches',
    bool(re.search(
        r'if Manual_Kill_Switch.*?else if v_Registry_Expired.*?else if v_Holiday_Block.*?'
        r'else if Time\s*>=\s*DailyFlat_Time.*?else if Time\s*>=\s*845',
        s, re.DOTALL)),
    'Kill > Registry > Holiday > DailyFlat > DaySession')

# Holiday registry preserved
entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)
chk('63 Holiday registry entries preserved',
    len(entries) == 63, f'got {len(entries)}')

# Existing labels preserved
for lbl in ['LE_NM_Long', 'LX_NM_SL', 'LX_NM_TP', 'LX_NM_Trail',
            'LX_NM_Kill', 'LX_NM_RegistryEnd', 'LX_NM_Holiday']:
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
    print('S1 v2.3 ready for MC12 simulation deployment')
else:
    print('Issues found')
