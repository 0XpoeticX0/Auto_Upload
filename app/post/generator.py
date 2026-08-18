import random
import re
from app.llm.provider import extract_json, generate_text
from app.logger import logger
from app.database import get_connection, get_recent_facebook_posts

POST_PILLARS = [
    {
        "key": "daily_life",
        "name": "দৈনন্দিন জীবন ও হালাল-হারাম (Daily Life)",
        "description": "আচরণ, লেনদেন, সততা, পরিবারের হক, প্রতিবেশীর অধিকার, রাগ নিয়ন্ত্রণ, কথা বলার আদব, হালাল জীবিকা।",
        "seed_concepts": [
            "যে ব্যক্তি মানুষের প্রতি দয়া করে না, আল্লাহ তার প্রতি দয়া করেন না",
            "প্রকৃত বীর সে নয় যে কুস্তিতে জিতে, বরং সে যে রাগের সময় নিজেকে নিয়ন্ত্রণ করে",
            "কারও ক্ষতি করো না এবং ক্ষতিগ্রস্ত হয়ো না",
            "প্রতিবেশীকে কষ্ট দিয়ে কোনো ব্যক্তি পূর্ণ মুমিন হতে পারে না",
            "কথা বললে ভালো কথা বলো, অন্যথায় চুপ থাকো",
            "লজ্জা ও শালীনতা ঈমানের অঙ্গ",
            "সৎ ব্যবসায়ী কিয়ামতের দিন নবী ও শহীদদের সাথে থাকবে",
            "মুসলমানের রক্ত, ধন-সম্পদ ও সম্মান অপরের জন্য হারাম",
            "দান-সদকা কখনো সম্পদ কমায় না",
            "উত্তম চরিত্র ও সুন্দর ব্যবহারের চেয়ে ভারী কোনো আমল পাল্লায় নেই",
            "মায়ের পায়ের নিচে সন্তানের জান্নাত",
            "ধোঁকাবাজ ও প্রতারক আমাদের দলের অন্তর্ভুক্ত নয়",
            "মুচকি হাসিও একটি সদকা",
            "অহংকার যার অন্তরে সামান্যতম থাকবে সে জান্নাতে প্রবেশ করবে না",
            "গোপন দান আল্লাহর ক্রোধকে নিভিয়ে দেয়",
            "মুমিন কখনো পরনিন্দাকারী ও অভিশাপদানকারী হতে পারে না",
            "রাস্তা থেকে কষ্টদায়ক বস্তু সরিয়ে ফেলা ঈমানের শাখা",
            "আল্লাহর সন্তুষ্টি পিতামাতার সন্তুষ্টিতে",
            "মুনাফিকের তিনটি নিদর্শন: মিথ্যা বলা, ওয়াদা ভঙ্গ করা ও আমানতে খিয়ানত করা",
            "যে ব্যক্তি কারও গোপন ত্রুটি গোপন রাখবে, আল্লাহ দুনিয়া ও আখিরাতে তার ত্রুটি গোপন রাখবেন"
        ]
    },
    {
        "key": "dua_cures",
        "name": "দোয়া ও মানসিক প্রশান্তি (Dua & Spiritual Cures)",
        "description": "বিপদ, রোগ, দুশ্চিন্তা, ঋণমুক্তি, ক্ষমা প্রার্থনা এবং সকাল-সন্ধ্যার পরীক্ষিত সহীহ দোয়া।",
        "seed_concepts": [
            "ইউনুস (আ.)-এর মাছের পেটের দোয়া: লা ইলাহা ইল্লা আনতা সুবহানাকা ইন্নি কুনতু মিনাজ জোয়ালিমীন",
            "সাইয়্যিদুল ইস্তিগফার: ক্ষমার শ্রেষ্ঠ দোয়া যা পড়লে জান্নাত ওয়াজিব হয়",
            "বিপদ ও উদ্বেগের দোয়া: আল্লাহুম্মা ইন্নি আউযুবিকা মিনাল হাম্মি ওয়াল হাযান",
            "শত্রু ও ভয়ের সময়ের দোয়া: হাসবুনাল্লাহু ওয়া নি'মাল ওয়াকিল",
            "রোগমুক্তির দোয়া: আইয়ুব (আ.)-এর দোয়া (আন্নি মাস্সানিয়াদ্দুররু ওয়া আনতা আরহামুর রাহিমীন)",
            "ঋণমুক্তির বিশেষ দোয়া: আল্লাহুম্মাকফিনী বিহালালিকা আন হারামিক",
            "হে আল্লাহ! আমার অন্তরকে আপনার দ্বীনের ওপর অবিচল রাখুন (ইয়া মুকাল্লিবাল কুলুব)",
            "লা হাওলা ওয়ালা কুওয়াতা ইল্লা বিল্লাহ জান্নাতের গুপ্তধন",
            "আল্লাহুম্মা ইন্নি আসআলুকাল আফওয়া ওয়াল আফিয়াহ (নিরাপত্তা ও সুস্থতা)",
            "ঘর থেকে বের হওয়ার দোয়া: বিসমিল্লাহি তাওয়াক্কালতু আলাল্লাহ",
            "ঘুমের পূর্বে আয়াতুল কুরসি পাঠ করলে সারারাত ফেরেশতা পাহারা দেয়",
            "সূরা ইখলাস, ফালাক ও নাস ৩ বার পাঠ করলে সব অনিষ্ট থেকে সুরক্ষা",
            "বৃষ্টির সময়ের দোয়া: আল্লাহুম্মা সায়্যিবান নাফিয়া",
            "কবরের আযাব ও জাহান্নাম থেকে পানাহ চাওয়ার দোয়া",
            "আল্লাহর কাছে তাওফিক চাওয়ার দোয়া: রাব্বি যিদনি ইলমা",
            "মা-বাবার জন্য দোয়া: রাব্বির হামহুমা কামা রাব্বায়ানি সাগিরা",
            "জান্নাতুল ফিরদাউস চেয়ে দোয়া করার নির্দেশ",
            "দাজ্জালের ফিতনা থেকে বাঁচতে সূরা কাহাফের প্রথম দশ আয়াত",
            "দুনিয়ায় সুখ ও আখিরাতে কল্যাণের সার্বজনীন দোয়া: রাব্বানা আতিনা ফিদ্দুনিয়া হাসানাহ",
            "আল্লাহর নিকট আন্তরিক তওবা ও ক্ষমা চাওয়ার বিশেষ ফযিলত"
        ]
    },
    {
        "key": "heart_softeners",
        "name": "অন্তর গলানো নসিহত (Heart Softeners)",
        "description": "তওবা, আল্লাহর অসীম দয়া ও ভালোবাসা, নির্জনে চোখের পানি, একনিষ্ঠতা ও আখিরাতের স্মরণ।",
        "seed_concepts": [
            "আল্লাহ তওবাকারীকে সেই ব্যক্তির চেয়েও বেশি ভালোবাসেন যে মরুভূমিতে হারিয়ে যাওয়া উট ফিরে পায়",
            "আল্লাহ বলেন: হে বান্দা! তুমি যদি পৃথিবী পরিমাণ গুনাহ নিয়ে আসো, তবে ক্ষমা নিয়ে তোমার কাছে আসব",
            "যে দুটি চোখ জাহান্নামের আগুন স্পর্শ করবে না: আল্লাহর ভয়ে কাঁদা চোখ ও সীমান্ত পাহারাদার চোখ",
            "আল্লাহর ছায়ায় আশ্রয় পাওয়া ৭ শ্রেণির মানুষ (যেমন গোপনে নির্জনে আল্লাহর ভয়ে কাঁদা ব্যক্তি)",
            "দুনিয়া মুমিনের জন্য কারাগার এবং কাফিরের জন্য জান্নাত",
            "সকল কাজের ফলাফল নিয়তের ওপর নির্ভরশীল",
            "মৃত্যুর কথা বেশি বেশি স্মরণ করো যা সব স্বাদ বিনষ্ট করে দেয়",
            "আল্লাহ বান্দার প্রতি তার মায়ের চেয়েও বেশি দয়ালু",
            "মুমিনের অবস্থা চমৎকার: সুখে থাকলে শুকরিয়া আদায় করে, কষ্টে থাকলে ধৈর্য ধরে",
            "কোরআন তিলাওয়াত যার মাধ্যমে অন্তরের জং ও মরিচা দূর হয়",
            "তাহাজ্জুদের নামাজে বান্দা আল্লাহর সবচেয়ে কাছাকাছি পৌঁছায়",
            "যে ব্যক্তি আল্লাহর জন্য বিনয়ী হয়, আল্লাহ তার মর্যাদা বৃদ্ধি করে দেন",
            "দুনিয়াতে এমনভাবে চলো যেন তুমি একজন মুসাফির বা পথিক",
            "কবরের প্রথম রাতের অবস্থা ও নেক আমলের আলো",
            "কিয়ামতের মাঠে বান্দাকে একা আল্লাহর সামনে দাঁড়িয়ে হিসাব দিতে হবে",
            "আল্লাহর যিকিরে অন্তরে প্রকৃত শান্তি আসে",
            "আল্লাহ তাঁর বান্দার প্রতি তার ধারণার চেয়েও উত্তম আচরণ করেন",
            "বান্দা যখন এক বিঘত কাছে আসে, আল্লাহ এক হাত কাছে আসেন",
            "আল্লাহকে গোপনে ভয় করার পুরস্কার হলো মহা মাগফিরাত ও বড় প্রতিদান",
            "ধৈর্যধারণকারীদের জন্য রয়েছে বিনা হিসেবে অগণিত পুরস্কার"
        ]
    },
    {
        "key": "islamic_knowledge",
        "name": "কুরআন ও হাদিসের বিশেষ জ্ঞান (Islamic Knowledge)",
        "description": "ফেরেশতা, আরশ, জান্নাত-জাহান্নাম, নবীদের অলৌকিক ঘটনা ও সৃষ্টির অপার বিস্ময়।",
        "seed_concepts": [
            "আল্লাহর আরশ বহনকারী ফেরেশতার বিশালতা (কানের লতি থেকে কাঁধের দূরত্ব ৭০০ বছরের পথ)",
            "জান্নাতের তুবা গাছ যার ছায়া অতিক্রমে ঘোড়সওয়ারের ১০০ বছর লাগবে",
            "জান্নাতের সর্বনিম্ন স্তরের মানুষকে দুনিয়ার চেয়ে দশগুণ বড় রাজ্য দেওয়া হবে",
            "সিদরাতুল মুনতাহা ও জিবরাঈল (আ.)-এর ৬০০ ডানার অপরূপ রূপ",
            "মিরাজের রাতে নবীজির আসমান ভ্রমণ ও উম্মতের জন্য উপহার",
            "মিজানের পাল্লায় দুটি বাক্য অত্যন্ত ভারী: সুবহানাল্লাহি ওয়া বিহামদিহি সুবহানাল্লাহিল আযিম",
            "ফেরেশতারা ইলম অন্বেষণকারীর সন্তুষ্টিতে নিজেদের ডানা বিছিয়ে দেয়",
            "কিয়ামতের দিন সূর্য মানুষের এক মাইল নিকটে চলে আসবে",
            "হাওযে কাওসারের পানির স্ফটিক রূপ ও সুমিষ্ট স্বাদ",
            "শাফাআতে কুবরা: কিয়ামতের ময়দানে নবীজির সুপারিশের মহিমান্বিত ক্ষণ",
            "জান্নাতবাসীদের জন্য সবচেয়ে বড় নিয়ামত: মহান আল্লাহর দিদার লাভ",
            "কুরআনের সূরা মুলক যা কবরের আযাব থেকে মুক্তি দিতে সুপারিশ করবে",
            "জান্নাতের দরজাসমূহ (রাইয়ান, সালাত, জিহাদ, সদকা)",
            "আল্লাহ প্রথম কলম সৃষ্টি করে তাকদির লিপিবদ্ধ করার নির্দেশ দিয়েছিলেন",
            "আসমান ও জমিন সৃষ্টির পূর্বে আল্লাহর আরশ ছিল পানির ওপর",
            "বিনা হিসাবে ৭০,০০০ মানুষের জান্নাতে প্রবেশের সুসংবাদ",
            "আল্লাহর ৯৯টি সুন্দর নাম যে ব্যক্তি মুখস্থ ও আমল করবে সে জান্নাতি হবে",
            "শুক্রবার হলো সপ্তাহের শ্রেষ্ঠ দিন এবং এই দিনে একটি দোয়া কবুলের সময় আছে",
            "কুরআন তিলাওয়াতের প্রতি হরফে ১০টি করে নেকি",
            "ইসরাফিলের শিঙায় ফুৎকার ও মহাজাগতিক পুনরুত্থান"
        ]
    }
]

