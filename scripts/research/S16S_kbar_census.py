"""
刪除跳空型態後、剩下 21 種在 7,712 個死叉上的實際共現次數
定義依用戶確認版：長實體 >= 50%、十字 < 10% 全距、約略相等 = 完全相同
"""
import io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
_src = open('A1_kbtype_census.py', encoding='utf-8').read().split("# ---------- 5.")[0]
exec(chr(10).join(l for l in _src.split(chr(10)) if not l.startswith("sys.stdout")))


def xav(s, n):
    a = 2.0 / (n + 1); o = [0.0] * len(s); o[0] = s[0]
    for i in range(1, len(s)):
        o[i] = o[i - 1] + a * (s[i] - o[i - 1])
    return o


ZF = xav([C[i] * 2 - C[max(0, i - 12)] for i in range(N)], 25)
ZS = xav([C[i] * 2 - C[max(0, i - 34)] for i in range(N)], 70)
BRK = [seq[i + 1] - seq[i] > 5 for i in range(N - 1)] + [True]

Rng = lambda i: H[i] - L[i]
Bd = lambda i: abs(C[i] - O[i])
BP = lambda i: Bd(i) / Rng(i) if Rng(i) > 0 else 0
Up = lambda i: C[i] > O[i]
Dn = lambda i: C[i] < O[i]
Top = lambda i: max(O[i], C[i])
Bot = lambda i: min(O[i], C[i])
Mid = lambda i: (O[i] + C[i]) / 2
US = lambda i: H[i] - Top(i)
DS = lambda i: Bot(i) - L[i]
LONG = lambda i: BP(i) >= 0.50
DOJI = lambda i: BP(i) < 0.10 and Rng(i) >= 3 and US(i) >= 1 and DS(i) >= 1


def pats(i):
    """i = 訊號那根。回傳成立的型態名稱集合。需要 i-2 可用。"""
    f = set()
    a, b = i - 1, i - 2            # a = 前一根, b = 前二根
    two = a >= 0 and not BRK[a]
    three = two and b >= 0 and not BRK[b]

    if two:
        # A 類
        if Up(a) and Dn(i) and O[i] >= C[a] and C[i] <= O[a] and Bd(i) > Bd(a):
            f.add('A01 空頭吞噬')
        if Dn(a) and Up(i) and O[i] <= C[a] and C[i] >= O[a] and Bd(i) > Bd(a):
            f.add('A02 多頭吞噬')
        if Up(a) and LONG(a) and Dn(i) and Top(i) <= C[a] and Bot(i) >= O[a]:
            f.add('A05 空頭孕線')
        if Dn(a) and LONG(a) and Up(i) and Top(i) <= O[a] and Bot(i) >= C[a]:
            f.add('A06 多頭孕線')
        if Up(a) and LONG(a) and DOJI(i) and Top(i) <= C[a] and Bot(i) >= O[a]:
            f.add('A07 空頭十字孕線')
        if Dn(a) and LONG(a) and DOJI(i) and Top(i) <= O[a] and Bot(i) >= C[a]:
            f.add('A08 多頭十字孕線')
        if H[i] <= H[a] and L[i] >= L[a]:
            f.add('A09 內含線')
        if H[i] >= H[a] and L[i] <= L[a]:
            f.add('A10 外包線')
        if H[i] == H[a] and Up(a) and Dn(i):
            f.add('A18 鑷子頂')
        if L[i] == L[a] and Dn(a) and Up(i):
            f.add('A19 鑷子底')

    if three:
        if (Dn(b) and Dn(a) and Dn(i) and LONG(b) and LONG(a) and LONG(i)
                and C[a] < C[b] and C[i] < C[a]
                and O[a] < O[b] and O[a] > C[b] and O[i] < O[a] and O[i] > C[a]):
            f.add('B25 三隻烏鴉')
        if (Up(b) and Up(a) and Up(i) and LONG(b) and LONG(a) and LONG(i)
                and C[a] > C[b] and C[i] > C[a]
                and O[a] > O[b] and O[a] < C[b] and O[i] > O[a] and O[i] < C[a]):
            f.add('B26 三白兵')
        if (Up(b) and LONG(b) and Dn(a) and Top(a) <= C[b] and Bot(a) >= O[b]
                and Dn(i) and C[i] < C[a]):
            f.add('B27 三內部下跌')
        if (Dn(b) and LONG(b) and Up(a) and Top(a) <= O[b] and Bot(a) >= C[b]
                and Up(i) and C[i] > C[a]):
            f.add('B28 三內部上漲')
        if (Up(b) and Dn(a) and O[a] >= C[b] and C[a] <= O[b] and Bd(a) > Bd(b)
                and Dn(i) and C[i] < C[a]):
            f.add('B29 三外部下跌')
        if (Dn(b) and Up(a) and O[a] <= C[b] and C[a] >= O[b] and Bd(a) > Bd(b)
                and Up(i) and C[i] > C[a]):
            f.add('B30 三外部上漲')
        if (Dn(b) and Dn(a) and Dn(i) and LONG(b) and LONG(a) and LONG(i)
                and O[a] == C[b] and O[i] == C[a] and C[a] < C[b] and C[i] < C[a]):
            f.add('B34 三胎鴉')
        if (Up(b) and Up(a) and Up(i) and C[a] > C[b] and C[i] > C[a]
                and Bd(a) < Bd(b) and Bd(i) < Bd(a)
                and US(a) > 0 and US(i) > 0 and US(i) > US(b)):
            f.add('B35 大敵當前')
        if (Up(b) and Up(a) and Up(i) and LONG(b) and LONG(a)
                and C[a] > C[b] and C[i] > C[a]
                and Bd(i) < Bd(a) / 2 and O[i] >= C[a]):
            f.add('B36 步步為營')
        if (Dn(b) and Dn(a) and Dn(i) and LONG(b) and DS(b) > 0
                and O[a] < O[b] and O[a] > C[b] and L[a] > L[b] and Bd(a) < Bd(b)
                and H[i] <= H[a] and L[i] >= L[a] and Bd(i) < Bd(a)):
            f.add('B37 南方三星')
        if (Dn(b) and LONG(b) and Dn(a) and O[a] <= O[b] and O[a] >= C[b]
                and L[a] < L[b] and C[a] > C[b]
                and Up(i) and Bd(i) < Bd(a) and C[i] < C[a]):
            f.add('B38 獨特三河床')
    return f


