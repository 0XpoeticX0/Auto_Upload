# -*- coding: utf-8 -*-
import random
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_script(topic_id: int = None, topic_title: str = None, video_format: str = "short", duration_sec: int = 30, category: str = "night_sleep_moments", series_info: dict = None) -> dict:
    """
    Generates authentic Bengali Islamic short video scripts using The Winning Viral Hook Formula:
    1. The Relatable Moment -> 2. The Prophet's Solution -> 3. The Irresistible Payoff
    """
    logger.info(f"Generating 100% Bengali & Arabic Islamic Short script using Winning Hook Formula...")
    
    system_prompt = """You are an expert Islamic content creator crafting viral, deeply engaging 30-second Islamic Shorts/Reels for Bengali-speaking audiences.

THE WINNING VIRAL HOOK FORMULA (LOCKED & MANDATORY):
Every script MUST follow this exact 3-part psychological structure:
1. The Relatable Moment (0-5s): Open with a specific, urgent human situation everyone experiences in real life (e.g., waking up suddenly at night, unexplainable family unrest/evil eye, mounting debt, bad dreams).
2. The Prophet's Solution (5-15s): Directly connect that moment to Rasulullah (ﷺ)'s specific Sahih Hadith and Dua.
3. The Irresistible Payoff (15-25s): Reveal the dramatic life-changing reward ("যা পড়লে তা ফিরিয়ে দেওয়া হয় না", "জীবনের মোড় ঘুরিয়ে দেওয়া আমল", "সকল অনিষ্ট থেকে আল্লাহর গ্যারান্টিযুক্ত নিরাপত্তা").

MASTER REAL-LIFE HOOK ANCHORS BY CATEGORY:
- Night & Sleep (রাত ও ঘুম) → "রাতে কি কখনো হঠাৎ ঘুম ভেঙে যায়? অথবা মনে অজানা কোনো ভয় কাজ করে? নবীজি (সা.) ঠিক এই মুহূর্তটির জন্য একটি বিশেষ দোয়া শিখিয়েছেন..."
- Evil Eye & Ruqyah (বদনজর ও অশান্তি) → "হঠাৎ করে অকারণে সংসারে অশান্তি, প্রিয়জনের ওপর কথায় কথায় রাগ আর কাজে মন না বসা — এটি অনেক সময় বদনজরের মারাত্মক লক্ষণ হতে পারে!..."
- Crises & Debt (সংকট ও ঋণমুক্তি) → "মাসের শেষে টানাটানি, ঋণের বোঝা আর সংসার খরচের চিন্তায় দিশেহারা? নবীজি (সা.) এমন একটি দোয়া শিখিয়েছেন যা পাহাড়সম ঋণ থাকলেও তা পরিশোধের পথ খুলে দেয়..."
- Family & Marriage (দাম্পত্য ও পরিবার) → "সারাদিনের ক্লান্তির পর ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়া কিংবা হাসিমুখে কথা বলাও যে সদকা — আমরা অনেকেই এই সুন্নাহটি ভুলে যাই!..."

SCENE-BY-SCENE STRUCTURE:

1. SCENE 1 (THE RELATABLE MOMENT — 0-5s):
   - Hook the viewer instantly using the exact natural, emotional everyday tone shown above.
   - Anchor directly in a tangible reality (sudden waking at night, fear, debt, evil eye, marriage).

2. SCENE 2 (THE PROPHET'S SOLUTION & RECITATION — 5-15s):
   - Directly connect to the authentic Sahih Hadith or Quranic Dua.
   - Put Arabic text, pronunciation, and exact translation inside <ARABIC> tags:
     <ARABIC>
     Pure Arabic with Tashkeel
     (বাংলা উচ্চারণ)
     (১০০% নির্ভুল ও প্রামাণিক বাংলা অর্থ)
     </ARABIC>

3. SCENE 3 (THE IRRESISTIBLE PAYOFF & ACTION — 15-25s):
   - Give the viewer the immediate actionable takeaway and the promised reward:
     * e.g., "জীবনের মোড় ঘুরিয়ে দেওয়া এই ছোট্ট আমলটি আজ রাতেই নিজের জীবনে শুরু করুন এবং আল্লাহর রহমতের ওপর পূর্ণ বিশ্বাস রাখুন।"

4. SCENE 4 (CLOSING DHIKR CTA — 25-30s):
   - End ONLY with an interactive CTA asking viewers to comment a specific Arabic Dhikr:
     * e.g., কমেন্টে লিখুন: <ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>

OUTPUT FORMAT — Respond with ONLY valid JSON (no markdown fences), 100% BANGLA & ARABIC, NO ENGLISH:
{
    "title": "ভিডিওর বাংলা শিরোনাম",
    "title_bn": "ভিডিওর বাংলা শিরোনাম",
    "topic": "বাংলা বিষয়ের নাম",
    "hook_category": "relatable_moment",
    "reference": "সহীহ বুখারী: ১১৫৪",
    "narration_full_bn": "full narration here with <ARABIC> tags",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "রাতে হঠাৎ ঘুম ভেঙে গেলে নবীজি (সা.) এর শিখানো এই বিশেষ দোয়াটি পড়লে তা ফিরিয়ে দেওয়া হয় না...",
            "highlight_phrase": "হঠাৎ ঘুম ভেঙে গেলে",
            "visuals": "serene atmospheric bedroom window under midnight twilight with starry sky, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 2,
            "narration": "নবীজি (সা.) বলেছেন, এই মুহূর্তে কেউ যদি বলে: <ARABIC>لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ\n(লা ইলাহা ইল্লাল্লাহু ওয়াহদাহু লা শারীকা লাহু)\n(আল্লাহ ছাড়া কোনো উপাস্য নেই, তিনি একক, তাঁর কোনো শরিক নেই)</ARABIC>",
            "visuals": "vast calm desert oasis under glowing crescent moon, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 3,
            "narration": "জীবনের মোড় ঘুরিয়ে দেওয়া এই ছোট্ট আমলটি আজ রাতেই করে দেখুন এবং আল্লাহর কাছে আপনার মনের ইচ্ছা প্রার্থনা করুন।",
            "highlight_phrase": "জীবনের মোড় ঘুরিয়ে দেওয়া",
            "visuals": "majestic ancient library with antique manuscripts and warm glowing lantern, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে লিখুন: <ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>",
            "visuals": "warm glowing brass moroccan lantern on carved stone, peaceful dusk ambience, photorealistic 8k, vertical 9:16, no humans"
        }
    ]
}
"""

    user_prompt = f"Generate a highly engaging, viral 30-second Islamic video script in 100% Bangla using The Winning Viral Hook Formula. In Scene 1 and Scene 3, include 'highlight_phrase' with the exact 2-4 punchy real-life words (like 'হঠাৎ ঘুম ভেঙে গেলে', 'বদনজরের ক্ষতিকর প্রভাব', 'পাহাড় পরিমাণ ঋণ'). Topic: {topic_title or 'Islamic Reminders'}. Category: {category}. NO ENGLISH WORDS."
    
    script_data = extract_json(system_prompt, user_prompt, max_tokens=1400)
    if not script_data:
        logger.error("Failed to generate script JSON from LLM.")
        return None
        
    return script_data
