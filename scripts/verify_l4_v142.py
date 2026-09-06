"""L4 v14.2 cross-verification: A/B engine for Path A + Path B variants.

Builds on verify_l4_v141_precision.py. Confirms v14.2 doesn't break
any v14.1 invariants and adds new A/B variant infrastructure correctly.
"""
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

l4 = content['L4']
results = []

def report(check, ok, detail=""):
    mark = "OK  " if ok else "FAIL"
    print(f"  [{mark}] {check}: {detail}")
    results.append(ok)

def strip_pl_comments(s):
    return re.sub(r'\{[^}]*?\}', '', s, flags=re.DOTALL)

# ============================================================
print("=" * 72)
print("LAYER REG: v14.1 invariants preserved")
print("=" * 72)

# Header
report("REG1: Version v14.2",
       bool(re.search(r'Version\s*:\s*v14\.2', l4)), "")
report("REG2: Holiday registry preserved (63 entries)",
       len(re.findall(r'Holiday_Tail\[\s*\d+\s*\]\s*=\s*\d+', l4)) == 63, "")
report("REG3: Freeze_SL_On(true) preserved",
       bool(re.search(r'Freeze_SL_On\s*\(\s*true\s*\)', l4)), "")
report("REG4: Holiday_Flat_Time(415) preserved",
       bool(re.search(r'Holiday_Flat_Time\s*\(\s*415\s*\)', l4)), "")
report("REG5: Registry_Valid_Until(1270101) preserved",
       bool(re.search(r'Registry_Valid_Until\s*\(\s*1270101\s*\)', l4)), "")

# All v14.1 exit labels still present
for label in ['CS_Kill', 'CS_RegistryEnd', 'CS_Holiday',
              'CS_BreakExit', 'CS_TimeExit', 'CS_SL', 'CS_Entry']:
    report(f"REG6: label {label} preserved",
           bool(re.search(rf'\b{label}\b', l4)), "")

# ExitFired pattern preserved
report("REG7: ExitFired = 0 reset preserved",
       'ExitFired = 0' in l4, "")
report("REG8: Frozen stop formula preserved",
       'v_Stop_Level = v_Frozen_LockedTop + (ATR_Stop_Mult * v_Frozen_ATR)' in l4, "")
report("REG9: v14.0 dynamic fallback formula preserved",
       'v_Stop_Level = v_Locked_Top + (ATR_Stop_Mult * v_Current_ATR)' in l4, "")

# ============================================================
print()
print("=" * 72)
print("LAYER PA: Path A - Night entry block")
print("=" * 72)

# Input
m = re.search(r'Night_Block_On\s*\(\s*(\w+)\s*\)', strip_pl_comments(l4))
report("PA1: Night_Block_On input declared",
       m is not None, f"got '{m.group(1) if m else None}'")
report("PA2: Night_Block_On default = true (v14.2B Variant B production)",
       m and m.group(1).lower() == 'true', "")

# Variable
report("PA3: v_Night_Block variable declared",
       bool(re.search(r'v_Night_Block\s*\(\s*false\s*\)', l4)), "")

# Logic: 02:00-04:59 window
report("PA4: Night detection logic (Time >= 200 and Time < 500)",
       bool(re.search(r'Night_Block_On\s*=\s*true\s+and\s+Time\s*>=\s*200\s+and\s+Time\s*<\s*500', l4)), "")

# Entry gate has v_Night_Block
m = re.search(
    r'if MarketPosition\s*=\s*0(.*?)SellShort\s*\(\s*"CS_Entry"\s*\)',
    l4, re.DOTALL)
if m:
    body = m.group(1)
    report("PA5: Entry gate has v_Night_Block = false",
           'v_Night_Block' in body and 'false' in body, "")
else:
    report("PA5: Entry block parseable", False, "regex failed")

# ============================================================
print()
print("=" * 72)
print("LAYER PB: Path B - BE + SP inputs")
print("=" * 72)

stripped = strip_pl_comments(l4)
inputs_check = {
    'BE_Trigger_Pts': '0',
    'BE_Offset_Pts': '5',
    'SP_Trigger_Pts': '0',
    'SP_Retain_Pct': '50',
}
for name, expected in inputs_check.items():
    m = re.search(rf'{name}\s*\(\s*(\w+)\s*\)', stripped)
    actual = m.group(1) if m else None
    report(f"PB1: {name} = {expected} (production default)",
           actual == expected, f"got '{actual}'")

