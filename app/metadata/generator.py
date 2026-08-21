# -*- coding: utf-8 -*-
import json
import re
from app.llm.provider import extract_json
from app.logger import logger

def format_video_description(metadata_desc: str, script_data: dict, english_summary: str = "") -> str:
    """
    Builds the exact same viral caption format used for photo posts.
    Format: Hook 🌿 → Narrator + Quote → ✨ Arabic/Dua → 📖 Sources → 💡 শিক্ষা → 💬 CTA → ━━━━━━━━━━━━━━━━━━━━ → @DailyDosOfIslam → Hashtags
    """
    # 1. Hook title line
    title = script_data.get("title", script_data.get("title_bn", "")).strip()
    hook_line = metadata_desc.strip().split("\n")[0].strip() if metadata_desc else title
    if "#" in hook_line:
        hook_line = hook_line.split("#")[0].strip()
    if not (hook_line.endswith("🌿") or hook_line.endswith("✨") or hook_line.endswith("🌙")):
        hook_line = f"{hook_line} 🌿"

    # 2. Narrator + Hadith Quote
    narrator = script_data.get("header", script_data.get("narrator", "")).strip()
    if not narrator:
        for sc in script_data.get("scenes", []):
            if sc.get("narrator") or sc.get("header"):
                narrator = sc.get("narrator", sc.get("header", "")).strip()
                break

    quote = script_data.get("quote", script_data.get("hadith_text", "")).strip()
    if not quote:
        for sc in script_data.get("scenes", []):
            if sc.get("quote") or sc.get("hadith_text"):
                quote = sc.get("quote", sc.get("hadith_text", "")).strip()
                break

    narrator_block = ""
    if narrator and quote:
        narrator_block = f"\n\n{narrator}\n\"{quote}\""
    elif narrator:
        narrator_block = f"\n\n{narrator}"
    elif quote:
        narrator_block = f"\n\n\"{quote}\""

    # 3. Arabic / Dua / Pronunciation / Meaning
    arabic_text = script_data.get("arabic_text", "")
    pronunciation = script_data.get("pronunciation", "")
    translation = script_data.get("translation", script_data.get("meaning", ""))

    if not arabic_text:
        for sc in script_data.get("scenes", []):
            if sc.get("arabic_text"):
                arabic_text = sc.get("arabic_text", "")
                pronunciation = sc.get("pronunciation", pronunciation)
                translation = sc.get("translation", sc.get("meaning", translation))
                break

    arabic_block = ""
    if arabic_text:
        arabic_block = f"\n\n✨ সেই বরকতময় বাক্য / দোয়াটি:\n{arabic_text}"
        if pronunciation:
            arabic_block += f'\nউচ্চারণ: "{pronunciation}"'
        if translation:
            arabic_block += f'\nঅর্থ: "{translation}"'

    # 4. Sahih References
    raw_refs = script_data.get("references", [script_data.get("reference", "")])
    if isinstance(raw_refs, str):
        raw_refs = [raw_refs]
    valid_refs = [r.strip() for r in raw_refs if r and str(r).strip()]

    ref_block = "\n\n📖 সহীহ তথ্যসূত্র:"
    if valid_refs:
        ref_block += "\n" + "\n".join([f"• {r}" for r in valid_refs])
    else:
        ref_block += "\n• কুরআনুল কারীম ও সহীহ হাদিস"

    # 5. শিক্ষা ও আমল (explanation / takeaway)
    explanation = script_data.get("explanation", script_data.get("lesson", "")).strip()
    if not explanation:
        lines = [l.strip() for l in metadata_desc.strip().split("\n") if l.strip() and "#" not in l]
        explanation = " ".join(lines[1:3]) if len(lines) > 1 else ""

    lesson_block = ""
    if explanation:
        lesson_block = f"\n\n💡 শিক্ষা ও আমল:\n{explanation}"

    # 6. CTA comment prompt
    dhikr = "সুবহানাল্লাহ"
    combined_text = f"{quote} {explanation} {title}"
    if "আলহামদুলিল্লাহ" in combined_text:
        dhikr = "আলহামদুলিল্লাহ"
    elif "আমিন" in combined_text:
        dhikr = "আমিন"
    elif "ইস্তিগফার" in combined_text or "ক্ষমা" in combined_text:
        dhikr = "আস্তাগফিরুল্লাহ"
    cta_block = f'\n\n💬 আজকের জিকির:\nকমেন্টে একবার "{dhikr}" লিখে আপনার উপস্থিতি জানান এবং নেকির অংশীদার হোন! 🤍'

    # 7. Topic-specific hashtag
    category = str(script_data.get("category", "")).lower()
    topic_tag_map = {
        "dreams_and_sleep": "#ঘুমেরসুন্নাহ",
        "dua_cures": "#দোয়া",
        "heart_softeners": "#তাওবা",
        "islamic_knowledge": "#ইসলামিকজ্ঞান",
        "protection_ruqyah": "#রুকইয়াহ",
        "rizq_barakah": "#রিজিক",
        "husband_wife_family": "#পরিবার",
        "halal_haram_daily": "#হালালহারাম",
        "seerah": "#সীরাহ",
        "islamic_stories": "#ইসলামিককাহিনী",
    }
    topic_tag = topic_tag_map.get(category, "#ইসলামিক")

    # 8. Footer divider, Follow CTA and Curated Hashtags
    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━"
        f"\n📌 প্রতিদিনের সহীহ হাদিস ও দোয়ার জন্য ফলো করুন:"
        f"\n👉 @DailyDosOfIslam"
        f"\n\n#BanglaHadith #IslamicQuotes #DailyReminder #সহীহ_হাদিস #দ্বীন_ইসলাম #DailyDos #Sunnah {topic_tag}"
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
