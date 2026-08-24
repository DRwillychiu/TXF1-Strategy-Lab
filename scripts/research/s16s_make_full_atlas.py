# -*- coding: utf-8 -*-
"""The complete pattern universe -> one HTML atlas.

Part 1  candlestick patterns   68  (33 coded + 23 gap-excluded + 12 single-bar)
Part 2  chart formations       32  (17 defined + 15 not coded)

Coded candlesticks are drawn from the UNIT TEST FIXTURES, so those drawings
are shapes the shipped .pla provably fires on. Everything else is drawn from
its textbook definition and is labelled as such.
"""
import io, os, sys
sys.path.insert(0, os.path.abspath('scripts/research'))
from s16s_kbar_unittest import FIX

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', '..', 'docs', 'research', 'S16S_pattern_atlas_full.html')

# ------------------------------------------------------------------ 1. data
CODED = {
 1: ('空頭吞噬', 'Bearish Engulfing', 27249, 40),
 2: ('空頭孕線', 'Bearish Harami', 28880, 1),
 3: ('空頭十字孕線', 'Bearish Harami Cross', 6091, 0),
 4: ('鑷子頂', 'Tweezers Top', 15085, 6),
 5: ('高價配', 'Matching High', 1879, 0),
 6: ('三隻烏鴉', 'Three Black Crows', 567, 2),
 7: ('三內部下跌', 'Three Inside Down', 12469, 12),
 8: ('三外部下跌', 'Three Outside Down', 11334, 19),
 9: ('三胎鴉', 'Identical Three Crows', 1165, 5),
 10: ('大敵當前', 'Advance Block', 2100, 0),
 11: ('步步為營', 'Deliberation', 2991, 0),
 12: ('下降三法', 'Falling Three Methods', 5, 0),
 13: ('三線打擊（跌）', 'Bearish Three Line Strike', 177, 2),
 14: ('空頭 Hikkake', 'Bearish Hikkake', 6425, 4),
 15: ('下降之鷹', 'Descending Hawk', 3598, 0),
 16: ('多頭吞噬', 'Bullish Engulfing', 27760, 0),
 17: ('多頭孕線', 'Bullish Harami', 28018, 0),
 18: ('多頭十字孕線', 'Bullish Harami Cross', 5747, 0),
 19: ('鑷子底', 'Tweezers Bottom', 14275, 0),
 20: ('低價配', 'Matching Low', 1837, 0),
 21: ('三白兵', 'Three White Soldiers', 628, 0),
 22: ('三內部上漲', 'Three Inside Up', 12470, 0),
 23: ('三外部上漲', 'Three Outside Up', 12113, 0),
 24: ('南方三星', 'Three Stars in the South', 9, 0),
 25: ('獨特三河床', 'Unique Three River Bottom', 1, 0),
 26: ('上升三法', 'Rising Three Methods', 12, 0),
 27: ('梯底', 'Ladder Bottom', 11, 0),
 28: ('三線打擊（漲）', 'Bullish Three Line Strike', 189, 0),
 29: ('內含線', 'Inside Bar', 87942, 1),
 30: ('外包線', 'Outside Bar', 65039, 26),
 31: ('多頭 Hikkake', 'Bullish Hikkake', 4132, 0),
 32: ('家鴿', 'Homing Pigeon', 3509, 0),
 33: ('三明治', 'Stick Sandwich', 3341, 0),
}
BULL3 = set(range(21, 29)) | {31}
BEAR, BULL, NEU = list(range(1, 16)), list(range(16, 29)) + [31, 32, 33], [29, 30]

