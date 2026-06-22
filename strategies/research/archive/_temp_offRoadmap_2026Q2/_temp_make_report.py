import pandas as pd
import numpy as np

monthly = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_monthly.pkl')
daily = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_daily.pkl')
pearson = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_pearson.pkl')
spearman = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_spearman.pkl')
daily_pearson = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_daily_pearson.pkl')
pdf = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_pairs.pkl')
sdf = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_stats.pkl')
loose_neg = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_loose_neg.pkl')
loose_pos = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_loose_pos.pkl')
all_neg = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_all_neg.pkl')
all_pos = pd.read_pickle('C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_all_pos.pkl')

strategies = list(monthly.columns)

def matrix_to_md(mat, name):
    cols = mat.columns.tolist()
    header = '| ' + name + ' | ' + ' | '.join(cols) + ' |'
    sep = '|' + '|'.join(['---'] * (len(cols) + 1)) + '|'
    rows = []
    for r in cols:
        cells = [r] + [f'{mat.loc[r,c]:+.3f}' if r != c else '1.000' for c in cols]
        rows.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join([header, sep] + rows)

L = []
L.append('# 月度組合相關性分析報告')
L.append('')
L.append('- 來源資料：`scripts/_temp_portfolio_pnl.json`')
L.append(f'- 涵蓋日期：{daily.index.min().strftime("%Y-%m-%d")} ~ {daily.index.max().strftime("%Y-%m-%d")}')
L.append(f'- 交易日筆數：{len(daily)}')
L.append(f'- 月度樣本數：{len(monthly)} 個月（2019-12 ~ 2026-06）')
L.append(f'- 策略：{", ".join(strategies)}')
L.append('')

L.append('## 1. 方法論')
L.append('')
L.append('1. 將 6 條策略的每日已平倉 PnL（單口、未扣手續費）依日期合併為寬表，未交易日補 0。')
L.append('2. 以「月起始 (MS)」重採樣求和，得到每策略每月 PnL；月內未交易則為 0。')
L.append('3. 月度相關採 Pearson（線性同向性）與 Spearman（秩相關，對極端月份較不敏感）。')
L.append('4. 與 1142 個交易日的日度 Pearson 比較，找出「日相關低、月相關高」的策略對 — 通常代表多日趨勢同向、但日內進出時點錯開。')
L.append('5. Per-strategy 統計從該策略第一個非零月份起算，年化 Sharpe = mean / std × √12（每月 PnL 視為等距樣本，無風險利率設為 0）。')
L.append('6. 「組合危機 / 順風月」嚴格定義為「全 6 策略當月皆為負 / 皆為正」；寬鬆定義為「至少 3 條策略有交易且皆同號」，後者較能反映 2021 年前 L2/L4/L5 尚未上線的事實。')
L.append('')

L.append('## 2. 月度 Pearson 相關矩陣 (6x6)')
L.append('')
L.append(matrix_to_md(pearson.round(3), 'Pearson'))
L.append('')

L.append('## 3. 月度 Spearman 秩相關矩陣 (6x6)')
L.append('')
L.append(matrix_to_md(spearman.round(3), 'Spearman'))
L.append('')
L.append('參考用：**日度 Pearson 矩陣**（n=1142 交易日）：')
L.append('')
L.append(matrix_to_md(daily_pearson.round(3), 'Daily Pearson'))
L.append('')

L.append('## 4. 值得關注的策略對')
L.append('')
L.append('### 4.1 月度 |Pearson| > 0.5 的策略對')
L.append('')
L.append('| pair | monthly_pearson | monthly_spearman | daily_pearson | delta(month-day) |')
L.append('|---|---|---|---|---|')
hot = pdf[pdf['monthly_pearson'].abs() > 0.5]
for _, r in hot.iterrows():
    L.append(f"| **{r['pair']}** | {r['monthly_pearson']:+.3f} | {r['monthly_spearman']:+.3f} | {r['daily_pearson']:+.3f} | {r['monthly_minus_daily']:+.3f} |")
L.append('')

L.append('### 4.2 所有 15 對排序（依 |月度 Pearson|）')
L.append('')
L.append('| pair | monthly_pearson | monthly_spearman | daily_pearson | delta(month-day) |')
L.append('|---|---|---|---|---|')
for _, r in pdf.iterrows():
    L.append(f"| {r['pair']} | {r['monthly_pearson']:+.3f} | {r['monthly_spearman']:+.3f} | {r['daily_pearson']:+.3f} | {r['monthly_minus_daily']:+.3f} |")
L.append('')

