@echo off
REM Registers Windows Scheduled Task for Daily 1 Quran Recitation Video
REM Runs once every morning at 06:00 AM BST

echo ====================================================
echo  Daily 1 Quran Video Automation - Scheduler Setup
echo ====================================================
echo.

schtasks /create /tn "Daily_Quran_Recitation" /tr "E:\Project\youtube_video\schedule_quran.bat" /sc daily /st 06:00 /f /rl highest
if %errorlevel% == 0 (
    echo [OK] Daily Quran task registered successfully!
    echo Runs automatically every day at 06:00 AM BST.
) else (
    echo [FAILED] Could not register scheduled task. Make sure to Run as Administrator!
)

echo.
echo ====================================================
echo  Done! Exactly 1 Pure Quran video will be generated
echo  and published daily at 06:00 AM.
echo  Alternates daily between Alafasy and Al-Dossari.
echo ====================================================
echo.
pause
