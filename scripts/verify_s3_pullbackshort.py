"""Verify S3_RapidPullbackShort.pla v1.0 against all 11 design+constitution checks.

Pattern: mirrors verify_settlement_flat.py / verify_all_live.py style.
Target : strategies/research/S03_PullbackShort/S3_RapidPullbackShort.pla

Check groups (total ~60):
  A. Rule #11  Settlement_Flat 7 elements              (5)
  B. Rule #12  P3b SetStopLoss                         (5)
  C. Rule #13  10-dim eval readiness / inputs          (3)
  D. Entry logic correctness                           (10)
  E. Exit logic correctness                            (10)
  F. Time safety (closed-interval audit)               (5)
  G. Volume safety (S2 v0.4 lesson)                    (1)
  H. Filter redundancy check                           (3)
  I. Same-day cooldown                                 (3)
  J. Label convention (SE_RPS_/SX_RPS_, short-only)    (5)
  K. Other (header / inits / feeds / inputs doc)       (10)

Output: per-check OK/FAIL lines + final TOTAL: X/60.
"""
import re
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PLA_PATH = 'strategies/research/S03_PullbackShort/S3_RapidPullbackShort.pla'


def strip_pl_comments(s):
    """Depth-aware {...} comment stripper (PowerLanguage).

    Same routine used in verify_all_live.py - naive regex fails when
    header contains nested-looking text. Walks character-by-character
    tracking brace depth.
    """
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


# -------- load file --------
if not os.path.exists(PLA_PATH):
    print(f"ERROR: cannot find {PLA_PATH}")
    print("       (run from repo root: C:/Users/User/Desktop/TXF1-Strategy-Lab)")
    sys.exit(2)

with open(PLA_PATH, 'r', encoding='utf-8') as f:
    raw = f.read()

clean = strip_pl_comments(raw)
clean_lc = clean.lower()

results = []


def chk(name, ok, detail=''):
    mark = 'OK  ' if ok else 'FAIL'
    print(f'  [{mark}] {name}: {detail}')
    results.append((name, bool(ok)))


# ===============================================================
# A. Rule #11 - Settlement_Flat 7 elements (5 checks)
# ===============================================================
print('=' * 75)
print('A. Rule #11 - Settlement_Flat (5 checks)')
print('=' * 75)

# A1: Settlement_Flat_Time(1230) input present
m = re.search(r'Settlement_Flat_Time\s*\(\s*(\d+)\s*\)', clean)
chk('A1: Settlement_Flat_Time(1230) input',
    bool(m) and m.group(1) == '1230',
    f'got {m.group(1) if m else "missing"}')

# A2: v_Settlement_Day variable declared
chk('A2: v_Settlement_Day variable declared',
    bool(re.search(r'\bv_Settlement_Day\s*\(', clean, re.IGNORECASE)), '')

# A3: DayOfWeek=3 detection logic
chk('A3: DayOfWeek(Date)=3 detection logic',
    bool(re.search(
        r'v_Settlement_Day\s*=\s*\(\s*DayOfWeek\s*\(\s*Date\s*\)\s*=\s*3\s*\)',
        clean, re.IGNORECASE)), '')

# A4: DayOfMonth in [15,21] bounds
chk('A4: DayOfMonth in [15,21] bounds',
    bool(re.search(
        r'DayOfMonth\s*\(\s*Date\s*\)\s*>=\s*15\s*\)?\s+and\s*\(?\s*'
        r'DayOfMonth\s*\(\s*Date\s*\)\s*<=\s*21',
        clean, re.IGNORECASE)), '')

# A5: Settlement label in Priority 0 chain (SX_RPS_Settlement)
chk('A5: SX_RPS_Settlement label in Priority 0',
    'SX_RPS_Settlement' in raw and
    bool(re.search(
        r'v_Settlement_Day\s*=\s*True\s*\)\s*and\s*\(\s*'
        r'Time\s*>=\s*Settlement_Flat_Time', clean, re.IGNORECASE)), '')


# ===============================================================
# B. Rule #12 - SetStopLoss (5 checks)
# ===============================================================
print()
print('=' * 75)
print('B. Rule #12 - P3b SetStopLoss (5 checks)')
print('=' * 75)

setstoploss_calls = re.findall(r'\bSetStopLoss\s*\(', clean, re.IGNORECASE)

