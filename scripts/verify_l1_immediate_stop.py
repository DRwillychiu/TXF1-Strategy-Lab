"""Verify L1_TrendLong P3b Immediate Stop Guard implementation.

Checks:
  1. Version string includes ImmediateStop
  2. Changelog has V2.6+ P3b entry
  3. Header STRATEGY LOGIC has P3b Guard line
  4. SetStopLoss call exists with correct formula
     (V2.9: MinList of distances = the TIGHTER leg, mirroring P3
      which takes MaxList of PRICES. The pre-V2.9 verifier asserted
      MaxList of distances -- it encoded the bug as the standard.
      Lesson: assert SEMANTICS (which leg), not formula shape.)
  5. SetStopLoss guarded by MP <= 0 (freeze when in position)
  6. SetStopLoss placed BEFORE entry block (MP = 0)
  7. SetStopLoss uses same variables as P3 Frozen SL
  8. BigPointValue used (MC reserved word for TXF1 = 200)
  9. Existing Frozen SL (v_SL_Locked) still intact
  10. Settlement_Flat module still intact
  13. SetStopContract declared (per-contract basis, lot-count invariant)
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA = 'strategies/live/L1_TrendLong.pla'

results = []
def chk(name, ok, detail=''):
    print(f'  [{"OK  " if ok else "FAIL"}] {name}{": " + detail if detail else ""}')
    results.append(ok)

with open(PLA, 'r', encoding='utf-8') as f:
    raw = f.read()
lines = raw.split('\n')

print(f'=== L1 TrendLong P3b Immediate Stop Guard Verification ===')
print(f'    File: {PLA}')
print(f'    Lines: {len(lines)}')
print()

# --- 1. Version string ---
chk('V-1: Version includes ImmediateStop',
    bool(re.search(r'Version\s*:\s*.*ImmediateStop', raw)),
    'checking header')

# --- 2. Changelog ---
chk('V-2: Changelog has V2.6+ P3b entry',
    bool(re.search(r'V2\.6\+.*P3b\s+Immediate\s+Stop', raw)),
    'checking changelog')

# --- 3. Strategy logic header ---
chk('V-3: Header has P3b Guard line',
    bool(re.search(r'P3b\s+Guard\s*:.*SetStopLoss', raw)),
    'checking strategy logic block')

# --- 4. SetStopLoss call exists with correct formula (V2.9: MinList) ---
ssl_match = re.search(
    r'SetStopLoss\s*\(\s*MinList\s*\(\s*Current_ATR\s*\*\s*SL_Multiplier\s*,'
    r'\s*Daily_ATR\s*\*\s*Daily_Cap_Multiplier\s*\)\s*\*\s*BigPointValue\s*\)',
    raw)
chk('V-4: SetStopLoss = MinList(ATR*SL, DATR*Cap)*BPV (TIGHTER leg, mirrors P3)',
    bool(ssl_match),
    'exact formula match')
# V-4b: the buggy MaxList form must be GONE from executable code
chk('V-4b: no MaxList inside SetStopLoss (pre-V2.9 bug absent)',
    not re.search(r'SetStopLoss\s*\(\s*MaxList', raw),
    'looser-leg form eliminated')

# --- 5. Guarded by MP <= 0 ---
mp_guard = re.search(r'if\s+MP\s*<=\s*0\s+then\s*\n\s*SetStopLoss', raw)
chk('V-5: SetStopLoss guarded by MP <= 0',
    bool(mp_guard),
    'freeze mechanism')

# --- 6. Placement: SetStopLoss BEFORE entry block ---
ssl_line = None
entry_line = None
for i, line in enumerate(lines):
    if 'SetStopLoss' in line and 'MinList' in line:
        ssl_line = i
    # semantic anchor: the actual entry order statement (the old literal
    # 'if MP = 0 then begin' never matched the multi-line entry gate)
    if 'Buy ("TL_Entry")' in line and entry_line is None:
        entry_line = i
chk('V-6: SetStopLoss placed before entry block',
    ssl_line is not None and entry_line is not None and ssl_line < entry_line,
    f'SetStopLoss at line {ssl_line+1 if ssl_line else "?"}, entry at line {entry_line+1 if entry_line else "?"}')

# --- 7. Uses same variables as P3 Frozen SL ---
frozen_sl_block = re.search(
    r'Exit_Price_ATR\s*=\s*Entry_P\s*-\s*\(\s*Current_ATR\s*\*\s*SL_Multiplier\s*\)',
    raw)
frozen_sl_cap = re.search(
    r'Exit_Price_Cap\s*=\s*Entry_P\s*-\s*\(\s*Daily_ATR\s*\*\s*Daily_Cap_Multiplier\s*\)',
    raw)
chk('V-7a: P3 Frozen SL uses Current_ATR * SL_Multiplier',
    bool(frozen_sl_block), '')
chk('V-7b: P3 Frozen SL uses Daily_ATR * Daily_Cap_Multiplier',
    bool(frozen_sl_cap), '')

# --- 8. BigPointValue present ---
chk('V-8: BigPointValue used in SetStopLoss call',
    'BigPointValue' in raw and bool(ssl_match),
    'MC reserved word for TXF1 = 200 NTD/pt')

# --- 9. Existing Frozen SL still intact ---
chk('V-9a: v_SL_Locked variable still present',
    'v_SL_Locked' in raw, '')
chk('V-9b: Frozen SL if-guard still present',
    bool(re.search(r'if\s+v_SL_Locked\s*=\s*False\s+then', raw)), '')
chk('V-9c: v_SL_Locked = True assignment still present',
    bool(re.search(r'v_SL_Locked\s*=\s*True', raw)), '')

# --- 10. Settlement_Flat still intact ---
chk('V-10a: Settlement_Flat_Time input present',
    bool(re.search(r'Settlement_Flat_Time', raw)), '')
chk('V-10b: v_Settlement_Day variable present',
    bool(re.search(r'v_Settlement_Day', raw)), '')
chk('V-10c: TL_Settlement exit label present',
    bool(re.search(r'TL_Settlement', raw)), '')

# --- 11. No duplicate SetStopLoss calls (outside comments) ---
def strip_comments(s):
    out = []; depth = 0
    for c in s:
        if c == '{': depth += 1; continue
        if c == '}':
            if depth > 0: depth -= 1
            continue
        if depth == 0: out.append(c)
    return ''.join(out)
clean = strip_comments(raw)
ssl_count = len(re.findall(r'SetStopLoss\s*\(', clean))
chk('V-11: Exactly 1 SetStopLoss call (outside comments)',
    ssl_count == 1,
    f'found {ssl_count}')

# --- 12. IOG=false still present (confirms the need for P3b) ---
chk('V-12: IntrabarOrderGeneration = false confirmed',
    bool(re.search(r'IntrabarOrderGeneration\s*=\s*false', raw, re.IGNORECASE)),
    'IOG=false = entry bar unprotected without SetStopLoss')

# --- 13. SetStopContract declared (V2.9: lot-count invariance) ---
chk('V-13: SetStopContract declared before SetStopLoss',
    bool(re.search(r'SetStopContract\s*;[\s\S]*?SetStopLoss\s*\(', clean)),
    'per-contract basis; per-position default halves distance at 2 lots')

# Summary
print()
passed = sum(results)
total = len(results)
print(f'=== RESULT: {passed}/{total} {"ALL PASS" if passed == total else "FAILURES DETECTED"} ===')
sys.exit(0 if passed == total else 1)