L.append('### 4.3 日 vs 月相關差異最大的對 (|delta| 前 5)')
L.append('')
L.append('「日相關很低、月相關卻很高」通常意味著兩條策略在**同一個趨勢段內**都會吃到行情，但**進出時點錯開**，所以日層級看不出共動，月層級才浮現。')
L.append('')
L.append('| pair | monthly_pearson | daily_pearson | delta |')
L.append('|---|---|---|---|')
diff = pdf.reindex(pdf['monthly_minus_daily'].abs().sort_values(ascending=False).index).head(5)
for _, r in diff.iterrows():
    L.append(f"| {r['pair']} | {r['monthly_pearson']:+.3f} | {r['daily_pearson']:+.3f} | {r['monthly_minus_daily']:+.3f} |")
L.append('')

L.append('### 4.4 Pearson 與 Spearman 嚴重不一致')
L.append('')
L.append('「Pearson 高、Spearman 低」表示相關性被少數極端月份撐起來，**典型槓桿風險訊號**：移除幾個爆衝月後，這對策略其實沒有可靠的共動性。')
L.append('')
L.append('| pair | Pearson | Spearman | abs(delta) |')
L.append('|---|---|---|---|')
ps_diff = pdf.copy()
ps_diff['ps_gap'] = (ps_diff['monthly_pearson'] - ps_diff['monthly_spearman']).abs()
for _, r in ps_diff.sort_values('ps_gap', ascending=False).head(5).iterrows():
    L.append(f"| {r['pair']} | {r['monthly_pearson']:+.3f} | {r['monthly_spearman']:+.3f} | {r['ps_gap']:.3f} |")
L.append('')

L.append('## 5. 各策略月度統計')
L.append('')
L.append('| strategy | first_active | months | mean PnL | std | annualized Sharpe | total PnL | pos / neg / zero |')
L.append('|---|---|---|---|---|---|---|---|')
for _, r in sdf.iterrows():
    L.append(
        f"| **{r['strategy']}** | {r['first_active_month']} | {int(r['active_months_n'])} "
        f"| {r['mean']:+,.0f} | {r['std']:,.0f} | **{r['sharpe_annualized']:.2f}** "
        f"| {r['total_pnl']:+,.0f} | {int(r['pos_months'])} / {int(r['neg_months'])} / {int(r['zero_months'])} |"
    )
L.append('')
L.append('註：mean / std / Sharpe 以「該策略第一個有交易的月份起」計算。零月份（無交易）也算入分母，反映「策略上線後的真實月度體驗」。')
L.append('')

L.append('## 6. 組合危機月（全策略皆負）')
L.append('')
L.append('### 6.1 嚴格定義：全 6 策略同月皆為負')
L.append('')
if len(all_neg) == 0:
    n_common = len(monthly.loc['2021-09':])
    L.append(f'共同上線期間（2021-09 ~ 2026-06，共 {n_common} 個月）**無單一月份**所有 6 策略同時為負，這已是組合分散的最強證據。')
else:
    L.append('| month | ' + ' | '.join(strategies) + ' |')
    L.append('|' + '|'.join(['---'] * 7) + '|')
    for d, row in all_neg.iterrows():
        L.append(f"| {d.strftime('%Y-%m')} | " + ' | '.join([f"{v:+,.0f}" for v in row]) + ' |')
L.append('')

L.append('### 6.2 寬鬆定義：>=3 條策略當月有交易且皆為負')
L.append('')
L.append(f'共 {len(loose_neg)} 個月。')
L.append('')
L.append('| month | ' + ' | '.join(strategies) + ' | sum |')
L.append('|' + '|'.join(['---'] * 8) + '|')
for d, row in loose_neg.iterrows():
    s = row.sum()
    cells = [f"{v:+,.0f}" if v != 0 else '—' for v in row]
    L.append(f"| **{d.strftime('%Y-%m')}** | " + ' | '.join(cells) + f' | **{s:+,.0f}** |')
L.append('')

L.append('## 7. 組合順風月（活躍策略皆正）')
L.append('')
L.append('### 7.1 嚴格定義：全 6 策略同月皆為正')
L.append('')
if len(all_pos) == 0:
    L.append('共同上線期間內**亦無單一月份**所有 6 策略同時為正 — 顯示組合的「全紅日」幾乎不會出現，多數順風月仍有 1~2 條策略無交易或小虧。')
else:
    L.append('| month | ' + ' | '.join(strategies) + ' |')
    L.append('|' + '|'.join(['---'] * 7) + '|')
    for d, row in all_pos.iterrows():
        L.append(f"| {d.strftime('%Y-%m')} | " + ' | '.join([f"{v:+,.0f}" for v in row]) + ' |')
