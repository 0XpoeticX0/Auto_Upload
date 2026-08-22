# -*- coding: utf-8 -*-
import random
import re
from app.llm.provider import extract_json, generate_text
from app.logger import logger
from app.database import get_connection, get_recent_facebook_posts

# ==============================================================================
# 4 HIGH-RETENTION CAROUSEL TOPIC FORMATS (VIRAL BLUEPRINTS)
# ==============================================================================
CAROUSEL_FORMATS = [
    {
        "key": "practical_blueprint",
        "name": "The Step-by-Step Practical Blueprint (কার্যকর সমাধান)",
        "description": "দোয়া কবুল না হওয়ার কারণ ও প্রতিকার, গুনাহ মাফের নিশ্চিত উপায়, নামাজে মনোযোগ বাড়ানোর ৩টি গোপন কৌশল।",
        "seed_concepts": [
            "দোয়া কবুল না হওয়ার প্রধান ৩টি কারণ ও এর সুন্নাহ সমাধান [সহীহ মুসলিম: ১০১৫, সহীহ বুখারী: ৬৩৪০]",
            "নামাজে দাঁড়িয়ে মনের অস্থিরতা ও শয়তানের ওয়াসওয়াসা কাটানোর ৩টি কৌশল [সহীহ মুসলিম: ২২০৩]",
            "বিশাল পাহাড়সম ঋণ ও অর্থাভাব দূর করার ৩টি প্রমাণিত আমল [তিরমিযী: ৩৫৬০, আবু দাউদ: ১৫৫৫]",
            "অভাবনীয় রিজিক পাওয়ার ৩টি সহজ কুরআনিক আমল যা জীবনে বরকত আনে [সূরা নূহ: ১০-১২, সূরা তালাক: ২-৩]"
        ]
    },
    {
        "key": "problem_sunnah_remedy",
        "name": "The Problem -> Sunnah Remedy Formula (সমস্যা ও সুন্নাহ নিরাময়)",
        "description": "অতিরিক্ত মানসিক দুশ্চিন্তা ও হতাশা, রাতে ঘুম না আসা, বদনজর ও সংসারে অশান্তি দূর করার সুন্নাহ প্রেসক্রিপশন।",
        "seed_concepts": [
            "অতিরিক্ত মানসিক দুশ্চিন্তা ও হতাশা দূর করার ৩টি সুন্নাহ আমল [সহীহ বুখারী: ৬৩৬৩, মুসনাদে আহমদ: ২২৩৩]",
            "মাঝরাতে হঠাৎ ঘুম ভেঙে যাওয়া ও দুঃস্বপ্ন দেখলে নবীজির নির্দেশিত ৩টি তাত্ক্ষণিক আমল [সহীহ বুখারী: ১১৫৪, সহীহ মুসলিম: ২২৬১]",
            "সংসারে অকারণে অশান্তি ও বদনজর কাটাতে নবীজির শেখানো ৩টি সুরক্ষা আমল [সহীহ বুখারী: ৩৩৭৪, সহীহ মুসলিম: ৭৮০]",
            "প্রচণ্ড রাগের মুহূর্তে যে ৩টি কাজ ইসলামে কঠোরভাবে নিষেধ ও এর তাৎক্ষণিক নিরাময় [সহীহ বুখারী: ৬১১৬]"
        ]
    },
    {
        "key": "everyday_checklist",
        "name": "The Halal vs. Haram Everyday Checklist (সচেতনতা ও সতর্কতা)",
        "description": "দৈনন্দিন জীবনের সাধারণ ভুল যা অজান্তেই আমল ধ্বংস করে, গীবত, অফিসের ফাঁকি, সামাজিক মাধ্যমের সতর্কতা।",
        "seed_concepts": [
            "দৈনন্দিন জীবনের ৩টি সাধারণ ভুল যা অজান্তেই নেক আমল ধ্বংস করে দেয় [সহীহ মুসলিম: ২৫৮১]",
            "অজান্তেই পরিবারের বরকত কেড়ে নেওয়া ৩টি বদভ্যাস ও এর সুন্নাহ প্রতিকার [সুনান আবু দাউদ: ৫০৯৫]",
            "সামাজিক মাধ্যম ও মুখের ৩টি বড় গুনাহ যা মানুষ হালকা মনে করে [সহীহ বুখারী: ৬৪৭৪]",
            "মা-বাবা ও স্ত্রীর সাথে আচরণের ৩টি সূক্ষ্ম ভুল যা বড় গুনাহ ডেকে আনে [সহীহ বুখারী: ৫৩৫৪, জামে আত-তিরমিযী: ৩৮৯৫]"
        ]
    },
    {
        "key": "sunnah_routines",
        "name": "Night & Morning Sunnah Routines (দৈনিক রুটিন ও আমল)",
        "description": "রাতে ঘুমানোর আগের ৩টি ছোট আমল (সারা রাত সুরক্ষায়), ফজরের পরের ৩টি বরকতময় আমল, জুমার দিনের গোপন মুহূর্ত।",
        "seed_concepts": [
            "রাতে ঘুমানোর আগের ৩টি ছোট আমল (যা সারা রাত মহান আল্লাহর সুরক্ষায় রাখবে) [সহীহ বুখারী: ৫০১৭, ৫০৪০, ২৩১১]",
            "ফজরের নামাজের পর যে ৩টি আমল করলে সারাদিন অফুরন্ত বরকত মেলে [সহীহ মুসলিম: ৭০৭, সুনান আন-নাসায়ী: ৯৯২৮]",
            "জুমার দিনের আসর থেকে মাগরিব: সেই গোপন মুহূর্তে দোয়া কবুলের ৩টি গোপন নিয়ম [সুনান আবু দাউদ: ১০৪৮]",
            "ঘর থেকে বের হওয়া ও ঘরে প্রবেশের ৩টি বরকতময় সুন্নাহ [সুনান আবু দাউদ: ৫০৯৫, জামে আত-তিরমিযী: ২৬৯৮]"
        ]
    }
]

