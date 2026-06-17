"""
verify_range_force_exit.py (INVERTED 2026-06-17)
RangeForceExit 模組已被回滾 — 此腳本現在驗證「所有策略都不含 RangeForceExit」.

歷史:
  v13.3/v14.3 嘗試在 L3/L4 加入 RangeForceExit (Constitution v1.1 Clause 7)
  v13.3.1/v14.3.1 hotfix 加入時段上界
  v13.4/v14.4 完全回滾, 因實盤 L4 績效轉負 + 概念尚未充分驗證.

詳見 docs/range_force_exit_rollback_20260617.md.

未來重新設計 RangeForceExit 時, 此腳本應改為「正向驗證」.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path

BASE = Path('C:/Users/User/Desktop/TXF1-Strategy-Lab/strategies')

ALL_STRATEGIES = [
    ('L1', 'live/L1_TrendLong.pla'),
    ('L2', 'live/L2_TrendShort.pla'),
    ('L3', 'live/L3_ConsolidationLong.pla'),
    ('L4', 'live/L4_ConsolidationShort.pla'),
    ('L5', 'live/L5_BreakoutLong.pla'),
    ('S1', 'live_simulation/S1_NightMomentum.pla'),
]

FORBIDDEN_TOKENS = [
    'Range_ForceExit_Time',
    'Range_ForceExit_End',
    'CL_RangeForceExit',
    'CS_RangeForceExit',
    'BL_RangeForceExit',
    'TL_RangeForceExit',
    'TS_RangeForceExit',
    'NM_RangeForceExit',
]


print('=' * 80)
print('RangeForceExit ROLLBACK Verification (no strategy should contain it)')
print('=' * 80)
print()

all_pass = True
results = []

for sid, path in ALL_STRATEGIES:
    fp = BASE / path
    text = fp.read_text(encoding='utf-8', errors='replace')

    # Strip comment blocks for fair check: PowerLanguage uses { } for comments.
    # We keep the changelog references (which mention rollback) but flag any
    # live code or live input that uses the forbidden tokens.
    # Simple heuristic: flag the token unless every occurrence is in a comment.
    flagged = []
    for token in FORBIDDEN_TOKENS:
        if token in text:
            # Check if every occurrence is inside { ... } comment block
            in_code = False
            i = 0
            depth = 0
            while i < len(text):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth = max(0, depth - 1)
                elif depth == 0 and text[i:i+len(token)] == token:
                    in_code = True
                    break
                i += 1
            if in_code:
                flagged.append(token)

    if flagged:
        all_pass = False
        print(f'  [FAIL] {sid}: live code/input still references: {flagged}')
        results.append((sid, False, flagged))
    else:
        print(f'  [OK  ] {sid}: clean (any mentions are in comments only)')
        results.append((sid, True, []))

print()
print('=' * 80)
passed = sum(1 for _, ok, _ in results if ok)
print(f'TOTAL: {passed}/{len(results)} clean')
if all_pass:
    print('Rollback verified - no live RangeForceExit code in any strategy.')
else:
    print('*** ROLLBACK INCOMPLETE - live code still contains RangeForceExit ***')
    sys.exit(1)
