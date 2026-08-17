import json
from app.logger import logger
from app.database import get_connection
from app.llm.provider import extract_json

# The 4 pillars in fixed rotation order — each run picks the NEXT pillar
PILLARS = [
    {
        "category": "daily_life",
        "label": "দৈনন্দিন জীবন",
        "description": "হালাল/হারাম, সম্পর্ক, আচরণ, লেনদেন, নামাজ-রোজার ফজিলত, পরিবার"
    },
    {
        "category": "dua_cures",
        "label": "দোয়া ও নিরাময়",
        "description": "বিপদ, রোগ, মানসিক কষ্ট থেকে মুক্তির সহীহ দোয়া ও আমল"
    },
    {
        "category": "heart_softeners",
        "label": "অন্তর গলানো নসিহত",
        "description": "তওবা, আল্লাহর রহমত, অনুপ্রেরণা, গুনাহ থেকে ফেরার পথ, আল্লাহর ভালোবাসা"
    },
    {
        "category": "islamic_knowledge",
        "label": "শেষ যামানা ও আখিরাত",
        "description": "কিয়ামতের আলামত, কবরের জীবন, জান্নাত-জাহান্নামের বর্ণনা, দাজ্জাল"
    },
]

def _get_next_pillar(cursor) -> dict:
    """
    Determines which pillar to use next based on what was last used.
    Rotates: daily_life → dua_cures → heart_softeners → islamic_knowledge → daily_life → ...
    """
    try:
        # Find the category of the most recently used topic
        cursor.execute(
            "SELECT source FROM topics WHERE status = 'IN_PROGRESS' ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row and row["source"]:
            # Source is stored as "Gemini AI Discovery (category)"
            src = row["source"]
            last_cat = src.split("(")[-1].rstrip(")").strip() if "(" in src else None
            if last_cat:
                # Find this category in PILLARS and return the NEXT one
                for i, p in enumerate(PILLARS):
                    if p["category"] == last_cat:
                        next_pillar = PILLARS[(i + 1) % len(PILLARS)]
                        logger.info(f"Round-robin: last pillar was '{last_cat}' → next is '{next_pillar['category']}'")
                        return next_pillar
    except Exception as e:
        logger.warning(f"Could not determine last pillar: {e}")

    # Default: start from the first pillar
    logger.info("Starting round-robin from first pillar: 'daily_life'")
    return PILLARS[0]


def generate_topic_for_pillar(pillar: dict, recent_titles: list) -> dict | None:
    """Ask Gemini for ONE fresh topic for the given pillar with strict concept-level deduplication."""
    avoid_section = ""
    if recent_titles:
        avoid_section = "\n\nCRITICAL CONCEPT DEDUPLICATION RULE:\nBelow is the list of topics/stories ALREADY covered in the last 40 days:\n"
        for t in recent_titles:
            avoid_section += f"- {t}\n"
        avoid_section += """
YOU MUST NOT COVER THE SAME CORE CONCEPT, STORY, EVENT, OR HADITH EVEN UNDER A DIFFERENT NAME OR TITLE!
Examples of forbidden concept repetitions:
- If "দাজ্জালের চোখ" was covered, do NOT make "দাজ্জালের শারীরিক গঠন", "দাজ্জাল অন্ধ হবে কোন চোখে", or any topic about Dajjal's eyes/appearance. Pick a completely different topic (e.g. ইয়াজুজ মাজুজ, সুরমা ব্যবহারের সুন্নত, মুসা (আ.) ও খিজির (আ.), ইত্যাদি).
- If "ইউনুস (আ.) এর দোয়া" was covered, do NOT make "মাছের পেটের দোয়া" or "বিপদ মুক্তির ইউনুসি আমল". Pick Ayub (AS)'s shifa dua, Ibrahim (AS)'s dua in fire, etc.
- If "কবরের প্রথম রাত" was covered, do NOT make "কবরের আযাব" or "কবরে যা ঘটবে". Pick পুলসিরাত পার হওয়ার আমল, হাউজে কাওসারের পানি, মিজানের পাল্লা, etc.

CHOOSE A COMPLETELY UNRELATED EVENT, SAHIH HADITH, OR LESSON FROM THE VAST ISLAMIC TRADITION!"""

    system_prompt = f"""You are an expert Islamic content researcher for viral Bengali YouTube Shorts and Reels.
Generate ONE highly engaging, deeply emotional Islamic topic in Bangla (বাংলা) for this specific pillar:

PILLAR: {pillar['label']}
FOCUS: {pillar['description']}

Rules:
- Backed strictly by authentic Quran verses or Sahih Hadith only
- Emotionally gripping, high-CTR Bengali title (max 12 words)
- 100% unique core concept — MUST NOT be a thematic clone of any recently covered topic
{avoid_section}

Output ONLY valid JSON:
{{
    "title": "...",
    "core_concept": "Brief explanation of the specific unique Hadith/story covered",
    "category": "{pillar['category']}",
    "score": 99.0
}}"""

    user_prompt = f"Generate ONE unique, never-before-covered Bengali Islamic Short topic for the '{pillar['label']}' pillar. Ensure zero conceptual overlap with the recent topics list."

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=400)
        if data and "title" in data:
            data["category"] = pillar["category"]  # Enforce correct category
            logger.info(f"Generated fresh concept: '{data.get('core_concept', 'N/A')}' -> Title: '{data['title']}'")
            return data
    except Exception as e:
        logger.error(f"Error generating topic for pillar '{pillar['label']}': {e}")
    return None