# gap-dependent, structurally excluded (intraday gap median is 1 point)
GAPX = [
 ('空', '烏雲罩頂', 'Dark Cloud Cover', 2, '開盤 > 前根最高'),
 ('空', '頸上線', 'On-Neck Line', 2, '開盤 < 前根最低'),
 ('空', '頸內線', 'In-Neck Line', 2, '開盤 < 前根最低'),
 ('空', '插入線', 'Thrusting Line', 2, '開盤 < 前根最低'),
 ('空', '空頭分手線', 'Bearish Separating Lines', 2, '開盤跳離前根收盤'),
 ('空', '空頭反擊線', 'Bearish Counterattack', 2, '開盤 > 前根最高'),
 ('空', '夜星', 'Evening Star', 3, '第 2 根實體向上跳離'),
 ('空', '夜十字星', 'Evening Doji Star', 3, '同上 ＋ 十字'),
 ('空', '空頭棄嬰', 'Bearish Abandoned Baby', 3, '兩側都跳空'),
 ('空', '雙飛烏鴉', 'Upside Gap Two Crows', 3, '第 2 根向上跳離'),
 ('空', '向下跳空三法', 'Downside Gap Three Methods', 5, '兩黑棒間留缺口'),
 ('多', '貫穿線', 'Piercing Line', 2, '開盤 < 前根最低'),
 ('多', '晨星', 'Morning Star', 3, '第 2 根實體向下跳離'),
 ('多', '晨十字星', 'Morning Doji Star', 3, '同上 ＋ 十字'),
 ('多', '多頭棄嬰', 'Bullish Abandoned Baby', 3, '兩側都跳空'),
 ('多', '多頭分手線', 'Bullish Separating Lines', 2, '開盤跳離前根收盤'),
 ('多', '會遇線', 'Bullish Counterattack', 2, '開盤 < 前根最低'),
 ('多', '向上跳空三法', 'Upside Gap Three Methods', 5, '兩白棒間留缺口'),
 ('多', '並排白線', 'Side-by-Side White Lines', 3, '第 2 根向上跳空'),
 ('多', '脫離型態', 'Breakaway', 5, '第 2 根跳空'),
 ('多', '執墊', 'Mat Hold', 5, '第 2 根向上跳空'),
 ('多', '藏嬰吞沒', 'Concealing Baby Swallow', 4, '第 3 根向下跳空'),
 ('中', '上升／下降缺口', 'Rising / Falling Window', 2, '定義本身就是缺口'),
]

# single-bar, excluded by the two-bar floor
ONEBAR = [
 ('空', '流星', 'Shooting Star', '上影 ≥ 2×實體，下影 ≈ 0'),
 ('空', '吊人', 'Hanging Man', '下影 ≥ 2×實體，上影 ≈ 0'),
 ('空', '墓碑十字', 'Gravestone Doji', '開 ＝ 收 ＝ 最低'),
 ('空', '空頭捉腰帶線', 'Bearish Belt Hold', '開盤 ＝ 最高，長黑'),
 ('空', '光頭光腳黑棒', 'Black Marubozu', '開 ＝ 最高 且 收 ＝ 最低'),
 ('空', '長黑實體', 'Long Black Candle', '實體 ≥ 50% 區間　★ 已是元件 v_KB_L0'),
 ('多', '錘子', 'Hammer', '下影 ≥ 2×實體，出現在下跌後'),
 ('多', '倒錘', 'Inverted Hammer', '上影 ≥ 2×實體，出現在下跌後'),
 ('多', '蜻蜓十字', 'Dragonfly Doji', '開 ＝ 收 ＝ 最高'),
 ('多', '多頭捉腰帶線', 'Bullish Belt Hold', '開盤 ＝ 最低，長白'),
 ('多', '光頭光腳白棒', 'White Marubozu', '開 ＝ 最低 且 收 ＝ 最高'),
 ('多', '長白實體', 'Long White Candle', '實體 ≥ 50% 區間　★ 已是元件'),
 ('中', '十字線', 'Doji', '實體 < 10% 區間　★ 已是元件 KB_Pat_DojiRatio'),
 ('中', '陀螺', 'Spinning Top', '小實體 ＋ 上下影都長'),
 ('中', '長腳十字', 'Long-Legged Doji', '十字 ＋ 上下影都很長'),
]

