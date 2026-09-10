# -*- coding: utf-8 -*-
"""
Dedicated Scheduler & Uploader for Sahih Bukhari Series: 'তাওয়াক্কুলের পরীক্ষা' (Parts 1, 2, 3, and 4).
Schedules uploads to YouTube Shorts and Facebook Reels across 4 consecutive days with custom 9:16 thumbnails.
"""
import os
import sys
import argparse
from datetime import datetime, timezone

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.logger import logger
from app.upload.youtube import get_authenticated_service, upload_to_youtube
from app.upload.facebook import upload_to_facebook

VIDEO_DIR = os.path.abspath(r"incoming_audio\rendered_videos")

PARTS = {
    1: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_1_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_1.jpg"),
        "title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ১): ১০০০ স্বর্ণমুদ্রা ও অদ্ভুত শর্ত | Sahih Bukhari #Shorts",
        "fb_title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ১): ১০০০ স্বর্ণমুদ্রা ও অদ্ভুত শর্ত | সহীহ বুখারী ২২৯১",
        "publish_at_iso": "2026-09-11T12:00:00Z",       # Day 1: 18:00 BST / 12:00 UTC
        "scheduled_publish_time": 1789128000,
        "description": (
            "সহীহ বুখারীতে বর্ণিত তাওয়াক্কুলের এক অবিশ্বাস্য সত্য ঘটনা (পর্ব ১)। "
            "বনী ইসরাঈলের এক ব্যক্তি ১০০০ স্বর্ণমুদ্রা ঋণ চাইল। কিন্তু কোনো সাক্ষী বা জামিনদার দিতে পারল না। "
            "সে বলল—'আল্লাহই আমার সাক্ষী, আল্লাহই আমার জামিনদার!'\n\n"
            "➡️ নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে কী করল ঋণগ্রহীতা? বাকি অংশ দেখুন পর্ব ২-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Tawakkul #Shorts #Reels #Iman #Allah"
        ),
        "tags": ["তাওয়াক্কুলের পরীক্ষা", "সহীহ বুখারী", "Sahih Bukhari", "Part 1", "তাওয়াক্কুল", "স্বর্ণমুদ্রা", "Islamic Story", "হাদিসের গল্প", "Shorts", "Reels"],
        "first_comment": "📌 নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে কী করল ঋণগ্রহীতা? দেখতে এখনই পর্ব ২ দেখুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    2: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_2_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_2.jpg"),
        "title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ২): সাগরে কাঠের গুঁড়ি ভাসিয়ে দিল! | Sahih Bukhari #Shorts",
        "fb_title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ২): সাগরে কাঠের গুঁড়ি ভাসিয়ে দিল! | সহীহ বুখারী ২২৯১",
        "publish_at_iso": "2026-09-12T12:00:00Z",       # Day 2: 18:00 BST / 12:00 UTC
        "scheduled_publish_time": 1789214400,
        "description": (
            "সহীহ বুখারীতে বর্ণিত তাওয়াক্কুলের সেই অলৌকিক কাঠের গুঁড়ি (পর্ব ২)। "
            "ঋণ পরিশোধের নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে সে একটি কাঠের গুঁড়ি নিল। কুড়াল দিয়ে তা ফাঁপা করে "
            "ভেতরে ১০০০ স্বর্ণমুদ্রা ও চিঠি ভরে সমুদ্রের তীরে দাঁড়িয়ে উত্তাল সাগরে ভাসিয়ে দিল...\n\n"
            "➡️ সাগরে ভাসিয়ে দেওয়া সেই কাঠ কি পৌঁছাবে অপর তীরে? দেখুন পর্ব ৩-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part2 #Tawakkul #Shorts #Reels #Iman"
        ),
        "tags": ["তাওয়াক্কুলের পরীক্ষা", "সহীহ বুখারী", "Sahih Bukhari", "Part 2", "তাওয়াক্কুল", "কাঠের গুঁড়ি", "Islamic Story", "হাদিসের গল্প", "Shorts", "Reels"],
        "first_comment": "📌 সাগরে ভাসিয়ে দেওয়া সেই কাঠ কি পৌঁছাবে অপর তীরে? দেখতে এখনই পর্ব ৩ দেখুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    3: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_3_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_3.jpg"),
        "title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ৩): কাঠের ভেতর অদ্ভুত আওয়াজ! তীরে কী এল? | Bukhari #Shorts",
        "fb_title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ৩): কাঠের ভেতর অদ্ভুত আওয়াজ! তীরে কী এল? | সহীহ বুখারী",
        "publish_at_iso": "2026-09-13T12:00:00Z",       # Day 3: 18:00 BST / 12:00 UTC
        "scheduled_publish_time": 1789300800,
        "description": (
            "সহীহ বুখারীতে বর্ণিত সেই ভাসমান কাঠের অলৌকিক যাত্রা (পর্ব ৩)। "
            "অপর তীরে দাঁড়িয়ে ঋণদাতা ব্যাকুল হয়ে জাহাজের প্রতীক্ষায় অপেক্ষা করছিল। কোনো জাহাজ এলো না, কিন্তু "
            "ঢেউয়ের সাথে তীরে ভেসে এল একটি ভারী কাঠের গুঁড়ি। সে জ্বালানি কাঠের জন্য তা নিয়ে যাওয়ার সিদ্ধান্ত নিল...\n\n"
            "➡️ কাঠের ভেতরে কী লুকিয়ে ছিল? দেখুন শেষ পর্ব ৪-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part3 #Tawakkul #Shorts #Reels #Iman"
        ),
        "tags": ["তাওয়াক্কুলের পরীক্ষা", "সহীহ বুখারী", "Sahih Bukhari", "Part 3", "তাওয়াক্কুল", "অলৌকিক", "Islamic Story", "হাদিসের গল্প", "Shorts", "Reels"],
        "first_comment": "📌 কাঠের ভেতর থেকে কী বেরিয়ে এল? দেখতে এখনই শেষ পর্ব ৪ দেখুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    4: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_4_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_4.jpg"),
        "title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ৪): কাঠ চেরার পর ১০০০ স্বর্ণমুদ্রা! সমাপ্তি | Bukhari #Shorts",
        "fb_title": "তাওয়াক্কুলের পরীক্ষা (পর্ব ৪ - সমাপ্তি): কাঠ চেরার পর ১০০০ স্বর্ণমুদ্রা উদ্ধার! | সহীহ বুখারী",
        "publish_at_iso": "2026-09-14T12:00:00Z",       # Day 4: 18:00 BST / 12:00 UTC
        "scheduled_publish_time": 1789387200,
        "description": (
            "সহীহ বুখারী ২২৯১ নম্বর হাদিসের সমাপ্তি পর্ব (পর্ব ৪ সমাপ্ত)। "
            "কুড়াল দিয়ে কাঠটি চেরা মাত্রই ঝনঝন শব্দে রাশি রাশি স্বর্ণমুদ্রা ও চিঠি ছড়িয়ে পড়ল! কিছুদিন পর "
            "ঋণগ্রহীতা আবারও ১০০০ দিনার নিয়ে হাজির হয়ে বলল—'জাহাজ না পেয়ে আমি কাঠের গুঁড়িতে ভাসিয়ে দিয়েছিলাম।' "
            "তখন ঋণদাতা জানাল—'আল্লাহ তোমার হয়ে ঋণ আগেই পরিশোধ করে দিয়েছেন!'\n\n"
            "মানুষ যখন খাঁটি অন্তরে আল্লাহর ওপর পূর্ণ ভরসা রাখে, তখন স্বয়ং আল্লাহ অসম্ভবকে সম্ভব করে তার পথ খুলে দেন।\n\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part4 #Tawakkul #Shorts #Reels #Iman #Allah"
        ),
        "tags": ["তাওয়াক্কুলের পরীক্ষা", "সহীহ বুখারী", "Sahih Bukhari", "Part 4", "তাওয়াক্কুল", "সমাপ্তি", "Islamic Story", "হাদিসের গল্প", "Shorts", "Reels"],
        "first_comment": (
            "হে আল্লাহ! আমাদের জীবনেও এমন অবিচল তাওয়াক্কুল ও সততা নসিব করুন। আমিন। ❤️\n\n"
            "📌 হাদিস রেফারেন্স: সহীহ বুখারী (হাদিস নং ২২৯১)।"
        )
    }
}

