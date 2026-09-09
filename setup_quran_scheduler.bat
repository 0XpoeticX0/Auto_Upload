@echo off
REM Registers Windows Scheduled Tasks for Pure Quran Recitation Videos
REM Runs at:
REM 1. 05:30 AM BST (Dawn Prime)
REM 2. 05:45 PM BST (Maghrib Prime)
REM 3. 10:15 PM BST (Night Peace)

echo ============================================
echo  Pure Quran Automation - Scheduler Setup
echo ============================================
echo.

schtasks /create /tn "QuranRecitation_Dawn" /tr "E:\Project\youtube_video\schedule_quran.bat" /sc daily /st 05:30 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Dawn task created - runs at 05:30 AM every day
) else (
    echo [FAILED] Could not create dawn task
)

schtasks /create /tn "QuranRecitation_Evening" /tr "E:\Project\youtube_video\schedule_quran.bat" /sc daily /st 17:45 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Evening task created - runs at 05:45 PM every day
) else (
    echo [FAILED] Could not create evening task
)

schtasks /create /tn "QuranRecitation_Night" /tr "E:\Project\youtube_video\schedule_quran.bat" /sc daily /st 22:15 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Night task created - runs at 10:15 PM every day
) else (
    echo [FAILED] Could not create night task
)

echo.
echo ============================================
echo  Done! Pure Quran videos are now scheduled
echo  daily at 05:30 AM, 05:45 PM, and 10:15 PM.
echo ============================================
echo.
pause
