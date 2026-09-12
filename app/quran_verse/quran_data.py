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

# Curated bank of guaranteed complete self-contained passages under 90s (Fallback & Rotation)
CURATED_COMPLETE_PASSAGES = [
    {
        "surah": 94,
        "ayah_start": 1,
        "ayah_end": 8,
        "theme_hint": "কষ্টের পরেই স্বস্তির মহাপ্রতিশ্রুতি (Surah Ash-Sharh Complete)",
        "reflection_bn": "আল্লাহ তায়ালা মুমিনকে সান্ত্বনা দিয়ে নিশ্চিত করেছেন যে, প্রতিটি সংকটের সাথেই আল্লাহ মুক্তির পথ ও প্রশান্তি নির্ধারণ করে রেখেছেন।"
    },
    {
        "surah": 93,
        "ayah_start": 1,
        "ayah_end": 11,
        "theme_hint": "হতাশা দূরীকরণ ও আল্লাহর গভীর অনুগ্রহ (Surah Ad-Duha Complete)",
        "reflection_bn": "আল্লাহ কখনো তাঁর বান্দাকে ত্যাগ করেন না। অন্ধকার রাতের পর যেমন সোনালী সকাল আসে, তেমনি জীবনের কঠিন সময়ও কেটে যায়।"
    },
    {
        "surah": 65,
        "ayah_start": 3,
        "ayah_end": 3,
        "theme_hint": "তাকওয়া, অভাবনীয় রিজিক ও তাওয়াক্কুল (Surah At-Talaq 3)",
        "reflection_bn": "যে ব্যক্তি আল্লাহর ওপর তাওয়াক্কুল করে, আল্লাহ তাঁর জন্য এমন উৎস থেকে রিজিক দেন যা মানুষ কল্পনাও করতে পারে না এবং তার জন্য আল্লাহই যথেষ্ট।"
    },
    {
        "surah": 3,
        "ayah_start": 173,
        "ayah_end": 174,
        "theme_hint": "হাসবুনাল্লাহু ওয়া নি'মাল ওয়াকিল ও নিরাপত্তা (Surah Al-Imran 173-174)",
        "reflection_bn": "বিপদে আল্লাহর ওপর পূর্ণ আস্থা রাখলে মহান আল্লাহ বান্দাকে অপূরণীয় বরকত ও নিরাপত্তা দান করেন।"
    },
    {
        "surah": 21,
        "ayah_start": 87,
        "ayah_end": 88,
        "theme_hint": "ইউনুস (আ.)-এর দোয়া ও সর্বসংকট মুক্তি (Surah Al-Anbiya 87-88)",
        "reflection_bn": "মাছের পেটের মতো ঘোর অন্ধকারেও যখন নবী ইউনুস (আ.) খাঁটি তওবা করে ডাক দিয়েছিলেন, আল্লাহ সেই অসম্ভব সংকট থেকেও তাঁকে উদ্ধার করেছিলেন।"
    },
    {
        "surah": 2,
        "ayah_start": 255,
        "ayah_end": 255,
        "theme_hint": "আয়াতুল কুরসী—আল্লাহর সার্বভৌমত্ব ও পরাক্রম (Surah Al-Baqarah 255)",
        "reflection_bn": "পবিত্র কুরআনের সর্বশ্রেষ্ঠ এই আয়াতে আল্লাহর মহত্ত্ব, জীবন্ত সত্তা এবং নিখিল বিশ্বের ওপর তাঁর পূর্ণ কর্তৃত্বের প্রকাশ ঘটেছে।"
    },
    {
        "surah": 59,
        "ayah_start": 22,
        "ayah_end": 24,
        "theme_hint": "আল্লাহর গুণবাচক শ্রেষ্ঠ নামসমূহ—ইসমে আজম (Surah Al-Hashr 22-24)",
        "reflection_bn": "আল্লাহর পবিত্র গুণবাচক নামগুলোর জিকির হৃদয়ে গভীর ভয় ও শ্রদ্ধা জাগিয়ে তোলে।"
    },
    {
        "surah": 2,
        "ayah_start": 285,
        "ayah_end": 286,
        "theme_hint": "আমানার রাসূলু—ক্ষমা, রহমত ও শক্তি চাওয়ার সেরা দোয়া (Surah Al-Baqarah 285-286)",
        "reflection_bn": "আল্লাহ কোনো আত্মাকে তার সাধ্যের অতিরিক্ত দায়িত্ব চাপান না। এই আয়াতদ্বয় রাতের বেলা পাঠ করলে সব অনিষ্ট থেকে সুরক্ষার জন্য যথেষ্ট।"
    },
    {
        "surah": 28,
        "ayah_start": 24,
        "ayah_end": 24,
        "theme_hint": "মুসা (আ.)-এর অভাব দূর ও সাহায্যের দোয়া (Surah Al-Qasas 24)",
        "reflection_bn": "মুসা (আ.) যখন একাকী, ক্ষুধার্ত ও সহায়হীন অবস্থায় গাছের ছায়ায় বসে কাতর কণ্ঠে এই দোয়া করেছিলেন, আল্লাহ তাৎক্ষণিক তাঁর খাদ্য, নিরাপত্তা ও পরিবারের ব্যবস্থা করে দিয়েছিলেন।"
    },
    {
        "surah": 25,
        "ayah_start": 74,
        "ayah_end": 74,
        "theme_hint": "নেককার সন্তান ও সুখী দাম্পত্যের সেরা দোয়া (Surah Al-Furqan 74)",
        "reflection_bn": "পারিবারিক শান্তি ও চোখ জুড়ানো নেককার সন্তানের জন্য রহমানুর রাহীমের কাছে প্রার্থনার এক অনন্য শিক্ষা।"
    },
    {
        "surah": 89,
        "ayah_start": 27,
        "ayah_end": 30,
        "theme_hint": "প্রশান্ত আত্মার জন্য জান্নাতের ডাক (Surah Al-Fajr 27-30)",
        "reflection_bn": "যে আত্মা আল্লাহর ওপর সন্তুষ্ট থাকে, মৃত্যুর সময় আল্লাহ নিজে তাকে পরম সমাদরে জান্নাতে ডেকে নেন।"
    }
]

