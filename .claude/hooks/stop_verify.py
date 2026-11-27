"""TXF1 Stop hook: before Claude ends a turn, run the same checks as verify.bat.

  - nothing changed in the working tree        -> allow
  - this stop already follows a hook block     -> allow (stop_hook_active; avoids loops)
  - a check fails                              -> exit 2, the tail of its output goes back to Claude
This is a strong nudge, not a hard gate: the hard gate is push.bat / .githooks/pre-commit.
"""
import json
import os
import subprocess
import sys

CHECKS = [
    ("G0 文件", ["python", "tools/verify_docs.py", "."]),
    ("G0b 版本同步", ["python", "tools/verify_versions.py", "."]),
    ("G1 靜態", ["python", "tools/verify_static.py", "strategies/live"]),
    ("委託名稱", ["python", "tools/check_order_names.py", "strategies/live"]),
    ("單元測試", ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]),
]


def run(cmd, env):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return 0
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if not run(["git", "status", "--porcelain"], env).stdout.strip():
        return 0
    for name, cmd in CHECKS:
        r = run(cmd, env)
        if r.returncode:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-25:])
            print(f"收尾檢查沒過（{name}）：{' '.join(cmd)}\n{tail}\n"
                  "修好再收尾；修不好就照實回報「部分完成」與原因。", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
