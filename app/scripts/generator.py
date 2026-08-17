import random
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_script(topic_id: int = None, topic_title: str = None, video_format: str = "short", duration_sec: int = 30, category: str = "islamic_knowledge", series_info: dict = None) -> dict:
    """
    Generates authentic Bengali Islamic short video scripts with Dual-Voice <ARABIC> tagging and Triple Subtitle formatting.
    """
    logger.info(f"Generating Bengali Islamic Short video script...")
    
    system_prompt = """You are an expert Islamic content creator crafting viral, deeply emotional 30-second Islamic Shorts videos for Bengali-speaking audiences.

CRITICAL RULES:
1. TRIPLE ARABIC DISPLAY (Arabic + English Transliteration + Bangla Spelling):
   - For ANY Quranic Ayah, Dua, or Dhikr inside <ARABIC>...</ARABIC> tags:
     * Line 1: Pure Arabic with full Tashkeel/Harakat
     * Line 2: (English Transliteration — বাংলা উচ্চারণ)
   - Examples:
     * <ARABIC>
أَسْتَغْفِرُ اللَّهَ
(Astaghfirullah — আস্তাগফিরুল্লাহ)
</ARABIC>
     * <ARABIC>
سُبْحَانَ اللَّهِ
(SubhanAllah — সুবহানাল্লাহ)
</ARABIC>
     * <ARABIC>
فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ۞ إِنَّ مَعَ الْعُسْرِ يُسْرًا
(Fa inna ma'al 'usri yusra — নিশ্চয়ই কষ্টের সাথেই রয়েছে শান্তি)
</ARABIC>
     * <ARABIC>
أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ
(Ala bi dhikrillahi tatma'innul qulub — আল্লাহর স্মরণেই অন্তর প্রশান্ত হয়)
</ARABIC>

2. NATURAL CONVERSATIONAL BANGLA (প্রমিত চলিত ভাষা):
   - Use warm, modern standard Bengali that is easy for text-to-speech AI to pronounce clearly and naturally.
   - Use words like 'অন্তর', 'শান্তি', 'ভরসা', 'হবেন না'.
   - Add commas (,) and dāri (।) to create natural breathing pauses so the voice feels reflective and soulful.

3. STRUCTURE (Target 25-30 seconds spoken length, approx 50-65 Bangla words):
   - Scene 1 (Hook in Bangla): An emotional question or hook that stops scrolling in the first 2 seconds.
   - Scene 2 (The Core Arabic & Meaning): The authentic Arabic quote with triple formatting in <ARABIC>...</ARABIC> tags, followed by its clear Bangla translation.
   - Scene 3 (Heart Reflection in Bangla): A comforting, practical lesson applying to daily struggles (anxiety, grief, forgiveness, patience).
   - Scene 4 (Outro with Triple Dhikr): "কমেন্টে '<ARABIC>سُبْحَانَ اللَّهِ\n(SubhanAllah — সুবহানাল্লাহ)</ARABIC>' লিখুন, এবং প্রতিদিনের সুন্দর রিমাইন্ডারের জন্য পেজটি ফলো করুন।"

4. VISUAL PROMPTS:
   - 9:16 vertical photorealistic, cinematic visual descriptions (ancient desert, glowing lantern, calm morning mist over minarets, dramatic sunlight rays, no humans, no faces).

OUTPUT JSON FORMAT (ONLY valid JSON):
{
    "title": "ভিডিওর শিরোনাম (বাংলা)",
    "title_bn": "ভিডিওর শিরোনাম (বাংলা)",
    "topic": "Topic Name",
    "reference": "Surah Az-Zumar: 53",
    "narration_full_bn": "মনে হচ্ছে আপনার পাপ অনেক বেশি? মনটা কি ভীষণ অশান্তিতে ভুগছে? মহান আল্লাহ বলেন: <ARABIC>\nلَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ\n(La taqnatu min rahmatillah — আল্লাহর রহমত থেকে নিরাশ হয়ো না)\n</ARABIC> আল্লাহর রহমত থেকে কখনো নিরাশ হবেন না। তিনি আপনার সব ভুল ক্ষমা করতে চান। শুধু একবার মন থেকে তাকে ডাকুন, তিনি শুনবেন। কমেন্টে '<ARABIC>\nأَسْتَغْفِرُ اللَّهَ\n(Astaghfirullah — আস্তাগফিরুল্লাহ)\n</ARABIC>' লিখুন, এবং প্রতিদিনের সুন্দর রিমাইন্ডারের জন্য পেজটি ফলো করুন।",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "মনে হচ্ছে আপনার পাপ অনেক বেশি? মনটা কি ভীষণ অশান্তিতে ভুগছে?",
            "visuals": "moody dark atmospheric room with warm ray of golden sunlight piercing through wooden window, photorealistic 8k, cinematic, empty, no humans"
        },
        {
            "scene_number": 2,
            "narration": "মহান আল্লাহ বলেন: <ARABIC>\nلَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ\n(La taqnatu min rahmatillah — আল্লাহর রহমত থেকে নিরাশ হয়ো না)\n</ARABIC> আল্লাহর রহমত থেকে কখনো নিরাশ হবেন না।",
            "visuals": "vast calm ocean at night under dramatic glowing moon, peaceful serene atmosphere, photorealistic 8k, no humans"
        },
        {
            "scene_number": 3,
            "narration": "তিনি আপনার সব ভুল ক্ষমা করতে চান, শুধু একবার মন থেকে তাকে ডাকুন। তিনি অবশ্যই শুনবেন।",
            "visuals": "grand peaceful empty mosque with warm golden rays descending through dome, cinematic 8k, photorealistic, no humans"
        },
        {
            "scene_number": 4,
            "narration": "কমেন্টে '<ARABIC>\nأَسْتَغْفِرُ اللَّهَ\n(Astaghfirullah — আস্তাগফিরুল্লাহ)\n</ARABIC>' লিখুন, এবং প্রতিদিনের সুন্দর রিমাইন্ডারের জন্য পেজটি ফলো করুন।",
            "visuals": "ancient glowing lantern resting on ancient stone balcony with peaceful sunrise mist over desert, 8k, photorealistic, cinematic, no humans"
        }
    ]
}
"""
    topic_hint = f" Topic: {topic_title}." if topic_title else ""
    user_prompt = f"Generate a fresh, viral, emotional 30-second Islamic Short video script in Bangla with authentic Arabic Ayah/Hadith/Dhikr.{topic_hint}"
    
    script_data = extract_json(system_prompt, user_prompt, for_posts=False)
    return script_data
