"""
S3_S v1.9.6-ANTIHUNT Config B + OPT — Stress Testing 6 events
Date: 2026-07-06
Baseline: 71T / +731K / PF 1.749 / MDD -17.17%

Rule #18 Stress Test Gates:
    - Single event loss < 5% account (< 50,000 NTD)
    - Event cluster loss < 15% account (< 150,000 NTD)
    - Crash insurance strategy expects POSITIVE P&L in crashes (bonus)

Events in backtest period (2019-09 to 2026-06):
    E1: 2020-02-20 to 2020-04-20   COVID crash + limit-down series
    E2: 2022-01-01 to 2022-12-31   Full year bear market (Fed hike + Russia/Ukraine)
    E3: 2022-09-13 to 2022-10-15   CPI shock + Q4 tail
    E4: 2024-08-01 to 2024-08-15   BoJ yen carry unwind crash
    E5: 2025-04-01 to 2025-04-15   Trump tariff crash (04-07 core)
    E6: 2026-06-01 to 2026-06-20   Latest crash cluster (06-05/06/08)

Historical events outside backtest window (proxy interpretation only):
    - 1987 Black Monday, 2008 Lehman, 2010 Flash Crash, 2015 China crash
    -> Coverage gap flagged, cannot back-test but note strategy nature.
"""
import sys, io, json
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from openpyxl import load_workbook
from collections import defaultdict

PATH = r'C:/Users/User/Downloads/TXF1  VolSqueezeShort_v196_ANTIHUNT 策略回測績效報告OPT.xlsx'
ACCOUNT = 1_000_000
SINGLE_LOSS_GATE = ACCOUNT * 0.05     # 50,000
CLUSTER_LOSS_GATE = ACCOUNT * 0.15    # 150,000

# =============================================================================
# 1. Load trades
# =============================================================================
wb = load_workbook(PATH, data_only=True)
ws = wb['交易明細']
trades = []
current = None
for r in ws.iter_rows(min_row=4, values_only=True):
    if not r or not r[3]:
        continue
    sig = str(r[3])
    date_v = r[4]
    time_v = r[5]
    pnl_v = r[8]
    max_favor = r[12] if len(r) > 12 else None
    max_adverse = r[14] if len(r) > 14 else None

    if 'SE_' in sig:
        d = date_v.date() if hasattr(date_v, 'date') else date_v
        pnl = pnl_v if isinstance(pnl_v, (int, float)) else 0
        current = {
            'ed': d, 'et': time_v,
            'pnl': pnl,
            'max_favor': max_favor if isinstance(max_favor, (int, float)) else 0,
            'max_adverse': max_adverse if isinstance(max_adverse, (int, float)) else 0,
        }
    elif 'SX_' in sig and current is not None:
        trades.append({**current, 'sig': sig})
        current = None

n_trades = len(trades)
total_net = sum(t['pnl'] for t in trades)
print('=' * 100)
print('S3_S v1.9.6-ANTIHUNT Config B + OPT — STRESS TESTING 6 EVENTS')
print('=' * 100)
print(f'Total trades parsed: {n_trades}')
print(f'Total net profit:    {total_net:+,.0f}')
print()

# =============================================================================
# 2. Event definitions
# =============================================================================
EVENTS = [
    {
        'id': 'E1',
        'name': '2020 COVID Crash',
        'start': date(2020, 2, 20),
        'end':   date(2020, 4, 20),
        'context': 'S&P -34% in 33 days. TXF1 hit multiple limit-down. Historic vol spike VIX 82.',
        'expected': 'crash-insurance thesis SHOULD capture heavy shorts.',
    },
    {
        'id': 'E2',
        'name': '2022 Full-Year Bear',
        'start': date(2022, 1, 1),
        'end':   date(2022, 12, 31),
        'context': 'Fed 425bp hikes + Russia/Ukraine + China COVID. TWII -22% peak-to-trough.',
        'expected': 'Extended bear regime, strategy should engage frequently.',
    },
    {
        'id': 'E3',
        'name': '2022-Q4 CPI/Tail Shock',
        'start': date(2022, 9, 13),
        'end':   date(2022, 10, 15),
        'context': 'Aug CPI 8.3 shock (09-13), UK gilt crisis, Q4 recession fears. TWII -18% window.',
        'expected': 'Sharp compression + break, ideal S3_S environment.',
    },
    {
        'id': 'E4',
        'name': '2024-08 BoJ Yen Carry Unwind',
        'start': date(2024, 8, 1),
        'end':   date(2024, 8, 15),
        'context': 'BoJ hike 07-31 -> yen carry unwind 08-05 Nikkei -12.4% single day. TXF1 -8%.',
        'expected': 'Single-day event, may or may not trigger (Regime block possible in bull yr).',
    },
    {
        'id': 'E5',
        'name': '2025-04-07 Trump Tariff Crash',
        'start': date(2025, 4, 1),
        'end':   date(2025, 4, 15),
        'context': 'Trump reciprocal tariff announcement 04-02. Global sell-off 04-04 to 04-08.',
        'expected': 'Major TXF1 crash. Backtest T51 captured this at +278.8K.',
    },
    {
        'id': 'E6',
        'name': '2026-06 Crash Cluster',
        'start': date(2026, 6, 1),
        'end':   date(2026, 6, 20),
        'context': 'Latest crash cluster: 06-05 (main) / 06-06 (continuation) / 06-08 (V-turn).',
        'expected': 'Multi-day crash sequence, cluster capture critical for alpha.',
    },
]


