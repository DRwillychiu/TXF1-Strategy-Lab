"""Verify S3_RapidPullbackShort.pla v1.1 against all design+constitution checks.

Pattern: mirrors verify_settlement_flat.py / verify_all_live.py style.
Target : strategies/research/S03_PullbackShort/S3_RapidPullbackShort.pla

Check groups (total ~86):
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
  L. PL function existence + v1.0.1 bug-fix audit      (8) <-- added 2026-06-19
  M. v1.1 patch behavior verification                  (18) <-- added 2026-06-19

Output: per-check OK/FAIL lines + final TOTAL: X/86.
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

# D7: Entry window 08:50 - 12:30 (v1.1 bumped 845->850 per #16 bar-stamp)
m_open = re.search(r'Entry_Open_Time\s*\(\s*(\d+)\s*\)', clean)
m_cut = re.search(r'Entry_Cutoff_Time\s*\(\s*(\d+)\s*\)', clean)
chk('D7: Entry window default 0850-1230 (v1.1 bar-stamp aware)',
    bool(m_open) and bool(m_cut) and
    m_open.group(1) == '850' and m_cut.group(1) == '1230',
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

# E5: SL has BOTH engine SetStopLoss AND Frozen SL backup (v1.1 #10 belt-and-suspenders)
# v1.0 used engine only; v1.1 added explicit BuyToCover at v_SL_Level Stop as backup
has_engine = bool(re.search(r'\bSetStopLoss\s*\(', clean, re.IGNORECASE))
has_backup = bool(re.search(
    r'BuyToCover\s*\(\s*"SX_RPS_SL"[^)]*\)\s*next\s+bar\s+at\s+v_SL_Level\s+Stop',
    clean, re.IGNORECASE))
chk('E5: SL has BOTH engine SetStopLoss AND Frozen SL backup (v1.1)',
    has_engine and has_backup,
    f'engine={has_engine} backup={has_backup}')

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

# E10: Exit "at Stop" orders limited to v1.1 Frozen SL backup only
# (no rogue Sell at Stop / SellShort at Stop elsewhere)
all_stop_orders = [m.group(0) for m in re.finditer(
    r'\b(?:Sell|BuyToCover)\b[^;\n]*\bat\b[^;\n]*\bStop\b',
    clean, re.IGNORECASE)]
# All matches must contain v_SL_Level (the Frozen SL backup is the only legit one)
stop_orders_ok = all('v_SL_Level' in m for m in all_stop_orders) if all_stop_orders else True
chk('E10: All "at Stop" orders use Frozen SL v_SL_Level (v1.1 only legit)',
    stop_orders_ok, f'found {len(all_stop_orders)} stop order(s)')


# ===============================================================
# F. Time safety - closed-interval audit (5 checks)
# ===============================================================
print()
print('=' * 75)
print('F. Time safety (closed-interval, 5 checks)')
print('=' * 75)

# F1: Time < 500 (strict) for Holiday tail detection (v1.1 #2 fix)
# Original v1.0 used <= 500 which allowed cross-holiday fill on Time=500 bar
chk('F1: Time < 500 (strict) for Holiday tail scan (v1.1)',
    bool(re.search(r'Time\s*<\s*500\b', clean, re.IGNORECASE)) and
    not bool(re.search(r'Time\s*<=\s*500\b', clean, re.IGNORECASE)), '')

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

# F4: Time >= Daily_Flat_Time paired with Time <= 1340 (v1.1 #3 fix - was 1345)
# 1340 prevents fill at 15:00 night open across 1h15m gap
chk('F4: Daily_Flat_Time inside MP=-1 block AND paired with Time <= 1340 (v1.1)',
    bool(re.search(
        r'Time\s*>=\s*Daily_Flat_Time\s*\)\s*and\s*\(\s*Time\s*<=\s*1340',
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

# I3: Cleared on new date AT day-session-open (v1.1 #8 split-cadence fix)
# v1.1 changed reset gate to nested: Date<>LastSeenDate AND Time>=Entry_Open_Time
# (prevents premature reset at 00:00 night-session bar before entry window opens)
chk('I3: Cooldown cleared when Date changes AND Time>=Entry_Open_Time (v1.1)',
    bool(re.search(
        r'if\s+Date\s*<>\s*v_LastSeenDate\s+then\s+begin'
        r'.*?if\s+Time\s*>=\s*Entry_Open_Time\s+then\s+begin'
        r'.*?v_DailyCooldown_Active\s*=\s*False',
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

# K8: Header changelog has Version v1.1 + CREATED date + UPDATED line
chk('K8: Header has Version v1.1 + CREATED + UPDATED date',
    bool(re.search(r'Version\s*:\s*v1\.[01]', raw, re.IGNORECASE)) and
    bool(re.search(r'CREATED\s+2026-06-2[0-9]', raw, re.IGNORECASE)) and
    bool(re.search(r'UPDATED\s+2026-06-\d+\s*\(v1\.1\)', raw, re.IGNORECASE)), '')

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
# L. PowerLanguage function existence + bug-fix verification (8 checks)
#
# Added 2026-06-19 after user caught LastBarOnChart_Ex(0) — a non-existent
# PowerLanguage function that the original verify_s3 (60 checks) missed
# because it only checked structural patterns, not function legitimacy.
# This group enforces:
#   - blacklist of known-invalid PL function names
#   - presence of the snapshot-based Daily RSI fix (v1.0.1)
# ===============================================================
print()
print('=' * 75)
print('L. PL function existence + v1.0.1 bug-fix audit (8 checks)')
print('=' * 75)

# L1: LastBarOnChart_Ex must NOT be used in EXECUTABLE code (compile blocker)
# Use `clean` (comments stripped) - mentions inside {bug-fix comments} are OK.
chk('L1: LastBarOnChart_Ex NOT in executable code (non-existent PL function)',
    'LastBarOnChart_Ex' not in clean,
    '' if 'LastBarOnChart_Ex' not in clean
    else 'found - MC will fail to compile - use LastBarOnChart instead')

# L2: blacklist of other known non-existent PL functions (executable only)
BAD_PL_FUNCTIONS = [
    'LastBarOnChart_Ex', 'LastBarOnChart_ex', 'lastbaronchart_ex',
    'IsFirstBarOfDay',  # not standard PL
    'GetSymbolName_s',  # not standard
    'BarStatus_Ex',     # not standard
    'IntrabarPersist_Ex',  # not standard
]
found_bad = [fn for fn in BAD_PL_FUNCTIONS if fn in clean]
chk('L2: no other non-existent PL functions (executable)',
    not found_bad,
    'found: ' + ', '.join(found_bad) if found_bad else 'clean')

# L3: snapshot variables declared (v_Daily_RSI_Snap0..3) for sustained-fix
snap_decls = sum(1 for i in range(4)
                 if re.search(rf'v_Daily_RSI_Snap{i}\s*\(', clean, re.IGNORECASE))
chk('L3: v_Daily_RSI_Snap0..3 snapshot vars declared (sustained-fix)',
    snap_decls == 4,
    f'found {snap_decls}/4 snapshot vars')

# L4: snapshot shift logic present in Section 4 (new-day boundary)
snap_shift_ok = (
    re.search(r'v_Daily_RSI_Snap3\s*=\s*v_Daily_RSI_Snap2', clean, re.IGNORECASE) and
    re.search(r'v_Daily_RSI_Snap2\s*=\s*v_Daily_RSI_Snap1', clean, re.IGNORECASE) and
    re.search(r'v_Daily_RSI_Snap1\s*=\s*v_Daily_RSI_Snap0', clean, re.IGNORECASE) and
    re.search(r'v_Daily_RSI_Snap0\s*=\s*RSI\s*\(\s*Close\s*,', clean, re.IGNORECASE)
)
chk('L4: snapshot shift logic at new-day boundary (Snap3<-2<-1<-0<-RSI)',
    bool(snap_shift_ok), '')

# L5: sustained loop NOT using Data1-indexed RSI(...)[hidx] anymore
bad_sustained = re.search(
    r'for\s+\w+\s*=\s*1\s+to\s+Daily_RSI_Sustained_Bars\s+begin\s*'
    r'.*?RSI\s*\([^)]*of\s+Data3[^)]*\)\s*\[\s*\w+\s*\]\s*<=',
    clean, re.IGNORECASE | re.DOTALL)
chk('L5: sustained check NOT using broken RSI(... of Data3)[hidx] pattern',
    bad_sustained is None,
    'found broken pattern (must use Snap0..3 instead)' if bad_sustained else 'OK')

# L6: sustained check uses snapshot vars (4 if-blocks for Snap0..3)
snap_check_blocks = sum(1 for i in range(4) if re.search(
    rf'Daily_RSI_Sustained_Bars\s*>=\s*{i+1}\s+and\s+'
    rf'v_Daily_RSI_Snap{i}\s*<=\s*Daily_RSI_Threshold',
    clean, re.IGNORECASE))
chk('L6: sustained check uses Snap0..3 blocks (4 if-tiers)',
    snap_check_blocks == 4,
    f'found {snap_check_blocks}/4 snapshot if-tiers')

# L7: v_Daily_RSI now reads from snapshot (not inline RSI(... of Data3)[1])
v_daily_rsi_assigns = re.findall(
    r'v_Daily_RSI\s*=\s*([^;]+?);', clean, re.IGNORECASE)
v_daily_rsi_ok = any('v_Daily_RSI_Snap0' in a for a in v_daily_rsi_assigns)
v_daily_rsi_bad = any(re.search(r'RSI\s*\(\s*Close\s+of\s+Data3', a, re.IGNORECASE)
                      for a in v_daily_rsi_assigns)
chk('L7: v_Daily_RSI reads from Snap0 (not broken RSI(... of Data3)[1])',
    v_daily_rsi_ok and not v_daily_rsi_bad,
    f'snap-read={v_daily_rsi_ok} broken-pattern={v_daily_rsi_bad}')

# L8: LastBarOnChart (correct bool keyword) usage if any logging present
# Either Print is gated by Date<>Date[1] (new-day) OR by LastBarOnChart
print_count = len(re.findall(r'\bPrint\s*\(', clean, re.IGNORECASE))
if print_count > 0:
    new_day_gate = bool(re.search(
        r'Date\s*<>\s*Date\s*\[\s*1\s*\]', clean, re.IGNORECASE))
    last_bar_gate = bool(re.search(
        r'\bLastBarOnChart\b(?!_)', clean))  # not followed by underscore
    chk('L8: Print gated by new-day (Date<>Date[1]) or LastBarOnChart',
        new_day_gate or last_bar_gate,
        f'new_day_gate={new_day_gate} last_bar_gate={last_bar_gate}')
else:
    chk('L8: no Print calls (logging removed)', True, 'no Print used')


# ===============================================================
# M. v1.1 patch behavior verification (18 checks)
#
# Added 2026-06-19. v1.1 introduced multi-data feed fixes, behavioral
# safeguards (frozen SL, TP_EMA20 guards, holiday/daily flat bounds),
# and architectural cleanups (DaySess high tracking, single-call EMA,
# explicit Data3 parentheses). This group enforces that the v1.0->v1.1
# patches landed correctly and didn't regress.
# ===============================================================
print()
print('=' * 75)
print('M. v1.1 patch behavior verification (18 checks)')
print('=' * 75)

# M1: v_Entry_Bar NOT used anywhere in executable code (replaced by BarsSinceEntry)
m1_hits = re.findall(r'\bv_Entry_Bar\b', clean)
chk('M1: v_Entry_Bar NOT in executable code (BarsSinceEntry replaces it)',
    len(m1_hits) == 0,
    f'{len(m1_hits)} hits' if m1_hits else 'clean')

# M2: BarsSinceEntry IS referenced in v_Bars_Held assignment
chk('M2: v_Bars_Held = BarsSinceEntry assignment present',
    bool(re.search(r'v_Bars_Held\s*=\s*BarsSinceEntry',
                   clean, re.IGNORECASE)), '')

# M3: Frozen SL variables declared (v_SL_Locked / v_Frozen_ATR_5M / v_SL_Level)
frozen_sl_vars = ['v_SL_Locked', 'v_Frozen_ATR_5M', 'v_SL_Level']
missing_m3 = [v for v in frozen_sl_vars
              if not re.search(rf'\b{v}\s*\(', clean, re.IGNORECASE)]
chk('M3: Frozen SL variables declared (v_SL_Locked/v_Frozen_ATR_5M/v_SL_Level)',
    not missing_m3,
    'missing: ' + ','.join(missing_m3) if missing_m3 else 'all 3 present')

# M4: Frozen SL backup exit fires SX_RPS_SL with "at v_SL_Level Stop"
chk('M4: Frozen SL backup BuyToCover SX_RPS_SL at v_SL_Level Stop',
    bool(re.search(
        r'BuyToCover\s*\(\s*"SX_RPS_SL"\s*\)[^;]*next\s+bar\s+at\s+v_SL_Level\s+Stop',
        clean, re.IGNORECASE)), '')

# M5: TP_EMA20_MinBars input present (HIGH #1 fix marker)
chk('M5: TP_EMA20_MinBars input present (HIGH #1 fix marker)',
    bool(re.search(r'TP_EMA20_MinBars\s*\(\s*\d+\s*\)',
                   clean, re.IGNORECASE)), '')

# M6: TP EMA20 backup guarded by 3 conditions
# (v_Bars_Held >= TP_EMA20_MinBars + v_5M_EMA20[1] < EntryPrice + Close[1] > v_5M_EMA20[1])
m6_minbars = bool(re.search(
    r'v_Bars_Held\s*>=\s*TP_EMA20_MinBars', clean, re.IGNORECASE))
m6_ema20_below = bool(re.search(
    r'v_5M_EMA20\s*\[\s*1\s*\]\s*<\s*EntryPrice', clean, re.IGNORECASE))
chk('M6: TP EMA20 backup guarded by MinBars + EMA20[1]<EntryPrice',
    m6_minbars and m6_ema20_below,
    f'minbars={m6_minbars} ema20_below={m6_ema20_below}')

# M7: Holiday block uses strict < 500 (NOT <= 500) -- wait, spec says
# "Time < 500 present AND Time <= 500 NOT present (in executable)".
# Re-read: the executable should use strict < 500 for the holiday tail check.
m7_strict_lt = bool(re.search(r'Time\s*<\s*500\b', clean))
m7_lte_present = bool(re.search(r'Time\s*<=\s*500\b', clean))
chk('M7: Holiday block uses Time < 500 (strict), no Time <= 500',
    m7_strict_lt and not m7_lte_present,
    f'strict_lt={m7_strict_lt} lte_present={m7_lte_present}')

# M8: P0-3 Holiday flat has upper bound (Time <= 455)
# Locate HolFlat block and confirm Time <= 455 appears within it.
m8_ok = False
hol_idx = clean.find('SX_RPS_HolFlat')
if hol_idx > 0:
    # examine a generous window around the HolFlat label
    window = clean[max(0, hol_idx - 400):hol_idx + 400]
    m8_ok = bool(re.search(r'Time\s*<=\s*455', window, re.IGNORECASE))
chk('M8: P0-3 HolFlat block contains Time <= 455 upper bound', m8_ok, '')

# M9: P0a Daily flat upper bound is 1340 (NOT 1345) -- check executable
day_close_idx = clean.find('SX_RPS_DayClose')
m9_ok = False
m9_detail = 'DayClose label not found'
if day_close_idx > 0:
    window = clean[max(0, day_close_idx - 400):day_close_idx + 400]
    has_1340 = bool(re.search(r'Time\s*<=\s*1340', window))
    has_1345 = bool(re.search(r'Time\s*<=\s*1345', window))
    m9_ok = has_1340 and not has_1345
    m9_detail = f'has_1340={has_1340} has_1345={has_1345}'
chk('M9: P0a DayClose block uses Time <= 1340 (not 1345)', m9_ok, m9_detail)

# M10: HighD(0) NOT referenced in pullback calc (replaced by v_DaySess_High)
highd0_hits = re.findall(r'HighD\s*\(\s*0\s*\)', clean, re.IGNORECASE)
v_daysess_present = bool(re.search(r'\bv_DaySess_High\b', clean, re.IGNORECASE))
chk('M10: No HighD(0) in executable + v_DaySess_High IS used',
    len(highd0_hits) == 0 and v_daysess_present,
    f'highd0_hits={len(highd0_hits)} daysess_present={v_daysess_present}')

# M11: v_DaySess_High + v_DaySess_HighDate variables declared
m11_vars = ['v_DaySess_High', 'v_DaySess_HighDate']
missing_m11 = [v for v in m11_vars
               if not re.search(rf'\b{v}\s*\(', clean, re.IGNORECASE)]
chk('M11: v_DaySess_High + v_DaySess_HighDate variables declared',
    not missing_m11,
    'missing: ' + ','.join(missing_m11) if missing_m11 else 'both declared')

# M12: Pullback calc uses v_DaySess_High (not HighD(0))
# Look for the v_Pullback_Pct assignment and confirm v_DaySess_High in denominator.
pullback_assign = re.search(
    r'v_Pullback_Pct\s*=\s*([^;]+);', clean, re.IGNORECASE)
m12_ok = False
m12_detail = 'v_Pullback_Pct assignment not found'
if pullback_assign:
    expr = pullback_assign.group(1)
    m12_ok = 'v_DaySess_High' in expr and 'HighD' not in expr
    m12_detail = f'uses_daysess={"v_DaySess_High" in expr} ' \
                 f'uses_highd={"HighD" in expr}'
chk('M12: Pullback calc uses v_DaySess_High in denominator', m12_ok, m12_detail)

# M13: ( Close of Data3 )[1] explicit parentheses pattern in Dist calc
chk('M13: (Close of Data3)[1] explicit parentheses pattern present',
    bool(re.search(
        r'\(\s*Close\s+of\s+Data3\s*\)\s*\[\s*1\s*\]',
        clean, re.IGNORECASE)), '')

# M14: XAverage called once (not twice) for EMA5 -- uses v_5M_EMA[1] for prev
# Count XAverage calls in proximity to v_5M_EMA assignment and check
# v_5M_EMA_Prev uses v_5M_EMA[1] (not a second XAverage call).
xavg_calls = re.findall(r'\bXAverage\s*\(', clean, re.IGNORECASE)
ema_prev_ok = bool(re.search(
    r'v_5M_EMA_Prev\s*=\s*v_5M_EMA\s*\[\s*1\s*\]',
    clean, re.IGNORECASE))
# spec: XAverage exactly 1 occurrence near v_5M_EMA
# (there may be other XAverage calls for EMA20 etc., so we focus
# on whether v_5M_EMA_Prev avoids a second XAverage call)
ema5_xavg_double = bool(re.search(
    r'v_5M_EMA_Prev\s*=\s*XAverage\s*\(', clean, re.IGNORECASE))
chk('M14: EMA5 XAverage called once + v_5M_EMA_Prev = v_5M_EMA[1]',
    ema_prev_ok and not ema5_xavg_double,
    f'prev_uses_subscript={ema_prev_ok} prev_calls_xavg={ema5_xavg_double} '
    f'total_xavg={len(xavg_calls)}')

# M15: Holiday_Flat_Time = 245 (spec compliance)
m_hft = re.search(r'Holiday_Flat_Time\s*\(\s*(\d+)\s*\)', clean)
chk('M15: Holiday_Flat_Time = 245',
    bool(m_hft) and m_hft.group(1) == '245',
    f'got {m_hft.group(1) if m_hft else "missing"}')

# M16: MC Load Name has S3_ infix
chk('M16: STRATEGY_GEN_S3_RapidPullbackShort load-name present',
    bool(re.search(r'STRATEGY_GEN_S3_RapidPullbackShort',
                   raw, re.IGNORECASE)), '')

# M17: Entry_Open_Time = 850 (bar-close-stamp aware)
m_eot = re.search(r'Entry_Open_Time\s*\(\s*(\d+)\s*\)', clean)
chk('M17: Entry_Open_Time = 850 (bar-close-stamp aware)',
    bool(m_eot) and m_eot.group(1) == '850',
    f'got {m_eot.group(1) if m_eot else "missing"}')

# M18: Cooldown reset gated by Time >= Entry_Open_Time inside Date<>LastSeenDate block
# Find the date-rollover block and confirm a nested
# "if Time >= Entry_Open_Time" exists within it.
date_block = re.search(
    r'if\s+Date\s*<>\s*v_LastSeenDate\s+then\s+begin([\s\S]*?)end\s*;',
    clean, re.IGNORECASE)
m18_ok = False
m18_detail = 'date-rollover block not found'
if date_block:
    body = date_block.group(1)
    m18_ok = bool(re.search(
        r'if\s+Time\s*>=\s*Entry_Open_Time',
        body, re.IGNORECASE))
    m18_detail = 'nested time-gate found' if m18_ok else 'no nested time-gate'
chk('M18: Cooldown reset gated by Time >= Entry_Open_Time in date-rollover',
    m18_ok, m18_detail)


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
