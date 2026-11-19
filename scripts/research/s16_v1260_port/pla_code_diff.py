"""兩份 .pla 去掉 { } 註解與空白行後做 diff，只看程式碼差異。"""
import difflib
import re
import sys


def code(p):
    t = open(p, encoding="utf-8", errors="replace").read()
    t = re.sub(r"\{[^}]*\}", "", t)
    return [ln.rstrip() for ln in t.splitlines() if ln.strip()]


a, b = code(sys.argv[1]), code(sys.argv[2])
for ln in difflib.unified_diff(a, b, "a", "b", n=1, lineterm=""):
    print(ln)
