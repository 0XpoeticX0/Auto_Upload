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
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    catalog_data = json.load(f)

meta_map = catalog_data.get("clip_metadata", {})
by_cat = catalog_data.get("catalog_by_50_categories", {})

# Load audit cache and rejected clips
audit_cache = {}
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            audit_cache = json.load(f)
    except Exception:
        audit_cache = {}

rejected_clips = {}
if os.path.exists(REJECTED_PATH):
    try:
        with open(REJECTED_PATH, "r", encoding="utf-8") as f:
            rejected_clips = json.load(f)
    except Exception:
        rejected_clips = {}

BANNED_ID_BLACKLIST = set(rejected_clips.keys())
for b in ["19501", "9514", "1986", "14138", "2490", "45402", "45022", "45395", "4441", "18308", "42495", "35472"]:
    BANNED_ID_BLACKLIST.add(b)

def is_valid_video_url(url: str) -> bool:
    """Verifies that the video URL exists on CDN and is a valid MP4 file (> 1.2MB)."""
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                cl = int(resp.headers.get('Content-Length', 0))
                return cl > 1200000
    except Exception:
        pass
    return False

def audit_candidate(url: str, client_idx: int) -> dict:
    """Extracts frame and runs Gemini Vision check."""
    clip_id = url.split("/")[4] if "videos/" in url else str(abs(hash(url)))[:8]
    if clip_id in BANNED_ID_BLACKLIST:
        return {"pass": False, "has_violation": True, "reason": f"Banned clip ID {clip_id}", "id": clip_id, "url": url}

    if url in audit_cache:
        cached = audit_cache[url]
        cached["id"] = clip_id
        cached["url"] = url
        return cached

    # Quick HEAD check
    if not is_valid_video_url(url):
        return {"pass": False, "has_violation": False, "reason": "URL unavailable or file too small", "id": clip_id, "url": url}

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

def save_current_catalog(target_count: int = 1000):
    total = sum(len(v) for v in by_cat.values())
    catalog_data["total_unique"] = total
    catalog_data["clip_metadata"] = meta_map
    catalog_data["catalog_by_50_categories"] = by_cat
    
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2, ensure_ascii=False)
        
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_cache, f, indent=2, ensure_ascii=False)
        
    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        json.dump(rejected_clips, f, indent=2, ensure_ascii=False)

def main():
    target_total = 1000
    current_total = sum(len(v) for v in by_cat.values())
    print(f"Starting Catalog Expansion: currently {current_total} verified clips. Target: {target_total} clips.", flush=True)

    # 1. Collect candidate URLs pool
    candidate_urls = []
    
    # Add from scraped candidate pool
    if os.path.exists("data/scraped_candidates_pool.json"):
        with open("data/scraped_candidates_pool.json", "r", encoding="utf-8") as f:
            scraped = json.load(f)
        for cat_name, ids in scraped.items():
            for cid in ids:
                u = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4"
                if u not in meta_map and u not in candidate_urls and cid not in BANNED_ID_BLACKLIST:
                    candidate_urls.append((u, cat_name))

    # Add from diverse CDN numeric ranges
    cdn_ranges = [
        (4000, 4400, "nature"),
        (1000, 1300, "landscape"),
        (11000, 11400, "space"),
        (20000, 20400, "night_sky"),
        (31000, 31500, "mountains"),
        (41000, 41600, "forest"),
        (44000, 44600, "ocean"),
        (51000, 51600, "nature_hd"),
        (14000, 14400, "water"),
        (17000, 17400, "architecture"),
    ]
    for start, end, default_tag in cdn_ranges:
        for cid in range(start, end):
            u = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4"
            if u not in meta_map and u not in [c[0] for c in candidate_urls] and str(cid) not in BANNED_ID_BLACKLIST:
                candidate_urls.append((u, default_tag))

    print(f"Total candidate clips in audit queue: {len(candidate_urls)}", flush=True)

    # 2. Process candidate clips with ThreadPoolExecutor
    added_in_session = 0
    client_counter = 0

    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        future_to_url = {}
        for url, suggested_cat in candidate_urls:
            if current_total + added_in_session >= target_total:
                break
            client_counter += 1
            future = executor.submit(audit_candidate, url, client_counter)
            future_to_url[future] = (url, suggested_cat)

        for future in as_completed(future_to_url):
            url, suggested_cat = future_to_url[future]
            try:
                res = future.result()
            except Exception as e:
                continue

            clip_id = res.get("id")
            is_pass = res.get("pass", False)
            has_violation = res.get("has_violation", False)
            reason = res.get("reason", "")
            cat = res.get("category", suggested_cat).lower().replace(" ", "_")

            if not is_pass or has_violation:
                rejected_clips[url] = {"id": clip_id, "reason": reason}
                BANNED_ID_BLACKLIST.add(clip_id)
                print(f"❌ [REJECTED {clip_id}]: {reason}", flush=True)
            else:
                # Halal clip accepted!
                if cat not in by_cat:
                    # Map to nearest standard category
                    cat = "nature" if "nature" in cat else "clouds"
                    if cat not in by_cat:
                        by_cat[cat] = []

                if url not in by_cat[cat]:
                    by_cat[cat].append(url)
                    meta_map[url] = {
                        "category": cat,
                        "title": reason[:60],
                        "duration": 15.0,
                        "id": clip_id,
                        "url": url
                    }
                    added_in_session += 1
                    total_now = sum(len(v) for v in by_cat.values())
                    print(f"[{total_now}/{target_total}] ✅ HALAL CERTIFIED Clip {clip_id} ({cat}): {reason}", flush=True)

                    if added_in_session % 10 == 0:
                        save_current_catalog(target_total)
                        print(f"💾 Checkpoint saved: {total_now} total verified clips in catalog.", flush=True)

                    if total_now >= target_total:
                        print("🎉 TARGET REACHED: 1,000 Verified 100% Halal Video Links!", flush=True)
                        save_current_catalog(target_total)
                        break

    save_current_catalog(target_total)
    final_total = sum(len(v) for v in by_cat.values())
    print(f"\n================ AUDIT & EXPANSION FINISHED ================", flush=True)
    print(f"Final Total Verified Halal Clips in Catalog: {final_total}", flush=True)
    print(f"Total Non-Halal Clips Blacklisted: {len(rejected_clips)}", flush=True)

if __name__ == "__main__":
    main()
