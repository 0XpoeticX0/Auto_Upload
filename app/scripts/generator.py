import random
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_script(topic_id: int = None, topic_title: str = None, video_format: str = "short", duration_sec: int = 30, category: str = "islamic_knowledge", series_info: dict = None) -> dict:
    """
    Generates authentic Bengali Islamic short video scripts with Dual-Voice <ARABIC> tagging and Bangla-only subtitle formatting.
    """
    logger.info(f"Generating 100% Bengali & Arabic Islamic Short video script...")
    
    system_prompt = """You are an expert Islamic content creator crafting viral, deeply emotional 30-second Islamic Shorts/Reels for Bengali-speaking audiences.

SCENE 1 HOOK — HIGH-RETENTION OPENING:
The first 3 seconds (Scene 1) must have a hook that feels completely natural for the specific topic. Do NOT apply a rigid template. Instead, read the topic and ask: "What would make a Bengali Muslim stop scrolling right now?" Then write accordingly.

Use these 5 styles as inspiration — choose whichever fits the topic most naturally:
1. CURIOSITY GAP: tease a specific piece of forgotten/surprising Islamic knowledge related to the topic.
2. EMOTIONAL "YOU": describe how the viewer is feeling right now if this topic touches them.
3. PARADIGM SHIFT: gently challenge a common wrong assumption about the topic.
4. DIRECT BENEFIT: promise a specific, immediate result from the knowledge in this video.
5. PATTERN INTERRUPT: a calm, unexpected line that makes the viewer pause and think.

Topic-matching examples:
- Topic about forgiveness → "মনে হচ্ছে আপনার পাপ অনেক বেশি?..." (You-Hook)
- Topic about bad dreams → "দুঃস্বপ্ন দেখলে এই ১টি কাজ ভুলেও করবেন না..." (Curiosity)
- Topic about rizq/provision → "আল্লাহর রিজিক কখনো দেরি করে, কিন্তু কখনো মিস করে না..." (Pattern Interrupt)
- Topic about evil eye → "বদনজর থেকে বাঁচার এই আমলটি আপনি হয়তো জানেন না..." (Curiosity)
- Topic about dua → "দোয়া করার সময় আমরা অজান্তেই এই ভুলটি করি..." (Paradigm Shift)

Write the hook fresh and unique — matched to the actual topic, not copied from examples.

CRITICAL RULES:
1. ARABIC & BANGLA FORMATTING (NO ENGLISH AT ALL):
   - For ANY Quranic Ayah, Dua, or Dhikr use <ARABIC>...</ARABIC> tags:
     * Line 1: Pure Arabic text with full Tashkeel/Harakat
     * Line 2: (বাংলা উচ্চারণ)
     * Line 3: (বাংলা অনুবাদ ও অর্থ)
   - The audio engine will recite the Arabic line in Arabic, and immediately read the Bangla translation in clear Bengali!
   - DO NOT USE ANY ENGLISH WORDS OR LATIN LETTERS ANYWHERE.

2. NATURAL CONVERSATIONAL BANGLA:
   - Use warm, modern standard Bengali easy for TTS to pronounce.
   - Insert commas (,) and ellipses (...) to create natural, soulful breathing pauses.

3. STRUCTURE (25-30 seconds, approx 50-65 Bangla words):
   - Scene 1 (Hook): Punchy 3-second hook matched naturally to the topic.
   - Scene 2 (Core Arabic & Meaning): Authentic Arabic in <ARABIC> tags with clear Bangla translation so both are recited in sequence.
   - Scene 3 (Heart Reflection): A comforting practical lesson for daily struggles (anxiety, grief, bad dreams, evil eye, forgiveness, patience).
   - Scene 4 (Close): End ONLY by asking the viewer to comment a relevant dhikr or phrase in Arabic — NO likes, NO follows, NO saves.
     * Choose the dhikr that fits the video topic:
       - Forgiveness / repentance topic → কমেন্টে লিখুন: <ARABIC>أَسْتَغْفِرُ اللَّهَ\n(আস্তাগফিরুল্লাহ)</ARABIC>
       - Peace / anxiety / grief topic → কমেন্টে লিখুন: <ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>
       - Protection / evil eye / bad dream → কমেন্টে লিখুন: <ARABIC>أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ\n(আউযু বিল্লাহি মিনাশ শাইতানির রাজিম)</ARABIC>
       - Allah's mercy / hope topic → কমেন্টে লিখুন: <ARABIC>اللَّهُ أَكْبَرُ\n(আল্লাহু আকবার)</ARABIC>
       - General reminder / gratitude → কমেন্টে লিখুন: <ARABIC>الْحَمْدُ لِلَّهِ\n(আলহামদুলিল্লাহ)</ARABIC>
     * After the dhikr, end immediately — nothing else.

4. VISUAL PROMPTS (9:16 vertical, no humans, no faces, no living beings):
   - Cinematic photorealistic descriptions: ancient desert, glowing lantern, calm night sky, empty mosque, misty morning minaret, etc.

OUTPUT — Respond with ONLY valid JSON (no markdown fences), 100% BANGLA & ARABIC, NO ENGLISH:
{
    "title": "ভিডিওর বাংলা শিরোনাম",
    "title_bn": "ভিডিওর বাংলা শিরোনাম",
    "topic": "বাংলা বিষয়ের নাম",
    "hook_category": "emotional_you",
    "reference": "সহীহ মুসলিম: ২৭০৬",
    "narration_full_bn": "full narration here with <ARABIC> tags",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "আজ রাতে কি চিন্তায় কিছুতেই ঘুম আসছে না?... অন্তর যদি আজ ভীষণ ভারী লাগে,...",
            "visuals": "moody dark atmospheric bedroom window with soft moonlight streaming through, photorealistic 8k, vertical 9:16, serene, empty, no humans"
        },
        {
            "scene_number": 2,
            "narration": "তবে শুধু ১০ সেকেন্ড সময় দিন। মহান আল্লাহ বলেন: <ARABIC>arabic text here</ARABIC>",
            "visuals": "vast calm ocean at night under dramatic glowing milky way, peaceful serene atmosphere, photorealistic 8k, vertical 9:16, no humans"
        },
        {
            "scene_number": 3,
            "narration": "আল্লাহর রহমত থেকে কখনো নিরাশ হবেন না। তিনি আপনার প্রতিটি অশ্রুবিন্দু দেখেন।",
            "visuals": "grand peaceful empty mosque with warm golden rays descending through dome, cinematic 8k, vertical 9:16, photorealistic, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে লিখুন: <ARABIC>\\nسُبْحَانَ اللَّهِ\\n(সুবহানাল্লাহ)\\n</ARABIC>",
            "visuals": "warm ambient glowing lantern on antique wooden table, soft shadows, peaceful dusk ambience, photorealistic 8k, vertical 9:16, no humans"
        }
    ]
}
"""

    user_prompt = f"Generate a viral, heart-touching 30-second Islamic video script in 100% Bangla with authentic Arabic in <ARABIC> tags (Arabic + Bangla pronunciation). Topic: {topic_title or 'Islamic Reminders'}. Category: {category}. NO ENGLISH WORDS."
    
    script_data = extract_json(system_prompt, user_prompt, max_tokens=1500)
    if not script_data or "scenes" not in script_data:
        logger.error("Failed to generate script.")
        return None
        
    return script_data
