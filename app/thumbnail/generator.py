import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from app.logger import logger

def generate_thumbnail(title: str, topic_id: int, base_image_path: str):
    logger.info(f"Generating thumbnail for: {title}")
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)
    
    final_path = os.path.join(output_dir, f"thumbnail_{topic_id}.jpg")
    
    if not base_image_path or not os.path.exists(base_image_path):
        logger.error(f"Thumbnail generation failed: Base image not found at {base_image_path}")
        return None
        
    try:
        img = Image.open(base_image_path)
        # Ensure it's 1280x720 for YouTube
        img = img.resize((1280, 720))
        
        font_path = "C:\\Windows\\Fonts\\impact.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 80)
        else:
            font = ImageFont.load_default()
            
        w, h = img.size
        
        # Apply evocative visual enhancements to make the thumbnail "pop"
        # Increase contrast by 20%
        enhancer_contrast = ImageEnhance.Contrast(img)
        img = enhancer_contrast.enhance(1.2)
        
        # Increase color saturation by 20%
        enhancer_color = ImageEnhance.Color(img)
        img = enhancer_color.enhance(1.2)
        
        # We now use the thumbnail_hook instead of the title, or fallback to first 4 words
        short_title = title
        
        # Instantiate draw AFTER image enhancements
        draw = ImageDraw.Draw(img)
        
        # Draw a semi-transparent black overlay on the bottom third to make text pop
        draw.rectangle(((0, h - 150), (w, h)), fill=(0, 0, 0, 150))
        
        # Draw text
        draw.text((50, h - 120), short_title, font=font, fill="white", stroke_width=4, stroke_fill="black")
        
        # Convert to RGB in case the base image had an alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.save(final_path)
        logger.info(f"Thumbnail created at {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None
