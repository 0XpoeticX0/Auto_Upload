"""
Sunnah Calendar & Prophetic 'Ibadah Video Generator (New Dedicated Series)
Produces high-retention 7-second videos alerting viewers of blessed Sunnah days
and teaching the exact 'Ibadah taught by Prophet Muhammad (ﷺ).

STRICT SEPARATION:
- Completely separate from Loop Reel ("আজকের আমল • পর্ব XX").
- ZERO "আজকের আমল • পর্ব ৪৮" badges.
- Line 1 features the Day Reminder + Bangladesh Gregorian Date + Islamic Hijri Date:
  e.g., 'আগামীকাল সোমবার (৪ অক্টোবর • ২১ রবিউস সানি ✦):'
- Line 2 & Line 3 pose the high-stakes curiosity hook about the Prophet's specific 'ibadah.
"""

import os
import re
import json
import time
import logging
import datetime
from typing import Optional, Dict, Any, List

from app.calendar.hijri_events import (
    get_active_or_upcoming_hijri_event,
    format_bangladesh_and_hijri_date,
    get_current_bangladesh_date
)
from app.loop_reel.generator import (
    sanitize_text_for_ass,
    revise_and_balance_hook_lines,
    clean_hadith_body,
    get_or_download_quran_audio,
    SAFE_ASS_CHARS
)
from app.llm.provider import extract_json

logger = logging.getLogger("SunnahCalendar")


