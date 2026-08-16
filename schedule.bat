@echo off
REM ============================================================
REM Auto-posting schedule: runs at 7:00 AM and 8:00 PM local time
REM Picks a RANDOM duration between 120s (2 min) and 960s (16 min)
REM ============================================================
cd /d "%~dp0"

REM Generate a random duration between 120 and 300 seconds (2-5 min)
REM Capped at 300s: beyond this the free LLM starts repeating itself
FOR /F %%i IN ('powershell -command "Get-Random -Minimum 120 -Maximum 301"') DO SET DURATION=%%i
echo [Schedule] Selected random duration: %DURATION% seconds

python -m app.main --duration %DURATION%

REM Keep the window open if run manually so you can see what happens
pause
