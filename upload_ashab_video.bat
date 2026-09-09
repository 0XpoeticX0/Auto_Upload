@echo off
chcp 65001 > nul
cd /d "e:\Project\youtube_video"
echo ========================================================
echo Uploading Ashab al-Ukhdud Story Video
echo Platforms: YouTube Shorts, Facebook Reels, Instagram Reels
echo ========================================================
python upload_ashab_video.py
pause
