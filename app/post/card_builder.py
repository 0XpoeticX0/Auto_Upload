# -*- coding: utf-8 -*-
import os
import re
import urllib.parse
import time
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont
from app.logger import logger
from app.quiz.card_builder import clean_text_ass
from app.loop_reel.audio_library import get_or_download_quran_audio

CARD_WIDTH = 1080
CARD_HEIGHT = 1350

COLOR_WHITE = (255, 255, 255)
COLOR_CREAM = (244, 240, 230)
COLOR_GOLD = (235, 175, 65)        # Warm golden amber (#EBAF41)
COLOR_EMERALD = (40, 160, 100)
COLOR_BG_DARK = (10, 12, 16)

NEGATIVE_PROMPT = urllib.parse.quote(
    "close-up face, extreme close up, portrait, selfie, blurry, bad anatomy, "
    "low quality, watermark, logo, text, deformed, ugly, duplicate, cropped, "
    "human, person, face, eye, man, woman, child, people, crowd, animal, dog, cat, bird, insect, living being"
)

def download_card_background(prompt: str, output_path: str) -> str:
    """Provides a certified 1080x1350 aesthetic background with zero watermarks and zero living beings."""
    candidates = [
        "app/assets/scenes/moorish_palace_arches.jpg",
        "app/assets/scenes/glowing_calligraphy.jpg",
        "app/assets/scenes/desert_dawn_sunrise.jpg",
        "app/assets/quran_rehal_master.jpg"
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with Image.open(c) as img:
                    img = img.convert("RGB")
                    w, h = img.size
                    target_aspect = 1080 / 1350
                    current_aspect = w / h
                    if current_aspect > target_aspect:
                        new_w = int(h * target_aspect)
                        left = (w - new_w) // 2
                        img = img.crop((left, 0, left + new_w, h))
                    else:
                        new_h = int(w / target_aspect)
                        top = (h - new_h) // 2
                        img = img.crop((0, top, w, top + new_h))
                    img = img.resize((1080, 1350), Image.Resampling.LANCZOS)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    img.save(output_path, "JPEG", quality=95)
                    logger.info(f"Deployed certified 1080x1350 background from: {c}")
                    return output_path
            except Exception as e:
                logger.warning(f"Error preparing background from {c}: {e}")

    img = Image.new("RGB", (1080, 1350), (14, 16, 22))
    img.save(output_path, "JPEG")
    return output_path

def split_text_wrap_ass(text: str, max_chars: int = 36) -> list:
    """Wraps text cleanly for ASS subtitle rendering."""
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
            if cur_visible_len + w_len + 1 <= max_chars or not cur_line:
                cur_line.append(w)
                cur_visible_len += w_len + 1
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_visible_len = w_len
        if cur_line:
            lines.append(" ".join(cur_line))
    return lines

def format_quote_with_highlights_ass(quote_text: str, highlight_phrases: list) -> str:
    """Highlights specific phrases in warm golden amber ASS tags."""
    styled = quote_text
    for hl in highlight_phrases:
        if not hl.strip():
            continue
        clean_hl = hl.strip()
        styled = styled.replace(clean_hl, f"{{\\c&H003DBFF2&}}{{\\b1}}{clean_hl}{{\\r\\c&H00FFFFFF&}}")
    return styled

def create_glassmorphism_canvas(bg_path: str) -> Image.Image:
    """Creates a full-bleed vertical background with cinematic dark vignette and readability overlay."""
    try:
        with Image.open(bg_path).convert("RGB") as bg:
            bg_scaled = bg.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
            overlay = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (6, 8, 12, 185))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CARD_HEIGHT):
                if y < 350:
                    alpha = int(140 + (y / 350) * 50)
                else:
                    alpha = int(190 + min(45, (y - 350) / 1000 * 45))
                for x in range(0, CARD_WIDTH, 4):
                    draw_ov.point((x, y), fill=(6, 8, 12, alpha))
            bg_rgba = bg_scaled.convert("RGBA")
            combined = Image.alpha_composite(bg_rgba, overlay)
            return combined.convert("RGB")
    except Exception as e:
        logger.warning(f"Error building canvas: {e}")
        return Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), COLOR_BG_DARK)

