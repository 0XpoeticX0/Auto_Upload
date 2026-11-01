# -*- coding: utf-8 -*-
import os
import json
import time
import urllib.request
import urllib.error
import re
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from app.logger import logger

HISTORY_FILE = os.path.abspath("data/history_log.json")

DEFAULT_SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
DEFAULT_SUPABASE_KEY = os.environ.get("SUPABASE_KEY", os.environ.get("SUPABASE_ANON_KEY", ""))

def _get_supabase_config():
    raw_url = os.environ.get("SUPABASE_URL", DEFAULT_SUPABASE_URL).strip()
    if raw_url.startswith("postgresql://") or raw_url.startswith("postgres://") or "fvboniedjpcjldoniqtp" in raw_url or not raw_url.startswith("http"):
        raw_url = DEFAULT_SUPABASE_URL
    raw_url = raw_url.rstrip("/")
    if raw_url and "/rest/v1" not in raw_url:
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
                req_url = f"{url}/{tbl}?select=id,title,source,created_at&order=created_at.desc&limit={limit}"
                req = urllib.request.Request(req_url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, list) and data:
                            return data
            except Exception:
                # Fallback to id.desc if created_at column is missing on secondary tables
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

def fetch_recent_quran_pipeline_history(limit: int = 50) -> list[dict]:
    """
    Fetches the dedicated chronological history of published Quran recitation videos
    strictly sorted by real timestamp (created_at.desc) from Supabase and local cache.
    Extracts Surah number and title to guarantee zero duplicate Surahs/Ayahs.
    """
    records = []
    try:
        url, key = _get_supabase_config()
        if url and key:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            req_url = f"{url}/used_islamic_video?source=eq.quran_verse_pipeline&order=created_at.desc&limit={limit}"
            req = urllib.request.Request(req_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list):
                        records.extend(data)
    except Exception as e:
        logger.warning(f"Failed to fetch dedicated Quran history from Supabase: {e}")

    # Fallback to general Supabase search if specific query returned empty
    if not records:
        try:
            cloud_all = _supabase_fetch_all_recent(limit=100)
            records = [r for r in cloud_all if r.get("source") == "quran_verse_pipeline" or "[কুরআন তিলাওয়াত]" in r.get("title", "")]
        except Exception:
            records = []

    # Also merge local cache records from load_history()
    try:
        hist = load_history()
        local_quran = hist.get("quran_videos", [])
        seen_ids = {str(r.get("id")) for r in records if r.get("id")}
        for lq in local_quran:
            if str(lq.get("id")) not in seen_ids:
                records.append(lq)
    except Exception:
        pass

    # Ground-truth: Check actual recent YouTube uploads so duplicate videos/Surahs are NEVER repeated
    try:
        from app.upload.youtube import get_authenticated_service
        yt = get_authenticated_service()
        if yt:
            channels = yt.channels().list(mine=True, part='contentDetails').execute()
            uploads_playlist_id = channels['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            playlist_items = yt.playlistItems().list(
                playlistId=uploads_playlist_id,
                part='snippet',
                maxResults=25
            ).execute()
            seen_titles = {str(r.get("title", "")) for r in records}
            for item in playlist_items.get('items', []):
                t_yt = item['snippet']['title']
                if ('সূরা' in t_yt or 'Surah' in t_yt) and t_yt not in seen_titles:
                    records.append({
                        "id": f"yt_{item['snippet'].get('resourceId', {}).get('videoId', '')}",
                        "title": t_yt,
                        "source": "youtube_live",
                        "created_at": item['snippet'].get('publishedAt')
                    })
                    seen_titles.add(t_yt)
    except Exception as e:
        logger.debug(f"YouTube live history fetch notice: {e}")

    parsed_records = []
    for r in records:
        row_id = str(r.get("id", ""))
        title = str(r.get("title", ""))
        created_at = r.get("created_at")

        surah_num = r.get("surah")
        if surah_num is None:
            parts = row_id.split("_")
            if len(parts) >= 3 and parts[1].isdigit():
                surah_num = int(parts[1])

        # If surah_num is still None, attempt to detect from title
        if surah_num is None and title:
            try:
                from app.quran_verse.quran_data import SURAH_NAMES_BN, SURAH_NAMES_EN
                for num, bn_name in SURAH_NAMES_BN.items():
                    if bn_name in title:
                        surah_num = num
                        break
                if surah_num is None:
                    for num, en_name in SURAH_NAMES_EN.items():
                        if en_name.lower() in title.lower():
                            surah_num = num
                            break
            except Exception:
                pass

        # Extract Ayah range from record, row_id, or title
        ayah_start = r.get("ayah_start")
        ayah_end = r.get("ayah_end")

        if ayah_start is None:
            parts = row_id.split("_")
            if len(parts) >= 5 and parts[0] == "quran" and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
                ayah_start = int(parts[2])
                ayah_end = int(parts[3])

        if ayah_start is None and title:
            t = title
            for bn_digit, en_digit in zip('০১২৩৪৫৬৭৮৯', '0123456789'):
                t = t.replace(bn_digit, en_digit)
            m = re.search(r'\((?:আয়াত|ayah|verses?)\s*:?\s*(\d+)(?:\s*[-–—]\s*(\d+))?\)', t, re.IGNORECASE)
            if m:
                ayah_start = int(m.group(1))
                ayah_end = int(m.group(2)) if m.group(2) else ayah_start

        parsed_records.append({
            "id": row_id,
            "title": title,
            "surah": surah_num,
            "ayah_start": ayah_start,
            "ayah_end": ayah_end,
            "created_at": created_at
        })

    return parsed_records

