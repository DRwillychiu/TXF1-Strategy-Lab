"""Single source of truth for the TXF1 calendar risk module.

WHY THIS MODULE EXISTS
----------------------
Ten strategies each carry their own hand-typed copy of the Holiday_Tail
registry.  A 2026-08-04 audit confirmed all ten copies are byte-identical to
one another -- and that this proves nothing, because they share the same
holes.  Cross-checked against TAIFEX official data, the shared table was
missing 13 real market closures, one of which (2021-04-30 Labour Day) is an
ordinary annual holiday sitting inside the backtest window.

The fix is generation-time sharing (rules handbook D-1, NOT a PowerLanguage
User Function): data/taifex_market_closures.json is the only place a date is
ever written by a human, every .pla block is generated from it, and this
module asserts that every copy still matches.

REGISTRY SEMANTICS
------------------
Holiday_Tail = the calendar date stamped on the 00:00-05:00 tail bars of the
last night session before a market closure = last trading day + 1 day.

That semantics rests on a fact verified against TAIFEX official quotes: the
after-hours row of trade date T is the session that ran from the PREVIOUS
trading day 15:00 to T 05:00.  The eve-of-closure night session therefore
always runs; it is simply booked to the first business day after the closure.
See data/taifex_market_closures.json -> session_fact.

USAGE
-----
  python scripts/taifex_calendar.py --list
  python scripts/taifex_calendar.py --verify            # compare every .pla copy
  python scripts/taifex_calendar.py --emit L1_TrendLong # generated .pla block

EXIT CODES
----------
  0  everything matched
  1  a registry copy disagrees with the source, OR a structural failure
     (source unreadable, zero files discovered, coverage mismatch).
     Structural failures exit 1 unconditionally -- a gatekeeper that cannot
     see its own scope must never report success (rules handbook D-4).
"""
import argparse
import datetime
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategy_discovery  # noqa: E402

REPO_ROOT = strategy_discovery.REPO_ROOT
SOURCE_PATH = os.path.join(REPO_ROOT, 'data', 'taifex_market_closures.json')

REGISTRY_RE = re.compile(r'Holiday_Tail\[(\d+)\]\s*=\s*(\d+)\s*;')
ARRAY_DECL_RE = re.compile(r'Holiday_Tail\[(\d+)\]\s*\(')


# --------------------------------------------------------------------------
# Date helpers (PowerLanguage stores dates as YYYMMDD, YYY = year - 1900)
# --------------------------------------------------------------------------

def to_mc(d):
    return (d.year - 1900) * 10000 + d.month * 100 + d.day