def render_ass_to_image(canvas_path: str, ass_path: str, output_path: str):
    """Renders ASS subtitles onto the base canvas via FFmpeg HarfBuzz font engine."""
    rel_ass = os.path.relpath(ass_path).replace("\\", "/")
    cmd = [
        "ffmpeg", "-y",
        "-i", canvas_path,
        "-vf", f"subtitles='{rel_ass}'",
        "-frames:v", "1",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ==============================================================================
# SLIDE 1: THE COVER HOOK CARD
# ==============================================================================
def render_cover_slide(post_data: dict, bg_path: str, output_path: str) -> str:
    temp_dir = os.path.join("data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    canvas_path = os.path.join(temp_dir, f"cover_canvas_{ts}.jpg")
    ass_path = os.path.join(temp_dir, f"cover_sub_{ts}.ass")

    card = create_glassmorphism_canvas(bg_path)
    draw = ImageDraw.Draw(card)
    
    # Top Gold Category Pill
    draw.rounded_rectangle((100, 90, CARD_WIDTH - 100, 175), radius=24, fill=(18, 16, 10, 230), outline=(235, 175, 65), width=2)
    # Center Frosted Glass Card for Title
    draw.rounded_rectangle((70, 400, CARD_WIDTH - 70, 1040), radius=32, fill=(10, 13, 18, 220), outline=(50, 70, 95), width=2)
    # Decorative Accent Lines
    draw.line((180, 460, CARD_WIDTH - 180, 460), fill=(235, 175, 65), width=2)
    draw.line((180, 980, CARD_WIDTH - 180, 980), fill=(235, 175, 65), width=2)
    # Bottom Swipe Pill
    draw.rounded_rectangle((280, 1160, CARD_WIDTH - 280, 1245), radius=24, fill=(16, 36, 26, 235), outline=(50, 180, 110), width=2)
    card.save(canvas_path, "JPEG", quality=95)

    badge = post_data.get("topic_badge", "✦ দৈনন্দিন সহীহ আমল ও সতর্কতা ✦")
    cover_data = post_data.get("cover", {})
    title_lines = cover_data.get("title_lines", [post_data.get("title", "বরকতময় সুন্নাহ আমল")])
    hl_words = cover_data.get("highlight_phrases", [])

    full_hook = "\\N".join(title_lines)
    for hw in hl_words:
        if hw in full_hook:
            full_hook = full_hook.replace(hw, f"{{\\c&H003DBFF2&}}{{\\b1}}{hw}{{\\r\\c&H00FFFFFF&}}")

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Noto Sans Bengali,34,&H003DBFF2&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,8,70,70,112,1
Style: HookTitle,Noto Sans Bengali,62,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.0,2.0,8,95,95,520,1
Style: SwipeCTA,Noto Sans Bengali,38,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,60,60,1182,1
Style: Watermark,Noto Sans Bengali,24,&H00707070&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.0,0.0,8,60,60,1285,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,Badge,,0,0,0,,{badge}
Dialogue: 0,0:00:00.00,0:00:10.00,HookTitle,,0,0,0,,{{\\fnNoto Sans Bengali\\fs62\\b1\\c&HFFFFFF&}}{full_hook}
Dialogue: 0,0:00:00.00,0:00:10.00,SwipeCTA,,0,0,0,,(সোয়াইপ করুন 👉)
Dialogue: 0,0:00:00.00,0:00:10.00,Watermark,,0,0,0,,@dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    render_ass_to_image(canvas_path, ass_path, output_path)
    return output_path

# ==============================================================================
# CONTENT SLIDE (HADITH / PROBLEM & SUNNAH REMEDY / DUA)
# ==============================================================================
def render_content_slide(slide_data: dict, bg_path: str, output_path: str, slide_idx: int, total_slides: int) -> str:
    temp_dir = os.path.join("data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    canvas_path = os.path.join(temp_dir, f"content_can_{ts}.jpg")
    ass_path = os.path.join(temp_dir, f"content_sub_{ts}.ass")

    card = create_glassmorphism_canvas(bg_path)
    draw = ImageDraw.Draw(card)
    
    title = slide_data.get("title", f"{slide_idx-1}. সহীহ আমল")
    narrator = slide_data.get("header", "").strip()
    main_text = slide_data.get("main_text", slide_data.get("quote", "")).strip()
    hl_phrases = slide_data.get("highlight_phrases", [])
    solution = slide_data.get("solution", "").strip()
    ref = slide_data.get("reference", "").strip()
    arabic = slide_data.get("arabic", "").strip()
    pron = slide_data.get("pronunciation", "").strip()
    meaning = slide_data.get("meaning", "").strip()

    # Top Section Pill
    draw.rounded_rectangle((100, 85, CARD_WIDTH - 100, 165), radius=22, fill=(15, 22, 32, 230), outline=(50, 130, 200), width=2)
    
    # Check slide type: Arabic Dua vs Hadith/Remedy
    if arabic:
        draw.rounded_rectangle((70, 200, CARD_WIDTH - 70, 540), radius=26, fill=(15, 20, 28, 240), outline=(235, 175, 65), width=2)
        draw.rounded_rectangle((70, 570, CARD_WIDTH - 70, 1180), radius=26, fill=(12, 16, 22, 230), outline=(40, 60, 80), width=1)
        card.save(canvas_path, "JPEG", quality=95)

        arabic_lines = split_text_wrap_ass(arabic, max_chars=34)
        full_arabic = "\\N".join(arabic_lines)
        pron_lines = split_text_wrap_ass(f'উচ্চারণ: "{pron}"', max_chars=38)
        full_pron = "\\N".join(pron_lines)
        meaning_lines = split_text_wrap_ass(f'অর্থ: "{meaning}"', max_chars=38)
        full_meaning = "\\N".join(meaning_lines)

        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitlePill,Noto Sans Bengali,34,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,8,70,70,105,1
Style: ArabicText,Noto Sans Arabic,46,&H003DBFF2&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,240,1
Style: PronText,Noto Sans Bengali,36,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.5,0.0,8,95,95,610,1
Style: MeaningText,Noto Sans Bengali,34,&H00D0E8D0&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.5,0.0,8,95,95,860,1
Style: Counter,Noto Sans Bengali,34,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,3,70,110,80,1
Style: Watermark,Noto Sans Bengali,24,&H00707070&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.0,0.0,8,60,60,1285,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,TitlePill,,0,0,0,,{title}
Dialogue: 0,0:00:00.00,0:00:10.00,ArabicText,,0,0,0,,{{\\fs46\\b1}}{full_arabic}
Dialogue: 0,0:00:00.00,0:00:10.00,PronText,,0,0,0,,{{\\fs36\\c&H00FFFFFF&}}{full_pron}
Dialogue: 0,0:00:00.00,0:00:10.00,MeaningText,,0,0,0,,{{\\fs34\\c&H00D0E8D0&}}{full_meaning}
Dialogue: 0,0:00:00.00,0:00:10.00,Counter,,0,0,0,,({slide_idx}/{total_slides}) 👉
Dialogue: 0,0:00:00.00,0:00:10.00,Watermark,,0,0,0,,@dailydos_islam
"""
    else:
        if solution:
            draw.rounded_rectangle((65, 200, CARD_WIDTH - 65, 720), radius=26, fill=(10, 13, 18, 230), outline=(40, 55, 75), width=2)
            draw.rounded_rectangle((65, 750, CARD_WIDTH - 65, 1180), radius=26, fill=(16, 32, 24, 230), outline=(40, 140, 85), width=2)
        else:
            draw.rounded_rectangle((65, 200, CARD_WIDTH - 65, 1180), radius=28, fill=(10, 13, 18, 230), outline=(40, 55, 75), width=2)
            
        if ref:
            draw.rounded_rectangle((90, 1210, 540, 1275), radius=14, fill=(18, 22, 28, 240), outline=(60, 75, 90), width=1)
        card.save(canvas_path, "JPEG", quality=95)

        styled_main = format_quote_with_highlights_ass(main_text, hl_phrases)
        main_lines = split_text_wrap_ass(styled_main, max_chars=34)
        full_main = "\\N".join(main_lines)

        sol_lines = split_text_wrap_ass(solution, max_chars=36) if solution else []
        full_sol = "\\N".join(sol_lines)

        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitlePill,Noto Sans Bengali,34,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,8,70,70,105,1
Style: Narrator,Noto Sans Bengali,36,&H003DBFF2&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,8,95,95,235,1
Style: MainText,Noto Sans Bengali,48,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,315,1
Style: SolText,Noto Sans Bengali,42,&H00D0FFD0&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,790,1
Style: RefBadge,Noto Sans Bengali,28,&H00D0D0D0&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.0,0.0,1,110,70,90,1
Style: Counter,Noto Sans Bengali,34,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,3,70,110,90,1
Style: Watermark,Noto Sans Bengali,24,&H00707070&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.0,0.0,8,60,60,1285,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,TitlePill,,0,0,0,,{title}
"""
        if narrator:
            ass_content += f"Dialogue: 0,0:00:00.00,0:00:10.00,Narrator,,0,0,0,,{narrator}\n"
        ass_content += f"Dialogue: 0,0:00:00.00,0:00:10.00,MainText,,0,0,0,,{{\\fs48\\b1\\c&HFFFFFF&}}{full_main}\n"
        if solution:
            ass_content += f"Dialogue: 0,0:00:00.00,0:00:10.00,SolText,,0,0,0,,{{\\fs42\\c&H00D0FFD0&}}{full_sol}\n"
        if ref:
            ass_content += f"Dialogue: 0,0:00:00.00,0:00:10.00,RefBadge,,0,0,0,,📚 [{ref}]\n"
        ass_content += f"""Dialogue: 0,0:00:00.00,0:00:10.00,Counter,,0,0,0,,({slide_idx}/{total_slides}) 👉
Dialogue: 0,0:00:00.00,0:00:10.00,Watermark,,0,0,0,,@dailydos_islam
"""

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    render_ass_to_image(canvas_path, ass_path, output_path)
    return output_path

# ==============================================================================
# FINAL SLIDE: ACTION BLUEPRINT & SAVE CTA
# ==============================================================================
def render_final_action_slide(slide_data: dict, bg_path: str, output_path: str, slide_idx: int, total_slides: int) -> str:
    temp_dir = os.path.join("data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    ts = int(time.time() * 1000)
    canvas_path = os.path.join(temp_dir, f"action_can_{ts}.jpg")
    ass_path = os.path.join(temp_dir, f"action_sub_{ts}.ass")

    card = create_glassmorphism_canvas(bg_path)
    draw = ImageDraw.Draw(card)
    
    # Top Pill
    draw.rounded_rectangle((100, 85, CARD_WIDTH - 100, 165), radius=22, fill=(15, 22, 32, 230), outline=(50, 130, 200), width=2)
    # Action Rule Box (y: 190 to 660)
    draw.rounded_rectangle((65, 190, CARD_WIDTH - 65, 660), radius=24, fill=(16, 26, 20, 230), outline=(40, 120, 75), width=2)
    # Save & Share Community Box (y: 690 to 1180)
    draw.rounded_rectangle((65, 690, CARD_WIDTH - 65, 1180), radius=24, fill=(24, 20, 12, 230), outline=(235, 175, 65), width=2)
    card.save(canvas_path, "JPEG", quality=95)

    title = slide_data.get("title", "৩. আমলের সর্বোত্তম নিয়ম")
    main_text = slide_data.get("main_text", "দোয়া কবুলের সঠিক নিয়ম অনুযায়ী আমল করুন।").strip()
    sol = slide_data.get("solution", "").strip()
    dhikr = slide_data.get("dhikr_word", "আমিন")

    action_full = main_text
    if sol:
        action_full = action_full + "\n\n" + sol
    inst_lines = split_text_wrap_ass(action_full, max_chars=38)
    full_inst = "\\N".join(inst_lines)

    cta_text = f"পরবর্তীতে আমল করার জন্য পোস্টটি 🔖 Save করুন এবং কমেন্টে একবার \"{dhikr}\" লিখে বন্ধুদের সাথে শেয়ার করুন! 🤍"
    cta_lines = split_text_wrap_ass(cta_text, max_chars=36)
    full_cta = "\\N".join(cta_lines)

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitlePill,Noto Sans Bengali,34,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,8,70,70,105,1
Style: ActionHeader,Noto Sans Bengali,36,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,220,1
Style: ActionBody,Noto Sans Bengali,36,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,290,1
Style: CTAHeader,Noto Sans Bengali,36,&H003DBFF2&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,720,1
Style: CTABody,Noto Sans Bengali,40,&H00FFFFFF&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,2.0,1.0,8,95,95,800,1
Style: FollowCredit,Noto Sans Bengali,28,&H003DBFF2&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,1,100,70,90,1
Style: Counter,Noto Sans Bengali,34,&H0041AFEB&,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,1.5,0.0,3,70,100,90,1
Style: Watermark,Noto Sans Bengali,24,&H00707070&,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,1.0,0.0,8,60,60,1285,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,TitlePill,,0,0,0,,{title}
Dialogue: 0,0:00:00.00,0:00:10.00,ActionHeader,,0,0,0,,💡 দৈনন্দিন জীবনের শিক্ষা ও আমল:
Dialogue: 0,0:00:00.00,0:00:10.00,ActionBody,,0,0,0,,{{\\fs36\\c&HFFFFFF&}}{full_inst}
Dialogue: 0,0:00:00.00,0:00:10.00,CTAHeader,,0,0,0,,💬 আজকের জিকির ও আমল:
Dialogue: 0,0:00:00.00,0:00:10.00,CTABody,,0,0,0,,{{\\fs40\\c&HFFFFFF&}}{full_cta}
Dialogue: 0,0:00:00.00,0:00:10.00,FollowCredit,,0,0,0,,👉 Follow: @dailydos_islam
Dialogue: 0,0:00:00.00,0:00:10.00,Counter,,0,0,0,,({slide_idx}/{total_slides}) 🏁
Dialogue: 0,0:00:00.00,0:00:10.00,Watermark,,0,0,0,,@dailydos_islam
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    render_ass_to_image(canvas_path, ass_path, output_path)
    return output_path

# ==============================================================================
# ORCHESTRATOR: DYNAMIC MULTI-SLIDE CAROUSEL
# ==============================================================================
def create_carousel_image_cards(post_data: dict, output_dir: str = "data/output") -> list[str]:
    """Generates matching 1080x1350 image cards for the dynamic Carousel."""
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    timestamp = int(time.time())
    bg_path = os.path.join(temp_dir, f"carousel_bg_{timestamp}.jpg")
    
    visual_p = post_data.get("visual_prompt", "vertical 4:5, aesthetic serene prayer rug on polished wooden floor before large window, warm soft dawn rays, photorealistic 8k, no people")
    download_card_background(visual_p, bg_path)

    slide_paths = []
    slides = post_data.get("slides", [])
    total_slides = len(slides) + 1  # 1 cover + N content slides
    
    # 1. Slide 1 (Cover Hook)
    s1_path = os.path.join(output_dir, f"carousel_{timestamp}_slide1_cover.jpg")
    render_cover_slide(post_data, bg_path, s1_path)
    slide_paths.append(s1_path)
    
    # 2. Content Slides
    for idx, s in enumerate(slides):
        slide_idx = idx + 2
        is_last = (slide_idx == total_slides)
        s_path = os.path.join(output_dir, f"carousel_{timestamp}_slide{slide_idx}.jpg")
        
        if is_last:
            render_final_action_slide(s, bg_path, s_path, slide_idx, total_slides)
        else:
            render_content_slide(s, bg_path, s_path, slide_idx, total_slides)
        slide_paths.append(s_path)

    logger.info(f"Successfully generated {len(slide_paths)}-Slide Image Carousel in {output_dir}")
    return slide_paths

def create_carousel_video_slides(image_paths: list[str], output_dir: str = "data/output") -> list[str]:
    """
    Renders matching 6-second 1080x1350 Micro-Videos with subtle zoom push and soothing Quran recitation.
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_path = get_or_download_quran_audio(duration=6.0)
    
    video_paths = []
    fps = 30
    duration = 6.0
    total_frames = int(fps * duration)
    zoom_total = 0.05  # Subtle 1.05x continuous push-in for micro-video
    
    for idx, img_path in enumerate(image_paths):
        out_vid = img_path.replace(".jpg", ".mp4")
        logger.info(f"Rendering 4:5 Micro-Video Slide {idx+1}/{len(image_paths)}: {out_vid}...")
        
        base_img = Image.open(img_path).convert("RGB")
        orig_w, orig_h = base_img.size
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{orig_w}x{orig_h}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-i", audio_path,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            out_vid
        ]
        
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(total_frames):
            if proc.poll() is not None:
                break
            p = i / float(total_frames - 1) if total_frames > 1 else 0.0
            current_scale = 1.0 + (zoom_total * p)
            
            crop_w = orig_w / current_scale
            crop_h = orig_h / current_scale
            crop_x = (orig_w - crop_w) / 2.0
            crop_y = (orig_h - crop_h) / 2.0
            
            cropped = base_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            frame = cropped.resize((orig_w, orig_h), Image.Resampling.BILINEAR)
            try:
                proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break
                
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()
        
        video_paths.append(out_vid)
        logger.info(f"Micro-Video Slide {idx+1} rendered successfully: {out_vid}")
        
    return video_paths

# Backward compatibility alias
def create_post_image_card(post_data: dict, output_path: str) -> str:
    cards = create_carousel_image_cards(post_data, os.path.dirname(output_path))
    return cards[0] if cards else output_path
