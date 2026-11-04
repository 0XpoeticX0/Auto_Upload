# -*- coding: utf-8 -*-
"""
Daily 6:00 PM BST Automated Scheduler for Quran Mix (Arabic + Spoken Bangla) Recitations.
Target Time: 06:00 PM BST (12:00 PM UTC) - Evening Prime
Recitation: Sheikh Mishary Rashid Alafasy + Zayed Iqbal (Islamic Foundation translation)
Visuals: 100% Halal Live-Motion Footage
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from app.logger import logger
from app.quran_verse.mix_generator import generate_quran_mix_video
from app.history import record_quran_history

BST = timezone(timedelta(hours=6))
DAILY_MIX_TIME = "06:00 PM BST (12:00 UTC)"

def execute_daily_mix_run(upload: bool = True, surah: int = None) -> dict:
    now_bst = datetime.now(BST)
    date_str = now_bst.strftime("%Y-%m-%d")

    logger.info(f"=== LAUNCHING DAILY 6:00 PM QURAN MIX (ARABIC + BANGLA) PIPELINE ===")
    logger.info(f"Date: {date_str} | Target Time: {DAILY_MIX_TIME}")

    result = generate_quran_mix_video(surah=surah)
    video_path = result["video_path"]
    thumbnail_path = result.get("thumbnail_path")
    metadata = result["metadata"]
    chosen_surah = result["surah"]

    if upload:
        logger.info("Uploading Quran Mix video to platforms...")
        upload_meta = {
            "youtube_title": metadata["title"],
            "description": metadata["description"],
            "pinned_comment": metadata["pinned_comment"],
            "tags": metadata["tags"]
        }

        # 1. YouTube Shorts
        try:
            from app.upload.youtube import upload_to_youtube
            yt_res = upload_to_youtube(video_path, upload_meta, thumbnail_path=thumbnail_path)
            logger.info(f"YouTube Shorts Upload Result: {yt_res}")
        except Exception as e:
            logger.warning(f"YouTube upload notice: {e}")

        # 2. Record to Supabase & Local History
        history_title = f"[কুরআন মিক্স] {metadata['title']}"
        try:
            record_quran_history(
                surah=chosen_surah,
                ayah_start=1,
                ayah_end=result.get("total_ayahs", 1),
                title=history_title,
                reciter_id="alafasy_zayed_iqbal"
            )
            logger.info(f"Recorded to Quran History: Surah {chosen_surah} ('{history_title}')")
        except Exception as e:
            logger.error(f"Failed to record history: {e}")

        # 3. Facebook & Instagram Reels
        try:
            from app.upload.facebook import upload_to_facebook
            fb_res = upload_to_facebook(video_path, upload_meta, video_type="reel", thumbnail_path=thumbnail_path)
            logger.info(f"Facebook/Instagram Reels Upload Result: {fb_res}")
        except Exception as e:
            logger.warning(f"Facebook upload notice: {e}")

        # 4. TikTok
        try:
            from app.upload.tiktok import upload_to_tiktok
            tt_res = upload_to_tiktok(video_path, caption=metadata["title"], tags=metadata["tags"])
            logger.info(f"TikTok Upload Result: {tt_res.get('status')}")
        except Exception as e:
            logger.warning(f"TikTok upload notice: {e}")

    logger.info("=== QURAN MIX PIPELINE FINISHED SUCCESSFULLY ===")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily 6 PM Quran Mix Scheduler")
    parser.add_argument("--surah", type=int, default=None, help="Force specific Surah number")
    parser.add_argument("--upload", action="store_true", default=True, help="Auto upload to platforms")
    parser.add_argument("--no-upload", dest="upload", action="store_false", help="Render only")

    args = parser.parse_args()
    execute_daily_mix_run(upload=args.upload, surah=args.surah)
