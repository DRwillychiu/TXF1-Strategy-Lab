"""v1.28.0 候選（同時段門檻）的 Python 原生實作檢查與 MC 預測。

1. 門檻關（TOD_Gate_Days=0）＝ MC 260825：192 筆、3,232,800
2. 原生實作（txfcore，和 .pla 同一套寫法）vs 研究用 veto（vol_gate_robust.tod_veto）：資料都從 2000 年起，逐筆比對
3. MC 預測：資料從 2019-12-31 起（和 MC 逐筆考題相同），A＝60 日 p70、B＝90 日 p70；
   列出因「暖機」（MC 資料起點較晚，同時段歷史還沒存滿）而和 2000 年起版本不同的交易
Usage: python -I scripts/research/s16_streak_20261118/tod_gate_check.py <1min.txt> <out.md> <csv_dir>
"""
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from vol_gate_robust import tod_veto  # noqa: E402

END = datetime(2026, 11, 16, 12, 20)
SETS = {"A": (60, 0.70), "B": (90, 0.70)}


def key(t):
    return (t.entry_dt, t.entry_label, t.exit_dt, t.exit_label, round(t.net_ntd))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = s16.pla_params(s16.PLA_2611181)
    hol = s16.holiday_tail(s16.PLA_2611181)
    out = ["# S16 v1.28.0 候選（同時段門檻）：Python 原生實作檢查與 MC 預測（推論）", ""]

    b19 = load_bars(sys.argv[1], datetime(2019, 12, 31), END)
    off = s16.run(b19, dict(p, TOD_Gate_Days=0), hol).trades
    out += ["## 1. 門檻關＝260825", "",
            f"- 筆數 {len(off)}、淨利 {sum(t.net_ntd for t in off):,.0f}（必須是 192、3,232,800）", ""]

    b00 = load_bars(sys.argv[1], datetime(2000, 1, 1), END)
    ap = atr_pct_series(b00)
    slot_idx = defaultdict(list)
    for i, b in enumerate(b00):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)
    warm = {}
    out += ["## 2. 原生實作 vs 研究用 veto（資料 2000 年起，全部交易逐筆）", ""]
    for name, (d, q) in SETS.items():
        nat = s16.run(b00, dict(p, TOD_Gate_Days=d, TOD_Gate_Q=q), hol).trades
        ref = s16.run(b00, dict(p, TOD_Gate_Days=0), hol, veto=tod_veto(b00, ap, slot_idx, d, q)).trades
        warm[name] = nat
        same = [key(t) for t in nat] == [key(t) for t in ref]
        diff = sorted(set(map(key, nat)) ^ set(map(key, ref)))
        out.append(f"- {name}（{d} 日 p{int(q*100)}）：原生 {len(nat)} 筆、研究 {len(ref)} 筆，逐筆相同：{'是' if same else '否'}")
        for x in diff[:10]:
            out.append(f"  - 不同：{x[0]:%Y-%m-%d %H:%M} {x[1]} → {x[2]:%Y-%m-%d %H:%M} {x[3]} {x[4]:,}")
    out.append("")

    out += ["## 3. MC 預測（資料 2019-12-31 起，和 MC 逐筆考題相同）", "",
            "| 組 | MC 口徑筆數 | MC 口徑淨利（大台 2 口、滑價 1,000） | 首筆 | 末筆 | 微台 2 口 2020 起淨利 | 年化 | 期望值 | 最大回撤 | 最長連虧 |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    csv_dir = Path(sys.argv[3])
    notes = []
    for name, (d, q) in SETS.items():
        tr = s16.run(b19, dict(p, TOD_Gate_Days=d, TOD_Gate_Q=q), hol).trades
        x = full_stats([micro_net(t) for t in tr if t.exit_dt >= datetime(2020, 1, 1)], 6.876)
        out.append(f"| {name} | {len(tr)} | {sum(t.net_ntd for t in tr):,.0f} | {tr[0].entry_dt:%Y-%m-%d %H:%M} | "
                   f"{tr[-1].entry_dt:%Y-%m-%d %H:%M} | {x['net']:,.0f} | {x['ann']:.1f}% | {x['exp']:,.0f} | "
                   f"{x['mdd']:,.0f}（{x['mdd']/CAP*100:.1f}%） | {x['streak']} |")
        with open(csv_dir / f"candidate_v1280_{name}_trades_mcstart.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["no", "entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_ntd", "micro_net"])
            for n, t in enumerate(tr, 1):
                w.writerow([n, f"{t.entry_dt:%Y-%m-%d %H:%M}", t.entry_label, t.entry_px, f"{t.exit_dt:%Y-%m-%d %H:%M}",
                            t.exit_label, t.exit_px, round(t.net_ntd), round(micro_net(t))])
        wk = {key(t) for t in warm[name] if t.entry_dt >= datetime(2019, 12, 31)}
        ck = {key(t) for t in tr}
        only_cold, only_warm = sorted(ck - wk), sorted(wk - ck)
        last = max([k[0] for k in only_cold + only_warm], default=None)
        notes.append(f"- {name}：暖機造成的差異 {len(only_cold)} 筆只在 MC 起點版、{len(only_warm)} 筆只在 2000 年起版；"
                     f"最後一筆差異 {last:%Y-%m-%d} " if last else f"- {name}：兩種起點逐筆相同")
    out += ["", "暖機差異（MC 資料起點較晚，前幾十天同時段歷史還沒存滿，門檻較鬆或不啟動）：", ""] + notes + [""]
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
