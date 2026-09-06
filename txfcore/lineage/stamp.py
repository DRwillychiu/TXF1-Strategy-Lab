"""血緣雜湊。

每份結果攜帶產生它的全部上游雜湊：程式碼、組態、資料、行事曆。

加了這個，L3 那類「基準線自己從 360 變 361」的事故在**結構上不可能**發生——
新舊結果的雜湊不同，`diff` 會直接拒絕比較，而不是印出一堆無意義的差異。

> 這是規劃書 §3.4 的第五個機制「不可變匯出」的實作。
> 原本只寫了「MC12 報告要加 SHA-256」，但真正需要的是
> **每份結果攜帶全部上游**——只雜湊報告，換了程式碼還是比得下去。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj) -> str:
    """組態物件的雜湊。鍵排序，確保同內容同雜湊。"""
    return sha256_text(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str))


@dataclass(frozen=True, slots=True)
class Lineage:
    """四個上游。任一改變，結果就不可與舊結果比較。"""

    code: str      # txfcore 的 git commit 或原始碼樹雜湊
    config: str    # 策略參數 + 容差門檻
    data: str      # 報價來源檔案
    calendar: str  # 假日註冊表 + 結算日曆

    def matches(self, other: "Lineage") -> bool:
        return self == other

    def diff_fields(self, other: "Lineage") -> list[str]:
        return [k for k in ("code", "config", "data", "calendar")
                if getattr(self, k) != getattr(other, k)]

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def short(self) -> str:
        return " ".join(f"{k}:{v[:8]}" for k, v in self.to_dict().items())


class LineageMismatch(ValueError):
    """上游不同的兩份結果不得比較。

    這是 diff 的守門員：與其印出一堆無法解釋的差異，
    不如直接說「你在比兩個不同的東西」。
    """


def require_match(ours: Lineage, theirs: Lineage) -> None:
    if not ours.matches(theirs):
        bad = ours.diff_fields(theirs)
        raise LineageMismatch(
            f"上游不一致，拒絕比較。不同的欄位：{bad}\n"
            f"  ours   {ours.short}\n"
            f"  theirs {theirs.short}"
        )


def code_hash(root: str | Path = "txfcore") -> str:
    """原始碼樹雜湊。逐檔內容排序後合併。"""
    root = Path(root)
    h = hashlib.sha256()
    for f in sorted(root.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        h.update(f.relative_to(root).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()
