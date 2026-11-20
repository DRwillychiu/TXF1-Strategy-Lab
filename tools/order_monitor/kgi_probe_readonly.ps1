# kgi_probe_readonly.ps1  -- 凱基 TradeCom 唯讀連線實測（只在非交易時段跑）
# 目的：1) 第二個連線會不會把下單大師踢掉  2) 當天委託/成交回報欄位（IOC/ROD、PriceMark、成交價）
# 唯讀：只呼叫 LoginDirect / 回報訂閱與回補 / Logout。不含任何下單、刪改單方法（tests/test_order_monitor_readonly.py 會檢查）。
# 帳密：環境變數 KGI_ID / KGI_PWD；沒有就當場輸入，不寫檔。輸出自動遮罩帳號、身分證、姓名。
param([int]$Seconds = 90)
$ErrorActionPreference = "Stop"
$now = Get-Date; $hm = $now.Hour * 100 + $now.Minute
$weekend = $now.DayOfWeek -in 'Saturday','Sunday'
if (-not $weekend -and -not ($hm -ge 1350 -and $hm -le 1450)) { Write-Host "只准在 13:50-14:50 或週末執行，現在 $($now.ToString('HH:mm'))，不執行。"; exit 1 }

$out = "$env:USERPROFILE\Desktop\kgi_probe_$($now.ToString('yyyyMMdd_HHmm')).txt"
$log = New-Object System.Collections.Generic.List[string]
function Add-Line($s) { $log.Add("[{0}] {1}" -f (Get-Date).ToString('HH:mm:ss.fff'), $s) }
function Hide-Sensitive($s) { $s -replace '(?<!\d)\d{7}(?!\d)', '*******' -replace '[A-Z]\d{9}', 'A*********' -replace '[A-Z]\d{5}\*{4}', 'A*********' -replace '邱柏崴', '***' }

# 1. 下單大師目錄（找執行中的程式，找不到就搜尋）
$om = (Get-Process OrderMaster64 -EA SilentlyContinue | Select-Object -First 1).Path
if (-not $om) { Write-Host "下單大師沒在執行，這次實測沒有意義，不執行。"; exit 1 }
$omDir = Split-Path $om
$tlog = Get-ChildItem "$omDir\Logs\$($now.ToString('yyyyMMdd'))" -Filter "T*.txt" -EA SilentlyContinue | Sort-Object LastWriteTime -Desc | Select-Object -First 1
$omLog = "$omDir\OMLog\$($now.ToString('yyyyMMdd')).txt"
$tlogLines0 = if ($tlog) { (Get-Content $tlog.FullName).Count } else { 0 }
$omLines0 = if (Test-Path $omLog) { (Get-Content $omLog -Encoding UTF8).Count } else { 0 }

# 2. 把 TradeCom 元件複製到獨立資料夾，不動下單大師
$probe = "C:\kgi_probe"; New-Item -ItemType Directory -Force $probe | Out-Null
foreach ($n in 'TradeCom.dll','PushClient.dll','Package.dll','ICSharpCode.SharpZipLib.dll') {
  $src = Get-ChildItem $omDir -Recurse -Filter $n -EA SilentlyContinue | Select-Object -First 1
  if (-not $src) { $src = Get-ChildItem "$env:USERPROFILE\Downloads" -Recurse -Filter $n -EA SilentlyContinue | Select-Object -First 1 }
  if (-not $src) { Write-Host "找不到 $n，停止。"; exit 1 }
  Copy-Item $src.FullName $probe -Force; Add-Line "元件 $n <- $($src.FullName)"
}
Get-ChildItem $omDir -Filter "KGICGCAPIATL2*.dll" | ForEach-Object { Copy-Item $_.FullName $probe -Force }
if (Test-Path "$omDir\Data") { Copy-Item "$omDir\Data" $probe -Recurse -Force }
Set-Location $probe
Add-Type -Path "$probe\Package.dll"; Add-Type -Path "$probe\PushClient.dll"; Add-Type -Path "$probe\TradeCom.dll"

# 3. 帳密
$id = $env:KGI_ID; $kp = $env:KGI_PWD
if (-not $id) { $id = Read-Host "凱基身分證字號" }
if (-not $kp) { $sp = Read-Host "凱基密碼" -AsSecureString; $kp = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sp)) }

# 4. 登入（唯讀：只開回報訂閱與回補）
$asm = [AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.Location -like "$probe*TradeCom.dll" }
$type = $asm.GetTypes() | Where-Object { $_.Name -eq 'TaiFexCom' } | Select-Object -First 1
$langT = $asm.GetTypes() + ([AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { $_.Location -like "$probe*" } | ForEach-Object { $_.GetTypes() }) | Where-Object { $_.Name -eq 'Language' -and $_.IsEnum } | Select-Object -First 1
$com = [Activator]::CreateInstance($type, @('itrade.kgi.com.tw', [uint16]8000, 'API', [Enum]::Parse($langT, 'Chinese')))
$com.AutoSubReport = $true; $com.AutoRecoverReport = $true
$com.AutoSubReportForeign = $false; $com.AutoRecoverReportForeign = $false
$com.AutoRetriveProductInfo = $true

Register-ObjectEvent $com OnRcvMessage -SourceIdentifier kgiMsg | Out-Null
Register-ObjectEvent $com OnGetStatus -SourceIdentifier kgiSt | Out-Null
Register-ObjectEvent $com OnRecoverStatus -SourceIdentifier kgiRec | Out-Null

Add-Line "登入 itrade.kgi.com.tw:8000"
$com.LoginDirect('itrade.kgi.com.tw', [uint16]8000, "$id,,$kp|")
$kp = $null
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end) {
  $e = Wait-Event -Timeout 1
  if (-not $e) { continue }
  try {
    switch ($e.SourceIdentifier) {
      'kgiMsg' { $p = $e.SourceArgs[1]; Add-Line ("MSG {0} {1}" -f $p.GetType().Name, $p.ToLog()) }
      'kgiSt'  { $m = $e.SourceArgs[2]; $t = if ($m) { [Text.Encoding]::Default.GetString($m) } else { '' }; Add-Line ("STATUS {0} {1}" -f $e.SourceArgs[1], $t) }
      'kgiRec' { Add-Line ("RECOVER {0} {1} {2}" -f $e.SourceArgs[1], $e.SourceArgs[2], $e.SourceArgs[3]) }
    }
  } catch { Add-Line "解析錯誤: $($_.Exception.Message)" }
  Remove-Event -EventIdentifier $e.EventIdentifier
}
$com.Logout(); Add-Line "登出"
Start-Sleep 5
$com.Dispose()

# 5. 下單大師在實測期間有沒有斷線
Add-Line "== 下單大師 T log 實測期間新增 =="
if ($tlog) { (Get-Content $tlog.FullName | Select-Object -Skip $tlogLines0) | ForEach-Object { $log.Add("  OM-T " + $_) } }
Add-Line "== 下單大師 OMLog 實測期間新增 =="
if (Test-Path $omLog) { (Get-Content $omLog -Encoding UTF8 | Select-Object -Skip $omLines0) | ForEach-Object { $log.Add("  OM-L " + $_) } }
Add-Line ("下單大師行程仍在: " + [bool](Get-Process OrderMaster64 -EA SilentlyContinue))

Hide-Sensitive ($log -join "`r`n") | Out-File $out -Encoding utf8
Remove-Item $probe -Recurse -Force -EA SilentlyContinue
notepad $out