# B1: SetStopLoss exists
chk('B1: SetStopLoss exists', len(setstoploss_calls) >= 1,
    f'found {len(setstoploss_calls)} call(s)')

# B2: Called when MP >= 0 (short variant guard)
chk('B2: SetStopLoss gated by MarketPosition >= 0',
    bool(re.search(
        r'if\s+MarketPosition\s*>=\s*0\s+then\s+SetStopLoss\s*\(',
        clean, re.IGNORECASE)), '')

# B3: Distance uses SL_ATR_Mult * ATR * BigPointValue
chk('B3: SL formula = SL_ATR_Mult * ATR * BigPointValue',
    bool(re.search(
        r'SetStopLoss\s*\(\s*[^)]*SL_ATR_Mult[^)]*BigPointValue',
        clean, re.IGNORECASE)) or
    bool(re.search(
        r'SetStopLoss\s*\(\s*v_SL_ATR\s*\*\s*SL_ATR_Mult\s*\*\s*BigPointValue',
        clean, re.IGNORECASE)), '')

# B4: Single call only
chk('B4: Exactly one SetStopLoss call',
    len(setstoploss_calls) == 1, f'count={len(setstoploss_calls)}')

# B5: Active BEFORE the entry block.
# Section 5 (SetStopLoss) must appear before the SellShort entry line.
sl_idx = clean.lower().find('setstoploss')
entry_idx = clean.lower().find('sellshort')
chk('B5: SetStopLoss appears before SellShort entry',
    sl_idx > 0 and entry_idx > 0 and sl_idx < entry_idx,
    f'sl@{sl_idx} entry@{entry_idx}')


# ===============================================================
# C. Rule #13 - 10-dim eval readiness (3 checks)
# ===============================================================
print()
print('=' * 75)
print('C. Rule #13 - Inputs / Allocation / Header (3 checks)')
print('=' * 75)

# C1: All numeric thresholds are inputs - no hardcoded magic numbers
# in entry/exit *conditions*. Heuristic: scan the entry condition block
# and the exit chain for raw decimal literals that should be inputs
# (skip 0, 1, -1 - those are legitimate state values).
# We use a focused scan rather than a global one, since 1325/1345/500 are
# input-derived or absolute time bounds that the design intentionally hardcodes.
# Strategy: confirm every Tier 1 + Tier 2 + TP + SL parameter is referenced
# by its input name in the body (not as a literal).
required_inputs = [
    'Daily_FastMA_Len', 'Daily_SlowMA_Len', 'Daily_RSI_Len',
    'Daily_RSI_Threshold', 'Daily_RSI_Sustained_Bars', 'Daily_Dist_MA20_Pct',
    'Consec_Red_Bars', 'EMA_Fast_Len', 'ATR_Short_Len', 'ATR_Long_Len',
    'ATR_Spike_Mult', 'Pullback_Min_Pct', 'Pullback_Max_Pct',
    'TP_Pct', 'TP_MA_Len', 'SL_ATR_Len', 'SL_ATR_Mult', 'Max_Bars_TimeStop',
    'Entry_Open_Time', 'Entry_Cutoff_Time', 'Daily_Flat_Time',
]
missing_inputs = [n for n in required_inputs
                  if not re.search(rf'\b{n}\b', clean)]
chk('C1: All ~21 thresholds are PowerLanguage inputs (used by name)',
    len(missing_inputs) == 0,
    'missing: ' + ','.join(missing_inputs) if missing_inputs else 'all present')

# C2: Allocation % and sample target documented in header (raw, comments kept)
has_alloc_doc = (
    re.search(r'L4\s*Disposition.*Retire\s*L4.*3\s*%', raw, re.IGNORECASE | re.DOTALL) is not None
    or re.search(r'S3\s*gets\s*the\s*slot', raw, re.IGNORECASE) is not None
)
chk('C2: Allocation % documented (D6 - S3 gets 3% slot)',
    has_alloc_doc, '')

# C3: Reference to portfolio_allocation_v3 / design_spec_v2 in header
has_spec_ref = (
    'design_spec_v2' in raw or
    'portfolio_allocation_v3' in raw or
    'S3_PullbackShort_design_spec_v2' in raw or
    'S3_RapidPullbackShort_strategy' in raw
)
chk('C3: Header references design_spec_v2 / strategy.md',
    has_spec_ref, '')


