# L2／L4 出場效率量化（2026-11-09）

報告：`docs/research/L2_L4_exit_efficiency_20261109.md`

資料：MC 匯出 1 分 K（2000/1/4–2026/11/7）。新匯出有 12 欄，`txfcore` 只收 7 欄，先轉檔：保留 Date, Time, Open, High, Low, Close, TotalVolume（第 9 欄），表頭換成舊格式。只用 2019/1/2 起的資料，確保 MC 報表區間逐筆相同（程式內有斷言）。

```
python scripts/research/l2l4_exit_eff_20261109/exit_eff.py <1分K> <輸出.json>   # 約 45 秒
python scripts/research/l2l4_exit_eff_20261109/l2grid.py  <1分K>                # L2 保留比例 × TTP 波段門檻
python scripts/research/l2l4_exit_eff_20261109/l2ttp.py   <1分K>                # L2 盤中 TTP 反事實
```

反事實（盤中觸價、第二口保護）是沿原路徑找第一次觸價，不重跑後續交易，只用來篩選；要進 MC 的項目仍需引擎重跑＋MC 報表。
