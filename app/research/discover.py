# -*- coding: utf-8 -*-
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

# ==============================================================================
# ACTIVE WINNING FORMULA MOMENT PILLARS (The 4 High-Reach Clusters)
# Formula: 1. The Relatable Moment -> 2. The Prophet's Solution -> 3. The Irresistible Payoff
# ==============================================================================
ALL_DIVERSE_ISLAMIC_PILLARS = [
    {
        "category": "islamic_stories",
        "label": "সত্যিকারের ইসলামিক ঘটনা ও সাহাবাদের জীবন",
        "description": "কুরআনে বর্ণিত নবীদের রোমাঞ্চকর ঘটনা, আসহাবুল কাহফ, এবং সাহাবায়ে কেরামের ত্যাগ ও বীরত্বের অবিশ্বাস্য কাহিনী",
        "seed_concepts": [
            "ইউনুস (আ.)-এর মাছের পেটের সেই অন্ধকার ও আল্লাহর উদ্ধার [সূরা আম্বিয়া: ৮৭]",
            "আসহাবুল কাহফের যুবকদের গুহায় ৩০০ বছরের অলৌকিক ঘুম [সূরা কাহাফ: ৯-২৫]",
            "ইউসুফ (আ.)-এর অন্ধকূপ থেকে মিশরের শাসক হওয়ার অবিশ্বাস্য ঘটনা [সূরা ইউসুফ]",
            "খালিদ বিন ওয়ালিদ (রা.)-এর ওপর আল্লাহর দেওয়া অপরাজেয় তলোয়ারের বীরত্বগাথা",
            "হযরত উমর (রা.)-এর ইসলাম গ্রহণ ও মক্কার জমিনে প্রথম প্রকাশ্যে আজান",
            "হযরত বিলাল (রা.)-এর বুকে জ্বলন্ত পাথরের ওপর অবিচল ঈমান ও 'আহাদ আহাদ'",
            "মুসা (আ.) ও লোহিত সাগরের পানির পাহাড় হয়ে রাস্তা খুলে দেওয়ার অলৌকিক মুহূর্ত [সূরা শুয়ারা: ৬৩]"
        ]
    },
    {
        "category": "akhirah_unseen",
        "label": "শেষ যামানা, কিয়ামতের আলামত ও আখিরাত",
        "description": "কিয়ামতের বড় ও ছোট আলামত, কবরের প্রথম রাত, পুলসিরাত, জান্নাত ও জাহান্নামের হৃদয় কাঁপানো বর্ণনা",
        "seed_concepts": [
            "কিয়ামতের সেই ভয়ংকর দিন যখন মানুষ নিজের মা ও সন্তানকেও ফেলে পালাবে [সূরা আবাসা: ৩৪-৩৭]",
            "কবরের প্রথম রাতের সেই নিস্তব্ধ অন্ধকার ও মুনকার-নাকিরের ৩টি প্রশ্ন [সহীহ বুখারী: ১৩৭৪]",
            "শেষ যামানায় দাজ্জালের আত্মপ্রকাশ ও তার থেকে বাঁচার সহীহ আমল [সহীহ মুসলিম: ২৯৩৭]",
            "পুলসিরাতের ওপর দিয়ে বাতাসের গতিতে বিজলির মতো পার হয়ে যাওয়ার মুহূর্ত [সহীহ বুখারী: ৭৪৩৯]",
            "জান্নাতের সবচেয়ে নিম্নস্তরের মানুষের জন্য পৃথিবীর চেয়ে ১০ গুণ বড় সাম্রাজ্য [সহীহ মুসলিম: ১৮৬]",
            "আরশের নিচে কেয়ামতের ভয়াবহ উত্তাপে যে ৭ শ্রেণির মানুষ আশ্রয় পাবে [সহীহ বুখারী: ৬৬০]"
        ]
    },
    {
        "category": "seerah",
        "label": "নবীজি (ﷺ)-এর জীবন, মুজিজা ও সীরাহ",
        "description": "রাসূলুল্লাহ (ﷺ)-এর জীবনের অবিস্মরণীয় ঘটনা, অলৌকিক মুজিজা, চরম ত্যাগ ও তাঁর অনুপম চরিত্র",
        "seed_concepts": [
            "তায়েফের ময়দানে রক্তাক্ত হয়েও রাসুলুল্লাহ (ﷺ)-এর ক্ষমা প্রার্থনার সেই কান্না [সহীহ বুখারী: ৩২৩১]",
            "মিরাজের রাতে ঊর্ধ্বাকাশে ভ্রমণ ও আল্লাহর সঙ্গে সরাসরি কথোপকথনের সেই ক্ষণ [সহীহ বুখারী: ৩৮৮৭]",
            "বদর প্রান্তরে মাত্র ৩১৩ জন নিরস্ত্র সাহাবীর পক্ষে আসমান থেকে ফেরেশতা নামার মুহূর্ত [সূরা আনফাল: ৯]",
            "নবীজি (ﷺ)-এর হাতের ইশারায় চাঁদের দ্বিখণ্ডিত হওয়ার অবিশ্বাস্য মুজিজা [সহীহ বুখারী: ৩৬৩৬]",
            "হিজরতের রাতে সাওর গুহায় মাকড়সার জাল ও 'ভয় পেয়ো না, আল্লাহ আমাদের সাথে আছেন' [সূরা তাওবা: ৪০]"
        ]
    },
    {
        "category": "misconceptions",
        "label": "প্রচলিত ভুল ধারণা ও সহীহ সুন্নাহ",
        "description": "আমাদের সমাজে প্রচলিত ভিত্তিহীন কুসংস্কার, বিদআত বনাম রাসূল (ﷺ)-এর প্রমাণিত সহীহ আমল",
        "seed_concepts": [
            "বিড়াল রাস্তা কাটলে বা চোখ নাচলে অমঙ্গল মনে করার কুসংস্কারের বিরুদ্ধে ইসলামের বিধান [সহীহ মুসলিম: ২২২৪]",
            "শবে বরাতে নির্দিষ্ট নিয়মে নামাজ পড়ার কোনো সহীহ ভিত্তি আছে কি না [সহীহ সুন্নাহ বিশ্লেষণ]",
            "কবর পাকা করা বা মাজারে মানত করার ব্যাপারে ইসলামের কঠোর সতর্কতা [সহীহ মুসলিম: ৯৭০]",
            "জাদু-টোনা কাটানোর নামে ধোঁকাবাজ তান্ত্রিক বা গণকের কাছে যাওয়ার ভয়ংকর পরিণতি [সহীহ মুসলিম: ২২৩০]",
            "মুসাফাহা করার পর বুকে হাত দেওয়ার প্রচলিত রীতি কি সুন্নাহসম্মত? [সহীহ হাদিস যাচাই]"
        ]
    },
    {
        "category": "character_dealings",
        "label": "উত্তম চরিত্র, সততা ও মোয়ামালাত",
        "description": "ব্যবসা-বাণিজ্যে সততা, প্রতিবেশীর হক, পিতা-মাতার মর্যাদা, মানুষকে ক্ষমা করার বিশাল সওয়াব",
        "seed_concepts": [
            "ব্যবসা ও লেনদেনে সত্যবাদী ও বিশ্বস্ত বণিকের হাশর হবে নবী ও শহীদদের সাথে [জামে আত-তিরমিযী: ১২০৯]",
            "পিতা-মাতার দিকে কেবল একটি ভালোবাসার দৃষ্টিতে কবুল হজের সওয়াব [শুআবুল ঈমান: ৭৮৫৯]",
            "প্রতিবেশীকে কষ্ট দিয়ে যে ব্যক্তি রাতে শান্তিতে ঘুমায় সে মুমিন নয় [সহীহ মুসলিম: ৪৬]",
            "প্রচণ্ড রাগের মুহূর্তে যে ব্যক্তি নিজেকে নিয়ন্ত্রণ করে সেই আসল বীর [সহীহ বুখারী: ৬১১৪]",
            "কাউকে অন্যায়ভাবে গীবত বা অপমান করার কারণে কিয়ামতে নেকি ছিনিয়ে নেওয়ার ভয়ংকর দৃশ্য [সহীহ মুসলিম: ২৫৮১]"
        ]
    },
    {
        "category": "crises_debt_turnaround",
        "label": "সংকট, ঋণ ও মোড় ঘোরানো দোয়া",
        "description": "দেয়ালে পিঠ ঠেকে যাওয়া কঠিন বিপদ, পাহাড়সম ঋণমুক্তি, ইসমে আজম ও তাৎক্ষণিক কবুল হওয়া দোয়া",
        "seed_concepts": [
            "দেয়ালে পিঠ ঠেকে গেলে ও অসম্ভব বিপদ কাটাতে ইউনুস (আ.)-এর সেই বিশেষ দোয়া [জামে আত-তিরমিযী: ৩৫০৫]",
            "পাহাড় পরিমাণ ঋণের বোঝা থাকলেও তা পরিশোধে সাহায্য করার জাদুকরী দোয়া [জামে আত-তিরমিযী: ৩৫৬০]",
            "আল্লাহর সেই বিশেষ গোপন নাম যা দিয়ে দোয়া করলে কোনো দোয়া ফেরত দেওয়া হয় না (ইসমে আজম) [সুনান আবু দাউদ: ১৪৯৩]",
            "জুমার দিনের আসর থেকে মাগরিবের মধ্যবর্তী সেই বিশেষ মুহূর্ত—যখন কোনো দোয়া ফিরিয়ে দেওয়া হয় না [সুনান আবু দাউদ: ১০৪৮]",
            "মনের তীব্র দুশ্চিন্তা, হতাশা ও অভাব কাটাতে নবীজি (সা.)-এর শেখানো দোয়া [সহীহ বুখারী: ৬৩৬৩]",
            "সাইয়্যিদুল ইস্তিগফার: ক্ষমার শ্রেষ্ঠ দোয়া যা বিশ্বাস সহকারে রাতে পড়লে জান্নাত ওয়াজিব [সহীহ বুখারী: ৬৩০৬]"
        ]
    },
    {
        "category": "daily_sunnah",
        "label": "দৈনন্দিন ছোট আমলের পাহাড়সমান সওয়াব",
        "description": "মাত্র ২ মিনিটে করা যায় এমন সহজ দৈনন্দিন সুন্নাহ ও জিকির যার সওয়াব ও প্রতিদান অপরিসীম",
        "seed_concepts": [
            "অযুর পর মাত্র ১টি বাক্য পাঠ করলে জান্নাতের ৮টি দরজার যেকোনোটি দিয়ে প্রবেশের অধিকার [সহীহ মুসলিম: ২৩৪]",
            "মাত্র ১ মিনিট সময় নিয়ে সুবহানাল্লাহি ওয়া বিহামদিহি ১০০ বার পড়লে সমুদ্রের ফেনা পরিমাণ গুনাহ মাফ [সহীহ বুখারী: ৬৪০৫]",
            "ঘরে প্রবেশ করার সময় সালাম দিলে দারিদ্র্য দূর হয় ও শয়তানের প্রবেশ বন্ধ হয় [জামে আত-তিরমিযী: ২৬৯৮]",
            "মানুষকে দেখে হাসিমুখে তাকানোও একটি সদকা [জামে আত-তিরমিযী: ১৯৫৬]",
            "ফরজ সালাতের পর আয়াতুল কুরসি পাঠকারী ব্যক্তির জান্নাতে প্রবেশে একমাত্র বাধা তার মৃত্যু [সুনান নাসাঈ: ৯৯২৮]"
        ]
    },
    {
        "category": "family_marriage_sunnah",
        "label": "দাম্পত্য সুখ, পরিবার ও আচরণ",
        "description": "দাম্পত্য জীবনে ভালোবাসা বাড়ানোর সুন্নাহ, পরিবারে শান্তি ও নেককার সন্তান পাওয়ার দিকনির্দেশনা",
        "seed_concepts": [
            "সারাদিনের ক্লান্তি শেষে ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়াও সদকা [সহীহ বুখারী: ৫৩৫৪]",
            "পরিবারে শান্তি ও নেককার সন্তান পাওয়ার শ্রেষ্ঠ কুরআনীয় দোয়া [সূরা আল-ফুরকান: ৭৪]",
            "উত্তম চরিত্র ও সুন্দর ব্যবহারের চেয়ে মিজানের পাল্লায় ভারী কিছু নেই [জামে আত-তিরমিযী: ২০০২]",
            "সন্তানদের মাঝে ইনসাফ ও সমতা বজায় রাখার বিষয়ে নবীজি (ﷺ)-এর কঠোর নির্দেশ [সহীহ বুখারী: ২৫৮৭]"
        ]
    }
]

