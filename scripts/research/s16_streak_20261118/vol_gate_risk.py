"""自適應 60 日 p70 的風險檢查（2023 起，2 口微台）：
  A. 停損大小：進場時 ATR×4 與 1% 價格上限誰生效、單筆最大虧損
  B. ATR 失真：開盤跳空灌進 ATR、單一根爆量 K 棒主導 ATR 的進場，各自損益
  C. 對照：去掉開盤跳空的 ATR（開盤第一根只算高低差）做同樣的 p70 門檻
Usage: python -I scripts/research/s16_streak_20261118/vol_gate_risk.py <1min.txt>
"""
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, rolling_pct_veto, s16, load_bars, micro_net, stats, CAP  # noqa: E402

SESSION_FIRST = {(8, 50), (15, 5)}


def tr_series(bars, gapfree):
    out = []
    for i, b in enumerate(bars):
        first = (b.dt.hour, b.dt.minute) in SESSION_FIRST
        if i == 0 or (gapfree and first):
            out.append(b.h - b.l)
        else:
            out.append(max(b.h, bars[i - 1].c) - min(b.l, bars[i - 1].c))
    return out


def atr_from_tr(bars, tr, n=14):
    out, q, s = [], deque(), 0.0
    for b, x in zip(bars, tr):
        q.append(x); s += x
        if len(q) > n:
            s -= q.popleft()
        out.append(s / len(q) / b.c * 100)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2000, 1, 1), datetime(2026, 11, 16, 12, 20))
    idx = {b.dt: i for i, b in enumerate(bars)}
    p = s16.pla_params(s16.PLA_260825)
    hol = s16.holiday_tail(s16.PLA_260825)
    tr = tr_series(bars, gapfree=False)
    ap = atr_pct_series(bars)
    trades = [t for t in s16.run(bars, dict(p), hol, veto=rolling_pct_veto(ap, 60, 0.70)).trades
              if t.exit_dt >= datetime(2023, 1, 1)]

    print("== A. 停損大小（自適應 60 日 p70，2023 起）")
    cap_bind, worst = 0, []
    for t in trades:
        i = idx[t.entry_dt] - 1                       # 訊號棒
        atr_pts = ap[i] * bars[i].c / 100
        atr_stop, pct_stop = atr_pts * 4, t.entry_px * 0.01
        cap_bind += pct_stop < atr_stop
        worst.append((micro_net(t), t.entry_dt, t.exit_label, min(atr_stop, pct_stop)))
    worst.sort()
    print(f"筆數 {len(trades)}；1% 價格上限比 ATR×4 更緊（上限生效）的筆數 {cap_bind}")
    print("最差 5 筆：損益（元）| 進場 | 出場類型 | 進場時停損距離（點）")
    for w in worst[:5]:
        print(f"  {w[0]:,.0f} | {w[1]:%Y-%m-%d %H:%M} | {w[2]} | {w[3]:.0f}")
    print(f"停損距離換算 2 口微台的最大可能虧損（以 43,000 點、1% 上限）：{43000*0.01*10*2:,.0f} 元 = {43000*0.01*20/CAP*100:.1f}% 資金")

    print("\n== B. ATR 失真檢查（同一批交易）")
    gap_in, spike, normal = [], [], []
    for t in trades:
        i = idx[t.entry_dt] - 1
        win = range(max(0, i - 13), i + 1)
        has_open = any((bars[j].dt.hour, bars[j].dt.minute) in SESSION_FIRST for j in win)
        trs = [tr[j] for j in win]
        dom = max(trs) / sum(trs) if sum(trs) else 0
        (gap_in if has_open else spike if dom >= 0.30 else normal).append(micro_net(t))
    for name, v in (("ATR 視窗內含開盤第一根（跳空灌進 ATR）", gap_in),
                    ("單一根 K 棒佔 ATR 30% 以上（爆量一根主導）", spike), ("其他", normal)):
        x = stats(v) if v else dict(n=0, net=0, win=0)
        print(f"{name}: {x['n']} 筆，淨利 {x['net']:,.0f}，勝率 {x['win']*100:.0f}%")

    print("\n== C. 去掉開盤跳空的 ATR 做 p70 門檻（對照）")
    ap_gf = atr_from_tr(bars, tr_series(bars, gapfree=True))
    for name, a in (("一般 ATR（含跳空）", ap), ("去跳空 ATR", ap_gf)):
        tt = [t for t in s16.run(bars, dict(p), hol, veto=rolling_pct_veto(a, 60, 0.70)).trades
              if t.exit_dt >= datetime(2023, 1, 1)]
        x = stats([micro_net(t) for t in tt])
        print(f"{name}: {x['n']} 筆 淨利 {x['net']:,.0f} PF {x['pf']:.2f} 回撤 {x['mdd']:,.0f}（{x['mdd']/CAP*100:.1f}%）連虧 {x['streak']}")
    by = {}
    for t in trades:
        by.setdefault(t.exit_dt.year, []).append(t)
    print("\n自適應 p70 每年筆數：", {y: len(v) for y, v in sorted(by.items())})


if __name__ == "__main__":
    main()