# ===============================================================
# D. Entry logic correctness (10 checks)
# ===============================================================
print()
print('=' * 75)
print('D. Entry logic (10 checks)')
print('=' * 75)

# D1: Tier 1 Regime Gate = A AND (B OR C)
chk('D1: Regime A AND (B OR C)',
    bool(re.search(
        r'v_Trend_OK\s+and\s*\(\s*v_RSI_OK\s+or\s+v_Dist_OK\s*\)',
        clean, re.IGNORECASE)), '')

# D2: M1 consecutive red bars (loop or chain)
chk('D2: M1 consecutive red bars via loop',
    bool(re.search(
        r'for\s+v_red_idx\s*=\s*0\s+to\s+Consec_Red_Bars\s*-\s*1',
        clean, re.IGNORECASE)) and
    bool(re.search(
        r'Close\s*\[\s*v_red_idx\s*\]\s*>=\s*Open\s*\[\s*v_red_idx\s*\]',
        clean, re.IGNORECASE)), '')

# D3: M2 below EMA5 AND EMA5 declining
chk('D3: M2 Close<EMA AND EMA slope<0',
    bool(re.search(
        r'\(\s*Close\s*<\s*v_5M_EMA\s*\)\s*and\s*\(\s*v_5M_EMA\s*<\s*v_5M_EMA_Prev\s*\)',
        clean, re.IGNORECASE)), '')

# D4: M3 ATR spike ratio
chk('D4: M3 ATR_Short > ATR_Long * ATR_Spike_Mult',
    bool(re.search(
        r'v_5M_ATR_Short\s*>\s*v_5M_ATR_Long\s*\*\s*ATR_Spike_Mult',
        clean, re.IGNORECASE)), '')

# D5: M4 pullback band
chk('D5: M4 pullback in [Pullback_Min_Pct, Pullback_Max_Pct]',
    bool(re.search(
        r'v_Pullback_Pct\s*>=\s*Pullback_Min_Pct', clean, re.IGNORECASE)) and
    bool(re.search(
        r'v_Pullback_Pct\s*<=\s*Pullback_Max_Pct', clean, re.IGNORECASE)), '')

# D6: Entry combines regime + trigger + P0 gates + MP=0
entry_block = re.search(
    r'if\s*\(\s*MarketPosition\s*=\s*0\s*\)[^;]*?SellShort',
    clean, re.IGNORECASE | re.DOTALL)
combined_ok = False
if entry_block:
    blk = entry_block.group(0)
    combined_ok = all(
        re.search(p, blk, re.IGNORECASE) for p in [
            r'v_Regime_Watch\s*=\s*True',
            r'v_Trigger_Fired\s*=\s*True',
            r'Time\s*>=\s*Entry_Open_Time',
            r'Time\s*<=\s*Entry_Cutoff_Time',
            r'v_DailyCooldown_Active\s*=\s*False',
            r'v_Holiday_Block\s*=\s*False',
            r'v_Settlement_Day\s*=\s*False',
            r'v_Registry_Expired\s*=\s*False',
        ])
chk('D6: Entry combines 4M + regime + window + P0 gates', combined_ok, '')

# D7: Entry window 08:45 - 12:30
m_open = re.search(r'Entry_Open_Time\s*\(\s*(\d+)\s*\)', clean)
m_cut = re.search(r'Entry_Cutoff_Time\s*\(\s*(\d+)\s*\)', clean)
chk('D7: Entry window default 0845-1230',
    bool(m_open) and bool(m_cut) and
    m_open.group(1) == '845' and m_cut.group(1) == '1230',
    f'open={m_open.group(1) if m_open else "?"} '
    f'cut={m_cut.group(1) if m_cut else "?"}')

# D8: Same-day cooldown checked in entry
chk('D8: Same-day cooldown in entry condition',
    bool(re.search(
        r'v_DailyCooldown_Active\s*=\s*False', clean, re.IGNORECASE)), '')

# D9: SellShort with SE_RPS_Entry label
chk('D9: SellShort uses SE_RPS_Entry label',
    bool(re.search(
        r'SellShort\s*\(\s*"SE_RPS_Entry"\s*\)', clean)), '')

# D10: next bar at Market
chk('D10: Entry is "next bar at Market"',
    bool(re.search(
        r'SellShort\s*\([^)]*\)\s*next\s+bar\s+at\s+Market',
        clean, re.IGNORECASE)), '')


