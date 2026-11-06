@echo off
REM Registers Windows Scheduled Task for Daily Quran Mix Recitation Video
REM Runs once every afternoon at 03:00 PM BST (15:00)

echo ====================================================
echo  Daily Quran Mix Automation - Scheduler Setup
echo  Runs every day at 03:00 PM BST (15:00)
echo ====================================================
echo.

schtasks /create /tn "Daily_Quran_Mix_Recitation" /tr "E:\Project\youtube_video\schedule_quran_mix.bat" /sc daily /st 15:00 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Daily Quran Mix task registered successfully!
    echo Runs automatically every day at 03:00 PM BST.
) else (
    echo [FAILED] Could not register scheduled task. Make sure to Run as Administrator!
)

echo.
echo ====================================================
echo  Done! Daily Quran Mix video will be generated
echo  and published daily at 03:00 PM BST.
echo ====================================================
echo.
pause
