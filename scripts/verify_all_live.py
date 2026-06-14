"""Master cross-verification for ALL live strategies L1-L5.

Confirms:
  1. Cross-strategy invariants (Holiday registry, grid params, kill labels)
  2. Each strategy at its sealed production version
  3. Each strategy's signature mechanisms intact
  4. PowerLanguage syntax sanity per file

Supersedes verify_l4_v141.py / verify_l4_v141_precision.py
(those were v14.1 snapshots, now obsolete after v14.2B seal).
verify_l4_v142.py kept as the L4-specific deep dive.
"""
import re, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FILES = {
    'L1': 'strategies/live/L1_TrendLong.pla',
    'L2': 'strategies/live/L2_TrendShort.pla',
    'L3': 'strategies/live/L3_ConsolidationLong.pla',
    'L4': 'strategies/live/L4_ConsolidationShort.pla',
    'L5': 'strategies/live/L5_BreakoutLong.pla',
}
content = {}
for k, p in FILES.items():
    with open(p, 'r', encoding='utf-8') as f:
        content[k] = f.read()

results = []
def report(check, ok, detail=""):
    mark = "OK  " if ok else "FAIL"
    print(f"  [{mark}] {check}: {detail}")
    results.append((check, ok))

def strip_pl_comments(s):
    """Depth-aware bracket parser. PL uses {...} comments;
    naive regex fails when header contains nested-looking text
    (e.g. input lines like Foo(0) { description }). This walks
    character-by-character tracking brace depth."""
    out = []
    depth = 0
    for c in s:
        if c == '{':
            depth += 1
            continue
        if c == '}':
            if depth > 0:
                depth -= 1
            continue
        if depth == 0:
            out.append(c)
    return ''.join(out)

# ===== LAYER X: Cross-Strategy Invariants =====
print("=" * 75)
print("LAYER X: Cross-Strategy Invariants (L1/L2/L3/L4 must agree)")
print("=" * 75)

def extract_registry(s):
    # Strip comments first - changelogs may mention Holiday_Tail[80] = 63 in prose
    clean = strip_pl_comments(s)
    return {int(i): int(v) for i, v in
            re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)}

regs = {k: extract_registry(content[k]) for k in FILES}
for k in 'L1 L2 L3 L4 L5'.split():
    report(f"X1: {k} holiday registry has 63 entries",
           len(regs[k]) == 63, f"got {len(regs[k])}")

# Pairwise equality
ref = regs['L3']
for k in 'L1 L2 L4 L5'.split():
    diffs = sum(1 for i in set(ref) | set(regs[k]) if ref.get(i) != regs[k].get(i))
    report(f"X2: {k} registry identical to L3", diffs == 0, f"{diffs} diffs")

# Registry_Valid_Until
for k in FILES:
    m = re.search(r'Registry_Valid_Until\s*\(\s*(\d+)\s*\)', strip_pl_comments(content[k]))
    val = m.group(1) if m else None
    report(f"X3: {k} Registry_Valid_Until = 1270101", val == '1270101', f"got {val}")

# Holiday_Flat_Time per grid
expected_flat = {'L1': '345', 'L2': '300', 'L3': '415', 'L4': '415', 'L5': '415'}
for k, exp in expected_flat.items():
    m = re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', strip_pl_comments(content[k]))
    val = m.group(1) if m else None
    report(f"X4: {k} Holiday_Flat_Time = {exp}", val == exp, f"got {val}")

# Manual_Kill_Switch default = false
for k in FILES:
    m = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', strip_pl_comments(content[k]))
    val = m.group(1).lower() if m else None
    report(f"X5: {k} Manual_Kill_Switch default = false", val == 'false', f"got {val}")

# Distinct kill labels
kill_labels = {'L1': 'TL_Kill', 'L2': 'TS_Kill', 'L3': 'CL_Kill',
               'L4': 'CS_Kill', 'L5': 'BL_Kill'}
for k, lbl in kill_labels.items():
    report(f"X6: {k} kill label = {lbl}",
           lbl in content[k], "")

