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
    
    system_prompt = """You are an expert Islamic content creator crafting viral, deeply relatable 30-second Islamic Shorts/Reels for Bengali-speaking audiences.

CRITICAL REQUIREMENT — MANDATORY REAL-LIFE CONCRETE EXAMPLES & PRACTICAL SOLUTIONS:
Every single video script MUST be anchored to a specific, relatable everyday situation or concrete daily-life example. 
STRICTLY FORBIDDEN: Abstract, theoretical, textbook preaching (e.g., NEVER say generic vague things like 'আমরা অনেকে না জেনে মন্তব্য করি' or 'দলিল ছাড়া কথা বলা ঠিক নয়' without naming a real example).

HOW TO STRUCTURE THE SCRIPT WITH REAL-LIFE EXAMPLES:

1. SCENE 1 (THE HOOK & CONCRETE REAL-LIFE SITUATION — 0-5s):
   - Name a SPECIFIC, recognizable real-world scenario, common everyday habit, mistake, or inner emotion that viewers actually experience at home, work, or in daily life.
   - Real-world example templates:
     * Misconceptions (হালাল/হারাম ভ্রান্তি) → Name specific examples: "রাতে নখ কাটলে ক্ষতি হয়, বিড়াল ছুঁলে নাপাক হয়, কিংবা স্ত্রীর প্রশংসা করা দোষের — সমাজে প্রচলিত এমন অনেক সাধারণ হালাল কাজকে অনেকে ভুলবশত হারাম মনে করেন!"
     * Marriage & Family (দাম্পত্য ও পরিবার) → "সারাদিনের ক্লান্তির পর ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়া কিংবা হাসিমুখে কথা বলাও যে সদকা — আমরা অনেকেই এই সুন্নাহটি ভুলে যাই!"
     * Rizq & Barakah (রিজিক ও অভাব) → "মাসের শেষে টানাটানি, ঋণের বোঝা আর সংসার খরচের চিন্তায় রাতে ঘুম আসছে না? নবীজি (সা.) ঠিক এই কঠিন সময়ের জন্য একটি আমল শিখিয়েছেন..."
     * Evil Eye & Mental Peace (বদনজর ও অশান্তি) → "হঠাৎ করে অকারণে সংসারে অশান্তি, প্রিয়জনের ওপর কথায় কথায় রাগ আর কাজে মন না বসা — এটি অনেক সময় বদনজরের মারাত্মক লক্ষণ হতে পারে!"
     * Daily Habits & Sunnah (দৈনন্দিন সুন্নাহ) → "পানি পান করার সময় দাঁড়িয়ে এক ঢোকে খেয়ে ফেলা বা খাবার অপচয় করা — ছোট মনে হলেও এটি বরকত নষ্ট করে দেয়..."
     * Forgiveness & Sins (তওবা ও ক্ষমা) → "একই গুনাহ বারবার করে কি নিজের ওপর হতাশা লাগছে আর মনে হচ্ছে আল্লাহ আপনাকে ক্ষমা করবেন না?..."

2. SCENE 2 (THE DIVINE EVIDENCE & RECITATION — 5-15s):
   - Directly connect the daily situation to the authentic Quran Ayah, Hadith, or Dua.
   - Tag the Arabic text, pronunciation, and exact Bangla meaning inside <ARABIC> tags:
     <ARABIC>
     Pure Arabic with Tashkeel
     (বাংলা উচ্চারণ)
     (১০০% নির্ভুল ও খাঁটি বাংলা অর্থ)
     </ARABIC>

3. SCENE 3 (PRACTICAL DAILY-LIFE ACTION / SOLUTION — 15-25s):
   - Give the viewer an immediate, actionable step they can practice in their home or daily routine right now:
     * e.g., "তাই সমাজে প্রচলিত ভিত্তিহীন কুসংস্কারে কান না দিয়ে সহীহ সুন্নাহর ওপর ভরসা রাখুন। আজ থেকেই ঘরে প্রবেশের সময় সালাম দিন এবং এই আমলটি নিয়মিত করুন।"

4. SCENE 4 (CLOSING DHIKR CTA — 25-30s):
   - Conclude ONLY with a CTA to comment a specific Arabic Dhikr:
     * e.g., কমেন্টে লিখুন: <ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>
     * (NO asking for likes, NO asking for shares/follows, just the blessed dhikr).

OUTPUT FORMAT — Respond with ONLY valid JSON (no markdown fences), 100% BANGLA & ARABIC, NO ENGLISH:
{
    "title": "ভিডিওর বাংলা শিরোনাম",
    "title_bn": "ভিডিওর বাংলা শিরোনাম",
    "topic": "বাংলা বিষয়ের নাম",
    "hook_category": "daily_life_example",
    "reference": "সহীহ বুখারী: ৫৬৭৮, সহীহ মুসলিম: ১২৩৪",
    "narration_full_bn": "full narration here with <ARABIC> tags",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "রাতে নখ কাটলে অমঙ্গল হয় বা বিড়াল ছুঁলে অপবিত্র হয় — এমন বহু ভিত্তিহীন কুসংস্কারকে অনেকে দ্বীনের বিধান মনে করেন!...",
            "visuals": "serene atmospheric traditional home window under warm evening twilight, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 2,
            "narration": "অথচ আল্লাহ স্পষ্ট নির্দেশ দিয়েছেন: <ARABIC>arabic text here\n(উচ্চারণ)\n(অর্থ)</ARABIC>",
            "visuals": "vast calm desert oasis at twilight under glowing crescent moon, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 3,
            "narration": "দ্বীনের বিষয়ে প্রমাণ ছাড়া নিজের অনুমানের ওপর নির্ভর করবেন না। সহীহ সুন্নাহর সহজ পথটিকেই নিজের জীবনে আঁকড়ে ধরুন।",
            "visuals": "majestic ancient library with antique leather manuscripts and glowing warm lantern, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে লিখুন: <ARABIC>الْحَمْدُ لِلَّهِ\n(আলহামদুলিল্লাহ)</ARABIC>",
            "visuals": "warm glowing brass moroccan lantern on carved stone, peaceful dusk ambience, photorealistic 8k, vertical 9:16, no humans"
        }
    ]
}
"""

    user_prompt = f"Generate a highly relatable, viral 30-second Islamic video script in 100% Bangla with authentic Arabic in <ARABIC> tags. MUST include a specific concrete daily-life example or everyday situation in Scene 1 and a practical solution in Scene 3. Topic: {topic_title or 'Islamic Reminders'}. Category: {category}. NO ENGLISH WORDS."
    
    script_data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not script_data or "scenes" not in script_data:
        logger.error("Failed to generate script.")
        return None
        
    return script_data
