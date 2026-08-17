import os
import re
import urllib.parse
import time
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont
from app.logger import logger

CARD_WIDTH = 1080
CARD_HEIGHT = 1350

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

# ----------------- ENGLISH CARD BUILDER (PIL) -----------------

def get_font(font_name: str, size: int):
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
    lines = []
    for para in text.split("\n"):
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
    text = text.replace('\ufdfa', '(peace be upon him)').replace('ﷺ', '(peace be upon him)')
    text = re.sub(r'[\u2018\u2019\u201a\u201b\']', "'", text)
    text = re.sub(r'[\u201c\u201d\u201e\u201f\"]', '"', text)
    return text

def tag_and_wrap_quote(quote: str, highlight_phrases: list, font_normal: ImageFont.ImageFont, font_bold: ImageFont.ImageFont, max_width: int):
    norm_quote = normalize_text_for_matching(quote)
    spans = []
    for hl in highlight_phrases:
        if not hl.strip():
            continue
        norm_hl = normalize_text_for_matching(hl.strip())
        pattern = re.escape(norm_hl)
        for m in re.finditer(pattern, norm_quote, re.IGNORECASE):
            spans.append((m.start(), m.end()))
            
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
    current_line = []
    current_w = 0
    
    for word, is_hl in tokens:
        f = font_bold if is_hl else font_normal
        bbox = f.getbbox(word)
        w = bbox[2] - bbox[0]
        needed = w if not current_line else current_w + space_w + w
        if needed <= max_width:
            current_line.append((word, is_hl, w))
            current_w = needed
        else:
            if current_line:
                lines.append(current_line)
            current_line = [(word, is_hl, w)]
            current_w = w
    if current_line:
        lines.append(current_line)
    return lines, space_w

def download_card_background(prompt: str, output_path: str) -> str:
    encoded_prompt = urllib.parse.quote(
        f"{prompt}, dark cinematic atmosphere, photorealistic, 8k, majestic soft golden ambient light, peaceful, empty, no humans, no faces"
    )
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=650&nologo=true&negative={NEGATIVE_PROMPT}"
    for attempt in range(1, 4):
        try:
            logger.info(f"Downloading background visual (attempt {attempt}/3)...")
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                with Image.open(output_path) as img:
                    img.verify()
                logger.info("Background visual downloaded successfully.")
                return output_path
        except Exception as e:
            logger.warning(f"Visual download failed on attempt {attempt}: {e}")
            time.sleep(2)
            
    img = Image.new("RGB", (1080, 650), (12, 14, 18))
    img.save(output_path, "JPEG")
    return output_path

