# -*- coding: utf-8 -*-
"""
Quran Data Fetcher & AI Contextual Passage Selector.
Fetches authentic Uthmani Arabic text and verified Bengali translations from Quran.com API v4,
and provides Gemini-powered complete self-contained passage selection.
"""

import urllib.request
import urllib.parse
import json
import re
from app.logger import logger
from app.llm.provider import extract_json

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
    }
]

def clean_bengali_translation(text: str) -> str:
    """Strips footnote and HTML markers and cleans excessive parenthetical commentary from translations."""
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Strip footnote explanations starting with asterisk (e.g. *অর্থ কুরবানী কর)
    text = re.sub(r'\*[^\*।]*।?', '', text)
    # Strip footnote numbers like [১], [২], [1], [2]
    text = re.sub(r'\[[০-৯0-9]+\]', '', text)
    # Strip excessively long commentary in parentheses (tafsir explanations inserted by translators)
    text = re.sub(r'\([^\)]{12,}\)', '', text)
    # Remove remaining standalone parentheses while retaining the text inside
    text = re.sub(r'[\(\)]', '', text)
    # Normalize spaces and trailing punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_html_tags(text: str) -> str:
    """Backward compatibility wrapper."""
    return clean_bengali_translation(text)

def clean_english_translation(text: str) -> str:
    """Strips HTML tags, footnote indices, and normalizes spaces for English translations."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[[0-9]+\]', '', text)
    # Strip footnote numbers attached to trailing punctuation or words (e.g. 'off.1' -> 'off.')
    text = re.sub(r'(?<=[a-zA-Z\.?!,;])\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_verse_data(surah: int, ayah_start: int, ayah_end: int = None) -> dict:
    """
    Fetches Arabic text with Tashkeel, authentic Bengali translation, and English translation (Saheeh International)
    for the verse range directly from api.quran.com/api/v4/.
    """
    if ayah_end is None or ayah_end < ayah_start:
        ayah_end = ayah_start

    surah_name_bn = SURAH_NAMES_BN.get(surah, f"সূরা নম্বর {surah}")
    surah_name_en = SURAH_NAMES_EN.get(surah, f"Surah {surah}")
    logger.info(f"Fetching {surah_name_bn} / {surah_name_en} (Ayah {ayah_start}-{ayah_end}) from Quran.com API...")

    verses_list = []
    full_arabic = []
    full_bengali = []
    full_english = []

    for ayah in range(ayah_start, ayah_end + 1):
        # Prioritize 162 (Rawai Al-bayan) for pure verse translation, fallback to 163 and 161
        bn_text = ""
        ar_text = ""
        en_text = ""

        for trans_id in [162, 163, 161]:
            url = f"https://api.quran.com/api/v4/verses/by_key/{surah}:{ayah}?language=bn&translations={trans_id}&fields=text_uthmani"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    v = data.get("verse", {})
                    ar_text = v.get("text_uthmani", "").strip()
                    trans = v.get("translations", [])
                    if trans and trans[0].get("text"):
                        candidate_bn = clean_bengali_translation(trans[0].get("text", ""))
                        if candidate_bn:
                            bn_text = candidate_bn
                            break
            except Exception as e:
                logger.warning(f"Translation {trans_id} fetch notice for {surah}:{ayah}: {e}")
                continue

        # Fetch English translation (Resource 20: Saheeh International, fallback 85: Abdel Haleem)
        for en_trans_id in [20, 85]:
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
    # 1. Check curated passages
    for p in CURATED_COMPLETE_PASSAGES:
        if p["surah"] == surah and p["ayah_start"] == ayah_start:
            return p.get("ideal_reciter", "alafasy")

    # 2. Known emotional mapping
    # Alafasy territory: Softening sorrow, comfort, prayer, family, Jannah
    alafasy_surahs = {94, 93, 55, 12, 19, 76, 89, 90, 91, 92, 108, 110, 113, 114}
    # Dossari territory: Majesty, sovereignty, Day of Judgment, warnings, battle
    dossari_surahs = {65, 67, 69, 75, 77, 78, 79, 81, 82, 85, 101, 104, 50, 59}

    if surah in alafasy_surahs:
        return "alafasy"
    if surah in dossari_surahs:
        return "dossari"

    # Default balance
    return "alafasy"

def select_meaningful_passage_ai(reciter_id: str = None, recent_history: list = None) -> dict:
    """
    Uses Gemini to intelligently select a complete, self-contained passage from the Quran
    that has 100% complete meaning, zero missing context, and can finish recitation within 85 seconds.
    Intelligently assigns the most appealing reciter (Alafasy vs. Dossari) based on the passage's emotion.
    """
    avoid_list = "\n- ".join(recent_history[:30]) if recent_history else "None"

    system_prompt = """You are a senior Quran scholar, master audio director, and video producer.
