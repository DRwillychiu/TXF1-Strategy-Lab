"""v1.27.0 候選（.pla 預設值，Vol_Gate_Pct 0.20）：從 .pla 讀參數跑，核對與 veto 研究版一致，輸出 MC 要重現的數字。"""
from __future__ import annotations

import csv
import pickle
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from txfcore.strategies import s16_s_v1_26 as s16  # noqa: E402
from common import CAP, micro_net, stats  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Path(sys.argv[1])
    bars = pickle.loads((d / "bars.pkl").read_bytes())
    p = s16.pla_params(s16.PLA_261118)
    assert p["Build_ID"] == 261118 and p["Vol_Gate_Pct"] == 0.20
    base = s16.pla_params(s16.PLA_260825)
    extra = {k for k in p if k not in base}
    diff = {k for k in base if p[k] != base[k]}
    print(f"參數：新增 {extra}，與 260825 不同 {diff}（只應有 Build_ID）")
    res = s16.run(bars, p, s16.holiday_tail(s16.PLA_261118))
    off = s16.run(bars, {**p, "Vol_Gate_Pct": 0}, s16.holiday_tail(s16.PLA_261118))
    ref = list(csv.DictReader(open(ROOT / "tests/fixtures/mc_S16_v1.26.0_b260825_to20261116_trades.csv",
                                   encoding="utf-8")))
    off20 = [t for t in off.trades if t.entry_dt.year >= 2020]
    same = sum(t.entry_dt.strftime("%Y-%m-%d %H:%M") == m["entry_dt"] and abs(t.net_ntd - float(m["net_ntd"])) < 1
               for t, m in zip(off20, ref))
    print(f"Vol_Gate_Pct=0 時對 MC 260825：{same}/{len(ref)}（筆數 {len(off20)}）")
    ts = [t for t in res.trades if t.entry_dt.year >= 2020]
    mc_net = sum(t.net_ntd for t in ts)
    print(f"\n== MC 要重現（大台 2 口口徑、MC 設定同 260825 報表，起 2020-02-26、迄 2026-11-16 12:20）")
    print(f"   交易 {len(ts)} 筆，淨利 {mc_net:,.0f}，首筆 {ts[0].entry_dt}，末筆 {ts[-1].entry_dt}")
    s = stats([micro_net(t) for t in ts])
    print(f"== 微台 2 口：淨利 {s['net']:,.0f} PF {s['pf']:.2f} 平倉回撤 {s['mdd']:,.0f}（{s['mdd'] / CAP * 100:.1f}%）"
          f" 最長連虧 {s['streak']} 快停 {sum(t.exit_label.startswith('SX_MA_QuickStop') for t in ts)}")
    by = defaultdict(list)
    for t in ts:
        by[t.exit_dt.year].append(t)
    for y, v in sorted(by.items()):
        print(f"   {y}: {len(v)} 筆 MC口徑 {sum(t.net_ntd for t in v):>11,.0f}  微台2口 {sum(micro_net(t) for t in v):>9,.0f}")
    with open(d / "candidate_v1270_trades_2020on.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entry_dt", "entry_label", "entry_px", "exit_dt", "exit_label", "exit_px", "net_mc_ntd",
                    "net_micro2"])
        for t in ts:
            w.writerow([t.entry_dt, t.entry_label, t.entry_px, t.exit_dt, t.exit_label, t.exit_px, round(t.net_ntd),
                        round(micro_net(t), 1)])


if __name__ == "__main__":
    main()