# ---- chart formations. path = polyline in a 120x76 box, y down = price up ----
CHART = [
 ('P01', 'NR4', 'Narrowest of 4', '收斂', 4, 92582, 1, 'candle',
  [(0, 40, 8, 62), (0, 34, 10, 58), (0, 38, 20, 52), (0, 42, 30, 46)], '—'),
 ('P02', 'NR7', 'Narrowest of 7', '收斂', 7, 51970, 0, 'candle',
  [(0, 30, 6, 66), (0, 34, 12, 62), (0, 32, 18, 58), (0, 36, 24, 54),
   (0, 38, 30, 50), (0, 40, 34, 48), (0, 42, 40, 46)], '—'),
 ('P03', '內含線 ×2', 'Two Inside Bars', '收斂', 2, 12684, 0, 'candle',
  [(0, 24, 4, 70), (0, 32, 12, 62), (0, 40, 20, 54)], '—'),
 ('P04', '內含線 ×3', 'Three Inside Bars', '收斂', 3, 1738, 0, 'candle',
  [(0, 20, 2, 72), (0, 28, 10, 64), (0, 36, 18, 56), (0, 42, 26, 50)], '—'),
 ('P05', 'ID/NR4', 'Inside AND NR4', '收斂', 4, 41479, 0, 'candle',
  [(0, 30, 8, 64), (0, 34, 14, 60), (0, 38, 22, 54), (0, 42, 32, 48)], '—'),
 ('P06', '三根遞減區間', 'Three Shrinking Ranges', '收斂', 3, 63010, 5, 'candle',
  [(0, 22, 4, 70), (0, 30, 14, 62), (0, 38, 24, 52)], '—'),
 ('P08', '下降三角', 'Descending Triangle', '空', 8, 7320, 0, 'line',
  [(4, 8), (22, 62), (40, 22), (58, 62), (76, 36), (94, 62), (112, 50)],
  [((4, 8), (94, 40)), ((22, 62), (112, 62))]),
 ('P09', '上升三角', 'Ascending Triangle', '多', 8, 8986, 2, 'line',
  [(4, 66), (22, 14), (40, 52), (58, 14), (76, 38), (94, 14), (112, 26)],
  [((4, 14), (112, 14)), ((4, 66), (94, 30))]),
 ('P10', '對稱三角', 'Symmetrical Triangle', '續勢', 8, 78621, 35, 'line',
  [(4, 8), (22, 68), (40, 20), (58, 58), (76, 32), (94, 46), (112, 38)],
  [((4, 8), (112, 38)), ((4, 68), (112, 38))]),
 ('P11', '上升楔形', 'Rising Wedge', '空', 8, 59380, 16, 'line',
  [(4, 66), (22, 30), (40, 56), (58, 22), (76, 44), (94, 16), (112, 34)],
  [((4, 30), (94, 12)), ((4, 70), (112, 26))]),
 ('P12', '下降楔形', 'Falling Wedge', '多', 8, 45614, 25, 'line',
  [(4, 10), (22, 46), (40, 20), (58, 54), (76, 32), (94, 60), (112, 42)],
  [((4, 10), (112, 50)), ((4, 46), (112, 64))]),
 ('P13', '空方旗形', 'Bear Flag', '空', 4, 20938, 40, 'line',
  [(4, 6), (26, 58), (40, 44), (52, 54), (64, 40), (76, 50), (88, 36),
   (100, 60), (114, 70)],
  [((26, 52), (100, 32)), ((26, 64), (100, 44))]),
 ('P14', '空方三角旗', 'Bear Pennant', '空', 5, 4634, 2, 'line',
  [(4, 6), (26, 58), (42, 34), (56, 60), (70, 42), (82, 54), (92, 48),
   (104, 64), (114, 72)],
  [((26, 30), (98, 50)), ((26, 66), (98, 50))]),
 ('P17', '雙頂', 'Double Top', '空', 8, 17960, 2, 'line',
  [(4, 64), (24, 14), (46, 46), (68, 14), (90, 50), (112, 68)],
  [((4, 14), (112, 14)), ((4, 46), (112, 46))]),
 ('P19', '雙底', 'Double Bottom', '多', 8, 16784, 1, 'line',
  [(4, 12), (24, 62), (46, 30), (68, 62), (90, 26), (112, 8)],
  [((4, 62), (112, 62)), ((4, 30), (112, 30))]),
 ('P20', '下降通道', 'Descending Channel', '空', 8, 104841, 57, 'line',
  [(4, 12), (22, 40), (40, 22), (58, 50), (76, 32), (94, 60), (112, 42)],
  [((4, 10), (112, 40)), ((4, 42), (112, 72))]),
 ('P22', '箱型', 'Rectangle / Box', '中性', 8, 1405, 0, 'line',
  [(4, 58), (22, 20), (40, 58), (58, 20), (76, 58), (94, 20), (112, 40)],
  [((4, 20), (112, 20)), ((4, 58), (112, 58))]),
]