# 6/18 Dragon Boat (next live test)
for k in FILES:
    report(f"X7: {k} has 1260619 (Dragon Boat eve+1)",
           bool(re.search(r'Holiday_Tail\[\s*58\s*\]\s*=\s*1260619', content[k])), "")

# ===== LAYER L1 =====
print()
print("=" * 75)
print("LAYER L1: V2.6 + StopProfit + FrozenSL + HolidayFlat_v3")
print("=" * 75)

l1 = content['L1']
report("L1-1: Version V2.6 in header", 'V2.6' in l1, "")
report("L1-2: StopProfit module signature present",
       'posbleProfit_Long' in l1 and 'stopProfitPrice_L' in l1, "")
report("L1-3: stopProfitPoints_Long(250) default",
       bool(re.search(r'stopProfitPoints_Long\s*\(\s*250\s*\)', l1)), "")
report("L1-4: profitReturnPrcnt_Long(55) default",
       bool(re.search(r'profitReturnPrcnt_Long\s*\(\s*55\s*\)', l1)), "")
report("L1-5: FrozenSL signature (v_SL_Locked or v_Frozen_SL)",
       'v_SL_Locked' in l1 or 'v_Frozen_SL' in l1, "")
report("L1-6: TL_SP label emitted", 'TL_SP' in l1, "")
report("L1-7: TL_Entry label emitted", 'TL_Entry' in l1, "")
report("L1-8: TL_Holiday label emitted", 'TL_Holiday' in l1, "")
report("L1-9: Holiday entry gate (v_Holiday_Block in entry block)",
       'v_Holiday_Block' in l1, "")

# ===== LAYER L2 =====
print()
print("=" * 75)
print("LAYER L2: 5.2 + HolidayFlat_v3 (sealed)")
print("=" * 75)

l2 = content['L2']
report("L2-1: Version 5.2 in header", '5.2' in l2, "")
report("L2-2: SL_Locked pattern present", 'SL_Locked' in l2, "")
report("L2-3: stopProfitPoints_Shrt(250)",
       bool(re.search(r'stopProfitPoints_Shrt\s*\(\s*250\s*\)', l2)), "")
report("L2-4: profitReturnPrcnt_Shrt(55)",
       bool(re.search(r'profitReturnPrcnt_Shrt\s*\(\s*55\s*\)', l2)), "")
report("L2-5: TS_Holiday label emitted", 'TS_Holiday' in l2, "")
report("L2-6: TS_StopProfit label emitted", 'TS_StopProfit' in l2, "")
report("L2-7: Entry gate has v_Holiday_Block",
       bool(re.search(r'\(\s*v_Holiday_Block\s*=\s*False\s*\)', l2)), "")

# ===== LAYER L3 =====
print()
print("=" * 75)
print("LAYER L3: v13.2B PRODUCTION (Freeze ON, BE OFF per A/B verdict)")
print("=" * 75)

l3 = content['L3']
report("L3-1: Version v13.2B in header", 'v13.2B' in l3, "")
l3_clean = strip_pl_comments(l3)
m = re.search(r'Freeze_SL_On\s*\(\s*(\w+)\s*\)', l3_clean)
report("L3-2: Freeze_SL_On default = true (production)",
       m and m.group(1).lower() == 'true', f"got {m.group(1) if m else None}")
m = re.search(r'BE_Trigger_Pts\s*\(\s*(\d+)\s*\)', l3_clean)
report("L3-3: BE_Trigger_Pts default = 0 (Variant D rejected)",
       m and m.group(1) == '0', f"got {m.group(1) if m else None}")
report("L3-4: CL_Holiday label", 'CL_Holiday' in l3, "")
report("L3-5: CL_BreakExit label", 'CL_BreakExit' in l3, "")
report("L3-6: CL_TP_Bot + CL_TP_Mid labels",
       'CL_TP_Bot' in l3 and 'CL_TP_Mid' in l3, "")
report("L3-7: CL_BE label preserved (code preserved, input off)",
       'CL_BE' in l3, "")
report("L3-8: Frozen leg / SL / Target locked at entry",
       'v_Frozen_SL' in l3 and 'v_Frozen_Target' in l3, "")

