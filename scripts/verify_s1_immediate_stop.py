"""Verify S1_NightMomentum P3b Immediate Stop Guard implementation.

Checks:
  1. Version string includes ImmediateStop
  2. Changelog has P3b entry
  3. SetStopLoss call exists with correct formula
  4. SetStopLoss guarded by MarketPosition <= 0
  5. SetStopLoss placed BEFORE entry block
  6. Uses same variables as existing SL (v_ATR, StopATRMult)
  7. BigPointValue used
  8. Existing v_EntryATR freeze still intact
  9. Settlement_Flat module still intact
  10. Exactly 1 SetStopLoss call (outside comments)
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA = 'strategies/live_simulation/S1_NightMomentum.pla'

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

print(f'=== S1 NightMomentum P3b Immediate Stop Guard Verification ===')
print(f'    File: {PLA}')
print(f'    Lines: {len(lines)}')
print()

# --- 1. Version string ---
chk('V-1: Version includes ImmediateStop',
    bool(re.search(r'ImmediateStop', raw)),
    'checking header line 2')

# --- 2. Changelog ---
chk('V-2: Changelog has P3b entry',
    bool(re.search(r'v2\.6\+\s+P3b\s+CHANGELOG', raw)),
    'checking changelog block')

# --- 3. SetStopLoss call with correct formula ---
ssl_match = re.search(
    r'SetStopLoss\s*\(\s*v_ATR\s*\*\s*StopATRMult\s*\*\s*BigPointValue\s*\)',
    clean)
chk('V-3: SetStopLoss formula = v_ATR * StopATRMult * BigPointValue',
    bool(ssl_match),
    'exact formula match')

# --- 4. Guarded by MarketPosition <= 0 ---
mp_guard = re.search(r'if\s+MarketPosition\s*<=\s*0\s+then\s*\n\s*SetStopLoss', raw)
chk('V-4: SetStopLoss guarded by MarketPosition <= 0',
    bool(mp_guard),
    'freeze mechanism')

# --- 5. Placement: SetStopLoss BEFORE entry block ---
ssl_line = None
entry_line = None
for i, line in enumerate(lines):
    if 'SetStopLoss' in line and 'v_ATR' in line and ssl_line is None:
        ssl_line = i
    if 'LE_NM_Long' in line and entry_line is None:
        entry_line = i
chk('V-5: SetStopLoss placed before entry block',
    ssl_line is not None and entry_line is not None and ssl_line < entry_line,
    f'SetStopLoss at line {ssl_line+1 if ssl_line else "?"}, entry at line {entry_line+1 if entry_line else "?"}')

# --- 6. Uses same variables as existing SL ---
existing_sl = re.search(r'EntryPrice\s*-\s*v_EntryATR\s*\*\s*StopATRMult', clean)
chk('V-6: Existing SL uses v_EntryATR * StopATRMult',
    bool(existing_sl),
    'confirms SetStopLoss uses same multiplier')

# --- 7. BigPointValue ---
chk('V-7: BigPointValue in SetStopLoss call',
    'BigPointValue' in clean and bool(ssl_match),
    'MC reserved word for TXF1 = 200 NTD/pt')

# --- 8. v_EntryATR freeze still intact ---
chk('V-8a: v_EntryATR freeze at entry still present',
    bool(re.search(r'v_EntryATR\s*=\s*v_ATR', clean)), '')
chk('V-8b: Freeze guard (MarketPosition = 1 and v_Prev_MP <= 0)',
    bool(re.search(r'MarketPosition\s*=\s*1\s+and\s+v_Prev_MP\s*<=\s*0', clean)), '')

# --- 9. Settlement_Flat still intact ---
chk('V-9a: Settlement_Flat_Time input present',
    bool(re.search(r'Settlement_Flat_Time', raw)), '')
chk('V-9b: v_Settlement_Day variable present',
    bool(re.search(r'v_Settlement_Day', raw)), '')
chk('V-9c: LX_NM_Settlement exit label present',
    bool(re.search(r'LX_NM_Settlement', raw)), '')

# --- 10. Exactly 1 SetStopLoss call (outside comments) ---
ssl_count = len(re.findall(r'SetStopLoss\s*\(', clean))
chk('V-10: Exactly 1 SetStopLoss call (outside comments)',
    ssl_count == 1,
    f'found {ssl_count}')

# --- 11. Holiday module still intact ---
chk('V-11: Holiday_Flat_Time input present',
    bool(re.search(r'Holiday_Flat_Time', raw)), '')
chk('V-12: LX_NM_Holiday exit label present',
    bool(re.search(r'LX_NM_Holiday', raw)), '')

# Summary
print()
passed = sum(results)
total = len(results)
print(f'=== RESULT: {passed}/{total} {"ALL PASS" if passed == total else "FAILURES DETECTED"} ===')
sys.exit(0 if passed == total else 1)
