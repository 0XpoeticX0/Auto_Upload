import os
import re
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont
from app.logger import logger

# Card dimensions (4:5 aspect ratio - optimal for Facebook/Instagram mobile feeds)
CARD_WIDTH = 1080
CARD_HEIGHT = 1350

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_CREAM = (240, 236, 225)
COLOR_OFFWHITE = (220, 220, 220)
COLOR_GOLD = (235, 175, 65)        # Warm golden amber (#EBAF41)
COLOR_MUTED = (160, 160, 160)
COLOR_DIM = (100, 100, 100)

def get_font(font_name: str, size: int):
    """
    Load requested TrueType font with robust fallbacks for Windows and Linux.
    """
    font_candidates = [
        font_name,
        f"C:/Windows/Fonts/{font_name}",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        f"/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "georgia.ttf",
        "georgiab.ttf",
        "arial.ttf",
        "arialbd.ttf"
    ]
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()

def wrap_text_to_lines(text: str, font: ImageFont.ImageFont, max_width: int) -> list:
    """Wraps text cleanly into multiple lines that fit within max_width."""
    lines = []
    paragraphs = text.split("\n")
    for para in paragraphs:
        if not para.strip():
            lines.append("")
            continue
        words = para.split()
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
    return lines

def tag_and_wrap_quote(quote: str, highlight_phrases: list, font_normal: ImageFont.ImageFont, font_bold: ImageFont.ImageFont, max_width: int):
    """
    Identifies exact highlight phrases and wraps words into balanced lines with measured width.
    """
    spans = []
    for hl in highlight_phrases:
        if not hl.strip():
            continue
        pattern = re.escape(hl.strip())
        for m in re.finditer(pattern, quote, re.IGNORECASE):
            spans.append((m.start(), m.end()))
            
    is_hl_char = [False] * len(quote)
    for start, end in spans:
        for i in range(start, end):
            is_hl_char[i] = True
            
    tokens = []
    for m in re.finditer(r'\S+', quote):
        word = m.group()
        w_start, w_end = m.start(), m.end()
        hl_count = sum(1 for i in range(w_start, w_end) if is_hl_char[i])
        is_hl = (hl_count / max(1, len(word))) >= 0.5
        tokens.append((word, is_hl))
        
    space_w = font_normal.getbbox(" ")[2] - font_normal.getbbox(" ")[0]
    lines = []
    cur_line = []
    cur_w = 0
    
    for word, is_hl in tokens:
        f = font_bold if is_hl else font_normal
        bbox = f.getbbox(word)
        w = bbox[2] - bbox[0]
        needed = w if not cur_line else (cur_w + space_w + w)
        if needed <= max_width:
            cur_line.append((word, is_hl, w))
            cur_w = needed
        else:
            if cur_line:
                lines.append((cur_line, cur_w))
            cur_line = [(word, is_hl, w)]
            cur_w = w
            
    if cur_line:
        lines.append((cur_line, cur_w))
        
    return lines

