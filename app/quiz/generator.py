import json
from app.llm.provider import extract_json
from app.logger import logger

def generate_quiz_script(recent_questions: list[str] = None, language: str = "en") -> dict | None:
    """
    Generates a 5-Question interactive Islamic Quiz script adhering to strict timing and difficulty progression.
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
  "title": "ইসলামিক জ্ঞান কুইজ #১ ☪️ (৫-এ কত পেলেন?)",
  "hook": {
    "headline": "ইসলামিক জ্ঞান যাচাই করুন! ☪️",
    "sub_text": "💡 সময় বেশি লাগলে ভিডিওটি পজ করুন!",
    "sfx": "whoosh"
  },
  "questions": [
    {
      "number": 1,
      "category": "মৌলিক জ্ঞান",
      "question": "ইসলামের মূল স্তম্ভ কয়টি?",
      "options": ["ক) ৪টি", "খ) ৫টি", "গ) ৬টি"],
      "correct_option": "খ) ৫টি",
      "explanation": "সহীহ বুখারী: ৮ (ইসলাম পাঁচটি স্তম্ভের ওপর প্রতিষ্ঠিত)",
      "question_duration_sec": 8,
      "reveal_duration_sec": 3.5,
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    }
  ],
  "outro": {
    "score_prompt": "৫-এ আপনার স্কোর কত হলো? কমেন্টে জানান! 👇",
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

QUIZ DESIGN & TIMING RULES:
1. SCENE 1: THE HOOK (0 - 4s)
2. 5 QUESTIONS PROGRESSION (Q1 to Q5):
   - Q1: Basic foundation (Five pillars, Shahada, core beliefs)
   - Q2: Daily worship & practices (Salah, fasting, charity, wudu)
   - Q3: Prophets & companions (Sahih Hadith, Seerah facts)
   - Q4: Quranic knowledge (Surah facts, unique verse details)
   - Q5: Thought-provoking Islamic history / Hadith trivia

3. STRICT CONSTRAINTS:
   - Exactly 3 clean options per question.
   - Exactly ONE correct option matching one of the options.
   - Authentic Sahih references only (Sahih Bukhari, Sahih Muslim, Quran Surah:Ayah).
   - Keep question text punchy, clear, and easy to read on mobile.
   - 1-line short explanation/reference on reveal.

4. SCENE 7: OUTRO (Score prompt + Follow CTA)
{avoid_section}

Respond with ONLY valid JSON (no markdown wrapping, no code blocks):"""

    user_prompt = f"Generate a fresh, engaging 5-Question Islamic Quiz Reel script in {language.upper()} with difficulty progression from Q1 to Q5. Follow all structure rules exactly."

    data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not data or "questions" not in data or len(data["questions"]) != 5:
        logger.error("Failed to generate valid 5-question quiz script.")
        return None

    return data
