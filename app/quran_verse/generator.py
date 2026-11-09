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
import json
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

from app.logger import logger
from app.history import (
    get_recent_video_titles,
    _supabase_insert,
    fetch_recent_quran_pipeline_history,
    record_quran_history,
    get_used_ayahs_map
)
from app.quran_verse.quran_data import (
    RECITERS_CONFIG,
    SURAH_NAMES_BN,
    SURAH_NAMES_EN,
    fetch_verse_data,
    select_meaningful_passage_ai,
    determine_best_reciter_for_passage
)
from app.quran_verse.verifier import verify_quran_passage_3x
from app.quran_verse.audio_manager import prepare_recitation_audio
from app.quran_verse.renderer import render_quran_verse_video
from app.quran_verse.metadata import generate_quran_metadata

SELECTION_STATE_FILE = os.path.abspath("data/quran_selection_state.json")

def get_next_quran_selection_mode() -> str:
    """Alternates between 'saved' (curated viral masterpieces) and 'random' (AI discovery)."""
    last_mode = "random"
    if os.path.exists(SELECTION_STATE_FILE):
        try:
            with open(SELECTION_STATE_FILE, "r", encoding="utf-8") as f:
                last_mode = json.load(f).get("last_mode", "random")
        except Exception:
            pass
    return "saved" if last_mode == "random" else "random"

