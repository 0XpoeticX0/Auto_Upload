@echo off
REM ============================================================
REM Daily 1 Quran Recitation Video Pipeline (<90s)
REM Runs daily at 06:00 AM BST (Morning Prime).
REM Alternates daily between Sheikh Alafasy & Sheikh Al-Dossari,
REM passes 3-Stage Gemini Clearance, renders 1080x1920 60FPS video,
REM and publishes automatically to YouTube Shorts, Facebook, and Instagram.
REM ============================================================
cd /d "%~dp0"
echo [Daily Quran Automation] Starting Daily 1 Quran Video Pipeline...

python -m app.quran_verse.scheduler --upload

pause
