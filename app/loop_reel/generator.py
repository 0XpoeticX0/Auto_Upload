import os
import re
import json
import time
import math
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

# Emotionally-weighted Islamic Domains (Hot domains 2x, cold domains 1x — Bangla audience psychology)
DYNAMIC_ISLAMIC_DOMAINS = [
    {
        "name": "ব্যবসায়িক সততা ও লেনদেন (Business & Trade Ethics)",
        "theme": "সঠিক মাপে দেওয়া, ক্রয়-বিক্রয়ে সত্যবাদিতা, ভেজালমুক্ত ব্যবসা, শ্রমিকের পারিশ্রমিক",
        "guidance": "Focus on Sahih Hadiths regarding honesty in commerce, returning trusts, not hiding defects in goods, paying workers promptly before their sweat dries."
    },
    {
        "name": "প্রতিবেশী ও সমাজের হক (Neighbor & Social Rights)",
        "theme": "প্রতিবেশীর প্রতি সদাচরণ, কষ্ট না দেওয়া, খাবার হাদিয়া দেওয়া, মেহমানদারি",
        "guidance": "Focus on the immense rights of neighbors in Sahih Hadiths (Jibreel AS advising so much the Prophet thought neighbors would inherit), honoring guests, smiling, removing harmful objects."
    },
    {
        "name": "মুখ ও জিহ্বার হেফাজত (Guarding the Tongue)",
        "theme": "গীবত বর্জন, কথা কম বলা, সত্য বলা অথবা চুপ থাকা, কটূক্তি পরিহার",
        "guidance": "Focus on Hadiths about guarding the tongue and private parts guaranteeing Jannah, 'whoever believes in Allah and the Last Day let him speak good or remain silent'."
    },
    {
        "name": "অহংকার বর্জন ও বিনয় (Humility vs Arrogance)",
        "theme": "অন্তরে সরিষার দানা পরিমাণ অহংকার, বিনয়ীদের আল্লাহ সম্মান দেন, পোশাক ও চালচলন",
        "guidance": "Focus on authentic Hadiths about arrogance preventing entry to Jannah, the virtue of humble character, greeting poorer people, walking with humility."
    },
    {
        "name": "মা-বাবা ও আত্মীয়তার সম্পর্ক (Parents & Kinship)",
        "theme": "পিতা-মাতার খেদমত, রক্ত সম্পর্কীয় আত্মীয়দের সাথে সম্পর্ক বজায় রাখা (সিলাহ রাহমি)",
        "guidance": "Focus on Silah Rahmi expanding Rizq and life span, kindness to mother and father, not breaking ties even if relatives cut ties."
    },
    {
        "name": "জীবজন্তু ও প্রকৃতির প্রতি দয়া (Kindness to Animals & Nature)",
        "theme": "পিপাসার্ত কুকুরকে পানি পান করিয়ে ক্ষমা, গাছ লাগানো সাদকা, পানি অপচয় না করা",
        "guidance": "Focus on authentic narrations of forgiveness through mercy to animals, planting trees that birds or humans eat from counting as ongoing Sadaqah."
    },
    {
        "name": "দৈনন্দিন ছোট সুন্নাহ ও আদব (Everyday Manners & Micro-Sunnahs)",
        "theme": "সালামের প্রসার, ডান দিক থেকে শুরু, হাঁচির জবাব, মেসওয়াকের ফযিলত",
        "guidance": "Focus on simple beautiful daily Sunnahs that carry huge rewards: spreading Salam among acquaintances and strangers, smiling, Sunnah of eating/drinking."
    },
    {
        "name": "রাগ নিয়ন্ত্রণ ও ক্ষমা (Anger Control & Forgiving People)",
        "theme": "রাগ দমনের পুরস্কার, যে ক্ষমা করে আল্লাহ তার সম্মান বাড়িয়ে দেন, বিবাদ মিটমাট",
        "guidance": "Focus on 'The strong man is not the wrestler, but the one who controls anger', forgiving others so Allah forgives you, reconciling between two Muslims."
    },
    {
        "name": "সুস্থতা ও রুগ্ন ব্যক্তিকে দেখতে যাওয়া (Visiting the Sick & Health)",
        "theme": "অসুস্থ ব্যক্তিকে দেখতে যাওয়ার ফযিলত (৭০,০০০ ফেরেশতার দোয়া), আল্লাহর নিয়ামত স্বাস্থ্য",
        "guidance": "Focus on authentic Hadiths on visiting the sick, picking fruits of Jannah, angels praying for the visitor, taking care of one's health."
    },
    {
        "name": "সহজীকরণ ও মানুষের উপকার (Making Things Easy & Helping Others)",
        "theme": "যে মানুষের কষ্ট দূর করে আল্লাহ তার কিয়ামতের কষ্ট দূর করবেন, দ্বীন সহজ",
        "guidance": "Focus on 'Allah helps His servant as long as the servant helps his brother', making matters easy and not creating hardship, relieving distress."
    },
    {
        "name": "ইলম ও দ্বীনের জ্ঞান অর্জন (Seeking Knowledge & Sincerity)",
        "theme": "জ্ঞান অর্জনের পথে চলা জান্নাতের পথ, যে ব্যক্তি নিয়ত খাঁটি রাখে",
        "guidance": "Focus on the angels lowering their wings for the seeker of knowledge, sincerity of deeds (ইখলাস), purity of heart."
    },
    {
        "name": "দান-সদকা ও গোপন নেক আমল (Sadaqah & Secret Deeds)",
        "theme": "এক টুকরো খেজুর দিয়ে হলেও জাহান্নাম থেকে বাঁচা, গোপন সদকা আল্লাহর রাগ নিভিয়ে দেয়",
        "guidance": "Focus on small consistent charities, secret good deeds between a servant and Allah, feeding the hungry, helping an orphan."
    },
    # ── 2x HIGH-EMOTION duplicates (Bangla audience responds most to these) ────
    {
        "name": "মা-বাবা ও আত্মীয়তার সম্পর্ক — গভীর আবেগ (Parents — Emotional Depth)",
        "theme": "পিতার চোখের জল, মায়ের দোয়া, সিলাহ রাহমিতে রিজিক বৃদ্ধি, সন্তানের কর্তব্য",
        "guidance": "Deep emotional focus: a mother's dua opening doors of Rizq, a father's anger being Allah's anger, the Hadith on children neglecting parents and its consequences."
    },
    {
        "name": "রাগ নিয়ন্ত্রণ — পারিবারিক শান্তি (Anger — Family Peace)",
        "theme": "স্বামী-স্ত্রীর মনোমালিন্য, ক্ষমার মাধ্যমে সম্পর্ক মেরামত, রাগে শয়তানের প্রবেশ",
        "guidance": "Focus on domestic peace: forgiving spouse, controlling anger to protect family bond, Hadith on Shaytan's power during anger and how to neutralize it."
    },
    {
        "name": "দৈনন্দিন ছোট সুন্নাহ — অদৃশ্য বরকত (Everyday Sunnah — Hidden Barakah)",
        "theme": "ঘরে প্রবেশের সুন্নাহ, খাবারে বিসমিল্লাহ ভুললে শয়তান শরিক হয়, রাতের ঘুমের সুন্নাহ আমল",
        "guidance": "Focus on micro-sunnahs most people miss daily: Bismillah when entering home, right hand sunnah, specific duas for ordinary moments that bring unseen barakah."
    },
    {
        "name": "দান-সদকা — হাতের কাছের আমল (Sadaqah — Acts Within Reach)",
        "theme": "হাসি সদকা, রাস্তা থেকে কষ্টদায়ক বস্তু সরানো, প্রতিবেশীকে এক বাটি তরকারি দেওয়া",
        "guidance": "Focus on the smallest sadaqahs people overlook: a genuine smile, removing a stone from the road, sharing one bowl of food with a neighbor — each counted by Allah."
    }
]