L.append('')

L.append('### 7.2 寬鬆定義：>=3 條策略當月有交易且皆為正')
L.append('')
L.append(f'共 {len(loose_pos)} 個月。')
L.append('')
L.append('| month | ' + ' | '.join(strategies) + ' | sum |')
L.append('|' + '|'.join(['---'] * 8) + '|')
for d, row in loose_pos.iterrows():
    s = row.sum()
    cells = [f"{v:+,.0f}" if v != 0 else '—' for v in row]
    L.append(f"| **{d.strftime('%Y-%m')}** | " + ' | '.join(cells) + f' | **{s:+,.0f}** |')
L.append('')

L.append('## 8. 解讀與啟示')
L.append('')
L.append('### 8.1 月度相關結構：三條共動軸 + 三條孤立軸')
L.append('')
L.append('- **L2 vs L4 (r=+0.61)**：兩條皆為偶發、低頻型策略（L2 n=78、L4 n=76），開單月份高度集中在大波段月份，因此月度共動非常強。Spearman 反而為 -0.17，提示這個 +0.61 來自少數共同爆衝月（2020-03 武肺、2024-08 日圓套利、2025-04 川普關稅）— 屬於「同類事件型」共動而非結構性同向。')
L.append('- **L1 vs L5 (r=+0.52)**：L1 與 L5 皆為趨勢/動能類，日層級相關 ~ 0，月層級卻拉到 0.52，是最典型「同趨勢、不同時點」對 — delta = +0.526 為全表最大。組合內這兩條會在同一波段彼此放大盈虧。')
L.append('- **L5 vs S1 (r=+0.50)**：L5（多單動能）和 S1（高頻空單系統）月度居然同向，意味著「行情有發動的月份」兩邊都吃得到 — 日層級僅 +0.13。')
L.append('- **S1 對所有其他策略皆呈現 +0.18 ~ +0.34 的正相關**，是組合的「廣域共振源」。S1 雖名為 Short，但月度顯示它的盈虧與整體市場波動共同呼吸。')
L.append('- **L3 與 L1/L2/L4 月度相關都 < 0.06**：L3 是組合內最佳的「分散器」。')
L.append('')
L.append('### 8.2 日 vs 月相關落差的意義')
L.append('')
L.append('- L1-L5、L5-S1、L2-S1、L2-L4 四對的 delta(month-day) 都 > 0.27，代表**日度看似獨立、月度卻明顯共動**。')
L.append('- 對部位管理的意涵：用「日相關」估組合波動會嚴重低估月度回撤。實際資金曲線的回撤節奏是月度的，因此應以**月度相關矩陣**為加權配置（risk parity）的輸入，而非日度。')
L.append('')
L.append('### 8.3 Sharpe 排序與配置建議')
L.append('')
L.append('- L1 與 S1 並列最高 Sharpe ~ 0.94，L5 0.91，L2 0.81 — 上層四條皆優於 0.8。')
L.append('- L3 (0.55) 與 L4 (0.29) Sharpe 偏低，但 L3 的低相關性具有顯著分散貢獻；L4 既低 Sharpe 又與 L2 高度共動 (+0.61)，是組合內**邊際貢獻最值得質疑**的一條，可考慮升級或併入 L2 框架。')
L.append('')
L.append('### 8.4 危機月與順風月模式')
L.append('')
L.append('- **嚴格全 6 同負 / 同正月份皆為 0**，這本身就是組合分散有效的最強證據。')
L.append('- 寬鬆定義下，5 個全負月以「**趨勢失效 + 盤整**」為共通主題；2022-12 (-200K)、2024-11 (-199K) 與 2025-06 (-151K) 為三大痛月，其中 2024-11 是少數連 L4、L5 都同時虧損的月份 — 是觀察組合尾部風險的關鍵壓力點。')
L.append('- 14 個全正月集中在 2023H2 ~ 2025 大波段年；最甜月份為 2025-04 (+899K，川普關稅)、2024-08 (+754K，日圓套利) — 這兩個月正是 L2、L4 的爆衝點，也解釋了為何 L2-L4 月度 Pearson 看起來那麼高。')
L.append('')
L.append('---')
L.append('')
L.append('_報告產出時間：2026-06-19_')

content = '\n'.join(L)
out_path = 'C:/Users/User/Desktop/TXF1-Strategy-Lab/scripts/_temp_monthly_corr.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'written {len(content)} chars to {out_path}')
