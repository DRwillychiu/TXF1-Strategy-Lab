"""S16 B 實戰前必做的優化與檢查（Willy 11/19：「開發之前還有那些數據是在實戰前絕對需要做優化的?立即完整優化給我」）。

全部用 v1.28.1 候選（B 預設：同時段 90 日 p70）；2 口微台、資金 140,200；只用當下以前的資料。
  A. 今日價位風險：把每筆歷史交易的點數依「今天收盤 ÷ 進場價」放大，看同樣的行情發生在今天的指數位階，
     回撤、單筆最大虧損會變多大（點數損益和指數位階成正比；滑價、手續費不放大）
  B. 停損大小：SL_Pct（價格 %）× StopATRMult（ATR 倍數）網格，看原始與今日價位兩種口徑
  C. 再進場：B 的再進場單表現；再進場也套門檻；關掉再進場
  D. 滑價承受度：每邊再多 x 點，損益兩平的滑價
  E. 實戰期（上線～2027-01-05）與一年期的模擬：自助抽樣歷史交易（今日價位），
     看賺錢機率、碰到 15% 的機率、連虧筆數分布 → 停止條件
Usage: python -I scripts/research/s16_streak_20261118/s16_prelive.py <1min.txt> <out.md>
"""
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol_gate_years import atr_pct_series, s16, load_bars, micro_net, CAP  # noqa: E402
from vol_gate_methods import full_stats  # noqa: E402
from vol_gate_robust import tod_veto  # noqa: E402
from common import PV, LOTS, TAX, FEE  # noqa: E402

END = datetime(2026, 11, 16, 12, 20)
IS_START = datetime(2020, 1, 1)
L23 = datetime(2023, 1, 1)
LAST = 41_823                 # 2026-11-16 12:20 收盤（S16_literature_backtest_20261119.md）
SLIP_PTS = 5                  # MC 口徑：每口每邊 1,000 元 ÷ 200 ＝ 5 點
LIMIT = CAP * 0.15            # 21,030
GO_LIVE = date(2026, 11, 23)
D3_END = date(2027, 1, 5)
HOLI = {date(2026, 12, 25), date(2027, 1, 1)}    # 期交所 115、116 年行事曆
SIMS = 20_000


def today_net(t, extra_slip=0.0):
    """同一筆交易搬到今天的指數位階：毛點數 ×（LAST ÷ 進場價），滑價手續費稅照今天算。"""
    gross = (t.entry_px - t.exit_px) * LAST / t.entry_px
    return (gross - 2 * (SLIP_PTS + extra_slip)) * PV * LOTS - 2 * LAST * PV * TAX * LOTS - FEE * 2 * LOTS


def stats(tr, a, yrs, f=micro_net):
    x = full_stats([f(t) for t in tr if t.exit_dt >= a], yrs)
    pn = [f(t) for t in tr if t.exit_dt >= a]
    x["worst"] = min(pn) if pn else 0.0
    x["mdd_pct"] = x["mdd"] / CAP * 100
    return x


def row(name, x):
    return (f"| {name} | {x['n']} | {x['ann']:.1f}% | {x['exp']:,.0f} | {x['mdd']:,.0f}（{x['mdd_pct']:.1f}%） | "
            f"{x['streak']}／{x['streak_amt']:,.0f} | {x['worst']:,.0f} |")


HDR = ["| 版本 | 筆數 | 年化 | 每筆期望值 | 最大回撤（佔資金） | 最長連虧（筆／金額） | 單筆最大虧損 |", "|---|---|---|---|---|---|---|"]


def sim(pool, n_trades_mean, sims, rng):
    """Poisson 筆數、自助抽樣；回傳總損益、最大回撤、最長連虧的樣本。"""
    tot, mdd, stk = [], [], []
    for _ in range(sims):
        # Poisson 抽樣（Knuth）
        L, k, p = pow(2.718281828459045, -n_trades_mean), 0, 1.0
        while True:
            p *= rng.random()
            if p <= L:
                break
            k += 1
        eq = peak = dd = 0.0
        run = longest = 0
        for _ in range(k):
            x = pool[rng.randrange(len(pool))]
            eq += x
            peak = max(peak, eq)
            dd = min(dd, eq - peak)
            run = run + 1 if x < 0 else 0
            longest = max(longest, run)
        tot.append(eq); mdd.append(dd); stk.append(longest)
    return tot, mdd, stk


