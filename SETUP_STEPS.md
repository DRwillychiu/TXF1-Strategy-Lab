# 這次更新要怎麼放進 repo（三步）

1. **解壓**：ZIP 右鍵 → 解壓縮到桌面
2. **覆蓋**：打開解壓資料夾 → 全選裡面的檔案與資料夾 → 複製 → 貼到 **repo 根目錄**（有 `CLAUDE.md`、`strategies`、隱藏的 `.git` 那一層）→ 選「取代」
3. **執行**：在 repo 根目錄雙擊 `push.bat` → 出現 `Commit message:` 時輸入訊息 → Enter

- 視窗會停在結果畫面，按任意鍵才關閉
- 看到 `[OK] verified, committed, pushed.` 即完成；出現 `[x]` 就把畫面貼給 Claude
- 第一次若出現 `ModuleNotFoundError: openpyxl`：先在 PowerShell 執行 `pip install openpyxl`，再跑一次

## 訊息打不出中文時
改用 PowerShell 帶參數執行（Shift＋右鍵 → 在這裡開啟 PowerShell）：
```
.\push.bat "文件：CLAUDE.md 三層架構、七個部門、驗證系統"
```

## 之後每個 Task
```
.\push.bat "Task 3.3：L3 R1 規則關/開驗證"
```

## 重要：.bat 檔不要用記事本加中文
`push.bat`、`verify.bat` 必須維持**純英文（ASCII）＋ CRLF 換行**；一加中文，cmd 會把檔案讀壞，出現
`'essage' 不是內部或外部命令` 這類亂碼錯誤。
