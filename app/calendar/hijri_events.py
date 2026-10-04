"""
Islamic Hijri Calendar & 500-Day Blessed Seasons Event Tracker (1448 AH – 1449 AH)
Optimized for Bangladesh & Global Crescent Sighting Standards.

Enables automated creation of high-retention 'Event Horizon' Sunnah alert videos,
Reels, and Post Carousels with psychological open-loop hooks.
"""

import datetime
from typing import Optional, Dict, Any, List

# Approximate Bangladeshi Hijri Month Starts for 1448 AH - 1449 AH (+1 day offset from Umm al-Qura)
# Format: (Year, Month, Day) representing 1st of that Hijri month in Bangladesh.
BANGLADESH_HIJRI_STARTS = [
    # 1448 AH
    ("1448-03", datetime.date(2026, 8, 15)), # 1 Rabi' al-Awwal 1448
    ("1448-04", datetime.date(2026, 9, 14)), # 1 Rabi' al-Thani 1448
    ("1448-05", datetime.date(2026, 10, 13)), # 1 Jumada al-Ula 1448
    ("1448-06", datetime.date(2026, 11, 12)), # 1 Jumada al-Thani 1448
    ("1448-07", datetime.date(2026, 12, 12)), # 1 Rajab 1448 (Sacred Month)
    ("1448-08", datetime.date(2027, 1, 11)),  # 1 Sha'ban 1448
    ("1448-09", datetime.date(2027, 2, 9)),   # 1 Ramadan 1448
    ("1448-10", datetime.date(2027, 3, 11)),  # 1 Shawwal 1448 (Eid al-Fitr)
    ("1448-11", datetime.date(2027, 4, 10)),  # 1 Dhul-Qi'dah 1448 (Sacred Month)
    ("1448-12", datetime.date(2027, 5, 9)),   # 1 Dhul-Hijjah 1448 (10 Blessed Days)
    # 1449 AH
    ("1449-01", datetime.date(2027, 6, 7)),   # 1 Muharram 1449 (Sacred Month & Islamic New Year)
    ("1449-02", datetime.date(2027, 7, 7)),   # 1 Safar 1449
    ("1449-03", datetime.date(2027, 8, 5)),   # 1 Rabi' al-Awwal 1449
    ("1449-04", datetime.date(2027, 9, 4)),   # 1 Rabi' al-Thani 1449
    ("1449-05", datetime.date(2027, 10, 3)),  # 1 Jumada al-Ula 1449
    ("1449-06", datetime.date(2027, 11, 2)),  # 1 Jumada al-Thani 1449
    ("1449-07", datetime.date(2027, 12, 1)),  # 1 Rajab 1449 (Sacred Month)
    ("1449-08", datetime.date(2027, 12, 31)), # 1 Sha'ban 1449
    ("1449-09", datetime.date(2028, 1, 29)),  # 1 Ramadan 1449
]

BENGALI_HIJRI_MONTHS = {
    1: "মুহররম",
    2: "সফর",
    3: "রবিউল আউয়াল",
    4: "রবিউস সানি",
    5: "জমাদিউল আউয়াল",
    6: "জমাদিউস সানি",
    7: "রজব",
    8: "শাবান",
    9: "রমজান",
    10: "শাওয়াল",
    11: "জিলকদ",
    12: "জিলহজ",
}

BENGALI_GREGORIAN_MONTHS = {
    1: "জানুয়ারি",
    2: "ফেব্রুয়ারি",
    3: "মার্চ",
    4: "এপ্রিল",
    5: "মে",
    6: "জুন",
    7: "জুলাই",
    8: "আগস্ট",
    9: "সেপ্টেম্বর",
    10: "অক্টোবর",
    11: "নভেম্বর",
    12: "ডিসেম্বর",
}

BENGALI_WEEKDAYS = {
    0: "সোমবার",
    1: "মঙ্গলবার",
    2: "বুধবার",
    3: "বৃহস্পতিবার",
    4: "শুক্রবার",
    5: "শনিবার",
    6: "রবিবার",
}

def to_bengali_num(n: Any) -> str:
    """Converts English numerals to Bengali digits."""
    bn_digits = {"0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪", "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯"}
    return "".join(bn_digits.get(ch, ch) for ch in str(n))

