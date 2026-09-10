@echo off
title Instagram Reels 4-Day Scheduler ('তাওয়াক্কুলের পরীক্ষা')
cd /d "e:\Project\youtube_video"
echo =======================================================
echo Starting Instagram Reels 4-Day Background Scheduler...
echo =======================================================
python -X utf8 schedule_instagram_parts.py --daemon
pause
