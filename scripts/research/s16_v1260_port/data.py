"""讀 MC 1 分 K → S16 用的 5 分 K。放在策略層之外（strategies 不得 import quotes，txfcore/LAYERS.md）。"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from txfcore.quotes.history import MC12MinuteSource  # noqa: E402
from txfcore.strategies.s16_s_v1_26 import Bar5, aggregate_5m  # noqa: E402


def load_bars(path: str | Path, start: datetime | None = None,
              end: datetime | None = None) -> list[Bar5]:
    return aggregate_5m(MC12MinuteSource(path, validate=False).stream(), start, end)
