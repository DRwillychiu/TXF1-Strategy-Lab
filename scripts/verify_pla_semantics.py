"""
PowerLanguage .pla 語意交叉驗證器

檢查 inputs / variables / 訂單標籤 / 出場串接 / 時間字面值 / 回看長度 /
開關鏡射 / 訂單型態，以及 CLAUDE.md Rule #11 #12 的結構要件。

★ 「指派 vs 比較」的分類器會先通過 8 個合成情境測試才開始檢查。
   PowerLanguage 用同一個 `=` 表示指派與相等，而本專案的進場條件是
   多行 `and` 串接，所以 `v_X = False and` 是【比較】、
   `v_X = ( A and` 是【指派的首行】。分辨錯了就會產出整批假陽性 ——
   這在開發本工具時實際發生過三次，所以測試不過就直接離開，不輸出結論。

usage: python scripts/verify_pla_semantics.py <path-to.pla>
"""
import io, os, sys, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if len(sys.argv) < 2:
    print('usage: python scripts/verify_pla_semantics.py <path-to.pla>')
    sys.exit(2)
P = sys.argv[1]
raw = open(P, encoding='ascii').read()

# ---------- 剝註解，保留行結構 ----------
lines, depth = [], 0
for ln in raw.split(chr(10)):
    out, d = '', depth
    for ch in ln:
        if ch == '{':
            d += 1
        elif ch == '}':
            d = max(0, d - 1)
        elif d == 0:
            out += ch
    depth = d
    lines.append(out.rstrip())
code = chr(10).join(lines)

# ---------- 宣告區 vs 執行本體 ----------
DECL, spans = {}, []
for kw in ('inputs', 'variables', 'arrays'):
    m = re.search(r'^[ \t]*' + kw + r'[ \t]*:(.*?);[ \t]*$', code, re.S | re.M | re.I)
    if not m:
        continue
    spans.append((m.start(), m.end()))
    for name, dv in re.findall(r'([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*\(\s*([^)]*?)\s*\)', m.group(1)):
        DECL[name] = (kw, dv)
body = code
for a, b in sorted(spans, reverse=True):
    body = body[:a] + chr(10) * body[a:b].count(chr(10)) + body[b:]

BODY_LINES = [l.strip() for l in body.split(chr(10))]

# 2026-08-20 修正：字串常數的內容不是識別字。
# 舊版直接對 body 取詞，於是 Print( "S16_S build ", ... ) 裡的 S16_S 與 build
# 都被當成未宣告識別字。L1_TrendLong 那一長串 DECL 假警告（Green / Red /
# TAIFEX / HOLIDAY / CALENDAR / REGISTRY ...）全部來自同一個原因。
# 只在取詞時剝掉字串；BODY_LINES 保留原文，因為指派/比較分類器要看原始敘述。
_tok_src = re.sub(r'"[^"\n]*"', '""', body)
occ = collections.Counter(re.findall(r'\b([A-Za-z_]\w*)\b', _tok_src))

# ---------- 分類器：指派 vs 比較 ----------
# 判準是「敘述起始」：上一個非空行以 ; / begin / then / else 收尾。
# 多行條件的續行（上一行以 = 或 and / or 收尾）一律視為比較。
STMT_END = re.compile(r'(;|\]|\bbegin\b|\bthen\b|\belse\b)\s*$', re.I)
# 陣列元素指派 v_PvPx[v_j] = ... 也是一次寫入。舊版的 \w* 後面直接接 =，
# 於是整個陣列被判成「只讀不寫，恆為初值」—— 假 WARN，而假 WARN 會讓
# 真的「宣告了卻忘記賦值」被忽略。下標整段可選。
ASSIGN = re.compile(r'^(?:for\s+)?([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*=(?!=)')


def classify(src):
    wr, prev = collections.Counter(), ';'
    for ln in src:
        t = ln.strip()
        if not t:
            continue
        m = ASSIGN.match(t)
        if m and STMT_END.search(prev) and not t.lower().startswith('for '):
            wr[m.group(1)] += 1
        prev = t
    return wr