def from_mc(n):
    n = int(n)
    return datetime.date(1900 + n // 10000, (n // 100) % 100, n % 100)


# --------------------------------------------------------------------------
# Source of truth
# --------------------------------------------------------------------------

def load_source(path=SOURCE_PATH):
    """Load the closure list.  Any failure here is structural."""
    if not os.path.isfile(path):
        raise SystemExit('STRUCTURAL: calendar source not found: %s' % path)
    with io.open(path, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    rows = doc.get('closed_weekdays')
    if not rows:
        raise SystemExit('STRUCTURAL: calendar source has no closed_weekdays')
    closed = {}
    for r in rows:
        d = datetime.date(*map(int, r['date'].split('-')))
        if d.weekday() >= 5:
            raise SystemExit(
                'STRUCTURAL: %s is a weekend; closed_weekdays must hold '
                'business days only' % r['date'])
        closed[d] = r
    return doc, closed


def coverage(doc):
    """Return (start, end) of the window the source can speak for."""
    ch = doc['evidence_channels']
    lo = min(datetime.date(*map(int, ch[k]['covers'][0].split('-'))) for k in ch)
    hi = max(datetime.date(*map(int, ch[k]['covers'][1].split('-'))) for k in ch)
    return lo, hi


# --------------------------------------------------------------------------
# Derivation
# --------------------------------------------------------------------------

def trading_days(closed, start, end):
    out = []
    d = start
    step = datetime.timedelta(days=1)
    while d <= end:
        if d.weekday() < 5 and d not in closed:
            out.append(d)
        d += step
    return out


def holiday_tails(closed, start, end):
    """Derive the Holiday_Tail list.

    One entry per closure block that swallows at least one business day.
    Ordinary weekends are NOT registry entries -- they are handled by each
    strategy's own weekend rule (e.g. L5's Saturday 04:00 flat).
    """
    days = trading_days(closed, start, end)
    out = []
    for a, b in zip(days, days[1:]):
        gap = (b - a).days
        if gap <= 1:
            continue
        skipped = [a + datetime.timedelta(days=k) for k in range(1, gap)]
        if not any(x.weekday() < 5 for x in skipped):
            continue  # plain weekend
        out.append({
            'tail': a + datetime.timedelta(days=1),
            'last_trading_day': a,
            'reopen': b,
            'closed_business_days': [x for x in skipped if x.weekday() < 5],
        })
    return out


# --------------------------------------------------------------------------
# .pla registry copies
# --------------------------------------------------------------------------

def read_registry(pla):
    """Return (ordered list of MC ints, declared array size) or (None, None)."""
    raw = pla.raw
    if raw is None:
        return None, None
    if 'Holiday_Tail' not in raw:
        return None, None
    entries = {}
    for m in REGISTRY_RE.finditer(raw):
        entries[int(m.group(1))] = int(m.group(2))
    if not entries:
        return None, None
    size = None
    m = ARRAY_DECL_RE.search(raw)
    if m:
        size = int(m.group(1))
    idx = sorted(entries)
    if idx != list(range(1, len(idx) + 1)):
        raise SystemExit(
            'STRUCTURAL: %s has non-contiguous Holiday_Tail indices' % pla.rel)
    return [entries[i] for i in idx], size


def discover_registry_files():
    files = strategy_discovery.discover_strategies(REPO_ROOT)
    out = []
    for p in files:
        raw = p.raw
        if raw is not None and REGISTRY_RE.search(raw):
            out.append(p)
    return files, out


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------

def emit_block(tails, indent='    '):
    """Render the .pla assignment block.  100% ASCII (Rule #15)."""
    lines = []
    year = None
    for i, t in enumerate(tails, 1):
        d = t['tail']
        ref = t['last_trading_day']
        if ref.year != year:
            year = ref.year
            lines.append('')
            lines.append('%s{ --- %d --- }' % (indent, year))
        n = len(t['closed_business_days'])
        lines.append(
            '%sHoliday_Tail[%-2d] = %d;  { last trade %s, %d business day%s shut, '
            'reopen %s }'
            % (indent, i, to_mc(d), ref.isoformat(), n, '' if n == 1 else 's',
               t['reopen'].isoformat()))
    return '\n'.join(lines).lstrip('\n')


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_list(doc, closed, args):
    lo, hi = coverage(doc)
    tails = holiday_tails(closed, lo, hi)
    print('=' * 78)
    print('Derived Holiday_Tail registry')
    print('source window : %s .. %s' % (lo, hi))
    print('entries       : %d' % len(tails))
    print('=' * 78)
    for i, t in enumerate(tails, 1):
        flag = 'adhoc' if any(
            closed[x]['channel'] == 'adhoc' for x in t['closed_business_days']
        ) else '     '
        print('  [%2d] %d  %s  %s  last trade %s -> reopen %s'
              % (i, to_mc(t['tail']), t['tail'], flag,
                 t['last_trading_day'], t['reopen']))
    return 0


def cmd_emit(doc, closed, args):
    lo, hi = coverage(doc)
    print(emit_block(holiday_tails(closed, lo, hi)))
    return 0


def cmd_verify(doc, closed, args):
    lo, hi = coverage(doc)
    all_files, reg_files = discover_registry_files()

    print('=' * 78)
    print('Holiday_Tail Registry Verifier')
    print('Source : %s' % os.path.relpath(SOURCE_PATH, REPO_ROOT).replace(os.sep, '/'))
    print('Window : %s .. %s' % (lo, hi))
    print('=' * 78)
    for line in strategy_discovery.format_tier_counts(all_files):
        print(line)
    print('  %-16s %3d files carry a Holiday_Tail registry' % ('REGISTRY', len(reg_files)))
    print('=' * 78)
    print()

    empty = strategy_discovery.empty_deployed_tiers(all_files)
    if empty:
        print('STRUCTURAL ERROR: deployed tier(s) matched zero files: %s'
              % ', '.join(empty))
        return 1
    if not reg_files:
        print('STRUCTURAL ERROR: zero files carry a Holiday_Tail registry.')
        return 1

    expected = [to_mc(t['tail']) for t in holiday_tails(closed, lo, hi)]
    checked = 0
    failed = []
    for p in reg_files:
        got, size = read_registry(p)
        checked += 1
        if got is None:
            failed.append((p.rel, 'registry unreadable'))
            print('  [FAIL] %s  registry unreadable' % p.rel)
            continue
        # a copy may legitimately start later than the source window; compare
        # on the intersection, then report anything the source has and the
        # copy does not.
        got_set, exp_set = set(got), set(expected)
        first = min(got) if got else None
        in_scope = {v for v in exp_set if first is None or v >= first}
        missing = sorted(in_scope - got_set)
        # An entry dated past the source window is forward cover the source
        # cannot speak for yet (next year's calendar is published in Q4).
        # Report it, but do not call it an error.
        hi_mc = to_mc(hi)
        beyond = sorted(v for v in got_set - exp_set if v > hi_mc)
        extra = sorted(v for v in got_set - exp_set if v <= hi_mc)
        for v in beyond:
            print('  [NOTE] %s  entry %d (%s) is past the source window %s; '
                  'not verifiable until that year is published'
                  % (p.rel, v, from_mc(v), hi))
        if size is not None and len(expected) > size:
            failed.append((p.rel, 'array size %d < %d entries' % (size, len(expected))))
            print('  [FAIL] %s  Holiday_Tail[%d] too small for %d entries'
                  % (p.rel, size, len(expected)))
            continue
        if missing or extra:
            failed.append((p.rel, '%d missing / %d unknown' % (len(missing), len(extra))))
            print('  [FAIL] %s  %d entries; missing %d, unknown %d'
                  % (p.rel, len(got), len(missing), len(extra)))
            if args.detail:
                for v in missing:
                    print('           missing %d  %s' % (v, from_mc(v)))
                for v in extra:
                    print('           unknown %d  %s' % (v, from_mc(v)))
        else:
            print('  [PASS] %s  %d entries' % (p.rel, len(got)))

    print()
    print('=' * 78)
    print('COVERAGE: registry files %d / checked %d  ->  %s'
          % (len(reg_files), checked, 'OK' if checked == len(reg_files) else 'MISMATCH'))
    print('RESULT:   %d/%d PASS, %d FAIL'
          % (len(reg_files) - len(failed), len(reg_files), len(failed)))
    print('=' * 78)
    if checked != len(reg_files):
        return 1
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--list', action='store_true', help='print the derived registry')
    g.add_argument('--verify', action='store_true', help='check every .pla copy')
    g.add_argument('--emit', action='store_true', help='print the generated .pla block')
    ap.add_argument('--detail', action='store_true',
                    help='print every differing entry, not just the counts')
    args = ap.parse_args()

    doc, closed = load_source()
    if args.list:
        return cmd_list(doc, closed, args)
    if args.emit:
        return cmd_emit(doc, closed, args)
    return cmd_verify(doc, closed, args)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')
    sys.exit(main())
