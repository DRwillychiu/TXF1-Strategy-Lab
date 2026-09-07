"""資料版本守門。

**2026-09-07 的實際事故**：換一台機器跑，`data/` 不在 git 裡所以沒同步。
而那台硬碟上有**三份**同名或近似的檔案：

    Multichart_9\\報價\\TXF1 1 分鐘.txt        107,247,523
    Multichart_9\\報價\\TXF1 1 分鐘0703.txt     96,478,761   ← 兩個月前的舊版
    Downloads\\TXF1 1 分鐘.txt                107,247,523

**指到舊版就會跑出一堆對不上的數字，而那看起來會像程式錯了。**

更嚴重的是 `tradecal/settlement.py` 的 92 天結算日曆是從**特定版本**的資料
反推出來的。換資料而不重推，日曆就是錯的，而且不會有任何東西報錯。

所以工具啟動時必須先驗雜湊，不一致**立刻停**。
"""

from __future__ import annotations

from pathlib import Path

from txfcore.lineage.stamp import sha256_file
from txfcore.tradecal.settlement import SOURCE_ROWS, SOURCE_SHA256


class DataVersionMismatch(RuntimeError):
    """資料版本與記錄的不符。**不做寬鬆處理。**"""


def check(path: str | Path, expected: str = SOURCE_SHA256,
          strict: bool = True) -> tuple[bool, str]:
    """驗證資料檔的 SHA-256。回傳 (是否一致, 實際雜湊)。

    `strict = True` 時不一致即拋例外，因為結算日曆是從特定版本反推的。
    """
    actual = sha256_file(path)
    ok = actual.lower() == expected.lower()
    if not ok and strict:
        raise DataVersionMismatch(
            f"資料版本不符，停止。\n"
            f"  檔案    {path}\n"
            f"  實際    {actual}\n"
            f"  記錄    {expected}\n"
            f"\n"
            f"結算日曆的 {SOURCE_ROWS:,} 列 / 92 天是從記錄的那一版反推的。\n"
            f"若這是新匯出的資料，需要：\n"
            f"  1. 重新反推結算日曆（日盤末根戳記 = 1330 的日子）\n"
            f"  2. 更新 settlement.py 的 SOURCE_SHA256 / SOURCE_ROWS / VERIFIED_UNTIL\n"
            f"  3. 全部 anchor 對比重跑\n"
            f"若這是舊版檔案，改用正確的路徑。"
        )
    return ok, actual


def banner(path: str | Path) -> str:
    """工具開頭印的一行。"""
    ok, actual = check(path, strict=False)
    mark = "✓ 與 settlement.py 記錄的一致" if ok else "✗ 不一致 —— 結算日曆可能是錯的"
    return f"資料 SHA-256  {actual[:12]}…   {mark}"
