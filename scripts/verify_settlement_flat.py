"""Verify the Settlement_Flat module (CLAUDE.md Rule #11) on every
in-service strategy.

Detection rule: 3rd Wed of month = DayOfWeek(Date)=3 AND DayOfMonth in [15,21].
Each strategy must carry all 7 elements:

  1. Settlement_Flat_Time(1230) input
  2. v_Settlement_Day variable declared
  3. DayOfWeek(Date)=3 detection logic
  4. DayOfMonth in [15,21] bounds
  5. A Priority-0 settlement EXIT order emitting a *_Settlement* label
  6. Entry blocked on settlement day
  7. That exit gated by Time >= Settlement_Flat_Time

WHAT CHANGED 2026-08-04
-----------------------
The previous version hard-coded a dict of 6 pre-refactor paths plus their
expected exit labels. After the 2026-07-26 folder refactor every path was
stale, the first open() raised FileNotFoundError and the script died at
exit 1 without checking anything. It also never covered S3_L / S3_S /
S3_RPS / S16_S at all. This version:

  * takes its file list from scripts/strategy_discovery.py (no paths here)
  * DERIVES each exit label from the file itself instead of comparing
    against a hard-coded table
  * is FAIL-CLOSED: an unreadable file marks all 7 elements FAIL for that
    strategy and the run continues. Nothing is ever silently skipped and
    nothing crashes.
  * asserts coverage: strategies discovered must equal strategies checked,
    and live/ + live_simulation/ must each yield at least one strategy.

A structural failure (coverage gap / empty deployed tier) exits 1 even
WITHOUT --strict. Element failures follow the usual --strict convention,
matching verify_pla_ascii.py.

Usage:
  python scripts/verify_settlement_flat.py            # report
  python scripts/verify_settlement_flat.py --strict   # exit 1 on any FAIL
"""
import os
import re
import sys
import io
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategy_discovery as discovery  # noqa: E402

REPO_ROOT = discovery.REPO_ROOT

EXPECTED_FLAT_TIME = '1230'
ELEMENTS_PER_STRATEGY = 7

# --------------------------------------------------------------------------
# Patterns.  All are applied to the COMMENT-STRIPPED source so that prose
# and commented-out code cannot satisfy a check.
# --------------------------------------------------------------------------

RE_FLAT_TIME_DECL = re.compile(
    r'Settlement_Flat_Time\s*\(\s*(\d+)\s*\)', re.IGNORECASE)

RE_VAR_DECL = re.compile(
    r'\bv_Settlement_Day\s*\(', re.IGNORECASE)

RE_DETECTION = re.compile(
    r'v_Settlement_Day\s*=\s*\(\s*DayOfWeek\s*\(\s*Date\s*\)\s*=\s*3\s*\)',
    re.IGNORECASE)

RE_DAY_BOUNDS = re.compile(
    r'DayOfMonth\s*\(\s*Date\s*\)\s*>=\s*15[\s\)]*and[\s\(]*'
    r'DayOfMonth\s*\(\s*Date\s*\)\s*<=\s*21',
    re.IGNORECASE)

# Any order statement carrying a quoted label that contains "Settlement".
# The verb is captured so entry orders can be told from exit orders.
RE_SETTLEMENT_ORDER = re.compile(
    r'\b(?P<verb>buy\s+to\s+cover|buytocover|sell\s+short|sellshort|buy|sell)\b'
    r'\s*\(\s*"(?P<label>[^"]*Settlement[^"]*)"\s*\)',
    re.IGNORECASE)

# Verbs that CLOSE a position.  "buy" and "sell short" OPEN one.
EXIT_VERBS = ('buy to cover', 'buytocover', 'sell')

RE_ENTRY_BLOCK_FLAG = re.compile(
    r'v_Settlement_Day\s*=\s*false', re.IGNORECASE)

RE_ENTRY_BLOCK_GATEVAR = re.compile(
    r'if\s+v_Settlement_Day\s*(?:=\s*True\s*)?then\s+'
    r'v_\w*(?:Allow|Entry|Block|Trade)\w*\s*=\s*(?:false|true)',
    re.IGNORECASE)

