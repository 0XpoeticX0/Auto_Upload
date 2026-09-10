import os
import re
import json
import time
import datetime
import subprocess
import requests
import urllib.parse
from PIL import Image

from app.logger import logger
from app.llm.provider import extract_json
from app.history import _supabase_insert, get_recent_video_titles, get_next_episode_number
from app.loop_reel.audio_library import get_or_download_quran_audio
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook

# 2 Daily Prime Slots (BST / GMT+6) with Merged High-Demand Topics
SLOT_CONFIGS = {
    "slot_1_morning": {
        "name": "🌅 Slot 1: Morning & Day Prime (06:00 AM BST)",
        "theme": "Morning Dua, Protection from Evil Eye, Guaranteed Duas (ইসমে আজম), Rizq Unlocking, Marriage & Family Sunnah",
        "system_instruction": "Create a high-curiosity 'MUST-KNOW / WANT-TO-KNOW' day reminder. Focus on one of these high-performing topics: (1) 3 morning deeds for immense Barakah, (2) The greatest name of Allah (ইসমে আজম) where no Dua is rejected, (3) 7 signs Allah is answering your Dua, (4) The 1 forgotten prayer that opens closed doors and relieves crushing debt, (5) 1 secret Sunnah deed between husband and wife (feeding spouse, smiling, good character), (6) 3 things forbidden in anger, or (7) Protecting your family from Evil Eye (বদনজর) with morning Azkar.",
        "visual_prompt": "vertical 9:16, inside a majestic ancient Andalusian Islamic hall with intricate Moorish geometric arched wooden windows, golden morning dawn light rays shining onto an antique carved wooden rehal holding the Holy Quran on an emerald velvet prayer rug, floating glowing dust particles in cinematic god rays, photorealistic 8k, architectural digest, high aesthetic, deeply spiritual, no people, no living beings"
    },
    "slot_2_evening": {
        "name": "🌙 Slot 2: Prime Evening & Night (08:00 PM BST)",
        "theme": "Heart-Softeners, Grave Protection (সূরা মুলক), Sins-Wiping Prayers, Tahajjud Miracles & Night Peace",
        "system_instruction": "Create a profound, emotionally powerful 'HEART-TOUCHING' nighttime reminder. Focus on one of these high-performing topics: (1) The 30-verse Surah (সূরা মুলক) that miraculously shields you inside the grave, (2) The 1 Sunnah prayer that wipes years of sins in minutes (সালাতুত তাসবীহ / আওয়াবীন), (3) What to say if you wake up suddenly in the night with anxiety to have all Duas accepted instantly, (4) The magic of 2 Rakat Tahajjud for impossible miracles, or (5) Sayyidul Istighfar: the master repentance Dua that guarantees Jannah.",
        "visual_prompt": "vertical 9:16, inside a serene Ottoman mosque prayer sanctuary at twilight dusk, glowing ornate brass Islamic lanterns casting warm amber geometric light, intricately carved wooden archway overlooking a peaceful courtyard, velvet crimson prayer carpet, photorealistic 8k, cinematic lighting, deeply peaceful, no people, no living beings"
    }
}

def determine_current_slot() -> str:
    """
    Determines the active slot.
    Morning slot is held (dedicated to Daily Quran Recitation at 06:00 AM BST).
    The Hadith Loop Reel pipeline runs exclusively once daily for the Prime Evening Slot (08:00 PM BST).
    """
    return "slot_2_evening"


ANGLES = [
    {
        "name": "Micro-Moment (ব্যক্তিগত মুহূর্ত)",
        "desc": "দৈনন্দিন জীবনের সূক্ষ্ম কিন্তু গভীর অনুভূতির বাস্তব চিত্র (যেমন: ভোরের নির্জনতায় একাকীত্ব, কাজে বের হওয়ার উদ্বেগ, পরিবারে ছোটখাটো মনোমালিন্য, সারাদিনের ক্লান্তি)",
        "example_hook": "সকালে ঘুম থেকে উঠে যখন ভবিষ্যতের অনিশ্চয়তা আর দুশ্চিন্তায় মনটা ভারী হয়ে আসে..."
    },
    {
        "name": "Story Snippet (ঐতিহাসিক গল্প বা পেছনের প্রেক্ষাপট)",
        "desc": "হাদিসের পেছনের বাস্তব ঘটনা বা সাহাবীর পরিস্থিতি দিয়ে শুরু",
        "example_hook": "মসজিদে একা বসে কাঁদছিলেন এক সাহাবী; নবীজি (ﷺ) গিয়ে জিজ্ঞেস করলেন—'এখানে অসময়ে কেন?'"
    },
    {
        "name": "Paradox & Contrasting (ভুল বনাম সত্য)",
        "desc": "মানুষ যেখানে সমাধান খোঁজে বনাম আসল সমাধান",
        "example_hook": "আমরা শান্তির খোঁজে ঘণ্টার পর ঘণ্টা ফোন স্ক্রোল করি, অথচ মন শান্ত করার রাস্তাটা ছিল ঠিক বিপরীত..."
    },
    {
        "name": "Deep Observation (প্রত্যক্ষ উপলব্ধি ও মানব স্বভাব)",
        "desc": "মানুষের সাধারণ স্বভাব ও অমূলক ভয় তুলে ধরা",
        "example_hook": "আমরা ভবিষ্যতের এমন অনেক কিছু নিয়ে ভয় পাই, যা হয়তো জীবনে কখনোই ঘটবে না।"
    },
    {
        "name": "Reflective Advice (গভীর ও শান্ত পরামর্শ)",
        "desc": "ধীরস্থির, মমতাময়ী ও চিন্তাশীল আত্মউপলব্ধি",
        "example_hook": "সব দায়িত্ব নিজের কাঁধে টেনে না নিয়ে কিছু বিষয় আল্লাহর ওপর ছেড়ে দেওয়া শিখতে হয়।"
    }
]

