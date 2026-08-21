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
from app.history import _supabase_insert, _supabase_fetch_recent, get_recent_video_titles
from app.loop_reel.audio_library import get_or_download_quran_audio
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook

# 4 Daily Peak Release Windows (BST / GMT+6)
SLOT_CONFIGS = {
    "slot_1_fajr": {
        "name": "🌅 Slot 1: Post-Fajr & Morning Commute (06:30 AM - 08:30 AM BST)",
        "theme": "Morning Dua, Protection, Rizq & Barakah reminders",
        "system_instruction": "Create a high-curiosity morning Fajr reminder about morning Duas, Rizq, Barakah, protection, or 3 powerful morning deeds.",
        "visual_prompt": "vertical 9:16, aesthetic interior of a modern serene home with an emerald green velvet prayer rug on polished wooden floor before a large floor-to-ceiling glass window overlooking misty lush morning hills and soft cloudy dawn sky after Fajr, cinematic warm morning light rays, photorealistic 8k, architectural digest, no people, no living beings"
    },
    "slot_2_midday": {
        "name": "☀️ Slot 2: Midday / Pre-Dhuhr Break (12:30 PM - 01:45 PM BST)",
        "theme": "Short Hadith reflections, Sunnah habits, midday mindfulness",
        "system_instruction": "Create a high-curiosity midday reminder about quick Sunnah habits, honest livelihood, peace of mind, or easily forgotten daily Hadith.",
        "visual_prompt": "vertical 9:16, aesthetic minimal wooden Rehal holding an open antique Holy Quran with gold embossed pages next to warm glowing amber Moroccan lantern on polished marble table by sunlit courtyard window, volumetric light beams, photorealistic 8k, serene atmosphere, no people, no living beings"
    },
    "slot_3_asr": {
        "name": "🌿 Slot 3: Post-Asr / Pre-Maghrib (04:45 PM - 05:45 PM BST)",
        "theme": "Sunnah habits, relationship & marriage advice, family, parents' rights, Halal living",
        "system_instruction": "Create a high-curiosity late afternoon reminder about marriage blessings, kindness to spouse/parents, good character, or sweet Sunnah practices.",
        "visual_prompt": "vertical 9:16, peaceful traditional oriental courtyard garden at golden hour dusk, tranquil water fountain with lotus reflection, glowing warm brass lanterns, blooming white jasmine vines climbing stone archways, warm amber and rose-gold dusk palette, 8k resolution, serene, no people, no living beings"
    },
    "slot_4_evening": {
        "name": "🌙 Slot 4: Prime Evening (08:30 PM - 10:00 PM BST)",
        "theme": "Heart-softeners, forgiveness, Akhirah, repentance, grave protection, Surah Al-Mulk, Tahajjud",
        "system_instruction": "Create a profound nighttime reflection on grave protection (Surah Al-Mulk), heartfelt repentance, Tahajjud prayer, or Allah's boundless mercy.",
        "visual_prompt": "vertical 9:16, luxury balcony view looking out over the illuminated Holy Kaaba and Masjid Al-Haram in Makkah at twilight night, glowing emerald green minarets, polished marble courtyard, soft atmospheric mist, high aesthetic cinematic lighting, photorealistic 8k, architectural digest, no humans in focus"
    }
}

def determine_current_slot() -> str:
    """Calculates the current peak slot based on BST (UTC+6) time."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_bst = now_utc + datetime.timedelta(hours=6)
    hour = now_bst.hour

    if 4 <= hour < 11:
        return "slot_1_fajr"
    elif 11 <= hour < 15:
        return "slot_2_midday"
    elif 15 <= hour < 19:
        return "slot_3_asr"
    else:
        return "slot_4_evening"

def generate_loop_reel_content(slot_key: str = None) -> dict:
    """Generates viral 7-second curiosity hook and high-value point-by-point caption with deduplication."""
    if not slot_key or slot_key not in SLOT_CONFIGS:
        slot_key = determine_current_slot()
    
    cfg = SLOT_CONFIGS[slot_key]
    logger.info(f"Targeting {cfg['name']} ({cfg['theme']})")

    # Fetch recent topics to ensure zero duplication
    recent_titles = get_recent_video_titles(limit=60)
    avoid_context = "\n- ".join(recent_titles[:30]) if recent_titles else "None"

    system_prompt = f"""You are a master viral Islamic content creator specializing in the high-retention "7-Second Aesthetic Loop + High-Value Point-by-Point Caption" Reel format.