SLOT_CONFIGS = {
    "dynamic": {
        "name": "🌟 Dynamic Sahih Sunnah Feed",
        "theme": "Authentic Hadiths Across All Spheres of Islamic Life",
        "system_instruction": "Select a 100% fresh, unexplored Sunnah teaching.",
        "visual_prompt": "vertical 9:16, inside an ancient Islamic sanctuary, photorealistic 8k, no people, no living beings"
    }
}

def determine_current_slot() -> str:
    """Returns dynamic slot key."""
    return "dynamic"



ANGLES = [
    {
        "name": "High-Stakes Paradox (অপ্রত্যাশিত তুলনা ও তীব্র কৌতূহল)",
        "desc": "সাধারণ ধারণার বিপরীতে সুন্নাহর এক অবিশ্বাস্য তুলনা যা শুনলে দর্শক চমকে ওঠে। হুকে সমাধান বলা নিষিদ্ধ!",
        "example_hook": "হাজার রাকাত নফল নামাজের চেয়েও নবীজি (ﷺ) কোন ১টি আমলের জান্নাতের দায়িত্ব নিলেন?",
        "cta_example": "☞ কোন আমলের কথা বলা হয়েছিল? ক্যাপশনে দেখুন ➔"
    },
    {
        "name": "Real Pain-Point & Moral Dilemma (ব্যক্তিগত সংকট ও নৈতিক দ্বন্দ্ব)",
        "desc": "মানুষের মনের ভেতরের গভীর ক্ষোভ, সম্পর্কের টানাপোড়েন বা অপমানের অনুভূতিকে স্পর্শ করে অমীমাংসিত প্রশ্ন তোলা। উপদেশ দেওয়া নিষিদ্ধ, সংকট তোলা বাধ্যতামূলক!",
        "example_hook": "যে আত্মীয় চরম অপমান করে সম্পর্ক ছিন্ন করল, তার সাথে কি আবারও কথা বলা উচিত?",
        "cta_example": "☞ নবীজি কী উত্তর দিয়েছিলেন? ক্যাপশনে পড়ুন ➔"
    },
    {
        "name": "Unfinished Prophetic Scene (নাটকীয় অসম্পূর্ণ দৃশ্য — Zeigarnik Effect)",
        "desc": "হাদিসের সত্য ঘটনার সবচেয়ে নাটকীয় ক্লাইম্যাক্স মুহূর্তে হুক থামিয়ে দেওয়া, যার সমাধান শুধুমাত্র ক্যাপশনে জানা যাবে।",
        "example_hook": "নবীজির সামনে রেগে লাল হয়ে গেল এক ব্যক্তি; সবাই যখন তাকে থামাতে পারল না, তখন নবীজি বললেন—",
        "cta_example": "☞ রাগ নিভানোর ৪ শব্দের দোয়াটি ক্যাপশনে দেখুন ➔"
    },
    {
        "name": "99% Blindspot & Loss Aversion (অজান্তেই বড় ক্ষতি হওয়ার ভয়)",
        "desc": "দৈনন্দিন সাধারণ ভুল বা অসতর্কতা যা মানুষের অজান্তেই নেক আমল নষ্ট করে। মানুষ পাওয়ার চেয়ে ক্ষতি ঠেকাতে ২.৫ গুণ বেশি দ্রুত ক্লিক করে!",
        "example_hook": "আমরা অজান্তেই প্রতিদিন যে ৩টি ভুল কথা বলে ফেলি, যা সারাদিনের সব আমল এক নিমেষে ধ্বংস করে দেয়!",
        "cta_example": "☞ কোন ৩টি মারাত্মক ভুল? ক্যাপশনে জানুন ➔"
    },
    {
        "name": "Secret Prophetic Remedy (গোপন সুন্নাহ ও অমীমাংসিত প্রশ্ন)",
        "desc": "কঠিন মানসিক অবস্থা, একাকীত্ব বা সংকটে নবীজির শেখানো এক বিশেষ অপ্রত্যাশিত সমাধান যা বেশিরভাগ মানুষ জানে না।",
        "example_hook": "মন যখন অতিরিক্ত ভারী লাগে আর কোনো কাজে মন বসে না, নবীজি (ﷺ) গোপনে কোন কাজটি করতে বলেছিলেন?",
        "cta_example": "☞ গোপনে শেখানো আমলটি ক্যাপশনে পড়ুন ➔"
    }
]

TONES = [
    "Intense Curiosity & Shock (চমকে দেওয়ার মতো কৌতূহল ও বিস্ময়)",
    "Deep Emotional Dilemma (গভীর আত্মউপলব্ধি ও আবেগী দ্বন্দ্ব)",
    "Dramatic Narrative Tension (নাটকীয় সাসপেন্স ও অসম্পূর্ণ দৃশ্য)",
    "High-Stakes Loss Aversion (সতর্কবার্তা ও অজান্তেই ক্ষতি ঠেকানোর আকুলতা)"
]

BANNED_HOOK_PREFIXES = [
    (r'^(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*\([ﷺসা\.]+\)\s*বলেছেন\s*[:ঃ\s]*',
     r'(?:রাসূলুল্লাহ|রাসূল|নবীজি|আল্লাহর\s*রাসূল)\s*\([ﷺসা\.]+\)\s*বলেছেন'),
    (r'^(?:নবীজির|নবীজি|রাসূলের)\s*\([ﷺসা\.]+\)\s*শেখানো\s*',
     r'(?:নবীজির|নবীজি|রাসূলের)\s*\([ﷺসা\.]+\)\s*শেখানো'),
]

BANNED_CLICHE_PHRASES = [
    'ভাগ্যের তালা', 'ভাগ্য বদলে', 'জীবন বদলে'
]

FORMULAIC_HOOK_WORDS = [
    '১টি আমল', '১টি গোপন আমল', '১টি কার্যকরী আমল', '১টি আমল করলে', '১টি বাক্য', '৫ সেকেন্ডের', '২ মিনিটের'
]

def check_hook_monotony(content: dict, recent_history: list, last_hook_text: str = "") -> tuple[bool, str]:
    """Strictly validates hook diversity to prevent robotic, repetitive reel openings."""
    line_1 = (content.get("line_1") or "").strip()
    line_2 = (content.get("line_2") or "").strip()
    full_hook = f"{line_1} {line_2}".strip()

    if not line_1:
        return False, "Hook line_1 is missing or empty."

    # 1. Ban clickbait clichés unconditionally
    for c in BANNED_CLICHE_PHRASES:
        if c in full_hook:
            return False, f"Banned cliché '{c}' detected in hook! Use authentic, natural phrasing."

    # 2. Prevent authority prefix on Line 1 (Line 1 must be human-first situation/hook)
    for new_pat, _ in BANNED_HOOK_PREFIXES:
        if re.search(new_pat, line_1):
            return False, f"Line 1 must NOT start with Hadith preface '{line_1[:25]}...'. Open with a relatable human situation, emotion, or observation first!"

    # 3. Restrict formulaic phrase frequency (e.g. '১টি আমল', '৫ সেকেন্ডের')
    for phrase in FORMULAIC_HOOK_WORDS:
        if phrase in full_hook:
            count = sum(1 for prev in recent_history[:4] if phrase in prev)
            if count >= 1:
                return False, f"Formulaic phrase '{phrase}' appeared in recent videos. Vary the vocabulary and structure!"

    # 4. Enforce Zero Grammatical/Word Overlap in first 5 words against last hook
    if last_hook_text:
        new_first_5 = set(re.sub(r'[^\w\s]', '', line_1).lower().split()[:5])
        last_first_5 = set(re.sub(r'[^\w\s]', '', last_hook_text).lower().split()[:5])
        overlap = new_first_5 & last_first_5
        if len(overlap) >= 2:
            return False, f"Opening words share repetitive overlap {overlap} with last hook: '{last_hook_text[:30]}...'"

    # 5. Enforce syntactic dissimilarity (Jaccard on line_1)
    cleaned_new = set(re.sub(r'[^\w\s]', '', line_1).lower().split())
    for prev in recent_history[:8]:
        cleaned_prev = set(re.sub(r'[^\w\s]', '', prev).lower().split())
        if not cleaned_prev:
            continue
        sim = len(cleaned_new & cleaned_prev) / len(cleaned_new | cleaned_prev)
        if sim >= 0.50:
            return False, f"Hook line_1 is syntactically too similar ({sim:.2f}) to recent content: '{prev[:40]}...'"

    # 6. Reject preachy/sermon imperative spoilers that kill curiosity
    preachy_imperatives = [
        r'(?:সঠিক\s*)?হেফাজত\s*করুন',
        r'মিশে\s*চলুন',
        r'নিয়ম\s*মেনে\s*চলুন',
        r'ভালো\s*ব্যবহার\s*করুন',
        r'সবর\s*করুন',
    ]
    for pat in preachy_imperatives:
        if re.search(pat, line_1) or re.search(pat, line_2):
            return False, f"Hook sounds like a preachy sermon ('{pat}'). Must pose an open loop, shocking dilemma, or question!"

    return True, "OK"