# ===============================================================
# E. Exit logic correctness (10 checks)
# ===============================================================
print()
print('=' * 75)
print('E. Exit logic (10 checks)')
print('=' * 75)

# E1: Priority 0 chain order
exit_block = clean[clean.lower().find('if marketposition = -1'):]
order_ok = True
priorities = [
    ('Manual_Kill_Switch', 'SX_RPS_Kill'),
    ('v_Registry_Expired', 'SX_RPS_RegistryEnd'),
    ('v_Holiday_Block', 'SX_RPS_HolFlat'),
    ('v_Settlement_Day', 'SX_RPS_Settlement'),
    ('Daily_Flat_Time', 'SX_RPS_DayClose'),
]
prev_idx = -1
order_detail = []
for cond, lbl in priorities:
    idx = exit_block.find(lbl)
    order_detail.append(f'{lbl}@{idx}')
    if idx < 0 or idx < prev_idx:
        order_ok = False
    prev_idx = idx
chk('E1: P0 chain order Kill>Registry>Holiday>Settlement>DayClose',
    order_ok, ' '.join(order_detail))

# E2: All five P0 exit labels present
e2_labels = ['SX_RPS_Kill', 'SX_RPS_RegistryEnd', 'SX_RPS_HolFlat',
             'SX_RPS_Settlement', 'SX_RPS_DayClose']
missing_e2 = [l for l in e2_labels if l not in raw]
chk('E2: All 5 P0 exit labels present',
    not missing_e2, 'missing: ' + ','.join(missing_e2) if missing_e2 else '')

# E3: TP formula = EntryPrice * (1 - TP_Pct / 100)
chk('E3: TP formula = EntryPrice * (1 - TP_Pct/100)',
    bool(re.search(
        r'v_TP_Pct_Level\s*=\s*EntryPrice\s*\*\s*\(\s*1\s*-\s*TP_Pct\s*/\s*100\s*\)',
        clean, re.IGNORECASE)), '')

# E4: TP EMA20 backup gated by TP_Use_EMA20_Backup
chk('E4: TP EMA20 backup (TP_Use_EMA20_Backup gate)',
    bool(re.search(
        r'TP_Use_EMA20_Backup\s*=\s*True', clean, re.IGNORECASE)) and
    bool(re.search(
        r'Close\s*<=\s*v_TP_EMA20', clean, re.IGNORECASE)), '')

# E5: SL handled by SetStopLoss engine (no SellAtStop in exit block)
no_sellatstop = not bool(re.search(
    r'BuyToCover\s*\([^)]*\)\s*next\s+bar\s+at\s+\S+\s+Stop',
    clean, re.IGNORECASE))
chk('E5: SL handled by engine (no BuyToCover at Stop)',
    no_sellatstop, '')

# E6: Time stop = 24 bars (Max_Bars_TimeStop)
chk('E6: Time stop via v_Bars_Held >= Max_Bars_TimeStop',
    bool(re.search(
        r'v_Bars_Held\s*>=\s*Max_Bars_TimeStop', clean, re.IGNORECASE)) and
    bool(re.search(
        r'Max_Bars_TimeStop\s*\(\s*24\s*\)', clean, re.IGNORECASE)), '')

# E7: ExitFired guard prevents double-trigger
exit_fired_guards = len(re.findall(
    r'ExitFired\s*=\s*0', clean, re.IGNORECASE))
chk('E7: ExitFired guard (>=5 occurrences across P0 chain)',
    exit_fired_guards >= 5, f'{exit_fired_guards} guards')

# E8: Daily flat 13:25 strict (Time >= Daily_Flat_Time, default 1325)
m_df = re.search(r'Daily_Flat_Time\s*\(\s*(\d+)\s*\)', clean)
chk('E8: Daily_Flat_Time = 1325',
    bool(m_df) and m_df.group(1) == '1325',
    f'got {m_df.group(1) if m_df else "?"}')

# E9: BuyToCover with SX_RPS_* labels (mirror Short exits)
btc_labels = re.findall(r'BuyToCover\s*\(\s*"(SX_RPS_[A-Za-z]+)"', clean)
chk('E9: BuyToCover uses SX_RPS_* labels (>=6 exits)',
    len(btc_labels) >= 6, f'{len(btc_labels)} BuyToCover calls')

