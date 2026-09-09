# -*- coding: utf-8 -*-
"""
Automated Daily Scheduler & Slot Manager for Quran Recitation Videos (< 90s).
Configured for: Exactly 1 Daily High-Impact Video at 06:00 AM BST (Dawn / Morning Prime).
Automatically alternates daily between:
- Sheikh Mishary Rashid Alafasy (শায়খ মিশারি রশিদ আল-আফাসি)
- Sheikh Yasser Al-Dossari (শায়খ ইয়াসির আদ-দাওসারি)
"""

import sys
import os
import time
import random
import argparse
from datetime import datetime, timezone, timedelta
from app.logger import logger
from app.quran_verse.generator import run_quran_verse_pipeline
from app.quran_verse.quran_data import RECITERS_CONFIG

BST = timezone(timedelta(hours=6))

DAILY_QURAN_TIME = "06:00 AM BST"

def get_daily_alternating_reciter() -> str:
    """
    Alternates daily between Alafasy and Dossari based on the calendar day.
    Even days: alafasy
    Odd days: dossari
    """
    day_num = datetime.now(BST).toordinal()
    return "alafasy" if day_num % 2 == 0 else "dossari"

def execute_daily_quran_run(upload: bool = True, reciter_id: str = None) -> dict:
    """
    Executes the Daily 1 Quran Recitation video pipeline:
    1. Alternates reciter (Alafasy / Dossari)
    2. Selects meaningful self-contained Quranic passage
    3. 3-Stage Gemini Clearance Gate
    4. Downloads authentic audio & studio vocal mastering
    5. Renders 1080x1920 60FPS video with centered subtitles
    6. Automatically publishes to YouTube Shorts, Facebook & Instagram
    """
    now_bst = datetime.now(BST)
    date_str = now_bst.strftime("%Y-%m-%d")
    
    if not reciter_id:
        reciter_id = get_daily_alternating_reciter()

    reciter = RECITERS_CONFIG[reciter_id]
    logger.info(f"=== LAUNCHING DAILY 1 QURAN RECITATION VIDEO PIPELINE ===")
    logger.info(f"Date: {date_str} | Target Time: {DAILY_QURAN_TIME}")
    logger.info(f"Daily Reciter: {reciter['name_bn']} ({reciter['name_en']})")

    result = run_quran_verse_pipeline(
        reciter_id=reciter_id,
        upload=upload
    )

    logger.info("🎉 Daily 1 Quran video execution completed successfully!")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily 1 Quran Video Automated Scheduler")
    parser.add_argument("--reciter", choices=["alafasy", "dossari"], default=None, help="Force specific reciter")
    parser.add_argument("--upload", action="store_true", default=True, help="Auto upload to social media")
    parser.add_argument("--no-upload", dest="upload", action="store_false", help="Render video only without uploading")

    args = parser.parse_args()
    execute_daily_quran_run(
        upload=args.upload,
        reciter_id=args.reciter
    )
