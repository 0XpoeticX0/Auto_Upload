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
ACTIVE_VIRAL_MOMENT_PILLARS = [
    {
        "category": "night_sleep_moments",
        "label": "রাত ও ঘুমের অলৌকিক আমল",
        "description": "মাঝরাতে হঠাৎ ঘুম ভাঙলে, দুঃস্বপ্ন দেখলে, ঘুম না আসলে, গভীর রাতের অস্থিরতা ও মোড় ঘোরানো দোয়া",
        "seed_concepts": [
            "রাতে হঠাৎ ঘুম ভেঙে গেলে নবীজি (সা.)-এর শেখানো সেই বিশেষ দোয়া যা সাথে সাথে কবুল হয় [সহীহ বুখারী: ১১৫৪]",
            "দুঃস্বপ্ন বা ভয়ংকর স্বপ্ন দেখলে নবীজির নির্দেশিত ৩টি তাত্ক্ষণিক আমল [সহীহ মুসলিম: ২২৬১]",
            "বিছানায় যাওয়ার পর ঘুম না আসলে ও গভীর রাতে মনের অস্থিরতা কাটাতে নবীজির আমল [জামে আত-তিরমিযী: ৩৫২৮]",
            "ঘুমন্ত মানুষের মাথায় শয়তানের দেওয়া ৩টি গিঁট খোলার সহজ সুন্নাহ কৌশল [সহীহ বুখারী: ১১৪২]",
            "ঘুমানোর আগে দুই তালুতে ৩ কুল পড়ে সারা শরীর মুছে নেওয়ার বরকতময় সুন্নাহ [সহীহ বুখারী: ৫০১৭]",
            "মধ্যরাতে ভয় বা আতঙ্কে চমকে উঠলে পাঠ করার বিশেষ সহীহ দোয়া [সুনান আবু দাউদ: ৩৮৯৩]",
            "তাহাজ্জুদের শেষ প্রহরে বান্দার অশ্রু বিসর্জন ও আল্লাহর প্রথম আসমানে নেমে আসার ক্ষণ [সহীহ বুখারী: ১১৪৫]",
            "ঘুমানোর পূর্বে সূরা মুলক তেলাওয়াত করলে কবরের সমস্ত আজাব থেকে মুক্তি [সুনান আত-তিরমিযী: ২৮৯১]"
        ]
    },
    {
        "category": "protection_evil_eye",
        "label": "বদনজর, হিংসা ও আত্মরক্ষা",
        "description": "বদনজর, কুদৃষ্টি, হিংসা, জাদু ও অদৃশ্য অনিষ্ট থেকে পরিবার ও নিজের সুরক্ষায় নবীজির শেখানো আমল",
        "seed_concepts": [
            "বদনজর ও হিংসার ক্ষতিকর প্রভাব থেকে নিজেকে ও পরিবারকে সুরক্ষিত রাখার কার্যকর দোয়া [সহীহ বুখারী: ৩৩৭৪]",
            "সুন্দর কিছু দেখলে নিজের অজান্তেই যাতে বদনজর না লাগে—নবীজির শেখানো বরকতময় দোয়া [মুয়াত্তা মালিক]",
            "ঘর থেকে বের হওয়ার সময় মাত্র ১টি বাক্য যা সারাদিন শয়তানের হাত থেকে বাঁচায় [সুনান আবু দাউদ: ৫০৯৫]",
            "খাবার ও পানীয়তে ক্ষতি বা বিষ থেকে বাঁচতে নবীজির সকাল-সন্ধ্যার সুরক্ষা দোয়া [জামে আত-তিরমিযী: ৩৩৪৭]",
            "ছোট বাচ্চাদের বদনজর ও রোগবালাই থেকে রক্ষা করতে নবীজির শেখানো বিশেষ দোয়া [সহীহ বুখারী: ৩৩৭১]",
            "শরীরের কোনো স্থানে তীব্র ব্যথা বা অসুখ হলে হাত রেখে নবীজির শেখানো রুকইয়াহ [সহীহ মুসলিম: ২২০২]",
            "যে ঘরে সূরা বাকারা পড়া হয় সেখান থেকে শয়তানের পলায়ন [সহীহ মুসলিম: ৭৮০]"
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
            "লা হাওলা ওয়ালা কুওয়াতা ইল্লা বিল্লাহ: আরশের নিচের অফুরন্ত গুপ্তধন [সহীহ বুখারী: ৪২০৫]",
            "সাইয়্যিদুল ইস্তিগফার: ক্ষমার শ্রেষ্ঠ দোয়া যা বিশ্বাস সহকারে রাতে পড়লে জান্নাত ওয়াজিব [সহীহ বুখারী: ৬৩০৬]"
        ]
    },
    {
        "category": "family_marriage_sunnah",
        "label": "দাম্পত্য সুখ, পরিবার ও আচরণ",
        "description": "দাম্পত্য জীবনে ভালোবাসা বাড়ানোর সুন্নাহ, রাগের মুহূর্তে সংযম, পিতা-মাতার অধিকার ও ঘরে বরকত",
        "seed_concepts": [
            "সারাদিনের ক্লান্তি শেষে ঘরে ফিরে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়াও সদকা [সহীহ বুখারী: ৫৩৫৪]",
            "প্রচণ্ড রাগের মুহূর্তে যে ৩টি কাজ ও কথা ইসলামে কঠোরভাবে নিষেধ [সহীহ বুখারী: ৬১১৬]",
            "পিতা-মাতার দিকে কেবল ১টি ভালোবাসার দৃষ্টিতে কবুল হজের সওয়াব [শুআবুল ঈমান: ৭৮৫৯]",
            "ঘরে প্রবেশ করে পরিবারকে হাসিমুখে সালাম দিলে শয়তানের পলায়ন ও বরকত বৃদ্ধি [জামে আত-তিরমিযী: ২৬৯৮]",
            "পরিবারে শান্তি ও নেককার সন্তান পাওয়ার শ্রেষ্ঠ কুরআনীয় দোয়া [সূরা আল-ফুরকান: ৭৪]",
            "উত্তম চরিত্র ও সুন্দর ব্যবহারের চেয়ে মিজানের পাল্লায় ভারী কিছু নেই [জামে আত-তিরমিযী: ২০০২]"
        ]
    }
]

