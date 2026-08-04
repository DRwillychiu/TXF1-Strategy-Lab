"""Download TAIFEX official TX daily quotes and rebuild data/taifex_market_closures.json.

WHY
---
The Holiday_Tail registry needs a source of truth that is EVIDENCE, not memory.
The exchange's annual calendar PDF is a plan published the previous Q4 -- it can
never contain an ad-hoc (typhoon) closure, and archived years are no longer served
(2025Calendar.pdf and earlier now 404).

The daily quote feed does not have that weakness: a business day with no published
TX quote is a day the market was shut, whatever the reason.  That makes it the
stronger source for backtest fidelity, at the cost of not preserving the
annual/ad-hoc split -- which is why the JSON keeps both channels separate.

USAGE
-----
  python scripts/fetch_taifex_quotes.py              # fetch (cached) + rebuild JSON
  python scripts/fetch_taifex_quotes.py --check      # rebuild only, no network
  python scripts/fetch_taifex_quotes.py --to 2027-12-31

The cache directory is git-ignored: it is ~5 MB of raw exchange CSV that can be
re-fetched at any time, and checking it in would put a mirror of exchange data
under version control for no benefit.

LIMITATION
----------
This script cannot classify a closure as annual vs ad-hoc on its own.  Dates listed
in ADHOC below carry that label because Taiwan has no statutory market holiday on
them in any year (see docs/research/calendar_module_taifex_verification_20260804.md
section 5.3).  Adding a NEW ad-hoc closure means adding it to ADHOC here.
"""
import argparse
import calendar
import datetime
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(REPO_ROOT, 'data', '_taifex_cache')
OUT_PATH = os.path.join(REPO_ROOT, 'data', 'taifex_market_closures.json')

URL = 'https://www.taifex.com.tw/cht/3/futDataDown'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://www.taifex.com.tw/cht/3/futDailyMarketReport',
}
FIRST_YEAR = 2019
WK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Closures that provably cannot come from an annual calendar: Taiwan has no
# statutory market holiday on these dates in any year.
ADHOC = {
    '2019-08-09': 'typhoon closure (no statutory holiday exists in early August)',
    '2019-09-30': 'typhoon closure (Mid-Autumn 2019 was 09-13; no holiday on 09-30)',
    '2023-08-03': 'typhoon closure (no statutory holiday exists in early August)',
    '2024-07-24': 'typhoon closure (no statutory holiday exists in late July)',
    '2024-07-25': 'typhoon closure (no statutory holiday exists in late July)',
    '2024-10-02': 'typhoon closure (no statutory holiday exists on 10-02)',
    '2024-10-03': 'typhoon closure (no statutory holiday exists on 10-03)',
    '2024-10-31': 'typhoon closure (no statutory holiday exists on 10-31)',
    '2026-07-10': 'typhoon Bavi; absent from the official ROC-115 annual calendar; '
                  'announced 2026-07-09 (CNA / Economic Daily)',
}

# Closures known from the official annual calendar but not yet reachable by the
# quote feed (the year has not finished).  Format: 'YYYY-MM-DD': 'ROC-nnn calendar'.
FORWARD = {
    '2026-09-25': 'ROC-115 annual calendar',
    '2026-09-28': 'ROC-115 annual calendar',
    '2026-10-09': 'ROC-115 annual calendar',
    '2026-10-26': 'ROC-115 annual calendar',
    '2026-12-25': 'ROC-115 annual calendar',
}


def month_bounds(year, month):
    last = calendar.monthrange(year, month)[1]
    return ('%04d/%02d/01' % (year, month), '%04d/%02d/%02d' % (year, month, last))


def fetch_month(year, month, pause=0.8):
    path = os.path.join(CACHE_DIR, 'TX_%04d%02d.csv' % (year, month))
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return False
    start, end = month_bounds(year, month)
    body = urllib.parse.urlencode({
        'down_type': '1',
        'commodity_id': 'TX',
        'queryStartDate': start,
        'queryEndDate': end,
    }).encode()
    last_exc = None
    for _ in range(3):
        try:
            req = urllib.request.Request(URL, data=body, headers=HEADERS)
            raw = urllib.request.urlopen(req, timeout=90).read()
            with open(path, 'wb') as f:
                f.write(raw)
            time.sleep(pause)
            return True
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(3)
    raise SystemExit('STRUCTURAL: could not fetch %04d-%02d: %s' % (year, month, last_exc))


def traded_dates():
    """Dates carrying a published TX regular-session quote."""
    import csv
    out = set()
    if not os.path.isdir(CACHE_DIR):
        raise SystemExit('STRUCTURAL: no cache at %s; run without --check first'
                         % CACHE_DIR)
    files = sorted(f for f in os.listdir(CACHE_DIR) if f.startswith('TX_'))
    if not files:
        raise SystemExit('STRUCTURAL: cache is empty; run without --check first')
    for fn in files:
        raw = open(os.path.join(CACHE_DIR, fn), 'rb').read().decode('big5', 'ignore')
        rows = list(csv.reader(io.StringIO(raw)))
        if not rows:
            continue
        try:
            sess = rows[0].index('交易時段')  # "trading session"
        except ValueError:
            raise SystemExit('STRUCTURAL: %s has no session column' % fn)
        for r in rows[1:]:
            if len(r) <= sess or not r[0].strip():
                continue
            try:
                d = datetime.datetime.strptime(r[0].strip(), '%Y/%m/%d').date()
            except ValueError:
                continue
            if r[sess].strip() == '一般':  # regular session
                out.add(d)
    if not out:
        raise SystemExit('STRUCTURAL: parsed zero trading days from the cache')
    return out


