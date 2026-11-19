"""共用：實際規模換算（微台 2 口）、分段、統計。"""
from __future__ import annotations

CAP = 140_200
LOTS = 2
PV = 10            # 微台 1 點 10 元
TAX = 0.00002      # 期交稅（每邊、依成交價 × 每點價值）
FEE = 12           # 手續費（每口每邊，Willy 11/18 提供）
LIMIT_D3 = CAP * 0.15

# 預先登記的切分（看結果前寫死，2026-11-18）
DESIGN = ("2001-01-01", "2019-12-31")
VALID = ("2020-01-01", "2026-08-22")
HOLD = ("2026-08-23", "2099-12-31")


def micro_net(t) -> float:
    """引擎的 net_ntd 是大台 2 口、含 MC 滑價（市價／停損單每口每邊 5 點）。換成微台 2 口淨額。"""
    pts = t.net_ntd / (200 * 2)
    tax = (t.entry_px + t.exit_px) * PV * TAX * LOTS
    return pts * PV * LOTS - tax - FEE * 2 * LOTS


def seg_of(dt: str) -> str:
    d = dt[:10]
    if d <= DESIGN[1]:
        return "design"
    if d <= VALID[1]:
        return "valid"
    return "hold"


def stats(pnls: list[float]) -> dict:
    eq = peak = 0.0
    mdd = 0.0
    run = longest = 0
    for x in pnls:
        eq += x
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
        run = run + 1 if x < 0 else 0
        longest = max(longest, run)
    gp = sum(x for x in pnls if x > 0)
    gl = -sum(x for x in pnls if x < 0)
    return dict(n=len(pnls), net=sum(pnls), pf=(gp / gl if gl else float("inf")), mdd=mdd,
                streak=longest, win=(sum(1 for x in pnls if x > 0) / len(pnls) if pnls else 0.0))
