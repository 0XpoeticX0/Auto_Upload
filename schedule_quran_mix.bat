@echo off
chcp 65001 > nul
echo ========================================================
echo  Daily Quran Mix (Arabic + Bangla) Recitation Runner
echo  Scheduled for 03:00 PM BST Daily (09:00 AM UTC)
echo ========================================================
cd /d "%~dp0"
python -m app.quran_verse.mix_scheduler --upload %*
