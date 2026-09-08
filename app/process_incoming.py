# -*- coding: utf-8 -*-
"""
Automated Incoming Video Processor & Multi-Platform Uploader
1. Detects newly dropped videos in incoming_videos/ (or Downloads)
2. Removes watermarks & enforces vertical 9:16 (1080x1920) Shorts format
3. Auto-generates high-CTR metadata & authentic Hadith captions
4. Uploads to YouTube Shorts, Facebook Reels, Instagram Reels, and TikTok
5. Moves processed files to incoming_videos/processed/
"""

import os
import sys
import time
import shutil
import glob
from app.logger import logger
from app.video.watermark_remover import process_and_clean_video, get_video_info
from app.llm.provider import extract_json
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook
from app.upload.tiktok import upload_to_tiktok

INCOMING_DIR = os.path.abspath("incoming_videos")
PROCESSED_DIR = os.path.join(INCOMING_DIR, "processed")
CLEANED_DIR = os.path.join(INCOMING_DIR, "cleaned_output")

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)

def generate_video_metadata(filename: str, clean_video_path: str) -> dict:
    """Uses Gemini to generate viral, authentic titles, captions, and hashtags."""
    base_name = os.path.splitext(os.path.basename(filename))[0]
    
    system_prompt = """You are a master viral Islamic 3D animation content strategist for YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok.
Generate engaging, viral metadata for this video in Bengali and English.

MANDATORY RULES:
1. Title: Catchy, curiosity-driven (under 60 chars) with relevant emojis and #Shorts.
2. Description: Hook in first line, Islamic context, authentic Hadith reference (e.g. Sahih Muslim or Sahih Bukhari), followed by clean Dawah CTA.
3. Authentic CTA: Use 'রাসূলুল্লাহ (ﷺ) বলেছেন: যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়। [সহীহ মুসলিম: ১৮৯৩] 🌿'
4. NEVER use unverified claims like 'কমেন্টে লিখলে সদকায়ে জারিয়া হবে'.
5. Pinned Comment: A thoughtful question or reminder.

Output ONLY valid JSON:
{
    "youtube_title": "New fear unlocked 😳 খালেদের মুখ দিয়ে শয়তান ঢোকার উপক্রম! 😭 #Shorts",
    "facebook_title": "হাই তোলার সময় মুখ না ঢাকলে যা ঘটে 😳 (নবীজির সহীহ সুন্নাহ)",
    "description": "ভিডিওর ক্যাপশন ও সহীহ হাদিস...",
    "pinned_comment": "আপনি কি হাই তোলার সময় মুখ ঢাকেন? সুন্নাহ মেনে আমল করার জন্য রিলটি Save করে রাখুন 🌿",
    "tags": ["Shorts", "Sunnah", "IslamicAnimation", "MuslimKids", "Hadith", "DailyDos", "ReelsViral", "সহীহ_হাদিস"]
}"""

    user_prompt = f"Video Filename / Topic: {base_name}\\nGenerate high-CTR metadata in Bengali and English."

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=1000)
        if data and isinstance(data, dict):
            return data
    except Exception as e:
        logger.warning(f"Failed to generate LLM metadata: {e}")

    # Fallback metadata
    return {
        "youtube_title": f"{base_name[:60]} #Shorts",
        "facebook_title": f"{base_name[:60]}",
        "description": f"""✨ দৈনন্দিন সহীহ আমল ও সুন্নাহ শিক্ষা ✨

{base_name}

রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿

#Shorts #Sunnah #DailyDos #IslamicReminder""",
        "pinned_comment": "আমলটি নিয়মিত পালন করতে রিলটি Save করে রাখুন এবং বন্ধুদের সাথে Share করুন 🌿",
        "tags": ["Shorts", "Sunnah", "IslamicAnimation", "DailyDos", "সহীহ_হাদিস"]
    }