def save_quran_selection_mode(mode: str):
    try:
        os.makedirs(os.path.dirname(SELECTION_STATE_FILE), exist_ok=True)
        with open(SELECTION_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_mode": mode, "timestamp": int(time.time())}, f, indent=2)
    except Exception as e:
        logger.debug(f"Failed to save selection mode: {e}")

def generate_quran_verse_video(
    surah: int = None,
    ayah_start: int = None,
    ayah_end: int = None,
    reciter_id: str = None,
    video_slot: int = None
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

    # 1. Check if caller forced a specific reciter, otherwise let AI match emotion-to-voice
    forced_reciter_id = reciter_id if reciter_id in RECITERS_CONFIG else None
    if forced_reciter_id:
        logger.info(f"User forced reciter: {RECITERS_CONFIG[forced_reciter_id]['name_en']}")

    # 2. Select & Clear Quran Verse Passage via 3-Stage Gemini Clearance Gate
    # Dedicated chronological history of published Quran videos from Supabase + local cache
    quran_history = fetch_recent_quran_pipeline_history(limit=60)
    used_ayahs_map = get_used_ayahs_map(quran_history, limit=60)
    past_titles = [r.get("title", "") for r in quran_history[:60] if r.get("title")]

    logger.info(f"🚫 [Zero-Duplication Gate] Tracking already used Ayahs across {len(used_ayahs_map)} Surahs in last 60 videos:")
    for s_num, ayahs in sorted(used_ayahs_map.items()):
        bn_s = SURAH_NAMES_BN.get(s_num, "")
        logger.info(f"   - Surah {s_num} ({bn_s}): used Ayahs {sorted(list(ayahs))}")

    target_mode = get_next_quran_selection_mode() if not (surah and ayah_start) else "manual"
    logger.info(f"🔄 [Quran Rotation] Active Selection Mode: '{target_mode.upper()}' (Alternating Saved vs. Random AI)")

    max_selection_retries = 8
    verse_data = None
    dynamic_used_ayahs = {k: set(v) for k, v in used_ayahs_map.items()}
    rejected_passages = []
    last_fail_reason = ""

    for attempt in range(1, max_selection_retries + 1):
        if surah and ayah_start:
            end = ayah_end or ayah_start
            chosen_rec = forced_reciter_id or determine_best_reciter_for_passage(surah, ayah_start, end)
            reciter = RECITERS_CONFIG[chosen_rec]
            v_cand = fetch_verse_data(surah, ayah_start, end)
            v_cand["reciter_id"] = chosen_rec
            v_cand["reciter"] = reciter
            v_cand["theme_headline"] = f"{v_cand['surah_name_bn']} (আয়াত {v_cand['verse_range_str']})"
            v_cand["reflection_bn"] = ""
        else:
            # Alternating rotation: 'saved' selects from curated bank; 'random' discovers via AI
            # If attempt 1 hits an Ayah overlap, toggle mode on attempt 2 to guarantee zero deadlock
            if attempt == 1:
                use_curated = (target_mode == "saved")
            elif attempt == 2:
                use_curated = not (target_mode == "saved")
            else:
                use_curated = (attempt % 2 == 1)

            logger.info(f"🔍 [Passage Selection Attempt {attempt}/{max_selection_retries}] Engine: {'SAVED CURATED BANK' if use_curated else 'DYNAMIC AI RANDOM DISCOVERY'}")
            v_cand = select_meaningful_passage_ai(
                reciter_id=forced_reciter_id,
                recent_history=past_titles,
                used_ayahs_map=dynamic_used_ayahs,
                rejected_passages=rejected_passages,
                last_fail_reason=last_fail_reason,
                use_curated_fallback=use_curated
            )

        # STRICT ZERO-DUPLICATION ENFORCEMENT GATE: AYAH-LEVEL REJECTION
        cand_surah = v_cand.get("surah")
        cand_start = v_cand.get("ayah_start")
        cand_end = v_cand.get("ayah_end") or cand_start
        cand_surah_name_bn = v_cand.get("surah_name_bn", "")
        cand_range_str = str(v_cand.get("verse_range_str", ""))

        if not (surah and ayah_start):
            # Check 1: Ayah-level overlap check (rejection occurs ONLY if specific Ayahs have been used)
            cand_ayahs = set(range(cand_start, cand_end + 1))
            banned_ayahs = dynamic_used_ayahs.get(cand_surah, set())
            overlap = cand_ayahs & banned_ayahs
            if overlap:
                logger.warning(
                    f"🚫 [Zero-Duplication Gate] REJECTED (Attempt {attempt}/{max_selection_retries}): "
                    f"Surah {cand_surah} ({cand_surah_name_bn}) Ayahs {cand_range_str} overlaps with already used Ayahs: {sorted(list(overlap))}!"
                )
                dynamic_used_ayahs.setdefault(cand_surah, set()).update(cand_ayahs)
                rejected_passages.append(f"Surah {cand_surah}:{cand_range_str}")
                continue

            # Check 2: Exact duplicate title check against past 30 Quran titles
            is_title_duplicate = False
            for past_entry in past_titles[:60]:
                if cand_surah_name_bn in past_entry and f"আয়াত {cand_range_str}" in past_entry:
                    logger.warning(
                        f"🚫 [Zero-Duplication Gate] REJECTED (Attempt {attempt}/{max_selection_retries}): "
                        f"{cand_surah_name_bn} (আয়াত {cand_range_str}) already found in past title '{past_entry}'!"
                    )
                    is_title_duplicate = True
                    break
            if is_title_duplicate:
                dynamic_used_ayahs.setdefault(cand_surah, set()).update(cand_ayahs)
                rejected_passages.append(f"Surah {cand_surah}:{cand_range_str}")
                continue

        # Ayah Count Guard: Shorts must never attempt large verse blocks
        cand_count = cand_end - cand_start + 1
        if not (surah and ayah_start) and cand_count > 6:
            logger.warning(
                f"🚫 [Ayah Count Gate] REJECTED (Attempt {attempt}/{max_selection_retries}): "
                f"Surah {cand_surah}:{cand_range_str} has {cand_count} ayahs (maximum 6 allowed for Shorts under 85s)!"
            )
            dynamic_used_ayahs.setdefault(cand_surah, set()).update(cand_ayahs)
            rejected_passages.append(f"Surah {cand_surah}:{cand_range_str} ({cand_count} ayahs - too long)")
            continue

        cleared, clearance_report = verify_quran_passage_3x(v_cand)
        if not cleared:
            logger.warning(f"Passage failed 3-Stage Clearance Gate on attempt {attempt}: {clearance_report}")
            if surah and ayah_start:
                verse_data = v_cand
                break
            if cand_surah and cand_start and cand_end:
                dynamic_used_ayahs.setdefault(cand_surah, set()).update(range(cand_start, cand_end + 1))
                rejected_passages.append(f"Surah {cand_surah}:{cand_range_str}")
                last_fail_reason = str(clearance_report.get("details", {}).get("reason", ""))
            continue

        # HARD DURATION ENFORCEMENT GATE: Recitation MUST be between 20s and 85s (Strictly under 90s)
        try:
            cand_audio = prepare_recitation_audio(v_cand)
            cand_dur = cand_audio.get("total_duration", 0.0)
            if not (surah and ayah_start) and (cand_dur > 85.0 or cand_dur < 20.0):
                logger.warning(
                    f"🚫 [Duration Gate] REJECTED (Attempt {attempt}/{max_selection_retries}): "
                    f"Surah {cand_surah}:{cand_range_str} duration is {cand_dur:.1f}s (must be 20s–85s)!"
                )
                dynamic_used_ayahs.setdefault(cand_surah, set()).update(range(cand_start, cand_end + 1))
                rejected_passages.append(f"Surah {cand_surah}:{cand_range_str} ({cand_dur:.0f}s - out of bounds)")
                last_fail_reason = f"Duration {cand_dur:.1f}s is out of bounds (must be 20s-85s). Select fewer verses (2-5 verses max)."
                continue

            verse_data = v_cand
            verse_data["clearance_report"] = clearance_report
            audio_data = cand_audio
            logger.info(f"✅ Passage cleared all gates on attempt {attempt}: {verse_data['surah_name_bn']} ({verse_data['verse_range_str']}) [{cand_dur:.1f}s]")
            if target_mode in ("saved", "random"):
                save_quran_selection_mode(target_mode)
            break
        except Exception as e:
            logger.warning(f"Audio duration verification error on attempt {attempt}: {e}")
            continue

    if not verse_data:
        raise RuntimeError("Failed to obtain a 100% verified Quran passage after 3-Stage Gemini Clearance checks.")

    # 3. Download & Master Audio (< 90s)
    if "audio_data" not in locals() or audio_data is None:
        audio_data = prepare_recitation_audio(verse_data)
    total_dur = audio_data["total_duration"]

    if total_dur > 90.0:
        raise ValueError(f"STRICT GATE VIOLATION: Quran audio duration {total_dur:.1f}s exceeds strict 90s limit!")

    # 4. Generate Metadata
    metadata = generate_quran_metadata(verse_data, audio_data)

    # 5. Render Video (1080x1920 60FPS) with Centered Bengali Translation Subtitles
    video_path = render_quran_verse_video(verse_data, audio_data, video_slot=video_slot)

    # 6. Extract a clean thumbnail frame at t=3.0s from the rendered video
    thumbnail_path = None
    try:
        import subprocess as _sp
        thumb_filename = os.path.splitext(os.path.basename(video_path))[0] + "_thumb.jpg"
        thumb_out = os.path.join("data", "output", thumb_filename)
        sample_t = min(3.0, audio_data.get("total_duration", 10.0) - 1.0)
        _sp.run([
            "ffmpeg", "-y",
            "-ss", str(sample_t),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            thumb_out
        ], check=True, capture_output=True)
        if os.path.exists(thumb_out):
            thumbnail_path = thumb_out
            logger.info(f"✅ Quran thumbnail extracted at t={sample_t:.1f}s: {thumbnail_path}")
    except Exception as e:
        logger.warning(f"Thumbnail extraction notice: {e}")

    # Mandatory Pass 2: Shariah Visual Compliance Gate (0 Living Beings Audit)
    from app.quality.triple_gemini_verifier import pass_2_halal_vision_and_visual_defects
    logger.info(f"Running Mandatory Pass 2: Shariah Visual Compliance Gate on {video_path}...")
    audit = pass_2_halal_vision_and_visual_defects(video_path)
    if not audit.get("pass", False):
        reason = audit.get("reason", "Contains living beings, human body parts, or Shariah violation")
        logger.critical(f"❌ [SHARIAH COMPLIANCE VIOLATION] Video rejected: {reason}")
        if os.path.exists(video_path):
            os.remove(video_path)
        raise ValueError(f"Shariah Visual Compliance Gate Failed: {reason}")
    logger.info("✅ [Pass 2 PASSED] 100% Halal Live-Motion Footage Confirmed (Strictly 0 living beings, 0 faces, 0 silhouettes).")

    return {
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
        "metadata": metadata,
        "verse_data": verse_data,
        "audio_data": audio_data,
        "shariah_passed": True
    }

def run_quran_verse_pipeline(
    surah: int = None,
    ayah_start: int = None,
    ayah_end: int = None,
    reciter_id: str = None,
    video_slot: int = None,
    upload: bool = False
) -> dict:
    """
    Executes the Quran video pipeline, with optional automated social media upload.
    """
    result = generate_quran_verse_video(surah, ayah_start, ayah_end, reciter_id, video_slot=video_slot)
    video_path = result["video_path"]
    thumbnail_path = result.get("thumbnail_path")
    metadata = result["metadata"]

    if upload:
        if not result.get("shariah_passed", False):
            logger.critical("🛑 ABORTING UPLOAD: Shariah Visual Compliance Gate was not verified!")
            raise RuntimeError("CRITICAL: Cannot upload video because it did not pass the Shariah Visual Compliance Gate!")

        logger.info("Uploading Quran video to platforms...")
        upload_meta = {
            "youtube_title": metadata["title"],
            "description": metadata["description"],
            "pinned_comment": metadata["pinned_comment"],
            "tags": metadata["tags"]
        }

        # YouTube Shorts
        yt_ok = None
        try:
            from app.upload.youtube import upload_to_youtube
            yt_ok = upload_to_youtube(video_path, upload_meta, thumbnail_path=thumbnail_path)
            logger.info(f"YouTube Shorts Upload: {yt_ok}")
        except Exception as e:
            logger.warning(f"YouTube upload notice: {e}")

        # Record to Supabase & Local History Cache IMMEDIATELY (Ground-Truth Persistence)
        surah_num = result['verse_data']['surah']
        a_start = result['verse_data']['ayah_start']
        a_end = result['verse_data']['ayah_end']
        history_title = f"[কুরআন তিলাওয়াত] {metadata['title']}"
        reciter_id = result['verse_data'].get('reciter_id', '')

        try:
            record_quran_history(
                surah=surah_num,
                ayah_start=a_start,
                ayah_end=a_end,
                title=history_title,
                reciter_id=reciter_id
            )
            logger.info(f"✅ Recorded to Quran History: Surah {surah_num}:{a_start}-{a_end} ('{history_title}')")
        except Exception as e:
            logger.error(f"Failed to record Quran history: {e}")

        # Facebook & Instagram Reels
        try:
            from app.upload.facebook import upload_to_facebook
            fb_ok = upload_to_facebook(video_path, upload_meta, video_type="reel", thumbnail_path=thumbnail_path)
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