THEME: {cfg['theme']}
INSTRUCTION: {cfg['system_instruction']}

CRITICAL FORMAT RULES:
1. VIRAL HOOK ARCHETYPES (Cycle dynamically through these high-converting angles):
   • Archetype 1 [The Guaranteed Dua]: "রাসূলুল্লাহ (ﷺ) বলেছেন: আল্লাহর এমন ১টি নাম আছে, যা দিয়ে দোয়া করলে আল্লাহ তা কখনো ফিরিয়ে দেন না..." (ইসমে আজম)
   • Archetype 2 [Spiritual Signs]: "৭টি নিশ্চিত লক্ষণ যা প্রমাণ করে আল্লাহ আপনার দোয়া কবুল করছেন — যদিও আপনি তা এখনই দেখতে পাচ্ছেন না..."
   • Archetype 3 [The Forgotten Key Prayer]: "এমন ১টি অবহেলিত সুন্নাহ নামাজ যা আপনার জীবনের সমস্ত বন্ধ দরজা খুলে দিতে পারে..."
   • Archetype 4 [Mind-Blowing Quranic Miracle]: "কুরআনে কেন আল্লাহ কিয়ামতকে অতীত কাল (Past Tense) দিয়ে বর্ণনা করেছেন তা জানলে আপনি বিস্মিত হবেন..."
   • Archetype 5 [Astronomical Rewards / Sins Wiping]: "এমন ১টি সুন্নাহ আমল... যা মাত্র কয়েক মিনিটে বহু বছরের গুনাহ ধুয়ে ফেলে..."
   • Archetype 6 [Time-Locked Barakah]: "ফজরের পর মাত্র ৫ মিনিটে এই ৩টি আমল করুন এবং দেখুন কীভাবে আল্লাহ পুরো দিনকে বরকতে ভরিয়ে দেন..."

2. ON-SCREEN TEXT (Hook):
   - A single, curiosity-driving sentence in 2-3 short lines in authentic BANGLA (বাংলা).
   - Must specify:
     a) The Action/Topic (e.g. "৩টি আমল", "১টি নাম", "গোপন নামাজ", "৭টি লক্ষণ")
     b) The Divine Entity ("আল্লাহ")
     c) The Promised Outcome/Benefit (e.g. "বরকতে ভরিয়ে দেন", "দোয়া কখনো ফিরিয়ে দেন না", "সব বন্ধ দরজা খুলে যায়")
   - Specify "highlight_words": list of 2-3 exact words/phrases to be highlighted in Warm Gold and enlarged (+4px) (MUST include the action, 'আল্লাহ', and the outcome).

3. VALUE-PACKED CAPTION:
   - Must provide the COMPLETE point-by-point answers and exact Sahih Hadith / Quranic references!
   - Numbered steps (১, ২, ৩) with clear explanations.
   - For Duas: Arabic text + Bengali pronunciation + Bengali meaning.
   - Sahih book references: [সহীহ বুখারী / সহীহ মুসলিম / সহীহ আন-নাসায়ী / সহীহ ইবনে মাজাহ / জামে আত-তিরমিযী].
   - Community Dhikr comment prompt.
   - Follow credit MUST be 👉 @dailydos_islam

3. TOPICS RECENTLY COVERED (DO NOT REPEAT ANY OF THESE):
- {avoid_context}

