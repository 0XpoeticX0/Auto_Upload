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
    """Calculates the current peak slot based on BST (UTC+6) time (2 runs per day)."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_bst = now_utc + datetime.timedelta(hours=6)
    hour = now_bst.hour

    if 3 <= hour < 15:
        return "slot_1_morning"
    else:
        return "slot_2_evening"

def generate_loop_reel_content(slot_key: str = None) -> dict:
    """Generates viral 7-second curiosity hook and high-value point-by-point caption with deduplication."""
    if not slot_key or slot_key not in SLOT_CONFIGS:
        slot_key = determine_current_slot()
    
    cfg = SLOT_CONFIGS[slot_key]
    logger.info(f"Targeting {cfg['name']} ({cfg['theme']})")

    # Fetch recent topics to ensure zero duplication
    recent_titles = get_recent_video_titles(limit=60)
    avoid_context = "\n- ".join(recent_titles[:30]) if recent_titles else "None"

    # Calculate Series Episode Number and 30-Day Diverse Curriculum Topic
    ep_int, ep_bn = get_next_episode_number()
    from app.curriculum import get_curriculum_for_episode
    curriculum = get_curriculum_for_episode(ep_int)
    
    logger.info(f"Targeting 30-Day Curriculum Day #{curriculum['day']}: {curriculum['theme']} ({curriculum['reference']})")

    system_prompt = f"""You are a master viral Islamic content creator specializing in the high-retention "7-Second Aesthetic Loop + High-Value Point-by-Point Caption" Reel format.

TODAY'S MANDATORY 30-DAY CURRICULUM TOPIC (100% UNIQUE, NO REPETITION):
- Day #{curriculum['day']}/30: {curriculum['theme']}
- Category: {curriculum['category']}
- Hadith Focus: {curriculum['hadith_core']}
- Exact Sahih Citation: {curriculum['reference']}
- Suggested Hook Model:
  Line 1: "{curriculum['hook_line_1']}"
  Line 2: "{curriculum['hook_line_2']}"
SERIES CONTEXT: "দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"

# ==============================================================================
# RULE #1 SUPREME MANDATE: ZERO TOLERANCE FOR ISLAMIC INACCURACY & HALLUCINATION
# ==============================================================================
RULE 0: ABSOLUTE ISLAMIC AUTHENTICITY & ANTI-HALLUCINATION (MANDATORY FIRST RULE):
1. NEVER MERGE HADITHS: Never combine multiple separate Hadiths into one quotation or under one reference. E.g., Surah Sajdah before sleep (Tirmidhi 2892) and Surah Mulk grave protection (Tirmidhi 2891) are SEPARATE Hadiths. Keep distinct narrations separate with their own exact citations!
2. EXACT BOOK & HADITH NUMBER ONLY: Never write vague references like "সহীহ বুখারী ও মুসলিম" or "সহীহ হাদিস সমগ্র". Every single Hadith quote MUST have the exact specific book and Hadith number (e.g., "সহীহ বুখারী: ৬৩২৪", "জামে আত-তিরমিযী: ২৮৯১", "সহীহ মুসলিম: ৭০৭", "সুনানে আবু দাউদ: ১৪০০").
3. NO FABRICATED "ফলাফল" OR PROMISES: Never invent unverified summary promises like "যে ব্যক্তি এটি করবে সে আল্লাহর আশ্রয়ে থাকবে এবং জান্নাতের সুসংবাদ পাবে". Only state what the Prophet (ﷺ) explicitly stated in the cited Hadith!
4. AUTHENTIC DUAS ONLY: Arabic Dua must be 100% authentic with accurate Bengali pronunciation and genuine meaning.

