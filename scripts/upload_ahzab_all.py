import os
import sys
import json
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from app.logger import logger
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook
from app.upload.tiktok import upload_to_tiktok

video_path = "e:/Project/youtube_video/surah_al_ahzab_35_vertical.mp4"

title_yt = "সূরা আল-আহযাব (আয়াত ৩৫) | মুমিনদের ১০টি গুণ | Surah Al-Ahzab 35 #shorts #quran"
title_fb = "সূরা আল-আহযাব (আয়াত ৩৫) • মুমিনদের ১০টি অনন্য গুণ ও মহাপুরস্কার"

caption = """📖 সূরা আল-আহযাব (আয়াত ৩৫) • মুমিনদের ১০টি অনন্য গুণ ও মহাপুরস্কার

بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

إِنَّ الْمُسْلِمِينَ وَالْمُسْلِمَاتِ وَالْمُؤْمِنِينَ وَالْمُؤْمِنَاتِ وَالْقَانِتِينَ وَالْقَانِتَاتِ وَالصَّادِقِينَ وَالصَّادِقَاتِ وَالصَّابِرِينَ وَالصَّابِرَاتِ وَالْخَاشِعِينَ وَالْخَاشِعَاتِ وَالْمُتَصَدِّقِينَ وَالْمُتَصَدِّقَاتِ وَالصَّائِمِينَ وَالصَّائِمَاتِ وَالْحَافِظِينَ فُرُوجَهُمْ وَالْحَافِظَاتِ وَالذَّاكِرِينَ اللَّهَ كَثِيرًا وَالذَّاكِرَاتِ أَعَدَّ اللَّهُ لَهُم مَّغْفِرَةً وَأَجْرًا عَظِيمًا

✨ বাংলা অনুবাদ:
“নিশ্চয়ই আত্মসমর্পণকারী পুরুষ ও আত্মসমর্পণকারী নারী, মুমিন পুরুষ ও মুমিন নারী, অনুগত পুরুষ ও অনুগত নারী, সত্যবাদী পুরুষ ও সত্যবাদী নারী, ধৈর্যশীল পুরুষ ও ধৈর্যশীল নারী, বিনীত পুরুষ ও বিনীত নারী, দানশীল পুরুষ ও দানশীল নারী, সিয়াম পালনকারী পুরুষ ও সিয়াম পালনকারী নারী, নিজেদের শালীনতা ও যৌনাঙ্গ হেফাজতকারী পুরুষ ও নারী এবং আল্লাহকে অধিক স্মরণকারী পুরুষ ও নারী— আল্লাহ তাদের জন্য প্রস্তুত রেখেছেন মহাক্ষমা ও এক মহাপুরস্কার।”

🌿 প্রতিদিনের সহীহ আমল, দোয়া ও কুরআন তিলাওয়াতের জন্য Follow করুন:
👉 @dailydos_islam

💬 কমেন্টে একবার 'সুবহানাল্লাহ' অথবা 'আমিন' লিখুন এবং সদকায়ে জারিয়া হিসেবে ভিডিওটি শেয়ার করুন।

#surahalahzab #quranrecitation #quranbangla #islamicvideo #dailydos_islam #quranverses #islamicstatus #banglaislamic #shorts #reels #viralquran"""

tags = [
    "surahalahzab", "surah al ahzab 35", "quran recitation", 
    "quran bangla", "islamic video", "dailydos_islam", "quran verses", 
    "islamic status", "bangla islamic", "shorts", "reels", "viral quran"
]

yt_metadata = {
    "youtube_title": title_yt,
    "description": caption,
    "tags": tags,
    "category_id": "27",
    "privacy_status": "public"
}

fb_metadata = {
    "facebook_title": title_fb,
    "youtube_title": title_yt,
    "description": caption,
    "pinned_comment": "আল্লাহ আমাদের সবাইকে এই গুণগুলো অর্জন করার তাওফিক দিন—আমিন! 🌿 সদকায়ে জারিয়া হিসেবে শেয়ার করুন।"
}

print("==================================================")
print("Multi-Platform Upload (No-Duplicate Instagram Flow)")
print("==================================================")

results = {}

# 1. YouTube Shorts Upload
print("\n[1/3] Uploading to YouTube Shorts...")
try:
    yt_res = upload_to_youtube(video_path, yt_metadata)
    results["YouTube"] = "SUCCESS" if yt_res else "FAILED"
except Exception as e:
    results["YouTube"] = f"ERROR: {e}"

# 2. Facebook Reels + Instagram Cross-Post (Single execution)
print("\n[2/3] Uploading to Facebook Reels & Instagram (@dailydos_islam)...")
try:
    fb_res = upload_to_facebook(video_path, fb_metadata, video_type="reel")
    results["Facebook & Instagram"] = "SUCCESS" if fb_res else "FAILED"
except Exception as e:
    results["Facebook & Instagram"] = f"ERROR: {e}"

# 3. TikTok Upload
print("\n[3/3] Uploading to TikTok...")
try:
    tiktok_res = upload_to_tiktok(video_path, caption[:1000], tags=tags[:5])
    results["TikTok"] = tiktok_res.get("status", "FAILED") if isinstance(tiktok_res, dict) else "SUCCESS"
except Exception as e:
    results["TikTok"] = f"ERROR: {e}"

print("\n==================================================")
print("Upload Summary:")
for platform, status in results.items():
    print(f"  - {platform}: {status}")
print("==================================================")