def format_bangladesh_and_hijri_date(target_date: Optional[datetime.date] = None) -> dict[str, str]:
    """
    Formats complete Gregorian date for Bangladesh and Islamic Hijri date in Bengali.
    """
    if target_date is None:
        target_date = get_current_bangladesh_date()

    hijri_day, hijri_month, hijri_key = get_approx_hijri_day_for_date(target_date)
    hijri_year_str = hijri_key.split("-")[0]
    hijri_year_bn = to_bengali_num(hijri_year_str)
    hijri_day_bn = to_bengali_num(hijri_day)
    hijri_month_bn = BENGALI_HIJRI_MONTHS.get(hijri_month, "হিজরি")

    greg_day_bn = to_bengali_num(target_date.day)
    greg_month_bn = BENGALI_GREGORIAN_MONTHS.get(target_date.month, "")
    greg_year_bn = to_bengali_num(target_date.year)
    weekday_bn = BENGALI_WEEKDAYS.get(target_date.weekday(), "")

    gregorian_display = f"{greg_day_bn} {greg_month_bn} {greg_year_bn} ({weekday_bn})"
    hijri_display = f"{hijri_day_bn} {hijri_month_bn} {hijri_year_bn} হিজরি"
    badge_display = f"{greg_day_bn} {greg_month_bn} • {hijri_day_bn} {hijri_month_bn}"

    return {
        "gregorian_bn": gregorian_display,
        "hijri_bn": hijri_display,
        "badge_bn": badge_display,
        "full_display": f"বাংলাদেশ: {gregorian_display} | হিজরি: {hijri_display}",
        "caption_header": f"📅 বাংলাদেশ তারিখ: {gregorian_display}\n🌙 হিজরি তারিখ: {hijri_display}"
    }