# ===== LAYER L5 =====
print()
print("=" * 75)
print("LAYER L5: v19.8 + Pre-Trail SP A/B Engine + HolidayFlat_v3 + FrozenSL")
print("=" * 75)

l5 = content['L5']
report("L5-1: Version v19.8 in header", 'v19.8' in l5, "")
l5_clean = strip_pl_comments(l5)
m = re.search(r'Freeze_SL_On\s*\(\s*(\w+)\s*\)', l5_clean)
report("L5-2: Freeze_SL_On default = true (v19.7 carried over)",
       m and m.group(1).lower() == 'true', f"got {m.group(1) if m else None}")
m = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', l5_clean)
report("L5-3: Manual_Kill_Switch default = false",
       m and m.group(1).lower() == 'false', f"got {m.group(1) if m else None}")
report("L5-4: BL_Holiday label", 'BL_Holiday' in l5, "")
report("L5-5: BL_RegistryEnd label", 'BL_RegistryEnd' in l5, "")
report("L5-6: BL_Kill label", 'BL_Kill' in l5, "")
report("L5-7: BL_Entry_Bot + BL_Entry_Mid preserved",
       'BL_Entry_Bot' in l5 and 'BL_Entry_Mid' in l5, "")
report("L5-8: BL_BE preserved (existing mechanism untouched)",
       'BL_BE_Bot' in l5 and 'BL_BE_Mid' in l5, "")
report("L5-9: BL_Trail preserved (God Mode)",
       'BL_Trail_Bot' in l5 and 'BL_Trail_Mid' in l5, "")
report("L5-10: DayOfWeek=7 dead code REMOVED (from code, not changelog)",
       'DayOfWeek(Date) = 7' not in l5_clean and 'DayOfWeek(Date)= 7' not in l5_clean, "")
report("L5-11: BL_SatClose dead labels REMOVED (from code, not changelog)",
       'BL_SatClose' not in l5_clean, "")
report("L5-12: Frozen ATR Buffer formula present",
       'v_Frozen_ATR_Buffer = v_Frozen_ATR * ATR_Stop_Mult' in l5, "")
report("L5-13: Holiday block as entry gate (v_Allow_Entry = false)",
       'if v_Holiday_Block then' in l5 and 'v_Allow_Entry = false' in l5, "")
# v19.8 SP module checks
m = re.search(r'SP_Trigger_Pts\s*\(\s*(\d+)\s*\)', l5_clean)
report("L5-14: SP_Trigger_Pts default = 0 (v19.8 A/B engine OFF in production)",
       m and m.group(1) == '0', f"got {m.group(1) if m else None}")
m = re.search(r'SP_Retain_Pct\s*\(\s*(\d+)\s*\)', l5_clean)
report("L5-15: SP_Retain_Pct default = 50",
       m and m.group(1) == '50', f"got {m.group(1) if m else None}")
report("L5-16: v_Peak_Profit close-based tracking (L1 SP pattern)",
       'Close - EntryPrice > v_Peak_Profit' in l5, "")
report("L5-17: v_SP_Floor formula = EntryPrice + Peak*(1-Retain/100)",
       bool(re.search(
           r'v_SP_Floor\s*=\s*EntryPrice\s*\+\s*\(\s*v_Peak_Profit\s*\*\s*'
           r'\(\s*1\s*-\s*SP_Retain_Pct\s*/\s*100\s*\)\s*\)', l5)), "")
report("L5-18: BL_SP_Bot + BL_SP_Mid labels emitted",
       'BL_SP_Bot' in l5 and 'BL_SP_Mid' in l5, "")
report("L5-19: SP arming gated by SP_Trigger_Pts > 0",
       bool(re.search(r'SP_Trigger_Pts\s*>\s*0\s+and\s+v_Peak_Profit\s*>=\s*SP_Trigger_Pts',
                      l5)), "")
report("L5-20: Trail > SP priority (Trail uses MaxList with SP_Floor)",
       'MaxList(EntryPrice, v_SP_Floor)' in l5, "")

