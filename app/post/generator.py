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
    Generates authentic Islamic photo card content + Facebook/Instagram caption with simple, relatable, heart-softening language.
    """
    selected_category = random.choice(POST_CATEGORIES)
    logger.info(f"Selected category for Facebook Post: {selected_category['name']}")
    
    # Query past posts to strictly prevent repeating content for 30+ days
    recent_posts = get_recent_facebook_posts(limit=40)
    past_topics_text = ""
    if recent_posts:
        past_topics_list = [f"- Reference: {dict(p).get('reference', '')} | Quote: {dict(p).get('quote', '')[:60]}..." for p in recent_posts]
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list)

    system_prompt = f"""You are an expert Islamic content creator crafting viral, deeply relatable, and beautiful Islamic reflection cards and captions for Facebook and Instagram.
Category: {selected_category['name']} — {selected_category['description']}

CRITICAL TONE & LANGUAGE RULES:
1. SIMPLE, EASY & RELATABLE WORDS:
   - Use simple, everyday, warm, heart-touching English that EVERYONE can easily understand and relate to.
   - Avoid archaic, stiff, or overly academic words (e.g. instead of "divine reverence" or "transgressions", use simple words like "a tear shed in secret for Allah", "turning back to Allah with an open heart", "our daily mistakes and worries").
   - Make the message speak directly to the reader's real feelings (feeling stressed, seeking forgiveness, needing peace at night, guarding our speech).

2. 100% AUTHENTICITY:
   - The Ayah or Hadith MUST be 100% authentic from the Quran or Sahih Sunnah (Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami' at-Tirmidhi, Sunan an-Nasa'i, Sunan Ibn Majah). No weak or fabricated claims.

3. NO REPETITIONS:
   - You must choose a FRESH, UNIQUE Hadith or Ayah that has NOT been used in recent posts.

4. FORMAT OF THE IMAGE CARD:
   - "header": E.g. "The Prophet (peace be upon him) said:" or "Allah says in the Quran:".
   - "quote": The authentic English translation of the Hadith or Ayah in single quotes. Make it powerful, clear, simple, and self-contained (25-45 words max).
   - "highlight_phrases": An array of 1 or 2 of the MOST IMPORTANT, STRIKING PUNCHLINES OR PROMISES from the quote to be highlighted in bold golden amber (#EBAF41) on the image card.
     * Examples of what to highlight:
       - If about tears/forgiveness: ["an eye that wept out of fear of Allah", "I shall forgive you"]
       - If about modesty: ["Do not be alone with a woman", "is like death"]
       - If about relief: ["Allah is with the patient", "after hardship comes ease"]
     * RULE: NEVER highlight single tiny filler words. Highlight the core punchline (3 to 6 words).
     * The highlighted words MUST appear word-for-word inside your "quote" field.
   - "explain_title": "Explain:"
   - "explanation": Exactly 2 to 3 simple, heartfelt sentences explaining the practical daily lesson in easy words so anyone can apply it immediately (30-45 words max).
   - "reference": Exact authentic citation (e.g. 'Sahih Muslim: 2172 a', 'Jami` at-Tirmidhi: 1639', 'Sahih al-Bukhari: 6474').

5. CAPTION FOR SOCIAL MEDIA:
   - "caption": A captivating, relatable caption. Start with a warm relatable hook ("When was the last time you sat alone at night...", "We often forget how heavy a few words can be..."). Explain the wisdom simply, encourage readers to save & share, and include 5-8 relevant hashtags (#Islam #Hadith #DailyReminder #Sunnah #IslamicQuotes #Faith #Muslim #Allah).

6. VISUAL BACKGROUND PROMPT:
   - "image_prompt": A moody, atmospheric, cinematic visual description for the background photo (e.g. 'moody ancient doorway with warm sunlight beaming through, shadows, serene quiet atmosphere, photorealistic, 8k, empty room, cinematic lighting, no humans, no faces').

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON, no markdown outside):
{{
    "category": "{selected_category['key']}",
    "title": "Short title describing the topic",
    "header": "The Prophet (peace be upon him) said:",
    "quote": "‘Exact authentic quote text here...’",
    "highlight_phrases": ["key phrase 1", "key phrase 2"],
    "explain_title": "Explain:",
    "explanation": "Simple, warm, relatable 2-3 sentence reflection here...",
    "reference": "Sahih al-Bukhari: 6474",
    "caption": "Full rich social media caption with hook, reflection, and hashtags...",
    "image_prompt": "moody dark atmospheric hallway with warm sunlight through door, cinematic lighting, 8k, photorealistic, no humans"
}}
"""

    user_prompt = f"Generate an authentic, deeply relatable, and simple Islamic post card and caption for category: {selected_category['name']}."
    
    post_data = extract_json(system_prompt, user_prompt, for_posts=True)
    if not post_data or "quote" not in post_data:
        logger.error("Failed to generate post content from LLM.")
        return None
        
    logger.info(f"Generated Post: '{post_data.get('title')}' | Ref: {post_data.get('reference')}")
    return post_data