SAFE_ASS_CHARS = {'✦', '☞', '➔', '•', '—', '–', '।', '?', '!', ':', '-', ',', '.', '(', ')', '@', '#'}

def sanitize_text_for_ass(text: str) -> str:
    """
    Strips emojis, variation selectors, and pictorial symbols to eliminate
    the broken 'tofu box' (▯) in FFmpeg libass rendering under Noto Sans Bengali.
    Preserves universal safe symbols: ✦, ☞, ➔, •, punctuation, English, Bengali.
    """
    if not text:
        return ""
    # Map directional/action emojis to clean typography symbols
    text = text.replace('👇', ' ➔').replace('👉', '☞ ').replace('👈', '☜ ')
    text = text.replace('➡', '➔').replace('➡️', '➔').replace('⬇', '➔')
    text = text.replace('📖', '').replace('🤲', '').replace('🤍', '').replace('🌿', '')
    text = text.replace('✨', '').replace('🔥', '').replace('📌', '').replace('🔖', '')

    out = []
    for ch in text:
        code = ord(ch)
        # Drop Supplementary Multilingual Plane emojis (U+1F000 to U+1FAFF)
        if 0x1F000 <= code <= 0x1FAFF:
            continue
        # Drop variation selectors & zero-width joiner
        if code in (0xFE0E, 0xFE0F, 0x200D):
            continue
        # In Dingbats/Misc Symbols range, keep only explicitly safe symbols
        if (0x2600 <= code <= 0x27BF) and ch not in SAFE_ASS_CHARS:
            continue
        out.append(ch)
    return re.sub(r' +', ' ', ''.join(out)).strip()

def revise_and_balance_hook_lines(l1: str, l2: str = "", l3: str = "", l4: str = "") -> list[str]:
    """
    Intelligent Subtitle Typography Auto-Revision Engine:
    - Eliminates clause duplication and substring containment (e.g. LLM putting full sentence in line_1 and repeating in line_2/3).
    - Removes identical duplicate lines.
    - If a single run-on line is provided, auto-splits it into 2 to 3 natural, balanced clauses.
    - Preserves line_1, line_2, line_3 (and optional line_4, up to 4 lines max) without dropping line 3.
    - Never throws or blocks; guarantees returning a list of clean, non-repeating lines.
    """
    def _clean(t: str) -> str:
        t = sanitize_text_for_ass(t or '')
        t = t.strip(' \t\n\r"\'“”‘’')
        t = re.sub(r'[\s\.\—\–\,\-]+$', '', t)
        t = t.strip(' ,;-—')
        # Deduplicate repeated adjacent words or 2-word phrases within line (e.g. "জান্নাতের জিম্মাদার ... জান্নাতের জিম্মাদার")
        words = t.split()
        if len(words) > 2:
            cleaned_words = []
            i = 0
            while i < len(words):
                if i + 3 < len(words) and words[i] == words[i+2] and words[i+1] == words[i+3]:
                    cleaned_words.extend([words[i], words[i+1]])
                    i += 4
                elif i + 1 < len(words) and words[i] == words[i+1]:
                    cleaned_words.append(words[i])
                    i += 2
                else:
                    cleaned_words.append(words[i])
                    i += 1
            t = " ".join(cleaned_words)
        return t

    l1 = _clean(l1)
    l2 = _clean(l2)
    l3 = _clean(l3)
    l4 = _clean(l4)

    if not l1 and not l2 and not l3 and not l4:
        return []

    # 1. Resolve substring containment / clause repetition (e.g., Episode 47 where l1 contained full l2 and l3)
    if l2 and l2 in l1:
        prefix = _clean(l1.split(l2)[0])
        if prefix:
            l1 = prefix
        else:
            remainder = _clean(l1[len(l2):])
            if remainder:
                l1 = l2
                l2 = remainder
            else:
                l2 = ""

    if l3 and l3 in l1:
        prefix = _clean(l1.split(l3)[0])
        if prefix:
            l1 = prefix

    if l3 and l2 and l3 in l2:
        prefix = _clean(l2.split(l3)[0])
        if prefix:
            l2 = prefix
        else:
            remainder = _clean(l2[len(l3):])
            if remainder:
                l2 = l3
                l3 = remainder
            else:
                l3 = ""

    if l4 and l3 and l4 in l3:
        prefix = _clean(l3.split(l4)[0])
        if prefix:
            l3 = prefix

    # 2. Gather non-empty lines and deduplicate identical or near-identical lines
    raw_lines = [l for l in [l1, l2, l3, l4] if l]
    deduped_lines = []
    for line in raw_lines:
        line_clean = _clean(line)
        if not line_clean:
            continue
        is_dup = False
        for ex in deduped_lines:
            if line_clean == ex or (len(line_clean) > 8 and line_clean in ex):
                is_dup = True
                break
        if not is_dup:
            deduped_lines.append(line_clean)

    # 3. If only one single long line exists (> 7 words), auto-split into balanced clauses (2 or 3 lines)
    if len(deduped_lines) == 1:
        words = deduped_lines[0].split()
        if len(words) >= 8:
            if len(words) <= 12:
                mid = len(words) // 2
                best_split = mid
                for idx in range(max(1, mid - 2), min(len(words) - 1, mid + 3)):
                    prev_w = words[idx - 1]
                    curr_w = words[idx]
                    if prev_w.endswith(',') or prev_w.endswith(';') or curr_w in ['আর', 'যে', 'কিন্তু', 'এবং', 'তবে', 'অথচ', 'নবীজি', 'নবীজির']:
                        best_split = idx
                        break
                p1 = _clean(" ".join(words[:best_split]))
                p2 = _clean(" ".join(words[best_split:]))
                deduped_lines = [p for p in [p1, p2] if p]
            else:
                chunk = len(words) // 3
                s1 = max(1, chunk)
                s2 = max(s1 + 1, chunk * 2)
                for idx in range(max(1, s1 - 1), min(len(words) - 2, s1 + 2)):
                    if words[idx - 1].endswith(',') or words[idx] in ['আর', 'যে', 'কিন্তু', 'এবং', 'তবে', 'অথচ', 'নবীজি', 'নবীজির']:
                        s1 = idx
                        break
                for idx in range(max(s1 + 1, s2 - 1), min(len(words) - 1, s2 + 2)):
                    if words[idx - 1].endswith(',') or words[idx] in ['আর', 'যে', 'কিন্তু', 'এবং', 'তবে', 'অথচ', 'নবীজি', 'নবীজির']:
                        s2 = idx
                        break
                p1 = _clean(" ".join(words[:s1]))
                p2 = _clean(" ".join(words[s1:s2]))
                p3 = _clean(" ".join(words[s2:]))
                deduped_lines = [p for p in [p1, p2, p3] if p]

    # 4. Cap at maximum 4 lines
    if len(deduped_lines) > 4:
        deduped_lines = deduped_lines[:3] + [" ".join(deduped_lines[3:])]

    final_lines = [_clean(line) for line in deduped_lines if _clean(line)]
    return final_lines

def normalize_and_balance_hook_lines(l1: str, l2: str = "", l3: str = "", l4: str = "") -> list[str]:
    """Compatibility wrapper returning list of clean, non-repeating lines."""
    return revise_and_balance_hook_lines(l1, l2, l3, l4)

