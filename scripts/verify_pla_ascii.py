"""Verify all .pla files in active strategies/ folders are 100% ASCII.

CLAUDE.md Rule #15: MC PowerLanguage tolerates UTF-8 inconsistently across
builds. To guarantee compile success, all .pla files MUST be pure ASCII
(no Chinese, no em dash, no math symbols, no emoji).

Scan scope comes from scripts/strategy_discovery.py (single source of truth):
  strategies/live/**/*.pla
  strategies/live_simulation/**/*.pla
  strategies/research/**/*.pla
  (EXCLUDES archive/ - killed strategies frozen as historical record)
  (EXCLUDES *.bak* - backups are not compiled)

STRUCTURAL GUARDS (added 2026-08-04 after a 9-day silent failure)
-----------------------------------------------------------------
Before the refactor of 2026-07-26 this script used non-recursive globs for
live/ and live_simulation/. After the refactor it matched ZERO deployed
strategies, printed "36/36 PASS" and exited 0 while a real Rule #15
violation sat in strategies/live/. Two guards now make that impossible:

  G1 COVERAGE ASSERTION - the number of files DISCOVERED must equal the
     number of files actually SCANNED. Any gap is a FAIL.
  G2 DEPLOYED-TIER FLOOR - if live/ or live_simulation/ yields zero files,
     that is a FAIL regardless of how many research files passed.

A structural failure (G1/G2) exits 1 even WITHOUT --strict: a gatekeeper
that cannot see its own subjects must never be able to report success.
Content failures (non-ASCII chars) follow the usual --strict convention.

Usage:
  python scripts/verify_pla_ascii.py            # report all
  python scripts/verify_pla_ascii.py --strict   # exit 1 if any fail (CI mode)
  python scripts/verify_pla_ascii.py --detail   # per-character locations
"""
import os
import sys
import io
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategy_discovery as discovery  # noqa: E402

REPO_ROOT = discovery.REPO_ROOT


def scan_file(path):
    """Scan one file for non-ASCII characters.

    Returns (findings, error) where findings is a list of
    (lineno, col, char, codepoint) and error is None on success or a
    string describing why the file could not be read.
    """
    findings = []
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for lineno, line in enumerate(f, 1):
                for col, ch in enumerate(line, 1):
                    if ord(ch) > 127:
                        findings.append((lineno, col, ch, ord(ch)))
    except (IOError, OSError) as exc:
        return [], '%s: %s' % (type(exc).__name__, exc)
    return findings, None


def main():
    parser = argparse.ArgumentParser(description='Verify .pla files are pure ASCII')
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 if any file fails (CI mode)')
    parser.add_argument('--detail', action='store_true',
                        help='Print every non-ASCII char location')
    args = parser.parse_args()

    files = discovery.discover_strategies(REPO_ROOT)
    discovered = len(files)

    print('=' * 78)
    print('PLA ASCII Compliance Scanner  (CLAUDE.md Rule #15)')
    print('Scope: strategies/live + live_simulation + research (excl. archive)')
    print('Discovery: scripts/strategy_discovery.py')
    print('=' * 78)
    for line in discovery.format_tier_counts(files):
        print(line)
    print('  %-16s %3d files' % ('DISCOVERED', discovered))
    print('=' * 78)
    print()

    structural = []

    # G2 - deployed-tier floor.
    for tier in discovery.empty_deployed_tiers(files):
        structural.append(
            'deployed tier "%s" matched ZERO .pla files - discovery is broken '
            '(this is the exact 2026-07-26 silent-failure signature)' % tier)

    disc_warnings = discovery.collect_warnings(files)
    if disc_warnings:
        print('DISCOVERY WARNINGS (%d):' % len(disc_warnings))
        for w in disc_warnings:
            print('  ! %s' % w)
        print()

    pass_count = 0
    fail_count = 0
    scanned = 0

    for pf in files:
        rel = pf.rel
        findings, error = scan_file(pf.path)
        if error is not None:
            fail_count += 1
            print('  [FAIL] %s: UNREADABLE - %s' % (rel, error))
            continue
        scanned += 1
        if findings:
            fail_count += 1
            print('  [FAIL] %s: %d non-ASCII chars' % (rel, len(findings)))
            shown = findings if args.detail else findings[:10]
            for lineno, col, ch, code in shown:
                print('         L%d C%d: U+%04X "%s"' % (lineno, col, code, ch))
            if not args.detail and len(findings) > 10:
                print('         ... +%d more (use --detail)' % (len(findings) - 10))
        else:
            pass_count += 1
            print('  [PASS] %s' % rel)

    # G1 - coverage assertion.
    if scanned != discovered:
        structural.append(
            'COVERAGE GAP: discovered %d files but only scanned %d '
            '(%d file(s) could not be read)'
            % (discovered, scanned, discovered - scanned))

    print()
    print('=' * 78)
    print('COVERAGE: discovered %d / scanned %d  ->  %s'
          % (discovered, scanned,
             'OK' if scanned == discovered else 'FAIL'))
    print('RESULT:   %d/%d PASS, %d/%d FAIL'
          % (pass_count, discovered, fail_count, discovered))
    print('=' * 78)

    if structural:
        print()
        print('!' * 78)
        print('STRUCTURAL FAILURE - the scanner cannot vouch for its own scope.')
        for s in structural:
            print('  * %s' % s)
        print('Fix scripts/strategy_discovery.py before trusting any result above.')
        print('!' * 78)

    if fail_count > 0:
        print()
        print('Per CLAUDE.md Rule #15, all .pla files MUST be 100% ASCII.')
        print('Run with --detail for per-character locations.')
        print()
        print('Common fixes:')
        print('  Chinese text        -> English translation')
        print('  em dash             -> ASCII hyphen "-"')
        print('  arrow               -> "->"')
        print('  multiply sign U+00D7-> "x"')
        print('  U+2265 sign         -> ">="')
        print('  emoji / check mark  -> "[PASS]" / "[OK]" / remove')

    if structural:
        sys.exit(1)
    if args.strict and fail_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    # Windows consoles default to cp950 here; --detail prints the offending
    # non-ASCII characters, so force UTF-8 on stdout.  Kept inside the
    # __main__ guard so importing this module has no global side effects.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')
    main()