RE_TIME_GATE = re.compile(
    r'Time\s*>=\s*Settlement_Flat_Time', re.IGNORECASE)


def _norm_verb(verb):
    return re.sub(r'\s+', ' ', verb.strip().lower())


def derive_settlement_exits(clean):
    """Derive the strategy's own settlement exit labels from its source.

    Returns (exit_labels, entry_labels).  Nothing is hard-coded: whatever
    label the file actually emits from a closing order is what gets
    reported.  L5 legitimately emits more than one (_Bot / _Mid).
    """
    exits, entries = [], []
    for m in RE_SETTLEMENT_ORDER.finditer(clean):
        verb = _norm_verb(m.group('verb'))
        label = m.group('label')
        bucket = exits if verb in EXIT_VERBS else entries
        if label not in bucket:
            bucket.append(label)
    return exits, entries


def check_strategy(pf):
    """Run the 7 Rule #11 element checks on one PlaFile.

    Returns a list of (element_id, description, ok, detail).  Never raises:
    an unreadable file yields 7 FAILs with the read error as the detail.
    """
    if pf.raw is None:
        reason = 'file unreadable: %s' % pf.read_error
        return [(i, 'element %d not evaluated' % i, False, reason)
                for i in range(1, ELEMENTS_PER_STRATEGY + 1)]

    clean = pf.clean
    results = []

    # 1 - Settlement_Flat_Time(1230) input.
    times = RE_FLAT_TIME_DECL.findall(clean)
    ok1 = EXPECTED_FLAT_TIME in times
    results.append((1, 'Settlement_Flat_Time(1230) input', ok1,
                    'got %s' % (', '.join(times) if times else 'missing')))

    # 2 - v_Settlement_Day variable declared.
    ok2 = bool(RE_VAR_DECL.search(clean))
    results.append((2, 'v_Settlement_Day variable declared', ok2,
                    '' if ok2 else 'no "v_Settlement_Day (" declaration'))

    # 3 - DayOfWeek(Date)=3 detection logic.
    ok3 = bool(RE_DETECTION.search(clean))
    results.append((3, 'DayOfWeek(Date)=3 detection logic', ok3,
                    '' if ok3 else 'assignment from DayOfWeek(Date)=3 not found'))

    # 4 - DayOfMonth in [15,21] bounds.
    ok4 = bool(RE_DAY_BOUNDS.search(clean))
    results.append((4, 'DayOfMonth in [15,21] bounds', ok4,
                    '' if ok4 else '>=15 and <=21 bounds not found'))

    # 5 - Settlement exit label, DERIVED from the file (never hard-coded).
    exits, entries = derive_settlement_exits(clean)
    ok5 = bool(exits)
    if ok5:
        detail5 = 'derived: %s' % ', '.join('"%s"' % e for e in exits)
    elif entries:
        detail5 = ('only OPENING orders carry a Settlement label (%s) - no '
                   'closing order found' % ', '.join('"%s"' % e for e in entries))
    else:
        detail5 = ('no closing order emits a *Settlement* label; searched '
                   'buy-to-cover / sell with a quoted label')
    results.append((5, 'Priority-0 settlement exit label emitted', ok5, detail5))

    # 6 - Entry blocked on settlement day.
    by_flag = bool(RE_ENTRY_BLOCK_FLAG.search(clean))
    by_gate = bool(RE_ENTRY_BLOCK_GATEVAR.search(clean))
    ok6 = by_flag or by_gate
    if by_flag and by_gate:
        detail6 = 'via "v_Settlement_Day = false" gate + allow-flag'
    elif by_flag:
        detail6 = 'via "v_Settlement_Day = false" in entry condition'
    elif by_gate:
        detail6 = 'via allow-flag cleared on settlement day'
    else:
        detail6 = 'entry is NOT gated on v_Settlement_Day'
    results.append((6, 'Entry blocked on settlement day', ok6, detail6))

    # 7 - Exit gated by Time >= Settlement_Flat_Time.
    ok7 = bool(RE_TIME_GATE.search(clean))
    results.append((7, 'Exit gated by Time >= Settlement_Flat_Time', ok7,
                    '' if ok7 else '"Time >= Settlement_Flat_Time" not found'))

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Verify Settlement_Flat module (CLAUDE.md Rule #11)')
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 if any element fails (CI mode)')
    args = parser.parse_args()

    all_deployed = discovery.discover_deployed(REPO_ROOT,
                                               include_indicators=True)
    strategies = [p for p in all_deployed if p.is_strategy()]
    indicators = [p for p in all_deployed if not p.is_strategy()]
    discovered = len(strategies)

    print('=' * 78)
    print('Settlement_Flat Module Verifier  (CLAUDE.md Rule #11)')
    print('Scope: strategies/live + live_simulation (excl. archive, indicators)')
    print('Discovery: scripts/strategy_discovery.py')
    print('=' * 78)
    for line in discovery.format_tier_counts(all_deployed,
                                             discovery.DEPLOYED_TIERS):
        print(line)
    print('  %-16s %3d strategies under Rule #11' % ('DISCOVERED', discovered))
    if indicators:
        print('  excluded as indicators (Rule #11 N/A):')
        for p in indicators:
            print('      %s' % p.rel)
    print('=' * 78)

    structural = []
    for tier in discovery.empty_deployed_tiers(all_deployed):
        structural.append(
            'deployed tier "%s" matched ZERO .pla files - discovery is broken '
            '(2026-07-26 silent-failure signature)' % tier)

    disc_warnings = discovery.collect_warnings(all_deployed)
    if disc_warnings:
        print()
        print('DISCOVERY WARNINGS (%d):' % len(disc_warnings))
        for w in disc_warnings:
            print('  ! %s' % w)

    checked = 0
    element_pass = 0
    element_total = 0
    failing_strategies = []

    for pf in strategies:
        key = os.path.splitext(pf.name)[0]
        print()
        print('=== %s (%s) ===' % (key, pf.rel))
        results = check_strategy(pf)
        checked += 1
        strat_fail = 0
        for eid, desc, ok, detail in results:
            element_total += 1
            if ok:
                element_pass += 1
            else:
                strat_fail += 1
            tag = '[OK  ]' if ok else '[FAIL]'
            suffix = (': %s' % detail) if detail else ''
            print('  %s %s-%d: %s%s' % (tag, key, eid, desc, suffix))
        if strat_fail:
            failing_strategies.append((key, strat_fail))
            print('  -> %d/%d elements FAILED' % (strat_fail, len(results)))

    if checked != discovered:
        structural.append(
            'COVERAGE GAP: discovered %d strategies but checked %d'
            % (discovered, checked))

    print()
    print('=' * 78)
    print('COVERAGE: discovered %d / checked %d  ->  %s'
          % (discovered, checked, 'OK' if checked == discovered else 'FAIL'))
    if element_total:
        print('ELEMENTS: %d/%d OK (%.0f%%)'
              % (element_pass, element_total,
                 100.0 * element_pass / element_total))
    else:
        print('ELEMENTS: 0/0 - NOTHING WAS CHECKED')
        structural.append('no strategy was checked at all')
    print('STRATEGIES: %d/%d fully compliant'
          % (checked - len(failing_strategies), checked))
    print('=' * 78)

    if failing_strategies:
        print()
        print('Rule #11 NOT satisfied by:')
        for key, n in failing_strategies:
            print('  * %s (%d/%d elements failed)'
                  % (key, n, ELEMENTS_PER_STRATEGY))
        print('See docs/policies/SETTLEMENT_DAY_DESIGN_CONSTITUTION.md')

    if structural:
        print()
        print('!' * 78)
        print('STRUCTURAL FAILURE - the verifier cannot vouch for its own scope.')
        for s in structural:
            print('  * %s' % s)
        print('Fix scripts/strategy_discovery.py before trusting any result above.')
        print('!' * 78)
        sys.exit(1)

    if failing_strategies and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    # Force UTF-8 stdout (Windows consoles default to cp950).  Kept inside
    # the __main__ guard so importing this module has no global side effects.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')
    main()
