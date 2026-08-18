import json
import random
from app.logger import logger
from app.database import get_connection
from app.llm.provider import extract_json
from app.history import (
    get_next_pillar_from_history,
    record_video_history,
    get_recent_video_titles
)

# The 4 pillars in fixed rotation order — each run picks the NEXT pillar
PILLARS = [
    {
        "category": "daily_life",
        "label": "দৈনন্দিন জীবন",
        "description": "হালাল/হারাম, সম্পর্ক, আচরণ, লেনদেন, নামাজ-রোজার ফজিলত, পরিবার, পিতা-মাতার হক",
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
        "category": "dua_cures",
        "label": "দোয়া ও নিরাময়",
        "description": "বিপদ, রোগ, মানসিক কষ্ট থেকে মুক্তির সহীহ দোয়া ও আমল, তাহাজ্জুদ, ইস্তিগফার",
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
        "category": "heart_softeners",
        "label": "অন্তর গলানো নসিহত",
        "description": "তওবা, আল্লাহর রহমত, অনুপ্রেরণা, গুনাহ থেকে ফেরার পথ, আল্লাহর ভালোবাসা, নির্জনে কান্না",
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
        "category": "islamic_knowledge",
        "label": "শেষ যামানা ও আখিরাত",
        "description": "কিয়ামতের আলামত, কবরের জীবন, জান্নাত-জাহান্নামের বর্ণনা, দাজ্জাল, ফেরেশতা ও সৃষ্টিজগৎ",
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
    },
    {
        "category": "dreams_and_sleep",
        "label": "স্বপ্ন ও ঘুম",
        "description": "ভালো স্বপ্ন ও দুঃস্বপ্নের তাৎপর্য, দুঃস্বপ্ন দেখলে হাদিসের নির্দেশনা, ঘুমের দোয়া, তাহাজ্জুদের ফযিলত ও ঘুমের সুন্নাহ",
        "seed_concepts": [
            "দুঃস্বপ্ন দেখলে বাম দিকে ৩ বার থুথু ফেলা ও পার্শ্ব পরিবর্তন করার সুন্নাহ",
            "ভালো স্বপ্ন আল্লাহর পক্ষ থেকে সুসংবাদ এবং তা কেবল শুভাকাঙ্ক্ষীকে বলা উচিত",
            "শয়তান ঘুমন্ত মানুষের মাথার পেছনে ৩টি গিঁট দেয় এবং ফজরের সময় তা খোলার উপায়",
            "ঘুমের মধ্যে ভয় পেলে বা চমকে উঠলে পাঠ করার বিশেষ সহীহ দোয়া",
            "রাতে হঠাৎ ঘুম ভেঙে গেলে যে দোয়া পড়লে সাথে সাথে দোয়া কবুল হয়",
            "ঘুমানোর পূর্বে ডান কাতে শোয়া ও দুই হাতের তালুতে ৩ কুল পড়ে শরীর মুছে নেওয়া",
            "ঘুম না আসলে এবং গভীর রাতের মানসিক অস্থিরতা কাটানোর আমল",
            "স্বপ্নে কোনো খারাপ কিছু দেখলে কারও কাছে না বলা যাতে ক্ষতি না হয়",
            "তাহাজ্জুদের শেষ প্রহরে জাগ্রত হয়ে রবের নৈকট্য লাভ ও অশ্রু বিসর্জন",
            "ঘুমানোর পূর্বে সূরা মুলক ও সূরা সাজদাহ তিলাওয়াত করার সুন্নাহ"
        ]
    },
    {
        "category": "protection_ruqyah",
        "label": "বদনজর ও আত্মরক্ষা",
        "description": "কালো জাদু, কুদৃষ্টি, বদনজর, হিংসা ও শয়তানি অনিষ্ট থেকে কুরআন-সুন্নাহ অনুযায়ী আত্মরক্ষা ও রুকইয়াহ",
        "seed_concepts": [
            "বদনজর বা কুদৃষ্টি সত্য এবং তা মানুষকে অসুস্থ ও কবরে পর্যন্ত নিয়ে যেতে পারে",
            "সুন্দর কিছু দেখলে 'মাশাআল্লাহ লা কুওয়াতা ইল্লা বিল্লাহ' ও বরকতের দোয়া করার নির্দেশ",
            "সকাল-সন্ধ্যায় ৩ বার সূরা ইখলাস, ফালাক ও নাস পাঠ করলে সব অপশক্তি থেকে সুরক্ষা",
            "ঘরে প্রবেশ ও বের হওয়ার দোয়া এবং সূরা বাকারার তিলাওয়াতে শয়তান পলায়ন করে",
            "অসুস্থতায় ও ব্যথায় নবীজি (সা.)-এর শেখানো ঝাড়ফুঁক ও দোয়া",
            "কারও হিংসা ও শত্রুতার ভয় পেলে পাঠ করার বিশেষ দোয়া: হাসবুনাল্লাহু ওয়া নি'মাল ওয়াকিল",
            "আয়াতুল কুরসি পাঠ করে ঘুমালে সারারাত আল্লাহর পক্ষ থেকে একজন ফেরেশতা পাহারাদার থাকে",
            "ছোট বাচ্চাদের বদনজর থেকে রক্ষা করতে নবীজি (সা.)-এর শেখানো সুরক্ষার দোয়া",
            "খাবার ও পানীয়তে বিষ বা ক্ষতি থেকে বাঁচতে 'বিসমিল্লাহিল্লাজি লা ইয়াদুররু' দোয়া",
            "জাদুটোনা ও শয়তানি ওয়াসওয়াসা দূর করার পরীক্ষিত কুরআনি আমল"
        ]
    }
]

