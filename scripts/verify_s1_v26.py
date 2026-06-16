"""S1 v2.6 verification — Trend Filter on entry side (VolRatio / DailyMA / WeeklyMA)."""
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
    print(f'  [{"OK  " if ok else "FAIL"}] {name}{": " + detail if detail else ""}')
    checks.append(ok)

print('=' * 65)
print('S1 v2.6 — TREND FILTER VERIFICATION')
print('=' * 65)

# ─── v2.6 identity ───
chk('Version v2.6 in header', 'v2.6' in s)

# ─── v2.6 Trail_Mode default changed to 0 ───
m = re.search(r'Trail_Mode\s*\(\s*(\d+)\s*\)', clean)
chk('Trail_Mode default = 0 (was 2 in v2.5, Trail_B failed)',
    m and m.group(1) == '0', f'got {m.group(1) if m else "none"}')

# ─── v2.6 NEW INPUTS ───
m = re.search(r'TrendFilterMode\s*\(\s*(\d+)\s*\)', clean)
chk('NEW input TrendFilterMode = 0 (off = v2.4 baseline)',
    m and m.group(1) == '0', f'got {m.group(1) if m else "none"}')

m = re.search(r'TF_VolRatioMin\s*\(\s*([\d.]+)\s*\)', clean)
chk('NEW input TF_VolRatioMin = 1.00 (stricter than base 0.80)',
    m and float(m.group(1)) == 1.0, f'got {m.group(1) if m else "none"}')

m = re.search(r'TF_DailyMALen\s*\(\s*(\d+)\s*\)', clean)
chk('NEW input TF_DailyMALen = 20',
    m and m.group(1) == '20', f'got {m.group(1) if m else "none"}')

m = re.search(r'TF_WeeklyMALen\s*\(\s*(\d+)\s*\)', clean)
chk('NEW input TF_WeeklyMALen = 13 (Adaptive Farmer Layer 1)',
    m and m.group(1) == '13', f'got {m.group(1) if m else "none"}')

# ─── v2.6 NEW VARIABLES ───
for v in ['v_TrendPass', 'v_TF_VolOK', 'v_TF_DailyOK', 'v_TF_WeeklyOK',
          'v_DailyMA', 'v_WeeklyMA']:
    chk(f'NEW variable {v} declared',
        bool(re.search(rf'\b{v}\s*\(', clean)))

# ─── v2.6 TREND FILTER LOGIC ───
chk('Mode 0 sets TrendPass = true (v2.4 regression safe)',
    bool(re.search(r'if TrendFilterMode\s*=\s*0\s+then\s+v_TrendPass\s*=\s*true', clean)))

chk('Mode 1+ checks v_VolRatio >= TF_VolRatioMin',
    'v_VolRatio >= TF_VolRatioMin' in clean)

chk('Mode 2+ uses Average(Close of data2) for DailyMA',
    'Average(Close of data2, TF_DailyMALen)' in s)

chk('Mode 3 uses Average(Close of data3) for WeeklyMA',
    'Average(Close of data3, TF_WeeklyMALen)' in s)

chk('DailyMA uses [1] index (CLAUDE.md rule: data2 current bar unreliable)',
    'Average(Close of data2, TF_DailyMALen)[1]' in clean)

chk('WeeklyMA uses [1] index (data3 current bar unreliable)',
    'Average(Close of data3, TF_WeeklyMALen)[1]' in clean)

chk('Final gate: v_TrendPass = v_TF_VolOK and v_TF_DailyOK and v_TF_WeeklyOK',
    'v_TrendPass = v_TF_VolOK and v_TF_DailyOK and v_TF_WeeklyOK' in clean)

# ─── v2.6 ENTRY CHANGE ───
chk('v_TrendPass added to entry condition',
    bool(re.search(r'v_VolPass\s+and\s+v_TrendPass\s+and', clean)))

# ─── v2.6 EXIT LOGIC UNCHANGED (iron law #7) ───
exit_marker = s.index('Priority 0: Holiday Safety')
exit_section_raw = s[exit_marker:]
exit_section_clean = strip_comments(exit_section_raw)
chk('v_TrendPass NOT in exit logic (entry-only gate)',
    'v_TrendPass' not in exit_section_clean)

for lbl in ['LX_NM_SL', 'LX_NM_TP', 'LX_NM_Time',
            'LX_NM_Kill', 'LX_NM_RegistryEnd', 'LX_NM_Holiday']:
    chk(f'Exit label {lbl} preserved', lbl in clean)

# ─── v2.4 BASE PRESERVED ───
m = re.search(r'ExitTime\s*\(\s*(\d+)\s*\)', clean)
chk('ExitTime = 500 preserved (v2.4 gap capture)',
    m and m.group(1) == '500')

m = re.search(r'VolRatioMin\s*\(\s*([\d.]+)\s*\)', clean)
chk('Base VolRatioMin = 0.80 preserved (v2.4 base gate)',
    m and float(m.group(1)) == 0.80)

chk('Entry label LE_NM_Long preserved', 'LE_NM_Long' in clean)

# ─── v2.5 TRAIL preserved (just default changed) ───
chk('Trail label LX_NM_Trail_A preserved', 'LX_NM_Trail_A' in clean)
chk('Trail label LX_NM_Trail_B preserved', 'LX_NM_Trail_B' in clean)
chk('TrailActATR = 1.5 preserved',
    bool(re.search(r'TrailActATR\s*\(\s*1\.5\s*\)', clean)))
chk('Dead-config warning preserved', 'TRAIL DEAD' in clean)

# ─── v2.4 Holiday module preserved ───
entries = re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)
chk('63 Holiday registry entries preserved',
    len(entries) == 63, f'got {len(entries)}')

# ─── Syntax sanity ───
b = len(re.findall(r'\bbegin\b', clean, re.IGNORECASE))
e = len(re.findall(r'\bend\b', clean, re.IGNORECASE))
chk(f'begin/end balance ({b}/{e})', b == e)

last_char = s.rstrip()[-1]
chk('File ends cleanly', last_char in ';}')

print()
passed = sum(1 for c in checks if c)
total = len(checks)
print(f'PASSED: {passed}/{total} ({100*passed/total:.0f}%)')
if passed == total:
    print('S1 v2.6 ready — Trend Filter deployed')
    print('  TrendFilterMode=0: v2.4 baseline (regression check)')
    print('  TrendFilterMode=1: Stricter VolRatio >= 1.00')
    print('  TrendFilterMode=2: Mode 1 + Daily MA20 uptrend')
    print('  TrendFilterMode=3: Mode 2 + Weekly MA13 uptrend')
    print('  A/B: TrendFilterMode = Optimize(0, 0, 3, 1)')
else:
    print(f'*** {total - passed} CHECK(S) FAILED ***')
    sys.exit(1)
