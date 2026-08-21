# -*- coding: utf-8 -*-
import random
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_script(topic_id: int = None, topic_title: str = None, video_format: str = "short", duration_sec: int = 30, category: str = "islamic_knowledge", series_info: dict = None) -> dict:
    """
    Generates authentic Bengali Islamic short video scripts with Dual-Voice <ARABIC> tagging and Bangla-only subtitle formatting.
    """
    logger.info(f"Generating 100% Bengali & Arabic Islamic Short video script...")
    
    system_prompt = """You are an expert Islamic content creator crafting viral, deeply engaging 30-second Islamic Shorts/Reels for Bengali-speaking audiences.

THE WINNING VIRAL SCRIPT FORMULA:
Every script MUST begin with a high-curiosity question hook (like 'আপনি কি জানেন...?' / 'আপনি কি জানেন, স্পষ্ট দলিল ছাড়া কোনো হালাল কাজকে হারাম মনে করা কত বড় গুনাহ?...') combined with specific, concrete daily-life examples and practical solutions.

SCENE-BY-SCENE STRUCTURE:

1. SCENE 1 (POWERFUL QUESTION HOOK + CONCRETE REAL-LIFE EXAMPLES — 0-5s):
   - ALWAYS start with an engaging, curiosity-sparking question (e.g. 'আপনি কি জানেন...?') and immediately follow with 1-2 recognizable real-world examples from everyday Bengali life.
   - Master Examples by Category:
     * Misconceptions (হালাল/হারাম ভ্রান্তি) → "আপনি কি জানেন, স্পষ্ট দলিল ছাড়া কোনো হালাল কাজকে হারাম মনে করা কত বড় গুনাহ? যেমন—রাতে নখ কাটা, সন্ধ্যায় ঘর ঝাড়ু দেওয়া কিংবা বিড়াল ছুঁলে অপবিত্র মনে করা!"
     * Marriage & Family (দাম্পত্য ও পরিবার) → "আপনি কি জানেন, ঘরের ছোট্ট একটি কাজেই কত বিপুল সওয়াব রয়েছে? যেমন—সারাদিনের ক্লান্তির পর ভালোবেসে স্ত্রীর মুখে খাবার তুলে দেওয়াও একটি সদকা!"
     * Rizq & Barakah (রিজিক ও অভাব) → "আপনি কি জানেন, অভাবের দিনে রিজিক ও বরকত বৃদ্ধির সবচেয়ে শক্তিশালী আমল কোনটি? মাসের শেষে ঋণের দুশ্চিন্তায় রাতের ঘুম নষ্ট না করে এই আমলটি করুন..."
     * Evil Eye & Ruqyah (বদনজর ও অশান্তি) → "আপনি কি জানেন, অকারণে পরিবারে অশান্তি কিংবা কথায় কথায় মেজাজ খিটখিটে হওয়া প্রায়ই বদনজরের লক্ষণ হতে পারে?..."
     * Sleep & Night Sunnah (ঘুম ও স্বপ্ন) → "আপনি কি জানেন, প্রতি রাতে ঘুমানোর পূর্বে ছোট্ট একটি আমল করলে কবরের সমস্ত আজাব থেকে চিরমুক্তি মিলবে?..."
     * Forgiveness & Repentance (তওবা ও ক্ষমা) → "আপনি কি জানেন, বারবার গুনাহ হয়ে যাওয়ার পরও আল্লাহর রহমত আপনার কত নিকটে?..."

2. SCENE 2 (AUTHENTIC DIVINE EVIDENCE & RECITATION — 5-15s):
   - Directly connect the hook & example to the authentic Quran Ayah, Hadith, or Dua.
   - Put Arabic text, pronunciation, and exact translation inside <ARABIC> tags:
     <ARABIC>
     Pure Arabic with Tashkeel
     (বাংলা উচ্চারণ)
     (১০০% নির্ভুল ও প্রামাণিক বাংলা অর্থ)
     </ARABIC>

3. SCENE 3 (PRACTICAL DAILY-LIFE ACTION / SOLUTION — 15-25s):
   - Give the viewer an immediate, actionable step they can practice in their daily routine right now:
     * e.g., "তাই ভিত্তিহীন কুসংস্কারে কান না দিয়ে সহীহ সুন্নাহ জানুন এবং আজ থেকেই নিজের দৈনন্দিন জীবনে এই আমলটি শুরু করুন।"

4. SCENE 4 (CLOSING DHIKR CTA — 25-30s):
   - End ONLY with an interactive CTA asking viewers to comment a specific Arabic Dhikr:
     * e.g., কমেন্টে লিখুন: <ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>
     * (NO asking for likes, NO asking for shares/follows).

OUTPUT FORMAT — Respond with ONLY valid JSON (no markdown fences), 100% BANGLA & ARABIC, NO ENGLISH:
{
    "title": "ভিডিওর বাংলা শিরোনাম",
    "title_bn": "ভিডিওর বাংলা শিরোনাম",
    "topic": "বাংলা বিষয়ের নাম",
    "hook_category": "question_hook_with_daily_example",
    "reference": "সহীহ বুখারী: ৫৬৭৮, সহীহ মুসলিম: ১২৩৪",
    "narration_full_bn": "full narration here with <ARABIC> tags",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "আপনি কি জানেন, স্পষ্ট দলিল ছাড়া কোনো হালাল কাজকে হারাম মনে করা কত বড় গুনাহ? যেমন—রাতে নখ কাটা, কিংবা বিড়াল ছুঁলে অপবিত্র মনে করা!...",
            "visuals": "serene atmospheric traditional home window under warm evening twilight, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 2,
            "narration": "অথচ মহান আল্লাহ স্পষ্ট ভাষায় নিষেধ করেছেন: <ARABIC>arabic text here\n(উচ্চারণ)\n(অর্থ)</ARABIC>",
            "visuals": "vast calm desert oasis at twilight under glowing crescent moon, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 3,
            "narration": "তাই সমাজে প্রচলিত ভিত্তিহীন কুসংস্কারে কান না দিয়ে সহীহ সুন্নাহ জানুন এবং নিজের জীবনকে সহজ ও বরকতময় রাখুন।",
            "visuals": "majestic ancient library with antique leather manuscripts and glowing warm lantern, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে লিখুন: <ARABIC>أَسْتَغْفِرُ اللَّهَ\n(আস্তাগফিরুল্লাহ)</ARABIC>",
            "visuals": "warm glowing brass moroccan lantern on carved stone, peaceful dusk ambience, photorealistic 8k, vertical 9:16, no humans"
        }
    ]
}
"""

    user_prompt = f"Generate a highly engaging, viral 30-second Islamic video script in 100% Bangla with authentic Arabic in <ARABIC> tags. Scene 1 MUST start with an engaging 'আপনি কি জানেন...?' style question hook combined with specific real-life daily examples, and Scene 3 MUST give a practical solution. Topic: {topic_title or 'Islamic Reminders'}. Category: {category}. NO ENGLISH WORDS."
    
    script_data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not script_data or "scenes" not in script_data:
        logger.error("Failed to generate script.")
        return None
        
    return script_data
