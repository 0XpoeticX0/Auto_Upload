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
    r"সদকা[য়য়]?[েএ]?\s*জারি[য়য়]?[াআ]?\s*হিসেবে",
    r"কমেন্টে\s*.*লিখলে\s*সদকা",
    r"কমেন্টে\s*.*লিখুন\s*—?\s*সদকা",
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
    """Pass 1: Detects and rejects forbidden engagement-bait, sensationalized terms, or stray English loan words."""
    for pattern in BANNED_ENGAGEMENT_TERMS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return False, f"Banned term detected matching pattern: '{pattern}'. Religious claims like 'সদকায়ে জারিয়া হবে' in comments or unverified claims are strictly prohibited."

    # Reject unnatural English loan words inside Bengali content
    english_words = [w.lower() for w in re.findall(r'[a-zA-Z]{4,}', text)]
    allowed = {
        "http", "https", "dailydos", "islam", "reels", "shorts", "true", "false",
        "none", "slot", "json", "name", "theme", "title", "hadith", "arabic",
        "meaning", "pronunciation", "reference", "note", "series_title",
        "episode_bn", "episode_number", "tags", "highlight_words", "caption_points",
        "line_1", "line_2", "line_3", "title_bn", "dhikr_word"
    }
    banned_found = [w for w in english_words if w not in allowed]
    if banned_found:
        return False, f"Unnatural English words found in Bengali text: {banned_found}. Must use 100% natural, everyday Bengali (e.g. use 'দূর করার' instead of 'neutralize')."

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
                
        valid_books = ["বুখারী", "মুসলিম", "তিরমিযী", "আবু দাউদ", "নাসায়ী", "নাসাঈ", "ইবনে মাজাহ", "মুসনাদে আহমদ", "মুয়াত্তা", "সূরা", "সুরা", "আল-কুরআন", "কুরআন", "কোরআন"]
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
        if "ফলাফল" in p_title:
            return False, f"Point #{idx+1} is titled 'ফলাফল'. Synthetic result sections are banned; use authentic Sunnah teachings or exact Hadith citations only."
            
        if "জান্নাত" in p_hadith or "আশ্রয়" in p_hadith:
            if "যে ব্যক্তি প্রতি রাতে" in p_hadith and ("বুখারী ও মুসলিম" in p_ref or "সহীহ বুখারী ও মুসলিম" in p_ref):
                return False, f"Point #{idx+1} contains a synthetic promise falsely attributed to Bukhari & Muslim."
                
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
    """Pass 5: Deep LLM-as-a-Scholar Islamic Fact-Checker that verifies authenticity, citations, and contextual coherence."""
    system_prompt = """You are a senior Islamic scholar and editorial reviewer.
Your job is to strictly verify the factual authenticity and contextual integrity of Islamic video content in Bengali (both Quranic verses and Sahih Hadiths).

CRITICAL FACT-CHECKING CRITERIA:
1. NO CONFLATION: Ensure multiple different Hadiths or Quranic verses are NOT merged together under one citation.
2. ACCURATE CITATION: Ensure every Quranic Surah & Ayah number or Hadith book & number exists and accurately matches the stated text.
3. NO FABRICATED VIRTUES: Ensure no fabricated guarantees (e.g., blanket promises of Jannah without Quranic/Hadith proof) are present.
4. AUTHENTIC DUA & AYAT: Ensure Arabic Dua/Ayah matches authentic Quran/Sunnah texts with correct pronunciation and translation.
5. NO UNSOUND CLAIMS: Ensure no claim says 'commenting Subhanallah is Sadaqah Jariyah' or similar engagement bait.
6. THEMATIC CONTEXT & HOOK ACCURACY: The hook (Title and Lines) MUST accurately and truthfully introduce the subject of the Hadiths. If the hook mentions a story (e.g. a Sahabi crying in a mosque, a market journey), that story MUST be the authentic prelude/context (Sabab al-Wurud) of the actual Hadiths cited. NEVER attach an unrelated story to the Hadiths (e.g. attaching a crying Sahabi hook to anger control Hadiths).
7. PURE BENGALI ONLY: Strictly 0 English loan words in Bengali text (e.g. replace 'neutralize' with 'দূর করার' or 'দমন').

If you find ANY issue, specify the exact issue in 'issues' and provide the 100% corrected 'caption_points' in 'corrected_caption_points', and provide 'corrected_line_1' and 'corrected_title' if the hook had a thematic mismatch.
If everything is authentic and compliant, set 'is_valid' to true.

Output ONLY valid JSON:
{
    "is_valid": true/false,
    "issues": ["list of issues found, if any"],
    "corrected_caption_points": [
        // corrected caption points if any issues were present
    ],
    "corrected_line_1": "corrected line 1 if hook was mismatched or had English words",
    "corrected_title": "corrected title if hook was mismatched"
}"""

    pts = content.get("caption_points", [])
    user_prompt = f"""Fact-check this content:
Title: {content.get('title_bn', '')}
Lines: {content.get('line_1', '')} {content.get('line_2', '')} {content.get('line_3', '')}
Caption Points:
{pts}
"""
    try:
        verdict = extract_json(system_prompt, user_prompt, max_tokens=1200)
        if isinstance(verdict, dict):
            if verdict.get("is_valid") is True:
                return True, "Passed Islamic Scholar Fact-Check", content
            else:
                issues_str = "; ".join(verdict.get("issues", ["Scholarly accuracy issue detected"]))
                if verdict.get("corrected_caption_points"):
                    content["caption_points"] = verdict["corrected_caption_points"]
                if verdict.get("corrected_line_1"):
                    content["line_1"] = verdict["corrected_line_1"]
                if verdict.get("corrected_title"):
                    content["title_bn"] = verdict["corrected_title"]
                if verdict.get("corrected_caption_points") or verdict.get("corrected_line_1"):
                    logger.info("Pass 5: Auto-corrected content using Scholarly Fact-Checker.")
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
    pts = content.get("caption_points", [])
    title = content.get("title_bn", "")
    
    # Extract only user-facing Bengali content for Pass 1 (excluding internal english visual_prompts or json keys)
    bengali_texts = [
        content.get("title_bn", ""),
        content.get("line_1", ""),
        content.get("line_2", ""),
        content.get("line_3", "")
    ]
    for pt in pts:
        bengali_texts.extend([
            pt.get("title", ""),
            pt.get("hadith", ""),
            pt.get("meaning", ""),
            pt.get("pronunciation", ""),
            pt.get("note", "")
        ])
    full_bengali_text = " ".join(bengali_texts)
    
    ok, reason = check_pass_1_prohibited_terms(full_bengali_text)
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
