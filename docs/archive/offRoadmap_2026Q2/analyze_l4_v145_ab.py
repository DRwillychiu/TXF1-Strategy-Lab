"""
L4 v14.5 4 配置 A/B 對比分析腳本

讀 4 份 xlsx (Config 1-4)，產出:
  - inputs 確認（驗證 user 確實跑了對的配置）
  - 績效對比表（樣本/WR/PF/淨利/MDD）
  - A 獨立貢獻 / B 獨立貢獻 / Combined
  - 出場標籤分布（含 CS_FastBreakExit）
  - 年度績效對比
  - 正交性判斷
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path

BASE = Path('C:/Users/User/Downloads')
FILES = [
    ('1_v14.4', 'TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告_14.4.xlsx'),
    ('2_AOnly', 'TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告_A.xlsx'),
    ('3_BOnly', 'TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告_B.xlsx'),
    ('4_Full',  'TXF1  STRATEGY_WILLY_SHORT_CTEST2 策略回測績效報告.xlsx'),
]


def read_setting(fp):
    """讀 設定 sheet 抓 inputs"""
    df = pd.read_excel(fp, sheet_name='設定', header=None)
    s = {}
    for i in range(min(60, len(df))):
        row = df.iloc[i].tolist()
        if pd.notna(row[0]) and pd.notna(row[1]):
            key = str(row[0]).strip()
            val = str(row[1]).strip()
            s[key] = val
    return s


def read_summary(fp):
    """讀 策略分析 sheet 抓績效"""
    df = pd.read_excel(fp, sheet_name='策略分析', header=None)
    out = {}
    for i in range(min(40, len(df))):
        row = df.iloc[i].tolist()
        if pd.notna(row[0]):
            key = str(row[0]).strip()
            if pd.notna(row[1]):
                out[key] = row[1]
    return out


def read_trades(fp):
    raw = pd.read_excel(fp, sheet_name='交易明細', header=None)
    h = None
    for i in range(10):
        if str(raw.iloc[i,0]).strip() == '交易編號':
            h = i; break
    df = pd.read_excel(fp, sheet_name='交易明細', header=h).dropna(how='all').reset_index(drop=True)
    trades = []
    last = None
    for _, r in df.iterrows():
        typ = str(r.get('類型','')).strip()
        if '進入' in typ:
            last = dict(r)
        elif '離開' in typ and last is not None:
            trades.append({
                'entry_date': pd.to_datetime(last['日期']),
                'exit_date': pd.to_datetime(r['日期']),
                'exit_sig': r['訊號'],
                'pnl': last['獲利(¤)'],
            })
            last = None
    return pd.DataFrame(trades)


# ============================================================
print('=' * 90)
print('L4 v14.5 4 配置 A/B 完整對比分析')
print('=' * 90)
print()

data = {}
for name, f in FILES:
    fp = BASE / f
    if not fp.exists():
        print(f'[MISSING] {f}')
        continue
    data[name] = {
        'settings': read_setting(fp),
        'summary': read_summary(fp),
        'trades': read_trades(fp),
    }

# ============================================================
# 1. Inputs 確認
# ============================================================
print('### 1. INPUTS 確認 ###')
print(f'{"配置":<10} {"Strong_Long_Filter_On":<22} {"Fast_BreakExit_On":<20}')
print('-' * 60)
for name in data:
    s = data[name]['settings']
    slo = s.get('Strong_Long_Filter_On', '?')
    fbe = s.get('Fast_BreakExit_On', '?')
    print(f'{name:<10} {slo:<22} {fbe:<20}')
print()

# ============================================================
# 2. 績效核心指標對比
# ============================================================
print('### 2. 績效核心指標對比 ###')
print(f'{"配置":<10} {"樣本":>6} {"淨利":>12} {"PF":>8} {"WR%":>6} {"MDD%":>8} {"年化%":>8}')
print('-' * 80)
for name in data:
    s = data[name]['summary']
    n = len(data[name]['trades'])
    net = s.get('淨利', 0)
    pf = s.get('獲利因子', 0)
    wr = s.get('%勝率', 0)
    mdd_pct = s.get('最大策略虧損 (%)', 0)
    yr_ret = s.get('年報酬率', 0)
    print(f'{name:<10} {n:>6} {net:>12,.0f} {pf:>8.3f} {wr:>6.1f} {mdd_pct:>8.2f} {yr_ret:>8.2f}')
print()

# ============================================================
# 3. A/B 獨立貢獻分析
# ============================================================
print('### 3. A/B 獨立貢獻分析（增量分析）###')
baseline = data['1_v14.4']['summary'].get('淨利', 0)
a_only = data['2_AOnly']['summary'].get('淨利', 0)
b_only = data['3_BOnly']['summary'].get('淨利', 0)
full = data['4_Full']['summary'].get('淨利', 0)

a_contrib = a_only - baseline
b_contrib = b_only - baseline
ab_combined = full - baseline
ab_sum = a_contrib + b_contrib

print(f'Baseline (v14.4)     淨利: {baseline:>12,.0f}')
print(f'A only               淨利: {a_only:>12,.0f}  → A 獨立貢獻: {a_contrib:>+10,.0f}')
print(f'B only               淨利: {b_only:>12,.0f}  → B 獨立貢獻: {b_contrib:>+10,.0f}')
print(f'A + B 加總                                    : {ab_sum:>+10,.0f}')
print(f'Full (v14.5)         淨利: {full:>12,.0f}  → A+B 實際組合: {ab_combined:>+10,.0f}')
print()

if abs(ab_sum) > 0:
    orthogonality_ratio = ab_combined / ab_sum
    print(f'正交性比率 (Combined/Sum): {orthogonality_ratio:.2f}')
    if 0.85 <= orthogonality_ratio <= 1.15:
        print('  → A 與 B 大致正交（互不影響）')
    elif orthogonality_ratio < 0.85:
        print('  → A 與 B 有重疊（部分 redundant）')
    else:
        print('  → A 與 B 互補（疊加效果更佳）')
print()

# ============================================================
# 4. 出場標籤分布對比
# ============================================================
print('### 4. 出場標籤分布對比（焦點：CS_BreakExit / CS_FastBreakExit）###')
all_labels = set()
for name in data:
    all_labels.update(data[name]['trades']['exit_sig'].unique())
all_labels = sorted(all_labels)

print(f'{"標籤":<22}', end='')
for name in data:
    print(f' {name:>14}', end='')
print()
print('-' * (22 + 15 * len(data)))

for lbl in all_labels:
    row = f'{lbl:<22}'
    for name in data:
        t = data[name]['trades']
        sub = t[t['exit_sig'] == lbl]
        n = len(sub)
        net = sub['pnl'].sum()
        row += f' {n:>4} ({net:>+7,.0f})'[:15].ljust(15)
    print(row)
print()

# ============================================================
# 5. CS_BreakExit 系列重點分析
# ============================================================
print('### 5. CS_BreakExit 痛點解剖（A+B 設計目的）###')
print(f'{"配置":<10} {"CS_BreakExit":<22} {"CS_FastBreakExit":<22} {"合計":<20}')
print('-' * 80)
for name in data:
    t = data[name]['trades']
    be = t[t['exit_sig'] == 'CS_BreakExit']
    fbe = t[t['exit_sig'] == 'CS_FastBreakExit']
    be_total = f'{len(be)}筆 / {be["pnl"].sum():+,.0f}'
    fbe_total = f'{len(fbe)}筆 / {fbe["pnl"].sum():+,.0f}'
    sum_n = len(be) + len(fbe)
    sum_pnl = be["pnl"].sum() + fbe["pnl"].sum()
    sum_str = f'{sum_n}筆 / {sum_pnl:+,.0f}'
    print(f'{name:<10} {be_total:<22} {fbe_total:<22} {sum_str:<20}')
print()

# ============================================================
# 6. 年度績效對比
# ============================================================
print('### 6. 年度績效對比 ###')
year_data = {}
for name in data:
    t = data[name]['trades'].copy()
    t['Year'] = t['entry_date'].dt.year
    yr = t.groupby('Year')['pnl'].sum()
    year_data[name] = yr

years = sorted(set().union(*[s.index for s in year_data.values()]))
print(f'{"年份":<6}', end='')
for name in data:
    print(f' {name:>12}', end='')
print()
print('-' * (6 + 13 * len(data)))
for yr in years:
    row = f'{yr:<6}'
    for name in data:
        v = year_data[name].get(yr, 0)
        row += f' {v:>12,.0f}'
    print(row)
print()

# ============================================================
# 7. 結論判斷
# ============================================================
print('=' * 90)
print('### 7. 結論判斷 ###')
print('=' * 90)
print()

config_full_pf = data['4_Full']['summary'].get('獲利因子', 0)
config_baseline_pf = data['1_v14.4']['summary'].get('獲利因子', 0)
pf_improvement = config_full_pf - config_baseline_pf

print(f'PF 變化: v14.4 {config_baseline_pf:.3f} → v14.5 Full {config_full_pf:.3f} (Δ {pf_improvement:+.3f})')
print()

if ab_combined > 0 and a_contrib > 0 and b_contrib > 0:
    print('✅ A + B 都正向貢獻 → 保留 v14.5 預設 (Strong_Long_Filter_On=true + Fast_BreakExit_On=true)')
elif a_contrib > 0 and b_contrib <= 0:
    print('⚠️ 只有 A 有效 → 建議改 default: Fast_BreakExit_On=false')
elif b_contrib > 0 and a_contrib <= 0:
    print('⚠️ 只有 B 有效 → 建議改 default: Strong_Long_Filter_On=false')
else:
    print('❌ A+B 都無效或反向 → 回滾到 v14.4 default')
