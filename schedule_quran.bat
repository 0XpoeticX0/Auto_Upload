@echo off
REM ============================================================
REM Auto-posting schedule for Pure Quran Recitation Videos (<90s)
REM Automatically detects active BST Prime Slot (Dawn/Evening/Night),
REM runs 3-Stage Gemini Clearance, renders 1080x1920 60FPS video,
REM and publishes to YouTube Shorts, Facebook, and Instagram.
REM ============================================================
cd /d "%~dp0"
echo [Schedule] Launching Pure Quran Recitation Automation...

python -m app.quran_verse.scheduler --slot auto --upload

pause
