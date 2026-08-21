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
Every script MUST begin with a gripping real-life hook (either a curiosity question 'আপনি কি জানেন...?' OR a deeply relatable real-life scenario) anchored directly in specific everyday Bengali life situations and practical solutions.

MASTER REAL-LIFE ANCHORS BY CATEGORY (LOCKED & PREFERRED):
- Marriage & Family (দাম্পত্য ও পরিবার) → "সারাদিনের ক্লান্তির পর ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়া কিংবা হাসিমুখে কথা বলাও যে সদকা — আমরা অনেকেই এই সুন্নাহটি ভুলে যাই!..."
- Rizq & Debt (রিজিক ও অভাব) → "মাসের শেষে টানাটানি, ঋণের বোঝা আর সংসার খরচের চিন্তায় রাতে ঘুম আসছে না? নবীজি (সা.) ঠিক এই কঠিন সময়ের জন্য একটি দোয়া শিখিয়েছেন..."
- Evil Eye & Ruqyah (বদনজর ও অশান্তি) → "হঠাৎ করে অকারণে সংসারে অশান্তি, প্রিয়জনের ওপর কথায় কথায় রাগ আর কাজে মন না বসা — এটি অনেক সময় বদনজরের মারাত্মক লক্ষণ হতে পারে!..."
- Misconceptions (হালাল/হারাম ভ্রান্তি) → "আপনি কি জানেন, স্পষ্ট দলিল ছাড়া কোনো হালাল কাজকে হারাম বা অশুভ মনে করা কত বড় গুনাহ? যেমন—রাতে নখ কাটা, সন্ধ্যায় ঘর ঝাড়ু দেওয়া কিংবা বিড়াল ছুঁলে অপবিত্র মনে করা!"
- Sleep & Night Sunnah (ঘুম ও স্বপ্ন) → "প্রতি রাতে ঘুমানোর পূর্বে ছোট্ট একটি আমল করলে কবরের সমস্ত আজাব থেকে চিরমুক্তি মিলবে..."
- Forgiveness & Repentance (তওবা ও ক্ষমা) → "বারবার একই গুনাহ হয়ে যাওয়ার পরও আল্লাহর রহমত আপনার কত নিকটে?..."

SCENE-BY-SCENE STRUCTURE:

1. SCENE 1 (THE HOOK & REAL-LIFE SITUATION — 0-5s):
   - Hook the viewer instantly using the exact natural, emotional everyday tone shown above.
   - Anchor directly in a tangible reality (home, spouse, debt, sleep, anxiety, evil eye, superstitions).

2. SCENE 2 (AUTHENTIC DIVINE EVIDENCE & RECITATION — 5-15s):
   - Directly connect the hook & situation to the authentic Quran Ayah, Hadith, or Dua.
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
    "hook_category": "daily_life_example",
    "reference": "সহীহ বুখারী: ৫৬৭৮, সহীহ মুসলিম: ১২৩৪",
    "narration_full_bn": "full narration here with <ARABIC> tags",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "হঠাৎ করে অকারণে সংসারে অশান্তি, প্রিয়জনের ওপর কথায় কথায় রাগ আর কাজে মন না বসা — এটি অনেক সময় বদনজরের মারাত্মক লক্ষণ হতে পারে!...",
            "visuals": "serene atmospheric traditional home window under warm evening twilight, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 2,
            "narration": "নবীজি (সা.) এই অবস্থায় আশ্রয় চাইতে নির্দেশ দিয়েছেন: <ARABIC>arabic text here\n(উচ্চারণ)\n(অর্থ)</ARABIC>",
            "visuals": "vast calm desert oasis at twilight under glowing crescent moon, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 3,
            "narration": "তাই প্রতিদিন সকাল-সন্ধ্যায় এই পবিত্র দোয়াটি পাঠ করুন এবং ঘরের ভেতরে বরকত ফিরিয়ে আনুন।",
            "visuals": "majestic ancient library with antique leather manuscripts and glowing warm lantern, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে লিখুন: <ARABIC>أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ\n(আউযু বিল্লাহি মিনাশ শাইতানির রাজিম)</ARABIC>",
            "visuals": "warm glowing brass moroccan lantern on carved stone, peaceful dusk ambience, photorealistic 8k, vertical 9:16, no humans"
        }
    ]
}
"""

    user_prompt = f"Generate a highly engaging, viral 30-second Islamic video script in 100% Bangla with authentic Arabic in <ARABIC> tags. Scene 1 MUST start with a gripping real-life situation/example, and Scene 3 MUST give a practical solution. Topic: {topic_title or 'Islamic Reminders'}. Category: {category}. NO ENGLISH WORDS."
    
    script_data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not script_data or "scenes" not in script_data:
        logger.error("Failed to generate script.")
        return None
        
    return script_data