def get_used_ayahs_map(quran_history: list[dict], limit: int = 30) -> dict[int, set[int]]:
    """
    Builds a mapping of {surah_number: set_of_used_ayah_numbers}
    from the last `limit` published Quran videos.
    Allows different Ayahs of the same Surah to be recited while strictly
    forbidding duplicate recitation of already-used Ayahs.
    """
    used_map = {}
    for r in quran_history[:limit]:
        s = r.get("surah")
        a_s = r.get("ayah_start")
        a_e = r.get("ayah_end") or a_s
        if s and a_s:
            if s not in used_map:
                used_map[s] = set()
            for a in range(a_s, a_e + 1):
                used_map[s].add(a)
    return used_map

def record_quran_history(surah: int, ayah_start: int, ayah_end: int, title: str, reciter_id: str = ""):
    """Records a published Quran video to both Supabase and local history cache."""
    hist = load_history()
    if "quran_videos" not in hist:
        hist["quran_videos"] = []

    rec_id = f"quran_{surah}_{ayah_start}_{ayah_end}_{int(time.time())}"
    entry = {
        "id": rec_id,
        "surah": surah,
        "ayah_start": ayah_start,
        "ayah_end": ayah_end,
        "title": title,
        "reciter_id": reciter_id,
        "timestamp": int(time.time()),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    hist["quran_videos"] = [entry] + [v for v in hist["quran_videos"] if v.get("title") != title][:99]
    save_history(hist)

    ok = _supabase_insert({
        "id": rec_id,
        "title": title,
        "source": "quran_verse_pipeline"
    })
    if ok:
        logger.info(f"Globally recorded Quran video to Supabase: '{title}'")
    else:
        logger.info(f"Recorded Quran video locally: '{title}'")

def _init_history_structure() -> dict:
    return {
        "last_video_pillar": None,
        "last_post_pillar": None,
        "videos": [],
        "posts": [],
        "quran_videos": []
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

SEMANTIC_TOPIC_GROUPS = [
    {"name": "surah_mulk_kabor", "keywords": ["মুলক", "কবর", "কবরের আজাব", "কবরের বাতি", "সূরা মুলক", "মুনকার", "নাকির", "বারজাখ"]},
    {"name": "morning_danger_protection", "keywords": ["সকালের আমল", "সকাল-সন্ধ্যা", "সকাল সন্ধ্যা", "সকালের দোয়া", "সকাল ও সন্ধ্যার", "সকাল-সন্ধ্যার", "বিসমিল্লাহিল্লাজি লা ইয়াদুররু"]},
    {"name": "destiny_turnaround_cliche", "keywords": ["ভাগ্যের তালা", "ভাগ্য বদলে", "ভাগ্য পরিবর্তন", "জীবন বদলে"]},
    {"name": "anxiety_and_depression", "keywords": ["দুশ্চিন্তা", "পেরেশানি", "অস্থিরতা", "মানসিক অশান্তি", "হতাশা", "মন খারাপ", "ভয় ও শঙ্কা", "ভয় ও শঙ্কা"]},
    {"name": "hammi_wal_hazan_dua", "keywords": ["হাম্মি", "হাযানি", "আল-হাম্মি", "৬৩৬৯", "আবু উমামাহ"]},
    {"name": "hasbiyallahu_dua", "keywords": ["হাসবিয়াল্লাহু", "নি‘মাল ওয়াকিল", "৪৫৬৩", "আগুনে নিক্ষিপ্ত"]},
    {"name": "isme_azam", "keywords": ["ইসমে আজম", "মহান নাম", "কখনো ফিরিয়ে দেন না"]},
    {"name": "market_dua", "keywords": ["বাজারে প্রবেশ", "বাজারের দোয়া", "১০ লক্ষ নেকি"]},
    {"name": "tahajjud_prayer", "keywords": ["তাহাজ্জুদ", "শেষ রাতে", "অসম্ভব চাওয়া", "তাহাজ্জুদের", "রাতের নামাজ"]},
    {"name": "sayyidul_istighfar", "keywords": ["সাইয়্যিদুল ইস্তিগফার", "সেরা ইস্তিগফার", "ক্ষমার শ্রেষ্ঠ দোয়া"]},
    {"name": "yunus_dua", "keywords": ["ইউনুস", "মাছের পেট", "লা ইলাহা ইল্লা আনতা"]},
    {"name": "sleeping_dua", "keywords": ["ঘুমানোর আমল", "ঘুমাতে যাওয়ার", "বিসমিকা আল্লাহুম্মা", "মাঝরাতে ঘুম ভাঙলে", "দুঃস্বপ্ন", "বিছানায় যাওয়ার দোয়া"]},
    {"name": "evil_eye_badnazar", "keywords": ["বদনজর", "কুদৃষ্টি", "৩৩৭১", "৩৩৭৪", "নজর লাগা", "জাদু", "আছর", "রুকইয়া"]},
    {"name": "forgiveness_sins", "keywords": ["পাহাড় পরিমাণ গুনাহ", "পৃথিবী সমান গুনাহ", "সমুদ্রের ফেনা", "পাপ মোচন", "গুনাহ মাফ", "তওবা ও ক্ষমা"]},
    {"name": "salatul_tasbeeh", "keywords": ["সালাতুত তাসবীহ", "সালাতুত তাসবিহ", "আওয়াবীন"]},
    {"name": "parents_honor", "keywords": ["পিতা-মাতা", "পিতামাতা", "মা-বাবা", "মায়ের দোয়া", "বাবার হক", "পিতা মাতার"]},
    {"name": "anger_control", "keywords": ["রাগ নিয়ন্ত্রণ", "ক্রোধ দমন", "রাগের মাথায়", "রাগ কমানোর", "রাগ দমন"]},
    {"name": "prayer_waswasa", "keywords": ["নামাজে মনোযোগ", "নামাজে ওয়াসওয়াসা", "খিনজাব"]},
    {"name": "tongue_backbiting", "keywords": [
        "গীবত", "পরনিন্দা", "চোগলখোরি", "জিহ্বার হেফাজত", "জবানের হেফাজত", "মুখের অপব্যবহার",
        "লজ্জাস্থান", "দুই চোয়াল", "চোয়াল", "চোয়ালের", "জিম্মাদার", "জিহ্বা", "জবান", "দুই অঙ্গ", "২টি অঙ্গ",
        "মুখ ও জিহ্বা", "জিহ্বা ও লজ্জাস্থান", "মুখ আর লজ্জাস্থান", "মুখ ও লজ্জাস্থান", "চোয়ালের মাঝখানের",
        "মুখের এক কথায়", "দুই জিনিস ঠিক রাখলে", "৬৪৭৪"
    ]},
    {"name": "halal_rizq", "keywords": ["হালাল রিজিক", "হারাম খাবার", "ব্যবসা", "সততা", "উপার্জন"]},
    {"name": "neighbor_rights", "keywords": ["প্রতিবেশী", "প্রতিবেশীর হক", "প্রতিবেশীর"]},
    {"name": "two_prostrations_dua", "keywords": ["দুই সিজদা", "সিজদার মাঝে দোয়া", "দুই সিজদার মাঝের"]},
    {"name": "wudu_dua_doors", "keywords": ["অযুর পর", "অজুর পর", "৮টি দরজা", "ওজুর দোয়া", "অজুর দোয়া", "অযুর দোয়া"]},
    {"name": "debt_relief", "keywords": ["ঋণ পরিশোধ", "দেনা", "পাহাড়সমান ঋণ", "৩৫৬০", "ঋণমুক্তি", "ঋণ থেকে মুক্তি", "অর্থকষ্ট", "আর্থিক সংকট"]},
    {"name": "sick_visit", "keywords": ["রোগী দেখতে যাওয়া", "৭০ হাজার ফেরেশতা", "রোগীর সেবা", "অসুস্থ ব্যক্তিকে দেখতে"]},
    {"name": "spouse_love", "keywords": ["স্বামী-স্ত্রী", "স্ত্রীর হক", "স্বামীর হক", "দাম্পত্য", "দাম্পত্য জীবন"]},
    {"name": "jummah_kahf", "keywords": ["জুম্মা", "সূরা কাহাফ", "কাহফ", "জুমার দিনের"]},
    {"name": "istighfar_doors", "keywords": ["ইস্তিগফার", "আস্তাগফিরুল্লাহ", "ইস্তিগফারের ক্ষমতা"]},
    {"name": "seven_under_shade", "keywords": ["আরশের ছায়া", "সাত শ্রেণির মানুষ"]},
    {"name": "azan_dua", "keywords": ["আজানের দোয়া", "মুয়াজ্জিন", "ইকামত", "আজানের পর দোয়া"]},
    {"name": "salam_greeting", "keywords": ["সালামের প্রসার", "আসসালামু আলাইকুম", "সালাম দেওয়া"]},
    {"name": "patience_sabr", "keywords": ["ধৈর্য ধারণ", "সবর করা", "মুসিবতে সবর", "বিপদাপদে সবর"]},
    {"name": "charity_sadaqah", "keywords": ["সদকা", "দান-সদকা", "গোপন দান", "খয়রাত", "গরিবকে দান"]},
    {"name": "truth_honesty", "keywords": ["সত্যবাদিতা", "মিথ্যা বলা", "আমানত রক্ষা", "প্রতারণা বর্জন"]},
    {"name": "arrogance_kibr", "keywords": ["অহংকার", "দাম্ভিকতা", "বিনয় প্রকাশ", "অহংকার বর্জন"]},
    {"name": "cleanliness_taharah", "keywords": ["পরিচ্ছন্নতা", "ঈমানের অঙ্গ", "পবিত্রতা অর্জন", "তাহরাত"]},
    {"name": "guest_hospitality", "keywords": ["মেহমানদারি", "অতিথি আপ্যায়ন", "মেহমানের হক"]}
]

BANNED_OVERSATURATED_GROUPS = {
    "destiny_turnaround_cliche",
    "surah_mulk_kabor",
    "sleeping_dua",
    "anxiety_and_depression",
    "debt_relief",
    "forgiveness_sins",
    "morning_danger_protection"
}

HADITH_REGISTRY_FILE = os.path.abspath("data/used_hadiths_registry.json")

BOOK_CANONICAL_MAP = {
    'বুখারী': 'bukhari', 'বুখারি': 'bukhari', 'bukhari': 'bukhari',
    'মুসলিম': 'muslim', 'muslim': 'muslim',
    'তিরমিযী': 'tirmidhi', 'তিরমিজি': 'tirmidhi', 'tirmidhi': 'tirmidhi',
    'দাউদ': 'abu_dawood', 'dawud': 'abu_dawood', 'dawood': 'abu_dawood',
    'নাসায়ী': 'nasai', 'নাসাঈ': 'nasai', 'nasai': 'nasai',
    'মাজাহ': 'ibn_majah', 'majah': 'ibn_majah',
    'আহমদ': 'ahmad', 'ahmad': 'ahmad',
    'মালিক': 'malik', 'মুয়াত্তা': 'malik', 'malik': 'malik'
}

HADITH_CITATION_REGEX = re.compile(
    r'(সহীহ\s*বুখারী|সহীহ\s*বুখারি|বুখারী|বুখারি|সহীহ\s*মুসলিম|মুসলিম|জামে\s*আত-তিরমিযী|তিরমিযী|তিরমিজি|সুনানে\s*আবু\s*দাউদ|আবু\s*দাউদ|সুনান\s*আন-নাসায়ী|নাসায়ী|নাসাঈ|সুনান\s*ইবনে\s*মাজাহ|ইবনে\s*মাজাহ|মাজাহ|মুসনাদে\s*আহমদ|আহমদ|মুয়াত্তা\s*মালিক|মুয়াত্তা|bukhari|muslim|tirmidhi|abu\s*dawud|abu\s*dawood|nasai|ibn\s*majah)[\s:：#\.\-–—]*(?:হাদিস|হাদীস|নং|হাদিস\s*নং|hadith|no)?[\s:：#\.\-–—]*(\d+)',
    re.IGNORECASE
)

def extract_hadith_identifiers(source) -> list[dict]:
    """
    Extracts structured Hadith identifiers (canonical book, integer number, raw citation)
    from a string or a content dict (caption_points, title, references, etc.).
    """
    bn_digits = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
    def _norm(s: str) -> str:
        return "".join(bn_digits.get(ch, ch) for ch in str(s))

    text_blocks = []
    if isinstance(source, dict):
        text_blocks.append(source.get("title_bn", ""))
        text_blocks.append(source.get("title", ""))
        for pt in source.get("caption_points", []):
            text_blocks.append(pt.get("reference", ""))
            text_blocks.append(pt.get("hadith", ""))
            text_blocks.append(pt.get("title", ""))
    elif isinstance(source, (list, tuple, set)):
        for item in source:
            if isinstance(item, dict):
                text_blocks.append(item.get("reference", ""))
                text_blocks.append(item.get("hadith", ""))
            else:
                text_blocks.append(str(item))
    elif isinstance(source, str):
        text_blocks.append(source)

    combined = " ".join(text_blocks)
    combined_en = _norm(combined)

    extracted = []
    seen = set()
    for m in HADITH_CITATION_REGEX.finditer(combined_en):
        raw_book = m.group(1).lower()
        num_int = int(m.group(2))
        canon = "unknown"
        for k, v in BOOK_CANONICAL_MAP.items():
            if k in raw_book:
                canon = v
                break
        pair = (canon, num_int)
        if pair not in seen and num_int > 0:
            seen.add(pair)
            extracted.append({
                "book": canon,
                "number": num_int,
                "raw_match": m.group(0).strip()
            })

    # Also detect explicit Hadith number tags like "হাদিস নং ৬৪৭৪" or "Hadith #6474"
    for ref_num in re.findall(r'(?:হাদিস|নং|hadith|ref|reference)[\s:：#\.\-–—]*(\d{2,5})', combined_en, re.IGNORECASE):
        n = int(ref_num)
        if n >= 10 and not any(e["number"] == n for e in extracted):
            pair = ("any", n)
            if pair not in seen:
                seen.add(pair)
                extracted.append({
                    "book": "any",
                    "number": n,
                    "raw_match": f"Hadith #{n}"
                })

    return extracted

def get_used_hadith_registry(limit: int = 100) -> list[dict]:
    """
    Retrieves used Hadiths from the persistent registry and recent Supabase history.
    Guarantees strict coverage across at least the last `limit` (default 100) videos.
    """
    records = []
    seen = set()

    # 1. From persistent registry file
    if os.path.exists(HADITH_REGISTRY_FILE):
        try:
            with open(HADITH_REGISTRY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        book = item.get("book", "unknown")
                        num = item.get("number")
                        if num and (book, num) not in seen:
                            seen.add((book, num))
                            records.append(item)
        except Exception as e:
            logger.warning(f"Failed to read {HADITH_REGISTRY_FILE}: {e}")

    # 2. From recent Supabase history
    cloud_items = _supabase_fetch_all_recent(limit=limit)
    for it in cloud_items:
        t = it.get("title", "")
        extracted = extract_hadith_identifiers(t)
        for ex in extracted:
            key = (ex["book"], ex["number"])
            if key not in seen and ex["number"]:
                seen.add(key)
                records.append({
                    "book": ex["book"],
                    "number": ex["number"],
                    "reference": ex["raw_match"],
                    "title": t[:80],
                    "source": it.get("source", "")
                })

    return records

def check_hadith_number_duplicate(content_or_text, limit: int = 50) -> tuple[bool, str]:
    """
    STRICT NO SAME HADITH CHECK:
    Extracts all Hadith numbers from candidate content and compares against the past `limit` (default 50) videos.
    Matches exact Hadith numbers (e.g. 6474, 1893, 2692, 5095) regardless of phrasing or keywords.
    Returns (is_duplicate: bool, reason: str).
    """
    candidate_hadiths = extract_hadith_identifiers(content_or_text)
    if not candidate_hadiths:
        return False, ""

    used_registry = get_used_hadith_registry(limit=limit)

    for cand in candidate_hadiths:
        c_num = cand["number"]
        c_book = cand["book"]

        for past in used_registry:
            p_num = past.get("number")
            p_book = past.get("book", "unknown")

            if c_num == p_num:
                same_book = (c_book == p_book) or (c_book in ("unknown", "any")) or (p_book in ("unknown", "any"))
                if same_book or c_num >= 50:
                    past_ref = past.get("reference") or f"{p_book} #{p_num}"
                    past_title = past.get("title", "")
                    reason = (
                        f"STRICT NO SAME HADITH MANDATE: Hadith #{c_num} ({c_book}) matches previously used Hadith "
                        f"'{past_ref}' in recent videos ('{past_title}')! Duplicate Hadiths are strictly forbidden for 50 videos."
                    )
                    logger.warning(reason)
                    return True, reason

    return False, ""

def record_used_hadith(episode_bn: str, references: list[str], title_bn: str, source: str = "loop_reel_series"):
    """
    Permanently records newly used Hadith numbers to prevent duplicate selection for the next 50+ videos.
    """
    new_entries = []
    for ref in (references or []):
        extracted = extract_hadith_identifiers(ref)
        for ex in extracted:
            new_entries.append({
                "book": ex["book"],
                "number": ex["number"],
                "reference": ref,
                "episode": episode_bn,
                "title": title_bn[:80],
                "source": source,
                "timestamp": int(time.time())
            })

    if not new_entries:
        for ex in extract_hadith_identifiers(title_bn):
            new_entries.append({
                "book": ex["book"],
                "number": ex["number"],
                "reference": ex["raw_match"],
                "episode": episode_bn,
                "title": title_bn[:80],
                "source": source,
                "timestamp": int(time.time())
            })

    if not new_entries:
        return

    os.makedirs(os.path.dirname(HADITH_REGISTRY_FILE), exist_ok=True)
    existing = []
    if os.path.exists(HADITH_REGISTRY_FILE):
        try:
            with open(HADITH_REGISTRY_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    seen = {(e.get("book"), e.get("number")) for e in existing}
    added = False
    for ne in new_entries:
        key = (ne["book"], ne["number"])
        if key not in seen:
            seen.add(key)
            existing.insert(0, ne)
            added = True

    if added:
        try:
            with open(HADITH_REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(existing[:200], f, ensure_ascii=False, indent=2)
            logger.info(f"Recorded {len(new_entries)} Hadith numbers to registry for Episode {episode_bn}")
        except Exception as e:
            logger.error(f"Failed to write {HADITH_REGISTRY_FILE}: {e}")

def get_topic_semantic_group(text: str) -> str:
    if not text:
        return ""
    text_lower = text.lower()
    for group in SEMANTIC_TOPIC_GROUPS:
        for kw in group["keywords"]:
            if kw.lower() in text_lower:
                return group["name"]
    return ""

def check_topic_duplicate_global_detail(
    new_topic_text: str,
    threshold: float = 0.40,
    check_semantic: bool = True
) -> tuple[bool, str]:
    """
    Checks if a candidate topic/quote/hadith has already been covered in recent videos.
    - Exact Hadith Number & Book: Checked against past 50+ videos (STRICT NO SAME HADITH RULE).
    - Clickbait clichés: 100% unconditionally banned.
    - Semantic topic categories: 50-video cooldown across all categories (STRICT NO TOPIC REPEAT FOR 50 VIDEOS).
    - Exact Hadith citations & Jaccard overlap: checked against the full LAST 100 VIDEOS (Jaccard depth: 50).
    Returns (is_duplicate: bool, reason_or_match: str).
    """
    if not new_topic_text or len(new_topic_text.strip()) < 5:
        return False, ""

    # 0. STRICT HADITH NUMBER DEDUPLICATION (Checks exact Hadith number - NO SAME HADITH FOR 50 VIDEOS)
    is_hadith_dup, hadith_dup_reason = check_hadith_number_duplicate(new_topic_text, limit=50)
    if is_hadith_dup:
        return True, hadith_dup_reason
        
    all_used = get_all_used_topics_global(limit=150)
    cleaned_new = re.sub(r'[^\w\s]', '', new_topic_text).lower()
    new_words = set(cleaned_new.split())
    
    if check_semantic:
        # 1. Ban clickbait clichés unconditionally
        new_group = get_topic_semantic_group(new_topic_text)
        if new_group == "destiny_turnaround_cliche":
            msg = f"Banned cliché hook detected ('destiny_turnaround_cliche'): '{new_topic_text}'"
            logger.warning(msg)
            return True, msg

        # 2. Block semantic category repetition for at least 50 videos
        if new_group:
            cooldown_depth = 50
            for past in all_used[:cooldown_depth]:
                past_group = get_topic_semantic_group(past)
                if past_group == new_group:
                    msg = f"Semantic category '{new_group}' was already covered in past {cooldown_depth} videos: '{past}'"
                    logger.warning(msg)
                    return True, msg

    bn_to_en = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
    def _norm_digits(s: str) -> str:
        return "".join(bn_to_en.get(c, c) for c in s)

    # Filter out small single-digit counts (<=5) like '৩টি আমল' to avoid false positives
    new_numbers = set(n for n in re.findall(r'\d+', _norm_digits(new_topic_text)) if len(n) >= 2 or (n.isdigit() and int(n) > 5))
    
    for idx, past in enumerate(all_used[:100]):
        cleaned_past = re.sub(r'[^\w\s]', '', past).lower()
        past_words = set(cleaned_past.split())
        if not past_words:
            continue
            
        # 3. Exact reference / Hadith number match across all major Hadith books (checked across ALL 100 videos)
        past_numbers = set(n for n in re.findall(r'\d+', _norm_digits(past)) if len(n) >= 2 or (n.isdigit() and int(n) > 5))
        if new_numbers and past_numbers and len(new_numbers.intersection(past_numbers)) >= 1:
            major_hadith_sources = ["বুখারী", "মুসলিম", "তিরমিযী", "তিরমিজি", "দাউদ", "নাসায়ী", "নাসাঈ", "ইবনে মাজাহ", "আহমদ"]
            if any(src in new_topic_text and src in past for src in major_hadith_sources):
                matching_nums = new_numbers.intersection(past_numbers)
                msg = f"Duplicate Hadith reference detected (number {matching_nums}) in last 100 videos: '{past}'"
                logger.warning(f"Duplicate Hadith reference detected: '{new_topic_text}' vs '{past}'")
                return True, msg
                
        # 4. Word overlap Jaccard similarity across recent 50 videos
        if idx < 50:
            intersection = new_words.intersection(past_words)
            union = new_words.union(past_words)
            similarity = len(intersection) / len(union) if union else 0
            if similarity >= threshold:
                msg = f"High similarity ({similarity:.2f}) with recent video: '{past}'"
                logger.warning(f"High similarity ({similarity:.2f}) with past content: '{new_topic_text}' vs '{past}'")
                return True, msg
                msg = f"High similarity ({similarity:.2f}) with recent video: '{past}'"
                logger.warning(f"High similarity ({similarity:.2f}) with past content: '{new_topic_text}' vs '{past}'")
                return True, msg
            
    return False, ""

def is_topic_duplicate_global(new_topic_text: str, threshold: float = 0.40) -> bool:
    """
    Checks if a candidate topic/quote/hadith has already been covered in the last 100 videos.
    Uses Semantic Topic Grouping, Exact Hadith Citations, and Jaccard Word Overlap.
    """
    is_dup, _ = check_topic_duplicate_global_detail(new_topic_text, threshold)
    return is_dup

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
    Starts strictly from Episode 51 onwards without any count cap (51 -> 52 -> 53...).
    """
    cloud_items = _supabase_fetch_all_recent(limit=300)
    
    max_ep = 50  # Baseline: start strictly from 51 (after episode 50)
    bn_map = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
    
    for item in cloud_items:
        src = item.get("source", "")
        title = item.get("title", "")
        
        if "loop" in src or "loop" in item.get("id", "") or "পর্ব" in title:
            match = re.search(r"পর্ব\s*([০-৯\d]+)", title)
            if match:
                bn_digits = match.group(1)
                en_str = "".join(bn_map.get(ch, ch) for ch in bn_digits)
                try:
                    ep_val = int(en_str)
                    if ep_val >= 1:
                        if ep_val > max_ep:
                            max_ep = ep_val
                except Exception:
                    pass

    next_ep = max_ep + 1
    return next_ep, to_bangla_digits(next_ep)

def get_unique_background(category: str = None) -> str:
    """
    Returns an 8K background guaranteed to be non-repeating across the last 15-20 videos.
    Cycles through all available 8K scenes without consecutive duplicate images.
    If category is supplied, prioritizes assets tailored to that category.
    """
    from app.quality.vision_guardian import PILLAR_THEMATIC_ASSETS
    
    scenes_dir = os.path.abspath("app/assets/scenes")
    candidates = []
    
    if category and category in PILLAR_THEMATIC_ASSETS:
        candidates = [os.path.abspath(c) for c in PILLAR_THEMATIC_ASSETS[category] if os.path.exists(c)]
        
    if not candidates and os.path.exists(scenes_dir):
        for f in os.listdir(scenes_dir):
            if f.endswith(".jpg") and "clean_bg" not in f:
                candidates.append(os.path.join(scenes_dir, f))
        quran_master = os.path.abspath("app/assets/quran_rehal_master.jpg")
        if os.path.exists(quran_master):
            candidates.append(quran_master)

    if not candidates:
        return ""

    hist = load_history()
    recent_bg = hist.get("recent_backgrounds", [])

    # Filter out any background used in recent runs (up to len(candidates) - 2)
    cutoff = max(1, min(len(candidates) - 2, 20))
    recently_used_names = set(os.path.basename(p) for p in recent_bg[-cutoff:])

    available = [c for c in candidates if os.path.basename(c) not in recently_used_names]
    if not available:
        available = candidates

    import random
    chosen = random.choice(available)
    
    # Record usage
    recent_bg.append(os.path.basename(chosen))
    hist["recent_backgrounds"] = recent_bg[-50:]
    save_history(hist)
    
    logger.info(f"🎨 Non-repeating background selected: {os.path.basename(chosen)} (Excluded recent: {len(recently_used_names)})")
    return chosen


