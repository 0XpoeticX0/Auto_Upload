import sqlite3
import random
import json
from app.logger import logger
from app.database import get_connection
from app.llm.provider import extract_json

def generate_islamic_topics(recent_titles=None):
    system_prompt = """You are an expert Islamic content researcher for viral Bengali YouTube Shorts and Reels.
Your goal is to generate 4 highly engaging, deeply emotional Islamic topic ideas in Bangla (বাংলা) based purely on authentic Quran and Sahih Hadith.

Generate ONE topic for each of these 4 pillars:
1. দৈনন্দিন জীবন: প্রতিদিনের জীবনে হালাল ও হারাম, জবান হেফাজত, লেনদেন
2. দোয়া ও নিরাময়: মানসিক অস্থিরতা, দুশ্চিন্তা ও বিপদ থেকে মুক্তির সহীহ দোয়া
3. অন্তর গলানো নসিহত: তওবা, আল্লাহর সীমাহীন রহমত, গুনাহ মাফের উপায়
4. শেষ যামানা ও আখিরাত: মৃত্যুর পরবর্তী জীবন, কিয়ামতের আলামত, কবরের শান্তি

Output JSON format (ONLY valid JSON):
{
    "topics": [
        {"title": "হতাশা ও দুশ্চিন্তা দূর করার সেরা দোয়া", "category": "dua_cures", "score": 99.5},
        {"title": "আল্লাহর দরবারে সবচেয়ে প্রিয় দুটি সহজ বাক্য", "category": "heart_softeners", "score": 98.0},
        {"title": "কথা বলার আগে ভাবুন: ঈমানদারের বিশেষ গুণ", "category": "daily_life", "score": 97.5},
        {"title": "শেষ যামানার ভয়ংকর আলামত ও ঈমানের হেফাজত", "category": "islamic_knowledge", "score": 99.0}
    ]
}"""

    user_prompt = "Generate 4 fresh, authentic Bengali Islamic Short topics covering the 4 pillars."
    
    if recent_titles:
        user_prompt += "\n\nCRITICAL RULE - DO NOT use or repeat any of these recently covered topics:\n"
        for t in recent_titles:
            user_prompt += f"- {t}\n"

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
    
    try:
        cursor.execute("SELECT title FROM topics ORDER BY id DESC LIMIT 20")
        recent_titles = [row["title"] for row in cursor.fetchall()]
    except Exception as e:
        recent_titles = []
    
    topics = generate_islamic_topics(recent_titles)
    
    if not topics:
        logger.warning("No topics generated. Using fallback topics in Bangla.")
        topics = [
            {"title": "আল্লাহর দরবারে সবচেয়ে প্রিয় দুটি সহজ বাক্য", "category": "heart_softeners", "score": 98.0},
            {"title": "হতাশা ও মানসিক কষ্ট দূর করার কার্যকরী দোয়া", "category": "dua_cures", "score": 99.0},
            {"title": "তওবার দরজা কখন বন্ধ হয়ে যাবে?", "category": "islamic_knowledge", "score": 97.0},
            {"title": "মানুষের সাথে উত্তম আচরণের অপার সওয়াব", "category": "daily_life", "score": 96.0}
        ]
        
    for t in topics:
        title = t.get("title", "")
        score = t.get("score", 90.0)
        try:
            cursor.execute(
                "INSERT INTO topics (title, source, score, status) VALUES (?, ?, ?, 'DISCOVERED')",
                (title, "Gemini AI Discovery", score)
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