def clean_bengali_translation(text: str) -> str:
    """Strips footnote and HTML markers and cleans excessive parenthetical commentary from translations."""
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Strip footnote numbers like [১], [২], [1], [2]
    text = re.sub(r'\[[০-৯0-9]+\]', '', text)
    # Strip excessively long commentary in parentheses (tafsir explanations inserted by translators)
    text = re.sub(r'\([^\)]{12,}\)', '', text)
    # Remove remaining standalone parentheses while retaining the text inside
    text = re.sub(r'[\(\)]', '', text)
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_html_tags(text: str) -> str:
    """Backward compatibility wrapper."""
    return clean_bengali_translation(text)

def fetch_verse_data(surah: int, ayah_start: int, ayah_end: int = None) -> dict:
    """
    Fetches Arabic text with Tashkeel and authentic Bengali translation for the verse range
    directly from api.quran.com/api/v4/.
    Prioritizes Rawai Al-bayan (162) and Sheikh Mujibur Rahman (163) for direct, concise phrasing.
    """
    if ayah_end is None or ayah_end < ayah_start:
        ayah_end = ayah_start

    surah_name_bn = SURAH_NAMES_BN.get(surah, f"সূরা নম্বর {surah}")
    logger.info(f"Fetching {surah_name_bn} (Ayah {ayah_start}-{ayah_end}) from Quran.com API...")

    verses_list = []
    full_arabic = []
    full_bengali = []

    for ayah in range(ayah_start, ayah_end + 1):
        # Prioritize 162 (Rawai Al-bayan) for pure verse translation, fallback to 163 and 161
        bn_text = ""
        ar_text = ""

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

        if not ar_text:
            raise RuntimeError(f"Could not retrieve Arabic text for {surah}:{ayah} from Quran.com API")

        verses_list.append({
            "ayah_number": ayah,
            "arabic": ar_text,
            "bengali": bn_text
        })
        full_arabic.append(ar_text)
        full_bengali.append(bn_text)

    verse_range_str = f"{ayah_start}" if ayah_start == ayah_end else f"{ayah_start}-{ayah_end}"

    return {
        "surah": surah,
        "ayah_start": ayah_start,
        "ayah_end": ayah_end,
        "verse_range_str": verse_range_str,
        "surah_name_bn": surah_name_bn,
        "verses": verses_list,
        "combined_arabic": " • ".join(full_arabic),
        "combined_bengali": " ".join(full_bengali)
    }

