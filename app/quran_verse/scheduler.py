# -*- coding: utf-8 -*-
"""
Automated Scheduler & Slot Manager for Quran Recitation Videos (< 90s).
Optimized for peak Islamic engagement hours in Bangladesh Time (BST / UTC+6):
1. 🌅 Slot 1: Fajr & Dawn Prime (05:30 AM BST) - Morning Barakah, Hope, Protection
2. 🌇 Slot 2: Asr & Maghrib Prime (05:45 PM BST) - Solace, Forgiveness, Rizq & Tawakkul
3. 🌙 Slot 3: Night & Tahajjud Peace (10:15 PM BST) - Night Tranquility, Al-Mulk, Protection
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

QURAN_SLOTS = {
    "dawn": {
        "id": "dawn",
        "name": "🌅 Slot 1: Fajr & Dawn Prime (05:30 AM BST)",
        "theme": "Morning Barakah, Solace, Ayat al-Kursi, Divine Ease & Protection",
        "preferred_surahs": [94, 93, 1, 2, 112, 113, 114],
        "default_reciter": "alafasy"
    },
    "evening": {
        "id": "evening",
        "name": "🌇 Slot 2: Asr & Maghrib Prime (05:45 PM BST)",
        "theme": "Evening Reflection, Relief from Grief, Yunus Dua, Names of Allah, Rizq",
        "preferred_surahs": [59, 21, 65, 55, 3, 28],
        "default_reciter": "dossari"
    },
    "night": {
        "id": "night",
        "name": "🌙 Slot 3: Night & Tahajjud Peace (10:15 PM BST)",
        "theme": "Night Peace, Surah Al-Mulk, Amanar Rasul, The Peaceful Soul",
        "preferred_surahs": [67, 2, 89, 25, 39],
        "default_reciter": "alafasy"
    }
}

def detect_current_slot() -> str:
    """Determines the active Quran video slot based on current BST time."""
    now_bst = datetime.now(BST)
    hour = now_bst.hour

    if 4 <= hour < 12:
        return "dawn"
    elif 12 <= hour < 19:
        return "evening"
    else:
        return "night"

def execute_scheduled_quran_run(slot_id: str = "auto", upload: bool = True, reciter_id: str = None) -> dict:
    """
    Executes a scheduled Quran recitation video run with 3-Stage Gemini Clearance.
    """
    if not slot_id or slot_id == "auto":
        slot_id = detect_current_slot()

    slot_info = QURAN_SLOTS.get(slot_id, QURAN_SLOTS["dawn"])
    logger.info(f"=== LAUNCHING SCHEDULED QURAN RECITATION RUN ===")
    logger.info(f"Active Slot: {slot_info['name']}")
    logger.info(f"Slot Theme: {slot_info['theme']}")

    # Select Reciter (alternate or use slot preference if not specified)
    if not reciter_id:
        reciter_id = slot_info.get("default_reciter", "alafasy")

    logger.info(f"Chosen Reciter: {reciter_id} ({RECITERS_CONFIG[reciter_id]['name_bn']})")

    # Run complete pipeline (Passage Selection -> 3-Stage Clearance -> Audio Download -> Render -> Upload)
    result = run_quran_verse_pipeline(
        reciter_id=reciter_id,
        upload=upload
    )

    logger.info(f"Scheduled Quran run for {slot_info['name']} completed successfully!")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quran Video Automated Scheduler")
    parser.add_argument("--slot", choices=["auto", "dawn", "evening", "night"], default="auto", help="Target Quran slot")
    parser.add_argument("--reciter", choices=["alafasy", "dossari"], default=None, help="Reciter choice")
    parser.add_argument("--upload", action="store_true", default=True, help="Auto upload to YouTube, Facebook, Instagram")
    parser.add_argument("--no-upload", dest="upload", action="store_false", help="Render video only without uploading")

    args = parser.parse_args()
    execute_scheduled_quran_run(
        slot_id=args.slot,
        upload=args.upload,
        reciter_id=args.reciter
    )
