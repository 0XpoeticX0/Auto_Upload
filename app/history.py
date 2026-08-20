import os
import json
import time
import urllib.request
import urllib.error
from app.logger import logger

HISTORY_FILE = os.path.abspath("data/history_log.json")

DEFAULT_SUPABASE_URL = "https://tvezntceubxaqvcicyyc.supabase.co"
DEFAULT_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR2ZXpudGNldWJ4YXF2Y2ljeXljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM3NTg0NjgsImV4cCI6MjA5OTMzNDQ2OH0.sx5A6WT54mQUqqMDvrDZqo-mCURidOpVri-j7JFekq0"

def _get_supabase_config():
    raw_url = os.environ.get("SUPABASE_URL", DEFAULT_SUPABASE_URL).rstrip("/")
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
            "source": row_data.get("source", "video")
        }).encode("utf-8")

        # 1. Try used_islamic_video / used_islamic_videos
        for tbl in ["used_islamic_video", "used_islamic_videos"]:
            try:
                req = urllib.request.Request(f"{url}/{tbl}", data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201):
                        return True
            except Exception:
                pass

        # 2. Fallback to used_videos
        req = urllib.request.Request(f"{url}/used_videos", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        logger.warning(f"Supabase insert notice: {e}")
        return False

def _supabase_fetch_recent(source_prefix: str, limit: int = 50) -> list[dict]:
    """Fetches recent topics from Supabase used_islamic_video (or used_videos fallback)."""
    try:
        url, key = _get_supabase_config()
        if not key or not url:
            return []
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        # 1. Try used_islamic_video / used_islamic_videos
        for tbl in ["used_islamic_video", "used_islamic_videos"]:
            try:
                req_url = f"{url}/{tbl}?source=like.{source_prefix}*&select=id,title,source&limit={limit}"
                req = urllib.request.Request(req_url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, list) and data:
                            return data
            except Exception:
                pass

        # 2. Fallback to used_videos
        req_url = f"{url}/used_videos?source=like.{source_prefix}*&select=id,title,source&limit={limit}"
        req = urllib.request.Request(req_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list):
                    return data
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

def record_video_history(title: str, category: str, core_concept: str = ""):
    """Records a generated video topic to Supabase and local cache."""
    # 1. Update local cache
    hist = load_history()
    hist["last_video_pillar"] = category
    entry = {
        "title": title,
        "category": category,
        "core_concept": core_concept,
        "timestamp": int(time.time()),
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    hist["videos"] = [entry] + [v for v in hist.get("videos", []) if v.get("title") != title][:149]
    save_history(hist)

    # 2. Sync to Supabase in real-time
    full_title = f"{title} (Concept: {core_concept})" if core_concept else title
    v_id = f"vid_{int(time.time())}"
    ok = _supabase_insert({"id": v_id, "title": full_title, "source": f"video_{category}"})
    if ok:
        logger.info(f"Recorded video topic to Supabase (used_videos): '{title}'")
    else:
        logger.info(f"Recorded video topic locally: '{title}'")

def record_post_history(title: str, category: str, quote: str, reference: str):
    """Records a generated social media post to Supabase and local cache."""
    # 1. Update local cache
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
    hist["posts"] = [entry] + [p for p in hist.get("posts", []) if p.get("reference") != reference][:149]
    save_history(hist)

    # 2. Sync to Supabase in real-time
    post_label = f"[{reference}] {quote[:70]}" if reference else title
    p_id = f"post_{int(time.time())}"
    ok = _supabase_insert({"id": p_id, "title": post_label, "source": f"post_{category}"})
    if ok:
        logger.info(f"Recorded post topic to Supabase (used_videos): [{reference}]")
    else:
        logger.info(f"Recorded post topic locally: [{reference}]")

def get_recent_video_titles(limit: int = 50) -> list[str]:
    """Returns list of recently covered video titles/concepts from Supabase (fallback to local)."""
    # Try Supabase first
    cloud_items = _supabase_fetch_recent("video_", limit=limit)
    if cloud_items:
        return [item["title"] for item in cloud_items if item.get("title")]
        
    # Local fallback
    hist = load_history()
    titles = []
    for v in hist.get("videos", [])[:limit]:
        t = v.get("title", "")
        c = v.get("core_concept", "")
        if c and c != "N/A":
            titles.append(f"{t} (Concept: {c})")
        elif t:
            titles.append(t)
    return titles

def get_recent_post_records(limit: int = 50) -> list[dict]:
    """Returns list of recently covered post references & quotes from Supabase (fallback to local)."""
    cloud_items = _supabase_fetch_recent("post_", limit=limit)
    if cloud_items:
        return [{"reference": item["title"], "quote": item["title"]} for item in cloud_items if item.get("title")]
        
    hist = load_history()
    return hist.get("posts", [])[:limit]

def get_next_pillar_from_history(pillars: list, pillar_type: str = "video") -> dict:
    """
    Computes the next pillar in fixed round-robin order using Supabase (fallback to local/deterministic).
    """
    prefix = "video_" if pillar_type == "video" else "post_"
    cloud_items = _supabase_fetch_recent(prefix, limit=1)
    last_key = None
    
    if cloud_items:
        src = cloud_items[0].get("source", "")
        if src.startswith(prefix):
            last_key = src[len(prefix):]
            
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
                
    # Fallback to deterministic time slot (Hour + Day modulo pillars)
    day_slot = int(time.time() // 86400)
    hour_slot = int((time.time() % 86400) // (3600 * 4))
    idx = (day_slot + hour_slot) % len(pillars)
    chosen = pillars[idx]
    logger.info(f"Deterministic slot fallback: selected pillar '{chosen.get('category') or chosen.get('key')}'")
    return chosen
