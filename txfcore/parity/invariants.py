"""不變量的執行時檢查 —— 判官 (2)。

**這是唯一能在沒有 MC 報告的情況下抓到移植錯誤的東西。**

規格表第七節把每支的承諾列成斷言，但那是文件。文件不會叫。
本模組讓它們在每根 K 棒上執行，錯了當場報。

> 五個歷史事故裡，逐筆對帳只抓到 0.5 個，不變量抓到 3 個。
> 而不變量**不需要對照組**——這是它現在最有價值的地方。

**失敗語意**（規格表的裁決）：

    持倉中觸發    停止新進場 + 立即告警 + 維持現有保護性停損 + 不自動平倉
    非持倉觸發    停止新進場 + 立即告警
    例外          #7 / #9（假日與結算日強制平倉）自動市價平倉
                  —— 不動作的代價明確大於動作的代價

回測時不停機，改為**記錄全部違反**，跑完一次看清楚。
實盤時才套用上面的動作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    KNOWN = "known"      # 規格表已記錄的落差，照抄的，不算失敗
    WARN = "warn"
    FAIL = "fail"


class OnFailure(str, Enum):
    HALT_ENTRIES = "halt_entries"   # 停止新進場，保留部位
    FLATTEN = "flatten"             # 自動平倉。只有 #7 / #9
    LOG_ONLY = "log_only"


@dataclass(frozen=True, slots=True)
class Violation:
    code: str
    mc_date: int
    mc_time: int
    detail: str
    severity: Severity


@dataclass(slots=True)
class InvariantLog:
    violations: list[Violation] = field(default_factory=list)
    checks_run: int = 0

    def record(self, code: str, d: int, t: int, detail: str,
               sev: Severity = Severity.FAIL) -> None:
        self.violations.append(Violation(code, d, t, detail, sev))

    def by_code(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for v in self.violations:
            out[v.code] = out.get(v.code, 0) + 1
        return out

    def failures(self) -> list[Violation]:
        return [v for v in self.violations if v.severity is Severity.FAIL]

    def report(self) -> str:
        counts = self.by_code()
        if not counts:
            return f"不變量：{self.checks_run:,} 次檢查，零違反"
        lines = [f"不變量：{self.checks_run:,} 次檢查，{len(self.violations)} 次違反"]
        for code, n in sorted(counts.items(), key=lambda x: -x[1]):
            sev = next(v.severity for v in self.violations if v.code == code)
            mark = {"known": "○", "warn": "▲", "fail": "✗"}[sev.value]
            first = next(v for v in self.violations if v.code == code)
            lines.append(f"  {mark} {code:<22} {n:>5} 次   首例 "
                         f"{first.mc_date}/{first.mc_time:04d}  {first.detail}")
        return "\n".join(lines)


class L2Invariants:
    """L2 的承諾。規格表第七節，12 條中 3 條已知不成立。"""

    def __init__(self, log: InvariantLog) -> None:
        self.log = log
        self._sl_trig_at_lock: float | None = None
        self._tsl_line_prev: float | None = None
        self._active_sl_prev: float | None = None
        self._entry_price: float = 0.0

    def check(self, view, state) -> None:
        pt, ps = state.per_trade, state.per_session
        d, t = view.mc_date, view.mc_time
        pos = view.position
        self.log.checks_run += 1
        in_pos = pos.market_position.value == -1

        if not in_pos:
            self._sl_trig_at_lock = None
            self._tsl_line_prev = None
            self._active_sl_prev = None
            return

        # #1 凍結停損整筆交易不得改變
        if pt.sl_locked and pt.sl_trig > 0:
            if self._sl_trig_at_lock is None:
                self._sl_trig_at_lock = pt.sl_trig
                self._entry_price = pos.entry_price
            elif abs(pt.sl_trig - self._sl_trig_at_lock) > 1e-9:
                self.log.record("L2-1 凍結停損被改", d, t,
                                f"{self._sl_trig_at_lock:.2f} -> {pt.sl_trig:.2f}")

        # #2 SL_Pct 封頂（空單天花板不得高於 Entry × (1+1.25%)）
        cap = pos.entry_price * (1 + 1.25 / 100)
        if pt.sl_trig > 0 and pt.sl_trig > cap + 1e-6:
            self.log.record("L2-2 SL_Pct 未封頂", d, t,
                            f"sl_trig {pt.sl_trig:.2f} > cap {cap:.2f}")

        # #10 TSL_Line 單向（只降不升）
        if pt.tsl_armed and pt.tsl_line > 0:
            if self._tsl_line_prev is not None and pt.tsl_line > self._tsl_line_prev + 1e-9:
                self.log.record("L2-10 TSL_Line 上升", d, t,
                                f"{self._tsl_line_prev:.2f} -> {pt.tsl_line:.2f}")
            self._tsl_line_prev = pt.tsl_line

        # #3 追蹤停損只收緊 —— **規格表 D-2 已記錄不成立**
        if pt.active_sl > 0:
            if self._active_sl_prev is not None and pt.active_sl > self._active_sl_prev + 1e-6:
                self.log.record("L2-3 追蹤停損放鬆", d, t,
                                f"{self._active_sl_prev:.2f} -> {pt.active_sl:.2f}"
                                f"  src={pt.sl_src}", Severity.KNOWN)
            self._active_sl_prev = pt.active_sl

        # #7 StopProfit 必在獲利區
        if pt.stop_profit_price > 0 and pt.stop_profit_price >= pos.entry_price:
            self.log.record("L2-7 StopProfit 非獲利區", d, t,
                            f"{pt.stop_profit_price:.2f} >= entry {pos.entry_price:.2f}")

        # #5 Iron Rule：**05:00 收盤前**必須空手，不是 03:00 當下。
        #    .pla：「03:00 觸發，03:00 成交，04:00 重試，always flat before
        #    the 05:00 close」——訂單在 03:00 掛出，下一根才成交。
        #    斷言若寫成 Time >= 300 就會誤報（2026-09-06 實測誤報 2 次）。
        if view.calendar.holiday_block and t >= 500:
            self.log.record("L2-5 假日 05:00 仍持倉", d, t, "Iron Rule 違反")
        # #6 結算日：13:30 停止交易，12:30 觸發 → 12:45 成交
        if view.calendar.settlement_day and t >= 1330:
            self.log.record("L2-6 結算日 13:30 仍持倉", d, t, "Settlement_Flat 違反")


class L4Invariants:
    """L4 的承諾。規格表第七節，10 條全數成立。"""

    def __init__(self, log: InvariantLog) -> None:
        self.log = log
        self._frozen_atr: float | None = None
        self._stop_prev: float | None = None
        self._trail_was_active = False

    def check(self, view, state) -> None:
        pt, ps = state.per_trade, state.per_session
        d, t = view.mc_date, view.mc_time
        pos = view.position
        self.log.checks_run += 1
        in_pos = pos.market_position.value == -1

        if not in_pos:
            self._frozen_atr = None
            self._stop_prev = None
            self._trail_was_active = False
            return

        # #3 凍結 ATR 持倉期間不得漂移
        if pt.sl_locked and pt.frozen_atr > 0:
            if self._frozen_atr is None:
                self._frozen_atr = pt.frozen_atr
            elif abs(pt.frozen_atr - self._frozen_atr) > 1e-9:
                self.log.record("L4-3 凍結 ATR 漂移", d, t,
                                f"{self._frozen_atr:.4f} -> {pt.frozen_atr:.4f}")

        # #1 追蹤啟動後只收緊（空單「更低 = 更緊」）
        if pt.trail_active and pt.stop_level > 0:
            if self._trail_was_active and self._stop_prev is not None:
                if pt.stop_level > self._stop_prev + 1e-6:
                    self.log.record("L4-1 追蹤停損放鬆", d, t,
                                    f"{self._stop_prev:.2f} -> {pt.stop_level:.2f}")
            self._trail_was_active = True
            self._stop_prev = pt.stop_level

        # #2 SL_Pct 統一封頂全部路徑
        cap = pos.entry_price * (1 + 1.50 / 100)
        if pt.stop_level > 0 and pt.stop_level > cap + 1e-6:
            self.log.record("L4-2 SL_Pct 未封頂", d, t,
                            f"stop {pt.stop_level:.2f} > cap {cap:.2f}")

        # #10 誘多區六根衰減
        if ps.trap_counter > 6 and ps.in_trap_zone:
            self.log.record("L4-10 誘多區未衰減", d, t,
                            f"counter={ps.trap_counter}")

        # Iron Rule 同 L2：檢查 05:00 收盤，不是觸發時刻
        if view.calendar.holiday_block and t >= 500:
            self.log.record("L4-5 假日 05:00 仍持倉", d, t, "Iron Rule 違反")
        if view.calendar.settlement_day and t >= 1330:
            self.log.record("L4-6 結算日 13:30 仍持倉", d, t, "Settlement_Flat 違反")