def build_sunnah_calendar_system_prompt(event_data: dict, date_info: dict) -> str:
    """Builds the specialized prompt for the Sunnah Calendar series."""
    day_rem = event_data.get("day_reminder", event_data["name"])
    day_prefix = day_rem.split('(')[0].strip()
    date_badge = date_info.get("badge_bn", "")
    p_ebadah = event_data.get("prophet_ebadah", "")
    h_ref = event_data.get("hadith_ref", "")
    guidance = event_data.get("guidance", "")
    model_hook = event_data.get("model_hook", "")
    cta = event_data.get("suggested_cta", "☞ নবীজির শেখানো আমলটি ক্যাপশনে দেখুন ➔")

    return f"""You are a master viral Islamic content creator specializing in high-retention 7-second aesthetic Reels for a NEW DEDICATED SERIES: "Sunnah Calendar & Prophetic 'Ibadah".

# ==============================================================================
# STRICT SERIES SEPARATION MANDATE
# ==============================================================================
- This is a STANDALONE NEW SERIES. 
- ❌ ABSOLUTELY NEVER mention or write 'আজকের আমল' or any episode number like 'পর্ব ৪৮'!
- The sole purpose of this video is:
  1. REMIND OF THE BLESSED DAY & DATE (Bangladesh + Islamic Hijri date).
  2. TEACH THE SPECIFIC 'IBADAH TAUGHT BY PROPHET MUHAMMAD (ﷺ) on that day.

# ==============================================================================
# CURRENT BLESSED OCCASION & PROPHETIC 'IBADAH
# ==============================================================================
• Blessed Day / Event: {event_data['name']}
• Day Reminder: {day_rem}
• Date Info (Bangladesh & Hijri): {date_badge}
• 'Ibadah Taught by Prophet Muhammad (ﷺ): {p_ebadah}
• Core Hadith Citation: {h_ref}
• Topic Guidance: {guidance}
• Model Hook Reference: "{model_hook}"

# ==============================================================================
# ON-SCREEN TEXT MANDATES (STRICT 3-LINE STRUCTURE)
# ==============================================================================
1. LINE 1 MUST INCLUDE BOTH DAY AND DATE IN PARENTHESES:
   - Line 1 MUST state the day reminder followed by the exact date in parentheses with a trailing colon!
   - EXACT FORMAT: '{day_prefix} ({date_badge} ✦):'
   - EXAMPLE: 'আগামীকাল সোমবার ({date_badge} ✦):'

2. LINE 2 & LINE 3 (নবীজির শেখানো ইবাদত ও কৌতূহলী হুক):
   - Pose an irresistible, high-stakes curiosity question or dramatic contrast about the specific 'Ibadah taught by Prophet Muhammad (ﷺ).
   - STRICT ZERO SPOILER RULE: Never reveal the full Hadith answer or sermon on screen!
   - Line 3 ends with the bridge arrow '➔'.
   - EXACT 3-LINE EXAMPLE:
     line_1: 'আগামীকাল সোমবার ({date_badge} ✦):'
     line_2: 'পেটে পাথর বেঁধেও নবীজি (ﷺ)'
     line_3: 'কেন রোজা ছাড়তেন না? ➔'

3. CAPTION CTA:
   - Write a short, punchy 1-line call-to-action connecting directly to the hook:
   - E.g.: "{cta}"

# ==============================================================================
# HIGH-VALUE CAPTION BREAKDOWN (3 STRUCTURED POINTS)
# ==============================================================================
• Point 1: দিনটির তাৎপর্য ও নববী স্মরণ (Why Prophet Muhammad ﷺ honored this day; mention significance and exact timing in Bangladesh).
• Point 2: নবীজির (ﷺ) শেখানো নির্দিষ্ট ইবাদত (The exact Sunnah 'Ibadah taught by Prophet Muhammad ﷺ: exact Arabic Dua with pronunciation & meaning, fasting method, or Dhikr, backed by {h_ref}).
• Point 3: আমল করার সঠিক সময় ও ফায়দা (Practical guidance for Bangladeshi Muslims, when to start, and immense divine rewards).

Output ONLY valid JSON:
{{
    "title_bn": "আগামীকাল সোমবার: পেটে পাথর বেঁধেও নবীজি (ﷺ) কেন রোজা ছাড়তেন না?",
    "title_en": "Why Prophet Muhammad fasted on Mondays #Sunnah #IslamicReminder",
    "line_1": "{day_prefix} ({date_badge} ✦):",
    "line_2": "পেটে পাথর বেঁধেও নবীজি (ﷺ)",
    "line_3": "কেন রোজা ছাড়তেন না? ➔",
    "caption_cta": "{cta}",
    "highlight_words": ["{day_prefix}", "নবীজি (ﷺ)", "রোজা"],
    "caption_points": [
        {{
            "number": "১",
            "title": "দিনটির বিশেষ মর্যাদা",
            "hadith": "নবীজি (ﷺ) বলেছেন: সোমবার ও বৃহস্পতিবার বান্দার আমলনামা আল্লাহর দরবারে পেশ করা হয়। আর আমি চাই আমার আমল যেন রোজাদার অবস্থায় পেশ করা হোক।",
            "reference": "জামে তিরমিযী: ৭৪৭"
        }},
        {{
            "number": "২",
            "title": "নবীজির শেখানো সুন্নাত আমল",
            "hadith": "রাসূলুল্লাহ (ﷺ)-কে সোমবারের রোজা সম্পর্কে জিজ্ঞেস করা হলে তিনি বলেন: 'এ দিনেই আমি জন্মগ্রহণ করেছি এবং এ দিনেই আমার ওপর ওহী নাযিল হয়েছে।'",
            "reference": "সহীহ মুসলিম: ১১৬২"
        }},
        {{
            "number": "৩",
            "title": "আমলের নিয়ম ও প্রস্তুতি",
            "hadith": "আজ রাতেই সেহরির নিয়ত করুন। খাঁটি মনে এই সুন্নাত সিয়াম পালন করে আল্লাহর ক্ষমা ও নৈকট্য অর্জন করুন।",
            "reference": "সহীহ বুখারী: ১৮৯১"
        }}
    ],
    "dhikr_word": "আলহামদুলিল্লাহ",
    "visual_prompt": "Cinematic 8K view of an ancient open Holy Quran resting on a carved wooden rehal inside a grand luminous mosque, morning golden light, dust particles",
    "tags": ["Sunnah", "IslamicCalendar", "রোজা", "সহীহ_হাদিস", "বাংলাদেশ", "DailyReminder"]
}}
"""


