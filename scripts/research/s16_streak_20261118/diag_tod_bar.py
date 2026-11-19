"""單一訊號棒的同時段門檻細節：ATR%、門檻、排序後附近的值、差距（找 MC 與 Python 不同的原因）。
Usage: python -I scripts/research/s16_streak_20261118/diag_tod_bar.py <1min.txt> "2021-05-25 12:10" [days=90] [q=0.70] [start=2019-12-31]
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sig = datetime.fromisoformat(sys.argv[2])
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    q = float(sys.argv[4]) if len(sys.argv) > 4 else 0.70
    start = datetime.fromisoformat(sys.argv[5]) if len(sys.argv) > 5 else datetime(2019, 12, 31)
    bars = load_bars(sys.argv[1], start, datetime(2026, 11, 16, 12, 20))
    C = [b.c for b in bars]; H = [b.h for b in bars]; L = [b.l for b in bars]
    i = next(k for k, b in enumerate(bars) if b.dt == sig)

    def ap(k):                                   # 與引擎相同：14 根 TR 直接加總
        a = sum(max(H[j], C[j - 1]) - min(L[j], C[j - 1]) for j in range(k - 13, k + 1)) / 14
        return a / C[k] * 100

    mbb = s16.MAX_BARS_BACK
    slot = (bars[i].dt.hour, bars[i].dt.minute)
    hist = [k for k in range(mbb - 1, i) if (bars[k].dt.hour, bars[k].dt.minute) == slot][-days:]
    vals = sorted(ap(k) for k in hist)
    n = len(vals)
    kidx = min(n - 1, int(n * q))
    now = ap(i)
    print(f"訊號棒 {sig}  slot {slot}  歷史筆數 {n}  門檻索引 {kidx}（{n}×{q}={n*q!r}）")
    print(f"ATR% 現在 {now:.10f}  門檻 {vals[kidx]:.10f}  差 {now - vals[kidx]:+.3e}  → {'放行' if now >= vals[kidx] else '擋'}")
    print("門檻附近排序值：", [f"{v:.8f}" for v in vals[max(0, kidx - 3):kidx + 4]])
    print("最早一筆歷史：", bars[hist[0]].dt, " 最後一筆：", bars[hist[-1]].dt)
    gaps = [(bars[hist[j]].dt - bars[hist[j - 1]].dt).days for j in range(1, len(hist))]
    print("歷史日期間隔最大：", max(gaps), "天")


if __name__ == "__main__":
    main()
