"""空方帳戶 15 萬（Willy 11/19「目前已經規畫的是空方資金就是15萬」）的實戰期風險。推論。

交易與盯市權益同 short_account_combo.py（L2 V1.1.0、L4 V1.1.0、S16 B，各 2 口微台）。定義看結果前寫死：
- 資金 150,000；15% ＝ 22,500；10% ＝ 15,000。
- 交易日：夜盤 08:00 前的 K 棒算前一天。每天結束權益＝當天最後一根 5 分 K 的盯市權益。
- 實戰期視窗：30 個交易日，約等於 11/23～1/5。每一個交易日都當一次起點，2020 起逐日滾動。
  - 起點權益＝前一個交易日結束權益。
  - 視窗內最大虧損＝視窗內任一根 5 分 K 的盯市權益 − 起點權益的最小值，也就是「從起始資金算的虧損」。
  - 視窗結果＝最後一天結束權益 − 起點權益。
- 帳戶停單線（從最高點回落 15%）：
  - 盯市權益從 2020 起的最高點回落 ≥ 22,500 就算觸發。
  - 觸發後要等權益創新高，才計下一次。
  - 列出觸發日，以及觸發後 60 個交易日的損益，也就是停單會錯過或避開的部分。
- 對照組合：
  - L2＋L4
  - L2＋L4＋S16
  - L2＋L4＋S16 1 口（S16 損益與部位減半，只供參考；口數規則是實戰通過前固定 2 口）

Usage: python -I scripts/research/s16_streak_20261118/short_account_window.py <1min.txt> <out.md>
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from short_account_combo import load_all, mtm_series  # noqa: E402

CAP = 150_000
LIM, LIM10 = CAP * 0.15, CAP * 0.10
WIN = 30
FWD = 60
A23 = dt.datetime(2023, 1, 1)


def tdate(k):
    return (k - dt.timedelta(days=1)).date() if k.hour < 8 else k.date()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tr, bars = load_all(sys.argv[1])
    bdt = [b.dt for b in bars]
    half = [dict(t, q=1, net=t["net"] / 2) if t["s"] == "S16" else t for t in tr]
    combos = [("L2＋L4", [t for t in tr if t["s"] != "S16"]),
              ("L2＋L4＋S16", tr),
              ("L2＋L4＋S16 1 口（參考）", half)]
    out = [f"# 空方帳戶 15 萬：實戰期風險（推論；L2、L4 各 2 口，S16 2 口；資金 {CAP:,}）", "",
           "定義寫在程式開頭 `short_account_window.py`。", ""]
    for start_name, a0 in (("2020 起", dt.datetime(2020, 1, 1)), ("2023 起", A23)):
        out += [f"## 30 個交易日視窗：從起始資金算的最大虧損（起點 {start_name}）", "",
                "| 組合 | 視窗數 | 最大虧損 ≥ 10%（15,000） | ≥ 15%（22,500） | 最差視窗虧損（起點） | 視窗結束賺錢的比例 | 視窗結束損益中位數 |",
                "|---|---|---|---|---|---|---|"]
        for nm, sel in combos:
            eq = mtm_series(sel, bars, bdt)
            days, end_eq, bar_day = [], {}, []
            for k, v in eq:
                d = tdate(k)
                if not days or days[-1] != d:
                    days.append(d)
                end_eq[d] = v
                bar_day.append(len(days) - 1)
            # 每天的最低盯市權益
            day_min = [float("inf")] * len(days)
            for (k, v), di in zip(eq, bar_day):
                day_min[di] = min(day_min[di], v)
            res = []
            for i in range(1, len(days) - WIN + 1):
                if days[i] < a0.date():
                    continue
                s0 = end_eq[days[i - 1]]
                worst = min(day_min[i:i + WIN]) - s0
                fin = end_eq[days[i + WIN - 1]] - s0
                res.append((days[i], worst, fin))
            if not res:
                continue
            w = min(res, key=lambda r: r[1])
            fins = sorted(r[2] for r in res)
            out.append(f"| {nm} | {len(res)} | {sum(1 for r in res if r[1] <= -LIM10) / len(res) * 100:.1f}% | "
                       f"{sum(1 for r in res if r[1] <= -LIM) / len(res) * 100:.1f}% | {w[1]:,.0f}（{w[0]}） | "
                       f"{sum(1 for r in res if r[2] > 0) / len(res) * 100:.0f}% | {fins[len(fins) // 2]:,.0f} |")
        out.append("")

    out += ["## 帳戶停單線：從最高點回落 22,500（15 萬的 15%）會在哪些時候觸發（2020 起）", ""]
    for nm, sel in combos:
        eq = mtm_series(sel, bars, bdt)
        days, end_eq = [], {}
        for k, v in eq:
            d = tdate(k)
            if not days or days[-1] != d:
                days.append(d)
            end_eq[d] = v
        idx = {d: i for i, d in enumerate(days)}
        pk = -1e18; armed = True; ev = []
        for k, v in eq:
            if v > pk:
                pk = v; armed = True
            if armed and v - pk <= -LIM:
                d = tdate(k); i = idx[d]
                j = min(len(days) - 1, i + FWD)
                ev.append((k, v - pk, end_eq[days[j]] - v, days[j]))
                armed = False
        out.append(f"- {nm}：觸發 {len(ev)} 次" + ("" if not ev else "：" + "；".join(
            f"{k:%Y-%m-%d %H:%M} 回落 {dd:,.0f}，之後 {FWD} 個交易日（到 {d2}）{fw:+,.0f}" for k, dd, fw, d2 in ev)))
    out.append("")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