# Variables
pb_vars = ['v_Peak_Profit_Pts', 'v_BE_Armed', 'v_SP_Armed',
           'v_BE_Floor', 'v_SP_Floor', 'v_Effective_Stop']
for v in pb_vars:
    ok = bool(re.search(rf'\b{v}\s*\(', l4))
    report(f"PB2: variable {v} declared", ok, "")

# ============================================================
print()
print("=" * 72)
print("LAYER PB-LOGIC: Path B - arming & floor formulas")
print("=" * 72)

# MFE tracking (close-based)
report("PB-L1: MFE tracking uses EntryPrice - Close",
       'EntryPrice - Close > v_Peak_Profit_Pts' in l4, "")

# BE arming logic
report("PB-L2: BE arming gated by BE_Trigger_Pts > 0",
       bool(re.search(r'BE_Trigger_Pts\s*>\s*0\s+and\s+v_Peak_Profit_Pts\s*>=\s*BE_Trigger_Pts',
                      l4)), "")

# SP arming logic
report("PB-L3: SP arming gated by SP_Trigger_Pts > 0",
       bool(re.search(r'SP_Trigger_Pts\s*>\s*0\s+and\s+v_Peak_Profit_Pts\s*>=\s*SP_Trigger_Pts',
                      l4)), "")

# BE floor formula
report("PB-L4: BE floor = EntryPrice - BE_Offset_Pts",
       'v_BE_Floor = EntryPrice - BE_Offset_Pts' in l4, "")

# SP floor formula
sp_formula = re.search(
    r'v_SP_Floor\s*=\s*EntryPrice\s*-\s*\(\s*v_Peak_Profit_Pts\s*\*\s*'
    r'\(\s*1\s*-\s*SP_Retain_Pct\s*/\s*100\s*\)\s*\)',
    l4)
report("PB-L5: SP floor = EntryPrice - Peak*(1-Retain/100)",
       bool(sp_formula), "")

# ============================================================
print()
print("=" * 72)
print("LAYER PB-EXIT: labeled stop priority (CS_SP > CS_BE > CS_SL)")
print("=" * 72)

# All three labels emitted
for label in ['CS_BE', 'CS_SP']:
    has = bool(re.search(rf'BuyToCover\s*\(\s*"{label}"\s*\)', l4))
    report(f"PB-X1: {label} emitted somewhere", has, "")

# Priority order: SP block appears before BE block appears before SL block
sp_pos = l4.find('BuyToCover ("CS_SP")')
be_pos = l4.find('BuyToCover ("CS_BE")')
sl_pos = l4.rfind('BuyToCover ("CS_SL")')  # rfind for last occurrence
report("PB-X2: SP labeled stop appears before BE", 0 <= sp_pos < be_pos,
       f"SP@{sp_pos}, BE@{be_pos}")
report("PB-X3: BE labeled stop appears before SL", 0 <= be_pos < sl_pos,
       f"BE@{be_pos}, SL@{sl_pos}")

# Mutually exclusive if/else if/else
ifelse_block = re.search(
    r'v_Effective_Stop\s*=\s*v_Stop_Level\s*;.*?'
    r'if\s+v_SP_Armed.*?then\s+begin.*?end\s+else\s+if\s+v_BE_Armed.*?then\s+begin.*?end\s+else\s+begin',
    l4, re.DOTALL)
report("PB-X4: SP/BE/SL emitted via mutually exclusive if/else if/else",
       bool(ifelse_block), "guards prevent parallel stop orders")

# Floor binding conditions (must be < Effective_Stop)
report("PB-X5: SP floor binding requires v_SP_Floor < v_Effective_Stop",
       bool(re.search(r'v_SP_Floor\s*<\s*v_Effective_Stop', l4)), "")
report("PB-X6: BE floor binding requires v_BE_Floor < v_Effective_Stop",
       bool(re.search(r'v_BE_Floor\s*<\s*v_Effective_Stop', l4)), "")

# ============================================================
print()
print("=" * 72)
print("LAYER STATE: state reset on flat (all v14.2 vars included)")
print("=" * 72)

# Walk forward from "Snapshot box and reset"
anchor = l4.find('Snapshot box and reset')
pos = l4.find('if MarketPosition = 0 then begin', anchor)
depth = 1
i = pos + len('if MarketPosition = 0 then begin')
start = i
while depth > 0 and i < len(l4):
    m = re.search(r'\b(begin|end)\b', l4[i:], re.IGNORECASE)
    if not m: break
    tok = m.group(1).lower()
    if tok == 'begin': depth += 1
    else: depth -= 1
    i += m.end()
