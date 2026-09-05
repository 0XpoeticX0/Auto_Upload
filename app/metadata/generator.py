# -*- coding: utf-8 -*-
import json
import re
from app.llm.provider import extract_json
from app.logger import logger

def format_video_description(metadata_desc: str, script_data: dict, english_summary: str = "") -> str:
    """
    Builds the exact same viral caption format used for photo posts.
    Format: Hook 🌿 → Narrator + Quote → ✨ Arabic/Dua (উচ্চারণ + অর্থ) → 📖 Sources → 💡 শিক্ষা ও আমল → 💬 CTA → ━━━━━━━━━━━━━━━━━━━━ → @DailyDosOfIslam → Hashtags
    """
    # 1. Hook title line
    title = script_data.get("title", script_data.get("title_bn", "")).strip()
    hook_line = metadata_desc.strip().split("\n")[0].strip() if metadata_desc else title
    if "#" in hook_line:
        hook_line = hook_line.split("#")[0].strip()
    if not (hook_line.endswith("🌿") or hook_line.endswith("✨") or hook_line.endswith("🌙")):
        hook_line = f"{hook_line} 🌿"

    # 2. Extract Arabic, Pronunciation, Meaning (from direct keys or <ARABIC>...</ARABIC> tags inside scenes)
    arabic_text = script_data.get("arabic_text", "").strip()
    pronunciation = script_data.get("pronunciation", "").strip()
    translation = script_data.get("translation", script_data.get("meaning", "")).strip()

    # Search through scenes for <ARABIC> blocks (find the main one, not the closing dhikr)
    if not arabic_text or not translation:
        for sc in script_data.get("scenes", []):
            narr = sc.get("narration", "")
            if "<ARABIC>" in narr and "</ARABIC>" in narr:
                tags = re.findall(r"<ARABIC>(.*?)</ARABIC>", narr, flags=re.DOTALL)
                for tag in tags:
                    lines = [l.strip() for l in tag.strip().split("\n") if l.strip()]
                    if len(lines) >= 3:
                        arabic_text = lines[0]
                        pronunciation = lines[1].strip("()")
                        translation = lines[2].strip("()")
                        break
                    elif len(lines) == 2 and not arabic_text:
                        arabic_text = lines[0]
                        pronunciation = lines[1].strip("()")
            if arabic_text and translation:
                break

    arabic_block = ""
    if arabic_text:
        arabic_block = f"\n\n✨ সেই বরকতময় বাক্য / দোয়াটি:\n{arabic_text}"
        if pronunciation:
            arabic_block += f'\nউচ্চারণ: "{pronunciation}"\n'
        if translation:
            arabic_block += f'\nঅর্থ: "{translation}"'

    # 3. Narrator / Hadith intro block (if not already covered by hook)
    narrator = script_data.get("header", script_data.get("narrator", "")).strip()
    quote = script_data.get("quote", script_data.get("hadith_text", "")).strip()
    narrator_block = ""
    if narrator and quote:
        narrator_block = f"\n\n{narrator}\n\"{quote}\""
    elif narrator:
        narrator_block = f"\n\n{narrator}"

    # 4. Sahih References
    raw_refs = script_data.get("references", [script_data.get("reference", "")])
    if isinstance(raw_refs, str):
        raw_refs = [raw_refs]
    valid_refs = [r.strip() for r in raw_refs if r and str(r).strip()]

    ref_block = "\n\n📖 সহীহ তথ্যসূত্র:"
    if valid_refs:
        ref_block += "\n" + "\n".join([f"• {r}" for r in valid_refs])
    else:
        ref_block += "\n• সহীহ বুখারী ও সহীহ মুসলিম"

    # 5. শিক্ষা ও আমল (Practical takeaway)
    explanation = script_data.get("explanation", script_data.get("lesson", "")).strip()
    if not explanation:
        # Check Scene 3 for the practical lesson
        for sc in script_data.get("scenes", []):
            if sc.get("scene_number") == 3:
                explanation = sc.get("narration", "").strip()
                break
    if not explanation:
        lines = [l.strip() for l in metadata_desc.strip().split("\n") if l.strip() and "#" not in l]
        explanation = " ".join(lines[1:3]) if len(lines) > 1 else ""

    lesson_block = ""
    if explanation:
        lesson_block = f"\n\n💡 শিক্ষা ও আমল:\n{explanation}"

    # 6. Interactive CTA comment prompt
    dhikr = "সুবহানাল্লাহ"
    combined_text = f"{quote} {explanation} {title} {translation}"
    if "আলহামদুলিল্লাহ" in combined_text:
        dhikr = "আলহামদুলিল্লাহ"
    elif "ইস্তিগফার" in combined_text or "ক্ষমা" in combined_text:
        dhikr = "আস্তাগফিরুল্লাহ"
    cta_block = f'\n\n💬 আজকের আমল ও দাওয়াত:\nপরবর্তীতে আমল করার জন্য পোস্টটি Save করে রাখুন এবং বন্ধুদের সাথে শেয়ার করুন। রাসূলুল্লাহ (ﷺ) বলেছেন: “যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।” [সহীহ মুসলিম: ১৮৯৩] 🤍'

    # 7. Topic-specific hashtag
    category = str(script_data.get("category", "")).lower()
    topic_tag_map = {
        "dreams_and_sleep": "#ঘুমেরসুন্নাহ",
        "dua_cures": "#দোয়া",
        "heart_softeners": "#তাওবা",
        "islamic_knowledge": "#ইসলামিকজ্ঞান",
        "protection_ruqyah": "#রুকইয়াহ",
        "rizq_barakah": "#রিজিক",
        "husband_wife_family": "#দাম্পত্যসুখ #পরিবার",
        "relationships": "#দাম্পত্যসুখ #পরিবার",
        "halal_haram_daily": "#হালালহারাম",
        "seerah": "#সীরাহ",
        "islamic_stories": "#ইসলামিককাহিনী",
    }
    topic_tag = topic_tag_map.get(category, "#ইসলামিক")

    # 8. Footer divider, Follow CTA and Curated Hashtags
    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━"
        f"\n📌 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য ফলো করুন:"
        f"\n👉 @dailydos_islam"
        f"\n\n#DeenOverDunya #IslamicReminders #MuslimUmmah #Sunnah #সহীহ_হাদিস #দ্বীন_ইসলাম #কুরআনের_আলো #ইসলামিকপোস্ট #DailyDos {topic_tag}"
    )

    return f"{hook_line}{narrator_block}{arabic_block}{ref_block}{lesson_block}{cta_block}{footer}".strip()

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
    "description": "ক্লান্ত দিনের শেষে স্ত্রীর মুখে এক লোকমা খাবার তুলে দেওয়া বা হাসিমুখে কথা বলাও যে কত বড় ইবাদত!...",
    "pinned_comment": "সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন—রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿",
    "english_title": "Feeding Your Wife is Charity in Islam #Shorts",
    "english_description": "A short and profound Islamic reminder on marriage Sunnah and daily rewards. Subscribe for daily Sahih Islamic reminders.",
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
        metadata["pinned_comment"] = "সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন—রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿"
        
    if "youtube_title" in metadata:
        yt_t = metadata["youtube_title"].strip()
        if "#Shorts" not in yt_t and "#shorts" not in yt_t:
            yt_t = f"{yt_t} #Shorts"
        metadata["youtube_title"] = yt_t[:100]
        
    return metadata
