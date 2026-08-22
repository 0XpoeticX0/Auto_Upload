# -*- coding: utf-8 -*-
import os
import json
import time
import urllib.request
import urllib.error
import re
from app.logger import logger

HISTORY_FILE = os.path.abspath("data/history_log.json")

DEFAULT_SUPABASE_URL = "https://tvezntceubxaqvcicyyc.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR2ZXpudGNldWJ4YXF2Y2ljeXljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3NTg0NjgsImV4cCI6MjA5OTMzNDQ2OH0.sx5A6WT54mQUqqMDvrDZqo-mCURidOpVri-j7JFekq0"

def _get_supabase_config():
    raw_url = os.environ.get("SUPABASE_URL", DEFAULT_SUPABASE_URL).strip()
    if raw_url.startswith("postgresql://") or raw_url.startswith("postgres://") or "fvboniedjpcjldoniqtp" in raw_url or not raw_url.startswith("http"):
        raw_url = DEFAULT_SUPABASE_URL
    raw_url = raw_url.rstrip("/")
    if "/rest/v1" not in raw_url:
        raw_url = f"{raw_url}/rest/v1"
    key = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_ANON_KEY", DEFAULT_SUPABASE_KEY))
    return raw_url, key

DEFAULT_SUPABASE_TABLE = "used_islamic_video"

