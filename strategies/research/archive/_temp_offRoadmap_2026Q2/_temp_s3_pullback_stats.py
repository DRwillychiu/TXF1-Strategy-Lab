"""
S3 RapidPullbackShort — statistical analysis of pullback magnitude
when Daily MA structure bullish AND RSI > 75.

Computes 1-day, 2-day, 3-day forward pullback distributions to inform TP placement.
"""
import csv
import math
import statistics
import json
from pathlib import Path

CSV_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/backtest/twii_daily.csv")


def load_twii():
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "date": r["Date"],
                "close": float(r["Close"]),
                "high": float(r["High"]),
                "low": float(r["Low"]),
                "open": float(r["Open"]),
            })
    return rows


def sma(values, n):
    out = [None] * len(values)
    for i in range(n - 1, len(values)):
        out[i] = sum(values[i - n + 1: i + 1]) / n
    return out


def rsi(closes, n=14):
    """Standard Wilder RSI"""
    rsi_vals = [None] * len(closes)
    if len(closes) < n + 1:
        return rsi_vals
    gains = []
    losses = []
    for i in range(1, n + 1):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0))
        losses.append(max(-ch, 0))
    avg_g = sum(gains) / n
    avg_l = sum(losses) / n
    if avg_l == 0:
        rsi_vals[n] = 100.0
    else:
        rs = avg_g / avg_l
        rsi_vals[n] = 100 - 100 / (1 + rs)
    for i in range(n + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        g = max(ch, 0)
        l = max(-ch, 0)
        avg_g = (avg_g * (n - 1) + g) / n
        avg_l = (avg_l * (n - 1) + l) / n
        if avg_l == 0:
            rsi_vals[i] = 100.0
        else:
            rs = avg_g / avg_l
            rsi_vals[i] = 100 - 100 / (1 + rs)
    return rsi_vals


def atr(highs, lows, closes, n=14):
    """Wilder ATR"""
    atr_vals = [None] * len(closes)
    trs = [None]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if len(closes) < n + 1:
        return atr_vals
    first_atr = sum(trs[1:n + 1]) / n
    atr_vals[n] = first_atr
    for i in range(n + 1, len(closes)):
        atr_vals[i] = (atr_vals[i - 1] * (n - 1) + trs[i]) / n
    return atr_vals


def pct(values, p):
    """Percentile, 0-100, linear interpolation"""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def main():
    rows = load_twii()
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    ma20 = sma(closes, 20)
    ma60 = sma(closes, 60)
    rsi14 = rsi(closes, 14)
    atr14 = atr(highs, lows, closes, 14)

    triggers = []  # bars where bull regime + RSI > 75
    for i in range(len(rows)):
        if ma20[i] is None or ma60[i] is None or rsi14[i] is None:
            continue
        if i < 60:
            continue
        # Bull-regime gate
        bull = closes[i] > ma20[i] and ma20[i] > ma60[i]
        # 60-day return > +5% (strong bull, not "just barely")
        if i >= 60:
            ret60 = (closes[i] - closes[i - 60]) / closes[i - 60] * 100
        else:
            ret60 = 0
        bull_strong = ret60 > 5.0
        # Overheat
        overheat = rsi14[i] > 75
        if bull and bull_strong and overheat:
            triggers.append(i)

    print(f"Total bars: {len(rows)}")
    print(f"Bull+strong+RSI>75 triggers: {len(triggers)}")
    print(f"Trigger frequency: {len(triggers) / len(rows) * 100:.2f}% of bars")

    # De-dup: keep only first bar of each cluster (RSI must drop below 70 before re-arming)
    armed = True
    dedup_triggers = []
    for i in range(len(rows)):
        if rsi14[i] is None:
            continue
        if rsi14[i] < 70:
            armed = True
        if i in triggers and armed:
            dedup_triggers.append(i)
            armed = False

    print(f"\nDe-dup triggers (first-bar-of-overheat-episode): {len(dedup_triggers)}")
    print(f"Per year (6.4y): ~{len(dedup_triggers) / 6.4:.1f}")

    # For each trigger, compute forward pullback magnitudes
    pullbacks_1d_pct = []  # 1-day low-to-entry % drop
    pullbacks_2d_pct = []
    pullbacks_3d_pct = []
    pullbacks_1d_pts = []  # absolute points
    pullbacks_2d_pts = []
    pullbacks_3d_pts = []
    pullbacks_1d_atr = []  # in ATR multiples
    pullbacks_2d_atr = []
    pullbacks_3d_atr = []
    max_adverse_1d_pct = []  # high above entry within 1 day (max adverse for short)
    max_adverse_2d_pct = []

    for idx in dedup_triggers:
        entry = closes[idx]
        cur_atr = atr14[idx]
        if cur_atr is None or cur_atr == 0:
            continue
        # 1-day forward low
        for n_days in [1, 2, 3]:
            end = min(idx + n_days, len(rows) - 1)
            if end <= idx:
                continue
            lo = min(lows[idx + 1: end + 1])
            hi = max(highs[idx + 1: end + 1])
            drop_pts = entry - lo
            drop_pct = drop_pts / entry * 100
            rise_pts = hi - entry
            rise_pct = rise_pts / entry * 100
            drop_atr = drop_pts / cur_atr
            if n_days == 1:
                pullbacks_1d_pct.append(drop_pct)
                pullbacks_1d_pts.append(drop_pts)
                pullbacks_1d_atr.append(drop_atr)
                max_adverse_1d_pct.append(rise_pct)
            elif n_days == 2:
                pullbacks_2d_pct.append(drop_pct)
                pullbacks_2d_pts.append(drop_pts)
                pullbacks_2d_atr.append(drop_atr)
                max_adverse_2d_pct.append(rise_pct)
            else:
                pullbacks_3d_pct.append(drop_pct)
                pullbacks_3d_pts.append(drop_pts)
                pullbacks_3d_atr.append(drop_atr)

    def stats(data, name, unit):
        if not data:
            print(f"{name}: no data")
            return None
        d = {
            "n": len(data),
            "min": min(data),
            "p10": pct(data, 10),
            "p25": pct(data, 25),
            "median": pct(data, 50),
            "p75": pct(data, 75),
            "p90": pct(data, 90),
            "max": max(data),
            "mean": statistics.mean(data),
        }
        print(f"\n{name} ({unit}):")
        print(f"  n={d['n']:3d}  min={d['min']:.3f}  max={d['max']:.3f}  mean={d['mean']:.3f}")
        print(f"  P10={d['p10']:.3f}  P25={d['p25']:.3f}  MED={d['median']:.3f}  P75={d['p75']:.3f}  P90={d['p90']:.3f}")
        return d

    print("\n" + "=" * 70)
    print("FORWARD PULLBACK MAGNITUDE FROM TRIGGER BAR CLOSE")
    print("=" * 70)
    r = {}
    r["1d_pct"] = stats(pullbacks_1d_pct, "1-day max drawdown from entry close (favourable for short)", "%")
    r["2d_pct"] = stats(pullbacks_2d_pct, "2-day max drawdown from entry close", "%")
    r["3d_pct"] = stats(pullbacks_3d_pct, "3-day max drawdown from entry close", "%")
    r["1d_pts"] = stats(pullbacks_1d_pts, "1-day max drawdown", "TXF points")
    r["2d_pts"] = stats(pullbacks_2d_pts, "2-day max drawdown", "TXF points")
    r["3d_pts"] = stats(pullbacks_3d_pts, "3-day max drawdown", "TXF points")
    r["1d_atr"] = stats(pullbacks_1d_atr, "1-day max drawdown", "x daily ATR(14)")
    r["2d_atr"] = stats(pullbacks_2d_atr, "2-day max drawdown", "x daily ATR(14)")
    r["3d_atr"] = stats(pullbacks_3d_atr, "3-day max drawdown", "x daily ATR(14)")

    print("\n" + "=" * 70)
    print("MAX ADVERSE EXCURSION FOR THE SHORT (price ran AGAINST us)")
    print("=" * 70)
    r["adv_1d_pct"] = stats(max_adverse_1d_pct, "1-day max rise above entry close (adverse for short)", "%")
    r["adv_2d_pct"] = stats(max_adverse_2d_pct, "2-day max rise above entry close", "%")

    # ATR baseline
    valid_atrs = [a for a in atr14 if a is not None]
    valid_atr_pct = [
        atr14[i] / closes[i] * 100
        for i in range(len(closes))
        if atr14[i] is not None and closes[i] > 0
    ]
    print("\n" + "=" * 70)
    print("DAILY ATR(14) BASELINE (TXF1 / TWII proxy)")
    print("=" * 70)
    stats(valid_atrs, "Daily ATR(14) absolute", "TWII pts")
    stats(valid_atr_pct, "Daily ATR(14) as % of close", "%")

    # ATR at trigger bars only (vol context for shorts we'd actually take)
    trigger_atrs = [atr14[idx] for idx in dedup_triggers if atr14[idx] is not None]
    trigger_atr_pct = [atr14[idx] / closes[idx] * 100 for idx in dedup_triggers if atr14[idx] is not None]
    print("\nATR at S3 trigger bars only:")
    stats(trigger_atrs, "ATR at trigger", "pts")
    stats(trigger_atr_pct, "ATR at trigger", "%")

    # Save raw results
    out = {
        "n_triggers": len(dedup_triggers),
        "stats": {k: v for k, v in r.items() if v is not None},
        "trigger_dates_sample": [rows[i]["date"] for i in dedup_triggers[:50]],
    }
    with open(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_s3_pullback_stats.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nSaved to _temp_s3_pullback_stats.json")


if __name__ == "__main__":
    main()