def stress_test_event(ev, trades):
    hits = [t for t in trades if t['ed'] and ev['start'] <= t['ed'] <= ev['end']]
    if not hits:
        return {'event': ev, 'trades': [], 'n': 0, 'net': 0, 'wins': 0, 'losses': 0,
                'max_win': 0, 'max_loss': 0, 'worst_single': 0, 'notes': 'No trades - Regime blocked or no squeeze fire'}
    net = sum(t['pnl'] for t in hits)
    wins = sum(1 for t in hits if t['pnl'] > 0)
    losses = sum(1 for t in hits if t['pnl'] < 0)
    max_win = max((t['pnl'] for t in hits if t['pnl'] > 0), default=0)
    max_loss = min((t['pnl'] for t in hits if t['pnl'] < 0), default=0)
    return {
        'event': ev, 'trades': hits, 'n': len(hits), 'net': net,
        'wins': wins, 'losses': losses, 'max_win': max_win, 'max_loss': max_loss,
        'worst_single': max_loss,
    }


# =============================================================================
# 3. Run all 6 events
# =============================================================================
results = []
print()
for ev in EVENTS:
    r = stress_test_event(ev, trades)
    results.append(r)
    print(f'{"=" * 100}')
    print(f'[{ev["id"]}] {ev["name"]}  ({ev["start"]} to {ev["end"]})')
    print(f'{"=" * 100}')
    print(f'  Context : {ev["context"]}')
    print(f'  Expected: {ev["expected"]}')
    print()
    print(f'  Trades N        : {r["n"]}')
    print(f'  Net P&L         : {r["net"]:+13,.0f}')
    print(f'  Wins / Losses   : {r["wins"]}W / {r["losses"]}L')
    print(f'  Max Win         : {r["max_win"]:+13,.0f}')
    print(f'  Max Loss        : {r["max_loss"]:+13,.0f}')
    print(f'  Worst single    : {r["worst_single"]:+13,.0f}  ({abs(r["worst_single"])/ACCOUNT*100:.2f}% account)')

    # Gate 1: worst single loss < 50K
    single_gate = 'PASS' if abs(r['worst_single']) < SINGLE_LOSS_GATE else 'FAIL'
    print(f'  Gate: worst single loss < 5% account (50K): {single_gate}')

    # Gate 2: cluster loss < 150K
    if r['net'] < 0:
        cluster_gate = 'PASS' if abs(r['net']) < CLUSTER_LOSS_GATE else 'FAIL'
    else:
        cluster_gate = 'BONUS'   # Positive net during crash = crash insurance win
    print(f'  Gate: cluster loss < 15% account (150K):   {cluster_gate}')

    # Trades detail
    if r['trades']:
        print()
        print('  Trade details:')
        for t in sorted(r['trades'], key=lambda x: (x['ed'], x['et'] or 0)):
            et_str = str(t['et'])[:8] if t['et'] else '-'
            print(f'    {t["ed"]} {et_str}  {t["sig"]:<24} {t["pnl"]:+11,.0f}  MFE={t["max_favor"]:+7,.0f} MAE={t["max_adverse"]:+7,.0f}')
    print()

# =============================================================================
# 4. Aggregate verdict
# =============================================================================
print('=' * 100)
print('SUMMARY VERDICT')
print('=' * 100)

single_fails = [r for r in results if abs(r['worst_single']) >= SINGLE_LOSS_GATE]
cluster_fails = [r for r in results if r['net'] < 0 and abs(r['net']) >= CLUSTER_LOSS_GATE]

no_trade_events = [r for r in results if r['n'] == 0]
loss_events = [r for r in results if r['net'] < 0]
win_events = [r for r in results if r['net'] > 0]

