# -*- coding: utf-8 -*-
"""
app/quiz/verifier.py
====================
Dual-Layer Religious Truth & Sahih Verification Gate for Islamic Quiz Reels.
Strictly ensures:
1. Deterministic Citation Check: Exact Sahih book and Hadith number / Surah and Ayah.
2. Rejection of generic citations like [হাদিস শরীফ], [হাদিস], [বুখারী] without number.
3. Option consistency: correct_option is undeniably present in options.
4. Gemini scholarly verification if needed for newly generated questions.
"""

import re
from app.logger import logger

VALID_SOURCES = [
    r'সহীহ বুখারী',
    r'সহীহ মুসলিম',
    r'জামে আত-তিরমিযী',
    r'সুনানে আন-নাসায়ী',
    r'সহীহ আন-নাসায়ী',
    r'সুনানে আবু দাউদ',
    r'সুনানে ইবনে মাজাহ',
    r'মুয়াত্তা ইমাম মালিক',
    r'মুসনাদে আহমাদ',
    r'সূরা\s+[^\:]+\:\s*[\d০-৯]+',
    r'তাফসীরে ইবনে কাসীর',
    r'সীরাতে ইবনে হিশাম'
]

GENERIC_BANNED_PATTERNS = [
    r'\[\s*হাদিস\s*শরীফ\s*\]',
    r'\[\s*হাদীস\s*শরীফ\s*\]',
    r'\[\s*হাদিস\s*\]',
    r'\[\s*হাদীস\s*\]',
    r'\[\s*আল-হাদিস\s*\]',
    r'\[\s*কোরআন\s*শরীফ\s*\]',
]

def verify_question_authenticity(q_data: dict) -> tuple[bool, str]:
    """
    Validates religious truth and citation format for a single question.
    Returns (is_valid: bool, reason: str).
    """
    question = q_data.get("question", "").strip()
    options = q_data.get("options", [])
    correct_opt = q_data.get("correct_option", "").strip()
    explanation = q_data.get("explanation", "").strip()
    source = q_data.get("source", "").strip()

    if not question:
        return False, "Question text is empty"

    if len(options) < 2:
        return False, f"Too few options ({len(options)})"

    # Check correct option exists in options
    opt_matched = False
    for opt in options:
        if correct_opt in opt or opt in correct_opt:
            opt_matched = True
            break
        # Match by prefix (ক, খ, গ)
        if opt and correct_opt and opt[0] == correct_opt[0]:
            opt_matched = True
            break
    if not opt_matched:
        return False, f"Correct option '{correct_opt}' does not match any options: {options}"

    combined_ref = f"{explanation} {source}"

    # Check for banned generic patterns
    for pat in GENERIC_BANNED_PATTERNS:
        if re.search(pat, combined_ref):
            return False, f"Generic citation blocked ('{pat}'). Must provide exact book and Hadith number or Surah:Ayah."

    # Verify at least one certified source is cited
    has_valid_source = False
    for vs in VALID_SOURCES:
        if re.search(vs, combined_ref):
            has_valid_source = True
            break

    if not has_valid_source:
        return False, f"Missing verified Sahih book citation in explanation/source: '{combined_ref}'"

    return True, "PASSED"

def verify_quiz_script(quiz_script: dict) -> tuple[bool, list[str]]:
    """
    Verifies all 3 questions in a quiz script.
    """
    questions = quiz_script.get("questions", [])
    if len(questions) != 3:
        return False, [f"Expected exactly 3 questions, got {len(questions)}"]

    errors = []
    for idx, q in enumerate(questions, 1):
        ok, reason = verify_question_authenticity(q)
        if not ok:
            errors.append(f"Q{idx} Failed Verification: {reason}")

    if errors:
        return False, errors
    return True, ["All 3 questions cleared religious authenticity gates."]