# ===== LAYER L4 =====
print()
print("=" * 75)
print("LAYER L4: v14.2B PRODUCTION (Variant B = Path A on, Path B off)")
print("=" * 75)

l4 = content['L4']
report("L4-1: Version v14.2B in header", 'v14.2B' in l4, "")
l4_clean = strip_pl_comments(l4)
m = re.search(r'Night_Block_On\s*\(\s*(\w+)\s*\)', l4_clean)
report("L4-2: Night_Block_On default = true (Variant B)",
       m and m.group(1).lower() == 'true', f"got {m.group(1) if m else None}")
m = re.search(r'BE_Trigger_Pts\s*\(\s*(\d+)\s*\)', l4_clean)
report("L4-3: BE_Trigger_Pts default = 0 (variants C/E rejected)",
       m and m.group(1) == '0', f"got {m.group(1) if m else None}")
m = re.search(r'SP_Trigger_Pts\s*\(\s*(\d+)\s*\)', l4_clean)
report("L4-4: SP_Trigger_Pts default = 0 (variants D/F/G rejected)",
       m and m.group(1) == '0', f"got {m.group(1) if m else None}")
m = re.search(r'Freeze_SL_On\s*\(\s*(\w+)\s*\)', l4_clean)
report("L4-5: Freeze_SL_On default = true (v14.1 frozen SL preserved)",
       m and m.group(1).lower() == 'true', f"got {m.group(1) if m else None}")
report("L4-6: CS_Holiday label", 'CS_Holiday' in l4, "")
report("L4-7: CS_BE / CS_SP labels preserved (code preserved, input off)",
       'CS_BE' in l4 and 'CS_SP' in l4, "")
report("L4-8: CS_BreakExit label (untouched)", 'CS_BreakExit' in l4, "")

# ===== LAYER SYN: PowerLanguage syntax per file =====
print()
print("=" * 75)
print("LAYER SYN: PowerLanguage syntax (begin/end balance per file)")
print("=" * 75)

for k in FILES:
    clean = strip_pl_comments(content[k])
    b = len(re.findall(r'\bbegin\b', clean, re.IGNORECASE))
    e = len(re.findall(r'\bend\b', clean, re.IGNORECASE))
    report(f"SYN-{k}: begin/end balance ({b}/{e})", b == e, "")
    last = content[k].rstrip()[-1]
    report(f"SYN-{k}: file ends cleanly ('{last}')", last in ';}', "")

# ===== LAYER DOC: documentation files =====
print()
print("=" * 75)
print("LAYER DOC: documentation completeness")
print("=" * 75)

required_docs = [
    'docs/entry_exit_sop.md',
    'docs/position_sizing_and_capacity.md',
    'docs/L4_v142_pathA_entry_diagnostic.md',
    'docs/L4_v142_pathB_variant_matrix.md',
    'docs/L4_v142_variant_results.md',
    'strategies/live/L1_TrendLong_annotated.md',
    'strategies/live/L1_TrendLong_review.md',
    'strategies/live/L2_TrendShort_review.md',
    'strategies/live/L3_ConsolidationLong_annotated.md',
    'strategies/live/L3_ConsolidationLong_review.md',
    'strategies/live/L4_ConsolidationShort_annotated.md',
    'strategies/live/L5_BreakoutLong_annotated.md',
    'strategies/live/L5_BreakoutLong_review.md',
    'docs/L5_v198_pretrail_sp_design.md',
]
for p in required_docs:
    report(f"DOC: {p}", os.path.exists(p), "")

# ===== SUMMARY =====
print()
print("=" * 75)
print("MASTER VERIFICATION SUMMARY (L1-L5 all sealed productions)")
print("=" * 75)
passed = sum(1 for _, ok in results if ok)
total = len(results)
print(f"  Passed: {passed}/{total} ({100*passed/total:.1f}%)")
failed = [c for c, ok in results if not ok]
if failed:
    print(f"  Failed checks:")
    for c in failed:
        print(f"    - {c}")
else:
    print(f"  ALL LIVE STRATEGIES VERIFIED AT PRODUCTION VERSION")
