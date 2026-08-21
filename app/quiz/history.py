import os
import json
import time
import urllib.request
import urllib.error
from app.logger import logger
from app.history import _get_supabase_config

LOCAL_QUIZ_HISTORY_FILE = "data/used_quiz_questions.json"

def fetch_used_quiz_questions(limit: int = 50) -> list[str]:
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
    Generates high-converting, SEO-optimized metadata for the Quiz video
    including all 5 questions, correct answers, and Sahih references.
    """
    raw_title = quiz_script.get("title", "ইসলামিক জ্ঞান কুইজ ☪️ (৫-এ আপনার স্কোর কত?)")
    if "#Shorts" not in raw_title and "#shorts" not in raw_title:
        yt_title = f"{raw_title} #Shorts"
    else:
        yt_title = raw_title
        
    hook_text = quiz_script.get("hook", {}).get("headline", "আপনার ইসলামিক জ্ঞান যাচাই করুন!")
    
    desc = f"{hook_text} কুইজের ৫টি প্রশ্নের সঠিক উত্তর দিতে পেরেছেন কি? আপনার দ্বীনি জ্ঞান বৃদ্ধি করতে পুরো ভিডিওটি দেখুন এবং কমেন্টে আপনার স্কোর জানান।\n\n"
    desc += "✨ কুইজের ৫টি প্রশ্ন, সঠিক উত্তর ও সহীহ রেফারেন্স:\n"
    
    bn_nums = {1: "১", 2: "২", 3: "৩", 4: "৪", 5: "৫"}
    for q in quiz_script.get("questions", []):
        q_n = bn_nums.get(q.get("number", 1), str(q.get("number", 1)))
        q_txt = q.get("question", "").strip()
        c_opt = q.get("correct_option", "").strip()
        expl = q.get("explanation", "").strip()
        desc += f"{q_n}. {q_txt}\n   👉 সঠিক উত্তর: {c_opt}\n   📖 তথ্যসূত্র: {expl}\n\n"
        
    desc += "💬 আজকের স্কোর:\nআপনার স্কোর ৫-এ কত হলো? কমেন্টে অবশ্যই জানান!\n\n"
    desc += "━━━━━━━━━━━━━━━━━━━━\n📌 আমাদের সাথে যুক্ত থাকুন:\n🔹 YouTube: https://www.youtube.com/@dailydos-no1\n🔹 Facebook: https://www.facebook.com/DailyDosNo1\n\n"
    desc += "#Shorts #IslamicQuiz #MuslimQuiz #TestYourKnowledge #BanglaIslamic #ইসলামিকপোস্ট #DailyDos #ReelsViral #ShortsFeed #সহীহ_হাদিস #LearnIslam"
    
    return {
        "youtube_title": yt_title[:100],
        "facebook_title": raw_title,
        "description": desc.strip(),
        "pinned_comment": "আজকের কুইজে আপনার স্কোর ৫-এ কত হলো? ৫/৫, ৪/৫ নাকি ৩/৫? কমেন্টে জানান! 👇",
        "english_title": "Islamic Knowledge Quiz: Test Your Deen #Shorts",
        "english_description": "Interactive 5-question Islamic quiz on core pillars, worship, prophets, Quran, and Sahih Hadith. Test your knowledge and share your score in the comments.",
        "tags": ["Shorts", "IslamicQuiz", "MuslimQuiz", "TestYourKnowledge", "BanglaIslamic", "ইসলামিকপোস্ট", "DailyDos", "ReelsViral", "ShortsFeed", "সহীহ_হাদিস", "LearnIslam", "ExplorePage"],
        "category": "educational"
    }
