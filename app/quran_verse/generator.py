# -*- coding: utf-8 -*-
"""
Main Pipeline Runner for Quran Verse Video Generation (< 90s).
Handles:
1. Meaningful passage selection (AI or manual)
2. Authentic online audio download & mastering (Alafasy / Dossari)
3. 60 FPS vertical video rendering with centered Bengali subtitles
4. Platform metadata generation & optional auto-upload.
"""

import os
import sys
import time
import random
import argparse
from app.logger import logger
from app.history import get_recent_video_titles, _supabase_insert
from app.quran_verse.quran_data import (
    RECITERS_CONFIG,
    fetch_verse_data,
    select_meaningful_passage_ai
)
from app.quran_verse.verifier import verify_quran_passage_3x
from app.quran_verse.audio_manager import prepare_recitation_audio
from app.quran_verse.renderer import render_quran_verse_video
from app.quran_verse.metadata import generate_quran_metadata

def generate_quran_verse_video(
    surah: int = None,
    ayah_start: int = None,
    ayah_end: int = None,
    reciter_id: str = None
) -> dict:
    """
    End-to-end generation of a Quran video under 90s.
    Returns {
        "video_path": str,
        "metadata": dict,
        "verse_data": dict,
        "audio_data": dict
    }
    """
    logger.info("=== STARTING PURE QURAN RECITATION VIDEO PIPELINE ===")

    # 1. Select reciter (rotate between Alafasy and Dossari if not specified)
    if not reciter_id or reciter_id not in RECITERS_CONFIG:
        reciter_id = random.choice(["alafasy", "dossari"])

    reciter = RECITERS_CONFIG[reciter_id]
    logger.info(f"Selected Reciter: {reciter['name_bn']} ({reciter['name_en']})")

    # 2. Select & Clear Quran Verse Passage via 3-Stage Gemini Clearance Gate
    recent_history = get_recent_video_titles(limit=40)
    max_selection_retries = 3
    verse_data = None

    for attempt in range(1, max_selection_retries + 1):
        if surah and ayah_start:
            end = ayah_end or ayah_start
            v_cand = fetch_verse_data(surah, ayah_start, end)
            v_cand["reciter_id"] = reciter_id
            v_cand["reciter"] = reciter
            v_cand["theme_headline"] = f"{v_cand['surah_name_bn']} (আয়াত {v_cand['verse_range_str']})"
            v_cand["reflection_bn"] = ""
        else:
            v_cand = select_meaningful_passage_ai(reciter_id=reciter_id, recent_history=recent_history)

        cleared, clearance_report = verify_quran_passage_3x(v_cand)
        if cleared:
            verse_data = v_cand
            verse_data["clearance_report"] = clearance_report
            logger.info(f"Passage cleared all 3 stages on attempt {attempt}: {verse_data['surah_name_bn']} ({verse_data['verse_range_str']})")
            break
        else:
            logger.warning(f"Passage failed 3-Stage Clearance Gate on attempt {attempt}: {clearance_report}")
            if surah and ayah_start:
                # If specific manual passage was requested, still proceed with warning
                verse_data = v_cand
                break

    if not verse_data:
        raise RuntimeError("Failed to obtain a 100% verified Quran passage after 3-Stage Gemini Clearance checks.")

    # 3. Download & Master Audio (< 90s)
    audio_data = prepare_recitation_audio(verse_data)
    total_dur = audio_data["total_duration"]

    if total_dur > 90.0:
        logger.warning(f"Audio duration {total_dur:.1f}s is over 90s. Trimming or proceeding with warning.")

    # 4. Generate Metadata
    metadata = generate_quran_metadata(verse_data, audio_data)

    # 5. Render Video (1080x1920 60FPS) with Centered Bengali Translation Subtitles
    video_path = render_quran_verse_video(verse_data, audio_data)

    return {
        "video_path": video_path,
        "metadata": metadata,
        "verse_data": verse_data,
        "audio_data": audio_data
    }

def run_quran_verse_pipeline(
    surah: int = None,
    ayah_start: int = None,
    ayah_end: int = None,
    reciter_id: str = None,
    upload: bool = False
) -> dict:
    """
    Executes the Quran video pipeline, with optional automated social media upload.
    """
    result = generate_quran_verse_video(surah, ayah_start, ayah_end, reciter_id)
    video_path = result["video_path"]
    metadata = result["metadata"]

    if upload:
        logger.info("Uploading Quran video to platforms...")
        upload_meta = {
            "youtube_title": metadata["title"],
            "description": metadata["description"],
            "pinned_comment": metadata["pinned_comment"],
            "tags": metadata["tags"]
        }

        # YouTube Shorts
        try:
            from app.upload.youtube import upload_to_youtube
            yt_ok = upload_to_youtube(video_path, upload_meta)
            logger.info(f"YouTube Shorts Upload: {yt_ok}")
        except Exception as e:
            logger.warning(f"YouTube upload notice: {e}")

        # Facebook & Instagram Reels
        try:
            from app.upload.facebook import upload_to_facebook
            fb_ok = upload_to_facebook(video_path, upload_meta, video_type="reel")
            logger.info(f"Facebook/Instagram Reels Upload: {fb_ok}")
        except Exception as e:
            logger.warning(f"Facebook upload notice: {e}")

        # TikTok
        try:
            from app.upload.tiktok import upload_to_tiktok
            tt_res = upload_to_tiktok(video_path, caption=metadata["title"], tags=metadata["tags"])
            logger.info(f"TikTok Upload: {tt_res.get('status')}")
        except Exception as e:
            logger.warning(f"TikTok upload notice: {e}")

        # Record to Supabase
        rec_id = f"quran_{result['verse_data']['surah']}_{int(time.time())}"
        history_title = f"[কুরআন তিলাওয়াত] {metadata['title']}"
        _supabase_insert({
            "id": rec_id,
            "title": history_title,
            "source": "quran_verse_pipeline"
        })
        logger.info(f"Recorded to Supabase: '{history_title}'")

    logger.info("=== QURAN PIPELINE EXECUTION FINISHED SUCCESSFULLY ===")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quran Verse Video Pipeline (< 90s)")
    parser.add_argument("--surah", type=int, default=None, help="Surah number (e.g. 94)")
    parser.add_argument("--ayah", type=str, default=None, help="Ayah or range (e.g. '5' or '1-8')")
    parser.add_argument("--reciter", type=str, choices=["alafasy", "dossari"], default=None, help="Reciter id")
    parser.add_argument("--upload", action="store_true", help="Upload after rendering")

    args = parser.parse_args()

    a_start = None
    a_end = None
    if args.ayah:
        if "-" in args.ayah:
            parts = args.ayah.split("-")
            a_start = int(parts[0])
            a_end = int(parts[1])
        else:
            a_start = int(args.ayah)
            a_end = a_start

    run_quran_verse_pipeline(
        surah=args.surah,
        ayah_start=a_start,
        ayah_end=a_end,
        reciter_id=args.reciter,
        upload=args.upload
    )
