"""S1 v2.5 verification — Trail A/B engine (fix dead Trail + true ratcheting trail)."""
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
print('S1 v2.5 — TRAIL A/B ENGINE VERIFICATION')
print('=' * 65)

# Version
chk('Version v2.5 in header', 'v2.5' in s, '')

# v2.4 base preserved
m = re.search(r'ExitTime\s*\(\s*(\d+)\s*\)', clean)
chk('ExitTime = 500 preserved (v2.4 gap capture)',
    m and m.group(1) == '500', '')

# v2.5 Trail parameter CHANGES
m = re.search(r'TrailActATR\s*\(\s*([\d.]+)\s*\)', clean)
chk('TrailActATR = 1.5 (lowered from 2.75)',
    m and float(m.group(1)) == 1.5, f'got {m.group(1) if m else "none"}')

m = re.search(r'TrailOffATR\s*\(\s*([\d.]+)\s*\)', clean)
chk('TrailOffATR = 0.7 (unchanged)',
    m and float(m.group(1)) == 0.7, '')

# Trail < Target check
m_act = re.search(r'TrailActATR\s*\(\s*([\d.]+)\s*\)', clean)
m_tgt = re.search(r'TargetATRMult\s*\(\s*([\d.]+)\s*\)', clean)
if m_act and m_tgt:
    chk('TrailActATR < TargetATRMult (Trail CAN activate)',
        float(m_act.group(1)) < float(m_tgt.group(1)),
        f'{m_act.group(1)} < {m_tgt.group(1)}')

# v2.5 NEW input Trail_Mode
m = re.search(r'Trail_Mode\s*\(\s*(\d+)\s*\)', clean)
chk('NEW input Trail_Mode = 2 (default = Variant B true trail)',
    m and m.group(1) == '2', f'got {m.group(1) if m else "none"}')

# v2.5 NEW variables
for v in ['v_HighestClose', 'v_TrailArmed', 'Trail_Warn_ID']:
    chk(f'NEW variable {v} declared',
        bool(re.search(rf'\b{v}\s*\(', clean)), '')

# v2.5 NEW labels
chk('NEW label LX_NM_Trail_A emitted',
    'LX_NM_Trail_A' in clean, '')
chk('NEW label LX_NM_Trail_B emitted',
    'LX_NM_Trail_B' in clean, '')

# Old dead Trail label REMOVED (no more bare LX_NM_Trail)
# Only LX_NM_Trail_A and LX_NM_Trail_B should exist
old_trail_count = len(re.findall(r'"LX_NM_Trail"', clean))
chk('Old dead LX_NM_Trail label REMOVED',
    old_trail_count == 0, f'found {old_trail_count} bare references')

# HighestClose tracking logic
chk('HighestClose tracking active during position',
    'if Close > v_HighestClose then' in clean, '')

# Trail arming logic
chk('Trail armed by MaxContractProfit threshold',
    'MaxContractProfit / 200 >= v_EntryATR * TrailActATR' in clean, '')

# Mutually exclusive A/B emission
chk('Trail_Mode = 1 emits Trail_A (fixed lock)',
    bool(re.search(r'Trail_Mode = 1 then.*?LX_NM_Trail_A', clean, re.DOTALL)), '')

chk('Trail_Mode = 2 emits Trail_B (true ratcheting)',
    bool(re.search(r'Trail_Mode = 2 then.*?LX_NM_Trail_B', clean, re.DOTALL)), '')

# Variant B uses HighestClose
chk('Variant B uses v_HighestClose for trail stop',
    'v_HighestClose - v_EntryATR * TrailOffATR' in clean, '')

# Variant A uses EntryPrice (fixed)
chk('Variant A uses EntryPrice for fixed lock',
    'EntryPrice + v_EntryATR * (TrailActATR - TrailOffATR)' in clean, '')

# Dead-config warning
chk('Dead-config warning text present',
    'TRAIL DEAD' in clean, '')

# State reset on flat
chk('State reset: v_HighestClose = 0 on flat',
    bool(re.search(
        r'if MarketPosition\s*=\s*0\s+then begin.*?v_HighestClose\s*=\s*0',
        clean, re.DOTALL)), '')

chk('State reset: v_TrailArmed = false on flat',
    bool(re.search(
        r'if MarketPosition\s*=\s*0\s+then begin.*?v_TrailArmed\s*=\s*false',
        clean, re.DOTALL)), '')

# v2.4 holiday module preserved
for name in ['Holiday_Flat_Time', 'Registry_Valid_Until', 'Manual_Kill_Switch']:
    chk(f'v2.4 input {name} preserved',
        bool(re.search(rf'\b{name}\s*\(', clean)), '')

# v2.1 labels preserved
for lbl in ['LE_NM_Long', 'LX_NM_SL', 'LX_NM_TP', 'LX_NM_Time',
            'LX_NM_Kill', 'LX_NM_RegistryEnd', 'LX_NM_Holiday']:
    chk(f'Preserved label {lbl}', lbl in s, '')

# 63 holiday entries
entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)
chk('63 Holiday registry entries preserved',
    len(entries) == 63, f'got {len(entries)}')

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
    print('S1 v2.5 ready - Trail A/B engine deployed')
    print('  Trail_Mode=0: v2.4 behavior (regression check)')
    print('  Trail_Mode=1: Variant A fixed lock (resurrected dead trail)')
    print('  Trail_Mode=2: Variant B true ratcheting trail (DEFAULT, recommended)')
