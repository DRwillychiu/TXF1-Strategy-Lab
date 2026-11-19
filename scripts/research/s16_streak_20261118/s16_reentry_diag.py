"""S16 被洗出場後的再進場診斷（Willy 11/19：「今天如果被洗出場，我還會重複進場?假設行情又照著預期往下走?」）

B（v1.28.1，Build 2611191）2020-01～2026-11-16。Python 引擎在 B 上和 MC v1281c 逐筆相同（推論）。
洗出場：虧損出場（2 口微台淨額 < 0）。之後 48 根 5 分 K（＝MaxHoldingBars，原本這筆最長持有的時間）內：
  - 回到原進場價：任一根最低價 ≤ 原進場價
  - 照預期往下走：最低價 ≤ 原進場價 ×（1 − 2.3%）（＝原本的停利目標）
  - B 有沒有再進場：視窗內下一筆 B 交易的進場標籤
擋住原因（照引擎 SECTION 5.5／9 的條件逐根重算）：
  - 結構翻多：出場後、回到原進場價前，ZLEMA 快線 ≥ 慢線（再進場解除）
  - 斜率不足：回到原進場價前一根，單根跌速沒到 MinSlope_Rate（每分鐘 0.05%，5 分 K 要跌 0.25%）
簡易估算（推論，只用來看問題大小）：回到原進場價時以原進場價再空，之後先碰 +1% 算停損、先碰 −2.3% 算停利，
同一根兩者都碰算停損，48 根都沒碰按收盤；扣 MC 滑價每邊 5 點，換成微台 2 口。

Usage: python -I scripts/research/s16_streak_20261118/s16_reentry_diag.py <1min.txt> <out.md>
"""
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import s16, load_bars, micro_net, CAP  # noqa: E402

CUT = datetime(2026, 11, 16, 12, 20)
S20 = datetime(2020, 1, 1)
W = 48
TP, SL = 0.023, 0.010
SLIP_PTS = 5


def zlema(bars, n, start):
    lag = int((n - 1) / 2); k = 2.0 / (n + 1)
    z = [None] * len(bars)
    v = None
    for i in range(start, len(bars)):
        p = 2 * bars[i].c - bars[i - lag].c
        v = p if v is None else v + k * (p - v)
        z[i] = v
    return z


