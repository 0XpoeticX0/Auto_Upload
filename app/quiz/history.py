import os
import json
import time
import urllib.request
import urllib.error
from app.logger import logger
from app.history import _get_supabase_config

LOCAL_QUIZ_HISTORY_FILE = "data/used_quiz_questions.json"

def fetch_used_quiz_questions(limit: int = 100) -> list[str]:
    """
    Fetches recent quiz questions from Supabase `used_quiz_questions` table
    (with local JSON cache fallback) to ensure zero question repetition across runs.
    """
    questions = []
    
    # 1. Fetch from Supabase
    try:
        url, key = _get_supabase_config()
        if url and key:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            req = urllib.request.Request(
                f"{url}/used_quiz_questions?select=question_text&order=id.desc&limit={limit}",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read().decode("utf-8"))
                    for r in rows:
                        qt = r.get("question_text")
                        if qt and qt not in questions:
                            questions.append(qt.strip())
                    logger.info(f"Loaded {len(questions)} previous quiz questions from Supabase.")
    except Exception as e:
        logger.warning(f"Supabase fetch quiz questions notice: {e}")
        
    # 2. Merge local cache
    if os.path.exists(LOCAL_QUIZ_HISTORY_FILE):
        try:
            with open(LOCAL_QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                local_list = json.load(f)
                for q in local_list:
                    if isinstance(q, str) and q not in questions:
                        questions.append(q.strip())
                    elif isinstance(q, dict) and q.get("question") and q["question"] not in questions:
                        questions.append(q["question"].strip())
        except Exception:
            pass
            
    return questions[:limit]

def record_used_quiz_questions(quiz_script: dict, video_id: int | None = None) -> bool:
    """
    Records all 5 questions from the quiz script to Supabase `used_quiz_questions`
    and updates the local cache file.
    """
    questions = quiz_script.get("questions", [])
    if not questions:
        return False
        
    vid_id = video_id or int(time.time())
    url, key = _get_supabase_config()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    } if url and key else None
    
    # 1. Insert into Supabase
    if headers:
        for q in questions:
            q_text = q.get("question", "").strip()
            topic = q.get("category", "ইসলামিক জ্ঞান").strip()
            if not q_text:
                continue
            payload = json.dumps({
                "video_id": vid_id,
                "question_text": q_text,
                "topic_tag": topic
            }).encode("utf-8")
            try:
                req = urllib.request.Request(f"{url}/used_quiz_questions", data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    pass
            except Exception as e:
                logger.warning(f"Failed to record quiz question to Supabase: {e}")
                
    # 2. Update local JSON
    os.makedirs("data", exist_ok=True)
    local_data = []
    if os.path.exists(LOCAL_QUIZ_HISTORY_FILE):
        try:
            with open(LOCAL_QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except Exception:
            local_data = []
            
    for q in questions:
        q_text = q.get("question", "").strip()
        if q_text and q_text not in local_data:
            local_data.append(q_text)
            
    try:
        with open(LOCAL_QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(local_data[-100:], f, indent=2, ensure_ascii=False)
        logger.info(f"Recorded 5 quiz questions to database history log.")
        return True
    except Exception as e:
        logger.warning(f"Failed to write local quiz history: {e}")
        return False

def format_quiz_metadata(quiz_script: dict) -> dict:
    """
    Generates high-converting, SEO-optimized metadata for the 3-Question Quiz video
    including dynamic pinned comments and score challenge copy.
    """
    raw_title = quiz_script.get("title", "৯৯% মানুষ ৩ নম্বর প্রশ্নে আটকে যায়! 🧠 (৩-এ আপনার স্কোর কত?)")
    if "#Shorts" not in raw_title and "#shorts" not in raw_title:
        yt_title = f"{raw_title} #Shorts"
    else:
        yt_title = raw_title
        
    hook_text = quiz_script.get("hook", {}).get("headline", "৯৯% মানুষ ২ ও ৩ নম্বর প্রশ্নে আটকে যায়! 🧠")
    outro_pinned = quiz_script.get("outro", {}).get("pinned_comment", "৩/৩ কার কার হয়েছে? কমেন্টে 'মাশাআল্লাহ' লিখুন! 👇 আর ২ নম্বর প্রশ্নের উত্তর আপনি কি আগে জানতেন?")
    
    desc = f"{raw_title}\n\nআপনার ইসলামিক জ্ঞান কতটা মজবুত? ☪️\n৩টি আকর্ষণীয় প্রশ্নের উত্তর দিয়ে নিজের স্কোর যাচাই করুন!\n\n💡 কতগুলো সঠিক হলো? সততার সাথে কমেন্টে আপনার স্কোর (৩/৩, ২/৩) জানান! 👇\n\n"
    desc += "✨ In English:\nInteractive 3-Question Islamic Quiz. Test your knowledge on core pillars, common misconceptions, prophets, and Quran secrets. Share your score in the comments!\n\n"
    desc += "━━━━━━━━━━━━━━━━━━━━\n📌 আমাদের সাথে যুক্ত থাকুন:\n🔹 YouTube: https://www.youtube.com/@dailydos-no1\n🔹 Facebook: https://www.facebook.com/DailyDosNo1\n\n"
    desc += "#IslamicQuiz #BanglaIslamic #DailyDos #MuslimQuiz #ইসলামিককুইজ #Shorts #ReelsViral #ExplorePage"
    
    return {
        "youtube_title": yt_title[:100],
        "facebook_title": raw_title,
        "description": desc.strip(),
        "pinned_comment": outro_pinned,
        "english_title": "Islamic Knowledge Quiz: 99% Fail Q3! Can You Score 3/3? #Shorts",
        "english_description": "Interactive 3-question Islamic quiz on daily worship, common misconceptions, and Quran secrets. Test your knowledge and share your score in the comments.",
        "tags": ["Shorts", "IslamicQuiz", "MuslimQuiz", "TestYourKnowledge", "BanglaIslamic", "ইসলামিককুইজ", "DailyDos", "ReelsViral", "ShortsFeed", "সহীহ_হাদিস", "LearnIslam", "ExplorePage"],
        "category": "educational"
    }
