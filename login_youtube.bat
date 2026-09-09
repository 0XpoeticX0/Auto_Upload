@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   YouTube Authentication ^& Quran Video Uploader
echo ========================================================
echo.
echo Opening browser for Google login...
echo Please select your YouTube account and click 'Allow'.
echo.
python upload_latest_video.py
echo.
pause
