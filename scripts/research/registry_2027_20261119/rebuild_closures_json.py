"""Rebuild data/taifex_market_closures.json with the ROC-116 (2027) closures, without the quote cache.

Why: scripts/fetch_taifex_quotes.py builds the JSON from a git-ignored cache of TAIFEX
daily quotes (not on this machine). The 2027 rows come only from the annual calendar
(FORWARD), so the quote-derived part does not need re-fetching: the traded days are
reconstructed from the existing JSON, and the generator's own build()/make_doc() are used.

Safety: before writing, it proves the reconstruction is faithful (old FORWARD -> exactly the
old closed_weekdays) and that the new list = old list + the 2027 rows only.

Usage:  python scripts/research/registry_2027_20261119/rebuild_closures_json.py [--write]
        (no --write = dry run)
"""
import datetime as dt
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fetch_taifex_quotes as gen  # noqa: E402

old = json.load(io.open(gen.OUT_PATH, encoding="utf-8"))
qlo, qhi = (dt.date.fromisoformat(x) for x in old["evidence_channels"]["quote_data"]["covers"])
quote_closed = {dt.date.fromisoformat(r["date"]) for r in old["closed_weekdays"]
                if "quote_data" in r["evidence"]}
traded = set()
d = qlo
while d <= qhi:
    if d.weekday() < 5 and d not in quote_closed:
        traded.add(d)
    d += dt.timedelta(days=1)

old_forward = {k: v for k, v in gen.FORWARD.items() if k < "2027-01-01"}
lo, hi, again = gen.build(traded, old_forward)
assert (lo, hi) == (qlo, qhi), (lo, hi, qlo, qhi)
assert again == old["closed_weekdays"], "reconstruction does not reproduce the existing JSON"

lo, hi, new = gen.build(traded, gen.FORWARD)
n_old = len(old["closed_weekdays"])
assert new[:n_old] == old["closed_weekdays"], "rows up to 2026 changed"
added = new[n_old:]
assert all(r["date"].startswith("2027-") for r in added) and len(added) == 19, added
doc = gen.make_doc(lo, hi, new)
assert doc["evidence_channels"]["quote_data"] == old["evidence_channels"]["quote_data"]

print("reconstruction faithful: %d rows reproduced; quote window %s .. %s" % (n_old, qlo, qhi))
print("adding %d rows (2027):" % len(added))
for r in added:
    print("  %s %s  %s" % (r["date"], r["weekday"], r.get("note", "")))
if "--write" in sys.argv:
    gen.write_doc(doc)
else:
    print("dry run: nothing written (add --write)")