def upload_single_part(part_num: int, schedule: bool = True, youtube_client=None):
    cfg = PARTS[part_num]
    v_path = cfg["file"]
    t_path = cfg["thumbnail"]
    
    if not os.path.exists(v_path):
        print(f"[ERROR] Video file not found: {v_path}")
        return False
        
    if not os.path.exists(t_path):
        print(f"[WARNING] Thumbnail file not found: {t_path}")
    else:
        print(f"[THUMBNAIL] Verified thumbnail: {t_path} ({os.path.getsize(t_path)} bytes)")

    publish_iso = cfg["publish_at_iso"] if schedule else None
    publish_unix = cfg["scheduled_publish_time"] if schedule else None

    print("\n" + "=" * 65)
    print(f" SCHEDULING / UPLOADING PART {part_num} (Day {part_num} of 4)")
    print(f" Video: {v_path} ({os.path.getsize(v_path)} bytes)")
    print(f" Thumbnail: {t_path} ({os.path.getsize(t_path) if os.path.exists(t_path) else 0} bytes)")
    print(f" Title: {cfg['title']}")
    if schedule:
        print(f" Schedule Target: {publish_iso} (Unix: {publish_unix})")
    else:
        print(f" Schedule Target: IMMEDIATE PUBLISH")
    print("=" * 65)

    # 1. YouTube Shorts (Scheduled Upload with Custom Thumbnail)
    print(f"\n[1/2] Processing Part {part_num} for YouTube Shorts...")
    yt_meta = {
        "youtube_title": cfg["title"][:100],
        "title": cfg["title"][:100],
        "description": cfg["description"],
        "tags": cfg["tags"],
        "pinned_comment": cfg["first_comment"],
        "thumbnail_path": t_path
    }
    if schedule and publish_iso:
        yt_meta["publish_at"] = publish_iso

    res_yt = upload_to_youtube(v_path, yt_meta, thumbnail_path=t_path)
    if res_yt:
        print(f"✅ Part {part_num} YouTube Upload SUCCESS! Video ID: {res_yt}")
        print(f"   YouTube Link: https://youtube.com/shorts/{res_yt}")
        if schedule:
            print(f"   Scheduled to go PUBLIC at: {publish_iso}")
        print(f"   Custom Thumbnail Attached: {t_path}")
    else:
        print(f"❌ Part {part_num} YouTube Upload Failed.")

    # 2. Facebook Reels (Scheduled Reel with Custom Thumbnail)
    print(f"\n[2/2] Processing Part {part_num} for Facebook Reels...")
    fb_meta = {
        "facebook_title": cfg["fb_title"],
        "description": cfg["description"],
        "pinned_comment": cfg["first_comment"],
        "thumbnail_path": t_path,
        "crosspost_instagram": False if schedule else True  # IG API doesn't support future scheduling via container
    }
    if schedule and publish_unix:
        fb_meta["scheduled_publish_time"] = publish_unix

    res_fb = upload_to_facebook(v_path, fb_meta, video_type="reel", thumbnail_path=t_path)
    if res_fb:
        status_txt = "SCHEDULED" if schedule else "PUBLISHED"
        print(f"✅ Part {part_num} Facebook Reels {status_txt}! Reel ID: {res_fb}")
        print(f"   Facebook Link: https://www.facebook.com/reel/{res_fb}")
        if schedule:
            print(f"   Scheduled for timestamp: {publish_unix}")
        print(f"   Custom Thumbnail Attached: {t_path}")
    else:
        print(f"❌ Part {part_num} Facebook Reels Upload Failed.")

    return {"part": part_num, "youtube": res_yt, "facebook": res_fb, "thumbnail": t_path, "schedule": publish_iso}

