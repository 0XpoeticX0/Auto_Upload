import re
import json
from app.llm.provider import extract_json
from app.logger import logger

STOP_WORDS = {
    'কি', 'কী', 'কোন', 'কোনটি', 'কোনটা', 'কত', 'কয়', 'কয়', 'কোথায়', 'কেন', 'কাকে', 'কার',
    'হলো', 'হল', 'হবে', 'আছে', 'হয়', 'হয়েছিল', 'থাকে', 'এর', 'একটি', 'হচ্ছে', 'বলা',
    'নেই', 'না', 'বা', 'ও', 'এবং', 'করা', 'দিনে', 'দিন', 'রাতে', 'রাত', 'আগে', 'পরে',
    'দেওয়া', 'দেয়া', 'রাখা', 'যায়', 'হলে', 'হওয়া', 'ছাড়া', 'জন্য', 'থেকে', 'পর্যন্ত',
    'নাম', 'কীভাবে', 'কিভাবে', 'বলে', 'হয়েছে', 'তাঁর', 'তার', 'নিয়ে', 'নিয়েছিল', 'পারেনি',
    'পর', 'ছিলেন', 'ছিল', 'হয়েছে'
}

COMMON_ISLAMIC_TERMS = {
    'পবিত্র', 'কোরআন', 'কোরআনে', 'কোরআনের', 'সূরা', 'সূরায়', 'সূরার',
    'হযরত', 'নবী', 'নবীর', 'সালাত', 'সালাতে', 'সালাতের', 'নামাজ', 'নামাজে',
    'ইসলাম', 'ইসলামে', 'ইসলামের', 'রাসূলুল্লাহ', 'রাসুলুল্লাহ'
}

BENGALI_SUFFIXES = [
    'দেরকে', 'গুলো', 'গুলি', 'দের', 'য়ের', 'তের', 'খানা', 'খানি',
    'টিতে', 'টাতে', 'টির', 'টার', 'টি', 'টা', 'েরা', 'রা', 'ের', 'তে',
    'কে', 'রে', 'র', 'ে', 'য়'
]

def stem_bengali_word(w: str) -> str:
    """Stems common Bengali noun/verb grammatical suffixes to base lemma."""
    if len(w) <= 3:
        return w
    for sfx in BENGALI_SUFFIXES:
        if w.endswith(sfx) and len(w) - len(sfx) >= 2:
            return w[:-len(sfx)]
    return w

def normalize_bengali(text: str):
    """Normalizes Bengali question text and extracts stemmed content and specific tokens."""
    if not text:
        return "", set(), set()
    cleaned = re.sub(r'^(?:প্রশ্ন\s*[০-৯\d]+[:।\-]?\s*|Q\d+[:.\-]?\s*)', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'[?।,\-–—!\"\'\(\):;]', ' ', cleaned)
    tokens = [w.strip() for w in cleaned.split() if w.strip()]
    content_tokens = set()
    specific_tokens = set()
    
    for t in tokens:
        stemmed = stem_bengali_word(t)
        if stemmed not in STOP_WORDS and len(stemmed) > 1:
            content_tokens.add(stemmed)
            if stemmed not in COMMON_ISLAMIC_TERMS and t not in COMMON_ISLAMIC_TERMS:
                specific_tokens.add(stemmed)
                
    return ' '.join(tokens), content_tokens, specific_tokens

def check_question_duplicate(candidate: str, past_questions: list[str], threshold: float = 0.40) -> tuple[bool, str | None, str]:
    """
    Checks if `candidate` question duplicates, resembles, or shares key intent with ANY question in `past_questions`.
    Uses exact match, substring match, Jaccard token overlap, and stemmed specific concept overlap.
    Returns: (is_duplicate: bool, matched_question: str | None, reason: str)
    """
    if not candidate or not past_questions:
        return False, None, "none"
        
    cand_clean, cand_content, cand_specific = normalize_bengali(candidate)
    if not cand_clean:
        return False, None, "empty"
        
    for past in past_questions:
        if not past:
            continue
        past_clean, past_content, past_specific = normalize_bengali(past)
        
        # 1. Exact match
        if cand_clean == past_clean:
            return True, past, "exact_match"
            
        # 2. Substring match (at least 12 characters to prevent short substring false alarms)
        if len(cand_clean) >= 12 and (cand_clean in past_clean or past_clean in cand_clean):
            return True, past, "substring_match"
            
        # 3. Overall Jaccard similarity on all content tokens
        inter_all = cand_content & past_content
        union_all = cand_content | past_content
        sim_all = len(inter_all) / len(union_all) if union_all else 0.0
        if sim_all >= threshold:
            return True, past, f"jaccard_similarity_{sim_all:.2f}"
            
        # 4. Stemmed specific content tokens overlap (distinctive domain concepts)
        inter_spec = cand_specific & past_specific
        if len(inter_spec) >= 2:
            spec_ratio = len(inter_spec) / max(len(cand_specific), 1)
            if spec_ratio >= 0.35:
                return True, past, f"stemmed_concept_overlap_{inter_spec}"
                
    return False, None, "none"