NOTCODED = [
 ('P07', '布林帶寬擠壓', 'Bollinger Squeeze', '收斂', '需 BB 長度、標準差、回看 —— 三個自由參數', 'line',
  [(4, 40), (20, 26), (36, 48), (52, 34), (68, 42), (84, 38), (100, 40), (114, 66)],
  [((4, 16), (100, 34)), ((4, 64), (100, 46))]),
 ('P15', '頭肩頂', 'Head and Shoulders', '空', '需 5 樞紐；樞紐間隔中位數 4 根 → 跨度 20-25 根，5 分 K 噪音壓過形狀', 'line',
  [(4, 66), (20, 34), (34, 54), (50, 10), (66, 54), (82, 30), (98, 56), (114, 70)],
  [((20, 54), (114, 56))]),
 ('P16', '頭肩底', 'Inverse Head and Shoulders', '多', '同上', 'line',
  [(4, 10), (20, 42), (34, 22), (50, 66), (66, 22), (82, 46), (98, 20), (114, 6)],
  [((20, 22), (114, 20))]),
 ('P18', '三重頂', 'Triple Top', '空', '三個樞紐高完全相等 —— 全歷史近乎不出現', 'line',
  [(4, 62), (20, 14), (36, 46), (52, 14), (68, 46), (84, 14), (100, 50), (114, 66)],
  [((4, 14), (114, 14)), ((4, 46), (114, 46))]),
 ('P21', '上升通道', 'Ascending Channel', '多', '可編碼，尚未接線（P20 的鏡像）', 'line',
  [(4, 64), (22, 36), (40, 54), (58, 26), (76, 44), (94, 16), (112, 34)],
  [((4, 66), (112, 36)), ((4, 34), (112, 4))]),
 ('P23', '三重底', 'Triple Bottom', '多', '三個樞紐低完全相等 —— 近乎不出現', 'line',
  [(4, 14), (20, 62), (36, 30), (52, 62), (68, 30), (84, 62), (100, 26), (114, 10)],
  [((4, 62), (114, 62)), ((4, 30), (114, 30))]),
 ('P24', '多方旗形', 'Bull Flag', '多', '可編碼；旗桿需要「暴漲棒」定義，本策略只有暴跌棒（斜率閘門）', 'line',
  [(4, 70), (26, 18), (40, 32), (52, 22), (64, 36), (76, 26), (88, 40),
   (100, 16), (114, 6)],
  [((26, 24), (100, 44)), ((26, 12), (100, 32))]),
 ('P25', '多方三角旗', 'Bull Pennant', '多', '同上', 'line',
  [(4, 70), (26, 18), (42, 42), (56, 16), (70, 34), (82, 22), (92, 28),
   (104, 12), (114, 4)],
  [((26, 46), (98, 26)), ((26, 10), (98, 26))]),
 ('P26', '圓弧頂', 'Rounding Top', '空', '需曲線擬合 —— 擬合階數本身就是自由參數', 'line',
  [(4, 66), (18, 46), (32, 28), (46, 16), (60, 12), (74, 16), (88, 28),
   (102, 46), (114, 66)], []),
 ('P27', '圓弧底', 'Rounding Bottom', '多', '同上', 'line',
  [(4, 10), (18, 30), (32, 48), (46, 60), (60, 64), (74, 60), (88, 48),
   (102, 30), (114, 10)], []),
 ('P28', '杯柄', 'Cup and Handle', '多', '需曲線擬合 ＋ 數十根，5 分 K 不可行', 'line',
  [(4, 12), (16, 34), (28, 52), (42, 62), (56, 62), (70, 52), (82, 34),
   (92, 14), (100, 30), (108, 24), (114, 6)], []),
 ('P29', '擴散三角／喇叭形', 'Broadening Formation', '中性', '可編碼（三角的反向），高遞增 ＋ 低遞減', 'line',
  [(4, 40), (20, 26), (36, 50), (54, 16), (72, 58), (92, 8), (112, 68)],
  [((4, 34), (112, 6)), ((4, 44), (112, 70))]),
 ('P30', '鑽石頂', 'Diamond Top', '空', '先擴散後收斂 —— 兩段組合，需要分段點（自由參數）', 'line',
  [(4, 40), (18, 28), (32, 52), (48, 14), (64, 62), (80, 24), (94, 48),
   (106, 34), (114, 60)],
  [((4, 40), (48, 12)), ((48, 12), (114, 40)), ((4, 40), (64, 64)), ((64, 64), (114, 40))]),
 ('P31', '島狀反轉', 'Island Reversal', '空', '定義是兩側缺口 —— 已結構性排除（盤中跳空中位數 1 點）', 'line',
  [(4, 62), (20, 40), (34, 26), (44, 20), (56, 14), (68, 16), (78, 20),
   (92, 34), (106, 52), (114, 66)], []),
 ('P32', 'V 型反轉', 'V Reversal', '空', '無形狀約束可寫 —— 「急漲後急跌」不是幾何定義', 'line',
  [(4, 66), (24, 48), (44, 26), (60, 8), (76, 28), (96, 48), (114, 66)], []),
]