PILLARS = ALL_DIVERSE_ISLAMIC_PILLARS

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

THE WINNING VIRAL HOOK FORMULA (MANDATORY):
1. The Relatable Moment: A specific urgent human situation everyone experiences (e.g. 'রাতে হঠাৎ ঘুম ভেঙে গেলে', 'বদনজর ও হিংসার ক্ষতিকর প্রভাব', 'অসম্ভব ঋণ ও টানাপোড়েন').
2. The Prophet's Solution: Direct connection to Rasulullah (ﷺ)'s specific Sahih Hadith / Dua.
3. The Irresistible Payoff: The dramatic life-changing reward ('তা কখনো ফিরিয়ে দেওয়া হয় না', 'জীবনের মোড় ঘুরিয়ে দেওয়া আমল', 'সারাদিনের জন্য আল্লাহর নিরাপত্তা').

FRESH TOPIC SEED INSPIRATIONS:
{seed_text}

Rules:
- Backed strictly by authentic Quran verses or Sahih Hadith only
- Emotionally gripping, high-CTR Bengali title (max 12 words)
- 100% unique core concept — MUST NOT be a thematic clone of any recently covered topic
{avoid_section}

Respond with ONLY valid JSON (no markdown formatting, no other text):
{{
    "title": "ভিডিওর জন্য আকর্ষণীয় ও ক্লিক করার মতো বাংলা শিরোনাম (সর্বোচ্চ ১২ শব্দ)",
    "core_concept": "এক লাইনে মূল হাদিস বা ঘটনার মূল বিষয়বস্তু",
    "category": "{pillar['category']}",
    "hook_category": "relatable_moment",
    "reference": "সহীহ তথ্যসূত্র (উদা: সহীহ বুখারী: ১১৫৪ / সহীহ মুসলিম: ২২৬১)",
    "why_relevant": "কেন এই মুহূর্তে সাধারণ মানুষের জন্য এই আমলটি অত্যন্ত প্রয়োজনীয়"
}}"""

    user_prompt = f"Generate ONE unique, viral, highly relatable topic for pillar '{pillar['label']}'. Ensure the title follows 'The Winning Viral Hook Formula'."
    res = extract_json(system_prompt, user_prompt, max_tokens=600)
    if res and res.get("title"):
        return res
    return None

def discover_topics(limit: int = 1):
    """
    Picks the next pillar in round-robin sequence from Supabase history and generates a unique topic.
    """
    logger.info("Discovering fresh topic using The Winning Viral Hook Formula...")
    
    # 1. Get recent titles from Supabase to prevent repeats
    recent_titles = get_recent_video_titles(limit=50)
    
    # 2. Pick next pillar in round-robin order
    pillar = get_next_pillar_from_history(PILLARS, pillar_type="video")
    logger.info(f"Selected Pillar: {pillar['label']} ({pillar['category']})")
    
    from app.history import is_topic_duplicate_global
    topic_data = None
    for attempt in range(3):
        topic_cand = generate_topic_for_pillar(pillar, recent_titles)
        if topic_cand and topic_cand.get("title"):
            cand_title = topic_cand.get("title", "").strip()
            if is_topic_duplicate_global(cand_title):
                logger.warning(f"Attempt {attempt+1}: Discovered topic '{cand_title}' flagged as duplicate in global history! Retrying...")
                continue
            topic_data = topic_cand
            break

    if not topic_data:
        logger.warning(f"Using filtered seed fallback for {pillar['label']}...")
        seeds = pillar.get("seed_concepts", ["রাতে হঠাৎ ঘুম ভেঙে গেলে নবীজির বিশেষ দোয়া"])
        valid_seed = None
        for s in seeds:
            st = s.split("[")[0].strip()
            if not is_topic_duplicate_global(st):
                valid_seed = s
                break
        if not valid_seed:
            valid_seed = random.choice(seeds)
            
        topic_data = {
            "title": valid_seed.split("[")[0].strip(),
            "core_concept": valid_seed,
            "category": pillar["category"],
            "hook_category": "relatable_moment",
            "reference": "সহীহ বুখারী",
            "why_relevant": "দৈনন্দিন জীবনে তাৎক্ষণিক আমল"
        }
        
    title = topic_data.get("title", "").strip()
    category = topic_data.get("category", pillar["category"])
    core_concept = topic_data.get("core_concept", "")
    
    # 4. Save to local SQLite database
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO topics (title, source, score, status) VALUES (?, ?, ?, ?)",
            (title, f"ai_discovered_{category}", 9.5, "DISCOVERED")
        )
        conn.commit()
        cursor.execute("SELECT id FROM topics WHERE title = ? ORDER BY id DESC LIMIT 1", (title,))
        row = cursor.fetchone()
        topic_id = row[0] if row else 1
    except Exception as e:
        logger.warning(f"Database insert note: {e}")
        topic_id = 1
    finally:
        conn.close()
        
    # 5. Record to Supabase cloud history
    record_video_history(title=title, category=category, core_concept=core_concept)
    
    topic_data["id"] = topic_id
    logger.info(f"Discovered and recorded topic ID {topic_id}: '{title}'")
    return [topic_data]

def run_discovery() -> dict | None:
    """Convenience alias for main pipeline: returns a single discovered topic dict."""
    topics = discover_topics(1)
    return topics[0] if topics else None

if __name__ == "__main__":
    topics = discover_topics(1)
    print(json.dumps(topics, ensure_ascii=False, indent=2))
