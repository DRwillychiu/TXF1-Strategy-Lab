"""L4 v14.1 PRECISION cross-verification (round 2).

Builds on verify_l4_v141.py with semantic ordering, byte-level
holiday-module comparison vs L3, edge-case checks, and full
parameter-grid consistency vs the rest of the live shelf.
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

# Helper: find a code section by walking begin/end depth
def extract_block(s, start_pattern):
    m = re.search(start_pattern, s)
    if not m:
        return None
    pos = m.end()
    depth = 1
    start = pos
    while depth > 0 and pos < len(s):
        nxt = re.search(r'\b(begin|end)\b', s[pos:], re.IGNORECASE)
        if not nxt:
            break
        tok = nxt.group(1).lower()
        if tok == 'begin':
            depth += 1
        else:
            depth -= 1
        pos += nxt.end()
    return s[start:pos]

# Index lookup helpers
def pos(s, substr):
    return s.find(substr)

# ============================================================
print("=" * 72)
print("LAYER A: SEMANTIC ORDERING (precision)")
print("=" * 72)

# A1: v_Holiday_Block reset BEFORE the tail-detection for loop
hb_reset = pos(l4, 'v_Holiday_Block = false')
hb_loop = pos(l4, 'for hidx = 1 to 80')
report("A1: v_Holiday_Block reset BEFORE tail-detection loop",
       0 <= hb_reset < hb_loop, f"reset@{hb_reset}, loop@{hb_loop}")

# A2: Freeze block BEFORE stop calc
freeze_block = pos(l4, 'if Freeze_SL_On and v_SL_Locked = false then begin')
stop_calc = pos(l4, '{ 4. Stop Level Calculation }')
report("A2: Freeze block BEFORE stop calc",
       0 <= freeze_block < stop_calc, f"freeze@{freeze_block}, calc@{stop_calc}")

# A3: ExitFired = 0 BEFORE Priority 0 checks
exitfired_reset = pos(l4, 'ExitFired = 0;')
priority0 = pos(l4, 'Priority 0 - Manual Kill')
report("A3: ExitFired = 0 BEFORE Priority 0 checks",
       0 <= exitfired_reset < priority0, f"reset@{exitfired_reset}, p0@{priority0}")

# A4: Priority order strictly enforced in file
labels_in_order = ['CS_Kill', 'CS_RegistryEnd', 'CS_Holiday',
                   'CS_BreakExit', 'CS_TimeExit', 'CS_SL']
positions = []
for label in labels_in_order:
    m = re.search(rf'BuyToCover\s*\(\s*"{label}"\s*\)', l4)
    positions.append((label, m.start() if m else -1))
is_sorted = all(positions[i][1] < positions[i+1][1] for i in range(len(positions)-1))
report("A4: Exit labels appear in strict priority order in file",
       is_sorted, str([p[0] for p in positions]))

# A5: v_Current_ATR computed BEFORE Phase 3 (so freeze can capture it)
atr_calc = pos(l4, 'v_Current_ATR = AvgTrueRange(ATR_Length);')
phase3 = pos(l4, 'Phase 3: Exit Logic')
report("A5: v_Current_ATR computed BEFORE Phase 3 freeze block",
       0 <= atr_calc < phase3, f"atr@{atr_calc}, phase3@{phase3}")

# A6: State reset block AFTER comments, BEFORE MarketPosition = -1 block
reset_anchor = pos(l4, 'Snapshot box and reset tracking when flat')
mp_minus = pos(l4, 'if MarketPosition = -1 then begin')
report("A6: State reset (flat) appears BEFORE MarketPosition = -1 block",
       0 <= reset_anchor < mp_minus,
       f"reset@{reset_anchor}, mp=-1@{mp_minus}")

# A7: Entry gate AFTER v_Holiday_Block computation
hb_compute = pos(l4, 'v_Holiday_Block = true;')  # in registry expiry section
entry = pos(l4, 'SellShort ("CS_Entry") next bar at Market;')
report("A7: Entry gate AFTER v_Holiday_Block determination",
       0 <= hb_compute < entry, f"hb@{hb_compute}, entry@{entry}")

# ============================================================
print()
print("=" * 72)
print("LAYER B: HOLIDAY MODULE BYTE-COMPARISON (L4 vs L3, same 15M grid)")
print("=" * 72)

def extract_holiday_section(s):
    # Extract just the array-init block (61 lines starting with first Holiday_Tail[1])
    m = re.search(r'(if CurrentBar = 1 then begin.*?{ 2027 CNY onward.*?})', s, re.DOTALL)
    return m.group(1) if m else None

l3_h = extract_holiday_section(content['L3'])
l4_h = extract_holiday_section(l4)
# Normalize whitespace
def normalize(s):
    return re.sub(r'\s+', ' ', s).strip() if s else ''
n3, n4 = normalize(l3_h), normalize(l4_h)
report("B1: Holiday array init blocks byte-equivalent (L3 vs L4)",
       n3 == n4, f"L3={len(n3)} bytes, L4={len(n4)} bytes")

# Diff registry value-by-value
def extract_pairs(s):
    return dict((int(i), int(v)) for i, v in re.findall(r'Holiday_Tail\[\s*(\d+)\s*\]\s*=\s*(\d+)', s))
p3 = extract_pairs(content['L3'])
p4 = extract_pairs(l4)
diff_keys = [k for k in set(p3) | set(p4) if p3.get(k) != p4.get(k)]
report("B2: Per-entry registry values identical (L3 vs L4)",
       len(diff_keys) == 0, f"{len(diff_keys)} mismatches")

# Holiday_Flat_Time matches 15M grid choice
hft_l3 = re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', content['L3'])
hft_l4 = re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', l4)
report("B3: Holiday_Flat_Time = 415 in both L3 and L4 (15M grid)",
       hft_l3 and hft_l4 and hft_l3.group(1) == '415' and hft_l4.group(1) == '415',
       f"L3={hft_l3.group(1) if hft_l3 else 'N/A'}, L4={hft_l4.group(1) if hft_l4 else 'N/A'}")

# Detection logic byte-comparison (Time<=500 + for loop)
def extract_detect(s):
    m = re.search(r'(v_Holiday_Block = false;.*?for hidx = 1 to 80 begin.*?end;)',
                  s, re.DOTALL)
    return normalize(m.group(1)) if m else None
report("B4: Tail-detection logic byte-equivalent (L3 vs L4)",
       extract_detect(content['L3']) == extract_detect(l4), "")

# Registry fail-safe + warning byte-comparison
def extract_failsafe(s):
    m = re.search(r'(v_Registry_Expired = false;.*?Text_SetAttribute.*?end;.*?end;)',
                  s, re.DOTALL)
    return normalize(m.group(1)) if m else None
report("B5: Registry fail-safe + 30-day warning byte-equivalent (L3 vs L4)",
       extract_failsafe(content['L3']) == extract_failsafe(l4), "")

# ============================================================
print()
print("=" * 72)
print("LAYER C: VARIABLE DECLARATION UNIQUENESS")
print("=" * 72)

# Extract variables block
vars_block = re.search(r'variables:(.*?)arrays:', l4, re.DOTALL)
if vars_block:
    decls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', vars_block.group(1))
    from collections import Counter
    counter = Counter(decls)
    dups = {k: v for k, v in counter.items() if v > 1}
    report("C1: No duplicate variable declarations",
           len(dups) == 0, f"dups: {dups}" if dups else f"{len(set(decls))} unique vars")
else:
    report("C1: Variables block found", False, "regex failed")

# Required v14.1 vars present exactly once
v141_vars = ['v_SL_Locked', 'v_Frozen_ATR', 'v_Frozen_LockedTop',
             'v_Holiday_Block', 'v_Registry_Expired', 'ExitFired']
if vars_block:
    body = vars_block.group(1)
    for v in v141_vars:
        n = len(re.findall(rf'\b{v}\s*\(', body))
        report(f"C2: {v} declared exactly once", n == 1, f"count={n}")

# ============================================================
print()
print("=" * 72)
print("LAYER D: EDGE CASES")
print("=" * 72)

# D1: v_SL_Locked initial value = false (so freeze runs on first entry bar)
m = re.search(r'v_SL_Locked\s*\(\s*(\w+)\s*\)', l4)
report("D1: v_SL_Locked default = false (freeze fires on entry bar)",
       m and m.group(1).lower() == 'false', f"got '{m.group(1) if m else None}'")

# D2: v_Frozen_ATR default = 0
m = re.search(r'v_Frozen_ATR\s*\(\s*(\d+)\s*\)', l4)
report("D2: v_Frozen_ATR default = 0", m and m.group(1) == '0', "")

# D3: v_Frozen_LockedTop default = 0
m = re.search(r'v_Frozen_LockedTop\s*\(\s*(\d+)\s*\)', l4)
report("D3: v_Frozen_LockedTop default = 0", m and m.group(1) == '0', "")

# D4: ExitFired default = 0
m = re.search(r'ExitFired\s*\(\s*(\d+)\s*\)', l4)
report("D4: ExitFired default = 0", m and m.group(1) == '0', "")

# D5: Stop calc has BOTH frozen path AND fallback path
has_frozen = 'v_Stop_Level = v_Frozen_LockedTop + (ATR_Stop_Mult * v_Frozen_ATR)' in l4
has_fallback = 'v_Stop_Level = v_Locked_Top + (ATR_Stop_Mult * v_Current_ATR)' in l4
report("D5: Both frozen path and v14.0 fallback present", has_frozen and has_fallback, "")

# D6: Trail path uses v_Current_ATR (intentional)
trail_uses_current = bool(re.search(
    r'v_Stop_Level = MinList\s*\(\s*v_Stop_Level\[1\]\s*,\s*'
    r'v_Lowest_Low \+ \(Trail_ATR_Mult \* v_Current_ATR\)\s*\)', l4))
report("D6: Trail layer uses v_Current_ATR (intentional design)",
       trail_uses_current, "")

# D7: CS_SL Stop order is UNCONDITIONALLY armed (after exit chain)
# The pattern: after all ExitFired checks, CS_SL Stop fires every bar in position
sl_section = l4[l4.rfind('Priority 3'):]
sl_unconditional = ('BuyToCover ("CS_SL") next bar at v_Stop_Level Stop;' in sl_section
                    and 'ExitFired' not in sl_section.split('BuyToCover ("CS_SL")')[0][-200:])
report("D7: CS_SL Stop always armed (not gated by ExitFired)",
       sl_unconditional, "Stop type cedes to Market on next bar fill")

# ============================================================
print()
print("=" * 72)
print("LAYER E: CROSS-STRATEGY GRID CONSISTENCY")
print("=" * 72)

# All 4 strategies have same Registry_Valid_Until
ru = {k: re.search(r'Registry_Valid_Until\s*\(\s*(\d+)\s*\)', v) for k, v in content.items()}
ru_vals = {k: m.group(1) if m else None for k, m in ru.items()}
report("E1: Registry_Valid_Until consistent across L1/L2/L3/L4",
       len(set(ru_vals.values())) == 1 and '1270101' in ru_vals.values(),
       f"L1={ru_vals['L1']}, L2={ru_vals['L2']}, L3={ru_vals['L3']}, L4={ru_vals['L4']}")

# Holiday_Flat_Time matches each strategy's grid
hft = {k: re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', v) for k, v in content.items()}
expected = {'L1': '345', 'L2': '300', 'L3': '415', 'L4': '415'}
for k, exp in expected.items():
    val = hft[k].group(1) if hft[k] else None
    report(f"E2: {k} Holiday_Flat_Time = {exp} (matches grid)",
           val == exp, f"got {val}")

# Manual_Kill_Switch default = false in all
# (Strip block comments first - changelogs reference Manual_Kill_Switch by name)
def strip_pl_comments(s):
    return re.sub(r'\{[^}]*?\}', '', s, flags=re.DOTALL)
for k, s in content.items():
    s_no_comments = strip_pl_comments(s)
    m = re.search(r'Manual_Kill_Switch\s*\(\s*(\w+)\s*\)', s_no_comments)
    val = m.group(1).lower() if m else None
    report(f"E3: {k} Manual_Kill_Switch default = false",
           val == 'false', f"got {val}")

# Kill labels per strategy
kill_labels = {'L1': 'TL_Kill', 'L2': 'TS_Kill', 'L3': 'CL_Kill', 'L4': 'CS_Kill'}
for k, lbl in kill_labels.items():
    has = bool(re.search(rf'\b{lbl}\b', content[k]))
    report(f"E4: {k} kill label = {lbl} present", has, "")

# ============================================================
print()
print("=" * 72)
print("LAYER F: ENTRY GATE SEMANTIC COMPLETENESS")
print("=" * 72)

# Extract the CS_Entry block precisely
m = re.search(
    r'if MarketPosition\s*=\s*0\s+and\s+([^;]+?)\s+then begin\s+SellShort \("CS_Entry"\)',
    l4, re.DOTALL)
if m:
    conditions = m.group(1)
    required = [
        ('v_BarsSinceExit', '>=', 'Cooldown_Bars'),
        ('v_Trend_Dir', '=', '-1'),
        ('v_Macro_Block', '=', 'false'),
        ('v_In_Trap_Zone', '=', 'true'),
        ('Close', '<', 'v_Trigger_Price'),
        ('v_Holiday_Block', '=', 'false'),
    ]
    for var, op, val in required:
        # The conditions block uses multi-spaced operators, normalize
        norm = re.sub(r'\s+', ' ', conditions)
        ok = re.search(rf'{var}\s*{re.escape(op)}\s*{val}', norm) is not None
        report(f"F1: Entry gate has '{var} {op} {val}'", ok, "")
else:
    report("F: CS_Entry block parseable", False, "regex failed")

# ============================================================
print()
print("=" * 72)
print("LAYER G: HEADER + DOCUMENTATION COMPLETENESS")
print("=" * 72)

report("G1: Script Name has v14.1",
       bool(re.search(r'Script Name\s*:\s*_Live_Adaptive_Farmer_v14\.1', l4)), "")
report("G2: Version line correct",
       'Version     : v14.1 + HolidayFlat_v3 + FrozenSL' in l4, "")
report("G3: Changelog has v14.0 entry (history)", 'v14.0' in l4, "")
report("G4: Changelog has v14.1 entry with 2026-06-13 date",
       'v14.1' in l4 and '(2026-06-13)' in l4, "")
report("G5: Header notes 'Deploy only when flat'",
       'Deploy only when flat' in l4, "")
report("G6: Header notes CS_BreakExit deferred",
       'DEFERRED' in l4 and 'CS_BreakExit' in l4, "")
report("G7: Header preserves v14.0 baseline performance",
       '569,200' in l4 and '1.602' in l4, "")

# ============================================================
print()
print("=" * 72)
print("LAYER H: ANNOTATED MD SYNC")
print("=" * 72)

md_path = 'strategies/live/L4_ConsolidationShort_annotated.md'
with open(md_path, 'r', encoding='utf-8') as f:
    md = f.read()
report("H1: MD title reflects v14.1",
       'v14.1 + HolidayFlat_v3 + FrozenSL' in md, "")
report("H2: MD has 部署檢查清單 section", '部署檢查清單' in md, "")
report("H3: MD lists CS_BreakExit as v14.2 candidate",
       'CS_BreakExit 改造' in md, "")
report("H4: MD entry-gate diagram shows v_Holiday_Block",
       'v_Holiday_Block = false' in md, "")
report("H5: MD parameter table includes Freeze_SL_On + Holiday_Flat_Time",
       'Freeze_SL_On' in md and 'Holiday_Flat_Time' in md, "")

# ============================================================
print()
print("=" * 72)
print("FINAL PRECISION SUMMARY")
print("=" * 72)
passed = sum(1 for r in results if r)
total = len(results)
print(f"  Passed: {passed}/{total} ({100*passed/total:.1f}%)")
print(f"  Layers covered: A(ordering) B(byte-diff) C(uniqueness) "
      f"D(edge cases) E(grid) F(entry gate) G(header) H(docs)")
if passed == total:
    print("  PRECISION VERIFIED - L4 v14.1 cleared for MC9 deployment")
else:
    print(f"  {total - passed} CHECKS FAILED")