# ------------------------------------------------------------------ 2. draw
def candles(bars):
    lo = min(b[2] for b in bars)
    hi = max(b[1] for b in bars)
    rng = max(hi - lo, 1e-9)
    n = len(bars)
    W, H, PAD = 30.0, 108.0, 9.0
    y = lambda v: PAD + (hi - v) / rng * (H - 2 * PAD)
    o = []
    for i, (op, h, l, c) in enumerate(bars):
        x = i * W + W / 2.0
        cls = 'up' if c >= op else 'dn'
        bt, bb = y(max(op, c)), y(min(op, c))
        if bb - bt < 1.6:
            m = (bt + bb) / 2.0
            bt, bb = m - .8, m + .8
        o.append('<line class="wk %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (cls, x, y(h), x, y(l)))
        o.append('<rect class="bd %s" x="%.1f" y="%.1f" width="12" height="%.1f" rx="1"/>'
                 % (cls, x - 6, bt, bb - bt))
    return ('<svg viewBox="0 0 %.0f %.0f" preserveAspectRatio="xMidYMid meet">%s</svg>'
            % (n * W, H, ''.join(o)))


def schematic(bars_or_pts, lines, kind):
    if kind == 'candle':
        # (dir, hi, lo, ...) tuples were authored as (x, hi, ?, lo); rebuild
        n = len(bars_or_pts)
        W = 118.0 / max(n, 1)
        o = []
        for i, t in enumerate(bars_or_pts):
            _, hi, _, lo = t
            x = 4 + i * W + W / 2
            o.append('<line class="wk dn" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (x, hi, x, lo))
            m = (hi + lo) / 2
            hgt = max((lo - hi) * .55, 3)
            o.append('<rect class="bd dn" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1"/>'
                     % (x - min(W * .3, 7), m - hgt / 2, min(W * .6, 14), hgt))
        return '<svg viewBox="0 0 126 80" preserveAspectRatio="xMidYMid meet">%s</svg>' % ''.join(o)
    pts = ' '.join('%d,%d' % p for p in bars_or_pts)
    o = ['<polyline class="px" points="%s"/>' % pts]
    for (a, b) in (lines or []):
        o.append('<line class="tl" x1="%d" y1="%d" x2="%d" y2="%d"/>'
                 % (a[0], a[1], b[0], b[1]))
    return '<svg viewBox="0 0 120 76" preserveAspectRatio="xMidYMid meet">%s</svg>' % ''.join(o)


FX = dict((c, b) for c, _, b, _ in FIX)
TOT = 421513


def cs_card(code):
    zh, en, occ, gate = CODED[code]
    t = []
    if code in (31, 32, 33):
        t.append('<i class="tg new">新增</i>')
    if code in BULL3:
        t.append('<i class="tg exit">出場旗標</i>')
    if occ <= 20:
        t.append('<i class="tg rare">近乎不出現</i>')
    if gate:
        t.append('<i class="tg gate">進場棒 %d</i>' % gate)
    return ('<figure class="c"><div class="ch">%s</div><figcaption>'
            '<div class="hd"><b class="no">%d</b><b class="zh">%s</b>'
            '<span class="bn">%d 根</span></div><div class="en">%s</div>'
            '<div class="oc"><b>%s</b> 次 <span>%.2f%%</span></div>'
            '<div class="tgs">%s</div></figcaption></figure>'
            % (candles(FX[code]), code, zh, len(FX[code]), en,
               format(occ, ','), 100.0 * occ / TOT, ''.join(t)))


def chart_card(p):
    cid, zh, en, dirn, k, occ, gate, kind, pts, lines = p
    t = ['<i class="tg dir%s">%s</i>' % ({'空': 'b', '多': 'u'}.get(dirn, 'n'), dirn)]
    if gate:
        t.append('<i class="tg gate">進場棒 %d</i>' % gate)
    return ('<figure class="c"><div class="ch sc">%s</div><figcaption>'
            '<div class="hd"><b class="no">%s</b><b class="zh">%s</b>'
            '<span class="bn">%d 根</span></div><div class="en">%s</div>'
            '<div class="oc"><b>%s</b> 次 <span>%.2f%%</span></div>'
            '<div class="tgs">%s</div></figcaption></figure>'
            % (schematic(pts, lines, kind), cid, zh, k, en,
               format(occ, ','), 100.0 * occ / TOT, ''.join(t)))


def nc_card(p):
    cid, zh, en, dirn, why, kind, pts, lines = p
    return ('<figure class="c dim"><div class="ch sc">%s</div><figcaption>'
            '<div class="hd"><b class="no">%s</b><b class="zh">%s</b></div>'
            '<div class="en">%s</div><div class="why">%s</div>'
            '<div class="tgs"><i class="tg dir%s">%s</i></div>'
            '</figcaption></figure>'
            % (schematic(pts, lines, kind), cid, zh, en, why,
               {'空': 'b', '多': 'u'}.get(dirn, 'n'), dirn))


def listrow(items, cols):
    o = ['<div class="lst">']
    for it in items:
        d = it[0]
        o.append('<div class="li"><i class="tg dir%s">%s</i>'
                 '<b>%s</b><span class="le">%s</span>'
                 '%s<span class="lw">%s</span></div>'
                 % ({'空': 'b', '多': 'u'}.get(d, 'n'), d, it[1], it[2],
                    ('<span class="lb">%d 根</span>' % it[3]) if cols == 5 else '',
                    it[-1]))
    o.append('</div>')
    return ''.join(o)


# ------------------------------------------------------------------ 3. page
CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '_atlas.css'), encoding='utf-8').read()