def process_single_video(raw_video_path: str, upload_platforms: bool = True) -> bool:
    """Full workflow: clean watermark -> format 9:16 -> generate metadata -> upload -> archive."""
    logger.info(f"=== PROCESSING INCOMING VIDEO: {os.path.basename(raw_video_path)} ===")
    
    filename = os.path.basename(raw_video_path)
    clean_filename = f"clean_{int(time.time())}_{filename}"
    clean_path = os.path.join(CLEANED_DIR, clean_filename)

    # 1. Remove Watermark & Enforce 9:16 (1080x1920)
    try:
        process_and_clean_video(
            input_path=raw_video_path,
            output_path=clean_path,
            mode="smart_safe_crop"
        )
    except Exception as e:
        logger.error(f"Failed to clean video: {e}")
        return False

    # 2. Generate Metadata
    metadata = generate_video_metadata(filename, clean_path)
    logger.info(f"Generated Title: {metadata.get('youtube_title')}")

    # 3. Upload to All Platforms if enabled
    if upload_platforms:
        logger.info("Uploading to social platforms...")

        # YouTube Shorts
        try:
            yt_ok = upload_to_youtube(clean_path, metadata)
            logger.info(f"YouTube Upload Status: {yt_ok}")
        except Exception as e:
            logger.warning(f"YouTube upload error: {e}")

        # Facebook & Instagram Reels
        try:
            fb_ok = upload_to_facebook(clean_path, metadata, video_type="reel")
            logger.info(f"Facebook / Instagram Upload Status: {fb_ok}")
        except Exception as e:
            logger.warning(f"Facebook/Instagram upload error: {e}")

        # TikTok
        try:
            tt_res = upload_to_tiktok(
                clean_path,
                caption=metadata.get("youtube_title", filename),
                tags=metadata.get("tags", [])
            )
            logger.info(f"TikTok Upload Status: {tt_res.get('status')}")
        except Exception as e:
            logger.warning(f"TikTok upload error: {e}")

    # 4. Move raw video to processed folder
    dest_path = os.path.join(PROCESSED_DIR, filename)
    try:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        shutil.move(raw_video_path, dest_path)
        logger.info(f"Archived original video to: {dest_path}")
    except Exception as e:
        logger.warning(f"Could not move original video: {e}")

    logger.info(f"=== COMPLETED INCOMING VIDEO: {filename} ===")
    return True

def run_incoming_scan(upload_platforms: bool = True):
    """Scans incoming_videos/ for pending video files."""
    valid_exts = ("*.mp4", "*.mov", "*.mkv", "*.webm")
    files = []
    for ext in valid_exts:
        files.extend(glob.glob(os.path.join(INCOMING_DIR, ext)))

    if not files:
        logger.info(f"No pending videos found in {INCOMING_DIR}")
        return

    logger.info(f"Found {len(files)} pending video(s) to process.")
    for f in files:
        process_single_video(f, upload_platforms=upload_platforms)

def watch_incoming_folder(poll_interval: int = 10, upload_platforms: bool = True):
    """Continuously monitors incoming_videos/ for new downloads."""
    logger.info(f"Watching '{INCOMING_DIR}' for new video downloads (Ctrl+C to stop)...")
    while True:
        try:
            run_incoming_scan(upload_platforms=upload_platforms)
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped watching folder.")
            break
        except Exception as e:
            logger.error(f"Watcher error: {e}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process incoming videos & upload to all platforms")
    parser.add_argument("--watch", action="store_true", help="Continuously monitor incoming_videos/ folder")
    parser.add_argument("--file", type=str, help="Process a specific video file")
    parser.add_argument("--no-upload", action="store_true", help="Clean & format only, skip uploading")
    args = parser.parse_args()

    upload = not args.no_upload
    if args.file:
        process_single_video(args.file, upload_platforms=upload)
    elif args.watch:
        watch_incoming_folder(upload_platforms=upload)
    else:
        run_incoming_scan(upload_platforms=upload)