# Major Chronological Milestones (Gregorian range in Bangladesh)
MAJOR_ANNUAL_SEASONS = [
    {
        "key": "rajab_1448",
        "name": "পবিত্র রজব মাস (Sacred Month of Rajab 1448)",
        "start": datetime.date(2026, 12, 12),
        "end": datetime.date(2027, 1, 10),
        "theme": "হারাম চার মাসের একটি, গুনাহ থেকে আত্মরক্ষা ও নফল ইবাদতের প্রস্তুতি",
        "day_reminder": "পবিত্র রজব মাস (চারটি পবিত্র হারাম মাসের একটি)",
        "prophet_ebadah": "গুনাহ থেকে কঠোরভাবে আত্মরক্ষা, অধিক নফল নামাজ, নফল রোজা ও রমজানের আত্মশুদ্ধির প্রস্তুতি",
        "hadith_ref": "সহীহ বুখারী: ৩১৯৭, সূরা আত-তাওবাহ ৯:৩৬",
        "guidance": "Focus on Rajab being one of the four sacred months (Ashhur al-Hurum, Surah At-Tawbah 9:36, Bukhari 3197). Emphasize that sins are graver and good deeds carry amplified weight. Highlight the Prophet's instruction to purify oneself for Ramadan.",
        "model_hook": "হাজারো মানুষ জানেন না এই ৪টি পবিত্র মাসে একটি সাধারণ গুনাহের শাস্তি কেন দ্বিগুণ হয়?",
        "suggested_cta": "☞ হারাম মাসের বিশেষ আমলটি ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "shaban_1448",
        "name": "পবিত্র শাবান মাস ও প্রস্তুতি (Month of Sha'ban 1448)",
        "start": datetime.date(2027, 1, 11),
        "end": datetime.date(2027, 2, 8),
        "theme": "রমজানের পূর্বপ্রস্তুতি, নবীজির সর্বাধিক নফল রোজা ও আমল পেশ",
        "day_reminder": "পবিত্র শাবান মাস (রমজানের ঠিক পূর্ববর্তী মোবারক মাস)",
        "prophet_ebadah": "নবীজি (ﷺ)-এর সর্বাধিক নফল রোজা রাখা এবং আল্লাহর দরবারে আমলনামা পেশের সময় রোজাদার থাকা",
        "hadith_ref": "সহীহ বুখারী: ১৯৬৯, সহীহ মুসলিম: ১১৫৬, সুনানে নাসাঈ: ২৩৫৭",
        "guidance": "Focus on the Prophet (ﷺ) fasting more in Sha'ban than any other month outside Ramadan (Bukhari 1969, Muslim 1156). He said it is a month people neglect between Rajab and Ramadan, where deeds are raised to Allah, and he loved his deeds to be raised while fasting.",
        "model_hook": "রমজানের আগে নবীজি (ﷺ) পুরো শাবান মাস জুড়ে কেন এত বেশি নফল রোজা রাখতেন?",
        "suggested_cta": "☞ নবীজির শাবানের আমলটি ক্যাপশনে জানুন ➔"
    },
    {
        "key": "nisf_shaban_1448",
        "name": "১৫ শাবান — শবে বরাত ও ক্ষমা প্রার্থনা (Mid-Sha'ban 1448)",
        "start": datetime.date(2027, 1, 24),
        "end": datetime.date(2027, 1, 26),
        "theme": "আল্লাহর সাধারণ ক্ষমা, তওবা, রাতের নামাজ ও দিনের নফল রোজা",
        "day_reminder": "১৫ শাবান — নিসফে শাবানের রাত ও দিনের সিয়াম",
        "prophet_ebadah": "রাতের নামাজ (কিয়ামুল লাইল), ইস্তিগফার, দিনের নফল সিয়াম এবং অন্তরে ভাইদের প্রতি হিংসা-বিদ্বেষ ও শিরক সম্পূর্ণরূপে দূর করা",
        "hadith_ref": "সুনানে ইবনে মাজাহ: ১৩৮৮, ১৩৯০",
        "guidance": "Focus on Allah forgiving His creation on the night of Mid-Sha'ban except the polytheist and the one holding malice/grudge against his brother (Ibn Majah 1390). Sincere repentance, solitary night prayer, and clearing hatred from the heart.",
        "model_hook": "১৫ শাবানের রাতে আল্লাহ সবাইকে ক্ষমা করে দিলেও কোন ২ শ্রেণির মানুষকে ক্ষমা করেন না?",
        "suggested_cta": "☞ ক্ষমার সেই শর্ত দুটি ক্যাপশনে পড়ুন ➔"
    },
    {
        "key": "ramadan_1448",
        "name": "পবিত্র মাহে রমজান (The Blessed Month of Ramadan 1448)",
        "start": datetime.date(2027, 2, 9),
        "end": datetime.date(2027, 3, 10),
        "theme": "ফরজ সিয়াম, কিয়ামুল লাইল (তারাবীহ), কুরআন তিলাওয়াত ও অসীম রহমত",
        "day_reminder": "পবিত্র মাহে রমজান (রহমত, মাগফিরাত ও নাজাতের মাস)",
        "prophet_ebadah": "ফরজ সিয়াম পালন, কিয়ামুল লাইল (তারাবীহ), প্রতিদিন ইফতারের ঠিক পূর্বমুহূর্তে রবের কাছে খাস দোয়া, কুরআন তিলাওয়াত ও অকাতরে দান",
        "hadith_ref": "সহীহ বুখারী: ৩৭, ৩৮, জামে তিরমিযী: ৩৫৯৮",
        "guidance": "Focus on the immense blessings of Ramadan (Bukhari 37, 38). Gates of Jannah opened, gates of Hellfire closed, devils chained. The Prophet's Sunnah of Dua right before Iftar (Tirmidhi 3598).",
        "model_hook": "রমজানের প্রতিদিন ইফতারের ঠিক আগে কোন দোয়াটি পড়লে কখনো ফিরিয়ে দেওয়া হয় না?",
        "suggested_cta": "☞ ইফতারের মুহূর্তের খাস দোয়াটি ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "qadr_1448",
        "name": "লাইলাতুল কদর ও শেষ দশ রাত (Last 10 Nights & Laylat al-Qadr)",
        "start": datetime.date(2027, 2, 28),
        "end": datetime.date(2027, 3, 10),
        "theme": "১০০০ মাসের চেয়েও শ্রেষ্ঠ রাত, ক্ষমা ও তওবার সর্বশ্রেষ্ঠ মুহূর্ত",
        "day_reminder": "লাইলাতুল কদরের অনুসন্ধান (রমজানের শেষ দশ রাত: ২১, ২৩, ২৫, ২৭, ২৯তম রাত)",
        "prophet_ebadah": "তাহাজ্জুদ নামাজ, মসজিদে ইতিকাফ, এবং মা আয়েশাকে শেখানো ক্ষমা প্রার্থনার দোয়া: 'আল্লাহুম্মা ইন্নাকা আফুউউন তুহিব্বুল আফওয়া ফা'ফু আন্নী'",
        "hadith_ref": "জামে তিরমিযী: ৩৫১৩, সহীহ বুখারী: ২০২৪",
        "guidance": "Focus on seeking Laylat al-Qadr in the odd nights (21, 23, 25, 27, 29). The exact Dua taught to Aisha (RA): 'Allahumma innaka 'afuwwun tuhibbul 'afwa fa'fu 'anni' (Tirmidhi 3513). Tahajjud, I'tikaf, shedding tears in solitude.",
        "model_hook": "মা আয়েশা (রা.) নবীজিকে জিজ্ঞেস করেছিলেন: কদরের রাতে কোন ১টি দোয়া পড়ব? নবীজির সেই শ্রেষ্ঠ দোয়া...",
        "suggested_cta": "☞ কদরের রাতের সেই ভারী দোয়াটি ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "eid_fitr_1448",
        "name": "পবিত্র ঈদুল ফিতর (Eid al-Fitr 1448)",
        "start": datetime.date(2027, 3, 11),
        "end": datetime.date(2027, 3, 12),
        "theme": "ফিতরা আদায়, ঈদের নামাজ ও তাকবীর (এই দিনে রোজা রাখা হারাম)",
        "day_reminder": "পবিত্র ঈদুল ফিতর (১ শাওয়াল — সিয়াম সমাপ্তির মহোৎসব)",
        "prophet_ebadah": "ঈদের নামাজের পূর্বে সদকাতুল ফিতর আদায়, বিজোড় সংখ্যক খেজুর খেয়ে ঈদগাহে যাওয়া, তাকবীর পাঠ ও আনন্দ প্রকাশ (এই দিনে রোজা রাখা হারাম)",
        "hadith_ref": "সহীহ বুখারী: ১৫০৩, ১৯৯৫",
        "guidance": "Focus on Sunnah of Eid al-Fitr: Zakat al-Fitr before the prayer (Bukhari 1503), eating dates in odd numbers before leaving, Takbeerat, meeting Muslims with joy.",
        "model_hook": "ঈদের দিন নামাজে যাওয়ার আগে নবীজি (ﷺ) কোন ছোট সুন্নাতটি কখনো বাদ দিতেন না?",
        "suggested_cta": "☞ ঈদের সকালের সুন্নাতটি ক্যাপশনে জানুন ➔"
    },
    {
        "key": "shawwal_six_1448",
        "name": "শাওয়ালের ৬ রোজা (Six Days of Shawwal 1448)",
        "start": datetime.date(2027, 3, 12),
        "end": datetime.date(2027, 4, 9),
        "theme": "রমজানের পর ৬টি রোজা রেখে সারাবছর রোজা রাখার সমতুল্য সওয়াব",
        "day_reminder": "শাওয়ালের ৬ রোজা (ঈদের পর পুরো শাওয়াল মাস জুড়ে)",
        "prophet_ebadah": "রমজানের পর শাওয়াল মাসে যেকোনো ৬ দিন নফল সিয়াম পালন করা, যা ৩৬৫ দিন রোজা রাখার সওয়াব এনে দেয়",
        "hadith_ref": "সহীহ মুসলিম: ১১৬৪",
        "guidance": "Focus on Sahih Muslim 1164: whoever fasts Ramadan and follows it with six days of Shawwal, it is as if he fasted the entire year. Explain the divine math (each good deed multiplied by 10).",
        "model_hook": "রমজানের পর মাত্র ৬ দিন রোজা রাখলে পুরো ৩৬৫ দিন রোজা রাখার সওয়াব কীভাবে হিসাব হয়?",
        "suggested_cta": "☞ ৩৬৫ দিনের সওয়াবের হিসাবটি ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "dhul_hijjah_10_1448",
        "name": "জিলহজের প্রথম ১০ দিন (First 10 Days of Dhul-Hijjah 1448)",
        "start": datetime.date(2027, 5, 9),
        "end": datetime.date(2027, 5, 18),
        "theme": "বছরের সর্বশ্রেষ্ঠ ১০ দিন, জিহাদের চেয়েও প্রিয় আমল, তাকবীর ও দান",
        "day_reminder": "জিলহজের প্রথম ১০ দিন (বছরের সর্বশ্রেষ্ঠ ১০টি দিন)",
        "prophet_ebadah": "১ থেকে ৯ জিলহজ নফল সিয়াম, অধিক তাকবীর (আল্লাহু আকবার), তাহলীল (লা ইলাহা ইল্লাল্লাহ) ও তাহমীদ (আলহামদুলিল্লাহ) পাঠ এবং সদকা বৃদ্ধি",
        "hadith_ref": "সহীহ বুখারী: ৯৬৯, মুসনাদে আহমাদ: ৫৪৪৬",
        "guidance": "Focus on Sahih al-Bukhari 969: there are no days in which righteous deeds are more beloved to Allah than these 10 days. Fasting days 1-9, abundant Dhikr (Tahleel, Takbeer, Tahmeed).",
        "model_hook": "সারা বছরের সব দিনের চেয়েও জিলহজের এই ১০ দিনের একটি ছোট আমল আল্লাহর কাছে এত প্রিয় কেন?",
        "suggested_cta": "☞ বছরের সেরা ১০ দিনের আমল ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "arafah_1448",
        "name": "পবিত্র আরাফা দিবস (Day of 'Arafah 1448)",
        "start": datetime.date(2027, 5, 16),
        "end": datetime.date(2027, 5, 18),
        "theme": "পেছনের ১ বছর ও সামনের ১ বছরের গুনাহ মাফ, দোয়া কবুলের শ্রেষ্ঠ দিন",
        "day_reminder": "পবিত্র আরাফা দিবস (৯ জিলহজ — হজের মূল দিন)",
        "prophet_ebadah": "অ-হাজীদের জন্য আরাফার দিনের ১ দিনের নফল সিয়াম পালন এবং আসরের পর থেকে মাগরিব পর্যন্ত সর্বোত্তম দোয়া পাঠ: 'লা ইলাহা ইল্লাল্লাহু ওয়াহদাহু লা শারীকা লাহু...'",
        "hadith_ref": "সহীহ মুসলিম: ১১৬২, জামে তিরমিযী: ৩৫৮৫",
        "guidance": "Focus on Sahih Muslim 1162: fasting on the Day of Arafah expiates sins of the preceding year and coming year. Best Dua is the Dua of Arafah (Tirmidhi 3585).",
        "model_hook": "মাত্র ১ দিনের একটি নফল রোজা কীভাবে পেছনের ১ বছর ও সামনের ১ বছরের গুনাহ মুছে দেয়?",
        "suggested_cta": "☞ আরাফার দিনের খাস আমল ও দোয়া ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "eid_adha_1448",
        "name": "ঈদুল আজহা ও তাশরীক (Eid al-Adha & Days of Tashreeq 1448)",
        "start": datetime.date(2027, 5, 18),
        "end": datetime.date(2027, 5, 21),
        "theme": "কুরবানি, তাকবীরে তাশরীক, খাওয়া-দাওয়া ও আল্লাহর জিকির (রোজা রাখা হারাম)",
        "day_reminder": "ঈদুল আজহা ও তাশরীকের দিনগুলো (১০, ১১, ১২, ১৩ জিলহজ)",
        "prophet_ebadah": "কুরবানি করা, প্রত্যেক ফরজ নামাজের পর তাকবীরে তাশরীক পাঠ, আনন্দ ও পানাহারের মাঝে আল্লাহর কৃতজ্ঞতা প্রকাশ (এই দিনগুলোতে রোজা রাখা সম্পূর্ণ হারাম)",
        "hadith_ref": "সহীহ মুসলিম: ১১৪১, সুনানে আবু দাউদ: ২৮১৩",
        "guidance": "Focus on Days of Tashreeq (11, 12, 13 Dhul-Hijjah) being days of eating, drinking, and remembering Allah (Muslim 1141). Reciting Takbeer al-Tashreeq after every obligatory prayer.",
        "model_hook": "কুরবানির ঈদের দিনগুলোতে ভুলেও রোজা রাখা হারাম কেন? নবীজির (ﷺ) স্পষ্ট হুকুম...",
        "suggested_cta": "☞ তাশরীকের দিনগুলোর আমল ক্যাপশনে পড়ুন ➔"
    },
    {
        "key": "ashura_1449",
        "name": "পবিত্র আশুরা ও তাসুআ (9 & 10 Muharram 1449)",
        "start": datetime.date(2027, 6, 14),
        "end": datetime.date(2027, 6, 17),
        "theme": "মুসা (আ.)-এর মুক্তি, বিগত ১ বছরের গুনাহ মাফ, ৯ ও ১০ মহররমের সিয়াম",
        "day_reminder": "পবিত্র আশুরা ও তাসুআ (৯ ও ১০ মহররম)",
        "prophet_ebadah": "মুসা (আ.)-এর কৃতজ্ঞতায় ১০ মহররম নফল সিয়াম পালন (বিগত ১ বছরের গুনাহ মাফ) এবং অন্যান্য জাতির স্বাতন্ত্র্যে ৯ মহররমও অতিরিক্ত সিয়াম পালন করা",
        "hadith_ref": "সহীহ মুসলিম: ১১৩৪, ১১৬২",
        "guidance": "Focus on Sahih Muslim 1162: fasting Ashura expiates the sins of the past year. Also Muslim 1134: fasting the 9th along with the 10th to differ from earlier nations.",
        "model_hook": "আশুরার দিনে শুধু ১০ মহররম রোজা রাখলে নবীজি (ﷺ) কেন ৯ তারিখেও রোজা রাখতে বললেন?",
        "suggested_cta": "☞ কেন ৯ ও ১০ মহররম রোজা রাখবেন? ক্যাপশনে ➔"
    },
    {
        "key": "rajab_1449",
        "name": "পবিত্র রজব মাস ১৪৪৯ হিজরি (Sacred Month of Rajab 1449)",
        "start": datetime.date(2027, 12, 1),
        "end": datetime.date(2027, 12, 30),
        "theme": "হারাম চার মাসের একটি, গুনাহ থেকে আত্মরক্ষা ও নফল ইবাদতের প্রস্তুতি",
        "day_reminder": "পবিত্র রজব মাস ১৪৪৯ হিজরি (চারটি হারাম মাসের একটি)",
        "prophet_ebadah": "গুনাহ থেকে আত্মসংযম, নফল নামাজ ও সিয়ামের মাধ্যমে আত্মশুদ্ধি অর্জন",
        "hadith_ref": "সহীহ বুখারী: ৩১৯৭, সূরা আত-তাওবাহ ৯:৩৬",
        "guidance": "Focus on sacredness of Rajab in 1449 AH. Amplified weight of good deeds and grave warning against sins.",
        "model_hook": "পবিত্র রজব মাস শুরু: নবীজি (ﷺ) এই বিশেষ ৪টি মাসে গুনাহ থেকে এত সতর্ক করতেন কেন?",
        "suggested_cta": "☞ হারাম মাসের বিশেষ আমলটি ক্যাপশনে দেখুন ➔"
    },
    {
        "key": "shaban_1449",
        "name": "পবিত্র শাবান মাস ১৪৪৯ হিজরি (Month of Sha'ban 1449)",
        "start": datetime.date(2027, 12, 31),
        "end": datetime.date(2028, 1, 28),
        "theme": "রমজানের পূর্বপ্রস্তুতি, নবীজির সর্বাধিক নফল রোজা ও আমল পেশ",
        "day_reminder": "পবিত্র শাবান মাস ১৪৪৯ হিজরি (রমজানের আগের মাস)",
        "prophet_ebadah": "নবীজি (ﷺ)-এর সর্বাধিক নফল সিয়াম ও আমলনামা পেশের প্রস্তুতি",
        "hadith_ref": "সহীহ বুখারী: ১৯৬৯, সহীহ মুসলিম: ১১৫৬",
        "guidance": "Focus on Sha'ban 1449 AH. Fasting extensively to prepare the body and soul for Ramadan.",
        "model_hook": "রমজানের ঠিক আগের মাসে নবীজি (ﷺ) কেন এত বেশি নফল রোজা রাখতেন?",
        "suggested_cta": "☞ নবীজির শাবানের আমলটি ক্যাপশনে জানুন ➔"
    },
    {
        "key": "ramadan_1449",
        "name": "পবিত্র মাহে রমজান ১৪৪৯ হিজরি (Ramadan 1449)",
        "start": datetime.date(2028, 1, 29),
        "end": datetime.date(2028, 2, 14),
        "theme": "ফরজ সিয়াম, কিয়ামুল লাইল (তারাবীহ), কুরআন ও ক্ষমা",
        "day_reminder": "পবিত্র মাহে রমজান ১৪৪৯ হিজরি (মহিমান্বিত সিয়ামের মাস)",
        "prophet_ebadah": "ফরজ সিয়াম, কিয়ামুল লাইল, ইফতারের পূর্বে খাস দোয়া ও কুরআন তিলাওয়াত",
        "hadith_ref": "সূরা আল-বাকারা ২:১৮৫, সহীহ বুখারী: ৩৭",
        "guidance": "Focus on Ramadan 1449 AH beginning up to the 500-day window. Sincere fasting and devotion.",
        "model_hook": "মাহে রমজানের প্রথম দিনে নবীজির (ﷺ) শেখানো সেই ১টি আমল যা জান্নাতের দরজা খুলে দেয়...",
        "suggested_cta": "☞ রমজানের প্রথম দিনের আমল ক্যাপশনে দেখুন ➔"
    }
]


