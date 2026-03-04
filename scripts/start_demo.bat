@echo off
REM Start VeriSight Demo Site (Windows)

echo Starting VeriSight Demo Site...
cd demo
python -m http.server 8000
pause
