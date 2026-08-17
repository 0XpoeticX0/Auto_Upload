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
        "description": "Repentance (Tawbah), weeping in secret, crying out of fear of Allah, sincerity, fleeting nature of this world, mercy of Allah."
    },
    {
        "key": "general_knowledge",
        "name": "Authentic General Islamic Knowledge",
        "description": "Fascinating authentic details from Quran & Sunnah about Angels, the Throne, Jannah, the Unseen world, and Prophetic miracles."
    }
]

def generate_post_content() -> dict:
    """
    Generates authentic Islamic photo card content + Facebook caption with strict anti-repetition rules.
    """
    selected_category = random.choice(POST_CATEGORIES)
    logger.info(f"Selected category for Facebook Post: {selected_category['name']}")
    
    # Query past posts to strictly prevent repeating content for 30+ days
    recent_posts = get_recent_facebook_posts(limit=40)
    past_topics_text = ""
    if recent_posts:
        past_topics_list = [f"- Reference: {dict(p).get('reference', '')} | Quote: {dict(p).get('quote', '')[:60]}..." for p in recent_posts]
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list)

    system_prompt = f"""You are an expert Islamic content curator and scholar creating viral, beautiful Facebook image reflection cards and post captions.
Category: {selected_category['name']} — {selected_category['description']}

STRICT REQUIREMENTS:
1. 100% AUTHENTICITY: The Ayah or Hadith MUST be completely authentic from the Quran or Sahih Sunnah (Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami' at-Tirmidhi, Sunan an-Nasa'i, Sunan Ibn Majah). No weak or fabricated claims.
2. NO REPETITIONS: You must choose a FRESH, UNIQUE Hadith or Ayah that has NOT been used in recent posts.
3. FORMAT OF THE IMAGE CARD:
   - "header": E.g. "The Prophet (peace be upon him) said:" or "Allah says in the Quran:".
   - "quote": The exact authentic English translation of the Hadith or Ayah in single quotes. Make it powerful, self-contained, and complete (30-50 words max).
   - "highlight_phrases": An array of 1 or 2 of the MOST IMPORTANT, CORE PUNCHLINES, COMMANDS, OR PROMISES from the quote to be highlighted in bold golden yellow on the image card.
     * Examples of what to highlight:
       - If about modesty: ["Do not be alone with a woman", "The husband's brother is like death"]
       - If about forgiveness: ["forgiven all his sins", "even as much as the foam of the sea"]
       - If about trials: ["greatest reward comes with the greatest trial", "When Allah loves a people He tests them"]
       - If about patience: ["Allah is with the patient"]
     * RULE: NEVER highlight small random filler words. Highlight the entire core action, key ruling, or striking promise (3 to 6 consecutive words).
     * The words in "highlight_phrases" MUST appear word-for-word inside your "quote" field.
   - "explain_title": "Explain:"
   - "explanation": Exactly 2 to 3 concise, clear, powerful sentences explaining the deeper wisdom, why this was said, and how it directly applies to modern daily life (35-55 words max).
   - "reference": Exact authentic citation (e.g. 'Sahih Muslim: 2172 a', 'Sahih al-Bukhari: 6306', 'Surah Al-Baqarah: 153').
4. FACEBOOK CAPTION:
   - "caption": A gripping, thought-provoking Facebook post caption. Start with a vivid storytelling hook ("Imagine sitting in the warm shade of Madinah...", "Have you ever wondered why..."). Give relatable context, reflect deeply on the lesson, encourage readers to save & share, and include 5-8 relevant hashtags (#Islam #Hadith #DailyReminder #Sunnah #IslamicQuotes #Faith #Muslim).
5. VISUAL BACKGROUND PROMPT:
   - "image_prompt": A dramatic, atmospheric, cinematic visual description for the background photo (e.g. 'moody ancient doorway with sunlight beaming in, warm golden ambient light, shadows, mysterious atmosphere, photorealistic, 8k, empty room, cinematic lighting, no humans, no faces').

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON, no markdown outside):
{{
    "category": "{selected_category['key']}",
    "title": "Short title describing the topic",
    "header": "The Prophet ﷺ said:",
    "quote": "‘Exact authentic quote text here...’",
    "highlight_phrases": ["key phrase 1", "key phrase 2"],
    "explain_title": "Explain:",
    "explanation": "Clear 2-3 sentence explanation here...",
    "reference": "Sahih Muslim: 2172 a",
    "caption": "Full rich Facebook post caption with hook, reflection, and hashtags...",
    "image_prompt": "moody dark atmospheric hallway with warm sunlight through door, cinematic lighting, 8k, photorealistic, no humans"
}}
"""

    user_prompt = f"Generate an authentic, captivating Facebook post card and caption for category: {selected_category['name']}."
    
    post_data = extract_json(system_prompt, user_prompt, for_posts=True)
    if not post_data or "quote" not in post_data:
        logger.error("Failed to generate Facebook post content from LLM.")
        return None
        
    logger.info(f"Generated Facebook Post: '{post_data.get('title')}' | Ref: {post_data.get('reference')}")
    return post_data