def generate_sunnah_calendar_content(target_date: Optional[datetime.date] = None) -> dict:
    """Generates a verified, high-retention video script for the Sunnah Calendar series."""
    if target_date is None:
        target_date = get_current_bangladesh_date()

    date_info = format_bangladesh_and_hijri_date(target_date)
    event_data = get_active_or_upcoming_hijri_event(target_date)

    if not event_data:
        # Fallback to weekly Jumu'ah or Monday/Thursday Sunnah if no annual event active
        weekday = target_date.weekday()
        if weekday in [3, 4]:
            event_data = {
                "name": "পবিত্র জুমার দিনের বিশেষ আমল",
                "day_reminder": "পবিত্র জুমাবার",
                "prophet_ebadah": "সূরা কাহাফ, দরূদ শরীফ এবং আসর-মাগরিবের শেষ ৬০ মিনিটের খাস দোয়া",
                "hadith_ref": "সহীহ মুসলিম: ৮৫৪, সুনানে আবু দাউদ: ১০৪৮",
                "guidance": "Focus on Friday Sunnahs and Dua of Sa'at al-Istijabah.",
                "model_hook": f"আজ পবিত্র জুমাবার ({date_info['badge_bn']} ✦): আসর থেকে মাগরিবের মাঝে ঠিক কোন মুহূর্তে সব দোয়া কবুল হয়?",
                "suggested_cta": "☞ কবুল হওয়ার সেই গোপন মুহূর্তটি ক্যাপশনে দেখুন ➔"
            }
        else:
            event_data = {
                "name": "সাপ্তাহিক সুন্নাত রোজা ও আমল",
                "day_reminder": "সোমবার ও বৃহস্পতিবারের নফল রোজা",
                "prophet_ebadah": "সাপ্তাহিক নফল সিয়াম পালন করা ও আল্লাহর কাছে আমল পেশ",
                "hadith_ref": "জামে তিরমিযী: ৭৪৭",
                "guidance": "Focus on fasting when deeds are presented to Allah.",
                "model_hook": f"সাপ্তাহিক সুন্নাত ({date_info['badge_bn']} ✦): নবীজি (ﷺ) প্রতি সপ্তাহে কেন এই দিনে রোজা ছাড়তেন না?",
                "suggested_cta": "☞ নবীজির শেখানো সুন্নাতটি ক্যাপশনে পড়ুন ➔"
            }

    system_prompt = build_sunnah_calendar_system_prompt(event_data, date_info)
    user_prompt = f"Generate the Sunnah Calendar video script for '{event_data['name']}' in Bangladesh on {date_info['gregorian_bn']} ({date_info['hijri_bn']}). Strictly follow the 3-line open loop structure with Line 1 containing the date badge."

    data = extract_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=2000
    )

    day_rem = event_data.get("day_reminder", event_data["name"])
    day_prefix = day_rem.split('(')[0].strip()
    date_badge = date_info.get("badge_bn", "")

    if not data:
        logger.warning("LLM returned empty data, using curated fallback.")
        data = {
            "title_bn": f"{event_data['name']}: নবীজির শেখানো আমল",
            "title_en": f"{event_data.get('theme', 'Sunnah Reminder')} #Sunnah",
            "line_1": f"{day_prefix} ({date_badge} ✦):",
            "line_2": "পেটে পাথর বেঁধেও নবীজি (ﷺ)",
            "line_3": "কেন রোজা ছাড়তেন না? ➔",
            "caption_cta": event_data.get("suggested_cta", "☞ নবীজির শেখানো আমলটি ক্যাপশনে দেখুন ➔"),
            "highlight_words": [day_prefix, "নবীজি (ﷺ)", "রোজা"],
            "caption_points": [
                {
                    "number": "১",
                    "title": "দিনটির বিশেষ মর্যাদা",
                    "hadith": "নবীজি (ﷺ) বলেছেন: সোমবার ও বৃহস্পতিবার বান্দার আমলনামা আল্লাহর দরবারে পেশ করা হয়। আর আমি চাই আমার আমল যেন রোজাদার অবস্থায় পেশ করা হোক।",
                    "reference": "জামে তিরমিযী: ৭৪৭"
                },
                {
                    "number": "২",
                    "title": "নবীজির শেখানো সুন্নাত আমল",
                    "hadith": "রাসূলুল্লাহ (ﷺ)-কে সোমবারের রোজা সম্পর্কে জিজ্ঞেস করা হলে তিনি বলেন: 'এ দিনেই আমি জন্মগ্রহণ করেছি এবং এ দিনেই আমার ওপর ওহী নাযিল হয়েছে।'",
                    "reference": "সহীহ মুসলিম: ১১৬২"
                },
                {
                    "number": "৩",
                    "title": "আমলের নিয়ম ও প্রস্তুতি",
                    "hadith": "আজ রাতেই সেহরির নিয়ত করুন। খাঁটি মনে এই সুন্নাত সিয়াম পালন করে আল্লাহর ক্ষমা ও নৈকট্য অর্জন করুন।",
                    "reference": "সহীহ বুখারী: ১৮৯১"
                }
            ],
            "dhikr_word": "আলহামদুলিল্লাহ",
            "visual_prompt": "Cinematic 8K view of an ancient open Holy Quran resting on a carved wooden rehal inside a grand luminous mosque, morning golden light, dust particles",
            "tags": ["Sunnah", "IslamicCalendar", "রোজা", "সহীহ_হাদিস", "বাংলাদেশ", "DailyReminder"]
        }

    # Enforce Line 1 Date Badge structure
    l1 = data.get("line_1", "").strip()
    if date_badge and "(" not in l1:
        base = l1.rstrip(" :➔")
        data["line_1"] = f"{base} ({date_badge} ✦):"
    elif not l1.endswith(":"):
        data["line_1"] = f"{l1.rstrip(' ➔')}:"

    # Enforce 3 clean lines
    clean_lines = revise_and_balance_hook_lines(data.get("line_1", ""), data.get("line_2", ""), data.get("line_3", ""))
    if clean_lines:
        data["line_1"] = clean_lines[0]
        data["line_2"] = clean_lines[1] if len(clean_lines) > 1 else ""
        data["line_3"] = clean_lines[2] if len(clean_lines) > 2 else ""

    data["date_info"] = date_info
    data["event_data"] = event_data
    return data


