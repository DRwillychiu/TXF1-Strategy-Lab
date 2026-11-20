"""六支策略 MC 投資組合報告 → 換算實盤（微台 2 口）年化報酬與回撤。
Usage: python -I scripts/research/portfolio_20261120/portfolio_annual.py <投資組合績效報告.xls(x)> <out.md> <TXF1 1 分鐘.txt> [資金=300000]

口徑：
- MC 報告是大台（每點 200 元）、每支 2 口、滑價每口每邊 1,000 元；實盤是微台（每點 10 元）2 口 → 金額 ÷ 20。
- 資金：多單帳戶 15 萬（L1、L3、L5）＋空單帳戶 15 萬（L2、L4、L6）＝ 30 萬（Willy 11/20）。
- 年化 ＝ 單利（期間淨利 ÷ 資金 ÷ 年數），因為口數固定、不複利。
- 回撤用「每日平倉損益」累積（Daily 週期分析），不含持倉中浮動；MC 的「投組最大可能虧損」另列。
"""
import datetime as dt
import shutil
import sys
import tempfile

import openpyxl

SCALE = 20


def main():
    src, out = sys.argv[1], sys.argv[2]
    f1 = sys.argv[3]
    cap = float(sys.argv[4]) if len(sys.argv) > 4 else 300000.0
    px = {}
    with open(f1, encoding="utf-8", errors="replace") as f:
        next(f)
        for ln in f:
            q = ln.split(",")
            if q[0] >= "2019" or q[0][:4] >= "2019":
                y, m, d = map(int, q[0].split("/"))
                if y >= 2019:
                    px[dt.date(y, m, d)] = float(q[5])  # 每天最後一根收盤
    tmp = tempfile.mkdtemp()
    p = shutil.copy(src, tmp + "/r.xlsx")  # 原檔是 xlsx 內容、副檔名 .xls
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)

    st = {r[0]: r[1:] for r in wb["策略分析"].iter_rows(values_only=True) if r[0]}
    cfg = {r[0]: r[1] for r in wb["設定"].iter_rows(values_only=True) if r[0]}
    t0, t1 = cfg["開始日期"], cfg["結束日期"]
    t0 = dt.datetime(t0.year, t0.month, t0.day)
    daily = sorted((r[0], r[1]) for r in wb["Daily 週期分析"].iter_rows(values_only=True)
                   if isinstance(r[0], dt.datetime))
    syms = [r for r in wb["商品概要"].iter_rows(values_only=True) if r[0] and str(r[0]).startswith("TXF1")]
    eqa = {i: r for i, r in enumerate(r for r in wb["權益曲線分析"].iter_rows(values_only=True)
                                       if r[0] and str(r[0]).startswith("TXF1"))}

    total = sum(v for _, v in daily)
    assert abs(total - st["淨利"][0]) < 1, (total, st["淨利"][0])  # 每日加總 = MC 總淨利

    def years(a, b):
        return (b - a).total_seconds() / 86400 / 365.25

    # 回撤（每日平倉）
    eq = pk = mdd = 0.0
    mdd_d = None
    for d, v in daily:
        eq += v / SCALE
        if eq > pk:
            pk = eq
        if pk - eq > mdd:
            mdd, mdd_d = pk - eq, d

    L = ["# 六支策略組合：實盤口徑年化（2026-11-20，MC 投資組合報告換算）", "",
         f"- 來源：Willy 11/20 匯出的 MC 投資組合績效報告（六支，{t0:%Y-%m-%d} ～ {t1:%Y-%m-%d}）",
         f"- 換算：大台 → 微台 ÷{SCALE}；資金 {cap:,.0f}（多單帳戶 15 萬＋空單帳戶 15 萬）；年化＝單利", "",
         "## 一、結論", ""]

    def span(a):
        s = sum(v for d, v in daily if d >= a) / SCALE
        y = years(a, t1)
        return s, y, s / cap / y * 100

    pdays = sorted(px)
    now_px = px[pdays[-1]]

    def ratio(d):
        import bisect
        i = bisect.bisect_right(pdays, d.date()) - 1
        return now_px / px[pdays[max(i, 0)]]

    def span_now(a):
        s = sum(v * ratio(d) for d, v in daily if d >= a) / SCALE
        return s / cap / years(a, t1) * 100

    rows = []
    for lab, a in (("全期", t0), ("六支都有交易起（2021-05-12）", dt.datetime(2021, 5, 12)),
                   ("2023 起", dt.datetime(2023, 1, 1)), ("2025 起", dt.datetime(2025, 1, 1))):
        s, y, ann = span(a)
        rows.append((lab, s, y, ann, span_now(a)))
    L += ["| 期間 | 淨利（元，微台） | 年數 | 年化（單利） | 換算今天指數位階的年化 |", "|---|---|---|---|---|"]
    L += [f"| {lab} | {s:,.0f} | {y:.2f} | **{ann:.1f}%** | {an:.1f}% |" for lab, s, y, ann, an in rows]
    L += ["", f"- 換算今天指數位階：每天損益 × (最新 TXF1 收盤 {now_px:,.0f} ÷ 當天收盤)。固定口數下，指數越高每點波動越大，"
          "早年損益偏小，換算後才是『今天上線』可期待的比例（推論）。"]
    L += ["", f"- 最大回撤（每日平倉）：{mdd:,.0f} 元 ＝ 資金的 {mdd / cap * 100:.1f}%（低點 {mdd_d:%Y-%m-%d}）",
          f"- MC 投組最大可能虧損（含持倉浮動）：{st['投組最大可能虧損'][0] / SCALE:,.0f} 元 ＝ 資金的 "
          f"{-st['投組最大可能虧損'][0] / SCALE / cap * 100:.1f}%（{st['最大投組虧損日期'][0]}）", ""]

    L += ["## 二、逐年", "", "| 年 | 淨利（元，微台） | 佔資金 | 換算今天指數位階 | 備註 |", "|---|---|---|---|---|"]
    by, bn = {}, {}
    for d, v in daily:
        by[d.year] = by.get(d.year, 0) + v / SCALE
        bn[d.year] = bn.get(d.year, 0) + v * ratio(d) / SCALE
    for y in sorted(by):
        note = "部分年度（%s 起）" % f"{t0:%m-%d}" if y == t0.year else ("到 %s" % f"{t1:%m-%d}" if y == t1.year else "")
        L.append(f"| {y} | {by[y]:,.0f} | {by[y] / cap * 100:.1f}% | {bn[y] / cap * 100:.1f}% | {note} |")

    names = {"45": "L1 趨勢多", "60": "L2 趨勢空", "5 ": "L6 均線空"}
    L += ["", "## 三、各支（MC 報告原值 ÷20）", "",
          "| 策略（時間框架） | 起 | 筆數 | 淨利（元，微台） | 最大拉回（元，微台） |", "|---|---|---|---|---|"]
    for i, r in enumerate(syms):
        nm = r[0].replace("TXF1 (", "").replace(" Minutes)", "M")
        L.append(f"| {nm} | {r[1]:%Y-%m-%d} | {r[4]} | {r[3] / SCALE:,.0f} | {eqa[i][1] / SCALE:,.0f} |")
    L += ["", "- 對應：45M＝L1、60M＝L2、5M＝L6（145 筆，和 L6 MC 驗收筆數相同）；三支 15M＝L3、L4、L5（報告未標名，待確認哪支是哪支）",
          "- 所有數字是 MC 回測換算（推論），不是實盤對帳單。"]
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    sys.stdout.buffer.write(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
