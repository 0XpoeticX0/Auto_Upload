import os
import re
import urllib.parse
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from app.logger import logger

# Card dimensions (4:5 aspect ratio - optimal for Facebook/Instagram mobile feeds)
CARD_WIDTH = 1080
CARD_HEIGHT = 1350

# Colors for maximum readability on solid dark backgrounds
COLOR_WHITE = (255, 255, 255)
COLOR_CREAM = (244, 240, 230)
COLOR_OFFWHITE = (220, 220, 220)
COLOR_GOLD = (235, 175, 65)        # Warm golden amber (#EBAF41)
COLOR_MUTED = (160, 160, 160)
COLOR_DIM = (120, 120, 120)

NEGATIVE_PROMPT = urllib.parse.quote(
    "close-up face, extreme close up, portrait, selfie, blurry, bad anatomy, "
    "low quality, watermark, logo, text, deformed, ugly, duplicate, cropped, "
    "human, person, face, eye, man, woman, child, people, crowd, animal, dog, cat, bird, insect, living being"
)

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

def normalize_text_for_matching(text: str) -> str:
    """Normalize quotes, apostrophes, and special punctuation for reliable matching."""
    text = text.replace('\ufdfa', '(peace be upon him)').replace('ﷺ', '(peace be upon him)')
    text = re.sub(r'[\u2018\u2019\u201a\u201b\']', "'", text)
    text = re.sub(r'[\u201c\u201d\u201e\u201f\"]', '"', text)
    return text

def tag_and_wrap_quote(quote: str, highlight_phrases: list, font_normal: ImageFont.ImageFont, font_bold: ImageFont.ImageFont, max_width: int):
    """
    Identifies exact highlight phrases and wraps words into balanced lines with measured width.
    """
    norm_quote = normalize_text_for_matching(quote)
    spans = []
    for hl in highlight_phrases:
        if not hl.strip():
            continue
        norm_hl = normalize_text_for_matching(hl.strip())
        pattern = re.escape(norm_hl)
        for m in re.finditer(pattern, norm_quote, re.IGNORECASE):
            spans.append((m.start(), m.end()))
            
    # Fallback: if exact substring match didn't find spans, match words sequence
    if not spans and highlight_phrases:
        for hl in highlight_phrases:
            hl_words = [re.sub(r'[^\w]', '', w.lower()) for w in hl.split() if w.strip()]
            if not hl_words:
                continue
            words_in_quote = list(re.finditer(r'\S+', quote))
            clean_q_words = [re.sub(r'[^\w]', '', m.group().lower()) for m in words_in_quote]
            
            k = len(hl_words)
            for i in range(len(clean_q_words) - k + 1):
                if clean_q_words[i:i+k] == hl_words:
                    start_pos = words_in_quote[i].start()
                    end_pos = words_in_quote[i+k-1].end()
                    spans.append((start_pos, end_pos))

    is_hl_char = [False] * len(quote)
    for start, end in spans:
        for i in range(start, min(end, len(quote))):
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

