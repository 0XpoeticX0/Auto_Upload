# -*- coding: utf-8 -*-
"""
Metadata & Caption Generator for Quran Recitation Videos.
Creates professional titles, detailed contextual descriptions, full Arabic & Bengali text,
and high-converting dawah hashtags.
"""

def generate_quran_metadata(verse_data: dict, audio_data: dict) -> dict:
    """
    Generates YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok metadata.
    """
    surah_name = verse_data["surah_name_bn"]
    range_str = verse_data["verse_range_str"]
    reciter_info = audio_data["reciter"]
    reciter_bn = reciter_info["name_bn"]
    badge_name = reciter_info.get("title_badge", reciter_bn)
    theme_headline = verse_data.get("theme_headline", "কোরআনের পরম শান্তি ও হেদায়াত")
    reflection = verse_data.get("reflection_bn", "")
    verses = verse_data.get("verses", [])

    # High-converting title (< 100 characters)
    # e.g., "কঠিন সময়ে মন শান্ত করার আয়াত—সূরা আশ-শারহ | মিশারি আল-আফাসি #Shorts"
    clean_headline = theme_headline.replace("(", "").replace(")", "")
    if len(clean_headline) > 35:
        clean_headline = clean_headline[:35]

    yt_title = f"{clean_headline}—{surah_name} (আয়াত {range_str}) | {badge_name} #Shorts"
    if len(yt_title) > 95:
        yt_title = f"{surah_name} (আয়াত {range_str}) | {badge_name} #Shorts"

    # Detailed Description
    description = (
        f"✨ পবিত্র কুরআন তিলাওয়াত ও বাংলা অনুবাদ ✨\n"
        f"📖 {surah_name} • আয়াত {range_str}\n"
        f"🎙️ তিলাওয়াত: {reciter_bn}\n"
        f"📖 উৎস: EveryAyah.com / Quran.com API (Free Religious & Educational Public Distribution)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📜 আয়াত ও বাংলা অর্থ:\n\n"
    )

    bn_digits = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    def to_bn(n):
        return "".join(bn_digits.get(c, c) for c in str(n))

    for v in verses:
        a_num = to_bn(v.get("ayah_number", ""))
        ar = v.get("arabic", "").strip()
        bn = v.get("bengali", "").strip()
        description += f"({a_num}) {ar}\n"
        description += f"🗣️ অর্থ: “{bn}”\n\n"

    if reflection:
        description += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌿 কুরআনের বার্তা ও সান্ত্বনা:\n"
            f"{reflection}\n\n"
        )

    description += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 পরবর্তীতে তিলাওয়াত শোনার জন্য ভিডিওটি 🔖 Save করে রাখুন।\n"
        f"🤍 কুরআন ও সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন।\n"
        f"রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿\n\n"
        f"👉 প্রতিদিনের বিশুদ্ধ কুরআন তিলাওয়াত ও সহীহ হাদিসের জন্য Follow করুন: @dailydos_islam\n\n"
        f"#Quran #QuranTilawat #কুরআন_তিলাওয়াত #{surah_name.replace(' ', '_')} "
        f"#IslamicReminders #MuslimUmmah #DeenOverDunya #Alhamdulillah #Shorts #Reels #ViralReels"
    )

    pinned_comment = (
        f"আলহামদুলিল্লাহ! পবিত্র কুরআনের এই আয়াতটি আপনার হৃদয়ে কেমন অনুভূতি সৃষ্টি করেছে? "
        f"মন্তব্যে শেয়ার করুন এবং সহীহ দ্বীনি দাওয়াত ছড়িয়ে দিতে ভিডিওটি Share করুন। 🤲🌿"
    )

    tags = [
        "Quran", "QuranRecitation", "কুরআন_তিলাওয়াত",
        surah_name.replace(" ", ""), "Islam", "DailyDos",
        badge_name.replace(" ", ""), "Shorts", "Reels"
    ]

    return {
        "title": yt_title,
        "description": description.strip(),
        "pinned_comment": pinned_comment,
        "tags": tags,
        "reciter_name": reciter_bn,
        "surah_name": surah_name,
        "range_str": range_str
    }