def _get_next_post_pillar(cursor) -> dict:
    """Round-robin rotation for Facebook posts across the 4 pillars."""
    try:
        cursor.execute("SELECT category FROM facebook_posts ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row and row["category"]:
            last_cat = row["category"]
            for i, p in enumerate(POST_PILLARS):
                if p["key"] == last_cat:
                    next_p = POST_PILLARS[(i + 1) % len(POST_PILLARS)]
                    logger.info(f"Post Round-Robin: Last was '{last_cat}' → Next is '{next_p['key']}'")
                    return next_p
    except Exception as e:
        logger.warning(f"Could not read last post pillar: {e}")
        
    return POST_PILLARS[0]

def generate_post_content(language: str = "bangla") -> dict:
    """
    Generates authentic Islamic photo card content with 4-pillar round-robin and 80+ concept deduplication.
    """
    conn = get_connection()
    cursor = conn.cursor()
    selected_pillar = _get_next_post_pillar(cursor)
    conn.close()
    
    logger.info(f"Selected Pillar for Post ({language.upper()}): {selected_pillar['name']}")
    
    recent_posts = get_recent_facebook_posts(limit=60)
    past_topics_list = []
    if recent_posts:
        for p in recent_posts:
            p_dict = dict(p)
            ref = p_dict.get("reference", "")
            q = p_dict.get("quote", "")[:50]
            if ref or q:
                past_topics_list.append(f"- Ref: {ref} | Quote: {q}...")
                
    past_topics_text = ""
    if past_topics_list:
        past_topics_text = "STRICTLY FORBIDDEN PREVIOUS TOPICS/HADITHS (DO NOT REPEAT ANY OF THESE):\n" + "\n".join(past_topics_list[:30])

    available_seeds = selected_pillar.get("seed_concepts", [])
    suggested_seeds = random.sample(available_seeds, min(3, len(available_seeds)))
    suggested_text = "\n".join([f"- {s}" for s in suggested_seeds])

    if language == "bangla":
        system_prompt = f"""You are an expert Islamic scholar and content creator crafting authentic, viral Islamic reflection photo posts in Bangla (বাংলা).
Pillar: {selected_pillar['name']} — {selected_pillar['description']}

SUGGESTED FRESH TOPIC INSPIRATION:
{suggested_text}

CRITICAL RULES (100% STRICT):
1. AUTHENTICITY & SAHABI ATTRIBUTION:
   - Must be 100% authentic from Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami` at-Tirmidhi, or the Holy Quran.
   - For Hadiths: Always include the Sahabi narrator in the header (e.g. 'জাবির ইবনে আব্দুল্লাহ (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:' or 'আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:').
   - For Quranic Ayahs: 'মহান আল্লাহ তা'আলা পবিত্র কুরআনে এরশাদ করেছেন:'.

2. QUOTE ACCURACY (NO ALTERATION):
   - Provide the EXACT authentic Bangla translation inside Bangla quotes ‘...’.
   - Select 2-3 key impactful phrases for highlight_phrases (which will be rendered in golden amber #EBAF41).

3. SHORT & HEART-TOUCHING REFLECTION (ব্যাখ্যা):
   - Exactly 1-2 comforting, emotionally uplifting sentences connecting the Hadith to peace of mind and faith.

4. SOCIAL MEDIA CAPTION:
   - Engaging Bengali title + Sahabi narrator + Arabic quote + Bangla translation + spiritual reflection + verified citation + hashtags.

{past_topics_text}

OUTPUT JSON FORMAT (ONLY valid JSON):
{{
    "language": "bangla",
    "category": "{selected_pillar['key']}",
    "title": "পোস্টের শিরোনাম (বাংলা)",
    "header": "জাবির ইবনে আব্দুল্লাহ (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:",
    "quote": "‘আমাকে আল্লাহর আরশ বহনকারী ফেরেশতাদের মধ্য থেকে একজন ফেরেশতার বর্ণনা দেওয়ার অনুমতি দেওয়া হয়েছে। তাঁর কানের লতি থেকে কাঁধের দূরত্ব হলো সাতশত বছরের পথ।’",
    "highlight_phrases": ["আরশ বহনকারী ফেরেশতাদের", "সাতশত বছরের পথ"],
    "explain_title": "ব্যাখ্যা:",
    "explanation": "আল্লাহর সৃষ্টি একজন ফেরেশতাই যদি এত বিশাল হন, তবে তাঁর সৃষ্টিকর্তা আল্লাহ কত মহান ও মহাশক্তিশালী! আপনার জীবনের বিপদ যখন বড় মনে হবে, তখন মনে রাখবেন এই মহাবিশ্বের মালিক সর্বশক্তিমান আল্লাহ সর্বদা আপনার সাথে আছেন।",
    "reference": "সুনানে আবু দাউদ: ৪৭২৭",
    "caption": "✨ আল্লাহর আরশ বহনকারী ফেরেশতার বিশালতা ✨\\n\\nজাবির ইবনে আব্দুল্লাহ (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:\\n\\n‘আমাকে আল্লাহর আরশ বহনকারী ফেরেশতাদের মধ্য থেকে একজন ফেরেশতার বর্ণনা দেওয়ার অনুমতি দেওয়া হয়েছে। তাঁর কানের লতি থেকে কাঁধের দূরত্ব হলো সাতশত বছরের পথ।’\\n\\n📖 রেফারেন্স: সুনানে আবু দাউদ (৪৭২৭)\\n\\n🌿 শিক্ষা:\\nআল্লাহর একজন ফেরেশতার সৃষ্টিই যদি এত বিশাল হয়, তবে সমগ্র মহাবিশ্বের সৃষ্টিকর্তা আল্লাহ কত মহান! যে আল্লাহ এই সুবিশাল সৃষ্টিকে পরিচালনা করছেন, তিনি আপনার প্রতিটি কষ্ট ও দুশ্চিন্তা দূর করতে সম্পূর্ণ সক্ষম।\\n\\n💬 কমেন্টে ‘সুবহানাল্লাহ’ লিখুন এবং শেয়ার করে অন্যকেও জানার সুযোগ দিন।\\n\\n#DailyDosOfIslam #BanglaHadith #IslamicPost #HadithReminder",
    "image_prompt": "vast tranquil desert sand dunes under warm glowing twilight sunset, cinematic atmospheric photography 8k, serene, empty, no humans, no living beings"
}}
"""
        user_prompt = f"Generate an authentic, unrepeated Islamic reflection post in Bangla for pillar: {selected_pillar['name']}. Choose an inspiring fresh Hadith."
    else:
        system_prompt = f"""You are an expert Islamic scholar crafting authentic English reflection posts for Facebook/Instagram.
Pillar: {selected_pillar['name']} — {selected_pillar['description']}

SUGGESTED FRESH TOPIC INSPIRATION:
{suggested_text}

CRITICAL RULES:
1. Include the Sahabi narrator in the header (e.g. 'Abu Hurairah reported: The Messenger of Allah (peace be upon him) said:').
2. Exact verbatim quote with highlight_phrases in golden amber.
3. 1-2 sentences of comforting spiritual reflection under Explain.
4. Complete citation (e.g. 'Sunan Abi Dawud: 4727').
5. image_prompt: atmospheric natural landscape or architecture (NO humans, NO living beings).

{past_topics_text}

OUTPUT JSON ONLY:
{{
    "language": "english",
    "category": "{selected_pillar['key']}",
    "title": "Post Title",
    "header": "Jabir b. 'Abd Allah reported that the Prophet (peace be upon him) said:",
    "quote": "‘I have been permitted to speak about an angel from the angels of Allah who carry the Throne. The distance between his earlobe and his shoulder is a journey of seven hundred years.’",
    "highlight_phrases": ["angels of Allah who carry the Throne", "journey of seven hundred years"],
    "explain_title": "Explain:",
    "explanation": "If a single angel created by Allah is this vast, imagine how grand and powerful the Creator Himself is. When your problems feel overwhelming, remember that the Almighty who controls this vast universe is always by your side.",
    "reference": "Sunan Abi Dawud: 4727",
    "image_prompt": "vast moody cinematic desert dunes under soft glowing golden dusk sky, atmospheric, 8k, photorealistic, no humans"
}}
"""
        user_prompt = "Generate a fresh authentic Islamic post with Sahabi narrator, exact verbatim Sunnah.com translation, and inspiring reflection."

    data = extract_json(system_prompt, user_prompt, for_posts=True)
    if data and "language" not in data:
        data["language"] = language
    return data