def sec(title, sub, desc, body):
    return ('<section><header class="sh"><h2>%s</h2><span class="sub">%s</span></header>'
            '<p class="sd">%s</p>%s</section>' % (title, sub, desc, body))


def grid(x):
    return '<div class="grid">%s</div>' % x


B = []
B.append(sec('K 棒型態 · 已編碼 33 種', '代碼 1-33',
             '零自由參數，33/33 通過單元測試。K 線圖直接取自測試 fixture，'
             '<b>是程式碼實際會觸發的形狀</b>。',
             '<h3 class="g3">空方 15 種　代碼 1-15</h3>' + grid(''.join(cs_card(c) for c in BEAR)) +
             '<h3 class="g3">多方 16 種　代碼 16-28、31-33</h3>' + grid(''.join(cs_card(c) for c in BULL)) +
             '<h3 class="g3">中性 2 種　代碼 29-30</h3>' + grid(''.join(cs_card(c) for c in NEU))))
B.append(sec('K 棒型態 · 因跳空排除 23 種', '結構性排除',
             '定義本身要求「開盤跳離前根實體」。TXF1 盤中跳空<b>中位數 1 點</b>，'
             '這類定義在 5 分 K 上會產生大量假訊號，全數排除。',
             listrow(GAPX, 5)))
