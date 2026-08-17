import os
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "data/output/branding_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLOR_GOLD = (235, 175, 65)       # Warm golden amber (#EBAF41)
COLOR_WHITE = (255, 255, 255)
COLOR_CREAM = (244, 240, 230)
COLOR_MUTED = (160, 160, 160)

def get_font(font_name: str, size: int):
    candidates = [
        f"C:/Windows/Fonts/{font_name}",
        font_name,
        "georgiab.ttf",
        "georgia.ttf",
        "arialbd.ttf",
        "arial.ttf"
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()

def download_or_generate_texture(prompt: str, width: int, height: int, output_path: str):
    """Download background with majestic atmospheric lighting."""
    encoded = urllib.parse.quote(f"{prompt}, dark moody cinematic lighting, photorealistic, 8k, majestic, no text, no humans")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    try:
        resp = requests.get(url, timeout=25)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            img = Image.open(output_path).resize((width, height), Image.Resampling.LANCZOS)
            return img
    except Exception:
        pass
        
    img = Image.new("RGB", (width, height), (10, 12, 16))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, int(height * 0.4)
    for r in range(max(width, height) // 2, 0, -15):
        alpha = int(35 * (1.0 - (r / (max(width, height) // 2))))
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(20 + alpha, 22 + int(alpha*0.8), 28 + alpha))
    return img

def create_facebook_cover():
    """Facebook Page Cover (1640x924 - optimal for desktop & mobile crop)."""
    w, h = 1640, 924
    bg_path = os.path.join(OUTPUT_DIR, "temp_fb_bg.jpg")
    bg = download_or_generate_texture("majestic grand mosque archway with soft golden morning sunlight beams, dramatic atmosphere, cinematic depth", w, h, bg_path)
    
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    for y in range(h):
        alpha = int(140 + 100 * (abs(y - h/2) / (h/2))**0.8)
        d_ov.line([(0, y), (w, y)], fill=(8, 8, 10, min(230, alpha)))
        
    card = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(card)
    
    f_title = get_font("georgiab.ttf", 64)
    f_sub = get_font("georgia.ttf", 32)
    f_badge = get_font("arialbd.ttf", 22)
    
    title = "DAILYDOS OF ISLAM"
    sub = "Daily Quranic Reflections & Authentic Sunnah Wisdom"
    badge = "AUTHENTIC SAHIH SOURCES   •   DAILY REMINDERS"
    
    t_bbox = f_title.getbbox(title)
    s_bbox = f_sub.getbbox(sub)
    b_bbox = f_badge.getbbox(badge)
    
    cy = (h - 220) // 2
    
    # Badge
    bw = b_bbox[2] - b_bbox[0]
    draw.text(((w - bw) // 2, cy), badge, font=f_badge, fill=COLOR_GOLD)
    
    # Title
    tw = t_bbox[2] - t_bbox[0]
    draw.text(((w - tw) // 2, cy + 50), title, font=f_title, fill=COLOR_WHITE)
    
    # Subtitle
    sw = s_bbox[2] - s_bbox[0]
    draw.text(((w - sw) // 2, cy + 140), sub, font=f_sub, fill=COLOR_CREAM)
    
    out_path = os.path.join(OUTPUT_DIR, "facebook_cover_banner.jpg")
    card.convert("RGB").save(out_path, "JPEG", quality=95)
    print(f"Created Facebook Cover: {out_path}")
    return out_path

def create_youtube_banner():
    """YouTube Channel Banner (2560x1440 with safe area in center)."""
    w, h = 2560, 1440
    bg_path = os.path.join(OUTPUT_DIR, "temp_yt_bg.jpg")
    bg = download_or_generate_texture("grand architectural Islamic arched hall, glowing ambient lanterns, cinematic volumetric rays", w, h, bg_path)
    
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    for y in range(h):
        alpha = int(160 + 80 * (abs(y - h/2) / (h/2))**0.8)
        d_ov.line([(0, y), (w, y)], fill=(6, 6, 8, min(240, alpha)))
        
    card = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(card)
    
    f_title = get_font("georgiab.ttf", 84)
    f_sub = get_font("georgia.ttf", 40)
    f_badge = get_font("arialbd.ttf", 26)
    
    title = "DAILYDOS OF ISLAM"
    sub = "Authentic Quranic Wisdom   •   Prophetic Hadith   •   Daily Peace"
    badge = "SUBSCRIBE FOR DAILY INSPIRATION & BARAKAH"
    
    t_bbox = f_title.getbbox(title)
    s_bbox = f_sub.getbbox(sub)
    b_bbox = f_badge.getbbox(badge)
    
    cy = (h - 240) // 2
    
    bw = b_bbox[2] - b_bbox[0]
    draw.text(((w - bw) // 2, cy), badge, font=f_badge, fill=COLOR_GOLD)
    
    tw = t_bbox[2] - t_bbox[0]
    draw.text(((w - tw) // 2, cy + 60), title, font=f_title, fill=COLOR_WHITE)
    
    sw = s_bbox[2] - s_bbox[0]
    draw.text(((w - sw) // 2, cy + 170), sub, font=f_sub, fill=COLOR_CREAM)
    
    out_path = os.path.join(OUTPUT_DIR, "youtube_channel_banner.jpg")
    card.convert("RGB").save(out_path, "JPEG", quality=95)
    print(f"Created YouTube Banner: {out_path}")
    return out_path

def create_highlight_cover(title: str, subtitle: str, filename: str):
    """Creates a 1080x1080 Story Highlight Cover with gold geometry."""
    size = 1080
    img = Image.new("RGB", (size, size), (8, 9, 12))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    
    # Outer gold circle ring
    r_outer = 320
    draw.ellipse([(cx - r_outer, cy - r_outer), (cx + r_outer, cy + r_outer)], outline=COLOR_GOLD, width=6)
    
    # Inner gold fine ring
    r_fine = 300
    draw.ellipse([(cx - r_fine, cy - r_fine), (cx + r_fine, cy + r_fine)], outline=(120, 90, 35), width=2)
    
    # Inner subtle dark glow
    for r in range(290, 0, -10):
        factor = (1.0 - (r / 290)) * 0.2
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(int(15 + 70*factor), int(14 + 50*factor), int(10 + 15*factor)))
        
    f_main = get_font("georgiab.ttf", 64)
    f_sub = get_font("arial.ttf", 26)
    
    # Draw Main Title
    t_bbox = f_main.getbbox(title)
    tw = t_bbox[2] - t_bbox[0]
    th = t_bbox[3] - t_bbox[1]
    draw.text(((size - tw) // 2, cy - 35), title, font=f_main, fill=COLOR_GOLD)
    
    # Draw Subtitle
    s_bbox = f_sub.getbbox(subtitle)
    sw = s_bbox[2] - s_bbox[0]
    draw.text(((size - sw) // 2, cy + 45), subtitle, font=f_sub, fill=COLOR_CREAM)
    
    # Top and bottom decorative diamonds
    draw.polygon([(cx, cy - 140), (cx + 8, cy - 130), (cx, cy - 120), (cx - 8, cy - 130)], fill=COLOR_GOLD)
    draw.polygon([(cx, cy + 120), (cx + 8, cy + 130), (cx, cy + 140), (cx - 8, cy + 130)], fill=COLOR_GOLD)
    
    out_path = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path, "JPEG", quality=95)
    print(f"Created Highlight Cover: {out_path}")
    return out_path

if __name__ == "__main__":
    create_facebook_cover()
    create_youtube_banner()
    create_highlight_cover("DUAS", "AUTHENTIC PRAYERS", "highlight_duas.jpg")
    create_highlight_cover("QURAN", "HOLY VERSES", "highlight_quran.jpg")
    create_highlight_cover("HADITH", "SAHIH SUNNAH", "highlight_hadith.jpg")
    create_highlight_cover("PEACE", "HEART SOFTENERS", "highlight_reminders.jpg")
    print("All branding assets generated successfully!")
