"""TXF1 PreToolUse guard for Bash / PowerShell commands and file-writing tools.

Enforces what CLAUDE.md says only Willy does:
  - Claude never commits or pushes (Willy runs push.bat)      -> deny
  - baselines and live .pla change only with Willy's consent  -> ask in default/acceptEdits/plan,
    deny in auto (auto mode let an ask through without a prompt, 2026-11-27 live test)
    (Write / Edit / MultiEdit / NotebookEdit by target path; shell commands by write verbs)
Wired by .claude/settings.json matcher "Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit";
tests/test_claude_hooks.py checks that wiring (2026-11-27: "Bash\\|PowerShell" matched no tool at all).
Prints a PreToolUse decision as JSON and always exits 0 (JSON is only applied on exit 0).
"""
import json
import re
import sys

DENY = [
    (r"\bgit\b[^\n;&|]*\b(commit|push)\b", "Claude 不 commit、不 push：整理好檔案後請 Willy 執行 push.bat。"),
    (r"\bpush\.bat\b", "push.bat 由 Willy 執行：它會先跑檢查、列出檔案請他確認。"),
]
ASK = [
    (r"\bmake_baseline\.py\b", "產生基準檔需要 Willy 核准（只能用他核准的版本，並單獨一次推送）。"),
]
PROTECTED = r"strategies/live(?![\w-])|tools/baselines"
FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
LIVE_REASON = ("要改實盤檔或基準檔（strategies/live、tools/baselines）：需要 Willy 同意；"
               "研究版請放 strategies/research/。")
WRITES = (r"(^|[\s;&|(])(cp|mv|rm|tee|touch|sed\s+-i|copy|move|del|ren|"
          r"Copy-Item|Move-Item|Remove-Item|Rename-Item|Set-Content|Add-Content|Out-File|New-Item)\b"
          r"|(?<![0-9&])>(?!&)")


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


ASK_MODES = {"default", "acceptEdits", "plan"}   # 這些模式的 ask 會跳確認給 Willy
AUTO_NOTE = ("（權限模式：{mode}。自動模式會把「先問」自動放行（2026-11-27 實測），所以這裡直接擋下；"
             "Willy 同意要改時，請他把權限模式切成 default 再叫我做，會跳出確認。）")


def consent(data, reason):
    """需要 Willy 同意的動作：會跳確認的模式回 ask；自動模式或不知道模式時回 deny。"""
    mode = data.get("permission_mode")
    if mode in ASK_MODES:
        decide("ask", reason)
    decide("deny", reason + AUTO_NOTE.format(mode=mode or "未提供"))


def main():
    data = json.load(sys.stdin)
    inp = data.get("tool_input") or {}
    if data.get("tool_name") in FILE_TOOLS:   # 寫檔工具：看目標路徑
        path = (inp.get("file_path") or inp.get("notebook_path") or "").replace("\\", "/")
        if re.search(r"(^|/)(strategies/live|tools/baselines)/", path, re.I):
            consent(data, LIVE_REASON)
        return
    cmd = inp.get("command") or ""
    c = cmd.replace("\\", "/")
    for pat, why in DENY:
        if re.search(pat, c, re.I):
            decide("deny", why)
    for pat, why in ASK:
        if re.search(pat, c, re.I):
            consent(data, why)
    if re.search(PROTECTED, c, re.I) and re.search(WRITES, c, re.I):
        consent(data, "這個指令會用 shell 改動實盤檔或基準檔（strategies/live、tools/baselines），需要 Willy 同意；只是要讀的話改用 Read 工具。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
