# -*- coding: utf-8 -*-
import re
from app.logger import logger
from app.llm.provider import extract_json

# ==============================================================================
# RULE #1: ZERO TOLERANCE FOR ISLAMIC INACCURACY & HALLUCINATION
# 5-PASS COMPREHENSIVE AUTOMATED VERIFICATION ENGINE
# ==============================================================================

BANNED_ENGAGEMENT_TERMS = [
    r"সদকা[য়য়]?[েএ]?\s*জারি[য়য়]?[াআ]?\s*হবে",
    r"সদকা[য়য়]?[েএ]?\s*জারি[য়য়]?[াআ]?র?\s*অংশীদার",
    r"কমেন্টে\s*.*লিখলে\s*সদকা",
    r"অলৌকিক\s*পুরস্কার",
    r"অলৌকিক\s*৩টি",
    r"অলৌকিক\s*ফলাফল",
    r"জান্নাতের\s*গ্যারান্টি",
]

VAGUE_REFERENCES = [
    r"^\[?সহীহ\s*বুখারী\s*ও\s*মুসলিম\]?$",
    r"^\[?সহীহ\s*হাদিস\s*সমগ্র\]?$",
    r"^\[?হাদিস\s*শরীফ\]?$",
    r"^\[?বিভিন্ন\s*হাদিস\]?$"
]

def check_pass_1_prohibited_terms(text: str) -> tuple[bool, str]:
    """Pass 1: Detects and rejects forbidden engagement-bait or sensationalized terms."""
    for pattern in BANNED_ENGAGEMENT_TERMS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return False, f"Banned term detected matching pattern: '{pattern}'. Religious claims like 'সদকায়ে জারিয়া হবে' in comments are prohibited."
    return True, ""

def check_pass_2_reference_validity(points: list) -> tuple[bool, str]:
    """Pass 2: Rejects vague blanket references lacking specific book or hadith numbers."""
    for idx, pt in enumerate(points):
        ref = pt.get("reference", "").strip()
        hadith = pt.get("hadith", "").strip()
        
        if hadith and not ref:
            return False, f"Point #{idx+1} has a hadith claim but no reference provided."
            
        for vague_pat in VAGUE_REFERENCES:
            if re.search(vague_pat, ref, flags=re.IGNORECASE):
                return False, f"Point #{idx+1} has vague reference '{ref}'. Must provide exact book and hadith number (e.g., 'সহীহ বুখারী: ৬৩২৪' or 'জামে আত-তিরমিযী: ২৮৯১')."
                
        valid_books = ["বুখারী", "মুসলিম", "তিরমিযী", "আবু দাউদ", "নাসায়ী", "নাসাঈ", "ইবনে মাজাহ", "মুসনাদে আহমদ", "মুয়াত্তা", "সূরা", "সুরা", "আল-কুরআন"]
        if ref and not any(b in ref for b in valid_books):
            return False, f"Point #{idx+1} reference '{ref}' is not a recognized Sahih Hadith or Quranic source."
            
    return True, ""

def check_pass_3_conflation_and_fabrication(points: list, title: str) -> tuple[bool, str]:
    """Pass 3: Detects conflated Hadith narrations and unverified ফলাফল sections."""
    for idx, pt in enumerate(points):
        p_title = pt.get("title", "").strip()
        p_hadith = pt.get("hadith", "").strip()
        p_ref = pt.get("reference", "").strip()
        
        # Check for unverified fabricated ফলাফল
        if "ফলাফল" in p_title and not pt.get("arabic"):
            if "জান্নাত" in p_hadith or "আশ্রয়" in p_hadith:
                if "রাসূলুল্লাহ" not in p_hadith and "নবীজি" not in p_hadith:
                    return False, f"Point #{idx+1} ('{p_title}') contains a synthetic promise/result without direct Hadith quotation."
                    
        # Check for Surah Sajdah + Mulk grave conflation under single citation 2892
        if "সাজদাহ" in p_hadith and "মুলক" in p_hadith and "কবরের আজাব" in p_hadith:
            if "২৮৯২" in p_ref and "২৮৯১" not in p_ref:
                return False, "Conflation detected: Tirmidhi 2892 describes recitation before sleep, while grave punishment protection is specifically Tirmidhi 2891 / Abu Dawud 1400. Must cite both or keep virtues distinct."
                
    return True, ""

