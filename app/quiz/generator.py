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

    system_prompt = f"""You are an expert viral short-form video producer specializing in high-retention 3-Question interactive Islamic quiz videos for YouTube Shorts, Instagram Reels, and Facebook Reels (Target Duration: ~35 Seconds).

{lang_instruction}

VIRAL 3-QUESTION RETENTION FRAMEWORK (CHOOSE 3 RELATABLE QUESTIONS ACROSS THESE THEMES):

Every video MUST generate EXACTLY 3 simple, highly relatable questions from the following high-engagement categories:

1. DAILY LIFE & SALAH (Everyday Habits):
   - পাঁচ ওয়াক্ত সালাতে মোট ফরজ নামাজ কয় রাকাত? (১৭ রাকাত)
   - দিনে ও রাতে কোন ফরজ সালাতে কেরাত আস্তে পড়তে হয়? (যোহর ও আসর)
   - সালাতের সিজদায় আমরা কোন তাসবীহ পাঠ করি? (সুবহানা রাব্বিয়াল আ'লা)
   - সালাতের রুকুতে কোন তাসবীহ পাঠ করতে হয়? (সুবহানা রাব্বিয়াল আজীম)

2. HALAL VS. HARAM (Everyday Situations):
   - ব্যাংকের ফিক্সড ডিপোজিট বা সুদের টাকা খাওয়া কি হালাল নাকি হারাম? (সম্পূর্ণ হারাম)
   - পণ্য বিক্রির সময় পণ্যের আসল দোষ লুকিয়ে রাখা কি জায়েজ? (হারাম ও প্রতারণা)
   - কারো অনুপস্থিতিতে তার অপ্রিয় সত্য দোষ আলোচনা করাকে কী বলে? (গীবত ও হারাম)

3. MARRIAGE & RELATIONSHIPS (High Comment Drivers):
   - বিয়ের ক্ষেত্রে মোহরানা পরিশোধ করা বরের জন্য কী? (ফরজ ও বাধ্যতামূলক)
   - বিয়ের আগে গায়রে মাহরাম নারী-পুরুষের নির্জনে দেখা করা কি জায়েজ? (সম্পূর্ণ নিষেধ / হারাম)
   - রাসূলুল্লাহ (ﷺ) কার সাথে ভালো ব্যবহারকারীকে সর্বোত্তম বলেছেন? (নিজের স্ত্রীর সাথে)

4. PARENTS & FAMILY (Emotional Shares):
   - পিতা-মাতার মৃত্যুর পর তাদের জন্য সন্তানের কোন কাজটি সদকায়ে জারিয়া? (সন্তানের নেক আমল ও দোয়া)
   - পিতা-মাতার সাথে কেমন আচরণে আল্লাহ কুরআনে 'উফ' বলতেও নিষেধ করেছেন? (রাগ বা বিরক্তি প্রকাশ)

5. BASIC QURAN & PROPHETS (Inspiring Stories):
   - পবিত্র কুরআনের হৃদয় বা 'হার্ট' বলা হয় কোন সূরাকে? (সূরা ইয়াসীন)
   - কুরআনের সবচেয়ে ছোট সূরার নাম কী? (সূরা আল-কাওসার)
   - কোন সূরা ১ বার পড়লে এক-তৃতীয়াংশ কুরআন খতমের সওয়াব? (সূরা আল-ইখলাস)
   - কোন নবীকে মাছের পেট থেকে আল্লাহ রক্ষা করেছিলেন? (হযরত ইউনুস আ.)
   - কোন নবীর জন্য আগুন ফুলবাগান হয়ে গিয়েছিল? (হযরত ইব্রাহিম আ.)
   - ইসলামের প্রথম খলিফা কে ছিলেন? (হযরত আবু বকর রা.)
   - ইসলামের প্রথম শহীদ নারী কে ছিলেন? (হযরত সুমাইয়্যাহ রা.)

CRITICAL FORMATTING RULES:
1. Generate EXACTLY 3 questions (diverse themes per video).
2. Short & Punchy: Keep question text under 9 words.
3. Options: Exactly 3 clean, concise options per question (1-3 words each).
4. Respectful Honorifics: Use "হযরত ... (আ.)", "হযরত ... (রা.)", "নবীজি (সা.)".
{avoid_section}

Respond with ONLY valid JSON (no markdown wrapping, no code blocks):"""

    user_prompt = f"Generate a fresh, high-retention 3-Question Islamic Quiz Reel script in {language.upper()} strictly following the 3-Slot Formula (Q1 Daily Salah/Habit -> Q2 Basic Quran/Dua -> Q3 Beloved Prophet Story). Keep questions short and punchy under 8 words. Return ONLY JSON."

    data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not data or "questions" not in data or len(data["questions"]) != 3:
        logger.error("Failed to generate valid 3-question quiz script.")
        return None

    return data