# E10: No explicit "Sell at Stop" / "SellShort ... Stop" in exit logic
no_explicit_stop = not bool(re.search(
    r'\b(Sell|BuyToCover)\b[^;\n]*\bat\b[^;\n]*\bStop\b',
    clean, re.IGNORECASE))
chk('E10: No explicit Sell/BuyToCover ... at ... Stop',
    no_explicit_stop, '')


# ===============================================================
# F. Time safety - closed-interval audit (5 checks)
# ===============================================================
print()
print('=' * 75)
print('F. Time safety (closed-interval, 5 checks)')
print('=' * 75)

# F1: Time <= 500 used for Holiday tail detection
chk('F1: Time <= 500 for Holiday tail scan',
    bool(re.search(r'Time\s*<=\s*500', clean, re.IGNORECASE)), '')

# F2: Time >= Holiday_Flat_Time paired with v_Holiday_Block guard
chk('F2: Time >= Holiday_Flat_Time guarded by v_Holiday_Block',
    bool(re.search(
        r'v_Holiday_Block\s*=\s*True\s*\)\s*and\s*\(\s*Time\s*>=\s*Holiday_Flat_Time',
        clean, re.IGNORECASE)), '')

# F3: Time >= Settlement_Flat_Time paired with v_Settlement_Day guard
chk('F3: Time >= Settlement_Flat_Time guarded by v_Settlement_Day',
    bool(re.search(
        r'v_Settlement_Day\s*=\s*True\s*\)\s*and\s*\(\s*Time\s*>=\s*Settlement_Flat_Time',
        clean, re.IGNORECASE)), '')

# F4: Time >= Daily_Flat_Time has no upper bound BUT position-state guards
# (MP = -1 surrounds the whole block); we also accept the pla's explicit
# pairing with Time <= 1345 as a stricter form.
chk('F4: Daily_Flat_Time inside MP=-1 block AND paired with Time <= 1345',
    bool(re.search(
        r'Time\s*>=\s*Daily_Flat_Time\s*\)\s*and\s*\(\s*Time\s*<=\s*1345',
        clean, re.IGNORECASE)) and
    'if MarketPosition = -1' in clean, '')

# F5: No isolated Time >= X without state/upper-bound.
# Scan every "Time >= X" occurrence and verify it satisfies one of:
#   (a) followed by "and ... Time <= Y" within ~120 chars
#   (b) preceded by a state guard variable (v_Holiday_Block / v_Settlement_Day / MP)
isolated = []
for mt in re.finditer(r'Time\s*>=\s*(\w+)', clean, re.IGNORECASE):
    span_start = max(0, mt.start() - 200)
    span_end = min(len(clean), mt.end() + 200)
    window = clean[span_start:span_end]
    has_upper = bool(re.search(r'Time\s*<=', window, re.IGNORECASE))
    has_state = bool(re.search(
        r'v_Holiday_Block|v_Settlement_Day|MarketPosition\s*=\s*-1',
        window, re.IGNORECASE))
    if not (has_upper or has_state):
        isolated.append(mt.group(0))
chk('F5: No isolated Time>=X without state/upper-bound',
    not isolated, 'isolated: ' + ','.join(isolated) if isolated else '')


# ===============================================================
# G. Volume safety (1 check)
# ===============================================================
print()
print('=' * 75)
print('G. Volume safety (1 check)')
print('=' * 75)

# G1: No Volume reference in entry/exit logic (S2 v0.4 lesson)
# Search the comment-stripped body for the bare token 'Volume'.
# Allow 'BigPointValue' and other matches; use word boundary on Volume.
vol_refs = re.findall(r'\bVolume\b', clean)
chk('G1: No bare Volume reference in code',
    len(vol_refs) == 0, f'{len(vol_refs)} hits')


# ===============================================================
# H. Filter redundancy check (3 checks)
# ===============================================================
print()
print('=' * 75)
print('H. Filter redundancy (3 checks)')
print('=' * 75)

# H1: Header documents the orthogonality of M1..M4 (orthogonal / redundant words)
h1_ok = (
    re.search(r'orthogonal', raw, re.IGNORECASE) is not None
    and re.search(r'M1\.\.M4', raw) is not None
)
chk('H1: Header justifies M1..M4 orthogonality', h1_ok, '')

# H2: No filter is subset of another - mention of "Filter_Redundancy" rule
chk('H2: Header references Filter_Redundancy lesson rule',
    bool(re.search(r'Filter_Redundancy|FILTER REDUNDANCY',
                   raw)), '')

