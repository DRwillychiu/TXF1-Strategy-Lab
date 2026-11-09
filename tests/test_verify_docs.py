"""G0（CLAUDE.md／PROJECT.md）與 G0b R6（上架檔 ＝ LIVE_VERSIONS 所列版本）的回歸測試。"""
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


verify_docs = _load("verify_docs")
verify_versions = _load("verify_versions")

GOOD_CLAUDE = """<context>
- 現況：@PROJECT.md
</context>
<commands>
- 測試：pytest
</commands>
<project_rules>
- 規則一。原因：測試用。
</project_rules>
"""

GOOD_PROJECT = """## 目前狀態
- 最後更新：2026-10-31
## 下一步
1. 一
2. 二
## 考題
## 決策紀錄
- 2026-10-01｜決定：甲｜原因：乙｜放棄的選項：丙
- 2026-10-31｜決定：甲｜原因：乙｜放棄的選項：丙
## 已知坑
"""


def test_repo_docs_pass_g0():
    assert verify_docs.check(ROOT) == []


def test_claude_rule_without_reason_fails():
    bad = GOOD_CLAUDE.replace("規則一。原因：測試用。", "規則一，沒寫理由")
    assert verify_docs.check_claude(GOOD_CLAUDE) == []
    assert any("沒寫原因" in x for x in verify_docs.check_claude(bad))


def test_claude_missing_block_fails():
    bad = GOOD_CLAUDE.replace("<commands>", "").replace("</commands>", "")
    assert any("<commands>" in x for x in verify_docs.check_claude(bad))


def test_project_next_steps_capped_at_three():
    assert verify_docs.check_project(GOOD_PROJECT) == []
    bad = GOOD_PROJECT.replace("2. 二", "2. 二\n3. 三\n4. 四")
    assert any("下一步" in x for x in verify_docs.check_project(bad))


def test_project_decision_log_is_append_only_and_formatted():
    swapped = GOOD_PROJECT.replace("2026-10-01｜", "2026-11-30｜")
    assert any("依序" in x for x in verify_docs.check_project(swapped))
    malformed = GOOD_PROJECT.replace("｜放棄的選項：丙\n- 2026-10-31", "\n- 2026-10-31")
    assert any("格式錯誤" in x for x in verify_docs.check_project(malformed))


def test_eval_pointing_to_missing_test_fails(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_real():\n    pass\n", encoding="utf-8")
    proj = tmp_path / "PROJECT.md"
    proj.write_text("`tests/test_a.py::test_real`　`test_real`", encoding="utf-8")
    assert verify_docs.check_links(tmp_path, [proj]) == []
    proj.write_text("`tests/test_a.py::test_gone`　`test_ghost`", encoding="utf-8")
    out = verify_docs.check_links(tmp_path, [proj])
    assert any("test_gone" in x for x in out) and any("test_ghost" in x for x in out)


def test_live_folder_matches_live_versions():
    """2026-10-31：G1 好幾週都在檢查 10/5 前的舊上架檔。上架檔必須 ＝ LIVE_VERSIONS 所列研究版。"""
    fails, _ = verify_versions.live_check(ROOT)
    assert fails == []


def test_live_check_catches_stale_live_file(tmp_path):
    for rel in ["docs/LIVE_VERSIONS.md",
                "strategies/live/L2_TrendShort/L2_TrendShort.pla",
                "strategies/research/L2_TrendShort/L2_v5.11/L2_TrendShort_v5.11.pla"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    lv = tmp_path / "docs/LIVE_VERSIONS.md"
    lv.write_text("\n".join(l for l in lv.read_text(encoding="utf-8").splitlines()
                            if not l.startswith(("| **L1", "| **L3", "| **L4", "| **L5"))), encoding="utf-8")
    assert verify_versions.live_check(tmp_path)[0] == []
    (tmp_path / "strategies/live/L2_TrendShort/L2_TrendShort.pla").write_text("old", encoding="utf-8")
    assert any("L2_TrendShort" in x for x in verify_versions.live_check(tmp_path)[0])