from app.history import (
    get_next_pillar_from_history,
    get_recent_post_records
)

def _get_next_format() -> dict:
    """Round-robin rotation across the 4 High-Retention Carousel Formats."""
    return get_next_pillar_from_history(CAROUSEL_FORMATS, "post")

def format_carousel_caption(post_data: dict) -> str:
    """Builds a short, informative, high-converting caption with zero duplication."""
    cover_lines = post_data.get("cover", {}).get("title_lines", [])
    hook = " ".join(cover_lines).strip() if cover_lines else post_data.get("title", "বরকতময় সুন্নাহ আমল")
    
    caption = f"{hook} 🤲\n\n"
    
    slides = post_data.get("slides", [])
    for idx, s in enumerate(slides):
        title = s.get("title", "")
        main_t = s.get("main_text", "").strip("‘ ’'\"")
        arabic = s.get("arabic", "").strip()
        pron = s.get("pronunciation", "").strip()
        meaning = s.get("meaning", "").strip()
        sol = s.get("solution", "").strip()
        ref = s.get("reference", "").strip()
        
        if title:
            caption += f"✨ {title}:\n"
        if main_t:
            caption += f'"{main_t}"\n'
        if arabic:
            caption += f"{arabic}\n"
        if pron:
            caption += f'উচ্চারণ: "{pron}"\n\n'
        if meaning:
            caption += f'অর্থ: "{meaning}"\n\n'
        if sol:
            caption += f"{sol}\n"
        if ref:
            caption += f"[{ref}]\n"
        caption += "\n"
        
    last_slide = slides[-1] if slides else {}
    dhikr = last_slide.get("dhikr_word", "আমিন")
    
    caption += (
        f"📌 আমলটি মনে রাখতে পোস্টটি 🔖 Save করুন।\n"
        f"কমেন্টে একবার \"{dhikr}\" লিখুন — সদকায়ে জারিয়া হবে! 🤍\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 @dailydos_islam\n\n"
    )
    
    core_tags = [
        "IslamicReminders", "Sunnah", "DailyDos",
        "সহীহ_হাদিস", "দ্বীন_ইসলাম", "ইসলামিক_পোস্ট",
        "QuranAndSunnah", "MuslimUmmah", "DeenOverDunya",
        "Alhamdulillah", "Reels", "Carousel"
    ]
    slot_tags = [t.strip("#").strip() for t in post_data.get("tags", [])
                 if t.strip("#").strip() not in core_tags and len(t.strip("#").strip()) > 1]
    all_tags = core_tags + slot_tags[:5]
    tags = " ".join([f"#{t}" for t in all_tags])
    
    return (caption + tags).strip()