def format_sunnah_calendar_caption(data: dict) -> str:
    """Formats the standalone caption for the Sunnah Calendar series."""
    date_info = data.get("date_info") or format_bangladesh_and_hijri_date()
    title_bn = data.get("title_bn", "").strip()
    pts = data.get("caption_points", [])

    caption = f"{date_info['caption_header']}\n\n"
    hook_parts = [data.get(k, "").strip() for k in ["line_1", "line_2", "line_3"] if data.get(k)]
    hook = " ".join(hook_parts) if hook_parts else title_bn
    hook = hook.rstrip(" :➔")
    caption += f"{hook} 🤲\n\n"

    bn_nums = ["১", "২", "৩", "৪", "৫"]
    for idx, pt in enumerate(pts):
        num_str = pt.get("number") or (bn_nums[idx] if idx < len(bn_nums) else str(idx + 1))
        title = pt.get("title", "").strip()
        hadith = pt.get("hadith", "").strip()
        arabic = pt.get("arabic", "").strip()
        pron = pt.get("pronunciation", "").strip()
        meaning = pt.get("meaning", "").strip()
        ref = pt.get("reference", "").strip()

        if title:
            caption += f"{num_str}. {title}:\n"
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
        caption += "\n"

    caption += (
        "📌 এই মোবারক আমলটি 🔖 Save করে রাখুন — যেন ভুলে না যান!\n"
        "🤍 প্রিয়জনদের Share করে দিন — রাসুলুল্লাহ (ﷺ) বলেছেন: "
        "'যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।' [সহীহ মুসলিম: ১৮৯৩] 🌿\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👉 প্রতিদিনের সহীহ হাদিস ও সুন্নাহ রিমাইন্ডারের জন্য Follow করুন: @dailydos_islam\n\n"
    )

    tags = " ".join(["#" + t.strip("#") for t in data.get("tags", ["Sunnah", "IslamicCalendar", "সহীহ_হাদিস", "বাংলাদেশ"])])
    return (caption + tags).strip()


SACRED_SANCTUARY_SCENES = [
    "app/assets/scenes/quran_rehal_cinematic.jpg",
    "app/assets/quran_rehal_master.jpg",
    "app/assets/scenes/quran_rehal_sanctuary.jpg",
    "app/assets/scenes/quran_rehal_sunbeam.jpg",
    "app/assets/scenes/golden_dome_night.jpg",
    "app/assets/scenes/moorish_palace_arches.jpg",
    "app/assets/scenes/tranquil_courtyard_fountain.jpg",
]

def get_sacred_calendar_background() -> str:
    """Returns a majestic Shariah-compliant sacred sanctuary background for the Sunnah Calendar."""
    import random
    import shutil
    available = [p for p in SACRED_SANCTUARY_SCENES if os.path.exists(p)]
    if available:
        try:
            from app.history import get_recent_backgrounds, record_background_usage
            recent = get_recent_backgrounds(limit=len(available) - 1)
            candidates = [p for p in available if os.path.basename(p) not in recent]
            chosen = random.choice(candidates if candidates else available)
            record_background_usage(os.path.basename(chosen))
            return chosen
        except Exception:
            return random.choice(available)
    if os.path.exists("app/assets/quran_rehal_master.jpg"):
        return "app/assets/quran_rehal_master.jpg"
    from app.history import get_unique_background
    return get_unique_background()