print()
print(f'{"Event":<32} {"N":>4} {"Net":>13} {"Worst Single":>14} {"Verdict":>16}')
print('-' * 100)
for r in results:
    ev = r['event']
    if r['n'] == 0:
        v = 'NO TRADE'
    elif r['net'] > 0:
        v = 'CRASH WIN'
    elif abs(r['net']) < CLUSTER_LOSS_GATE and abs(r['worst_single']) < SINGLE_LOSS_GATE:
        v = 'SURVIVED'
    else:
        v = 'FAIL'
    print(f'  {ev["id"]} {ev["name"]:<28} {r["n"]:>4} {r["net"]:>+13,.0f} {r["worst_single"]:>+14,.0f} {v:>16}')

print()
print(f'Events tested          : {len(EVENTS)}')
print(f'Crash-win events       : {len(win_events)} ({len(win_events)/len(EVENTS)*100:.1f}%)')
print(f'No-trade events        : {len(no_trade_events)} ({len(no_trade_events)/len(EVENTS)*100:.1f}%)')
print(f'Loss events            : {len(loss_events)} ({len(loss_events)/len(EVENTS)*100:.1f}%)')
print(f'Single loss > 50K fails: {len(single_fails)}')
print(f'Cluster loss > 150K fails: {len(cluster_fails)}')
print()

# Overall stress test verdict
if not single_fails and not cluster_fails:
    if len(win_events) >= 4:
        verdict = 'STRONG PASS'
    elif len(win_events) >= 3:
        verdict = 'PASS'
    else:
        verdict = 'MARGINAL PASS'
else:
    verdict = 'FAIL'

print(f'>>> STRESS TEST OVERALL: {verdict}')
print()

# =============================================================================
# 5. Historical coverage gap
# =============================================================================
print('=' * 100)
print('HISTORICAL COVERAGE GAP (events OUTSIDE backtest 2019-09 to 2026-06)')
print('=' * 100)
gaps = [
    ('1987 Black Monday', 'Oct 1987', 'Cannot test - pre-data. TXF1 did not exist.'),
    ('2008 Lehman', 'Sep-Oct 2008', 'Cannot test - pre-data. Strategy formulation post-dates this.'),
    ('2010 Flash Crash', 'May 2010', 'Cannot test - pre-data.'),
    ('2015 China Crash', 'Aug 2015', 'Cannot test - pre-data.'),
]
for name, when, note in gaps:
    print(f'  [{when}] {name}: {note}')
print()
print('  Interpretation:')
print('  - Strategy DESIGN is regime-agnostic (BB compression + break, not calendar-based)')
print('  - 2020 COVID + 2022 bear + 2025-2026 crashes cover diverse crash flavors:')
print('    * Systemic panic (COVID)')
print('    * Extended monetary tightening (2022 Fed)')
print('    * Policy shock (Trump tariff 2025, BoJ 2024)')
print('    * Structural break (2026-06 cluster)')
print('  - Historical gap acknowledged but structural nature of strategy suggests')
print('    behavior would be similar in un-testable earlier crashes.')

# =============================================================================
# 6. Save JSON
# =============================================================================
out = {
    'version': 'v1.9.6-ANTIHUNT Config B + OPT',
    'date': '2026-07-06',
    'account': ACCOUNT,
    'gates': {
        'single_loss_max_pct': 5,
        'cluster_loss_max_pct': 15,
        'single_loss_max_abs': SINGLE_LOSS_GATE,
        'cluster_loss_max_abs': CLUSTER_LOSS_GATE,
    },
    'events': [
        {
            'id': r['event']['id'],
            'name': r['event']['name'],
            'start': str(r['event']['start']),
            'end': str(r['event']['end']),
            'n_trades': r['n'],
            'net_pnl': r['net'],
            'wins': r['wins'],
            'losses': r['losses'],
            'max_win': r['max_win'],
            'max_loss': r['max_loss'],
            'single_gate_pass': abs(r['worst_single']) < SINGLE_LOSS_GATE,
            'cluster_gate_pass': (r['net'] >= 0) or (abs(r['net']) < CLUSTER_LOSS_GATE),
        }
        for r in results
    ],
    'aggregate': {
        'events_tested': len(EVENTS),
        'crash_win_events': len(win_events),
        'no_trade_events': len(no_trade_events),
        'loss_events': len(loss_events),
        'single_loss_fails': len(single_fails),
        'cluster_loss_fails': len(cluster_fails),
        'verdict': verdict,
    },
    'historical_gap': {name: note for name, _, note in gaps},
}
OUT_JSON = r'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop/9ced3e1d-bba8-4f45-8a66-0d1aa6c9177f/scratchpad/stress_test_v196_opt_result.json'
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\n[JSON saved to {OUT_JSON}]')