THE 4 CORE PSYCHOLOGY HOOK RULES (MANDATORY):
Rule 1: Name the Authority First (MANDATORY in Line 1): Every hook MUST explicitly state who taught or promised this in Line 1 (e.g. "রাসূলুল্লাহ (ﷺ) বলেছেন:...", "নবীজির (ﷺ) শেখানো...", "আল্লাহ তায়ালা কুরআনে প্রতিশ্রুতি দিয়েছেন..."). ALWAYS use "(ﷺ)", NEVER "(সা.)". NEVER omit who taught it!
Rule 2: Promise High Gain with Micro Effort (STRICT LOW-FRICTION RULE):
  - ❌ STRICTLY BANNED: NEVER mention large, scary numbers like "৩০টি আয়াত", "১০০ বার", "৫০ বার", "১ ঘণ্টা". Viewers get scared of the effort and immediately swipe away!
  - ✅ ALWAYS USE EFFORTLESS MICRO-FRAMING: "মাত্র ১টি আমল", "ছোট ১টি সূরা", "মাত্র ৫ সেকেন্ডের দোয়া", "মাত্র ২ মিনিটের আমল", "১টি ছোট আয়াত". For Surah Mulk or long Surahs, say "ঘুমানোর আগে ছোট এই সূরাটি পড়ুন" or "মাত্র ২ মিনিটের এই আমলটি", NEVER "৩০টি আয়াত"!
Rule 3: Target a Pain Point or Deep Desire (Rizq/Money, Peace/Anxiety, Protection/Kaborer Azab)
Rule 4: Leave the Loop Open (End with unfinished promise "...যা পড়লে মনের চাওয়া আল্লাহ পূরণ করেন", "...যা আপনার ভাগ্য বদলে দিতে পারে")

CRITICAL GOLDEN HIGHLIGHT RULES (MANDATORY):
In "highlight_words", you MUST provide 3 to 4 exact phrases from your lines covering:
1. The Sacred Authority: "রাসূলুল্লাহ (ﷺ) বলেছেন:" or "নবীজির (ﷺ) শেখানো" (MUST BE HIGHLIGHTED IN GOLD whenever present!)
2. The Divine Name: "আল্লাহ" or "আল্লাহর" (MUST BE HIGHLIGHTED IN GOLD)
3. The Numbered Action: e.g. "১টি আমল", "ছোট এই সূরাটি", "৫ সেকেন্ডের দোয়া", "২ মিনিটের আমল" (MUST BE HIGHLIGHTED IN GOLD)
4. The Ultimate Reward/Outcome: e.g. "কখনো ফিরিয়ে দেন না", "সব বিপদ থেকে রক্ষা করবেন", "ভাগ্যের তালা খুলে দেয়", "সব দুশ্চিন্তা দূর করে দেবেন" (MUST BE HIGHLIGHTED IN GOLD)

PROVEN HOOK EXAMPLES TO MODEL AFTER:
• Model 1 (Mental Relief / Peace):
  line_1: "রাসূলুল্লাহ (ﷺ) বলেছেন: মন অশান্ত হলে"
  line_2: "মাত্র ৫ সেকেন্ডের এই দোয়াটি পড়ুন,"
  line_3: "আল্লাহ আপনার সমস্ত দুশ্চিন্তা দূর করে দেবেন..."
  highlight_words: ["রাসূলুল্লাহ (ﷺ) বলেছেন:", "৫ সেকেন্ডের এই দোয়াটি", "আল্লাহ", "সমস্ত দুশ্চিন্তা দূর করে দেবেন"]

• Model 2 (Guaranteed Dua / Isme Azam):
  line_1: "রাসূলুল্লাহ (ﷺ) বলেছেন: এমন ১টি দোয়া আছে"
  line_2: "যা পাঠ করলে আল্লাহ বান্দার কোনো চাওয়া"
  line_3: "কখনো ফিরিয়ে দেন না..."
  highlight_words: ["রাসূলুল্লাহ (ﷺ) বলেছেন:", "এমন ১টি দোয়া আছে", "আল্লাহ", "কখনো ফিরিয়ে দেন না"]

