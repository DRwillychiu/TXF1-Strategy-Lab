"""期交所保證金　資料資產。

**來源**：期交所新聞稿 PDF（`docs/data/taifex_margin/`）。
每一則公告載明公告日、生效日、調整前後三個金額。

## 裁決 2026-09-08

```
回測      用**當前最新保證金**，不做歷史查表，不拒絕交易
組合監控  M6 才需要保證金檢查（實戰用途）
```

理由：回測是為了實戰，而實戰用的是現在的保證金。
歷史查表留給 M6 的組合監控與事後歸因。

## 為什麼仍然存時間序列

**因為保證金在 2026 年漲了 70%**（微台 20,600 → 35,050），
而那個變化直接影響「同時能開幾口」——那是組合監控要回答的問題。

實測（微台 2 口/支）：

```
                     每口可用    現在需要         撐不住的起點
帳戶 A 多 20 萬 / 6 口  33,333   210,300（105%）   2026-08-12
帳戶 B 空 10 萬 / 4 口  25,000   140,200（140%）   2026-04-22
```

> 空單帳戶（L2 · L4）現在需要 140%。
> 但 L2 是趨勢空頭，**只在週 K 20MA 之下啟動**，
> 多頭週期本來就不觸發，所以 4 口同時開倉是罕見情況。

## ★ 結構性事實：保證金比例恆等於點值比例

```
TX : MTX : TMF  =  20 : 5 : 1     六個時點全部成立
點值             200 :  50 : 10  =  20 : 5 : 1
```

**這條在 `verify_ratio()` 裡機器檢查。** 若某次公告打破它，代表
期交所改了計算方式，或我抄錯了——兩者都必須立刻知道。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

# 生效時點：公告寫「自 X 月 X 日一般交易時段結束後起實施」。
# **理解為該日 13:45 日盤收盤後生效，當晚夜盤開始適用。**
# 未經用戶確認，標為待確認。
EFFECTIVE_AFTER_DAY_CLOSE = True
EFFECTIVE_TIME = 1345

# 當沖減收：期交所對最近兩個到期月份、僅限一般交易時段的當沖交易
# 減收 50% 保證金。**五支策略均有跨夜部位，預設不適用。**
DAY_TRADE_DISCOUNT_APPLIES = False


@dataclass(frozen=True, slots=True)
class MarginRow:
    """一個商品在一個時點的三個保證金。"""

    initial: int        # 原始保證金：建立新部位的門檻
    maintenance: int    # 維持保證金：持有期間的生死線
    clearing: int       # 結算保證金：期貨商與期交所之間，我們用不到


@dataclass(frozen=True, slots=True)
class Announcement:
    """一則調整公告。"""

    announced: date
    effective: date
    source: str                     # PDF 檔名
    after: dict[str, MarginRow]     # 調整後
    before: dict[str, MarginRow]    # 調整前


def _r(i: int, m: int, c: int) -> MarginRow:
    return MarginRow(i, m, c)


# ---------------------------------------------------------------------------
# 資料。**新增公告時只改這裡，並跑 verify_chain() 確認鏈結不斷。**
# ---------------------------------------------------------------------------
ANNOUNCEMENTS: tuple[Announcement, ...] = (
    Announcement(
        date(2026, 3, 10), date(2026, 3, 11),
        "taifex_margin_20260310.pdf",
        {"TX": _r(454000, 348000, 336000),
         "MTX": _r(113500, 87000, 84000),
         "TMF": _r(22700, 17400, 16800)},
        {"TX": _r(412000, 316000, 305000),
         "MTX": _r(103000, 79000, 76250),
         "TMF": _r(20600, 15800, 15250)},
    ),
    Announcement(
        date(2026, 3, 31), date(2026, 4, 1),
        "taifex_margin_20260331.pdf",
        {"TX": _r(477000, 366000, 353000),
         "MTX": _r(119250, 91500, 88250),
         "TMF": _r(23850, 18300, 17650)},
        {"TX": _r(454000, 348000, 336000),
         "MTX": _r(113500, 87000, 84000),
         "TMF": _r(22700, 17400, 16800)},
    ),
    Announcement(
        date(2026, 4, 21), date(2026, 4, 22),
        "taifex_margin_20260421.pdf",
        {"TX": _r(526000, 403000, 389000),
         "MTX": _r(131500, 100750, 97250),
         "TMF": _r(26300, 20150, 19450)},
        {"TX": _r(477000, 366000, 353000),
         "MTX": _r(119250, 91500, 88250),
         "TMF": _r(23850, 18300, 17650)},
    ),
    Announcement(
        date(2026, 5, 26), date(2026, 5, 27),
        "taifex_margin_20260526.pdf",
        {"TX": _r(578000, 443000, 428000),
         "MTX": _r(144500, 110750, 107000),
         "TMF": _r(28900, 22150, 21400)},
        {"TX": _r(526000, 403000, 389000),
         "MTX": _r(131500, 100750, 97250),
         "TMF": _r(26300, 20150, 19450)},
    ),
    Announcement(
        date(2026, 6, 17), date(2026, 6, 18),
        "taifex_margin_20260617.pdf",
        {"TX": _r(636000, 488000, 471000),
         "MTX": _r(159000, 122000, 117750),
         "TMF": _r(31800, 24400, 23550)},
        {"TX": _r(578000, 443000, 428000),
         "MTX": _r(144500, 110750, 107000),
         "TMF": _r(28900, 22150, 21400)},
    ),
    Announcement(
        date(2026, 8, 11), date(2026, 8, 12),
        "taifex_margin_20260811.pdf",
        {"TX": _r(701000, 538000, 519000),
         "MTX": _r(175250, 134500, 129750),
         "TMF": _r(35050, 26900, 25950)},
        {"TX": _r(636000, 488000, 471000),
         "MTX": _r(159000, 122000, 117750),
         "TMF": _r(31800, 24400, 23550)},
    ),
)

PRODUCTS = ("TX", "MTX", "TMF")

# 原始 PDF 的 SHA-256。**檔名改成 ASCII 是因為 Windows 的 tar
# 解不開中文檔名**（2026-09-08 實測：六份全部 "Invalid empty pathname"）。
# 檔名雖改，內容雜湊不變，可據此驗證安裝是否完整。
PDF_SHA256: dict[str, str] = {
    "taifex_margin_20260310.pdf":
        "28A397A35DB3F1817CF0E551FD82FD0BA5A0F4891BF20B335CDE960A0CBD6E5B",
    "taifex_margin_20260331.pdf":
        "5A25EADA68A298F9071D012FF6881181A46C318960D9D28012508D3991C2C7C8",
    "taifex_margin_20260421.pdf":
        "D542302151911EA8A1425344241771EAD05A3338046F540538D5873253A7A576",
    "taifex_margin_20260526.pdf":
        "60E0299D39EFA19A7B616545DFBF6EAA3A5E5D9C019445C0DA5D8B46ED04B0F8",
    "taifex_margin_20260617.pdf":
        "D4B24675D9356660BA579249AFD0091251A76F39A3D47DB865B381EE3587464B",
    "taifex_margin_20260811.pdf":
        "43C5985B1FC2722F9F5D340945B9ADDCA4A83A4035C3474E4A6428993D0F073F",
}
PDF_DIR = "docs/data/taifex_margin"

# 驗證範圍。最早的一筆是第一則公告的「調整前」，其生效日不詳。
VERIFIED_FROM = ANNOUNCEMENTS[0].effective
VERIFIED_UNTIL = ANNOUNCEMENTS[-1].effective
UNKNOWN_BEFORE = ANNOUNCEMENTS[0].effective   # 此日之前只有一筆推定值

# 商品代號對照。**小台是 MTX，不是 MXF**（2026-09-08 修正）。
TXFCORE_CODE = {"TX": "TXF", "MTX": "MXF", "TMF": "TMF"}
POINT_VALUE = {"TX": 200, "MTX": 50, "TMF": 10}


class MarginChainBroken(RuntimeError):
    """鏈結斷裂：某筆的「調整前」不等於前一筆的「調整後」。"""


class MarginOutOfRange(RuntimeError):
    """查詢日期超出已驗證範圍。**不猜，直接拒絕。**"""


def verify_chain() -> list[str]:
    """每筆的「調整前」必須等於前一筆的「調整後」。

    **斷鏈代表漏了一則公告。** 漏了就會用錯保證金，而數字看起來仍然合理。
    """
    bad = []
    for i in range(1, len(ANNOUNCEMENTS)):
        prev, cur = ANNOUNCEMENTS[i - 1], ANNOUNCEMENTS[i]
        for p in PRODUCTS:
            if prev.after[p] != cur.before[p]:
                bad.append(
                    f"{cur.announced} {p}：前份調整後 {prev.after[p].initial:,}"
                    f" ≠ 本份調整前 {cur.before[p].initial:,}")
    return bad


def verify_ratio() -> list[str]:
    """保證金比例必須恆等於點值比例 TX : MTX : TMF = 20 : 5 : 1。

    打破它代表期交所改了計算方式，或資料抄錯——**兩者都必須立刻知道**。
    """
    bad = []
    for a in ANNOUNCEMENTS:
        for label, book in (("調整後", a.after), ("調整前", a.before)):
            tmf = book["TMF"].initial
            for p, mult in (("TX", 20), ("MTX", 5)):
                if book[p].initial != tmf * mult:
                    bad.append(f"{a.effective} {label} {p}："
                               f"{book[p].initial:,} ≠ {tmf:,} × {mult}")
    return bad


def current(product: str = "TMF") -> MarginRow:
    """當前保證金。**回測用這個**（裁決 2026-09-08）。"""
    return ANNOUNCEMENTS[-1].after[product]


def as_of(day: date, product: str = "TMF", strict: bool = True) -> MarginRow:
    """某一天適用的保證金。**供 M6 組合監控與事後歸因使用。**

    `strict = True` 時，早於已驗證範圍即拋例外——**不外插，不猜**。
    """
    if day < UNKNOWN_BEFORE:
        if strict:
            raise MarginOutOfRange(
                f"{day} 早於已驗證範圍（{UNKNOWN_BEFORE} 起）。\n"
                f"該日的保證金需要更早的公告才能確定。\n"
                f"若只是要粗估，改用 strict=False 會回傳"
                f"第一則公告的『調整前』值，**但那不是該日的真實值**。")
        return ANNOUNCEMENTS[0].before[product]
    row = ANNOUNCEMENTS[0].after[product]
    for a in ANNOUNCEMENTS:
        if a.effective <= day:
            row = a.after[product]
        else:
            break
    return row


def max_lots(capital: float, day: date | None = None,
             product: str = "TMF") -> int:
    """該筆資金在該時點最多能開幾口（以原始保證金計）。"""
    m = current(product) if day is None else as_of(day, product)
    return int(capital // m.initial)


def source_hash() -> str:
    """資料指紋。**改了資料而沒改雜湊，就是有人偷改。**"""
    blob = "|".join(
        f"{a.effective}:{a.source}:" + ",".join(
            f"{p}={a.after[p].initial}/{a.after[p].maintenance}/{a.after[p].clearing}"
            for p in PRODUCTS)
        for a in ANNOUNCEMENTS)
    return hashlib.sha256(blob.encode()).hexdigest().upper()


def timeline() -> list[tuple[date, dict[str, int]]]:
    """原始保證金的時間序列，供報告使用。"""
    out = [(UNKNOWN_BEFORE, {p: ANNOUNCEMENTS[0].before[p].initial
                             for p in PRODUCTS})]
    for a in ANNOUNCEMENTS:
        out.append((a.effective, {p: a.after[p].initial for p in PRODUCTS}))
    return out