CASES = [
    (['v_X = True;'], 1, '單行指派'),
    (['v_A = 1;', 'v_X = False;'], 1, '連續指派'),
    (['if a then begin', 'v_X = True;', 'end;'], 1, 'begin 之後的指派'),
    (['v_Entry =', '   v_X   = False and', '   v_Y = 0 );'], 0, '多行條件裡的比較'),
    (['v_A = 1;', 'v_X = ( DayOfWeek(Date) = 3 and', '  DayOfMonth(Date) >= 15 );'], 1,
     '多行指派、首行以 and 收尾'),
    (['for v_X = 1 to 80 begin'], 0, 'for 迴圈計數器'),
    (['if v_X = True then begin'], 0, 'if 條件'),
    (['v_A = 1;', 'v_X = 0;', 'v_X = 1;'], 2, '同名多次指派'),
]
for src, exp, why in CASES:
    got = classify(src)['v_X']
    if got != exp:
        print('!!! 分類器測試失敗（%s）期望 %d 實得 %d  %r' % (why, exp, got, src))
        sys.exit(1)

WR = classify(BODY_LINES)
LOOPVARS = set(re.findall(r'for\s+([A-Za-z_]\w*)\s*=', body, re.I))
print('%s' % P.replace(chr(92), '/').split('/')[-1])
print('分類器自我測試通過（%d 個合成情境）　宣告 %d 個　執行本體 %d 行'
      % (len(CASES), len(DECL), sum(1 for t in BODY_LINES if t)))

FAIL, WARN, OK = [], [], []
f = lambda c, m: FAIL.append((c, m))
w_ = lambda c, m: WARN.append((c, m))
o = lambda c, m: OK.append((c, m))

BUILTIN = set("""and or not if then else begin end for to downto while true false
value1 value2 close open high low date time volume barnumber currentbar maxbarsback
marketposition entryprice barssinceentry bigpointvalue numeric truefalse string
buy sell short cover next bar at market stop limit this setstoploss setstopcontract
setprofittarget xaverage average highest lowest atr avgtruerange truerange minlist
maxlist intportion absvalue mod square squareroot dayofweek dayofmonth month year
currentdate currenttime iff numericseries numericsimple booleansimple print inputs
variables arrays crosses above below alert barinterval timetominutes
plot1 plot2 plot3 plot4 plot5 plot6 plot7 plot8 plot9 noplot
setplotcolor setplotwidth setplottype plotpaintbar
tl_new tl_delete tl_setcolor tl_setsize tl_setend tl_setbegin
text_new text_delete text_setcolor text_setsize text_setstyle
numtostr strtonum lastbaronchart absvalue maxlist minlist
darkgreen darkred darkcyan darkbrown lightgray darkgray
tl_setextright tl_setextleft tl_setstyle tl_getactive
red green blue cyan magenta yellow white black darkred darkgreen darkblue
minutestotime rsi exitfired intrabarordergeneration o h l c
datetojulian juliantodate""".split())
# plotpaintbar added 2026-08-26: the standard PowerLanguage paintbar plot.
# It occupies Plot1..Plot4 internally, which is why IND_S16S_P29's own plots
# start at 5 -- worth remembering before adding a plot to that file.
# datetojulian / juliantodate added 2026-08-20: standard PowerLanguage builtins,
# in use across every live strategy (L1-L5, S1, S3 family). They were missing from
# this list, so any file using them drew a false DECL warning.

inps = {k: v for k, (b, v) in DECL.items() if b == 'inputs'}
vars_ = {k: v for k, (b, v) in DECL.items() if b in ('variables', 'arrays')}

# ---------- 1. inputs ----------
dead = [k for k in inps if occ[k] == 0]
f('INPUT', '宣告但從未讀取: %s' % ', '.join(sorted(dead))) if dead else \
    o('INPUT', '%d 個 input 全部至少被讀取一次' % len(inps))
asg = [k for k in inps if WR[k] > 0]
f('INPUT', 'input 被指派值（PowerLanguage 禁止）: %s' % ', '.join(asg)) if asg else \
    o('INPUT', '無 input 被指派值')

# ---------- 2. variables ----------
dv, wo, ro = [], [], []
for k in vars_:
    tot, wr = occ[k], WR[k]
    rd = tot - wr
    if tot == 0:
        dv.append(k)
    elif rd == 0:
        wo.append('%s (寫%d/讀0)' % (k, wr))
    elif (wr == 0 and not k.startswith('Holiday_')
          and not re.search(r'\bfor\s+' + re.escape(k) + r'\s*=', body, re.I)):
        ro.append('%s (讀%d/寫0，恆為初值 %s)' % (k, rd, vars_[k]))
f('VAR', '宣告但完全未使用: %s' % ', '.join(sorted(dv))) if dv else \
    o('VAR', '%d 個 variable/array 全部有被使用' % len(vars_))
f('VAR', '只寫不讀（結果被丟棄）: %s' % '; '.join(sorted(wo))) if wo else \
    o('VAR', '無「只寫不讀」變數')