def revise_and_enforce_hook_typography(content: dict) -> tuple[bool, str, dict]:
    """
    Typography Quality Gate & Auto-Revision Engine:
    - Auto-revises hook mistakes (removes duplicate clauses, repairs run-ons, balances lines).
    - Preserves line_1, line_2, line_3 (and optional line_4, up to 4 lines max) without dropping line 3.
    - Never blocks the pipeline: automatically revises and repairs in-place.
    """
    l1 = (content.get("line_1") or "").strip()
    l2 = (content.get("line_2") or "").strip()
    l3 = (content.get("line_3") or "").strip()
    l4 = (content.get("line_4") or "").strip()

    # If line_1 is missing, derive it from title_bn so we never block
    if not l1:
        title = (content.get("title_bn") or "").strip()
        if title:
            logger.info("Hook line_1 was empty; auto-revising from title_bn.")
            parts = [p.strip() for p in re.split(r'[,;।\—\-]', title) if p.strip()]
            l1 = parts[0] if len(parts) > 0 else title[:40]
            l2 = parts[1] if len(parts) > 1 else ""
            l3 = parts[2] if len(parts) > 2 else ""
        else:
            l1 = "নবীজির (ﷺ) এই ১টি আমল শিখুন"
            l2 = "জীবন বরকতে ভরে যাবে ➔"

    clean_lines = revise_and_balance_hook_lines(l1, l2, l3, l4)
    if not clean_lines:
        clean_lines = [l1]

    content["line_1"] = clean_lines[0]
    content["line_2"] = clean_lines[1] if len(clean_lines) > 1 else ""
    content["line_3"] = clean_lines[2] if len(clean_lines) > 2 else ""
    if len(clean_lines) > 3:
        content["line_4"] = clean_lines[3]
    elif "line_4" in content:
        del content["line_4"]

    # Sanitize or populate dynamic caption_cta
    raw_cta = content.get("caption_cta", "")
    if raw_cta and len(raw_cta.strip()) >= 5:
        content["caption_cta"] = sanitize_text_for_ass(raw_cta)
    else:
        content["caption_cta"] = "☞ পুরো হাদিস ও আমলটি ক্যাপশনে দেখুন ➔"

    logger.info(f"Hook typography auto-revised successfully ({len(clean_lines)} lines): {clean_lines}")
    return True, "OK", content

# Backwards compatibility alias
check_and_enforce_hook_typography = revise_and_enforce_hook_typography

