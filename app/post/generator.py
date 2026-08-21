# -*- coding: utf-8 -*-
import random
import re
from app.llm.provider import extract_json, generate_text
from app.logger import logger
from app.database import get_connection, get_recent_facebook_posts

# ==============================================================================
# 4 HIGH-REACH RELATABLE MOMENT PILLARS FOR IMAGE POSTS
# Formula: Relatable Human Problem/Moment -> The Prophet's Solution -> Guaranteed Payoff
# ==============================================================================
POST_PILLARS = [
    {
        "key": "night_sleep_moments",
        "name": "রাত, ঘুম ও মানসিক অস্থিরতা (Night, Sleep & Peace)",
        "description": "মাঝরাতে হঠাৎ ঘুম ভেঙে যাওয়া, দুঃস্বপ্ন দেখা, বিছানায় গিয়ে ঘুম না আসা, গভীর রাতের উদ্বেগ ও মোড় ঘোরানো দোয়া।",
        "seed_concepts": [
            "রাতে হঠাৎ ঘুম ভেঙে গেলে নবীজি (সা.)-এর শেখানো সেই বিশেষ দোয়া যা সাথে সাথে কবুল হয় [সহীহ বুখারী: ১১৫৪]",
            "দুঃস্বপ্ন বা ভয়ংকর স্বপ্ন দেখলে নবীজির নির্দেশিত ৩টি তাত্ক্ষণিক আমল [সহীহ মুসলিম: ২২৬১]",
            "বিছানায় যাওয়ার পর ঘুম না আসলে ও গভীর রাতে মনের অস্থিরতা কাটাতে নবীজির আমল [জামে আত-তিরমিযী: ৩৫২৮]",
            "ঘুমন্ত মানুষের মাথায় শয়তানের দেওয়া ৩টি গিঁট খোলার সহজ সুন্নাহ কৌশল [সহীহ বুখারী: ১১৪২]",
            "ঘুমানোর আগে দুই তালুতে ৩ কুল পড়ে সারা শরীর মুছে নেওয়ার বরকতময় সুন্নাহ [সহীহ বুখারী: ৫০১৭]",
            "মধ্যরাতে ভয় বা আতঙ্কে চমকে উঠলে পাঠ করার বিশেষ সহীহ দোয়া [সুনান আবু দাউদ: ৩৮৯৩]",
            "তাহাজ্জুদের শেষ প্রহরে বান্দার অশ্রু বিসর্জন ও আল্লাহর প্রথম আসমানে নেমে আসার ক্ষণ [সহীহ বুখারী: ১১৪৫]",
            "ঘুমানোর পূর্বে সূরা মুলক তেলাওয়াত করলে কবরের সমস্ত আজাব থেকে মুক্তি [সুনান আত-তিরমিযী: ২৮৯১]"
        ]
    },
    {
        "key": "protection_evil_eye",
        "name": "বদনজর, হিংসা ও ঘরের সুরক্ষা (Evil Eye & Home Peace)",
        "description": "অকারণে সংসারে অশান্তি, কুদৃষ্টি, বদনজর, হিংসা ও অদৃশ্য ক্ষতি থেকে নিজেকে ও পরিবারকে সুরক্ষিত রাখার আমল।",
        "seed_concepts": [
            "বদনজর ও হিংসার ক্ষতিকর প্রভাব থেকে নিজেকে ও পরিবারকে সুরক্ষিত রাখার কার্যকর দোয়া [সহীহ বুখারী: ৩৩৭৪]",
            "সুন্দর কিছু দেখলে নিজের অজান্তেই যাতে বদনজর না লাগে—নবীজির শেখানো বরকতময় দোয়া [মুয়াত্তা মালিক]",
            "ঘর থেকে বের হওয়ার সময় মাত্র ১টি বাক্য যা সারাদিন শয়তানের হাত থেকে বাঁচায় [সুনান আবু দাউদ: ৫০৯৫]",
            "খাবার ও পানীয়তে ক্ষতি বা বিষ থেকে বাঁচতে নবীজির সকাল-সন্ধ্যার সুরক্ষা দোয়া [জামে আত-তিরমিযী: ৩৩৪৭]",
            "ছোট বাচ্চাদের বদনজর ও রোগবালাই থেকে রক্ষা করতে নবীজির শেখানো বিশেষ দোয়া [সহীহ বুখারী: ৩৩৭১]",
            "শরীরের কোনো স্থানে তীব্র ব্যথা বা অসুখ হলে হাত রেখে নবীজির শেখানো রুকইয়াহ [সহীহ মুসলিম: ২২০২]",
            "যে ঘরে সূরা বাকারা পড়া হয় সেখান থেকে শয়তানের পলায়ন ও সংসারে স্থায়ী শান্তি [সহীহ মুসলিম: ৭৮০]"
        ]
    },
    {
        "key": "crises_debt_turnaround",
        "name": "সংকট, ঋণ ও মোড় ঘোরানো দোয়া (Crises, Debt & Rizq)",
        "description": "দেয়ালে পিঠ ঠেকে যাওয়া কঠিন বিপদ, পাহাড়সম ঋণমুক্তি, ইসমে আজম, অর্থাভাব দূর করা ও তাৎক্ষণিক দোয়া কবুল।",
        "seed_concepts": [
            "দেয়ালে পিঠ ঠেকে গেলে ও অসম্ভব বিপদ কাটাতে ইউনুস (আ.)-এর সেই বিশেষ দোয়া [জামে আত-তিরমিযী: ৩৫০৫]",
            "পাহাড় পরিমাণ ঋণের বোঝা থাকলেও তা পরিশোধে সাহায্য করার জাদুকরী দোয়া [জামে আত-তিরমিযী: ৩৫৬০]",
            "আল্লাহর সেই বিশেষ গোপন নাম যা দিয়ে দোয়া করলে কোনো দোয়া ফেরত দেওয়া হয় না (ইসমে আজম) [সুনান আবু দাউদ: ১৪৯৩]",
            "জুমার দিনের আসর থেকে মাগরিবের মধ্যবর্তী সেই বিশেষ মুহূর্ত—যখন কোনো দোয়া ফিরিয়ে দেওয়া হয় না [সুনান আবু দাউদ: ১০৪৮]",
            "মনের তীব্র দুশ্চিন্তা, হতাশা ও টানাটানি কাটাতে নবীজি (সা.)-এর শেখানো দোয়া [সহীহ বুখারী: ৬৩৬৩]",
            "লা হাওলা ওয়ালা কুওয়াতা ইল্লা বিল্লাহ: আরশের নিচের অফুরন্ত গুপ্তধন [সহীহ বুখারী: ৪২০৫]",
            "সাইয়্যিদুল ইস্তিগফার: ক্ষমার শ্রেষ্ঠ দোয়া যা বিশ্বাস সহকারে রাতে পড়লে জান্নাত ওয়াজিব [সহীহ বুখারী: ৬৩০৬]"
        ]
    },
    {
        "key": "husband_wife_family",
        "name": "দাম্পত্য সুখ, পরিবার ও আচরণ (Marriage, Spouse & Family)",
        "description": "সারাদিনের ক্লান্তি শেষে দাম্পত্যে ভালোবাসা বাড়ানোর সুন্নাহ, রাগের মুহূর্তে সংযম, মা-বাবার হক ও ঘরে বরকত।",
        "seed_concepts": [
            "সারাদিনের ক্লান্তি শেষে ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়াও সদকা [সহীহ বুখারী: ৫৩৫৪]",
            "প্রচণ্ড রাগের মুহূর্তে যে ৩টি কাজ ও কথা ইসলামে কঠোরভাবে নিষেধ [সহীহ বুখারী: ৬১১৬]",
            "পিতা-মাতার দিকে কেবল ১টি ভালোবাসার দৃষ্টিতে কবুল হজের সওয়াব [শুআবুল ঈমান: ৭৮৫৯]",
            "ঘরে প্রবেশ করে পরিবারকে হাসিমুখে সালাম দিলে শয়তানের পলায়ন ও বরকত বৃদ্ধি [জামে আত-তিরমিযী: ২৬৯৮]",
            "পরিবারে শান্তি ও নেককার সন্তান পাওয়ার শ্রেষ্ঠ কুরআনীয় দোয়া [সূরা আল-ফুরকান: ৭৪]",
            "তোমাদের মধ্যে সর্বোত্তম ব্যক্তি সে, যে তার স্ত্রীর কাছে সর্বোত্তম [জামে আত-তিরমিযী: ৩৮৯৫]"
        ]
    }
]

