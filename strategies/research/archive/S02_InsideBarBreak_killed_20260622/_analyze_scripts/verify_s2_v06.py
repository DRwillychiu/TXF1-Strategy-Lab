"""Verify S2_InsideBarBreak v0.6 changes.

Checks:
  1. Version header says v0.6
  2. Input defaults: VolFilter_On(false), ConfirmBars(1),
     Compression_On(false), BB_Filter_On(false), ATR_Filter_On(false)
  3. MaxDailyEntries(1) input exists
  4. v_DailyEntryCount and v_LastEntryDate variables declared
  5. Daily count reset block present
  6. Long Stage 1 has daily limit check + counter
  7. Long Stage 2 has daily limit check + counter
  8. Short Stage 1 has daily limit check + counter
  9. Short Stage 2 has daily limit check + counter
  10. TargetMult(1.0) preserved from v0.5
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA = 'strategies/research/S02_InsideBarBreak/S2_InsideBarBreak.pla'

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
    print(f'  [{"OK  " if ok else "FAIL"}] {name}{": " + detail if detail else ""}')
    results.append(ok)

with open(PLA, 'r', encoding='utf-8') as f:
    raw = f.read()
clean = strip_comments(raw)

print(f'=== S2 InsideBarBreak v0.6 Verification ({PLA}) ===')
print(f'    File length: {len(raw)} chars, {raw.count(chr(10))+1} lines')
print()

# --- 1. Version header ---
chk('V-1: Version header says v0.6',
    bool(re.search(r'Version\s*:\s*v0\.6', raw)),
    'checking raw (with comments)')

# --- 2. Input defaults (B-series fix) ---
m = re.search(r'VolFilter_On\s*\(\s*(true|false)\s*\)', clean, re.IGNORECASE)
chk('V-2a: VolFilter_On default = false (B-3 fix)',
    m and m.group(1).lower() == 'false',
    f'got {m.group(1) if m else "missing"}')

m = re.search(r'ConfirmBars\s*\(\s*(\d+)\s*\)', clean)
chk('V-2b: ConfirmBars default = 1 (B-2 fix)',
    m and m.group(1) == '1',
    f'got {m.group(1) if m else "missing"}')

# --- 3. A-series defaults off ---
m = re.search(r'Compression_On\s*\(\s*(true|false)\s*\)', clean, re.IGNORECASE)
chk('V-3a: Compression_On default = false (A-1 reset)',
    m and m.group(1).lower() == 'false',
    f'got {m.group(1) if m else "missing"}')

m = re.search(r'BB_Filter_On\s*\(\s*(true|false)\s*\)', clean, re.IGNORECASE)
chk('V-3b: BB_Filter_On default = false (A-2 reset)',
    m and m.group(1).lower() == 'false',
    f'got {m.group(1) if m else "missing"}')

m = re.search(r'ATR_Filter_On\s*\(\s*(true|false)\s*\)', clean, re.IGNORECASE)
chk('V-3c: ATR_Filter_On default = false (A-3 reset)',
    m and m.group(1).lower() == 'false',
    f'got {m.group(1) if m else "missing"}')

# --- 4. MaxDailyEntries input ---
m = re.search(r'MaxDailyEntries\s*\(\s*(\d+)\s*\)', clean)
chk('V-4: MaxDailyEntries(1) input exists',
    m and m.group(1) == '1',
    f'got {m.group(1) if m else "missing"}')

# --- 5. TargetMult preserved from v0.5 ---
m = re.search(r'TargetMult\s*\(\s*([\d.]+)\s*\)', clean)
chk('V-5: TargetMult(1.0) preserved from v0.5',
    m and float(m.group(1)) == 1.0,
    f'got {m.group(1) if m else "missing"}')

# --- 6. v_DailyEntryCount and v_LastEntryDate variables ---
chk('V-6a: v_DailyEntryCount variable declared',
    bool(re.search(r'\bv_DailyEntryCount\s*\(', clean)), '')

chk('V-6b: v_LastEntryDate variable declared',
    bool(re.search(r'\bv_LastEntryDate\s*\(', clean)), '')

# --- 7. Daily count reset block ---
chk('V-7: Daily count reset (Date <> v_LastEntryDate)',
    bool(re.search(r'Date\s*<>\s*v_LastEntryDate', clean)), '')

# --- 8-11: Use raw text (comments have block labels) to find sections ---
def get_block(text, start_marker, end_marker):
    s = text.find(start_marker)
    if s < 0:
        return None
    e = text.find(end_marker, s + len(start_marker))
    if e < 0:
        e = len(text)
    return strip_comments(text[s:e])

long_s1 = get_block(raw, 'Long: stage 1', 'Long: stage 2')
if long_s1:
    chk('V-8a: Long S1 has daily limit check',
        'v_DailyEntryCount < MaxDailyEntries' in long_s1, '')
    chk('V-8b: Long S1 has counter increment',
        'v_DailyEntryCount = v_DailyEntryCount + 1' in long_s1, '')
else:
    chk('V-8a: Long S1 block found', False, 'block not found')
    chk('V-8b: Long S1 counter', False, 'block not found')

long_s2 = get_block(raw, 'Long: stage 2', 'Short: stage 1')
if long_s2:
    chk('V-9a: Long S2 has daily limit check',
        'v_DailyEntryCount < MaxDailyEntries' in long_s2, '')
    chk('V-9b: Long S2 has counter increment',
        'v_DailyEntryCount = v_DailyEntryCount + 1' in long_s2, '')
else:
    chk('V-9a: Long S2 block found', False, 'block not found')
    chk('V-9b: Long S2 counter', False, 'block not found')

short_s1 = get_block(raw, 'Short: stage 1', 'Short: stage 2')
if short_s1:
    chk('V-10a: Short S1 has daily limit check',
        'v_DailyEntryCount < MaxDailyEntries' in short_s1, '')
    chk('V-10b: Short S1 has counter increment',
        'v_DailyEntryCount = v_DailyEntryCount + 1' in short_s1, '')
else:
    chk('V-10a: Short S1 block found', False, 'block not found')
    chk('V-10b: Short S1 counter', False, 'block not found')

short_s2 = get_block(raw, 'Short: stage 2', 'EXIT LOGIC')
if short_s2 is None:
    short_s2 = get_block(raw, 'Short: stage 2', 'v_Prev_MP = MarketPosition')
if short_s2:
    chk('V-11a: Short S2 has daily limit check',
        'v_DailyEntryCount < MaxDailyEntries' in short_s2, '')
    chk('V-11b: Short S2 has counter increment',
        'v_DailyEntryCount = v_DailyEntryCount + 1' in short_s2, '')
else:
    chk('V-11a: Short S2 block found', False, 'block not found')
    chk('V-11b: Short S2 counter', False, 'block not found')

# --- 12. Long_Only_Mode preserved from v0.5 ---
m = re.search(r'Long_Only_Mode\s*\(\s*(true|false)\s*\)', clean, re.IGNORECASE)
chk('V-12: Long_Only_Mode(true) preserved from v0.5',
    m and m.group(1).lower() == 'true',
    f'got {m.group(1) if m else "missing"}')

# --- 13. Settlement_Flat module still intact ---
chk('V-13a: Settlement_Flat_Time(1230) input',
    bool(re.search(r'Settlement_Flat_Time\s*\(\s*1230\s*\)', clean)), '')
chk('V-13b: v_Settlement_Day variable',
    bool(re.search(r'\bv_Settlement_Day\b', clean)), '')
chk('V-13c: IB_Settlement label',
    bool(re.search(r'IB_Settlement', raw)), '')

# Summary
print()
passed = sum(results)
total = len(results)
print(f'=== RESULT: {passed}/{total} {"ALL PASS" if passed == total else "FAILURES DETECTED"} ===')
sys.exit(0 if passed == total else 1)
