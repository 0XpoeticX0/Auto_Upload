import random
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_recent_facebook_posts

POST_CATEGORIES = [
    {
        "key": "daily_life",
        "name": "Daily Life: What is Halal and Haram",
        "description": "Everyday Islamic ethics, dealings, relations with in-laws/non-mahrams, speech, modesty, business, rights of family & neighbors."
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

def generate_post_content() -> dict:
    """
    Generates authentic Islamic photo card content + Facebook/Instagram caption with EXACT verbatim Hadith translations from Sunnah.com and Sahabi narrator attribution.
    """
    selected_category = random.choice(POST_CATEGORIES)
    logger.info(f"Selected category for Facebook Post: {selected_category['name']}")
    
    # Query past posts to strictly prevent repeating content for 30+ days
    recent_posts = get_recent_facebook_posts(limit=40)
    past_topics_text = ""
    if recent_posts:
        past_topics_list = [f"- Reference: {dict(p).get('reference', '')} | Quote: {dict(p).get('quote', '')[:60]}..." for p in recent_posts]
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list)

    system_prompt = f"""You are an expert Islamic scholar and content creator crafting authentic, beautiful reflection cards and captions for Facebook and Instagram.
Category: {selected_category['name']} — {selected_category['description']}

STRICT SACRED RULES FOR HADITH & NARRATOR ATTRIBUTION:
1. SAHABI NARRATOR ATTRIBUTION:
   - For Hadith, the "header" MUST include the authentic Sahabi narrator who reported it from the Prophet ﷺ:
     * Examples:
       - "Jabir ibn 'Abdullah reported that the Prophet ﷺ said:"
       - "Abu Hurairah reported: The Messenger of Allah ﷺ said:"
       - "'Aisha (may Allah be pleased with her) reported:"
       - "Ibn 'Abbas reported that the Prophet ﷺ said:"
   - For Quranic Ayahs: "Allah says in the Quran:" or "Allah ﷻ says:".

2. EXACT VERBATIM TRANSLATION (DO NOT CHANGE OR PARAPHRASE):
   - The "quote" MUST be the EXACT, OFFICIAL WORD-FOR-WORD English translation as found on Sunnah.com / Darussalam / Sahih International.
   - STRICTLY NEVER modernize, paraphrase, rewrite, summarize, or alter ANY words of the Hadith text. Keep it 100% faithful to the official recorded translation.

3. 100% AUTHENTICITY:
   - The Hadith MUST be graded Sahih or Hasan from the standard Kutub al-Sittah (Sahih al-Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, Sunan an-Nasa'i, Sunan Ibn Majah) or authentic Quranic Ayah. No weak or unverified narrations.

4. NO REPETITIONS:
   - You must choose a FRESH, UNIQUE Hadith or Ayah that has NOT been used in recent posts.

5. FORMAT OF THE IMAGE CARD:
   - "header": E.g. "Jabir ibn 'Abdullah reported that the Prophet ﷺ said:"
   - "quote": The EXACT, verbatim authentic English translation in single quotes (25-50 words).
   - "highlight_phrases": An array of 1 or 2 core punchline phrases from the quote to be rendered in bold golden amber (#EBAF41).
     * RULE: Must be EXACT substrings that appear word-for-word inside your "quote" field.
   - "explain_title": "Explain:"
   - "explanation": Exactly 2 to 3 simple, warm, heartfelt sentences explaining the practical daily lesson and how it applies to our modern daily lives in easy, relatable words (30-45 words max).
   - "reference": Exact authentic citation matching Sunnah.com (e.g. 'Sunan Abi Dawud: 4727', 'Sahih al-Bukhari: 6474', 'Sahih Muslim: 2202').

6. SOCIAL MEDIA CAPTION:
   - "caption": A captivating caption. Start with a warm relatable hook, include the full narrator and authentic reference, explain the practical reflection simply, encourage readers to save & share, and include 5-8 relevant hashtags (#Islam #Hadith #DailyReminder #Sunnah #IslamicQuotes #Faith #Muslim #Allah).

7. VISUAL BACKGROUND PROMPT:
   - "image_prompt": A moody, atmospheric, cinematic visual description for the background photo (e.g. 'moody ancient stone archway with warm morning sunbeams, dramatic atmospheric shadows, serene quiet ambience, photorealistic, 8k, empty room, cinematic lighting, no humans, no faces').

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON, no markdown outside):
{{
    "category": "{selected_category['key']}",
    "title": "Short title describing the topic",
    "header": "Abu Hurairah reported that the Prophet ﷺ said:",
    "quote": "‘Exact official verbatim translation from Sunnah.com here...’",
    "highlight_phrases": ["exact phrase 1", "exact phrase 2"],
    "explain_title": "Explain:",
    "explanation": "Simple, warm, relatable 2-3 sentence explanation...",
    "reference": "Sunan Abi Dawud: 4727",
    "caption": "Full rich social media caption with hook, reflection, and hashtags...",
    "image_prompt": "moody dark atmospheric hallway with warm sunlight through door, cinematic lighting, 8k, photorealistic, no humans"
}}
"""

    user_prompt = f"Generate an authentic Islamic post card with the Sahabi narrator, the EXACT verbatim English translation from Sunnah.com, and a simple daily explanation for category: {selected_category['name']}."
    
    post_data = extract_json(system_prompt, user_prompt, for_posts=True)
    if not post_data or "quote" not in post_data:
        logger.error("Failed to generate post content from LLM.")
        return None
        
    logger.info(f"Generated Post: '{post_data.get('title')}' | Ref: {post_data.get('reference')}")
    return post_data