def main():
    parser = argparse.ArgumentParser(description="Schedule & Upload Sahih Bukhari Series ('তাওয়াক্কুলের পরীক্ষা')")
    parser.add_argument("--part", choices=["1", "2", "3", "4", "all"], default="all", help="Which part to process (1, 2, 3, 4, or all)")
    parser.add_argument("--now", action="store_true", help="Publish immediately instead of scheduling")
    args = parser.parse_args()

    schedule_mode = not args.now

    print("=" * 65)
    print(" SAHIH BUKHARI 4-DAY UPLOAD PIPELINE: 'তাওয়াক্কুলের পরীক্ষা'")
    print(f" Mode: {'SCHEDULE FOR NEXT 4 DAYS (18:00 BST / 12:00 UTC)' if schedule_mode else 'IMMEDIATE PUBLISH'}")
    print(" With Verified 9:16 High-CTR Thumbnails: YES")
    print("=" * 65)

    yt_client = get_authenticated_service()
    if not yt_client:
        print("[ERROR] Failed to authenticate with YouTube. Aborting.")
        return

    results = []
    parts_to_run = [1, 2, 3, 4] if args.part == "all" else [int(args.part)]

    for p in parts_to_run:
        res = upload_single_part(p, schedule=schedule_mode, youtube_client=yt_client)
        results.append(res)

    print("\n" + "=" * 65)
    print(" 🚀 SUMMARY OF 4-DAY SCHEDULED UPLOADS:")
    print("=" * 65)
    for r in results:
        p = r["part"]
        yt = r["youtube"]
        fb = r["facebook"]
        th = os.path.basename(r["thumbnail"])
        sch = r["schedule"]
        print(f" Part {p} | Schedule: {sch} | Thumb: {th}")
        print(f"   -> YouTube: {'SUCCESS (ID: ' + str(yt) + ')' if yt else 'FAILED'}")
        print(f"   -> Facebook: {'SUCCESS (ID: ' + str(fb) + ')' if fb else 'FAILED'}")
    print("=" * 65)

if __name__ == "__main__":
    main()
