import os
import json
import time
from app.logger import logger

HISTORY_FILE = os.path.abspath("data/history_log.json")

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
    """Saves content history to persistent JSON file."""
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved persistent history to {HISTORY_FILE}")
    except Exception as e:
        logger.error(f"Failed to save history file: {e}")

def record_video_history(title: str, category: str, core_concept: str = ""):
    """Records a generated video topic to persistent history."""
    hist = load_history()
    hist["last_video_pillar"] = category
    
    entry = {
        "title": title,
        "category": category,
        "core_concept": core_concept,
        "timestamp": int(time.time()),
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Prepend new entry and cap at 150 items
    hist["videos"] = [entry] + [v for v in hist.get("videos", []) if v.get("title") != title][:149]
    save_history(hist)
    logger.info(f"Recorded video '{title}' to persistent history.")

def record_post_history(title: str, category: str, quote: str, reference: str):
    """Records a generated social media post to persistent history."""
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
    logger.info(f"Recorded post [{reference}] to persistent history.")

def get_recent_video_titles(limit: int = 50) -> list[str]:
    """Returns list of recently covered video titles/concepts for negative prompting."""
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
    """Returns list of recently covered post references & quotes."""
    hist = load_history()
    return hist.get("posts", [])[:limit]

def get_next_pillar_from_history(pillars: list, pillar_type: str = "video") -> dict:
    """
    Computes the next pillar in fixed round-robin order using persistent history
    with a deterministic time-slot fallback.
    """
    hist = load_history()
    last_key = hist.get("last_video_pillar") if pillar_type == "video" else hist.get("last_post_pillar")
    
    if last_key:
        for i, p in enumerate(pillars):
            key = p.get("category") or p.get("key")
            if key == last_key:
                next_p = pillars[(i + 1) % len(pillars)]
                logger.info(f"Round-robin from history: last was '{last_key}' -> next is '{next_p.get('category') or next_p.get('key')}'")
                return next_p
                
    # Fallback to deterministic time slot (Hour + Day modulo pillars)
    day_slot = int(time.time() // 86400)
    hour_slot = int((time.time() % 86400) // (3600 * 4)) # 6 slots per day
    idx = (day_slot + hour_slot) % len(pillars)
    chosen = pillars[idx]
    logger.info(f"Deterministic slot fallback: selected pillar '{chosen.get('category') or chosen.get('key')}'")
    return chosen
