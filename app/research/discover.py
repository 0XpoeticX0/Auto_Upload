import sqlite3
import random
import json
from app.logger import logger
from app.database import get_connection
from app.llm.provider import extract_json

# Core theme keywords for deduplication — prevent same theme appearing twice
THEME_KEYWORDS = {
    "দুশ্চিন্তা": ["দুশ্চিন্তা", "মানসিক অস্থিরতা", "উদ্বেগ", "পেরেশানি"],
    "তওবা": ["তওবা", "গুনাহ মাফ", "ক্ষমা", "ইস্তিগফার"],
    "কবর": ["কবর", "মৃত্যু", "সাকরাতুল মাউত", "আখিরাত"],
    "হালাল": ["হালাল", "হারাম", "রিজিক", "উপার্জন"],
    "জবান": ["জবান", "কথা", "মুখ", "বাক্য"],
    "দোয়া": ["দোয়া", "আমল", "যিকির", "তাসবিহ"],
    "কিয়ামত": ["কিয়ামত", "শেষ যামানা", "দাজ্জাল", "ইমাম মাহদি"],
}

def _get_topic_theme(title: str) -> str:
    """Returns the theme key if a title matches a known theme, else None."""
    title_lower = title.lower()
    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return theme
    return None

def generate_islamic_topics(recent_titles=None, used_themes=None):
    used_themes = used_themes or set()
    
    # Build strict avoidance rules for the prompt
    avoid_section = ""
    if recent_titles:
        avoid_section += "\n\nCRITICAL RULE — DO NOT repeat or slightly rephrase any of these recent topics:\n"
        for t in recent_titles:
            avoid_section += f"- {t}\n"
    
    if used_themes:
        avoid_section += f"\nALSO AVOID these themes entirely (already covered recently): {', '.join(used_themes)}\n"

    system_prompt = f"""You are an expert Islamic content researcher for viral Bengali YouTube Shorts and Reels.
Generate 4 highly engaging, deeply emotional Islamic topics in Bangla (বাংলা) — one per pillar below.
Each topic MUST be backed by authentic Quran or Sahih Hadith.
Each topic MUST be completely different in theme from the others.
Titles should be emotionally gripping (max 12 words each).

PILLARS (one topic per pillar, no exceptions):
1. দৈনন্দিন জীবন: হালাল/হারাম, সম্পর্ক, আচরণ, লেনদেন, নামাজ-রোজার ফজিলত
2. দোয়া ও নিরাময়: বিপদ, রোগ, মানসিক কষ্ট থেকে মুক্তির সহীহ দোয়া ও আমল
3. অন্তর গলানো নসিহত: তওবা, আল্লাহর রহমত, অনুপ্রেরণা, গুনাহ থেকে ফেরার পথ
4. শেষ যামানা ও আখিরাত: কিয়ামতের আলামত, কবরের জীবন, জান্নাত-জাহান্নামের বর্ণনা
{avoid_section}

Output ONLY valid JSON in this exact format:
{{
    "topics": [
        {{"title": "...", "category": "daily_life", "score": 97.5}},
        {{"title": "...", "category": "dua_cures", "score": 98.0}},
        {{"title": "...", "category": "heart_softeners", "score": 99.0}},
        {{"title": "...", "category": "islamic_knowledge", "score": 98.5}}
    ]
}}"""

    user_prompt = "Generate 4 fresh unique Bengali Islamic Short topics, one per pillar. No repetition of themes."

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=1000)
        return data.get("topics", [])
    except Exception as e:
        logger.error(f"Error generating Islamic topics: {e}")
        return []

def run_discovery():
    category = "islamic_knowledge"
    logger.info(f"Selected content category: {category.upper().replace('_', ' ')}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch last 20 produced titles for anti-repetition
    try:
        cursor.execute("SELECT title FROM topics WHERE status IN ('IN_PROGRESS', 'DONE', 'DISCOVERED') ORDER BY id DESC LIMIT 20")
        recent_titles = [row["title"] for row in cursor.fetchall()]
    except Exception:
        recent_titles = []
    
    # Find which themes are already covered in the pending queue
    try:
        cursor.execute("SELECT title FROM topics WHERE status = 'DISCOVERED' ORDER BY id DESC")
        pending = [row["title"] for row in cursor.fetchall()]
        used_themes = set(filter(None, [_get_topic_theme(t) for t in pending]))
    except Exception:
        used_themes = set()

    topics = generate_islamic_topics(recent_titles, used_themes)
    
    if not topics:
        logger.warning("No topics generated. Using fallback topics in Bangla.")
        topics = [
            {"title": "নামাজে মনোযোগ ধরে রাখার কার্যকর আমল", "category": "daily_life", "score": 98.0},
            {"title": "ইউনুস (আ.)-এর দোয়া: ঘোর বিপদ থেকে মুক্তির পথ", "category": "dua_cures", "score": 99.0},
            {"title": "আল্লাহর ভালোবাসা পাওয়ার সহজ ৩টি আমল", "category": "heart_softeners", "score": 97.5},
            {"title": "কিয়ামতের দিন নবীজির শাফাআত কারা পাবেন?", "category": "islamic_knowledge", "score": 98.5}
        ]
    
    # Deduplicate: skip topics whose theme is already in the pending queue
    new_topics = []
    for t in topics:
        theme = _get_topic_theme(t.get("title", ""))
        if theme and theme in used_themes:
            logger.info(f"Skipping duplicate-theme topic: {t['title']} (theme: {theme})")
            continue
        if theme:
            used_themes.add(theme)
        new_topics.append(t)

    for t in new_topics:
        title = t.get("title", "")
        score = t.get("score", 90.0)
        cat = t.get("category", "islamic_knowledge")
        try:
            cursor.execute(
                "INSERT INTO topics (title, source, score, status) VALUES (?, ?, ?, 'DISCOVERED')",
                (title, f"Gemini AI Discovery ({cat})", score)
            )
        except Exception:
            pass
            
    conn.commit()
    
    # Pick the top undiscovered topic
    cursor.execute("SELECT id, title, score FROM topics WHERE status = 'DISCOVERED' ORDER BY score DESC LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        logger.error("No valid discovered topic found.")
        conn.close()
        return None
        
    topic = {
        "id": row["id"],
        "title": row["title"],
        "score": row["score"],
        "category": category
    }
    
    cursor.execute("UPDATE topics SET status = 'IN_PROGRESS' WHERE id = ?", (topic["id"],))
    conn.commit()
    conn.close()
    
    logger.info(f"Selected topic for production: {topic['title']} (ID: {topic['id']})")
    return topic
