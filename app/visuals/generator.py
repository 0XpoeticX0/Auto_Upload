import os
import urllib.parse
import requests
import time
from app.logger import logger

# Negative prompt blocks unwanted AI defaults like close-up faces, bad anatomy, and LIVING BEINGS
NEGATIVE_PROMPT = (
    "pale, washed out, blurry, foggy gray, bright overcast, "
    "close-up face, extreme close up, portrait, selfie, bad anatomy, "
    "low quality, watermark, logo, text, deformed, ugly, duplicate, cropped, "
    "human, person, face, eye, man, woman, child, people, crowd, animal, dog, cat, bird, insect, living being"
)

def get_visual_style_prompt(pillar_category: str = "daily_life") -> str:
    """Returns specialized, high-contrast visual prompts based on the Islamic topic pillar."""
    styles = {
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
    }

    return styles.get(pillar_category, styles["daily_life"])

def generate_image_for_scene(visual_prompt: str, output_filepath: str, seed: int = 42) -> bool:
    """Generates 9:16 high-contrast vertical backgrounds via Pollinations AI (FLUX Model)."""
    logger.info(f"Generating high-contrast Flux background image for prompt: '{visual_prompt[:40]}...'")
    
    enhanced_prompt = f"{visual_prompt}, high contrast, rich shadows, deep saturation, masterpiece, 8k resolution"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    base_url = "https://image.pollinations.ai/prompt/"
    params = {
        "width": 1080,
        "height": 1920,
        "seed": seed,
        "model": "flux",  # Flux model produces deep shadows and metallic gold reflections
        "nologo": "true",
        "enhance": "false",
        "negative": NEGATIVE_PROMPT,
    }
    query_string = urllib.parse.urlencode(params)
    request_url = f"{base_url}{encoded_prompt}?{query_string}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(request_url, timeout=60)
            if response.status_code == 200 and len(response.content) > 5000:
                with open(output_filepath, "wb") as f:
                    f.write(response.content)
                logger.info(f"Background successfully generated: {output_filepath} ({len(response.content)//1024} KB)")
                return True
            else:
                logger.warning(f"Attempt {attempt+1}: Status {response.status_code}")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: Error generating image: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(5)
            
    # Fallback to standard model if flux fails
    try:
        logger.info("Attempting fallback standard model generation...")
        fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}&negative={urllib.parse.quote(NEGATIVE_PROMPT)}"
        resp = requests.get(fallback_url, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(output_filepath, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        logger.error(f"Fallback generation error: {e}")
        
    return False

def generate_all_images(scenes: list, topic_id: int, video_format: str = "short", pillar_category: str = "daily_life"):
    """Generates the master visual background tailored to the topic's pillar category."""
    updated_scenes = []
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(base_dir, exist_ok=True)
    
    master_image_path = os.path.join(base_dir, "master_scene.jpg")
    
    # 1. Get specialized high-contrast pillar prompt
    custom_visuals = scenes[0].get("visuals", "") if scenes else ""
    base_style_prompt = get_visual_style_prompt(pillar_category)
    
    if custom_visuals and len(custom_visuals) > 10:
        enhanced_prompt = f"{base_style_prompt}, {custom_visuals}"
    else:
        enhanced_prompt = base_style_prompt
        
    logger.info(f"Generating Master Image (Pillar: {pillar_category}) with Flux engine...")
    success = generate_image_for_scene(enhanced_prompt, master_image_path, seed=topic_id)
    
    for scene in scenes:
        scene["image_path"] = master_image_path if success else None
        updated_scenes.append(scene)
        
    return updated_scenes
