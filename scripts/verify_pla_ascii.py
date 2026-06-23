"""Verify all .pla files in active strategies/ folders are 100% ASCII.

CLAUDE.md Rule #15: MC PowerLanguage tolerates UTF-8 inconsistently across
builds. To guarantee compile success, all .pla files MUST be pure ASCII
(no Chinese, no em dash, no math symbols, no emoji).

Scan scope:
  strategies/live/*.pla
  strategies/live_simulation/*.pla
  strategies/research/**/*.pla
  (EXCLUDES archive/ - killed strategies frozen as historical record)

Usage:
  python scripts/verify_pla_ascii.py            # report all
  python scripts/verify_pla_ascii.py --strict   # exit 1 if any fail (CI mode)
"""
import os
import sys
import io
import glob
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_file(path):
    """Return list of (lineno, col, char, codepoint) for non-ASCII chars."""
    findings = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for lineno, line in enumerate(f, 1):
            for col, ch in enumerate(line, 1):
                if ord(ch) > 127:
                    findings.append((lineno, col, ch, ord(ch)))
    return findings


def find_active_pla_files():
    """Discover all .pla files in active (non-archive) strategy folders."""
    patterns = [
        os.path.join(REPO_ROOT, 'strategies', 'live', '*.pla'),
        os.path.join(REPO_ROOT, 'strategies', 'live_simulation', '*.pla'),
        os.path.join(REPO_ROOT, 'strategies', 'research', '**', '*.pla'),
    ]
    files = set()
    for pat in patterns:
        for f in glob.glob(pat, recursive=True):
            if os.sep + 'archive' + os.sep in f:
                continue
            files.add(os.path.normpath(f))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description='Verify .pla files are pure ASCII')
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 if any file fails (CI mode)')
    parser.add_argument('--detail', action='store_true',
                        help='Print every non-ASCII char location')
    args = parser.parse_args()

    files = find_active_pla_files()

    print('=' * 78)
    print(f'PLA ASCII Compliance Scanner  (CLAUDE.md Rule #15)')
    print(f'Scope: strategies/live + live_simulation + research (excl. archive)')
    print(f'Files scanned: {len(files)}')
    print('=' * 78)
    print()

    pass_count = 0
    fail_count = 0
    fail_files = []

    for path in files:
        rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, '/')
        findings = scan_file(path)
        if findings:
            fail_count += 1
            fail_files.append((rel, findings))
            print(f'  [FAIL] {rel}: {len(findings)} non-ASCII chars')
            if args.detail:
                for lineno, col, ch, code in findings[:10]:
                    print(f'         L{lineno} C{col}: U+{code:04X} "{ch}"')
                if len(findings) > 10:
                    print(f'         ... +{len(findings) - 10} more')
        else:
            pass_count += 1
            print(f'  [PASS] {rel}')

    print()
    print('=' * 78)
    print(f'RESULT: {pass_count}/{len(files)} PASS, {fail_count}/{len(files)} FAIL')
    print('=' * 78)

    if fail_count > 0:
        print()
        print('Per CLAUDE.md Rule #15, all .pla files MUST be 100% ASCII.')
        print('Run with --detail for per-character locations.')
        print()
        print('Common fixes:')
        print('  Chinese text       -> English translation')
        print('  em dash "-"        -> ASCII hyphen "-"')
        print('  arrow ->            -> "->"')
        print('  multiply x          -> "x"')
        print('  >= sign             -> ">="')
        print('  emoji / check mark  -> "[PASS]" / "[OK]" / remove')

    if args.strict and fail_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
