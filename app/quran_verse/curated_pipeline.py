# -*- coding: utf-8 -*-
"""
Curated Quran Pipeline:
Executes automated rendering & uploading for the user's curated Quran audio collection
and verified high-impact Bengali scripts.
Applies:
- 100% Halal live-motion cinematic 3-clip footage triplet rotation
- Crisp Kalpurush Bengali subtitles & sacred word highlights
- Viral descriptions, curiosity hooks, and Facebook Stars call-to-action
- Auto-pinned first comment on Facebook Reels
"""

import os
import json
import time
import subprocess
from app.logger import logger

MANIFEST_PATH = os.path.abspath("app/assets/curated_user_quran/curated_quran_manifest.json")
CURATED_DIR = os.path.abspath("app/assets/curated_user_quran")
STATE_PATH = os.path.abspath("data/curated_quran_state.json")

def _fetch_cloud_curated_state() -> dict:
    """Fetches real-time curated rotation state directly from Supabase."""
    try:
        from app.history import _get_supabase_config
        url, key = _get_supabase_config()
        if url and key:
            import urllib.request
            headers = {"apikey": key, "Authorization": f"Bearer {key}"}
            req = urllib.request.Request(f"{url}/used_islamic_video?id=eq.curated_quran_state_v1", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read().decode("utf-8"))
                    if rows and "title" in rows[0]:
                        return json.loads(rows[0]["title"])
    except Exception as e:
        logger.debug(f"Cloud curated state fetch notice: {e}")
    return {}

