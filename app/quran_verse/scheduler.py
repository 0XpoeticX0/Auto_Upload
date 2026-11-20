# -*- coding: utf-8 -*-
"""
Automated Daily Scheduler & Slot Manager for Quran Recitation Videos (< 90s).
Configured for 4 Daily Slots:
- 2 Slots Curated User Audio & High-Impact Bengali Script
- 2 Slots Random / AI Quran Video
Automatically alternates between Curated and Random modes.
Both modes strictly enforce:
- 100% Halal live-motion cinematic video triplet rotation (GEMINI.md)
- Authentic recitations & broadcast audio mastering
- Pure Bengali typography & curiosity hooks
- Facebook Stars call-to-action & auto-pinned first comment
- Viral hashtags & metadata
"""

import sys
import os
import time
import random
import argparse
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure environment variables are loaded immediately
load_dotenv()

from app.logger import logger
from app.quran_verse.generator import run_quran_verse_pipeline
from app.quran_verse.curated_pipeline import run_curated_quran_pipeline, get_curated_state, save_curated_state
from app.quran_verse.quran_data import RECITERS_CONFIG

BST = timezone(timedelta(hours=6))

DAILY_QURAN_TIME = "4 Times Daily (03:00 AM, 06:00 AM, 09:00 AM, 12:00 PM BST)"

def execute_daily_quran_run(upload: bool = True, reciter_id: str = None, mode: str = "auto") -> dict:
    """
    Executes the scheduled Quran video pipeline:
    - In 'curated' mode: Runs the curated audio & verified Bengali script pipeline.
    - In 'random' mode: Runs the intelligent random passage & AI discovery pipeline.
    - In 'auto' mode: Seamlessly alternates 2 Curated and 2 Random runs per day.
    """
    now_bst = datetime.now(BST)
    date_str = now_bst.strftime("%Y-%m-%d %H:%M:%S BST")
    
    logger.info(f"=== LAUNCHING SCHEDULED QURAN RECITATION PIPELINE ===")
    logger.info(f"Time: {date_str} | Schedule: {DAILY_QURAN_TIME}")
    
    state = get_curated_state()
    active_mode = mode
    if active_mode == "auto":
        active_mode = state.get("next_mode", "curated")
        
    logger.info(f"🎯 Execution Target Mode: '{active_mode.upper()}' (2 Curated / 2 Random Daily Mix)")

    if active_mode == "curated":
        logger.info("Executing Curated Quran Pipeline (User Audio + Verified Bengali Script)...")
        result = run_curated_quran_pipeline(upload=upload)
        # run_curated_quran_pipeline automatically advances index, queues 'random' mode, and syncs to Supabase.
    else:
        logger.info("Executing Random Quran Pipeline (AI Discovery & Pure Nature Triplet)...")
        result = run_quran_verse_pipeline(
            reciter_id=reciter_id,
            upload=upload
        )
        # Advance mode to curated for next schedule slot using fresh cloud state
        fresh_state = get_curated_state()
        fresh_state["next_mode"] = "curated"
        save_curated_state(fresh_state)

    final_state = get_curated_state()
    logger.info(f"🎉 Scheduled Quran video execution completed! Next Mode queued: '{final_state.get('next_mode', 'curated').upper()}' | Next Curated Index: {final_state.get('next_curated_index', 0)}")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Quran Video Automated Scheduler")
    parser.add_argument("--reciter", choices=["alafasy", "dossari"], default=None, help="Force specific reciter")
    parser.add_argument("--mode", choices=["auto", "curated", "random"], default="auto", help="Scheduling mode: auto (alternates 2+2), curated, or random")
    parser.add_argument("--upload", action="store_true", default=True, help="Auto upload to social media")
    parser.add_argument("--no-upload", dest="upload", action="store_false", help="Render video only without uploading")

    args = parser.parse_args()
    execute_daily_quran_run(
        upload=args.upload,
        reciter_id=args.reciter,
        mode=args.mode
    )
