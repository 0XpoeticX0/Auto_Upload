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
        avoid_section = "\n\n🚫 ABSOLUTE ZERO REPETITION DIRECTIVE (MANDATORY):\nBelow is the complete list of questions/topics ALREADY used in previous videos:\n"
        for q in recent_questions[:100]:
            avoid_section += f"- {q}\n"
        avoid_section += "\nCRITICAL: You MUST NOT generate ANY question, topic, answer, or theme that matches, resembles, or mirrors anything in the list above. Every single question must be 100% FRESH, UNIQUE, and UNUSED.\n"

    if language == "bn":
        lang_instruction = """Generate ALL content strictly in authentic, natural BANGLA (বাংলা).
Options must be labelled with Bengali letters: "ক) ...", "খ) ...", "গ) ...".
Example format:
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
      "category": "সহজ দৈনন্দিন আমল",
      "question": "পাঁচ ওয়াক্ত সালাতে মোট ফরজ নামাজ কয় রাকাত?",
      "options": ["ক) ১৫ রাকাত", "খ) ১৭ রাকাত", "গ) ২০ রাকাত"],
      "correct_option": "খ) ১৭ রাকাত",
      "explanation": "সহীহ বুখারী ও মুসলিম: প্রতিদিন ৫ ওয়াক্তে মোট ১৭ রাকাত ফরজ সালাত।",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 2,
      "tier": "debate_misconception",
      "category": "কমন ভুল ধারণা ও মাসয়ালা",
      "question": "দাঁড়িয়ে পানি পান করা ইসলামের দৃষ্টিতে কী?",
      "options": ["ক) সম্পূর্ণ হারাম", "খ) মাকরুহ (অনুচিত)", "গ) মোস্তাহাব"],
      "correct_option": "খ) মাকরুহ (অনুচিত)",
      "explanation": "সহীহ মুসলিম: ২০২৪ — নিষেধ এসেছে তবে এটি হারাম নয়, অনুচিত/মাকরুহ।",
      "debate_prompt": "উত্তর দেখার আগেই কমেন্টে লিখুন!",
      "sfx_timer": "clock_tick",
      "sfx_reveal": "correct_bell"
    },
    {
      "number": 3,
      "tier": "mindblowing_secret",
      "category": "কোরআনের রহস্য ও নবীদের ইতিহাস",
      "question": "কোন নবীর মৃত্যুর খবর তাঁর লাঠি ভেঙে পড়ার আগ পর্যন্ত জিনরা জানতে পারেনি?",
      "options": ["ক) হযরত সুলাইমান (আ.)", "খ) হযরত দাউদ (আ.)", "গ) হযরত মুসা (আ.)"],
      "correct_option": "ক) হযরত সুলাইমান (আ.)",
      "explanation": "সূরা সাবা: ১৪ — উইপোকা লাঠি খেয়ে ফেলার পর সুলাইমান (আ.) মাটিতে পড়ে যান।",
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
   - A widely known, basic Deen/Salah/Quran fact that gives the viewer an instant confident "Yes, I know this!" to stop the scroll.
   - Examples: পবিত্র কোরআনের সবচেয়ে বড় সূরা (আল-বাকারা), পাঁচ ওয়াক্তে মোট ফরজ নামাজ কয় রাকাত (১৭ রাকাত), সিজদায় পড়ার তাসবীহ (সুবহানা রাব্বিয়াল আ'লা), কাবা শরীফ কোন দেশে অবস্থিত (সৌদি আরব), প্রথম কোন সূরার আয়াত নাজিল হয় (সূরা আল-আলাক).

2. Q2: THE DEBATE & COMMON MISCONCEPTION MAGNET (Massive Comment Driver):
   - A widely misunderstood daily practice, Halal vs. Makruh vs. Haram issue, or common wudu/salah myth where everyday Muslims often argue or hold mistaken beliefs.
   - Crucial: This triggers viewers to rush to the comments section to debate or state their opinion!
   - Examples:
     * দাঁড়িয়ে পানি পান করা কী? (মাকরুহ/অনুচিত — অনেকে হারাম মনে করে তর্ক করে)
     * কোন কাজটি করলে ওজু ভাঙে না? (নখ বা চুল কাটলে — সমাজে প্রচলিত ভুল বিশ্বাস আছে যে ওজু ভেঙে যায়)
     * ফরজ গোসলে মোট ফরজ কয়টি? (৩টি — অনেকে ৪ বা ৫ বলে ভুল করে)
     * বিয়ের মোহরানা বরের জন্য কী? (ফরজ ও বাধ্যতামূলক — মাফ চাওয়া অনুচিত)
     * জুমার দিনে কোন সূরা পড়া বিশেষ সুন্নত? (সূরা আল-কাহফ)

3. Q3: THE MINDBLOWING PROPHET/QURAN SECRET (Score & Share Driver):
   - An awe-inspiring Quranic miracle, surprising historical fact, or afterlife detail that makes viewers say "SubhanAllah", share the video, and comment their final score (e.g. 3/3 or 2/3).
   - Examples:
     * কোন নবীর মৃত্যুর খবর লাঠি ভেঙে পড়ার আগ পর্যন্ত জিনরা জানতে পারেনি? (হযরত সুলাইমান আ. — সূরা সাবা: ১৪)
     * কোন সাহাবীর ইন্তেকালে আল্লাহর আরশ কেঁপে উঠেছিল? (হযরত সাদ বিন মুয়াজ রা.)
     * জান্নাতে মানুষের বয়স কত বছর থাকবে? (৩৩ বছর — তিরমিযী: ২৫৪৫)
     * কোন সূরায় প্রতি আয়াতেই 'আল্লাহ' নাম রয়েছে? (সূরা আল-মুজাদালাহ)
     * ১ বার পাঠ করলে ১/৩ কোরআন খতমের সওয়াব পাওয়া যায় কোন সূরায়? (সূরা আল-ইখলাস)

CRITICAL FORMATTING RULES:
1. Question Text: Keep under 8-10 words. Punchy, clear, everyday Bangla.
2. Options: Exactly 3 clean options (1-3 words each).
3. Honorifics: Always use "হযরত ... (আ.)", "হযরত ... (রা.)", "রাসূলুল্লাহ (ﷺ)".
4. Pinned Comment: Always generate a friction-free pinned comment prompt that encourages 1-word answers (e.g. 'মাশাআল্লাহ' or '৩/৩').
{avoid_section}

Respond with ONLY valid JSON:"""

    user_prompt = f"Generate a fresh, viral 3-Question Islamic Quiz Reel script in {language.upper()} following the exact 3-tier formula (Q1 Confidence -> Q2 Debate/Misconception -> Q3 Mindblowing Secret). Ensure Q2 is a controversial/common misconception that drives comments. Return ONLY JSON."

    data = extract_json(system_prompt, user_prompt, max_tokens=2500)
    if not data or "questions" not in data or len(data["questions"]) != 3:
        logger.error("Failed to generate valid 3-question quiz script.")
        return None

    # Anti-repeat safety check
    if recent_questions:
        cleaned_prev = [p.replace("?", "").replace("।", "").strip() for p in recent_questions if p]
        for q in data.get("questions", []):
            qt = q.get("question", "").replace("?", "").replace("।", "").strip()
            for prev in cleaned_prev:
                if len(qt) > 5 and (qt == prev or qt in prev or prev in qt):
                    logger.warning(f"Duplicate question prevented: '{qt}' matched historical '{prev}'.")

    return data