TONES = [
    "Emotional & Empathetic (শান্ত, হৃদয়স্পর্শী ও মমতাময়ী)",
    "Curious & Story-driven (কৌতূহল ও গল্পের মাধ্যমে শুরু)",
    "Reflective & Philosophical (গভীর আত্মউপলব্ধিমূলক)",
    "Direct & Actionable (বাস্তবধর্মী সমাধান)"
]

BANNED_HOOK_PREFIXES = [
    (r'^(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*\([ﷺসা\.]+\)\s*বলেছেন\s*[:ঃ\s]*',
     r'(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*\([ﷺসা\.]+\)\s*বলেছেন'),
    (r'^(?:নবীজির|নবীজি|রাসূলের)\s*\([ﷺসা\.]+\)\s*শেখানো\s*',
     r'(?:নবীজির|নবীজি|রাসূলের)\s*\([ﷺসা\.]+\)\s*শেখানো'),
]

BANNED_CLICHE_PHRASES = [
    'ভাগ্যের তালা', 'ভাগ্য বদলে', 'জীবন বদলে'
]

FORMULAIC_HOOK_WORDS = [
    '১টি আমল', '১টি গোপন আমল', '১টি কার্যকরী আমল', '১টি আমল করলে', '১টি দোয়া', '১টি বাক্য', '৫ সেকেন্ডের', '২ মিনিটের'
]

def check_hook_monotony(content: dict, recent_history: list, last_hook_text: str = "") -> tuple[bool, str]:
    """Strictly validates hook diversity to prevent robotic, repetitive reel openings."""
    line_1 = (content.get("line_1") or "").strip()
    line_2 = (content.get("line_2") or "").strip()
    full_hook = f"{line_1} {line_2}".strip()

    if not line_1:
        return False, "Hook line_1 is missing or empty."

    # 1. Ban clickbait clichés unconditionally
    for c in BANNED_CLICHE_PHRASES:
        if c in full_hook:
            return False, f"Banned cliché '{c}' detected in hook! Use authentic, natural phrasing."

    # 2. Prevent authority prefix on Line 1 (Line 1 must be human-first situation/hook)
    for new_pat, _ in BANNED_HOOK_PREFIXES:
        if re.search(new_pat, line_1):
            return False, f"Line 1 must NOT start with Hadith preface '{line_1[:25]}...'. Open with a relatable human situation, emotion, or observation first!"

    # 3. Restrict formulaic phrase frequency (e.g. '১টি আমল', '৫ সেকেন্ডের')
    for phrase in FORMULAIC_HOOK_WORDS:
        if phrase in full_hook:
            count = sum(1 for prev in recent_history[:4] if phrase in prev)
            if count >= 1:
                return False, f"Formulaic phrase '{phrase}' appeared in recent videos. Vary the vocabulary and structure!"

    # 4. Enforce Zero Grammatical/Word Overlap in first 5 words against last hook
    if last_hook_text:
        new_first_5 = set(re.sub(r'[^\w\s]', '', line_1).lower().split()[:5])
        last_first_5 = set(re.sub(r'[^\w\s]', '', last_hook_text).lower().split()[:5])
        overlap = new_first_5 & last_first_5
        if len(overlap) >= 2:
            return False, f"Opening words share repetitive overlap {overlap} with last hook: '{last_hook_text[:30]}...'"

    # 5. Enforce syntactic dissimilarity (Jaccard on line_1)
    cleaned_new = set(re.sub(r'[^\w\s]', '', line_1).lower().split())
    for prev in recent_history[:8]:
        cleaned_prev = set(re.sub(r'[^\w\s]', '', prev).lower().split())
        if not cleaned_prev:
            continue
        sim = len(cleaned_new & cleaned_prev) / len(cleaned_new | cleaned_prev)
        if sim >= 0.50:
            return False, f"Hook line_1 is syntactically too similar ({sim:.2f}) to recent content: '{prev[:40]}...'"

    return True, "OK"