def pct(v, q):
    s = sorted(v)
    return s[min(len(s) - 1, int(len(s) * q))]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bars = load_bars(sys.argv[1], datetime(2019, 1, 1), END)
    p = s16.pla_params(s16.PLA_2611191)
    hol = s16.holiday_tail(s16.PLA_2611191)
    ap = atr_pct_series(bars)
    slot_idx = defaultdict(list)
    for i, b in enumerate(bars):
        slot_idx[(b.dt.hour, b.dt.minute)].append(i)

    def go(**kw):
        extra = {k: kw.pop(k) for k in ("reentry_veto",) if k in kw}
        return [t for t in s16.run(bars, dict(p, **kw), hol, **extra).trades if t.exit_dt >= IS_START]

    B = go()
    base = go(TOD_Gate_Days=0)
    print("B", len(B), "base", len(base), flush=True)
    out = ["# S16 B 實戰前優化與檢查（推論，Python；v1.28.1 候選；2 口微台、資金 140,200）", "",
           f"今日價位＝把歷史交易點數乘上（{LAST:,} ÷ 進場價）；滑價每邊 {SLIP_PTS} 點、手續費 {FEE}、期交稅照今天算。", ""]

    # A
    out += ["## A. 同樣的行情發生在今天的指數位階（2020 起）", ""] + HDR
    for name, tr in (("0825 原始", base), ("B 原始", B)):
        out.append(row(name, stats(tr, IS_START, 6.876)))
    for name, tr in (("0825 今日價位", base), ("B 今日價位", B)):
        out.append(row(name, stats(tr, IS_START, 6.876, today_net)))
    out.append("")
    out += ["2023 起：", ""] + HDR
    for name, tr in (("B 原始", B), ("B 今日價位", B)):
        out.append(row(name, stats(tr, L23, 3.876, micro_net if "原始" in name else today_net)))
    out.append("")

    # B 停損網格
    out += ["## B. 停損大小（B 之上；SL_Pct＝價格 %，StopATRMult＝ATR 倍數；現行 1.0／4）", "",
            "| SL_Pct | ATR 倍數 | 筆數 | 原始年化 | 原始期望值 | 原始回撤 | 今日價位年化 | 今日價位期望值 | 今日價位回撤 | 今日價位連虧 | 今日價位單筆最大虧損 |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    grid = {}
    for slp in (0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
        for m in (3.0, 4.0, 5.0):
            tr = B if (slp, m) == (1.0, 4.0) else go(SL_Pct=slp, StopATRMult=m)
            r, t_ = stats(tr, IS_START, 6.876), stats(tr, IS_START, 6.876, today_net)
            grid[(slp, m)] = (r, t_)
            tag = "（現行）" if (slp, m) == (1.0, 4.0) else ""
            out.append(f"| {slp}{tag} | {m} | {r['n']} | {r['ann']:.1f}% | {r['exp']:,.0f} | {r['mdd_pct']:.1f}% | "
                       f"{t_['ann']:.1f}% | {t_['exp']:,.0f} | {t_['mdd_pct']:.1f}% | {t_['streak']} | {t_['worst']:,.0f} |")
            print("grid", slp, m, flush=True)
    out.append("")

    # C 再進場
    re_tr = [t for t in B if t.entry_label != "SE_MA_DeathCross"]
    dc_tr = [t for t in B if t.entry_label == "SE_MA_DeathCross"]
    out += ["## C. 再進場", "", "| B 的進場來源 | 筆數 | 淨利 | 每筆期望值 | 勝率 |", "|---|---|---|---|---|"]
    for name, tr in (("死亡交叉", dc_tr), ("再進場", re_tr)):
        v = [micro_net(t) for t in tr]
        out.append(f"| {name} | {len(v)} | {sum(v):,.0f} | {sum(v)/len(v) if v else 0:,.0f} | "
                   f"{sum(1 for x in v if x > 0)/len(v)*100 if v else 0:.0f}% |")
    out.append("")
    gate90 = tod_veto(bars, ap, slot_idx, 90, 0.70)
    variants = {"B（現行）": B, "B＋再進場也套門檻": go(reentry_veto=gate90), "B＋關掉再進場": go(ReEntry_On=0)}
    out += HDR
    for name, tr in variants.items():
        out.append(row(name, stats(tr, IS_START, 6.876)))
    out.append("")

    # D 滑價
    out += ["## D. 滑價承受度（B，2020 起，每邊再多 x 點）", "", "| 多加滑價（每邊點數） | 淨利 | 年化 | 每筆期望值 |", "|---|---|---|---|"]
    for x in (0, 2, 5, 10, 20):
        v = [micro_net(t) - 2 * x * PV * LOTS for t in B]
        out.append(f"| {x} | {sum(v):,.0f} | {sum(v)/CAP/6.876*100:.1f}% | {sum(v)/len(v):,.0f} |")
    be = sum(micro_net(t) for t in B) / (2 * PV * LOTS * len(B))
    be_t = sum(today_net(t) for t in B) / (2 * PV * LOTS * len(B))
    out += ["", f"損益兩平：每邊再多 **{be:.1f} 點**（原始）／**{be_t:.1f} 點**（今日價位）。", ""]

    # E 模擬
    rng = random.Random(20261119)
    tdays = sum(1 for k in range((D3_END - GO_LIVE).days + 1)
                if (GO_LIVE + timedelta(days=k)).weekday() < 5 and (GO_LIVE + timedelta(days=k)) not in HOLI)
    pool_all = [today_net(t) for t in B]
    pool_26 = [today_net(t) for t in B if t.exit_dt.year == 2026]
    rate_all = len(B) / (6.876 * 250)
    rate_26 = len(pool_26) / (date(2026, 11, 16) - date(2026, 1, 1)).days * 365 / 250
    out += [f"## E. 實戰期模擬（{GO_LIVE}～{D3_END}，{tdays} 個交易日；今日價位；{SIMS:,} 次自助抽樣）", "",
            "| 假設 | 預期筆數 | 賺錢機率 | 總損益中位數 | 回撤 ≥ 15%（21,030）機率 | 連虧 ≥ 6 機率 | 連虧 ≥ 8 機率 |",
            "|---|---|---|---|---|---|---|"]
    for name, pool, rate in (("像 2026 年（高波動）", pool_26, rate_26), ("像 2020 起平均", pool_all, rate_all)):
        tot, mdd, stk = sim(pool, rate * tdays, SIMS, rng)
        out.append(f"| {name} | {rate*tdays:.1f} | {sum(1 for x in tot if x > 0)/SIMS*100:.0f}% | {pct(tot, .5):,.0f} | "
                   f"{sum(1 for x in mdd if x <= -LIMIT)/SIMS*100:.1f}% | {sum(1 for x in stk if x >= 6)/SIMS*100:.1f}% | "
                   f"{sum(1 for x in stk if x >= 8)/SIMS*100:.1f}% |")
    out += ["", "沒交易也算「沒賺」：預期筆數少時，賺錢機率包含 0 筆的情況。", ""]
    out += ["## E2. 一年期（今日價位）：策略正常時會看到的最壞情況 → 停止條件", "",
            "| 假設 | 一年筆數 | 最大回撤 中位數／90%／95%／99% | 最長連虧 中位數／90%／95%／99% | 一年內回撤 ≥ 15% 機率 |",
            "|---|---|---|---|---|"]
    for name, pool, rate in (("像 2026 年（高波動）", pool_26, rate_26), ("像 2020 起平均", pool_all, rate_all)):
        tot, mdd, stk = sim(pool, rate * 250, SIMS, rng)
        m = [-x for x in mdd]
        out.append(f"| {name} | {rate*250:.0f} | " + "／".join(f"{pct(m, q):,.0f}" for q in (.5, .9, .95, .99)) + " | "
                   + "／".join(f"{pct(stk, q)}" for q in (.5, .9, .95, .99)) + f" | {sum(1 for x in m if x >= LIMIT)/SIMS*100:.1f}% |")
    out.append("")
    Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
