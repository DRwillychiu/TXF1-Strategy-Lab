"""研究 A 的診斷：偏離是不是分鐘收盤不同步的雜訊？
(1) 訊號當下那一分鐘就成交（實際做不到）的毛利；(2) 訊號後下一個有成交分鐘，偏離還剩多少。
Usage: python -I scripts/research/calspread_20261120/research_a_diag.py <TXF1> <TXF2> [起始年=2020]
"""
import sys, statistics as st
sys.path.insert(0, __file__.rsplit("research_a_diag.py", 1)[0])
from research_a import build

def main():
    bars, cycles = build(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2020)
    N = 5
    out = ["| K | 訊號次數 | 訊號當下偏離（點，中位） | 下一分鐘剩下的偏離（點，中位） | 剩下比例 | 60 分鐘後剩下（點，中位） |", "|---|---|---|---|---|---|"]
    for K in (2, 3, 4, 6):
        d0, d1, d60 = [], [], []
        for D in cycles:
            for i, d in enumerate(D):
                if i < N:
                    continue
                hist = [s for dd in D[i - N:i] for (_, s, _) in bars.get(dd, [])]
                day = bars.get(d, [])
                if len(hist) < 50 or len(day) < 3:
                    continue
                med = st.median(hist)
                sig = 1.4826 * max(st.median([abs(x - med) for x in hist]), 2.0)
                prev_sig = False
                for j in range(len(day) - 1):
                    dev = day[j][1] - med
                    hit = abs(dev) >= K * sig
                    if hit and not prev_sig:
                        sgn = 1 if dev > 0 else -1
                        d0.append(abs(dev)); d1.append(sgn * (day[j + 1][1] - med))
                        hm = int(day[j][0][:2]) * 60 + int(day[j][0][3:]) + 60
                        later = [b for b in day[j + 1:] if int(b[0][:2]) * 60 + int(b[0][3:]) >= hm]
                        if later:
                            d60.append(sgn * (later[0][1] - med))
                    prev_sig = hit
        out.append(f"| {K} | {len(d0)} | {st.median(d0):.1f} | {st.median(d1):.1f} | {st.median(d1)/st.median(d0)*100:.0f}% | {st.median(d60):.1f} |")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))

if __name__ == "__main__":
    main()