def download_background_image(prompt: str, output_path: str) -> str:
    """
    Downloads an atmospheric background image from Pollinations API.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    enhanced_prompt = f"{prompt}, vertical portrait 4:5, dark moody cinematic lighting, atmospheric depth, photorealistic, 8k, shadows, empty, no humans, no faces, no text, no watermark"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = os.urandom(2).hex()
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1350&nologo=true&seed={seed}"
    
    logger.info(f"Downloading background image from Pollinations...")
    try:
        resp = requests.get(image_url, timeout=40)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            logger.info("Background image downloaded successfully.")
            return output_path
    except Exception as e:
        logger.warning(f"Failed to download background image: {e}")
        
    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=(12, 12, 12))
    img.save(output_path)
    return output_path

def create_post_image_card(post_data: dict, output_filepath: str) -> str:
    """
    Builds the 1080x1350 aesthetic Islamic reflection card matching the reference design.
    """
    temp_bg_path = output_filepath.replace(".jpg", "_raw_bg.jpg")
    download_background_image(post_data.get("image_prompt", "ancient doorway with warm sunlight"), temp_bg_path)
    
    try:
        bg_image = Image.open(temp_bg_path).convert("RGBA")
        bg_image = bg_image.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
    except Exception:
        bg_image = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (12, 12, 12, 255))
        
    # Create smooth dark gradient overlay (top shows image, middle fades down, bottom is solid black)
    gradient = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    
    fade_start = int(CARD_HEIGHT * 0.28)  # ~380px
    fade_mid = int(CARD_HEIGHT * 0.50)    # ~675px
    fade_end = int(CARD_HEIGHT * 0.62)    # ~840px
    
    for y in range(CARD_HEIGHT):
        if y < fade_start:
            alpha = int(70 * (y / fade_start))
        elif y < fade_mid:
            progress = (y - fade_start) / (fade_mid - fade_start)
            alpha = int(70 + (185 * (progress ** 1.4)))
        elif y < fade_end:
            progress = (y - fade_mid) / (fade_end - fade_mid)
            alpha = min(255, int(255 * progress))
        else:
            alpha = 255
            
        draw_grad.line([(0, y), (CARD_WIDTH, y)], fill=(6, 6, 6, alpha))
        
    card = Image.alpha_composite(bg_image, gradient)
    draw = ImageDraw.Draw(card)
    
    # Load Typography Fonts
    font_header = get_font("georgiab.ttf", 36)
    font_quote = get_font("georgia.ttf", 33)
    font_quote_bold = get_font("georgiab.ttf", 33)
    font_explain_title = get_font("georgia.ttf", 32)
    font_explain_body = get_font("segoeui.ttf", 28)
    font_ref = get_font("georgiab.ttf", 30)
    font_watermark = get_font("segoeui.ttf", 22)
    
    # Clean header text to avoid missing Unicode ligature squares (e.g. ﷺ -> peace be upon him)
    raw_header = post_data.get("header", "The Prophet (peace be upon him) said:")
    header_text = raw_header.replace("ﷺ", "(peace be upon him)").replace("  ", " ").strip()
    if not header_text.endswith(":"):
        header_text += ":"
        
    raw_quote = post_data.get("quote", "").strip()
    # Normalize clean quotes
    raw_quote = raw_quote.strip(" \t\n\r\"'‘'“”")
    clean_quote = f"'{raw_quote}'"
        
    highlight_phrases = post_data.get("highlight_phrases", [])
    explain_title = post_data.get("explain_title", "Explain:").strip()
    if not explain_title.endswith(":"):
        explain_title += ":"
        
    explanation_text = post_data.get("explanation", "").strip()
    reference_text = post_data.get("reference", "").strip()
    watermark_text = "@authentic.islamic.reminders"
    
    max_text_width = CARD_WIDTH - 180  # 90px margin on each side (900px content width)
    
    # Calculate vertical starting position
    current_y = int(CARD_HEIGHT * 0.44)  # ~594px
    
    # 1. Draw Header ("The Prophet (peace be upon him) said:")
    h_bbox = font_header.getbbox(header_text)
    h_w = h_bbox[2] - h_bbox[0]
    draw.text(((CARD_WIDTH - h_w) // 2, current_y), header_text, font=font_header, fill=COLOR_WHITE)
    current_y += (h_bbox[3] - h_bbox[1]) + 26
    
    # 2. Draw Quote with Exact Golden Highlighted Words
    quote_lines = tag_and_wrap_quote(clean_quote, highlight_phrases, font_quote, font_quote_bold, max_text_width)
    space_w = font_quote.getbbox(" ")[2] - font_quote.getbbox(" ")[0]
    
    for tokens, line_w in quote_lines:
        start_x = (CARD_WIDTH - line_w) // 2
        x_cursor = start_x
        for word, is_hl, w in tokens:
            w_font = font_quote_bold if is_hl else font_quote
            w_color = COLOR_GOLD if is_hl else COLOR_CREAM
            draw.text((x_cursor, current_y), word, font=w_font, fill=w_color)
            x_cursor += w + space_w
            
        line_h = font_quote.getbbox("Tg")[3] - font_quote.getbbox("Tg")[1]
        current_y += line_h + 16
        
    current_y += 18
    
    # 3. Draw Section Title ("Explain:")
    exp_t_bbox = font_explain_title.getbbox(explain_title)
    exp_t_w = exp_t_bbox[2] - exp_t_bbox[0]
    draw.text(((CARD_WIDTH - exp_t_w) // 2, current_y), explain_title, font=font_explain_title, fill=COLOR_OFFWHITE)
    current_y += (exp_t_bbox[3] - exp_t_bbox[1]) + 20
    
    # 4. Draw Explanation Body
    exp_lines = wrap_text_to_lines(explanation_text, font_explain_body, max_text_width)
    for line in exp_lines:
        l_bbox = font_explain_body.getbbox(line)
        l_w = l_bbox[2] - l_bbox[0]
        draw.text(((CARD_WIDTH - l_w) // 2, current_y), line, font=font_explain_body, fill=COLOR_OFFWHITE)
        current_y += (l_bbox[3] - l_bbox[1]) + 14
        
    current_y += 24
    
    # 5. Draw Reference ("Sahih Muslim: 2172 a")
    ref_bbox = font_ref.getbbox(reference_text)
    ref_w = ref_bbox[2] - ref_bbox[0]
    draw.text(((CARD_WIDTH - ref_w) // 2, current_y), reference_text, font=font_ref, fill=COLOR_WHITE)
    current_y += (ref_bbox[3] - ref_bbox[1]) + 14
    
    # 6. Draw Subtle Watermark / Branding
    wm_bbox = font_watermark.getbbox(watermark_text)
    wm_w = wm_bbox[2] - wm_bbox[0]
    draw.text(((CARD_WIDTH - wm_w) // 2, current_y), watermark_text, font=font_watermark, fill=COLOR_DIM)
    
    final_card = card.convert("RGB")
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    final_card.save(output_filepath, format="JPEG", quality=95)
    
    if os.path.exists(temp_bg_path):
        try:
            os.remove(temp_bg_path)
        except Exception:
            pass
            
    logger.info(f"Aesthetic Islamic post card generated at {output_filepath}")
    return output_filepath