B.append(sec('K 棒型態 · 單根型態 15 種', '因「至少兩根」排除',
             '本專案的型態一律要求 ≥ 2 根，因為單根形狀在 5 分 K 上不構成結構。'
             '其中 <b>長黑實體、長白實體、十字線已經是現行程式碼的元件</b>。',
             listrow(ONEBAR, 4)))
B.append(sec('圖形型態 · 已定義 17 種', 'P01-P22',
             '全部只用三種殺旋鈕的辦法：<b>從已固定的東西推導</b>（旗桿＝斜率閘門）、'
             '<b>用排名取代門檻</b>（最近 N 根最窄）、'
             '<b>用精確幾何</b>（樞紐＝<code>H[i] &gt; H[i-1] and H[i] &gt; H[i+1]</code>，'
             '「相等」＝完全相等）。',
             grid(''.join(chart_card(p) for p in CHART))))
B.append(sec('圖形型態 · 未編碼 15 種', 'P07、P15-P32',
             '每一張都附上<b>為什麼沒編</b>。其中 <b>P21 上升通道、P24/P25 多方旗形、'
             'P29 擴散三角</b>是可編碼的，只是尚未接線。',
             grid(''.join(nc_card(p) for p in NOTCODED))))

HTML = ('<title>S16_S 型態全圖鑑</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700'
        '&amp;family=Noto+Sans+TC:wght@400;500;700&amp;family=JetBrains+Mono:wght@500'
        '&amp;display=swap" rel="stylesheet">\n<style>%s</style>\n' % CSS
        + '<div class="wrap"><header class="top">'
        '<p class="meta">S16_S_MACrossShort v1.26.0 &nbsp;·&nbsp; Build_ID 260826'
        ' &nbsp;·&nbsp; 2026-08-24</p>'
        '<h1>型態全圖鑑</h1>'
        '<p class="lede">K 棒型態 <b>71 種</b>（已編碼 33 ／ 跳空排除 23 ／ 單根 15）'
        '＋ 圖形型態 <b>32 種</b>（已定義 17 ／ 未編碼 15）'
        '＝ <b>103 種</b>，完整成列。'
        '出現次數量自 421,513 根 5 分 K（2019-01-02 ~ 2026-08-22）。</p>'
        '<div class="legend">'
        '<span><i class="sw up"></i><b>陽線</b> 收 ≥ 開</span>'
        '<span><i class="sw dn"></i><b>陰線</b> 收 &lt; 開</span>'
        '<span><i class="tg dirb">空</i>看空　<i class="tg diru">多</i>看多　'
        '<i class="tg dirn">中性</i></span>'
        '<span><i class="tg gate">進場棒 N</i> 實際進場訊號棒上出現 N 次</span>'
        '<span><i class="tg exit">出場旗標</i> 3 根以上多頭結構</span>'
        '</div></header>'
        + ''.join(B) +
        '<footer class="foot">'
        '<p>K 線圖（已編碼 33 種）取自 <code>scripts/research/s16s_kbar_unittest.py</code> 的 fixture；'
        '圖形型態為示意線圖，依定義繪製。次數取自 '
        '<code>s16s_pattern_census.py</code> 與 <code>s16s_chart_pattern_census.py</code>，'
        '兩者皆<b>無損益欄</b>。</p></footer></div>')

path = os.path.normpath(OUT)
open(path, 'w', encoding='utf-8').write(HTML)
print('wrote %s  %d KB' % (path, len(HTML) // 1024))
print('  K 棒 %d + 跳空 %d + 單根 %d ｜ 圖形 %d + 未編碼 %d = %d'
      % (len(CODED), len(GAPX), len(ONEBAR), len(CHART), len(NOTCODED),
         len(CODED) + len(GAPX) + len(ONEBAR) + len(CHART) + len(NOTCODED)))