def build_loop_reel_system_prompt(
    ep_bn: str,
    target_angle: dict,
    target_tone: str,
    last_hook_text: str,
    avoid_context: str,
    cfg: dict
) -> str:
    """Builds the comprehensive system prompt customized for the specific angle, tone, slot and episode."""
    return f"""You are a master viral Islamic content creator specializing in high-retention 7-second aesthetic Reels with high-value captions.

CONTRASTIVE DYNAMIC ANGLE PRINCIPLE (NO TOPIC BANNING):
Do NOT ban vital daily human topics (such as anxiety, forgiveness, prayer, debt, sleep, patience). Human beings need these reminders every day!
Instead, diversify 100% through FRESH ANGLES, LENSES, and OPPOSITE STRUCTURE!

[ASSIGNED ANGLE & LENS FOR EPISODE #{ep_bn}]
• Angle Archetype: {target_angle['name']}
• Angle Focus: {target_angle['desc']}
• Tone: {target_tone}
• Model Hook Pattern: "{target_angle['example_hook']}"

[LAST POSTED HOOK TO CONTRAST AGAINST]
"{last_hook_text}"

[CONTRASTIVE ANTI-SIMILARITY DIRECTIVE]
1. Read the [LAST POSTED HOOK].
2. Determine its opening style (Question? Story? Direct action? Emotion?).
3. Create a hook with a COMPLETELY CONTRASTING structure:
   - If the last hook was a Question -> Use a Micro-Moment Story or Direct Observation.
   - If the last hook offered a Fast Micro-Action -> Use a Deep, Slow, Reflective Realization.
   - If the last hook mentioned an Action -> Start with a raw, relatable Human Emotion or Situation.
4. ZERO WORD OVERLAP: The first 5 words of Line 1 must NOT share any vocabulary or grammar pattern with the last hook.
5. NO HADITH PREFACE IN LINE 1: Line 1 must NEVER start with "রাসূলুল্লাহ (ﷺ) বলেছেন:" or "নবীজির শেখানো". Line 1 belongs purely to the relatable human struggle or situation. The Prophet's authentic Sunnah and Sahih citation belong in Line 2/3 and the structured caption points!

SERIES CONTEXT: "দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"

# ==============================================================================
# RULE #1 SUPREME MANDATE: ZERO TOLERANCE FOR ISLAMIC INACCURACY & HALLUCINATION
# ==============================================================================
RULE 0: ABSOLUTE ISLAMIC AUTHENTICITY & ANTI-HALLUCINATION (MANDATORY FIRST RULE):
1. NEVER MERGE HADITHS: Never combine multiple separate Hadiths into one quotation or under one reference. Keep distinct narrations separate with their own exact citations!
2. EXACT BOOK & HADITH NUMBER ONLY: Never write vague references like "সহীহ বুখারী ও মুসলিম" or "সহীহ হাদিস সমগ্র". Every single Hadith quote MUST have the exact specific book and Hadith number (e.g., "সহীহ বুখারী: ৬৩২৪", "জামে আত-তিরমিযী: ২৮৯১", "সহীহ মুসলিম: ৭০৭", "সুনানে আবু দাউদ: ১৪০০").
3. NO FABRICATED "ফলাফল" OR PROMISES: Never invent unverified summary promises like "যে ব্যক্তি এটি করবে সে আল্লাহর আশ্রয়ে থাকবে এবং জান্নাতের সুসংবাদ পাবে". Only state what the Prophet (ﷺ) explicitly stated in the cited Hadith!
4. AUTHENTIC DUAS ONLY: Arabic Dua must be 100% authentic with accurate Bengali pronunciation and genuine meaning.

THE 4 CORE PSYCHOLOGY HOOK RULES (MANDATORY):
Rule 1: Hook Diversity (STRICT ANTI-MONOTONY RULE):
  - ❌ STRICTLY BANNED: NEVER start every single hook with "রাসূলুল্লাহ (ﷺ) বলেছেন: মাত্র ৫ সেকেন্ডের...". That makes the channel look like an automated bot!
  - ✅ ROTATE AMONG THESE 5 DIVERSE HOOK ARCHETYPES:
    • Archetype 1 (Situational / Emotion First): "মন যখন অতিরিক্ত দুশ্চিন্তায় ভারী হয়ে ওঠে...", "প্রচণ্ড রেগে গিয়ে যখন নিজেকে সামলানো যায় না...", "ঘরে প্রবেশের সময় মাত্র ৫ সেকেন্ডের ১টি সুন্নাত..."
    • Archetype 2 (Curiosity Question): "নামাজে দাঁড়ালেই কি মন হাজারটা চিন্তায় হারিয়ে যায়?", "ঘুমের আগে শেষ কোন কাজটি করলে সারারাত আল্লাহর পাহারা মেলে?", "বিপদে পড়লে নবীজি (ﷺ) তাৎক্ষণিক কী করতে বলতেন?"
    • Archetype 3 (Prophetic Habit / Teaching): "নবীজির (ﷺ) শেখানো অত্যন্ত প্রিয় ১টি সুন্নাহ আমল...", "সাহাবীদের কঠিন অর্থকষ্টে রাসূলুল্লাহ (ﷺ) কী শিখিয়েছিলেন?", "রাসূলুল্লাহ (ﷺ) বলেছেন: এমন ১টি সহজ আমল আছে..."
    • Archetype 4 (Common Habit / Contrast): "আমরা অনেকেই প্রতিদিন অজান্তেই এই ভুলটি করে ফেলি...", "খাওয়ার সময় যে ছোট ১টি ভুল শয়তানকে ডেকে আনে..."
    • Archetype 5 (Action-First): "মাত্র ১টি ছোট বাক্য যা আপনার জীবনে বরকতের দুয়ার খুলে দেবে..."

Rule 2: Promise High Gain with Micro Effort (STRICT LOW-FRICTION RULE):
  - ❌ STRICTLY BANNED: NEVER mention large numbers like "৩০টি আয়াত", "১০০ বার", "৫০ বার".
  - ✅ ALWAYS USE EFFORTLESS FRAMING: "মাত্র ১টি আমল", "ছোট ১টি সূরা", "মাত্র ৩০ সেকেন্ডের দোয়া", "১টি ছোট সুন্নাত".
Rule 3: Target a Pain Point or Deep Desire: Anchor in real daily emotions (মনের অশান্তি, রাগ, ঋণের চাপ, পরিবারের অমিল, নামাজের একাগ্রতা).
Rule 4: Leave the Loop Open (End with unfinished promise "...যা নিয়মিত করলে আল্লাহ মনের অশান্তি দূর করে দেন").
- ❌ STRICTLY BANNED HOOK CLICHÉS: NEVER use "ভাগ্যের তালা খুলে দেবে", "ভাগ্য বদলে দেবে".

CRITICAL GOLDEN HIGHLIGHT RULES (MANDATORY):
In "highlight_words", you MUST provide 3 to 4 exact phrases from your lines covering:
1. The Core Focus / Subject (e.g. "মন অতিরিক্ত দুশ্চিন্তায়", "প্রচণ্ড রেগে গেলে", "নবীজির (ﷺ) প্রিয় সুন্নাত")
2. The Divine Name: "আল্লাহ" or "আল্লাহর"
3. The Action: e.g. "১টি আমল", "ছোট এই দোয়াটি", "১টি সুন্নাত"
4. The Outcome: e.g. "মুহূর্তেই শান্তি নেমে আসে", "সব সংকট দূর করে দেন", "অভাব দূর হবে"

PROVEN DIVERSE HOOK EXAMPLES TO MODEL AFTER:
• Model A (Situational Emotional Hook):
  line_1: "মন যখন অতিরিক্ত দুশ্চিন্তায় ভারী হয়ে ওঠে,"
  line_2: "নবীজির (ﷺ) শেখানো ছোট এই ১টি আমল করুন,"
  line_3: "মুহূর্তেই হৃদয়ে গভীর প্রশান্তি নেমে আসবে..."
  highlight_words: ["অতিরিক্ত দুশ্চিন্তায়", "নবীজির (ﷺ) শেখানো", "ছোট এই ১টি আমল", "গভীর প্রশান্তি"]

• Model B (Curiosity Question Hook):
  line_1: "নামাজে দাঁড়ালেই কি মন দুনিয়ার চিন্তায় হারিয়ে যায়?"
  line_2: "রাসূলুল্লাহর (ﷺ) শেখানো এই ১টি কৌশল মানলে"
  line_3: "শয়তানের কোনো ওয়াসওয়াসা আর প্রভাব ফেলতে পারবে না..."
  highlight_words: ["নামাজে দাঁড়ালেই কি", "রাসূলুল্লাহর (ﷺ) শেখানো", "১টি কৌশল", "কোনো ওয়াসওয়াসা"]

• Model C (Prophetic Habit Hook):
  line_1: "সাহাবীদের চরম আর্থিক সংকটে নবীজি (ﷺ)"
  line_2: "নিয়মিত যে ১টি বিশেষ দোয়া পাঠ করতে বলতেন,"
  line_3: "যা পাঠ করলে আল্লাহ অভাব দূর করে দেন..."
  highlight_words: ["চরম আর্থিক সংকটে", "নবীজি (ﷺ)", "১টি বিশেষ দোয়া", "অভাব দূর করে দেন"]

• Model D (Family & Home Barakah Hook):
  line_1: "ঘরে প্রবেশের সময় মাত্র ৫ সেকেন্ডের এই ১টি সুন্নাত মানলে"
  line_2: "আল্লাহ পরিবারে অভাব ও অশান্তি দূর করে দেন,"
  line_3: "যা রাসূলুল্লাহ (ﷺ) সাহাবীদের বিশেষ উপদেশ দিয়েছিলেন..."
  highlight_words: ["৫ সেকেন্ডের এই ১টি সুন্নাত", "আল্লাহ", "অভাব ও অশান্তি দূর", "রাসূলুল্লাহ (ﷺ)"]

CRITICAL DUA & CAPTION RULES (MANDATORY):
1. Complete Arabic Dua: The caption MUST contain full Arabic text with Tashkeel, accurate phonetic Bengali pronunciation (উচ্চারণ), authentic Bengali meaning (অর্থ), and Sahih Book Reference.
2. Value-Packed Caption: Point-by-point breakdown with exact references (সহীহ বুখারী / সহীহ মুসলিম / জামে আত-তিরমিযী / সহীহ আন-নাসায়ী / সহীহ ইবনে মাজাহ).
3. Community Dhikr CTA + Follow Credit: 👉 @dailydos_islam

TOPICS RECENTLY COVERED (DO NOT REPEAT):
- {avoid_context}

Output ONLY valid JSON:
{{
    "series_title": "দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}",
    "title_bn": "ফজরের পর এই ৩টি আমল করুন এবং দেখুন কীভাবে আল্লাহ আপনার পুরো দিনকে বরকতে ভরিয়ে দেন",
    "title_en": "Do these 3 things after Fajr and watch Allah fill your day with barakah #Shorts",
    "line_1": "ফজরের পর এই ৩টি আমল করুন",
    "line_2": "এবং দেখুন কীভাবে আল্লাহ আপনার",
    "line_3": "পুরো দিনকে বরকতে ভরিয়ে দেন।",
    "highlight_words": ["৩টি আমল", "আল্লাহ", "বরকতে ভরিয়ে দেন"],
    "caption_points": [
        {{
            "number": "১",
            "title": "আয়াতুল কুরসী পাঠ করা",
            "hadith": "রাসূলুল্লাহ (ﷺ) বলেছেন: 'যে ব্যক্তি প্রতি ফরজ নামাজের পর আয়াতুল কুরসী পাঠ করবে, তার জান্নাতে প্রবেশের মাঝে মৃত্যু ছাড়া আর কোনো বাধা থাকবে না।'",
            "reference": "সহীহ আন-নাসায়ী: ৯৯২৮"
        }},
        {{
            "number": "২",
            "title": "রিজিক ও বরকতের খাস দোয়া",
            "arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا",
            "pronunciation": "আল্লাহুম্মা ইন্নি আসআলুকা ইলমান নাফেআ, ওয়া রিযকান তায়্যিবা, ওয়া আমালান মুতাক্বাব্বালা।",
            "meaning": "হে আল্লাহ! আমি আপনার কাছে উপকারী জ্ঞান, পবিত্র রিজিক এবং কবুলযোগ্য আমল প্রার্থনা করছি।",
            "reference": "সহীহ ইবনে মাজাহ: ৯২৫"
        }},
        {{
            "number": "৩",
            "title": "সকাল-সন্ধ্যার তাসবীহের ফযিলত",
            "hadith": "রাসূলুল্লাহ (ﷺ) বলেছেন: 'যে ব্যক্তি সকাল এবং সন্ধ্যায় ১০০ বার সুবহানাল্লাহি ওয়া বিহামদিহি পাঠ করবে, কিয়ামতের দিন তার চেয়ে উত্তম আমল নিয়ে আর কেউ উপস্থিত হতে পারবে না।'",
            "reference": "সহীহ মুসলিম: ২৬৯২"
        }}
    ],
    "dhikr_word": "সুবহানাল্লাহ",
    "visual_prompt": "{cfg['visual_prompt']}",
    "tags": ["Islam", "DailyReminder", "Sunnah", "সহীহ_হাদিস", "দোয়া", "DailyDos"]
}}"""

