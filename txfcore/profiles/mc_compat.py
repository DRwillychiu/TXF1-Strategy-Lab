"""MC 相容設定：Python 回測要重現 MC 報表時必須同時打開的引擎行為（規則手冊 R4）。

實證範圍（docs/specs/python_port_plan_20261007.md 第六節）：只在 L2、L4（空單）逐筆驗證過。
第 1 項只驗了買停損、買限價（空單出場）；第 4 項只驗了限價出場。多單方向的進位與
限價進場免滑價（L5 兩腿）尚未驗證，移植 L3、L5 時要先用 MC 報表逐筆確認（審查 M4）。
  1 停損／限價價位進位到 tick（買停損往上、賣停損往下）
  2 SetStopLoss 只在空手時呼叫的策略，引擎停損只在進場那一根有效（L1 Guard_Persist 例外，移植時覆寫）
  3 進場那根可被引擎停損打掉
  4 成本口徑：滑價每口每邊 1,000，限價單不加，手續費 0
  5 日 K 依收盤日歸屬（前一晚夜盤＋當天日盤；週五夜盤自成一根）
  6 結算日用 .pla 靜態規則（第三個週三）
  7 TP1 限價與停損可同根先後成交
"""
from __future__ import annotations

from txfcore.engine.fill_mc12 import FillPolicy
from txfcore.instruments.spec import TXF
from txfcore.quotes.daily import NIGHT_FIRST
from txfcore.runtime.backtest import BacktestRunner
from txfcore.runtime.multi import MultiStreamRunner

POLICY = FillPolicy(allow_same_bar_exit=True, round_to_tick=True, engine_stop_entry_bar_only=True)
COST_PER_LOT_SIDE = 1000
DAILY_MODE = NIGHT_FIRST
STATIC_SETTLEMENT = True
MC_LAST_DATE = 1260924          # 目前 MC 報表與 1 分 K 的共同迄日


def single_runner(strategy, policy: FillPolicy = POLICY) -> BacktestRunner:
    return BacktestRunner(strategy, TXF, policy=policy, mc_cost_per_lot_side=COST_PER_LOT_SIDE)


def multi_runner(strategy, policy: FillPolicy = POLICY, warmup_bars: int = 200) -> MultiStreamRunner:
    return MultiStreamRunner(strategy, TXF, policy=policy, warmup_bars=warmup_bars,
                             mc_cost_per_lot_side=COST_PER_LOT_SIDE, allow_multi_exit_per_bar=True)
