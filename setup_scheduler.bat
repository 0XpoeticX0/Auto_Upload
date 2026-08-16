@echo off
REM This script must be run as Administrator
REM It will register your YouTube Automation to run at 7:00 AM and 8:00 PM every day

echo ============================================
echo  YouTube Automation - Task Scheduler Setup
echo ============================================
echo.

REM Create Morning Task (7:00 AM daily)
schtasks /create /tn "YouTubeAutomation_Morning" /tr "E:\Project\youtube_video\schedule.bat" /sc daily /st 07:00 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Morning task created - runs at 7:00 AM every day
) else (
    echo [FAILED] Could not create morning task
)

REM Create Evening Task (8:00 PM daily)
schtasks /create /tn "YouTubeAutomation_Evening" /tr "E:\Project\youtube_video\schedule.bat" /sc daily /st 20:00 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Evening task created - runs at 8:00 PM every day
) else (
    echo [FAILED] Could not create evening task
)

echo.
echo ============================================
echo  Done! Your videos will now upload daily
echo  automatically at 7:00 AM and 8:00 PM.
echo  This persists through shutdowns/restarts.
echo ============================================
echo.
pause
