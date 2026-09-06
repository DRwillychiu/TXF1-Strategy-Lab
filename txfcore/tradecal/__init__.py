"""行事曆閘門。假日註冊表 + 結算日曆 + 偵測邏輯。"""

from __future__ import annotations

import hashlib
import json


def calendar_hash() -> str:
    """本套件全部行事曆資料的雜湊。任一筆日期變動即改變。

    **模組自己雜湊自己的內容**——放在 lineage/ 會讓層 0 反向依賴支撐層。
    2026-09-06 由分層檢查抓出並修正。
    """
    from txfcore.tradecal.registry import HOLIDAY_TAIL, REGISTRY_VALID_UNTIL
    from txfcore.tradecal.settlement import SETTLEMENT_DAYS, VERIFIED_UNTIL

    payload = {
        "holiday_tail": list(HOLIDAY_TAIL),
        "registry_valid_until": REGISTRY_VALID_UNTIL,
        "settlement_days": list(SETTLEMENT_DAYS),
        "settlement_verified_until": VERIFIED_UNTIL,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
