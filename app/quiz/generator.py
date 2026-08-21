import json
from app.llm.provider import extract_json
from app.logger import logger

def generate_quiz_script(recent_questions: list[str] = None, language: str = "bn") -> dict | None:
    """
    Generates a 5-Question interactive Islamic Quiz script adhering to the viral 5-Slot Retention Formula.
    """
    logger.info(f"Generating 5-Question Islamic Quiz Reel script (language={language})...")
    
    avoid_section = ""
    if recent_questions:
        avoid_section = "\n\nCRITICAL ANTI-REPEAT RULE:\nBelow is the list of question concepts ALREADY used in previous videos:\n"
        for q in recent_questions[:50]:
            avoid_section += f"- {q}\n"
        avoid_section += "\nYOU MUST NOT COVER ANY QUESTION, THEME, OR ANSWER THAT MATCHES OR CLOSELY MIRRORS ANYTHING IN THE LIST ABOVE!\n"

    if language == "bn":
        lang_instruction = """Generate ALL content strictly in authentic, natural BANGLA (বাংলা).
Options must be labelled with Bengali letters: "ক) ...", "খ) ...", "গ) ...".
Example format:
{
  "title": "ইসলামিক জ্ঞান কুইজ ☪️ (৫-এ আপনার স্কোর কত?)",
  "hook": {
    "headline": "আপনার ইসলামিক জ্ঞান যাচাই করুন! ☪️",
    "sub_text": "💡 সময় বেশি লাগলে ভিডিওটি পজ করুন!",
    "sfx": "whoosh"
  },
  "questions": [
    {
      "number": 1,
      "category": "মৌলিক জ্ঞান",
      "question": "ইসলামের সর্বপ্রথম ও মূল স্তম্ভ কোনটি?",
      "options": ["ক) সালাত", "খ) শাহাদাহ্", "গ) সাওম"],
      "correct_option": "খ) শাহাদাহ্",
      "explanation": "সহীহ বুখারী: ৮ (ইসলাম পাঁচটি স্তম্ভের ওপর প্রতিষ্ঠিত)",
      "question_duration_sec": 8,
      "reveal_duration_sec": 3.5,
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    }
  ],
  "outro": {
    "score_prompt": "আজকের কুইজে আপনার স্কোর ৫-এ কত হলো? কমেন্টে জানান! 👇",
    "follow_cta": "দ্বীনি জ্ঞান বৃদ্ধি করতে আমাদের ফলো করুন! 🌿",
    "duration_sec": 4,
    "sfx": "outro_riser"
  }
}"""
    else:
        lang_instruction = """Generate all text strictly in ENGLISH.
Options must be labelled: "A) ...", "B) ...", "C) ...".
"""

    system_prompt = f"""You are an expert viral short-form video producer specializing in high-retention interactive Islamic quiz videos for YouTube Shorts, Instagram Reels, and Facebook Reels.

{lang_instruction}

VIRAL 5-QUESTION RETENTION BLUEPRINT (MANDATORY STRUCTURE):

Every video MUST follow this exact 5-slot psychological progression to maximize watch time and comments:

• SLOT 1 (Q1: Warm-up & Confidence Hook — Stop the Scroll):
  - Goal: An easy, universally known Islamic fact that gives the viewer an instant confident "Yes!" so they stay hooked.
  - Examples: Core Pillars of Islam (৫টি), Number of daily Fard prayers (৫ ওয়াক্ত), First pillar of Islam (শাহাদাহ্).

• SLOT 2 (Q2: Prophet Stories & Miracles — Narrative Curiosity):
  - Goal: Story-based intrigue about beloved Prophets and their miracles.
  - Examples: Which Prophet built the Kaaba with his son? (ইব্রাহিম আ.), Days Yunus (AS) spent in the whale, Prophet known as Kaleemullah (মুসা আ.), Prophet Nuh's years of Dawah (৯৫০ বছর).

• SLOT 3 (Q3: Quranic Facts & Surah Secrets — Spiritual Intrigue):
  - Goal: "Did You Know?" Quran trivia and misconceptions that spark curiosity.
  - Examples: Which Surah does not begin with Bismillah? (সূরা আত-তাওবাহ), Heart of the Quran (সূরা ইয়াসীন), Surah protecting from grave punishment (সূরা আল-মুলক), Friday Noor Surah (সূরা আল-কাহফ), Total years of Quran revelation (২৩ বছর).

• SLOT 4 (Q4: The Grave, Akhirah & Day of Judgment — High-Stakes Tension):
  - Goal: Solemn, emotional, high-stakes reflection on the Afterlife.
  - Examples: Name of the Angel who will blow the Trumpet (ইসরাফিল আ.), The 2 Angels who question in the grave (মুনকার ও নাকির), Jannah gate reserved exclusively for fasting people (রাইয়ান), Highest level of Jannah (জান্নাতুল ফেরদাউস).

• SLOT 5 (Q5: Challenging Final Boss & Debate Driver — Viral Comments):
  - Goal: A thought-provoking Islamic history fact or Hadith detail that drives viewers to comment their score (5/5 vs 4/5) and discuss.
  - Examples: First person to accept Islam (খাদিজা রা.), First female martyr in Islam (সুমাইয়্যাহ রা.), The daily Dhikr lightest on tongue but heaviest on the scale (সুবহানাল্লাহি ওয়া বিহামদিহী...).

CRITICAL FORMATTING & PHRASING RULES:
1. STRICT SINGLE-TERM OPTIONS:
   - NEVER put bracketed synonyms or translations inside options (e.g. NEVER write "ক) সালাত (নামাজ)", "খ) শাহাদাহ্ (ঈমান)", "গ) সাওম (রোজা)").
   - Write ONLY clean, single concise terms: "ক) সালাত", "খ) শাহাদাহ্", "গ) সাওম" (or "ক) নামাজ", "খ) ঈমান", "গ) রোজা").
   - Absolutely NO parentheses/brackets in options so text-to-speech speaks cleanly.

2. Exactly 3 clean options per question.
3. Exactly ONE correct option matching one of the options verbatim.
4. Authentic Sahih references only (Sahih Bukhari, Sahih Muslim, Quran Surah:Ayah) in the explanation.
5. Keep question text punchy and easy to read in 2 seconds on a mobile screen.
{avoid_section}

Respond with ONLY valid JSON (no markdown wrapping, no code blocks):"""

    user_prompt = f"Generate a fresh, high-retention 5-Question Islamic Quiz Reel script in {language.upper()} strictly following the 5-Slot Progression Blueprint (Q1 Warm-up -> Q2 Prophet Fact -> Q3 Quran Secret -> Q4 Grave/Akhirah -> Q5 Final Boss)."

    data = extract_json(system_prompt, user_prompt, max_tokens=4000)
    if not data or "questions" not in data or len(data["questions"]) != 5:
        logger.error("Failed to generate valid 5-question quiz script.")
        return None

    return data
