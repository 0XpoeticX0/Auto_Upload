import sqlite3
import random
import json
from app.logger import logger
from app.database import get_connection
from app.llm.provider import extract_json

def generate_islamic_topics(recent_titles=None):
    system_prompt = """You are an expert Islamic content researcher for YouTube Shorts.
Your goal is to generate exactly 4 highly viral, extremely engaging topic ideas based purely on authentic Islamic knowledge (Quran and Sahih Sunnah).
Do not use weak Hadiths. 

You MUST generate exactly ONE topic for each of the following 4 categories, in this exact order:
1. Daily Life: What is Halal and Haram in modern daily life (very important).
2. Duas & Cures: Powerful Duas for forgiveness, curing sadness/disease, and success.
3. Heart Softeners: Fear of Allah (Taqwa), repenting from Haram, and the Mercy of Allah.
4. General Islamic Knowledge: End of times, unseen world, miracles, or stories of prophets.

Make sure the title clearly hints at which of the 4 categories it belongs to so people can easily find it!

Output JSON format:
{
    "topics": [
        {"title": "Ultra-short curiosity title (3-5 words)", "score": 99.5},
        ... (exactly 4 total)
    ]
}"""

    user_prompt = "Generate exactly 4 new, highly engaging Islamic topics. You must provide exactly one topic for Category 1, one for Category 2, one for Category 3, and one for Category 4."
    
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
        logger.warning("No topics generated. Using fallback.")
        topics = [
            {"title": "The terrifying sign of Qiyamah happening right now", "score": 95.0},
            {"title": "What happens to your soul when you sleep?", "score": 90.0}
        ]

    
    saved_count = 0
    for topic in topics:
        try:
            cursor.execute('''
                INSERT INTO topics (title, source, score, status)
                VALUES (?, ?, ?, 'DISCOVERED')
            ''', (topic["title"], "AI_GENERATED", topic.get("score", 50.0)))
            saved_count += 1
        except sqlite3.IntegrityError:
            pass
            
    conn.commit()
    logger.info(f"Saved {saved_count} new topics to database.")
    
    cursor.execute('''
        SELECT * FROM topics 
        WHERE status = 'DISCOVERED' 
        ORDER BY id ASC 
        LIMIT 1
    ''')
    best_topic = cursor.fetchone()
    
    if not best_topic:
        logger.warning("Topic pool exhausted. Recycling old topics...")
        cursor.execute("UPDATE topics SET status = 'DISCOVERED' WHERE status IN ('RESEARCHING', 'SCRIPTING', 'DONE')")
        conn.commit()
        cursor.execute('''
            SELECT * FROM topics 
            WHERE status = 'DISCOVERED' 
            ORDER BY id ASC 
            LIMIT 1
        ''')
        best_topic = cursor.fetchone()
    
    if best_topic:
        cursor.execute("UPDATE topics SET status = 'RESEARCHING' WHERE id = ?", (best_topic["id"],))
        conn.commit()
        conn.close()
        
        logger.info(f"Selected topic: {best_topic['title']}")
        topic_dict = dict(best_topic)
        topic_dict["category"] = category
            
        return topic_dict
    
    conn.close()
    return None