def build_loop_reel_system_prompt(
    ep_bn: str,
    target_angle: dict,
    target_tone: str,
    last_hook_text: str,
    avoid_context: str,
    cfg: dict,
    assigned_domain: dict = None
) -> str:
    """Builds the comprehensive system prompt customized for the specific angle, tone, domain and episode."""
    domain_name = assigned_domain['name'] if assigned_domain else "দৈনন্দিন সুন্নাহ ও চারিত্রিক সৌন্দর্য"
    domain_guidance = assigned_domain['guidance'] if assigned_domain else "Authentic Sahih Hadith from major books."

    return f"""You are a master viral Islamic content creator specializing in high-retention 7-second aesthetic Reels with high-value captions.

# ==============================================================================
# STRICT 100-VIDEO ZERO-SIMILARITY & FRESH TOPIC MANDATE
# ==============================================================================
STRICT ZERO-SIMILARITY MANDATE (LAST 100 VIDEOS):
You must select a 100% FRESH, NOVEL, and UNEXPLORED Sahih Hadith topic that has ZERO similarity to any of the last 100 videos.
STRICTLY FORBIDDEN TO REPEAT RECENT OR OVERSATURATED THEMES:
- ❌ NO Sleep / Bedtime / Night waking (ঘুমানোর আমল, বিছানায় যাওয়া, দুঃস্বপ্ন, তাহাজ্জুদ)
- ❌ NO Grave / Torment of the grave / Surah Mulk (কবর, কবরের আজাব, সূরা মুলক)
- ❌ NO Anxiety / Depression / Mental agitation / Heaviness (দুশ্চিন্তা, পেরেশানি, মানসিক অশান্তি, মন খারাপ)
- ❌ NO Debt / Money crises / Poverty (ঋণ পরিশোধ, দেনা, পাহাড়সমান ঋণ)
- ❌ NO Sins erasing like sea foam (সমুদ্রের ফেনা, পাহাড় পরিমাণ গুনাহ মাফ)

ASSIGNED SPECIFIC ISLAMIC DOMAIN FOR THIS REEL:
• Domain: {domain_name}
• Specific Focus: {domain_guidance}

[ASSIGNED ANGLE & LENS FOR EPISODE #{ep_bn}]
• Angle Archetype: {target_angle['name']}
• Angle Focus: {target_angle['desc']}
• Tone: {target_tone}
• Model Hook Pattern: "{target_angle['example_hook']}"

[LAST POSTED HOOK TO CONTRAST AGAINST]
"{last_hook_text}"

[CONTRASTIVE ANTI-SIMILARITY DIRECTIVE]
1. Read the [LAST POSTED HOOK].
2. Determine its opening style (Question? Story? Direct action? Emotion?).
3. Create a hook with a COMPLETELY CONTRASTING structure:
   - If the last hook was a Question -> Use a Micro-Moment Story or Direct Observation.
   - If the last hook offered a Fast Micro-Action -> Use a Deep, Slow, Reflective Realization.
   - If the last hook mentioned an Action -> Start with a raw, relatable Human Emotion or Situation.
4. ZERO WORD OVERLAP: The first 5 words of Line 1 must NOT share any vocabulary or grammar pattern with the last hook.
5. OPENING LINE DIRECTIVE:
   - For blessed calendar events: Line 1 establishes the day reminder / timing urgency (e.g., '{day_rem.split()[0] if assigned_domain and assigned_domain.get("is_hijri_event") else ""}...').
   - Otherwise, Line 1 must NOT start with 'রাসূলুল্লাহ (ﷺ) বলেছেন:' or 'নবীজির শেখানো'; it belongs purely to the relatable human struggle or situation. The Prophet's authentic Sunnah and Sahih citation belong in Line 2/3 and the structured caption points!

SERIES CONTEXT: "আজকের আমল • পর্ব {ep_bn}"

# ==============================================================================
# RULE #0 SUPREME MANDATE: 100% CONTEXTUAL COHERENCE & TRUTHFUL HOOK
# ==============================================================================
RULE 0: ABSOLUTE ISLAMIC AUTHENTICITY, CONTEXTUAL COHERENCE & ZERO HALLUCINATED CONTEXT:
1. 100% CONTEXTUAL MATCH: The hook (Line 1, Line 2, Line 3) and title_bn MUST DIRECTLY AND TRUTHFULLY INTRODUCE the EXACT Hadith and topic in caption_points!
   - ❌ STRICTLY FORBIDDEN: Writing an unrelated story in the hook (e.g. NEVER write 'মসজিদে একা বসে কাঁদছিলেন এক সাহাবী' if the Hadith is about anger management, parents, or honesty!).
   - If the Hadiths are about Anger (রাগ নিয়ন্ত্রণ), the hook and title MUST be about anger (e.g. 'খুব বেশি রাগ উঠলে নবীজি (ﷺ) কী করতে বলেছিলেন?').
   - If using a Story Snippet, the story MUST be the authentic prelude/background (Sabab al-Wurud) of that exact Hadith (e.g., 'নবীজির সামনে দুই ব্যক্তি রেগে লাল হয়ে গিয়েছিল...'), NOT a fabricated or borrowed story from an unrelated Hadith!
2. NEVER MERGE HADITHS: Never combine multiple separate Hadiths into one quotation or under one reference. Keep distinct narrations separate with their own exact citations!
3. EXACT BOOK & HADITH NUMBER ONLY: Never write vague references like "সহীহ বুখারী ও মুসলিম" or "সহীহ হাদিস সমগ্র". Every single Hadith quote MUST have the exact specific book and Hadith number (e.g., "সহীহ বুখারী: ৬৩২৪", "জামে আত-তিরমিযী: ২৮৯১", "সহীহ মুসলিম: ৭০৭", "সুনানে আবু দাউদ: ১৪০০").
4. NO FABRICATED "ফলাফল" OR PROMISES: Never invent unverified summary promises like "যে ব্যক্তি এটি করবে সে আল্লাহর আশ্রয়ে থাকবে এবং জান্নাতের সুসংবাদ পাবে". Only state what the Prophet (ﷺ) explicitly stated in the cited Hadith!
5. AUTHENTIC DUAS ONLY: Arabic Dua must be 100% authentic with accurate Bengali pronunciation and genuine meaning.
6. PURE BENGALI ONLY: Strictly ZERO English loan words in Bengali text (❌ BANNED: 'neutralize', 'boost', 'negative', 'mindset', etc. ✅ USE: 'দূর করার উপায়', 'দমন করার উপায়').
7. COMPLETE NARRATIVE CLOSURE IN CAPTION:
   - Dramatic Story Snippet hooks (e.g. 'মসজিদে একা বসে কাঁদছিলেন এক সাহাবী; নবীজি (ﷺ) কাছে গিয়ে জিজ্ঞেস করলেন—') are EXCELLENT for viewer engagement and retention.
   - When using a Story Snippet hook:
     • Point 1 of caption_points MUST immediately resolve the opening scene (explain why the person was crying/in distress, what the Prophet asked, and the companion's reply).
     • Point 2 provides the Prophet's instruction, Sunnah act, or exact Dua with full Arabic, pronunciation, meaning, and Sahih citation.
     • Point 3 provides the resolution and result (e.g., how the companion practiced it and their worries/debt were relieved).
8. STRICT OPEN-LOOP & ZERO SOLUTION SPOILAGE MANDATE (হুকে সমাধান ফাঁস করা সম্পূর্ণ নিষিদ্ধ):
   - A 7-second Loop Reel is a CURIOSITY MAGNET, NOT A SERMON!
   - ❌ ABSOLUTELY BANNED: Preaching or telling viewers what to do on screen (e.g., 'জিহ্বা আর লজ্জাস্থানের সঠিক হেফাজত করুন', 'মিশে চলুন', 'আমলটি করুন').
   - ❌ ABSOLUTELY BANNED: Revealing the full Hadith answer/resolution on screen (e.g., 'জিহ্বা হেফাজত করুন, নবীজি জান্নাতের দায়িত্ব নিলেন'). This destroys all curiosity and viewers will NEVER open the caption!
   - ✅ MANDATORY: The on-screen text ('line_1', 'line_2', 'line_3') must ONLY pose the burning question, the emotional dilemma, the dramatic scene, or the shocking contrast.
   - The ONLY place where the Prophet's exact Hadith answer, Arabic Dua, and action steps are revealed is IN THE CAPTION!
   - Line 3 (or the end of Line 2) MUST create a bridge pointing to the caption (e.g., 'নবীজির (ﷺ) এই ১টি উত্তর আপনার চোখ ভিজিয়ে দেবে ➔', 'চমকে যাওয়ার মতো হাদিসটি ক্যাপশনে দেওয়া হলো ➔', 'রাগ নিভানোর ৪ শব্দের দোয়াটি ক্যাপশনে দেখুন ➔').
   - The hook should consist of 2 to 3 (max 4) short, punchy lines (3-5 words each, total 8-16 words).
   - In 'caption_cta', write a short, punchy 1-line call-to-action directly connected to the hook's question (e.g., "☞ নবীজি কী উত্তর দিয়েছিলেন? ক্যাপশনে দেখুন ➔").
   - ZERO EMOJIS in on-screen text lines ('line_1', 'line_2', 'line_3')! Use clean text and the arrow symbol '➔'.

# ==============================================================================
# RULE #2 SUPREME MANDATE: SIMPLE, CONVERSATIONAL BENGALI (সহজ মুখের ভাষা)
# ==============================================================================
LANGUAGE SIMPLICITY (MANDATORY — ZERO TOLERANCE FOR LITERARY/COMPLEX BENGALI):
- ❌ STRICTLY BANNED: Overly literary, poetic, or complex Bengali words and sentence structures.
  Examples of BANNED complex phrases: "একাকী জীবনের ব্যস্ততায়", "বিশাল দুয়ার বন্ধ হয়ে যায়", "অনাবিল প্রশান্তি", "সুমধুর পরিবেশ", "হৃদয়ে গভীর প্রশান্তি নেমে আসবে", "অভাবনীয় বরকত"
- ✅ ALWAYS USE: Simple, everyday spoken Bengali (মুখের ভাষা) that a 12-year-old Bangladeshi student can instantly understand.
  Good examples: "ঘরে ঢোকার সময়", "মন খারাপ লাগলে", "রাগ উঠলে", "টাকার সমস্যা হলে", "আল্লাহ সাহায্য করবেন", "জান্নাতে যেতে পারবে"
- Write like you're talking to a friend — NOT writing a newspaper article or Bangla literature essay.
- Keep sentences SHORT and DIRECT. No unnecessary adjectives or flowery descriptions.
- Use common words: "সাহায্য" not "সহায়তা", "ঘর" not "গৃহ", "খুশি" not "পরিতৃপ্ত", "ভালো" not "উত্তম", "দরজা" not "দুয়ার"

THE 5 CORE PSYCHOLOGY HOOK ARCHETYPES (MANDATORY ROTATION):
• Archetype 1 (High-Stakes Paradox & Shocking Contrast):
  Compare something massive/difficult to an astonishing simple Sunnah.
  Example:
  line_1: "হাজার রাকাত নফল নামাজের চেয়েও"
  line_2: "নবীজি কোন ১টি সাধারণ আমলের জান্নাতের দায়িত্ব নিলেন?"
  line_3: "চমকে যাওয়ার মতো হাদিসটি ক্যাপশনে দেওয়া হলো ➔"
  caption_cta: "☞ কোন আমলের কথা বলা হয়েছিল? ক্যাপশনে দেখুন ➔"

• Archetype 2 (Personal Dilemma & Real Pain-Point):
  Trigger a raw, universal human conflict (family pain, betrayal, unfair insults, difficult relatives).
  Example:
  line_1: "যে আত্মীয় চরম অপমান করে সম্পর্ক ছিন্ন করল,"
  line_2: "তার সাথে কি আবারও কথা বলা উচিত?"
  line_3: "নবীজির (ﷺ) এই ১টি উত্তর আপনার চোখ ভিজিয়ে দেবে ➔"
  caption_cta: "☞ নবীজি কী উত্তর দিয়েছিলেন? ক্যাপশনে পড়ুন ➔"

• Archetype 3 (Unfinished Prophetic Scene — Zeigarnik Effect):
  Drop the viewer right at the climax of an authentic dramatic Hadith moment.
  Example:
  line_1: "নবীজির সামনে রেগে লাল হয়ে গেল এক ব্যক্তি,"
  line_2: "সবাই যখন তাকে থামাতে পারল না, তখন নবীজি বললেন—"
  line_3: "রাগ দমন করার ৪ শব্দের সেই দোয়াটি ক্যাপশনে দেখুন ➔"
  caption_cta: "☞ ৪ শব্দের দোয়াটি ক্যাপশনে দেখুন ➔"

• Archetype 4 (99% Blindspot & Loss Aversion):
  Highlight a daily unconscious mistake that destroys deeds. Fear of loss is 2.5x more urgent!
  Example:
  line_1: "আমরা অজান্তেই প্রতিদিন যে ৩টি ভুল কথা বলে ফেলি,"
  line_2: "যা সারাদিনের সব আমল এক নিমেষে ধ্বংস করে দেয়!"
  line_3: "সহীহ হাদিস নম্বরসহ সতর্ক থাকুন ➔ ক্যাপশনে"
  caption_cta: "☞ কোন ৩টি মারাত্মক ভুল? ক্যাপশনে জানুন ➔"

• Archetype 5 (Secret Prophetic Remedy):
  When feeling deep mental exhaustion, sadness, or struggle, the special Sunnah act taught privately.
  Example:
  line_1: "মন যখন অতিরিক্ত ভারী লাগে আর কোনো কাজে মন বসে না,"
  line_2: "নবীজি (ﷺ) এক সাহাবীকে গোপনে কোন কাজটি করতে বলেছিলেন?"
  line_3: "পুরো সুন্নাহ ও দোয়াটি ক্যাপশনে পড়ুন ➔"
  caption_cta: "☞ গোপনে শেখানো আমলটি ক্যাপশনে পড়ুন ➔"

CRITICAL GOLDEN HIGHLIGHT RULES (MANDATORY — Emotional Salience Priority):
In "highlight_words", you MUST provide 3 to 4 exact phrases from your lines.
Pick words using this EMOTIONAL PRIORITY ORDER (the brain reacts STRONGEST to these):
Priority 1 — FEAR / REWARD words (highest attention): জান্নাত, জাহান্নাম, ক্ষমা, বিপদ, সুরক্ষা, শাস্তি, সওয়াব
Priority 2 — IDENTITY words (self-relevance): মুমিন, সাহাবী, রাসূলুল্লাহ (ﷺ), আল্লাহ, নবীজি (ﷺ)
Priority 3 — ACTION verbs (engagement): পড়লে, করলে, বললে, মানলে, শিখুন
Priority 4 — NUMBERS & QUANTITIES (specificity): ১০০ গুণ, ১ মিনিট, ৩টি, প্রতিদিন
Always include at least ONE Priority 1 or Priority 2 word. Example:
  highlight_words: ["হাজার রাকাত", "নবীজি (ﷺ)", "জান্নাতের দায়িত্ব"]

CRITICAL DUA & CAPTION RULES (MANDATORY):
1. Complete Arabic Text: At least ONE caption point MUST contain full Arabic text with Tashkeel (either a relevant Dua OR the authentic Arabic wording of the Prophet's statement/Hadith), accurate phonetic Bengali pronunciation (উচ্চারণ), authentic Bengali meaning (অর্থ), and Sahih Book Reference.
2. Value-Packed Caption: Point-by-point breakdown with exact references (সহীহ বুখারী / সহীহ মুসলিম / জামে আত-তিরমিযী / সহীহ আন-নাসায়ী / সহীহ ইবনে মাজাহ).
3. Community Dhikr CTA + Follow Credit: 👉 @dailydos_islam

TOPICS RECENTLY COVERED (DO NOT REPEAT):
- {avoid_context}

Output ONLY valid JSON:
{{
    "series_title": "আজকের আমল • পর্ব {ep_bn}",
    "title_bn": "যে আত্মীয় চরম অপমান করে সম্পর্ক ছিন্ন করেছে, তার সাথে আবারও কথা বলা কি বোকামি? নবীজির এই এক জবাবে আপনি বাকরুদ্ধ হয়ে যাবেন",
    "title_en": "What the Prophet said about relatives who cut ties with you #Shorts",
    "line_1": "যে আত্মীয় চরম অপমান করে সম্পর্ক ছিন্ন করল,",
    "line_2": "তার সাথে কি আবারও কথা বলা উচিত?",
    "line_3": "নবীজির (ﷺ) এই ১টি উত্তর আপনার চোখ ভিজিয়ে দেবে ➔",
    "caption_cta": "☞ নবীজি কী উত্তর দিয়েছিলেন? ক্যাপশনে পড়ুন ➔",
    "highlight_words": ["চরম অপমান", "নবীজির (ﷺ)", "১টি উত্তর"],
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
    "visual_prompt": "{cfg['visual_prompt']}",
    "tags": ["Islam", "DailyReminder", "Sunnah", "সহীহ_হাদিস", "দোয়া", "DailyDos"]
}}"""