w_('VAR', '只讀不寫: %s' % '; '.join(sorted(ro))) if ro else \
    o('VAR', '無「只讀不寫」變數')

# ---------- 3. 未宣告識別字 ----------
und = sorted({t for t in occ if t.lower() not in BUILTIN and t not in DECL
              and not re.match(r'^(SE|SX|LE|LX)_', t)})
w_('DECL', '未宣告（逐一確認是否為內建函式）: %s' % ', '.join(und)) if und else \
    o('DECL', '本體無未宣告識別字')

# ---------- 4. 標籤 ----------
orders = re.findall(r'\b(buy to cover|sell short|buy|sell)\s*(\(\s*"([^"]+)"\s*\))?', body)
lab = [(v, n) for v, h, n in orders if h]
nolab = sum(1 for v, h, n in orders if not h)
PFX = {'sell short': 'SE_', 'buy to cover': 'SX_', 'buy': 'LE_', 'sell': 'LX_'}
bad = [(v, n) for v, n in lab if not n.startswith(PFX[v])]
dup = [n for n, c in collections.Counter(n for _, n in lab).items() if c > 1]
f('LABEL', '%d 筆下單無標籤' % nolab) if nolab else o('LABEL', '所有 %d 筆下單都有標籤' % len(lab))
f('LABEL', '前綴不符: %s' % bad) if bad else o('LABEL', '%d 個標籤前綴全部正確' % len(lab))
f('LABEL', '重複標籤: %s' % dup) if dup else o('LABEL', '無重複標籤')

# ---------- 5. ExitFired 護欄：用 begin/end 巢狀深度追蹤，不用鄰近文字 ----------
# if 的條件可跨多行（"if ExitFired = 0 and" 換行後才 "then begin"），
# 所以累積條件文字到看見 begin 為止，再判定這一層有沒有護欄
stack, depth_now, noguard, pend = [], 0, [], ''
seen_exit, head = [], None
for t in BODY_LINES:
    if not t:
        continue
    pend += ' ' + t
    opens = len(re.findall(r'\bbegin\b', t, re.I))
    closes = len(re.findall(r'\bend\b(?!ing)', t, re.I))
    for m in re.finditer(r'buy to cover\s*\(\s*"([^"]+)"', t):
        seen_exit.append(m.group(1))
        if any(g for d, g in stack):
            continue
        if len(seen_exit) == 1:          # 串接第一個：前面不可能有東西先觸發
            head = m.group(1)            # 但它必須自己收尾
            continue
        noguard.append(m.group(1))
    if opens:
        stack.append((depth_now + 1, bool(re.search(r'ExitFired\s*=\s*0', pend))))
    depth_now += opens - closes
    while stack and stack[-1][0] > depth_now:
        stack.pop()
    if re.search(r'(;|\bbegin\b|\bend\b)\s*$', t, re.I):
        pend = ''
f('FLOW', '出場未受 ExitFired 護欄保護: %s' % ', '.join(noguard)) if noguard else \
    o('FLOW', '所有 buy to cover 都在 ExitFired = 0 護欄的巢狀範圍內')

# ---------- 6. 時間 ----------
bt = [m.group(0) for m in re.finditer(r'\bTime\s*(?:>=|<=|>|<|=|<>)\s*(\d{3,4})\b', body, re.I)
      if int(m.group(1)) % 100 > 59]
bt += ['%s = %s' % (k, v) for k, v in inps.items()
       if re.search(r'time|from|cutoff', k, re.I) and re.match(r'^\d{3,4}$', v.strip())
       and int(v) % 100 > 59]
f('TIME', '分鐘數 > 59 的非法時間: %s' % ', '.join(bt)) if bt else \
    o('TIME', '所有時間字面值與時間型 input 的分鐘數皆在 00-59')

# ---------- 7. 回看長度 ----------
lng = [(float(v), k) for k, v in inps.items()
       if re.search(r'len|length|lookback', k, re.I) and re.match(r'^[\d.]+$', v.strip())]
over = ['%s = %g' % (k, n) for n, k in lng if n > 99]
if over:
    f('MBB', '超過 MaxBarsBack 99: %s' % ', '.join(over))
elif lng:
    o('MBB', '最長回看 %s = %g，未超過 99' % (max(lng)[1], max(lng)[0]))
else:
    # 沒有 len/length/lookback 命名的 input。指標與純鎖存式模組會走到這裡
    # （IND_S16S_P29 把樞紐價格鎖存進陣列，型態判定完全不回看）。
    # 舊版直接 max([]) 會 ValueError 讓驗證器整個崩掉 —— 守門員自己倒下。
    o('MBB', '無 len/length/lookback 型 input，無回看長度可查')