• Model 3 (Tahajjud / Late Night):
  line_1: "রাসূলের (ﷺ) শেখানো তাহাজ্জুদের ১টি আমল"
  line_2: "যা নিয়মিত পালন করলে আল্লাহ"
  line_3: "মনের যেকোনো অসম্ভব চাওয়া পূরণ করেন..."
  highlight_words: ["রাসূলের (ﷺ) শেখানো", "তাহাজ্জুদের ১টি আমল", "আল্লাহ", "যেকোনো অসম্ভব চাওয়া পূরণ করেন"]

• Model 4 (Family / Home Barakah):
  line_1: "রাসূলুল্লাহ (ﷺ) বলেছেন: ঘরে প্রবেশের সময়"
  line_2: "মাত্র ৫ সেকেন্ডের এই ১টি সুন্নত মানলে"
  line_3: "আল্লাহ পরিবারে অভাব ও অশান্তি দূর করে দেন..."
  highlight_words: ["রাসূলুল্লাহ (ﷺ) বলেছেন:", "৫ সেকেন্ডের এই ১টি সুন্নত", "আল্লাহ", "অভাব ও অশান্তি দূর করে দেন"]

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
    "visual_prompt": "{curriculum.get('visual_prompt', cfg['visual_prompt'])}",
    "tags": ["Islam", "DailyReminder", "Sunnah", "সহীহ_হাদিস", "দোয়া", "DailyDos"]
}}"""

    from app.history import is_topic_duplicate_global
    from app.quality.islamic_verifier import verify_and_enforce_islamic_accuracy

    base_user_prompt = f"Generate 1 high-CTR viral Islamic Loop Reel for Day #{curriculum['day']} of the 30-Day Sunnah Curriculum: '{curriculum['theme']}'. Series episode: {ep_bn}. Use the exact authentic Sahih Hadith reference: {curriculum['reference']}. Return valid JSON only."
    user_prompt = base_user_prompt

    for attempt in range(5):
        content = extract_json(system_prompt, user_prompt, max_tokens=1500)
        if not content:
            logger.warning(f"Attempt {attempt+1}: Failed to parse valid Loop Reel JSON from LLM. Retrying...")
            continue
            
        title_bn = content.get("title_bn", "").strip()
        if is_topic_duplicate_global(title_bn):
            logger.warning(f"Loop Reel topic '{title_bn}' flagged as duplicate in global history! Retrying with a fresh topic...")
            user_prompt = base_user_prompt + f"\nPrevious topic '{title_bn}' was duplicate. Choose a completely different Sahih Amal."
            continue
            
        # Check that complete Arabic Dua is included
        has_arabic = any(pt.get("arabic") and (pt.get("meaning") or pt.get("pronunciation")) for pt in content.get("caption_points", []))
        if not has_arabic and not content.get("arabic"):
            logger.warning(f"Attempt {attempt+1}: Generated content is missing mandatory complete Arabic Dua/Meaning! Retrying...")
            user_prompt = base_user_prompt + "\nMANDATORY: Must include full Arabic Dua with pronunciation and meaning in caption_points."
            continue

        # RULE #1 SUPREME 5-PASS ISLAMIC VERIFICATION ENGINE
        is_accurate, fail_reason, validated_content = verify_and_enforce_islamic_accuracy(content)
        if not is_accurate:
            logger.warning(f"Attempt {attempt+1} REJECTED by Islamic 5-Pass Verifier: {fail_reason}. Retrying...")
            user_prompt = base_user_prompt + f"\nCRITICAL CORRECTION (CHECK FAILED): {fail_reason}. You MUST fix this error immediately. Ensure 100% authentic Sahih Hadith, exact book and number, and zero conflation."
            continue

        content = validated_content
        content["slot_key"] = slot_key
        content["episode_number"] = ep_int
        content["episode_bn"] = ep_bn
        if not content.get("series_title"):
            content["series_title"] = f"দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"
        return content

    raise RuntimeError("Failed to generate a 100% verified, authentic, non-duplicate Loop Reel after 5 rigorous checks.")

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

    # KEY HADITH QUOTE (first point)
    if pts:
        pt = pts[0]
        if pt.get("hadith"):
            clean_h = clean_hadith_body(pt["hadith"])
            caption += "📖 হাদীস শরীফে এসেছে:\n"
            caption += "“" + clean_h + "”\n"
            if pt.get("reference"):
                caption += "📚 [" + pt["reference"] + "]\n"
            caption += "\n"

    # Determine Dua vs. Quranic Ayah Header
    combined_ctx = (title_bn + " " + hook + " " + data.get("arabic", "")).lower()
    is_quranic = any(k in combined_ctx for k in ["সূরা", "সুরা", "আয়াত", "আয়াত", "আয়াতুল কুরসী", "কুরআন", "কোরআন"])
    dua_header = "📖 সূরার বরকতময় আয়াত:" if is_quranic else "🤲 পূর্ণাঙ্গ দোয়া:"

    # COMPLETE ARABIC DUA / AYAH
    dua_found = False
    for pt in pts:
        if pt.get("arabic"):
            caption += f"{dua_header}\n" + pt["arabic"].strip() + "\n\n"
            if pt.get("pronunciation"):
                caption += "🗣️ উচ্চারণ: “" + pt["pronunciation"].strip() + "”\n\n"
            if pt.get("meaning"):
                caption += "🌿 অর্থ: “" + pt["meaning"].strip() + "”\n\n"
            if pt.get("reference") and pt != pts[0]:
                caption += "📚 [" + pt["reference"].strip() + "]\n\n"
            dua_found = True
            break

    # If top-level arabic keys exist
    if not dua_found and data.get("arabic"):
        caption += f"{dua_header}\n" + data["arabic"].strip() + "\n\n"
        if data.get("pronunciation"):
            caption += "🗣️ উচ্চারণ: “" + data["pronunciation"].strip() + "”\n\n"
        if data.get("meaning"):
            caption += "🌿 অর্থ: “" + data["meaning"].strip() + "”\n\n"
        if data.get("reference"):
            caption += "📚 [" + data["reference"].strip() + "]\n\n"

    # PRACTICAL TIP (2nd non-arabic point)
    for pt in pts[1:]:
        if pt.get("hadith") and not pt.get("arabic"):
            clean_tip = clean_hadith_body(pt["hadith"])
            tip_title = pt.get("title", "আমলের নিয়ম").replace("ফলাফল", "আমলের তাৎপর্য ও শিক্ষা")
            caption += "💡 " + tip_title + ":\n" + clean_tip + "\n\n"
            if pt.get("reference") and pt.get("reference").strip() not in ["সহীহ বুখারী ও মুসলিম", "সহীহ হাদিস সমগ্র"]:
                caption += "📚 [" + pt["reference"] + "]\n\n"
            break

    # CLEAR CTA & AUTHENTIC SUNNAH DAWAH TRIGGER
    caption += (
        "📌 নিয়মিত আমল করার জন্য রিলটি 🔖 Save করে রাখুন।\n"
        "🤍 সহীহ আমলের দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন।\n"
        "রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩]\n\n"
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
        
    fb_title = content.get("title_bn", "ইসলামিক রিলস")
    pinned_comment = f"পরবর্তীতে আমল করার জন্য রিলটি Save করে রাখুন এবং কমেন্টে একবার '{content.get('dhikr_word', 'সুবহানাল্লাহ')}' লিখে সদকায়ে জারিয়া হিসেবে শেয়ার করুন 🌿"

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
    record_payload = {
        "id": f"loop_{content.get('slot_key', 'slot')}_{int(time.time())}",
        "title": f"[পর্ব {content.get('episode_bn', '')}] {content.get('title_bn', '')}",
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
