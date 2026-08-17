import random
import re
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_recent_facebook_posts

POST_CATEGORIES = [
    {
        "key": "daily_life",
        "name": "Daily Life: What is Halal and Haram",
        "description": "Everyday Islamic ethics, dealings, speech, modesty, business, rights of family & neighbors."
    },
    {
        "key": "dua_cures",
        "name": "Dua Cures & Spiritual Remedies",
        "description": "Authentic Prophetic Duas for anxiety, illness, protection from evil eye, forgiveness, and morning/evening adhkar."
    },
    {
        "key": "heart_softeners",
        "name": "Heart Softeners (Raqaa'iq)",
        "description": "Repentance (Tawbah), crying in secret out of love & fear of Allah, sincerity, finding peace in worship, Allah's vast mercy."
    },
    {
        "key": "general_knowledge",
        "name": "Authentic General Islamic Knowledge",
        "description": "Fascinating authentic details from Quran & Sunnah about Angels, the Throne, Jannah, the Unseen world, and Prophetic miracles."
    }
]

def generate_post_content(language: str = "english") -> dict:
    """
    Generates authentic Islamic photo card content + Facebook/Instagram caption.
    Supports both English (verbatim Sunnah.com) and Bangla (with pure Arabic quote).
    """
    selected_category = random.choice(POST_CATEGORIES)
    logger.info(f"Selected category for Post ({language.upper()}): {selected_category['name']}")
    
    # Query past posts to strictly prevent repeating content for 30+ days
    recent_posts = get_recent_facebook_posts(limit=40)
    past_topics_text = ""
    if recent_posts:
        past_topics_list = [f"- Reference: {dict(p).get('reference', '')} | Quote: {dict(p).get('quote', '')[:60]}..." for p in recent_posts]
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list)

    if language == "bangla":
        system_prompt = f"""You are an expert Islamic scholar and content creator specializing in authentic, viral Islamic reflection posts in Bangla (বাংলা).
Category: {selected_category['name']} — {selected_category['description']}

CRITICAL REQUIREMENTS:
1. AUTHENTICITY & SAHABI ATTRIBUTION:
   - Must be 100% authentic from Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, or the Holy Quran.
   - For Hadiths: Always include the Sahabi narrator in the header (e.g. 'আবু হুরায়রা (রাঃ) থেকে বর্ণিত, রাসূলুল্লাহ (ﷺ) বলেছেন:').
   - For Quranic Ayahs: 'মহান আল্লাহ তা'আলা পবিত্র কুরআনে এরশাদ করেছেন:'.

2. QUOTE ACCURACY:
   - Provide the exact Arabic text with full Tashkeel/Harakat.
   - Provide the exact, accurate Bangla translation.
   - Select 2-3 key impactful phrases for highlight_phrases (which will be rendered in golden amber #EBAF41).

3. SHORT & PUNCHY EXPLANATION (ব্যাখ্যা):
   - Keep the explanation to EXACTLY 1-2 SHORT, COMFORTING SENTENCES (Maximum 20-30 words).

4. CAPTION FOR SOCIAL MEDIA:
   - Engaging Bengali title + Sahabi narrator + Arabic quote + English transliteration + Bangla meaning + reflection + verified citation + hashtags (#IslamicPost #BanglaHadith #DailyDosOfIslam).

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON):
{{
    "language": "bangla",
    "category": "{selected_category['key']}",
    "title": "পোস্টের শিরোনাম (বাংলা)",
    "header": "আবু হুরায়রা (রাঃ) থেকে বর্ণিত, রাসূলুল্লাহ (ﷺ) বলেছেন:",
    "arabic_quote": "مَنْ صَلَّى عَلَيَّ وَاحِدَةً صَلَّى اللَّهُ عَلَيْهِ عَشْرًا",
    "quote": "‘যে ব্যক্তি আমার ওপর একবার দরুদ পাঠ করবে, আল্লাহ তার ওপর দশবার রহমত বর্ষণ করবেন।’",
    "bangla_quote": "‘যে ব্যক্তি আমার ওপর একবার দরুদ পাঠ করবে, আল্লাহ তার ওপর দশবার রহমত বর্ষণ করবেন।’",
    "highlight_phrases": ["একবার দরুদ পাঠ করবে", "দশবার রহমত বর্ষণ করবেন"],
    "explain_title": "ব্যাখ্যা:",
    "explanation": "কঠিন সময়ে রাসূলুল্লাহ (ﷺ)-এর ওপর বেশি বেশি দরুদ পড়ুন; আল্লাহ আপনার জীবনে রহমতের দরজা খুলে দেবেন।",
    "reference": "সহীহ মুসলিম: ৪০৮",
    "caption": "✨ রাসূলুল্লাহ (ﷺ)-এর ওপর দরুদ পাঠের অপার মহিমা ✨\\n\\nআবু হুরায়রা (রাঃ) থেকে বর্ণিত, রাসূলুল্লাহ (ﷺ) বলেছেন:\\n\\n'مَنْ صَلَّى عَلَيَّ وَاحِدَةً صَلَّى اللَّهُ عَلَيْهِ عَشْرًا'\\n(Man salla 'alayya wahidatan salla Allahu 'alayhi 'ashran)\\n\\n‘যে ব্যক্তি আমার ওপর একবার দরুদ পাঠ করবে, আল্লাহ তার ওপর দশবার রহমত বর্ষণ করবেন।’\\n\\n📖 রেফারেন্স: সহীহ মুসলিম (৪০৮)\\n\\n🌿 শিক্ষা:\\nআমরা যখন জীবনে পেরেশানি বা বরকতের অভাব অনুভব করি, তখন বেশি বেশি দরুদ পাঠ করা উচিত।\\n\\n💬 কমেন্টে ‘আল্লাহুম্মা সাল্লি আলা মুহাম্মদ’ লিখুন এবং শেয়ার করে সাদাকায়ে জারিয়ার অংশ হোন।\\n\\n#IslamicPost #DailyDosOfIslam #BanglaHadith #IslamicReminder",
    "image_prompt": "moody dark atmospheric ancient mosque archway with soft golden sunset rays, photorealistic 8k, serene, cinematic, empty, no humans"
}}
"""
        user_prompt = "Generate a fresh authentic Islamic post in Bangla with Sahabi narrator, Arabic quote with Tashkeel, Bangla translation, and concise reflection."
    else:
        system_prompt = f"""You are an expert Islamic scholar and content creator crafting authentic, beautiful reflection cards and captions for Facebook and Instagram.
Category: {selected_category['name']} — {selected_category['description']}

STRICT SACRED RULES FOR HADITH & NARRATOR ATTRIBUTION:
1. SAHABI NARRATOR ATTRIBUTION:
   - For Hadith, the "header" MUST include the authentic Sahabi narrator who reported it from the Prophet (peace be upon him):
     * Examples:
       - "Jabir ibn 'Abdullah reported that the Prophet (peace be upon him) said:"
       - "Abu Hurairah reported: The Messenger of Allah (peace be upon him) said:"
       - "'Aisha (may Allah be pleased with her) reported:"
       - "Ibn 'Abbas reported that the Prophet (peace be upon him) said:"
   - For Quranic Ayahs: "Allah says in the Quran:" or "Allah ﷻ says:".

2. EXACT VERBATIM TRANSLATION (DO NOT CHANGE OR PARAPHRASE):
   - The "quote" MUST be the EXACT, OFFICIAL WORD-FOR-WORD English translation as found on Sunnah.com / Darussalam / Sahih International.
   - STRICTLY NEVER modernize, paraphrase, rewrite, summarize, or alter ANY words of the Hadith text. Keep it 100% faithful to the official recorded translation.

3. 100% AUTHENTICITY:
   - Must be from Sahih al-Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, Sunan an-Nasa'i, Sunan Ibn Majah, Riyad as-Salihin, or the Holy Quran.
   - You MUST provide the exact collection name and Hadith/Ayah number in the "reference" field (e.g. "Sunan Abi Dawud: 4727", "Sahih al-Bukhari: 6407", "Surah Al-Baqarah: 286").

4. HIGHLIGHTS & EXPLANATION:
   - "highlight_phrases": 1-3 key punchy phrases that will be colored in gold on the card.
   - "explanation": 1-2 short, relatable reflection sentences applying the lesson to daily life.

5. CAPTION:
   - Engaging title + Sahabi narrator + exact Hadith quote + explanation + citation + call-to-action + hashtags (#DailyDosOfIslam #IslamicReminder #Hadith).

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON):
{{
    "language": "english",
    "category": "{selected_category['key']}",
    "title": "Short Impactful Title",
    "header": "Jabir b. 'Abd Allah reported that the Prophet (peace be upon him) said:",
    "quote": "‘I have been permitted to tell about one of Allah’s angels who bears the throne that the distance between the lobe of his ear and his shoulder is a journey of seven hundred years.’",
    "highlight_phrases": ["angels who bears the throne", "journey of seven hundred years"],
    "explain_title": "Explain:",
    "explanation": "If a single creation of Allah is this immense, imagine the boundless greatness of the Creator. Place all your trust in Him.",
    "reference": "Sunan Abi Dawud: 4727",
    "caption": "✨ The Immensity of Allah’s Creation ✨\\n\\nJabir b. 'Abd Allah reported that the Prophet (peace be upon him) said:\\n\\n‘I have been permitted to tell about one of Allah’s angels who bears the throne that the distance between the lobe of his ear and his shoulder is a journey of seven hundred years.’\\n\\n📖 Reference: Sunan Abi Dawud (4727)\\n\\n🌿 Reflection:\\nWhen we realize how vast Allah's creation is, our worldly worries become small. Keep your heart attached to the Lord of the heavens and the earth.\\n\\n💬 Comment 'SubhanAllah' and share to inspire others.\\n\\n#DailyDosOfIslam #IslamicReminder #Hadith #SunanAbiDawud #IslamicPost",
    "image_prompt": "vast moody cinematic desert dunes under soft glowing golden dusk sky, atmospheric, 8k, photorealistic, no humans"
}}
"""
        user_prompt = "Generate a fresh authentic Islamic post with Sahabi narrator, exact verbatim Sunnah.com translation, and inspiring reflection."

    data = extract_json(system_prompt, user_prompt, for_posts=True)
    if data and "language" not in data:
        data["language"] = language
    return data
