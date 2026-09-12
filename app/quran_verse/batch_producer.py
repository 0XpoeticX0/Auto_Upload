# -*- coding: utf-8 -*-
"""
Batch Producer for 10 Guaranteed Zero-Duplicate Quran Recitation Videos.
Each video uses:
- A completely distinct Quranic passage & recitation
- An exclusive video bucket (video_01 through video_10) with 0 overlapping footage
- An exclusive sacred Quran anchor opening scene
- Upgraded large typography (Bengali 74pt, Arabic 86pt, TopBadge 48pt)
- 3-Stage Gemini Clearance Gate verification
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.logger import logger
from app.quran_verse.generator import generate_quran_verse_video
from app.quran_verse.quran_data import fetch_verse_data, RECITERS_CONFIG

TEN_UNIQUE_PASSAGES = [
    {
        "slot": 1,
        "surah": 1,
        "ayah_start": 1,
        "ayah_end": 7,
        "reciter_id": "alafasy",
        "theme": "সূরা আল-ফাতিহা — পূর্ণাঙ্গ তিলাওয়াত ও অনুবাদ"
    },
    {
        "slot": 2,
        "surah": 94,
        "ayah_start": 1,
        "ayah_end": 8,
        "reciter_id": "alafasy",
        "theme": "সূরা আশ-শারহ — কষ্টের পরেই স্বস্তির মহাপ্রতিশ্রুতি"
    },
    {
        "slot": 3,
        "surah": 93,
        "ayah_start": 1,
        "ayah_end": 11,
        "reciter_id": "dossari",
        "theme": "সূরা আদ-দুহা — হতাশা দূরীকরণ ও আল্লাহর অনুগ্রহ"
    },
    {
        "slot": 4,
        "surah": 65,
        "ayah_start": 2,
        "ayah_end": 3,
        "reciter_id": "alafasy",
        "theme": "সূরা আত-ত্বালাক্ব — অভাবনীয় রিজিক ও তাওয়াক্কুল"
    },
    {
        "slot": 5,
        "surah": 3,
        "ayah_start": 173,
        "ayah_end": 174,
        "reciter_id": "dossari",
        "theme": "সূরা আলে ইমরান — হাসবুনাল্লাহু ওয়া নি'মাল ওয়াকিল"
    },
    {
        "slot": 6,
        "surah": 21,
        "ayah_start": 87,
        "ayah_end": 88,
        "reciter_id": "alafasy",
        "theme": "সূরা আল-আম্বিয়া — ইউনুস (আ.)-এর দোয়া ও সংকট মুক্তি"
    },
    {
        "slot": 7,
        "surah": 2,
        "ayah_start": 255,
        "ayah_end": 255,
        "reciter_id": "alafasy",
        "theme": "সূরা আল-বাক্বারাহ — আয়াতুল কুরসী"
    },
    {
        "slot": 8,
        "surah": 59,
        "ayah_start": 22,
        "ayah_end": 24,
        "reciter_id": "dossari",
        "theme": "সূরা আল-হাশর — আল্লাহর গুণবাচক শ্রেষ্ঠ নামসমূহ (ইসমে আজম)"
    },
    {
        "slot": 9,
        "surah": 2,
        "ayah_start": 285,
        "ayah_end": 286,
        "reciter_id": "alafasy",
        "theme": "সূরা আল-বাক্বারাহ — আমানার রাসূলু (সুরক্ষা ও ক্ষমার দোয়া)"
    },
    {
        "slot": 10,
        "surah": 89,
        "ayah_start": 27,
        "ayah_end": 30,
        "reciter_id": "dossari",
        "theme": "সূরা আল-ফজর — প্রশান্ত আত্মার জন্য জান্নাতের সুসংবাদ"
    }
]

def render_single_slot(slot_idx: int) -> dict:
    """Renders a single Quran video for a specific slot (1-10) with zero overlap."""
    if slot_idx < 1 or slot_idx > len(TEN_UNIQUE_PASSAGES):
        raise ValueError(f"Slot must be between 1 and {len(TEN_UNIQUE_PASSAGES)}")
    
    cfg = TEN_UNIQUE_PASSAGES[slot_idx - 1]
    logger.info(f"🚀 [Batch Producer] Rendering Slot {cfg['slot']}/10: {cfg['theme']} (Reciter: {cfg['reciter_id']})")
    
    res = generate_quran_verse_video(
        surah=cfg["surah"],
        ayah_start=cfg["ayah_start"],
        ayah_end=cfg["ayah_end"],
        reciter_id=cfg["reciter_id"],
        video_slot=cfg["slot"]
    )
    res["slot"] = cfg["slot"]
    res["theme"] = cfg["theme"]
    return res

def produce_all_10_videos() -> list:
    """Produces all 10 videos end-to-end with 0 visual duplicate footage."""
    results = []
    output_summary = []
    total = len(TEN_UNIQUE_PASSAGES)

    print(f"\n=======================================================")
    print(f"🎬 STARTING BATCH PRODUCTION OF {total} UNIQUE QURAN VIDEOS")
    print(f"=======================================================\n")

    for idx, cfg in enumerate(TEN_UNIQUE_PASSAGES, 1):
        slot = cfg["slot"]
        logger.info(f"\n▶ [{idx}/{total}] Processing Slot {slot}: {cfg['theme']}")
        t0 = time.time()
        
        try:
            res = render_single_slot(slot)
            elapsed = time.time() - t0
            v_path = res["video_path"]
            logger.info(f"✅ Finished Slot {slot} in {elapsed:.1f}s: {v_path}")
            results.append(res)
            output_summary.append({
                "slot": slot,
                "surah": cfg["surah"],
                "range": f"{cfg['ayah_start']}-{cfg['ayah_end']}",
                "theme": cfg["theme"],
                "reciter": cfg["reciter_id"],
                "video_path": v_path,
                "elapsed_sec": round(elapsed, 1),
                "status": "SUCCESS"
            })
        except Exception as e:
            logger.error(f"❌ Failed to render Slot {slot}: {e}")
            output_summary.append({
                "slot": slot,
                "theme": cfg["theme"],
                "error": str(e),
                "status": "FAILED"
            })

    summary_file = os.path.join("data", "output", "batch_10_quran_videos_manifest.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(output_summary, f, ensure_ascii=False, indent=2)

    logger.info(f"\n🎉 [Batch Producer Completed] Summary written to: {summary_file}")
    return output_summary

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target_slot = int(sys.argv[1])
        res = render_single_slot(target_slot)
        print(f"SUCCESS: Slot {target_slot} rendered at {res['video_path']}")
    else:
        produce_all_10_videos()
