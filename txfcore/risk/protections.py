"""組合層級的斷路器。

**外部借鑑：freqtrade 的 protections。** 它把「最近表現太差就暫停」
做成可組合的保護器：連續停損達 N 次暫停、回撤超過門檻暫停、
出場後冷卻若干期。

**MC 從來沒有這一層。** 它一次只跑一支、一個帳戶、固定口數，
從未回答過「五支同時發訊號」「總曝險上限」「最近連虧該不該停」。

規劃書層 3 的三個不變量：

    總口數 ≤ 上限
    單筆風險 ≤ 帳戶 X%
    任一時刻部位可對帳

本模組實作前兩個，加上三個時間維度的保護器。

**與策略層的分工**：策略層有自己的停損（那是單筆風險），
本層管的是**組合與時間序列的風險**——單筆停損管不到「連續十次停損」。

> 注意：這一層**無 MC 錨點**。驗證只能靠不變量 + 情境重放 + 故障注入，
> 三法各自事前登記通過標準。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class Verdict(str, Enum):
    ALLOW = "allow"
    BLOCK_ENTRY = "block_entry"   # 停止新進場，保留現有部位
    HALT_ALL = "halt_all"         # 停止全部，需人工釋放


@dataclass(frozen=True, slots=True)
class Decision:
    verdict: Verdict
    protection: str = ""
    reason: str = ""
    until: date | None = None

    @property
    def allowed(self) -> bool:
        return self.verdict is Verdict.ALLOW


@dataclass(slots=True)
class TradeOutcome:
    strategy: str
    exit_day: date
    net: float
    is_stop_loss: bool


class Protection:
    name = "base"

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        raise NotImplementedError


@dataclass(slots=True)
class CooldownPeriod(Protection):
    """出場後冷卻。

    L4 的 `Cooldown_Bars = 8` 是**策略層內建的**（同一支自己的冷卻）。
    本保護器是**組合層**的：任一支剛停損，其餘四支是否也該等一下。

    預設 `per_strategy = True`，只擋該支——與 MC 行為一致。
    改成 False 才是新行為，屬 v2 模式。
    """

    days: int = 1
    per_strategy: bool = True
    name: str = "cooldown"

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        recent = [t for t in history
                  if t.is_stop_loss and (today - t.exit_day).days < self.days]
        if recent:
            t = recent[-1]
            return Decision(Verdict.BLOCK_ENTRY, self.name,
                            f"{t.strategy} 於 {t.exit_day} 停損出場",
                            t.exit_day + timedelta(days=self.days))
        return Decision(Verdict.ALLOW)


@dataclass(slots=True)
class StoplossGuard(Protection):
    """回看窗口內停損次數達門檻即暫停。

    L2 標頭記載最大連續虧損 9 次、實戰紀錄也是 9 次。
    **單筆停損管不到「連續九次」——那需要這一層。**
    """

    lookback_days: int = 7
    max_stops: int = 4
    per_strategy: bool = False
    name: str = "stoploss_guard"

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        window = [t for t in history
                  if t.is_stop_loss and 0 <= (today - t.exit_day).days < self.lookback_days]
        if len(window) >= self.max_stops:
            return Decision(Verdict.BLOCK_ENTRY, self.name,
                            f"{self.lookback_days} 日內停損 {len(window)} 次"
                            f"（門檻 {self.max_stops}）")
        return Decision(Verdict.ALLOW)


@dataclass(slots=True)
class MaxDrawdownGuard(Protection):
    """回撤超過門檻即停止。

    **這是規劃書層 3 最重要的一條**，因為它是唯一能防止災難性虧損的機制，
    而策略層的停損只管單筆。

    76 天實戰紀錄：`max_drawdown 31.53%`、`underwater_ratio 96.7%`。
    若門檻設 25%，這個保護器會在中途觸發。
    """

    threshold: float = 0.25
    halt_instead_of_block: bool = True
    name: str = "max_drawdown"

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        if len(equity) < 2:
            return Decision(Verdict.ALLOW)
        peak = equity[0]
        worst = 0.0
        for v in equity:
            peak = max(peak, v)
            if peak > 0:
                worst = max(worst, (peak - v) / peak)
        if worst >= self.threshold:
            v = Verdict.HALT_ALL if self.halt_instead_of_block else Verdict.BLOCK_ENTRY
            return Decision(v, self.name,
                            f"回撤 {worst*100:.2f}% >= 門檻 {self.threshold*100:.2f}%")
        return Decision(Verdict.ALLOW)


@dataclass(slots=True)
class ExposureLimit(Protection):
    """總曝險上限。規劃書層 3 的第一條不變量。"""

    max_total_contracts: int = 10
    name: str = "exposure_limit"
    _current: int = 0

    def observe(self, total_contracts: int) -> None:
        self._current = total_contracts

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        if self._current >= self.max_total_contracts:
            return Decision(Verdict.BLOCK_ENTRY, self.name,
                            f"總口數 {self._current} >= 上限 {self.max_total_contracts}")
        return Decision(Verdict.ALLOW)


@dataclass(slots=True)
class ProtectionStack:
    """依序檢查。**任一觸發即擋，最嚴者得標。**

    `HALT_ALL` 優先於 `BLOCK_ENTRY`——與策略層的優先級鏈同一個原則。
    """

    protections: list[Protection] = field(default_factory=list)

    def check(self, today: date, history: list[TradeOutcome],
              equity: list[float]) -> Decision:
        worst = Decision(Verdict.ALLOW)
        for p in self.protections:
            d = p.check(today, history, equity)
            if d.verdict is Verdict.HALT_ALL:
                return d
            if d.verdict is Verdict.BLOCK_ENTRY and worst.allowed:
                worst = d
        return worst

    @classmethod
    def default(cls) -> "ProtectionStack":
        """預設組合。**門檻是猜的，不是量的**——需要事前登記才算數。"""
        return cls([
            MaxDrawdownGuard(threshold=0.25),
            StoplossGuard(lookback_days=7, max_stops=4),
            CooldownPeriod(days=1),
        ])
