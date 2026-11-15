@echo off
title DailyDos Messenger AI Bot
cd /d "%~dp0"
echo ===================================================
echo     DailyDos of Islam - Messenger AI Bot
echo ===================================================
echo Checking environment and starting Auto-Reply Poller...
python -m app.bot.poller --loop --interval 20
pause
