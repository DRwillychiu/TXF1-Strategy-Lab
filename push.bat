@echo off
REM ============================================================
REM  push.bat  -  verify (G0+G1) -> git add -A -> commit -> push
REM  Double-click is fine: it asks for the message and pauses.
REM  Or:  .\push.bat "Task 3.3 summary"
REM  NOTE: this file must stay pure ASCII + CRLF, or cmd.exe garbles it.
REM ============================================================
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d %~dp0

set "MSG=%~1"
if not defined MSG set /p "MSG=Commit message: "
if not defined MSG (
  echo No message. Abort.
  goto END
)

where git >nul 2>nul
if errorlevel 1 (
  echo [x] git not found. Install Git for Windows first.
  goto END
)
git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo [x] Not a git repo: %CD%
  echo     Put push.bat in the repo root ^(the folder that has .git^) and run again.
  goto END
)

call verify.bat
if errorlevel 1 (
  echo.
  echo [x] Verification FAILED - nothing committed. Send the lines marked x to Claude.
  goto END
)

echo.
echo ==== Files that will be committed ====
git status --short
echo.
set "OK="
set /p "OK=Commit ALL of the above? (y/N): "
if /I not "%OK%"=="y" (
  echo Aborted - nothing committed.
  goto END
)
git add -A
git commit -m "%MSG%"
if errorlevel 1 (
  echo.
  echo [!] Nothing to commit, or commit failed.
  goto END
)
git push
if errorlevel 1 (
  echo.
  echo [x] Push failed - check network or GitHub login.
  goto END
)
echo.
echo [OK] verified, committed, pushed.

:END
echo.
pause
endlocal