# H3: Pass rate / expected behavior documented somewhere in header
chk('H3: Expected behavior / counts documented (WATCH days, trade count)',
    bool(re.search(r'5\s*days/month|25-40\s*trades', raw, re.IGNORECASE)) or
    bool(re.search(r'Expected\s+WATCH|target\s+WR', raw, re.IGNORECASE)), '')


# ===============================================================
# I. Same-day cooldown (3 checks)
# ===============================================================
print()
print('=' * 75)
print('I. Same-day cooldown (3 checks)')
print('=' * 75)

# I1: variable exists
chk('I1: v_DailyCooldown_Active variable declared',
    bool(re.search(r'v_DailyCooldown_Active\s*\(', clean, re.IGNORECASE)), '')

# I2: Set true after exit
chk('I2: v_DailyCooldown_Active set True on exit',
    bool(re.search(
        r'if\s+ExitFired\s*>\s*0\s+then[^;]*v_DailyCooldown_Active\s*=\s*True',
        clean, re.IGNORECASE | re.DOTALL)), '')

# I3: Cleared on new date
chk('I3: Cooldown cleared when Date changes',
    bool(re.search(
        r'if\s+Date\s*<>\s*v_LastSeenDate\s+then[^;]*v_DailyCooldown_Active\s*=\s*False',
        clean, re.IGNORECASE | re.DOTALL)), '')


# ===============================================================
# J. Label convention (5 checks)
# ===============================================================
print()
print('=' * 75)
print('J. Label conventions (5 checks)')
print('=' * 75)

# J1: SE_RPS_Entry
chk('J1: SE_RPS_Entry short-entry label present',
    'SE_RPS_Entry' in raw, '')

# J2: SX_RPS_TP / TimeStop / DayClose
j2_labels = ['SX_RPS_TP', 'SX_RPS_TimeStop', 'SX_RPS_DayClose']
missing_j2 = [l for l in j2_labels if l not in raw]
chk('J2: SX_RPS_{TP,TimeStop,DayClose} present',
    not missing_j2, 'missing: ' + ','.join(missing_j2) if missing_j2 else '')

# J3: SX_RPS_Kill / RegistryEnd / HolFlat / Settlement
j3_labels = ['SX_RPS_Kill', 'SX_RPS_RegistryEnd',
             'SX_RPS_HolFlat', 'SX_RPS_Settlement']
missing_j3 = [l for l in j3_labels if l not in raw]
chk('J3: SX_RPS_{Kill,RegistryEnd,HolFlat,Settlement} present',
    not missing_j3, 'missing: ' + ','.join(missing_j3) if missing_j3 else '')

# J4: No Long-side labels (LE_/LX_)
long_labels = re.findall(r'\b(LE_|LX_)\w+', clean)
chk('J4: No Long-side labels (Short-only strategy)',
    not long_labels, ','.join(set(long_labels)) if long_labels else '')

# J5: RPS prefix used consistently - every SE_/SX_ label must contain RPS
mismatched = []
for m in re.finditer(r'"(S[EX]_[A-Za-z_]+)"', clean):
    lbl = m.group(1)
    if '_RPS_' not in lbl:
        mismatched.append(lbl)
chk('J5: RPS prefix used consistently on all SE_/SX_ labels',
    not mismatched, ','.join(set(mismatched)) if mismatched else '')


# ===============================================================
# K. Other completeness (10 checks)
# ===============================================================
print()
print('=' * 75)
print('K. Other completeness (10 checks)')
print('=' * 75)

# K1: IntrabarOrderGeneration = false
chk('K1: [IntrabarOrderGeneration = false] directive present',
    bool(re.search(
        r'\[\s*IntrabarOrderGeneration\s*=\s*false\s*\]',
        raw, re.IGNORECASE)), '')

# K2: Holiday_Tail registry has 63 valid entries
reg = {int(i): int(v) for i, v in
       re.findall(r'Holiday_Tail\s*\[\s*(\d+)\s*\]\s*=\s*(\d+)', clean)}
chk('K2: Holiday_Tail registry has 63 entries',
    len(reg) == 63, f'got {len(reg)}')

# K3: Init via "if CurrentBar = 1 then"
chk('K3: Init guard "if CurrentBar = 1 then"',
    bool(re.search(r'if\s+CurrentBar\s*=\s*1\s+then',
                   clean, re.IGNORECASE)), '')

