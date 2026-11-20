"""用最後結算價量近月期現價差（只描述，不含進出場規則）。
最後結算價 = 當天 13:00-13:30 加權指數平均（月合約與週合約同一算法），所以每個結算日（多為週三）
都能量一次：近月價差 = TXF1 在 13:01-13:30 的平均收盤 - 最後結算價。
來源：Willy 11/20 提供的期交所最後結算價 PDF，用 pdftotext 轉成文字（fsp_pdf_text_20261120.txt）。
Usage: python -I scripts/research/calspread_20261120/basis_weekly.py <fsp文字檔> <TXF1 1分.txt> <out.md> <out.csv> [起始年=2020]
"""
import re, sys, statistics as st
from collections import defaultdict

def parse_fsp(path):
    rows = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s*(\d{4})/(\d{2})/(\d{2})\s+(\d{6})(W\d)?\s+(\S+)", ln)
        if m and re.fullmatch(r"\d+(\.\d+)?", m.group(6)):
            d = f"{int(m.group(1))}/{int(m.group(2))}/{int(m.group(3))}"
            rows.append((d, m.group(4) + (m.group(5) or ""), float(m.group(6)), "週" if m.group(5) else "月"))
    return rows

def dkey(s):
    y, m, d = s.split("/")
    return (int(y), int(m), int(d))

def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]

def main():
    fsp_path, f1, out, csv = sys.argv[1:5]
    y0 = int(sys.argv[5]) if len(sys.argv) > 5 else 2020
    rows = parse_fsp(fsp_path)
    with open(csv, "w", encoding="utf-8", newline="\n") as f:
        f.write("date,contract,type,tx_final_settlement\n")
        for d, c, v, k in sorted(rows, key=lambda r: dkey(r[0])):
            f.write(f"{d},{c},{k},{v:g}\n")
    want = {r[0] for r in rows if dkey(r[0])[0] >= y0}
    win, last, cnt, c1330 = defaultdict(list), defaultdict(str), defaultdict(int), {}
    with open(f1, encoding="utf-8", errors="replace") as f:
        next(f)
        for ln in f:
            p = ln.split(",")
            if int(p[0].split("/")[0]) < y0:
                continue
            t = p[1][:5]
            if "08:46" <= t <= "13:45":
                last[p[0]] = max(last[p[0]], t); cnt[p[0]] += 1
                if p[0] in want and "13:01" <= t <= "13:30":
                    win[p[0]].append(float(p[5]))
                    if t == "13:30":
                        c1330[p[0]] = float(p[5])
    days = sorted(cnt, key=dkey)
    settle = {d for d in days if last[d] <= "13:30" and cnt[d] > 200}
    dts, nxt = {}, None
    for d in reversed(days):
        if d in settle:
            nxt = 0
        dts[d] = nxt
        if nxt is not None:
            nxt += 1
    monthly = {r[0] for r in rows if r[3] == "月" and dkey(r[0])[0] >= y0}
    L = [f"# 用最後結算價量近月期現價差（{y0} 起）", "",
         "- 價差 = 近月期貨 13:01–13:30 平均 − 最後結算價（當天 13:00–13:30 加權指數平均）。負數＝逆價差。",
         f"- 結算價表：月合約 {sum(r[3]=='月' for r in rows)} 筆、週合約 {sum(r[3]=='週' for r in rows)} 筆，{min(rows,key=lambda r:dkey(r[0]))[0]}–{max(rows,key=lambda r:dkey(r[0]))[0]}。", "",
         "## 一、對帳：結算價表的月結算日 vs 由 1 分 K 反推的結算日"]
    L.append(f"- 表上月結算日 {len(monthly)} 個，1 分 K 反推 {len(settle)} 個；只在表上：{sorted(monthly - settle, key=dkey)}；只在 1 分 K：{sorted(settle - monthly, key=dkey)}")
    fspd = {r[0]: r[2] for r in rows if r[3] == "月"}
    diff = [c1330[d] - fspd[d] for d in sorted(monthly & settle, key=dkey) if d in c1330]
    L.append(f"- 月結算日：近月 13:30 最後一根收盤 − 最後結算價，{len(diff)} 天；中位 {st.median(diff):.0f} 點，最小 {min(diff):.0f}，最大 {max(diff):.0f}，絕對值中位 {st.median([abs(x) for x in diff]):.0f}")
    obs = []
    for d, c, v, k in rows:
        if d in win and len(win[d]) >= 20 and dts.get(d) is not None:
            b = st.mean(win[d]) - v
            obs.append((d, dts[d], b, b / v * 100))
    def table(title, keyf, order=None):
        g = defaultdict(list)
        for o in obs:
            g[keyf(o)].append(o)
        L.extend(["", title, "| 分組 | 次數 | 中位數（點） | 5% | 95% | 中位數（%） | 逆價差比例 |", "|---|---|---|---|---|---|---|"])
        for k in (order or sorted(g)):
            if k in g:
                p = [o[2] for o in g[k]]; r = [o[3] for o in g[k]]
                L.append(f"| {k} | {len(p)} | {st.median(p):.0f} | {q(p,.05):.0f} | {q(p,.95):.0f} | {st.median(r):.2f} | {sum(x<0 for x in p)/len(p)*100:.0f}% |")
    def bucket(o):
        k = o[1]
        return "0（結算日）" if k == 0 else "1–7 天" if k <= 7 else "8–12 天" if k <= 12 else "13–17 天" if k <= 17 else "18 天以上"
    table("## 二、依距離月結算的交易日數", bucket, ["18 天以上", "13–17 天", "8–12 天", "1–7 天", "0（結算日）"])
    nz = [o for o in obs if o[1] > 0]
    obs_all = obs[:]
    obs[:] = nz
    table("## 三、逐年（不含月結算日）", lambda o: dkey(o[0])[0])
    table("## 四、逐月份（不含月結算日）", lambda o: dkey(o[0])[1])
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))

if __name__ == "__main__":
    main()
