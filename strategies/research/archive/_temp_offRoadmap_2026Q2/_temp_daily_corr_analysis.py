"""Daily PnL correlation analysis for 6 strategies (L1-L5, S1)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

JSON_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
OUT_PATH = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_daily_corr.md")

STRATS = ["L1", "L2", "L3", "L4", "L5", "S1"]


def load_df() -> pd.DataFrame:
    with JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Build union of dates
    frames = {}
    for s in STRATS:
        if s not in data:
            print(f"WARN: {s} missing from json", file=sys.stderr)
            frames[s] = pd.Series(dtype=float)
            continue
        ser = pd.Series(data[s], dtype=float)
        ser.index = pd.to_datetime(ser.index)
        frames[s] = ser
    df = pd.concat(frames, axis=1).sort_index()
    df.columns = STRATS  # ensure order
    return df


def fmt_matrix(mat: pd.DataFrame) -> str:
    """Markdown table for a correlation matrix."""
    cols = list(mat.columns)
    header = "| | " + " | ".join(cols) + " |"
    sep = "|---|" + "|".join(["---"] * len(cols)) + "|"
    rows = [header, sep]
    for r in cols:
        row_vals = []
        for c in cols:
            v = mat.loc[r, c]
            if pd.isna(v):
                row_vals.append("NaN")
            else:
                row_vals.append(f"{v:.2f}")
        rows.append(f"| **{r}** | " + " | ".join(row_vals) + " |")
    return "\n".join(rows)


def pairs_from_matrix(mat: pd.DataFrame):
    """Return list of (a, b, r) for upper triangle."""
    out = []
    cols = list(mat.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = cols[i], cols[j]
            r = mat.loc[a, b]
            out.append((a, b, r))
    return out


def classify_pair(r: float):
    """Return list of tags for a correlation value."""
    tags = []
    if pd.isna(r):
        return ["INSUFFICIENT_DATA"]
    if abs(r) > 0.7:
        tags.append("REDUNDANT_WARN (|r|>0.7)")
    elif abs(r) > 0.5:
        tags.append("NOTABLE (|r|>0.5)")
    if r < -0.3:
        tags.append("HEDGE_VALUE (r<-0.3)")
    return tags


def rolling_median_corr(df: pd.DataFrame, window: int = 90) -> pd.DataFrame:
    """Compute median 90-day rolling correlation per pair (zero-filled basis)."""
    df0 = df.fillna(0.0)
    cols = list(df0.columns)
    n = len(cols)
    out = pd.DataFrame(np.nan, index=cols, columns=cols)
    for i in range(n):
        for j in range(i, n):
            a, b = cols[i], cols[j]
            if i == j:
                out.loc[a, b] = 1.0
                continue
            roll = df0[a].rolling(window).corr(df0[b])
            med = roll.dropna().median()
            out.loc[a, b] = med
            out.loc[b, a] = med
    return out


def coverage_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Trade-day counts and overlap matrix."""
    cols = list(df.columns)
    counts = df.notna().sum()
    overlap = pd.DataFrame(0, index=cols, columns=cols, dtype=int)
    for a in cols:
        for b in cols:
            overlap.loc[a, b] = int((df[a].notna() & df[b].notna()).sum())
    return counts, overlap