Output ONLY valid JSON:
{{
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

    user_prompt = f"Slot: {slot_key}. Create a brand new, highly engaging Islamic Loop Reel."
    content = extract_json(system_prompt, user_prompt, max_tokens=1500)
    if not content:
        raise RuntimeError("Failed to generate Loop Reel content from LLM.")
    
    content["slot_key"] = slot_key
    return content

def format_loop_caption(data: dict) -> str:
    """Builds the comprehensive, high-value point-by-point viral caption in 100% Bangla."""
    title_bn = data.get("title_bn", "").strip()
    header = f"{title_bn} 🌿\n\n"
    
    points_text = ""
    for pt in data.get("caption_points", []):
        num = pt.get("number", "•")
        p_title = pt.get("title", "")
        points_text += f"{num}. {p_title}:\n"
        if pt.get("hadith"):
            points_text += f"{pt.get('hadith')}\n"
        if pt.get("arabic"):
            points_text += f"{pt.get('arabic')}\n"
        if pt.get("pronunciation"):
            points_text += f"উচ্চারণ: \"{pt.get('pronunciation')}\"\n"
        if pt.get("meaning"):
            points_text += f"অর্থ: \"{pt.get('meaning')}\"\n"
        if pt.get("reference"):
            points_text += f"📚 [{pt.get('reference')}]\n"
        points_text += "\n"

    dhikr = data.get("dhikr_word", "সুবহানাল্লাহ")
    cta_block = (
        f"💬 আজকের জিকির:\n"
        f"কমেন্টে একবার \"{dhikr}\" লিখুন এবং বন্ধুদের সাথে শেয়ার করে সদকায়ে জারিয়ার অংশীদার হোন! 🤍\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য ফলো করুন:\n"
        f"👉 @dailydos_islam\n\n"
    )

    tags = " ".join([f"#{t.strip('#')}" for t in data.get("tags", ["Islam", "DailyReminder", "Sunnah", "সহীহ_হাদিস", "DailyDos"])])
    return f"{header}{points_text}{cta_block}{tags}".strip()

def render_loop_reel_video(content: dict, output_dir: str = "data/output") -> str:
    """Renders 60 FPS buttery smooth 1.22x continuous zoom video with authentic Quran recitation."""
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp", "loop_reel_run")
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Background image generation
    bg_path = os.path.join(temp_dir, "background.jpg")
    visual_p = content.get("visual_prompt", SLOT_CONFIGS["slot_1_fajr"]["visual_prompt"])
    
    # Try Pollinations Flux first
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
        # Fallback to local default aesthetic images if available
        sample_img = "data/temp/loop_reel_sample/fajr_prayer_mat.jpg"
        if os.path.exists(sample_img):
            import shutil
            shutil.copyfile(sample_img, bg_path)
            logger.info("Using cached high-aesthetic background.")
        else:
            raise RuntimeError("Could not generate or find background image.")

    # 2. Authentic Quran Audio
    audio_path = get_or_download_quran_audio(duration=8.0, output_path=os.path.join(temp_dir, "audio.mp3"))

    # 3. Build ASS Subtitle with enlarged Warm Gold highlights
    l1 = content.get("line_1", "")
    l2 = content.get("line_2", "")
    l3 = content.get("line_3", "")
    
    # Apply Warm Gold & fs74 size bump to highlighted words
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
Style: MainHook,Noto Sans Bengali,66,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.5,2.5,5,70,70,0,1
Style: CaptionCTA,Noto Sans Bengali,48,&H0041AFEB,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.0,2.0,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:08.00,MainHook,,0,0,0,,{{\\fnNoto Sans Bengali\\fs66\\b1\\c&HFFFFFF&}}{full_hook_text}
Dialogue: 0,0:00:00.00,0:00:08.00,CaptionCTA,,0,0,0,,{{\\fnNoto Sans Bengali\\fs50\\b1\\c&H0041AFEB&}}👉 বিস্তারিত ক্যাপশনে পড়ুন 👇{{\\c&HFFFFFF&}}
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
    duration = 8.0
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
        p = i / float(total_frames - 1)
        current_scale = 1.0 + (zoom_total * p)
        
        crop_w = orig_w / current_scale
        crop_h = orig_h / current_scale
        crop_x = (orig_w - crop_w) / 2.0
        crop_y = (orig_h - crop_h) / 2.0
        
        cropped = base_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        frame = cropped.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
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
    pinned_comment = f"কমেন্টে একবার '{content.get('dhikr_word', 'সুবহানাল্লাহ')}' লিখে সদকায়ে জারিয়ার অংশীদার হোন 🌿"

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

    # 6. Save to Supabase for zero-topic repetition
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