def micro_pts(pts, px_in, px_out):
    """空單點數 → 微台 2 口淨額（扣 MC 滑價每邊 5 點、稅、手續費）。"""
    return (pts - 2 * SLIP_PTS) * 10 * 2 - (px_in + px_out) * 10 * 0.00002 * 2 - 12 * 2 * 2


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), CUT)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    tr = [t for t in s16.run(bars, p, hol).trades if S20 <= t.exit_dt <= CUT]
    ix = {b.dt: i for i, b in enumerate(bars)}
    st = s16.MAX_BARS_BACK - 1
    zf = zlema(bars, int(p["ZLEMA_Fast"]), st)
    zs = zlema(bars, int(p["ZLEMA_Slow"]), st)
    slope_min = p["MinSlope_Rate"]

    out = ["# S16 被洗出場後會不會再進場：診斷（B，2020-01～2026-11-16；推論：Python 引擎＝MC 逐筆）", "",
           "定義寫在程式開頭 `s16_reentry_diag.py`。2 口微台淨額。", ""]

    # 1. 出場方式
    by = defaultdict(list)
    for t in tr:
        by[t.exit_label].append(micro_net(t))
    out += ["## 1. B 怎麼出場（2020 起）", "", "| 出場方式 | 筆數 | 虧損筆數 | 淨利 |", "|---|---|---|---|"]
    for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        out.append(f"| {k} | {len(v)} | {sum(1 for x in v if x < 0)} | {sum(v):,.0f} |")
    ent = Counter(t.entry_label for t in tr)
    out += ["", "進場來源：" + "、".join(f"{k} {v} 筆" for k, v in ent.most_common()), ""]

    # 2. 每筆虧損出場之後
    rows = []
    for n, t in enumerate(tr):
        if micro_net(t) >= 0:
            continue
        e = ix[t.exit_dt]
        end = min(len(bars) - 1, e + W)
        nxt = tr[n + 1] if n + 1 < len(tr) else None
        nxt_i = ix[nxt.entry_dt] if nxt else None
        re_lab = nxt.entry_label if nxt and nxt_i <= end else ""
        touch = next((j for j in range(e + 1, end + 1) if bars[j].l <= t.entry_px), None)
        lo = min(bars[j].l for j in range(e + 1, end + 1)) if end > e else t.exit_px
        hit_tp = lo <= t.entry_px * (1 - TP)
        hit_1 = lo <= t.entry_px * (1 - 0.01)
        why = ""
        est = None
        if touch is not None:
            flip = next((j for j in range(e, touch) if zf[j] >= zs[j]), None)
            j0 = touch - 1
            el = 5
            sr = ((bars[j0 - 1].c - bars[j0].c) / bars[j0].c * 100) / el
            if flip is not None:
                why = "結構翻多"
            elif not sr > slope_min:
                why = "斜率不足"
            elif bars[j0].c < t.entry_px:
                why = "前一根已在進場價下"
            else:
                why = "其他（時段／收盤／型態）"
            # 簡易估算：原進場價再空
            fill = min(bars[touch].o, t.entry_px)
            res = None
            for j in range(touch, min(len(bars) - 1, touch + W) + 1):
                if bars[j].h >= fill * (1 + SL):
                    res = -fill * SL; break
                if bars[j].l <= fill * (1 - TP):
                    res = fill * TP; break
            if res is None:
                res = fill - bars[min(len(bars) - 1, touch + W)].c
            est = micro_pts(res, fill, fill - res)
        rows.append(dict(t=t, net=micro_net(t), touch=touch is not None, hit1=hit_1, tp=hit_tp, re=re_lab,
                         why=why, est=est, lo=(lo / t.entry_px - 1) * 100))

    def summ(sel, title):
        n = len(sel)
        tch = [r for r in sel if r["touch"]]
        tp = [r for r in sel if r["tp"]]
        tp_no = [r for r in tp if r["re"] == ""]
        re_any = [r for r in sel if r["re"]]
        est = [r["est"] for r in tch if r["est"] is not None and r["re"] == ""]
        return (f"| {title} | {n} | {sum(r['net'] for r in sel):,.0f} | {len(tch)} | "
                f"{sum(1 for r in sel if r['hit1'])} | {len(tp)} | {len(re_any)} | {len(tp_no)} | "
                f"{len(est)} 筆、{sum(est):,.0f} |")

    out += ["## 2. 虧損出場之後 48 根（4 小時交易時間）內", "",
            "| 期間 | 虧損筆數 | 虧損合計 | 價格回到原進場價 | 再跌破原進場 1% | 跌到原停利 −2.3%（照預期走） | B 有再進場（任何方式） | 照預期走但 B 沒進場 | 若回到原進場價就再空（簡易估算，B 沒進場的） |",
            "|---|---|---|---|---|---|---|---|---|"]
    out.append(summ(rows, "2020–2026/11/16"))
    out.append(summ([r for r in rows if r["t"].exit_dt.year <= 2022], "2020–2022"))
    out.append(summ([r for r in rows if r["t"].exit_dt.year >= 2023], "2023–2026"))
    for y in range(2023, 2027):
        out.append(summ([r for r in rows if r["t"].exit_dt.year == y], str(y)))

    out += ["", "## 3. 回到原進場價、但 B 沒再進場：擋住的原因", "", "| 原因 | 筆數 | 其中照預期跌到 −2.3% | 簡易估算合計 |", "|---|---|---|---|"]
    miss = [r for r in rows if r["touch"] and r["re"] == ""]
    for k in ("結構翻多", "斜率不足", "前一根已在進場價下", "其他（時段／收盤／型態）"):
        s = [r for r in miss if r["why"] == k]
        out.append(f"| {k} | {len(s)} | {sum(1 for r in s if r['tp'])} | {sum(r['est'] for r in s):,.0f} |")

    out += ["", "## 4. 照預期跌到 −2.3% 但 B 沒進場的每一筆（2020 起）", "",
            "| 出場時間 | 出場方式 | 原進場價 | 這筆虧損 | 48 根內最低（距原進場） | 擋住原因 | 簡易估算 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["tp"] and r["re"] == "":
            t = r["t"]
            out.append(f"| {t.exit_dt:%Y-%m-%d %H:%M} | {t.exit_label} | {t.entry_px:,.0f} | {r['net']:,.0f} | {r['lo']:.1f}% | "
                       f"{r['why'] or '沒回到原進場價'} | {'' if r['est'] is None else format(r['est'], ',.0f')} |")
    out += ["", f"B 2020 起總淨利 {sum(micro_net(t) for t in tr):,.0f}（{len(tr)} 筆）；資金 {CAP:,}。", ""]
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
