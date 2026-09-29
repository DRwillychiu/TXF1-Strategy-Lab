@echo off
REM ============================================================
REM  verify.bat  -  run before every commit (G0 + G0b + G1), and
REM  after any backtest (G3).   Usage:
REM    verify.bat                                  -> G0 + G0b + G1
REM    verify.bat <report.xlsx> <baseline.json>    -> G0 + G0b + G1 + G3
REM ============================================================
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d %~dp0

echo ==== G0 docs check: CLAUDE.md / PROGRESS.md ====
python tools\verify_docs.py .
if errorlevel 1 goto FAIL

echo.
echo ==== G0b version sync: LIVE_VERSIONS / research Load Names / retired phrases / decision links ====
python tools\verify_versions.py .
if errorlevel 1 goto FAIL

echo.
echo ==== G1 static check: strategies\live ====
python tools\verify_static.py strategies\live
if errorlevel 1 goto FAIL

if "%~1"=="" goto SKIPG3
echo.
echo ==== G3 backtest baseline ====
python tools\verify_baseline.py "%~1" "%~2"
if errorlevel 1 goto FAIL
goto PASS

:SKIPG3
echo.
echo ==== G3 skipped (no report given) ====

:PASS
echo.
echo ALL PASS - OK to commit
exit /b 0

:FAIL
echo.
echo FAILED - STOP. Do not commit. Send the lines marked x to Claude.
exit /b 1
