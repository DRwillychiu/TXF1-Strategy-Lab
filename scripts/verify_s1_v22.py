"""Quick sanity check for S1 v2.2 (P0 + P1 fixes)."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('strategies/batch01/S1_NightMomentum.pla', 'r', encoding='utf-8') as f:
    s = f.read()

def strip_comments(s):
    out = []
    depth = 0
    for c in s:
        if c == '{':
            depth += 1; continue
        if c == '}':
            if depth > 0: depth -= 1
            continue
        if depth == 0:
            out.append(c)
    return ''.join(out)

clean = strip_comments(s)

checks = []
def chk(name, ok, detail=''):
    mark = 'OK  ' if ok else 'FAIL'
    print(f'  [{mark}] {name}: {detail}')
    checks.append(ok)

print('=' * 60)
print('S1 v2.2 SANITY CHECK')
print('=' * 60)

# Version
chk('Header version v2.2', 'v2.2' in s, '')

# P0 fix
exit_pat = re.search(r'ExitTime\s*\(\s*(\d+)\s*\)', clean)
chk('P0: ExitTime = 415 (was 500)',
    exit_pat and exit_pat.group(1) == '415',
    f"got {exit_pat.group(1) if exit_pat else 'none'}")

# P1 inputs
hft = re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', clean)
chk('P1: Holiday_Flat_Time = 415',
    hft and hft.group(1) == '415', '')

rvu = re.search(r'Registry_Valid_Until\s*\(\s*(\d+)\s*\)', clean)
chk('P1: Registry_Valid_Until = 1270101',
    rvu and rvu.group(1) == '1270101', '')

mks = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', clean)
chk('P1: Manual_Kill_Switch default = false',
    mks and mks.group(1).lower() == 'false', '')

# Holiday registry
chk('P1: Holiday_Tail[80] array declared',
    'Holiday_Tail[80](0)' in clean, '')

entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)
chk(f'P1: 63 registry entries', len(entries) == 63, f"got {len(entries)}")

chk('P1: 1260619 (Dragon Boat eve+1) present',
    '1260619' in clean, '')

# Compare with L4 registry (byte-equivalent check)
with open('strategies/live/L4_ConsolidationShort.pla', 'r', encoding='utf-8') as f:
    l4 = f.read()
l4_clean = strip_comments(l4)
l4_entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', l4_clean)
s1_dict = {int(i): int(v) for i, v in entries}
l4_dict = {int(i): int(v) for i, v in l4_entries}
diffs = sum(1 for k in set(s1_dict) | set(l4_dict)
            if s1_dict.get(k) != l4_dict.get(k))
chk('P1: Registry identical to L4 (byte-equivalent)',
    diffs == 0, f'{diffs} diffs')

# New labels
for lbl in ['LX_NM_Kill', 'LX_NM_RegistryEnd', 'LX_NM_Holiday']:
    chk(f'P1: new label {lbl}', lbl in s, '')

# Existing labels preserved
for lbl in ['LE_NM_Long', 'LX_NM_SL', 'LX_NM_TP', 'LX_NM_Trail', 'LX_NM_Time']:
    chk(f'Preserved label {lbl}', lbl in s, '')

# Entry gate has v_Holiday_Block
entry_match = re.search(
    r'if v_RangeReady.*?then begin', clean, re.DOTALL)
chk('P1: Entry gate has v_Holiday_Block = false',
    entry_match and 'v_Holiday_Block' in entry_match.group(0), '')

# Priority 0 exit chain
chk('P1: Kill exit before RegistryEnd before Holiday',
    bool(re.search(
        r'Manual_Kill_Switch.*?LX_NM_Kill.*?Registry_Expired.*?'
        r'LX_NM_RegistryEnd.*?Holiday_Block.*?LX_NM_Holiday',
        s, re.DOTALL)), '')

# 30-day warning
chk('P1: 30-day Text_New warning',
    'Text_New' in s and 'Registry_Warn_ID' in s, '')

# Variables
for v in ['v_Holiday_Block', 'v_Registry_Expired', 'Registry_Warn_ID', 'hidx']:
    chk(f'P1: variable {v} declared',
        bool(re.search(rf'\b{v}\s*\(', clean)), '')

# Syntax sanity
b = len(re.findall(r'\bbegin\b', clean, re.IGNORECASE))
e = len(re.findall(r'\bend\b', clean, re.IGNORECASE))
chk(f'Syntax: begin/end balance ({b}/{e})', b == e, '')

last_char = s.rstrip()[-1]
chk('Syntax: file ends cleanly',
    last_char in ';}', f"last char: {last_char}")

print()
passed = sum(1 for c in checks if c)
print(f'PASSED: {passed}/{len(checks)} ({100*passed/len(checks):.0f}%)')
if passed == len(checks):
    print('S1 v2.2 ready for MC9/MC12 deployment when flat')
else:
    print('Issues found - review above')