def main() -> int:
    df = load_df()
    n_dates = len(df.index)
    date_min = df.index.min()
    date_max = df.index.max()

    counts, overlap = coverage_stats(df)

    # 1. Pairwise dropna Pearson (trade-days only)
    corr_pairwise = df.corr(method="pearson", min_periods=10).round(4)
    # 2. Zero-filled Pearson
    corr_zero = df.fillna(0.0).corr(method="pearson").round(4)
    # 3. Rolling 90-day median
    roll_med = rolling_median_corr(df, window=90).round(4)

    # Notable pairs
    pairs_pairwise = pairs_from_matrix(corr_pairwise)
    pairs_zero = pairs_from_matrix(corr_zero)

    # Build pair table combining both
    pair_rows = []
    flagged = []
    for (a, b, r1) in pairs_pairwise:
        r2 = corr_zero.loc[a, b]
        rm = roll_med.loc[a, b]
        ov = overlap.loc[a, b]
        tags_p = classify_pair(r1)
        tags_z = classify_pair(r2)
        all_tags = sorted(set(tags_p + tags_z))
        pair_rows.append({
            "pair": f"{a}-{b}",
            "trade_days_overlap": int(ov),
            "r_pairwise": r1,
            "r_zerofill": r2,
            "r_rolling_median": rm,
            "tags": all_tags,
        })
        if all_tags and all_tags != ["INSUFFICIENT_DATA"]:
            flagged.append(f"{a}-{b}: pairwise r={r1:.2f}, zerofill r={r2:.2f}, rolling_med r={rm:.2f} -> {', '.join(all_tags)}")

    # Build markdown report
    md = []
    md.append("# TXF1 6-Strategy Daily PnL Correlation Analysis")
    md.append("")
    md.append(f"Generated from `{JSON_PATH.name}` on union of trade dates "
              f"({n_dates} unique dates, {date_min.date()} ~ {date_max.date()}).")
    md.append("")
    md.append("## 1. Methodology")
    md.append("")
    md.append("- **Source**: per-strategy daily PnL dict (strategy -> date -> NTD).")
    md.append("- **Universe**: 6 strategies — L1 (TrendLong), L2 (TrendShort), "
              "L3 (ConsolidationLong), L4 (ConsolidationShort), L5 (BreakoutLong), "
              "S1 (NightMomentum, simulation).")
    md.append("- **Index**: sorted union of all trading dates that appear in any strategy's PnL series. "
              "Cells are NaN when that strategy did not trade that day.")
    md.append("- **Formula**: Pearson product-moment correlation "
              "`r = cov(X, Y) / (std(X) * std(Y))`.")
    md.append("- **Two NaN treatments**:")
    md.append("  1. *Trade-days only (pairwise dropna)*: for each pair, keep only rows where "
              "both strategies traded. This measures co-movement *given* both strategies were active. "
              "`min_periods=10` to avoid spurious small-sample noise.")
    md.append("  2. *Zero-filled*: replace NaN with 0 (no trade = 0 PnL = no opinion). "
              "This measures portfolio-level daily co-movement, which is what actually drives "
              "portfolio variance.")
    md.append("- **Rolling stability**: 90-trading-day rolling Pearson (on zero-filled series), "
              "then take the median of the rolling series per pair. Stable pairs have rolling "
              "median close to the static estimate.")
    md.append("- **Thresholds** (per request):")
    md.append("  - `|r| > 0.5` -> NOTABLE")
    md.append("  - `|r| > 0.7` -> REDUNDANT_WARN (overlapping exposure, fails CLAUDE.md "
              "institutional risk gate: cross-strategy correlation < 0.7)")
    md.append("  - `r < -0.3` -> HEDGE_VALUE (meaningful negative correlation)")
    md.append("")
    md.append("### Trade-day coverage per strategy")
    md.append("")
    md.append("| Strategy | Trade days | First trade | Last trade |")
    md.append("|---|---|---|---|")
    for s in STRATS:
        nz = df[s].dropna()
        if len(nz) == 0:
            md.append(f"| {s} | 0 | - | - |")
        else:
            md.append(f"| {s} | {len(nz)} | {nz.index.min().date()} | {nz.index.max().date()} |")
    md.append("")
    md.append("### Pairwise trade-day overlap (both strategies active)")
    md.append("")
    md.append(fmt_matrix(overlap.astype(float)))
    md.append("")

    md.append("## 2. Trade-days-only correlation (pairwise dropna)")
    md.append("")
    md.append("Pearson r computed only on dates where *both* strategies have a fill. "
              "Answers: *when both are active, do their daily P&Ls move together?*")
    md.append("")
    md.append(fmt_matrix(corr_pairwise))
    md.append("")

    md.append("## 3. Zero-filled correlation")
    md.append("")
    md.append("Pearson r on the full union calendar with NaN -> 0. "
              "Answers: *at the portfolio level, do their daily contributions move together?*")
    md.append("")
    md.append(fmt_matrix(corr_zero))
    md.append("")

    md.append("## 4. Notable pairs")
    md.append("")
    md.append("All 15 unordered pairs, sorted by max(|r_pairwise|, |r_zerofill|) descending.")
    md.append("")
    md.append("| Pair | Overlap days | r (trade-days) | r (zero-fill) | r (rolling 90d median) | Tags |")
    md.append("|---|---|---|---|---|---|")

    def sort_key(row):
        a = abs(row["r_pairwise"]) if not pd.isna(row["r_pairwise"]) else 0.0
        b = abs(row["r_zerofill"]) if not pd.isna(row["r_zerofill"]) else 0.0
        return -max(a, b)

    for row in sorted(pair_rows, key=sort_key):
        r1 = "NaN" if pd.isna(row["r_pairwise"]) else f"{row['r_pairwise']:.2f}"
        r2 = "NaN" if pd.isna(row["r_zerofill"]) else f"{row['r_zerofill']:.2f}"
        rm = "NaN" if pd.isna(row["r_rolling_median"]) else f"{row['r_rolling_median']:.2f}"
        tags = ", ".join(row["tags"]) if row["tags"] else "-"
        md.append(f"| {row['pair']} | {row['trade_days_overlap']} | {r1} | {r2} | {rm} | {tags} |")
    md.append("")

    # Filtered flagged subsets
    md.append("### 4a. Pairs with |r| > 0.7 (REDUNDANT_WARN)")
    md.append("")
    hits = [row for row in pair_rows
            if (not pd.isna(row["r_pairwise"]) and abs(row["r_pairwise"]) > 0.7)
            or (not pd.isna(row["r_zerofill"]) and abs(row["r_zerofill"]) > 0.7)]
    if hits:
        for row in hits:
            md.append(f"- **{row['pair']}**: trade-days r={row['r_pairwise']:.2f}, "
                      f"zero-fill r={row['r_zerofill']:.2f}, rolling median r={row['r_rolling_median']:.2f}")
    else:
        md.append("- None. No pair exceeds the institutional 0.7 redundancy threshold.")
    md.append("")

    md.append("### 4b. Pairs with 0.5 < |r| <= 0.7 (NOTABLE)")
    md.append("")
    hits = []
    for row in pair_rows:
        r1, r2 = row["r_pairwise"], row["r_zerofill"]
        a1 = abs(r1) if not pd.isna(r1) else 0.0
        a2 = abs(r2) if not pd.isna(r2) else 0.0
        m = max(a1, a2)
        if 0.5 < m <= 0.7:
            hits.append(row)
    if hits:
        for row in hits:
            md.append(f"- **{row['pair']}**: trade-days r={row['r_pairwise']:.2f}, "
                      f"zero-fill r={row['r_zerofill']:.2f}, rolling median r={row['r_rolling_median']:.2f}")
    else:
        md.append("- None.")
    md.append("")

    md.append("### 4c. Pairs with r < -0.3 (HEDGE_VALUE)")
    md.append("")
    hits = [row for row in pair_rows
            if (not pd.isna(row["r_pairwise"]) and row["r_pairwise"] < -0.3)
            or (not pd.isna(row["r_zerofill"]) and row["r_zerofill"] < -0.3)]
    if hits:
        for row in hits:
            md.append(f"- **{row['pair']}**: trade-days r={row['r_pairwise']:.2f}, "
                      f"zero-fill r={row['r_zerofill']:.2f}, rolling median r={row['r_rolling_median']:.2f}")
    else:
        md.append("- None. No pair shows a strong negative-correlation hedge.")
    md.append("")

    md.append("## 5. Rolling 90-day correlation stability")
    md.append("")
    md.append("Median of 90-trading-day rolling Pearson (on zero-filled series). "
              "Compare against section 3 (zero-fill static r) to gauge whether the relationship is "
              "stable over time or driven by a few regime episodes.")
    md.append("")
    md.append(fmt_matrix(roll_med))
    md.append("")
    md.append("### Stability deltas (|rolling_median - zero_fill_static|)")
    md.append("")
    md.append("| Pair | r_zerofill | r_rolling_median | |delta| | Verdict |")
    md.append("|---|---|---|---|---|")
    stab_rows = []
    for row in pair_rows:
        r2 = row["r_zerofill"]
        rm = row["r_rolling_median"]
        if pd.isna(r2) or pd.isna(rm):
            delta = float("nan")
            verdict = "INSUFFICIENT_DATA"
        else:
            delta = abs(rm - r2)
            if delta < 0.05:
                verdict = "VERY STABLE"
            elif delta < 0.10:
                verdict = "STABLE"
            elif delta < 0.20:
                verdict = "MODERATE DRIFT"
            else:
                verdict = "UNSTABLE / REGIME-DEPENDENT"
        stab_rows.append((row["pair"], r2, rm, delta, verdict))
    for pair, r2, rm, delta, verdict in sorted(stab_rows, key=lambda x: -(0 if pd.isna(x[3]) else x[3])):
        r2s = "NaN" if pd.isna(r2) else f"{r2:.2f}"
        rms = "NaN" if pd.isna(rm) else f"{rm:.2f}"
        ds = "NaN" if pd.isna(delta) else f"{delta:.2f}"
        md.append(f"| {pair} | {r2s} | {rms} | {ds} | {verdict} |")
    md.append("")

    md.append("## 6. Interpretation")
    md.append("")
    # Auto-generated narrative
    # Which strategies look most correlated?
    sorted_pairs_z = sorted(pair_rows,
                            key=lambda r: -abs(r["r_zerofill"]) if not pd.isna(r["r_zerofill"]) else 0)
    top_pos = [p for p in sorted_pairs_z if not pd.isna(p["r_zerofill"]) and p["r_zerofill"] > 0][:3]
    top_neg = [p for p in sorted_pairs_z if not pd.isna(p["r_zerofill"]) and p["r_zerofill"] < 0][:3]

    md.append("### Headline read")
    md.append("")
    redundant = [row for row in pair_rows
                 if (not pd.isna(row["r_pairwise"]) and abs(row["r_pairwise"]) > 0.7)
                 or (not pd.isna(row["r_zerofill"]) and abs(row["r_zerofill"]) > 0.7)]
    if redundant:
        md.append(f"- {len(redundant)} pair(s) breach the |r|>0.7 institutional redundancy gate. "
                  "Review whether both strategies are paying separate slippage for the same exposure.")
    else:
        md.append("- **No pair breaches |r|>0.7.** All 15 pairs are below the institutional redundancy gate "
                  "defined in CLAUDE.md (cross-strategy correlation < 0.7). The 6-strategy portfolio looks "
                  "diversified at the daily-PnL level.")

    md.append("")
    md.append("### Strongest positive co-movement (zero-fill basis)")
    md.append("")
    for p in top_pos:
        md.append(f"- {p['pair']}: r={p['r_zerofill']:.2f} (trade-days r={p['r_pairwise']:.2f}). "
                  f"{'Long-long or short-short pair' if p['pair'][1]==p['pair'][4] or p['pair'][0]==p['pair'][3] else 'Cross-direction pair'}.")
    md.append("")
    md.append("### Strongest negative co-movement (zero-fill basis)")
    md.append("")
    if top_neg:
        for p in top_neg:
            md.append(f"- {p['pair']}: r={p['r_zerofill']:.2f} (trade-days r={p['r_pairwise']:.2f}).")
    else:
        md.append("- No pair has negative zero-fill correlation. The book has no built-in daily hedge — "
                  "downside protection relies on directional separation, not negative correlation.")
    md.append("")

    md.append("### Trade-days vs zero-fill divergence")
    md.append("")
    div = []
    for row in pair_rows:
        r1, r2 = row["r_pairwise"], row["r_zerofill"]
        if pd.isna(r1) or pd.isna(r2):
            continue
        d = r1 - r2
        if abs(d) >= 0.20:
            div.append((row["pair"], r1, r2, d))
    if div:
        for pair, r1, r2, d in sorted(div, key=lambda x: -abs(x[3])):
            md.append(f"- {pair}: trade-days r={r1:.2f} vs zero-fill r={r2:.2f} (delta={d:+.2f}). "
                      "Large delta means co-movement on overlapping days differs from the diluted "
                      "portfolio-level view — overlap is rare, so the zero-fill number is the one to use "
                      "for sizing.")
    else:
        md.append("- All pairs show <0.20 absolute gap between trade-days and zero-fill r — interpretation "
                  "is consistent across both views.")
    md.append("")

    md.append("### Recommendation")
    md.append("")
    md.append("- **Pairwise dropna r** answers a behavioral question (do they react the same way to the "
              "same day's tape?). Useful for entry-condition redundancy diagnosis.")
    md.append("- **Zero-filled r** answers a risk question (does my book have concentrated daily exposure?). "
              "This is the number that should drive position sizing and the institutional |r|<0.7 gate.")
    md.append("- **Rolling median** answers a stability question. Any pair where rolling_median diverges "
              "from the static estimate by >0.20 is regime-dependent — its diversification benefit may "
              "evaporate in the next regime, so do not lean on it.")
    md.append("")

    OUT_PATH.write_text("\n".join(md), encoding="utf-8")

    # Print summary for the agent
    print(f"WROTE: {OUT_PATH}")
    print(f"Dates: {n_dates} ({date_min.date()} ~ {date_max.date()})")
    print("Trade-days corr (pairwise):")
    print(corr_pairwise.to_string())
    print()
    print("Zero-fill corr:")
    print(corr_zero.to_string())
    print()
    print("Rolling 90d median:")
    print(roll_med.to_string())
    print()
    print("FLAGGED:")
    for f in flagged:
        print(" -", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
