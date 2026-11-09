@echo off
REM Python unit tests. For MC trade-by-trade tests: set TXF1_MIN_DATA=path\to\1min.txt first
cd /d %~dp0
python -m pytest -q -p no:cacheprovider tests
pause
