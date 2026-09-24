#!/usr/bin/env python3
r"""安裝驗證　—— repo 裡的檔案是不是都到位、內容對不對。

```powershell
python tools\verify_install.py
```

**Windows 的 tar 解不開中文檔名**（2026-09-08 實測：六份 PDF 全部
"Invalid empty pathname"），而**解壓縮失敗時前面的檔案已經解好了，
所以工具照樣能跑，只是資料不完整**——那是最難察覺的一種。

本工具逐項檢查：程式碼模組 · 測試 · 資料資產 · 原始 PDF · 行情資料。
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODULES = (
    "txfcore/types/bar.py", "txfcore/types/mctime.py", "txfcore/types/orders.py",
    "txfcore/types/stateful.py", "txfcore/instruments/spec.py",
    "txfcore/instruments/margin.py", "txfcore/instruments/capital.py", "txfcore/costs/fees.py", "txfcore/costs/slippage.py",
    "txfcore/metrics/drawdown.py", "txfcore/metrics/trades.py", "txfcore/timing/clock.py",
    "txfcore/timing/latency.py", "txfcore/lineage/stamp.py",
    "txfcore/indicators/core.py", "txfcore/tradecal/gates.py",
    "txfcore/tradecal/settlement.py", "txfcore/tradecal/registry.py", "txfcore/tradecal/accounting.py",
    "txfcore/quotes/session.py", "txfcore/quotes/bars.py",
    "txfcore/quotes/history.py", "txfcore/quotes/align.py",
    "txfcore/quotes/daily.py", "txfcore/quotes/guard.py",
    "txfcore/quotes/continuous.py", "txfcore/engine/orders.py",
    "txfcore/engine/position.py", "txfcore/engine/fill_mc12.py",
    "txfcore/engine/accounting.py", "txfcore/engine/daily_equity.py",
    "txfcore/engine/fill_slippage.py", "txfcore/strategies/base.py",
    "txfcore/strategies/l1_trendlong.py", "txfcore/strategies/l2_trendshort.py",
    "txfcore/strategies/l3_consollong.py", "txfcore/strategies/l4_consolshort.py",
    "txfcore/strategies/l5_breakoutlong.py", "txfcore/strategies/versions.py",
    "txfcore/parity/diff.py", "txfcore/parity/golden.py",
    "txfcore/parity/invariants.py", "txfcore/parity/anchors.py",
    "txfcore/parity/windows.py", "txfcore/parity/completeness.py",
    "txfcore/risk/protections.py", "txfcore/runtime/backtest.py",
    "txfcore/runtime/multi.py",
)
TOOLS = (
    "tools/audit.py", "tools/audit_port.py", "tools/flow_check.py",
    "tools/modules9.py", "tools/report.py", "tools/signals.py",
    "tools/status.py", "tools/verify_claims.py", "tools/verify_install.py",
    "tools/equity.py", "tools/slippage_impact.py", "tools/m2.py",
)
TESTS = ("tests/test_txfcore.py", "tests/test_engine.py",
         "tests/test_layer_boundaries.py", "tests/test_parity.py",
         "tests/test_oms.py", "tests/test_slippage.py", "tests/test_trades.py")
DOCS = (
    "docs/specs/CAPITAL_AND_MARGIN.md", "docs/specs/ZERO_TRIGGER_TRIAGE.md",
    "docs/specs/PORT_AUDIT_20260907.md", "docs/specs/BACKTEST_MODULE_DESIGN.md",
    "docs/specs/HYPOTHESIS_LOG.md", "docs/specs/strategy_baseline.md",
    "docs/specs/M1_ACCOUNTING.md", "docs/specs/M2_TRADE_STATS.md", "docs/specs/SUMMARY_20260908.md",
    
)
PLA = (
    "strategies/research/L1_TrendLong/L1_v3.2/L1_TrendLong_v3.2.pla",
    "strategies/research/L2_TrendShort/L2_v5.4/L2_TrendShort_v5.4.pla",
    "strategies/research/L3_ConsolidationLong/L3_v15.1/L3_ConsolidationLong_v15.1.pla",
    "strategies/research/L4_ConsolidationShort/L4_v14.7/L4_ConsolidationShort_v14.7.pla",
    "strategies/research/L5_BreakoutLong/L5_v19.9_R1/L5_BreakoutLong_v19.9_R1.pla",
)
DATA_SHA = "CD42303B1FB5300AB39AEC0D9C2B3435AC95B9B91364AB9B31629891E91FBD90"
DATA_PATHS = ("data/mc_export/TXF1 1 分鐘.txt",)
EXPECT_TESTS = 330


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


def check_group(title: str, paths, missing: list) -> tuple[int, int]:
    ok = 0
    for rel in paths:
        p = ROOT / rel
        if p.exists():
            ok += 1
        else:
            missing.append(rel)
    mark = "✓" if ok == len(paths) else "✗"
    print(f"  {mark} {title:<22}{ok}/{len(paths)}")
    return ok, len(paths)


def main() -> int:
    print("=" * 70)
    print(f"安裝驗證　{ROOT}")
    print("=" * 70)
    missing: list[str] = []
    print("\n【檔案是否到位】")
    check_group("txfcore 模組", MODULES, missing)
    check_group("tools 工具", TOOLS, missing)
    check_group("tests 測試", TESTS, missing)
    check_group("docs 文件", DOCS, missing)
    check_group("研究版 .pla", PLA, missing)

    print("\n【保證金原始 PDF】")
    try:
        from txfcore.instruments.margin import PDF_DIR, PDF_SHA256
        bad = []
        for name, want in PDF_SHA256.items():
            p = ROOT / PDF_DIR / name
            if not p.exists():
                bad.append(f"{name}　**檔案不存在**")
                missing.append(f"{PDF_DIR}/{name}")
            elif (got := sha(p)) != want:
                bad.append(f"{name}　雜湊不符 {got[:12]}… ≠ {want[:12]}…")
        mark = "✓" if not bad else "✗"
        print(f"  {mark} PDF 六份　　　　　　　{len(PDF_SHA256)-len(bad)}/{len(PDF_SHA256)}")
        for b in bad:
            print(f"      ✗ {b}")
    except Exception as e:                                    # noqa: BLE001
        print(f"  ✗ 無法載入 margin.py：{e}")

    print("\n【行情資料】")
    found = None
    for rel in DATA_PATHS:
        p = ROOT / rel
        if p.exists():
            found = p
            break
    if not found:
        print(f"  ✗ 找不到　{DATA_PATHS[0]}")
        print("      **不進 git（107 MB），需自行從 MC12 匯出或複製**")
    else:
        got = sha(found)
        mark = "✓" if got == DATA_SHA else "✗"
        print(f"  {mark} {found.name}　{found.stat().st_size:,} bytes")
        print(f"      SHA-256 {got[:16]}…　"
              f"{'與記錄一致' if got == DATA_SHA else '**與記錄不符**'}")

    print("\n【資料資產自檢】")
    try:
        from txfcore.instruments.margin import verify_chain, verify_ratio
        from txfcore.tradecal.settlement import SETTLEMENT_SET
        c, r = verify_chain(), verify_ratio()
        print(f"  {'✓' if not c else '✗'} 保證金鏈結　　　　　斷裂 {len(c)} 處")
        print(f"  {'✓' if not r else '✗'} 保證金比例 20:5:1　違反 {len(r)} 處")
        print(f"  ✓ 結算日曆　　　　　　{len(SETTLEMENT_SET)} 天")
    except Exception as e:                                    # noqa: BLE001
        print(f"  ✗ 資料資產載入失敗：{e}")

    print("\n【測試】")
    try:
        p = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        line = [l for l in p.stdout.splitlines() if "passed" in l or "failed" in l]
        got = line[-1].strip() if line else "無輸出"
        n = 0
        for tok in got.split():
            if tok.isdigit():
                n = int(tok)
                break
        mark = "✓" if n == EXPECT_TESTS and "failed" not in got else "✗"
        print(f"  {mark} {got}　　預期 {EXPECT_TESTS} passed")
        if n > EXPECT_TESTS:
            print("      **多出來的測試代表舊檔案還在硬碟上。**")
            print("      tar 只解壓縮，不會刪除。需手動移除已刪的模組。")
    except Exception as e:                                    # noqa: BLE001
        print(f"  ✗ 測試無法執行：{e}")

    print("\n" + "=" * 70)
    if missing:
        print(f"★ {len(missing)} 個檔案缺失：")
        for m in missing:
            print(f"    {m}")
        print("\n  **Windows 的 tar 遇到中文檔名會失敗**，且失敗時前面的檔案")
        print("  已經解好，所以工具照樣能跑，只是資料不完整。")
        return 1
    print("★ 全部到位")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
