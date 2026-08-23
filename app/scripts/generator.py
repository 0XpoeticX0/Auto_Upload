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

THE 4 CORE PSYCHOLOGY HOOK RULES (MANDATORY FOR ALL SCRIPTS):
Rule 1: Name the Authority First
- Start with an instant trust marker ("রাসূলুল্লাহ (ﷺ) বলেছেন...", "আল্লাহ তায়ালা কুরআনে প্রতিশ্রুতি দিয়েছেন...").
- Why: People stop scrolling immediately when they see a credible, sacred source.

Rule 2: Promise High Gain with Low Effort
- Use specific, small numbers ("মাত্র ১টি আমল", "প্রতিদিন ৩০ সেকেন্ড", "ঘুমানোর আগে ৩ বার", "মাত্র ২০ সেকেন্ড").
- Why: Specific numbers feel achievable and low friction.

Rule 3: Target a Pain Point or Deep Desire
- Rizq / Money: অভাব দূর হওয়া, দেনা পরিশোধ, ব্যবসায় বরকত
- Peace / Anxiety: মনের অস্থিরতা, দুশ্চিন্তা থেকে মুক্তি, মানসিক প্রশান্তি
- Protection: বিপদ-আপদ থেকে বেঁচে থাকা, কবরের আযাব থেকে মুক্তি, দোয়া কবুল হওয়া

Rule 4: Leave the Loop Open (Never reveal the whole answer in Scene 1)
- End the Scene 1 sentence with an unfinished promise ("...যা পড়লে বান্দার কোনো চাওয়া অপূর্ণ থাকে না", "...যা আপনার ভাগ্য বদলে দিতে পারে").
- Why: Forces the viewer to watch the whole video to find the answer.

UNIVERSAL HOOK TEMPLATES (PLUG & PLAY):
1. Guaranteed Result: [Authority] + এমন ১টি [আমল/দোয়া] আছে + যা করলে [বড় সমাধান]...
2. Mistake / Warning: আমরা প্রতিদিন এই ১টি ভুল করি + যার কারণে [বড় ক্ষতি/দোয়া আটকে যায়]...
3. Instant Protection: ঘর থেকে বের হওয়ার সময় / ঘুমানোর আগে + মাত্র ৩ সেকেন্ডে এই ১টি আমল...
4. Urgent Curiosity: আপনি কি জানেন + [সহজ কাজ] করলে আল্লাহ বান্দার জন্য কি প্রস্তুত রাখেন?

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