def download_background_image(prompt: str, output_path: str) -> bool:
    """
    Downloads background image from Pollinations with standard resolution and robust retries.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    enhanced_prompt = f"vertical 9:16, beautiful wide angle shot, {prompt}, masterpiece, 8k resolution, cinematic lighting, photorealistic, atmospheric depth, NO living beings, completely empty of humans or animals"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = int(time.time()) % 100000
    
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}&negative={NEGATIVE_PROMPT}"
    
    max_retries = 3
    for attempt in range(max_retries):
        logger.info(f"Downloading background visual (attempt {attempt+1}/{max_retries})...")
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 15000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info("Background visual downloaded successfully.")
                return True
            else:
                logger.warning(f"Attempt {attempt+1} failed with status: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} error: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(4)
            
    # Solid pitch dark canvas fallback
    img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=(10, 10, 12))
    img.save(output_path, "JPEG", quality=95)
    return False

def create_post_image_card(post_data: dict, output_filepath: str) -> str:
    """
    Builds the 1080x1350 aesthetic Islamic reflection card matching the reference design.
    """
    temp_bg_path = output_filepath.replace(".jpg", "_raw_bg.jpg")
    has_photo = download_background_image(post_data.get("image_prompt", "ancient stone doorway with radiant warm sunlight"), temp_bg_path)
    
    try:
        bg_image = Image.open(temp_bg_path).convert("RGBA")
        # Crop to top 45% of card (1080 x 600)
        bg_image = bg_image.resize((CARD_WIDTH, int(CARD_WIDTH * (1920/1080))), Image.Resampling.LANCZOS)
        # Create full card canvas
        card_canvas = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (8, 8, 10, 255))
        card_canvas.paste(bg_image, (0, 0))
    except Exception:
        card_canvas = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (8, 8, 10, 255))
        has_photo = False
        
    # Top 38% shows photo, smooth gradient completes to 100% solid pitch black by y = 470px
    gradient = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    
    fade_start = int(CARD_HEIGHT * 0.20)  # ~270px
    fade_end = int(CARD_HEIGHT * 0.35)    # ~470px
    
    for y in range(CARD_HEIGHT):
        if y < fade_start:
            alpha = int(25 * (y / fade_start))
        elif y < fade_end:
            progress = (y - fade_start) / (fade_end - fade_start)
            alpha = min(255, int(25 + (230 * (progress ** 1.3))))
        else:
            alpha = 255
            
        draw_grad.line([(0, y), (CARD_WIDTH, y)], fill=(8, 8, 10, alpha))
        
    card = Image.alpha_composite(card_canvas, gradient)
    draw = ImageDraw.Draw(card)
    
    # Typography Fonts matching Blossom.mee scale
    font_header = get_font("georgiab.ttf", 38)
    font_quote = get_font("georgia.ttf", 34)
    font_quote_bold = get_font("georgiab.ttf", 34)
    font_explain_title = get_font("georgia.ttf", 32)
    font_explain_body = get_font("segoeui.ttf", 29)
    font_ref = get_font("georgiab.ttf", 32)
    font_watermark = get_font("segoeui.ttf", 22)
    
    # Clean header text
    raw_header = post_data.get("header", "The Prophet (peace be upon him) said:")
    header_text = raw_header.replace("ﷺ", "(peace be upon him)").replace("  ", " ").strip()
    if not header_text.endswith(":"):
        header_text += ":"
        
    raw_quote = post_data.get("quote", "").strip()
    raw_quote = raw_quote.strip(" \t\n\r\"'‘'“”")
    clean_quote = f"‘{raw_quote}’"
        
    highlight_phrases = post_data.get("highlight_phrases", [])
    explain_title = post_data.get("explain_title", "Explain:").strip()
    if not explain_title.endswith(":"):
        explain_title += ":"
        
    explanation_text = post_data.get("explanation", "").replace("ﷺ", "(peace be upon him)").strip()
    reference_text = post_data.get("reference", "").strip()
    watermark_text = "@DailyDosOfIslam"
    
    max_text_width = 920  # 80px margin each side for balanced typography
    
    # Precalculate lines and element heights
    header_lines = wrap_text_to_lines(header_text, font_header, max_text_width)
    h_single_h = font_header.getbbox("Tg")[3] - font_header.getbbox("Tg")[1]
    header_total_h = len(header_lines) * (h_single_h + 8)
    
    quote_lines = tag_and_wrap_quote(clean_quote, highlight_phrases, font_quote, font_quote_bold, max_text_width)
    line_single_h = font_quote.getbbox("Tg")[3] - font_quote.getbbox("Tg")[1]
    quote_total_h = len(quote_lines) * (line_single_h + 16)
    
    exp_t_bbox = font_explain_title.getbbox(explain_title)
    exp_t_h = exp_t_bbox[3] - exp_t_bbox[1]
    
    exp_lines = wrap_text_to_lines(explanation_text, font_explain_body, max_text_width)
    exp_single_h = font_explain_body.getbbox("Tg")[3] - font_explain_body.getbbox("Tg")[1]
    exp_total_h = len(exp_lines) * (exp_single_h + 14)
    
    ref_bbox = font_ref.getbbox(reference_text)
    ref_h = ref_bbox[3] - ref_bbox[1]
    
    wm_bbox = font_watermark.getbbox(watermark_text)
    wm_h = wm_bbox[3] - wm_bbox[1]
    
    # Total height of all text elements and spacing gaps
    total_block_height = (
        header_total_h + 22 +
        quote_total_h + 22 +
        exp_t_h + 20 +
        exp_total_h + 26 +
        ref_h + 12 +
        wm_h
    )
    
    # Perfect mathematical centering in the bottom dark region (from y = 470 to y = 1350, height = 880px)
    dark_top = 470
    dark_bottom = 1350
    available_dark_space = dark_bottom - dark_top
    current_y = dark_top + max(0, (available_dark_space - total_block_height) // 2)
    
    # 1. Draw Header (multi-line safe & centered)
    for h_line in header_lines:
        h_bbox = font_header.getbbox(h_line)
        h_w = h_bbox[2] - h_bbox[0]
        draw.text(((CARD_WIDTH - h_w) // 2, current_y), h_line, font=font_header, fill=COLOR_WHITE)
        current_y += h_single_h + 8
    current_y += 22
    
    # 2. Draw Quote with Exact Golden Highlighted Words
    space_w = font_quote.getbbox(" ")[2] - font_quote.getbbox(" ")[0]
    for tokens, line_w in quote_lines:
        start_x = (CARD_WIDTH - line_w) // 2
        x_cursor = start_x
        for word, is_hl, w in tokens:
            w_font = font_quote_bold if is_hl else font_quote
            w_color = COLOR_GOLD if is_hl else COLOR_CREAM
            draw.text((x_cursor, current_y), word, font=w_font, fill=w_color)
            x_cursor += w + space_w
            
        current_y += line_single_h + 16
        
    current_y += 22
    
    # 3. Draw Section Title ("Explain:")
    exp_t_w = exp_t_bbox[2] - exp_t_bbox[0]
    draw.text(((CARD_WIDTH - exp_t_w) // 2, current_y), explain_title, font=font_explain_title, fill=COLOR_OFFWHITE)
    current_y += exp_t_h + 20
    
    # 4. Draw Explanation Body
    for line in exp_lines:
        l_bbox = font_explain_body.getbbox(line)
        l_w = l_bbox[2] - l_bbox[0]
        draw.text(((CARD_WIDTH - l_w) // 2, current_y), line, font=font_explain_body, fill=COLOR_OFFWHITE)
        current_y += exp_single_h + 14
        
    current_y += 26
    
    # 5. Draw Reference ("Sahih Muslim: 2172 a")
    ref_w = ref_bbox[2] - ref_bbox[0]
    draw.text(((CARD_WIDTH - ref_w) // 2, current_y), reference_text, font=font_ref, fill=COLOR_WHITE)
    current_y += ref_h + 12
    
    # 6. Draw Watermark with Page Username ("@DailyDosOfIslam")
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
