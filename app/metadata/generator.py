import json
from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection

def generate_viral_metadata(topic_id: int, script_data: dict):
    logger.info("Generating viral metadata for YouTube and Facebook...")
    
    system_prompt = """You are an expert viral Social Media Manager for YouTube and Facebook.
    Generate a highly clickable, emotionally charged title, description, and tags for an Islamic video.

    TITLE RULES:
    - Make the title short but MEANINGFUL (4 to 8 words).
    - It must create a curiosity gap but STILL clearly state what the video is about.
    - Examples: "The First Sign of Qiyamah...", "The Unknown Guard of the Heavens", "Hidden Gold in the Euphrates"
    - DO NOT summarize the entire video, just hook them.
    - DO NOT use clickbait that is false - the title must relate to the actual content.

    DESCRIPTION RULES (Optimize for Suggested Videos algorithm):
    - First sentence MUST be a keyword-rich overview of the video.
    - Write a highly descriptive, comprehensive summary paragraph explaining the core concepts, historical figures (e.g. Sahaba, Prophets), and themes discussed in the video. This helps the YouTube algorithm link your video to other similar Islamic content!
    - Next sentence must be a dramatic hook that expands on the title and draws the viewer in.
    - End with a call to action: "Follow for more authentic Islamic reminders every day!"
    - DO NOT include the references in your description generation, the system will inject them automatically.
    - Add 10-15 relevant viral hashtags at the end, and ALWAYS include #Shorts and #Islam.

    THUMBNAIL HOOK:
    - Generate a 'thumbnail_hook' which is a 2 to 4 word highly compelling, evocative question or statement to be drawn in massive font on the thumbnail. Examples: "End of Time?", "Why Do We Fast?", "The Final Gate".

    Output JSON format:
    {
        "youtube_title": "Max 60 chars, highly clickable with emotional trigger",
        "facebook_title": "Slightly longer engaging title for FB Reels",
        "description": "Descriptive summary... Hook sentence. Call to action. #hashtag1 #hashtag2 ...",
        "thumbnail_hook": "2-4 word compelling hook",
        "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }
    """
    
    narrations = " ".join([scene.get("narration", "") for scene in script_data.get("scenes", [])])
    user_prompt = f"Here is the video script:\n{script_data.get('title', '')}\n\n{narrations}"
    
    metadata = extract_json(system_prompt, user_prompt, max_tokens=1000)
    if not metadata:
        logger.error("Failed to generate metadata.")
        return None
        
    # Inject authentic references and social links into the description
    references = script_data.get("references", [])
    
    ref_text = "\n\n📚 Authentic Sources:\n"
    if references:
        ref_text += "\n".join([f"- {r}" for r in references]) + "\n\n"
    else:
        ref_text += "- Quran & Authentic Sunnah\n\n"
        
    social_links = "🔔 Subscribe on YouTube: https://www.youtube.com/@dailydos-no1\n👍 Follow on Facebook: https://www.facebook.com/DailyDosNo1\n\n"
    
    injection_text = ref_text + social_links
    
    desc = metadata.get("description", "")
    
    if "#" in desc:
        parts = desc.split("#", 1)
        metadata["description"] = parts[0] + injection_text + "#" + parts[1]
    else:
        metadata["description"] = desc + injection_text
            
    logger.info("Metadata generated successfully with references and links.")
    return metadata
