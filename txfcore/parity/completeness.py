"""模組功能完整度。

**`test_layer_boundaries.py` 只驗「誰不准 import 誰」，
沒有任何東西驗「這個套件該做的事做完了沒」。**

`contracts/` 定義了十個 Protocol。本模組檢查每一個有沒有實作。
**介面在、實作空**，是目前最大的一類缺口。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Capability:
    protocol: str          # contracts 裡的 Protocol 名稱
    package: str           # 應該實作它的套件
    impls: tuple[str, ...]  # 已知的實作類別
    why: str               # 沒有它會怎樣


CAPABILITIES: tuple[Capability, ...] = (
    Capability("Clock", "timing", ("BarClock", "SystemClock"),
               "策略層會直接讀系統時間，同一份程式碼在兩端行為不同"),
    Capability("QuoteSource", "quotes", ("MC12MinuteSource",),
               "無法接即時報價"),
    Capability("FillModel", "engine", ("MC12FillModel",),
               "無法撮合"),
    Capability("PositionBook", "engine", ("PositionBook",),
               "無法追蹤部位"),
    Capability("ParityChecker", "parity", ("compare",),
               "無法對帳"),
    Capability("OrderSink", "notify/broker", (),
               "**訂單送不出去。專案終點的一半。**"),
    Capability("Journal", "journal", (),
               "**無法重放。實盤出事時無法重現「那天系統看到的市場」**"),
    Capability("StateStore", "state", (),
               "**重啟後拿不回 v_Frozen_SL 這類值**"),
    Capability("KillSwitch", "state", (),
               "**需要停時停不了。實盤第一個功能，不是最後一個**"),
    Capability("Observer", "obs", (),
               "沒有心跳，無法區分「系統正常」與「策略迴圈卡死」"),
    Capability("TriggerMonitor", "obs", (),
               "**唯一能抓到 L2 停擺 443 天的東西**"),
    Capability("RiskGate", "risk", (),
               "**口數無人決定，訂單型別上送不出去**"),
)

# 已寫但沒有任何呼叫者的模組
ORPHANS: tuple[tuple[str, str], ...] = (
    ("risk/protections.py", "四個保護器全部存在，**沒有任何東西呼叫它們**"),
    ("timing/latency.py", "MeasuredLatency 樣本數 = 0，一筆實盤延遲都沒錄"),
    ("engine/orders.py", "訂單狀態機寫好了，runtime 還沒用它"),
    ("quotes/continuous.py", "只做換月標記，沒做 back-adjust 接續"),
    ("lineage/stamp.py", "血緣算得出來，**報告上沒印**"),
)

MISSING_MODULES: tuple[tuple[str, str], ...] = (
    ("engine/context.py", "IOG tick 生命週期。**擋住 L1 的正確性**"),
    ("engine/reality.py", "真實成交模型。**現在用的是 MC 的樂觀假設**"),
    ("runtime/live.py", "dry-run。**從 MC12 切換的唯一安全路徑**"),
    ("risk/reconcile.py", "券商部位對帳迴路"),
    ("parity/mc_report.py", "讀 MC12 的 Excel 報告"),
    ("parity/live_record.py", "讀實戰成交紀錄。**回測 vs 實戰對帳的前提**"),
)


def implemented(cap: Capability) -> bool:
    return bool(cap.impls)


def summary() -> tuple[int, int]:
    done = sum(1 for c in CAPABILITIES if implemented(c))
    return done, len(CAPABILITIES)