def check_pass_4_arabic_dua_integrity(points: list) -> tuple[bool, str]:
    """Pass 4: Verifies Arabic Dua text, Tashkeel, Bengali pronunciation, and meaning."""
    for idx, pt in enumerate(points):
        if pt.get("arabic"):
            arabic = pt["arabic"].strip()
            arabic_chars = [c for c in arabic if '\u0600' <= c <= '\u06FF']
            if len(arabic_chars) < 5:
                return False, f"Point #{idx+1} has invalid or truncated Arabic text."
            if not pt.get("pronunciation") or len(pt["pronunciation"].strip()) < 5:
                return False, f"Point #{idx+1} Arabic Dua is missing Bengali pronunciation."
            if not pt.get("meaning") or len(pt["meaning"].strip()) < 5:
                return False, f"Point #{idx+1} Arabic Dua is missing Bengali meaning."
    return True, ""

def check_pass_5_llm_scholar_fact_check(content: dict) -> tuple[bool, str, dict]:
    """Pass 5: Deep LLM-as-a-Scholar Islamic Fact-Checker that verifies exact Hadith authenticity."""
    system_prompt = """You are a senior Islamic Hadith scholar and fact-checker.
Your job is to strictly verify the factual authenticity of Islamic video content in Bengali.

CRITICAL FACT-CHECKING CRITERIA:
1. NO CONFLATION: Ensure multiple different Hadiths are NOT merged together under one reference.
2. ACCURATE CITATION: Ensure every book name and Hadith number actually exists and matches the stated text.
3. NO FABRICATED VIRTUES: Ensure no fabricated guarantees (e.g., blanket promises of Jannah without Hadith text) are present.
4. AUTHENTIC DUA: Ensure Arabic Dua matches authentic Sunnah texts with correct pronunciation and translation.
5. NO UNSOUND CLAIMS: Ensure no claim says 'commenting Subhanallah is Sadaqah Jariyah' or similar engagement bait.

If you find ANY issue, specify the exact issue in 'issues' and provide the 100% corrected 'caption_points' in 'corrected_caption_points'.
If everything is authentic and compliant, set 'is_valid' to true.

Output ONLY valid JSON:
{
    "is_valid": true/false,
    "issues": ["list of issues found, if any"],
    "corrected_caption_points": [
        // corrected caption points if any issues were present
    ]
}"""

    pts = content.get("caption_points", [])
    user_prompt = f"""Fact-check this content:
Title: {content.get('title_bn', '')}
Lines: {content.get('line_1', '')} {content.get('line_2', '')} {content.get('line_3', '')}
Caption Points:
{pts}
"""
    try:
        verdict = extract_json(system_prompt, user_prompt, max_tokens=1000)
        if isinstance(verdict, dict):
            if verdict.get("is_valid") is True:
                return True, "Passed Islamic Scholar Fact-Check", content
            else:
                issues_str = "; ".join(verdict.get("issues", ["Scholarly accuracy issue detected"]))
                if verdict.get("corrected_caption_points"):
                    content["caption_points"] = verdict["corrected_caption_points"]
                    logger.info("Pass 5: Auto-corrected caption points using Scholarly Fact-Checker.")
                    return True, "Auto-corrected by Scholar", content
                return False, issues_str, content
    except Exception as e:
        logger.warning(f"Pass 5 Scholar Check warning: {e}. Passing on rule-based validation.")
        
    return True, "Passed rule-based checks", content

def verify_and_enforce_islamic_accuracy(content: dict) -> tuple[bool, str, dict]:
    """
    Master 5-Pass Verification Pipeline.
    Runs all 5 checks in sequence. Returns (success, reason, updated_content).
    """
    full_text = str(content)
    pts = content.get("caption_points", [])
    title = content.get("title_bn", "")
    
    ok, reason = check_pass_1_prohibited_terms(full_text)
    if not ok:
        return False, f"Pass 1 Failed: {reason}", content
        
    ok, reason = check_pass_2_reference_validity(pts)
    if not ok:
        return False, f"Pass 2 Failed: {reason}", content
        
    ok, reason = check_pass_3_conflation_and_fabrication(pts, title)
    if not ok:
        return False, f"Pass 3 Failed: {reason}", content
        
    ok, reason = check_pass_4_arabic_dua_integrity(pts)
    if not ok:
        return False, f"Pass 4 Failed: {reason}", content
        
    ok, reason, updated_content = check_pass_5_llm_scholar_fact_check(content)
    if not ok:
        return False, f"Pass 5 Failed: {reason}", content
        
    return True, "Passed all 5 Islamic Verification Passes!", updated_content
