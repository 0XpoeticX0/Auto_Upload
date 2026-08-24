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
  "title": "সহজ ৩টি ইসলামিক প্রশ্ন ☪️ (৩-এ আপনার স্কোর কত?)",
  "hook": {
    "headline": "সহজ ৩টি ইসলামিক প্রশ্ন—৩-এ আপনার স্কোর কত? ☪️",
    "sub_text": "💡 সময় বেশি লাগলে ভিডিওটি পজ করুন!",
    "sfx": "whoosh"
  },
  "questions": [
    {
      "number": 1,
      "category": "দৈনন্দিন সালাত ও আমল",
      "question": "পাঁচ ওয়াক্ত সালাতে মোট ফরজ নামাজ কয় রাকাত?",
      "options": ["ক) ১৫ রাকাত", "খ) ১৭ রাকাত", "গ) ২০ রাকাত"],
      "correct_option": "খ) ১৭ রাকাত",
      "explanation": "সহীহ বুখারী ও মুসলিম (প্রতিদিন ১৭ রাকাত ফরজ সালাত)",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 2,
      "category": "কুরআন ও ফজিলত",
      "question": "পবিত্র কুরআনের হৃদয় বা 'হার্ট' বলা হয় কোন সূরাকে?",
      "options": ["ক) সূরা আর-রহমান", "খ) সূরা ইয়াসীন", "গ) সূরা আল-বাকারা"],
      "correct_option": "খ) সূরা ইয়াসীন",
      "explanation": "জামে আত-তিরমিযী: ২৮৮৭ (সূরা ইয়াসীন কুরআনের হৃদয়)",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 3,
      "category": "নবী ও সাহাবীগণ",
      "question": "কোন নবীকে মাছের পেট থেকে আল্লাহ রক্ষা করেছিলেন?",
      "options": ["ক) হযরত আইয়ুব (আ.)", "খ) হযরত ইউনুস (আ.)", "গ) হযরত নূহ (আ.)"],
      "correct_option": "খ) হযরত ইউনুস (আ.)",
      "explanation": "সূরা আল-আম্বিয়া: ৮৭ (হযরত ইউনুস আ.-এর মাছের পেটের দোয়া)",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    }
  ],
  "outro": {
    "score_prompt": "আজকের ৩টি প্রশ্নে আপনার স্কোর কত হলো? কমেন্টে জানান! 👇",
    "follow_cta": "প্রতিদিনের সহীহ ইসলামিক কুইজ ও হাদিসের জন্য Follow করুন! 🌿",
    "sfx": "outro_riser"
  }
}"""
    else:
        lang_instruction = """Generate all text strictly in ENGLISH.
Options must be labelled: "A) ...", "B) ...", "C) ...".
"""

    system_prompt = f"""You are an expert viral short-form video producer specializing in high-retention 3-Question interactive Islamic quiz videos for YouTube Shorts, Instagram Reels, and Facebook Reels (Target Duration: Under 40 Seconds).

{lang_instruction}

CONTENT STYLE & TONE (MANDATORY):
- Use simple, everyday conversational Bangla words (no overly complex, archaic, or bookish terms).
- Focus strictly on relatable, high-engagement topics that everyday Muslims know or care deeply about.

VIRAL 3-QUESTION BREAKDOWN FORMULA (MANDATORY STRUCTURE):

Every video MUST follow this exact 3-tier psychological progression:

• Q1: 1 EASY CONFIDENCE BUILDER (Stop the Scroll):
  - Easy, universally known Daily Salah or basic Deen fact that gives an instant confident "Yes!"
  - Examples: ৫ ওয়াক্তে মোট ফরজ নামাজ কয় রাকাত? (১৭ রাকাত), সিজদায় কোন তাসবীহ পাঠ করি? (সুবহানা রাব্বিয়াল আ'লা), কোন নামাজে কেরাত আস্তে পড়তে হয়? (যোহর ও আসর).

• Q2: 1 RELATABLE HALAL/HARAM OR MARRIAGE/FAMILY (High Engagement & Debate):
  - Everyday Halal vs. Haram, Marriage Sunnah, or Family/Parent relationship.
  - Examples: বিয়ের মোহরানা দেওয়া বরের জন্য কী? (ফরজ ও বাধ্যতামূলক), কারো অনুপস্থিতিতে দোষ চর্চাকে কী বলে? (গীবত ও হারাম), ব্যাংকের সুদের টাকা খাওয়া কী? (সম্পূর্ণ হারাম), রাসূলুল্লাহ (ﷺ) কার সাথে ভালো ব্যবহারকারীকে সর্বোত্তম বলেছেন? (নিজের স্ত্রীর সাথে).

• Q3: 1 THOUGHT-PROVOKING / SURPRISING (Prophet Story / Quran Secret / Score Driver):
  - Inspiring Prophet miracle, Surah secret, or Islamic fact that drives viewers to comment their final score (3/3).
  - Examples: কোন নবীকে মাছের পেট থেকে আল্লাহ রক্ষা করেছিলেন? (হযরত ইউনুস আ.), কুরআনের হৃদয় বলা হয় কোন সূরাকে? (সূরা ইয়াসীন), কোন নবীর জন্য আগুন ফুলবাগান হয়েছিল? (হযরত ইব্রাহিম আ.), ১ বার পড়লে ১/৩ কুরআন খতমের সওয়াব কোন সূরায়? (সূরা আল-ইখলাস).

CRITICAL FORMATTING RULES:
1. Generate EXACTLY 3 questions following the Q1 (Easy) -> Q2 (Relatable Halal/Marriage) -> Q3 (Surprising/Prophet) formula.
2. Short & Punchy: Keep question text under 8-9 words.
3. Options: Exactly 3 clean, concise options per question (1-3 words each).
4. Respectful Honorifics: Use "হযরত ... (আ.)", "হযরত ... (রা.)", "নবীজি (সা.)" in options.
{avoid_section}

Respond with ONLY valid JSON (no markdown wrapping, no code blocks):"""

    user_prompt = f"Generate a fresh, high-retention 3-Question Islamic Quiz Reel script in {language.upper()} following the exact 3-tier formula (Q1 Easy Salah/Habit -> Q2 Relatable Halal/Marriage -> Q3 Surprising Prophet/Quran Secret). Use simple everyday conversational Bangla. Return ONLY JSON."

    data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not data or "questions" not in data or len(data["questions"]) != 3:
        logger.error("Failed to generate valid 3-question quiz script.")
        return None

    return data