# ---------- 8. 開關鏡射 ----------
mir = dict(re.findall(r'(v_\w+)\s*=\s*\(\s*(\w+)\s*<>\s*0\s*\)', body))
sw = [k for k, v in inps.items() if re.match(r'^[01]$', v.strip()) and k.endswith('_On')]
miss = [k for k in sw if k not in mir.values()]
unused = [m for m in mir if occ[m] <= 1]
w_('SWITCH', '數值開關無布林鏡射: %s' % ', '.join(sorted(miss))) if miss else \
    o('SWITCH', '%d 個 _On 開關全部有布林鏡射' % len(sw))
f('SWITCH', '鏡射建立後未使用: %s' % ', '.join(sorted(unused))) if unused else \
    o('SWITCH', '%d 個鏡射變數全部有被使用' % len(mir))

# ---------- 9. 訂單型態 ----------
bado = []
for v, n, k in re.findall(
        r'\b(buy to cover|sell short)\s*\(\s*"([^"]+)"\s*\)\s*next bar at\s+([^;\n]+)', body):
    kk = k.strip().lower()
    if not (kk == 'market' or kk.endswith('stop') or kk.endswith('limit')):
        bado.append('%s -> "%s"' % (n, k.strip()))
f('ORDER', '指定價格但缺 stop/limit 關鍵字: %s' % ', '.join(bado)) if bado else \
    o('ORDER', '所有下單型態關鍵字完整（market / stop / limit）')

# ---------- 10. 規範與已知陷阱 ----------
# 這一段全部是 Rule #11 / #12 的策略專屬規範。指標沒有部位、不下單、
# 沒有結算日出場，套上去只會產生假 FAIL —— 而假 FAIL 讓真 FAIL 沒人看。
# 判定沿用 verify_settlement_flat.py 的做法：IND_ 前綴且無下單語句。
_IS_IND = ( os.path.basename(P).upper().startswith('IND_')
            and not re.search(r'(buy|sell short|sell|buy to cover)\s*\(', body, re.I) )
if _IS_IND:
    o('RULE', '指標：Rule #11 / #12 與 IOG 不適用，已跳過')
else:
    o('IOG', 'IntrabarOrderGeneration = False 存在') if re.search(
        r'\[IntrabarOrderGeneration\s*=\s*False\]', code) else f('IOG', 'IOG 宣告遺失')
    for pat, why in (('SetStopContract', 'Rule #12 每口停損'), ('SetStopLoss', 'Rule #12 引擎停損'),
                     ('v_Settlement_Day', 'Rule #11 結算日'), ('v_Prev_MP', '前根部位追蹤')):
        c = len(re.findall(pat, code))
        (o if c else f)('RULE', '%s 出現 %d 次（%s）' % (pat, c, why))
    a, b = code.find('SetStopContract'), code.find('SetStopLoss')
    (o if 0 <= a < b else f)('RULE', 'SetStopContract %s SetStopLoss' % ('先於' if 0 <= a < b else '未先於'))
# 前瞻索引 [0]。舊版用 re.search(r'\[\s*0\s*\]', body) 一律判死，分不出
# 棒位偏移 Close[0] 與陣列下標 v_PvPx[0]。任何用陣列的檔案都會拿到假 FAIL，
# 而真的前瞻會淹沒在雜訊裡 —— 守門員必須吵得準，不是吵得大聲。
_ARRNAMES = set(k.lower() for k, (b, _) in DECL.items() if b == 'arrays')
_fwd = [m.group(1) for m in re.finditer(r'([A-Za-z_]\w*)\s*\[\s*0\s*\]', body)
        if m.group(1).lower() not in _ARRNAMES]
(f if _fwd else o)('FUTURE', '無前瞻索引 [0]%s'
                   % ('' if not _fwd else '：' + ', '.join(sorted(set(_fwd)))))
last = [t for t in BODY_LINES if t][-1]
if _IS_IND:
    o('FLOW', '指標：最末行 v_Prev_MP 規範不適用')
else:
    (o if 'v_Prev_MP' in last else w_)('FLOW', '腳本最末行: %s' % last[:56])

print()
print('=' * 82)
for tag, items in (('FAIL', FAIL), ('WARN', WARN), ('PASS', OK)):
    for c, m in items:
        print('  [%s] %-7s %s' % (tag, c, m))
print('=' * 82)
print('  FAIL %d   WARN %d   PASS %d' % (len(FAIL), len(WARN), len(OK)))
