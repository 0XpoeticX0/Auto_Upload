# -*- coding: utf-8 -*-
"""
Dedicated Uploader for 'Ashab al-Ukhdud' Story Video
Uploads to YouTube Shorts, Facebook Reels, and Instagram Reels with auto-pinned comments.
"""
import os
import sys
import json

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.logger import logger
from app.upload.youtube import get_authenticated_service, upload_to_youtube
from app.upload.facebook import upload_to_facebook

VIDEO_PATH = os.path.abspath(r"incoming_audio\rendered_videos\ashab_al_ukhdud_story_9_16.mp4")
METADATA_PATH = os.path.abspath(r"incoming_audio\rendered_videos\ashab_al_ukhdud_story_9_16_metadata.json")

TITLE = "আসহাবুল উখদুদ ও ঈমানদার কিশোরের অবিশ্বাস্য আত্মত্যাগ | Islamic Story"
DESCRIPTION = (
    "সহীহ মুসলিমে বর্ণিত এক অবিশ্বাস্য সত্য ঘটনা—যেখানে এক কিশোর অহংকারী বাদশাহকে শিখিয়ে দিয়েছিল কীভাবে তাকে হত্যা করতে হবে। "
    "কিন্তু সেই ১টি তীরের আঘাতেই গোটা সাম্রাজ্য এক আল্লাহর ওপর ঈমান এনে ফেলে।\n\n"
    "📌 সূত্র: সহীহ মুসলিম (হাদিস নং ৭৪৮৩), সূরা আল-বুরুজ (আয়াত ৪–৯)।\n\n"
    "#IslamicStories #AshabulUkhdud #IslamicHistory #Shorts #Reels #Iman #Allah"
)
TAGS = ["আসহাবুল উখদুদ", "Ashabul Ukhdud", "Islamic Story", "হাদিসের গল্প", "Quran", "ইমান", "Shorts", "Reels", "Bengali Waz"]
FIRST_COMMENT = (
    "হে আল্লাহ! আমাদের ঈমানকে আসহাবুল উখদুদের সেই কিশোরের মতো অটল ও অবিচল রাখুন। আমিন। ❤️\n\n"
    "📌 হাদিস রেফারেন্স: সহীহ মুসলিম (হাদিস নং ৭৪৮৩), সূরা আল-বুরুজ (আয়াত ৪–৯)।"
)

def main():
    print("=" * 60)
    print("Ashab al-Ukhdud Video Uploader (YouTube, FB & IG)")
    print("=" * 60)

    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file not found at {VIDEO_PATH}")
        return False

    print(f"Target Video: {VIDEO_PATH} ({os.path.getsize(VIDEO_PATH)} bytes)")
    print(f"Title: {TITLE}")

    # 1. YouTube Upload
    print("\n[1/3] Uploading to YouTube Shorts...")
    youtube = get_authenticated_service()
    if youtube:
        yt_meta = {
            "title": TITLE[:100],
            "description": DESCRIPTION,
            "tags": TAGS,
            "first_comment": FIRST_COMMENT
        }
        res_yt = upload_to_youtube(VIDEO_PATH, yt_meta, youtube_client=youtube)
        if res_yt:
            print(f"YouTube Upload SUCCESS! Video ID: {res_yt.get('video_id')}")
        else:
            print("YouTube Upload failed.")
    else:
        print("Could not authenticate YouTube service.")

    # 2. Facebook & Instagram Upload
    print("\n[2/3] Uploading to Facebook Reels & Instagram Reels...")
    fb_meta = {
        "title": TITLE,
        "description": f"{TITLE}\n\n{DESCRIPTION}",
        "first_comment": FIRST_COMMENT
    }
    fb_ok = upload_to_facebook(VIDEO_PATH, fb_meta, is_reel=True)
    if fb_ok:
        print("Facebook & Instagram Reel upload finished successfully!")
    else:
        print("Facebook/Instagram upload returned False.")

    print("\n[3/3] Upload Process Completed!")
    return True

if __name__ == "__main__":
    main()