def generate_topic_for_pillar(pillar: dict, recent_titles: list) -> dict | None:
    """Ask Gemini for ONE fresh topic for the given pillar with strict concept-level deduplication."""
    avoid_section = ""
    if recent_titles:
        avoid_section = "\n\nCRITICAL CONCEPT DEDUPLICATION RULE:\nBelow is the list of topics/stories ALREADY covered in the last 40 days:\n"
        for t in recent_titles[:35]:
            avoid_section += f"- {t}\n"
        avoid_section += """
YOU MUST NOT COVER THE SAME CORE CONCEPT, STORY, EVENT, OR HADITH EVEN UNDER A DIFFERENT NAME OR TITLE!
CHOOSE A COMPLETELY UNRELATED EVENT, SAHIH HADITH, OR LESSON FROM THE VAST ISLAMIC TRADITION!"""

    seeds = pillar.get("seed_concepts", [])
    sampled_seeds = random.sample(seeds, min(3, len(seeds))) if seeds else []
    seed_text = "\n".join([f"- {s}" for s in sampled_seeds])

    system_prompt = f"""You are an expert Islamic content researcher for viral Bengali YouTube Shorts and Reels.
Generate ONE highly engaging, deeply emotional Islamic topic in Bangla (বাংলা) for this specific pillar:

PILLAR: {pillar['label']}
FOCUS: {pillar['description']}

FRESH TOPIC SEED INSPIRATIONS:
{seed_text}

Rules:
- Backed strictly by authentic Quran verses or Sahih Hadith only
- Emotionally gripping, high-CTR Bengali title (max 12 words)
- 100% unique core concept — MUST NOT be a thematic clone of any recently covered topic
{avoid_section}

Output ONLY valid JSON:
{{
    "title": "...",
    "core_concept": "Brief explanation of the specific unique Hadith/story covered",
    "category": "{pillar['category']}",
    "score": 99.0
}}"""

    user_prompt = f"Generate ONE unique, never-before-covered Bengali Islamic Short topic for the '{pillar['label']}' pillar. Ensure zero conceptual overlap with the recent topics list."

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=400)
        if data and "title" in data:
            data["category"] = pillar["category"]
            logger.info(f"Generated fresh concept: '{data.get('core_concept', 'N/A')}' -> Title: '{data['title']}'")
            return data
    except Exception as e:
        logger.error(f"Error generating topic for pillar '{pillar['label']}': {e}")
    return None

def run_discovery():
    # Step 1: Determine which pillar is next in rotation using persistent history
    pillar = get_next_pillar_from_history(PILLARS, "video")
    logger.info(f"Selected content category: {pillar['label'].upper()}")

    # Step 2: Fetch recent titles from persistent history for anti-repetition
    recent_titles = get_recent_video_titles(limit=50)

    # Step 3: Ask Gemini for a fresh topic for this pillar
    topic_data = generate_topic_for_pillar(pillar, recent_titles)

    if not topic_data:
        logger.warning(f"Gemini failed for pillar '{pillar['label']}'. Using fallback seed.")
        seeds = pillar.get("seed_concepts", ["আল্লাহর সন্তুষ্টি ও রহমত অর্জনের পথ"])
        chosen_seed = random.choice(seeds)
        topic_data = {
            "title": chosen_seed,
            "core_concept": chosen_seed,
            "category": pillar["category"],
            "score": 97.0
        }

    title = topic_data["title"]
    score = topic_data.get("score", 97.0)
    cat = pillar["category"]
    core_concept = topic_data.get("core_concept", "N/A")

    # Step 4: Record to persistent history file
    record_video_history(title, cat, core_concept)

    # Step 5: Save to DB (if available)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO topics (title, source, score, status) VALUES (?, ?, ?, 'IN_PROGRESS')",
            (title, f"Gemini AI Discovery ({cat})", score)
        )
        conn.commit()
        cursor.execute("SELECT id FROM topics WHERE title = ? ORDER BY id DESC LIMIT 1", (title,))
        row = cursor.fetchone()
        topic_id = row["id"] if row else 1
        conn.close()
    except Exception as e:
        logger.warning(f"DB insert notice: {e}")
        topic_id = 1

    return {
        "id": topic_id,
        "title": title,
        "score": score,
        "category": cat
    }
    conn.close()

    logger.info(f"Selected topic for production: {title} (ID: {topic_id})")
    return {
        "id": topic_id,
        "title": title,
        "score": score,
        "category": cat
    }
