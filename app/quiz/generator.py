# -*- coding: utf-8 -*-
"""
app/quiz/generator.py
=====================
3-Question Rapid-Fire Islamic Quiz Generator.
Engineered upon:
1. 3-Tier Interaction Formula (Q1 Confidence -> Q2 Debate Magnet -> Q3 Mindblowing Secret).
2. Supabase 300-question anti-repetition filter.
3. Certified Sahih Vault (app/quiz/vault.py) + Gemini LLM fallback.
4. Religious truth and citation verification gate (app/quiz/verifier.py).
"""

import os
import re
import json
import random
from app.logger import logger
from app.quiz.vault import CERTIFIED_QUESTIONS
from app.quiz.verifier import verify_question_authenticity, verify_quiz_script

STOP_WORDS = {
    'কি', 'কী', 'কোন', 'কোনটি', 'কোনটা', 'কত', 'কয়', 'কয়', 'কোথায়', 'কেন', 'কাকে', 'কার',
    'হলো', 'হল', 'হবে', 'আছে', 'হয়', 'হয়েছিল', 'থাকে', 'এর', 'একটি', 'হচ্ছে', 'বলা',
    'নেই', 'না', 'বা', 'ও', 'এবং', 'করা', 'দিনে', 'দিন', 'রাতে', 'রাত', 'আগে', 'পরে',
    'দেওয়া', 'দেয়া', 'রাখা', 'যায়', 'হলে', 'হওয়া', 'ছাড়া', 'জন্য', 'থেকে', 'পর্যন্ত',
    'নাম', 'কীভাবে', 'কিভাবে', 'বলে', 'হয়েছে', 'তাঁর', 'তার', 'নিয়ে', 'নিয়েছিল', 'পারেনি',
    'পর', 'ছিলেন', 'ছিল', 'হয়েছে'
}

COMMON_ISLAMIC_TERMS = {
    'পবিত্র', 'কোরআন', 'কোরআনে', 'কোরআনের', 'কুরআন', 'কুরআনে', 'কুরআনের', 'সূরা', 'সূরায়', 'সূরার',
    'হযরত', 'নবী', 'নবীর', 'সালাত', 'সালাতে', 'সালাতের', 'নামাজ', 'নামাজে',
    'ইসলাম', 'ইসলামে', 'ইসলামের', 'রাসূলুল্লাহ', 'রাসুলুল্লাহ'
}

BENGALI_SUFFIXES = [
    'দেরকে', 'গুলো', 'গুলি', 'দের', 'য়ের', 'তের', 'খানা', 'খানি',
    'টিতে', 'টাতে', 'টির', 'টার', 'টি', 'টা', 'েরা', 'রা', 'ের', 'তে',
    'কে', 'রে', 'র', 'ে', 'য়'
]

def stem_bengali_word(w: str) -> str:
    if len(w) <= 3:
        return w
    for sfx in BENGALI_SUFFIXES:
        if w.endswith(sfx) and len(w) - len(sfx) >= 2:
            return w[:-len(sfx)]
    return w

def normalize_bengali(text: str):
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
            
        # 2. Substring match
        if len(cand_clean) >= 12 and (cand_clean in past_clean or past_clean in cand_clean):
            return True, past, "substring_match"
            
        # 3. Jaccard similarity
        inter_all = cand_content & past_content
        union_all = cand_content | past_content
        sim_all = len(inter_all) / len(union_all) if union_all else 0.0
        if sim_all >= threshold:
            return True, past, f"jaccard_{sim_all:.2f}"
            
        # 4. Stemmed specific tokens overlap
        inter_spec = cand_specific & past_specific
        if len(inter_spec) >= 2:
            spec_ratio = len(inter_spec) / max(len(cand_specific), 1)
            if spec_ratio >= 0.35:
                return True, past, f"concept_overlap_{inter_spec}"
                
    return False, None, "none"

