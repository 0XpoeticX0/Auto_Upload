# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import re
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Ensure unbuffered output
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"E:\Project\youtube_video\.env")

from google import genai
from PIL import Image

CATALOG_PATH = "data/stock_video_catalog.json"
CACHE_PATH = "data/catalog_audit_cache.json"
REJECTED_PATH = "data/catalog_rejected_clips.json"
TEMP_FRAME_DIR = "data/temp/catalog_audit_frames"
os.makedirs(TEMP_FRAME_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

KEYS = [
    os.getenv('GEMINI_API_KEY'),
    os.getenv('GEMINI_POST_API_KEY'),
    os.getenv('GEMINI_BACKUP_API_KEY'),
    os.getenv('GEMINI_KEY_3'),
    os.getenv('GEMINI_KEY_4'),
    os.getenv('GEMINI_KEY_5'),
]
KEYS = [k for k in KEYS if k and len(k) > 10]
clients = [genai.Client(api_key=k) for k in KEYS]
print(f"Loaded {len(clients)} Gemini API clients for concurrent auditing.", flush=True)

SHARIAH_VISION_PROMPT = """You are an uncompromising Islamic Shariah Visual Auditor enforcing a ZERO LIVING BEINGS policy.
Inspect this video frame with extreme scrutiny.

CHECK FOR ANY OF THE FOLLOWING VIOLATIONS:
1. Any human being (man, woman, child, swimmer, worshipper, pedestrian, crowd, couple, silhouette, shadow).
2. Any human body part (face, eyes, hands, limbs, skin, legs, torso, hair, feet).
3. Any swimwear, bikini, beach crowd, or people in water.
4. Any living animal, bird, insect, fish, underwater sea creature, or reptile.
5. Any statue, sculpture, human figurine, idol, or church/cross/non-Islamic temple.
6. Any artificial graphic watermark or heavy text logo.

CATEGORIES LIST (Choose the single best matching category):
clouds, sky, sunset, sunrise, stars, night_sky, galaxy, space, moon, nebula,
ocean, sea, waves, waterfall, river, lake, water_stream, rain, water_droplets, ripples,
desert, sand_dunes, mountains, rock_formations, canyon, valley, cliff, hills, earth, horizon,
forest, trees, autumn_leaves, bamboo, meadow, grass, foliage, mist, fog, sunlight_beams,
mosque, dome, columns, arch, corridor, sacred_door, architecture, palace_hall, candle_light, lantern.

CRITERIA:
- If ANY living being, silhouette, human body part, swimwear, animal, statue, or church is present:
  "pass": false, "has_violation": true, "reason": "Detailed description of violation"
- If and ONLY IF it is 100% Halal atmospheric nature or sacred architecture:
  "pass": true, "has_violation": false, "category": "<one category from list above>", "reason": "Description of scene"

Respond strictly with JSON:
{
    "pass": true,
    "has_violation": false,
    "category": "ocean",
    "confidence": 0.99,
    "reason": "Gentle ocean waves under blue sky with no living beings"
}"""

# Load existing catalog
if os.path.exists(CATALOG_PATH):
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)
else:
    catalog_data = {
        "total_unique": 0,
        "halal_certified": True,
        "shariah_compliance": "Strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals",
        "clip_metadata": {},
        "catalog_by_50_categories": {}
    }

# Load audit cache
audit_cache = {}
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            audit_cache = json.load(f)
    except Exception:
        audit_cache = {}

# Load rejected clips
rejected_clips = {}
if os.path.exists(REJECTED_PATH):
    try:
        with open(REJECTED_PATH, "r", encoding="utf-8") as f:
            rejected_clips = json.load(f)
    except Exception:
        rejected_clips = {}

BANNED_ID_BLACKLIST = {
    "19501", "9514", "1986", "14138", "2490", "45402", "45022", "45395", "4441", "18308", "42495", "35472"
}

