# -*- coding: utf-8 -*-
"""
Metadata & Caption Generator for Quran Recitation Videos.
Optimized for International Viral Reach (< 100 char global titles, bilingual descriptions, universal tags).
No auto-first comments per user specification.
"""

from app.quran_verse.quran_data import SURAH_NAMES_EN

def generate_quran_metadata(verse_data: dict, audio_data: dict) -> dict:
    """
    Generates YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok metadata
    with international global reach.
    """
    surah_num = verse_data.get("surah", 1)
    surah_name_bn = verse_data.get("surah_name_bn", "")
    surah_name_en = verse_data.get("surah_name_en") or SURAH_NAMES_EN.get(surah_num, f"Surah {surah_num}")
    range_str = verse_data.get("verse_range_str", "")
    
    reciter_info = audio_data.get("reciter", verse_data.get("reciter", {}))
    reciter_en = reciter_info.get("name_en", "Sheikh Mishary Rashid Alafasy")
    reciter_bn = reciter_info.get("name_bn", "শায়খ মিশারি রশিদ আল-আফাসি")
    reciter_short = reciter_info.get("title_badge", "Alafasy")
    
    # Emotional English theme headline for international audience
    theme_headline_en = verse_data.get("theme_headline_en") or verse_data.get("theme_hint")
    if not theme_headline_en or any(ord(c) > 127 for c in theme_headline_en):
        # Default global curiosity hooks
        default_hooks = [
            "Heart Touching Quran Recitation",
            "When Your Heart Needs Peace",
            "Listen To This Beautiful Recitation",
            "A Powerful Message From Allah",
            "The Words That Heal Your Soul"
        ]
        import random
        theme_headline_en = random.choice(default_hooks)
    
    clean_hook = theme_headline_en.replace("(", "").replace(")", "").strip()
    if len(clean_hook) > 42:
        clean_hook = clean_hook[:42].strip()

    # International high-converting title (< 95 chars)
    # e.g., "When Your Heart Needs Peace ➔ Surah Al-Mulk (1-4) | Alafasy #Shorts #Quran"
    yt_title = f"{clean_hook} ➔ Surah {surah_name_en} ({range_str}) | {reciter_short} #Shorts #Quran"
    if len(yt_title) > 95:
        yt_title = f"Surah {surah_name_en} ({range_str}) | Beautiful Quran Recitation #Shorts #Quran"

    fb_title = f"{clean_hook} ➔ Surah {surah_name_en} ({range_str}) | {reciter_en}"

    verses = verse_data.get("verses", [])
    reflection = verse_data.get("reflection_bn", "")

    # Global International Bilingual Description
    description = (
        f"✨ {clean_hook} ✨\n"
        f"📖 Surah: {surah_name_en} ({surah_name_bn}) | Verses: {range_str}\n"
        f"🎙️ Recited by: {reciter_en}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📜 Sacred Verses & English Translation:\n\n"
    )

    for v in verses:
        a_num = v.get("ayah_number", "")
        ar = v.get("arabic", "").strip()
        en = v.get("english", "").strip()
        description += f"({a_num}) {ar}\n"
        if en:
            description += f"“{en}”\n\n"
        else:
            description += "\n"

    # Bengali section
    description += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 বাংলা অর্থ:\n\n"
    )
    for v in verses:
        a_num = v.get("ayah_number", "")
        bn = v.get("bengali", "").strip()
        if bn:
            description += f"({a_num}) “{bn}”\n"

    if reflection:
        description += (
            f"\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🌿 কুরআনের বার্তা:\n"
            f"{reflection}\n"
        )

    description += (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🤍 Spread the words of the Holy Quran — Share with your loved ones.\n"
        f"The Prophet Muhammad (ﷺ) said: 'Whoever guides someone to goodness will have a reward like one who did it.' [Sahih Muslim: 1893] 🌿\n\n"
        f"⭐ Support our dawah with Facebook Stars if this touched your heart.\n\n"
        f"#Quran #QuranRecitation #Surah{surah_name_en.replace(' ', '').replace('-', '')} #Islam #Allah #IslamicReminder "
        f"#Muslim #Deen #ProphetMuhammad #Shorts #Reels #DailyDosIslam #Viral #fyp"
    )

    # Global Tags
    tags = [
        "Quran", "QuranRecitation", f"Surah{surah_name_en.replace(' ', '').replace('-', '')}",
        "Islam", "Allah", "Muslim", "IslamicReminder", "ProphetMuhammad",
        reciter_short, "Shorts", "Reels", "DailyDosIslam", "Viral", "fyp"
    ]

    return {
        "title": yt_title,
        "youtube_title": yt_title,
        "facebook_title": fb_title,
        "description": description.strip(),
        "pinned_comment": None,  # No first comment
        "tags": tags,
        "reciter_name": reciter_en,
        "surah_name": surah_name_en,
        "range_str": range_str
    }
