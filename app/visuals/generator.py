import os
import urllib.parse
import requests
import time
from app.logger import logger

# Negative prompt blocks unwanted AI defaults like close-up faces, bad anatomy, and LIVING BEINGS
NEGATIVE_PROMPT = urllib.parse.quote(
    "close-up face, extreme close up, portrait, selfie, blurry, bad anatomy, "
    "low quality, watermark, logo, text, deformed, ugly, duplicate, cropped, "
    "human, person, face, eye, man, woman, child, people, crowd, animal, dog, cat, bird, insect, living being"
)

def generate_image_for_scene(visual_prompt: str, output_filepath: str, video_format: str, seed: int):
    logger.info(f"Generating image for prompt: '{visual_prompt[:30]}...'")
    encoded_prompt = urllib.parse.quote(visual_prompt)
    
    if video_format == "short":
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}&negative={NEGATIVE_PROMPT}"
    else:
        # Default to 16:9 for long and master formats
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={seed}&negative={NEGATIVE_PROMPT}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                with open(output_filepath, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                logger.warning(f"Attempt {attempt+1}: Failed to download image: {response.status_code}")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: Error generating image: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(10)
            
    logger.error(f"Failed to generate image after {max_retries} attempts.")
    return False

def generate_all_images(scenes: list, topic_id: int, video_format: str = "short"):
    updated_scenes = []
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(base_dir, exist_ok=True)
    
    seed_val = topic_id
    
    # ISLAMIC KNOWLEDGE OVERRIDE: We only generate ONE master image (no living beings).
    # We will use the first scene's visual prompt as the inspiration.
    master_visuals = scenes[0].get("visuals", "beautiful empty landscape")
    master_image_path = os.path.join(base_dir, "master_scene.jpg")
    
    orientation = "vertical 9:16" if video_format == "short" else "horizontal 16:9"
    enhanced_prompt = (
        f"{orientation}, beautiful wide angle establishing shot, full scene view, "
        f"empty cinematic landscape, masterpiece, 8k resolution, ultra-detailed, photorealistic, "
        f"dramatic lighting, {master_visuals}, NO living beings, completely empty of humans or animals"
    )
    
    logger.info("Generating Master Image for Islamic Shorts Pipeline...")
    success = generate_image_for_scene(enhanced_prompt, master_image_path, video_format, seed_val)
    
    for scene in scenes:
        scene["image_path"] = master_image_path if success else None
        updated_scenes.append(scene)
        
    return updated_scenes
