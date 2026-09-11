import os
import urllib.parse
import requests
import time
from app.logger import logger
from app.llm.provider import extract_json

# Negative prompt blocks unwanted AI defaults like close-up faces, bad anatomy, and LIVING BEINGS
NEGATIVE_PROMPT = (
    "pale, washed out, blurry, foggy gray, bright overcast, "
    "close-up face, extreme close up, portrait, selfie, bad anatomy, "
    "low quality, watermark, logo, text, deformed, ugly, duplicate, cropped, "
    "human, person, face, eye, nose, mouth, lips, hair, skin, hands, fingers, body, man, woman, girl, boy, child, baby, people, crowd, "
    "animal, dog, cat, bird, insect, fish, living being, living creatures, figure, silhouette of person"
)

# Hard-prepended prefix that guarantees strictly 0 humans in any AI prompt
NO_HUMAN_PREFIX = (
    "vertical 9:16, absolutely no humans no faces no living beings no animals, "
    "empty atmospheric Islamic scenery only, "
)

FALLBACK_PILLAR_STYLES = {
    "daily_life": (
        "vertical 9:16, majestic grand mosque interior at twilight, ornate islamic archways, "
        "glowing hanging brass moroccan lanterns, warm golden light rays, intricate arabesque "
        "geometric mosaic tiles, dark emerald green and royal gold palette, cinematic volumetric "
        "lighting, 8k octane render, empty of people, no living beings"
    ),
    "dua_cures": (
        "vertical 9:16, dark emerald green polished marble background with subtle glowing 24k gold "
        "islamic geometric arabesque patterns, soft divine light beam from top, luxury aesthetic texture, "
        "minimalist islamic art, cinematic 8k octane wallpaper, no living beings"
    ),
    "heart_softeners": (
        "vertical 9:16, majestic grand mosque courtyard at sunrise, warm glowing brass lantern on ancient stone, "
        "soft god rays, deep amber and dark bronze tone, atmospheric dust particles, 8k octane render, empty of people, no living beings"
    ),
    "islamic_knowledge": (
        "vertical 9:16, breathtaking night desert oasis under glowing crescent moon, starry milky way sky, "
        "cinematic ancient minaret silhouette in distance, warm glowing desert lantern on ancient stone, "
        "deep midnight sapphire and amber glow, 8k resolution, no people, no living beings"
    ),
    "dreams_and_sleep": (
        "vertical 9:16, deep midnight blue celestial sky, luminous glowing crescent moon, soft nebula clouds, "
        "subtle gold arabesque particles floating, serene and peaceful atmosphere, cinematic 8k wallpaper, no people, no living beings"
    ),
    "protection_ruqyah": (
        "vertical 9:16, dark obsidian stone wall with deeply carved glowing gold islamic geometric patterns, "
        "moody volumetric side lighting, high contrast shadows, luxury spiritual aesthetic, 8k render, no people, no living beings"
    ),
    "misconceptions": (
        "vertical 9:16, majestic ancient library of islamic scholarship, ancient leather manuscripts and glowing brass scales of justice, "
        "warm candle light, dark mahogany wood and antique gold aesthetics, cinematic volumetric lighting, 8k octane render, no people, no living beings"
    ),
    "relationships": (
        "vertical 9:16, peaceful traditional oriental courtyard garden at sunset, tranquil fountain reflection, glowing warm lanterns, "
        "blooming jasmine vines on stone archways, warm amber and rose-gold dusk palette, 8k resolution, serene, no people, no living beings"
    ),
    "islamic_stories": (
        "vertical 9:16, breathtaking ancient historical arabian desert landscape under dramatic crimson sunset, majestic ancient stone fortress in distance, "
        "warm atmospheric golden dust rays, cinematic historical documentary aesthetic, 8k octane render, no people, no living beings"
    ),
    "seerah": (
        "vertical 9:16, serene historical prophet city aesthetic, ancient medina architecture, date palm shadows under warm golden sunrise, "
        "ornate stone archway overlooking peaceful desert, soft divine volumetric god rays, majestic 8k render, no people, no living beings"
    ),
    "rizq_barakah": (
        "vertical 9:16, lush tranquil oasis garden with crystal clear flowing stream, golden morning sunbeams cutting through date palm leaves, "
        "abundant ripe dates and greenery, radiant warm golden light, blessing and barakah aesthetic, 8k wallpaper, no people, no living beings"
    ),
    "youth_modern": (
        "vertical 9:16, modern minimalist luxury interior window overlooking dark starry night skyline, soft glowing crescent moon, "
        "modern warm ambient desk lamp illuminating open book, deep indigo and warm amber contrast, peaceful contemplation, 8k, no people, no living beings"
    ),

}