def _supabase_insert(row_data: dict) -> bool:
    """Inserts a topic record to Supabase used_islamic_video (or used_videos fallback)."""
    try:
        url, key = _get_supabase_config()
        if not key or not url:
            return False
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        payload = json.dumps({
            "id": row_data.get("id"),
            "title": row_data.get("title"),
            "source": row_data.get("source", "content")
        }).encode("utf-8")

        # Try inserting to primary tables
        for tbl in ["used_islamic_video", "used_islamic_videos", "used_videos"]:
            try:
                req = urllib.request.Request(f"{url}/{tbl}", data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        return True
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Supabase insert notice: {e}")
    return False

def _supabase_fetch_all_recent(limit: int = 150) -> list[dict]:
    """Fetches all recent topics from Supabase across ALL pipelines (video, loop, post)."""
    try:
        url, key = _get_supabase_config()
        if not key or not url:
            return []
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        for tbl in ["used_islamic_video", "used_islamic_videos", "used_videos"]:
            try:
                req_url = f"{url}/{tbl}?select=id,title,source&order=id.desc&limit={limit}"
                req = urllib.request.Request(req_url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, list) and data:
                            return data
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Supabase fetch notice: {e}")
    return []

def _init_history_structure() -> dict:
    return {
        "last_video_pillar": None,
        "last_post_pillar": None,
        "videos": [],
        "posts": []
    }

def load_history() -> dict:
    """Loads content history from persistent JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.warning(f"Error loading history file: {e}")
            
    return _init_history_structure()

def save_history(data: dict):
    """Saves content history to local cache file."""
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save local history file: {e}")

def get_all_used_topics_global(limit: int = 150) -> list[str]:
    """
    Returns a UNIFIED global list of ALL used topics, Hadiths, and concepts across:
    - 🎙️ AI Voiceover Reels
    - 📖 7s Quran Loop Reels
    - 🖼️ Facebook & Instagram Image Cards
    Ensures absolute zero cross-pipeline duplication.
    """
    unified_list = []
    seen = set()

    # 1. Fetch from Supabase Cloud
    cloud_items = _supabase_fetch_all_recent(limit=limit)
    for item in cloud_items:
        t = (item.get("title") or "").strip()
        if t and t not in seen:
            seen.add(t)
            unified_list.append(t)

    # 2. Fetch from Local History Log
    hist = load_history()
    for v in hist.get("videos", []):
        t = v.get("title", "").strip()
        c = v.get("core_concept", "").strip()
        label = f"{t} (Concept: {c})" if c and c != "N/A" else t
        if label and label not in seen:
            seen.add(label)
            unified_list.append(label)

    for p in hist.get("posts", []):
        ref = p.get("reference", "").strip()
        q = p.get("quote", "").strip()
        label = f"[{ref}] {q[:60]}" if ref else q[:60]
        if label and label not in seen:
            seen.add(label)
            unified_list.append(label)

    # 3. Fetch from local SQLite if available
    try:
        from app.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM topics ORDER BY id DESC LIMIT 100")
        for row in cursor.fetchall():
            t = (row[0] or "").strip()
            if t and t not in seen:
                seen.add(t)
                unified_list.append(t)
        cursor.execute("SELECT quote, reference FROM posts ORDER BY id DESC LIMIT 100")
        for row in cursor.fetchall():
            q, ref = row[0] or "", row[1] or ""
            label = f"[{ref}] {q[:60]}" if ref else q[:60]
            if label and label not in seen:
                seen.add(label)
                unified_list.append(label)
        conn.close()
    except Exception:
        pass

    return unified_list[:limit]

def is_topic_duplicate_global(new_topic_text: str, threshold: float = 0.65) -> bool:
    """
    Checks if a candidate topic/quote/hadith has already been covered anywhere in the system.
    """
    if not new_topic_text or len(new_topic_text.strip()) < 5:
        return False
        
    all_used = get_all_used_topics_global(limit=200)
    cleaned_new = re.sub(r'[^\w\s]', '', new_topic_text).lower()
    new_words = set(cleaned_new.split())
    
    for past in all_used:
        cleaned_past = re.sub(r'[^\w\s]', '', past).lower()
        past_words = set(cleaned_past.split())
        if not past_words:
            continue
            
        # Exact reference match (e.g., ১১৫৪ or ৩৩৭৪)
        new_numbers = set(re.findall(r'\d+', new_topic_text))
        past_numbers = set(re.findall(r'\d+', past))
        if new_numbers and past_numbers and len(new_numbers.intersection(past_numbers)) >= 1:
            if "বুখারী" in new_topic_text and "বুখারী" in past:
                logger.warning(f"Duplicate Hadith reference detected: {new_topic_text} vs {past}")
                return True
                
        # Word overlap Jaccard similarity
        intersection = new_words.intersection(past_words)
        union = new_words.union(past_words)
        similarity = len(intersection) / len(union) if union else 0
        if similarity >= threshold:
            logger.warning(f"High similarity ({similarity:.2f}) with past content: '{new_topic_text}' vs '{past}'")
            return True
            
    return False

def record_video_history(title: str, category: str, core_concept: str = ""):
    """Records a generated video topic to Supabase and local cache."""
    hist = load_history()
    hist["last_video_pillar"] = category
    entry = {
        "title": title,
        "category": category,
        "core_concept": core_concept,
        "timestamp": int(time.time()),
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    hist["videos"] = [entry] + [v for v in hist.get("videos", []) if v.get("title") != title][:199]
    save_history(hist)

    full_title = f"{title} (Concept: {core_concept})" if core_concept else title
    v_id = f"vid_{int(time.time())}"
    ok = _supabase_insert({"id": v_id, "title": full_title, "source": f"video_{category}"})
    if ok:
        logger.info(f"Globally recorded video topic to Supabase: '{title}'")
    else:
        logger.info(f"Globally recorded video topic locally: '{title}'")

def record_post_history(title: str, category: str, quote: str, reference: str):
    """Records a generated social media post to Supabase and local cache."""
    hist = load_history()
    hist["last_post_pillar"] = category
    entry = {
        "title": title,
        "category": category,
        "quote": quote[:80] if quote else "",
        "reference": reference,
        "timestamp": int(time.time()),
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    hist["posts"] = [entry] + [p for p in hist.get("posts", []) if p.get("reference") != reference][:199]
    save_history(hist)

    post_label = f"[{reference}] {quote[:70]}" if reference else title
    p_id = f"post_{int(time.time())}"
    ok = _supabase_insert({"id": p_id, "title": post_label, "source": f"post_{category}"})
    if ok:
        logger.info(f"Globally recorded post topic to Supabase: [{reference}]")
    else:
        logger.info(f"Globally recorded post topic locally: [{reference}]")

def get_recent_video_titles(limit: int = 60) -> list[str]:
    """Returns list of recently covered video titles from global unified memory."""
    return get_all_used_topics_global(limit=limit)

def get_recent_post_records(limit: int = 60) -> list[dict]:
    """Returns list of recently covered posts from global unified memory."""
    all_used = get_all_used_topics_global(limit=limit)
    return [{"reference": item, "quote": item} for item in all_used]

def get_next_pillar_from_history(pillars: list, pillar_type: str = "video") -> dict:
    """
    Computes the next pillar in fixed round-robin order using Supabase history.
    """
    cloud_items = _supabase_fetch_all_recent(limit=10)
    prefix = "video_" if pillar_type == "video" else "post_"
    last_key = None
    
    for item in cloud_items:
        src = item.get("source", "")
        if src.startswith(prefix):
            last_key = src[len(prefix):]
            break
            
    if not last_key:
        hist = load_history()
        last_key = hist.get("last_video_pillar") if pillar_type == "video" else hist.get("last_post_pillar")
        
    if last_key:
        for i, p in enumerate(pillars):
            key = p.get("category") or p.get("key")
            if key == last_key:
                next_p = pillars[(i + 1) % len(pillars)]
                logger.info(f"Round-robin from Supabase: last was '{last_key}' -> next is '{next_p.get('category') or next_p.get('key')}'")
                return next_p
                
    day_slot = int(time.time() // 86400)
    hour_slot = int((time.time() % 86400) // (3600 * 4))
    idx = (day_slot + hour_slot) % len(pillars)
    chosen = pillars[idx]
    logger.info(f"Deterministic slot fallback: selected pillar '{chosen.get('category') or chosen.get('key')}'")
    return chosen

def to_bangla_digits(number: int) -> str:
    """Converts standard digits to Bengali numerals."""
    en_to_bn = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    return "".join(en_to_bn.get(ch, ch) for ch in str(number))

def get_next_episode_number() -> tuple[int, str]:
    """
    Calculates continuous series episode number for 'দৈনন্দিন সহীহ আমল'.
    Tracks actual loop reel series episodes from Supabase, accurately starting from Episode 2 -> 3 -> 4.
    """
    cloud_items = _supabase_fetch_all_recent(limit=300)
    
    max_ep = 2  # Baseline start (after episode 1 and 2)
    bn_map = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
    
    for item in cloud_items:
        src = item.get("source", "")
        title = item.get("title", "")
        
        if src.startswith("loop") or "loop" in item.get("id", ""):
            match = re.search(r"পর্ব\s*([০-৯\d]+)", title)
            if match:
                bn_digits = match.group(1)
                en_str = "".join(bn_map.get(ch, ch) for ch in bn_digits)
                try:
                    ep_val = int(en_str)
                    if 2 <= ep_val < 50:
                        if ep_val > max_ep:
                            max_ep = ep_val
                except Exception:
                    pass

    next_ep = max_ep + 1
    return next_ep, to_bangla_digits(next_ep)

