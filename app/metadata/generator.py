import json
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_viral_metadata(topic_id: int, script_data: dict):
    logger.info("Generating viral metadata in Bangla for YouTube and Facebook...")
    
    system_prompt = """You are an expert viral Social Media Manager for Bengali Islamic content on YouTube Shorts and Facebook Reels.
Generate a highly clickable, emotionally charged title, description, thumbnail hook, and tags STRICTLY in Bengali (বাংলা).

CRITICAL RULES:
- ALL titles, descriptions, and thumbnail hooks MUST be 100% in BANGLA (বাংলা). NO ENGLISH words in titles or descriptions.
- Make the title short, curiosity-inducing, and deeply engaging (4 to 8 Bangla words).
- Examples of good Bangla titles:
  * "কিয়ামতের ভয়ংকর নিদর্শন: তওবার দরজা কখন বন্ধ হবে?"
  * "আল্লাহর সবচেয়ে প্রিয় দুটি সহজ বাক্য যা সবার জানা উচিত"
  * "মন খারাপ ও দুশ্চিন্তা দূর করার কার্যকরী নববী আমল"
- Description: Write 2-3 engaging Bangla sentences summarizing the video's message, followed by an inspiring Islamic reminder in Bangla, then relevant hashtags.
- Thumbnail Hook: 2-3 evocative Bangla words for the thumbnail (e.g. "তওবার শেষ সময়?", "দুশ্চিন্তা মুক্তি").

Output JSON format (ONLY valid JSON):
{
    "youtube_title": "ক্লিক করার মতো আকর্ষণীয় বাংলা শিরোনাম (সর্বোচ্চ ৬০ অক্ষর)",
    "facebook_title": "ফেসবুক রিলসের জন্য মন ছুঁয়ে যাওয়া বাংলা শিরোনাম",
    "description": "ভিডিওর মূল বার্তা নিয়ে সংক্ষিপ্ত ও অনুপ্রেরণাদায়ী বাংলা বিবরণী... প্রতিদিনের সুন্দর ইসলামিক রিমাইন্ডারের জন্য পেজটি ফলো করুন। #Shorts #Islam #IslamicReminders #বাংলা",
    "thumbnail_hook": "২-৩ শব্দের বাংলা হুক",
    "tags": ["ইসলামিক", "কুরআন", "হাদিস", "দোয়া", "Shorts", "Islamic"]
}
"""
    
    narrations = " ".join([scene.get("narration", scene.get("narration_bn", "")) for scene in script_data.get("scenes", [])])
    title = script_data.get('title', script_data.get('title_bn', ''))
    user_prompt = f"ভিডিওর শিরোনাম ও বিষয়:\n{title}\n\nভিডিওর সম্পূর্ণ স্ক্রিপ্ট:\n{narrations}\n\nসম্পূর্ণ বাংলায় ভাইরাল মেটাডাটা তৈরি করুন।"
    
    metadata = extract_json(system_prompt, user_prompt, max_tokens=1000)
    if not metadata:
        logger.error("Failed to generate metadata.")
        return None
        
    references = script_data.get("references", [script_data.get("reference", "")])
    references = [r for r in references if r]
    
    ref_text = "\n\n📚 সহীহ তথ্যসূত্র:\n"
    if references:
        ref_text += "\n".join([f"- {r}" for r in references]) + "\n\n"
    else:
        ref_text += "- কুরআন ও সহীহ হাদিস\n\n"
        
    social_links = "🔔 ইউটিউবে সাবস্ক্রাইব করুন: https://www.youtube.com/@dailydos-no1\n👍 ফেসবুকে ফলো করুন: https://www.facebook.com/DailyDosNo1\n\n"
    
    injection_text = ref_text + social_links
    
    if "description" in metadata:
        parts = metadata["description"].split("#")
        main_desc = parts[0].strip()
        hashtags = " #" + " #".join([p.strip() for p in parts[1:]]) if len(parts) > 1 else "\n#Shorts #Islamic #Bangla #Quran #Hadith"
        metadata["description"] = f"{main_desc}\n{injection_text}{hashtags}".strip()
        
    if "youtube_title" in metadata:
        yt_t = metadata["youtube_title"].strip()
        if "#Shorts" not in yt_t and "#shorts" not in yt_t:
            yt_t = f"{yt_t} #Shorts"
        metadata["youtube_title"] = yt_t[:100]
        
    return metadata
