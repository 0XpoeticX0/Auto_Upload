# -*- coding: utf-8 -*-
import os
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
        "visual_prompt": "vertical 9:16, aesthetic interior of a modern serene home with an emerald green velvet prayer rug on polished wooden floor before a large floor-to-ceiling glass window overlooking misty lush morning hills and soft cloudy dawn sky after Fajr, cinematic warm morning light rays, photorealistic 8k, architectural digest, no people, no living beings"
    },
    "slot_2_evening": {
        "name": "🌙 Slot 2: Prime Evening & Night (08:00 PM BST)",
        "theme": "Heart-Softeners, Grave Protection (সূরা মুলক), Sins-Wiping Prayers, Tahajjud Miracles & Night Peace",
        "system_instruction": "Create a profound, emotionally powerful 'HEART-TOUCHING' nighttime reminder. Focus on one of these high-performing topics: (1) The 30-verse Surah (সূরা মুলক) that miraculously shields you inside the grave, (2) The 1 Sunnah prayer that wipes years of sins in minutes (সালাতুত তাসবীহ / আওয়াবীন), (3) What to say if you wake up suddenly in the night with anxiety to have all Duas accepted instantly, (4) The magic of 2 Rakat Tahajjud for impossible miracles, or (5) Sayyidul Istighfar: the master repentance Dua that guarantees Jannah.",
        "visual_prompt": "vertical 9:16, luxury balcony view looking out over the illuminated Holy Kaaba and Masjid Al-Haram in Makkah at twilight night, glowing emerald green minarets, polished marble courtyard, soft atmospheric mist, high aesthetic cinematic lighting, photorealistic 8k, architectural digest, no humans in focus"
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

    # Calculate Series Episode Number
    ep_int, ep_bn = get_next_episode_number()

    system_prompt = f"""You are a master viral Islamic content creator specializing in the high-retention "7-Second Aesthetic Loop + High-Value Point-by-Point Caption" Reel format.

THEME: {cfg['theme']}
INSTRUCTION: {cfg['system_instruction']}
SERIES CONTEXT: "দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"

CRITICAL FORMAT RULES:
1. VIRAL HOOK ARCHETYPES (Cycle dynamically through these high-converting angles):
   • Archetype 1 [The Guaranteed Dua]: "রাসূলুল্লাহ (ﷺ) বলেছেন: আল্লাহর এমন ১টি নাম আছে, যা দিয়ে দোয়া করলে আল্লাহ তা কখনো ফিরিয়ে দেন না..." (ইসমে আজম)
   • Archetype 2 [Spiritual Signs]: "৭টি নিশ্চিত লক্ষণ যা প্রমাণ করে আল্লাহ আপনার দোয়া কবুল করছেন — যদিও আপনি তা এখনই দেখতে পাচ্ছেন না..."
   • Archetype 3 [The Forgotten Key Prayer]: "এমন ১টি অবহেলিত সুন্নাহ নামাজ যা আপনার জীবনের সমস্ত বন্ধ দরজা খুলে দিতে পারে..."
   • Archetype 4 [Mind-Blowing Quranic Miracle]: "কুরআনে কেন আল্লাহ কিয়ামতকে অতীত কাল (Past Tense) দিয়ে বর্ণনা করেছেন তা জানলে আপনি বিস্মিত হবেন..."
   • Archetype 5 [Astronomical Rewards / Sins Wiping]: "এমন ১টি সুন্নাহ আমল... যা মাত্র কয়েক মিনিটে বহু বছরের গুনাহ ধুয়ে ফেলে..."
   • Archetype 6 [Time-Locked Barakah]: "ফজরের পর মাত্র ৫ মিনিটে এই ৩টি আমল করুন এবং দেখুন কীভাবে আল্লাহ পুরো দিনকে বরকতে ভরিয়ে দেন..."

2. ON-SCREEN TEXT & NUMBER PSYCHOLOGY (MANDATORY):
   - Every title and on-screen hook MUST contain a specific number (e.g. "৩টি আমল", "৭টি নিশ্চিত লক্ষণ", "১টি বিশেষ দোয়া", "২ রাকাত নামাজ", "১টি মারাত্মক ভুল", "৫ মিনিটে", "১২ বছরের গুনাহ"). Numbered hooks drive the highest engagement and retention!
   - A single, curiosity-driving sentence in 2-3 short lines in authentic BANGLA (বাংলা).
   - Must specify:
     a) The Numbered Action/Topic (e.g. "৩টি আমল", "১টি নাম", "২ রাকাত নামাজ", "৭টি লক্ষণ")
     b) The Divine Entity ("আল্লাহ")
     c) The Promised Outcome/Benefit (e.g. "বরকতে ভরিয়ে দেন", "দোয়া কখনো ফিরিয়ে দেন না", "সব বন্ধ দরজা খুলে যায়")
   - Specify "highlight_words": list of 2-3 exact words/phrases to be highlighted in Warm Gold and enlarged (+4px) (MUST include the numbered action, 'আল্লাহ', and the outcome).

3. CRITICAL DUA COMPLETENESS RULE (MANDATORY):
   - Whenever providing a Dua (especially from Sahih Muslim, Tirmidhi, Abu Dawood, Ibn Majah, etc.), NEVER output just the opening praise or half-sentence.
   - Example for Debt Relief (Sahih Muslim: 2713):
     WRONG: "اللَّهُمَّ رَبَّ السَّمَاوَاتِ السَّبْعِ وَرَبَّ الْعَرْشِ الْعَظِيمِ" (Incomplete, cut-off opening praise)
     MANDATORY COMPLETE FORMAT:
     Arabic: "اللَّهُمَّ رَبَّ السَّمَاوَاتِ السَّبْعِ وَرَبَّ الْعَرْشِ الْعَظِيمِ، رَبَّنَا وَرَبَّ كُلِّ شَيْءٍ... اقْضِ عَنَّا الدَّيْنَ وَأَغْنِنَا مِنَ الْفَقْرِ"
     Pronunciation: "আল্লাহুম্মা রব্বাস সামা-ওয়া-তিস সাব‘ই ওয়া রব্বাল ‘আরশিল ‘আযীম, রব্বানা- ওয়া রব্বা কুল্লি শাই... ইক্বদ্বি ‘আন্নাদ-দাইনা ওয়া আগনিনা- মিনাল ফাক্বর।"
     Meaning: "হে আল্লাহ! সাত আসমানের রব এবং মহান আরশের রব! আমাদের রব এবং প্রত্যেক বস্তুর রব... আমাদের সমস্ত ঋণ পরিশোধ করে দিন এবং আমাদের অভাব দূর করে স্বাবলম্বী করুন।"
   - The Arabic text MUST contain the full core supplication request.
   - Bengali pronunciation and Bengali meaning MUST translate the entire Dua completely with ZERO missing sentences.

4. VALUE-PACKED CAPTION:
   - Must provide the COMPLETE point-by-point answers and exact Sahih Hadith / Quranic references!
   - Numbered steps (১, ২, ৩) with clear explanations.
   - Sahih book references: [সহীহ বুখারী / সহীহ মুসলিম / সহীহ আন-নাসায়ী / সহীহ ইবনে মাজাহ / জামে আত-তিরমিযী].
   - Community Dhikr comment prompt.
   - Follow credit MUST be 👉 @dailydos_islam

5. TOPICS RECENTLY COVERED (DO NOT REPEAT ANY OF THESE):
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
            "title": "কিছুক্ষণ তাসবীহ ও ইস্তিগফারে থাকা",
            "hadith": "ফজরের পর নিজের জায়নামাজে বসে কিছুক্ষণ 'সুবহানাল্লাহ', 'আলহামদুলিল্লাহ' ও 'আস্তাগফিরুল্লাহ' পাঠ করা। সূর্যোদয় পর্যন্ত এই আমলটি সারাদিনের রিজিকে অভাবনীয় বরকত এনে দেয়।",
            "reference": "সহীহ মুসলিম"
        }}
    ],
    "dhikr_word": "সুবহানাল্লাহ",
    "visual_prompt": "{cfg['visual_prompt']}",
    "tags": ["Islam", "DailyReminder", "Sunnah", "সহীহ_হাদিস", "দোয়া", "DailyDos", "Fajr", "Barakah"]
}}"""

    from app.history import is_topic_duplicate_global
    user_prompt = f"Generate 1 high-CTR viral Islamic Loop Reel for the '{cfg['theme']}' theme in 100% Bangla. Series episode: {ep_bn}. Choose a fresh, unique topic NOT in the avoided list. Return valid JSON only."
    for attempt in range(3):
        content = extract_json(system_prompt, user_prompt, max_tokens=1500)
        if not content:
            logger.warning(f"Attempt {attempt+1}: Failed to parse valid Loop Reel JSON from LLM. Retrying...")
            continue
            
        title_bn = content.get("title_bn", "").strip()
        if is_topic_duplicate_global(title_bn):
            logger.warning(f"Loop Reel topic '{title_bn}' flagged as duplicate in global history! Retrying with a fresh topic...")
            continue
            
        content["slot_key"] = slot_key
        content["episode_number"] = ep_int
        content["episode_bn"] = ep_bn
        if not content.get("series_title"):
            content["series_title"] = f"দৈনন্দিন সহীহ আমল • পর্ব {ep_bn}"
        return content

    raise RuntimeError("Failed to generate a non-duplicate Loop Reel content after 3 attempts.")

def format_loop_caption(data: dict) -> str:
    """Short, punchy, high-converting caption with complete Dua and Series Branding."""
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
            caption += "📖 রাসূলুল্লাহ (ﷺ) বলেছেন:\n"
            caption += "“" + pt["hadith"] + "”\n"
            if pt.get("reference"):
                caption += "📚 [" + pt["reference"] + "]\n"
            caption += "\n"

    # COMPLETE ARABIC DUA
    for pt in pts:
        if pt.get("arabic"):
            caption += "🤲 পূর্ণাঙ্গ দোয়া:\n" + pt["arabic"] + "\n\n"
            if pt.get("pronunciation"):
                caption += "🗣️ উচ্চারণ: “" + pt["pronunciation"] + "”\n\n"
            if pt.get("meaning"):
                caption += "🌿 অর্থ: “" + pt["meaning"] + "”\n\n"
            if pt.get("reference") and pt != pts[0]:
                caption += "📚 [" + pt["reference"] + "]\n\n"
            break

    # PRACTICAL TIP (2nd non-arabic point)
    for pt in pts[1:]:
        if pt.get("hadith") and not pt.get("arabic"):
            caption += "💡 " + pt.get("title", "আমলের নিয়ম") + ":\n" + pt["hadith"] + "\n\n"
            if pt.get("reference"):
                caption += "📚 [" + pt["reference"] + "]\n\n"
            break

    # CLEAR CTA & FOLLOW TRIGGER
    caption += (
        "📌 পরবর্তীতে আমল করার জন্য রিলটি 🔖 Save করুন।\n"
        "💬 কমেন্টে একবার “" + dhikr + "” লিখুন — সদকায়ে জারিয়া হবে! 🤍\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন: @dailydos_islam\n\n"
    )

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

    # 1. Background image generation
    bg_path = os.path.join(temp_dir, "background.jpg")
    visual_p = content.get("visual_prompt", SLOT_CONFIGS["slot_1_morning"]["visual_prompt"])
    
    encoded = urllib.parse.quote(visual_p)
    neg = "human, person, face, woman, man, child, living being, low quality, blurry, watermark, text"
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={int(time.time())}&negative={urllib.parse.quote(neg)}"
    
    downloaded = False
    try:
        r = requests.get(url, timeout=60)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(bg_path, "wb") as f:
                f.write(r.content)
            downloaded = True
    except Exception as e:
        logger.warning(f"Pollinations notice: {e}")

    if not downloaded:
        sample_img = "data/temp/loop_reel_sample/fajr_prayer_mat.jpg"
        if os.path.exists(sample_img):
            import shutil
            shutil.copyfile(sample_img, bg_path)
            logger.info("Using cached high-aesthetic background.")
        else:
            # Fallback canvas
            img = Image.new("RGB", (1080, 1920), (12, 16, 22))
            img.save(bg_path, "JPEG")

    # 2. Authentic Quran Audio with 30-Video Anti-Repetition Guarantee
    audio_path = get_or_download_quran_audio(duration=8.0)

    # 3. Build ASS Subtitle with Series Branding, Warm Gold highlights, and Visual Follow Trigger
    series_badge = content.get("series_title", f"✦ দৈনন্দিন সহীহ আমল • পর্ব {content.get('episode_bn', '১')} ✦")
    if not series_badge.startswith("✦"):
        series_badge = f"✦ {series_badge} ✦"

    l1 = content.get("line_1", "")
    l2 = content.get("line_2", "")
    l3 = content.get("line_3", "")
    
    hw_list = content.get("highlight_words", ["৩টি আমল", "আল্লাহ", "বরকতে ভরিয়ে দেন"])
    full_hook_text = f"{l1}\\N{l2}\\N{l3}" if l2 else l1
    
    for hw in hw_list:
        if hw in full_hook_text:
            full_hook_text = full_hook_text.replace(hw, f"{{\\fs74\\c&H0041AFEB&}}{hw}{{\\fs66\\c&HFFFFFF&}}", 1)

    ass_path = os.path.join(temp_dir, "overlay.ass")
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SeriesBadge,Noto Sans Bengali,36,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,60,60,200,1
Style: MainHook,Noto Sans Bengali,66,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.5,2.5,5,70,70,0,1
Style: CaptionCTA,Noto Sans Bengali,48,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.0,2.0,2,60,60,430,1
Style: FollowTrigger,Noto Sans Bengali,32,&H00D0FFD0&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,2,60,60,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:08.00,SeriesBadge,,0,0,0,,{{\\fnNoto Sans Bengali\\fs36\\b1\\c&H0041AFEB&}}{series_badge}
Dialogue: 0,0:00:00.00,0:00:08.00,MainHook,,0,0,0,,{{\\fnNoto Sans Bengali\\fs66\\b1\\c&HFFFFFF&}}{full_hook_text}
Dialogue: 0,0:00:00.00,0:00:08.00,CaptionCTA,,0,0,0,,{{\\fnNoto Sans Bengali\\fs48\\b1\\c&H0041AFEB&}}👉 বিস্তারিত ক্যাপশনে পড়ুন 👇{{\\c&HFFFFFF&}}
Dialogue: 0,0:00:00.00,0:00:08.00,FollowTrigger,,0,0,0,,{{\\fnNoto Sans Bengali\\fs32\\b1\\c&H00D0FFD0&}}প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন 👉 @dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    rel_ass = os.path.relpath(ass_path).replace("\\", "/")

    # 4. Render 60 FPS Sub-pixel Lanczos continuous zoom video
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

    # 7. Save to Supabase for zero-topic repetition
    record_payload = {
        "id": f"loop_{content.get('slot_key', 'slot')}_{int(time.time())}",
        "title": content.get("title_bn", ""),
        "source": f"loop_{content.get('slot_key', 'slot')}"
    }
    _supabase_insert(record_payload)
    logger.info(f"Saved Loop Reel topic to Supabase: '{content.get('title_bn')}'")

    logger.info("=== LOOP REEL PIPELINE COMPLETED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    import sys
    slot = sys.argv[1] if len(sys.argv) > 1 else None
    run_loop_reel_pipeline(slot)
