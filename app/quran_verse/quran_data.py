# -*- coding: utf-8 -*-
"""
Quran Data Fetcher & AI Contextual Passage Selector.
Fetches authentic Uthmani Arabic text and verified Bengali translations from Quran.com API v4,
and provides Gemini-powered complete self-contained passage selection.
"""

import os
import urllib.request
import urllib.parse
import json
import re
import unicodedata
from app.logger import logger
from app.llm.provider import extract_json

_ISLAMIC_FOUNDATION_DB = None

def get_islamic_foundation_db() -> dict:
    """Loads Islamic Foundation Bangladesh Bengali Quran dataset into memory."""
    global _ISLAMIC_FOUNDATION_DB
    if _ISLAMIC_FOUNDATION_DB is not None:
        return _ISLAMIC_FOUNDATION_DB

    paths = [
        os.path.join("app", "assets", "quran", "islamic_foundation_quran.json"),
        os.path.join("data", "quran_islamic_foundation.json")
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _ISLAMIC_FOUNDATION_DB = json.load(f)
                    logger.info(f"Loaded Islamic Foundation Bangladesh Quran translation ({len(_ISLAMIC_FOUNDATION_DB)} verses).")
                    return _ISLAMIC_FOUNDATION_DB
            except Exception as e:
                logger.warning(f"Failed to load {p}: {e}")

    _ISLAMIC_FOUNDATION_DB = {}
    return _ISLAMIC_FOUNDATION_DB

# Supported pure studio / authentic renowned reciters chosen by user
RECITERS_CONFIG = {
    "alafasy": {
        "id": "alafasy",
        "name_bn": "শায়খ মিশারি রশিদ আল-আফাসি",
        "name_en": "Sheikh Mishary Rashid Alafasy",
        "folder": "Alafasy_128kbps",
        "title_badge": "মিশারি আল-আফাসি",
        "style": "মধুর, স্পষ্ট ও সর্বজনপ্রিয় সুরেলা কণ্ঠ"
    },
    "dossari": {
        "id": "dossari",
        "name_bn": "শায়খ ইয়াসির আদ-দাওসারি",
        "name_en": "Sheikh Yasser Al-Dossari",
        "folder": "Yasser_Ad-Dussary_128kbps",
        "title_badge": "ইয়াসির আদ-দাওসারি",
        "style": "গম্ভীর, বলিষ্ঠ ও রাজকীয় তেজোদ্দীপ্ত তিলাওয়াত"
    }
}

# Phonetic Bengali names for major Surahs
SURAH_NAMES_BN = {
    1: "সূরা আল-ফাতিহা",
    2: "সূরা আল-বাক্বারাহ",
    3: "সূরা আলে ইমরান",
    4: "সূরা আন-নিসা",
    5: "সূরা আল-মায়িদাহ",
    6: "সূরা আল-আন'আম",
    7: "সূরা আল-আ'রাফ",
    8: "সূরা আল-আনফাল",
    9: "সূরা আত-তাওবাহ",
    10: "সূরা ইউনুস",
    11: "সূরা হুদ",
    12: "সূরা ইউসুফ",
    13: "সূরা আর-রাদ",
    14: "সূরা ইব্রাহিম",
    15: "সূরা আল-হিজর",
    16: "সূরা আন-নাহল",
    17: "সূরা বনি ইসরাঈল",
    18: "সূরা আল-কাহফ",
    19: "সূরা মারইয়াম",
    20: "সূরা ত্বাহা",
    21: "সূরা আল-আম্বিয়া",
    22: "সূরা আল-হাজ্জ",
    23: "সূরা আল-মু'মিনুন",
    24: "সূরা আন-নূর",
    25: "সূরা আল-ফুরকান",
    26: "সূরা আশ-শু'আরা",
    27: "সূরা আন-নামল",
    28: "সূরা আল-কাসাস",
    29: "সূরা আল-আনকাবুত",
    30: "সূরা আর-রূম",
    31: "সূরা লুকমান",
    32: "সূরা আস-সাজদাহ",
    33: "সূরা আল-আহযাব",
    34: "সূরা সাবা",
    35: "সূরা ফাতির",
    36: "সূরা ইয়াসীন",
    37: "সূরা আস-সাফফাত",
    38: "সূরা সাদ",
    39: "সূরা আয-যুমার",
    40: "সূরা গাফির",
    41: "সূরা ফুসসিলাত",
    42: "সূরা আশ-শুরা",
    43: "সূরা আয-যুখরুফ",
    44: "সূরা আদ-দুখান",
    45: "সূরা আল-জাসিয়াহ",
    46: "সূরা আল-আহকাফ",
    47: "সূরা মুহাম্মদ",
    48: "সূরা আল-ফাতহ",
    49: "সূরা আল-হুজুরাত",
    50: "সূরা ক্বাফ",
    51: "সূরা আয-যারিয়াত",
    52: "সূরা আত-তুর",
    53: "সূরা আন-নাজম",
    54: "সূরা আল-কামার",
    55: "সূরা আর-রহমান",
    56: "সূরা আল-ওয়াকি'আহ",
    57: "সূরা আল-হাদিদ",
    58: "সূরা আল-মুজাদালাহ",
    59: "সূরা আল-হাশর",
    60: "সূরা আল-মুমতাহানাহ",
    61: "সূরা আস-সাফ",
    62: "সূরা আল-জুমু'আহ",
    63: "সূরা আল-মুনাফিকুন",
    64: "সূরা আত-তাগাবুন",
    65: "সূরা আত-ত্বালাক্ব",
    66: "সূরা আত-তাহরীম",
    67: "সূরা আল-মুলক",
    68: "সূরা আল-কলম",
    69: "সূরা আল-হাক্কাহ",
    70: "সূরা আল-মা'আরিজ",
    71: "সূরা নূহ",
    72: "সূরা আল-জিন",
    73: "সূরা আল-মুযযাম্মিল",
    74: "সূরা আল-মুদ্দাসসির",
    75: "সূরা আল-কিয়ামাহ",
    76: "সূরা আল-ইনসান",
    77: "সূরা আল-মুরসালাত",
    78: "সূরা আন-নাবা",
    79: "সূরা আন-নাযি'আত",
    80: "সূরা 'আবাসা",
    81: "সূরা আত-তাকবীর",
    82: "সূরা আল-ইনফিতার",
    83: "সূরা আল-মুতাফফিফীন",
    84: "সূরা আল-ইনশিকাক",
    85: "সূরা আল-বুরুজ",
    86: "সূরা আত-তারিক",
    87: "সূরা আল-আ'লা",
    88: "সূরা আল-গাশিয়াহ",
    89: "সূরা আল-ফজর",
    90: "সূরা আল-বালাদ",
    91: "সূরা আশ-শামস",
    92: "সূরা আল-লাইল",
    93: "সূরা আদ-দুহা",
    94: "সূরা আশ-শারহ",
    95: "সূরা আত-তীন",
    96: "সূরা আল-আলাক",
    97: "সূরা আল-ক্বদর",
    98: "সূরা আল-বাইয়িনাহ",
    99: "সূরা আয-যালযালাহ",
    100: "সূরা আল-আদিয়াত",
    101: "সূরা আল-কারিয়াহ",
    102: "সূরা আত-তাকাসুর",
    103: "সূরা আল-আসর",
    104: "সূরা আল-হুমাযাহ",
    105: "সূরা আল-ফীল",
    106: "সূরা কুরাইশ",
    107: "সূরা আল-মা'উন",
    108: "সূরা আল-কাউসার",
    109: "সূরা আল-কাফিরুন",
    110: "সূরা আন-নাসর",
    111: "সূরা আল-লাহাব",
    112: "সূরা আল-ইখলাস",
    113: "সূরা আল-ফালাক",
    114: "সূরা আন-নাস"
}

SURAH_NAMES_EN = {
    1: "Al-Fatihah", 2: "Al-Baqarah", 3: "Ali 'Imran", 4: "An-Nisa", 5: "Al-Ma'idah",
    6: "Al-An'am", 7: "Al-A'raf", 8: "Al-Anfal", 9: "At-Tawbah", 10: "Yunus",
    11: "Hud", 12: "Yusuf", 13: "Ar-Ra'd", 14: "Ibrahim", 15: "Al-Hijr",
    16: "An-Nahl", 17: "Al-Isra", 18: "Al-Kahf", 19: "Maryam", 20: "Taha",
    21: "Al-Anbiya", 22: "Al-Hajj", 23: "Al-Mu'minun", 24: "An-Nur", 25: "Al-Furqan",
    26: "Ash-Shu'ara", 27: "An-Naml", 28: "Al-Qasas", 29: "Al-'Ankabut", 30: "Ar-Rum",
    31: "Luqman", 32: "As-Sajdah", 33: "Al-Ahzab", 34: "Saba", 35: "Fatir",
    36: "Ya-Sin", 37: "As-Saffat", 38: "Sad", 39: "Az-Zumar", 40: "Ghafir",
    41: "Fussilat", 42: "Ash-Shura", 43: "Az-Zukhruf", 44: "Ad-Dukhan", 45: "Al-Jathiyah",
    46: "Al-Ahqaf", 47: "Muhammad", 48: "Al-Fath", 49: "Al-Hujurat", 50: "Qaf",
    51: "Adh-Dhariyat", 52: "At-Tur", 53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahman",
    56: "Al-Waqi'ah", 57: "Al-Hadid", 58: "Al-Mujadila", 59: "Al-Hashr", 60: "Al-Mumtahanah",
    61: "As-Saf", 62: "Al-Jumu'ah", 63: "Al-Munafiqun", 64: "At-Taghabun", 65: "At-Talaq",
    66: "At-Tahrim", 67: "Al-Mulk", 68: "Al-Qalam", 69: "Al-Haqqah", 70: "Al-Ma'arij",
    71: "Nuh", 72: "Al-Jinn", 73: "Al-Muzzammil", 74: "Al-Muddaththir", 75: "Al-Qiyamah",
    76: "Al-Insan", 77: "Al-Mursalat", 78: "An-Naba", 79: "An-Nazi'at", 80: "'Abasa",
    81: "At-Takwir", 82: "Al-Infitar", 83: "Al-Mutaffifin", 84: "Al-Inshiqaq", 85: "Al-Buruj",
    86: "At-Tariq", 87: "Al-A'la", 88: "Al-Ghashiyah", 89: "Al-Fajr", 90: "Al-Balad",
    91: "Ash-Shams", 92: "Al-Layl", 93: "Ad-Duha", 94: "Ash-Sharh", 95: "At-Tin",
    96: "Al-'Alaq", 97: "Al-Qadr", 98: "Al-Bayyinah", 99: "Az-Zalzalah", 100: "Al-'Adiyat",
    101: "Al-Qari'ah", 102: "At-Takathur", 103: "Al-'Asr", 104: "Al-Humazah", 105: "Al-Fil",
    106: "Quraysh", 107: "Al-Ma'un", 108: "Al-Kawthar", 109: "Al-Kafirun", 110: "An-Nasr",
    111: "Al-Masad", 112: "Al-Ikhlas", 113: "Al-Falaq", 114: "An-Nas"
}

# Curated bank of guaranteed complete self-contained passages under 90s (Fallback & Rotation)
CURATED_COMPLETE_PASSAGES = [
    {
        "surah": 94,
        "ayah_start": 1,
        "ayah_end": 8,
        "theme_hint": "কষ্টের পরেই স্বস্তির মহাপ্রতিশ্রুতি (Surah Ash-Sharh Complete)",
        "reflection_bn": "আল্লাহ তায়ালা মুমিনকে সান্ত্বনা দিয়ে নিশ্চিত করেছেন যে, প্রতিটি সংকটের সাথেই আল্লাহ মুক্তির পথ ও প্রশান্তি নির্ধারণ করে রেখেছেন।",
        "ideal_reciter": "alafasy"  # Comfort, gentle solace & heart healing
    },
    {
        "surah": 93,
        "ayah_start": 1,
        "ayah_end": 11,
        "theme_hint": "হতাশা দূরীকরণ ও আল্লাহর গভীর অনুগ্রহ (Surah Ad-Duha Complete)",
        "reflection_bn": "আল্লাহ কখনো তাঁর বান্দাকে ত্যাগ করেন না। অন্ধকার রাতের পর যেমন সোনালী সকাল আসে, তেমনি জীবনের কঠিন সময়ও কেটে যায়।",
        "ideal_reciter": "alafasy"  # Warm reassurance & divine affection
    },
    {
        "surah": 65,
        "ayah_start": 2,
        "ayah_end": 3,
        "theme_hint": "তাকওয়া, অভাবনীয় রিজিক ও তাওয়াক্কুল (Surah At-Talaq 2-3)",
        "reflection_bn": "যে ব্যক্তি আল্লাহর ওপর তাওয়াক্কুল করে, আল্লাহ তাঁর জন্য এমন উৎস থেকে রিজিক দেন যা মানুষ কল্পনাও করতে পারে না এবং তার জন্য আল্লাহই যথেষ্ট।",
        "ideal_reciter": "dossari"  # Absolute Tawakkul, firm decree & high authority
    },
    {
        "surah": 3,
        "ayah_start": 173,
        "ayah_end": 174,
        "theme_hint": "হাসবুনাল্লাহু ওয়া নি'মাল ওয়াকিল ও নিরাপত্তা (Surah Al-Imran 173-174)",
        "reflection_bn": "বিপদে আল্লাহর ওপর পূর্ণ আস্থা রাখলে মহান আল্লাহ বান্দাকে অপূরণীয় বরকত ও নিরাপত্তা দান করেন।",
        "ideal_reciter": "dossari"  # Courage, steadfastness & battlefield resolve
    },
    {
        "surah": 21,
        "ayah_start": 87,
        "ayah_end": 88,
        "theme_hint": "ইউনুস (আ.)-এর দোয়া ও সর্বসংকট মুক্তি (Surah Al-Anbiya 87-88)",
        "reflection_bn": "মাছের পেটের মতো ঘোর অন্ধকারেও যখন নবী ইউনুস (আ.) খাঁটি তওবা করে ডাক দিয়েছিলেন, আল্লাহ সেই অসম্ভব সংকট থেকেও তাঁকে উদ্ধার করেছিলেন।",
        "ideal_reciter": "alafasy"  # Heartfelt repentance, sorrowful Dua & relief
    },
    {
        "surah": 2,
        "ayah_start": 255,
        "ayah_end": 255,
        "theme_hint": "আয়াতুল কুরসী—আল্লাহর সার্বভৌমত্ব ও পরাক্রম (Surah Al-Baqarah 255)",
        "reflection_bn": "পবিত্র কুরআনের সর্বশ্রেষ্ঠ এই আয়াতে আল্লাহর মহত্ত্ব, জীবন্ত সত্তা এবং নিখিল বিশ্বের ওপর তাঁর পূর্ণ কর্তৃত্বের প্রকাশ ঘটেছে।",
        "ideal_reciter": "dossari"  # Supreme majesty, divine sovereignty & awe
    },
    {
        "surah": 59,
        "ayah_start": 22,
        "ayah_end": 24,
        "theme_hint": "আল্লাহর গুণবাচক শ্রেষ্ঠ নামসমূহ—ইসমে আজম (Surah Al-Hashr 22-24)",
        "reflection_bn": "আল্লাহর পবিত্র গুণবাচক নামগুলোর জিকির হৃদয়ে গভীর ভয় ও শ্রদ্ধা জাগিয়ে তোলে।",
        "ideal_reciter": "dossari"  # Grandeur of divine attributes & cosmic reverence
    },
    {
        "surah": 2,
        "ayah_start": 285,
        "ayah_end": 286,
        "theme_hint": "আমানার রাসূলু—ক্ষমা, রহমত ও শক্তি চাওয়ার সেরা দোয়া (Surah Al-Baqarah 285-286)",
        "reflection_bn": "আল্লাহ কোনো আত্মাকে তার সাধ্যের অতিরিক্ত দায়িত্ব চাপান না। এই আয়াতদ্বয় রাতের বেলা পাঠ করলে সব অনিষ্ট থেকে সুরক্ষার জন্য যথেষ্ট।",
        "ideal_reciter": "alafasy"  # Supplication for mercy, forgiveness & soul peace
    },
    {
        "surah": 28,
        "ayah_start": 24,
        "ayah_end": 24,
        "theme_hint": "মুসা (আ.)-এর অভাব দূর ও সাহায্যের দোয়া (Surah Al-Qasas 24)",
        "reflection_bn": "মুসা (আ.) যখন একাকী, ক্ষুধার্ত ও সহায়হীন অবস্থায় গাছের ছায়ায় বসে কাতর কণ্ঠে এই দোয়া করেছিলেন, আল্লাহ তাৎক্ষণিক তাঁর খাদ্য, নিরাপত্তা ও পরিবারের ব্যবস্থা করে দিয়েছিলেন।",
        "ideal_reciter": "alafasy"  # Humble helplessness & intimate prayer
    },
    {
        "surah": 25,
        "ayah_start": 74,
        "ayah_end": 74,
        "theme_hint": "নেককার সন্তান ও সুখী দাম্পত্যের সেরা দোয়া (Surah Al-Furqan 74)",
        "reflection_bn": "পারিবারিক শান্তি ও চোখ জুড়ানো নেককার সন্তানের জন্য রহমানুর রাহীমের কাছে প্রার্থনার এক অনন্য শিক্ষা।",
        "ideal_reciter": "alafasy"  # Gentle family love & righteous lineage
    },
    {
        "surah": 89,
        "ayah_start": 27,
        "ayah_end": 30,
        "theme_hint": "প্রশান্ত আত্মার জন্য জান্নাতের ডাক (Surah Al-Fajr 27-30)",
        "reflection_bn": "যে আত্মা আল্লাহর ওপর সন্তুষ্ট থাকে, মৃত্যুর সময় আল্লাহ নিজে তাকে পরম সমাদরে জান্নাতে ডেকে নেন।",
        "ideal_reciter": "alafasy"  # Tranquility, peace & welcome into Jannah
    },
    {
        "surah": 55,
        "ayah_start": 26,
        "ayah_end": 30,
        "theme_hint": "মহিমান্বিত রবের চিরস্থায়িত্ব ও সব সৃষ্টির বিলুপ্তি (Surah Ar-Rahman 26-30)",
        "reflection_bn": "ভূমণ্ডলের সবকিছুই ধ্বংসশীল, কেবল আপনার মহিমাময় ও মহানুভব রবের সত্তাই চিরকাল অবিনশ্বর থাকবে। আসমান ও জমিনের সবাই তাঁরই মুখাপেক্ষী।",
        "ideal_reciter": "dossari"
    },
    {
        "surah": 50,
        "ayah_start": 16,
        "ayah_end": 19,
        "theme_hint": "আল্লাহ মানুষের গলার রগের চেয়েও নিকটে (Surah Qaf 16-19)",
        "reflection_bn": "মানুষের মনের প্রতিটি দ্বিধাদ্বন্দ্ব আল্লাহ জানেন। তিনি মানুষের শাহরগের চেয়েও অতি নিকটে বিরাজমান।",
        "ideal_reciter": "dossari"
    },
    {
        "surah": 14,
        "ayah_start": 39,
        "ayah_end": 41,
        "theme_hint": "ইব্রাহিম (আ.)-এর দোআ—নামাজ ও পিতা-মাতার জন্য ক্ষমা (Surah Ibrahim 39-41)",
        "reflection_bn": "ইব্রাহিম (আ.) আল্লাহর কাছে প্রার্থনা করেছিলেন যেন তিনি ও তাঁর বংশধরেরা আজীবন নামাজের ওপর প্রতিষ্ঠিত থাকতে পারেন।",
        "ideal_reciter": "alafasy"
    },
    {
        "surah": 18,
        "ayah_start": 107,
        "ayah_end": 110,
        "theme_hint": "জান্নাতুল ফিরদাউস ও রবের মহিমান্বিত বাক্য (Surah Al-Kahf 107-110)",
        "reflection_bn": "যাঁরা বিশ্বাস স্থাপন করেছে ও সৎকর্ম করেছে, তাঁদের আপ্যায়নের জন্য রয়েছে জান্নাতুল ফিরদাউস। রবের প্রশংসা সাগরের কালিতেও শেষ হবে না।",
        "ideal_reciter": "dossari"
    },
    {
        "surah": 13,
        "ayah_start": 28,
        "ayah_end": 28,
        "theme_hint": "আল্লাহর জিকিরেই কেবল অন্তর প্রশান্ত হয় (Surah Ar-Rad 28)",
        "reflection_bn": "যারা ঈমান এনেছে তাদের অন্তর আল্লাহর স্মরণেই নিশ্চিত প্রশান্তি লাভ করে। জেনে রেখো, আল্লাহর জিকিরেই কেবল মানব হৃদয় শান্ত হয়।",
        "ideal_reciter": "alafasy"
    },
    {
        "surah": 36,
        "ayah_start": 55,
        "ayah_end": 58,
        "theme_hint": "জান্নাতবাসীদের অনাবিল আনন্দ ও রবের সালাম (Surah Ya-Sin 55-58)",
        "reflection_bn": "জান্নাতবাসীরা সেদিন চিরসুখে আনন্দমগ্ন থাকবে এবং পরম দয়ালু রবের পক্ষ থেকে তাদের প্রতি উচ্চারিত হবে শান্তির সম্ভাষণ: সালাম।",
        "ideal_reciter": "alafasy"
    },
    {
        "surah": 30,
        "ayah_start": 21,
        "ayah_end": 21,
        "theme_hint": "দাম্পত্য জীবনের ভালোবাসা ও প্রশান্তি (Surah Ar-Rum 21)",
        "reflection_bn": "আল্লাহর অন্যতম সেরা নিদর্শন যে তিনি আমাদের মধ্য থেকে জীবনসঙ্গী সৃষ্টি করেছেন এবং পরস্পরের মাঝে গভীর ভালোবাসা ও মায়া স্থাপন করেছেন।",
        "ideal_reciter": "alafasy"
    },
    {
        "surah": 2,
        "ayah_start": 186,
        "ayah_end": 186,
        "theme_hint": "আমি তো অতি নিকটে, প্রার্থনাকারীর ডাকে সাড়া দিই (Surah Al-Baqarah 186)",
        "reflection_bn": "বান্দা যখনই আল্লাহকে ডাকে, আল্লাহ তার অতি নিকটে থাকেন এবং আহ্বানকারীর আহ্বানে তাৎক্ষণিক সাড়া দেন।",
        "ideal_reciter": "alafasy"
    },
    {
        "surah": 67,
        "ayah_start": 1,
        "ayah_end": 4,
        "theme_hint": "মহিমান্বিত সার্বভৌমত্ব ও সৃষ্টির নিখুঁত ভারসাম্য (Surah Al-Mulk 1-4)",
        "reflection_bn": "বরকতময় সেই মহান সত্তা যাঁর হাতে নিখিল জাহানের রাজত্ব। পরম করুণাময়ের সৃষ্টিতে তুমি কোনো ত্রুটি দেখতে পাবে না।",
        "ideal_reciter": "dossari"
    },
    {
        "surah": 39,
        "ayah_start": 53,
        "ayah_end": 53,
        "theme_hint": "হতাশা ও পাপের অন্ধকারে আল্লাহর অপার রহমত (Surah Az-Zumar 53)",
        "reflection_bn": "হে আমার বান্দাগণ যারা নিজেদের ওপর অবিচার করেছ, তোমরা আল্লাহর রহমত থেকে কখনো নিরাশ হইও না। নিশ্চয় আল্লাহ সব পাপ ক্ষমা করে দেন।",
        "ideal_reciter": "alafasy"
    },
    # ── ICONIC MELODIOUS PASSAGES (EXCEPTIONALLY SWEET & EAR-PLEASING) ──
    {
        "surah": 19,
        "ayah_start": 1,
        "ayah_end": 7,
        "theme_hint": "জাকারিয়া (আ.)-এর গোপন কান্না ও অসম্ভবকে সম্ভব করার দোয়া (Surah Maryam 1-7)",
        "reflection_bn": "জাকারিয়া (আ.) বার্ধক্যে নিভৃতে কেঁদে রবকে ডেকেছিলেন। আল্লাহ অসম্ভবকেও নিমিষে সম্ভব করে দেন।",
        "ideal_reciter": "alafasy"  # Famous for heartfelt tearful Maqam Saba / Bayati
    },
    {
        "surah": 20,
        "ayah_start": 1,
        "ayah_end": 8,
        "theme_hint": "কুরআন কষ্ট দেওয়ার জন্য নয়, পরম দয়াময়ের স্মরণ (Surah Taha 1-8)",
        "reflection_bn": "কুরআন মানুষকে কষ্ট দেওয়ার জন্য নাজিল হয়নি, বরং অন্তরে শান্তি ও খোদাভীতির জন্য। পরম দয়ালু আল্লাহ আরশে সমুন্নত।",
        "ideal_reciter": "alafasy"  # Flowing, rhythmic, soothing cadence
    },
    {
        "surah": 76,
        "ayah_start": 12,
        "ayah_end": 22,
        "theme_hint": "সবরের মহাপুরস্কার জান্নাতের নয়নাভিরাম সৌন্দর্য (Surah Al-Insan 12-22)",
        "reflection_bn": "ধৈর্যের বিনিময়ে আল্লাহ মুমিনদের জন্য সাজিয়ে রেখেছেন জান্নাতের রেশমি পোশাক, কর্পূরের ঝরনা ও চিরশান্তির নিবাস।",
        "ideal_reciter": "alafasy"  # Incredibly melodious descriptions of Jannah
    },
    {
        "surah": 56,
        "ayah_start": 27,
        "ayah_end": 38,
        "theme_hint": "ডানদিকের সৌভাগ্যবানদের জন্য অফুরন্ত জান্নাতী নেয়ামত (Surah Al-Waqi'ah 27-38)",
        "reflection_bn": "কাঁটাহীন কুলগাছ, কাঁদিভরা কলাগাছ, প্রলম্বিত ছায়া ও প্রবাহমান ঝরনাধারা—সৌভাগ্যবানদের জন্য তৈরি স্বর্গীয় উদ্যান।",
        "ideal_reciter": "dossari"  # Rhythmic, cascading poetic meter
    },
    {
        "surah": 23,
        "ayah_start": 1,
        "ayah_end": 11,
        "theme_hint": "সফল মুমিনদের ৭টি গুণ ও জান্নাতুল ফিরদাউসের উত্তরাধিকার (Surah Al-Mu'minun 1-11)",
        "reflection_bn": "যাঁরা নামাজে বিনয়ী, অর্থহীন কথা থেকে দূরে থাকে এবং আমানত রক্ষা করে—তাঁরাই জান্নাতুল ফিরদাউসের চিরস্থায়ী ওয়ারিশ।",
        "ideal_reciter": "dossari"  # Majestic triumph & eternal reward
    },
    {
        "surah": 53,
        "ayah_start": 1,
        "ayah_end": 18,
        "theme_hint": "নক্ষত্রের শপথ, মিরাজ ও সিদরাতুল মুনতাহা (Surah An-Najm 1-18)",
        "reflection_bn": "নক্ষত্র যখন অস্ত যায়, রাসুল (সা.) আপন খেয়ালে কথা বলেন না। তিনি সিদরাতুল মুনতাহার পাশে রবের শ্রেষ্ঠ নিদর্শন প্রত্যক্ষ করেছিলেন।",
        "ideal_reciter": "dossari"  # Cosmic mystery, short rhyming cadence
    },
    {
        "surah": 87,
        "ayah_start": 1,
        "ayah_end": 15,
        "theme_hint": "সর্বোচ্চ রবের মহিমা ঘোষণা ও আত্মার পবিত্রতা (Surah Al-A'la 1-15)",
        "reflection_bn": "পবিত্রতা ঘোষণা করুন আপনার রবের, যিনি সৃষ্টি করেছেন এবং সুষম করেছেন। সফল সেই ব্যক্তি, যে নিজেকে পাপমুক্ত রাখে।",
        "ideal_reciter": "alafasy"  # Harmonious, gentle, ear-soothing melody
    },
    {
        "surah": 91,
        "ayah_start": 1,
        "ayah_end": 10,
        "theme_hint": "মহাজাগতিক ৭টি শপথ ও অন্তরের পরিশুদ্ধি (Surah Ash-Shams 1-10)",
        "reflection_bn": "সূর্য, চাঁদ, দিন ও রাতের শপথ—যে ব্যক্তি নিজের আত্মাকে পরিশুদ্ধ করেছে সে-ই সফলকাম হয়েছে।",
        "ideal_reciter": "alafasy"  # Poetic rolling -aha end-rhymes
    },
    {
        "surah": 82,
        "ayah_start": 6,
        "ayah_end": 12,
        "theme_hint": "হে মানুষ! কোন জিনিস তোমাকে তোমার দয়ালু রব থেকে দূরে রাখল? (Surah Al-Infitar 6-12)",
        "reflection_bn": "হে মানবজাতি! কোন্ প্রবঞ্চনা তোমাকে তোমার মহানুভব প্রতিপালক সম্পর্কে বিভ্রান্ত করল, যিনি তোমাকে সুঠাম করে সৃষ্টি করেছেন?",
        "ideal_reciter": "dossari"  # Heart-shattering acoustic resonance
    },
    {
        "surah": 57,
        "ayah_start": 16,
        "ayah_end": 16,
        "theme_hint": "মুমিনের হৃদয় কি আল্লাহর স্মরণে বিগলিত হওয়ার সময় আসেনি? (Surah Al-Hadid 16)",
        "reflection_bn": "ঈমানদারদের জন্য কি এখনো সেই সময় আসেনি যে তাদের অন্তর আল্লাহর স্মরণে ও নাজিলকৃত সত্যের সামনে শ্রদ্ধায় বিগলিত হয়ে যাবে?",
        "ideal_reciter": "alafasy"  # Heart-melting emotional awakening
    },
    {
        "surah": 48,
        "ayah_start": 28,
        "ayah_end": 29,
        "theme_hint": "মুহাম্মদ (ﷺ) আল্লাহর রাসুল—তাঁদের চেহারায় সিজদার নূর (Surah Al-Fath 28-29)",
        "reflection_bn": "মুহাম্মদ (ﷺ) আল্লাহর রাসুল। সত্যের সাক্ষ্য হিসেবে আল্লাহই যথেষ্ট। সিজদার প্রভাবে তাঁদের মুখমণ্ডলে রয়েছে বিশেষ জ্যোতি।",
        "ideal_reciter": "dossari"  # Deeply authoritative, uplifting delivery
    },
    {
        "surah": 55,
        "ayah_start": 26,
        "ayah_end": 30,
        "theme_hint": "সবকিছু নশ্বর, কেবল অবশিষ্ট থাকবে মহিমান্বিত রবের সত্ত্বা (Surah Ar-Rahman 26-30)",
        "reflection_bn": "পৃথিবীর সবকিছুই ধ্বংসশীল, কেবল চিরস্থায়ী থাকবে মহিমান্বিত ও পরম দয়ালু রবের চিরভাস্বর সত্ত্বা।",
        "ideal_reciter": "alafasy"  # Iconic soothing cadence
    }
]

def clean_bengali_translation(text: str) -> str:
    """Strips footnote and HTML markers, normalizes Unicode NFC, while preserving concise commentary."""
    if not text:
        return ""
    # Normalize unicode to NFC (fixes split vowels e.g. U+09C7 + U+09BE -> U+09CB 'ো')
    text = unicodedata.normalize('NFC', text)
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Strip footnote explanations starting with asterisk (e.g. *অর্থ কুরবানী কর)
    text = re.sub(r'\*[^\*।]*।?', '', text)
    # Strip footnote numbers like [১], [২], [1], [2]
    text = re.sub(r'\[[০-৯0-9\s]+\]', '', text)
    # Strip excessively long commentary in parentheses (> 40 chars)
    text = re.sub(r'\([^\)]{40,}\)', '', text)
    # Normalize archaic word-final hasantas (e.g. 'কোন্' -> 'কোন')
    text = re.sub(r'\u09cd(?=[\s\.,;!?।\)]|$)', '', text)
    # Normalize spaces before punctuation
    text = re.sub(r'\s+([,;!?।])', r'\1', text)
    # Normalize spaces and trailing punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_html_tags(text: str) -> str:
    """Backward compatibility wrapper."""
    return clean_bengali_translation(text)

def clean_english_translation(text: str) -> str:
    """Strips HTML tags, footnote indices, and modernizes archaic Victorian vocabulary (e.g. breast -> chest)."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[[0-9]+\]', '', text)
    # Strip footnote numbers attached to trailing punctuation or words (e.g. 'off.1' -> 'off.')
    text = re.sub(r'(?<=[a-zA-Z\.?!,;])\d+', '', text)
    # Modernize awkward archaic anatomical translations
    text = re.sub(r'\bbreast\b', 'chest', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbreasts\b', 'chests', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_verse_data(surah: int, ayah_start: int, ayah_end: int = None) -> dict:
    """
    Fetches Arabic text with Tashkeel, authentic Islamic Foundation Bengali translation,
    and English translation for the verse range.
    """
    if ayah_end is None or ayah_end < ayah_start:
        ayah_end = ayah_start

    surah_name_bn = SURAH_NAMES_BN.get(surah, f"সূরা নম্বর {surah}")
    surah_name_en = SURAH_NAMES_EN.get(surah, f"Surah {surah}")
    logger.info(f"Fetching {surah_name_bn} / {surah_name_en} (Ayah {ayah_start}-{ayah_end}) using Islamic Foundation Bangladesh translation...")

    verses_list = []
    full_arabic = []
    full_bengali = []
    full_english = []

    if_db = get_islamic_foundation_db()

    for ayah in range(ayah_start, ayah_end + 1):
        key = f"{surah}:{ayah}"
        bn_text = ""
        ar_text = ""
        en_text = ""

        # 1. Primary: Islamic Foundation Bangladesh (Local Vetted Dataset)
        if key in if_db and if_db[key]:
            bn_text = clean_bengali_translation(if_db[key])

        # 2. Secondary: If not in local dataset, fetch Islamic Foundation / Tanzil from AlQuran Cloud
        if not bn_text:
            url_if = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/bn.bengali"
            try:
                req_if = urllib.request.Request(url_if, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req_if, timeout=6) as resp:
                    data_if = json.loads(resp.read().decode("utf-8"))
                    cand_if = data_if.get("data", {}).get("text", "")
                    if cand_if:
                        bn_text = clean_bengali_translation(cand_if)
            except Exception as e:
                logger.debug(f"AlQuran Cloud fetch notice for {key}: {e}")

        # 3. Always fetch Arabic Uthmani text from Quran.com (and fallback Bengali if still empty)
        # Fallback order for Quran.com: 161 (Taisirul), 163 (Mujibur Rahman), 162 (Rawai), 213 (Zakaria)
        for trans_id in [161, 163, 162, 213]:
            url = f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}?language=bn&translations={trans_id}&fields=text_uthmani"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    v = data.get("verse", {})
                    if not ar_text:
                        ar_text = v.get("text_uthmani", "").strip()
                    if not bn_text:
                        trans = v.get("translations", [])
                        if trans and trans[0].get("text"):
                            candidate_bn = clean_bengali_translation(trans[0].get("text", ""))
                            if candidate_bn:
                                bn_text = candidate_bn
                    if ar_text and bn_text:
                        break
            except Exception as e:
                logger.warning(f"Translation {trans_id} fetch notice for {surah}:{ayah}: {e}")
                continue

        # Fetch English translation (Resource 85: M.A.S. Abdel Haleem Oxford / Resource 20: Saheeh International)
        for en_trans_id in [85, 20]:
            url_en = f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}?translations={en_trans_id}"
            try:
                req_en = urllib.request.Request(url_en, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req_en, timeout=8) as resp:
                    data_en = json.loads(resp.read().decode("utf-8"))
                    v_en = data_en.get("verse", {})
                    trans_en = v_en.get("translations", [])
                    if trans_en and trans_en[0].get("text"):
                        candidate_en = clean_english_translation(trans_en[0].get("text", ""))
                        if candidate_en:
                            en_text = candidate_en
                            break
            except Exception as e:
                logger.warning(f"English translation {en_trans_id} fetch notice for {surah}:{ayah}: {e}")
                continue

        if not ar_text:
            raise RuntimeError(f"Could not retrieve Arabic text for {surah}:{ayah} from Quran.com API")

        verses_list.append({
            "ayah_number": ayah,
            "arabic": ar_text,
            "bengali": bn_text,
            "english": en_text
        })
        full_arabic.append(ar_text)
        full_bengali.append(bn_text)
        if en_text:
            full_english.append(en_text)

    verse_range_str = f"{ayah_start}" if ayah_start == ayah_end else f"{ayah_start}-{ayah_end}"

    return {
        "surah": surah,
        "ayah_start": ayah_start,
        "ayah_end": ayah_end,
        "verse_range_str": verse_range_str,
        "surah_name_bn": surah_name_bn,
        "surah_name_en": surah_name_en,
        "verses": verses_list,
        "combined_arabic": " • ".join(full_arabic),
        "combined_bengali": " ".join(full_bengali),
        "combined_english": " ".join(full_english)
    }

def determine_best_reciter_for_passage(surah: int, ayah_start: int, ayah_end: int = None) -> str:
    """
    Intelligently assigns the best matching reciter (Alafasy vs. Dossari)
    based on the theological theme and emotional frequency of the Surah / Ayah range:
    - 'alafasy': Soothing, warm, melodic baritone -> Ideal for solace, hope, mercy, repentance, Dua, Jannah.
    - 'dossari': Dramatic, thunderous, high dynamic range -> Ideal for divine power, majesty, Qiyamah, firm decree.
    """
    end = ayah_end or ayah_start

    # 1. Check curated passages
    for p in CURATED_COMPLETE_PASSAGES:
        if p["surah"] == surah and p["ayah_start"] == ayah_start:
            return p.get("ideal_reciter", "alafasy")

    # 2. Check landmark Ayahs with strong theological identity
    if surah == 2 and (ayah_start <= 255 <= end):
        # Ayatul Kursi -> Supreme sovereignty and majestic throne
        return "dossari"
    elif surah == 2 and (ayah_start >= 285):
        # Amanar Rasul -> Mercy, forgiveness and soul peace
        return "alafasy"
    elif surah == 3 and (173 <= ayah_start <= 174):
        # Hasbunallahu wa ni'mal wakil -> Courage & steadfast resolve
        return "dossari"
    elif surah == 21 and (87 <= ayah_start <= 88):
        # Yunus (AS) Dua -> Repentance, tears and relief
        return "alafasy"
    elif surah == 28 and ayah_start == 24:
        # Musa (AS) Dua -> Helplessness and intimate prayer
        return "alafasy"
    elif surah == 59 and ayah_start >= 22:
        # Al-Hashr Ism-e-Azam -> Grandeur of divine attributes
        return "dossari"
    elif surah == 65 and (2 <= ayah_start <= 3):
        # At-Talaq -> Unfathomable provision & absolute Tawakkul
        return "dossari"

    # 3. Thematic Surah mapping
    # Alafasy territory: Softening sorrow, comfort, prayer, family, Jannah
    alafasy_surahs = {94, 93, 55, 12, 14, 19, 20, 25, 36, 76, 89, 90, 91, 92, 95, 108, 110, 112, 113, 114}
    # Dossari territory: Majesty, sovereignty, Day of Judgment, warnings, battle
    dossari_surahs = {50, 65, 67, 69, 75, 77, 78, 79, 81, 82, 85, 100, 101, 104}

    if surah in alafasy_surahs:
        return "alafasy"
    elif surah in dossari_surahs:
        return "dossari"
    else:
        # Guaranteed safe default
        return "alafasy"

def select_meaningful_passage_ai(
    reciter_id: str = None,
    recent_history: list = None,
    used_ayahs_map: dict = None,
    rejected_passages: list = None,
    last_fail_reason: str = "",
    use_curated_fallback: bool = False
) -> dict:
    """
    Uses Gemini to intelligently select a complete, self-contained passage from the Quran
    that has 100% complete meaning, zero missing context, and can finish recitation within 85 seconds.
    Intelligently assigns the most appealing reciter (Alafasy vs. Dossari) based on the passage's emotion.
    Enforces strict zero-duplication: already-used Ayahs within the last 30 videos are strictly forbidden.
    (Note: Different Ayahs of the same Surah ARE allowed, but duplicate Ayahs are forbidden).
    """
    used_ayahs_map = used_ayahs_map or {}
    avoid_list = "\n- ".join(recent_history[:30]) if recent_history else "None"

    # Build clear already-used Ayahs text per Surah
    used_items = []
    for s_num in sorted(used_ayahs_map.keys()):
        bn_name = SURAH_NAMES_BN.get(s_num, "")
        en_name = SURAH_NAMES_EN.get(s_num, "")
        ayah_list = sorted(list(used_ayahs_map[s_num]))
        if len(ayah_list) == 1:
            ayah_desc = f"Ayah {ayah_list[0]}"
        elif len(ayah_list) == (ayah_list[-1] - ayah_list[0] + 1):
            ayah_desc = f"Ayahs {ayah_list[0]}-{ayah_list[-1]}"
        else:
            ayah_desc = f"Ayahs {', '.join(str(a) for a in ayah_list)}"
        used_items.append(f"- Surah {s_num}: {en_name} ({bn_name}) -> ALREADY RECITED: {ayah_desc}")
    used_ayahs_section = "\n".join(used_items) if used_items else "None"

    if not use_curated_fallback:
        system_prompt = f"""You are a senior Quran scholar, master audio director, and video producer.
Your goal is to select a complete, self-contained Quranic passage (under 90 seconds recitation length) that provides a deeply moving, complete message to the viewer, and assign the IDEAL vocal reciter for maximum emotional appeal.

CRITICAL PASSAGE RULES (MANDATORY):
1. ZERO DUPLICATION OF ALREADY RECITED AYAHS:
   - The following specific Ayahs were ALREADY RECITED in the last 30 videos:
{used_ayahs_section}
   - STRICTLY DO NOT select any passage containing or overlapping with any of the already-recited Ayahs listed above!
   - You MAY select from any Surah of the Holy Quran (including other unrecited verses of these same Surahs, or any other Surah), but there must be ZERO OVERLAP with the already-used Ayahs.
2. COMPLETE MEANING & ZERO CUT-OFFS: The passage MUST form a complete, self-contained unit of thought. Never cut off in the middle of a sentence, list, or argument!
3. DURATION LIMIT: Total recitation length of the verse(s) MUST be between 25 and 85 seconds (typically 1 to 8 ayahs depending on verse length).
4. THEMATIC VOICE MATCHING (CHOOSE BETWEEN ALAFASY OR DOSSARI):
   - 'alafasy' (Sheikh Mishary Rashid Alafasy): Choose for comfort, relief from grief, hope, mercy, divine forgiveness, sincere supplication (Dua), family love, gentle reflection, and peace of Paradise. (His warm, melodic, soothing baritone provides deep emotional healing).
   - 'dossari' (Sheikh Yasser Ad-Dossari): Choose for divine power, supreme sovereignty, majesty, Day of Judgment (Qiyamah), warnings against arrogance, absolute Tawakkul in trials, and cosmic oaths. (His thunderous, high-dynamic, commanding delivery creates awe and reverence).
5. EAR-PLEASING AUDITORY MELODY & PHONETIC SWEETNESS (MANDATORY):
   - The selected Ayah(s) MUST sound exceptionally sweet, soothing, rhythmic, and captivating to human ears when recited aloud.
   - PRIORITIZE:
     a) Rhythmic rhyming end-cadences (Fawāṣil al-Āyāt) with flowing open vowels (e.g. -ūn, -īn, -ā, -hā).
     b) Passages celebrated for profound emotional auditory bliss: Jannah descriptions, divine affection, cosmic oaths, heartfelt prophet Duas (Zakariya, Musa, Ibrahim, Yunus), dawn/night serenity, and heart-melting reassurance.
     c) Verses where Sheikh Mishary Alafasy or Sheikh Yasser Ad-Dossari deliver their most famous, tearful, or awe-inspiring vocal melodies (e.g. Surah Maryam, Surah Taha, Surah Al-Insan, Surah Al-Waqi'ah, Surah Ar-Rahman, Surah Al-Fajr, Surah Ad-Duha, Surah Qaf, Surah Al-Hadid).
   - STRICTLY AVOID: Dry administrative, legalistic, commercial transactions, inheritance shares, or procedural verses that lack lyrical phonetic flow when listened to as audio. Every video must deliver an unforgettable, heart-soothing acoustic experience.

Output ONLY valid JSON:
{{
    "surah": 94,
    "ayah_start": 1,
    "ayah_end": 8,
    "theme_headline": "কঠিন সময়ে মন শান্ত করার পরম সান্ত্বনা",
    "reflection_bn": "আল্লাহ তায়ালা এই সূরায় জানিয়ে দিয়েছেন যে কষ্টের পরই স্বস্তি আসে। ধৈর্য ধারণ করলে আল্লাহ নিজে সব জটিলতা সহজ করে দেন।",
    "recommended_reciter": "alafasy",
    "reciter_rationale": "Surah Ash-Sharh is a gentle message of divine solace; Alafasy's warm, comforting baritone maximizes emotional appeal."
}}"""

        reciter_hint = f"Pre-selected reciter: {reciter_id}" if reciter_id else "Select the best matching reciter ('alafasy' or 'dossari') based on the theological emotion."

        rejection_warning = ""
        if rejected_passages:
            rejection_warning = (
                f"\n\n[CRITICAL CORRECTION FROM PREVIOUS ATTEMPT]:\n"
                f"The following passages were ALREADY REJECTED and MUST NOT be selected: {', '.join(rejected_passages)}.\n"
                f"Reason: {last_fail_reason}\n"
                f"You MUST select a COMPLETELY DIFFERENT Surah or passage!"
            )

        user_prompt = f"""Select a complete self-contained Quran passage under 90s recitation that sounds exceptionally melodious and soothing to the ears.
{reciter_hint}

ALREADY RECITED AYAHS IN LAST 30 VIDEOS (STRICTLY FORBIDDEN TO REPEAT THESE AYAHS):
{used_ayahs_section}

RECENT TITLES IN HISTORY:
- {avoid_list}{rejection_warning}

Select a fresh, inspiring, and ear-pleasing melodious passage with 100% complete contextual integrity. Ensure ZERO OVERLAP with the already recited Ayahs above. Return valid JSON only."""

        try:
            data = extract_json(system_prompt, user_prompt, max_tokens=600)
            if isinstance(data, dict) and data.get("surah") and data.get("ayah_start"):
                surah = int(data["surah"])
                start = int(data["ayah_start"])
                end = int(data.get("ayah_end") or start)
                
                # Check for Ayah-level overlap
                cand_ayahs = set(range(start, end + 1))
                banned_ayahs = used_ayahs_map.get(surah, set())
                overlap = cand_ayahs & banned_ayahs
                if overlap:
                    raise ValueError(
                        f"AI selected Surah {surah}:{start}-{end} which overlaps with already used Ayahs {sorted(list(overlap))}"
                    )

                # Determine winning reciter
                chosen_reciter_id = reciter_id
                if not chosen_reciter_id:
                    rec_candidate = str(data.get("recommended_reciter") or data.get("reciter_id") or "").lower().strip()
                    if rec_candidate in RECITERS_CONFIG:
                        chosen_reciter_id = rec_candidate
                    else:
                        chosen_reciter_id = determine_best_reciter_for_passage(surah, start, end)

                reciter = RECITERS_CONFIG.get(chosen_reciter_id, RECITERS_CONFIG["alafasy"])
                logger.info(f"🎙️ [Voice-Theme Matcher] Assigned {reciter['name_en']} ({chosen_reciter_id}) for Surah {surah}:{start}-{end}. Rationale: {data.get('reciter_rationale', 'Thematic resonance')}")

                # Fetch data from API
                verse_data = fetch_verse_data(surah, start, end)
                verse_data["theme_headline"] = data.get("theme_headline", "কোরআনের আলো ও হেদায়াত")
                verse_data["reflection_bn"] = data.get("reflection_bn", "")
                verse_data["reciter_id"] = chosen_reciter_id
                verse_data["reciter"] = reciter
                verse_data["reciter_rationale"] = data.get("reciter_rationale", "")
                return verse_data
        except Exception as e:
            logger.warning(f"AI passage selection notice: {e}. Falling back to curated bank.")

    # Fallback to curated rotation - STRICTLY EXCLUDE PASSAGES OVERLAPPING ALREADY USED OR REJECTED AYAHS
    import random
    available_curated = []
    for p in CURATED_COMPLETE_PASSAGES:
        p_surah = p["surah"]
        p_ayahs = set(range(p["ayah_start"], p["ayah_end"] + 1))
        banned_ayahs = used_ayahs_map.get(p_surah, set())
        if not (p_ayahs & banned_ayahs):
            pass_str = f"Surah {p_surah}:{p['ayah_start']}-{p['ayah_end']}"
            if rejected_passages and any(pass_str in r or f"Surah {p_surah}:" in r for r in rejected_passages):
                continue
            available_curated.append(p)

    if not available_curated:
        logger.warning("All curated passages overlapped with recent history! Using complete curated bank as emergency fallback.")
        available_curated = CURATED_COMPLETE_PASSAGES

    choice = random.choice(available_curated)
    chosen_reciter_id = reciter_id or choice.get("ideal_reciter", "alafasy")
    reciter = RECITERS_CONFIG.get(chosen_reciter_id, RECITERS_CONFIG["alafasy"])

    verse_data = fetch_verse_data(choice["surah"], choice["ayah_start"], choice["ayah_end"])
    verse_data["theme_headline"] = choice["theme_hint"]
    verse_data["reflection_bn"] = choice["reflection_bn"]
    verse_data["reciter_id"] = chosen_reciter_id
    verse_data["reciter"] = reciter
    verse_data["reciter_rationale"] = f"Curated optimal match for {verse_data['surah_name_en']}"
    return verse_data