def select_meaningful_passage_ai(reciter_id: str = "alafasy", recent_history: list = None) -> dict:
    """
    Uses Gemini to intelligently select a complete, self-contained passage from the Quran
    that has 100% complete meaning, zero missing context, and can finish recitation within 85 seconds.
    Falls back gracefully to curated passages.
    """
    avoid_list = "\n- ".join(recent_history[:15]) if recent_history else "None"
    reciter = RECITERS_CONFIG.get(reciter_id, RECITERS_CONFIG["alafasy"])

    system_prompt = """You are a senior Quran scholar and video producer.
Your goal is to select a complete, self-contained Quranic passage (under 90 seconds recitation length) that provides a deeply moving, complete message to the viewer.

CRITICAL PASSAGE RULES (MANDATORY):
1. COMPLETE MEANING & ZERO CUT-OFFS: The passage MUST form a complete, self-contained unit of thought. Never cut off in the middle of a sentence, list, or argument!
2. DURATION LIMIT: Total recitation length of the verse(s) MUST be between 25 and 85 seconds (typically 1 to 8 ayahs depending on verse length).
3. EXAMPLES OF COMPLETE UNITS:
   - A complete short Surah (e.g. Surah Ash-Sharh 94:1-8, Surah Ad-Duha 93:1-11, Surah Al-Fajr 89:27-30, Surah Al-Ikhlas 112:1-4).
   - A complete Quranic Dua (e.g. Surah Al-Anbiya 21:87-88 Yunus, Surah Taha 20:25-28 Musa, Surah Al-Furqan 25:74, Surah Al-Qasas 28:24).
   - A complete divine promise or law (e.g. Surah At-Talaq 65:2-3, Surah Al-Imran 3:173-174, Surah Al-Baqarah 2:285-286, Surah Al-Hashr 59:22-24).

Output ONLY valid JSON:
{
    "surah": 94,
    "ayah_start": 1,
    "ayah_end": 8,
    "theme_headline": "কঠিন সময়ে মন শান্ত করার পরম সান্ত্বনা",
    "reflection_bn": "আল্লাহ তায়ালা এই সূরায় জানিয়ে দিয়েছেন যে কষ্টের পরই স্বস্তি আসে। ধৈর্য ধারণ করলে আল্লাহ নিজে সব জটিলতা সহজ করে দেন।"
}"""

    user_prompt = f"""Select a complete self-contained Quran passage under 90s recitation.
Reciter: {reciter['name_bn']} ({reciter['name_en']}).
Avoid these recently used passages/titles:
- {avoid_list}

Select a fresh, inspiring passage with 100% complete contextual integrity. Return valid JSON only."""

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=600)
        if isinstance(data, dict) and data.get("surah") and data.get("ayah_start"):
            surah = int(data["surah"])
            start = int(data["ayah_start"])
            end = int(data.get("ayah_end") or start)
            
            # Fetch data from API
            verse_data = fetch_verse_data(surah, start, end)
            verse_data["theme_headline"] = data.get("theme_headline", "কোরআনের আলো ও হেদায়াত")
            verse_data["reflection_bn"] = data.get("reflection_bn", "")
            verse_data["reciter_id"] = reciter_id
            verse_data["reciter"] = reciter
            return verse_data
    except Exception as e:
        logger.warning(f"AI passage selection notice: {e}. Falling back to curated bank.")

    # Fallback to curated rotation
    import random
    choice = random.choice(CURATED_COMPLETE_PASSAGES)
    verse_data = fetch_verse_data(choice["surah"], choice["ayah_start"], choice["ayah_end"])
    verse_data["theme_headline"] = choice["theme_hint"]
    verse_data["reflection_bn"] = choice["reflection_bn"]
    verse_data["reciter_id"] = reciter_id
    verse_data["reciter"] = reciter
    return verse_data
