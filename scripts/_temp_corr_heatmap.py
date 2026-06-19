"""Compute 6x6 Pearson correlation matrix from portfolio PnL JSON and emit SVG heatmap."""
import json
import math
from pathlib import Path

INPUT = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_portfolio_pnl.json")
OUTPUT = Path(r"C:/Users/User/Desktop/TXF1-Strategy-Lab/docs/portfolio_correlation_heatmap_20260620.svg")

STRATS = ["L1", "L2", "L3", "L4", "L5", "S1"]

with INPUT.open("r", encoding="utf-8") as f:
    raw = json.load(f)

# Build per-strategy dict[date] -> pnl
series = {s: raw.get(s, {}) for s in STRATS}

# Pairwise dropna Pearson correlation
def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = 0.0
    sx2 = 0.0
    sy2 = 0.0
    for x, y in zip(xs, ys):
        dx = x - mx
        dy = y - my
        num += dx * dy
        sx2 += dx * dx
        sy2 += dy * dy
    den = math.sqrt(sx2 * sy2)
    if den == 0:
        return float("nan")
    return num / den

corr = [[0.0] * 6 for _ in range(6)]
pair_n = [[0] * 6 for _ in range(6)]
for i, a in enumerate(STRATS):
    for j, b in enumerate(STRATS):
        if i == j:
            corr[i][j] = 1.0
            pair_n[i][j] = len(series[a])
            continue
        # intersection of dates (trade days only, pairwise dropna)
        da = series[a]
        db = series[b]
        common = sorted(set(da.keys()) & set(db.keys()))
        xs = [float(da[d]) for d in common]
        ys = [float(db[d]) for d in common]
        r = pearson(xs, ys) if common else float("nan")
        corr[i][j] = r
        pair_n[i][j] = len(common)

# Print to stdout for parent to read
print("CORR MATRIX:")
print("     " + "  ".join(f"{s:>6}" for s in STRATS))
for i, a in enumerate(STRATS):
    row = [f"{corr[i][j]:+.3f}" for j in range(6)]
    print(f"{a:>4} " + "  ".join(f"{v:>6}" for v in row))

print("\nPAIR N (overlap trade-days):")
print("     " + "  ".join(f"{s:>6}" for s in STRATS))
for i, a in enumerate(STRATS):
    row = [f"{pair_n[i][j]:d}" for j in range(6)]
    print(f"{a:>4} " + "  ".join(f"{v:>6}" for v in row))

# ----- SVG generation -----
W, H = 1000, 800

# Layout
title = "Portfolio Cross-Strategy Daily PnL Correlation (2020-2026)"
subtitle = "Pearson r on overlapping trade-days (pairwise dropna)  -  Generated 2026-06-20  -  TXF1 Strategy Lab"

# Grid placement
grid_left = 180
grid_top = 130
cell_w = 100
cell_h = 90
grid_right = grid_left + 6 * cell_w  # 780
grid_bottom = grid_top + 6 * cell_h  # 670

# Color bar
bar_left = grid_right + 60       # 840
bar_top = grid_top               # 130
bar_w = 28
bar_h = 6 * cell_h               # 540

def lerp(a, b, t):
    return a + (b - a) * t

def color_for(r):
    """Diverging red(-1)->white(0)->blue(+1). Returns rgb tuple."""
    if r != r:  # NaN
        return (220, 220, 220)
    r = max(-1.0, min(1.0, r))
    if r >= 0:
        t = r
        # white (255,255,255) -> blue (33,102,172)
        R = int(round(lerp(255, 33, t)))
        G = int(round(lerp(255, 102, t)))
        B = int(round(lerp(255, 172, t)))
    else:
        t = -r
        # white (255,255,255) -> red (178,24,43)
        R = int(round(lerp(255, 178, t)))
        G = int(round(lerp(255, 24, t)))
        B = int(round(lerp(255, 43, t)))
    return (R, G, B)

def rgb_str(c):
    return f"rgb({c[0]},{c[1]},{c[2]})"

def text_color_for(r):
    """Contrast text color for cell."""
    if r != r:
        return "#666"
    intensity = abs(r)
    if intensity >= 0.55:
        return "#ffffff"
    return "#1a1a1a"

parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">')

# background
parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fafafa"/>')

# Title
parts.append(f'<text x="{W/2:.0f}" y="48" text-anchor="middle" font-size="22" font-weight="700" fill="#1a1a1a">{title}</text>')
parts.append(f'<text x="{W/2:.0f}" y="76" text-anchor="middle" font-size="13" fill="#555">{subtitle}</text>')
parts.append(f'<text x="{W/2:.0f}" y="96" text-anchor="middle" font-size="11" fill="#888" font-style="italic">Diagonal = self-correlation (greyed)  -  Bold border: |r| &gt; 0.7  -  Dashed border: r &lt; -0.3 (hedge)</text>')

# Column labels
for j, s in enumerate(STRATS):
    cx = grid_left + j * cell_w + cell_w / 2
    parts.append(f'<text x="{cx:.1f}" y="{grid_top - 14}" text-anchor="middle" font-size="15" font-weight="700" fill="#222">{s}</text>')

# Row labels
for i, s in enumerate(STRATS):
    cy = grid_top + i * cell_h + cell_h / 2 + 5
    parts.append(f'<text x="{grid_left - 18}" y="{cy:.1f}" text-anchor="end" font-size="15" font-weight="700" fill="#222">{s}</text>')