reset_body = l4[start:i]

for v in ['v_Lowest_Low', 'v_Trail_Active', 'v_SL_Locked',
          'v_Frozen_ATR', 'v_Frozen_LockedTop',
          'v_Peak_Profit_Pts', 'v_BE_Armed', 'v_SP_Armed',
          'v_BE_Floor', 'v_SP_Floor']:
    report(f"STATE: {v} reset on flat", v in reset_body, "")

# ============================================================
print()
print("=" * 72)
print("LAYER L3-TRAP: L3 variant D mistakes NOT repeated")
print("=" * 72)

report("L3T1: Default BE_Trigger_Pts = 0 (off, not the dangerous +50)",
       bool(re.search(r'BE_Trigger_Pts\s*\(\s*0\s*\)', stripped)), "")
report("L3T2: Default SP_Trigger_Pts = 0 (off in production)",
       bool(re.search(r'SP_Trigger_Pts\s*\(\s*0\s*\)', stripped)), "")
report("L3T3: BE arming gated (BE_Trigger > 0 required)",
       'BE_Trigger_Pts > 0' in l4, "off when input = 0")
report("L3T4: SP arming gated (SP_Trigger > 0 required)",
       'SP_Trigger_Pts > 0' in l4, "off when input = 0")
report("L3T5: Floors guarded by > 0 check before binding",
       'v_BE_Floor > 0 and v_BE_Floor < v_Effective_Stop' in l4 and
       'v_SP_Floor > 0 and v_SP_Floor < v_Effective_Stop' in l4, "")

# ============================================================
print()
print("=" * 72)
print("LAYER DOC: documentation completeness")
print("=" * 72)

import os
docs_dir = 'docs/'
report("DOC1: pathA_entry_diagnostic.md exists",
       os.path.exists(docs_dir + 'L4_v14.2_pathA_entry_diagnostic.md'), "")
report("DOC2: pathB_variant_matrix.md exists",
       os.path.exists(docs_dir + 'L4_v14.2_pathB_variant_matrix.md'), "")

# Header explanations
report("DOC3: Changelog v14.2 dated 2026-06-13",
       'v14.2' in l4 and '(2026-06-13)' in l4, "")
report("DOC4: Header lists named variants A-G",
       'A baseline' in l4 and 'F A+D' in l4, "")
report("DOC5: Header references L3 trap analysis",
       'L3 variant D' in l4 and 'NOT L3 variant D' in l4, "")
report("DOC6: Header lists acceptance criteria",
       'ACCEPTANCE CRITERIA' in l4 and 'CS_BE/SP WR >=50' in l4, "")

# ============================================================
print()
print("=" * 72)
print("LAYER SYN: PowerLanguage syntax sanity")
print("=" * 72)

l4_no_comments = strip_pl_comments(l4)
begin_count = len(re.findall(r'\bbegin\b', l4_no_comments, re.IGNORECASE))
end_count = len(re.findall(r'\bend\b', l4_no_comments, re.IGNORECASE))
report(f"SYN1: begin/end balance ({begin_count}/{end_count}, comments stripped)",
       begin_count == end_count, "")

# Inputs end with semicolon
report("SYN2: inputs block ends with semicolon",
       bool(re.search(r'SP_Retain_Pct\s*\(\s*50\s*\)\s*;', l4)), "")

# Variables block has all entries comma-separated, ends with semicolon
report("SYN3: variables block ends with semicolon",
       'ExitFired(0);' in l4, "")

# File ends cleanly
last_char = l4.rstrip()[-1]
report("SYN4: File ends cleanly", last_char in ';}', f"last char: '{last_char}'")

# ============================================================
print()
print("=" * 72)
print("FINAL v14.2 VERIFICATION SUMMARY")
print("=" * 72)
passed = sum(1 for r in results if r)
total = len(results)
print(f"  Passed: {passed}/{total} ({100*passed/total:.1f}%)")
print(f"  Layers: REG (v14.1 invariants) PA (Path A) PB (Path B inputs)")
print(f"          PB-LOGIC (arming/floors) PB-EXIT (labeled stop priority)")
print(f"          STATE (flat reset) L3-TRAP (safety) DOC (documentation)")
print(f"          SYN (PowerLanguage syntax)")
if passed == total:
    print("  v14.2 CLEARED for MC9 A/B testing (variants A-G)")
else:
    print(f"  {total - passed} CHECKS FAILED - review above")
