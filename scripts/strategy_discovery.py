"""Single source of truth for discovering active TXF1 strategy .pla files.

WHY THIS MODULE EXISTS
----------------------
The 2026-07-26 folder refactor moved every strategy into its own
sub-directory (strategies/live/L1_TrendLong/L1_TrendLong.pla).  Both
mandatory gatekeeper scripts had their own private file-discovery code and
both broke:

  * verify_pla_ascii.py       used NON-recursive globs for live/ and
                              live_simulation/.  After the refactor it
                              matched zero deployed strategies, yet still
                              printed "36/36 PASS" and exited 0.  A real
                              Rule #15 violation sat undetected for 9 days.
  * verify_settlement_flat.py used a hard-coded dict of 6 pre-refactor
                              paths.  After the refactor it crashed with
                              FileNotFoundError on the first file, and it
                              never covered S3_L / S3_S / S3_RPS / S16_S
                              at all.

Every discovery rule now lives here, exactly once.  Verification scripts
MUST import this module.  They MUST NOT write their own glob patterns.

DISCOVERY RULES
---------------
  include : *.pla found recursively under
              strategies/live/
              strategies/live_simulation/
              strategies/research/
  exclude : any path with an "archive" component (killed strategies are
            frozen as a historical record and are exempt from the rules)
  exclude : any file whose name contains ".bak"
  exclude : anything whose extension is not ".pla"

STRATEGY vs INDICATOR
---------------------
Rule #11 (Settlement_Flat) applies to strategies, not to indicators.  The
classifier uses TWO independent signals and never trusts just one:

  signal A (name) : basename starts with "IND_"
  signal B (code) : the comment-stripped source contains a PowerLanguage
                    order statement (buy / sell / sell short / buy to
                    cover ... next bar|this bar)

When the two signals agree, the file is classified silently.  When they
DISAGREE, the file is classified as a STRATEGY (so it stays inside the
Rule #11 net and fails loudly rather than being silently skipped) and a
warning is attached to it.  Callers are expected to surface warnings.

STANDALONE USE
--------------
  python scripts/strategy_discovery.py           # print the inventory
  python scripts/strategy_discovery.py --json    # machine-readable
"""
import os
import re
import sys
import io
import json
import argparse
from collections import OrderedDict

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# Tier name -> path components under the repo root.
TIER_DIRS = OrderedDict([
    ('live', ('strategies', 'live')),
    ('live_simulation', ('strategies', 'live_simulation')),
    ('research', ('strategies', 'research')),
])

ALL_TIERS = tuple(TIER_DIRS.keys())

# Tiers that are "in service" (deployed to a live or simulated account).
DEPLOYED_TIERS = ('live', 'live_simulation')

PLA_EXT = '.pla'
EXCLUDED_PATH_COMPONENT = 'archive'
EXCLUDED_NAME_TOKEN = '.bak'
INDICATOR_NAME_PREFIX = 'IND_'