def generate_loop_reel_content(slot_key: str = None) -> dict:
    """Generates viral 7-second curiosity hook and high-value point-by-point caption with dynamic deduplication."""
    if not slot_key or slot_key not in SLOT_CONFIGS:
        slot_key = determine_current_slot()
    
    cfg = SLOT_CONFIGS[slot_key]
    logger.info(f"Targeting {cfg['name']} ({cfg['theme']})")

    # Fetch recent topics to ensure zero duplication
    recent_titles = get_recent_video_titles(limit=100)
    avoid_context = "\n- ".join(recent_titles[:30]) if recent_titles else "None"

    # Calculate Series Episode Number
    ep_int, ep_bn = get_next_episode_number()

    # Extract last hook to contrast against
    last_entry = recent_titles[0] if recent_titles else ""
    last_hook_text = last_entry.split("| Hook:")[-1].strip() if "| Hook:" in last_entry else (last_entry.split("]")[-1].strip() if "]" in last_entry else last_entry)

    from app.history import check_topic_duplicate_global_detail
    from app.quality.islamic_verifier import verify_and_enforce_islamic_accuracy

    banned_hadiths = set()
    last_fail_reason = ""
    max_attempts = 7

    for attempt in range(max_attempts):
        # Dynamic Angle & Tone Rotation across attempts to break deadlocks
        angle_idx = (ep_int + attempt) % len(ANGLES)
        tone_idx = (ep_int + attempt) % len(TONES)
        target_angle = ANGLES[angle_idx]
        target_tone = TONES[tone_idx]

        logger.info(f"Attempt {attempt+1}/{max_attempts}: Angle '{target_angle['name']}' | Tone '{target_tone}' for Episode #{ep_bn}...")

        system_prompt = build_loop_reel_system_prompt(
            ep_bn=ep_bn,
            target_angle=target_angle,
            target_tone=target_tone,
            last_hook_text=last_hook_text,
            avoid_context=avoid_context,
            cfg=cfg
        )

        user_prompt = (
            f"Target Slot: {cfg['name']}\n"
            f"Required Slot Theme: {cfg['theme']}\n"
            f"Slot Content Guidance: {cfg['system_instruction']}\n"
            f"Series Episode: {ep_bn}. Assigned Angle: '{target_angle['name']}' ({target_angle['desc']}). Tone: '{target_tone}'.\n"
            f"Select 1 deeply important Sunnah teaching of the Prophet (ﷺ) solving a vital daily life struggle matching the slot theme. "
            f"Ensure 100% authentic Sahih Hadith with exact book and number (e.g., সহীহ বুখারী: ১২৩৪ or সহীহ মুসলিম: ৫৬৭), full Arabic Dua with Tashkeel, Bengali pronunciation, and meaning. "
            f"Do NOT select any topic/Hadith from the avoided list. Return valid JSON only."
        )

        if banned_hadiths or last_fail_reason:
            banned_list_str = "; ".join(sorted(list(banned_hadiths))[:12])
            user_prompt += (
                f"\n\n[CRITICAL CORRECTION FROM PREVIOUS ATTEMPT]:\n"
                f"{last_fail_reason}\n"
                f"STRICTLY FORBIDDEN TOPICS / HADITHS (ALREADY USED): {banned_list_str}.\n"
                f"You MUST choose a COMPLETELY DIFFERENT authentic Hadith and Sunnah deed from another chapter/book!"
            )

        content = extract_json(system_prompt, user_prompt, max_tokens=1500)
        if not content:
            logger.warning(f"Attempt {attempt+1}: Failed to parse valid Loop Reel JSON from LLM. Retrying...")
            last_fail_reason = "Failed to parse valid JSON from LLM response. Return strictly valid JSON."
            continue
            
        title_bn = content.get("title_bn", "").strip()
        pts_text = " ".join([f"{pt.get('title', '')} {pt.get('hadith', '')} {pt.get('reference', '')}" for pt in content.get("caption_points", [])])
        full_check_text = f"{title_bn} {content.get('arabic', '')} {pts_text}"

        is_dup_title, reason_title = check_topic_duplicate_global_detail(title_bn)
        is_dup_full, reason_full = check_topic_duplicate_global_detail(full_check_text)

        if is_dup_title or is_dup_full:
            dup_reason = reason_title or reason_full
            logger.warning(f"Attempt {attempt+1}: Loop Reel topic flagged as duplicate: {dup_reason}")
            if title_bn:
                banned_hadiths.add(title_bn)
            for pt in content.get("caption_points", []):
                ref = pt.get("reference", "").strip()
                if ref:
                    banned_hadiths.add(ref)
                pt_title = pt.get("title", "").strip()
                if pt_title:
                    banned_hadiths.add(pt_title)
            for num in re.findall(r'\d+', dup_reason):
                banned_hadiths.add(f"Hadith #{num}")
            past_match = re.search(r"'(.*?)'", dup_reason)
            if past_match:
                banned_hadiths.add(past_match.group(1)[:50])
            last_fail_reason = f"Duplicate topic or Hadith detected: {dup_reason}"
            continue
            
        # Check that complete Arabic Dua is included
        has_arabic = any(pt.get("arabic") and (pt.get("meaning") or pt.get("pronunciation")) for pt in content.get("caption_points", []))
        if not has_arabic and not content.get("arabic"):
            logger.warning(f"Attempt {attempt+1}: Generated content is missing mandatory complete Arabic Dua/Meaning! Retrying...")
            last_fail_reason = "MANDATORY: Must include full Arabic Dua with Tashkeel, Bengali pronunciation, and meaning in caption_points."
            continue

        # HOOK DIVERSITY & ANTI-MONOTONY VALIDATION
        is_diverse, monotony_reason = check_hook_monotony(content, recent_titles, last_hook_text=last_hook_text)
        if not is_diverse:
            logger.warning(f"Attempt {attempt+1}: Hook monotony check failed: {monotony_reason}. Retrying...")
            last_fail_reason = f"Hook monotony check failed: {monotony_reason}. Target Angle: '{target_angle['name']}'. Ensure Line 1 opens with a relatable human situation/emotion without any Hadith preface."
            continue

        # RULE #1 SUPREME 5-PASS ISLAMIC VERIFICATION ENGINE
        is_accurate, fail_reason, validated_content = verify_and_enforce_islamic_accuracy(content)
        if not is_accurate:
            logger.warning(f"Attempt {attempt+1} REJECTED by Islamic 5-Pass Verifier: {fail_reason}. Retrying...")
            last_fail_reason = f"Islamic Authenticity Check Failed: {fail_reason}. Ensure 100% authentic Sahih Hadith, exact book and number, and zero conflation."
            for pt in content.get("caption_points", []):
                ref = pt.get("reference", "").strip()
                if ref:
                    banned_hadiths.add(ref)
            continue

        content = validated_content
        content["slot_key"] = slot_key
        content["episode_number"] = ep_int
        content["episode_bn"] = ep_bn
        if not content.get("series_title"):
            content["series_title"] = f"দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"
        return content

    raise RuntimeError(f"Failed to generate a 100% verified, authentic, non-duplicate Loop Reel after {max_attempts} rigorous checks.")