Your goal is to select a complete, self-contained Quranic passage (under 90 seconds recitation length) that provides a deeply moving, complete message to the viewer, and assign the IDEAL vocal reciter for maximum emotional appeal.

CRITICAL PASSAGE RULES (MANDATORY):
1. ZERO SIMILAR CONTENT (STRICT ANTI-DUPLICATION): Strictly DO NOT select any Surah, Ayah range, or theme that appears in the last 30 videos listed below. It MUST be a completely fresh, distinct passage.
2. COMPLETE MEANING & ZERO CUT-OFFS: The passage MUST form a complete, self-contained unit of thought. Never cut off in the middle of a sentence, list, or argument!
3. DURATION LIMIT: Total recitation length of the verse(s) MUST be between 25 and 85 seconds (typically 1 to 8 ayahs depending on verse length).
4. THEMATIC VOICE MATCHING (CHOOSE BETWEEN ALAFASY OR DOSSARI):
   - 'alafasy' (Sheikh Mishary Rashid Alafasy): Choose for comfort, relief from grief, hope, mercy, divine forgiveness, sincere supplication (Dua), family love, gentle reflection, and peace of Paradise. (His warm, melodic, soothing baritone provides deep emotional healing).
   - 'dossari' (Sheikh Yasser Ad-Dossari): Choose for divine power, supreme sovereignty, majesty, Day of Judgment (Qiyamah), warnings against arrogance, absolute Tawakkul in trials, and cosmic oaths. (His thunderous, high-dynamic, commanding delivery creates awe and reverence).

Output ONLY valid JSON:
{
    "surah": 94,
    "ayah_start": 1,
    "ayah_end": 8,
    "theme_headline": "কঠিন সময়ে মন শান্ত করার পরম সান্ত্বনা",
    "reflection_bn": "আল্লাহ তায়ালা এই সূরায় জানিয়ে দিয়েছেন যে কষ্টের পরই স্বস্তি আসে। ধৈর্য ধারণ করলে আল্লাহ নিজে সব জটিলতা সহজ করে দেন।",
    "recommended_reciter": "alafasy",
    "reciter_rationale": "Surah Ash-Sharh is a gentle message of divine solace; Alafasy's warm, comforting baritone maximizes emotional appeal."
}"""

    reciter_hint = f"Pre-selected reciter: {reciter_id}" if reciter_id else "Select the best matching reciter ('alafasy' or 'dossari') based on the theological emotion."

    user_prompt = f"""Select a complete self-contained Quran passage under 90s recitation.
{reciter_hint}

MANDATORY AVOID LIST (Last 30 Videos - DO NOT REPEAT ANY OF THESE):
- {avoid_list}

Select a fresh, unique, inspiring passage not found in the list above with 100% complete contextual integrity and assign the winning reciter. Return valid JSON only."""

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=600)
        if isinstance(data, dict) and data.get("surah") and data.get("ayah_start"):
            surah = int(data["surah"])
            start = int(data["ayah_start"])
            end = int(data.get("ayah_end") or start)
            
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

    # Fallback to curated rotation
    import random
    choice = random.choice(CURATED_COMPLETE_PASSAGES)
    chosen_reciter_id = reciter_id or choice.get("ideal_reciter", "alafasy")
    reciter = RECITERS_CONFIG.get(chosen_reciter_id, RECITERS_CONFIG["alafasy"])

    verse_data = fetch_verse_data(choice["surah"], choice["ayah_start"], choice["ayah_end"])
    verse_data["theme_headline"] = choice["theme_hint"]
    verse_data["reflection_bn"] = choice["reflection_bn"]
    verse_data["reciter_id"] = chosen_reciter_id
    verse_data["reciter"] = reciter
    verse_data["reciter_rationale"] = f"Curated optimal match for {verse_data['surah_name_en']}"
    return verse_data