from app.history import (
    get_next_pillar_from_history,
    get_recent_post_records
)

def _get_next_post_pillar() -> dict:
    """Round-robin rotation for Facebook posts across the 4 Relatable Moment Pillars."""
    return get_next_pillar_from_history(POST_PILLARS, "post")

def generate_post_content(language: str = "bangla") -> dict:
    """
    Generates authentic, deeply relatable Islamic photo card content with 4-pillar round-robin and concept deduplication.
    """
    selected_pillar = _get_next_post_pillar()
    logger.info(f"Selected Pillar for Post ({language.upper()}): {selected_pillar['name']}")
    
    recent_posts = get_recent_post_records(limit=60)
    past_topics_list = []
    if recent_posts:
        for p in recent_posts:
            ref = p.get("reference", "")
            q = p.get("quote", "")[:50]
            if ref or q:
                past_topics_list.append(f"- Ref: {ref} | Quote: {q}...")
                
    past_topics_text = ""
    if past_topics_list:
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list[:30])

    available_seeds = selected_pillar.get("seed_concepts", [])
    suggested_seeds = random.sample(available_seeds, min(3, len(available_seeds)))
    suggested_text = "\n".join([f"- {s}" for s in suggested_seeds])

    if language == "bangla":
        system_prompt = f"""You are an expert Islamic scholar and content creator crafting viral, deeply relatable Islamic reflection photo posts in Bangla (বাংলা).
Pillar: {selected_pillar['name']} — {selected_pillar['description']}

THE WINNING RELATABLE FORMULA:
Focus on an urgent real-life human scenario everyone experiences (night anxiety, sudden waking, evil eye at home, crushing debt, anger, marital friction).
Provide Rasulullah (ﷺ)'s direct Sahih Hadith / Quranic solution that gives immediate relief and life-changing payoff.

SUGGESTED FRESH TOPIC INSPIRATION:
{suggested_text}

CRITICAL RULES (100% STRICT):
1. AUTHENTICITY & SAHABI ATTRIBUTION:
   - Must be 100% authentic from Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, or the Holy Quran.
   - For Hadiths: Always include the Sahabi narrator in the header (e.g. 'জাবির ইবনে আব্দুল্লাহ (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:' or 'আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:').
   - For Quranic Ayahs: 'মহান আল্লাহ তা'আলা পবিত্র কুরআনে এরশাদ করেছেন:'.

2. QUOTE & PHRASING ACCURACY (EASY, RELATABLE & 100% IDENTICAL):
   - Provide the EXACT authentic 100% identical Bangla translation from Sahih Hadith / Quran inside Bangla quotes ‘...’.
   - Length: 25 to 65 words (punchy, clear, beautifully readable on card).
   - highlight_phrases: 1 to 3 EXACT substrings (2-5 words each) from the quote to highlight in warm gold (e.g., "এই বিশেষ দোয়াটি পড়বে", "সকল গুনাহ মাফ", "অভাবনীয় রিজিক").

3. VISUAL BACKGROUND PROMPT:
   - Must be high-aesthetic, architectural or atmospheric nature (no people, no living beings, no text).
   - Example: "vertical 4:5, aesthetic wooden Rehal with open Holy Quran next to warm amber Moroccan lantern on marble courtyard table, photorealistic 8k, serene atmosphere, no people, no living beings".

4. CAPTION GENERATION (DEEP VALUE + RELATABLE HOOK + SAVE/SHARE TRIGGER):
   - 100% Bangla caption.
   - Structure:
   ✨ [Relatable Real-Life Hook & Situation]: [1-2 sentences on why every Muslim needs this today]
   
   📖 সহীহ দলিল ও প্রেক্ষিত:
   [Full background and context of the Hadith / Ayah]
   
   🤲 দোয়া ও উচ্চারণ:
   [Arabic Dua with full Tashkeel if applicable]
   উচ্চারণ: "[Bangla Phonetic Pronunciation]"
   অর্থ: "[Bangla Meaning]"
   📚 তথ্যসূত্র: [Specific Sahih Reference]
   
   💡 শিক্ষা ও আমল:
   [1-2 practical action sentences for daily life]

   💬 আজকের জিকির ও আমল:
   পরবর্তীতে আমল করার জন্য পোস্টটি Save করে রাখুন এবং কমেন্টে একবার "[সুবহানাল্লাহ / আলহামদুলিল্লাহ / আমিন / মাশাআল্লাহ]" লিখে বন্ধুদের সাথে শেয়ার করে সদকায়ে জারিয়ার অংশীদার হোন! 🤍

   ━━━━━━━━━━━━━━━━━━━━
   📌 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য ফলো করুন:
   👉 @dailydos_islam

   #DeenOverDunya #IslamicReminders #MuslimUmmah #Sunnah #সহীহ_হাদিস #দ্বীন_ইসলাম #কুরআনের_আলো #ইসলামিকপোস্ট #DailyDos #[TopicTag]

{past_topics_text}

Respond with ONLY valid JSON (no markdown formatting, no other text):
{{
    "topic_badge": "✦ ছোট আকর্ষণীয় ক্যাটাগরি ব্যাজ (উদা: রাতের বিশেষ আমল / ঋণমুক্তির দোয়া / বদনজর থেকে রক্ষা / দাম্পত্যের বরকত) ✦",
    "header": "আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:",
    "quote": "‘যে ব্যক্তি রাতে হঠাৎ ঘুম ভেঙে যাওয়ার পর এই দোয়াটি পড়বে, তার সকল গুনাহ মাফ করা হবে এবং তার নেক দোয়া অবিলম্বে কবুল করা হবে।’",
    "highlight_phrases": ["হঠাৎ ঘুম ভেঙে যাওয়ার পর", "সকল গুনাহ মাফ", "অবিলম্বে কবুল"],
    "reference": "সহীহ বুখারী: ১১৫৪",
    "caption": "[Complete high-retention structured caption as instructed above]",
    "visual_prompt": "vertical 4:5, aesthetic serene prayer rug on polished wooden floor before floor-to-ceiling glass window overlooking soft dawn sky, warm morning rays, photorealistic 8k, architectural digest, no people, no living beings",
    "topic": "রাতের বিশেষ দোয়া",
    "category": "{selected_pillar['key']}"
}}"""
    else:
        system_prompt = "English post generation..."

    user_prompt = f"Generate 1 high-CTR, deeply relatable Islamic photo post for pillar '{selected_pillar['name']}' in 100% Bangla."

    try:
        post_data = extract_json(system_prompt, user_prompt, max_tokens=1500)
        if not post_data or "quote" not in post_data:
            logger.error("Failed to generate valid post JSON from LLM.")
            return None
        return post_data
    except Exception as e:
        logger.error(f"Error generating post content: {e}")
        return None

if __name__ == "__main__":
    p = generate_post_content("bangla")
    import json
    print(json.dumps(p, ensure_ascii=False, indent=2))
