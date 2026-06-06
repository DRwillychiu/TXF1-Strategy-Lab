# TXF1-Strategy-Lab

台指期貨（TXF1）量化策略自動化研究庫

## 結構

```
strategies/       每批策略 Markdown + PowerLanguage 原始碼
  batch01/        第一批策略
  batch02/        第二批（自動生成，每週日更新）
backtest/         Python 模擬回測腳本與結果
scripts/          輔助工具
docs/             文件
```

## 規格

- 商品：TXF1（台指期近月連續）
- 合約乘數：1 點 = 200 NTD
- 平台：MultiCharts 12 / PowerLanguage
- 每口滑價：1,000 NTD（單邊 500）
- 固定口數：1 口
- 回測區間：2020/01/01 ~ 2026/06/06

## 自動更新

每週日中午 12:00（台灣時間）自動生成新一批 5 隻策略。