def create_english_post_card(post_data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_bg = output_path.replace(".jpg", "_bg_temp.jpg")
    
    image_prompt = post_data.get("image_prompt", "ancient grand library with glowing lantern on wooden desk, 8k")
    download_card_background(image_prompt, temp_bg)
    
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (11, 13, 17))
    try:
        with Image.open(temp_bg).convert("RGBA") as bg_img:
            bg_w, bg_h = bg_img.size
            target_h = 580
            scale = max(CARD_WIDTH / bg_w, target_h / bg_h)
            new_w = int(bg_w * scale)
            new_h = int(bg_h * scale)
            bg_scaled = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            crop_x = (new_w - CARD_WIDTH) // 2
            bg_cropped = bg_scaled.crop((crop_x, 0, crop_x + CARD_WIDTH, target_h))
            
            mask = Image.new("L", (CARD_WIDTH, target_h), 255)
            for y in range(target_h):
                if y < target_h * 0.38:
                    alpha = 255
                else:
                    progress = (y - target_h * 0.38) / (target_h * 0.62)
                    alpha = int(255 * (1.0 - (progress ** 1.6)))
                for x in range(CARD_WIDTH):
                    mask.putpixel((x, y), alpha)
                    
            card.paste(bg_cropped.convert("RGB"), (0, 0), mask)
    except Exception as e:
        logger.warning(f"Error applying background image: {e}")
        
    try:
        if os.path.exists(temp_bg):
            os.remove(temp_bg)
    except: pass
    
    draw = ImageDraw.Draw(card)
    
    font_header = get_font("georgiab.ttf", 44)
    font_quote_normal = get_font("georgia.ttf", 46)
    font_quote_bold = get_font("georgiab.ttf", 46)
    font_explain_title = get_font("georgiab.ttf", 34)
    font_explain_body = get_font("georgia.ttf", 36)
    font_ref = get_font("georgiab.ttf", 38)
    font_watermark = get_font("arial.ttf", 26)
    
    max_text_width = CARD_WIDTH - 160
    current_y = 560
    
    # 1. Header (Sahabi Narrator)
    header_text = post_data.get("header", "")
    if header_text:
        header_lines = wrap_text_to_lines(header_text, font_header, max_text_width)
        for line in header_lines:
            bbox = font_header.getbbox(line)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            draw.text(((CARD_WIDTH - lw) // 2, current_y), line, font=font_header, fill=COLOR_WHITE)
            current_y += lh + 12
        current_y += 20
        
    # 2. Exact Quote with Golden Highlights
    quote_text = post_data.get("quote", "")
    highlight_phrases = post_data.get("highlight_phrases", [])
    if quote_text:
        lines_data, space_w = tag_and_wrap_quote(quote_text, highlight_phrases, font_quote_normal, font_quote_bold, max_text_width)
        for line in lines_data:
            line_w = sum(w for _, _, w in line) + (len(line) - 1) * space_w
            x_start = (CARD_WIDTH - line_w) // 2
            max_lh = 0
            for word, is_hl, w in line:
                f = font_quote_bold if is_hl else font_quote_normal
                color = COLOR_GOLD if is_hl else COLOR_CREAM
                bbox = f.getbbox(word)
                max_lh = max(max_lh, bbox[3] - bbox[1])
                draw.text((x_start, current_y), word, font=f, fill=color)
                x_start += w + space_w
            current_y += max_lh + 16
        current_y += 24
        
    # 3. Explanation
    explain_title = post_data.get("explain_title", "Explain:")
    explanation = post_data.get("explanation", "")
    if explanation:
        bbox_et = font_explain_title.getbbox(explain_title)
        draw.text(((CARD_WIDTH - (bbox_et[2] - bbox_et[0])) // 2, current_y), explain_title, font=font_explain_title, fill=COLOR_MUTED)
        current_y += (bbox_et[3] - bbox_et[1]) + 14
        
        explain_lines = wrap_text_to_lines(explanation, font_explain_body, max_text_width)
        for line in explain_lines:
            bbox = font_explain_body.getbbox(line)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            draw.text(((CARD_WIDTH - lw) // 2, current_y), line, font=font_explain_body, fill=COLOR_OFFWHITE)
            current_y += lh + 10
        current_y += 30
        
    # 4. Reference & Watermark
    ref_text = post_data.get("reference", "")
    if ref_text:
        bbox_ref = font_ref.getbbox(ref_text)
        draw.text(((CARD_WIDTH - (bbox_ref[2] - bbox_ref[0])) // 2, CARD_HEIGHT - 120), ref_text, font=font_ref, fill=COLOR_WHITE)
        
    watermark = "@DailyDosOfIslam"
    bbox_wm = font_watermark.getbbox(watermark)
    draw.text(((CARD_WIDTH - (bbox_wm[2] - bbox_wm[0])) // 2, CARD_HEIGHT - 65), watermark, font=font_watermark, fill=COLOR_DIM)
    
    card.save(output_path, "JPEG", quality=95)
    logger.info(f"Aesthetic Islamic post card generated at {output_path}")
    return output_path

# ----------------- BANGLA CARD BUILDER (HarfBuzz FFmpeg) -----------------

def split_text_wrap_ass(text: str, max_chars: int = 46) -> list:
    lines = []
    paragraphs = text.split("\n")
    for para in paragraphs:
        if not para.strip():
            continue
        words = para.split()
        cur_line = []
        cur_visible_len = 0
        for w in words:
            visible_w = re.sub(r'{\\[^}]+}', '', w)
            w_len = len(visible_w)
            if cur_visible_len + w_len + 1 <= max_chars:
                cur_line.append(w)
                cur_visible_len += w_len + 1
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_visible_len = w_len
        if cur_line:
            lines.append(" ".join(cur_line))
    return lines

def format_quote_with_highlights_ass(quote_text: str, highlight_phrases: list) -> str:
    styled = quote_text
    for hl in highlight_phrases:
        if not hl.strip():
            continue
        clean_hl = hl.strip()
        styled = styled.replace(clean_hl, f"{{\\c&H003DBFF2&}}{{\\b1}}{clean_hl}{{\\r\\c&H00FFFFFF&}}")
    return styled

def create_bengali_post_card(post_data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_dir = os.path.join("data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = int(time.time() * 1000)
    temp_bg = os.path.join(temp_dir, f"bg_{timestamp}.jpg")
    temp_canvas = os.path.join(temp_dir, f"canvas_{timestamp}.jpg")
    temp_ass = os.path.join(temp_dir, f"card_{timestamp}.ass")
    
    # 1. Visual & Base Canvas (Atmospheric top arch image with soft feathering)
    image_prompt = post_data.get("image_prompt", "antique wooden arched window with warm glowing golden lantern light inside ancient room, dark atmospheric cinematic photography 8k, soft shadows")
    download_card_background(image_prompt, temp_bg)
    
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (11, 13, 17))
    try:
        with Image.open(temp_bg).convert("RGBA") as bg_img:
            bg_w, bg_h = bg_img.size
            target_h = 420
            scale = max(CARD_WIDTH / bg_w, target_h / bg_h)
            new_w = int(bg_w * scale)
            new_h = int(bg_h * scale)
            bg_scaled = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            crop_x = (new_w - CARD_WIDTH) // 2
            bg_cropped = bg_scaled.crop((crop_x, 0, crop_x + CARD_WIDTH, target_h))
            
            # Soft feather mask on bottom and sides
            mask = Image.new("L", (CARD_WIDTH, target_h), 255)
            for y in range(target_h):
                for x in range(CARD_WIDTH):
                    # Vertical fade
                    if y < target_h * 0.35:
                        alpha_v = 240
                    else:
                        progress_y = (y - target_h * 0.35) / (target_h * 0.65)
                        alpha_v = int(240 * (1.0 - (progress_y ** 1.8)))
                    
                    # Horizontal side fade
                    edge_dist_x = min(x, CARD_WIDTH - x)
                    if edge_dist_x < 100:
                        alpha_h = edge_dist_x / 100.0
                    else:
                        alpha_h = 1.0
                    
                    mask.putpixel((x, y), int(alpha_v * alpha_h))
                    
            card.paste(bg_cropped.convert("RGB"), (0, 0), mask)
    except Exception as e:
        logger.warning(f"Error blending background: {e}")
        
    card.save(temp_canvas, "JPEG", quality=95)
    
    # 2. Text layout & dynamic sizing (Matching exact reference design)
    header = post_data.get("header", "").strip()
    arabic_quote = post_data.get("arabic_quote", "").strip()
    bangla_quote = post_data.get("quote", post_data.get("bangla_quote", "")).strip()
    highlight_phrases = post_data.get("highlight_phrases", [])
    explain_title = post_data.get("explain_title", "ব্যাখ্যা:").strip()
    explanation = post_data.get("explanation", "").strip()
    reference = post_data.get("reference", "").strip()
    
    header_lines = split_text_wrap_ass(header, max_chars=48) if header else []
    arabic_lines = split_text_wrap_ass(arabic_quote, max_chars=60) if arabic_quote else []
    styled_quote = format_quote_with_highlights_ass(bangla_quote, highlight_phrases) if bangla_quote else ""
    quote_lines = split_text_wrap_ass(styled_quote, max_chars=46) if bangla_quote else []
    explain_lines = split_text_wrap_ass(explanation, max_chars=50) if explanation else []
    
    # Typography specs matching reference image
    f_header = 46
    f_arabic = 58
    f_quote = 44
    f_explain = 34
    f_ref = 42
    f_wm = 26
    
    h_step = 56
    a_step = 70
    q_step = 54
    e_step = 44
    
    start_y = 445
    current_y = start_y
    
    dialogues = []
    
    for h_l in header_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Header,,0,0,0,,{{\\pos(540,{current_y})}}{h_l}")
        current_y += h_step
    if header_lines: current_y += 18
        
    for a_l in arabic_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Arabic,,0,0,0,,{{\\pos(540,{current_y})}}{a_l}")
        current_y += a_step
    if arabic_lines: current_y += 22
        
    for q_l in quote_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Quote,,0,0,0,,{{\\pos(540,{current_y})}}{q_l}")
        current_y += q_step
    if quote_lines: current_y += 24
        
    if explanation:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,ExplainTitle,,0,0,0,,{{\\pos(540,{current_y})}}{explain_title}")
        current_y += (e_step + 4)
        for e_l in explain_lines:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Explain,,0,0,0,,{{\\pos(540,{current_y})}}{e_l}")
            current_y += e_step
            
    ref_y = max(1185, current_y + 36)
    wm_y = min(1280, ref_y + 48)
    
    if reference:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Reference,,0,0,0,,{{\\pos(540,{ref_y})}}{reference}")
    dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Watermark,,0,0,0,,{{\\pos(540,{wm_y})}}@DailyDosOfIslam")
    
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Header,Noto Sans Bengali,{f_header},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,5,60,60,0,1
Style: Arabic,Amiri,{f_arabic},&H003DBFF2,&H000000FF,&H00000000,&H80000000,-1,0,0,0,105,100,0,0,1,3,0,5,40,40,0,1
Style: Quote,Noto Sans Bengali,{f_quote},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,5,60,60,0,1
Style: ExplainTitle,Noto Sans Bengali,32,&H00A0A0A0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,60,60,0,1
Style: Explain,Noto Sans Bengali,{f_explain},&H00D4D4D4,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,60,60,0,1
Style: Reference,Noto Sans Bengali,{f_ref},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,5,60,60,0,1
Style: Watermark,Noto Sans Bengali,{f_wm},&H00808080,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues)

    with open(temp_ass, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    safe_ass = os.path.relpath(temp_ass).replace('\\', '/')
    
    # NOTE: Do NOT use :fontsdir here. Passing fontsdir disables HarfBuzz on Linux,
    # causing Bengali vowels (ো, ে, ি) to be drawn in wrong order (broken spelling).
    # Fonts are pre-installed into /usr/local/share/fonts/bengali/ by the workflow,
    # so libass uses system Fontconfig + HarfBuzz for correct Bengali shaping.
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_canvas,
        "-vf", f"subtitles='{safe_ass}'",
        "-frames:v", "1",
        "-update", "1",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Bengali post card generated at {output_path}")
    except Exception as e:
        logger.error(f"FFmpeg Bengali rendering error: {e}")
        
    for t in [temp_bg, temp_canvas, temp_ass]:
        try: os.remove(t)
        except: pass
        
    return output_path

def create_post_image_card(post_data: dict, output_path: str) -> str:
    """Universal card builder: routes automatically between English (PIL) and Bangla (HarfBuzz FFmpeg)."""
    lang = post_data.get("language", "english").lower()
    has_bengali = any('\u0980' <= char <= '\u09FF' for char in str(post_data.get("quote", "")))
    
    if lang == "bangla" or has_bengali or post_data.get("arabic_quote"):
        return create_bengali_post_card(post_data, output_path)
    else:
        return create_english_post_card(post_data, output_path)
