import json
import re
from app.llm.provider import extract_json
from app.logger import logger

def format_video_description(metadata_desc: str, script_data: dict, english_summary: str = "") -> str:
    """
    Builds a professional, aesthetic, and algorithm-friendly description adhering to the new standard.
    """
    # 1. Main hook / summary
    main_summary = metadata_desc.strip()
    # Remove old hashtag sections if present
    if "#" in main_summary:
        main_summary = main_summary.split("#")[0].strip()
        
    # 2. Extract Arabic, Pronunciation, Meaning
    arabic_text = script_data.get("arabic_text", "")
    pronunciation = script_data.get("pronunciation", "")
    translation = script_data.get("translation", "")
    
    # If not in top-level script_data, look inside scenes
    if not arabic_text:
        for sc in script_data.get("scenes", []):
            if sc.get("arabic_text"):
                arabic_text = sc.get("arabic_text")
                pronunciation = sc.get("pronunciation", pronunciation)
                translation = sc.get("translation", translation)
                break
                
    ayah_hadith_block = ""
    if arabic_text:
        ayah_hadith_block = f"\n\n🌿 মূল বাক্য / আয়াত ও হাদিস:\n{arabic_text}"
        if pronunciation:
            ayah_hadith_block += f'\nউচ্চারণ: "{pronunciation}"'
        if translation:
            ayah_hadith_block += f'\nঅর্থ: "{translation}"'
            
    # 3. Sahih References
    raw_refs = script_data.get("references", [script_data.get("reference", "")])
    if isinstance(raw_refs, str):
        raw_refs = [raw_refs]
    valid_refs = [r.strip() for r in raw_refs if r and str(r).strip()]
    
    ref_block = "\n\n📖 সহীহ রেফারেন্স:\n"
    if valid_refs:
        ref_block += "\n".join([f"• {r}" for r in valid_refs])
    else:
        ref_block += "• কুরআনুল কারীম ও সহীহ হাদিস"
        
    # 4. CTA Block
    cta_block = "\n\n💬 আজকের আমল:\nকমেন্টে একবার 'সুবহানাল্লাহ' লিখে আপনার বন্ধুদের সাথে শেয়ার করুন এবং নেকির অংশীদার হোন 🤍"

    # 5. English Translation Summary (For Global Search Discovery)
    en_block = ""
    if english_summary:
        en_block = f"\n\n✨ In English:\n{english_summary.strip()}"

    # 6. Social Links & High-Traffic Niche + Bengali Hashtags
    social_block = f"{en_block}\n\n━━━━━━━━━━━━━━━━━━━━\n📌 আমাদের সাথে যুক্ত থাকুন:\n🔹 YouTube: https://www.youtube.com/@DailyDosOfIslam\n🔹 Facebook: https://www.facebook.com/DailyDosOfIslam\n\n#Shorts #IslamicReminders #SahihHadith #BanglaIslamic #সহীহ_হাদিস #দোয়া #DailyDos #DeenOverDunya #ShortsFeed #ExplorePage"

    return f"{main_summary}{ayah_hadith_block}{ref_block}{cta_block}\n\n{social_block}".strip()

def generate_viral_metadata(topic_id: int, script_data: dict):
    logger.info("Generating viral metadata in Bangla & English localizations for YouTube and Facebook...")
    
    system_prompt = """You are an expert viral Social Media Manager for Bengali Islamic content on YouTube Shorts and Facebook Reels.
Generate a highly clickable, emotionally charged title, description hook, pinned comment, thumbnail hook, English SEO translation, and tags.

CRITICAL RULES:
- Primary YouTube/Facebook title and description MUST be 100% in authentic BANGLA (বাংলা).
- Make the title short, curiosity-inducing, and deeply engaging (4 to 8 Bangla words).
- Description hook: 2-3 engaging Bangla sentences summarizing the video's message and core spiritual reflection.
- Pinned comment: A warm, engagement-driving comment asking viewers to recite a specific Dhikr/Dua in the comments.
- English Title & Description: Clear, searchable English translations for YouTube's global search localization.

Output JSON format (ONLY valid JSON):
{
    "youtube_title": "ক্লিক করার মতো আকর্ষণীয় বাংলা শিরোনাম (সর্বোচ্চ ৬০ অক্ষর)",
    "facebook_title": "ফেসবুক রিলসের জন্য মন ছুঁয়ে যাওয়া বাংলা শিরোনাম",
    "description": "কিয়ামতের দিন মিজানের পাল্লায় ভারী হওয়ার মতো সহজ ও বরকতময় আমল শিখিয়েছেন প্রিয় নবীজি...",
    "pinned_comment": "কমেন্টে একবার 'সুবহানাল্লাহ' / 'আলহামদুলিল্লাহ' লিখে সদকায়ে জারিয়া হিসেবে বন্ধুদের সাথে শেয়ার করুন 🌿",
    "english_title": "Virtues of Two Blessed Words Beloved to Allah #Shorts",
    "english_description": "A short and profound Islamic reminder on easy daily deeds with immense rewards. Subscribe for daily Sahih Islamic reminders.",
    "thumbnail_hook": "২-৩ শব্দের বাংলা হুক",
    "tags": ["Shorts", "IslamicReminders", "SahihHadith", "BanglaIslamic", "সহীহ_হাদিস", "দোয়া", "DailyDos", "DeenOverDunya", "ShortsFeed", "ExplorePage", "ইসলামিক"]
}"""
    
    narrations = " ".join([scene.get("narration", scene.get("narration_bn", "")) for scene in script_data.get("scenes", [])])
    title = script_data.get('title', script_data.get('title_bn', ''))
    user_prompt = f"ভিডিওর শিরোনাম ও বিষয়:\n{title}\n\nভিডিওর সম্পূর্ণ স্ক্রিপ্ট:\n{narrations}\n\nসম্পূর্ণ বাংলায় ভাইরাল মেটাডাটা ও ইংরেজি লোকালাইজেশন তৈরি করুন।"
    
    metadata = extract_json(system_prompt, user_prompt, max_tokens=1200)
    if not metadata:
        logger.error("Failed to generate metadata.")
        return None
        
    raw_desc = metadata.get("description", "")
    metadata["description"] = format_video_description(raw_desc, script_data, english_summary=metadata.get("english_description", ""))
    
    if not metadata.get("pinned_comment"):
        metadata["pinned_comment"] = "কমেন্টে একবার 'সুবহানাল্লাহ' / 'আলহামদুলিল্লাহ' লিখে সদকায়ে জারিয়া হিসেবে বন্ধুদের সাথে শেয়ার করুন 🌿"
        
    if "youtube_title" in metadata:
        yt_t = metadata["youtube_title"].strip()
        if "#Shorts" not in yt_t and "#shorts" not in yt_t:
            yt_t = f"{yt_t} #Shorts"
        metadata["youtube_title"] = yt_t[:100]
        
    return metadata
