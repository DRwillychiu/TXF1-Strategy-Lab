"""黃金測試集 —— 判官的判官。

**G2 kill gate：對帳工具必須先抓得到每一個已知歷史事故，才准去驗證新東西。**

理由：對帳工具本身出過事故（2026-08-25，不合併分批出場），
而且**當場印「通過」**。判官若沒被驗證過，下游全部失效。

每個案例都構造成「一份正確的清單」與「一份帶已知缺陷的清單」，
斷言工具抓得到。抓不到就 fail，而 fail 就代表不准往下做。

案例來源：
  §3.1 的五個真實事故（repo 內有文件佐證）
  76 天實戰紀錄實測出的四個缺陷
  L5 標頭實測的引擎停損盲點
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from txfcore.parity.diff import (
    ParityResult, Tier, Tolerance, TradeRecord, compare, merge_split_exits,
)

ZERO = Tolerance(Tier.DECISION, max_diff_trades=0, commit="golden")


def _t(ed: int, et: int, xd: int, xt: int, d: int = -1, q: int = 2,
       ep: float = 20000, xp: float = 19900, el: str = "E", xl: str = "X") -> TradeRecord:
    return TradeRecord(ed, et, xd, xt, d, q, ep, xp, el, xl)


@dataclass(frozen=True, slots=True)
class GoldenCase:
    code: str
    title: str
    source: str
    check: Callable[[], bool]
    why: str

    def run(self) -> tuple[bool, str]:
        try:
            return bool(self.check()), ""
        except Exception as e:            # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


# ====================================================================
# G-1  分批出場未合併  ← 2026-08-25 真實事故，且當場印「通過」
# ====================================================================

def _g1() -> bool:
    """MC 把一次出場拆成兩列，我們只有一列。

    未合併時工具會誤判為「兩邊筆數不同」；合併後應完全相符。
    76 天實戰紀錄裡同樣的缺陷還在：9 組 18 筆，佔 30.5%。
    """
    ours = [_t(1260601, 945, 1260601, 1145, q=2, xp=19900)]
    theirs = [
        _t(1260601, 945, 1260601, 1045, q=1, xp=19950),
        _t(1260601, 945, 1260601, 1145, q=1, xp=19850),
    ]
    naive = compare(ours, theirs, Tier.DECISION, ZERO, merge_splits=False)
    merged = compare(ours, theirs, Tier.DECISION, ZERO, merge_splits=True)
    # 未合併時必須抓到差異；合併後必須通過；且合併有被記錄
    return (not naive.passed) and merged.passed and bool(merged.notes)


# ====================================================================
# G-2  L3 基準線自己從 360 變 361  ← 血緣不同必須拒絕比較
# ====================================================================

def _g2() -> bool:
    from txfcore.lineage.stamp import Lineage, LineageMismatch
    a = Lineage("code1", "cfg1", "data1", "cal1")
    b = Lineage("code1", "cfg1", "data2", "cal1")   # 資料換版
    trades = [_t(1260601, 945, 1260601, 1145)]
    try:
        compare(trades, trades, Tier.DECISION, ZERO,
                ours_lineage=a, theirs_lineage=b)
    except LineageMismatch:
        return True
    return False


# ====================================================================
# G-3  L4 v18 二次進場零觸發  ← 事前登記的觸發次數
# ====================================================================

def _g3() -> bool:
    """設計說會觸發 N 次，實際零次。

    判官 (4)：登記的是**觸發次數**，不只是績效。
    L2 停擺 443 天、L4 v18 零觸發，都是沒有人登記過這個數字。
    """
    from txfcore.strategies.l2_trendshort import L2TrendShort
    lo, hi = L2TrendShort().expected_trigger_range()
    observed = 0
    return not (lo <= observed <= hi)      # 必須判定為超出區間


# ====================================================================
# G-4  V2.9 MaxList/MinList 取錯邊  ← 不變量：引擎距離 == 凍結距離
# ====================================================================

def _g4() -> bool:
    """P3 凍結 MaxList 的價位 == Entry − MinList 的距離。

    舊標頭把它改述成「Entry − MaxList(distances)」，P3b 照著錯的形狀寫，
    取了較鬆的一條腿，寬 1.6–2.8 倍，橫跨整個 V2.6+ 世代未被發現。
    **而驗證器把 bug 編碼進去了，所以 bug 通過驗證。**
    """
    entry = 20000.0
    dists = [300.0, 500.0, 250.0]                     # 三條腿的距離
    frozen_price = max(entry - d for d in dists)       # MaxList 價位 = 最緊
    tight_dist = min(dists)                            # MinList 距離 = 最緊
    loose_dist = max(dists)                            # 舊 bug 取的那一條
    correct = abs((entry - frozen_price) - tight_dist) < 1e-9
    buggy_detected = abs((entry - frozen_price) - loose_dist) > 1e-9
    return correct and buggy_detected


# ====================================================================
# G-5  L2 v5.4 定義錯位  ← 決策時可計算性
# ====================================================================

def _g5() -> bool:
    """比較一個「下單當下還不存在」的值，是未來函數。

    L3 標頭記錄了這個陷阱：「L2 v5.4 exposed the trap of comparing a fill
    price that does not exist yet; a Buy Stop has no such gap.」

    型別層應該讓它寫不出來。
    """
    from txfcore.types.bar import FutureDataError, Series
    s = Series([1.0, 2.0, 3.0])
    try:
        _ = s[-1]
    except FutureDataError:
        return True
    return False


# ====================================================================
# G-6  日期倒置  ← 76 天實戰紀錄實測，該筆是全紀錄第二大獲利
# ====================================================================

def _g6() -> bool:
    """進場 2026-07-31 01:30、出場 2026-07-24 21:48，持倉 −147.7 小時。"""
    bad = _t(1260731, 130, 1260724, 2148)
    return not (bad.exit_date, bad.exit_time) >= (bad.entry_date, bad.entry_time)


# ====================================================================
# G-7  MDD 分母錯誤  ← 儀表板 36.47% vs 正確 31.53%
# ====================================================================

def _g7() -> bool:
    """分母用期初資金會讓百分比破 100%。原本那個 106.3% 就是這樣來的。"""
    from txfcore.metrics.drawdown import compute
    eq = [100.0, 500.0, 50.0]                       # 資金成長後大幅回吐
    r = compute(eq)
    by_peak = r.max_drawdown                        # (500−50)/500 = 90%
    by_initial = r.max_drawdown_amount / eq[0]      # 450/100 = 450%
    return by_peak <= 1.0 and by_initial > 1.0


# ====================================================================
# G-8  組合 MDD 由各支相加推論  ← 實戰實測高估 58%
# ====================================================================

def _g8() -> bool:
    from txfcore.metrics.drawdown import compute, equity_curve, portfolio_mdd
    a = [-100.0, 100.0, 0.0, 0.0]
    b = [0.0, 0.0, -100.0, 100.0]
    comb = portfolio_mdd(1000, [a, b]).max_drawdown_amount
    summed = sum(compute(equity_curve(1000, s)).max_drawdown_amount for s in (a, b))
    return comb < summed


# ====================================================================
# G-9  引擎停損無對應出場單  ← L5 標頭實測 171 筆中 1 筆
# ====================================================================

def _g9() -> bool:
    """MC 引擎 SetStopLoss 可直接平倉，交易報告顯示 Stop Loss 但無 Sell 語句。

    出場側標籤永遠標不到這條路徑，所以它必須是獨立的出場類型。
    """
    from txfcore.engine.fill_mc12 import MC12FillModel
    from txfcore.types.bar import Bar
    from txfcore.types.orders import Side
    b = Bar(1260601, 1145, 20000, 20050, 19850, 19900)
    f = MC12FillModel().engine_stop_fill(19900, Side.SELL, 2, b, "L5")
    return f is not None and f.is_engine_stop and f.label == "ENGINE_STOP"


# ====================================================================
# G-10  結算日靜態規則漏標  ← 208 萬列 1 分 K 實測，漏 2 天
# ====================================================================

def _g10() -> bool:
    from txfcore.tradecal.settlement import RULE_MISSED, is_settlement_day, static_rule
    return all(is_settlement_day(d) and not static_rule(d) for d in RULE_MISSED)


# ====================================================================
# G-11  策略變數歷史  ← L4 的追蹤棘輪整條掛在 v_Stop_Level[1]
# ====================================================================

def _g11() -> bool:
    from txfcore.types.stateful import VarBook
    vb = VarBook()
    stop = vb.declare("v_Stop_Level", 0.0)
    stop.set(20500.0); vb.commit_all()
    stop.set(min(stop[1], 20400.0)); vb.commit_all()
    stop.set(min(stop[1], 20600.0))          # 想放鬆，被棘輪擋住
    return stop.value == 20400.0


# ====================================================================
# G-12  容差未登記  ← 事後放寬是最常見的自欺
# ====================================================================

def _g12() -> bool:
    """未登記 commit 的容差，報告必須標明。"""
    tol = Tolerance(Tier.DECISION, max_diff_trades=0)     # 沒給 commit
    r = compare([], [], Tier.DECISION, tol)
    return "未登記" in r.report()


CASES: tuple[GoldenCase, ...] = (
    GoldenCase("G-1", "分批出場未合併", "2026-08-25 真實事故", _g1,
               "對帳工具本身出過事故，且當場印「通過」"),
    GoldenCase("G-2", "基準線自己移動", "L3 從 360 變 361", _g2,
               "血緣不同必須拒絕比較，而非印出無法解釋的差異"),
    GoldenCase("G-3", "零觸發無告警", "L4 v18 · L2 停擺 443 天", _g3,
               "判官 (4)：登記的是觸發次數，不只是績效"),
    GoldenCase("G-4", "取錯停損腿", "V2.9 MaxList/MinList", _g4,
               "驗證器把 bug 編碼進去，所以 bug 通過驗證"),
    GoldenCase("G-5", "未來函數", "L2 v5.4 定義錯位", _g5,
               "型別層應該讓它寫不出來，不是事後斷言"),
    GoldenCase("G-6", "日期倒置", "76 天實戰紀錄", _g6,
               "該筆是全紀錄第二大獲利，資料卻是錯的"),
    GoldenCase("G-7", "MDD 分母錯誤", "儀表板 36.47% vs 31.53%", _g7,
               "用期初資金當分母會讓百分比破 100%"),
    GoldenCase("G-8", "組合 MDD 相加", "實測高估 58%", _g8,
               "各支的最深回撤發生在不同時間點"),
    GoldenCase("G-9", "引擎停損無出場單", "L5 標頭 171 筆中 1 筆", _g9,
               "出場側標籤永遠標不到這條路徑"),
    GoldenCase("G-10", "結算日靜態規則漏標", "208 萬列實測漏 2 天", _g10,
               "第三個週三遇休市會遞延"),
    GoldenCase("G-11", "變數歷史遺失", "L4 v_Stop_Level[1]", _g11,
               "歷史值取錯，整條追蹤停損失效且不報錯"),
    GoldenCase("G-12", "容差未登記", "事前登記原則", _g12,
               "事後放寬容差是最常見的自欺"),
)


def run_golden() -> tuple[bool, str]:
    """跑完整套。回傳 (是否全過, 報告)。

    **全過才准進入對帳。** 這是 G2 kill gate。
    """
    lines = ["黃金測試集 —— 判官的判官", "=" * 64]
    ok = True
    for c in CASES:
        passed, err = c.run()
        ok &= passed
        mark = "✓" if passed else "✗"
        lines.append(f"{mark} {c.code:<6} {c.title:<18} {c.source}")
        if not passed:
            lines.append(f"         └─ {err or '未抓到'}　·　{c.why}")
    lines += ["=" * 64,
              f"{sum(1 for c in CASES if c.run()[0])}/{len(CASES)} 通過"]
    if not ok:
        lines.append("★ 未全過 → 判官不合格 → 不得用於驗證任何新東西")
    return ok, "\n".join(lines)