def generate_quiz_script(recent_questions: list[str] = None, language: str = "bn", max_retries: int = 5) -> dict | None:
    """
    Selects or generates a 3-Question interactive Islamic Quiz script:
    - Slot 1: Confidence Hook (90%+ hit rate)
    - Slot 2: Debate Misconception Magnet (Massive comments)
    - Slot 3: Mindblowing Secret / Sunnah (Awe & shares)
    
    Guarantees zero repetition against Supabase recent questions and strict Sahih verification.
    """
    logger.info(f"Generating 3-Question Islamic Quiz Reel script (language={language})...")
    avoid_list = list(recent_questions or [])
    
    # ── 1. Check Certified Vault First ────────────────────────────────────────
    t1_pool = [q for q in CERTIFIED_QUESTIONS if q.get("tier") == "confidence_builder"]
    t2_pool = [q for q in CERTIFIED_QUESTIONS if q.get("tier") == "debate_misconception"]
    t3_pool = [q for q in CERTIFIED_QUESTIONS if q.get("tier") == "mindblowing_secret"]

    def filter_available(pool):
        available = []
        for item in pool:
            q_text = item.get("question", "")
            is_dup, _, _ = check_question_duplicate(q_text, avoid_list)
            if not is_dup:
                available.append(item)
        return available

    avail_t1 = filter_available(t1_pool)
    avail_t2 = filter_available(t2_pool)
    avail_t3 = filter_available(t3_pool)

    logger.info(f"Certified Vault Status: Tier 1={len(avail_t1)}/{len(t1_pool)}, Tier 2={len(avail_t2)}/{len(t2_pool)}, Tier 3={len(avail_t3)}/{len(t3_pool)} available.")

    if avail_t1 and avail_t2 and avail_t3:
        q1 = dict(random.choice(avail_t1))
        q2 = dict(random.choice(avail_t2))
        q3 = dict(random.choice(avail_t3))

        q1["number"] = 1
        q1["total_questions"] = 3
        q2["number"] = 2
        q2["total_questions"] = 3
        q3["number"] = 3
        q3["total_questions"] = 3

        script = {
            "title": "৯৯% মানুষ ৩ নম্বর প্রশ্নে আটকে যায়! 🧠 (৩-এ আপনার স্কোর কত?)",
            "hook": {
                "headline": "৯৯% মানুষ ২ ও ৩ নম্বর প্রশ্নে আটকে যায়! 🧠",
                "sub_text": "সততার সাথে ৩-এ আপনার স্কোর কমেন্টে জানান! 👇"
            },
            "questions": [q1, q2, q3],
            "outro": {
                "score_prompt": "সততার সাথে ৩-এ আপনার স্কোর কত হলো কমেন্টে লিখুন! 👇",
                "follow_cta": "প্রতিদিনের বিশুদ্ধ ইসলামিক কুইজের জন্য Follow করে সাথে থাকুন! 🌿",
                "pinned_comment": "৩/৩ কার কার হয়েছে? কমেন্টে 'মাশাআল্লাহ' লিখুন! আর ২ নম্বর প্রশ্নের উত্তর কি আগে জানতেন?"
            }
        }

        # Verify religious accuracy
        is_valid, report = verify_quiz_script(script)
        if is_valid:
            logger.info("✅ Selected 3 certified questions from Sahih Vault with 100% religious verification:")
            for q in script["questions"]:
                logger.info(f"   - Q{q['number']} ({q['category']}): {q['question']} -> {q['correct_option']} [{q.get('source', '')}]")
            return script
        else:
            logger.warning(f"Vault questions failed verification check: {report}")

    # ── 2. LLM Fallback (If vault exhausted or specific generation needed) ────
    try:
        from app.llm.provider import extract_json
    except ImportError:
        logger.error("LLM provider not available and vault has insufficient unused questions.")
        return None

    avoid_block = ""
    if avoid_list:
        avoid_block = f"\n\n🚫 PREVIOUS QUESTIONS ALREADY PUBLISHED ON CHANNEL (TOTAL: {len(avoid_list[:150])}):\n"
        for idx, q in enumerate(avoid_list[:150], 1):
            avoid_block += f"{idx}. {q}\n"

    system_prompt = f"""You are an elite Islamic scholar and viral short-form video producer.
Generate a 3-Question interactive Islamic quiz reel in authentic, natural BANGLA (বাংলা).

VIRAL CONTENT PSYCHOLOGY (3-TIER FORMULA):
1. Q1 (Confidence Hook): 90%+ hit rate easy fundamental deen/salah question.
2. Q2 (Debate Magnet): Widely misunderstood misconception or daily practice that sparks comment debates.
3. Q3 (Mindblowing Secret): Inspiring Quranic miracle, Sunnah reward, or historical fact.

STRICT RELIGIOUS MANDATE:
- Every question MUST include an EXACT verified citation in 'explanation' and 'source' (e.g. সহীহ বুখারী: [নম্বর], সহীহ মুসলিম: [নম্বর], জামে আত-তিরমিযী: [নম্বর], সূরা [নাম]: [আয়াত]).
- STRICTLY ZERO generic citations like '[হাদিস শরীফ]' without book name and number!
- Output ONLY valid JSON:
{{
  "title": "৯৯% মানুষ ৩ নম্বর প্রশ্নে আটকে যায়! 🧠 (৩-এ আপনার স্কোর কত?)",
  "questions": [
    {{
      "number": 1,
      "tier": "confidence_builder",
      "category": "[বিভাগ]",
      "question": "[৮-১০ শব্দের প্রশ্ন]",
      "options": ["ক) ...", "খ) ...", "গ) ..."],
      "correct_option": "ক) ...",
      "explanation": "[সহীহ হাদিস/কুরআনের রেফারেন্সসহ ব্যাখ্যা]",
      "source": "সহীহ বুখারী: [নম্বর]"
    }},
    {{
      "number": 2,
      "tier": "debate_misconception",
      "category": "[বিভাগ]",
      "question": "[প্রশ্ন]",
      "options": ["ক) ...", "খ) ...", "গ) ..."],
      "correct_option": "খ) ...",
      "explanation": "[রেফারেন্সসহ ব্যাখ্যা]",
      "source": "সহীহ মুসলিম: [নম্বর]"
    }},
    {{
      "number": 3,
      "tier": "mindblowing_secret",
      "category": "[বিভাগ]",
      "question": "[প্রশ্ন]",
      "options": ["ক) ...", "খ) ...", "গ) ..."],
      "correct_option": "গ) ...",
      "explanation": "[রেফারেন্সসহ ব্যাখ্যা]",
      "source": "জামে আত-তিরমিযী: [নম্বর]"
    }}
  ]
}}"""

    for attempt in range(1, max_retries + 1):
        logger.info(f"Generating LLM script attempt {attempt}/{max_retries}...")
        prompt = f"Generate 3 fresh questions following the 3-tier formula with exact Sahih Hadith citations.\n{avoid_block}"
        data = extract_json(system_prompt, prompt, max_tokens=2500)
        if not data or "questions" not in data or len(data["questions"]) != 3:
            continue

        # Verify duplicate and authenticity
        is_dup = False
        for q in data["questions"]:
            dup, _, _ = check_question_duplicate(q.get("question", ""), avoid_list)
            if dup:
                is_dup = True
                break

        if is_dup:
            logger.warning(f"Attempt {attempt}: Duplicate question detected against Supabase history. Retrying...")
            continue

        is_valid, report = verify_quiz_script(data)
        if is_valid:
            logger.info(f"✅ Generated script cleared religious authenticity on attempt {attempt}.")
            return data
        else:
            logger.warning(f"Attempt {attempt}: Religious verification failed ({report}). Retrying...")

    logger.error("Failed to generate a certified non-duplicate quiz script.")
    return None