# K4: Three data feeds referenced (Data1/Data2/Data3 - at least Data1 and Data3)
data_feeds = set(re.findall(r'\bof\s+(Data[123])\b', clean, re.IGNORECASE))
# Normalize case
data_feeds_norm = set(d.lower() for d in data_feeds)
# Header must also describe all three
header_three = (
    re.search(r'Data1\s*=\s*5M', raw, re.IGNORECASE) is not None
    and re.search(r'Data2\s*=\s*60M', raw, re.IGNORECASE) is not None
    and re.search(r'Data3\s*=\s*Daily', raw, re.IGNORECASE) is not None
)
chk('K4: Three data feeds wired (Data3 used in code + all three in header)',
    'data3' in data_feeds_norm and header_three,
    f'feeds_used={sorted(data_feeds_norm)} header_3={header_three}')

# K5: Registry_Valid_Until present
chk('K5: Registry_Valid_Until input present',
    bool(re.search(r'Registry_Valid_Until\s*\(\s*\d+\s*\)',
                   clean, re.IGNORECASE)), '')

# K6: Manual_Kill_Switch present
chk('K6: Manual_Kill_Switch input present',
    bool(re.search(r'Manual_Kill_Switch\s*\(\s*\w+\s*\)',
                   clean, re.IGNORECASE)), '')

# K7: HighConviction logging input present (D8)
chk('K7: Log_HighConviction + HighConv_Threshold_Pct inputs',
    bool(re.search(r'Log_HighConviction\s*\(', clean, re.IGNORECASE)) and
    bool(re.search(r'HighConv_Threshold_Pct\s*\(', clean, re.IGNORECASE)), '')

# K8: Header changelog has CREATED date + version line
chk('K8: Header has Version + CREATED date',
    bool(re.search(r'Version\s*:\s*v1\.0', raw, re.IGNORECASE)) and
    bool(re.search(r'CREATED\s+2026-06-20', raw, re.IGNORECASE)), '')

# K9: Lesson reminders in header (Time pitfall / Filter redundancy / Volume)
k9_ok = all(
    re.search(p, raw, re.IGNORECASE) for p in [
        r'CLOSED TIME INTERVALS|MC_Time_24hr',
        r'FILTER REDUNDANCY|Filter_Redundancy',
        r'VOLUME SIGNAL DROPPED|S2 v0\.4 lesson',
    ])
chk('K9: All three lesson reminders in header', k9_ok, '')

# K10: All ~25-30 inputs documented with inline comments.
# Use raw text (comments preserved) and slice from `inputs:` to the first
# top-level semicolon that is NOT inside a {...} comment. Then count
# decl lines of the form `Name ( default )` and inline {comments} on
# the same physical line.
k10_ok = False
k10_detail = 'inputs block not found'
m_start = re.search(r'\binputs\s*:', raw, re.IGNORECASE)
if m_start:
    start = m_start.end()
    depth = 0
    end = None
    for i in range(start, len(raw)):
        c = raw[i]
        if c == '{':
            depth += 1
        elif c == '}':
            if depth > 0:
                depth -= 1
        elif c == ';' and depth == 0:
            end = i
            break
    if end is not None:
        body = raw[start:end + 1]
        # Per physical line: does it declare an input AND carry a {comment}?
        total_inputs = 0
        with_comment = 0
        for line in body.splitlines():
            if re.match(r'\s*\w+\s*\(\s*[^()]*\)\s*[,;]', line):
                total_inputs += 1
                if '{' in line and '}' in line:
                    with_comment += 1
        k10_ok = total_inputs >= 25 and with_comment >= total_inputs * 0.7
        k10_detail = f'total={total_inputs} with_comment={with_comment}'
chk('K10: >=25 inputs, >=70% have inline {comment}', k10_ok, k10_detail)


# ===============================================================
# SUMMARY
# ===============================================================
print()
print('=' * 75)
passed = sum(1 for _, ok in results if ok)
total = len(results)
status = 'PASS' if passed == total else 'FAIL'
print(f'TOTAL: {passed}/{total} {status}')
if passed != total:
    print()
    print('Failed checks:')
    for n, ok in results:
        if not ok:
            print(f'  - {n}')
print('=' * 75)
sys.exit(0 if passed == total else 1)
