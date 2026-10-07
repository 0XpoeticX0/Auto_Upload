"""
app/quality/bengali_hook_guardian.py
====================================
Gemini Bengali Grammar, Natural Phrasing & Curiosity Hook Guardian.
Enforces:
1. Zero Broken Bengali: Eliminates word repetitions, awkward run-on phrases, and grammatical errors.
2. Pure Curiosity Hook (Open Loop): Strictly forbids preaching/lecturing on screen ('চলুন', 'করুন', 'মানুন').
3. Auto-Edit via Gemini: If any flaw is detected, Gemini rewrites the hook in-place into natural,
   commanding, high-curiosity Bengali lines matching the certified standard.
"""

import re
from typing import Tuple, Dict, Any
from app.llm.provider import extract_json
from app.logger import logger


BANNED_PREACHY_WORDS = [
    r'সামলে\s*চলুন',
    r'হেফাজত\s*করুন',
    r'আমলটি\s*করুন',
    r'মিশে\s*চলুন',
    r'মেনে\s*চলুন',
    r'ভালো\s*হোন',
    r'সবর\s*করুন'
]


def detect_rule_based_flaws(line_1: str, line_2: str, line_3: str = "") -> Tuple[bool, list[str]]:
    """Fast deterministic rule-based pre-check for broken grammar or preachy wording."""
    issues = []
    combined = f"{line_1} {line_2} {line_3}".strip()
    
    # 1. Check preachy words
    for pat in BANNED_PREACHY_WORDS:
        if re.search(pat, combined):
            issues.append(f"Preachy imperative found ('{pat}'). Must pose a curiosity hook, not a sermon.")
            
    # 2. Check duplicate phrases in same line (e.g. 'জান্নাতের জিম্মাদার ... জান্নাতের জিম্মাদার' or 'রাসূল ... রাসূল')
    for line in [line_1, line_2, line_3]:
        if not line:
            continue
        words = line.split()
        for i in range(len(words) - 1):
            if words[i] == words[i+1] and len(words[i]) > 2:
                issues.append(f"Repeated consecutive word '{words[i]}' in line: '{line}'")
        # Check repeated 2-word phrase
        for i in range(len(words) - 3):
            if words[i:i+2] == words[i+2:i+4]:
                issues.append(f"Repeated 2-word phrase '{' '.join(words[i:i+2])}' in line: '{line}'")
                
    # 3. Check for obvious broken syntax or missing arrow
    if line_2 and not line_2.endswith('➔') and not (line_3 and line_3.endswith('➔')):
        issues.append("Hook does not end with bridge arrow '➔'.")
        
    return (len(issues) > 0), issues