def render_sunnah_calendar_video(content: dict, output_dir: str = "data/output") -> str:
    """
    Renders 60 FPS subpixel lanczos continuous zoom video for the Sunnah Calendar series.
    STRICT MANDATE: ZERO 'আজকের আমল • পর্ব XX' badge! Pure, majestic Kalpurush visual with Line 1 date badge!
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp", "sunnah_calendar_run")
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Background Image (Strictly Sacred Quran on Rehal & Sanctuary)
    import shutil
    bg_path = os.path.join(temp_dir, "background.jpg")
    chosen_bg = get_sacred_calendar_background()
    if chosen_bg and os.path.exists(chosen_bg):
        shutil.copyfile(chosen_bg, bg_path)
    else:
        from app.quality.vision_guardian import get_certified_safe_fallback
        get_certified_safe_fallback(bg_path)

    # 2. Audio
    topic_keywords = f"{content.get('title_bn', '')} {content.get('line_1', '')} {content.get('line_2', '')}"
    audio_path = get_or_download_quran_audio(topic_text=topic_keywords, duration=8.0)

    # 3. Build Subtitles with Kalpurush Typography Hierarchy
    l1 = content.get("line_1", "").strip()
    l2 = content.get("line_2", "").strip()
    l3 = content.get("line_3", "").strip()
    raw_cta = content.get("caption_cta", "নবীজির শেখানো আমলটি ক্যাপশনে দেখুন ➔")
    raw_cta = raw_cta.replace("☞", "").strip()
    caption_cta_text = sanitize_text_for_ass(raw_cta)

    GOLD_COLOR = "&H0015CCFA&"  # Radiant Sunnah Amber Gold (#FACC15)
    WHITE_COLOR = "&H00FFFFFF&" # Crisp Pure White

    # Line 1: Day Reminder & Date Badge (Guaranteed strictly 1 single line at fs40)
    l1_clean = sanitize_text_for_ass(l1)

    # Line 2 & Line 3: Prominent hook at fs58 with key highlights
    l2_clean = sanitize_text_for_ass(l2)
    l3_clean = sanitize_text_for_ass(l3)

    hw_list = content.get("highlight_words", ["নবীজি (ﷺ)", "রোজা"])
    body_lines = [l for l in [l2_clean, l3_clean] if l]
    body_text = "\\N".join(body_lines)

    for hw in sorted(hw_list, key=len, reverse=True):
        hw_clean = sanitize_text_for_ass(hw.strip())
        if not hw_clean or hw_clean in l1_clean:
            continue
        if hw_clean in body_text:
            body_text = body_text.replace(hw_clean, f"{{\\c{GOLD_COLOR}}}{hw_clean}{{\\c{WHITE_COLOR}}}", 1)

    ass_path = os.path.join(temp_dir, "overlay.ass")
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: DayAlert,Kalpurush,40,&H0015CCFA&,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,2.8,1.6,5,35,35,0,1
Style: HookLine,Kalpurush,58,&H00FFFFFF&,&H000000FF,&H00000000,&HB0000000,0,0,0,0,100,100,0,0,1,3.2,1.8,5,35,35,0,1
Style: CaptionCTA,Kalpurush,42,&H0015CCFA&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2.4,1.4,2,40,40,210,1
Style: FollowTrigger,Kalpurush,30,&H00E0E8F0&,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2.0,1.2,2,40,40,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:08.00,DayAlert,,0,0,0,,{{\\pos(540,460)\\c{GOLD_COLOR}}}{l1_clean}
Dialogue: 0,0:00:00.00,0:00:08.00,HookLine,,0,0,0,,{{\\pos(540,570)}}{body_text}
Dialogue: 0,0:00:00.00,0:00:08.00,CaptionCTA,,0,0,0,,{caption_cta_text}
Dialogue: 0,0:00:00.00,0:00:08.00,FollowTrigger,,0,0,0,,প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন ➔ @dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    rel_ass = os.path.relpath(ass_path).replace("\\", "/")
    rel_fonts = os.path.relpath("app/assets/fonts").replace("\\", "/")
    output_video = os.path.join(output_dir, f"sunnah_calendar_{int(time.time())}.mp4")

    # Render with FFmpeg: continuous 60fps subpixel zoompan + Kalpurush font via fontsdir + subtle color grading
    cmd = (
        f'ffmpeg -y -loop 1 -t 8.0 -i "{bg_path}" -i "{audio_path}" '
        f'-filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
        f'colorlevels=rimin=0.03:gimin=0.03:bimin=0.03:rimax=0.92:gimax=0.92:bimax=0.92,'
        f'zoompan=z=\'min(zoom+0.0006,1.20)\':d=480:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=1080x1920:fps=60,'
        f'subtitles=\'{rel_ass}\':fontsdir=\'{rel_fonts}\'[v]" '
        f'-map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 18 '
        f'-c:a aac -b:a 192k -shortest "{output_video}"'
    )
    logger.info("Executing enhanced Sunnah Calendar video render...")
    os.system(cmd)
    return output_video