def clean_hadith_body(text: str) -> str:
    """Strips duplicate leading authority prefixes and quotes so caption never stutters."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r'^[“"\'‘\s]+', '', t).strip()
    prefixes = [
        r'^(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*\([ﷺসা\.]+\)\s*বলেছেন\s*[:ঃ\-–—\s]*',
        r'^(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*বলেছেন\s*[:ঃ\-–—\s]*',
        r'^(?:হাদিসে|হাদীসে|হাদিস\s*শরীফে)\s*এসেছে\s*[:ঃ\-–—\s]*',
    ]
    for p in prefixes:
        t = re.sub(p, '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'^[“"\'‘\s]+', '', t).strip()
    t = re.sub(r'[”"\'’\s]+$', '', t).strip()
    return t

def format_loop_caption(data: dict) -> str:
    """Short, punchy, high-converting caption with complete Dua/Ayah and Series Branding."""
    title_bn = data.get("title_bn", "").strip()
    series_title = data.get("series_title", "দৈনন্দিন সহীহ আমল")
    dhikr = data.get("dhikr_word", "সুবহানাল্লাহ")
    pts = data.get("caption_points", [])

    # SERIES BRANDING & HOOK HEADER
    caption = f"✨ {series_title} ✨\n"
    hook = data.get("line_1", title_bn).strip()
    if data.get("line_2"):
        hook = hook + " " + data.get("line_2", "").strip()
    caption += hook + " 🤲\n\n"

    bn_nums = ["১", "২", "৩", "৪", "৫"]
    for idx, pt in enumerate(pts):
        num_str = pt.get("number") or (bn_nums[idx] if idx < len(bn_nums) else str(idx + 1))
        title = pt.get("title", "").strip().replace("ফলাফল", "আমলের শিক্ষা ও ফযিলত")
        hadith = pt.get("hadith", "").strip()
        arabic = pt.get("arabic", "").strip()
        pron = pt.get("pronunciation", "").strip()
        meaning = pt.get("meaning", "").strip()
        ref = pt.get("reference", "").strip()
        note = pt.get("note", "").strip()

        if title:
            caption += f"{num_str}. {title}:\n"
        elif hadith or arabic:
            caption += f"{num_str}. আমল:\n"

        if hadith:
            caption += f"“{clean_hadith_body(hadith)}”\n"

        if ref and not arabic:
            caption += f"📚 [{ref}]\n"

        if arabic:
            caption += f"{arabic}\n\n"
            if pron:
                caption += f"🗣️ উচ্চারণ: “{pron}”\n\n"
            if meaning:
                caption += f"🌿 অর্থ: “{meaning}”\n\n"
            if ref:
                caption += f"📚 [{ref}]\n"

        if note:
            caption += f"*(উল্লেখ্য: {note})*\n"

        caption += "\n"

    # CLEAR CTA & AUTHENTIC SUNNAH DAWAH TRIGGER
    caption += (
        "📌 নিয়মিত আমল করার জন্য রিলটি 🔖 Save করে রাখুন।\n"
        "🤍 সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন।\n"
        "রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন: @dailydos_islam\n\n"
    )

    # Clean replacement of unverified/inappropriate terms
    caption = caption.replace("অলৌকিক ৩টি পুরস্কার", "অসাধারণ ৩টি ফযিলত ও পুরস্কার")
    caption = caption.replace("অলৌকিক পুরস্কার", "অসাধারণ ফযিলত ও পুরস্কার")
    caption = caption.replace("অলৌকিক", "শক্তিশালী ও বরকতময়")

    # HASHTAGS
    core_tags = [
        "IslamicReminders", "Sunnah", "DailyDos",
        "সহীহ_হাদিস", "দ্বীন_ইসলাম", "ইসলামিক_পোস্ট",
        "QuranAndSunnah", "MuslimUmmah", "DeenOverDunya",
        "Alhamdulillah", "Shorts", "Reels", "ViralReels"
    ]
    slot_tags = [
        t.strip("#").strip() for t in data.get("tags", [])
        if t.strip("#").strip() not in core_tags and len(t.strip("#").strip()) > 1
    ]
    all_tags = core_tags + slot_tags[:5]
    tags = " ".join(["#" + t for t in all_tags])
    return (caption + tags).strip()


def render_loop_reel_video(content: dict, output_dir: str = "data/output") -> str:
    """Renders 60 FPS buttery smooth 1.22x continuous zoom video with Series Branding & Visual Follow Trigger."""
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp", "loop_reel_run")
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Background image generation with TRIPLE-CHECK VISION GUARDIAN (Checks 3 times over)
    from app.quality.vision_guardian import generate_verified_human_free_background, get_certified_safe_fallback
    bg_path = os.path.join(temp_dir, "background.jpg")
    visual_p = content.get("visual_prompt", SLOT_CONFIGS["slot_1_morning"]["visual_prompt"])
    
    downloaded = generate_verified_human_free_background(visual_p, bg_path, max_checks=3)
    if not downloaded or not os.path.exists(bg_path) or os.path.getsize(bg_path) < 5000:
        logger.warning("[Vision Guardian] Deploying certified human-free fallback background.")
        get_certified_safe_fallback(bg_path)

    # 2. Authentic Quran Audio with 30-Video Anti-Repetition Guarantee & Topic Alignment
    topic_keywords = f"{content.get('title_bn', '')} {content.get('theme', '')} {content.get('line_1', '')} {content.get('line_2', '')}"
    audio_path = get_or_download_quran_audio(topic_text=topic_keywords, duration=8.0)

    # 3. Build ASS Subtitle matching Reference Post (Top Series Badge, Golden Highlights, Caption CTA, Follow Trigger)
    series_badge = content.get("series_title", f"দৈনন্দিন সহীহ আমল • পর্ব {content.get('episode_bn', '১')}")
    if not series_badge.startswith("✦"):
        series_badge = f"✦ {series_badge} ✦"

    l1 = content.get("line_1", "").strip()
    l2 = content.get("line_2", "").strip()
    l3 = content.get("line_3", "").strip()
    
    hw_list = content.get("highlight_words", ["৩টি আয়াত", "আল্লাহ", "রক্ষা করবেন"])
    full_hook_text = f"{l1}\\N{l2}\\N{l3}" if l2 else l1
    if l3 and l3 not in full_hook_text:
        full_hook_text += f"\\N{l3}"
    
    # Apply Vibrant Golden/Yellow highlighting (&H002BD5FF&) to keywords
    GOLD_COLOR = "&H002BD5FF&"
    WHITE_COLOR = "&H00FFFFFF&"
    
    # Sort hw_list by longest string first so longer phrases match before substrings
    hw_list = sorted(hw_list, key=len, reverse=True)
    
    for hw in hw_list:
        hw_clean = hw.strip()
        if not hw_clean:
            continue
        if hw_clean in full_hook_text:
            full_hook_text = full_hook_text.replace(hw_clean, f"{{\\c{GOLD_COLOR}}}{hw_clean}{{\\c{WHITE_COLOR}}}", 1)

    ass_path = os.path.join(temp_dir, "overlay.ass")
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SeriesBadge,Noto Sans Bengali,38,&H002BD5FF&,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,3.2,2.2,8,60,60,220,1
Style: MainHook,Noto Sans Bengali,62,&H00FFFFFF&,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,4.5,3.0,5,70,70,0,1
Style: CaptionCTA,Noto Sans Bengali,44,&H002BD5FF&,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,3.5,2.5,2,60,60,420,1
Style: FollowTrigger,Noto Sans Bengali,32,&H00FFFFFF&,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,2.8,2.0,2,60,60,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:08.00,SeriesBadge,,0,0,0,,{{\\fnNoto Sans Bengali\\fs38\\b1\\c{GOLD_COLOR}}}{series_badge}
Dialogue: 0,0:00:00.00,0:00:08.00,MainHook,,0,0,0,,{{\\fnNoto Sans Bengali\\fs62\\b1\\c{WHITE_COLOR}}}{full_hook_text}
Dialogue: 0,0:00:00.00,0:00:08.00,CaptionCTA,,0,0,0,,{{\\fnNoto Sans Bengali\\fs44\\b1\\c{GOLD_COLOR}}}☞ বিস্তারিত ক্যাপশনে পড়ুন 👇{{\\c{WHITE_COLOR}}}
Dialogue: 0,0:00:00.00,0:00:08.00,FollowTrigger,,0,0,0,,{{\\fnNoto Sans Bengali\\fs32\\b1\\c{WHITE_COLOR}}}প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন ☞ @dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    rel_ass = os.path.relpath(ass_path).replace("\\", "/")

    # 4. Render 60 FPS Sub-pixel Lanczos continuous zoom video (Clean typography directly over Islamic visual)
    output_video = os.path.join(output_dir, f"loop_reel_{content.get('slot_key', 'slot')}_{int(time.time())}.mp4")
    
    base_img = Image.open(bg_path).convert("RGB")
    base_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS)
    orig_w, orig_h = base_img.size

    fps = 60
    duration = 6.0   # Match audio length (~6s) to avoid BrokenPipe from -shortest
    total_frames = int(fps * duration)
    zoom_total = 0.22  # 1.22x continuous monotonic push-in

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{orig_w}x{orig_h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", audio_path,
        "-vf", f"subtitles='{rel_ass}'",
        "-c:v", "libx264",
        "-crf", "16",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_video
    ]

    logger.info(f"Rendering 60 FPS Lanczos Loop Reel to {output_video}...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for i in range(total_frames):
        if proc.poll() is not None:
            break  # FFmpeg exited early (e.g. audio ended), stop writing frames
        p = i / float(total_frames - 1) if total_frames > 1 else 0.0
        current_scale = 1.0 + (zoom_total * p)
        
        crop_w = orig_w / current_scale
        crop_h = orig_h / current_scale
        crop_x = (orig_w - crop_w) / 2.0
        crop_y = (orig_h - crop_h) / 2.0
        
        cropped = base_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        frame = cropped.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        try:
            proc.stdin.write(frame.tobytes())
        except (BrokenPipeError, OSError):
            break  # FFmpeg closed stdin, stop gracefully

    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()

    logger.info(f"Successfully rendered 60 FPS Loop Reel: {output_video}")
    return output_video

def run_loop_reel_pipeline(slot_key: str = None) -> bool:
    """End-to-end execution: generation -> rendering -> upload -> Supabase recording."""
    logger.info("=== STARTING AESTHETIC LOOP REEL PIPELINE ===")
    
    # 1. Generate content
    content = generate_loop_reel_content(slot_key)
    caption = format_loop_caption(content)
    
    # 2. Render video
    video_path = render_loop_reel_video(content)
    
    # 3. Prepare metadata
    yt_title = content.get("title_bn", "ইসলামিক রিলস")
    if "#Shorts" not in yt_title and "#shorts" not in yt_title:
        yt_title = f"{yt_title} #Shorts"
        
    pinned_comment = (
        f"পরবর্তীতে আমল করার জন্য রিলটি Save করে রাখুন এবং সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন—"
        f"রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿"
    )

    # 4. Upload to YouTube Shorts
    metadata = {
        "youtube_title": yt_title,
        "description": caption,
        "pinned_comment": pinned_comment,
        "tags": content.get("tags", ["Shorts", "Islam", "DailyDos"])
    }
    
    yt_ok = upload_to_youtube(video_path, metadata)
    logger.info(f"YouTube Shorts Upload: {yt_ok}")

    # 5. Upload to Facebook & Instagram Reels
    fb_ok = upload_to_facebook(video_path, metadata, video_type="reel")
    logger.info(f"Facebook / Instagram Upload: {fb_ok}")

    # 6. Upload to TikTok
    from app.upload.tiktok import upload_to_tiktok
    tiktok_res = upload_to_tiktok(video_path, caption=yt_title, tags=content.get("tags", []))
    logger.info(f"TikTok Upload: {tiktok_res.get('status')}")

    # 7. Save to Supabase for series tracking and zero-topic repetition
    hook_str = content.get("line_1", "").strip()
    full_title_for_history = f"[পর্ব {content.get('episode_bn', '')}] {content.get('title_bn', '')} | Hook: {hook_str}"
    record_payload = {
        "id": f"loop_{content.get('slot_key', 'slot')}_{int(time.time())}",
        "title": full_title_for_history,
        "source": "loop_reel_series"
    }
    _supabase_insert(record_payload)
    logger.info(f"Saved Loop Reel Episode {content.get('episode_bn', '')} to Supabase: '{content.get('title_bn')}'")

    logger.info("=== LOOP REEL PIPELINE COMPLETED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    import sys
    slot = sys.argv[1] if len(sys.argv) > 1 else None
    run_loop_reel_pipeline(slot)