def audit_clip_url(url: str, client_idx: int) -> dict:
    """Extracts frame from URL and audits with Gemini Vision."""
    clip_id = url.split("/")[4] if "videos/" in url else str(abs(hash(url)))[:8]
    if clip_id in BANNED_ID_BLACKLIST:
        return {"pass": False, "has_violation": True, "reason": f"Banned clip ID {clip_id}", "id": clip_id, "url": url}

    if url in audit_cache:
        cached = audit_cache[url]
        cached["id"] = clip_id
        cached["url"] = url
        return cached

    # Extract frame
    frame_path = os.path.join(TEMP_FRAME_DIR, f"frame_{clip_id}.jpg")
    if not os.path.exists(frame_path) or os.path.getsize(frame_path) < 1000:
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:02.50", "-i", url,
            "-vframes", "1", "-q:v", "2", frame_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not os.path.exists(frame_path) or os.path.getsize(frame_path) < 1000:
            return {"pass": False, "has_violation": False, "reason": "Failed to extract frame", "id": clip_id, "url": url}

    # Vision audit
    client = clients[client_idx % len(clients)]
    try:
        img = Image.open(frame_path)
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[SHARIAH_VISION_PROMPT, img]
        )
        raw = resp.text.strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            data["id"] = clip_id
            data["url"] = url
            audit_cache[url] = data
            return data
    except Exception as e:
        return {"pass": False, "has_violation": False, "reason": f"API error: {e}", "id": clip_id, "url": url}

    return {"pass": False, "has_violation": False, "reason": "Invalid JSON response", "id": clip_id, "url": url}

def save_catalog_state(verified_by_cat: dict, metadata_map: dict):
    """Saves updated catalog to disk."""
    total = sum(len(v) for v in verified_by_cat.values())
    catalog_data["total_unique"] = total
    catalog_data["clip_metadata"] = metadata_map
    catalog_data["catalog_by_50_categories"] = verified_by_cat
    
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2, ensure_ascii=False)
        
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_cache, f, indent=2, ensure_ascii=False)
        
    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        json.dump(rejected_clips, f, indent=2, ensure_ascii=False)

def run_phase_1_existing_audit(by_cat: dict, meta_map: dict):
    """Audits every clip currently in the catalog and purges any Shariah violations."""
    print("\n--- PHASE 1: Auditing Existing Catalog Clips ---", flush=True)
    all_existing_urls = list(meta_map.keys())
    for cat_urls in by_cat.values():
        for u in cat_urls:
            if u not in all_existing_urls:
                all_existing_urls.append(u)

    print(f"Total existing clips to audit: {len(all_existing_urls)}", flush=True)
    purged_count = 0
    clean_count = 0

    for idx, url in enumerate(all_existing_urls, 1):
        res = audit_clip_url(url, idx)
        clip_id = res.get("id")
        if not res.get("pass", False) or res.get("has_violation", False):
            purged_count += 1
            reason = res.get("reason", "Violation detected")
            print(f"[{idx}/{len(all_existing_urls)}] ❌ PURGED Clip {clip_id}: {reason}", flush=True)
            rejected_clips[url] = {"id": clip_id, "reason": reason}
            # Remove from metadata
            if url in meta_map:
                del meta_map[url]
            # Remove from categories
            for cat, urls in by_cat.items():
                if url in urls:
                    urls.remove(url)
        else:
            clean_count += 1
            if idx % 25 == 0 or idx == len(all_existing_urls):
                print(f"[{idx}/{len(all_existing_urls)}] Clean Halal clips verified: {clean_count} (Purged so far: {purged_count})", flush=True)

    save_catalog_state(by_cat, meta_map)
    print(f"Phase 1 Complete: {clean_count} verified Halal clips retained, {purged_count} non-halal clips permanently purged.", flush=True)

if __name__ == "__main__":
    by_cat = catalog_data.get("catalog_by_50_categories", {})
    meta_map = catalog_data.get("clip_metadata", {})
    run_phase_1_existing_audit(by_cat, meta_map)
