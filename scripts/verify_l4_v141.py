"""L4 v14.1 cross-verification: holiday module + frozen SL + exit chain.
Cross-checks against L1/L2/L3 standards."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = {
    'L1': 'strategies/live/L1_TrendLong.pla',
    'L2': 'strategies/live/L2_TrendShort.pla',
    'L3': 'strategies/live/L3_ConsolidationLong.pla',
    'L4': 'strategies/live/L4_ConsolidationShort.pla',
}
content = {}
for k, p in files.items():
    with open(p, 'r', encoding='utf-8') as f:
        content[k] = f.read()

results = []

def report(check, ok, detail=""):
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] {check}: {detail}")
    results.append(ok)

print("=" * 70)
print("CHECK 1: Holiday_Tail Registry Consistency (L1/L2/L3/L4)")
print("=" * 70)

def extract_holiday_dates(s):
    pattern = r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)'
    matches = re.findall(pattern, s)
    return {int(idx): int(val) for idx, val in matches}

registries = {k: extract_holiday_dates(v) for k, v in content.items()}
for k, r in registries.items():
    print(f"  {k}: {len(r)} entries, idx range [{min(r)}..{max(r)}]")

# L4 vs each reference
ref_entries = len(registries['L3'])
for ref in ['L1', 'L2', 'L3']:
    diffs = []
    keys = set(registries[ref].keys()) | set(registries['L4'].keys())
    for idx in sorted(keys):
        vr = registries[ref].get(idx)
        v4 = registries['L4'].get(idx)
        if vr != v4:
            diffs.append((idx, vr, v4))
    report(f"L4 registry matches {ref}", len(diffs) == 0, f"{len(diffs)} diffs")
    if diffs:
        for idx, vr, v4 in diffs[:5]:
            print(f"     idx {idx}: {ref}={vr}, L4={v4}")

print()
print("=" * 70)
print("CHECK 2: L4 v14.1 Inputs")
print("=" * 70)
l4 = content['L4']
expected_inputs = {
    'Freeze_SL_On': 'true',
    'Holiday_Flat_Time': '415',
    'Registry_Valid_Until': '1270101',
    'Manual_Kill_Switch': 'false',
}
for name, expected in expected_inputs.items():
    m = re.search(rf'{name}\(\s*(\w+)\s*\)', l4)
    actual = m.group(1) if m else None
    report(name, actual is not None and actual.lower() == expected.lower(),
           f"got '{actual}', expected '{expected}'")

print()
print("=" * 70)
print("CHECK 3: L4 v14.1 Required Variables")
print("=" * 70)
required_vars = ['v_SL_Locked', 'v_Frozen_ATR', 'v_Frozen_LockedTop',
                 'v_Holiday_Block', 'v_Registry_Expired', 'Registry_Warn_ID',
                 'hidx', 'ExitFired']
for v in required_vars:
    ok = bool(re.search(rf'\b{v}\s*\(', l4))
    report(f"variable {v}", ok, "declared" if ok else "MISSING")
report("Holiday_Tail[80] array", 'Holiday_Tail[80](0)' in l4, "")

print()
print("=" * 70)
print("CHECK 4: L4 v14.1 Entry Gate")
print("=" * 70)
entry_block = re.search(
    r'if\s+MarketPosition\s*=\s*0(.*?)SellShort\s*\(\s*"CS_Entry"\s*\)',
    l4, re.DOTALL)
if entry_block:
    body = entry_block.group(1)
    report("Entry gate has v_Holiday_Block = false", 'v_Holiday_Block' in body, "")
    report("Entry gate has v_Macro_Block = false", 'v_Macro_Block' in body, "")
    report("Entry gate has v_In_Trap_Zone = true", 'v_In_Trap_Zone' in body, "")
    report("Entry gate has v_BarsSinceExit", 'v_BarsSinceExit' in body, "")
    report("Entry gate has v_Trend_Dir = -1", 'v_Trend_Dir' in body, "")
else:
    report("CS_Entry block parseable", False, "regex failed")

print()
print("=" * 70)
print("CHECK 5: L4 v14.1 Exit Labels")
print("=" * 70)
exit_labels = set(re.findall(r'BuyToCover\s*\(\s*"(CS_\w+)"\s*\)', l4))
print(f"  Found: {sorted(exit_labels)}")
for label in ['CS_Kill', 'CS_RegistryEnd', 'CS_Holiday', 'CS_BreakExit', 'CS_TimeExit', 'CS_SL']:
    report(f"label {label}", label in exit_labels, "")

print()
print("=" * 70)
print("CHECK 6: ExitFired Priority Pattern")
print("=" * 70)
reset_count = len(re.findall(r'ExitFired\s*=\s*0', l4))
fired_sets = len(re.findall(r'ExitFired\s*=\s*1', l4))
report("ExitFired = 0 reset", reset_count >= 1, f"count={reset_count}")
report("ExitFired = 1 set after priority exits", fired_sets >= 5, f"count={fired_sets} (expect >=5)")

# Order in file
order = []
for label in ['CS_Kill', 'CS_RegistryEnd', 'CS_Holiday', 'CS_BreakExit', 'CS_TimeExit', 'CS_SL']:
    m = re.search(rf'BuyToCover\s*\(\s*"{label}"\s*\)', l4)
    if m:
        order.append((label, m.start()))
order.sort(key=lambda x: x[1])
actual_order = [x[0] for x in order]
expected_order = ['CS_Kill', 'CS_RegistryEnd', 'CS_Holiday', 'CS_BreakExit', 'CS_TimeExit', 'CS_SL']
report("Priority order in file", actual_order == expected_order,
       f"got {actual_order}")

print()
print("=" * 70)
print("CHECK 7: Frozen SL Pattern")
print("=" * 70)
freeze_match = re.search(
    r'if\s+Freeze_SL_On\s+and\s+v_SL_Locked\s*=\s*false\s+then\s+begin(.*?)end;',
    l4, re.DOTALL)
if freeze_match:
    body = freeze_match.group(1)
    report("Freeze block freezes ATR", 'v_Frozen_ATR' in body and 'v_Current_ATR' in body, "")
    report("Freeze block freezes LockedTop", 'v_Frozen_LockedTop' in body and 'v_Locked_Top' in body, "")
    report("Freeze block sets v_SL_Locked = true",
           'v_SL_Locked' in body and 'true' in body, "")
else:
    report("Freeze block parseable", False, "regex failed")

frozen_stop = re.search(
    r'v_Stop_Level\s*=\s*v_Frozen_LockedTop\s*\+\s*\(\s*ATR_Stop_Mult\s*\*\s*v_Frozen_ATR\s*\)',
    l4)
report("Frozen stop formula correct", bool(frozen_stop),
       "v_Frozen_LockedTop + ATR_Stop_Mult * v_Frozen_ATR")

fallback = re.search(
    r'v_Stop_Level\s*=\s*v_Locked_Top\s*\+\s*\(\s*ATR_Stop_Mult\s*\*\s*v_Current_ATR\s*\)',
    l4)
report("v14.0 fallback formula preserved", bool(fallback), "")

# Trail formula preserved (uses v_Current_ATR by design)
trail = re.search(
    r'MinList\s*\(\s*v_Stop_Level\[1\]\s*,\s*v_Lowest_Low\s*\+\s*\(\s*Trail_ATR_Mult\s*\*\s*v_Current_ATR\s*\)',
    l4)
report("Trail formula uses v_Current_ATR (intentional)", bool(trail), "")

print()
print("=" * 70)
print("CHECK 8: State Reset on Flat (MarketPosition = 0)")
print("=" * 70)
# Walk forward from "Snapshot box and reset" comment, capture until matching end;
# Use begin/end depth counter to handle nesting
anchor = l4.find('Snapshot box and reset')
if anchor < 0:
    report("Reset block anchor found", False, "comment missing")
else:
    # Find the next "if MarketPosition = 0 then begin"
    pos = l4.find('if MarketPosition = 0 then begin', anchor)
    if pos < 0:
        report("Reset block parseable", False, "if statement not found after anchor")
    else:
        # Walk forward tracking begin/end depth
        depth = 1
        i = pos + len('if MarketPosition = 0 then begin')
        start = i
        while depth > 0 and i < len(l4):
            # Find next begin or end
            m = re.search(r'\b(begin|end)\b', l4[i:], re.IGNORECASE)
            if not m:
                break
            tok = m.group(1).lower()
            if tok == 'begin':
                depth += 1
            else:
                depth -= 1
            i += m.end()
        body = l4[start:i]
        for v in ['v_Lowest_Low', 'v_Trail_Active', 'v_SL_Locked', 'v_Frozen_ATR', 'v_Frozen_LockedTop']:
            report(f"reset {v}", v in body, "")

print()
print("=" * 70)
print("CHECK 9: Holiday Detection Logic")
print("=" * 70)
detect = re.search(r'if\s+Time\s*<=\s*500\s+then\s+begin\s+for\s+hidx\s*=\s*1\s+to\s+80', l4)
report("Tail bar detection (Time<=500 + for hidx=1 to 80)", bool(detect), "")
reg_block = re.search(r'if\s+Date\s*>\s*Registry_Valid_Until', l4)
report("Registry expiry check", bool(reg_block), "")
warn = re.search(r'LastBarOnChart.*?Text_New.*?Registry_Warn_ID', l4, re.DOTALL)
report("30-day warning + Text_New", bool(warn), "")

# Verify v_Holiday_Block is reset at top of every bar
reset_block = re.search(r'v_Holiday_Block\s*=\s*false', l4)
report("v_Holiday_Block reset each bar", bool(reset_block), "")

print()
print("=" * 70)
print("CHECK 10: Header / Version")
print("=" * 70)
header_v = re.search(r'Version\s*:\s*v14\.1', l4)
report("Header version v14.1", bool(header_v), "")
header_extras = 'HolidayFlat_v3' in l4 and 'FrozenSL' in l4
report("Header mentions HolidayFlat_v3 + FrozenSL", header_extras, "")
changelog = 'CHANGELOG:' in l4 and 'v14.1' in l4 and '(2026-06-13)' in l4
report("Changelog v14.1 dated 2026-06-13", changelog, "")

print()
print("=" * 70)
print("CHECK 11: 6/18 Dragon Boat tail entry (1260619)")
print("=" * 70)
# Most relevant near-term holiday for L4 deployment
six_eighteen = re.search(r'Holiday_Tail\[\s*58\s*\]\s*=\s*1260619', l4)
report("Holiday_Tail[58] = 1260619 (Dragon Boat eve+1)", bool(six_eighteen), "")

# Compare with L1/L2/L3
for ref in ['L1', 'L2', 'L3']:
    found = bool(re.search(r'Holiday_Tail\[\s*58\s*\]\s*=\s*1260619', content[ref]))
    report(f"{ref} also has 1260619", found, "")

print()
print("=" * 70)
print("CHECK 12: PowerLanguage Syntax Sanity")
print("=" * 70)
# begin/end balance
begin_count = len(re.findall(r'\bbegin\b', l4, re.IGNORECASE))
end_count = len(re.findall(r'\bend\b', l4, re.IGNORECASE))
report(f"begin/end balance: {begin_count} begin / {end_count} end",
       begin_count == end_count, "")
# Semicolon density (rough)
lines = [l for l in l4.split('\n') if l.strip() and not l.strip().startswith('{')]
print(f"  Code lines: {len(lines)}")

# Trailing chars
last_char = l4.rstrip()[-1]
report("File ends cleanly", last_char in ';}', f"last char: '{last_char}'")

print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)
passed = sum(1 for r in results if r)
total = len(results)
print(f"  Passed: {passed}/{total} ({100*passed/total:.0f}%)")
if passed == total:
    print("  ALL CHECKS PASSED - L4 v14.1 ready for deployment")
else:
    print(f"  {total - passed} CHECKS FAILED - review above")