# Active rotating pillars set exclusively to the Winning Moment Clusters
PILLARS = ACTIVE_VIRAL_MOMENT_PILLARS

# ==============================================================================
# ARCHIVED GENERAL PILLARS (Preserved safely for future reference)
# ==============================================================================
ARCHIVED_GENERAL_PILLARS = [
    {
        "category": "daily_life",
        "label": "দৈনন্দিন জীবন",
        "description": "হালাল/হারাম, সম্পর্ক, আচরণ, লেনদেন, নামাজ-রোজার ফজিলত, পরিবার, পিতা-মাতার হক"
    },
    {
        "category": "islamic_knowledge",
        "label": "শেষ যামানা ও আখিরাত",
        "description": "কিয়ামতের আলামত, কবরের জীবন, জান্নাত-জাহান্নামের বর্ণনা, দাজ্জাল, ফেরেশতা ও সৃষ্টিজগৎ"
    },
    {
        "category": "misconceptions",
        "label": "হালাল/হারাম ভ্রান্তি",
        "description": "যেগুলো মানুষ হারাম মনে করে কিন্তু আসলে হালাল, এবং যেগুলো হালাল ভাবে কিন্তু আসলে হারাম"
    },
    {
        "category": "islamic_stories",
        "label": "সত্যিকারের ইসলামিক গল্প",
        "description": "কুরআনে বর্ণিত নবীদের কাহিনী, সাহাবাদের বাস্তব ঘটনা"
    },
    {
        "category": "seerah",
        "label": "নবীজির জীবন ও সীরাহ",
        "description": "নবী মুহাম্মদ (সা.)-এর জীবনের সত্যিকারের ঘটনা ও সীরাহ"
    },
    {
        "category": "youth_modern",
        "label": "তরুণ প্রজন্ম ও আধুনিক জীবন",
        "description": "বিষণ্নতা, একাকীত্ব, সোশ্যাল মিডিয়া আসক্তি, ক্যারিয়ার চাপ ও আধুনিক জীবনের চ্যালেঞ্জ"
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