# Cells
for i in range(6):
    for j in range(6):
        x = grid_left + j * cell_w
        y = grid_top + i * cell_h
        r = corr[i][j]
        is_diag = (i == j)

        if is_diag:
            fill = "#d8d8d8"
            stroke = "#999"
            stroke_w = 1
            dasharray = ""
            text_fill = "#666"
        else:
            fill = rgb_str(color_for(r))
            text_fill = text_color_for(r)

            # Border rules
            if r != r:
                stroke = "#bbb"; stroke_w = 1; dasharray = ""
            elif abs(r) > 0.7:
                stroke = "#000"; stroke_w = 3; dasharray = ""
            elif r < -0.3:
                stroke = "#000"; stroke_w = 2; dasharray = "5,3"
            else:
                stroke = "#999"; stroke_w = 0.8; dasharray = ""

        dash_attr = f' stroke-dasharray="{dasharray}"' if dasharray else ""
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w}" height="{cell_h}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"{dash_attr}/>'
        )

        # Value text
        if r != r:
            txt = "n/a"
        else:
            txt = f"{r:+.2f}"
            if is_diag:
                txt = "1.00"
        cx = x + cell_w / 2
        cy = y + cell_h / 2 + 5
        parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" font-size="16" font-weight="600" fill="{text_fill}">{txt}</text>')

        # Tiny sample size (skip diagonal)
        if not is_diag:
            n = pair_n[i][j]
            parts.append(f'<text x="{cx:.1f}" y="{y + cell_h - 8:.1f}" text-anchor="middle" font-size="9" fill="{text_fill}" opacity="0.75">n={n}</text>')

# Color bar - draw as a series of thin horizontal strips so it stays "flat" per row
N_STRIPS = 60
for k in range(N_STRIPS):
    # Top of bar = +1, bottom = -1
    r_top = 1.0 - 2.0 * (k / N_STRIPS)
    r_bot = 1.0 - 2.0 * ((k + 1) / N_STRIPS)
    r_mid = (r_top + r_bot) / 2.0
    y = bar_top + k * (bar_h / N_STRIPS)
    h = bar_h / N_STRIPS + 0.5
    parts.append(f'<rect x="{bar_left}" y="{y:.2f}" width="{bar_w}" height="{h:.2f}" fill="{rgb_str(color_for(r_mid))}" stroke="none"/>')

# Color bar border
parts.append(f'<rect x="{bar_left}" y="{bar_top}" width="{bar_w}" height="{bar_h}" fill="none" stroke="#444" stroke-width="1"/>')

# Color bar tick labels
ticks = [(1.0, "+1.0"), (0.7, "+0.7"), (0.3, "+0.3"), (0.0, " 0.0"), (-0.3, "-0.3"), (-0.7, "-0.7"), (-1.0, "-1.0")]
for r_val, label in ticks:
    ty = bar_top + (1.0 - (r_val + 1.0) / 2.0) * bar_h
    parts.append(f'<line x1="{bar_left + bar_w}" y1="{ty:.1f}" x2="{bar_left + bar_w + 6}" y2="{ty:.1f}" stroke="#444" stroke-width="1"/>')
    parts.append(f'<text x="{bar_left + bar_w + 10}" y="{ty + 4:.1f}" font-size="11" fill="#222">{label}</text>')

# Color bar title
parts.append(f'<text x="{bar_left + bar_w/2:.1f}" y="{bar_top - 12}" text-anchor="middle" font-size="11" font-weight="700" fill="#222">Pearson r</text>')

# Legend / annotation footer
legend_y = grid_bottom + 30
parts.append(f'<text x="{grid_left}" y="{legend_y}" font-size="12" font-weight="700" fill="#222">Legend:</text>')

# Bold border swatch
lx = grid_left + 70
parts.append(f'<rect x="{lx}" y="{legend_y - 12}" width="18" height="14" fill="#ffffff" stroke="#000" stroke-width="3"/>')
parts.append(f'<text x="{lx + 24}" y="{legend_y}" font-size="11" fill="#222">|r| &gt; 0.7  concentration warning</text>')

# Dashed border swatch
lx2 = lx + 240
parts.append(f'<rect x="{lx2}" y="{legend_y - 12}" width="18" height="14" fill="#ffffff" stroke="#000" stroke-width="2" stroke-dasharray="5,3"/>')
parts.append(f'<text x="{lx2 + 24}" y="{legend_y}" font-size="11" fill="#222">r &lt; -0.3  hedge value</text>')

# Grey diagonal swatch
lx3 = lx2 + 200
parts.append(f'<rect x="{lx3}" y="{legend_y - 12}" width="18" height="14" fill="#d8d8d8" stroke="#999" stroke-width="1"/>')
parts.append(f'<text x="{lx3 + 24}" y="{legend_y}" font-size="11" fill="#222">Diagonal (self) = 1.00</text>')

# Methodology note
parts.append(f'<text x="{grid_left}" y="{legend_y + 22}" font-size="10" fill="#666" font-style="italic">n = overlapping trade-days used per pair (pairwise dropna).  Daily PnL in NTD, before fees/slippage applied at strategy level.</text>')

# Bottom-right tag
parts.append(f'<text x="{W - 20}" y="{H - 14}" text-anchor="end" font-size="9" fill="#999">TXF1-Strategy-Lab / docs/portfolio_correlation_heatmap_20260620.svg</text>')

parts.append('</svg>')

svg_str = "\n".join(parts)
OUTPUT.write_text(svg_str, encoding="utf-8")
print(f"\nSVG written: {OUTPUT}")
print(f"SVG bytes: {len(svg_str.encode('utf-8'))}")