def verify_and_auto_edit_hook_with_gemini(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submits hook lines to Gemini for rigorous Bengali linguistic evaluation.
    If the Bengali is broken, repetitive, preachy, or lacks curiosity,
    Gemini edits and rewrites it in-place.
    """
    l1 = (content.get("line_1") or "").strip()
    l2 = (content.get("line_2") or "").strip()
    l3 = (content.get("line_3") or "").strip()
    title_bn = (content.get("title_bn") or "").strip()
    hadith_summary = ""
    for pt in content.get("caption_points", []):
        hadith_summary += f"{pt.get('title', '')} {pt.get('hadith', '')} "
    hadith_summary = hadith_summary[:250].strip()

    has_flaws, detected_issues = detect_rule_based_flaws(l1, l2, l3)

    system_prompt = """You are the Senior Bengali Linguistic Editor & Viral Hook Specialist for an authentic Islamic media network.

Your mandate is to review the video on-screen hook lines ('line_1', 'line_2', and optional 'line_3') and ensure:
1. ZERO BROKEN BENGALI:
   - Sentences must be 100% grammatically pristine, natural, and idiomatic everyday spoken Bengali (সহজ ও বিশুদ্ধ মুখের ভাষা).
   - Absolutely NO stuttering or repeated words (e.g., 'রাসূল ... রাসূল', 'জান্নাতের জিম্মাদার ... জান্নাতের জিম্মাদার').
   - Absolutely NO ungrammatical clause mashups (e.g., 'মুখ ও লজ্জাস্থান সামলে চলুন রাসূল জান্নাতের জিম্মাদার').
2. PURE CURIOSITY HOOK (OPEN LOOP):
   - A short reel hook is a CURIOSITY MAGNET, NEVER A SERMON!
   - STRICTLY FORBIDDEN: Preaching or lecturing on screen (e.g., 'সামলে চলুন', 'হেফাজত করুন', 'আমল করুন', 'সবর করুন').
   - STRICTLY FORBIDDEN: Spoiling the whole Hadith answer on screen.
   - The hook must pose a burning question, dramatic dilemma, or shocking contrast that makes opening the caption irresistible.
   - MUST END with the bridge arrow '➔'.
3. APPROVED ARCHETYPE EXAMPLES:
   Line 1: 'মাত্র ২টি অঙ্গ হেফাজত করলে নবীজি (ﷺ)'
   Line 2: 'জান্নাতের জিম্মাদার হওয়ার ঘোষণা দিয়েছিলেন ➔'
   (or with question: 'কেন জান্নাতের জিম্মাদার হওয়ার ঘোষণা দিয়েছিলেন? ➔')

   Line 1: 'যে ব্যক্তি প্রতিদিন এই ছোট ভুলটি করে,'
   Line 2: 'তার সব নেক আমল কি আসমানে ওঠার আগেই মুছে যায়? ➔'

If the given lines already meet this standard, keep them as is and return 'is_perfect': true.
If the lines have ANY broken Bengali, repetition, preaching, or lack curiosity, REWRITE THEM IN-PLACE into 2 punchy lines ('line_1' and 'line_2') with appropriate 'highlight_words'.

Output ONLY valid JSON:
{
    "is_perfect": true/false,
    "critique": "brief explanation of quality or issues found",
    "line_1": "clean line 1 (4-8 words)",
    "line_2": "clean line 2 ending with ➔",
    "line_3": "",
    "caption_cta": "☞ সহীহ হাদিস নম্বরসহ ক্যাপশনে পড়ুন ➔",
    "highlight_words": ["key word 1", "key word 2"]
}"""

    user_prompt = f"""Evaluate and verify this on-screen hook:
Title: {title_bn}
Hadith Theme: {hadith_summary}
Line 1: {l1}
Line 2: {l2}
Line 3: {l3}
Known detected rule issues: {detected_issues}

Ensure 100% natural, grammatically correct Bengali with powerful curiosity!"""

    try:
        result = extract_json(system_prompt, user_prompt, max_tokens=800)
        if isinstance(result, dict) and result.get("line_1") and result.get("line_2"):
            if not result.get("is_perfect", False) or has_flaws:
                logger.info(f"✨ Gemini Hook Guardian Auto-Edited Hook: {result.get('critique', 'Revised for curiosity & grammar')}")
                logger.info(f"   Old: {l1} / {l2}")
                logger.info(f"   New: {result['line_1']} / {result['line_2']}")
                
                content["line_1"] = result["line_1"].strip()
                content["line_2"] = result["line_2"].strip()
                if result.get("line_3"):
                    content["line_3"] = result["line_3"].strip()
                elif "line_3" in content:
                    del content["line_3"]
                if result.get("highlight_words"):
                    content["highlight_words"] = result["highlight_words"]
                if result.get("caption_cta"):
                    content["caption_cta"] = result["caption_cta"]
            else:
                logger.info("✅ Hook verified: 100% natural Bengali and high-curiosity standard passed.")
        else:
            logger.warning("Gemini Hook Guardian returned unparseable response, falling back to deterministic sanitizer.")
    except Exception as e:
        logger.warning(f"Gemini Hook Guardian error: {e}. Keeping sanitized lines.")

    return content