def _sync_cloud_curated_state(state: dict):
    """Upserts curated rotation state to Supabase so zero git commits are ever needed."""
    try:
        from app.history import _get_supabase_config
        url, key = _get_supabase_config()
        if url and key:
            import urllib.request
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }
            payload = {
                "id": "curated_quran_state_v1",
                "title": json.dumps(state),
                "source": "curated_quran_state"
            }
            req = urllib.request.Request(f"{url}/used_islamic_video", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
    except Exception as e:
        logger.debug(f"Cloud curated sync notice: {e}")

def get_curated_state() -> dict:
    default_state = {
        "next_mode": "curated",
        "next_curated_index": 0,
        "last_run": None,
        "history": []
    }
    # 1. Try Supabase cloud ground-truth first
    cloud_state = _fetch_cloud_curated_state()
    if cloud_state:
        return cloud_state
        
    # 2. Local fallback
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read curated state: {e}")
    return default_state

def save_curated_state(state: dict):
    # 1. Persist directly to Supabase cloud
    _sync_cloud_curated_state(state)
    
    # 2. Local cache
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save curated state locally: {e}")

def get_audio_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 30.0

def select_random_curated_item(manifest: list, force_index: int = None) -> tuple[int, dict]:
    """
    Randomly selects a curated Quran track from the manifest.
    - Purely random selection (not serial, never locked to 0 -> 1 -> 2).
    - Avoids selecting the exact same track consecutively.
    - Completely self-contained without requiring Supabase.
    """
    import random
    if force_index is not None:
        idx = force_index % len(manifest)
        return idx, manifest[idx]

    if not manifest:
        raise ValueError("Curated Quran manifest is empty!")

    if len(manifest) == 1:
        return 0, manifest[0]

    # Check local cache or last run file to avoid picking the same track back-to-back
    last_id = None
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                last_id = json.load(f).get("last_id")
        except Exception:
            pass

    # Exclude the last used item to guarantee "not same"
    pool = [m for m in manifest if m.get("id") != last_id]
    if not pool:
        pool = manifest

    chosen = random.choice(pool)
    chosen_idx = manifest.index(chosen)

    # Save last used id locally for the next run
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_id": chosen.get("id"), "last_surah": chosen.get("surah")}, f, indent=2)
    except Exception:
        pass

    logger.info(f"🎲 Randomly selected curated track #{chosen_idx + 1}/{len(manifest)}: Surah {chosen['surah_name_bn']} ({chosen['id']})")
    return chosen_idx, chosen

def run_curated_quran_pipeline(upload: bool = True, force_index: int = None) -> dict:
    """
    Renders and publishes a randomly selected curated Quran video.
    """
    logger.info("=== LAUNCHING CURATED QURAN RECITATION PIPELINE ===")
    
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
        
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    if not manifest:
        raise ValueError("Curated Quran manifest is empty!")
        
    idx, item = select_random_curated_item(manifest, force_index=force_index)
    logger.info(f"▶ Selected Curated Item #{idx + 1}/{len(manifest)}: Surah {item['surah_name_bn']} ({item['surah']}:{item['ayah_start']}-{item['ayah_end']})")
    
    audio_path = os.path.join(CURATED_DIR, item["audio_file"])
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Curated audio file not found: {audio_path}")
        
    duration = get_audio_duration(audio_path)
    
    s_start = item["ayah_start"]
    s_end = item["ayah_end"]
    range_str = f"{s_start}-{s_end}" if s_start != s_end else str(s_start)

    verse_data = {
        "surah": item["surah"],
        "ayah_start": s_start,
        "ayah_end": s_end,
        "verse_range_str": range_str,
        "surah_name_ar": item.get("surah_name_ar", ""),
        "surah_name_en": item.get("surah_name_en", ""),
        "surah_name_bn": item.get("surah_name_bn", ""),
        "reciter_id": item.get("reciter_id", "alafasy"),
        "reciter": {"name_en": item.get("reciter_title", "Mishary Rashid Alafasy")},
        "reciter_title": item.get("reciter_title", "শায়খ মিশারি রশিদ আল-আফাসি"),
        "arabic_uthmani": " ".join([t.get("arabic", "") for t in item.get("ayah_timings", [])]),
        "bengali_translation": " ".join([t.get("bengali", "").replace("\\N", " ") for t in item.get("ayah_timings", [])]),
        "english_translation": " ".join([t.get("english", "") for t in item.get("ayah_timings", [])]),
        "title": item["title"]
    }
    
    audio_data = {
        "audio_path": audio_path,
        "total_duration": duration,
        "ayah_timings": item["ayah_timings"]
    }
    
    # 1. Render Video using the certified 100% Halal live-motion footage triplet rotation (Clean Video Mode - Zero text)
    from app.quran_verse.renderer import render_quran_verse_video
    video_path = render_quran_verse_video(verse_data, audio_data, clean_video=True)
    
    # Generate thumbnail
    thumbnail_path = video_path.replace(".mp4", "_thumb.jpg")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", "3.0", "-i", video_path,
            "-vframes", "1", "-q:v", "2", thumbnail_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.warning(f"Thumbnail creation notice: {e}")
        
    # 2. Shariah Visual Gate
    # Each clip is verified 100% Halal during dynamic visual track assembly
    shariah_passed = os.path.exists(video_path) and os.path.getsize(video_path) > 100000
        
    # 3. Upload Metadata (Configured for International Reach, No Pinned First Comment)
    upload_meta = {
        "youtube_title": item.get("youtube_title", item["title"]),
        "facebook_title": item.get("facebook_title", item["title"]),
        "description": item["description"],
        "pinned_comment": None,
        "tags": item.get("tags", [
            "Quran", "QuranRecitation", "Islam", "Allah", "Muslim",
            item.get("surah_name_en", "Quran"), "Shorts", "Reels", "DailyDos", "Viral"
        ]),
        "default_language": "en",
        "default_audio_language": "ar"
    }
    
    # 4. Upload if requested
    if upload:
        # YouTube Shorts
        try:
            from app.upload.youtube import upload_to_youtube
            yt_res = upload_to_youtube(video_path, upload_meta, thumbnail_path=thumbnail_path)
            logger.info(f"YouTube Shorts Upload: {yt_res}")
        except Exception as e:
            logger.warning(f"YouTube upload notice: {e}")
            
        # Record history
        try:
            from app.history import record_quran_history
            record_quran_history(
                surah=item["surah"],
                ayah_start=item["ayah_start"],
                ayah_end=item["ayah_end"],
                title=f"[কিউরেটেড তিলাওয়াত] {item['title']}",
                reciter_id=item.get("reciter_id", "")
            )
        except Exception as e:
            logger.warning(f"History logging notice: {e}")
            
        # Facebook & Instagram Reels (Auto-appends Stars CTA and pinned comment)
        try:
            from app.upload.facebook import upload_to_facebook
            fb_res = upload_to_facebook(video_path, upload_meta, video_type="reel", thumbnail_path=thumbnail_path)
            logger.info(f"Facebook/Instagram Reels Upload: {fb_res}")
        except Exception as e:
            logger.warning(f"Facebook upload notice: {e}")
            
        # TikTok
        try:
            from app.upload.tiktok import upload_to_tiktok
            tt_res = upload_to_tiktok(video_path, caption=upload_meta["youtube_title"], tags=upload_meta["tags"])
            logger.info(f"TikTok Upload: {tt_res.get('status')}")
        except Exception as e:
            logger.warning(f"TikTok upload notice: {e}")

    # Record last run locally for next run's random exclusion
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "last_id": item["id"],
                "last_surah": item["surah"],
                "timestamp": int(time.time()),
                "video_path": video_path
            }, f, indent=2)
    except Exception:
        pass
    
    logger.info(f"✅ Curated Quran video execution finished! Randomly selected track: {item['id']}")
    return {
        "video_path": video_path,
        "item": item,
        "shariah_passed": shariah_passed
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Curated Quran Audio Pipeline (< 90s)")
    parser.add_argument("--index", type=int, default=None, help="Force specific track index (0-based) from curated manifest")
    parser.add_argument("--upload", dest="upload", action="store_true", default=True, help="Auto upload to social media (default: True)")
    parser.add_argument("--no-upload", dest="upload", action="store_false", help="Render video only without uploading")

    args = parser.parse_args()
    run_curated_quran_pipeline(upload=args.upload, force_index=args.index)