def build(traded, forward):
    lo, hi = min(traded), max(traded)
    rows = []
    d = lo
    while d <= hi:
        if d.weekday() < 5 and d not in traded:
            rows.append((d, ['quote_data']))
        d += datetime.timedelta(days=1)
    for iso in sorted(forward):
        d = datetime.date(*map(int, iso.split('-')))
        if d > hi and d.weekday() < 5:
            rows.append((d, ['annual_pdf']))
    rows.sort()

    closures = []
    for d, ev in rows:
        iso = d.isoformat()
        rec = {
            'date': iso,
            'weekday': WK[d.weekday()],
            'channel': 'adhoc' if iso in ADHOC else 'annual',
            'evidence': ev,
        }
        note = ADHOC.get(iso) or forward.get(iso)
        if note:
            rec['note'] = note
        closures.append(rec)
    return lo, hi, closures


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true',
                    help='rebuild the JSON from the existing cache; no network')
    ap.add_argument('--to', default=None,
                    help='fetch up to this date (YYYY-MM-DD); default = today')
    args = ap.parse_args()

    if not args.check:
        os.makedirs(CACHE_DIR, exist_ok=True)
        end = (datetime.date(*map(int, args.to.split('-'))) if args.to
               else datetime.date.today())
        fetched = 0
        for y in range(FIRST_YEAR, end.year + 1):
            for m in range(1, 13):
                if datetime.date(y, m, 1) > end:
                    break
                if fetch_month(y, m):
                    fetched += 1
        print('fetched %d new month file(s); cache at %s'
              % (fetched, os.path.relpath(CACHE_DIR, REPO_ROOT).replace(os.sep, '/')))

    lo, hi, closures = build(traded_dates(), FORWARD)
    pdf_hi = max(FORWARD) if FORWARD else hi.isoformat()
    doc = {
        'schema_version': 1,
        'purpose': 'Single source of truth for TXF1 calendar risk. Holiday_Tail blocks '
                   'embedded in .pla files are GENERATED from this file and are never '
                   'edited by hand (rules handbook D-1: generation-time sharing).',
        'generated_by': 'scripts/fetch_taifex_quotes.py',
        'evidence_channels': {
            'annual_pdf': {
                'what': 'TAIFEX official annual futures-market calendar',
                'url': 'https://www.taifex.com.tw/file/taifex/CHINESE/4/2026Calendar.pdf',
                'roc_year': 115,
                'covers': ['2026-01-01', pdf_hi],
                'limitation': 'published the previous Q4; structurally cannot contain '
                              'ad-hoc closures. Archived years (2025 and earlier) are '
                              'no longer served by taifex.com.tw.',
            },
            'quote_data': {
                'what': 'TAIFEX official TX daily quotes; a business day with no '
                        'published quote is a day the market was shut',
                'endpoint': URL + ' (down_type=1, commodity_id=TX)',
                'covers': [lo.isoformat(), hi.isoformat()],
            },
        },
        'session_fact': {
            'claim': 'The after-hours row of trade date T is the night session that ran '
                     'from the PREVIOUS trading day 15:00 to T 05:00. The eve-of-closure '
                     'night session therefore always runs; it is booked to the first '
                     'business day after the closure. Holiday_Tail = last trading day '
                     'before the closure + 1 calendar day.',
            'how_verified': 'price continuity on official quotes: 2026-02-11 regular '
                            'close 33691 -> the after-hours row booked to 2026-02-23 '
                            'opens 33600 (a normal evening gap); that row closes 33969 '
                            '-> 2026-02-23 regular open 34269 carries the full 12-day '
                            'holiday gap. Same pattern at the 2026-07-10 closure.',
        },
        'maintenance': [
            'Every Q4: rebuild from the next ROC-year annual calendar and bump '
            'Registry_Valid_Until in every strategy.',
            'After EVERY ad-hoc closure announcement: add the date to ADHOC in '
            'scripts/fetch_taifex_quotes.py, re-run, regenerate the .pla blocks. '
            'An ad-hoc closure cannot be predicted, but it can be backfilled, and '
            'backfilling is what keeps the backtest honest.',
        ],
        'known_gaps': [
            'ROC-116 (2027) annual calendar not published yet, so the 2027-01-01 tail '
            'and Registry_Valid_Until(1270101) cannot be re-verified until Q4 2026.',
            'Annual PDFs for 2019-2025 are 404 on taifex.com.tw. Those years rest on the '
            'quote-data channel alone, which is stronger for backtesting but does not '
            'preserve the annual/ad-hoc split; that split is deduced from the absence '
            'of any statutory holiday on the date.',
        ],
        'closed_weekdays': closures,
    }
    with io.open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')
    ann = sum(1 for r in closures if r['channel'] == 'annual')
    adh = len(closures) - ann
    print('wrote %s: %d closed business days (annual %d / adhoc %d), %s .. %s'
          % (os.path.relpath(OUT_PATH, REPO_ROOT).replace(os.sep, '/'),
             len(closures), ann, adh, closures[0]['date'], closures[-1]['date']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
