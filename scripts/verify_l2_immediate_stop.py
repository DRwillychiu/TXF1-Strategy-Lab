"""Verify L2_TrendShort P3b Immediate Stop Guard implementation.

Checks:
  1. Version string includes ImmediateStop
  2. Changelog has P3b entry
  3. SetStopLoss call with correct formula (AbsValue anchor-based)
  4. SetStopLoss guarded by MarketPosition >= 0 (short strategy)
  5. SetStopLoss placed BEFORE entry order
  6. Uses same variables as Section 8 SL (DC_Lower, ATR_Val, SL_ATR_Ratio)
  7. BigPointValue used
  8. Existing SL_Locked freeze still intact
  9. Settlement_Flat module still intact
  10. Exactly 1 SetStopLoss call (outside comments)
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA = 'strategies/live/L2_TrendShort.pla'

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

with open(PLA, 'r', encoding='utf-8') as f:
    raw = f.read()
clean = strip_comments(raw)
lines = raw.split('\n')

print(f'=== L2 TrendShort P3b Immediate Stop Guard Verification ===')
print(f'    File: {PLA}')
print(f'    Lines: {len(lines)}')
print()

# --- 1. Version string ---
chk('V-1: Version includes ImmediateStop',
    bool(re.search(r'Version\s*:\s*.*ImmediateStop', raw)),
    'checking header')

# --- 2. Changelog ---
chk('V-2: Changelog has 5.2+ P3b entry',
    bool(re.search(r'5\.2\+.*P3b\s+Immediate\s+Stop', raw)),
    'checking changelog')

# --- 3. SetStopLoss formula (anchor-based for short) ---
ssl_match = re.search(
    r'SetStopLoss\s*\(\s*AbsValue\s*\(\s*\(\s*DC_Lower\s*\+\s*ATR_Val\s*\*\s*SL_ATR_Ratio\s*\)\s*-\s*Close\s*\)\s*'
    r'\*\s*BigPointValue\s*\)',
    clean, re.DOTALL)
chk('V-3: SetStopLoss formula = AbsValue((DC_Lower+ATR*Ratio)-Close)*BPV',
    bool(ssl_match),
    'anchor-based formula for short')

# --- 4. Guarded by MarketPosition >= 0 (short strategy) ---
mp_guard = re.search(r'If\s+MarketPosition\s*>=\s*0\s+Then\s*\n\s*SetStopLoss', raw, re.IGNORECASE)
chk('V-4: SetStopLoss guarded by MarketPosition >= 0',
    bool(mp_guard),
    'freeze when short position opens')

# --- 5. Placement before entry ---
ssl_line = None
entry_line = None
for i, line in enumerate(lines):
    if 'SetStopLoss' in line and 'AbsValue' in line and ssl_line is None:
        ssl_line = i
    if 'TS_Entry' in line and entry_line is None:
        entry_line = i
chk('V-5: SetStopLoss placed before entry order',
    ssl_line is not None and entry_line is not None and ssl_line < entry_line,
    f'SetStopLoss at line {ssl_line+1 if ssl_line else "?"}, entry at line {entry_line+1 if entry_line else "?"}')

# --- 6. Same variables as Section 8 SL ---
sec8_sl = re.search(r'SL_Trig\s*=\s*SL_Line\s*\+\s*\(\s*ATR_Val\s*\*\s*SL_ATR_Ratio\s*\)', clean)
chk('V-6a: Section 8 SL uses ATR_Val * SL_ATR_Ratio',
    bool(sec8_sl), '')
sec8_anchor = re.search(r'SL_Line\s*=\s*DC_Lower', clean)
chk('V-6b: Section 8 anchors SL_Line to DC_Lower',
    bool(sec8_anchor), '')

# --- 7. BigPointValue ---
chk('V-7: BigPointValue in SetStopLoss',
    'BigPointValue' in clean and bool(ssl_match),
    'MC reserved word = 200 NTD/pt')

# --- 8. SL_Locked freeze still intact ---
chk('V-8a: SL_Locked variable still present',
    'SL_Locked' in clean, '')
chk('V-8b: SL_Locked = True assignment present',
    bool(re.search(r'SL_Locked\s*=\s*True', clean, re.IGNORECASE)), '')
chk('V-8c: SL_Locked = False reset present',
    bool(re.search(r'SL_Locked\s*=\s*False', clean, re.IGNORECASE)), '')

# --- 9. Settlement_Flat still intact ---
chk('V-9a: Settlement_Flat_Time input present',
    bool(re.search(r'Settlement_Flat_Time', raw)), '')
chk('V-9b: v_Settlement_Day variable present',
    bool(re.search(r'v_Settlement_Day', raw)), '')
chk('V-9c: TS_Settlement exit label present',
    bool(re.search(r'TS_Settlement', raw)), '')

# --- 10. Exactly 1 SetStopLoss call ---
ssl_count = len(re.findall(r'SetStopLoss\s*\(', clean))
chk('V-10: Exactly 1 SetStopLoss call (outside comments)',
    ssl_count == 1,
    f'found {ssl_count}')

# Summary
print()
passed = sum(results)
total = len(results)
print(f'=== RESULT: {passed}/{total} {"ALL PASS" if passed == total else "FAILURES DETECTED"} ===')
sys.exit(0 if passed == total else 1)
