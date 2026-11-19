"""S16 260825：全歷史（2001–2026）基準回測＋全部死亡交叉事件的因子表。

用法：python -I scripts/research/s16_streak_20261118/build.py <1分K.txt> <輸出資料夾>
輸出：bars.pkl、trades_base.csv、events.csv（每個合格死亡交叉訊號一列；特徵只用訊號那根收盤前可見的資料）
"""
from __future__ import annotations

import csv
import math
import pickle
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/research/s16_v1260_port"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402

from common import micro_net  # noqa: E402


def load(data: str, out: Path):
    pk = out / "bars.pkl"
    if pk.exists():
        return pickle.loads(pk.read_bytes())
    from data import load_bars
    bars = load_bars(data, datetime(2000, 1, 1))
    pk.write_bytes(pickle.dumps(bars))
    return bars


def zlema(C, n):
    lag = int((n - 1) / 2)
    k = 2.0 / (n + 1)
    z, out = None, []
    for i in range(len(C)):
        x = 2 * C[i] - C[i - lag] if i >= lag else C[i]
        z = x if z is None else z + k * (x - z)
        out.append(z)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    bars = load(data, out)
    print(f"5 分 K {len(bars)} 根：{bars[0].dt} ～ {bars[-1].dt}")
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)

    sig = []
    res = s16.run(bars, p, hol, on_signal=lambda i, mp: sig.append((i, mp)))
    tr = res.trades
    with open(out / "trades_base.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sig_i", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px",
                    "net_mc_ntd", "net_micro2"])
        for t in tr:
            w.writerow([t.sig_i, t.entry_dt, t.entry_label, t.entry_px, t.exit_dt, t.exit_label, t.exit_px,
                        round(t.net_ntd), round(micro_net(t), 1)])
    print(f"基準交易 {len(tr)} 筆；合格死亡交叉訊號 {len(sig)} 個（其中持倉中 {sum(1 for _, m in sig if m != 0)}）")

    # ---------------- 特徵（全部 trailing，訊號那根收盤可見） ----------------
    O = [b.o for b in bars]; H = [b.h for b in bars]; L = [b.l for b in bars]
    C = [b.c for b in bars]; V = [b.v for b in bars]
    zf, zs = zlema(C, 25), zlema(C, 70)
    tr_ = [H[0] - L[0]] + [max(H[i], C[i - 1]) - min(L[i], C[i - 1]) for i in range(1, len(C))]
    # ATR14 與 ATR 的滾動百分位（過去 3000 根，約 1–3 個月）
    atr = [0.0] * len(C)
    s = 0.0
    for i in range(len(C)):
        s += tr_[i] - (tr_[i - 14] if i >= 14 else 0)
        atr[i] = s / min(i + 1, 14)
    natr = [atr[i] / C[i] * 100 for i in range(len(C))]
    # 交叉序列（任何方向）→ 震盪代理
    cross = [0] * len(C)
    for i in range(1, len(C)):
        if (zf[i - 1] >= zs[i - 1] and zf[i] < zs[i]) or (zf[i - 1] <= zs[i - 1] and zf[i] > zs[i]):
            cross[i] = 1
    ccum = [0] * (len(C) + 1)
    for i in range(len(C)):
        ccum[i + 1] = ccum[i] + cross[i]
    # 日線：每個交易日（以日期）最後收盤，供「前一日」日線趨勢
    day_close = {}
    for b in bars:
        day_close[b.dt.date()] = b.c
    days = sorted(day_close)
    dclose = [day_close[d] for d in days]

    def daily_feats(d):
        k = bisect_left(days, d)          # 前一日以前（不含當天）
        if k < 60:
            return math.nan, math.nan, math.nan
        prev = dclose[:k]
        ma20 = sum(prev[-20:]) / 20
        ma60 = sum(prev[-60:]) / 60
        r5 = prev[-1] / prev[-6] - 1
        return (prev[-1] / ma20 - 1) * 100, (prev[-1] / ma60 - 1) * 100, r5 * 100

    def er(i, n):
        if i < n:
            return math.nan
        num = abs(C[i] - C[i - n])
        den = sum(abs(C[j] - C[j - 1]) for j in range(i - n + 1, i + 1))
        return num / den if den else math.nan

    def pct_rank(arr, i, n):
        lo = max(0, i - n)
        w = arr[lo:i]
        if len(w) < 200:
            return math.nan
        return sum(1 for x in w if x < arr[i]) / len(w)

    taken = {t.sig_i: t for t in tr}
    rows = []
    last_cross = -10**9
    for i, mp in sig:
        b = bars[i]
        # 標籤：假設下一根開盤進場（與 MC 市價單一致），看第 4 根收盤是否仍 ≥ 進場價（＝快速停損條件）
        lab = {}
        if i + 49 < len(C):
            e = O[i + 1]
            lab["qs_fail"] = int(C[i + 1 + 4] >= e)
            lab["fwd12_atr"] = (e - C[i + 12]) / atr[i]
            lab["fwd48_atr"] = (e - C[i + 48]) / atr[i]
            lab["mfe48_atr"] = (e - min(L[i + 1:i + 49])) / atr[i]
            lab["mae4_atr"] = (max(H[i + 1:i + 6]) - e) / atr[i]
        else:
            continue
        # 前一次（任何方向）交叉距離：不含這一根
        prev_cross = [j for j in range(max(0, i - 2000), i) if cross[j]]
        bars_since = i - prev_cross[-1] if prev_cross else 2000
        d20, d60, r5 = daily_feats(b.dt.date())
        t = b.mc_time
        row = dict(
            i=i, dt=b.dt.isoformat(sep=" "), year=b.dt.year, mp=mp,
            taken=int(i in taken),
            outcome=(taken[i].exit_label if i in taken else ""),
            net_micro2=(round(micro_net(taken[i]), 1) if i in taken else ""),
            slope=((C[i - 1] - C[i]) / C[i] * 100) / 5,
            spread_atr=(zs[i] - zf[i]) / atr[i],
            dist_slow_atr=(zs[i] - C[i]) / atr[i],
            natr=natr[i],
            atr_rank=pct_rank(natr, i, 3000),
            er12=er(i, 12), er48=er(i, 48), er144=er(i, 144),
            ret12_atr=(C[i] - C[i - 12]) / atr[i], ret48_atr=(C[i] - C[i - 48]) / atr[i],
            relvol=V[i] / (sum(V[i - 20:i]) / 20) if sum(V[i - 20:i]) > 0 else math.nan,
            cross_n60=ccum[i] - ccum[i - 60], cross_n240=ccum[i] - ccum[i - 240],
            bars_since_cross=bars_since,
            body_atr=(O[i] - C[i]) / atr[i],
            d_ma20=d20, d_ma60=d60, d_r5=r5,
            hour=t // 100, night=int(not (845 < t <= 1345)),
            weekday=b.dt.weekday(), settle_week=int(15 <= b.dt.day <= 21),
            **lab)
        rows.append(row)
    with open(out / "events.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"事件 {len(rows)} 筆寫入 events.csv")


if __name__ == "__main__":
    main()