def run_discovery():
    conn = get_connection()
    cursor = conn.cursor()

    # Step 1: Determine which pillar is next in rotation
    pillar = _get_next_pillar(cursor)
    logger.info(f"Selected content category: {pillar['label'].upper()}")

    # Step 2: Check if we already have an unused DISCOVERED topic for this pillar
    try:
        cursor.execute(
            "SELECT id, title, score, source FROM topics WHERE status = 'DISCOVERED' AND source LIKE ? ORDER BY score DESC LIMIT 1",
            (f"%({pillar['category']}%",)
        )
        existing = cursor.fetchone()
        if existing:
            logger.info(f"Using existing queued topic for '{pillar['category']}': {existing['title']}")
            cursor.execute("UPDATE topics SET status = 'IN_PROGRESS' WHERE id = ?", (existing["id"],))
            conn.commit()
            conn.close()
            return {
                "id": existing["id"],
                "title": existing["title"],
                "score": existing["score"],
                "category": pillar["category"]
            }
    except Exception:
        pass

    # Step 3: Fetch recent titles (last 40 days) for anti-repetition
    try:
        cursor.execute(
            "SELECT title FROM topics WHERE status IN ('IN_PROGRESS', 'DONE', 'DISCOVERED') AND created_at >= datetime('now', '-40 days') ORDER BY id DESC"
        )
        recent_titles = [row["title"] for row in cursor.fetchall()]
    except Exception:
        recent_titles = []

    # Step 4: Ask Gemini for a fresh topic for this pillar
    topic_data = generate_topic_for_pillar(pillar, recent_titles)

    if not topic_data:
        logger.warning(f"Gemini failed for pillar '{pillar['label']}'. Using fallback.")
        fallbacks = {
            "daily_life":        {"title": "নামাজে মনোযোগ ধরে রাখার কার্যকর আমল", "score": 97.0},
            "dua_cures":         {"title": "ইউনুস (আ.)-এর দোয়া: ঘোর বিপদ থেকে মুক্তির পথ", "score": 97.0},
            "heart_softeners":   {"title": "আল্লাহর ভালোবাসা পাওয়ার সহজ ৩টি আমল", "score": 97.0},
            "islamic_knowledge": {"title": "কিয়ামতের দিন নবীজির শাফাআত কারা পাবেন?", "score": 97.0},
        }
        topic_data = fallbacks.get(pillar["category"], fallbacks["daily_life"])
        topic_data["category"] = pillar["category"]

    # Step 5: Save to DB
    title = topic_data["title"]
    score = topic_data.get("score", 97.0)
    cat = pillar["category"]

    try:
        cursor.execute(
            "INSERT INTO topics (title, source, score, status) VALUES (?, ?, ?, 'IN_PROGRESS')",
            (title, f"Gemini AI Discovery ({cat})", score)
        )
        conn.commit()
        topic_id = cursor.fetchone()  # May not return on all DB backends

        # Get the ID of the just-inserted row
        cursor.execute("SELECT id FROM topics WHERE title = ? ORDER BY id DESC LIMIT 1", (title,))
        row = cursor.fetchone()
        topic_id = row["id"] if row else None
    except Exception as e:
        logger.warning(f"Topic may already exist or insert failed: {e}")
        cursor.execute("SELECT id FROM topics WHERE title = ? LIMIT 1", (title,))
        row = cursor.fetchone()
        if row:
            topic_id = row["id"]
            cursor.execute("UPDATE topics SET status = 'IN_PROGRESS' WHERE id = ?", (topic_id,))
            conn.commit()
        else:
            conn.close()
            return None

    conn.commit()
    conn.close()

    logger.info(f"Selected topic for production: {title} (ID: {topic_id})")
    return {
        "id": topic_id,
        "title": title,
        "score": score,
        "category": cat
    }
