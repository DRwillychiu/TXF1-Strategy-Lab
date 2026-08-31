# -*- coding: utf-8 -*-
"""七種「邏輯已審查、等接線」的母體 —— 跑指標自己的十二槽鏈.

Willy 2026-08-31：「7 種接線。完整的邏輯分別說明以及完整優化進去指標中。」

七種：P15 頭肩頂／P26 圓弧頂／P32 V 型反轉／P56 死貓反彈／
      P59 穿越型態／P65 塔形頂／P72 訂單塊

定義**原樣取自已審查的來源**，本檔沒有重寫任何一條：
  P26 P32 P56 P59 P65 P72  <- scripts/research/s16s_census15_scan.py
  P15                      <- scripts/research/s16s_hs_scan.py（寬鬆版，零參數）

★ 為什麼要重跑而不是沿用普查的數字

普查用的是「所有連續 k 個交替樞紐」的滑動視窗。指標用的是**滾動鏈**：
十二槽、同型重置、滿了就位移。兩者在乾淨的交替序列上等價，但在同型相鄰
（重置）處不等價。2026-08-30 有一次整份普查跑在錯的鏈上要重算，教訓是
**任何要拿去跟 MC12 對的數字，都要用指標的那份鏈算**。

本檔因此逐根重放 IND_S16S_P29 SECTION 3 的鏈，包含：
  - 樞紐用 High[1] / Low[1]，同時段（S[i] >= 2 且 S[i+1] >= 3）
  - 同一根可同時是樞紐高與低，依 k = 1, 2 先高後低推入
  - 前一個同型 -> 鏈重置為 0
  - 鏈滿十二 -> 丟掉最舊的一個，其餘往前移

Run:  python scripts/research/s16s_seven_scan.py
"""
import collections
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, 's16s_5min.csv')
YRS = [str(y) for y in range(2019, 2027)]
SLOTS = 12


# ---- 述詞：原樣取自 s16s_census15_scan.py，一字未改 ---------------------
def dome(a, b, c, d, e):
    """先升後降，進場減速、出場加速。"""
    return (a < b < c > d > e
            and (b - a) > (c - b)
            and (c - d) < (d - e))


def spike(a, b, c, d, e):
    """先升後降，進場加速、出場減速 —— 一個尖頂。"""
    return (a < b < c > d > e
            and (b - a) < (c - b)
            and (c - d) > (d - e))


def inband(x, p, q):
    return min(p, q) <= x <= max(p, q)


# 每個述詞收一段連續樞紐 s，元素為 (bar, price, typ)，typ 1=高 2=低。
# need = 需要幾個樞紐，start = 這段必須以哪一型開頭。
def P15(s):                                    # 頭肩頂：頭高過兩肩
    return s[0][1] < s[2][1] > s[4][1]


def P26(s):                                    # 圓弧頂：五個高點成圓頂
    return dome(*[s[i][1] for i in (0, 2, 4, 6, 8)])


def P32(s):                                    # V 型反轉：五個高點成尖頂
    return spike(*[s[i][1] for i in (0, 2, 4, 6, 8)])


def P56(s):                                    # 死貓反彈
    h0, l1, h1, l2 = [x[1] for x in s[:4]]
    return l1 < h0 and inband(h1, l1, h0) and l2 < l1


def P59(s):                                    # 穿越型態：一個完成的 J
    h0, l1, l2, l3, h4 = s[0][1], s[1][1], s[3][1], s[5][1], s[6][1]
    return l1 > l2 < l3 and (l1 - l2) > (l3 - l2) and h4 > h0


def P65(s):                                    # 塔形頂：跌得不比漲慢
    l0, h1, l1 = [x[1] for x in s[:3]]
    ub, db = s[1][0] - s[0][0], s[2][0] - s[1][0]
    return h1 > l0 and l1 < l0 and db <= ub


def P72(s):                                    # 訂單塊
    h0, l1, h1 = [x[1] for x in s[:3]]
    return h1 > h0 and l1 < h0


SEVEN = [
    ('P15', '頭肩頂', 5, 1, P15),
    ('P26', '圓弧頂', 9, 1, P26),
    ('P32', 'V 型反轉', 9, 1, P32),
    ('P56', '死貓反彈', 4, 1, P56),
    ('P59', '穿越型態', 7, 1, P59),
    ('P65', '塔形頂', 3, 2, P65),
    ('P72', '訂單塊', 3, 1, P72),
]


def main():
    rows = list(csv.DictReader(io.open(CSV, encoding='utf-8')))
    H = [float(r['high']) for r in rows]
    L = [float(r['low']) for r in rows]
    S = [int(r['bars_in_sess']) for r in rows]
    Y = [r['ymd'] for r in rows]
    N = len(rows)
    print('母體 %s 根   %s ~ %s' % (format(N, ','), Y[0], Y[-1]))

    def is_ph(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and H[i] > H[i - 1] and H[i] > H[i + 1])

    def is_pl(i):
        return (1 <= i < N - 1 and S[i] >= 2 and S[i + 1] >= 3
                and L[i] < L[i - 1] and L[i] < L[i + 1])

    hit = collections.defaultdict(list)
    chain = []
    n_push = n_reset = 0
    for b in range(1, N):
        i = b - 1                              # 指標用 High[1]，樞紐在前一根
        for k in (1, 2):
            if not (is_ph(i) if k == 1 else is_pl(i)):
                continue
            if chain and chain[-1][2] == k:    # 前一個同型 -> 重置
                chain = []
                n_reset += 1
            if len(chain) >= SLOTS:            # 滿了 -> 丟最舊的
                chain = chain[1:]
            chain.append((i, H[i] if k == 1 else L[i], k))
            n_push += 1
            for code, _, need, start, fn in SEVEN:
                if len(chain) < need:
                    continue
                s = chain[-need:]
                if s[0][2] != start:
                    continue
                if fn(s):
                    hit[code].append((s[0][0], s[-1][0]))
    print('推入 %s 次   重置 %s 次   最終鏈長 %d'
          % (format(n_push, ','), format(n_reset, ','), len(chain)))
    print()
    print('=' * 78)
    print('%-6s %-12s %8s %8s %9s %8s' % ('代號', '名稱', '個數', '年均', '跨度中位', '掛零年'))
    print('-' * 78)
    ref = {}
    for code, zh, need, start, _ in SEVEN:
        hs = hit[code]
        ref[code] = len(hs)
        if not hs:
            print('%-6s %-12s %8d' % (code, zh, 0))
            continue
        yr = collections.Counter(Y[a][:4] for a, _ in hs)
        sp = sorted(b - a for a, b in hs)
        print('%-6s %-12s %8s %8.1f %9d %8d'
              % (code, zh, format(len(hs), ','), len(hs) / 7.64,
                 sp[len(sp) // 2], sum(1 for y in YRS if yr[y] == 0)))
        print('       逐年 %s' % '  '.join('%s=%d' % (y, yr[y]) for y in YRS))
    print()
    print('★ 指標驗收用的參考行：')
    print('   SEVEN TALLY  reference  ' + '  '.join(
        '%s=%d' % (c, ref[c]) for c, _, _, _, _ in SEVEN))


if __name__ == '__main__':
    main()