def generate_post_content(language: str = "bangla") -> dict:
    """
    Generates authentic, deeply relatable 4-Slide Islamic Carousel content using the 4 High-Retention Formats.
    """
    selected_format = _get_next_format()
    logger.info(f"Selected Carousel Format ({language.upper()}): {selected_format['name']}")
    
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

    available_seeds = selected_format.get("seed_concepts", [])
    suggested_seeds = random.sample(available_seeds, min(2, len(available_seeds)))
    suggested_text = "\n".join([f"- {s}" for s in suggested_seeds])

    system_prompt = f"""You are an expert Islamic scholar and viral content creator designing a high-retention 4-Slide Islamic Swipe Carousel for Instagram & Facebook in 100% Bangla (বাংলা).
Format Style: {selected_format['name']} — {selected_format['description']}

THE WINNING 4-SLIDE HIGH-RETENTION FORMULA:
- Slide 1 (Hook Cover): Curiosity-driven cover title (2-3 lines) with category badge and gold highlights (e.g., "দোয়া কবুল না হওয়ার প্রধান ৩টি কারণ ও সমাধান 🤲 (সোয়াইপ করুন 👉)").
- Slide 2 (Point 1 / Hadith 1): First cause/amol/mistake + Sahih Hadith + highlighted keywords + practical Sunnah remedy.
- Slide 3 (Point 2 / Hadith 2 or Dua): Second cause/amol/Dua + authentic Arabic text (if applicable) with pronunciation & meaning + Sahih reference.
- Slide 4 (Point 3 / Action Blueprint & Save CTA): Final amol / actionable checklist + community Save 🔖 & Share comment prompt.

SUGGESTED FRESH INSPIRATION:
{suggested_text}

CRITICAL RULES (100% STRICT):
1. AUTHENTICITY & SAHABI ATTRIBUTION:
   - Must be 100% authentic from Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, or the Holy Quran.
   - For Hadiths: Include Sahabi narrator in header (e.g. 'আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (ﷺ) বলেছেন:').

2. QUOTE & PHRASING ACCURACY (PUNCHY, RELATABLE & 100% IDENTICAL):
   - Provide the EXACT authentic Bangla translation inside quotes ‘...’.
   - highlight_phrases: 1 to 3 EXACT substrings (2-5 words each) to highlight in warm gold.

3. VISUAL BACKGROUND PROMPT:
   - Must be high-aesthetic, architectural or atmospheric nature in 4:5 portrait (no people, no living beings, no text).
   - Example: "vertical 4:5, aesthetic wooden Rehal with open Holy Quran next to warm amber Moroccan lantern on marble courtyard table at twilight, photorealistic 8k, serene atmosphere, no people, no living beings".

{past_topics_text}

Respond with ONLY valid JSON (no markdown formatting, no other text):
{{
    "format_type": "{selected_format['key']}",
    "topic_badge": "✦ দোয়া কবুল ও আত্মশুদ্ধি ✦",
    "title": "দোয়া কবুল না হওয়ার ৩টি কারণ ও সমাধান",
    "category": "{selected_format['key']}",
    "visual_prompt": "vertical 4:5, aesthetic serene wooden Rehal with Holy Quran next to warm amber Moroccan lantern on marble table, soft sunset twilight, photorealistic 8k, no people",
    "cover": {{
        "title_lines": [
            "দোয়া কবুল না হওয়ার",
            "প্রধান ৩টি কারণ ও এর সমাধান",
            "যা অনেকেরই অজানা"
        ],
        "highlight_phrases": ["দোয়া কবুল না হওয়ার", "৩টি কারণ ও এর সমাধান", "অনেকেরই অজানা"]
    }},
    "slides": [
        {{
            "slide_number": 2,
            "title": "১. হারাম উপার্জন ও অসচেতন মন",
            "header": "রাসূলুল্লাহ (ﷺ) বলেছেন:",
            "main_text": "‘এক ব্যক্তি ধূলিধূসর অবস্থায় আকাশের দিকে হাত তুলে দোয়া করে, অথচ তার খাদ্য হারাম, পানীয় হারাম, পোশাক হারাম এবং তার জীবিকা হারাম—তবে কীভাবে তার দোয়া কবুল হবে?’",
            "highlight_phrases": ["খাদ্য হারাম, পানীয় হারাম", "কীভাবে তার দোয়া কবুল হবে"],
            "solution": "💡 সুন্নাহ সমাধান: দোয়া কবুলের প্রথম শর্ত হলো হালাল রুজি এবং একাগ্র চিত্তে আল্লাহর কাছে প্রার্থনা করা।",
            "reference": "সহীহ মুসলিম: ১০১৫"
        }},
        {{
            "slide_number": 3,
            "title": "২. তাড়াহুড়ো করা ও নিরাশ হওয়া",
            "header": "আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (ﷺ) বলেছেন:",
            "main_text": "‘তোমাদের প্রত্যেকের দোয়া কবুল করা হয়, যতক্ষণ না সে তাড়াহুড়ো করে বলে—আমি তো দোয়া করলাম কিন্তু কবুল হলো না।’",
            "highlight_phrases": ["তাড়াহুড়ো করে", "আমি তো দোয়া করলাম কিন্তু কবুল হলো না"],
            "solution": "💡 সুন্নাহ সমাধান: পূর্ণ দৃঢ় বিশ্বাস রাখুন। আল্লাহ অবিলম্বে দান করবেন, নয়তো পরকালের জন্য জমা রাখবেন বা কোনো বিপদ দূর করবেন।",
            "reference": "সহীহ বুখারী: ৬৩৪০"
        }},
        {{
            "slide_number": 4,
            "title": "৩. দোয়া কবুলের সঠিক পদ্ধতি ও আমল",
            "main_text": "১. আল্লাহর প্রশংসা ও নবীজি (ﷺ)-এর ওপর দুরুদ পড়ে শুরু করুন।\n২. কাবার দিকে ফিরে দুই হাত তুলে বিনম্র কণ্ঠে চান।\n৩. ইসমে আজম পাঠ করে আপনার মনের আরজি জানান।",
            "solution": "💡 বরকতময় মুহূর্ত: শেষ রাত, সেজদারত অবস্থায় এবং জুমার দিনের আসরের শেষ সময়ে দোয়া করুন।",
            "dhikr_word": "আমিন"
        }}
    ],
    "tags": ["IslamicReminders", "Sunnah", "DailyDos", "সহীহ_হাদিস", "দ্বীন_ইসলাম", "ইসলামিক_পোস্ট", "Shorts", "Reels", "Carousel"]
}}"""

    user_prompt = f"Generate 1 high-CTR, deeply relatable 4-Slide Islamic Swipe Carousel using format '{selected_format['name']}' in 100% Bangla."

    from app.history import is_topic_duplicate_global
    for attempt in range(3):
        try:
            post_data = extract_json(system_prompt, user_prompt, max_tokens=2200, for_posts=True)
            if not post_data or "cover" not in post_data or "slides" not in post_data or len(post_data.get("slides", [])) < 2:
                logger.warning(f"Attempt {attempt+1}: Failed to parse valid Carousel JSON from LLM. Retrying...")
                continue
                
            first_slide = post_data.get("slides", [])[0]
            main_q = first_slide.get("main_text", "")
            ref = first_slide.get("reference", "")
            topic_str = f"[{ref}] {main_q}"
            
            # Cross-pipeline deduplication check
            if is_topic_duplicate_global(topic_str):
                logger.warning(f"Topic '{topic_str}' flagged as duplicate in global history! Retrying with a fresh topic...")
                continue
                
            # Build unified caption
            post_data["caption"] = format_carousel_caption(post_data)
            return post_data
        except Exception as e:
            logger.error(f"Error on carousel generation attempt {attempt+1}: {e}")
            
    logger.error("Failed to generate a non-duplicate Carousel after 3 attempts.")
    return None

if __name__ == "__main__":
    p = generate_post_content("bangla")
    import json
    print(json.dumps(p, ensure_ascii=False, indent=2))