KIND_STRATEGY = 'strategy'
KIND_INDICATOR = 'indicator'

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A PowerLanguage order statement: an order verb, then (within the same
# statement) an explicit bar reference.  Comments are stripped before this
# runs, so a verb mentioned in prose cannot match.
ORDER_STATEMENT_RE = re.compile(
    r'\b(?:buy\s+to\s+cover|buytocover|sell\s+short|sellshort|buy|sell)\b'
    r'[^;{}]{0,200}?'
    r'\b(?:next\s+bar|this\s+bar)\b',
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Source helpers
# --------------------------------------------------------------------------

def strip_comments(source):
    """Remove PowerLanguage brace comments, preserving character count.

    Comment bodies are replaced by spaces (newlines are kept) so that line
    numbers and offsets in the returned text still line up with the raw
    source.  Braces nest in PowerLanguage, so depth is tracked.
    """
    out = []
    depth = 0
    for ch in source:
        if ch == '{':
            depth += 1
            out.append(' ')
        elif ch == '}':
            if depth > 0:
                depth -= 1
            out.append(' ')
        elif depth > 0:
            out.append('\n' if ch == '\n' else ' ')
        else:
            out.append(ch)
    return ''.join(out)


def read_source(path):
    """Return (raw_text, error_message).  Never raises."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(), None
    except (IOError, OSError) as exc:
        return None, '%s: %s' % (type(exc).__name__, exc)


def has_order_statements(clean_source):
    """True if the comment-stripped source contains an order statement."""
    return bool(ORDER_STATEMENT_RE.search(clean_source))


# --------------------------------------------------------------------------
# Discovered-file record
# --------------------------------------------------------------------------

class PlaFile(object):
    """One discovered .pla file plus its classification and any warnings."""

    def __init__(self, path, repo_root, tier):
        self.path = os.path.normpath(path)
        self.repo_root = repo_root
        self.tier = tier
        self.name = os.path.basename(self.path)
        self.rel = os.path.relpath(self.path, repo_root).replace(os.sep, '/')
        self.kind = KIND_STRATEGY
        self.warnings = []
        self.read_error = None
        self._raw = None
        self._clean = None
        self._classify()

    # -- source access (read once, cached) ---------------------------------

    @property
    def raw(self):
        if self._raw is None and self.read_error is None:
            self._raw, self.read_error = read_source(self.path)
        return self._raw

    @property
    def clean(self):
        if self._clean is None:
            raw = self.raw
            self._clean = '' if raw is None else strip_comments(raw)
        return self._clean

    # -- classification ----------------------------------------------------

    def _classify(self):
        name_says_indicator = self.name.startswith(INDICATOR_NAME_PREFIX)

        raw = self.raw
        if raw is None:
            # Unreadable.  Fail CLOSED: keep it in the strategy net so the
            # callers report a FAIL instead of silently dropping the file.
            self.kind = KIND_STRATEGY
            self.warnings.append(
                'unreadable (%s) - classified as strategy so it cannot be '
                'silently skipped' % self.read_error)
            return

        code_says_strategy = has_order_statements(self.clean)

        if name_says_indicator and not code_says_strategy:
            self.kind = KIND_INDICATOR
        elif (not name_says_indicator) and code_says_strategy:
            self.kind = KIND_STRATEGY
        elif name_says_indicator and code_says_strategy:
            self.kind = KIND_STRATEGY
            self.warnings.append(
                'name/code mismatch: "%s" prefix says indicator but the file '
                'contains order statements - treated as STRATEGY'
                % INDICATOR_NAME_PREFIX)
        else:
            # No IND_ prefix and no order statements.  Could be an indicator
            # that was misnamed, or a strategy whose order logic was gutted.
            # Both need a human, so keep it in the strategy net.
            self.kind = KIND_STRATEGY
            self.warnings.append(
                'name/code mismatch: no "%s" prefix but no order statement '
                'found either - treated as STRATEGY (verify manually)'
                % INDICATOR_NAME_PREFIX)

    # -- misc --------------------------------------------------------------

    def is_strategy(self):
        return self.kind == KIND_STRATEGY

    def to_dict(self):
        return {
            'rel': self.rel,
            'tier': self.tier,
            'kind': self.kind,
            'warnings': list(self.warnings),
            'read_error': self.read_error,
        }

    def __repr__(self):
        return '<PlaFile %s tier=%s kind=%s>' % (self.rel, self.tier, self.kind)


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

def _is_excluded(path):
    """Apply the exclusion rules to an absolute path."""
    norm = path.replace('\\', '/')
    parts = norm.split('/')
    if any(p.lower() == EXCLUDED_PATH_COMPONENT for p in parts[:-1]):
        return True
    name = parts[-1]
    if EXCLUDED_NAME_TOKEN in name.lower():
        return True
    if os.path.splitext(name)[1].lower() != PLA_EXT:
        return True
    return False


def _walk_tier(repo_root, tier):
    """Yield absolute paths of surviving .pla files for one tier."""
    root = os.path.join(repo_root, *TIER_DIRS[tier])
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        # Do not descend into archive/ at all.
        dirnames[:] = [d for d in dirnames
                       if d.lower() != EXCLUDED_PATH_COMPONENT]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if not _is_excluded(full):
                yield full


def discover_strategies(repo_root=None, tiers=ALL_TIERS):
    """Discover every active .pla file (strategies AND indicators).

    Returns a list of PlaFile sorted by (tier order, relative path).
    """
    repo_root = os.path.abspath(repo_root or REPO_ROOT)
    found = []
    seen = set()
    for tier in tiers:
        if tier not in TIER_DIRS:
            raise ValueError('unknown tier: %r' % (tier,))
        for full in _walk_tier(repo_root, tier):
            key = os.path.normcase(os.path.normpath(full))
            if key in seen:
                continue
            seen.add(key)
            found.append(PlaFile(full, repo_root, tier))
    order = {t: i for i, t in enumerate(ALL_TIERS)}
    found.sort(key=lambda p: (order.get(p.tier, 99), p.rel.lower()))
    return found


def discover_deployed(repo_root=None, include_indicators=False):
    """Discover the in-service files: live/ + live_simulation/ only.

    By default indicators are excluded, because Rule #11 (Settlement_Flat)
    applies to strategies only.  Pass include_indicators=True to get the
    full deployed inventory.
    """
    files = discover_strategies(repo_root, tiers=DEPLOYED_TIERS)
    if include_indicators:
        return files
    return [p for p in files if p.is_strategy()]


# --------------------------------------------------------------------------
# Reporting helpers (shared by the verification scripts)
# --------------------------------------------------------------------------

def resolve(stem, repo_root=None, tiers=DEPLOYED_TIERS):
    """Repo-relative path of the deployed strategy whose filename stem matches.

    This exists so callers never hardcode a path.  The 2026-07-26 folder
    reorganisation silently broke every script that did, and the breakage went
    unnoticed for nine days because a missing file looked like a crash rather
    than a failed check.

    Fails LOUDLY on a miss: raises LookupError listing what was actually found.
    Never returns a guess.
    """
    want = stem[:-4] if stem.lower().endswith('.pla') else stem
    want = os.path.basename(want).lower()
    found = [f for f in discover_strategies(repo_root, tiers)
             if os.path.splitext(f.name)[0].lower() == want]
    if len(found) == 1:
        return found[0].rel
    if not found:
        avail = ', '.join(sorted(os.path.splitext(f.name)[0]
                                 for f in discover_strategies(repo_root, tiers)))
        raise LookupError('no deployed strategy named %r. found: %s' % (stem, avail))
    raise LookupError('%r is ambiguous: %s'
                      % (stem, ', '.join(f.rel for f in found)))


def group_by_tier(files):
    """Return OrderedDict tier -> [PlaFile], in canonical tier order."""
    groups = OrderedDict((t, []) for t in ALL_TIERS)
    for p in files:
        groups.setdefault(p.tier, []).append(p)
    return groups


def collect_warnings(files):
    """Return a flat list of 'rel: warning' strings."""
    out = []
    for p in files:
        for w in p.warnings:
            out.append('%s: %s' % (p.rel, w))
    return out


def empty_deployed_tiers(files):
    """Return the deployed tiers that produced ZERO files.

    A non-empty return value is the signature of the 2026-07-26 incident:
    discovery silently matching nothing while the caller reports success.
    """
    groups = group_by_tier(files)
    return [t for t in DEPLOYED_TIERS if not groups.get(t)]


def format_tier_counts(files, tiers=ALL_TIERS):
    """Return a list of 'tier: N files (S strategies, I indicators)' lines."""
    groups = group_by_tier(files)
    lines = []
    for tier in tiers:
        bucket = groups.get(tier, [])
        strategies = sum(1 for p in bucket if p.is_strategy())
        indicators = len(bucket) - strategies
        lines.append('  %-16s %3d files  (%d strategies, %d indicators)'
                     % (tier, len(bucket), strategies, indicators))
    return lines


# --------------------------------------------------------------------------
# Standalone inventory
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Inventory of active strategy .pla files')
    parser.add_argument('--json', action='store_true',
                        help='Emit machine-readable JSON')
    parser.add_argument('--deployed', action='store_true',
                        help='Only live + live_simulation strategies')
    args = parser.parse_args()

    if args.deployed:
        tiers = DEPLOYED_TIERS
        files = discover_deployed(REPO_ROOT, include_indicators=True)
    else:
        tiers = ALL_TIERS
        files = discover_strategies(REPO_ROOT)

    if args.json:
        print(json.dumps([p.to_dict() for p in files], indent=2))
        return 0

    print('=' * 78)
    print('Strategy Discovery Inventory')
    print('Repo root: %s' % REPO_ROOT)
    print('=' * 78)
    for line in format_tier_counts(files, tiers):
        print(line)
    print('  %-16s %3d files' % ('TOTAL', len(files)))
    print()
    for p in files:
        print('  [%-9s] %-15s %s' % (p.kind, p.tier, p.rel))
    warnings = collect_warnings(files)
    if warnings:
        print()
        print('WARNINGS (%d):' % len(warnings))
        for w in warnings:
            print('  ! %s' % w)
    empty = empty_deployed_tiers(files)
    if empty:
        print()
        print('STRUCTURAL ERROR: deployed tier(s) matched zero files: %s'
              % ', '.join(empty))
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')
    sys.exit(main())