cnt = collections.Counter()
tot = 0
for i in range(200, N - 30):
    if not (ZF[i - 1] >= ZS[i - 1] and ZF[i] < ZS[i]):
        continue
    tot += 1
    for p in pats(i):
        cnt[p] += 1

SIDE = {'A01': '支持', 'A02': '反對', 'A05': '支持', 'A06': '反對', 'A07': '支持',
        'A08': '反對', 'A09': '中性', 'A10': '中性', 'A18': '支持', 'A19': '反對',
        'B25': '支持', 'B26': '反對', 'B27': '支持', 'B28': '反對', 'B29': '支持',
        'B30': '反對', 'B34': '支持', 'B35': '支持', 'B36': '支持',
        'B37': '反對', 'B38': '反對'}
print('死叉總數 %s' % '{:,}'.format(tot))
print()
print('=' * 66)
print('  21 種型態在死叉當下的實際共現次數')
print('=' * 66)
print('%-20s %6s %8s %8s' % ('型態', '對空單', '次數', '佔死叉%'))
print('-' * 66)
for k in sorted(SIDE, key=lambda x: -cnt.get([n for n in cnt if n.startswith(x)][0] if any(n.startswith(x) for n in cnt) else '', 0)):
    nm = next((n for n in cnt if n.startswith(k)), None)
    c = cnt.get(nm, 0) if nm else 0
    label = nm if nm else k
    print('%-20s %6s %8d %7.2f%%' % (label, SIDE[k], c, c / tot * 100))
print('-' * 66)
print('  本腳本只普查次數,不做分類判定.')
print('  舊的 n >= 50 門檻已作廢 -- 無依據,見 spec 4.5.1.')
print('  分類(1 進檢定 / 2 以邏輯納入)見 spec 4.5.3 與 5/6 節的表.')
print('  正式門檻待 spec 8.0 量出檢定母體基準率後,依 8.1 檢定力計算訂定.')