def check_intra_script_duplicates(questions: list[dict]) -> tuple[bool, str | None]:
    """Ensures none of the 3 questions in the newly generated script overlap with each other."""
    texts = [q.get("question", "").strip() for q in questions if q.get("question")]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            is_dup, _, reason = check_question_duplicate(texts[i], [texts[j]])
            if is_dup:
                return True, f"Q{i+1} duplicates Q{j+1} ({reason})"
    return False, None

def generate_quiz_script(recent_questions: list[str] = None, language: str = "bn", max_retries: int = 5) -> dict | None:
    """
    Generates a 3-Question interactive Islamic Quiz script adhering to the viral 3-Slot Formula.
    Enforces a strict 300-question Supabase history anti-repetition filter with automatic retry loop.
    """
    logger.info(f"Generating 3-Question Islamic Quiz Reel script (language={language}, max_retries={max_retries})...")
    
    avoid_list = list(recent_questions or [])
    avoid_section = ""
    if avoid_list:
        avoid_section = f"\n\n🚫 ABSOLUTE ZERO REPETITION DIRECTIVE (MANDATORY - PAST {len(avoid_list)} QUESTIONS):\nBelow is the complete list of questions/topics ALREADY used in previous videos:\n"
        for q in avoid_list[:300]:
            avoid_section += f"- {q}\n"
        avoid_section += "\nCRITICAL: You MUST NOT generate ANY question, topic, answer, or theme that matches, resembles, or mirrors anything in the list above. Every single question must be 100% FRESH, UNIQUE, and UNUSED.\n"

    if language == "bn":
        lang_instruction = """Generate ALL content strictly in authentic, natural BANGLA (বাংলা).
Options must be labelled with Bengali letters: "ক) ...", "খ) ...", "গ) ...".
Example JSON format:
{
  "title": "৯৯% মানুষ ৩ নম্বর প্রশ্নে আটকে যায়! 🧠 (৩-এ আপনার স্কোর কত?)",
  "hook": {
    "headline": "৯৯% মানুষ ২ ও ৩ নম্বর প্রশ্নে আটকে যায়! 🧠",
    "sub_text": "সততার সাথে ৩-এ আপনার স্কোর কমেন্টে জানান! 👇",
    "sfx": "whoosh"
  },
  "questions": [
    {
      "number": 1,
      "tier": "confidence_builder",
      "category": "সহজ দৈনন্দিন আমল ও মূল ভিত্তি",
      "question": "[একটি সহজ মৌলিক ইসলামিক প্রশ্ন - সর্বোচ্চ ৮-১০ শব্দ]",
      "options": ["ক) [বিকল্প ১]", "খ) [বিকল্প ২]", "গ) [সঠিক উত্তর]"],
      "correct_option": "গ) [সঠিক উত্তর]",
      "explanation": "[সংক্ষিপ্ত প্রামাণিক রেফারেন্স/দলিল - সর্বোচ্চ ১০ শব্দ]",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 2,
      "tier": "debate_misconception",
      "category": "বহুল প্রচলিত ভুল ধারণা ও দৈনন্দিন মাসয়ালা",
      "question": "[একটি বহুল ভুল হওয়া মাসয়ালা বা বিতর্কিত প্রশ্ন - সর্বোচ্চ ৮-১০ শব্দ]",
      "options": ["ক) [সাধারণ মানুষের ভুল ধারণা]", "খ) [সঠিক উত্তর]", "গ) [অন্য একটি বিকল্প]"],
      "correct_option": "খ) [সঠিক উত্তর]",
      "explanation": "[সহীহ হাদিস/কোরআনের রেফারেন্স - সর্বোচ্চ ১০ শব্দ]",
      "debate_prompt": "উত্তর দেখার আগেই কমেন্টে লিখুন!",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 3,
      "tier": "mindblowing_secret",
      "category": "কোরআনের বিস্ময়কর রহস্য ও নবীদের ইতিহাস",
      "question": "[একটি চমকপ্রদ ও গভীর ঐতিহাসিক বা কোরআনিক তথ্য - সর্বোচ্চ ৮-১০ শব্দ]",
      "options": ["ক) [বিকল্প ১]", "খ) [বিকল্প ২]", "গ) [সঠিক উত্তর]"],
      "correct_option": "গ) [সঠিক উত্তর]",
      "explanation": "[সূরা বা হাদিসের প্রামাণ্য রেফারেন্স - সর্বোচ্চ ১০ শব্দ]",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    }
  ],
  "outro": {
    "score_prompt": "সততার সাথে ৩-এ আপনার স্কোর কত হলো কমেন্টে লিখুন! 👇",
    "follow_cta": "প্রতিদিনের বিশুদ্ধ ইসলামিক কুইজের জন্য Follow করে সাথে থাকুন! 🌿",
    "pinned_comment": "৩/৩ কার কার হয়েছে? কমেন্টে 'মাশাআল্লাহ' লিখুন! 👇 আর ২ নম্বর প্রশ্নের উত্তর আপনি কি আগে জানতেন?",
    "sfx": "outro_riser"
  }
}"""
    else:
        lang_instruction = """Generate all text strictly in ENGLISH.
Options must be labelled: "A) ...", "B) ...", "C) ...".
"""

    system_prompt = f"""You are an elite viral short-form video producer specializing in high-engagement, high-comment 3-Question interactive Islamic quiz reels for YouTube Shorts, Instagram Reels, and Facebook Reels.

{lang_instruction}

VIRAL CONTENT PSYCHOLOGY (MANDATORY):
To maximize comments, replays, and algorithmic reach, EVERY video must strictly follow the GOLDEN 3-TIER INTERACTION FORMULA:

1. Q1: THE CONFIDENCE HOOK (Easy Entry — 90%+ hit rate):
   - A widely known, basic Deen/Salah/Quran/Prophets fact that gives the viewer an instant confident "Yes, I know this!" to stop the scroll.
   - Focus on fundamental topics like core pillars, well-known Quranic facts, foundational Islamic history, or famous historical sites.

2. Q2: THE DEBATE & COMMON MISCONCEPTION MAGNET (Massive Comment Driver):
   - A widely misunderstood daily practice, Halal vs. Makruh vs. Haram issue, or common wudu/salah/social etiquette myth where everyday Muslims often argue or hold mistaken beliefs.
   - Crucial: This triggers viewers to rush to the comments section to debate or state their opinion before the answer is revealed!

3. Q3: THE MINDBLOWING PROPHET/QURAN SECRET (Score & Share Driver):
   - An awe-inspiring Quranic miracle, surprising historical event, afterlife detail, or lesser-known Prophet detail that makes viewers say "SubhanAllah", share the video, and comment their final score (e.g. 3/3 or 2/3).

CRITICAL FORMATTING RULES:
1. Question Text: Direct start inquiry only! Keep under 8-10 words. Punchy, clear, everyday Bangla. STRICTLY NEVER include 'প্রশ্ন ১', 'প্রশ্ন ২', 'Question 1', 'Q1:' or any numbering in the question text.
2. Options: Exactly 3 clean options (1-3 words each).
3. Honorifics: Always use "হযরত ... (আ.)", "হযরত ... (রা.)", "রাসূলুল্লাহ (ﷺ)".
4. Pinned Comment: Always generate a friction-free pinned comment prompt that encourages 1-word answers (e.g. 'মাশাআল্লাহ' or '৩/৩').
{avoid_section}

Respond with ONLY valid JSON:"""

    rejected_in_session: list[str] = []
    base_user_prompt = f"Generate a fresh, viral 3-Question Islamic Quiz Reel script in {language.upper()} following the exact 3-tier formula (Q1 Confidence -> Q2 Debate/Misconception -> Q3 Mindblowing Secret). Ensure Q2 is a controversial/common misconception that drives comments. Return ONLY JSON."

    for attempt in range(1, max_retries + 1):
        logger.info(f"Generating quiz script attempt {attempt}/{max_retries}...")
        
        current_user_prompt = base_user_prompt
        if rejected_in_session:
            current_user_prompt += f"\n\nCRITICAL NEGATIVE CONSTRAINTS (Attempt {attempt}):\nThe following questions were REJECTED because they duplicated existing videos. DO NOT REPEAT THEM OR ANY SIMILAR TOPIC:\n"
            for r in rejected_in_session[-10:]:
                current_user_prompt += f"- ❌ REJECTED: {r}\n"
            current_user_prompt += "Pick completely fresh, brand new topics!"

        data = extract_json(system_prompt, current_user_prompt, max_tokens=2500)
        if not data or "questions" not in data or len(data["questions"]) != 3:
            logger.warning(f"Attempt {attempt}: Invalid script JSON structure received. Retrying...")
            continue

        questions = data.get("questions", [])
        
        # Check intra-script duplicates (Q1 vs Q2 vs Q3)
        intra_dup, intra_reason = check_intra_script_duplicates(questions)
        if intra_dup:
            logger.warning(f"Attempt {attempt}: Intra-script duplicate detected ({intra_reason}). Retrying...")
            rejected_in_session.append(f"Internal overlap: {intra_reason}")
            continue

        # Check against Supabase 300 past questions + session rejected
        full_avoid_pool = avoid_list + rejected_in_session
        has_duplicate = False
        duplicate_info = ""

        for q in questions:
            q_text = q.get("question", "").strip()
            is_dup, matched_q, reason = check_question_duplicate(q_text, full_avoid_pool)
            if is_dup:
                has_duplicate = True
                duplicate_info = f"'{q_text}' matched historical '{matched_q}' (Reason: {reason})"
                rejected_in_session.append(q_text)
                logger.warning(f"⚠️ [Attempt {attempt}/{max_retries}] Duplicate question rejected: {duplicate_info}. Retrying fresh script...")
                break

        if not has_duplicate:
            logger.info(f"✅ Successfully generated 3 fresh, unique quiz questions on attempt {attempt}:")
            for q in questions:
                logger.info(f"   - Q{q.get('number')}: {q.get('question')} ({q.get('correct_option')})")
            return data

    logger.error(f"❌ Failed to generate a 100% non-duplicate quiz script after {max_retries} attempts.")
    return None