def get_current_bangladesh_date() -> datetime.date:
    """Returns today's date in Bangladesh Standard Time (UTC+6)."""
    now_utc = datetime.datetime.utcnow()
    bdt = now_utc + datetime.timedelta(hours=6)
    return bdt.date()


def get_approx_hijri_day_for_date(target_date: datetime.date) -> tuple[int, int, str]:
    """
    Returns (hijri_day, hijri_month, hijri_key) for the given Gregorian date in Bangladesh.
    """
    # Find matching month
    prev_m_key = None
    prev_m_start = None
    for m_key, m_start in BANGLADESH_HIJRI_STARTS:
        if target_date >= m_start:
            prev_m_key = m_key
            prev_m_start = m_start
        else:
            break
            
    if not prev_m_start:
        # Before roadmap
        return (1, 5, "1448-05")
        
    diff_days = (target_date - prev_m_start).days
    hijri_day = diff_days + 1
    parts = prev_m_key.split("-")
    hijri_month = int(parts[1])
    return (hijri_day, hijri_month, prev_m_key)


def get_active_or_upcoming_hijri_event(target_date: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """
    Intelligently determines if a major annual season, Ayyam al-Beed,
    Jumu'ah, or Sunnah Fasting (Mon/Thu) is happening today or within 24-48 hours.
    
    Priority Order:
    1. Major Annual Specific Days (Arafah, Ashura, Qadr, Nisf Sha'ban, Eid)
    2. Ayyam al-Beed (13, 14, 15 Hijri — Alert fired on 11th/12th through 15th)
    3. Major Annual Seasons (Ramadan, Dhul-Hijjah 1-10, Sha'ban, Rajab, Shawwal 6)
    4. Weekly Jumu'ah (Thursday evening / Friday)
    5. Weekly Monday / Thursday Fasting (Sunday evening or Wednesday evening)
    """
    if target_date is None:
        target_date = get_current_bangladesh_date()

    hijri_day, hijri_month, hijri_key = get_approx_hijri_day_for_date(target_date)
    weekday = target_date.weekday() # 0 = Monday, 3 = Thursday, 4 = Friday, 6 = Sunday

    # --- Priority 1: Check High-Stakes Specific Annual Days (sorted by duration so specific events take precedence) ---
    matching_seasons = [s for s in MAJOR_ANNUAL_SEASONS if s["start"] <= target_date <= s["end"]]
    matching_seasons.sort(key=lambda s: (s["end"] - s["start"]).days)

    if matching_seasons:
        top_season = matching_seasons[0]
        # If it's a specific acute milestone (<= 12 days, like Arafah, Qadr, Eid, Nisf Sha'ban)
        if (top_season["end"] - top_season["start"]).days <= 12:
            return {
                "event_key": top_season["key"],
                "name": top_season["name"],
                "theme": top_season["theme"],
                "day_reminder": top_season.get("day_reminder", top_season["name"]),
                "prophet_ebadah": top_season.get("prophet_ebadah", ""),
                "hadith_ref": top_season.get("hadith_ref", ""),
                "guidance": top_season["guidance"],
                "model_hook": top_season["model_hook"],
                "suggested_cta": top_season["suggested_cta"],
                "priority": "highest_acute"
            }

    # --- Priority 2: Monthly Ayyam al-Beed (13th, 14th, 15th of lunar month) ---
    # Trigger alert on 11th, 12th, 13th, 14th, 15th
    # Exclude Ramadan and Days of Tashreeq (10-13 Dhul-Hijjah) where fasting is either fardh or haram
    if 11 <= hijri_day <= 15 and hijri_month != 9 and not (hijri_month == 12 and hijri_day in [10, 11, 12, 13]):
        if hijri_day in [11, 12]:
            alert_prefix = "আর মাত্র ১-২ দিন পর শুরু হচ্ছে"
        else:
            alert_prefix = f"আজ আইয়ামে বিজের {hijri_day - 12}য় দিন"
            
        return {
            "event_key": f"ayyam_al_beed_{hijri_key}",
            "name": f"আইয়ামে বিজের ৩ দিনের নফল রোজা ({alert_prefix})",
            "theme": "প্রতি চান্দ্র মাসের ১৩, ১৪ ও ১৫ তারিখে রোজা রাখলে সারাজীবন রোজা রাখার সওয়াব",
            "day_reminder": f"আসন্ন আইয়ামে বিজ — {alert_prefix} (১৩, ১৪, ১৫ হিজরি)",
            "prophet_ebadah": "চান্দ্র মাসের পূর্ণিমার ৩ দিন নফল সিয়াম পালন করা, যা সারাজীবন রোজা রাখার সমতুল্য সওয়াব এনে দেয়",
            "hadith_ref": "সহীহ বুখারী: ১৯৮১, সহীহ মুসলিম: ১১৫৯",
            "guidance": "Focus on Ayyam al-Beed (13th, 14th, 15th of Hijri month). The Prophet (ﷺ) never abandoned them and said: 'Fasting three days of every month is like fasting for an entire lifetime' (Sahih al-Bukhari 1981, Sahih Muslim 1159). Remind people of the exact date in Bangladesh and urge them to fast.",
            "model_hook": "মাসে মাত্র ৩ দিন রোজা রেখে পুরো জীবন রোজা রাখার সওয়াব কীভাবে পাওয়া যায়?",
            "suggested_cta": "☞ কোন ৩ দিন রোজা রাখবেন? ক্যাপশনে দেখুন ➔",
            "priority": "high"
        }

    # --- Priority 3: Major Ongoing Seasonal Windows ---
    for season in MAJOR_ANNUAL_SEASONS:
        if season["start"] <= target_date <= season["end"]:
            return {
                "event_key": season["key"],
                "name": season["name"],
                "theme": season["theme"],
                "day_reminder": season.get("day_reminder", season["name"]),
                "prophet_ebadah": season.get("prophet_ebadah", ""),
                "hadith_ref": season.get("hadith_ref", ""),
                "guidance": season["guidance"],
                "model_hook": season["model_hook"],
                "suggested_cta": season["suggested_cta"],
                "priority": "medium_seasonal"
            }

    # --- Priority 4: Weekly Yawm al-Jumu'ah (Friday) ---
    # Trigger on Thursday afternoon/night (weekday == 3) or Friday daytime (weekday == 4)
    if weekday == 4: # Friday
        return {
            "event_key": "jumuah_today",
            "name": "পবিত্র জুমার দিনের বিশেষ আমল ও কবুলিয়াতের মুহূর্ত",
            "theme": "সপ্তাহের সেরা দিন, সূরা কাহাফ, দরূদ শরীফ এবং আসর-মাগরিবের শেষ ৬০ মিনিটের দোয়া",
            "day_reminder": "আজ পবিত্র জুমাবার (সপ্তাহের সর্বশ্রেষ্ঠ দিন)",
            "prophet_ebadah": "১. সূরা কাহাফ তিলাওয়াত, ২. নবীজির ওপর অধিক দরূদ পাঠ, ৩. আসর থেকে মাগরিবের শেষ ৬০ মিনিটে দোয়া (সা‘আতুল ইস্তিজাবাহ), ৪. গোসল ও সুগন্ধি মেখে মসজিদে আগেভাগে যাওয়া",
            "hadith_ref": "সহীহ মুসলিম: ৮৫৪, সুনানে আবু দাউদ: ১০৪৮, সুনানে আবু দাউদ: ১০৪৭, হাকেম: ৩৩৯২",
            "guidance": "Focus on Friday being the best day of the week (Sahih Muslim 854). Specifically highlight Sa'at al-Istijabah (the hour of accepted prayers) in the final hour after Asr before Maghrib (Sunan Abi Dawud 1048), Surah Al-Kahf illumination (Mustadrak 3392), and abundant Salawat.",
            "model_hook": "জুমার দিনে আসর থেকে মাগরিবের মাঝে ঠিক কোন মুহূর্তে সব দোয়া কবুল হয়?",
            "suggested_cta": "☞ কবুল হওয়ার সেই গোপন মুহূর্তটি ক্যাপশনে দেখুন ➔",
            "priority": "weekly_jumuah"
        }
    elif weekday == 3: # Thursday eve
        return {
            "event_key": "jumuah_eve",
            "name": "জুমার রাতের পূর্বপ্রস্তুতি ও বরকতময় আমল",
            "theme": "জুমার দিনের মর্যাদা, রাত থেকে দরূদ শরীফ শুরু এবং জুমার প্রস্তুতি",
            "day_reminder": "জুমার রাত (বৃহস্পতিবার সূর্যাস্তের পর থেকে)",
            "prophet_ebadah": "বৃহস্পতিবার সূর্যাস্তের পর থেকেই নবীজি (ﷺ)-এর ওপর অধিক দরূদ শরীফ পাঠ এবং জুমার দিনের প্রস্তুতি গ্রহণ",
            "hadith_ref": "সুনানে বায়হাকী: ৫৯৯৪",
            "guidance": "Focus on preparing for Friday: ritual bath, wearing clean clothes, reciting Salawat abundantly starting from Thursday sunset through Friday.",
            "model_hook": "বৃহস্পতিবার সূর্যাস্তের পর থেকে নবীজি (ﷺ) কোন আমলটি শতগুণ বাড়িয়ে দিতেন?",
            "suggested_cta": "☞ জুমার খাস আমলগুলো ক্যাপশনে জেনে নিন ➔",
            "priority": "weekly_jumuah"
        }

    # --- Priority 5: Weekly Monday & Thursday Voluntary Fasting ---
    # Sunday (weekday == 6) -> Alert for Monday Fast
    if weekday == 6:
        return {
            "event_key": "monday_fast_eve",
            "name": "সোমবারের নফল রোজা ও আমল পেশের দিন",
            "theme": "সোমবার আল্লাহর কাছে আমল পেশ করা হয় এবং নবীজির জন্ম ও ওহীর দিন",
            "day_reminder": "আগামীকাল সোমবার (সাপ্তাহিক আমলনামা পেশের দিন)",
            "prophet_ebadah": "সোমবারের নফল সিয়াম পালন করা (যেদিন আল্লাহর দরবারে আমলনামা পেশ করা হয় এবং যেদিন নবীজি জন্মগ্রহণ করেছিলেন ও ওহী পেয়েছিলেন)",
            "hadith_ref": "জামে তিরমিযী: ৭৪৭, সহীহ মুসলিম: ১১৬২",
            "guidance": "Focus on voluntary fasting on Monday. The Prophet (ﷺ) said: 'Deeds are presented on Monday and Thursday, and I love that my deeds be presented while I am fasting' (Tirmidhi 747). He was also born and received revelation on Monday (Muslim 1162).",
            "model_hook": "নবীজি (ﷺ) প্রতি সোমবার নিজের পেটে পাথর বেঁধেও কেন রোজা ছাড়তেন না?",
            "suggested_cta": "☞ সোমবার রোজা রাখার রহস্যটি ক্যাপশনে পড়ুন ➔",
            "priority": "weekly_fast"
        }
    # Wednesday (weekday == 2) -> Alert for Thursday Fast
    elif weekday == 2:
        return {
            "event_key": "thursday_fast_eve",
            "name": "বৃহস্পতিবারের নফল রোজা ও সাপ্তাহিক আমল পেশ",
            "theme": "বৃহস্পতিবার আমলনামা আল্লাহর দরবারে তোলা হয়",
            "day_reminder": "আগামীকাল বৃহস্পতিবার (সাপ্তাহিক আমলনামা পেশের দিন)",
            "prophet_ebadah": "বৃহস্পতিবারের নফল সিয়াম পালন করা (সাপ্তাহিক আমলনামা পেশ ও ক্ষমা লাভের সুন্নাত সিয়াম)",
            "hadith_ref": "জামে তিরমিযী: ৭৪৭",
            "guidance": "Focus on fasting Thursday as the weekly closure of deeds being presented to Allah (Jami' at-Tirmidhi 747). Sins are forgiven except for those with mutual hatred.",
            "model_hook": "প্রতি বৃহস্পতিবার সূর্যাস্তের ঠিক আগে আমাদের আমলনামা কোথায় নিয়ে যাওয়া হয়?",
            "suggested_cta": "☞ সহীহ হাদিসের সেই বর্ণনাটি ক্যাপশনে পড়ুন ➔",
            "priority": "weekly_fast"
        }

    return None
