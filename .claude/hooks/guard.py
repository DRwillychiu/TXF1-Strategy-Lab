"""TXF1 PreToolUse guard for Bash / PowerShell commands.

Enforces what CLAUDE.md says only Willy does:
  - Claude never commits or pushes (Willy runs push.bat)      -> deny
  - baselines and live .pla change only with Willy's consent  -> ask
Edit-tool writes to strategies/live and tools/baselines are handled by
permissions.ask in .claude/settings.json; this script closes the shell route.
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
PROTECTED = r"strategies/live|tools/baselines"
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


def main():
    data = json.load(sys.stdin)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    c = cmd.replace("\\", "/")
    for pat, why in DENY:
        if re.search(pat, c, re.I):
            decide("deny", why)
    for pat, why in ASK:
        if re.search(pat, c, re.I):
            decide("ask", why)
    if re.search(PROTECTED, c, re.I) and re.search(WRITES, c, re.I):
        decide("ask", "這個指令會用 shell 改動實盤檔或基準檔（strategies/live、tools/baselines），需要 Willy 同意；只是要讀的話改用 Read 工具。")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
