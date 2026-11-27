r"""Claude Code 設定的接線考題：hook 的 matcher 真的對得到工具名稱，guard 對關鍵指令的判定正確。

2026-11-27 的教訓：matcher 寫成 "Bash\|PowerShell"（含反斜線，會被當成正則，\| 是字面的直線符號），
一個工具都對不到。用假輸入測 guard 全部正確，但真實 session 裡 hook 從來沒被呼叫。這份考題擋住同樣的錯。
"""
import json
import pathlib
import re
import socket
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETTINGS = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
GUARD = ROOT / ".claude" / "hooks" / "guard.py"
TOOLS = ("Bash", "PowerShell", "Write", "Edit", "MultiEdit", "NotebookEdit", "Read", "Glob")


def matches(matcher, tool):
    """Claude Code 的規則：空字串或 * 對到全部；只含英數、底線、| 是精確名稱清單；其他當正則。"""
    if matcher in ("", "*"):
        return True
    if re.fullmatch(r"[A-Za-z0-9_|]+", matcher):
        return tool in matcher.split("|")
    return re.search(matcher, tool) is not None


def hooked(event="PreToolUse", script="guard.py"):
    out = set()
    for entry in SETTINGS.get("hooks", {}).get(event, []):
        if any(script in h.get("command", "") for h in entry.get("hooks", [])):
            out |= {t for t in TOOLS if matches(entry.get("matcher", ""), t)}
    return out


def decision(tool, mode=None, **tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input}
    if mode:
        payload["permission_mode"] = mode
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "allow"


def test_matcher_semantics_self_check():
    assert not matches(r"Bash\|PowerShell", "Bash")      # 2026-11-27 的錯誤寫法：什麼都對不到
    assert matches("Bash|PowerShell", "PowerShell") and not matches("Bash|PowerShell", "Write")


def test_guard_wired_to_shell_and_file_tools():
    assert {"Bash", "PowerShell", "Write", "Edit", "MultiEdit", "NotebookEdit"} <= hooked()
    assert not {"Read", "Glob"} & hooked()


def test_stop_hook_wired():
    assert any("stop_verify.py" in h.get("command", "") for e in SETTINGS["hooks"]["Stop"] for h in e["hooks"])


LIVE = str(ROOT / "strategies" / "live" / "_probe.txt")


@pytest.mark.parametrize("tool, inp, want", [
    ("Bash", {"command": "git push --dry-run"}, "deny"),
    ("Bash", {"command": "git -C . push --dry-run"}, "deny"),
    ("PowerShell", {"command": "git commit -m x"}, "deny"),
    ("PowerShell", {"command": r'.\push.bat "msg"'}, "deny"),
    ("Bash", {"command": "git status --short"}, "allow"),
    ("Bash", {"command": "cat strategies/live/L1_TrendLong/L1_TrendLong.pla"}, "allow"),
    ("Bash", {"command": "cp a.pla strategies/live/L1_TrendLong/L1_TrendLong.pla"}, "ask"),
    ("Bash", {"command": "echo x > strategies/live_simulation/a.txt"}, "allow"),
    ("Bash", {"command": "python tools/make_baseline.py L1"}, "ask"),
    ("Write", {"file_path": LIVE, "content": "x"}, "ask"),
    ("Edit", {"file_path": str(ROOT / "tools" / "baselines" / "b.json"), "old_string": "a", "new_string": "b"}, "ask"),
    ("Write", {"file_path": str(ROOT / "strategies" / "live_simulation" / "a.md"), "content": "x"}, "allow"),
    ("Write", {"file_path": str(ROOT / "strategies" / "research" / "a.md"), "content": "x"}, "allow"),
])
@pytest.mark.parametrize("mode", ["default", "acceptEdits", "auto", None])
def test_guard_decisions(tool, inp, want, mode):
    # 需要 Willy 同意的動作：會跳確認的模式是 ask；自動模式（或沒給模式）會自動放行 ask，所以改成 deny
    expect = "deny" if want == "ask" and mode not in ("default", "acceptEdits") else want
    assert decision(tool, mode, **inp) == expect