def generate_ai_visual_prompt(script_data: dict, topic_title: str = "", pillar_category: str = "daily_life") -> str:
    """
    Uses Gemini to craft a UNIQUE, high-contrast, topic-tailored visual prompt for the background
    based on the exact script storyline, Ayah/Hadith theme, and meaning.
    """
    logger.info("Directing Gemini AI to create a custom, topic-tailored visual background prompt...")
    
    system_prompt = """You are an expert AI art director for vertical 9:16 Islamic Reels and YouTube Shorts.
Your job is to read the Islamic script details and create a UNIQUE, breathtaking, high-contrast visual prompt for the background.

CRITICAL RULES:
1. MUST BE vertical 9:16 format.
2. ABSOLUTELY NO humans, NO faces, NO prophets, NO companions, NO animals, NO living beings, NO living creatures.
3. HIGH CONTRAST & ATMOSPHERIC: specify deep moody shadows (deep emerald, midnight obsidian, dark royal sapphire) with glowing warm accents (24k gold geometric arabesques, glowing brass lanterns, divine light beams, volumetric god rays).
4. Photorealistic, 8k octane render, masterpiece, cinematic depth of field.
5. Directly relate to the emotional theme of the Dua or Hadith (e.g., for Yunus AS dua: deep atmospheric ocean depths with glowing divine light beam; for morning dua: golden sunrise over empty ancient mosque archways; for forgiveness: calm midnight desert oasis under glowing crescent moon; for protection: dark carved obsidian stone with glowing gold geometric patterns).

Respond ONLY with valid JSON (no markdown):
{"visual_prompt": "your detailed english prompt here"}"""

    narrations = " ".join([sc.get("narration", "") for sc in script_data.get("scenes", [])])
    arabic_text = script_data.get("arabic_text", "")
    title = script_data.get("title", topic_title)
    
    user_prompt = f"Video Title: {title}\nCategory Pillar: {pillar_category}\nArabic Text: {arabic_text}\nScript Content: {narrations}"
    
    try:
        res = extract_json(system_prompt, user_prompt, max_tokens=300)
        if res and res.get("visual_prompt"):
            custom_prompt = res.get("visual_prompt").strip()
            # HARD SAFETY: always prepend no-human guarantee regardless of LLM output
            custom_prompt = NO_HUMAN_PREFIX + custom_prompt
            logger.info(f"✨ Gemini created unique visual prompt: {custom_prompt[:60]}...")
            return custom_prompt
    except Exception as e:
        logger.warning(f"Could not generate AI prompt via Gemini: {e}")
        
    logger.info("Using curated pillar style fallback...")
    return FALLBACK_PILLAR_STYLES.get(pillar_category, FALLBACK_PILLAR_STYLES["daily_life"])

def generate_image_for_scene(visual_prompt: str, output_filepath: str, seed: int = 42) -> bool:
    """Generates 9:16 high-contrast vertical backgrounds with TRIPLE-CHECK VISION GUARDIAN (0 Living Beings Guaranteed)."""
    from app.quality.vision_guardian import generate_verified_human_free_background, get_certified_safe_fallback
    success = generate_verified_human_free_background(visual_prompt, output_filepath, max_checks=3)
    if not success or not os.path.exists(output_filepath) or os.path.getsize(output_filepath) < 5000:
        logger.warning("[Vision Guardian] Triggering certified fallback in generate_image_for_scene.")
        return get_certified_safe_fallback(output_filepath)
    return True

def generate_all_images(scenes: list, topic_id: int, video_format: str = "short", pillar_category: str = "daily_life", script_data: dict = None):
    """Generates a master visual background dynamically crafted by Gemini specifically for this topic."""
    updated_scenes = []
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(base_dir, exist_ok=True)
    
    master_image_path = os.path.join(base_dir, "master_scene.jpg")
    
    # 1. Ask Gemini to craft a unique visual prompt for this exact script
    if script_data:
        dynamic_prompt = generate_ai_visual_prompt(script_data, pillar_category=pillar_category)
    else:
        dynamic_prompt = FALLBACK_PILLAR_STYLES.get(pillar_category, FALLBACK_PILLAR_STYLES["daily_life"])
        
    logger.info(f"Generating Master Background Image with Flux Engine...")
    success = generate_image_for_scene(dynamic_prompt, master_image_path, seed=topic_id)
    
    for scene in scenes:
        scene["image_path"] = master_image_path if success else None
        updated_scenes.append(scene)
        
    return updated_scenes