def generate_loop_reel_content(slot_key: str = None) -> dict:
    """Generates viral 7-second curiosity hook and high-value point-by-point caption with dynamic deduplication."""
    if not slot_key or slot_key not in SLOT_CONFIGS:
        slot_key = determine_current_slot()
    
    cfg = SLOT_CONFIGS[slot_key]
    logger.info(f"Targeting {cfg['name']} ({cfg['theme']})")

    # Fetch recent 100 topics to guarantee 100% zero duplication across the channel
    recent_titles = get_recent_video_titles(limit=100)
    avoid_context = "\n- ".join(recent_titles[:100]) if recent_titles else "None"

    # Calculate Series Episode Number
    ep_int, ep_bn = get_next_episode_number()

    # Extract last hook to contrast against
    last_entry = recent_titles[0] if recent_titles else ""
    last_hook_text = last_entry.split("| Hook:")[-1].strip() if "| Hook:" in last_entry else (last_entry.split("]")[-1].strip() if "]" in last_entry else last_entry)

    from app.history import check_topic_duplicate_global_detail
    from app.quality.islamic_verifier import verify_and_enforce_islamic_accuracy

    banned_hadiths = set()
    last_fail_reason = ""
    max_attempts = 10

    for attempt in range(max_attempts):
        # Dynamic Angle, Tone & Islamic Domain Rotation across attempts to break deadlocks
        angle_idx = (ep_int + attempt) % len(ANGLES)
        tone_idx = (ep_int + attempt) % len(TONES)
        domain_idx = (ep_int - 1 + attempt) % len(DYNAMIC_ISLAMIC_DOMAINS)

        target_angle = dict(ANGLES[angle_idx])
        target_tone = TONES[tone_idx]

        assigned_domain = DYNAMIC_ISLAMIC_DOMAINS[domain_idx]

        logger.info(f"Attempt {attempt+1}/{max_attempts}: Domain '{assigned_domain['name']}' | Angle '{target_angle['name']}' | Tone '{target_tone}' for Episode #{ep_bn}...")

        system_prompt = build_loop_reel_system_prompt(
            ep_bn=ep_bn,
            target_angle=target_angle,
            target_tone=target_tone,
            last_hook_text=last_hook_text,
            avoid_context=avoid_context,
            cfg=cfg,
            assigned_domain=assigned_domain
        )

        user_prompt = (
            f"Series Episode: {ep_bn}.\n"
            f"Assigned Islamic Domain: {assigned_domain['name']}\n"
            f"Domain Theme: {assigned_domain['theme']}\n"
            f"Guidance: {assigned_domain['guidance']}\n"
            f"Assigned Hook Angle: '{target_angle['name']}' ({target_angle['desc']}). Hook Tone: '{target_tone}'.\n"
            f"Select 1 deeply inspiring, authentic Sahih Hadith strictly within the domain '{assigned_domain['name']}'. "
            f"CRITICAL HOOK MANDATE: Create an irresistible OPEN LOOP hook that stops the scroll. NEVER spoil the answer, rule, or Hadith conclusion on screen! Pose the burning dilemma, dramatic unfinished scene, or shocking question. The answer belongs ONLY in the caption! Provide 'caption_cta' bridging the hook to the caption. "
            f"Ensure 100% authentic Sahih Hadith with exact book and number (e.g., সহীহ বুখারী: ২০৭৯ or সহীহ মুসলিম: ১৮৯৩). "
            f"Include authentic Arabic text with Tashkeel, Bengali pronunciation, and meaning for at least one point (either a relevant Dua or the Arabic wording of the Hadith). "
            f"STRICTLY FORBIDDEN: Do NOT select any topic from the avoided list below or any repetition of sleep, grave/Mulk, debt, or anxiety. Return valid JSON only with 'caption_cta'."
        )

        if banned_hadiths or last_fail_reason:
            banned_list_str = "; ".join(sorted(list(banned_hadiths))[:12])
            user_prompt += (
                f"\n\n[CRITICAL CORRECTION FROM PREVIOUS ATTEMPT]:\n"
                f"{last_fail_reason}\n"
                f"STRICTLY FORBIDDEN TOPICS / HADITHS (ALREADY USED): {banned_list_str}.\n"
                f"You MUST choose a COMPLETELY DIFFERENT authentic Hadith and Sunnah deed from another chapter/book!"
            )

        content = extract_json(system_prompt, user_prompt, max_tokens=1500)
        if not content:
            logger.warning(f"Attempt {attempt+1}: Failed to parse valid Loop Reel JSON from LLM. Retrying...")
            last_fail_reason = "Failed to parse valid JSON from LLM response. Return strictly valid JSON."
            time.sleep(2)
            continue
            
        title_bn = content.get("title_bn", "").strip()
        pts_text = " ".join([f"{pt.get('title', '')} {pt.get('hadith', '')} {pt.get('reference', '')}" for pt in content.get("caption_points", [])])
        full_check_text = f"{title_bn} {content.get('arabic', '')} {pts_text}"

        is_dup_title, reason_title = check_topic_duplicate_global_detail(title_bn, check_semantic=True)
        is_dup_full, reason_full = check_topic_duplicate_global_detail(full_check_text, check_semantic=False)

        if is_dup_title or is_dup_full:
            dup_reason = reason_title or reason_full
            logger.warning(f"Attempt {attempt+1}: Loop Reel topic flagged as duplicate: {dup_reason}")
            if title_bn:
                banned_hadiths.add(title_bn)
            for pt in content.get("caption_points", []):
                ref = pt.get("reference", "").strip()
                if ref:
                    banned_hadiths.add(ref)
                pt_title = pt.get("title", "").strip()
                if pt_title:
                    banned_hadiths.add(pt_title)
            for num in re.findall(r'\d+', dup_reason):
                banned_hadiths.add(f"Hadith #{num}")
            past_match = re.search(r"'(.*?)'", dup_reason)
            if past_match:
                banned_hadiths.add(past_match.group(1)[:50])
            last_fail_reason = f"Duplicate topic or Hadith detected: {dup_reason}"
            continue
            
        # Check that Arabic text or authentic Hadith is included
        has_arabic = any(
            (pt.get("arabic") and (pt.get("meaning") or pt.get("pronunciation"))) or
            bool(re.search(r'[\u0600-\u06FF]{4,}', pt.get("arabic", "") + pt.get("hadith", "")))
            for pt in content.get("caption_points", [])
        ) or bool(re.search(r'[\u0600-\u06FF]{4,}', content.get("arabic", "")))

        has_valid_hadiths = bool(content.get("caption_points")) and any(
            bool(pt.get("hadith")) and bool(pt.get("reference"))
            for pt in content.get("caption_points", [])
        )

        if not has_arabic and not has_valid_hadiths:
            logger.warning(f"Attempt {attempt+1}: Generated content is missing mandatory Arabic text or authentic Hadith references! Retrying...")
            last_fail_reason = "MANDATORY: Must include authentic Sahih Hadiths with exact references, and Arabic text with pronunciation and meaning where applicable."
            continue

        # HOOK DIVERSITY & ANTI-MONOTONY VALIDATION
        is_diverse, monotony_reason = check_hook_monotony(content, recent_titles, last_hook_text=last_hook_text)
        if not is_diverse:
            logger.warning(f"Attempt {attempt+1}: Hook monotony check failed: {monotony_reason}. Retrying...")
            last_fail_reason = f"Hook monotony check failed: {monotony_reason}. Target Angle: '{target_angle['name']}'. Ensure Line 1 opens with a relatable human situation/emotion without any Hadith preface."
            continue

        # RULE #1 SUPREME 5-PASS ISLAMIC VERIFICATION ENGINE
        is_accurate, fail_reason, validated_content = verify_and_enforce_islamic_accuracy(content)
        if not is_accurate:
            logger.warning(f"Attempt {attempt+1} REJECTED by Islamic 5-Pass Verifier: {fail_reason}. Retrying...")
            last_fail_reason = f"Islamic Authenticity Check Failed: {fail_reason}. Ensure 100% authentic Sahih Hadith, exact book and number, and zero conflation."
            for pt in content.get("caption_points", []):
                ref = pt.get("reference", "").strip()
                if ref:
                    banned_hadiths.add(ref)
            continue

        # Propagate Hijri event flags before typography check
        if assigned_domain.get("is_hijri_event"):
            content["is_hijri_event"] = True
            content["date_badge"] = assigned_domain.get("date_badge", "")

        # AUTO-REVISION TYPOGRAPHY QUALITY ENGINE (NON-BLOCKING AUTO-REPAIR)
        _, typo_reason, typo_content = revise_and_enforce_hook_typography(content)
        content = typo_content

        # GEMINI BENGALI GRAMMAR, CURIOSITY & ANTI-BROKEN-BANGLA PASS
        from app.quality.bengali_hook_guardian import verify_and_auto_edit_hook_with_gemini
        content = verify_and_auto_edit_hook_with_gemini(content)

        content["slot_key"] = slot_key
        content["episode_number"] = ep_int
        content["episode_bn"] = ep_bn
        if not content.get("series_title"):
            content["series_title"] = f"আজকের আমল • পর্ব {ep_bn}"
        return content

    raise RuntimeError(f"Failed to generate a 100% verified, authentic, non-duplicate Loop Reel after {max_attempts} rigorous checks.")

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

    def _sanitize_bengali_text(t: str) -> str:
        if not t:
            return ""
        replacements = [
            (r'\bneutralize\s*করার\b', 'দূর করার'),
            (r'\bneutralize\b', 'দূর'),
            (r'\bboost\b', 'বৃদ্ধি'),
            (r'\bmindset\b', 'মনোভাব'),
            (r'\bnegative\b', 'নেতিবাচক'),
            (r'\bpositive\b', 'ইতিবাচক'),
            (r'\btrigger\b', 'উত্তেজনা'),
        ]
        for pat, rep in replacements:
            t = re.sub(pat, rep, t, flags=re.IGNORECASE)
        return t

    # SERIES BRANDING & HOOK HEADER
    caption = f"✨ {series_title} ✨\n"
    hook_parts = [data.get(k, "").strip() for k in ["line_1", "line_2", "line_3", "line_4"] if data.get(k)]
    if hook_parts:
        hook = " ".join(hook_parts)
    else:
        hook = title_bn
    hook = hook.rstrip(' :➔')
    hook = _sanitize_bengali_text(hook)
    caption += hook + " 🤲\n\n"

    bn_nums = ["১", "২", "৩", "৪", "৫"]
    for idx, pt in enumerate(pts):
        num_str = pt.get("number") or (bn_nums[idx] if idx < len(bn_nums) else str(idx + 1))
        title = _sanitize_bengali_text(pt.get("title", "").strip().replace("ফলাফল", "আমলের শিক্ষা ও ফযিলত"))
        hadith = _sanitize_bengali_text(pt.get("hadith", "").strip())
        arabic = pt.get("arabic", "").strip()
        pron = pt.get("pronunciation", "").strip()
        meaning = pt.get("meaning", "").strip()
        ref = pt.get("reference", "").strip()
        note = pt.get("note", "").strip()

        if title:
            caption += f"{num_str}. {title}:\n"
        elif hadith or arabic:
            caption += f"{num_str}. আমল:\n"

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

        if note:
            caption += f"*(উল্লেখ্য: {note})*\n"

        caption += "\n"

    # PSYCHOLOGY-DRIVEN ENGAGEMENT CTA (Identity Trigger + Foot-in-the-Door + Loss Aversion)
    caption += (
        "📌 আজকের এই আমলটি 🔖 Save করে রাখুন — যেন ভুলে না যান!\n"
        "👇 আপনি কি এই আমলটি আগে জানতেন? কমেন্টে জানান!\n"
        "🤍 প্রিয় একজনকে Tag করে জানিয়ে দিন — "
        "রাসূলুল্লাহ (ﷺ) বলেছেন: 'যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।' [সহীহ মুসলিম: ১৮৯৩] 🌿\n\n"
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

    # 1. Background image selection: Guaranteed non-repeating across recent videos from 16 certified 8K scenes
    from app.history import get_unique_background
    import shutil
    bg_path = os.path.join(temp_dir, "background.jpg")
    chosen_bg = get_unique_background()
    if chosen_bg and os.path.exists(chosen_bg):
        shutil.copyfile(chosen_bg, bg_path)
        logger.info(f"🎨 Non-repeating 8K background deployed for Loop Reel: {os.path.basename(chosen_bg)}")
    else:
        from app.quality.vision_guardian import get_certified_safe_fallback
        get_certified_safe_fallback(bg_path)

    # 2. Authentic Quran Audio with 30-Video Anti-Repetition Guarantee & Topic Alignment
    topic_keywords = f"{content.get('title_bn', '')} {content.get('theme', '')} {content.get('line_1', '')} {content.get('line_2', '')}"
    audio_path = get_or_download_quran_audio(topic_text=topic_keywords, duration=8.0)

    # 3. Build ASS Subtitle matching Reference Post (Top Series Badge, Golden Highlights, Caption CTA, Follow Trigger)
    series_badge = content.get("series_title", f"আজকের আমল • পর্ব {content.get('episode_bn', '১')}")
    # Inject temporal urgency: "আজকের" triggers FOMO (Zeigarnik Effect)
    series_badge = series_badge.replace("দৈনন্দিন সহীহ আমল", "আজকের আমল")
    if not series_badge.startswith("✦"):
        series_badge = f"✦ {series_badge} ✦"
    series_badge = sanitize_text_for_ass(series_badge)

    l1 = content.get("line_1", "").strip()
    l2 = content.get("line_2", "").strip()
    l3 = content.get("line_3", "").strip()
    l4 = content.get("line_4", "").strip()

    # Dynamic Curiosity-Bridge CTA (from LLM) or High-Urgency Fallbacks (Zero emojis to prevent tofu boxes)
    import random as _rnd
    raw_cta = content.get("caption_cta")
    if not raw_cta or len(raw_cta.strip()) < 5:
        _CTA_HOOKS = [
            "☞ পুরো হাদিস ও গোপন আমলটি ক্যাপশনে দেখুন ➔",
            "☞ দলিলসহ সঠিক নিয়ম ক্যাপশনে পড়ুন ➔",
            "☞ ৯৯% মানুষ এটা জানেন না ➔ ক্যাপশনে দেখুন",
            "☞ না জানলে বড় সওয়াব মিস করবেন ➔ ক্যাপশনে",
            "☞ সহীহ হাদিস নম্বরসহ ক্যাপশনে পড়ুন ➔",
        ]
        raw_cta = _rnd.choice(_CTA_HOOKS)
    caption_cta_text = sanitize_text_for_ass(raw_cta)
    
    hw_list = content.get("highlight_words", ["৩টি আয়াত", "আল্লাহ", "রক্ষা করবেন"])
    clean_lines = revise_and_balance_hook_lines(l1, l2, l3, l4)
    full_hook_text = "\\N".join([l for l in clean_lines if l])
    full_hook_text = sanitize_text_for_ass(full_hook_text)
    
    # Apply Vibrant Golden/Yellow highlighting (&H002BD5FF&) to keywords
    GOLD_COLOR = "&H002BD5FF&"
    WHITE_COLOR = "&H00FFFFFF&"
    
    # Sort hw_list by longest string first so longer phrases match before substrings
    hw_list = sorted(hw_list, key=len, reverse=True)
    
    for hw in hw_list:
        hw_clean = sanitize_text_for_ass(hw.strip())
        if not hw_clean:
            continue
        if hw_clean in full_hook_text:
            full_hook_text = full_hook_text.replace(hw_clean, f"{{\\c{GOLD_COLOR}}}{hw_clean}{{\\c{WHITE_COLOR}}}", 1)

    ass_path = os.path.join(temp_dir, "overlay.ass")
    fonts_dir = os.path.abspath("app/assets/fonts").replace("\\", "/")
    fonts_dir_escaped = fonts_dir.replace(":", "\\:")

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SeriesBadge,Kalpurush,42,&H0015CCFA&,&H000000FF,&H00000000,&HB0000000,0,0,0,0,100,100,0,0,1,3.4,2.0,8,60,60,200,1
Style: MainHook,Kalpurush,56,&H00FFFFFF&,&H000000FF,&H00000000,&HC0000000,0,0,0,0,100,100,0,0,1,4.2,2.6,5,50,50,0,1
Style: CaptionCTA,Kalpurush,44,&H0015CCFA&,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,3.0,1.8,2,50,50,420,1
Style: FollowTrigger,Kalpurush,32,&H00E0E8F0&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2.4,1.4,2,50,50,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:08.00,SeriesBadge,,0,0,0,,{{\\fnKalpurush\\fs42\\c{GOLD_COLOR}}}{series_badge}
Dialogue: 0,0:00:00.00,0:00:08.00,MainHook,,0,0,0,,{{\\fnKalpurush\\fs56\\c{WHITE_COLOR}}}{full_hook_text}
Dialogue: 0,0:00:00.00,0:00:08.00,CaptionCTA,,0,0,0,,{{\\fnKalpurush\\fs44\\c{GOLD_COLOR}}}{caption_cta_text}{{\\c{WHITE_COLOR}}}
Dialogue: 0,0:00:00.00,0:00:08.00,FollowTrigger,,0,0,0,,{{\\fnKalpurush\\fs32\\c{WHITE_COLOR}}}প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য Follow করুন ➔ @dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    rel_ass = os.path.relpath(ass_path).replace("\\", "/")
    ass_escaped = rel_ass.replace(":", "\\:")
    sub_filter = f"subtitles='{ass_escaped}':fontsdir='{fonts_dir_escaped}'"

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
        "-vf", sub_filter,
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
        # Cosine ease for organic, buttery-smooth cinematic push-in
        p_eased = 0.5 * (1.0 - math.cos(math.pi * p))
        current_scale = 1.0 + (zoom_total * p_eased)
        
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
        
    # Rotating Pinned Comment — Foot-in-the-Door Psychology (easy 1-word action first → then share)
    import random as _rnd2
    _PINNED_COMMENTS = [
        (
            "আপনি কি এই আমলটি আগে জানতেন? 👇\n"
            "কমেন্টে লিখুন: 'জানতাম ✅' অথবা 'জানতাম না ❌'\n\n"
            "উপকার হলে প্রিয় একজনকে Tag করুন 🤍\n"
            "রাসূলুল্লাহ (ﷺ) বলেছেন: 'যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।' [সহীহ মুসলিম: ১৮৯৩] 🌿"
        ),
        (
            "এই আমলটি কি আপনি নিয়মিত করেন? 👇\n"
            "কমেন্টে লিখুন: 'করি ✅' অথবা 'আজ থেকে শুরু করব 🤲'\n\n"
            "একজন প্রিয়জনকে Tag করে জানিয়ে দিন 🤍"
        ),
        (
            "সবচেয়ে কাছের মানুষটিকে এটা জানাতে এখনই Tag করুন 👇🤍\n\n"
            "রাসূলুল্লাহ (ﷺ) বলেছেন: 'যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।' [সহীহ মুসলিম: ১৮৯৩] 🌿"
        ),
        (
            "এই হাদিসটি পড়ে আপনার মনে প্রথম কী অনুভূতি হলো? 👇\n"
            "একটি শব্দে কমেন্টে লিখুন 🤍\n\n"
            "পরবর্তীতে আমল করতে রিলটি 🔖 Save করে রাখুন।"
        ),
    ]
    pinned_comment = _rnd2.choice(_PINNED_COMMENTS)

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
    hook_str = content.get("line_1", "").strip()
    full_title_for_history = f"[পর্ব {content.get('episode_bn', '')}] {content.get('title_bn', '')} | Hook: {hook_str}"
    record_payload = {
        "id": f"loop_{content.get('slot_key', 'slot')}_{int(time.time())}",
        "title": full_title_for_history,
        "source": "loop_reel_series"
    }
    _supabase_insert(record_payload)
    from app.history import record_video_history
    record_video_history(full_title_for_history, "loop_reel", content.get("line_1", ""))
    logger.info(f"Saved Loop Reel Episode {content.get('episode_bn', '')} to history: '{content.get('title_bn')}'")

    logger.info("=== LOOP REEL PIPELINE COMPLETED SUCCESSFULLY ===")
    return True

if __name__ == "__main__":
    import sys
    slot = sys.argv[1] if len(sys.argv) > 1 else None
    run_loop_reel_pipeline(slot)
