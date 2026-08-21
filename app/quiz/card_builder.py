import os
import re
import time
import subprocess
from PIL import Image, ImageDraw
from app.logger import logger

WIDTH = 1080
HEIGHT = 1920

# ── Colors ───────────────────────────────────────────────────────────────────
BG_DARK = (10, 18, 16)            # Deep emerald dark background
CARD_BG = (18, 32, 28)            # Translucent card background
CARD_BORDER = (35, 65, 55)        # Subtle card border
ACCENT_GOLD_BG = (45, 36, 12)
ACCENT_GOLD_BORDER = (235, 185, 65)
CORRECT_GREEN = (0, 230, 118)     # Glowing emerald green

def draw_rounded_rect(draw: ImageDraw.ImageDraw, box: tuple, radius: int, fill: tuple, outline: tuple = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def create_base_canvas() -> Image.Image:
    """Creates a modern 9:16 dark gradient canvas with glowing ambiance."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # Top & bottom subtle ambient glow
    for y in range(0, 400):
        alpha = int(25 * (1.0 - y / 400.0))
        draw.line([(0, y), (WIDTH, y)], fill=(15 + alpha, 35 + alpha, 30 + alpha))
        
    for y in range(HEIGHT - 400, HEIGHT):
        ratio = (y - (HEIGHT - 400)) / 400.0
        alpha = int(25 * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(15 + alpha, 35 + alpha, 30 + alpha))
        
    return img

def render_ass_to_image(base_img_path: str, ass_path: str, out_img_path: str):
    """Uses FFmpeg libass + HarfBuzz to burn complex Bengali/English text with 100% proper glyph shaping."""
    rel_ass = os.path.relpath(ass_path).replace('\\', '/')
    cmd = [
        "ffmpeg", "-y",
        "-i", base_img_path,
        "-vf", f"subtitles='{rel_ass}'",
        "-frames:v", "1",
        out_img_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def clean_text_ass(text: str) -> str:
    """Strips emojis and complex non-font symbols so only crisp letters render."""
    if not text:
        return ""
    res = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    res = re.sub(r'[\u2600-\u27BF]', '', res)
    res = re.sub(r'[\uFE00-\uFE0F]', '', res)
    res = res.replace("☪️", "").replace("☪", "").replace("💡", "").replace("🌿", "").replace("⏳", "").replace("👇", "").replace("✍️", "")
    return re.sub(r'\s+', ' ', res).strip()

def split_text_wrap(text: str, max_chars: int = 34) -> list[str]:
    text = clean_text_ass(text)
    lines = []
    for para in text.split("\n"):
        words = para.strip().split()
        if not words:
            continue
        cur = []
        cur_len = 0
        for w in words:
            w_len = len(w)
            if cur_len + w_len + 1 <= max_chars or not cur:
                cur.append(w)
                cur_len += w_len + 1
            else:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = w_len
        if cur:
            lines.append(" ".join(cur))
    return lines

def render_hook_card(hook_data: dict, out_path: str) -> str:
    """Renders Scene 1: The Hook with HarfBuzz Bengali shaping."""
    temp_dir = "data/temp/quiz_render"
    os.makedirs(temp_dir, exist_ok=True)
    base_bg = os.path.join(temp_dir, "hook_canvas.jpg")
    ass_file = os.path.join(temp_dir, "hook.ass")
    
    # 1. Base Canvas & Boxes
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    # Top badge pill
    draw_rounded_rect(draw, (240, 435, 840, 505), radius=25, fill=ACCENT_GOLD_BG, outline=ACCENT_GOLD_BORDER, width=2)
    # Main Headline box
    draw_rounded_rect(draw, (80, 650, WIDTH - 80, 1070), radius=35, fill=(20, 38, 33), outline=CARD_BORDER, width=2)
    # Sub-hook instruction pill
    draw_rounded_rect(draw, (90, 1230, WIDTH - 90, 1315), radius=30, fill=(30, 50, 42), outline=CORRECT_GREEN, width=2)
    
    img.save(base_bg, quality=95)
    
    # 2. ASS Subtitles with Hind Siliguri (HarfBuzz shaped)
    headline = clean_text_ass(hook_data.get("headline", "ইসলামিক জ্ঞান যাচাই করুন!"))
    sub_text = clean_text_ass(hook_data.get("sub_text", "সময় বেশি লাগলে ভিডিওটি পজ করুন!"))
    
    hl_lines = split_text_wrap(headline, max_chars=28)
    hl_y = 820 - (len(hl_lines) - 1) * 45
    
    dialogues = [
        # Top Badge
        f"Dialogue: 0,0:00:00.00,0:00:10.00,GoldBadge,,0,0,0,,{{\\pos(540,470)}}ইসলামিক জ্ঞান কুইজ"
    ]
    
    for line in hl_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,Headline,,0,0,0,,{{\\pos(540,{hl_y})}}{line}")
        hl_y += 85
        
    dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,SubHook,,0,0,0,,{{\\pos(540,1272)}}{sub_text}")
    dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,Footer,,0,0,0,,{{\\pos(540,1600)}}৫টি প্রশ্ন • আপনার দ্বীন যাচাই করুন • লেভেল ১")

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: GoldBadge,Noto Sans Bengali,36,&H0041AFEB,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Headline,Noto Sans Bengali,68,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1
Style: SubHook,Noto Sans Bengali,40,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,5,0,0,0,1
Style: Footer,Noto Sans Bengali,32,&H00C3C8B4,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues) + "\n"

    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    render_ass_to_image(base_bg, ass_file, out_path)
    return out_path

def render_question_card(
    q_data: dict,
    countdown_val: int = None,
    is_revealed: bool = False,
    out_path: str = "data/temp/quiz_frame.jpg"
) -> str:
    """
    Renders Question Card with HarfBuzz Bengali text shaping:
    - Top header & category badge
    - Big bold question box
    - 3 Option Pills
    - 5-Second Countdown ("৫... ৪... ৩... ২... ১... ⏳")
    - Emerald Green answer reveal + Sahih reference
    """
    temp_dir = "data/temp/quiz_render"
    os.makedirs(temp_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    base_bg = os.path.join(temp_dir, f"q_base_{ts}.jpg")
    ass_file = os.path.join(temp_dir, f"q_{ts}.ass")
    
    q_num = q_data.get("number", 1)
    category = q_data.get("category", "ইসলামিক জ্ঞান")
    question = q_data.get("question", "")
    options = q_data.get("options", ["ক) ...", "খ) ...", "গ) ..."])
    correct_opt = q_data.get("correct_option", "ক").strip()
    explanation = q_data.get("explanation", "")
    
    # 1. Base Canvas with Boxes
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    # Progress pill top right
    draw_rounded_rect(draw, (790, 165, 1010, 225), radius=20, fill=(30, 50, 42), outline=ACCENT_GOLD_BORDER, width=2)
    
    # Main Question Box
    qcard_y = 280
    qcard_h = 360
    draw_rounded_rect(draw, (70, qcard_y, WIDTH - 70, qcard_y + qcard_h), radius=30, fill=(18, 35, 30), outline=CARD_BORDER, width=2)
    
    # 3 Option Pills
    opt_y = 700
    opt_h = 135
    opt_gap = 30
    
    correct_letter = correct_opt[0] if correct_opt else "ক"
    
    for opt in options:
        opt_str = opt.strip()
        opt_letter = opt_str[0] if opt_str else "ক"
        is_this_correct = (opt_letter == correct_letter) or (correct_opt in opt_str)
        box_coords = (70, opt_y, WIDTH - 70, opt_y + opt_h)
        
        if is_revealed and is_this_correct:
            draw_rounded_rect(draw, box_coords, radius=25, fill=CORRECT_GREEN, outline=(255, 255, 255), width=3)
        else:
            fill_c = (22, 40, 35) if not is_revealed else (15, 28, 25)
            border_c = (45, 80, 70) if not is_revealed else (25, 45, 40)
            draw_rounded_rect(draw, box_coords, radius=25, fill=fill_c, outline=border_c, width=2)
            
        opt_y += opt_h + opt_gap
        
    # Bottom Box: Timer OR Sahih Reference
    bottom_y = 1260
    if not is_revealed:
        t_color = (255, 100, 100) if countdown_val == 1 else ACCENT_GOLD_BORDER
        draw_rounded_rect(draw, (180, bottom_y - 10, WIDTH - 180, bottom_y + 80), radius=25, fill=(30, 45, 38), outline=t_color, width=2)
    else:
        if explanation:
            draw_rounded_rect(draw, (70, bottom_y, WIDTH - 70, bottom_y + 190), radius=25, fill=(20, 48, 36), outline=CORRECT_GREEN, width=2)
            
    # Footer 5 Progress Dots
    dots_y = 1680
    dot_spacing = 50
    start_dots_x = (WIDTH - (5 * dot_spacing)) // 2
    for i in range(1, 6):
        dx = start_dots_x + (i - 1) * dot_spacing
        dot_color = CORRECT_GREEN if i < q_num else (ACCENT_GOLD_BORDER if i == q_num else (45, 70, 60))
        draw.ellipse((dx, dots_y, dx + 22, dots_y + 22), fill=dot_color)
        
    img.save(base_bg, quality=95)
    
    # 2. Build ASS Dialogue Events for Bengali HarfBuzz Typography
    dialogues = [
        # Top Header Brand
        f"Dialogue: 0,0:00:00.00,0:00:10.00,Brand,,0,0,0,,{{\\pos(230,195)}}ডেইলি ডোজ ইসলাম",
        # Question Pill
        f"Dialogue: 0,0:00:00.00,0:00:10.00,Progress,,0,0,0,,{{\\pos(900,195)}}প্রশ্ন {q_num}/৫",
        # Category Tag
        f"Dialogue: 0,0:00:00.00,0:00:10.00,Category,,0,0,0,,{{\\pos(540,325)}}•  {category}  •"
    ]
    
    # Question text (centered wrap)
    qlines = split_text_wrap(question, max_chars=32)
    qy = 470 - (len(qlines) - 1) * 35
    for ql in qlines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,Question,,0,0,0,,{{\\pos(540,{qy})}}{ql}")
        qy += 68
        
    # 3 Options
    opt_y_text = 765
    for opt in options:
        opt_str = opt.strip()
        opt_letter = opt_str[0] if opt_str else "ক"
        is_this_correct = (opt_letter == correct_letter) or (correct_opt in opt_str)
        
        if is_revealed and is_this_correct:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,OptGreen,,0,0,0,,{{\\pos(540,{opt_y_text})}}{opt_str}")
        elif is_revealed:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,OptMuted,,0,0,0,,{{\\pos(540,{opt_y_text})}}{opt_str}")
        else:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,OptNormal,,0,0,0,,{{\\pos(540,{opt_y_text})}}{opt_str}")
            
        opt_y_text += 165
        
    # Bottom: Timer or Sahih Reference
    if not is_revealed:
        if countdown_val is not None and countdown_val > 0:
            # Map numbers to Bengali numerals if preferred
            bn_nums = {5: "৫", 4: "৪", 3: "৩", 2: "২", 1: "১"}
            bn_n = bn_nums.get(countdown_val, str(countdown_val))
            t_text = f"উত্তর আসছে:  {bn_n} সেকেন্ড"
            style_name = "TimerRed" if countdown_val == 1 else "TimerGold"
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,{style_name},,0,0,0,,{{\\pos(540,{bottom_y + 35})}}{t_text}")
        else:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,TimerGold,,0,0,0,,{{\\pos(540,{bottom_y + 35})}}সঠিক উত্তর কোনটি ভাবুন...")
    else:
        if explanation:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,RefBadge,,0,0,0,,{{\\pos(540,{bottom_y + 35})}}•  সহীহ তথ্যসূত্র  •")
            elines = split_text_wrap(explanation, max_chars=40)
            ey = bottom_y + 90
            for el in elines[:2]:
                dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,RefBody,,0,0,0,,{{\\pos(540,{ey})}}{el}")
                ey += 46

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Noto Sans Bengali,34,&H0041AFEB,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Progress,Noto Sans Bengali,34,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Category,Noto Sans Bengali,28,&H0041AFEB,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Question,Noto Sans Bengali,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1
Style: OptNormal,Noto Sans Bengali,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,5,0,0,0,1
Style: OptGreen,Noto Sans Bengali,46,&H000F1905,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: OptMuted,Noto Sans Bengali,44,&H00878C78,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: TimerGold,Noto Sans Bengali,42,&H0041AFEB,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: TimerRed,Noto Sans Bengali,44,&H006464FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: RefBadge,Noto Sans Bengali,30,&H0076E600,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: RefBody,Noto Sans Bengali,34,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues) + "\n"

    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    render_ass_to_image(base_bg, ass_file, out_path)
    
    try: os.remove(base_bg)
    except: pass
    try: os.remove(ass_file)
    except: pass
    
    return out_path

def render_outro_card(outro_data: dict, out_path: str) -> str:
    """Renders Scene 7: Outro & Score Evaluation CTA with HarfBuzz shaping."""
    temp_dir = "data/temp/quiz_render"
    os.makedirs(temp_dir, exist_ok=True)
    base_bg = os.path.join(temp_dir, "outro_canvas.jpg")
    ass_file = os.path.join(temp_dir, "outro.ass")
    
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    # Top badge pill
    draw_rounded_rect(draw, (290, 405, 790, 475), radius=25, fill=(10, 50, 30), outline=CORRECT_GREEN, width=2)
    # Main Score Card Box
    draw_rounded_rect(draw, (70, 580, WIDTH - 70, 960), radius=35, fill=(18, 38, 30), outline=ACCENT_GOLD_BORDER, width=2)
    # Follow CTA Box
    draw_rounded_rect(draw, (70, 1100, WIDTH - 70, 1420), radius=30, fill=(25, 48, 40), outline=CORRECT_GREEN, width=2)
    
    img.save(base_bg, quality=95)
    
    score_prompt = clean_text_ass(outro_data.get("score_prompt", "৫-এ আপনার স্কোর কত হলো? কমেন্টে জানান!"))
    follow_cta = clean_text_ass(outro_data.get("follow_cta", "দ্বীনি জ্ঞান বৃদ্ধি করতে আমাদের ফলো করুন!"))
    
    s_lines = split_text_wrap(score_prompt, max_chars=28)
    sy = 720 - (len(s_lines) - 1) * 40
    
    dialogues = [
        f"Dialogue: 0,0:00:00.00,0:00:10.00,TopBadge,,0,0,0,,{{\\pos(540,440)}}মূল্যায়ন সম্পন্ন"
    ]
    for sl in s_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,ScoreText,,0,0,0,,{{\\pos(540,{sy})}}{sl}")
        sy += 75
        
    dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,ScoreSub,,0,0,0,,{{\\pos(540,890)}}কমেন্টে লিখুন: ৫/৫, ৪/৫ অথবা ৩/৫")
    
    c_lines = split_text_wrap(follow_cta, max_chars=32)
    cy = 1230 - (len(c_lines) - 1) * 35
    for cl in c_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:10.00,CtaText,,0,0,0,,{{\\pos(540,{cy})}}{cl}")
        cy += 65

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopBadge,Noto Sans Bengali,36,&H0076E600,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: ScoreText,Noto Sans Bengali,60,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1
Style: ScoreSub,Noto Sans Bengali,34,&H0041AFEB,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: CtaText,Noto Sans Bengali,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues) + "\n"

    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    render_ass_to_image(base_bg, ass_file, out_path)
    
    try: os.remove(base_bg)
    except: pass
    try: os.remove(ass_file)
    except: pass
    
    return out_path
